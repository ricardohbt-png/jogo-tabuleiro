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
function estado({ atual, ordem = [], animados = [], prisioneiro = null, janela = 'm', done = [] }) {
  GS.injectPreviewState({
    type: 'game_state',
    master_pid: 'm',
    tiles: [[1]], explored: [], monsters: [], chests: [],
    players: [{ id: 'm', name: 'Pedro', alive: true, pos: [0, 0], animados }],
    prisoner: prisioneiro,
    animados_turn: janela,
    animados_order: ordem,
    animados_atual: { m: atual },
    animados_done: done,
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
estado({ atual: 'b', ordem: ['a', 'b', 'c'], animados: [A, B, C], done: ['a'] });
check('"a" ficou para tras -> devolve "b"', GS.animadoPendenteParaEncerrar('a') === 'b');
check('"c" ainda nao foi -> devolve "c"', GS.animadoPendenteParaEncerrar('c') === 'c');

console.log('\n[5] Vez do prisioneiro: todo servo ja passou');
estado({
  atual: 'prisoner', ordem: ['a', 'b'], animados: [A, B], done: ['a', 'b'],
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

console.log('\n[8] animadoAttackTargetTiles — regra unica de alcance do servo');
function comMonstros(animado, monstros) {
  GS.injectPreviewState({
    type: 'game_state', master_pid: 'm',
    tiles: Array.from({length:7}, () => [1,1,1,1,1,1,1]),
    explored: [], chests: [],
    monsters: monstros, players: [{ id:'m', name:'Pedro', alive:true, pos:[0,0], animados:[animado] }],
    animados_turn: 'm', animados_order: [animado.id], animados_atual: { m: animado.id },
  });
  return GS.animadoAttackTargetTiles(animado).map(t => t.x + ',' + t.y).sort();
}
const mon = (id, x, y) => ({ id, pos: [x, y], hp: 5, max_hp: 5 });

// Corpo a corpo: CARDINAL, como _cardinal_adjacent no servidor. O clique antigo
// aceitava a diagonal e mandava um ataque que o servidor recusava.
const zumbi = servo('z', { pos: [2, 2] });
check('melee alcanca o ortogonal',
      comMonstros(zumbi, [mon('m1', 2, 1)]).join('|') === '2,1');
check('melee NAO alcanca a diagonal',
      comMonstros(zumbi, [mon('m1', 3, 3)]).length === 0);

// Elemental com ficha: honra o alcance real. Os renders cravavam 1 e mentiam.
const eleme = servo('e', { pos: [2, 2], attacks: [{ range: 2 }] });
check('elemental de alcance 2 alcanca a 2 casas',
      comMonstros(eleme, [mon('m1', 2, 0)]).join('|') === '2,0');
check('elemental de alcance 2 inclui a diagonal',
      comMonstros(eleme, [mon('m1', 3, 3)]).join('|') === '3,3');
check('elemental de alcance 2 alcanca no limite (2 na diagonal)',
      comMonstros(eleme, [mon('m1', 0, 0)]).join('|') === '0,0');
check('elemental de alcance 2 NAO alcanca a 3 casas',
      comMonstros(eleme, [mon('m1', 2, 5)]).length === 0);

// range_shape restringe a linha reta.
const linha = servo('l', { pos: [2, 2], attacks: [{ range: 3, range_shape: 'line' }] });
check('em linha alcanca o ortogonal',
      comMonstros(linha, [mon('m1', 2, 0)]).join('|') === '2,0');
check('em linha NAO alcanca a diagonal',
      comMonstros(linha, [mon('m1', 3, 3)]).length === 0);

// Legado do elemental eletrico.
const eletr = servo('r', { pos: [2, 2], especial: 'linha_3q' });
check('linha_3q alcanca em linha ate 3',
      comMonstros(eletr, [mon('m1', 0, 2)]).join('|') === '0,2');
check('linha_3q NAO alcanca a diagonal',
      comMonstros(eletr, [mon('m1', 4, 4)]).length === 0);

check('monstro morto nunca entra',
      comMonstros(zumbi, [{ id:'d', pos:[2,1], hp:0 }]).length === 0);
check('servo morto nao mira nada',
      GS.animadoAttackTargetTiles(servo('x', { pos:[2,2], vida_atual:0 })).length === 0);
check('sem animado devolve vazio', GS.animadoAttackTargetTiles(null).length === 0);

console.log('\n[11] Raio do Elemental Elétrico — prévia de linha e bloqueios');
const elementalRaio = servo('raio', {
  tipo: 'elemental', tipo_elemental: 'eletrico', pos: [3, 3],
  attacks: [{ name: 'Raio', range: 4, range_shape: 'orthogonal', damage_types: ['lightning'] }],
});
function raioComMapa(animado, tiles, decorations = []) {
  GS.injectPreviewState({
    type: 'game_state', master_pid: 'm', tiles,
    explored: [], chests: [], decorations, monsters: [],
    players: [{ id:'m', name:'Pedro', alive:true, pos:[0,0], animados:[animado] }],
  });
  return GS.animadoAttackRangeTiles(animado).map(t => `${t.x},${t.y}`).sort();
}
const mapaRaio = Array.from({length:8}, () => Array(8).fill(1));
check('prévia inclui alcance ortogonal de quatro casas',
      raioComMapa(elementalRaio, mapaRaio).length === 14);
const mapaParede = mapaRaio.map(row => row.slice());
mapaParede[3][5] = 0;
const alcanceParede = raioComMapa(elementalRaio, mapaParede);
check('parede bloqueia e não destaca casas atrás dela',
      !alcanceParede.includes('5,3') && !alcanceParede.includes('6,3')
        && alcanceParede.includes('4,3'));
const mapaBorda = Array.from({length:4}, () => Array(4).fill(1));
check('casas fora do mapa não entram na prévia',
      raioComMapa(elementalRaio, mapaBorda).every(k => {
        const [x,y] = k.split(',').map(Number); return x < 4 && y < 4;
      }));
const raioOutroElemento = servo('vento', {
  tipo:'elemental', tipo_elemental:'ar', pos:[3,3],
  attacks:[{name:'Raio',range:4,range_shape:'orthogonal',damage_types:['lightning']}],
});
check('outros elementais não recebem a nova prévia',
      raioComMapa(raioOutroElemento, mapaRaio).length === 0);

console.log('\n[9] Escolha fora de ordem nao deixa a selecao presa numa peca gasta');
// Cenario do revisor: o atual e "a", o jogador escolhe "c" (adiante na fila) e
// encerra. `animados_atual` NAO muda -- continua "a" --, entao um espelho que so
// reage a mudanca de atual deixaria a selecao em "c", que ja foi. O botao
// passaria a levar recusa e o joystick agiria com a peca errada.
function estadoDone({ atual, ordem, animados, done = [] }) {
  GS.injectPreviewState({
    type: 'game_state', master_pid: 'm',
    tiles: [[1]], explored: [], monsters: [], chests: [],
    players: [{ id:'m', name:'Pedro', alive:true, pos:[0,0], animados }],
    prisoner: null, animados_turn: 'm',
    animados_order: ordem, animados_atual: { m: atual }, animados_done: done,
  });
}
estadoDone({ atual:'a', ordem:['a','b','c'], animados:[A,B,C], done:['c'] });
check('"c" ja encerrou, mesmo estando ADIANTE do atual',
      GS.animadoJaEncerrou('c') === true);
check('encerrar com "c" selecionado cai no atual',
      GS.animadoPendenteParaEncerrar('c') === 'a');
check('a selecao em "c" e reconhecida como obsoleta',
      GS.animadoSelecaoValida('c') === false);
check('a selecao em "b" continua valida', GS.animadoSelecaoValida('b') === true);
check('"a" (o atual) continua valido', GS.animadoSelecaoValida('a') === true);

console.log('\n[10] animadoSelecaoValida — bordas');
estadoDone({ atual:'a', ordem:['a','b'], animados:[A,B], done:[] });
check('null nunca e selecao valida', GS.animadoSelecaoValida(null) === false);
check('id inexistente nao e valido', GS.animadoSelecaoValida('zzz') === false);
const mortoD = servo('md', { vida_atual: 0 });
estadoDone({ atual:'a', ordem:['a','md'], animados:[A, mortoD], done:[] });
check('servo morto nao e selecao valida', GS.animadoSelecaoValida('md') === false);

console.log('\n' + '='.repeat(46));
console.log('  ' + PASS + ' passaram, ' + FAIL + ' falharam');
console.log('='.repeat(46));
process.exit(FAIL ? 1 : 0);
