// Solo com grupo — cliente. Roda da raiz:
//   node tools/test_solo_grupo_cliente.js
// `myPid` é o herói EM FOCO; `connPid` é a conexão. O foco pula sozinho para
// o herói meu que está na vez, e toda mensagem leva `heroi` quando há grupo.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

const enviados = [];
let sock = null;
const guardado = {};
global.WebSocket = class {
  constructor() { this.readyState = 1; sock = this; }
  send(s) { enviados.push(JSON.parse(s)); }
  close() {}
};
global.window = {};
global.localStorage = { getItem: k => guardado[k] ?? null,
                        setItem: (k, v) => { guardado[k] = v; }, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

const focos = [];
GS.on("focoHeroi", ev => focos.push(ev));

console.log("\n[1] Lobby: aprende a conexão e os heróis dela");
chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "warrior" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" },
  { id: "o", name: "Bia", class_id: "rogue" } ] });
check("connPid = principal", GS.connPid === "c");
check("myPid começa no principal", GS.myPid === "c");
check("meusHerois = principal + extra", JSON.stringify(GS.meusHerois.slice().sort()) === '["c","m"]');
check("temGrupo", GS.temGrupo === true);
check("ehMeuHeroi: extra sim, alheio não", GS.ehMeuHeroi("m") && !GS.ehMeuHeroi("o"));
check("cascaDaClasse('mage') = extra", GS.cascaDaClasse("mage") === "m");
check("sessão grava a CONEXÃO", JSON.parse(guardado.lfh_session).pid === "c");

console.log("\n[2] Foco segue a vez");
const estado = vez => ({ type: "game_state", current_turn: vez, players: [
  { id: "c", name: "Ana", pos: [1, 1], alive: true },
  { id: "m", name: "Pedro", pos: [2, 1], alive: true, controlador: "c" } ],
  monsters: [], tiles: [[1]], explored: [], rooms: [] });
chega(estado("m"));
check("vez do extra → foco nele", GS.myPid === "m");
check("isMyTurn verdadeiro", GS.isMyTurn === true);
check("evento focoHeroi automático", focos.length === 1 && focos[0].pid === "m" && focos[0].auto === true);
chega(estado("m"));
check("mesmo turno não repete o evento", focos.length === 1);

console.log("\n[3] Troca manual de foco");
check("focarHeroi recusa pid alheio", GS.focarHeroi("o") === false && GS.myPid === "m");
check("focarHeroi no principal", GS.focarHeroi("c") === true && GS.myPid === "c");
check("fora da vez dele → isMyTurn falso", GS.isMyTurn === false);
check("evento manual", focos[focos.length - 1].auto === false);
chega(estado("m"));
check("um novo game_state do mesmo turno NÃO rouba o foco manual", GS.myPid === "c");

console.log("\n[4] Mensagens levam o herói em foco");
enviados.length = 0;
GS.endTurn();
check("end_turn leva heroi = foco", enviados[0] && enviados[0].heroi === "c");
GS.setKnownSpells(["a", "b"], "m");
check("setKnownSpells com herói explícito", enviados[1] && enviados[1].heroi === "m");
GS.selectParty(["warrior", "mage"]);
check("selectParty manda a lista", enviados[2] && enviados[2].type === "select_party"
      && enviados[2].classes.length === 2);

console.log("\n[4b] Avisos com resposta focam o herói a que se destinam");
GS.focarHeroi("c");
focos.length = 0;
chega({ type: "trap_result", heroi: "m", nome: "x" });
check("mensagem informativa NÃO troca o foco", GS.myPid === "c" && focos.length === 0);
chega({ type: "spell_pick_prompt", heroi: "o", circulo: 1, count: 1, opcoes: [] });
check("aviso para pid que não é meu: nada", GS.myPid === "c" && focos.length === 0);
chega({ type: "spell_pick_prompt", heroi: "m", circulo: 1, count: 1, opcoes: [] });
check("spell_pick_prompt do extra → foco nele", GS.myPid === "m");
check("evento focoHeroi manual", focos.length === 1 && focos[0].pid === "m" && focos[0].auto === false);
chega({ type: "sorte_reacao", heroi: "m" });
check("já em foco: sem evento repetido", focos.length === 1);
check("souAnfitriao pela conexão com extra em foco", GS.souAnfitriao("c") === true && GS.souAnfitriao("m") === false);
check("souAnfitriao(null) falso", GS.souAnfitriao(null) === false);
GS.focarHeroi("c");

console.log("\n[4c] Prompt do PRINCIPAL (heroi = connPid) também foca; foco limpa o armado");
GS.focarHeroi("m");
chega({ type: "sorte_reacao", heroi: GS.connPid });
check("prompt com heroi = principal → foco no principal", GS.myPid === "c");
GS.toggleWarriorSkill("mira_certeira");
check("habilidade armada no herói A", GS.getWarriorSelected().length === 1);
GS.focarHeroi("m");
check("trocar o foco limpa o que estava armado", GS.getWarriorSelected().length === 0);
GS.focarHeroi("c");

