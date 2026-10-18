// Marcadores temporários da Vela Reveladora no mapa 2D/3D.
'use strict';
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(root, 'game.js'), 'utf8');
let pass = 0, fail = 0;
function check(label, ok) {
  if (ok) { pass++; console.log('  ✅ ' + label); }
  else { fail++; console.log('  ❌ ' + label); }
}

const start = game.indexOf('function _velaTrapRevealPositions(');
const end = game.indexOf('\nfunction _desenharVelaTrapMarkers2D', start);
let positions = null;
if (start >= 0 && end > start) {
  positions = new Function(`${game.slice(start, end)}; return _velaTrapRevealPositions;`)();
}
check('há um seletor puro de posições reveladas temporariamente', typeof positions === 'function');
if (positions) {
  const result = positions({
    traps: [
      { pos: [2, 3], vela_revelada: true },
      { pos: [8, 8], vela_revelada: false },
    ],
    armadilhas: [
      { pos: [2, 3], vela_revelada: true },
      { pos: [4, 5], vela_revelada: true },
    ],
    decorations: [
      { pos: [4, 5], trap_revelada_vela: true },
      { pos: [9, 9], trap_revelada_vela: false },
    ],
  });
  const keys = new Set(result.map(([x, y]) => `${x},${y}`));
  check('reúne os três tipos de armadilha e remove posições duplicadas',
    result.length === 2 && keys.has('2,3') && keys.has('4,5'));
  check('ignora armadilhas sem revelação temporária', !keys.has('8,8') && !keys.has('9,9'));
}

const fog = game.indexOf("ctx.fillRect(x*CELL, y*CELL, CELL, CELL);");
const draw2d = game.indexOf('_desenharVelaTrapMarkers2D(ctx, state, exploredSet);');
check('o marcador 2D é desenhado depois da névoa', fog >= 0 && draw2d > fog);
check('o renderizador 3D sincroniza marcadores independentes dos objetos',
  game.includes('_syncVelaTrapMarkers3D(state, exploredSet);')
    && game.includes('trapRevealMarkers'));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
