// O editor não pode apagar `sem_fato` ao salvar destino, conversa ou slide.
const fs = require('fs'), path = require('path');
const raiz = path.join(__dirname, '..');
let falhas = 0;
function ok(c, m) { if (!c) { falhas++; console.log('FALHOU:', m); } }
const w = fs.readFileSync(path.join(raiz, 'tools/editor_world.js'), 'utf8');
const c = fs.readFileSync(path.join(raiz, 'tools/editor_city.js'), 'utf8');
const s = fs.readFileSync(path.join(raiz, 'tools/editor_story.js'), 'utf8');
ok((w.match(/sem_fato/g) || []).length >= 5, 'editor_world.js trata sem_fato (padrão, serialização, formulário)');
ok(/data-conv-req="sem_fato"/.test(c), 'editor_city.js edita sem_fato na conversa');
ok(/sem_fato/.test(s), 'editor_story.js conserva sem_fato');
console.log(falhas ? falhas + ' falha(s)' : 'ok');
process.exit(falhas ? 1 : 0);
