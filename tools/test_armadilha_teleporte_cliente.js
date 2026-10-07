// Resultado da armadilha de teletransporte chega à animação. Roda da raiz:
//   node tools/test_armadilha_teleporte_cliente.js
// O servidor manda {type:"armadilha_teleporte"}; o gameState tratava só
// "armadilha_teletransporte" (o id do TIPO da armadilha), e o resultado nunca
// virava o evento armadilhaTeleporte que resolve o glifo em 2D/3D.
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

console.log("\n[1] O tipo que o servidor envia é o que o cliente trata");
const server = fs.readFileSync(path.join(raiz, "server.py"), "utf8");
const tipos = new Set([...server.matchAll(/"type": "(armadilha_tele\w*)"/g)].map(m => m[1]));
check("o servidor envia um único tipo: " + [...tipos].join(","), tipos.size === 1);
const tipo = [...tipos][0];

let recebido = null;
GS.on("armadilhaTeleporte", m => { recebido = m; });
sock.onmessage({ data: JSON.stringify({ type: tipo, alvo_id: "p1", origem: [2, 3], teleportado: true, destino: [9, 9] }) });
check("vira o evento armadilhaTeleporte", recebido && recebido.alvo_id === "p1");
check("com o destino", recebido && recebido.destino && recebido.destino[0] === 9);

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
