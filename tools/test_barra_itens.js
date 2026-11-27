// Botão "🎒 Itens" na barra de ações. Roda da raiz: node tools/test_barra_itens.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
const ini = game.indexOf("function _renderBarraAcoes(state, hero){");
const corpo = game.slice(ini, game.indexOf("\nfunction _barraSincronizar(){", ini));

console.log("\n[1] Lugar e aparência");
check("o botão fica depois de Habilidades e antes de Desfazer",
  /data-menu="habilidades"[\s\S]{0,400}tam-itens[\s\S]{0,400}tam-desfazer/.test(corpo));
check("usa o mesmo estilo translúcido da barra (classe tam-tab)", /class="tam-tab tam-itens"/.test(corpo));
check("funciona com o controle", /tam-itens"[^>]*data-gamepad-action="activate"/.test(corpo));
check("rótulo e dica traduzidos", /t\('ui\.menuacoes\.itens'\)/.test(corpo) && /t\('ui\.menuacoes\.itens_dica'\)/.test(corpo));

console.log("\n[2] Clique abre (ou fecha) o inventário completo do herói em foco");
const m = corpo.match(/querySelector\('\.tam-itens'\)\.onclick = \(\) => \{([^}]*)\}/);
check("tem o clique", !!m);
check("fecha os menus da barra antes", !!m && /_barraFechar\(\)/.test(m[1]));
check("alterna o inventário do herói em foco", !!m && /InventoryModal\.toggle\(GS\.myPid\)/.test(m[1]));

console.log("\n[3] Textos");
const lang = fs.readFileSync(path.join(raiz, "src/lang/interface.js"), "utf8");
for (const k of ["itens", "itens_dica"]) {
  const l = lang.match(new RegExp('"ui\\.menuacoes\\.' + k + '":[^\\n]*'));
  check("chave ui.menuacoes." + k + " com pt e en", !!l && /"en":/.test(l[0]) && /"pt":/.test(l[0]));
}

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
