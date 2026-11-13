// Comando no Solo com grupo — cliente. Roda da raiz:
//   node tools/test_comando_controle_cliente.js
// O controle de Comando é do HERÓI que lançou (o mago, um extra da conexão).
// Antes o cliente só reconhecia o controle se o herói EM FOCO fosse o mago;
// como outros heróis meus agem entre o lançamento e a vez do monstro, o foco
// já tinha saído dele e a ficha de controle nunca aparecia.
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
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "paladin" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" },
  { id: "o", name: "Bia", class_id: "rogue" } ] });

const estado = (vez, extra = {}) => Object.assign({ type: "game_state", current_turn: vez,
  players: [
    { id: "c", name: "Ana", pos: [1, 1], alive: true },
    { id: "m", name: "Pedro", pos: [2, 1], alive: true, controlador: "c" },
    { id: "o", name: "Bia", pos: [3, 1], alive: true } ],
  monsters: [{ id: "g", type: "goblin", hp: 5, pos: [4, 4] }],
  tiles: [[1]], explored: [], rooms: [] }, extra);

console.log("\n[1] O paladino agiu depois do mago: o foco está nele");
chega(estado("c"));
check("foco no paladino", GS.myPid === "c");

console.log("\n[2] Abre a janela de Comando do mago (vez do monstro)");
chega(estado(null, { command_control_pid: "m", command_control: { mid: "g", pid: "m" } }));
check("o cliente reconhece que controla o monstro", GS.isCommandController() === true);
check("o foco vai para o mago que lançou", GS.myPid === "m");
check("canControlMonster liga", GS.canControlMonster() === true);

console.log("\n[3] Mesmo com o foco trocado à mão, o controle continua meu");
GS.focarHeroi("c");
check("controle reconhecido com foco em outro herói meu", GS.isCommandController() === true);

console.log("\n[4] Comando de OUTRA conexão não é meu");
chega(estado(null, { command_control_pid: "o", command_control: { mid: "g", pid: "o" } }));
check("não controla o monstro da Bia", GS.isCommandController() === false);

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
