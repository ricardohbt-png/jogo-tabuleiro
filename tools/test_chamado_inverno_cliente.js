// Testes do lado do cliente do Chamado do Inverno (src/gameState.js): o
// alcance de movimento na Planície Nevada precisa espelhar o servidor, que
// divide pela metade o movimento RESTANTE ao entrar na neve.
//
// Roda da raiz:
//     node tools/test_chamado_inverno_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const STATE = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
let PASS = 0, FAIL = 0;
function check(name, cond){ if(cond){ PASS++; console.log('  ✅ ' + name); } else { FAIL++; console.log('  ❌ ' + name); } }

function fnSource(name){
  const i = STATE.indexOf('function ' + name + '(');
  if(i < 0) throw new Error('função não encontrada: ' + name);
  let d = 0;
  for(let k = STATE.indexOf('{', i); k < STATE.length; k++){
    if(STATE[k] === '{') d++;
    else if(STATE[k] === '}'){ d--; if(!d) return STATE.slice(i, k + 1); }
  }
  throw new Error('chaves desbalanceadas em ' + name);
}

// Corredor 1 casa de altura (y=5), x de 0..13; neve de x=2 em diante.
function montar(){
  const code = ['terrainMoveCost', '_custoVentoTempestade', 'bfsReachable', 'findPath', '_entraNaNeve', '_neveJaCobrada']
    .map(n => { try { return fnSource(n); } catch(e){ return ''; } }).join('\n');
  const materiais = {}; for(let x = 2; x < 14; x++) materiais[`${x},5`] = 'planicie_nevada';
  const ctx = {
    _custoElevacao: () => 0, _ponteEm: () => false, alturaDe: a => Number(a && a.altura) || 0,
    _walkable: (tiles, x, y) => y === 5 && x >= 0 && x < 14, _occupiedSet: () => new Set(),
    doorSets: () => ({ open: new Set() }), gameState: { materiais, zonas_especiais: [] },
  };
  const keys = Object.keys(ctx);
  const api = new Function(...keys, code + '\nreturn {bfs:bfsReachable, path:findPath};')(...keys.map(k => ctx[k]));
  const explored = new Set(); for(let x = 0; x < 14; x++) explored.add(`${x},5`);
  return { api, explored, moveCtx: { materiais, actor: {}, state: ctx.gameState } };
}

console.log('\n[1] Alcance na neve: o servidor anda 3 casas com 6 de movimento (1 + metade de 5)');
{
  const { api, explored, moveCtx } = montar();
  const out = new Set();
  api.bfs([], explored, 1, 5, 6, out, moveCtx);
  check('(2,5) alcançável — 1ª casa de neve', out.has('2,5'));
  check('(4,5) alcançável — 3ª casa (restante 5 → 2 → 1 → 0)', out.has('4,5'));
  check('(5,5) NÃO alcançável — o cliente mostrava até (7,5)', !out.has('5,5'));
  const voo = new Set();
  api.bfs([], explored, 1, 5, 6, voo, { ...moveCtx, actor: { voo: true, altura: 2 } });
  check('voador ignora a neve: (7,5) alcançável', voo.has('7,5'));
}

console.log('\n[2] Sem neve nada muda; começando NA neve o orçamento já veio reduzido do servidor');
{
  const { api, explored } = montar();
  const semNeve = new Set();
  api.bfs([], explored, 1, 5, 6, semNeve, { materiais: {}, actor: {}, state: { zonas_especiais: [] } });
  check('sem neve: (7,5) alcançável', semNeve.has('7,5'));
  const { api: api2, explored: ex2, moveCtx } = montar();
  const naNeve = new Set();
  api2.bfs([], ex2, 3, 5, 3, naNeve, moveCtx);            // já sobre a neve, moves_left já é a metade
  check('começando na neve: não divide de novo (3 casas com 3)', naNeve.has('6,5') && !naNeve.has('7,5'));
}

console.log('\n[3] findPath respeita a mesma regra (é ele quem dirige a caminhada)');
{
  const { api, explored, moveCtx } = montar();
  const ok = api.path([], explored, 1, 5, 4, 5, 6, false, moveCtx);
  check('caminho até (4,5) existe com 3 passos', Array.isArray(ok) && ok.length === 3);
  const longe = api.path([], explored, 1, 5, 5, 5, 6, false, moveCtx);
  check('caminho até (5,5) NÃO existe (o servidor pararia com erro no meio)', longe === null);
  const parcial = api.path([], explored, 1, 5, 9, 5, 6, true, moveCtx);
  check('parcial: para em (4,5), a última casa possível', Array.isArray(parcial) && parcial.length === 3);
}

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
