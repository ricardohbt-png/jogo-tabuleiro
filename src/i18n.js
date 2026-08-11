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

  function tem(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key);
  }

  // Devolve a chave de nome que serve para este objeto, ou null.
  function _chaveDeNome(o) {
    for (const campoId in FAMILIAS_POR_CAMPO) {
      const id = o[campoId];
      if (typeof id !== 'string' || !id) continue;
      for (const fam of FAMILIAS_POR_CAMPO[campoId]) {
        const key = 'cat.' + fam + '.' + id + '.nome';
        if (tem(key)) return key;
      }
    }
    return null;
  }

  // Percorre a mensagem recebida e troca os nomes de catálogo pelo idioma atual.
  // Muta o objeto de propósito: ele é JSON recém-parseado, ninguém mais o vê.
  // Objeto sem tradução para o seu id fica intacto — é assim que item e monstro
  // criados no editor mantêm o nome autoral.
  function traduzirNomes(msg) {
    if (lang === PADRAO) return msg;   // em português não há o que trocar
    const vistos = new Set();
    (function anda(o) {
      if (!o || typeof o !== 'object' || vistos.has(o)) return;
      vistos.add(o);
      if (Array.isArray(o)) { for (const v of o) anda(v); return; }
      const key = _chaveDeNome(o);
      if (key) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = t(key); break; }
        }
      }
      for (const k in o) anda(o[k]);
    })(msg);
    return msg;
  }

  window.I18N = {
    t: t,
    tem: tem,
    traduzirNomes: traduzirNomes,
    setLang: setLang,
    on: function (fn) { if (typeof fn === 'function') ouvintes.push(fn); },
    get lang() { return lang; },
    SUPORTADOS: SUPORTADOS,
    PADRAO: PADRAO,
  };
})();
