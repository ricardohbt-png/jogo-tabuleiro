// Motor de idioma do cliente — roda da raiz: node tools/test_idioma_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// O dicionário e o motor são <script> no navegador: aqui simulamos o window.
// Carregar SÓ o strings.js não simula o navegador: o index.html inclui os seis
// arquivos de src/lang/, e cada um faz Object.assign no LANG_STRINGS. Com um só,
// a checagem [5] acusava como órfã toda chave data-i18n que morasse nos outros —
// falso positivo medido no Lote 3, quando a interface passou a ter chaves lá.
const LANG_FILES = ["strings", "catalogo", "composto", "interface", "erros", "narracao"];
global.window = {};
for (const f of LANG_FILES)
  eval(fs.readFileSync(path.join(raiz, "src", "lang", f + ".js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
const DICT = global.window.LANG_STRINGS;
const I18N = global.window.I18N;

console.log("\n[1] Dicionário");
check("window.LANG_STRINGS carregou", DICT && Object.keys(DICT).length > 0);
check("toda entrada tem pt", Object.values(DICT).every(e => typeof e.pt === "string"));

console.log("\n[2] t() — idioma, fallback e chave ausente");
check("padrão é português", I18N.lang === "pt");
check("t() em português", I18N.t("erro.porta_longe") === "Aproxime-se da porta para abri-la.");
I18N.setLang("en");
check("setLang troca o idioma", I18N.lang === "en");
check("t() em inglês", I18N.t("erro.porta_longe") === "Get closer to the door to open it.");
DICT["_teste.so_pt"] = { pt: "só em português" };
check("falta 'en' → cai no português", I18N.t("_teste.so_pt") === "só em português");
check("chave inexistente devolve a própria chave", I18N.t("_teste.nao_existe") === "_teste.nao_existe");
I18N.setLang("klingon");
check("idioma não suportado é ignorado", I18N.lang === "en");
delete DICT["_teste.so_pt"];

console.log("\n[3] Parâmetros {nome}");
check("substitui por nome",
      I18N.t("narracao.abre_porta", { nome: "Thorin" }) === "🚪 **Thorin** opens a door!");
check("parâmetro que falta fica visível",
      I18N.t("narracao.abre_porta") === "🚪 **{nome}** opens a door!");

console.log("\n[4] Callbacks de troca");
let avisos = [];
I18N.on(code => avisos.push(code));
I18N.setLang("pt");
check("callback recebe o novo idioma", avisos.length === 1 && avisos[0] === "pt");
I18N.setLang("pt");
check("trocar para o mesmo idioma não dispara de novo", avisos.length === 1);

console.log("\n[5] Chaves data-i18n do game.js existem no dicionário");
const gamejs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const usadas = new Set();
for (const m of gamejs.matchAll(/data-i18n(?:-ph|-title|-html)?="([^"]+)"/g)) usadas.add(m[1]);
const orfas = [...usadas].filter(k => !DICT[k]);
check(`nenhuma chave data-i18n órfã (usadas: ${usadas.size})`, orfas.length === 0);
if (orfas.length) console.log("     órfãs:", orfas.join(", "));

console.log("\n[6] O idioma salvo é propagado ao servidor (regressão)");
// Bug real, achado só na verificação dentro do jogo: _langLoadPref restaurava o
// idioma direto no I18N e o gameState continuava achando que era português —
// então quem tinha inglês salvo abria a interface em inglês e recebia narração e
// erros do servidor em português. A correção é propagar por um OUVINTE do I18N,
// que cobre de uma vez o clique no seletor e a restauração do boot.
// Checagem estática: o teste não consegue carregar o game.js (ele monta o DOM
// inteiro no load), então verificamos a fiação no fonte.
check("game.js liga I18N.on a GS.setLang",
      /I18N\.on\(\s*code\s*=>\s*GS\.setLang\(code\)\s*\)/.test(gamejs));
check("propagação tem um caminho só (uma única chamada a GS.setLang)",
      (gamejs.match(/GS\.setLang\(/g) || []).length === 1);

console.log("");
console.log("[O] O markup inserido depois tambem e traduzido");
// Checagem estatica: o teste nao carrega o game.js (ele monta o DOM inteiro no
// load), entao verificamos a fiacao no fonte — mesmo padrao das outras secoes.
const gjObs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("o observador do body aplica _i18nApply",
      /new MutationObserver\([\s\S]{0,600}?_i18nApply/.test(gjObs));
check("ele escuta o body com subtree",
      /observe\(\s*document\.body\s*,\s*\{[^}]*subtree\s*:\s*true/.test(gjObs));
check("so trabalha quando o no traz data-i18n",
      /\[data-i18n/.test(gjObs));
check("continua havendo UM observador do body, nao dois",
      (gjObs.match(/observe\(\s*document\.body/g) || []).length === 1);

console.log("");
console.log("[A] O icone de habilidade nao depende do nome em portugues");
const gjAb = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("replaceAbilityEmoji prefere o data-ability-id ao texto",
      /dataset\.abilityId/.test(gjAb));
// indexOf de algo AUSENTE devolve -1, que e menor que qualquer indice — sem o
// teste de presenca, esta checagem passaria justamente quando o id nao existe.
check("o caminho por id vem ANTES do scan por texto",
      gjAb.includes("dataset.abilityId")
      && gjAb.indexOf("dataset.abilityId") < gjAb.indexOf("ABILITY_NAME_TO_ID).find"));
check("o scan por texto continua como retaguarda",
      /ABILITY_NAME_TO_ID\)\.find/.test(gjAb));
check("abilityIconHtml marca o id no img (para depurar e evitar reaplicar)",
      /data-ability-id/.test(gjAb));

console.log("");
console.log("[I] O dicionario da interface existe e foi carregado");
check("src/lang/interface.js existe",
      fs.existsSync(path.join(raiz, "src", "lang", "interface.js")));
const idxHtml = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
check("o index.html carrega o interface.js",
      /src\/lang\/interface\.js/.test(idxHtml));
check("as chaves da interface entraram no dicionario",
      Object.keys(DICT).some(k => k.startsWith("ui.")));

console.log("");
console.log("[G] gameState.js traduz sem conhecer o I18N");
// A regra do CLAUDE.md: zero window/document/THREE no gameState.js. O `t` global
// vem de window.I18N, entao usa-lo cru ali violaria a regra. A saida e a mesma
// que o modulo ja usa para o filtro de mensagens: quem conhece o I18N e o
// game.js, que injeta a funcao.
const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
const gsSemComentario = gsSrc
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/\/\/[^\n]*/g, "");
check("gameState.js nao referencia window/document/THREE",
      !/\b(window|document|THREE)\b/.test(gsSemComentario));
check("existe o injetor setTranslator", /function setTranslator/.test(gsSrc));
check("o setTranslator esta exportado", /\bsetTranslator,/.test(gsSrc));
const gjSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("o game.js registra o tradutor", /GS\.setTranslator\(/.test(gjSrc));
// Sem tradutor injetado o modulo TEM de cair no portugues — e o mesmo contrato
// de fallback do resto da etapa 5.
check("o _t tem fallback para o texto em portugues",
      /function _t\s*\([^)]*\)\s*\{[\s\S]{0,220}?\bpt\b/.test(gsSrc));

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
