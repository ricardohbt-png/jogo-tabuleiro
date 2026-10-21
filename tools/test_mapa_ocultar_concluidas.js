// Mapa-múndi: botão que oculta os destinos já concluídos (preferência local).
// Roda da raiz: node tools/test_mapa_ocultar_concluidas.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (...p) => fs.readFileSync(path.join(__dirname, '..', ...p), 'utf8').split('\r').join('');
const js = ler('game.js'), css = ler('game.css'), lang = ler('src', 'lang', 'interface.js');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }

const i = js.indexOf('function showWorldMap(){');
const corpo = js.slice(i, js.indexOf('// ── Fase 4b (história)', i));
check('há o predicado _destinoConcluido (progresso ≥ nº de etapas)', /function _destinoConcluido\(/.test(js) && /progresso/.test(js.slice(js.indexOf('function _destinoConcluido('), js.indexOf('function _destinoConcluido(') + 300)));
check('a preferência vive no localStorage com try/catch', /lfh_mapa_ocultar_concluidas/.test(js) && /function _mapaOcultaConcluidas\(/.test(js));
check('o mapa filtra os marcadores de aventura concluída', /_mapaOcultaConcluidas\(\)\s*&&\s*_destinoConcluido\(/.test(corpo));
check('há o botão de alternar no mapa (classe worldmap-hide-done)', /worldmap-hide-done/.test(corpo) && /showWorldMap\(\)/.test(corpo));
check('o CSS posiciona o botão', /\.worldmap-hide-done/.test(css));
for (const k of ['ui.mundo.ocultar_concluidas', 'ui.mundo.mostrar_concluidas']) {
  const a = lang.indexOf('"' + k + '": {');
  const b = a < 0 ? '' : lang.slice(a, lang.indexOf('\n  }', a));
  check(k + ' tem pt e en', /"pt":/.test(b) && /"en":/.test(b));
}
console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
