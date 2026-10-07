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

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
