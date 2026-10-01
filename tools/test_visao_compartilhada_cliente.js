// Visão compartilhada — lado do cliente. Roda da raiz:
//   node tools/test_visao_compartilhada_cliente.js
//
// Cobra a função pura GS.heroisVisaoCompartilhada, a mensagem ao servidor e o
// computeVisionSet REAL do game.js (extraído e rodado com stubs): com a opção
// desligada ou bloqueada pelo anfitrião nada muda; ligada, soma o que os outros
// heróis vivos enxergam.
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

const heroi = (id, x, y, extra = {}) => ({ id, pos: [x, y], alive: true, ...extra });
const estado = (players, extra = {}) => ({ players, explored: [], ...extra });

console.log("\n[1] Quem entra na soma (GS.heroisVisaoCompartilhada)");
const st = estado([heroi("eu", 0, 0), heroi("b", 5, 5), heroi("morto", 6, 6, { alive: false }),
                   heroi("fora", 7, 7, { fora_masmorra: { rodadas_restantes: 2 } }),
                   heroi("semPos", -1, -1)]);
const ids = l => l.map(p => p.id).sort().join(",");
check("desligada: ninguém", GS.heroisVisaoCompartilhada(st, "eu", false).length === 0);
check("ligada: só o aliado vivo e dentro da masmorra", ids(GS.heroisVisaoCompartilhada(st, "eu", true)) === "b");
const stCego = estado([heroi("eu", 0, 0, { cego: true }), heroi("b", 5, 5)]);
check("herói cego: ninguém (cegueira suspende a soma)", GS.heroisVisaoCompartilhada(stCego, "eu", true).length === 0);
check("sem o próprio herói no estado: ninguém", GS.heroisVisaoCompartilhada(st, "outro", true).length === 0);

console.log("\n[2] Mensagem ao servidor");
GS.connect("ws://x", "Ana", "create");
GS.setVisaoCompartilhada(false);
const m = enviados.filter(e => e.type === "set_visao_compartilhada").pop();
check("envia set_visao_compartilhada com enabled", !!m && m.enabled === false);

console.log("\n[3] computeVisionSet real do game.js");
const gj = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const extrai = (re, nome) => { const mm = gj.match(re); if (!mm) throw new Error("não achei " + nome); return mm[0]; };
const fonte = [
  extrai(/function computeVisionSet\(state, me\)\{[\s\S]*?\n\}/, "computeVisionSet"),
  extrai(/function visaoCompartilhadaPermitida\(state\)\{[\s\S]*?\n\}/, "visaoCompartilhadaPermitida"),
  extrai(/function visaoCompartilhadaAtiva\(state\)\{[\s\S]*?\n\}/, "visaoCompartilhadaAtiva"),
].join("\n");
let _visaoCompPref = false;
const getSightRadius = p => p.r || 1;
const GSstub = { isMaster: () => false, hasLineOfSight: () => true,
                 heroisVisaoCompartilhada: GS.heroisVisaoCompartilhada };
const fabrica = new Function("GS", "getSightRadius", "pref",
  "let _visaoCompPref = pref;\n" + fonte + "\nreturn { computeVisionSet, visaoCompartilhadaAtiva };");
const casas = []; for (let y = 0; y < 12; y++) for (let x = 0; x < 12; x++) casas.push([x, y]);
const sala = (permitida) => estado([heroi("eu", 0, 0, { r: 1 }), heroi("b", 9, 9, { r: 1 })],
                                   { explored: casas, ...(permitida === undefined ? {} : { visao_compartilhada_permitida: permitida }) });
const me = s => s.players[0];

let f = fabrica(GSstub, getSightRadius, false);
let s = sala(true);
check("opção desligada: não vê a casa do aliado", !f.computeVisionSet(s, me(s)).has("9,9"));
f = fabrica(GSstub, getSightRadius, true);
check("opção ligada + permitida: vê em volta do aliado", f.computeVisionSet(s, me(s)).has("9,9") && f.computeVisionSet(s, me(s)).has("10,10"));
check("e continua vendo em volta de si", f.computeVisionSet(s, me(s)).has("1,1"));
check("o raio do aliado é respeitado", !f.computeVisionSet(s, me(s)).has("11,11"));
s = sala(false);
check("anfitrião bloqueou: não soma", !f.computeVisionSet(s, me(s)).has("9,9"));
s = sala(undefined);
check("campo ausente conta como permitido", f.computeVisionSet(s, me(s)).has("9,9"));

console.log("\n[4] Fiação no game.js");
check("sombra dos objetos tira as casas vistas por um aliado",
      /compartilhada && mapa\.size[\s\S]{0,200}computeVisionSet\(state, me\)/.test(gj));
check("painel tem a caixa e o botão do anfitrião",
      gj.includes('id="cfg-visao-chk"') && gj.includes('id="cfg-visao-host-btn"'));
check("troca de idioma repinta a linha", /_refreshTurnTimerOption\(\); _refreshVisaoCompartilhadaOption\(\);[^\n]*\/\/ rótulos/.test(gj));
check("preferência salva no navegador", gj.includes("'lfh_visao_compartilhada'"));

console.log(`\n${"=".repeat(62)}\n  ${PASS} passaram, ${FAIL} falharam\n${"=".repeat(62)}`);
process.exit(FAIL ? 1 : 0);
