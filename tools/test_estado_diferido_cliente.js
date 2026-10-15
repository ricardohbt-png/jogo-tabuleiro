// game_state com `diferidos`: o cliente reaproveita o que já tem; sem cópia, pede o estado completo.
// Roda da raiz: node tools/test_estado_diferido_cliente.js
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

let sock = null; const enviados = [];
global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send(d) { enviados.push(JSON.parse(d)); } close() {} };
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chegar = m => sock.onmessage({ data: JSON.stringify(m) });
const base = (extra) => Object.assign({ type: "game_state", players: [], monsters: [], explored: [], round: 1, phase: "playing" }, extra);
const pedidos = () => enviados.filter(m => m.type === "pedir_estado_completo").length;

console.log("[1] completo, depois omitido");
chegar(base({ tiles: [[1, 2]], materiais: { a: 1 }, decorations: [{ id: "d" }] }));
check("estado completo é guardado", GS.gameState.materiais.a === 1);
const refTiles = GS.gameState.tiles;
chegar(base({ round: 2, diferidos: ["tiles", "materiais", "decorations"] }));
check("round novo entrou", GS.gameState.round === 2);
check("omitidos foram preenchidos", GS.gameState.materiais.a === 1 && GS.gameState.decorations[0].id === "d");
check("mesma referência reaproveitada (sem recopiar)", GS.gameState.tiles === refTiles);
check("nenhum pedido enviado", pedidos() === 0);

console.log("[2] mudança de um campo");
chegar(base({ round: 3, decorations: [{ id: "novo" }], diferidos: ["tiles", "materiais"] }));
check("campo reenviado vence", GS.gameState.decorations[0].id === "novo");
check("o resto segue reaproveitado", GS.gameState.materiais.a === 1);

console.log("[3] sem cópia anterior: pede o estado completo e não renderiza lixo");
chegar({ type: "city_state", players: [] });   // cidade zera o gameState
check("cidade zerou o estado", GS.gameState == null);
chegar(base({ round: 4, diferidos: ["tiles"] }));
check("pediu estado completo", pedidos() === 1);
check("estado incompleto não foi adotado", GS.gameState == null);
chegar(base({ round: 4, tiles: [[1]], materiais: {}, decorations: [] }));
check("o completo seguinte entra", GS.gameState && GS.gameState.round === 4);

console.log("[4] mensagem sem `diferidos` age como sempre");
chegar(base({ round: 5, tiles: [[9]] }));
check("sem lista, nada é preenchido", GS.gameState.round === 5 && GS.gameState.materiais === undefined);
check("não pediu nada", pedidos() === 1);

console.log("[5] fiação: handler do servidor conhece o pedido");
const srv = fs.readFileSync(path.join(raiz, "server.py"), "utf8");
check("server.py trata pedir_estado_completo", srv.includes('t == "pedir_estado_completo"'));
const lista = srv.match(/ESTADO_DIFERIVEL = \(([^)]*)\)/)[1].match(/"(\w+)"/g).map(s => s.replace(/"/g, ""));
check("ESTADO_DIFERIVEL tem os 10 campos", lista.length === 10);

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
