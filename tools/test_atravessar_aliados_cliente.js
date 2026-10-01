// Atravessar aliados — lado do cliente. Roda da raiz:
//   node tools/test_atravessar_aliados_cliente.js
//
// As casas azuis (GS.bfsReachable) e o caminho do clique (GS.findPath) seguem a
// regra do servidor (tools/test_atravessar_aliados.py): com a opção da sala
// ligada, a casa de herói, servo ou prisioneiro liberto pode ser CRUZADA, mas
// nunca é destino; monstro e prisioneiro preso bloqueiam sempre. E os servos e
// o prisioneiro mandam o caminho inteiro numa mensagem.
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

// Corredor 4×1: herói em (0,0); ocupante em (1,0); destino livre em (2,0).
const tiles = [[1, 1, 1, 1]];
const explorados = new Set(["0,0", "1,0", "2,0", "3,0"]);
function carregar({ ligada, ocupante }) {
  const heroi = { id: "h", pos: [0, 0], alive: true, moves_left: 6 };
  const st = { type: "game_state", players: [heroi], monsters: [], decorations: [],
               tiles, explored: [...explorados], rooms: [], materiais: {},
               atravessar_aliados: ligada };
  if (ocupante === "heroi") st.players.push({ id: "b", pos: [1, 0], alive: true });
  if (ocupante === "servo") heroi.animados = [{ id: "a", pos: [1, 0], vida_atual: 5 }];
  if (ocupante === "prisioneiro") st.prisoner = { pos: [1, 0], alive: true, freed: true };
  if (ocupante === "preso") st.prisoner = { pos: [1, 0], alive: true, freed: false };
  if (ocupante === "monstro") st.monsters.push({ id: "m", pos: [1, 0], hp: 5 });
  sock.onmessage({ data: JSON.stringify(st) });
}
const azuis = () => { const r = new Set(); GS.bfsReachable(tiles, explorados, 0, 0, 3, r); return r; };

console.log("\n[1] Desligada: aliado bloqueia como antes");
for (const oc of ["heroi", "servo", "prisioneiro"]) {
  carregar({ ligada: false, ocupante: oc });
  check(`${oc}: casa além dele não fica azul`, !azuis().has("2,0"));
  check(`${oc}: sem caminho até além dele`, GS.findPath(tiles, explorados, 0, 0, 2, 0, 3) === null);
}

console.log("\n[2] Ligada: cruza o aliado, nunca para nele");
for (const oc of ["heroi", "servo", "prisioneiro"]) {
  carregar({ ligada: true, ocupante: oc });
  const r = azuis();
  check(`${oc}: casa além dele fica azul`, r.has("2,0"));
  check(`${oc}: a casa DELE não fica azul`, !r.has("1,0"));
  const p = GS.findPath(tiles, explorados, 0, 0, 2, 0, 3);
  check(`${oc}: caminho atravessa até (2,0)`, !!p && p.length === 2);
  check(`${oc}: caminho até a casa dele é recusado`, GS.findPath(tiles, explorados, 0, 0, 1, 0, 3) === null);
}
carregar({ ligada: true, ocupante: "heroi" });
const parcial = GS.findPath(tiles, explorados, 0, 0, 3, 0, 1, true);
check("caminho parcial nunca termina em cima do aliado", !parcial || parcial.length === 0);

console.log("\n[3] Continua bloqueando com a opção ligada");
for (const oc of ["monstro", "preso"]) {
  carregar({ ligada: true, ocupante: oc });
  check(`${oc}: bloqueia`, !azuis().has("2,0"));
}

console.log("\n[4] Mensagens");
GS.moverAnimadoCaminho("a", [[1, 0], [1, 0]]);
GS.moverPrisioneiroCaminho([[0, 1]]);
GS.setAtravessarAliados(true);
const tipos = enviados.map(e => e.type);
check("servo manda o caminho inteiro", enviados.some(e => e.type === "mover_animado_caminho" && e.animado_id === "a" && e.path.length === 2));
check("prisioneiro manda o caminho inteiro", tipos.includes("mover_prisioneiro_caminho"));
check("anfitrião liga a opção", enviados.some(e => e.type === "set_atravessar_aliados" && e.enabled === true));

console.log("\n[5] game.js usa as mensagens de caminho e tem o botão do anfitrião");
const gj = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("clique do servo usa moverAnimadoCaminho", gj.includes("GS.moverAnimadoCaminho(animado.id, passos)"));
check("clique do prisioneiro usa moverPrisioneiroCaminho", gj.includes("GS.moverPrisioneiroCaminho(passos)"));
check("não sobra envio passo a passo do servo", !/for\(const \[dx,dy\] of passos\) GS\.moverAnimado\(/.test(gj));
check("painel ⚙️ tem o botão", gj.includes("cfg-atravessar-btn") && gj.includes("function _refreshAtravessarOption"));
check("o painel se atualiza junto da visão compartilhada",
      (gj.match(/_refreshVisaoCompartilhadaOption\(\); _refreshAtravessarOption\(\);/g) || []).length >= 4);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
