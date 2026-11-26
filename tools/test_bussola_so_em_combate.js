// A bússola de direção só abre em combate (ou quando a lição de treinamento a pede).
// Roda da raiz: node tools/test_bussola_so_em_combate.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
const game = fs.readFileSync(path.join(raiz, "game.js"), "utf8").split("\r\n").join("\n");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); } else { FAIL++; console.log("  ❌ " + name); } };

// Extrai `function nome(...){...}` de game.js por contagem de chaves.
function extrair(nome) {
  const i = game.indexOf(`function ${nome}(`);
  if (i < 0) return null;
  let j = game.indexOf("{", i), depth = 0, k = j;
  for (; k < game.length; k++) {
    if (game[k] === "{") depth++;
    else if (game[k] === "}") { depth--; if (depth === 0) break; }
  }
  return game.slice(i, k + 1);
}

const nomes = ["_autoTurnCombatActive", "_bussolaPedidaPelaLicao", "_bussolaEmCombate", "_bussolaCabe"];
const fontes = nomes.map(extrair);
check("as funções existem em game.js", fontes.every(Boolean));
if (fontes.every(Boolean)) {
  let GS;
  const contexto = new Function("GS", fontes.join("\n") + "\nreturn { _bussolaCabe, _bussolaEmCombate };");

  const base = () => ({
    phase: "playing", current_turn: "p1", monsters: [], players: [{ id: "p1", class_id: "warrior", alive: true, pos: [3, 3] }],
  });
  const roda = (estado, extra = {}) => {
    GS = { gameState: estado, myPid: "p1", isMyTurn: true, isMaster: () => false,
           me: estado.players.find(p => p.id === "p1"), ...extra };
    return contexto(GS)._bussolaCabe();
  };

  console.log("\n[1] Exploração: sem inimigo alerta, a bússola não abre");
  check("sem monstros", roda(base()) === false);
  let e = base(); e.monsters = [{ id: "m1", hp: 5 }];
  check("monstro dormente (nem alertado nem procurando)", roda(e) === false);
  e = base(); e.monsters = [{ id: "m1", hp: 0, alertado: true }];
  check("monstro alertado mas morto", roda(e) === false);

  console.log("\n[2] Combate: abre");
  e = base(); e.monsters = [{ id: "m1", hp: 5, alertado: true }];
  check("monstro vivo alertado", roda(e) === true);
  e = base(); e.monsters = [{ id: "m1", hp: 5, procurando: true }];
  check("monstro procurando o herói", roda(e) === true);
  e = base(); e.test_mode = true; e.test_combat = { active: true };
  check("mesa de teste (test_mode) nunca abre", roda(e) === false);

  console.log("\n[3] Lição de treinamento que pede a bússola");
  e = base(); e.tutorial = { training: true, por_classe: { warrior: { requer_escolher_direcao: true } } };
  check("lição escolher_direcao abre mesmo sem combate", roda(e) === true);
  e = base(); e.tutorial = { training: true, por_classe: { warrior: { requer_escolher_direcao: false } } };
  check("outra lição: não abre sem combate", roda(e) === false);
  e = base(); e.tutorial = { training: false, por_classe: { warrior: { requer_escolher_direcao: true } } };
  check("fora do treinamento a lição não conta", roda(e) === false);

  console.log("\n[4] As guardas de antes continuam valendo");
  const combate = () => { const x = base(); x.monsters = [{ id: "m1", hp: 5, alertado: true }]; return x; };
  check("não é a minha vez", roda(combate(), { isMyTurn: false }) === false);
  check("sou o Mestre", roda(combate(), { isMaster: () => true }) === false);
  e = combate(); e.last_stand_pid = "p1";
  check("Último Esforço", roda(e) === false);
  e = combate(); e.phase = "city";
  check("fora da masmorra", roda(e) === false);
  e = combate(); e.players[0].alive = false;
  check("herói morto", roda(e) === false);
}

console.log("\n[5] Os caminhos do controle e do auto-encerrar continuam sem bússola quando ela não cabe");
check("o aperto duplo do controle segue como fallback", /if\(_bussolaCabe\(\)\)\{[\s\S]{0,260}endTurn\(\);[\s\S]{0,200}if\(now <= _gamepadEndTurnConfirmUntil\)/.test(game));

console.log(`\nTotal: ${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
