// Regressão: a ferramenta geral Apagar deve remover a ponte inteira ao tocar nela.
// node tools/test_editor_bridge_delete.js
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, 'editor.js'), 'utf8').replace(/\r\n/g, '\n');
function extract(name){
  const i = src.indexOf('  function ' + name + '(');
  assert(i >= 0, 'função não encontrada: ' + name);
  let depth = 0, j = src.indexOf('{', i);
  for(let k = j; k < src.length; k++){
    if(src[k] === '{') depth++;
    else if(src[k] === '}' && --depth === 0) return src.slice(i, k + 1);
  }
  throw new Error('função sem fechamento: ' + name);
}

const bridge = { id: 'ponte_0', inicio: [0, 0], fim: [1, 0], largura: 1 };
const S = {
  tiles: [[1, 1]], entrance: null, exit: null, prisoner: null,
  heroSpawns: [], routeExits: [], monsters: [], chests: [], traps: [],
  decorations: [], secretPassages: [], falas: [], pontes: [bridge],
  materiais: {}, elevacoes: {}, alturasParede: {}, sel: null,
};
const trapAttached = { id: 'armadilha_ponte', tipo: 'chao_illusorio', ponte_id: bridge.id, pos: [0, 0] };
const trapUnrelated = { id: 'armadilha_piso', tipo: 'fosso', pos: [0, 0] };
S.traps.push(trapAttached, trapUnrelated);
const bridgeTilesOf = b => [[b.inicio[0], b.inicio[1]], [b.fim[0], b.fim[1]]];
const bridgeAt = (x, y) => S.pontes.find(b => bridgeTilesOf(b).some(([bx, by]) => bx === x && by === y)) || null;
const removeBridge = new Function('S', extract('removeBridge') + '; return removeBridge;')(S);
const eraseAt = new Function('S', 'DOOR', 'WALL', 'doorUnlink', 'monsterTiles', 'decorTiles', 'bridgeAt', 'removeBridge',
  extract('eraseAt') + '; return eraseAt;')(
  S, 2, 0, () => {}, () => [], () => [], bridgeAt, removeBridge);
eraseAt(1, 0); // clicar no meio da ponte precisa remover o objeto inteiro
assert.deepStrictEqual(S.pontes, [], 'a ferramenta Apagar deve remover a ponte inteira pelo footprint');
assert.strictEqual(S.tiles[0][1], 0, 'a ferramenta Apagar conserva seu comportamento de apagar o tile');
assert.deepStrictEqual(S.traps, [trapUnrelated], 'apagar uma ponte deve limpar armadilhas ligadas a ela');

const selected = { id: 'ponte_1', inicio: [0, 0], fim: [1, 0], largura: 1 };
const selectedState = { ...S, pontes: [selected], sel: { kind: 'bridge', ref: selected } };
const deleteSelectedEntity = new Function('S', 'removeBridge', 'renderPanel', 'render', 'updateStatus',
  extract('deleteSelectedEntity') + '; return deleteSelectedEntity;')(
  selectedState, new Function('S', extract('removeBridge') + '; return removeBridge;')(selectedState),
  () => {}, () => {}, () => {});
assert.strictEqual(deleteSelectedEntity(), true, 'exclusão pelo painel da ponte também deve continuar funcionando');
assert.deepStrictEqual(selectedState.pontes, []);

console.log('OK: ferramenta Apagar remove o footprint completo; exclusão pelo painel continua funcionando.');
