// Prévia de quem a área atinge: lógica pura (GS.atingidosNaArea) e fiação no game.js.
// Roda da raiz: node tools/test_previa_area_atingidos_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

global.WebSocket = class { constructor() {} send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");

const estado = () => ({
  players: [
    { id: "eu", name: "Pedro", alive: true, pos: [5, 5],
      animados: [{ id: "s1", nome: "Esqueleto", vida_atual: 5, pos: [6, 6] }] },
    { id: "b", name: "Bia", alive: true, pos: [6, 5] },
    { id: "morto", name: "Zé", alive: false, pos: [5, 6] },
    { id: "fora", name: "Ana", alive: true, pos: [-1, -1] },
  ],
  monsters: [
    { id: "m1", name: "Goblin", hp: 4, pos: [7, 5] },
    { id: "m2", name: "Ogro", hp: 9, pos: [8, 8], size: [2, 2] },
    { id: "m3", name: "Rato", hp: 0, pos: [6, 4] },
    { id: "m4", name: "Assassino", hp: 3, pos: [5, 4], invisivel_sombras: true },
  ],
  prisoners: [{ id: "refem_1", nome: "Tico", pos: [4, 5], freed: true }],
});
const area = new Set(["4,5", "5,5", "6,5", "7,5", "5,6", "6,6", "6,4", "5,4", "9,9"]);

console.log("\n[1] Efeito que atinge todos");
let r = GS.atingidosNaArea(estado(), area, "bola_fogo", "eu");
check("inimigos: só os vivos e visíveis dentro da área (Goblin e Ogro pelo footprint)",
  JSON.stringify(r.inimigos.map(x => x.id).sort()) === JSON.stringify(["m1", "m2"]));
check("aliados atingidos: Pedro, Bia, servo e refém liberto",
  JSON.stringify(r.aliados.map(x => x.id).sort()) === JSON.stringify(["b", "eu", "refem_1", "s1"]));
check("morto e quem está fora da masmorra não contam", !r.aliados.some(x => x.id === "morto" || x.id === "fora"));
check("nenhum beneficiado", r.beneficiados.length === 0);
check("o Ogro 2x2 traz as casas do footprint", r.inimigos.find(x => x.id === "m2").tiles.length === 4);

console.log("\n[2] Efeito que só beneficia aliados");
r = GS.atingidosNaArea(estado(), area, "abencoar", "eu");
check("Abençoar: aliados viram beneficiados e inimigos não aparecem",
  r.beneficiados.length === 4 && r.aliados.length === 0 && r.inimigos.length === 0);

console.log("\n[3] Efeito sem regra e visibilidade");
r = GS.atingidosNaArea(estado(), area, "silencio", "eu");
check("efeito fora da tabela: nada", r.inimigos.length + r.aliados.length + r.beneficiados.length === 0);
r = GS.atingidosNaArea(estado(), area, "granada", "eu", (x, y) => !(x === 7 && y === 5));
check("monstro numa casa que não enxergo não aparece", !r.inimigos.some(x => x.id === "m1"));
r = GS.atingidosNaArea(estado(), [["5,5"]].flat(), "granada", "eu");
check("aceita lista de casas além de Set", r.aliados.length === 1 && r.aliados[0].id === "eu");

console.log("\n[4] Fiação no game.js");
check("a mira de magia e a de arremesso calculam os atingidos",
  /_recomputarAreaMagia[\s\S]*?_atingidosPrever\(area\)/.test(game) && /_recomputarAreaThrow[\s\S]*?_atingidosPrever\(area\)/.test(game));
check("o resumo entra na linha da mira", /_atingidosSufixo\(/.test(game));
check("2D desenha os anéis dos atingidos", /function _desenharAtingidos2D/.test(game) && /_desenharAtingidos2D\(ctx/.test(game));
check("3D tem pool próprio dos atingidos", /spellAtingidoMeshes/.test(game));
check("lançar com aliado atingido pede um segundo clique (magia e arremesso)",
  (game.match(/_confirmaAtingirAliado\(/g) || []).length >= 3);

console.log("\n[5] Segundo clique");
const fonte = (n) => { const i = game.indexOf(`function ${n}(`); let k = game.indexOf("{", i), d = 0;
  for (; k < game.length; k++) { if (game[k] === "{") d++; else if (game[k] === "}") { d--; if (!d) break; } } return game.slice(i, k + 1); };
const avisos = [];
const ctx = new Function("window", "t", "_aimSetStatus", "toast",
  "let _confirmaAliadoChave = null;\n" + fonte("_confirmaAtingirAliado") + "\nreturn _confirmaAtingirAliado;");
const conf = ctx({ _spellHL: { atingidos: { aliados: [{ nome: "Bia" }] }, area: new Set(["1,1", "2,2"]) } },
  (k, p) => k + (p ? JSON.stringify(p) : ""), (m) => avisos.push(m), () => {});
check("1º clique: segura e avisa", conf() === false && avisos.length === 1);
check("2º clique na mesma área: libera", conf() === true);
const conf2 = ctx({ _spellHL: { atingidos: { aliados: [] }, area: new Set(["1,1"]) } }, (k) => k, () => {}, () => {});
check("sem aliado atingido: libera de primeira", conf2() === true);

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
