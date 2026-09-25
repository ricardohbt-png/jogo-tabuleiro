// Emoji/glifo do tabuleiro 2D não pode herdar o alfa do preenchimento de fundo.
// O Chrome aplica o alfa do fillStyle também ao glifo colorido: com o realce
// das decorações (0,12) em vigor, fonte/fogueira/barril/árvore/altar saíam a
// 31/255 de opacidade (medido). Roda da raiz: node tools/test_glifo_opaco_2d.js
'use strict';
const fs = require('fs');
const path = require('path');
const GAME = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8').replace(/\r\n/g, '\n');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if(c){ PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

console.log('\n[1] Decoração sem PNG: o emoji sai opaco');
check('caminho do emoji em escala 1',
  /ctx\.fillStyle = '#fff';\s*\n\s*ctx\.font = `\$\{Math\.floor\(CELL \* 0\.8\)\}px serif`;\s*\n\s*ctx\.fillText\(d\.emoji/.test(GAME));
check('caminho do emoji escalado',
  /\} else \{\s*\n\s*ctx\.fillStyle = '#fff';\s*\n\s*\/\/ emoji escalado/.test(GAME));

console.log('\n[2] Armadilhas: glifo opaco sobre o fundo translúcido');
check("armadilha de sala: '⚠' opaco", /ctx\.fillStyle='#ff5a4a';[^\n]*\n\s*ctx\.fillText\('⚠'/.test(GAME));
check('armadilha colocável: ícone opaco', /ctx\.fillStyle='#fff';[^\n]*\n\s*ctx\.fillText\(arm\.icone/.test(GAME));

console.log(`\n${'='.repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${'='.repeat(50)}`);
process.exit(FAIL ? 1 : 0);
