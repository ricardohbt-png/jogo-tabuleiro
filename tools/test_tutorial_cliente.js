// Lição do tutorial no cliente — roda da raiz: node tools/test_tutorial_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

function injetar(tutorial, classe = "warrior") {
  GS.injectPreviewState({
    type: "game_state", master_pid: "p1",
    players: [{ id: "p1", name: "G", class_id: classe, alive: true, pos: [1, 1] }],
    monsters: [], tiles: [[0]], rooms: [], explored: [], round: 1,
    tutorial,
  });
}

console.log("\n[1] licaoAtual devolve a lição da minha classe");
injetar({ por_classe: { warrior: { licao_id: "a", texto_curto: "Ataque o boneco",
                                   feito: 1, vezes: 3, concluidas: 2, total: 5 } } });
const lic = GS.licaoAtual();
check("achou a lição", lic && lic.licao_id === "a");
check("trouxe o texto curto", lic.texto_curto === "Ataque o boneco");
check("trouxe o progresso", lic.feito === 1 && lic.vezes === 3);

console.log("\n[2] Silêncio quando não há lição para mim");
injetar({ por_classe: { mage: { licao_id: "b", texto_curto: "x", feito: 0,
                                vezes: 1, concluidas: 0, total: 1 } } });
check("lição de outra classe não vaza", GS.licaoAtual() === null);

injetar({ por_classe: { warrior: { licao_id: null, texto_curto: "", feito: 0,
                                   vezes: 0, concluidas: 5, total: 5 } } });
check("sem pendência devolve null", GS.licaoAtual() === null);

injetar(null);
check("masmorra comum devolve null", GS.licaoAtual() === null);

console.log(`\n${"=".repeat(50)}\n  ${PASS} passaram, ${FAIL} falharam\n${"=".repeat(50)}`);
process.exit(FAIL ? 1 : 0);
