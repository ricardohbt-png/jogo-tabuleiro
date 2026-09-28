// setTab (tools/editor.js) testado por COMPORTAMENTO, não por regex de texto.
// Roda da raiz: node tools/test_editor_settab.js
//
// Extrai a função real do arquivo (entre "function setTab(tab, soRedesenhar) {"
// e a linha seguinte "  window.setTab = setTab;", que é onde o módulo a expõe —
// o próprio corpo da função termina 1 linha antes disso) e a avalia como uma
// expressão de função, com stubs para document/window e para os módulos que ela
// despacha. Substitui as checagens de regex que a seção [2a] do
// tools/test_editor_idioma.py fazia sobre o texto de "soRedesenhar &&
// window.EDITOR_X.sincronizar" — aqui o comportamento é exercitado de verdade.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

// ── Extrai o corpo real de setTab de tools/editor.js ──────────────────────────
const src = fs.readFileSync(path.join(raiz, "tools", "editor.js"), "utf8");
const INICIO = "function setTab(tab, soRedesenhar) {";
const FIM = "\n  window.setTab = setTab;";
const inicio = src.indexOf(INICIO);
if (inicio < 0) throw new Error("setTab(tab, soRedesenhar) não encontrada em tools/editor.js");
const fim = src.indexOf(FIM, inicio);
if (fim < 0) throw new Error("marcador 'window.setTab = setTab;' não encontrado após setTab");
// O corpo da função termina na linha "  }" logo antes do marcador; a própria
// declaração ("function setTab(...) { ... }") já inclui essa chave de fechamento
// — pegamos até `fim`, que aponta para o "\n" antes de "  window.setTab = setTab;".
const corpoSetTab = src.slice(inicio, fim);
check("extraiu um corpo de função não vazio", corpoSetTab.length > 200);
check("o corpo extraído contém os ramos de soRedesenhar", corpoSetTab.includes("soRedesenhar"));

// ── Ambiente falso: document com só os ids que setTab toca ────────────────────
function elStub() { return { style: {}, classList: { toggle: () => {} } }; }
const IDS = ["dungeon-controls", "toolbar", "workspace", "campaign-controls", "campaign-view",
  "bestiary-view", "monster-editor-view", "items-editor-view", "city-editor-view",
  "world-editor-view", "scenes-editor-view", "tab-masmorra", "tab-bestiario",
  "tab-editor-monstros", "tab-editor-itens", "tab-cidade", "tab-mapa-mundi",
  "tab-campanha", "tab-cenas"];
const ELS = {};
IDS.forEach(id => { ELS[id] = elStub(); });

let calls = [];
global.window = {};
global.document = { getElementById: id => ELS[id] || elStub() };

// render()/renderPanel() são chamadas SEM qualificador dentro de setTab (são
// funções de topo do IIFE de editor.js) — precisam existir como identificadores
// livres no escopo em que o eval() roda, não em window/document.
function render() { calls.push("render()"); }
function renderPanel() { calls.push("renderPanel()"); }

function novosModulos() {
  window.EDITOR_SCENES = {
    load: () => calls.push("scenes.load"),
    render: () => calls.push("scenes.render"),
  };
  window.EDITOR_MONSTER_EDITOR = {
    render: () => calls.push("monster.render"),
    sincronizar: () => calls.push("monster.sincronizar"),
  };
  window.EDITOR_ITEMS_EDITOR = {
    render: () => calls.push("items.render"),
    sincronizar: () => calls.push("items.sincronizar"),
  };
  window.EDITOR_BESTIARY = { render: () => calls.push("bestiary.render") };
  window.EDITOR_CITY = { render: () => calls.push("city.render") };
  window.EDITOR_WORLD = { render: () => calls.push("world.render") };
  window.EDITOR_CAMPAIGN = { renderCampaign: () => calls.push("campaign.render") };
}
novosModulos();

// ── Avalia a função extraída como expressão, closure sobre este escopo ────────
let setTab;
try {
  setTab = eval("(" + corpoSetTab + ")");
} catch (e) {
  throw new Error("falha ao avaliar o corpo extraído de setTab: " + e.message);
}
check("setTab avaliou para uma função", typeof setTab === "function");

// ── (a) setTab('cenas') chama load, não render ─────────────────────────────
calls = [];
setTab("cenas");
console.log("\n[a] setTab('cenas') sem soRedesenhar");
check("chamou scenes.load", calls.includes("scenes.load"));
check("NÃO chamou scenes.render", !calls.includes("scenes.render"));

// ── (b) setTab('cenas', true) chama render, não load ───────────────────────
calls = [];
setTab("cenas", true);
console.log("\n[b] setTab('cenas', true)");
check("chamou scenes.render", calls.includes("scenes.render"));
check("NÃO chamou scenes.load", !calls.includes("scenes.load"));

// ── (c) setTab('editor_monstros', true) chama sincronizar ANTES de render ──
calls = [];
setTab("editor_monstros", true);
console.log("\n[c] setTab('editor_monstros', true)");
check("chamou monster.sincronizar", calls.includes("monster.sincronizar"));
check("chamou monster.render", calls.includes("monster.render"));
check("sincronizar veio antes de render",
      calls.indexOf("monster.sincronizar") < calls.indexOf("monster.render"));

// ── (d) setTab('editor_monstros') SEM soRedesenhar não sincroniza ──────────
calls = [];
setTab("editor_monstros");
console.log("\n[d] setTab('editor_monstros') sem soRedesenhar");
check("chamou monster.render", calls.includes("monster.render"));
check("NÃO chamou monster.sincronizar", !calls.includes("monster.sincronizar"));

// ── (e) o mesmo par para editor_itens ───────────────────────────────────────
calls = [];
setTab("editor_itens", true);
console.log("\n[e1] setTab('editor_itens', true)");
check("chamou items.sincronizar", calls.includes("items.sincronizar"));
check("chamou items.render", calls.includes("items.render"));
check("sincronizar veio antes de render",
      calls.indexOf("items.sincronizar") < calls.indexOf("items.render"));

calls = [];
setTab("editor_itens");
console.log("\n[e2] setTab('editor_itens') sem soRedesenhar");
check("chamou items.render", calls.includes("items.render"));
check("NÃO chamou items.sincronizar", !calls.includes("items.sincronizar"));

// ── (f) sincronizar() que lança não impede o render() nem derruba setTab ───
console.log("\n[f] sincronizar() com defeito");
const sincronizarOriginal = window.EDITOR_MONSTER_EDITOR.sincronizar;
window.EDITOR_MONSTER_EDITOR.sincronizar = () => { throw new Error("rascunho corrompido"); };
calls = [];
let lancou = false;
try { setTab("editor_monstros", true); } catch (e) { lancou = true; }
check("setTab não propagou a exceção do sincronizar", !lancou);
check("render() do editor de criaturas rodou mesmo assim", calls.includes("monster.render"));
window.EDITOR_MONSTER_EDITOR.sincronizar = sincronizarOriginal;

// ── (g) window._abaAtualEditor reflete a aba pedida ─────────────────────────
console.log("\n[g] window._abaAtualEditor");
setTab("cidade");
check("aba 'cidade' gravada", window._abaAtualEditor === "cidade");
setTab("mapa_mundi", true);
check("aba 'mapa_mundi' gravada mesmo com soRedesenhar", window._abaAtualEditor === "mapa_mundi");

console.log(`\n  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
