const fs = require('fs');
const vm = require('vm');
const path = require('path');
const game = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
let passed = 0, failed = 0;
function check(name, ok) {
  if (ok) { passed++; console.log(`  ✅ ${name}`); }
  else { failed++; console.error(`  ❌ ${name}`); }
}
const match = game.match(/function _solucaoMecanismoAreaTiles\([\s\S]*?\n\}/);
check('define cálculo puro do raio de efeito', !!match);
if (match) {
  const area = new Function(`${match[0]}; return _solucaoMecanismoAreaTiles([5,5], 12, 12);`)();
  const keys = new Set(area.map(([x,y]) => `${x},${y}`));
  check('área centrada no herói inclui 49 casas no raio Chebyshev 3', area.length === 49 && keys.has('2,2') && keys.has('8,8') && !keys.has('9,5'));
  const clipped = new Function(`${match[0]}; return _solucaoMecanismoAreaTiles([0,0], 12, 12);`)();
  check('área é limitada ao tabuleiro perto das bordas', clipped.length === 16 && clipped.every(([x,y]) => x >= 0 && y >= 0));
}
check('selecionar o item abre prévia sem enviar o uso ao servidor',
  /it\?\.effect\s*===?\s*['"]disarm_traps_area['"]/.test(game)
  && /_iniciarPreviewSolucaoMecanismo\(itemId, sourceInfo\)/.test(game));
check('confirmação envia o item e cancelamento limpa a prévia',
  /GS\.useItem\(preview\.itemId, preview\.sourceInfo\)/.test(game)
  && /_cancelarPreviewSolucaoMecanismo/.test(game));
check('área aparece nos renderizadores 2D e 3D',
  /_desenharSolucaoMecanismoPreview2D\(ctx, state\)/.test(game)
  && /_syncSolucaoMecanismoPreview3D\(state\)/.test(game));
if (failed) process.exitCode = 1;
console.log(`\n=== ${passed} passaram, ${failed} falharam ===`);
