// Guia do tutorial no cliente — roda da raiz: node tools/test_guia_tutorial_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
const G = eval(fs.readFileSync(path.join(raiz, "src", "guiaTutorial.js"), "utf8") + "; window.GuiaTutorial");

console.log("\n[1] parseUi");
let r = G.parseUi("botao:encerrar_turno");
check("botão", r && r.tipo === "botao" && r.id === "encerrar_turno");
r = G.parseUi("habilidade:mira_certeira");
check("habilidade", r && r.tipo === "habilidade" && r.id === "mira_certeira");
r = G.parseUi("casa:[3,14]");
check("casa vira posição", r && r.tipo === "casa" && r.pos[0] === 3 && r.pos[1] === 14);
r = G.parseUi("porta:[10,2]");
check("porta vira posição", r && r.tipo === "porta" && r.pos[1] === 2);
check("lixo devolve null", G.parseUi("xyz") === null && G.parseUi("") === null
      && G.parseUi(null) === null && G.parseUi(5) === null);
check("tipo desconhecido devolve null", G.parseUi("voar:alto") === null);

console.log("\n[2] seletor (só o que o HUD desenha nesta fatia)");
let s = G.seletor("botao:encerrar_turno");
check("botão usa data-guia", s && s.css === '[data-guia="botao:encerrar_turno"]' && s.ancestral === null);
s = G.seletor("habilidade:mira_certeira");
check("habilidade acha o ícone e sobe ao botão",
      s && s.css === '[data-ability-id="mira_certeira"]' && s.ancestral === "button");
s = G.seletor("hud:fome");
check("medidor usa data-guia", s && s.css === '[data-guia="hud:fome"]');
check("casa ainda não tem seletor de HUD", G.seletor("casa:[1,2]") === null);
check("monstro ainda não tem seletor de HUD", G.seletor("monstro:boneco_treino") === null);
check("id com aspas não escapa do seletor", G.seletor('habilidade:a"b') === null);

console.log("\n[3] nivelDica");
const cfg = { dica1S: 12, dica2S: 30 };
check("recém-chegado: 0", G.nivelDica(0, 5000, cfg) === 0);
check("11,9 s: 0", G.nivelDica(0, 11900, cfg) === 0);
check("12 s: 1", G.nivelDica(0, 12000, cfg) === 1);
check("29,9 s: 1", G.nivelDica(0, 29900, cfg) === 1);
check("30 s: 2", G.nivelDica(0, 30000, cfg) === 2);
check("progresso reinicia", G.nivelDica(40000, 41000, cfg) === 0);
check("relógio andando para trás: 0", G.nivelDica(5000, 1000, cfg) === 0);

console.log("\n[4] textoDica");
const passo = { dica: ["primeira", "segunda"] };
check("nível 0 sem texto", G.textoDica(passo, 0) === "");
check("nível 1 = primeira", G.textoDica(passo, 1) === "primeira");
check("nível 2 = segunda", G.textoDica(passo, 2) === "segunda");
check("só uma dica: nível 2 repete a última", G.textoDica({ dica: ["única"] }, 2) === "única");
check("sem dica: vazio", G.textoDica({}, 2) === "" && G.textoDica(null, 1) === "");

console.log("\n[5] gameState: passo na lição, avanço e evento");
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.injectPreviewState({
  type: "game_state", master_pid: "p1",
  players: [{ id: "p1", name: "G", class_id: "warrior", alive: true, pos: [1, 1] }],
  monsters: [], tiles: [[0]], rooms: [], explored: [], round: 1,
  tutorial: { por_classe: { warrior: { licao_id: "a", texto_curto: "Ataque", feito: 0, vezes: 1,
    concluidas: 0, total: 2, passo: { i: 1, n: 3, texto: "Passo", ui: "botao:encerrar_turno" } } } },
});
const lic = GS.licaoAtual();
check("licaoAtual traz o passo", lic && lic.passo && lic.passo.i === 1 && lic.passo.n === 3);
check("GS.avancarPasso existe", typeof GS.avancarPasso === "function");

console.log("\n[6] fiação estática no game.js, index.html e CSS");
const gameSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const indexSrc = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
const cssSrc = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
check("botão encerrar turno tem data-guia", /id="btn-end-turn"[^>]*data-guia="botao:encerrar_turno"|data-guia="botao:encerrar_turno"[^>]*id="btn-end-turn"/.test(gameSrc));
check("um único GS.on('licaoPasso')", (gameSrc.match(/GS\.on\('licaoPasso'/g) || []).length === 1);
check("janela usa GuiaTutorial.seletor", /GuiaTutorial\.seletor\(/.test(gameSrc));
check("janela usa nivelDica com VC.tutorial", /GuiaTutorial\.nivelDica\(/.test(gameSrc) && /VC\.tutorial/.test(gameSrc));
check("botão Entendi chama GS.avancarPasso", /GS\.avancarPasso\(\)/.test(gameSrc));
check("index.html carrega guiaTutorial.js e tutorial.js",
      /src\/guiaTutorial\.js/.test(indexSrc) && /src\/lang\/tutorial\.js/.test(indexSrc));
check("CSS do halo existe", /\.guia-halo\b/.test(cssSrc) && /@keyframes guia-pulso/.test(cssSrc));
check("_guiaEncerrar existe", /function _guiaEncerrar\(/.test(gameSrc));
{
  const ini = (gameSrc.match(/function _guiaIniciar\([\s\S]*?\n}\r?\n/) || [""])[0];
  const tick = (gameSrc.match(/function _guiaTick\([\s\S]*?\n}\r?\n/) || [""])[0];
  check("_guiaEstadoRef em _guiaIniciar e _guiaTick", /_guiaEstadoRef/.test(ini) && /_guiaEstadoRef/.test(tick));
  check("_guiaTick chama _guiaEncerrar()", /_guiaEncerrar\(\)/.test(tick));
}
check("textos pelo tradutor, não literais", /ui\.tutorial\.passo_de/.test(gameSrc) && /ui\.tutorial\.entendi/.test(gameSrc));

console.log("\n[7] gameState encaminha licao_dica e licao_resultado");
{
  const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
  check("case licao_dica emite licaoDica", /case 'licao_dica':\s*\n\s*_emit\('licaoDica'/.test(gsSrc));
  check("case licao_resultado emite licaoResultado", /case 'licao_resultado':\s*\n\s*_emit\('licaoResultado'/.test(gsSrc));
}

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
