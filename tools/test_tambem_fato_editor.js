// Editores: "Também o fato" (tambem_fato) e os fatos extras do objetivo nunca se perdem no roundtrip.
// Roda da raiz: node tools/test_tambem_fato_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (n) => fs.readFileSync(path.join(__dirname, n), 'utf8').split('\r').join('');
const world = ler('editor_world.js'), city = ler('editor_city.js'), story = ler('editor_story.js'), ed = ler('editor.js');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }

console.log('\n[1] Destino (mapa-múndi)');
check('a etapa tem o campo', /data-req-key="tambem_fato"/.test(world));
check('o save da etapa conserva tambem_fato', /tambem_fato:\s*req\.tambem_fato/.test(world));
check('o destino tem o campo e o sync o conserva', /id="we-req-also"/.test(world) && /tambem_fato:\$\('#we-req-also',host\)\.value/.test(world));
check('o sync do destino não apaga o herói', /heroi_no_grupo:\(a\.requisito&&a\.requisito\.heroi_no_grupo\)/.test(world));
check('tambem_fato sozinho conta como requisito (ocultar até liberar)', /\(req\.tambem_fato\|\|''\)\.trim\(\)/.test(world));

console.log('\n[2] Conversa de cena');
check('a conversa tem o campo', /data-conv-req="tambem_fato"/.test(city));

console.log('\n[3] Slides');
check('condição de slide reconhece tambem_fato', /"tambem_fato"\]\.some/.test(story));

console.log('\n[4] Objetivo na masmorra');
check('objExtras conserva fatos', /x\.fatos\s*=\s*f/.test(ed));
check('o painel edita fatos', /\$\{pfx\}-fatos/.test(ed));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
