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

console.log("[2] valida / descartar: rodada E vez");
const st3 = { round: 3, current_turn: "a" };
const ok3 = { rodada: 3, vez: "a", itens: [] };
check("rodada e vez iguais: vale", IM.valida(ok3, st3) === true && IM.descartar(ok3, st3) === false);
check("rodada diferente: descarta", IM.descartar({ rodada: 2, vez: "a", itens: [] }, st3) === true);
check("mesma rodada, outra vez (outro herói): descarta", IM.descartar(ok3, { round: 3, current_turn: "b" }) === true);
check("mesma rodada, fase dos monstros (current_turn nulo): descarta", IM.descartar(ok3, { round: 3, current_turn: null }) === true);
check("rodada ausente nos dois lados não vale (undefined===undefined)",
      IM.valida({ vez: "a", itens: [] }, { current_turn: "a" }) === false);
check("vez ausente nos dois lados não vale", IM.valida({ rodada: 3, itens: [] }, { round: 3 }) === false);
check("itens não-lista: descarta", IM.descartar({ rodada: 3, vez: "a", itens: "x" }, st3) === true);
check("sem estado: descarta", IM.descartar(ok3, null) === true);
check("mensagem lixo: descarta", IM.descartar(null, st3) === true);

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

console.log("[8] fiação do game.js (3D)");
check("3D: função de atualização chamada junto do guia", /_guiaAtualizar3D\(\);[\s\S]{0,200}_intencoesAtualizar3D\(\)|_intencoesAtualizar3D\(\);[\s\S]{0,200}_guiaAtualizar3D\(\)/.test(jogo));
check("3D: pool reutilizável (sem criar malha por quadro)", jogo.includes("g3.intencoesPool"));
check("3D: dispose3D chama _intencoesDispose3D", /function dispose3D[\s\S]*?_intencoesDispose3D\(\)/.test(jogo));
check("3D: _intencoesDispose3D zera o pool", /function _intencoesDispose3D[\s\S]*?g3\.intencoesPool = null/.test(jogo));

