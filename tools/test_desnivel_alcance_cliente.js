// Desnível do terreno — lado do cliente. Roda da raiz:
//   node tools/test_desnivel_alcance_cliente.js
//
// O cliente decide se o clique no alvo vira ataque (GS.weaponCanReachTile) e se
// há linha de visão (GS.hasLineOfSight). Os dois têm de seguir a MESMA regra do
// servidor (tools/test_desnivel_alcance.py): 1 nível de terreno = 1 quadrado de
// distância; o raio de visão sai do olho de quem olha até o corpo do alvo, então
// a borda de um platô de 1 nível não esconde o que está em cima dele.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.WebSocket = class { constructor() { this.readyState = 1; } send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

const W = 9, H = 3;
const tiles = Array.from({ length: H }, () => Array(W).fill(1));
function estado(platos, monstro) {
  const elevacoes = {};
  for (const [x0, x1, n] of platos) for (let x = x0; x <= x1; x++)
    for (let y = 0; y < H; y++) elevacoes[`${x},${y}`] = n;
  return { tiles, elevacoes, rooms: [], materiais: {}, decorations: [],
           players: [], monsters: monstro ? [monstro] : [] };
}

console.log("[1] linha de visão por cima do platô de 1 nível");
for (const tx of [3, 4, 6, 8]) {
  const st = estado([[3, 8, 1]], { id: "m", pos: [tx, 1], hp: 5 });
  check(`do chão vê o alvo em cima do platô (x=${tx})`, GS.hasLineOfSight(st, 1, 1, tx, 1));
}
const paredao = { tiles, elevacoes: { "4,0": 2, "4,1": 2, "4,2": 2 }, rooms: [], materiais: {},
                  decorations: [], players: [], monsters: [] };
check("paredão de 2 níveis ainda tapa a visão entre dois no chão", !GS.hasLineOfSight(paredao, 1, 1, 7, 1));

console.log("[2] custo vertical: 1 nível = 1 quadrado; voo 2 pontos = 1");
check("1 nível custa 1", GS.custoVerticalTerreno([1, 1], 0, [3, 1], 0, estado([[3, 8, 1]])) === 1);
check("2 níveis custam 2", GS.custoVerticalTerreno([1, 1], 0, [3, 1], 0, estado([[3, 8, 2]])) === 2);
check("voo a 2 pontos custa 1", GS.custoVerticalTerreno([1, 1], 0, [3, 1], 2, estado([])) === 1);

console.log("[3] alcance da arma (o que decide o clique)");
const heroi = (arma) => ({ id: "h", pos: [1, 1], altura: 0, weapon: arma });
{
  const st = estado([[3, 8, 1]]);
  const arco = heroi({ id: "arco_curto", range: 3 });
  const c = (tx) => GS.custoVerticalTerreno(arco.pos, 0, [tx, 1], 0, st);
  check("arco alcance 3: alvo a 2 + 1 de subida cabe", 2 + c(3) <= 3);
  check("arco alcance 3: alvo a 3 + 1 de subida não cabe", 3 + c(4) > 3);
}
{
  const st = estado([[2, 8, 1]]);
  const espada = heroi({ id: "shortsword" });
  check("espada: adjacente 1 nível acima tem 1 quadrado de subida",
        GS.degrausCorpoACorpo(espada.pos, 0, [2, 1], 0, st) === 1);
  check("voo baixo (1 ponto) segue sem subida no corpo a corpo",
        GS.degrausCorpoACorpo([1, 1], 0, [2, 1], 1, estado([])) === 0);
  check("voo a 3 pontos = 1,5 quadrado de subida",
        GS.degrausCorpoACorpo([1, 1], 0, [2, 1], 3, estado([])) === 1.5);
}

console.log("[4] weaponCanReachTile com o estado do jogo carregado");
{
  let sock = null;
  global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send() {} close() {} };
  GS.connect("ws://x", "Ana", "create");
  const st = estado([[2, 8, 1]], { id: "m", pos: [2, 1], hp: 5 });
  const eu = { id: "h", pos: [1, 1], alive: true, altura: 0, weapon: { id: "shortsword" } };
  sock.onmessage({ data: JSON.stringify(Object.assign({ type: "game_state", explored: [] }, st, { players: [eu] })) });
  check("espada não alcança o alvo adjacente 1 nível acima", !GS.weaponCanReachTile(eu, 2, 1, 0));
  eu.weapon = { id: "lanca", reach: "lanca" };
  check("lança alcança o alvo adjacente 1 nível acima", GS.weaponCanReachTile(eu, 2, 1, 0));
  check("lança não alcança 2 casas + 1 de subida", !GS.weaponCanReachTile(eu, 3, 1, 0));
  eu.weapon = { id: "arco_curto", range: 3 };
  check("arco alcance 3 alcança o alvo a 2 casas em cima do platô", GS.weaponCanReachTile(eu, 3, 1, 0));
  check("arco alcance 3 não alcança a 3 casas em cima do platô", !GS.weaponCanReachTile(eu, 4, 1, 0));
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
