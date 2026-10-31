// Janela dos servos: o clique no monstro é do servo, nunca do herói.
// Roda da raiz: node tools/test_janela_servos_clique.js
//
// Bug: com o mago SEM ter agido no turno (action_done falso), clicar num
// monstro na vez do servo virava ataque do mago (que o servidor recusa) ou, no
// 3D, era engolido; o servo só conseguia atacar quando o mago já tinha agido.
'use strict';
const fs = require('fs');
const vm = require('vm');

const src = fs.readFileSync('src/gameState.js', 'utf8');
const sandbox = {
  window: {}, console,
  WebSocket: function () {},
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  setTimeout, clearTimeout, setInterval, clearInterval,
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(src + '\n;globalThis.__GS = GS;', sandbox);
const GS = sandbox.__GS;

let PASS = 0, FAIL = 0;
function check(nome, cond, extra) {
  if (cond) { PASS++; console.log('  ✅ ' + nome); }
  else { FAIL++; console.log('  ❌ ' + nome + (extra ? '\n     ' + extra : '')); }
}

const piso = Array.from({ length: 5 }, () => Array(5).fill(1));
function estado(janela) {
  GS.injectPreviewState({
    type: 'game_state', phase: 'playing',
    master_pid: 'm', current_turn: 'm',
    tiles: piso, explored: [], chests: [],
    monsters: [{ id: 'g', type: 'goblin', hp: 5, pos: [2, 1] }],
    players: [{ id: 'm', name: 'Pedro', class_id: 'mage', alive: true, pos: [1, 1],
                action_done: false, moves_left: 0,
                weapon: { name: 'Adaga', die: 4 },
                animados: [{ id: 'a', nome: 'Esqueleto', pos: [2, 2], vida_atual: 8, moves_left: 4 }] }],
    animados_turn: janela,
    animados_order: janela ? ['a'] : [],
    animados_atual: janela ? { m: 'a' } : {},
    animados_done: [],
  });
}

console.log('\n[1] Fora da janela, o mago adjacente ataca normalmente (controle)');
estado(null);
const fora = GS.resolveTileClick(2, 1);
check('isMyTurn', GS.isMyTurn === true);
check('clique no goblin = ataque do mago', fora && fora.type === 'attack', JSON.stringify(fora));

console.log('\n[2] Na janela dos servos, o mago não age');
estado('m');
const dentro = GS.resolveTileClick(2, 1);
check('clique no goblin NÃO vira ataque do mago', dentro === null, JSON.stringify(dentro));

console.log('\n[3] game.js entrega o clique ao servo antes de baú/item/objeto/3D');
const g = fs.readFileSync('game.js', 'utf8');
check('_alvoAtaqueDoMonstroSobPonteiro ignora a janela dos servos',
  /function _alvoAtaqueDoMonstroSobPonteiro[\s\S]{0,400}animados_turn === GS\.myPid\) return null/.test(g));
check('on3DClick manda o monstro direto ao handleTileClick na janela',
  /animados_turn === GS\.myPid\)\{\s*handleTileClick\(monsterUnderPointer\.pos\[0\], monsterUnderPointer\.pos\[1\]\)/.test(g));
const i0 = g.indexOf('const _janelaServos =');
const iServo = g.indexOf('// ── Controle de servos/elementais');
check('_janelaServos definido antes do bloco dos servos', i0 > 0 && iServo > i0);
const trecho = g.slice(i0, iServo);
check('escada, item no chão, baú e objeto pulam a janela',
  (trecho.match(/!_janelaServos/g) || []).length >= 4);

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
