// Raízes do Brejo — título próprio da loja no cliente (análise estática do game.js).
// Roda da raiz: node tools/test_zumbra_titulo_cliente.js
'use strict';
const fs = require('fs'), path = require('path');
const source = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
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
const abrir = body('openShop');

console.log('\n[1] openShop usa o título próprio do ponto');
check('lê titulo_loja do ponto aberto', /titulo_loja/.test(abrir) && /cityPoints\(\)/.test(abrir));
check('o título próprio vence o rótulo do tipo (e cai nele quando não há)',
  /\$\('shop-title'\)\.textContent\s*=\s*tituloProprio\s*\|\|/.test(abrir));
check('o texto vai por textContent (nome autoral nunca vira HTML)',
  !/shop-title'\)\.innerHTML/.test(abrir));
check('as abas e a classe do Mercador continuam pelo tipo', abrir.includes("shopId==='mercador'")
  && abrir.includes("'comprar','instrumentos'"));

console.log(`\n=== ${pass} passaram, ${fail} falharam ===`);
process.exit(fail ? 1 : 0);
