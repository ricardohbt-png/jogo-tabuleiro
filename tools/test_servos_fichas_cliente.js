// Fichas dos servos junto ao painel do herói — lógica pura (gameState.js) e desenho (game.js).
// Roda da raiz: node tools/test_servos_fichas_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

global.WebSocket = class { constructor() { this.readyState = 1; } send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: '', protocol: 'http:', host: 'x' };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8') + '; GS');

const servo = (id, extra = {}) => Object.assign({ id, nome: id, tipo: 'skeleton', vida_atual: 5, vida_max: 8, ca: 12,
  movimento: 3, moves_left: 3, acted: false, nivel: 2, dano: '1d4', attacks: [] }, extra);
function estado(extra = {}) {
  return Object.assign({
    players: [{ id: 'p', class_id: 'mage', animados: [servo('a'), servo('b'), servo('c', { vida_atual: 0 }), servo('d', { dominado_por_monstro: true })] }],
    servos_ordem: { p: ['b', 'a'] },
    prisoners: [{ id: 'refem_1', nome: 'Tomé', freed: true, alive: true, rescuer_pid: 'p', modo: 'guiar', hp: 7, max_hp: 7, ac: 10, move: 6, moves_left: 0 },
                { id: 'refem_2', nome: 'Ana', freed: true, alive: true, rescuer_pid: 'p', modo: 'seguir', hp: 7, max_hp: 7, ac: 10 },
                { id: 'refem_3', nome: 'Zé', freed: true, alive: true, rescuer_pid: 'outro', modo: 'guiar', hp: 7, max_hp: 7, ac: 10 }],
    animados_turn: null, animados_atual: {}, animados_done: [],
  }, extra);
}

console.log('\n[1] fichasDosServos: quem aparece e em que ordem');
let f = GS.fichasDosServos(estado(), 'p');
check('ordem do servidor (servos_ordem), depois o refém guiado', f.map(x => x.id).join(',') === 'b,a,refem_1');
check('morto, roubado, refém em Seguir e refém de outro herói ficam de fora', !f.some(x => ['c', 'd', 'refem_2', 'refem_3'].includes(x.id)));
check('refém marcado como refém', f[2].kind === 'refem' && f[0].kind === 'servo');
check('na vez do herói ninguém está "na vez" nem "feito"', f.every(x => !x.atual && !x.feito));
check('herói sem servos nem reféns: lista vazia', GS.fichasDosServos(estado({ players: [{ id: 'p', animados: [] }], prisoners: [] }), 'p').length === 0);
check('sem servos_ordem (estado antigo): usa a ordem da lista', GS.fichasDosServos(estado({ servos_ordem: undefined }), 'p').map(x => x.id).join(',') === 'a,b,refem_1');

console.log('\n[2] Na vez dos servos: o da vez e os que já agiram');
f = GS.fichasDosServos(estado({ animados_turn: 'p', animados_atual: { p: 'a' }, animados_done: ['b'] }), 'p');
check('o servo da vez é marcado', f.find(x => x.id === 'a').atual === true && f.filter(x => x.atual).length === 1);
check('quem já agiu fica no lugar, marcado como feito', f.map(x => x.id).join(',') === 'b,a,refem_1' && f[0].feito === true);
check('na vez de OUTRO herói, nada marca "na vez"', GS.fichasDosServos(estado({ animados_turn: 'outro', animados_atual: { p: 'a' } }), 'p').every(x => !x.atual));

console.log('\n[3] ataquesDoServo: o que o servidor deixa usar');
const atks = [{ name: 'Mordida', atk_bonus: 4, damage: '1d8+2', num_attacks: 1 }, { name: 'Garras', atk_bonus: 3, damage: '1d6+2', num_attacks: 2 }];
let a = GS.ataquesDoServo(servo('x', { attacks: atks }));
check('Animar Mortos básico: só o primeiro ataque, um golpe', a.length === 1 && a[0].nome === 'Mordida' && a[0].bonus === 4 && a[0].dano === '1d8+2' && a[0].vezes === 1);
a = GS.ataquesDoServo(servo('x', { attacks: [{ name: 'Golpe' }], nivel: 3, dano: '1d6' }));
check('básico sem bônus/dano no ataque: nível e dano do servo (como o servidor)', a[0].bonus === 3 && a[0].dano === '1d6');
a = GS.ataquesDoServo(servo('x', { attacks: [] }));
check('básico sem ataque nenhum: golpe genérico com nível e dano do servo', a.length === 1 && a[0].bonus === 2 && a[0].dano === '1d4');
a = GS.ataquesDoServo(servo('x', { attacks: atks, senhor_da_morte: true }));
check('Senhor da Morte: todos os ataques, com o número de golpes', a.length === 2 && a[1].nome === 'Garras' && a[1].vezes === 2);
a = GS.ataquesDoServo(servo('x', { tipo: 'elemental', tipo_elemental: 'fogo', attacks: atks }));
check('elemental: todos os ataques', a.length === 2);
check('refém não ataca', GS.ataquesDoServo({ id: 'refem_1', hp: 7 }, 'refem').length === 0);

console.log('\n[4] Desenho (game.js)');
const GAME = U.ler('game.js');
const render = U.funcao(GAME, 'renderTurnHeroHud');
// Uma chamada só, ANTES de qualquer saída antecipada do painel: vale na vez do herói e
// na vez dos servos (quando o painel mostra "Vez de Pedro" e retorna cedo).
const corpoRender = render.slice(render.indexOf('{') + 1);
check('o painel do herói desenha as fichas antes de qualquer saída (vale nas duas situações)',
  U.chamadas(corpoRender)[0] === '_renderServosFichas' && corpoRender.indexOf('_renderServosFichas(') < corpoRender.indexOf('return'));
const fichas = U.funcao(GAME, '_renderServosFichas');
check('usa a lógica pura do GS', U.chamadas(fichas).includes('GS.fichasDosServos'));
check('clique centraliza a câmera no servo', /centralizarCamera3DNoPeao|_scrollMapToTile/.test(fichas + U.funcao(GAME, '_centrarServoFicha')));
const css = fs.readFileSync(path.join(__dirname, '..', 'game.css'), 'utf8');
check('estilos: ficha pequena, grande e feita', /\.servo-ficha\b/.test(css) && /\.servo-ficha\.is-atual/.test(css) && /\.servo-ficha\.is-feito/.test(css));
const lang = fs.readFileSync(path.join(__dirname, '..', 'src', 'lang', 'interface.js'), 'utf8');
for (const k of ['titulo', 'ca', 'mov', 'acao_livre', 'acao_usada', 'so_move', 'na_vez'])
  check('chave ui.servos.' + k + ' com pt e en', new RegExp('"ui\\.servos\\.' + k + '":\\s*\\{[^}]*"en":[^}]*"pt":').test(lang));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
