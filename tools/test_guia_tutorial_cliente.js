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

console.log("\n[8] seletor: bolsa e slot (DOM do inventário)");
s = G.seletor("bolsa:racao_viagem");
check("bolsa acha o espaço pelo item", s && s.css === '.inv-bagslot[data-item-id="racao_viagem"]' && s.ancestral === null);
check("bolsa cai no botão da mochila se o inventário está fechado",
      s && s.alternativa === '[data-guia="botao:inventario"]');
s = G.seletor("slot:main_hand");
check("slot acha o espaço de equipamento", s && s.css === '.inv-slot[data-slot-key="main_hand"]');
s = G.seletor("botao:inventario");
check("botão da mochila usa data-guia", s && s.css === '[data-guia="botao:inventario"]');
check("alternativa só existe na bolsa", !G.seletor("botao:encerrar_turno").alternativa);

console.log("\n[9] alvoTabuleiro");
const estado = { monsters: [
  { id: "m1", type: "boneco_treino", pos: [5, 5], hp: 5 },
  { id: "m2", type: "boneco_treino", pos: [9, 9], hp: 5 },
  { id: "m3", type: "esqueleto_humano", pos: [1, 1], hp: 5 },
  { id: "m4", type: "boneco_treino", pos: [4, 5], hp: 0 },
] };
const todos = () => true;
let a = G.alvoTabuleiro("casa:[3,14]", estado, [0, 0], todos);
check("casa devolve a posição", a && a.tipo === "casa" && a.pos[0] === 3 && a.pos[1] === 14);
a = G.alvoTabuleiro("porta:[10,2]", estado, [0, 0], todos);
check("porta devolve a posição e marca caminho", a && a.tipo === "porta" && a.pos[0] === 10 && a.caminho === true);
a = G.alvoTabuleiro("casa:[3,14]", estado, [0, 0], () => false);
check("casa fora da visão: null", a === null);
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], todos);
check("monstro: o mais próximo vivo", a && a.tipo === "monstro" && a.id === "m1");
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], (x, y) => !(x === 5 && y === 5));
check("monstro: ignora quem está fora da visão", a && a.id === "m2");
a = G.alvoTabuleiro("monstro:boneco_treino", estado, [4, 4], () => false);
check("monstro: nenhum visível = null", a === null);
a = G.alvoTabuleiro("monstro:troll", estado, [4, 4], todos);
check("monstro: tipo que não existe = null", a === null);
a = G.alvoTabuleiro("monstro:boneco_treino", estado, null, todos);
check("monstro sem posição minha: pega o primeiro vivo", a && a.id === "m1");
check("botão não é alvo de tabuleiro", G.alvoTabuleiro("botao:encerrar_turno", estado, [0, 0], todos) === null);
check("lixo devolve null", G.alvoTabuleiro("xyz", estado, [0, 0], todos) === null
      && G.alvoTabuleiro(null, estado, [0, 0], todos) === null
      && G.alvoTabuleiro("monstro:boneco_treino", null, [0, 0], todos) === null);

console.log("\n[10] caminhoAbsoluto");
let c = G.caminhoAbsoluto([[1, 0], [1, 0], [0, 1]], 2, 3);
check("converte passos em casas", JSON.stringify(c) === "[[3,3],[4,3],[4,4]]");
check("passos vazios: vazio", G.caminhoAbsoluto([], 1, 1).length === 0);
check("não-lista: vazio", G.caminhoAbsoluto(null, 1, 1).length === 0);

console.log("\n[11] marcas no DOM e textos");
const invSrc = fs.readFileSync(path.join(raiz, "src", "ui", "inventoryModal.js"), "utf8");
check("espaço da bolsa leva o id do item", /dataset\.itemId\s*=/.test(invSrc));
check("botão da mochila tem data-guia", /id="fab-inventario"[^>]*data-guia="botao:inventario"|data-guia="botao:inventario"[^>]*id="fab-inventario"/.test(gameSrc));
const langSrc = fs.readFileSync(path.join(raiz, "src", "lang", "tutorial.js"), "utf8");
for (const k of ["dica_erro.fora_da_vez", "dica_erro.sem_acao", "dica_erro.longe_do_alvo",
                 "dica_erro.alvo_errado", "resultado.acerto", "resultado.critico", "resultado.erro"])
  check("chave ui.tutorial." + k, langSrc.includes('"ui.tutorial.' + k + '"'));

