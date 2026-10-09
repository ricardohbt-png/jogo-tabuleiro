// Guia do tutorial — lógica pura (sem DOM, canvas nem THREE).
// O game.js lê o passo recebido do servidor, pergunta aqui QUAL elemento
// destacar e QUANDO endurecer a dica; o desenho é dele.
(function () {
  const TIPOS_CASA = ['casa', 'porta'];
  const TIPOS_ID   = ['botao', 'habilidade', 'bolsa', 'slot', 'monstro', 'hud'];
  const ID_OK = /^[a-z0-9_]+$/;

  // "habilidade:mira_certeira" -> {tipo, id};  "casa:[3,14]" -> {tipo, pos:[3,14]}
  function parseUi(ui) {
    if (typeof ui !== 'string') return null;
    const i = ui.indexOf(':');
    if (i < 1) return null;
    const tipo = ui.slice(0, i), resto = ui.slice(i + 1);
    if (TIPOS_CASA.indexOf(tipo) >= 0) {
      const m = /^\[(\d+),(\d+)\]$/.exec(resto);
      return m ? { tipo, pos: [Number(m[1]), Number(m[2])] } : null;
    }
    if (TIPOS_ID.indexOf(tipo) >= 0 && ID_OK.test(resto)) return { tipo, id: resto };
    return null;
  }

  // Seletor CSS do elemento de DOM correspondente. Devolve null para o que é
  // desenhado no tabuleiro (casa, monstro, porta): para esses, alvoTabuleiro.
  // `ancestral`: o achado é um filho; o halo vai no ancestral indicado.
  // `alternativa`: seletor de reserva quando o primeiro não existe na tela
  // (a bolsa só existe com o inventário aberto; o botão da mochila sempre).
  function seletor(ui) {
    const a = parseUi(ui);
    if (!a) return null;
    if (a.tipo === 'botao' || a.tipo === 'hud') {
      const menu = a.tipo === 'botao' && ['habilidades', 'magias'].indexOf(a.id) >= 0;
      const css = menu
        ? '[data-guia="' + a.tipo + ':' + a.id + '"][data-guia-acao="abrir-menu"]'
        : '[data-guia="' + a.tipo + ':' + a.id + '"]';
      return { css, ancestral: null, alternativa: null };
    }
    if (a.tipo === 'habilidade')
      return { css: '[data-ability-id="' + a.id + '"]', ancestral: 'button', alternativa: null };
    if (a.tipo === 'bolsa')
      return { css: '.inv-bagslot[data-item-id="' + a.id + '"]', ancestral: null,
               alternativa: '[data-guia="botao:inventario"]' };
    if (a.tipo === 'slot')
      return { css: '.inv-slot[data-slot-key="' + a.id + '"]', ancestral: null, alternativa: null };
    return null;
  }

  // Alvo desenhado NO TABULEIRO: {tipo:'casa'|'porta'|'monstro', pos, id?, caminho?}.
  // `minhaPos` [x,y] escolhe o monstro mais próximo; `visivel(x,y)` filtra o que o
  // jogador não enxerga (o halo nunca revela o que a névoa esconde).
  function alvoTabuleiro(ui, estado, minhaPos, visivel) {
    const a = parseUi(ui);
    if (!a || !estado) return null;
    const ve = typeof visivel === 'function' ? visivel : () => true;
    if (a.tipo === 'casa' || a.tipo === 'porta') {
      if (!ve(a.pos[0], a.pos[1])) return null;
      return a.tipo === 'porta' ? { tipo: 'porta', pos: a.pos, caminho: true }
                                : { tipo: 'casa', pos: a.pos };
    }
    if (a.tipo !== 'monstro') return null;
    let melhor = null, melhorD = Infinity;
    for (const m of (estado.monsters || [])) {
      if (!m || m.type !== a.id || !(m.hp > 0) || !m.pos || !ve(m.pos[0], m.pos[1])) continue;
      const d = minhaPos ? Math.max(Math.abs(m.pos[0] - minhaPos[0]), Math.abs(m.pos[1] - minhaPos[1])) : 0;
      if (d < melhorD) { melhorD = d; melhor = m; }
    }
    return melhor ? { tipo: 'monstro', pos: [melhor.pos[0], melhor.pos[1]], id: melhor.id } : null;
  }

  // Placa da sala do herói em evidência (fatia 10): só na vez do herói em foco e só se a
  // casa está visível. Devolve {tipo:'casa', id, pos} ou null.
  function placaEmEvidencia(estado, myPid, visivel) {
    if (!estado || !estado.tutorial || estado.current_turn !== myPid) return null;
    const me = (estado.players || []).find(p => p && p.id === myPid);
    if (!me || me.alive === false || !me.class_id) return null;
    const pc = (estado.tutorial.por_classe || {})[me.class_id];
    const pl = pc && pc.placa;
    if (!pl || !Array.isArray(pl.pos) || pl.pos.length < 2
        || !Number.isFinite(pl.pos[0]) || !Number.isFinite(pl.pos[1])) return null;
    const ve = typeof visivel === 'function' ? visivel : () => true;
    if (!ve(pl.pos[0], pl.pos[1])) return null;
    return { tipo: 'casa', id: pl.id, pos: [pl.pos[0], pl.pos[1]] };
  }

  // [[dx,dy],...] a partir de (fx,fy) -> [[x,y],...] com as casas pisadas.
  function caminhoAbsoluto(passos, fx, fy) {
    if (!Array.isArray(passos)) return [];
    const out = []; let x = fx, y = fy;
    for (const p of passos) { x += p[0]; y += p[1]; out.push([x, y]); }
    return out;
  }

  // 0 = sem dica; 1 = primeira dica; 2 = segunda. `desde` e `agora` em ms.
  function nivelDica(desde, agora, cfg) {
    const s = (agora - desde) / 1000;
    if (!(s >= 0)) return 0;
    if (s >= cfg.dica2S) return 2;
    if (s >= cfg.dica1S) return 1;
    return 0;
  }

  function textoDica(passo, nivel) {
    const d = (passo && passo.dica) || [];
    if (!nivel || !d.length) return '';
    return d[Math.min(nivel, d.length) - 1] || '';
  }

  // Quebra o texto em pedaços: {texto} ou {termo, primeira}. `[[termo]]` só vale com
  // id minúsculo; `vistos` (Set) guarda o que já apareceu para sublinhar só a 1ª vez.
  function segmentos(texto, vistos) {
    if (typeof texto !== 'string' || !texto) return [];
    const ve = vistos || new Set();
    const out = [];
    // `[[atalho:<id>]]` não é glossário: é o atalho do dispositivo em uso (resolvido pelo game.js).
    const re = /\[\[(?:atalho:([a-z0-9_]+)|camera:([a-z0-9_]+)|([a-z0-9_]+))\]\]/g;
    let ultimo = 0, m;
    while ((m = re.exec(texto))) {
      if (m.index > ultimo) out.push({ texto: texto.slice(ultimo, m.index) });
      if (m[1]) out.push({ atalho: m[1] });
      else if (m[2] && CAMERA.indexOf(m[2]) >= 0) out.push({ camera: m[2] });
      else if (!m[2]) {
        out.push({ termo: m[3], primeira: !ve.has(m[3]) });
        ve.add(m[3]);
      }
      ultimo = m.index + m[0].length;
    }
    if (ultimo < texto.length) out.push({ texto: texto.slice(ultimo) });
    return out;
  }

  // Atalhos que o texto do guia pode citar; a chave de idioma depende do dispositivo.
  const ATALHOS = ['inventario', 'encerrar_turno', 'mover'];
  const CAMERA = ['zoom_in', 'zoom_out', 'rotate', 'pan'];
  function chaveAtalho(id, controleAtivo) {
    if (ATALHOS.indexOf(id) < 0) return null;
    return 'ui.tutorial.atalho.' + id + '.' + (controleAtivo ? 'controle' : 'teclado');
  }

  window.GuiaTutorial = { parseUi, seletor, alvoTabuleiro, placaEmEvidencia, caminhoAbsoluto, nivelDica, textoDica, segmentos, ATALHOS, chaveAtalho, CAMERA };
})();
