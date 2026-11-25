// Catálogo da Guilda vindo no game_state: o cliente o guarda e as técnicas concedidas por itens
// (ex.: Ataque Giratório da Lâmina do Vento) voltam a aparecer sem ter passado pela cidade.
// Roda da raiz: node tools/test_guild_catalog_cliente.js
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (n, c) => { if (c) { PASS++; console.log("  ✅ " + n); } else { FAIL++; console.log("  ❌ " + n); } };

let sock = null;
global.WebSocket = class { constructor() { this.readyState = 1; sock = this; } send() {} close() {} };
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
global.setTimeout = () => 0; global.clearTimeout = () => {};
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.connect("ws://x", "Ana", "create");
const chegar = m => sock.onmessage({ data: JSON.stringify(m) });
const giro = { id: "tecnica_ataque_giratorio", categoria: "tecnica", classe: null, nome: "Ataque Giratório", custo_fome: 4, custo_sede: 4 };
const exclusiva = { id: "x_mago", categoria: "tecnica", classe: ["mage"], nome: "Só do Mago" };
const base = (extra) => Object.assign({ type: "game_state", players: [], monsters: [], explored: [], round: 1, phase: "playing" }, extra);

check("sem catálogo, nada para a classe", GS.guildCatalogFor("warrior").length === 0);
chegar(base({ guild_catalog: [giro, exclusiva] }));
check("game_state guarda o catálogo (sem ter passado pela cidade)", GS.guildCatalogFor("warrior").some(i => i.id === "tecnica_ataque_giratorio"));
check("o filtro por classe continua valendo", !GS.guildCatalogFor("warrior").some(i => i.id === "x_mago") && GS.guildCatalogFor("mage").some(i => i.id === "x_mago"));

const lamina = { id: "lamina_do_vento", granted_ability: "guild_tecnica_ataque_giratorio" };
check("técnica concedida pelo item resolve no catálogo",
  GS.tecnicasConcedidasPorItem({ gear: { weapon: lamina } }).every(t => GS.guildCatalogFor("warrior").some(i => i.id === t)) &&
  GS.tecnicasConcedidasPorItem({ gear: { weapon: lamina } }).length === 1);

chegar(base({ round: 2, diferidos: ["guild_catalog"], guild_catalog: undefined }));
check("envio seguinte (campo omitido) mantém o catálogo", GS.guildCatalogFor("warrior").length === 1);
chegar(base({ guild_catalog: [] }));
check("catálogo vazio não apaga o que já havia", GS.guildCatalogFor("warrior").length === 1);

const srv = fs.readFileSync(path.join(raiz, "server.py"), "utf8");
check("servidor manda o catálogo no game_state", /"guild_catalog": list\(GUILD_CATALOG\.values\(\)\)/.test(srv));
console.log(`\n=== ${PASS} passaram, ${FAIL} falharam ===`);
process.exit(FAIL ? 1 : 0);
