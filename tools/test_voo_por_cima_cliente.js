// Voar por cima — lado do cliente. Roda da raiz:
//   node tools/test_voo_por_cima_cliente.js
//
// As casas azuis (GS.bfsReachable) e o caminho do clique (GS.findPath) têm de
// seguir a MESMA regra do servidor (`_pode_compartilhar_casa_voando` e
// `_voo_sobre_objeto`): altura mínima acima de quem está embaixo depende do
// porte — minúsculo/pequeno/médio 2 pontos, grande 4, enorme 6; objeto baixo 2,
// alto 4. A tabela é a mesma de tools/test_voo_por_cima.py.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

let sock = null;
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send() {}
  close() {}
};
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");

// Corredor 3×1: herói em (0,0), obstáculo em (1,0), destino em (2,0). Só dá
// para chegar a (2,0) passando por cima de (1,0).
const tiles = [[1, 1, 1]];
const explorados = new Set(["0,0", "1,0", "2,0"]);
function carregar({ altura, monstro = null, animado = null, decor = null }) {
  const heroi = { id: "h", pos: [0, 0], alive: true, voo: true, altura, moves_left: 6 };
  if (animado) heroi.animados = [];
  const outros = animado ? [{ id: "dono", pos: [9, 9], alive: true, animados: [animado] }] : [];
  sock.onmessage({ data: JSON.stringify({
    type: "game_state", players: [heroi, ...outros],
    monsters: monstro ? [monstro] : [], decorations: decor ? [decor] : [],
    tiles, explored: [...explorados], rooms: [], materiais: {},
  }) });
}
function alcanca() {
  const r = new Set();
  GS.bfsReachable(tiles, explorados, 0, 0, 2, r);
  return r.has("2,0");
}
function caminho() {
  return !!GS.findPath(tiles, explorados, 0, 0, 2, 0, 2);
}

const CASOS = [
  // [rótulo, cenário, altura mínima]
  ["monstro minúsculo", { monstro: { id: "m", pos: [1, 0], hp: 5, porte: "minusculo" } }, 2],
  ["monstro pequeno",   { monstro: { id: "m", pos: [1, 0], hp: 5, porte: "pequeno" } }, 2],
  ["monstro médio",     { monstro: { id: "m", pos: [1, 0], hp: 5, porte: "medio" } }, 2],
  ["monstro sem porte (médio)", { monstro: { id: "m", pos: [1, 0], hp: 5 } }, 2],
  ["monstro grande",    { monstro: { id: "m", pos: [1, 0], hp: 5, porte: "grande" } }, 4],
  ["monstro enorme",    { monstro: { id: "m", pos: [1, 0], hp: 5, porte: "enorme" } }, 6],
  ["servo animado",     { animado: { id: "a", pos: [1, 0], vida_atual: 5, porte: "medio" } }, 2],
  ["servo animado grande", { animado: { id: "a", pos: [1, 0], vida_atual: 5, porte: "grande" } }, 4],
  ["objeto baixo",      { decor: { id: "d", pos: [1, 0], size: [1, 1], pisavel: false, alto: false } }, 2],
  ["objeto alto",       { decor: { id: "d", pos: [1, 0], size: [1, 1], pisavel: false, alto: true } }, 4],
];

console.log("\n[1] Casas azuis e caminho: uma altura abaixo bloqueia, a mínima passa");
for (const [rotulo, cenario, minimo] of CASOS) {
  carregar({ ...cenario, altura: minimo - 1 });
  check(`${rotulo}: altura ${minimo - 1} não passa (azul)`, !alcanca());
  check(`${rotulo}: altura ${minimo - 1} não passa (caminho)`, !caminho());
  carregar({ ...cenario, altura: minimo });
  check(`${rotulo}: altura ${minimo} passa (azul)`, alcanca());
  check(`${rotulo}: altura ${minimo} passa (caminho)`, caminho());
}

console.log("\n[2] Quem está embaixo também voa: conta a diferença de altura");
carregar({ altura: 4, monstro: { id: "m", pos: [1, 0], hp: 5, porte: "medio", voo: true, altura: 2 } });
check("médio voando a 2, herói a 4: passa", alcanca());
carregar({ altura: 3, monstro: { id: "m", pos: [1, 0], hp: 5, porte: "medio", voo: true, altura: 2 } });
check("médio voando a 2, herói a 3: não passa", !alcanca());

console.log("\n[3] No chão (sem voo) nada muda");
carregar({ altura: 0, decor: { id: "d", pos: [1, 0], size: [1, 1], pisavel: false, alto: false } });
check("herói no chão não atravessa objeto baixo", !alcanca());
carregar({ altura: 0, decor: { id: "d", pos: [1, 0], size: [1, 1], pisavel: true, alto: false } });
check("objeto pisável continua livre", alcanca());

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
