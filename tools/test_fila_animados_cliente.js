// Fila de servos animados — lado do cliente (puro).
// Roda da raiz: node tools/test_fila_animados_cliente.js
//
// Exercita GS.animadoPendenteParaEncerrar, o predicado que decide se o botao
// "encerrar" fecha a vez de UMA peca da janela pos-turno do mago ou encerra o
// turno do heroi. E logica pura: nao toca DOM nem WebSocket.
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
function check(nome, cond) {
  if (cond) { PASS++; console.log('  ✅ ' + nome); }
  else { FAIL++; console.log('  ❌ ' + nome); }
}

// injectPreviewState faz myPid = msg.master_pid e passa pelo _handle normal,
// que e o unico caminho de entrada de estado do modulo.
function estado({ atual, ordem = [], animados = [], prisioneiro = null, janela = 'm' }) {
  GS.injectPreviewState({
    type: 'game_state',
    master_pid: 'm',
    tiles: [[1]], explored: [], monsters: [], chests: [],
    players: [{ id: 'm', name: 'Pedro', alive: true, pos: [0, 0], animados }],
    prisoner: prisioneiro,
    animados_turn: janela,
    animados_order: ordem,
    animados_atual: { m: atual },
  });
}
const servo = (id, extra = {}) => Object.assign(
  { id, nome: id, pos: [1, 1], vida_atual: 8 }, extra);

const A = servo('a'), B = servo('b'), C = servo('c');

console.log('\n[1] Sem selecao visual, segue a fila do servidor');
estado({ atual: 'a', ordem: ['a', 'b', 'c'], animados: [A, B, C] });
check('null devolve o atual', GS.animadoPendenteParaEncerrar(null) === 'a');

console.log('\n[2] Fora da janela, o botao encerra o TURNO (devolve null)');
estado({ atual: 'a', ordem: ['a'], animados: [A], janela: 'outro' });
check('janela de outro jogador', GS.animadoPendenteParaEncerrar(null) === null);
estado({ atual: null, ordem: [], animados: [], janela: null });
check('sem janela aberta', GS.animadoPendenteParaEncerrar(null) === null);

console.log('\n[3] Override manual: servo AINDA nao usado e respeitado');
estado({ atual: 'a', ordem: ['a', 'b', 'c'], animados: [A, B, C] });
check('escolher o "c" encerra o "c"', GS.animadoPendenteParaEncerrar('c') === 'c');
check('escolher o proprio atual', GS.animadoPendenteParaEncerrar('a') === 'a');

console.log('\n[4] Servo JA encerrado cai de volta no atual (nao gera recusa)');
// A fila avancou para "b": logo "a" ja encerrou, mesmo estando vivo na tela.
estado({ atual: 'b', ordem: ['a', 'b', 'c'], animados: [A, B, C] });
check('"a" ficou para tras -> devolve "b"', GS.animadoPendenteParaEncerrar('a') === 'b');
check('"c" ainda nao foi -> devolve "c"', GS.animadoPendenteParaEncerrar('c') === 'c');

console.log('\n[5] Vez do prisioneiro: todo servo ja passou');
estado({
  atual: 'prisoner', ordem: ['a', 'b'], animados: [A, B],
  prisioneiro: { alive: true, freed: true, rescuer_pid: 'm', pos: [2, 2] },
});
check('clicar num servo devolve o prisioneiro', GS.animadoPendenteParaEncerrar('a') === 'prisoner');
check('selecao do prisioneiro se mantem', GS.animadoPendenteParaEncerrar('prisoner') === 'prisoner');

console.log('\n[6] Servo morto ou dominado nao pode ser encerrado');
const morto = servo('d', { vida_atual: 0 });
const dominado = servo('e', { dominado_por_monstro: 'mX' });
estado({ atual: 'a', ordem: ['a', 'd', 'e'], animados: [A, morto, dominado] });
check('morto cai no atual', GS.animadoPendenteParaEncerrar('d') === 'a');
check('dominado cai no atual', GS.animadoPendenteParaEncerrar('e') === 'a');

console.log('\n[7] Id desconhecido cai no atual');
estado({ atual: 'a', ordem: ['a', 'b'], animados: [A, B] });
check('id que nao existe', GS.animadoPendenteParaEncerrar('nao_existe') === 'a');

console.log('\n' + '='.repeat(46));
console.log('  ' + PASS + ' passaram, ' + FAIL + ' falharam');
console.log('='.repeat(46));
process.exit(FAIL ? 1 : 0);
