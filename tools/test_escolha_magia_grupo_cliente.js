// Escolha de magia na subida de nível com grupo — cliente. Roda da raiz:
//   node tools/test_escolha_magia_grupo_cliente.js
// A resposta vai para o herói do AVISO (não o do foco), o foco volta à origem
// depois de uma fila de avisos, e o painel diz de quem é a escolha.
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
GS.connect("ws://x", "Ana", "create");
const chega = m => sock.onmessage({ data: JSON.stringify(m) });

chega({ type: "lobby_state", code: "ABCD", host: "c", players: [
  { id: "c", name: "Ana", class_id: "warrior" },
  { id: "l", name: "Lewis", class_id: "cleric", controlador: "c" },
  { id: "m", name: "Pedro", class_id: "mage", controlador: "c" } ] });
const estado = vez => ({ type: "game_state", current_turn: vez, players: [
  { id: "c", name: "Ana", pos: [1, 1], alive: true },
  { id: "l", name: "Lewis", pos: [2, 1], alive: true, controlador: "c" },
  { id: "m", name: "Pedro", pos: [3, 1], alive: true, controlador: "c" } ],
  monsters: [], tiles: [[1]], explored: [], rooms: [] });
chega(estado("c"));

console.log("\n[1] A resposta vai para o herói do aviso");
enviados.length = 0;
GS.escolherMagiaNivel("medo", "l");
check("com o herói do aviso explícito", enviados[0] && enviados[0].heroi === "l");
GS.focarHeroi("m");
enviados.length = 0;
GS.escolherMagiaNivel("medo", "l");
check("mesmo com o foco em outro herói", enviados[0] && enviados[0].heroi === "l");
enviados.length = 0;
GS.escolherMagiaNivel("medo", "x");
check("herói que não é meu não é nomeado (mesa de teste do Mestre)",
      enviados[0] && enviados[0].heroi !== "x");
GS.focarHeroi("c");

console.log("\n[2] Fila de avisos: o foco volta à ORIGEM no fim");
chega({ type: "spell_pick_prompt", heroi: "l", heroi_nome: "Lewis", circulo: "primeiro", count: 1, opcoes: [] });
check("aviso do clérigo foca o clérigo", GS.myPid === "l");
GS.escolherMagiaNivel("medo", "l");
// O servidor manda o aviso do próximo herói ANTES do game_state.
chega({ type: "spell_pick_prompt", heroi: "m", heroi_nome: "Pedro", circulo: "primeiro", count: 1, opcoes: [] });
check("aviso do mago foca o mago", GS.myPid === "m");
chega(estado("c"));
check("o game_state não devolve o foco com o mago por responder", GS.myPid === "m");
GS.escolherMagiaNivel("sono", "m");
chega(estado("c"));
check("respondido o último, o foco volta a Ana (a origem), não ao clérigo", GS.myPid === "c");

console.log("\n[2b] Na cidade o foco também volta (city_state)");
const cidade = () => ({ type: "city_state", code: "ABCD", players: [
  { id: "c", name: "Ana" }, { id: "l", name: "Lewis", controlador: "c" },
  { id: "m", name: "Pedro", controlador: "c" } ] });
chega(cidade());
chega({ type: "spell_pick_prompt", heroi: "l", heroi_nome: "Lewis", circulo: "primeiro", count: 1, opcoes: [] });
GS.escolherMagiaNivel("medo", "l");
chega({ type: "spell_pick_prompt", heroi: "m", heroi_nome: "Pedro", circulo: "primeiro", count: 1, opcoes: [] });
chega(cidade());
check("com o mago por responder, fica no mago", GS.myPid === "m");
GS.escolherMagiaNivel("sono", "m");
chega(cidade());
check("respondido, volta a Ana", GS.myPid === "c");

console.log("\n[2c] Mesa de teste: o Mestre escolhe pelo herói-teste");
chega({ type: "game_state", test_mode: true, master_pid: "c", current_turn: null, players: [
  { id: "c", name: "Ana", pos: [1, 1], alive: true },
  { id: "test_hero_mage", name: "Pedro", pos: [2, 1], alive: true, test_hero: true } ],
  monsters: [], tiles: [[1]], explored: [], rooms: [] });
enviados.length = 0;
GS.escolherMagiaNivel("sono", "test_hero_mage");
check("vai por teste_escolher_magia_nivel com o herói-teste",
      enviados[0] && enviados[0].type === "teste_escolher_magia_nivel"
      && enviados[0].hero_id === "test_hero_mage" && enviados[0].magia_id === "sono");
chega(estado("c"));
enviados.length = 0;
GS.escolherMagiaNivel("sono", "x");
check("fora da mesa de teste, herói alheio segue pelo caminho comum",
      enviados[0] && enviados[0].type === "escolher_magia_nivel");

console.log("\n[3] Painel diz de quem é a escolha");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("o painel guarda o herói do aviso", game.includes("el.dataset.heroi = msg.heroi || '';"));
check("e responde por ele", game.includes("GS.escolherMagiaNivel(id, (el && el.dataset.heroi) || undefined);"));
check("o título usa o nome do herói", game.includes("t('ui.magia.subiu_de_nivel_heroi', {nome: _esc(msg.heroi_nome)})"));
const lang = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8");
check("a chave existe em pt e en", /"ui\.magia\.subiu_de_nivel_heroi": \{\s*"en": "\{nome\}[^"]*",\s*"pt": "\{nome\}/.test(lang));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
