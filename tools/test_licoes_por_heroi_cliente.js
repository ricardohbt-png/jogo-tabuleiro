// Tutorial com vários heróis na mesma conexão (Solo com grupo): cada herói tem a
// própria lição em andamento, e a janela do Mestre de Armas mostra a do herói em foco.
// Antes havia um espaço só: a lição de um herói apagava a do outro, e a troca de foco
// fechava a janela sem nunca reabri-la.
// Roda da raiz: node tools/test_licoes_por_heroi_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
const G = eval(fs.readFileSync(path.join(raiz, "src", "guiaTutorial.js"), "utf8") + "; window.GuiaTutorial");

const fala = (id, heroi, i = 0) => ({ type: "fala", licao_id: id, heroi, passo: { i, n: 3 } });

console.log("\n[1] dono da mensagem");
const C = G.criarLicoesPorHeroi();
check("com grupo, o dono vem em `heroi`", C.dono({ heroi: "h2" }, "h1") === "h2");
check("sem grupo (sem `heroi`), é o herói em foco", C.dono({}, "h1") === "h1");

console.log("\n[2] lição de um herói não apaga a do outro");
check("guarda a do guerreiro", C.guardar(fala("treino_mira", "h1"), "h1") === "h1");
check("guarda a do ladino", C.guardar(fala("treino_esconder", "h2"), "h1") === "h2");
check("a do guerreiro continua lá", C.daVez("h1").licao_id === "treino_mira");
check("a do ladino também", C.daVez("h2").licao_id === "treino_esconder");

console.log("\n[3] passo de um herói atualiza só a dele");
let r = C.passo({ licao_id: "treino_esconder", heroi: "h2", passo: { i: 1, n: 3 } }, "h1");
check("devolve o dono e a lição nova", r && r.dono === "h2" && r.licao.passo.i === 1);
check("o guerreiro segue no passo 0", C.daVez("h1").passo.i === 0);
check("passo de lição que não é a dele é ignorado",
      C.passo({ licao_id: "outra", heroi: "h2", passo: { i: 2 } }, "h1") === null
      && C.daVez("h2").passo.i === 1);

console.log("\n[4] concluída/pulada tiram só a lição certa");
check("pulada de outro id não remove", C.remover({ licao_id: "x", heroi: "h1" }, "h1") === null
      && C.daVez("h1"));
r = C.remover({ licao_id: "treino_mira", heroi: "h1" }, "h2");
check("pulada do guerreiro remove a dele", r === "h1" && !C.daVez("h1"));
check("e não toca na do ladino", C.daVez("h2").licao_id === "treino_esconder");

console.log("\n[5] a lição do herói em foco confere com o servidor");
const est = (cls, licao, i) => ({ players: [{ id: "h1", class_id: "warrior" }, { id: "h2", class_id: "rogue" }],
                                  tutorial: { por_classe: { [cls]: { licao_id: licao, passo: { i, n: 3 } } } } });
check("a guardada vale se é a lição em andamento", C.emAndamento("h2", est("rogue", "treino_esconder", 1)).licao_id === "treino_esconder");
check("servidor mais adiantado: vale o do servidor", C.emAndamento("h2", est("rogue", "treino_esconder", 2)).passo.i === 2);
check("estado atrasado (aviso de passo chegou antes): vale o guardado",
      C.emAndamento("h2", est("rogue", "treino_esconder", 0)).passo.i === 1);
check("lição que o servidor já encerrou não volta", C.emAndamento("h2", est("rogue", null, 0)) === null);
check("herói sem lição guardada: nada", C.emAndamento("h1", est("warrior", "treino_mira", 0)) === null);

console.log(`\n=== ${PASS} passou, ${FAIL} falhou ===`);
process.exit(FAIL ? 1 : 0);
