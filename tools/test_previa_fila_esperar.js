// Prévia da fila ao Esperar. Roda da raiz: node tools/test_previa_fila_esperar.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

global.WebSocket = class { constructor() { this.readyState = 1; } send() {} close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

console.log("\n[1] filaAposEsperar (espelho de handle_esperar_vez: a vez vai para o fim da rodada)");
const o = [{kind: "player", id: "a"}, {kind: "monster", id: "m1"}, {kind: "player", id: "b"}, {kind: "monster", id: "m2"}];
const ids = l => l.map(e => e.id).join(",");
check("da posição 1: quem vem depois e, no fim, quem esperou", ids(GS.filaAposEsperar(o, 1)) === "b,m2,m1");
check("da posição 0", ids(GS.filaAposEsperar(o, 0)) === "m1,b,m2,a");
check("não muda a lista original", ids(o) === "a,m1,b,m2");
check("índice fora da fila devolve lista vazia", GS.filaAposEsperar(o, 7).length === 0 && GS.filaAposEsperar(o, -1).length === 0);
check("fila ausente devolve lista vazia", GS.filaAposEsperar(null, 0).length === 0);

console.log("\n[2] game.js: a coluna usa a prévia só com o botão sob o mouse ou com foco");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
check("a coluna troca a fila pela prévia quando ela vale",
  /GS\.filaAposEsperar\(order, currentIndex\)/.test(game));
check("a prévia exige o botão Esperar habilitado sob o mouse ou com foco",
  /\.tam-esperar:hover:not\(:disabled\)/.test(game) && /\.tam-esperar:focus:not\(:disabled\)/.test(game));
check("a prévia exige ser a minha vez e o servidor permitir esperar",
  /function _esperarPreviaAtiva[\s\S]{0,500}pode_esperar[\s\S]{0,200}GS\.isMyTurn/.test(game));
check("entrar e sair do botão redesenham a coluna",
  /\['mouseenter', *'mouseleave', *'focus', *'blur'\]/.test(game));
check("a prévia entra na chave de redesenho da coluna", /renderKey = JSON\.stringify\(\[[^\]]*previa/.test(game));
check("quem esperou ganha classe própria", /is-esperando/.test(game));
const css = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
check("estilo tracejado da prévia no CSS", /\.initiative-actor\.is-esperando[^{]*\{[^}]*dashed/.test(css));

console.log("\n[3] Textos");
const lang = fs.readFileSync(path.join(raiz, "src/lang/interface.js"), "utf8");
for (const k of ["esperar_dica_fila", "volta_aqui"]) {
  const m = lang.match(new RegExp('"ui\\.(menuacoes|hud)\\.' + k + '":[^\\n]*'));
  check("chave " + k + " com pt e en", !!m && /"en":/.test(m[0]) && /"pt":/.test(m[0]));
}

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
