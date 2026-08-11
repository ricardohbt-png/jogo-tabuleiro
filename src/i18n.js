'use strict';
// ─── IDIOMA (i18n) — motor PURO do cliente ─────────────────────────────────
// Gêmeo do bloco de i18n do server.py: mesmo dicionário (src/lang/strings.js),
// mesma regra de fallback, mesma substituição de {parametro} por nome.
//
// Este módulo NÃO toca no DOM (regra do CLAUDE.md). Quem aplica na tela é o
// game.js, via _i18nApply(); quem persiste a escolha também é o game.js.
(function () {
  const DICT = (typeof window !== 'undefined' && window.LANG_STRINGS) || {};
  const PADRAO = 'pt';
  const SUPORTADOS = ['pt', 'en'];
  const PARAM = /\{(\w+)\}/g;

  let lang = PADRAO;
  const ouvintes = [];

  // Sem tradução no idioma pedido → português. Sem a chave → devolve a própria
  // chave: aparece na tela (fica óbvio o que falta traduzir) e nada quebra.
  function t(key, params) {
    const entry = DICT[key];
    if (!entry) {
      console.warn('[i18n] chave ausente:', key);
      return key;
    }
    let text = entry[lang] || entry[PADRAO] || key;
    if (params) {
      text = text.replace(PARAM, (m, k) => (k in params ? String(params[k]) : m));
    }
    return text;
  }

  function setLang(code) {
    if (SUPORTADOS.indexOf(code) < 0 || code === lang) return;
    lang = code;
    for (const fn of ouvintes) {
      try { fn(code); } catch (e) { console.error('[i18n] ouvinte falhou:', e); }
    }
  }

  // ── Nomes de catálogo ──────────────────────────────────────────────────────
  // As chaves são cat.<família>.<id>.nome, geradas por tools/gerar_vocabulario.py.
  // O id já viaja no payload, então o nome traduzido é achado sem o servidor
  // precisar mandar nada novo. Ordem de busca por campo — não há colisão de id
  // entre famílias hoje, e o gerador falha alto se aparecer uma.
  const FAMILIAS_POR_CAMPO = {
    type: ['monstro', 'decor'],
    id:   ['item', 'guilda', 'magia', 'instrumento', 'armadilha', 'classe'],
  };
  const CAMPOS_NOME = ['name', 'nome'];
  const CAMPOS_DESC = ['desc', 'descricao'];
  // Usada quando o id vem da CHAVE do dicionário pai, caso em que não há campo
  // interno indicando de que família ele é.
  const TODAS_FAMILIAS = ['monstro', 'decor', 'item', 'guilda', 'magia',
                          'instrumento', 'armadilha', 'classe'];

  function tem(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key);
  }

  // Primeiro prefixo cat.<família>.<id> que tenha nome OU descrição no
  // dicionário. Aceitar qualquer um dos dois importa: há entradas com descrição
  // traduzida e sem nome, e o contrário.
  function _tentaFamilias(familias, id) {
    for (const fam of familias) {
      const base = 'cat.' + fam + '.' + id;
      if (tem(base + '.nome') || tem(base + '.desc')) return base;
    }
    return null;
  }

  // `idPai` é a chave sob a qual este objeto estava no dicionário pai. Vários
  // payloads (lobby_state.classes, game_start.instrumentos_base) são dicionários
  // chaveados pelo id, com o valor sem nenhum campo de id dentro.
  function _chaveBase(o, idPai) {
    for (const campoId in FAMILIAS_POR_CAMPO) {
      const id = o[campoId];
      if (typeof id !== 'string' || !id) continue;
      const base = _tentaFamilias(FAMILIAS_POR_CAMPO[campoId], id);
      if (base) return base;
    }
    if (typeof idPai === 'string' && idPai) {
      const base = _tentaFamilias(TODAS_FAMILIAS, idPai);
      if (base) return base;
    }
    return null;
  }

  // Percorre a estrutura e troca nome (e descrição, se soNome for falso) pelo
  // idioma ATUAL. Muta o objeto de propósito. Objeto sem chave no dicionário
  // fica intacto — é assim que item e monstro criados no editor mantêm o nome
  // autoral. Sem saída antecipada em português: os catálogos estáticos do
  // cliente precisam ser reescritos na volta ao português para restaurar o
  // texto original. A troca é por id, nunca por texto, então reaplicar noutro
  // idioma sempre parte da chave e nunca do texto já trocado.
  function aplicarCatalogo(obj, soNome) {
    const vistos = new Set();
    (function anda(o, idPai) {
      if (!o || typeof o !== 'object' || vistos.has(o)) return;
      vistos.add(o);
      if (Array.isArray(o)) { for (const v of o) anda(v, null); return; }
      const base = _chaveBase(o, idPai);
      if (base) {
        if (tem(base + '.nome')) {
          for (const campo of CAMPOS_NOME) {
            if (typeof o[campo] === 'string') { o[campo] = t(base + '.nome'); break; }
          }
        }
        if (!soNome && tem(base + '.desc')) {
          for (const campo of CAMPOS_DESC) {
            if (typeof o[campo] === 'string') { o[campo] = t(base + '.desc'); break; }
          }
        }
      }
      for (const k in o) anda(o[k], k);
    })(obj, null);
    return obj;
  }

  // Caminho das mensagens: em português não há o que trocar, e sair aqui deixa
  // o custo em zero no idioma padrão.
  function traduzirNomes(msg) {
    if (lang === PADRAO) return msg;
    return aplicarCatalogo(msg, false);
  }

  window.I18N = {
    t: t,
    tem: tem,
    traduzirNomes: traduzirNomes,
    aplicarCatalogo: aplicarCatalogo,
    setLang: setLang,
    on: function (fn) { if (typeof fn === 'function') ouvintes.push(fn); },
    get lang() { return lang; },
    SUPORTADOS: SUPORTADOS,
    PADRAO: PADRAO,
  };
})();
