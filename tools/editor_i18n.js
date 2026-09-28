"use strict";
// Cola do EDITOR com o motor de idioma (src/i18n.js). É o que o game.js faz para
// o jogo — t(), aplicar data-i18n, persistir a escolha —, em versão do editor.
//
// Carregado DEPOIS de src/lang/*.js e src/i18n.js e ANTES dos módulos do editor
// (tools/editor.html), por isso já roda no carregamento: o primeiro render dos
// módulos sai no idioma certo.
//
// • t(chave, params): global (window.t). Os módulos são IIFEs; um `t` local
//   (const t = …, (t) => …) SOMBREIA este — renomeie o local antes de migrar o
//   arquivo (o placar tools/test_editor_idioma.py [5] aponta onde há).
// • nomeCat(família, id, padrão): nome de catálogo traduzido pelo id; sem chave
//   (item/monstro criado pelo autor) devolve o padrão — o nome do autor.
// • Idioma em localStorage["lfh_lang"], a MESMA chave do jogo: o editor é
//   servido pelo mesmo servidor (/tools/editor.html), logo mesma origem.
// • trocarIdioma: reaplica a moldura (data-i18n) e redesenha a aba ativa por
//   setTab(abaAtual), que reconstrói a aba a partir do estado do módulo.
(function () {
  const CHAVE = "lfh_lang";
  const LANG_HTML = { pt: "pt-BR", en: "en" };

  function lerIdioma() {
    try { return window.localStorage.getItem(CHAVE) || window.I18N.PADRAO; }
    catch (e) { return window.I18N.PADRAO; }
  }
  function gravarIdioma(code) {
    try { window.localStorage.setItem(CHAVE, code); } catch (e) { /* aba privada */ }
  }

  function t(chave, params) { return window.I18N.t(chave, params); }

  function nomeCat(familia, id, padrao) {
    const k = "cat." + familia + "." + id + ".nome";
    return window.I18N.tem(k) ? window.I18N.t(k) : padrao;
  }

  // Só para elemento cujo conteúdo INTEIRO é o texto: textContent apaga filhos.
  // Rótulo com <input> dentro leva o texto num <span data-i18n>.
  function aplicar(raiz) {
    const alvo = raiz || document;
    alvo.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
    alvo.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
    alvo.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  }

  function sincronizar() {
    const sel = document.getElementById("ed-lang");
    if (sel) sel.value = window.I18N.lang;
    document.documentElement.lang = LANG_HTML[window.I18N.lang] || window.I18N.lang;
  }

  function trocarIdioma(code) {
    if (window.I18N.SUPORTADOS.indexOf(code) < 0 || code === window.I18N.lang) return;
    window.I18N.setLang(code);
    gravarIdioma(code);
    aplicar(document);
    sincronizar();
    if (typeof window.setTab === "function" && window._abaAtualEditor)
      window.setTab(window._abaAtualEditor);
  }

  function iniciar() {
    window.I18N.setLang(lerIdioma());
    aplicar(document);
    sincronizar();
    const sel = document.getElementById("ed-lang");
    if (sel) sel.onchange = () => trocarIdioma(sel.value);
  }

  window.t = t;
  window.nomeCat = nomeCat;
  window.EDITOR_I18N = { t, nomeCat, aplicar, trocarIdioma, iniciar };
  iniciar();
})();
