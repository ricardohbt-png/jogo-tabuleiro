// Desfazer movimento e Esperar — cliente. Roda da raiz: node tools/test_desfazer_esperar_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
global.WebSocket = class { constructor() { this.readyState = 1; } send(s) { enviados.push(JSON.parse(s)); } close() {} };
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");

console.log("\n[1] Mensagens");
enviados.length = 0;
GS.desfazerMovimento();
check("desfazerMovimento envia {type:desfazer_movimento}", enviados.length === 1 && enviados[0].type === "desfazer_movimento");
enviados.length = 0;
GS.esperarVez();
check("esperarVez envia {type:esperar_vez}", enviados.length === 1 && enviados[0].type === "esperar_vez");

console.log("\n[2] Botões, atalhos e textos em game.js");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
const lang = fs.readFileSync(path.join(raiz, "src/lang/interface.js"), "utf8");
check("a barra tem os botões Desfazer e Esperar antes de Encerrar",
  /tam-desfazer[\s\S]{0,400}tam-esperar[\s\S]{0,400}tam-tab tam-end/.test(game));
check("a disponibilidade vem do servidor (pode_desfazer / pode_esperar)",
  /desf\.disabled = !hero\?\.pode_desfazer/.test(game) && /esp\.disabled = !hero\?\.pode_esperar/.test(game));
check("Ctrl+Z desfaz e X espera, só quando o servidor permite",
  /e\.ctrlKey && me\.pode_desfazer/.test(game) && /!e\.ctrlKey && me\.pode_esperar/.test(game));
check("os atalhos ignoram campos de texto e repetição",
  /!e\.repeat && !e\.altKey && !e\.metaKey && !\(e\.target/.test(game));
for (const k of ["desfazer", "desfazer_dica", "esperar", "esperar_dica"]) {
  const m = lang.match(new RegExp('"ui\\.menuacoes\\.' + k + '":[^\\n]*'));
  check("chave ui.menuacoes." + k + " com pt e en", !!m && /"en":/.test(m[0]) && /"pt":/.test(m[0]));
}
check("ajuda cita Ctrl+Z e X", /"ui\.ajuda\.desfazer_esperar"[^\n]*Ctrl\+Z[^\n]*X/.test(lang));
check("a ajuda do menu inclui o parágrafo novo", /ui\.ajuda\.desfazer_esperar/.test(game));

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
