// Intenção dos monstros — lógica PURA do cliente (sem DOM, canvas ou THREE).
// O servidor prevê (prever_intencoes → intencoes_monstros); aqui só se decide
// o que mostrar. Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
(function () {
  const MODOS = ['off', 'grupo', 'todas'];
  const CORES = { corpo: '#e5484d', distancia: '#f08a24', ameaca: '#9b5de5' };

  function lerModo(raw) { return MODOS.includes(raw) ? raw : 'grupo'; }
  function proximoModo(modo) { return MODOS[(MODOS.indexOf(modo) + 1) % MODOS.length]; }

  // Resposta velha: a rodada da mensagem não bate com a do estado atual.
  function descartar(msg, state) {
    if (!msg || !state) return true;
    return msg.rodada !== state.round;
  }

  // modo: off | grupo (só quem alcança alguém) | todas. O monstro em destaque
  // (mouse/tooltip) entra sempre e é "forte".
  function selecionar(itens, opts) {
    const { modo, destaqueId } = opts || {};
    if (!Array.isArray(itens)) return [];
    const saida = [];
    for (const it of itens) {
      if (!it || typeof it !== 'object') continue;
      const forte = destaqueId != null && String(it.monstro_id) === String(destaqueId);
      const entra = forte || modo === 'todas' || (modo === 'grupo' && it.alcanca === true);
      if (entra) saida.push(Object.assign({}, it, { forte }));
    }
    return saida;
  }

  function contar(selecionados) {
    const n = {};
    for (const it of selecionados || []) n[it.alvo_id] = (n[it.alvo_id] || 0) + 1;
    return n;
  }

  function estilo(item) {
    const firme = item && item.certeza === 'firme';
    return {
      cor: CORES[item && item.acao] || CORES.corpo,
      tracejado: !firme,
      opacidade: firme ? 0.95 : 0.6,
    };
  }

  window.IntencaoMonstros = { MODOS, lerModo, proximoModo, descartar, selecionar, contar, estilo };
})();
