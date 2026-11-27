// Barrinha de ações acima da ficha do servo da vez (Encerrar servo + Habilidades).
// Roda da raiz: node tools/test_servo_barra_acoes.js
'use strict';
const U = require('./js_teste_util');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

const GAME = U.ler('game.js');

console.log('\n[1] Rótulo do Encerrar: o MESMO do botão do painel lateral');
const rot = (state, refem) => U.executar(GAME, ['_rotuloEncerrarServo'], {
  GS: { myPid: 'p', ehRefemId: id => !!refem && id === refem },
  t: (k, p) => k + (p ? JSON.stringify(p) : ''),
  _refensGuiadosNaFila: () => (refem ? 1 : 0),
}).api._rotuloEncerrarServo(state);
const base = { animados_turn: 'p', animados_order: ['a', 'b', 'c'] };
check('servo da vez: posição e total', rot({ ...base, animados_atual: { p: 'b' } }) === 'ui.hud.encerrar_servo{"pos":2,"total":3}');
check('refém da vez: Encerrar prisioneiro', rot({ ...base, animados_atual: { p: 'refem_1' } }, 'refem_1') === 'ui.hud.encerrar_prisioneiro');
check('fora da vez dos servos: nada', rot({ animados_turn: null, animados_atual: {} }) === null);
check('o botão do painel lateral usa a mesma função',
  U.chamadas(U.funcao(GAME, '_atualizarBotaoEncerrarTurno')).includes('_rotuloEncerrarServo'));

console.log('\n[2] A barrinha na ficha do servo da vez');
const fichas = U.funcao(GAME, '_renderServosFichas');
check('o desenho das fichas monta a barrinha', U.chamadas(fichas).includes('_servoBarraAcoes'));
const barra = U.funcao(GAME, '_servoBarraAcoes');
check('o Encerrar usa o rótulo comum e aciona o botão do painel (mesma ação)',
  U.chamadas(barra).includes('_rotuloEncerrarServo') && /btn-end-turn/.test(barra) && /\.click\(\)/.test(barra));
check('Habilidades só para Senhor da Morte e elementais (a mesma regra do painel)',
  /senhor_da_morte/.test(barra) && /tipo_elemental/.test(barra));
check('os dois botões usam o estilo da barra do Pedro e o controle', /tam-tab/.test(barra) && /gamepadAction/.test(barra));
const pop = U.funcao(GAME, '_servoHabilidadesAbrir');
check('a lista de habilidades vem da mesma função do painel', U.chamadas(pop).includes('_animadoManualAbilityList'));
check('escolher uma habilidade usa o mesmo caminho do painel', U.chamadas(pop).includes('selecionarHabilidadeAnimado'));

console.log('\n[3] Estilo e textos');
const fs = require('fs');
const path = require('path');
const css = fs.readFileSync(path.join(__dirname, '..', 'game.css'), 'utf8');
check('barrinha e lista com estilo próprio', /\.servo-barra\b/.test(css) && /#servos-hab-pop\b/.test(css));
// A camada do painel do herói ignora cliques (pointer-events: none): sem ligar de volta,
// o clique na lista atravessava para o tabuleiro (achado na prova no navegador).
check('a lista de habilidades recebe cliques', /#servos-hab-pop\s*\{[^}]*pointer-events:\s*auto/.test(css));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
