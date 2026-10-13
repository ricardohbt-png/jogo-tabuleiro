// Intenção dos monstros (cliente) — roda da raiz: node tools/test_intencoes_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };
global.window = {};
const IM = eval(fs.readFileSync(path.join(raiz, "src", "intencaoMonstros.js"), "utf8") + "; window.IntencaoMonstros");

const item = (over) => Object.assign({
  monstro_id: "m1", alvo_id: "a", alvo_tipo: "heroi", alvo_pos: [5, 5],
  acao: "corpo", alcanca: true, casa_ataque: [6, 5], certeza: "firme" }, over || {});

console.log("[1] modos");
check("MODOS", JSON.stringify(IM.MODOS) === '["off","grupo","todas"]');
check("lerModo válido", IM.lerModo("todas") === "todas" && IM.lerModo("off") === "off");
check("lerModo inválido/ausente cai em grupo", IM.lerModo("x") === "grupo" && IM.lerModo(null) === "grupo" && IM.lerModo(undefined) === "grupo");
check("proximoModo cicla", IM.proximoModo("off") === "grupo" && IM.proximoModo("grupo") === "todas" && IM.proximoModo("todas") === "off");

console.log("[2] descartar resposta velha");
check("rodada igual: mantém", IM.descartar({ rodada: 3 }, { round: 3 }) === false);
check("rodada diferente: descarta", IM.descartar({ rodada: 2 }, { round: 3 }) === true);
check("sem estado: descarta", IM.descartar({ rodada: 2 }, null) === true);
check("mensagem lixo: descarta", IM.descartar(null, { round: 1 }) === true);

console.log("[3] selecionar");
const itens = [item(), item({ monstro_id: "m2", alcanca: false, casa_ataque: null }),
               item({ monstro_id: "m3", acao: "distancia" })];
check("off: nada", IM.selecionar(itens, { modo: "off" }).length === 0);
check("grupo: só quem alcança", IM.selecionar(itens, { modo: "grupo" }).map(i => i.monstro_id).join() === "m1,m3");
check("todas: todos", IM.selecionar(itens, { modo: "todas" }).length === 3);
let s = IM.selecionar(itens, { modo: "grupo", destaqueId: "m2" });
check("destaque entra mesmo sem alcançar, e é forte",
      s.length === 3 && s.find(i => i.monstro_id === "m2").forte === true);
check("os demais não são fortes", s.filter(i => i.forte).length === 1);
s = IM.selecionar(itens, { modo: "off", destaqueId: "m1" });
check("off ainda mostra o destaque", s.length === 1 && s[0].monstro_id === "m1" && s[0].forte);
check("lixo não quebra", IM.selecionar(null, { modo: "todas" }).length === 0 && IM.selecionar([null, item()], { modo: "todas" }).length === 1);

console.log("[4] contar");
const c = IM.contar(IM.selecionar([item(), item({ monstro_id: "m9" }), item({ monstro_id: "m8", alvo_id: "b" })], { modo: "todas" }));
check("contador por alvo", c.a === 2 && c.b === 1);

console.log("[5] estilo");
check("firme: contínuo e forte", IM.estilo(item()).tracejado === false && IM.estilo(item()).opacidade > 0.9);
check("provável: tracejado e fraco", IM.estilo(item({ certeza: "provavel" })).tracejado === true && IM.estilo(item({ certeza: "provavel" })).opacidade < 0.7);
check("cores por ação", IM.estilo(item()).cor === "#e5484d" && IM.estilo(item({ acao: "distancia" })).cor === "#f08a24" && IM.estilo(item({ acao: "ameaca" })).cor === "#9b5de5");

console.log("[6] fiação do GS");
const gs = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
check("GS: pedirIntencoes envia prever_intencoes", /type:\s*'prever_intencoes'/.test(gs));
check("GS: trata intencoes_monstros", gs.includes("case 'intencoes_monstros'"));
check("GS: exporta pedirIntencoes e intencoes", /pedirIntencoes,/.test(gs) && /\bintencoes,/.test(gs));
const html = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
check("index.html carrega o módulo", html.includes("src/intencaoMonstros.js"));

console.log("[7] fiação do game.js (2D)");
const jogo = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("lê o modo salvo com try/catch", /lfh_intencoes/.test(jogo) && /IntencaoMonstros\.lerModo\(/.test(jogo));
check("desenho 2D chamado no fim do renderMap", /_intencoesDesenhar2D\(ctx, state, visionSet\);/.test(jogo));
check("usa o módulo puro para selecionar", jogo.includes("IntencaoMonstros.selecionar("));
check("descarta resposta velha", jogo.includes("IntencaoMonstros.descartar("));
check("pede no início da vez e depois de mover (com intervalo)", jogo.includes("_intencoesPedirAgora") && /250/.test(jogo));
check("tooltip do monstro ganha a linha de intenção", jogo.includes("_intencaoLinhaTooltip("));
check("Mestre e mesa de teste não pedem", /GS\.isMaster\(\)\s*\|\|[^;]*test_mode/.test(jogo.slice(jogo.indexOf("function _intencoesPodePedir"))));
const nOn = ev => (jogo.match(new RegExp("^GS\\.on\\('" + ev + "'", "gm")) || []).length;
check("GS.on('gameState' aparece uma única vez", nOn("gameState") === 1);
check("GS.on('intencoesMonstros' aparece uma única vez", nOn("intencoesMonstros") === 1);
const iH = jogo.search(/^GS\.on\('gameState'/m);
check("o pedido automático está no corpo do handler gameState sobrevivente",
      iH >= 0 && jogo.slice(iH, iH + 3000).includes("_intencoesPedirAgora()"));
check("desenho 2D protege save/restore e ignora posição inválida",
      /try \{\s*for\(const it of itens\)/.test(jogo) && jogo.includes("finally { ctx.restore(); }") && jogo.includes("!par(it.alvo_pos)"));
check("destaque do tooltip exige elemento visível", jogo.includes("el.getClientRects().length > 0"));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
