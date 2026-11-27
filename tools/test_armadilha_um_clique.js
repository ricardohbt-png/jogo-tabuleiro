// Criar Armadilha em um clique. Roda da raiz: node tools/test_armadilha_um_clique.js
// Executa as funções REAIS do quadro (extraídas do game.js) com uma página falsa mínima.
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
function trecho(inicio, fim) {
  const i = game.indexOf(inicio);
  const j = game.indexOf(fim, i + inicio.length);
  if (i < 0 || j < 0) throw new Error("trecho não achado: " + inicio);
  return game.slice(i, j);
}
const codigo = [
  trecho("const ARMADILHAS_LUCCAS = [", "\n// Venenos na bolsa"),
  trecho("function _venenosNaBolsa(me){", "\nfunction _rogueMyTurn(me){"),
  trecho("function _rogueMyTurn(me){", "\n// ── Painel: Criar Armadilha"),
  trecho("function abrirPainelCriarArmadilha(){", "\nfunction _ativarModoPlacementArmadilha("),
].join("\n");

function montar(bolsa) {
  const elementos = {};
  const document = {
    getElementById: id => elementos[id] || null,
    createElement: () => {
      const el = { style: {}, innerHTML: "", id: "",
        remove() { if (elementos[this.id] === this) delete elementos[this.id]; } };
      return el;
    },
    body: { appendChild: el => { elementos[el.id] = el; } },
  };
  const window = {};
  const mira = [];
  const logs = [];
  const GS = {
    me: { class_id: "rogue", alive: true, gold: 100, action_done: false, bag: bolsa || [] },
    isMyTurn: true, gameState: { phase: "playing" },
    CATALOGO_ITENS: {},
    ladinoArmadilhasDesbloqueadas: () => ["buraco", "armadilha_urso", "fosso_envenenado", "lamina_escondida"],
    adicionarLog: m => logs.push(m),
  };
  const f = new Function("document", "window", "GS", "t", "toast", "_ativarModoPlacementArmadilha",
    codigo + "\nreturn abrirPainelCriarArmadilha;");
  const abrir = f(document, window, GS, k => k, () => {}, (tipo, veneno) => mira.push([tipo, veneno]));
  return { abrir, window, mira, logs, painel: () => elementos["painel-armadilha"] || null };
}

console.log("\n[1] Armadilha comum: um clique fecha o quadro e liga a mira");
let c = montar();
c.abrir();
check("o quadro abre", !!c.painel());
check("não há mais botão Posicionar", !/ui\.armadilha\.posicionar"/.test(c.painel().innerHTML));
check("o botão Cancelar continua", /ui\.geral\.cancelar_caixa/.test(c.painel().innerHTML));
c.window.selecionarArmadilha("armadilha_urso");
check("o quadro fechou", c.painel() === null);
check("a mira foi ligada com a armadilha escolhida e sem veneno",
  c.mira.length === 1 && c.mira[0][0] === "armadilha_urso" && !c.mira[0][1]);

console.log("\n[2] Fosso Envenenado: escolhe o veneno, e o clique no veneno liga a mira");
c = montar([{ id: "veneno_aranha", veneno_id: "veneno_aranha", nome: "Veneno de Aranha" }]);
c.abrir();
c.window.selecionarArmadilha("fosso_envenenado");
check("o quadro continua aberto para escolher o veneno", !!c.painel() && c.mira.length === 0);
check("a lista de venenos aparece", /selecionarVenenoPara\('veneno_aranha'\)/.test(c.painel().innerHTML));
check("veneno obrigatório não oferece 'Sem veneno'", !/selecionarVenenoPara\(''\)/.test(c.painel().innerHTML));
c.window.selecionarVenenoPara("veneno_aranha");
check("o clique no veneno fecha o quadro e liga a mira com ele",
  c.painel() === null && c.mira.length === 1 && c.mira[0][0] === "fosso_envenenado" && c.mira[0][1] === "veneno_aranha");

console.log("\n[3] Lâmina Escondida: veneno opcional, com 'Sem veneno'");
c = montar([{ id: "veneno_aranha", veneno_id: "veneno_aranha", nome: "Veneno de Aranha" }]);
c.abrir();
c.window.selecionarArmadilha("lamina_escondida");
check("o quadro continua aberto e oferece 'Sem veneno'",
  !!c.painel() && c.mira.length === 0 && /selecionarVenenoPara\(''\)/.test(c.painel().innerHTML));
c.window.selecionarVenenoPara("");
check("'Sem veneno' fecha e liga a mira sem veneno",
  c.painel() === null && c.mira.length === 1 && c.mira[0][0] === "lamina_escondida" && !c.mira[0][1]);
c = montar([{ id: "veneno_aranha", veneno_id: "veneno_aranha", nome: "Veneno de Aranha" }]);
c.abrir();
c.window.selecionarArmadilha("lamina_escondida");
c.window.selecionarVenenoPara("veneno_aranha");
check("escolher um veneno também liga a mira com ele",
  c.mira.length === 1 && c.mira[0][1] === "veneno_aranha");

console.log("\n[4] Clicar de novo na armadilha de veneno escolhida desfaz a escolha");
c = montar([{ id: "veneno_aranha", veneno_id: "veneno_aranha", nome: "Veneno de Aranha" }]);
c.abrir();
c.window.selecionarArmadilha("lamina_escondida");
c.window.selecionarArmadilha("lamina_escondida");
check("a lista de venenos some e nada é posicionado",
  !!c.painel() && c.mira.length === 0 && !/selecionarVenenoPara\(/.test(c.painel().innerHTML));

console.log("\n[5] Texto");
const lang = fs.readFileSync(path.join(raiz, "src/lang/interface.js"), "utf8");
check("chave ui.armadilha.sem_veneno com pt e en",
  /"ui\.armadilha\.sem_veneno":\s*\{[^}]*"en":[^}]*"pt":/.test(lang));

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
