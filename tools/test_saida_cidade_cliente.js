// Saída pela escada no Solo com grupo — cliente. Roda da raiz:
//   node tools/test_saida_cidade_cliente.js
// Com o grupo na masmorra e um herói na cidade, o foco fica nele: compras, templo e
// "Voltar à masmorra" saem em nome dele, mesmo que o jogador clique no cartão de
// outro herói (antes o pedido ia em nome do herói clicado e o servidor o ignorava).
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
let sock = null;
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send(s) { enviados.push(JSON.parse(s)); }
  close() {}
};
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "warrior" },
  { id: "r", name: "Luccas", class_id: "rogue", controlador: "c" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" } ] });

const cidade = (fora, phase = "playing") => ({ type: "city_state", phase, players: [
  { id: "c", name: "Ana", alive: true },
  { id: "r", name: "Luccas", alive: true, controlador: "c", fora_masmorra: fora.r || null },
  { id: "m", name: "Pedro", alive: false, controlador: "c", fora_masmorra: fora.m || null } ] });

console.log("\n[1] O foco vai para quem está na cidade");
check("começa no principal", GS.myPid === "c");
chega(cidade({ r: { fase: "cidade" } }));
check("city_state com o ladino comprando: foco nele", GS.myPid === "r");
check("trocar para quem está na masmorra é recusado", GS.focarHeroi("c") === false && GS.myPid === "r");
check("…e para o morto também", GS.focarHeroi("m") === false && GS.myPid === "r");

console.log("\n[2] Voltar à masmorra sai em nome dele");
enviados.length = 0;
GS.voltarMasmorra();
check("voltar_masmorra leva heroi = ladino", enviados[0] && enviados[0].type === "voltar_masmorra" && enviados[0].heroi === "r");

console.log("\n[3] Ressuscitado no templo não toma o lugar de quem o trouxe");
chega(cidade({ r: { fase: "cidade" }, m: { fase: "cidade", acompanha: "r" } }));
enviados.length = 0;
GS.voltarMasmorra();
check("a volta continua em nome do ladino", enviados[0] && enviados[0].heroi === "r");

console.log("\n[4] Grupo inteiro na cidade: foco livre, como antes");
chega(cidade({}, "city"));
check("troca de foco permitida", GS.focarHeroi("c") === true && GS.myPid === "c");

console.log(`\n=== ${PASS} passou, ${FAIL} falhou ===`);
process.exit(FAIL ? 1 : 0);
