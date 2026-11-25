// Mercador (cliente): as abas vêm de GS.ABAS_MERCADOR, a venda é a última e uma aba sem itens
// avisa em vez de ficar em branco. Roda da raiz: node tools/test_mercador_abas_cliente.js
const fs = require('fs'), path = require('path');
const raiz = path.join(__dirname, '..');
const game = fs.readFileSync(path.join(raiz, 'game.js'), 'utf8');
const lang = fs.readFileSync(path.join(raiz, 'src', 'lang', 'interface.js'), 'utf8');
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log('  ✅ ' + n); } else { FAIL++; console.log('  ❌ ' + n); } };

check("as abas do Mercador vêm de GS.ABAS_MERCADOR", /shopId==='mercador'\s*\?\s*GS\.ABAS_MERCADOR/.test(game));
check("a aba de venda é achada pelo id, não por número", /activeShop==='mercador'&&GS\.ABAS_MERCADOR\[aba\]==='vender'/.test(game)
  && !/activeShop==='mercador'&&aba===\d/.test(game));
check("cada item é filtrado por GS.abaMercadorDoItem", /abaMercadorDoItem\(item\)===idAba/.test(game));
check("aba sem itens mostra o aviso (só no Mercador)", /!items\.length && GS\.activeShop==='mercador'[\s\S]{0,300}ui\.loja\.aba_vazia/.test(game));
const abas = ['elmos', 'aneis', 'botas', 'talismas_amuletos', 'mochila_carga', 'grimorios', 'outros_equipamentos', 'consumiveis',
  'instrumentos', 'arremessaveis', 'venenos', 'pergaminhos', 'vender'];
for (const a of abas) check(`rótulo PT/EN da aba ${a}`, new RegExp(String.raw`"ui\.loja\.aba\.${a}"\s*:\s*\{[^}]*"en"[^}]*"pt"`).test(lang));
check('mensagem de aba vazia em PT e EN', /"ui\.loja\.aba_vazia"\s*:\s*\{[^}]*"en"[^}]*"pt"/.test(lang));
console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
