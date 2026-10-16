// Deltas no cliente: merge de `deltas` no gameState.js real e tradução de nomes dentro deles.
// Roda da raiz: node tools/test_estado_delta_cliente.js
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
const pedidos = () => enviados.filter(m => m.type === "pedir_estado_completo").length;
const ds = extra => Object.assign({ type: "game_state", round: 1, phase: "playing", players: [] }, extra);   // delta real: sem monsters/explored
const base = extra => Object.assign({ type: "game_state", players: [], monsters: [], explored: [], round: 1, phase: "playing" }, extra);

console.log("[1] lista por entidade");
chegar(base({ monsters: [{ id: "a", hp: 5 }, { id: "b", hp: 6 }, { id: "c", hp: 7 }], explored: [[0, 0], [1, 0]] }));
const antes = GS.gameState.monsters;
chegar(ds({ round: 2, deltas: { monsters: { orden: ["a", "b", "c"], mudou: [{ id: "b", hp: 1 }] }, explored: { add: [] } } }));
const m = GS.gameState.monsters;
check("ordem preservada", m.map(x => x.id).join() === "a,b,c");
check("entrada mudada vence", m[1].hp === 1);
check("entradas iguais mantêm o valor", m[0].hp === 5 && m[2].hp === 7);
check("estado anterior não foi alterado (cópia rasa)", antes[1].hp === 6 && antes[0] !== m[0]);
check("deltas não fica no estado", GS.gameState.deltas === undefined);

console.log("[2] remoção e inclusão");
chegar(ds({ round: 3, deltas: { monsters: { orden: ["a", "c", "d"], mudou: [{ id: "d", hp: 9 }] }, explored: { add: [] } } }));
check("monstro morto some e o novo entra", GS.gameState.monsters.map(x => x.id).join() === "a,c,d");

console.log("[3] explored só com casas novas");
chegar(ds({ round: 4, deltas: { monsters: { orden: ["a", "c", "d"], mudou: [] }, explored: { add: [[2, 0]] } } }));
check("explored acumulado", GS.gameState.explored.length === 3 && GS.gameState.explored[2][0] === 2);

console.log("[4] sem cópia anterior ou entrada desconhecida: pede o completo");
const n0 = pedidos();
chegar(ds({ round: 5, deltas: { monsters: { orden: ["a", "zzz"], mudou: [] } } }));
check("id sem cópia => pediu estado completo", pedidos() === n0 + 1 && GS.gameState.round === 4);
chegar({ type: "city_state", players: [] });
chegar(ds({ round: 6, deltas: { monsters: { orden: ["a"], mudou: [] } } }));
check("sem estado anterior => pediu estado completo", pedidos() === n0 + 2 && GS.gameState == null);

console.log("[5] tradução alcança as entradas dentro de deltas");
global.window = global;
for (const f of ["strings", "catalogo", "composto", "interface", "erros", "narracao", "tutorial", "tutorial_guia"])
  eval(fs.readFileSync(path.join(raiz, "src", "lang", f + ".js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
window.I18N.setLang("en");
const msg = { type: "game_state", deltas: { monsters: { orden: ["m1"], mudou: [{ id: "m1", type: "skeleton", name: "Esqueleto" }] } } };
window.I18N.traduzirNomes(msg);
check("nome traduzido dentro do delta", msg.deltas.monsters.mudou[0].name === "Skeleton");

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
