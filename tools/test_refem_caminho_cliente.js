// Fatia 13 — o refém do exercício precisa de caminho DENTRO da sala de classe.
//   node tools/test_refem_caminho_cliente.js
// Causa raiz: `_walkable` barrava toda casa de sala com `allowed_class` quando o
// ator não tinha o mesmo `class_id`. O refém não é jogador (`findPath` o via como
// ator `{}`, sem `class_id`), então o clique na casa nunca achava caminho e o
// jogo não enviava nada ao servidor.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };
let sock = null;
global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");

// Sala 6x3 (x 2..7, y 0..2) exclusiva do paladino; herói em (3,1), refém em (6,1).
const W = 10, H = 3;
const tiles = Array.from({ length: H }, () => Array(W).fill(1));
const explorados = new Set();
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) explorados.add(`${x},${y}`);
function carregar(classe) {
  const st = { type: "game_state", tiles, explored: [...explorados], monsters: [], decorations: [],
    materiais: {}, rooms: [{ id: 1, x: 2, y: 0, w: 6, h: 3, allowed_class: "paladin", doors: [] }],
    players: [{ id: "h", class_id: classe, pos: [3, 1], alive: true, moves_left: 6 }],
    prisoner: { pos: [6, 1], alive: true, freed: true, rescuer_pid: "h", moves_left: 6, training_refem: true } };
  sock.onmessage({ data: JSON.stringify(st) });
}

console.log("\n[1] Refém anda dentro da sala exclusiva");
carregar("paladin");
let p = GS.findPath(tiles, explorados, 6, 1, 3, 0, 6);
check("refém acha caminho até uma casa da sala", Array.isArray(p) && p.length === 4);
const q = new Set(); GS.bfsReachable(tiles, explorados, 6, 1, 6, q);
check("casas azuis do refém existem", q.size > 3);

console.log("\n[2] A regra da sala continua valendo para o herói de outra classe");
carregar("mage");
check("mago não ganha caminho para dentro da sala do paladino", GS.findPath(tiles, explorados, 3, 1, 5, 1, 8) === null);
carregar("paladin");
check("paladino ganha", Array.isArray(GS.findPath(tiles, explorados, 3, 1, 5, 0, 8)));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
