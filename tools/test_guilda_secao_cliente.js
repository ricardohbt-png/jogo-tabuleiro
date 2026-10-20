// Guilda — seção e faixa de recarga zero das passivas Disparo Duplo/Arremesso Rápido.
// Roda da raiz: node tools/test_guilda_secao_cliente.js
'use strict';
const fs = require('fs'), path = require('path');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
const lang = fs.readFileSync(path.join(__dirname, '..', 'src', 'lang', 'interface.js'), 'utf8');
let pass = 0, fail = 0;
function check(label, ok) { if (ok) { pass++; console.log('  ✅ ' + label); } else { fail++; console.log('  ❌ ' + label); } }
function body(name) {
  const start = source.indexOf(`function ${name}(`);
  if (start < 0) return '';
  const brace = source.indexOf('{', start);
  let depth = 0;
  for (let i = brace; i < source.length; i++) {
    if (source[i] === '{') depth++;
    if (source[i] === '}' && --depth === 0) return source.slice(brace + 1, i);
  }
  return '';
}
const g = body('_renderGuild');

console.log('\n[1] _renderGuild usa a seção declarada pelo catálogo');
check('Técnicas incluem o que o catálogo manda para a seção técnica',
  /tecs\s*=\s*catalog\.filter\([^)]*secao\s*===\s*'tecnica'/.test(g));
check('Especializações não repetem o que foi para Técnicas',
  /specs\s*=\s*catalog\.filter\([^)]*secao\s*!==\s*'tecnica'/.test(g));
check('a faixa de recarga zero tem título próprio', /0\s*:\s*t\('ui\.guilda\.recarga_zero'\)/.test(g));

console.log('\n[2] Linha do item continua de especialização (compra, sem equipar)');
const linha = body('_guildItemRow');
check('o possuído/compra segue pela categoria, não pela seção',
  linha.includes("i.categoria === 'tecnica' ? (owned.tecnicas") && !linha.includes('secao'));

console.log('\n[3] Texto PT/EN');
const bloco = lang.match(/"ui\.guilda\.recarga_zero": \{([\s\S]*?)\n  \}/);
check('ui.guilda.recarga_zero tem pt e en', !!bloco && /"pt":/.test(bloco[1]) && /"en":/.test(bloco[1]));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
