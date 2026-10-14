// Reações elementais — lógica PURA do cliente (sem DOM/canvas/THREE).
(function () {
  const ESTILOS = {
    choque:   { cor: '#7fd4ff', duracaoMs: 700 },
    incendio: { cor: '#ff8a2a', duracaoMs: 900 },
    congelar: { cor: '#bfefff', duracaoMs: 900 },
    crosta:   { cor: '#8a5a44', duracaoMs: 900 },
  };
  function estilo(tipo) { return ESTILOS[tipo] ? Object.assign({}, ESTILOS[tipo]) : null; }

  function _restantes(state, key) {
    const exp = state && state.terrenos_temp && state.terrenos_temp[key];
    return exp == null ? null : Math.max(0, Number(exp) - Number(state.round));
  }

  // Crostas de lava que se desfazem na próxima virada (≤ 1 rodada restante).
  function crostasAcabando(state) {
    const out = [];
    const mats = (state && state.materiais) || {};
    for (const key of Object.keys(mats)) {
      if (mats[key] !== 'lava_solidificada') continue;
      const resta = _restantes(state, key);
      if (resta != null && resta <= 1) out.push(key.split(',').map(Number));
    }
    return out;
  }

  function _sobPonte(state, x, y) {
    return ((state && state.pontes) || []).some(p => ((p && p.tiles) || []).some(t => t && t[0] === x && t[1] === y));
  }

  function descreverCasa(state, x, y) {
    const key = `${x},${y}`;
    const mat = state && state.materiais && state.materiais[key];
    if (mat === 'piche') {
      const emChamas = ((state && state.zonas_especiais) || []).some(z => z && z.ativa && z.tipo === 'chamas_piche'
        && (z.tiles || []).some(t => `${t[0]},${t[1]}` === key));
      return { chave: emChamas ? 'ui.reacao.casa.piche_chamas' : 'ui.reacao.casa.piche', params: {} };
    }
    // Água sob ponte não protege (o servidor ignora a água sob a ponte): sem promessa.
    const ehAgua = mat === 'agua' || mat === 'agua_profunda' || mat === 'rodamoinho' || mat === 'rodamoinho_profundo';
    if (ehAgua && _sobPonte(state, x, y)) return null;
    if (mat === 'agua') return { chave: 'ui.reacao.casa.agua', params: {} };
    if (mat === 'agua_profunda' || mat === 'rodamoinho' || mat === 'rodamoinho_profundo')
      return { chave: 'ui.reacao.casa.agua_fogo', params: {} };
    if (mat === 'pantano') return { chave: 'ui.reacao.casa.pantano', params: {} };
    if (mat === 'lava_solidificada')
      return { chave: 'ui.reacao.casa.crosta', params: { n: Math.max(1, _restantes(state, key) || 1) } };
    return null;
  }

  window.ReacoesElementais = { estilo, crostasAcabando, descreverCasa };
})();
