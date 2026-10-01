// Solo com grupo — cliente. Roda da raiz:
//   node tools/test_solo_grupo_cliente.js
// `myPid` é o herói EM FOCO; `connPid` é a conexão. O foco pula sozinho para
// o herói meu que está na vez, e toda mensagem leva `heroi` quando há grupo.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
let sock = null;
const guardado = {};
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send(s) { enviados.push(JSON.parse(s)); }
  close() {}
};
global.window = {};
global.localStorage = { getItem: k => guardado[k] ?? null,
                        setItem: (k, v) => { guardado[k] = v; }, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

const focos = [];
GS.on("focoHeroi", ev => focos.push(ev));

console.log("\n[1] Lobby: aprende a conexão e os heróis dela");
chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "warrior" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" },
  { id: "o", name: "Bia", class_id: "rogue" } ] });
check("connPid = principal", GS.connPid === "c");
check("myPid começa no principal", GS.myPid === "c");
check("meusHerois = principal + extra", JSON.stringify(GS.meusHerois.slice().sort()) === '["c","m"]');
check("temGrupo", GS.temGrupo === true);
check("ehMeuHeroi: extra sim, alheio não", GS.ehMeuHeroi("m") && !GS.ehMeuHeroi("o"));
check("cascaDaClasse('mage') = extra", GS.cascaDaClasse("mage") === "m");
check("sessão grava a CONEXÃO", JSON.parse(guardado.lfh_session).pid === "c");

console.log("\n[2] Foco segue a vez");
const estado = vez => ({ type: "game_state", current_turn: vez, players: [
  { id: "c", name: "Ana", pos: [1, 1], alive: true },
  { id: "m", name: "Pedro", pos: [2, 1], alive: true, controlador: "c" } ],
  monsters: [], tiles: [[1]], explored: [], rooms: [] });
chega(estado("m"));
check("vez do extra → foco nele", GS.myPid === "m");
check("isMyTurn verdadeiro", GS.isMyTurn === true);
check("evento focoHeroi automático", focos.length === 1 && focos[0].pid === "m" && focos[0].auto === true);
chega(estado("m"));
check("mesmo turno não repete o evento", focos.length === 1);

console.log("\n[3] Troca manual de foco");
check("focarHeroi recusa pid alheio", GS.focarHeroi("o") === false && GS.myPid === "m");
check("focarHeroi no principal", GS.focarHeroi("c") === true && GS.myPid === "c");
check("fora da vez dele → isMyTurn falso", GS.isMyTurn === false);
check("evento manual", focos[focos.length - 1].auto === false);
chega(estado("m"));
check("um novo game_state do mesmo turno NÃO rouba o foco manual", GS.myPid === "c");

console.log("\n[4] Mensagens levam o herói em foco");
enviados.length = 0;
GS.endTurn();
check("end_turn leva heroi = foco", enviados[0] && enviados[0].heroi === "c");
GS.setKnownSpells(["a", "b"], "m");
check("setKnownSpells com herói explícito", enviados[1] && enviados[1].heroi === "m");
GS.selectParty(["warrior", "mage"]);
check("selectParty manda a lista", enviados[2] && enviados[2].type === "select_party"
      && enviados[2].classes.length === 2);

console.log("\n[5] Sem grupo, nada muda");
GS.connect("ws://x", "Leo", "create");
chega({ type: "lobby_state", code: "EFGH", host: "z", players: [{ id: "z", name: "Leo" }] });
enviados.length = 0;
GS.endTurn();
check("sem grupo: mensagem sem heroi", enviados[0] && enviados[0].heroi === undefined);
check("sem grupo: temGrupo falso", GS.temGrupo === false);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
