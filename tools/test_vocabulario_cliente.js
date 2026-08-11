// Filtro de nomes de catálogo — roda da raiz: node tools/test_vocabulario_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
eval(fs.readFileSync(path.join(raiz, "src", "lang", "strings.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "lang", "catalogo.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
const DICT = global.window.LANG_STRINGS;
const I18N = global.window.I18N;

console.log("\n[1] O catálogo entrou no dicionário");
check("catalogo.js fundiu em LANG_STRINGS", !!DICT["cat.monstro.goblin.nome"]);
check("o pt do goblin veio do catálogo", DICT["cat.monstro.goblin.nome"].pt === "Goblin");

console.log("\n[2] tem() diz se a chave existe");
check("tem() acha chave existente", I18N.tem("cat.monstro.goblin.nome") === true);
check("tem() nega chave inexistente", I18N.tem("cat.monstro.nao_existe.nome") === false);

// Traduções de teste, independentes do estado real do catalogo.js.
DICT["cat.monstro.goblin.nome"] = { pt: "Goblin", en: "Goblin Scout" };
DICT["cat.item.dagger.nome"]    = { pt: "Adaga",  en: "Dagger" };

console.log("\n[3] Em português o filtro não mexe em nada");
I18N.setLang("pt");
const emPt = I18N.traduzirNomes({ monsters: [{ type: "goblin", name: "Goblin" }] });
check("nome fica intacto em pt", emPt.monsters[0].name === "Goblin");

console.log("\n[4] Em inglês traduz monstro e item");
I18N.setLang("en");
const msg = I18N.traduzirNomes({
  monsters: [{ type: "goblin", name: "Goblin" }],
  players: [{ id: "id_7", name: "Thorin",
              bag: [{ id: "dagger", name: "Adaga" }],
              gear: { main_hand: { id: "dagger", name: "Adaga" } } }],
});
check("monstro traduzido pelo type", msg.monsters[0].name === "Goblin Scout");
check("item da bolsa traduzido pelo id", msg.players[0].bag[0].name === "Dagger");
check("item equipado (aninhado em objeto) traduzido",
      msg.players[0].gear.main_hand.name === "Dagger");
check("nome do JOGADOR não é tocado", msg.players[0].name === "Thorin");

console.log("\n[5] Conteúdo autoral sobrevive intacto");
const autoral = I18N.traduzirNomes({
  monsters: [{ type: "meu_monstro_custom", name: "Guardião de Pedra" }],
  chests: [{ items: [{ id: "meu_item_custom", name: "Lâmina do Autor" }] }],
});
check("monstro do editor mantém o nome", autoral.monsters[0].name === "Guardião de Pedra");
check("item do editor mantém o nome", autoral.chests[0].items[0].name === "Lâmina do Autor");

console.log("\n[6] Campo 'nome' (catálogos que usam português) também é traduzido");
DICT["cat.guilda.brutalidade.nome"] = { pt: "Brutalidade", en: "Brutality" };
const guilda = I18N.traduzirNomes({ guild: [{ id: "brutalidade", nome: "Brutalidade" }] });
check("campo nome traduzido", guilda.guild[0].nome === "Brutality");

console.log("\n[7] Ciclos não travam o filtro");
const ciclo = { monsters: [{ type: "goblin", name: "Goblin" }] };
ciclo.eu = ciclo;
let travou = false;
try { I18N.traduzirNomes(ciclo); } catch (e) { travou = true; }
check("estrutura com referência circular não estoura", !travou);

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
