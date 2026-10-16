// Ajudante do test_estado_delta.py: alimenta o gameState.js REAL com uma sequência de mensagens
// (arquivo JSON) e imprime o gameState depois de cada game_state. Uso: node tools/_estado_delta_node.js seq.json
const fs = require("fs"), path = require("path");
let sock = null; const pedidos = [];
global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send(d) { pedidos.push(JSON.parse(d)); } close() {} };
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(__dirname, "..", "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const seq = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const saida = [];
for (const m of seq) {
  const antes = pedidos.length;
  sock.onmessage({ data: JSON.stringify(m) });
  saida.push({ pediu: pedidos.length > antes, estado: GS.gameState });
}
process.stdout.write(JSON.stringify(saida));
