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

  // Seletor CSS do elemento de HUD correspondente. Devolve null para o que
  // ainda não é HUD (casa, monstro, porta, bolsa, slot: fatia do tabuleiro).
  // `ancestral`: o elemento achado é um filho; o halo vai no ancestral indicado.
  function seletor(ui) {
    const a = parseUi(ui);
    if (!a) return null;
    if (a.tipo === 'botao' || a.tipo === 'hud')
      return { css: '[data-guia="' + a.tipo + ':' + a.id + '"]', ancestral: null };
    if (a.tipo === 'habilidade')
      return { css: '[data-ability-id="' + a.id + '"]', ancestral: 'button' };
    return null;
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

  window.GuiaTutorial = { parseUi, seletor, nivelDica, textoDica };
})();
