// Direção/flanco/costas — espelho no cliente. Roda da raiz: node tools/test_direcao_flanco_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
global.WebSocket = class { constructor() { this.readyState = 1; } send(s) { enviados.push(JSON.parse(s)); } close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");

console.log("\n[1] Tabela 3/2/3");
const esperado = (f, rel) => {
  const dot = rel[0] * f[0] + rel[1] * f[1], cruz = Math.abs(rel[0] * f[1] - rel[1] * f[0]);
  if (dot < 0 && -dot >= cruz) return "costas";
  if (cruz > Math.abs(dot)) return "flanco";
  return "frente";
};
for (const f of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
  const alvo = { id: "t", type: "goblin", hp: 5, pos: [5, 5], facing: f, size: [1, 1] };
  let ok = true; const cont = { frente: 0, flanco: 0, costas: 0 };
  for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
    if (!dx && !dy) continue;
    const s = GS.setorAtaque({}, { pos: [5 + dx, 5 + dy], class_id: "warrior" }, alvo);
    cont[s]++; ok = ok && s === esperado(f, [dx, dy]);
  }
  check(`direção ${f}: setores e 3/2/3`, ok && cont.frente === 3 && cont.flanco === 2 && cont.costas === 3);
}

console.log("\n[2] Padrões, 2×2, incapaz e altura");
const heroi = { class_id: "warrior", pos: [5, 5] };
check("herói sem facing olha para o sul", JSON.stringify(GS.facingDe(heroi)) === "[0,1]");
check("orientado sem facing olha para oeste", JSON.stringify(GS.facingDe({ oriented: true })) === "[-1,0]");
check("facing diagonal cai no padrão", JSON.stringify(GS.facingDe({ facing: [1, 1] })) === "[0,1]");
const g = { id: "g", type: "ogro", hp: 9, pos: [5, 5], facing: [0, 1], size: [2, 2] };
check("2×2: costas, flanco e frente", GS.setorAtaque({}, { pos: [5, 3], class_id: "x" }, g) === "costas"
  && GS.setorAtaque({}, { pos: [7, 5], class_id: "x" }, g) === "flanco"
  && GS.setorAtaque({}, { pos: [5, 7], class_id: "x" }, g) === "frente");
const t = { class_id: "warrior", pos: [5, 5], facing: [0, 1], dormindo: true };
check("alvo dormindo = costas", GS.setorAtaque({}, { pos: [5, 6], class_id: "x" }, t) === "costas");
const inerte = { id: "i", type: "goblin", hp: 5, pos: [5, 5], facing: [0, 1], initiative_engaged: false };
check("monstro fora de combate = costas", GS.setorAtaque({}, { pos: [5, 6], class_id: "x" }, inerte) === "costas");
const st = { elevacoes: { "5,6": 3 } };
const alvoN = { id: "n", type: "goblin", hp: 5, pos: [5, 5], facing: [0, 1] };
let b = GS.bonusPosicional(st, { pos: [5, 6], class_id: "x" }, alvoN);
check("3 níveis acima = +2 (teto)", b.altura === 2 && b.total === 2);
b = GS.bonusPosicional({ elevacoes: { "5,4": 5 } }, { pos: [5, 4], class_id: "x" }, alvoN);
check("costas + altura = +4 (teto)", b.total === 4);
b = GS.bonusPosicional({}, { pos: [6, 5], class_id: "x" }, alvoN);
check("flanco = +1", b.total === 1 && b.setor === "flanco");

console.log("\n[3] end_turn leva a direção");
enviados.length = 0;
GS.endTurn([0, -1]);
check("com direção: {type:end_turn, facing}", enviados.length === 1 && enviados[0].type === "end_turn"
  && JSON.stringify(enviados[0].facing) === "[0,-1]");
enviados.length = 0;
GS.endTurn();
check("sem direção: não manda facing", enviados.length === 1 && !("facing" in enviados[0]));

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
