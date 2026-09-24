// tools/test_sfx_arquivos.js — catálogo × pasta assets/sfx/.
const fs = require('fs');
const path = require('path');
const raiz = path.join(__dirname, '..');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };
global.window = {};
eval(fs.readFileSync(path.join(raiz, 'src', 'soundBank.js'), 'utf8'));
const SB = global.window.SoundBank;
const base = path.join(raiz, 'assets', 'sfx');

const noCatalogo = new Set();
for (const def of Object.values(SB.SFX)) for (const a of def.arquivos) noCatalogo.add(a);
const naPasta = new Set();
(function varrer(dir, rel) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) varrer(path.join(dir, e.name), r); else naPasta.add(r);
  }
})(base, '');
naPasta.delete('LICENCAS.md');

const faltando = [...noCatalogo].filter(a => !naPasta.has(a));
const orfaos = [...naPasta].filter(a => !noCatalogo.has(a));
check('todo arquivo do catálogo existe: ' + (faltando.join(', ') || 'ok'), faltando.length === 0);
check('nenhum arquivo órfão na pasta: ' + (orfaos.join(', ') || 'ok'), orfaos.length === 0);
check('tudo é .ogg', [...naPasta].every(a => a.endsWith('.ogg')));
const licencas = fs.readFileSync(path.join(base, 'LICENCAS.md'), 'utf8');
const semLicenca = [...naPasta].filter(a => !licencas.includes(a));
check('todo arquivo está no LICENCAS.md: ' + (semLicenca.join(', ') || 'ok'), semLicenca.length === 0);
let efeitos = 0;
for (const a of naPasta) if (!a.startsWith('ambiente/')) efeitos += fs.statSync(path.join(base, a)).size;
check(`efeitos < 3 MB (${(efeitos / 1048576).toFixed(2)} MB)`, efeitos < 3 * 1048576);
for (const a of naPasta) if (a.startsWith('ambiente/'))
  check(`${a} < 2 MB`, fs.statSync(path.join(base, a)).size < 2 * 1048576);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
