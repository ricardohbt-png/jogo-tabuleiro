// Editor de masmorras: "foge ao ser derrotado" (fuga_chefe) conserva-se no roundtrip e tem painel.
// Roda da raiz: node tools/test_fuga_chefe_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (...p) => fs.readFileSync(path.join(__dirname, ...p), 'utf8').split('\r').join('');
const ed = ler('editor.js'), lang = ler('..', 'src', 'lang', 'editor.js');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }
check('buildJSON grava fuga_chefe do monstro', /if \(m\.fuga_chefe[^\n]*\n?[^\n]*o\.fuga_chefe/.test(ed));
check('loadJSON conserva fuga_chefe', /\.\.\.\(m\.fuga_chefe[^\n]*\{ fuga_chefe:/.test(ed));
check('painel do monstro tem fato e texto', /id="p-fuga-fato"/.test(ed) && /id="p-fuga-texto"/.test(ed));
for (const k of ['titulo', 'fato', 'texto']) {
  const key = 'ui.editor.masmorra.fuga.' + k;
  const i = lang.indexOf('"' + key + '": {');
  const b = i < 0 ? '' : lang.slice(i, lang.indexOf('\n  }', i));
  check(key + ' tem pt e en', /"pt":/.test(b) && /"en":/.test(b));
}
console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
