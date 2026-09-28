// Cola do editor com o motor de idioma — roda da raiz: node tools/test_editor_i18n.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// ── Ambiente falso: window, localStorage e um DOM mínimo ──────────────────────
function elemento(attrs) {
  return { dataset: Object.assign({}, attrs), textContent: "", title: "", placeholder: "", value: "" };
}
const ELS = {
  titulo: elemento({ i18n: "ui.editor.topo.titulo" }),
  aba:    elemento({ i18n: "ui.editor.topo.aba.cidade" }),
  dica:   elemento({ i18nTitle: "ui.editor.topo.visualizar_3d_dica" }),
  seletor: elemento({}),
};
const loja = {};
global.window = {
  localStorage: {
    getItem: k => (k in loja ? loja[k] : null),
    setItem: (k, v) => { loja[k] = String(v); },
  },
};
global.document = {
  documentElement: { lang: "pt-BR" },
  querySelectorAll(sel) {
    if (sel === "[data-i18n]") return [ELS.titulo, ELS.aba];
    if (sel === "[data-i18n-title]") return [ELS.dica];
    return [];
  },
  getElementById(id) { return id === "ed-lang" ? ELS.seletor : null; },
};
loja["lfh_lang"] = "en";                       // o jogo já estava em inglês

for (const f of ["strings", "catalogo", "composto", "interface", "erros", "narracao", "editor"])
  eval(fs.readFileSync(path.join(raiz, "src", "lang", f + ".js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
let abaRedesenhada = null;
let abaRedesenhadaSoRedesenhar = null;
window.setTab = (tab, soRedesenhar) => { abaRedesenhada = tab; abaRedesenhadaSoRedesenhar = soRedesenhar; };
eval(fs.readFileSync(path.join(raiz, "tools", "editor_i18n.js"), "utf8"));

console.log("\n[1] Início: lê o idioma do jogo e aplica a moldura");
check("adota lfh_lang do jogo", window.I18N.lang === "en");
check("aplicou data-i18n", ELS.aba.textContent === "City");
check("aplicou data-i18n-title", ELS.dica.title === "Previews the current dungeon without saving");
check("seletor mostra o idioma atual", ELS.seletor.value === "en");
check("t global", typeof window.t === "function" && window.t("ui.editor.topo.aba.cidade") === "City");

console.log("\n[2] nomeCat");
check("traduz nome de catálogo pelo id",
      window.nomeCat("monstro", "goblin", "Goblin X") === window.I18N.t("cat.monstro.goblin.nome"));
check("sem chave devolve o padrão (conteúdo do autor)",
      window.nomeCat("monstro", "monstro_do_autor_xyz", "Meu Bicho") === "Meu Bicho");

console.log("\n[3] trocarIdioma");
window._abaAtualEditor = "cidade";
window.EDITOR_I18N.trocarIdioma("pt");
check("troca o idioma", window.I18N.lang === "pt");
check("grava lfh_lang", loja["lfh_lang"] === "pt");
check("reaplica a moldura", ELS.aba.textContent === "Cidade");
check("redesenha a aba ativa", abaRedesenhada === "cidade");
check("redesenha sem recarregar do servidor (soRedesenhar=true)", abaRedesenhadaSoRedesenhar === true);
check("atualiza lang do documento", document.documentElement.lang === "pt-BR");
window.EDITOR_I18N.trocarIdioma("en");
check("volta ao inglês", ELS.aba.textContent === "City" && document.documentElement.lang === "en");
abaRedesenhada = null;
window.EDITOR_I18N.trocarIdioma("xx");
check("idioma inválido não muda nada nem redesenha", window.I18N.lang === "en" && abaRedesenhada === null);

console.log("\n[4] localStorage indisponível não derruba");
window.localStorage.getItem = () => { throw new Error("bloqueado"); };
window.localStorage.setItem = () => { throw new Error("bloqueado"); };
let ok = true;
try { window.EDITOR_I18N.trocarIdioma("pt"); } catch (e) { ok = false; }
check("trocarIdioma sobrevive a localStorage que lança", ok && window.I18N.lang === "pt");

console.log("\n[5] Início com armazenamento ruim");
// A partir daqui window.I18N já foi trocado várias vezes pelo teste; o motor
// guarda o idioma no fechamento da IIFE, então reavaliar src/i18n.js cria um
// window.I18N NOVO (lang volta a "pt") sem precisar mexer em módulo nenhum —
// é assim que cada sub-teste começa de um início limpo de verdade.
function reavaliarI18N() {
  eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
}
function reavaliarEditorI18N() {
  eval(fs.readFileSync(path.join(raiz, "tools", "editor_i18n.js"), "utf8"));
}

// [5a] lfh_lang guardado é inválido ("xx") — iniciar() tenta setLang("xx"),
// o motor recusa (fora de SUPORTADOS) e o idioma fica no padrão do I18N novo.
loja["lfh_lang"] = "xx";
window.localStorage.getItem = k => (k in loja ? loja[k] : null);
window.localStorage.setItem = (k, v) => { loja[k] = String(v); };
reavaliarI18N();
reavaliarEditorI18N();
check("lfh_lang inválido cai no padrão (pt)", window.I18N.lang === "pt");
check("seletor reflete o padrão (pt)", ELS.seletor.value === "pt");

// [5b] localStorage.getItem lança na inicialização — lerIdioma() cai no catch
// e usa window.I18N.PADRAO; nada escapa para fora do eval.
loja["lfh_lang"] = "en";
window.localStorage.getItem = () => { throw new Error("bloqueado"); };
window.localStorage.setItem = (k, v) => { loja[k] = String(v); };
reavaliarI18N();
let okInicio = true;
try { reavaliarEditorI18N(); } catch (e) { okInicio = false; }
check("getItem que lança na inicialização não derruba", okInicio);
check("cai no padrão (pt) quando getItem lança", window.I18N.lang === "pt");

// Restaura o localStorage saudável para as duas checagens seguintes, que
// olham o comportamento normal de trocarIdioma, não o de leitura.
window.localStorage.getItem = k => (k in loja ? loja[k] : null);
window.localStorage.setItem = (k, v) => { loja[k] = String(v); };

// [5c] trocarIdioma para o idioma ATUAL não chama setTab — o guard de topo
// (`code === window.I18N.lang`) já corta antes de tocar em qualquer coisa.
loja["lfh_lang"] = "pt";
reavaliarI18N();
reavaliarEditorI18N();
window._abaAtualEditor = "cidade";
abaRedesenhada = null;
window.EDITOR_I18N.trocarIdioma("pt");
check("trocar para o idioma atual não redesenha", abaRedesenhada === null);

// [5d] window._abaAtualEditor AUSENTE — o idioma troca de verdade (moldura
// reaplicada), mas setTab não é chamado porque não há aba pra redesenhar.
delete window._abaAtualEditor;
abaRedesenhada = null;
window.EDITOR_I18N.trocarIdioma("en");
check("troca o idioma mesmo sem aba atual", window.I18N.lang === "en");
check("sem _abaAtualEditor não chama setTab", abaRedesenhada === null);
window._abaAtualEditor = "cidade"; // devolve o estado pro resto do teste

// [5e] document.getElementById não acha #ed-lang (null) — nem iniciar() nem
// trocarIdioma podem lançar por causa disso.
loja["lfh_lang"] = "pt";
const getElementByIdOriginal = document.getElementById;
document.getElementById = () => null;
reavaliarI18N();
let okSemSeletor = true;
try {
  reavaliarEditorI18N();
  window._abaAtualEditor = "cidade";
  window.EDITOR_I18N.trocarIdioma("en");
} catch (e) { okSemSeletor = false; }
check("sem #ed-lang, início e troca de idioma não lançam", okSemSeletor);
document.getElementById = getElementByIdOriginal;

console.log(`\n  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
