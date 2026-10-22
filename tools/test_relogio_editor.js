// Editor de masmorras: relógio da campanha (relogio) e desconto na passagem secreta (relogio_desconto).
// Roda da raiz: node tools/test_relogio_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (...p) => fs.readFileSync(path.join(__dirname, ...p), 'utf8').split('\r').join('');
const ed = ler('editor.js'), lang = ler('..', 'src', 'lang', 'editor.js');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }

console.log('\n[1] Estado e roundtrip');
check('o estado inicial tem relogio nulo', /relogio:\s*null/.test(ed));
check('buildJSON só grava relogio com id preenchido', /S\.relogio && S\.relogio\.id[^\n]*relogio:/.test(ed));
check('loadJSON lê relogio normalizado', /S\.relogio\s*=\s*obj\.relogio/.test(ed));
check('a passagem secreta grava e lê relogio_desconto', /relogio_desconto:\s*p\.relogio_desconto/.test(ed) && /relogio_desconto:\s*Math\.max\(0/.test(ed));

console.log('\n[2] Painel');
check('há os campos do relógio no painel de nível', /id="rel-id"/.test(ed) && /id="rel-limite"/.test(ed) && /id="rel-fato"/.test(ed));
check('há a lista de avisos com adicionar/remover', /rel-aviso-add/.test(ed) && /rel-aviso-rm/.test(ed));
check('há o campo de desconto no painel da passagem', /id="sp-relogio"/.test(ed));

console.log('\n[3] Textos PT/EN');
for (const k of ['titulo', 'id', 'limite', 'fato', 'avisos', 'aviso_em', 'aviso_texto', 'adicionar_aviso', 'desconto']) {
  const key = 'ui.editor.masmorra.relogio.' + k;
  const i = lang.indexOf('"' + key + '": {');
  const b = i < 0 ? '' : lang.slice(i, lang.indexOf('\n  }', i));
  check(key + ' tem pt e en', /"pt":/.test(b) && /"en":/.test(b));
}
console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
