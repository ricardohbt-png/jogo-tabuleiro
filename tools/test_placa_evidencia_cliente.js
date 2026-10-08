// Placa em evidência — roda da raiz: node tools/test_placa_evidencia_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };
global.window = {};
const G = eval(fs.readFileSync(path.join(raiz, "src", "guiaTutorial.js"), "utf8") + "; window.GuiaTutorial");

const estado = (over) => Object.assign({
  current_turn: "p1",
  players: [{ id: "p1", class_id: "mage", alive: true, pos: [3, 3] },
            { id: "p2", class_id: "warrior", alive: true, pos: [4, 4] }],
  tutorial: { por_classe: { mage: { placa: { id: "placa_mage", pos: [22, 18] } },
                            warrior: { placa: { id: "placa_warrior", pos: [22, 13] } } } },
}, over || {});
const tudo = () => true;

check("existe", typeof G.placaEmEvidencia === "function");
let r = G.placaEmEvidencia(estado(), "p1", tudo);
check("na vez do mago: a placa do mago", r && r.id === "placa_mage" && r.pos[0] === 22 && r.pos[1] === 18 && r.tipo === "casa");
check("fora da vez: nada", G.placaEmEvidencia(estado({ current_turn: "p2" }), "p1", tudo) === null);
r = G.placaEmEvidencia(estado({ current_turn: "p2" }), "p2", tudo);
check("grupo solo: foco no guerreiro na vez dele", r && r.id === "placa_warrior");
check("névoa: casa não visível não revela", G.placaEmEvidencia(estado(), "p1", (x, y) => !(x === 22 && y === 18)) === null);
check("sem campo (cumprido): nada", G.placaEmEvidencia(estado({ tutorial: { por_classe: { mage: {} } } }), "p1", tudo) === null);
check("sem tutorial: nada", G.placaEmEvidencia(estado({ tutorial: null }), "p1", tudo) === null);
check("herói morto: nada", G.placaEmEvidencia(estado({ players: [{ id: "p1", class_id: "mage", alive: false }] }), "p1", tudo) === null);
check("lixo não quebra", G.placaEmEvidencia(null, "p1", tudo) === null
      && G.placaEmEvidencia(estado({ tutorial: { por_classe: { mage: { placa: { pos: "x" } } } } }), "p1", tudo) === null);
check("sem visivel: assume visível", G.placaEmEvidencia(estado(), "p1") !== null);

const jogo = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("fiação 2D: halo da placa desenhado antes do alvo do passo", /_guiaPlacaDesenhar2D\(ctx, state, visionSet, alvo\);\s*if\(!alvo\) return;/.test(jogo));
check("fiação 3D: marca guiaPlaca criada e descartada", jogo.includes("_guiaMarca3D('guiaPlaca')") && jogo.includes("['guiaMarca', 'guiaPlaca']"));
check("fiação: usa o módulo puro", jogo.includes("GuiaTutorial.placaEmEvidencia("));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
