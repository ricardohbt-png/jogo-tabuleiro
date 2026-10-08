// Passos guiados da lição (campo `guia`) — lógica pura do editor, sem DOM.
// As constantes espelham o servidor (GUIA_UI_RE, GUIA_MAX_PASSOS, LICAO_VERBOS);
// tools/test_editor_guia.py cobra a sincronia.
(function () {
  const MAX_PASSOS = 8;
  const MAX_DICAS = 2;
  const UI_RE_FONTE = "^(?:(?:botao|habilidade|bolsa|slot|monstro|hud):[a-z0-9_]+|(?:casa|porta):\\[\\d+,\\d+\\])$";
  const UI_RE = new RegExp(UI_RE_FONTE);
  const TIPOS_ID = ["botao", "habilidade", "bolsa", "slot", "monstro", "hud"];
  const TIPOS_CASA = ["casa", "porta"];
  const TIPOS_UI = TIPOS_ID.concat(TIPOS_CASA);
  // Mesma lista de LICAO_VERBOS do servidor (server.py).
  const VERBOS = ["mover_ate", "abrir_porta", "atacar", "matar", "pegar_item", "equipar", "encerrar_turno",
    "usar_item", "usar_magia", "usar_habilidade", "usar_tecnica", "usar_instrumento", "desarmar_armadilha",
    "arremessar_item", "libertar_refem", "proteger", "regenerar", "ataque_extra", "manter_cancao",
    "encerrar_cancao", "comandar_servo", "guiar_refem"];

  const ehChave = (s) => typeof s === "string" && /^ui\.tutorial\.[a-z0-9_.]+$/.test(s);

  function lerUi(ui) {
    if (typeof ui !== "string" || !ui.includes(":")) return { tipo: "", valor: "" };
    const i = ui.indexOf(":");
    const tipo = ui.slice(0, i), resto = ui.slice(i + 1);
    if (TIPOS_CASA.includes(tipo)) {
      const m = /^\[(\d+),(\d+)\]$/.exec(resto);
      return m ? { tipo, valor: m[1] + "," + m[2] } : { tipo, valor: "" };
    }
    return { tipo, valor: resto };
  }

  function montarUi(tipo, valor) {
    const v = String(valor == null ? "" : valor).trim();
    if (!TIPOS_UI.includes(tipo) || !v) return null;
    if (TIPOS_CASA.includes(tipo)) {
      const m = /^(\d+)\s*,\s*(\d+)$/.exec(v);
      return m ? tipo + ":[" + m[1] + "," + m[2] + "]" : null;
    }
    return tipo + ":" + v;
  }

  function carregar(guia) {
    if (!Array.isArray(guia)) return [];
    return guia.filter(p => p && typeof p === "object").map(p => ({
      ...(p.id != null ? { id: String(p.id) } : {}),
      texto: typeof p.texto === "string" ? p.texto : "",
      porque: typeof p.porque === "string" ? p.porque : "",
      ui: typeof p.ui === "string" && p.ui ? p.ui : null,
      dica: Array.isArray(p.dica) ? p.dica.filter(d => typeof d === "string").slice() : [],
      conclui_com: p.conclui_com && typeof p.conclui_com === "object" && p.conclui_com.tipo
        ? JSON.parse(JSON.stringify(p.conclui_com)) : null,
    }));
  }

  // Ordem das chaves = a do gerador (id, texto, porque, ui, dica, conclui_com).
  function serializar(passos) {
    if (!Array.isArray(passos)) return null;
    const out = passos.map(p => {
      const o = {};
      if (p.id != null && p.id !== "") o.id = p.id;
      o.texto = p.texto || "";
      if (p.porque) o.porque = p.porque;
      if (p.ui) o.ui = p.ui;
      const dica = (p.dica || []).filter(d => typeof d === "string" && d.trim() !== "");
      if (dica.length) o.dica = dica;
      if (p.conclui_com && p.conclui_com.tipo) o.conclui_com = JSON.parse(JSON.stringify(p.conclui_com));
      return o;
    });
    return out.length ? out : null;
  }

  // [{codigo, params}] — o editor traduz com V(codigo, params). `n` é o número do passo (1-based).
  function validar(passos) {
    const e = [];
    if (!Array.isArray(passos) || !passos.length) return e;
    if (passos.length > MAX_PASSOS) e.push({ codigo: "guia_muitos", params: { max: MAX_PASSOS } });
    passos.forEach((p, i) => {
      const n = i + 1;
      if (!String(p.texto || "").trim()) e.push({ codigo: "guia_sem_texto", params: { n } });
      if (p.ui && !UI_RE.test(p.ui)) e.push({ codigo: "guia_ui_invalida", params: { n, ui: p.ui } });
      if ((p.dica || []).length > MAX_DICAS) e.push({ codigo: "guia_dicas", params: { n, max: MAX_DICAS } });
      const cc = p.conclui_com;
      if (cc) {
        if (!VERBOS.includes(cc.tipo)) e.push({ codigo: "guia_conclui_invalido", params: { n, tipo: cc.tipo } });
        else if (i === passos.length - 1) e.push({ codigo: "guia_ultimo_conclui", params: { n } });
      }
    });
    return e;
  }

  window.EDITOR_GUIA = { MAX_PASSOS, MAX_DICAS, UI_RE_FONTE, TIPOS_ID, TIPOS_CASA, TIPOS_UI, VERBOS,
    ehChave, lerUi, montarUi, carregar, serializar, validar };
})();
