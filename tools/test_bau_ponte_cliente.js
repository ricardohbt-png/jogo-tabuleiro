// Regressão: o baú 3D deve apoiar no deck da ponte, não no terreno abaixo.
// node tools/test_bau_ponte_cliente.js
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8').replace(/\r\n/g, '\n');
function extract(name){
  const i = game.indexOf('function ' + name + '(');
  assert(i >= 0, 'função não encontrada: ' + name);
  let depth = 0, j = game.indexOf('{', i);
  for(let k = j; k < game.length; k++){
    if(game[k] === '{') depth++;
    else if(game[k] === '}' && --depth === 0) return game.slice(i, k + 1);
  }
  throw new Error('função sem fechamento: ' + name);
}

const chestStart = game.indexOf('// ── Chest 3D models');
const chestEnd = game.indexOf('// ── Itens no chão 3D', chestStart);
assert(chestStart >= 0 && chestEnd > chestStart, 'bloco de atualização dos baús 3D não encontrado');
const chestBlock = game.slice(chestStart, chestEnd);
assert.match(chestBlock,
  /chestMeshes\[chest\.id\]\.position\.y\s*=\s*topoSuperficie3D\(state, chest\.pos\[0\], chest\.pos\[1\], 0\.22\)/,
  'o baú deve usar o topo da superfície da ponte');

const surface = new Function(
  'const ELEVACAO_TERRENO_MIN=-1, ELEVACAO_TERRENO_MAX=40, TERRENO_ELEVACAO_STEP_3D=0.24, PONTE_SUPERFICIE_OFFSET_3D=0.20;'
    + extract('_bridgeTiles2D') + extract('elevacaoTerreno') + extract('topoTerreno3D')
    + extract('ponteNaCasa3D') + extract('topoSuperficie3D')
    + '; return topoSuperficie3D;')();

const state = {
  elevacoes: { '2,3': 4, '5,3': 4 },
  pontes: [{ id: 'ponte_0', inicio: [1, 3], fim: [3, 3], largura: 1, altura: 2 }],
};
assert.strictEqual(surface(state, 2, 3, 0.22), 0.22 + 2 * 0.24 + 0.20,
  'o baú sobre a ponte deve usar a altura do deck');
assert.strictEqual(surface(state, 5, 3, 0.22), 0.22 + 0.24 * 4,
  'fora da ponte, o baú deve continuar apoiado na elevação normal do piso');

console.log('OK: posicionamento do baú usa o deck da ponte e mantém a altura normal no piso.');
