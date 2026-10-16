// Cursor local e testável para as etapas da demonstração assistida.
(function () {
  function criar(opcoes) {
    const validar = opcoes.validar;
    const parseUi = opcoes.parseUi;
    let estado = 'inativa', roteiro = [], indice = 0;
    let alvoAtual = null, ultimaFoco = null, chaveAtual = null, passoAtual = null;
    let previsaoAtual = null;
    let suspensa = false, fallbackAtual = false;

    function publicar(fallback = fallbackAtual) {
      fallbackAtual = !!fallback;
      if (typeof opcoes.aoEstado === 'function')
        opcoes.aoEstado({ estado, alvo: alvoAtual, chave: chaveAtual, fallback: fallbackAtual });
    }

    function executar(operacao) {
      if (!operacao) return false;
      if (operacao.acao === 'prever_movimento' || operacao.acao === 'prever_equipamento'
          || operacao.acao === 'prever_habilidade') {
        previsaoAtual = Object.assign({}, operacao);
        return typeof opcoes.preverVisual === 'function'
          && opcoes.preverVisual(previsaoAtual) !== false;
      }
      if (operacao.acao === 'focar') {
        ultimaFoco = operacao.alvo;
        alvoAtual = operacao.alvo;
        return typeof opcoes.focar === 'function' && opcoes.focar(operacao.alvo) !== false;
      }
      if (operacao.acao === 'abrir_interface') {
        if (operacao.alvo === 'inventario') {
          alvoAtual = 'botao:inventario';
          if (typeof opcoes.inventarioAberto === 'function' && opcoes.inventarioAberto()) return true;
          if (typeof opcoes.abrirInventario !== 'function') return false;
          opcoes.abrirInventario();
          return true;
        }
        if (operacao.alvo === 'habilidades' && typeof opcoes.abrirHabilidades === 'function') {
          alvoAtual = 'botao:habilidades';
          opcoes.abrirHabilidades();
          return true;
        }
        if (operacao.alvo === 'magias' && typeof opcoes.abrirMagias === 'function') {
          alvoAtual = 'botao:magias';
          opcoes.abrirMagias();
          return true;
        }
      }
      return false;
    }

    function carregar(passo, chave) {
      if (typeof opcoes.limparVisual === 'function') opcoes.limparVisual('passo_novo');
      passoAtual = passo || null;
      chaveAtual = chave || null;
      alvoAtual = null;
      ultimaFoco = null;
      indice = 0;
      fallbackAtual = false;
      suspensa = false;
      previsaoAtual = null;
      const declarada = typeof validar === 'function' ? validar(passoAtual) : [];
      roteiro = Array.isArray(declarada) ? declarada.slice() : [];
      if (!roteiro.length && passoAtual && typeof passoAtual.ui === 'string'
          && typeof parseUi === 'function' && parseUi(passoAtual.ui))
        roteiro = [{ acao: 'focar', alvo: passoAtual.ui }];
      estado = roteiro.length ? 'executando' : 'aguardando_jogador';
    }

    function avancar(passo, chave) {
      const novaChave = chave || null;
      if (!chaveAtual || chaveAtual !== novaChave || estado === 'inativa') carregar(passo, chave);
      if (!roteiro.length) {
        fallbackAtual = true;
        publicar(true);
        return true;
      }

      if (suspensa) {
        suspensa = false;
        const atual = roteiro[Math.max(0, indice - 1)];
        const ok = executar(atual);
        estado = indice >= roteiro.length ? 'aguardando_jogador' : 'executando';
        publicar(!ok);
        return true;
      }

      if (indice >= roteiro.length) {
        const foco = ultimaFoco || passoAtual?.ui || null;
        const ok = previsaoAtual && typeof opcoes.preverVisual === 'function'
          ? opcoes.preverVisual(previsaoAtual) !== false
          : (foco && typeof opcoes.focar === 'function' ? opcoes.focar(foco) !== false : true);
        if (foco) { alvoAtual = foco; ultimaFoco = foco; }
        estado = 'aguardando_jogador';
        publicar(!ok);
        return true;
      }

      const atual = roteiro[indice++];
      const ok = executar(atual);
      if (!ok) {
        indice = roteiro.length;
        estado = 'aguardando_jogador';
        publicar(true);
        return true;
      }
      estado = indice >= roteiro.length ? 'aguardando_jogador' : 'executando';
      publicar(false);
      return true;
    }

    function suspender() {
      if (estado === 'inativa') return false;
      if (typeof opcoes.limparVisual === 'function') opcoes.limparVisual('suspender');
      estado = 'suspensa';
      suspensa = true;
      alvoAtual = null;
      publicar(false);
      return true;
    }

    function cancelar() {
      if (typeof opcoes.limparVisual === 'function') opcoes.limparVisual('cancelar');
      estado = 'inativa';
      roteiro = [];
      indice = 0;
      alvoAtual = null;
      ultimaFoco = null;
      chaveAtual = null;
      passoAtual = null;
      suspensa = false;
      previsaoAtual = null;
      fallbackAtual = false;
      publicar(false);
      return true;
    }

    function redesenhar() {
      if (estado === 'inativa') return false;
      if (estado === 'suspensa') { publicar(false); return false; }
      if (ultimaFoco && typeof opcoes.focar === 'function') {
        if (opcoes.focar(ultimaFoco) === false) {
          alvoAtual = null;
          publicar(true);
          return false;
        }
        alvoAtual = ultimaFoco;
      }
      publicar(false);
      return true;
    }

    return {
      avancar,
      iniciar: avancar,
      suspender,
      cancelar,
      interagir: () => {
        if (typeof opcoes.limparVisual === 'function') opcoes.limparVisual('interacao');
        return false;
      },
      redesenhar,
      estado: () => estado,
      alvo: () => alvoAtual,
      chave: () => chaveAtual,
      cursor: () => indice
    };
  }

  function entradaNova(botoes, anteriores, eixoAtivo, eixoAnteriorAtivo) {
    const atuais = Array.isArray(botoes) ? botoes : [];
    const previos = Array.isArray(anteriores) ? anteriores : [];
    const pressionado = botao => typeof botao === 'boolean' ? botao : !!botao?.pressed;
    return atuais.some((botao, i) => pressionado(botao) && !pressionado(previos[i]))
      || (!!eixoAtivo && !eixoAnteriorAtivo);
  }

  window.GuiaDemonstracao = { criar, entradaNova };
})();
