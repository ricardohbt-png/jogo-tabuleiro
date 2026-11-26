// Modo da bússola (⚙️) e atalhos de controle L2+B (desfazer) / L2+A (esperar).
// Roda da raiz: node tools/test_pontas_turno_cliente.js
const fs = require("fs");
const path = require("path");
const game = fs.readFileSync(path.join(__dirname, "..", "game.js"), "utf8").split("\r\n").join("\n");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };
function extrair(nome) {
  const i = game.indexOf(`function ${nome}(`);
  if (i < 0) return null;
  let k = game.indexOf("{", i), d = 0;
  for (; k < game.length; k++) { if (game[k] === "{") d++; else if (game[k] === "}") { d--; if (!d) break; } }
  return game.slice(i, k + 1);
}

console.log("\n[1] Modo da bússola");
const nomes = ["_autoTurnCombatActive", "_bussolaPedidaPelaLicao", "_bussolaLerModo", "_bussolaEmCombate"];
const fontes = nomes.map(extrair);
check("funções existem", fontes.every(Boolean));
check("chave de preferência declarada", /const _BUSSOLA_KEY = 'lfh_bussola_modo'/.test(game));
const mk = (modo) => new Function("GS", "let _bussolaModo = '" + modo + "';\n" + fontes.join("\n") + "\nreturn _bussolaEmCombate;");
const expl = { phase: "playing", monsters: [], players: [{ id: "p1", class_id: "warrior" }] };
const luta = { ...expl, monsters: [{ id: "m", hp: 5, alertado: true }] };
const licao = { ...expl, tutorial: { training: true, por_classe: { warrior: { requer_escolher_direcao: true } } } };
const GS = { myPid: "p1", isMaster: () => false };
check("combate: exploração não pergunta", mk("combate")(GS)(expl) === false);
check("combate: com monstro alerta pergunta", mk("combate")(GS)(luta) === true);
check("sempre: pergunta até na exploração", mk("sempre")(GS)(expl) === true);
check("nunca: não pergunta nem em combate", mk("nunca")(GS)(luta) === false);
check("nunca: a lição de treinamento ainda exige", mk("nunca")(GS)(licao) === true);
const ler = new Function(extrair("_bussolaLerModo") + "\nreturn _bussolaLerModo;")();
check("valor inválido cai em combate", ler("xyz") === "combate" && ler(null) === "combate" && ler("sempre") === "sempre" && ler("nunca") === "nunca");
check("select e persistência ligados no menu", /cfg-bussola-sel/.test(game) && /_setBussolaModo\(e\.target\.value\)/.test(game));

console.log("\n[2] Combos do controle");
const fn = extrair("_gamepadDesfazerEsperar");
check("função existe", !!fn);
function roda(botao, me, minhaVez) {
  const chamadas = [], avisos = [];
  const GS2 = { me, isMyTurn: minhaVez, desfazerMovimento: () => { chamadas.push("d"); return true; }, esperarVez: () => { chamadas.push("e"); return true; } };
  const f = new Function("GS", "_gamepadButtonEdge", "toast", "t", fn + "\nreturn _gamepadDesfazerEsperar;")(
    GS2, (pad, b) => b === botao, (m) => avisos.push(m), (k) => k);
  const r = f({});
  return { r, chamadas, avisos };
}
let x = roda(1, { pode_desfazer: true }, true);
check("L2+B desfaz e consome o botão", x.r === true && x.chamadas.join() === "d" && x.avisos.length === 1);
x = roda(0, { pode_esperar: true }, true);
check("L2+A espera e consome o botão", x.r === true && x.chamadas.join() === "e");
x = roda(1, { pode_desfazer: false }, true);
check("sem permissão do servidor: não envia, mas consome (não confirma/cancela)", x.r === true && x.chamadas.length === 0);
x = roda(0, { pode_esperar: true }, false);
check("fora da minha vez: não envia", x.r === true && x.chamadas.length === 0);
x = roda(2, { pode_desfazer: true }, true);
check("outro botão: não consome", x.r === false);
check("chamado só com L2 e sem L1/R1", /l2Held && !l1Held && !r1Held && playing\)\{\n    shortcutHandled = _gamepadDesfazerEsperar/.test(game));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
