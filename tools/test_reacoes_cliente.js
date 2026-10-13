// Reações elementais, lado do cliente: custo de movimento dos materiais novos
// (piche = 2 como lava/areia; lava_solidificada = chão normal) e paleta 2D.
// Roda da raiz: node tools/test_reacoes_cliente.js
'use strict';
const fs = require('fs');
const path = require('path');

const STATE = fs.readFileSync(path.join(__dirname, '..', 'src', 'gameState.js'), 'utf8');
const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
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

// Corredor de uma linha (y=5), x 0..13; material 'mat' de x=2 em diante.
function alcance(mat, mov){
  const code = ['terrainMoveCost', '_custoVentoTempestade', 'bfsReachable', 'findPath', '_entraNaNeve', '_neveJaCobrada', '_ignoraPenalidadePantano']
    .map(n => { try { return fnSource(n); } catch(e){ return ''; } }).join('\n');
  const materiais = {}; for(let x = 2; x < 14; x++) materiais[`${x},5`] = mat;
  const ctx = {
    _custoElevacao: () => 0, _ponteEm: () => false, alturaDe: a => Number(a && a.altura) || 0,
    _walkable: (tiles, x, y) => y === 5 && x >= 0 && x < 14, _occupiedSet: () => new Set(),
    doorSets: () => ({ open: new Set() }), gameState: { materiais, zonas_especiais: [] },
  };
  const keys = Object.keys(ctx);
  const api = new Function(...keys, code + '\nreturn {bfs:bfsReachable};')(...keys.map(k => ctx[k]));
  const explored = new Set(); for(let x = 0; x < 14; x++) explored.add(`${x},5`);
  const out = new Set();
  api.bfs([], explored, 1, 5, mov, out, { materiais, actor: {}, state: ctx.gameState });
  return out;
}

console.log('\n[1] Piche custa 2 por casa (4 de movimento = 2 casas)');
{
  const out = alcance('piche', 4);
  check('(3,5) alcançável — 2ª casa de piche', out.has('3,5'));
  check('(4,5) NÃO alcançável — 3ª casa', !out.has('4,5'));
}
console.log('\n[2] Chão normal e lava solidificada custam 1 (4 casas)');
{
  const chao = alcance('pedra_cinza', 4);
  check('chão normal: (5,5) alcançável', chao.has('5,5') && !chao.has('6,5'));
  const crosta = alcance('lava_solidificada', 4);
  check('lava_solidificada: (5,5) alcançável', crosta.has('5,5') && !crosta.has('6,5'));
}
console.log('\n[3] Paleta 2D do game.js');
check('piche em MAT_PALETTE_2D', /MAT_PALETTE_2D\s*=\s*\{[\s\S]*?\bpiche:\s*\{/.test(GAME));
check('lava_solidificada em MAT_PALETTE_2D', /MAT_PALETTE_2D\s*=\s*\{[\s\S]*?\blava_solidificada:\s*\{/.test(GAME));

console.log('\n' + '='.repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log('='.repeat(62));
process.exit(FAIL ? 1 : 0);
