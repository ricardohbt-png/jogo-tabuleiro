// Editores: o campo "Herói no grupo" (heroi_no_grupo) é editado e nunca se perde no roundtrip.
// Roda da raiz: node tools/test_requisito_heroi_editor.js
'use strict';
const fs = require('fs'), path = require('path');
const ler = (n) => fs.readFileSync(path.join(__dirname, n), 'utf8').split('\r').join('');
const world = ler('editor_world.js'), city = ler('editor_city.js'), story = ler('editor_story.js'), ed = ler('editor.js');
let pass = 0, fail = 0;
function check(l, ok) { if (ok) { pass++; console.log('  ✅ ' + l); } else { fail++; console.log('  ❌ ' + l); } }

console.log('\n[1] Destino (mapa-múndi)');
check('o formulário da etapa tem o select de herói', /data-req-key="heroi_no_grupo"/.test(world));
check('o save do destino conserva heroi_no_grupo', /heroi_no_grupo:\s*req\.heroi_no_grupo/.test(world));
check('heroi sozinho já conta como requisito preenchido (ocultar até liberar)', /String\(req\.heroi_no_grupo\|\|''\)\.trim\(\)/.test(world) && /\(req\.heroi_no_grupo\|\|''\)\.trim\(\)/.test(world));

console.log('\n[2] Conversa de cena');
check('a conversa tem o select de herói', /data-conv-req="heroi_no_grupo"/.test(city));

console.log('\n[3] Slides de história');
check('condição de slide reconhece heroi_no_grupo e não o apaga', /heroi_no_grupo/.test(story));

console.log('\n[4] Falas da masmorra');
check('buildJSON conserva o requisito da fala', /if \(f\.requisito[^\n]*out\.requisito/.test(ed));
check('loadJSON conserva o requisito da fala', /requisito:\s*f\.requisito \? JSON\.parse\(JSON\.stringify\(f\.requisito\)\) : null/.test(ed));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