console.log("[9] preferência e atalho");
check("seletor no painel ⚙️", jogo.includes('id="cfg-intencao-sel"'));
check("seletor grava via _setIntencaoModo", /cfg-intencao-sel['"]\)\.onchange[\s\S]{0,120}_setIntencaoModo\(/.test(jogo));
const iT = jogo.indexOf("e.key === 't' || e.key === 'T'");
const iTfim = jogo.indexOf("return;", jogo.indexOf("proximoModo(_intencaoModo)", iT));
const blocoT = iT > 0 ? jogo.slice(iT, iTfim + 7) : "";
check("atalho T alterna", /proximoModo/.test(blocoT));
check("atalho T ignora auto-repeat", /e\.repeat/.test(blocoT));
check("atalho T ignora SELECT/INPUT/TEXTAREA/contentEditable",
      /'SELECT'/.test(blocoT) && /'INPUT'/.test(blocoT) && /'TEXTAREA'/.test(blocoT) && /isContentEditable/.test(blocoT));
check("atalho T ignora a mesa de teste", /test_mode/.test(blocoT));
const lang = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8");
for (const k of ["ui.menu.intencao", "ui.menu.intencao.off", "ui.menu.intencao.grupo", "ui.menu.intencao.todas",
                 "ui.menu.intencao_dica", "ui.ajuda.intencao",
                 "ui.intencao.tooltip.corpo", "ui.intencao.tooltip.distancia", "ui.intencao.tooltip.ameaca",
                 "ui.intencao.provavel", "ui.intencao.um_aliado", "ui.intencao.modo_toast"]) {
  const m = lang.match(new RegExp('"' + k.replace(/\./g, "\\.") + '":\\s*\\{([\\s\\S]*?)\\n  \\}'));
  check("chave " + k + " com pt e en", !!m && /"pt"/.test(m[1]) && /"en"/.test(m[1]));
}

console.log("[10] GS de verdade: guarda por rodada E vez, reset ao entrar na masmorra");
{
  let sock = null;
  const W = global.WebSocket;
  global.WebSocket = class {
    constructor() { this.readyState = 1; sock = this; }
    send() {}
    close() {}
  };
  global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  global.location = { search: "", protocol: "http:", host: "x" };
  const sT = global.setTimeout, cT = global.clearTimeout;
  global.setTimeout = () => 0; global.clearTimeout = () => {};
  const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
  GS.connect("ws://x", "Ana", "create");
  const chegar = msg => sock.onmessage({ data: JSON.stringify(msg) });
  const estado = (round, current_turn) => chegar({ type: "game_state", players: [], monsters: [],
    tiles: [[1]], rooms: [], explored: [], round, current_turn, phase: "playing" });
  const resp = (over) => Object.assign({ type: "intencoes_monstros", rodada: 2, vez: "a", itens: [item()] }, over || {});
  const ev = [];
  GS.on("intencoesMonstros", m => ev.push(m));

  estado(2, "a");
  chegar(resp());
  check("resposta da rodada e vez atuais: GS.intencoes() traz o item", GS.intencoes().length === 1);
  check("evento emitido com rodada e vez", ev.length === 1 && ev[0].vez === "a" && ev[0].rodada === 2);
  estado(2, null);
  check("fase dos monstros na MESMA rodada: some", GS.intencoes().length === 0);
  estado(2, "b");
  check("vez de outro herói na mesma rodada: some", GS.intencoes().length === 0);
  estado(2, "a");
  check("de volta à mesma vez (sem nova resposta): reaparece", GS.intencoes().length === 1);
  estado(3, "a");
  check("rodada seguinte: some", GS.intencoes().length === 0);
  chegar(resp({ rodada: 2 }));
  check("resposta da rodada anterior não substitui", GS.intencoes().length === 0);
  chegar(resp({ rodada: 3, vez: "b" }));
  check("resposta de outra vez não substitui", GS.intencoes().length === 0);
  chegar(resp({ rodada: 3, vez: undefined }));
  check("resposta sem vez não vale", GS.intencoes().length === 0);
  chegar(resp({ rodada: 3, itens: "lixo" }));
  check("itens não-lista vira lista vazia", Array.isArray(GS.intencoes()) && GS.intencoes().length === 0);
  chegar(resp({ rodada: 3 }));
  check("resposta válida da nova rodada entra", GS.intencoes().length === 1);
  chegar({ type: "enter_dungeon" });
  estado(3, "a");
  check("enter_dungeon zera as intenções", GS.intencoes().length === 0);
  global.WebSocket = W; global.setTimeout = sT; global.clearTimeout = cT;
}

console.log("[11] game.js: cauda do agrupamento, nome escapado, tooltip desligado, vez");
const fnPedir = jogo.slice(jogo.indexOf("function _intencoesPedirAgora"), jogo.indexOf("// Monstro cujo tooltip"));
check("agrupa com pedido de cauda (setTimeout), não descarta", /setTimeout\(/.test(fnPedir) && /_intencaoPedidoAtrasado/.test(fnPedir));
check("cauda é cancelada quando não pode pedir (modo off / fora da vez)",
      /if\(!_intencoesPodePedir\(\)\)\{[\s\S]{0,140}clearTimeout\(_intencaoPedidoAtrasado\)/.test(fnPedir));
const fnTip = jogo.slice(jogo.indexOf("function _intencaoLinhaTooltip"), jogo.indexOf("GS.on('intencoesMonstros'"));
check("tooltip: vazio no modo off", /_intencaoModo === 'off'/.test(fnTip));
check("tooltip: nome do jogador escapado", /_esc\(alvo\.name\)/.test(fnTip));
check("desenho exige GS.isMyTurn (propriedade, sem parênteses)",
      /function _intencoesVisiveis[\s\S]{0,300}if\(!GS\.isMyTurn\) return \[\];/.test(jogo) && !/GS\.isMyTurn\(\)/.test(jogo));
check("listener descarta pela mensagem inteira (rodada e vez)", jogo.includes("IntencaoMonstros.descartar(msg, GS.gameState)"));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
