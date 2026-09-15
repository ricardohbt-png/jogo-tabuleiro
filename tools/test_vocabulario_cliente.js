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
eval(fs.readFileSync(path.join(raiz, "src", "lang", "composto.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8"));
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
// Id SINTETICO, que nunca vai existir no catalogo. A versao anterior usava
// "dagger" e ficou vermelha sozinha quando a adaga ganhou uma cat.item.dagger.desc:
// um teste de REGRA nao pode depender do conteudo que a regra mede.
const semDesc = I18N.traduzirNomes({ a: [{ id: "__item_sem_chave__", name: "Adaga", desc: "texto autoral" }] });
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
// `custo` é campo só do GRIMORIO_CLIENT: traduz por ui.magia.<id>.custo (sem par cat.*),
// e só quando soNome=false — como as descrições.
const comCusto = { x: { id: "x_teste", nome: "X", custo: "🍖-1 por rodada" } };
DICT["cat.magia.x_teste.nome"] = { pt: "X", en: "X" };
DICT["ui.magia.x_teste.custo"] = { pt: "🍖-1 por rodada", en: "🍖-1 per round" };
I18N.aplicarCatalogo(comCusto, true);
check("aplicarCatalogo(true) não toca no custo", comCusto.x.custo === "🍖-1 por rodada");
I18N.aplicarCatalogo(comCusto, false);
check("aplicarCatalogo(false) traduz o custo por ui.magia.<id>.custo", comCusto.x.custo === "🍖-1 per round");
I18N.setLang("pt"); I18N.aplicarCatalogo(comCusto, false); I18N.setLang("en");
check("a volta ao português restaura o custo", comCusto.x.custo === "🍖-1 por rodada");
check("as 3 magias com custo próprio têm a chave", ["tempestade_ciclones", "olhar_petrificante", "metamorfose"]
      .every(id => DICT["ui.magia." + id + ".custo"] && DICT["ui.magia." + id + ".custo"].en));

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

console.log("\n[N] Nomes compostos no cliente (etapa 4c)");
I18N.setLang("en");

// Sufixo de corroído: o filtro trocaria o nome pelo do catálogo e comeria o
// "(corroído)". O sufixo mora num CAMPO, então sobrevive à troca.
const corroido = { id: "alabarda_prata", name: "Alabarda de Prata", corrosao_inicial: 1 };
I18N.traduzirNomes(corroido);
check("item corroído mantém o sufixo em inglês",
      corroido.name === "Silver Halberd (corroded)");

// Munição: a contagem sai do ammo_count, não do nome.
const municao = { id: "virotes", name: "Virotes (×10)", ammo_count: 7 };
I18N.traduzirNomes(municao);
check("munição compõe a contagem", municao.name === "Bolts (×7)");

// Instrumento: id único por combinação, que NÃO existe no catálogo — sem o
// compositor, ficaria em português na bolsa.
//
// Esta tabela é A MESMA da seção [7] de tools/test_narracao.py, de propósito: a
// composição tem DUAS implementações (servidor e cliente) e nada além destes
// dois testes impede que elas divirjam. Mexeu numa, confira a outra.
const ARRANJOS = [
  ["harpa",  "padrao",   "humana", "nenhum", "Standard Harp"],
  ["harpa",  "velho",    "humana", "nenhum", "Old Harp"],
  ["tambor", "velho",    "humana", "nenhum", "Old War Drum"],
  ["harpa",  "rustico",  "elfica", "nenhum", "Rustic Elven Harp"],
  ["harpa",  "padrao",   "humana", "runico", "Standard Runic Harp"],
  ["harpa",  "refinado", "elfica", "runico", "Legendary Elven Harp"],
  ["alaude", "refinado", "ana",    "runico", "Legendary Dwarven Lute"],
];
for (const [base, qualidade, origem, encantamento, esperado] of ARRANJOS) {
  const inst = { id: "instrumento_" + base + "_" + qualidade, tipo_item: "instrumento",
                 name: "(português)", base, qualidade, origem, encantamento };
  I18N.traduzirNomes(inst);
  check(`instrumento ${base}/${qualidade}/${origem}/${encantamento}`,
        inst.name === esperado);
}

// Item autoral com sufixo: sem chave de catálogo, mas o sufixo ainda vale.
const autoralCorr = { id: "espada_do_autor", name: "Espada do Autor", corrosao_inicial: 1 };
I18N.traduzirNomes(autoralCorr);
check("item autoral corroído mantém nome autoral + sufixo",
      autoralCorr.name === "Espada do Autor (corroded)");

// Em português nada muda — o filtro sai cedo.
I18N.setLang("pt");
const corroidoPt = { id: "alabarda_prata", name: "Alabarda de Prata", corrosao_inicial: 1 };
I18N.traduzirNomes(corroidoPt);
check("em português o filtro não mexe", corroidoPt.name === "Alabarda de Prata");


console.log("\n[L] O t() do cliente junta listas");
DICT["teste.lista"] = { pt: "Controla {quem}.", en: "Controls {quem}." };
I18N.setLang("pt");
check("dois itens em pt",
      I18N.t("teste.lista", { quem: ["os animados", "o prisioneiro"] })
      === "Controla os animados e o prisioneiro.");
check("tres itens em pt",
      I18N.t("teste.lista", { quem: ["a", "b", "c"] }) === "Controla a, b e c.");
I18N.setLang("en");
check("dois itens em en",
      I18N.t("teste.lista", { quem: ["the minions", "the prisoner"] })
      === "Controls the minions and the prisoner.");
check("tres itens em en",
      I18N.t("teste.lista", { quem: ["a", "b", "c"] }) === "Controls a, b and c.");
check("lista vazia nao deixa separador solto",
      I18N.t("teste.lista", { quem: [] }) === "Controls .");
I18N.setLang("pt");

console.log("");
console.log("[U] A chave ui.* tem prioridade sobre a cat.* do servidor");
DICT["cat.magia.bola_fogo.nome"] = { pt: "Bola de Fogo", en: "Fireball" };
DICT["cat.magia.bola_fogo.desc"] = { pt: "Frase curta do servidor",
                                     en: "Server short line" };
DICT["ui.magia.bola_fogo.desc"]  = { pt: "<b>Card rico do cliente</b>",
                                     en: "<b>Rich client card</b>" };
const cliente = { bola_fogo: { id: "bola_fogo", nome: "Bola de Fogo",
                               descricao: "<b>Card rico do cliente</b>" } };
I18N.setLang("en");
I18N.aplicarCatalogo(cliente, false);
check("a descricao usa a chave ui.*, nao a cat.*",
      cliente.bola_fogo.descricao === "<b>Rich client card</b>");
check("o nome continua vindo da cat.* quando nao ha ui.*",
      cliente.bola_fogo.nome === "Fireball");
I18N.setLang("pt");
I18N.aplicarCatalogo(cliente, false);
check("voltar ao portugues restaura o card do cliente",
      cliente.bola_fogo.descricao === "<b>Card rico do cliente</b>");

// Sem chave ui.*, a cat.* ainda vale — e e isso que torna seguro trocar as
// chamadas para soNome=false ANTES de escrever todas as chaves.
// Id SINTETICO de proposito: desde a Task 5 as 27 magias reais tem chave
// ui.magia.<id>.desc, entao usar uma delas aqui testaria o contrario do que a
// secao diz. Este id nao existe em catalogo nenhum.
DICT["cat.magia.magia_so_no_servidor.desc"] = { pt: "Curta", en: "Short" };
const semUi = { relampago: { id: "magia_so_no_servidor", nome: "Relampago",
                             descricao: "<b>Card sem chave ui</b>" } };
I18N.setLang("en");
I18N.aplicarCatalogo(semUi, false);
check("sem ui.*, cai na cat.* (comportamento antigo)",
      semUi.relampago.descricao === "Short");
I18N.setLang("pt");

// ─────────────────────────────────────────────────────────────────────────────
// O _CSD (tela de seleção) não passa pelo aplicarCatalogo: as skills não têm
// família cat.* que estabeleça a base, e usar id de magia nelas colidiria com o
// GRIMORIO_CLIENT. Ele resolve por _rotulo, que monta a chave em runtime
// (prefixo + '.' + id) — então o que dá para provar sem navegador é COBERTURA:
// todo id que o _CSD leva à tela tem chave, com pt e en.
console.log("\n[S] Cobertura das chaves ui.selecao.* do _CSD");
const gameJs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const iCsd = gameJs.indexOf("const _CSD");
let prof = 0, kCsd = gameJs.indexOf("{", iCsd);
const aCsd = kCsd;
for (; kCsd < gameJs.length; kCsd++) {
  if (gameJs[kCsd] === "{") prof++;
  else if (gameJs[kCsd] === "}" && --prof === 0) break;
}
const blocoCsd = gameJs.slice(aCsd, kCsd + 1);
const classes = [...blocoCsd.matchAll(/\n {2}(\w+):\{/g)].map(m => m[1]);
const skills = [...blocoCsd.matchAll(/id:'(\w+)'/g)].map(m => m[1]);

check("o _CSD tem as 6 classes", classes.length === 6);
check("o _CSD tem 24 skills com id", skills.length === 24);
check("nenhum texto solto sobrou no _CSD",
      !/(?:name|nome|cls|desc):\s*'/.test(blocoCsd));

const semChave = [];
const semEn = [];
for (const cid of classes)
  for (const p of ["ui.selecao.classe", "ui.selecao.classe.cls", "ui.selecao.classe.desc"])
    (DICT[`${p}.${cid}`] ? (DICT[`${p}.${cid}`].en ? null : semEn) : semChave)
      ?.push(`${p}.${cid}`);
for (const sid of skills)
  for (const p of ["ui.selecao.skill", "ui.selecao.skill.desc"])
    (DICT[`${p}.${sid}`] ? (DICT[`${p}.${sid}`].en ? null : semEn) : semChave)
      ?.push(`${p}.${sid}`);

check("toda chave ui.selecao.* existe: " + (semChave.join(", ") || "ok"),
      semChave.length === 0);
check("toda chave ui.selecao.* tem en: " + (semEn.join(", ") || "ok"),
      semEn.length === 0);
check("o pt bate com a fonte (amostra)",
      DICT["ui.selecao.classe.warrior"].pt === "VICTOR COICE BRAVO" &&
      DICT["ui.selecao.skill.desc.cura"].pt.startsWith("Ação principal. 1d8 a 3d8"));

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
