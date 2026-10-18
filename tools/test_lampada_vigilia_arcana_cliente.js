// Gating de monstros revelados pela Lâmpada da Vigília Arcana.
'use strict';
const fs = require('fs');
const path = require('path');
const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let pass = 0, fail = 0;
function check(label, ok) {
  if (ok) { pass++; console.log('  ✅ ' + label); }
  else { fail++; console.log('  ❌ ' + label); }
}

const start = game.indexOf('function _monstroOcultadoParaJogador(');
const end = game.indexOf('\n}', start);
let ocultado = null;
const GS = { isMaster: () => false };
if (start >= 0 && end > start) {
  ocultado = new Function('GS', `${game.slice(start, end + 2)}; return _monstroOcultadoParaJogador;`)(GS);
}
check('há uma regra pura para ocultação do monstro no cliente', typeof ocultado === 'function');
if (ocultado) {
  check('sem lâmpada, um monstro nas sombras segue oculto',
    ocultado({ invisivel_sombras: true, revealed_by_arcane_vigilance: false }));
  check('a lâmpada permite ver e selecionar o monstro sem remover seu estado',
    !ocultado({ invisivel_sombras: true, revealed_by_arcane_vigilance: true }));
  check('o mestre conserva a visualização normal',
    (GS.isMaster = () => true, !ocultado({ invisivel_sombras: true })));
  GS.isMaster = () => false;
}

check('ataque por clique e gamepad respeita a revelação',
  game.includes('_monstroOcultadoParaJogador(target)')
    && game.includes('!_monstroOcultadoParaJogador(monster)'));
check('realce de ataque e renderização 2D/3D respeitam a revelação',
  (game.match(/_monstroOcultadoParaJogador\(m\)/g) || []).length >= 7);
check('a lâmpada não altera nem substitui o estado invisível do monstro',
  game.includes('revealed_by_arcane_vigilance')
    && game.includes('monstro?.invisivel_sombras'));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