console.log("\n[4d] Respondido o aviso, o foco volta a quem estava");
// Turno do principal ("c"); a magia ao subir de nível chega para o extra.
chega(estado("c"));
check("vez do principal, foco nele", GS.myPid === "c");
chega({ type: "spell_pick_prompt", heroi: "m", circulo: 1, count: 2, opcoes: [] });
check("aviso puxa o foco para o extra", GS.myPid === "m");
chega(estado("c"));
check("game_state antes da resposta NÃO devolve o foco", GS.myPid === "m");
enviados.length = 0;
GS.escolherMagiaNivel("x");
check("resposta sai em nome do extra", enviados[0] && enviados[0].heroi === "m");
chega({ type: "spell_pick_prompt", heroi: "m", circulo: 1, count: 1, opcoes: [] });
chega(estado("c"));
check("2º aviso da fila: o foco continua no extra", GS.myPid === "m");
GS.escolherMagiaNivel("y");
chega({ type: "error", msg: "magia inválida" });
chega(estado("c"));
check("resposta recusada: o foco continua no extra", GS.myPid === "m");
GS.escolherMagiaNivel("z");
focos.length = 0;
chega(estado("c"));
check("respondido o último: o foco volta ao principal", GS.myPid === "c");
check("evento focoHeroi de volta", focos.length === 1 && focos[0].pid === "c" && focos[0].volta === true);
check("e isMyTurn volta a valer", GS.isMyTurn === true);
// Trocar à mão no meio cancela a volta.
chega({ type: "sorte_reacao", heroi: "m" });
GS.focarHeroi("c"); GS.focarHeroi("m");
GS.responderSorteReacao(false);
chega(estado("c"));
check("troca manual no meio: o foco fica onde o jogador pôs", GS.myPid === "m");
GS.focarHeroi("c");

console.log("\n[5] Sem grupo, nada muda");
GS.connect("ws://x", "Leo", "create");
chega({ type: "lobby_state", code: "EFGH", host: "z", players: [{ id: "z", name: "Leo" }] });
enviados.length = 0;
GS.endTurn();
check("sem grupo: mensagem sem heroi", enviados[0] && enviados[0].heroi === undefined);
check("sem grupo: temGrupo falso", GS.temGrupo === false);
check("sem grupo: souAnfitriao usa myPid", GS.souAnfitriao("z") === true && GS.souAnfitriao("x") === false);

console.log("\n[6] game.js: XP de todos os meus heróis e destaque da vez");
{
  const GAME = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
  const extrair = nome => {
    const ini = GAME.indexOf("\nfunction " + nome + "(");
    if (ini < 0) throw new Error("função não encontrada: " + nome);
    return GAME.slice(ini, GAME.indexOf("\n}", ini) + 2);
  };
  const xpConst = GAME.match(/const XP_POR_NIVEL_CLIENTE = (\d+);/);
  const srv = fs.readFileSync(path.join(raiz, "server.py"), "utf8").match(/^XP_POR_NIVEL = (\d+)/m);
  check("XP_POR_NIVEL_CLIENTE espelha o servidor", xpConst && srv && xpConst[1] === srv[1]);
  const meus = ["c", "m"];
  const G = { ehMeuHeroi: id => meus.includes(id) };
  const f = new Function("GS", "t", "XP_POR_NIVEL_CLIENTE",
    ["_xpAcumulado", "_ganhosXpMeusHerois", "_textoGanhosXp", "_heroiMeuNaVez"].map(extrair).join("\n")
    + "\nreturn { _ganhosXpMeusHerois, _textoGanhosXp, _heroiMeuNaVez };")(
    G, (k, p) => k + JSON.stringify(p || {}), Number(xpConst[1]));
  const antes = new Map([["c", { xp: 290, level: 1 }], ["m", { xp: 10, level: 2 }], ["o", { xp: 0, level: 1 }]]);
  const st = { players: [
    { id: "c", name: "Ana", xp: 10, level: 2 },     // subiu: 290 → 300 (nível 2) + 10 = +20
    { id: "m", name: "Pedro", xp: 30, level: 2 },   // +20
    { id: "o", name: "Bia", xp: 20, level: 1 } ] }; // alheio
  const g = f._ganhosXpMeusHerois(antes, st);
  check("ganho conta a subida de nível (não some no xp zerado)", g.find(x => x.nome === "Ana")?.xp === 20);
  check("herói extra também ganha", g.find(x => x.nome === "Pedro")?.xp === 20);
  check("herói alheio fica de fora", !g.some(x => x.nome === "Bia"));
  check("ganhos iguais: uma linha 'para cada'", f._textoGanhosXp(g).startsWith("ui.hud.xp_cada_heroi")
        && f._textoGanhosXp(g).includes('"n":2'));
  check("um herói só: o texto de sempre", f._textoGanhosXp([{ nome: "Ana", xp: 7 }]) === "✨ +7 XP");
  check("ganhos diferentes: por herói", f._textoGanhosXp([{ nome: "Ana", xp: 7 }, { nome: "Pedro", xp: 3 }]) === "✨ Ana +7 · Pedro +3");
  check("herói meu na vez", f._heroiMeuNaVez({ current_turn: "m" }) === "m");
  check("Último Esforço também é vez", f._heroiMeuNaVez({ current_turn: "x", last_stand_pid: "c" }) === "c");
  check("vez de outro: null", f._heroiMeuNaVez({ current_turn: "o" }) === null);
}

console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
