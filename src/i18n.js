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

  window.I18N = {
    t: t,
    setLang: setLang,
    on: function (fn) { if (typeof fn === 'function') ouvintes.push(fn); },
    get lang() { return lang; },
    SUPORTADOS: SUPORTADOS,
    PADRAO: PADRAO,
  };
})();
