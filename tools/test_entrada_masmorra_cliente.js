// Regressão: GS.on substitui o callback anterior; limpezas não podem apagar a transição.
// node tools/test_entrada_masmorra_cliente.js
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8').replace(/\r\n/g, '\n');
const state = fs.readFileSync(path.join(root, 'src/gameState.js'), 'utf8');
const on = state.match(/function on\(ev, fn\)\s*\{[^\n]+\}/)[0];
const registrations = [...game.matchAll(/^GS\.on\('enterDungeon',/gm)].map(m => {
  const lineEnd = game.indexOf('\n', m.index);
  const end = game.slice(m.index, lineEnd).trimEnd().endsWith(';')
    ? lineEnd : game.indexOf('\n});', m.index) + '\n});'.length;
  return game.slice(m.index, end);
});

for (const three of [false, true]) {
  const calls = [];
  const context = { console, window: { THREE: three ? {} : null }, CITY_MODE: 'image',
    g3: three ? {} : null, mode3D: three, _hpSnapshot: new Map([['old', 10]]),
    _monsterKnowledgeLevels: new Set(['old']),
    showScreen: screen => calls.push(screen),
  };
  for (const name of ['_clearCityTravelTransition', 'fecharFichaCidade', '_limparMortesVisuais',
    '_limparAnimacoesTempestade', 'hideWorldMap', '_fecharEntradaMasmorra', '_sfxPreCarregar',
    '_sonsReset', 'sfx', '_resetTrapPopup', 'destroyCityImage', 'destroyCity3D', 'dispose3D',
    'toggle3D', '_reacoesFuligensLimpar']) context[name] = () => calls.push(name);
  vm.createContext(context);
  vm.runInContext(`const _handlers = {}; ${on}; const GS = { on };`, context);
  for (const registration of registrations) vm.runInContext(registration, context);
  vm.runInContext('_handlers.enterDungeon({});', context);
  assert(calls.includes('screen-game'), 'entrar na masmorra deve mostrar o tabuleiro');
  assert(calls.includes('destroyCityImage'), 'a imagem da cidade deve ser removida');
  assert(calls.includes('_fecharEntradaMasmorra'), 'a entrada da masmorra deve ser fechada');
  assert(calls.includes('_reacoesFuligensLimpar'), 'a fuligem anterior deve ser limpa');
  assert.strictEqual(context._hpSnapshot.size, 0, 'a referência de PV deve ser reiniciada');
  assert.strictEqual(context._monsterKnowledgeLevels.size, 0, 'conhecimento visual deve ser reiniciado');
  assert.strictEqual(calls.includes('dispose3D'), three, 'o renderizador antigo deve ser descartado');
  assert.strictEqual(calls.includes('toggle3D'), three, '3D deve iniciar quando disponível');
  console.log(`OK: cidade → masmorra com ${three ? '3D disponível' : '2D'}`);
}
