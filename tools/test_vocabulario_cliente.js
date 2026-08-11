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

console.log("\n[9] Descrições");
DICT["cat.guilda.brutalidade.nome"] = { pt: "Brutalidade", en: "Brutality" };
DICT["cat.guilda.brutalidade.desc"] = { pt: "+2 de dano", en: "+2 damage" };
DICT["cat.classe.warrior.nome"]     = { pt: "Guerreiro", en: "Warrior" };
DICT["cat.classe.warrior.desc"]     = { pt: "Tanque", en: "Tank" };
I18N.setLang("en");
const comDesc = I18N.traduzirNomes({
  guild: [{ id: "brutalidade", nome: "Brutalidade", desc: "+2 de dano" }],
  outro: [{ id: "brutalidade", nome: "Brutalidade", descricao: "+2 de dano" }],
});
check("troca o campo desc", comDesc.guild[0].desc === "+2 damage");
check("troca o campo descricao", comDesc.outro[0].descricao === "+2 damage");
check("o nome continua sendo trocado", comDesc.guild[0].nome === "Brutality");
const semDesc = I18N.traduzirNomes({ a: [{ id: "dagger", name: "Adaga", desc: "texto autoral" }] });
check("sem chave .desc no dicionário, a descrição fica intacta",
      semDesc.a[0].desc === "texto autoral");

console.log("\n[10] Id na chave do dicionário pai");
const porChave = I18N.traduzirNomes({
  classes: { warrior: { name: "Guerreiro", desc: "Tanque", color: "#f00" } },
});
check("dicionário chaveado por id traduz o nome",
      porChave.classes.warrior.name === "Warrior");
check("dicionário chaveado por id traduz a descrição",
      porChave.classes.warrior.desc === "Tank");
check("campo que não é id não vira tradução por acidente",
      porChave.classes.warrior.color === "#f00");

console.log("\n[11] aplicarCatalogo — catálogos estáticos");
const estatico = { bola_fogo: { id: "bola_fogo", nome: "Bola de Fogo", descricao: "<b>HTML</b>" } };
DICT["cat.magia.bola_fogo.nome"] = { pt: "Bola de Fogo", en: "Fireball" };
DICT["cat.magia.bola_fogo.desc"] = { pt: "Frase curta", en: "Short line" };
I18N.aplicarCatalogo(estatico, true);
check("aplicarCatalogo(true) troca o nome", estatico.bola_fogo.nome === "Fireball");
check("aplicarCatalogo(true) NÃO toca na descrição do cliente",
      estatico.bola_fogo.descricao === "<b>HTML</b>");
// A volta ao português é o motivo de aplicarCatalogo não ter a saída antecipada.
I18N.setLang("pt");
I18N.aplicarCatalogo(estatico, true);
check("aplicar em português restaura o original", estatico.bola_fogo.nome === "Bola de Fogo");
I18N.setLang("en");
I18N.aplicarCatalogo(estatico, true);
check("aplicar de novo em inglês volta a traduzir", estatico.bola_fogo.nome === "Fireball");

console.log("\n[8] A fiação com o gameState existe");
// Checagem estática: o teste não consegue carregar game.js nem gameState.js
// (o primeiro monta o DOM inteiro no load), então verificamos a fiação no fonte.
const gamejs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const gs = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
check("gameState expõe setMessageFilter", /setMessageFilter/.test(gs));
check("o filtro é aplicado antes do _handle",
      /_messageFilter[\s\S]{0,400}?_handle\(/.test(gs));
check("game.js registra I18N.traduzirNomes como filtro",
      /GS\.setMessageFilter\(\s*I18N\.traduzirNomes\s*\)/.test(gamejs));
check("game.js aplica o catálogo nos 3 estáticos",
      /aplicarCatalogo\(\s*GRIMORIO_CLIENT/.test(gamejs)
      && /aplicarCatalogo\(\s*ARMADILHAS_LUCCAS/.test(gamejs)
      && /aplicarCatalogo\(\s*GS\.CATALOGO_ITENS/.test(gamejs));
check("a conversão do inventário prefere o nome do servidor",
      /\{\s*\.\.\.cat,\s*nome:\s*it\.name\s*\|\|\s*cat\.nome\s*\}/.test(gamejs));

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
