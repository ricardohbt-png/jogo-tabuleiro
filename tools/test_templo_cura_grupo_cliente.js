// Plano da Cura Completa do Templo no cliente (espelho de GameRoom._plano_cura_grupo_templo).
// Roda da raiz: node tools/test_templo_cura_grupo_cliente.js
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

global.WebSocket = class { constructor() { this.readyState = 1; } send() {} close() {} };
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

const heroi = (id, falta, extra) => Object.assign(
  { id, name: id, class_id: "warrior", alive: true, connected: true, max_hp: 20, hp: 20 - falta, gold: 0, slot: 0 }, extra || {});
const estado = (herois, extra) => Object.assign({ players: herois }, extra || {});

console.log("[1] o exemplo do autor: 4 + 3 + 5 = 12 PV => 4 moedas");
let p = GS.planoCuraGrupoTemplo(estado([heroi("a", 4, { gold: 10 }), heroi("b", 3), heroi("c", 5)]), "a");
check("custo 4", p.custo === 4 && p.moedas === 4 && !p.parcial);
check("todos curados por inteiro", p.itens.length === 3 && p.itens.every(i => i.depois === 20));

console.log("[2] arredonda para baixo, mínimo de 1 moeda");
check("13 PV => 4", GS.planoCuraGrupoTemplo(estado([heroi("a", 13, { gold: 9 })]), "a").custo === 4);
check("2 PV => 1", GS.planoCuraGrupoTemplo(estado([heroi("a", 2, { gold: 9 })]), "a").custo === 1);
check("ninguém ferido => 0", GS.planoCuraGrupoTemplo(estado([heroi("a", 0, { gold: 9 })]), "a").custo === 0);

console.log("[3] morto e desconectado ficam de fora");
p = GS.planoCuraGrupoTemplo(estado([heroi("a", 3, { gold: 9 }), heroi("b", 3, { alive: false }), heroi("c", 3, { connected: false })]), "a");
check("só o 'a' entra", p.itens.length === 1 && p.itens[0].id === "a" && p.custo === 1);

console.log("[4] ouro insuficiente: parcial, o mais ferido primeiro");
p = GS.planoCuraGrupoTemplo(estado([heroi("a", 3, { gold: 2 }), heroi("b", 4), heroi("c", 5)]), "a");
const por = Object.fromEntries(p.itens.map(i => [i.id, i.depois]));
check("parcial: custo 4, paga 2", p.parcial && p.custo === 4 && p.moedas === 2);
check("o de 5 fica cheio, o de 4 recebe 1, o de 3 nada", por.c === 20 && por.b === 17 && por.a === undefined);

console.log("[5] ouro compartilhado do Solo soma o grupo");
p = GS.planoCuraGrupoTemplo(estado([heroi("a", 6, { gold: 1 }), heroi("b", 6, { gold: 4 })], { solo_grupo: true, ouro_compartilhado: true }), "a");
check("saldo = 5, custo 4, não parcial", p.saldo === 5 && p.custo === 4 && !p.parcial);
p = GS.planoCuraGrupoTemplo(estado([heroi("a", 6, { gold: 1 }), heroi("b", 6, { gold: 4 })], { solo_grupo: true }), "a");
check("sem a chave, só o ouro de quem paga", p.saldo === 1 && p.parcial);

console.log(`\n${"=".repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${"=".repeat(50)}`);
process.exit(FAIL ? 1 : 0);
