// Fatia 8 (cliente): número de dano do golpe que MATA e fim da janela de lição pulada.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const game = fs.readFileSync('game.js', 'utf8');
const gs = fs.readFileSync('src/gameState.js', 'utf8');

// [1] o monstro morto sai do game_state: o evento com reação ainda vira número
const fn = game.match(/^function _golpesLetaisComReacao[\s\S]*?^}/m)?.[0];
assert.ok(fn, 'helper dos golpes letais deve existir');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(`${fn}; this.f = _golpesLetaisComReacao;`, ctx);
const anterior = new Map([['m:id_1', {key: 'm:id_1', pos: [3, 4]}], ['m:id_2', {key: 'm:id_2', pos: [5, 5]}]]);
const ev = (key, extra) => Object.assign({entity_key: key, amount: 2, damage_reaction: 'vulnerable'}, extra);
let r = ctx.f([ev('m:id_1')], new Set(), anterior);
assert.strictEqual(r.length, 1);
assert.strictEqual(r[0].key, 'm:id_1');
assert.deepStrictEqual(Array.from(r[0].entry.pos), [3, 4]);
assert.strictEqual(ctx.f([ev('m:id_1')], new Set(['m:id_1']), anterior).length, 0, 'quem segue vivo não é letal');
assert.strictEqual(ctx.f([ev('m:id_9')], new Set(), anterior).length, 0, 'sem estado anterior não há onde desenhar');
assert.strictEqual(ctx.f([ev('m:id_1', {damage_reaction: null})], new Set(), anterior).length, 0, 'sem reação o "Derrotado" basta');
assert.strictEqual(ctx.f([ev('m:id_1', {amount: 0})], new Set(), anterior).length, 0);
r = ctx.f([ev('m:id_1'), ev('m:id_1', {damage_reaction: 'resisted'}), ev('m:id_2', {damage_reaction: 'resisted'})], new Set(), anterior);
assert.strictEqual(r.length, 2);
assert.strictEqual(r[0].events.length, 2);
assert.ok(/_golpesLetaisComReacao\(\s*st\?\.combat_damage_events/.test(game), 'o diff de HP deve usar o helper');
assert.ok(/new Set\(entries\.map\(e => e\.key\)\), _hpEntitySnapshot\)/.test(game), 'compara com o snapshot ANTES de reescrevê-lo');

// [2] a mensagem licao_pulada chega ao renderer e fecha a janela da lição aberta
assert.ok(/case 'licao_pulada':\s*_emit\('licaoPulada'/.test(gs), 'gameState repassa licao_pulada');
const ouvintes = game.match(/GS\.on\('licaoPulada'/g) || [];
assert.strictEqual(ouvintes.length, 1, 'GS.on substitui o ouvinte anterior: só um para licaoPulada');
const bloco = game.match(/GS\.on\('licaoPulada'[\s\S]*?^}\);/m)[0];
assert.ok(/msg\.licao_id !== _licaoUltima\.licao_id/.test(bloco), 'só fecha se for a lição aberta');
assert.ok(/_guiaEncerrar\(\)/.test(bloco));

console.log('tutorial fatia 8 cliente: ok');