console.log("\n[12] fiação do aviso e da alternativa no game.js");
check("um único GS.on('licaoDica')", (gameSrc.match(/GS\.on\('licaoDica'/g) || []).length === 1);
check("um único GS.on('licaoResultado')", (gameSrc.match(/GS\.on\('licaoResultado'/g) || []).length === 1);
check("aviso usa as chaves de dica de erro", /ui\.tutorial\.dica_erro\./.test(gameSrc));
check("aviso usa as chaves de resultado", /ui\.tutorial\.resultado\./.test(gameSrc));
check("janela tem o elemento licao-aviso", /id="licao-aviso"/.test(gameSrc));
check("halo usa a alternativa do seletor", /sel\.alternativa/.test(gameSrc));
check("CSS do aviso existe", /\.licao-aviso\b/.test(cssSrc));
check("'Me mostra' aparece para alvo de tabuleiro também", /botoes = \(passo && passo\.ui && GuiaTutorial\.parseUi\(passo\.ui\)\)/.test(gameSrc));

console.log("\n[13] halo 2D no game.js");
check("função _guiaDesenhar2D existe", /function _guiaDesenhar2D\(/.test(gameSrc));
check("renderMap 2D chama _guiaDesenhar2D", /_guiaDesenhar2D\(ctx, state, visionSet\)/.test(gameSrc));
check("o desenho usa alvoTabuleiro e caminhoAbsoluto",
      /GuiaTutorial\.alvoTabuleiro\(/.test(gameSrc) && /GuiaTutorial\.caminhoAbsoluto\(/.test(gameSrc));
check("o halo 2D mantém a animação por _agendarChamas2D", /function _guiaDesenhar2D[\s\S]{0,2200}_agendarChamas2D\(\)/.test(gameSrc));

console.log("\n[14] halo 3D no game.js");
check("função _guiaAtualizar3D existe", /function _guiaAtualizar3D\(/.test(gameSrc));
check("o laço 3D chama _guiaAtualizar3D", /startLoop3D[\s\S]{0,40000}_guiaAtualizar3D\(\)/.test(gameSrc));
check("dispose3D libera a marca do guia", /function dispose3D[\s\S]{0,6000}guiaMarca/.test(gameSrc));
check("a marca 3D usa topoSuperficie3D", /function _guiaAtualizar3D[\s\S]{0,2500}topoSuperficie3D\(/.test(gameSrc));

console.log("\n[15] glossário: segmentos");
{
  const vistos = new Set();
  const a = G.segmentos('Gaste [[movimento]] e depois [[movimento]] de novo, com [[ca]].', vistos);
  check('pedaços na ordem', a.map(s => s.termo ? '#' + s.termo : s.texto).join('|')
    === 'Gaste |#movimento| e depois |#movimento| de novo, com |#ca|.');
  check('1ª ocorrência é "primeira"', a[1].primeira === true);
  check('2ª ocorrência não é "primeira"', a[3].primeira === false);
  check('vistos guarda os termos', vistos.has('movimento') && vistos.has('ca'));
  const b = G.segmentos('Outro [[movimento]].', vistos);
  check('vistos persiste entre chamadas', b[1].primeira === false);
  const c = G.segmentos('sem marcas', new Set());
  check('texto sem marca vira 1 pedaço', c.length === 1 && c[0].texto === 'sem marcas' && !c[0].termo);
  const d = G.segmentos('[[Inválido]] e [[ok_1]]', new Set());
  check('só id minúsculo vira termo', d.some(s => s.termo === 'ok_1') && !d.some(s => s.termo === 'Inválido'));
  check('entrada não-string é segura', G.segmentos(null, new Set()).length === 0);
}

console.log("\n[16] fiação do glossário no game.js e no css");
{
  const gjs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
  const css = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
  check("game.js usa GuiaTutorial.segmentos", /GuiaTutorial\.segmentos\(/.test(gjs));
  check("game.js define _tutHTML", /function _tutHTML\(/.test(gjs));
  check("texto da lição passa por _tutHTML", /class="licao-texto">\$\{[^}]*_tutHTML\(/.test(gjs));
  check("balão do glossário existe", /guia-balao/.test(gjs) && /#guia-balao/.test(css));
  check("termo sublinhado no css", /\.guia-termo/.test(css));
  check("chave de definição usa ui.tutorial.glossario", /ui\.tutorial\.glossario\./.test(gjs));
}

console.log("\n[17] halo de habilidade escolhe o elemento visível, não o 1º do DOM");
{
  const gjs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
  const i = gjs.indexOf("function _guiaAplicarHalo()");
  check("_guiaAplicarHalo existe", i >= 0);
  const corpo = i >= 0 ? gjs.slice(i, i + 1200) : "";
  check("varre todos os candidatos (querySelectorAll)", corpo.includes("querySelectorAll(sel.css)"));
  check("exige elemento visível (getClientRects)", corpo.includes("getClientRects().length"));
}

console.log("\n[18] conclusão visível (fiação)");
{
  const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
  const gjSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
  const langT = fs.readFileSync(path.join(raiz, "src", "lang", "tutorial.js"), "utf8");
  check("gameState repassa licao_passo_ok", /case 'licao_passo_ok':[\s\S]{0,80}_emit\('licaoPassoOk'/.test(gsSrc));
  check("gameState repassa licao_concluida", /case 'licao_concluida':[\s\S]{0,80}_emit\('licaoConcluida'/.test(gsSrc));
  check("game.js trata licaoPassoOk", /GS\.on\('licaoPassoOk'/.test(gjSrc));
  check("game.js trata licaoConcluida", /GS\.on\('licaoConcluida'/.test(gjSrc));
  for (const k of ["passo_ok", "licao_concluida", "recompensa", "recompensa_trilha"])
    check("chave ui.tutorial." + k + " em pt e en",
          new RegExp('"ui\\.tutorial\\.' + k + '":[^\\n]*"pt"[^\\n]*"en"').test(langT));
}

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
