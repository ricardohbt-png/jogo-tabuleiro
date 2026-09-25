// Prévia de acerto no cliente — roda da raiz: node tools/test_previsao_ataque_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// WebSocket falso: guarda o que o cliente enviou e deixa o teste entregar mensagens.
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

GS.connect("ws://x", "Thorin", "create");
const chegar = msg => sock.onmessage({ data: JSON.stringify(msg) });
const pedidos = () => enviados.filter(m => m.type === "prever_ataque");

console.log("\n[1] Pedido deduplicado e resposta no cache");
GS.pedirPrevisaoAtaque("m1", [3, 4]);
GS.pedirPrevisaoAtaque("m1", [3, 4]);
check("dois hovers no mesmo alvo pedem uma vez só", pedidos().length === 1);
const p0 = pedidos()[0];
check("o pedido leva alvo, casa e chave", p0.target_id === "m1" && p0.target_pos.join() === "3,4" && !!p0.chave);
check("sem resposta ainda, a prévia é null", GS.previsaoAtaque("m1", [3, 4]) === null);
let evento = null;
GS.on("previsaoAtaque", m => { evento = m; });
chegar({ type: "previsao_ataque", target_id: "m1", chave: p0.chave, chance: 65,
         dano_dado: "1d8", dano_fixo: 3, golpe_mult: 1, furtivo_d4: 0 });
check("a resposta entra no cache", GS.previsaoAtaque("m1", [3, 4])?.chance === 65);
check("e avisa o renderer", evento && evento.chance === 65);
GS.pedirPrevisaoAtaque("m1", [3, 4]);
check("com resposta em cache, não pede de novo", pedidos().length === 1);

console.log("\n[2] Outra casa do mesmo monstro é outro pedido (ponto vulnerável)");
GS.pedirPrevisaoAtaque("m1", [4, 4]);
check("casa diferente pede de novo", pedidos().length === 2);

console.log("\n[3] game_state invalida tudo");
chegar({ type: "game_state", players: [], monsters: [], tiles: [[0]], rooms: [], explored: [], round: 2 });
check("o cache some", GS.previsaoAtaque("m1", [3, 4]) === null);
GS.pedirPrevisaoAtaque("m1", [3, 4]);
check("e o próximo hover pede de novo", pedidos().length === 3);

console.log("\n[4] Dano médio");
check("1d8+3 → ~8", GS.danoMedioPrevisao({ dano_dado: "1d8", dano_fixo: 3, golpe_mult: 1 }) === 8);
check("Golpe Devastador ×1,5 no dado", GS.danoMedioPrevisao({ dano_dado: "2d6", dano_fixo: 0, golpe_mult: 1.5 }) === 11);
check("furtivo soma 2,5 por d4", GS.danoMedioPrevisao({ dano_dado: "1d4", dano_fixo: 0, golpe_mult: 1, furtivo_d4: 2 }) === 8);
check("desarmado usa o número puro", GS.danoMedioPrevisao({ dano_dado: "1", dano_fixo: 1, golpe_mult: 1 }) === 2);
check("piso de 1, como no servidor", GS.danoMedioPrevisao({ dano_dado: "1", dano_fixo: -5, golpe_mult: 1 }) === 1);

console.log("\n[5] Fiação no game.js");
const jogo = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("o tooltip 2D e o 3D chamam a prévia",
      (jogo.match(/(?<!function )_linhaPrevisaoAtaque\(monster, tx, ty, myP\)/g) || []).length === 2);
check("um único ouvinte de previsaoAtaque (GS.on substitui)",
      (jogo.match(/GS\.on\('previsaoAtaque'/g) || []).length === 1);
const dic = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8");
for (const k of ["ui.previsao.chance", "ui.previsao.dano", "ui.previsao.vantagem",
                 "ui.previsao.desvantagem", "ui.previsao.calculando", "ui.previsao.dica"])
  check(`chave ${k} existe`, dic.includes(`"${k}"`));

console.log(`\n${"=".repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${"=".repeat(50)}`);
process.exit(FAIL ? 1 : 0);
