// Regra de movimento no piche na prévia compartilhada 2D/3D.
'use strict';
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
let sock;
global.WebSocket = class { constructor(){ this.readyState = 1; sock = this; } send(){} close(){} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'x' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(root, 'src', 'gameState.js'), 'utf8') + '; GS');
GS.connect('ws://x', 'Ana', 'create');
let pass = 0, fail = 0;
function check(label, ok) { if (ok) { pass++; console.log('  ✅ ' + label); } else { fail++; console.log('  ❌ ' + label); } }

const tiles = [Array(7).fill(1)];
const explored = new Set(tiles[0].map((_, x) => `${x},0`));
function load({ start = 0, tar = [2], bridge = [], flight = false } = {}) {
  const actor = { id: 'h', pos: [start, 0], alive: true, moves_left: 6,
    ...(flight ? { voo: true, altura: 1 } : {}) };
  const materiais = Object.fromEntries(tar.map(x => [`${x},0`, 'piche']));
  const st = { type: 'game_state', tiles, players: [actor], monsters: [], decorations: [],
    rooms: [], explored: [...explored], materiais,
    pontes: bridge.map(x => ({ tiles: [[x, 0]] })) };
  sock.onmessage({ data: JSON.stringify(st) });
  return { actor, materiais, state: st };
}
console.log('\n[1] Entrar no piche encerra o movimento na primeira casa coberta');
load();
const reach = new Set(); GS.bfsReachable(tiles, explored, 0, 0, 6, reach);
check('piche alcançável', reach.has('2,0'));
check('casas depois do piche não ficam alcançáveis', !reach.has('3,0') && !reach.has('6,0'));
check('caminho não atravessa o piche', GS.findPath(tiles, explored, 0, 0, 3, 0, 6) === null);
const partial = GS.findPath(tiles, explored, 0, 0, 6, 0, 6, true);
check('caminho parcial termina no piche', Array.isArray(partial) && partial.length === 2);

console.log('\n[2] Começar sobre o piche permite só um passo');
load({ start: 2 });
const fromTar = new Set(); GS.bfsReachable(tiles, explored, 2, 0, 6, fromTar);
check('pode sair uma casa para qualquer lado', fromTar.has('1,0') && fromTar.has('3,0'));
check('não alcança a segunda casa após sair', !fromTar.has('0,0') && !fromTar.has('4,0'));
check('caminho de dois passos não existe', GS.findPath(tiles, explored, 2, 0, 4, 0, 6) === null);

console.log('\n[3] Voo e ponte preservam a exceção existente');
load({ tar: [2], flight: true });
const flying = new Set(); GS.bfsReachable(tiles, explored, 0, 0, 6, flying);
check('voo acima do chão atravessa o piche', flying.has('6,0'));
load({ tar: [2], bridge: [2] });
const bridged = new Set(); GS.bfsReachable(tiles, explored, 0, 0, 6, bridged);
check('ponte sobre o piche permite seguir', bridged.has('6,0'));

console.log('\n[4] Servos e prisioneiro recebem o contexto correto na prévia 2D/3D');
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
check('alcance 2D considera o terreno do servo/prisioneiro',
  game.includes('{state, materiais: state.materiais, actor: selAnimado2D}')
    && game.includes('{state, materiais: state.materiais, actor: selPris2D}'));
check('alcance 3D considera o terreno do servo/prisioneiro',
  game.includes('{state, materiais: state.materiais, actor: selAnimado3D}')
    && game.includes('{state, materiais: state.materiais, actor: selPris3D}'));
check('cliques 2D/3D e gamepad usam actor nos caminhos de servo/prisioneiro',
  game.includes('actor: peca.ref') && game.includes('actor: _prisC') && game.includes('actor: a}'));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
