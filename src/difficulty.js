// Módulo de dificuldade compartilhado entre o editor e o cliente de jogo.
// Puro (sem DOM). Exposto como window.Difficulty (browser) / global.Difficulty (node).
// Ponto ÚNICO de calibração das faixas de dificuldade da Camada C.
(function (root) {
  'use strict';
  var CR_POR_TIER = { 1: 0.5, 2: 1.0, 3: 2.0, 4: 5.0 };
  // Faixas por razão CR/poder. Ordem crescente; `max` é o teto exclusivo da faixa.
  var FAIXAS = [
    { key: 'facil',       label: 'Fácil',       color: '#4caf50', max: 0.4 },
    { key: 'equilibrada', label: 'Equilibrada', color: '#c9b037', max: 0.8 },
    { key: 'dificil',     label: 'Difícil',     color: '#e08a2b', max: 1.2 },
    { key: 'mortal',      label: 'Mortal',      color: '#d0473f', max: Infinity }
  ];
  function crFromEntry(entry) {
    if (!entry) return 0;
    var cr = entry.cr;
    if (cr !== undefined && cr !== null && !isNaN(parseFloat(cr))) return parseFloat(cr);
    return CR_POR_TIER[entry.tier] || 1.0;
  }
  function poder(heroes, level) { return Math.max(1, (heroes || 0) * (level || 0)); }
  function faixa(nd, pod) {
    var ratio = nd / Math.max(1, pod);
    for (var i = 0; i < FAIXAS.length; i++) { if (ratio < FAIXAS[i].max) return FAIXAS[i]; }
    return FAIXAS[FAIXAS.length - 1];
  }
  root.Difficulty = { crFromEntry: crFromEntry, poder: poder, faixa: faixa, FAIXAS: FAIXAS };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
