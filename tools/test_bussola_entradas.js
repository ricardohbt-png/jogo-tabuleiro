// Bússola de direção: rotação pela roda do mouse e mapeamento do controle.
// Roda da raiz: node tools/test_bussola_entradas.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

global.WebSocket = class { constructor() {} send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

console.log("\n[1] GS.girarDirecao: anel N → L → S → O (sentido horário no mapa)");
const j = a => JSON.stringify(a);
check("passo +1 gira no sentido horário", j(GS.girarDirecao([0, -1], 1)) === "[1,0]"
  && j(GS.girarDirecao([1, 0], 1)) === "[0,1]" && j(GS.girarDirecao([0, 1], 1)) === "[-1,0]"
  && j(GS.girarDirecao([-1, 0], 1)) === "[0,-1]");
check("passo -1 gira no anti-horário", j(GS.girarDirecao([0, -1], -1)) === "[-1,0]"
  && j(GS.girarDirecao([-1, 0], -1)) === "[0,1]");
check("quatro passos voltam ao início", j([1, 2, 3, 4].reduce(f => GS.girarDirecao(f, 1), [0, 1])) === "[0,1]");
check("passos grandes dão a volta", j(GS.girarDirecao([0, -1], 5)) === "[1,0]" && j(GS.girarDirecao([0, -1], -5)) === "[-1,0]");
check("direção inválida cai no sul antes de girar", j(GS.girarDirecao([1, 1], 1)) === "[-1,0]"
  && j(GS.girarDirecao(null, 1)) === "[-1,0]");
check("passo 0 mantém", j(GS.girarDirecao([1, 0], 0)) === "[1,0]");

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
