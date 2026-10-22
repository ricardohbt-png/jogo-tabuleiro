// Editor de cidades: a conversa edita e conserva `efeito.fatos` (lista separada por vírgula).
// Roda da raiz: node tools/test_conversa_fatos_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const city = fs.readFileSync(path.join(__dirname, 'editor_city.js'), 'utf8').split('\r').join('');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }
check('o formulário tem o campo de fatos adicionais', /data-conv-effect="fatos"/.test(city));
check('o campo mostra a lista atual separada por vírgula', /\(effect\.fatos\|\|\[\]\)\.join\(', '\)/.test(city));
check('ao editar, a lista é gravada como array limpo', /convEffect==='fatos'\?/.test(city) && /split\(','\)/.test(city));
console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
