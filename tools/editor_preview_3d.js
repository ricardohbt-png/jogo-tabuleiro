/* Prévia da masmorra do editor.
 *
 * Este arquivo NÃO desenha nada. Ele hospeda o cliente REAL do jogo
 * (index.html?preview=1) num iframe e injeta nele o game_state que o servidor
 * monta com o mesmo load_authored_dungeon usado em partida. Sem renderer
 * próprio e sem carregador próprio, a prévia não tem como divergir do jogo:
 * objeto, monstro ou material novo aparece aqui sem tocar neste arquivo.
 *
 * Nada é salvo nem enviado para nenhuma sala — a masmorra vai como está na tela.
 */
(function () {
  "use strict";
  let active = null;

  function close() {
    if (!active) return;
    window.removeEventListener("message", active.onMessage);
    active.el.remove();
    active = null;
  }

  function setStatus(texto, erro) {
    if (!active) return;
    const bar = active.el.querySelector(".ed3d-status");
    bar.textContent = texto || "";
    bar.classList.toggle("erro", !!erro);
  }

  const ESTADO_ROTULO = {
    carregado:  ["✔", "modelo 3D"],
    carregando: ["⏳", "carregando"],
    erro:       ["✖", "FALHOU ao carregar"],
    imagem:     ["🖼", "imagem 2D (sem modelo 3D)"],
    procedural: ["◻", "forma genérica (sem arte)"],
  };

  // Lista o que cada objeto e cada monstro resolveu como arte 3D. É a resposta
  // para "por que isso não apareceu?": ou o modelo carregou, ou falhou, ou o
  // tipo não tem modelo e caiu no PNG/forma genérica.
  function renderModelos(msg) {
    if (!active) return;
    const linha = (it, kind) => {
      const [icone, rotulo] = ESTADO_ROTULO[it.arte.estado] || ["?", it.arte.estado];
      const alvo = it.arte.caminho ? it.arte.caminho.split("/").pop() : "—";
      const http = it.arte.motivo ? " — " + it.arte.motivo : "";
      return '<div class="ed3d-mrow ed3d-' + it.arte.estado + '">' +
        '<span class="ed3d-mico">' + icone + '</span>' +
        '<b>' + it.nome + '</b> <span class="ed3d-mpos">(' + it.pos.join(",") + ')</span>' +
        '<span class="ed3d-marte" title="' + (it.arte.caminho || "") + '">' + alvo + '</span>' +
        '<span class="ed3d-mest">' + rotulo + http + '</span></div>';
    };
    const box = active.el.querySelector(".ed3d-modelos-corpo");
    const partes = [];
    if (msg.objetos.length) partes.push('<div class="ed3d-mtit">Objetos</div>' +
      msg.objetos.map(o => linha(o, "obj")).join(""));
    if (msg.monstros.length) partes.push('<div class="ed3d-mtit">Monstros</div>' +
      msg.monstros.map(m => linha(m, "mon")).join(""));
    box.innerHTML = partes.join("") || "<em>Nada colocado nesta masmorra.</em>";
  }

  async function enviarEstado() {
    const editor = window.EDITOR;
    if (!editor || !window.EDITOR_SAVE || !window.EDITOR_SAVE.previewDungeon) {
      setStatus("A prévia não pôde carregar (editor incompleto).", true);
      return;
    }
    let defn;
    try {
      defn = editor.buildJSON();
    } catch (e) {
      setStatus("Não consegui ler a masmorra atual: " + e.message, true);
      return;
    }
    setStatus("Montando a prévia…");
    try {
      const res = await window.EDITOR_SAVE.previewDungeon(defn);
      if (!active) return;   // o autor fechou a prévia durante a espera
      active.frame.contentWindow.postMessage(
        { type: "preview_state", state: res.state }, "*");
      // Contagem sempre à vista: se o número não bater com o que está no editor,
      // alguma coisa se perdeu no caminho e o autor descobre na hora.
      const r = res.state.preview_resumo || {};
      const conta = `${r.monstros || 0} monstro(s) · ${r.objetos || 0} objeto(s) · ` +
                    `${r.baus || 0} baú(s) · ${r.armadilhas || 0} armadilha(s)`;
      setStatus(res.avisos.length ? conta + "  ⚠️ " + res.avisos.join(" · ") : conta);
    } catch (e) {
      setStatus("Falha ao montar a prévia: " + e.message +
                " — o servidor está rodando?", true);
    }
  }

  function open() {
    if (active) { close(); return; }
    const el = document.createElement("div");
    el.className = "ed3d-overlay";
    el.innerHTML =
      '<div class="ed3d-head"><b>◈ Prévia — masmorra atual</b>' +
      '<span class="ed3d-hint">Mesma aparência do jogo · esq: orbitar · roda: zoom · dir: mover</span>' +
      '<button type="button" id="ed3d-close">← Voltar ao editor</button></div>' +
      '<div class="ed3d-status"></div>' +
      // Endereço pelo servidor quando o editor está aberto como arquivo local:
      // em file:// o GLTFLoader (XHR) é bloqueado e NENHUM .glb carrega.
      '<div class="ed3d-view"><iframe class="ed3d-frame" src="' +
        (window.EDITOR_CLIENTE ? window.EDITOR_CLIENTE.url("?preview=1")
                               : "../index.html?preview=1") + '"></iframe>' +
      '<details class="ed3d-modelos"><summary>🧩 Arte 3D de cada objeto</summary>' +
      '<div class="ed3d-modelos-corpo"><em>Aguardando a prévia…</em></div></details></div>';
    document.body.appendChild(el);

    const frame = el.querySelector(".ed3d-frame");
    // O cliente avisa quando a tela de jogo já existe; só então o estado vai
    // (antes disso o init3D não teria onde desenhar).
    const onMessage = (ev) => {
      if (!ev.data) return;
      if (ev.data.type === "preview_ready") enviarEstado();
      if (ev.data.type === "preview_modelos") renderModelos(ev.data);
    };
    window.addEventListener("message", onMessage);
    active = { el, frame, onMessage };
    setStatus("Carregando o jogo…");

    el.querySelector("#ed3d-close").onclick = close;
    el.tabIndex = -1;
    el.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    el.focus();
  }

  const button = document.getElementById("btn-preview-3d");
  if (button) button.onclick = open;
  window.EDITOR_3D_PREVIEW = { open, close };
})();
