// Testes do módulo puro tools/editor_guia_logic.js (passos de lição no editor).
const fs = require("fs"), path = require("path");
const raiz = path.join(__dirname, "..");
global.window = {};
eval(fs.readFileSync(path.join(__dirname, "editor_guia_logic.js"), "utf8"));
const G = window.EDITOR_GUIA;
let PASS = 0, FAIL = 0;
function check(nome, cond) { if (cond) { PASS++; console.log("  ✅ " + nome); } else { FAIL++; console.log("  ❌ " + nome); } }

console.log("[1] ehChave / lerUi / montarUi");
check("chave de dicionário é reconhecida", G.ehChave("ui.tutorial.guia.fala_0.ver.texto") === true);
check("texto livre não é chave", G.ehChave("Clique no boneco.") === false);
check("lerUi botao", JSON.stringify(G.lerUi("botao:encerrar_turno")) === '{"tipo":"botao","valor":"encerrar_turno"}');
check("lerUi casa", JSON.stringify(G.lerUi("casa:[5,15]")) === '{"tipo":"casa","valor":"5,15"}');
check("lerUi vazio", JSON.stringify(G.lerUi(null)) === '{"tipo":"","valor":""}');
check("montarUi id", G.montarUi("habilidade", " mira_certeira ") === "habilidade:mira_certeira");
check("montarUi casa", G.montarUi("casa", "5, 15") === "casa:[5,15]");
check("montarUi porta", G.montarUi("porta", "13,15") === "porta:[13,15]");
check("montarUi tipo vazio = null", G.montarUi("", "x") === null);
check("montarUi valor vazio = null", G.montarUi("botao", "") === null);

console.log("[2] carregar / serializar");
const g0 = [{ id: "a", texto: "Passo um.", porque: "Porque sim.", ui: "botao:inventario", dica: ["d1", "d2"], conclui_com: { tipo: "pegar_item" } },
            { id: "b", texto: "Passo dois." }];
const c = G.carregar(g0);
check("carregar devolve 2 passos", c.length === 2);
check("carregar normaliza campos ausentes", c[1].porque === "" && c[1].ui === null && Array.isArray(c[1].dica) && c[1].dica.length === 0 && c[1].conclui_com === null);
check("serializar(carregar(x)) == x", JSON.stringify(G.serializar(c)) === JSON.stringify(g0));
check("carregar não aceita lixo", JSON.stringify(G.carregar("x")) === "[]" && JSON.stringify(G.carregar(null)) === "[]");
check("serializar descarta vazios", JSON.stringify(G.serializar([{ texto: "A", porque: "", ui: null, dica: ["", "x"], conclui_com: null }])) === '[{"texto":"A","dica":["x"]}]');
check("serializar de lista vazia = null", G.serializar([]) === null);
check("carregar clona (não alias)", (() => { const x = G.carregar(g0); x[0].texto = "Z"; return g0[0].texto === "Passo um."; })());

console.log("[3] validar");
const ok = (g) => G.validar(g).length === 0;
check("válido", ok([{ texto: "A", ui: "botao:encerrar_turno" }]));
check("mais de 8 passos", G.validar(Array.from({ length: 9 }, () => ({ texto: "x" }))).some(e => e.codigo === "guia_muitos"));
check("passo sem texto", G.validar([{ texto: "  " }]).some(e => e.codigo === "guia_sem_texto" && e.params.n === 1));
check("ui inválida", G.validar([{ texto: "A", ui: "botao:Maiúscula" }]).some(e => e.codigo === "guia_ui_invalida"));
check("mais de 2 dicas", G.validar([{ texto: "A", dica: ["1", "2", "3"] }]).some(e => e.codigo === "guia_dicas"));
check("conclui_com de verbo desconhecido", G.validar([{ texto: "A", conclui_com: { tipo: "voar" } }, { texto: "B" }]).some(e => e.codigo === "guia_conclui_invalido"));
check("último passo com conclui_com é aviso", G.validar([{ texto: "A", conclui_com: { tipo: "atacar" } }]).some(e => e.codigo === "guia_ultimo_conclui"));
check("conclui_com válido no meio", ok([{ texto: "A", conclui_com: { tipo: "atacar" } }, { texto: "B" }]));
check("passo vindo do dicionário é válido", ok([{ texto: "ui.tutorial.guia.fala_0.ver.texto" }]));

console.log("[4] roundtrip com as 62 lições reais do Campo de Treinamento");
const d = JSON.parse(fs.readFileSync(path.join(raiz, "dungeons", "campo_de_treinamento.json"), "utf8"));
const comGuia = d.falas.filter(f => f.guia);
check("há lições com guia no JSON", comGuia.length >= 62);
let iguais = 0;
for (const f of comGuia) if (JSON.stringify(G.serializar(G.carregar(f.guia))) === JSON.stringify(f.guia)) iguais++;
check("roundtrip idêntico em todas", iguais === comGuia.length);
check("nenhum guia real reprovado na validação", comGuia.every(f => G.validar(G.carregar(f.guia)).every(e => e.codigo === "guia_ultimo_conclui")));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
