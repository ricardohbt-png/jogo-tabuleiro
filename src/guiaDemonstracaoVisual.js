// Relógio isolado para prévias do tutorial; não conhece estado nem ações do jogo.
(function () {
  const DURACAO_PADRAO_MS = 1200;
  const OPERACOES_VISUAIS = new Set([
    'prever_movimento', 'prever_equipamento', 'prever_habilidade'
  ]);

  function criar(opcoes = {}) {
    const agendar = opcoes.agendar || (fn => requestAnimationFrame(fn));
    const cancelarAgendamento = opcoes.cancelarAgendamento || (id => cancelAnimationFrame(id));
    const agora = opcoes.agora || (() => (typeof performance !== 'undefined' ? performance.now() : Date.now()));
    const aoQuadro = typeof opcoes.aoQuadro === 'function' ? opcoes.aoQuadro : () => {};
    const aoFim = typeof opcoes.aoFim === 'function' ? opcoes.aoFim : () => {};
    const duracao = Number.isFinite(opcoes.duracaoMs) && opcoes.duracaoMs > 0
      ? opcoes.duracaoMs : DURACAO_PADRAO_MS;
    let idQuadro = null;
    let inicioMs = 0;
    let operacaoAtual = null;
    let contextoAtual = null;
    let estaAtivo = false;

    function cancelar() {
      if (idQuadro !== null) cancelarAgendamento(idQuadro);
      idQuadro = null;
      estaAtivo = false;
      operacaoAtual = null;
      contextoAtual = null;
      return true;
    }

    function quadro() {
      idQuadro = null;
      if (!estaAtivo) return;
      const progresso = Math.max(0, Math.min(1, (agora() - inicioMs) / duracao));
      aoQuadro({ operacao: operacaoAtual, progresso, contexto: contextoAtual });
      if (progresso >= 1) {
        estaAtivo = false;
        operacaoAtual = null;
        contextoAtual = null;
        aoFim();
        return;
      }
      idQuadro = agendar(quadro);
    }

    function iniciar(operacao, contexto) {
      cancelar();
      if (!operacao || typeof operacao !== 'object' || Array.isArray(operacao)
          || !OPERACOES_VISUAIS.has(operacao.acao)) return false;
      operacaoAtual = Object.assign({}, operacao);
      contextoAtual = contexto == null ? null : contexto;
      inicioMs = agora();
      estaAtivo = true;
      aoQuadro({ operacao: operacaoAtual, progresso: 0, contexto: contextoAtual });
      idQuadro = agendar(quadro);
      return true;
    }

    return { iniciar, cancelar, ativo: () => estaAtivo };
  }

  window.GuiaDemonstracaoVisual = { criar, DURACAO_PADRAO_MS };
})();
