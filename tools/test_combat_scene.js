// tools/test_combat_scene.js — roda da raiz: node tools/test_combat_scene.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };
const perto = (a, b, eps = 1e-6) => Math.abs(a - b) <= eps;

global.window = {};
eval(fs.readFileSync(path.join(raiz, "src", "combatScene.js"), "utf8"));
const CS = global.window.CombatScene;

// Mensagens de exemplo (mesma forma que game.js passa ao módulo)
const START = { attack_id: "atk_1_1", attacker_key: "p:id_1", target_key: "m:id_9",
                attacker_pos: [3, 5], target_pos: [4, 5] };
const RESULT_HIT = { ...START, hit: true, crit: false, natural_critical: false, natural_fumble: false };

console.log("\n[1] Linha do tempo básica sem dado");
CS.reset(); CS.configure({});
check("start cria a cena", CS.start(START, 1000) !== null);
CS.tick(1000);
check("entra em ARMANDO no primeiro tick", CS.phaseOf("atk_1_1") === "ARMANDO");
CS.tick(1100);
check("segue ARMANDO enquanto o windup roda", CS.phaseOf("atk_1_1") === "ARMANDO");
CS.tick(1200);
check("windup terminou mas sem result continua ARMANDO", CS.phaseOf("atk_1_1") === "ARMANDO");
CS.result(RESULT_HIT, 1250);
CS.tick(1250);
check("com result e windup pronto vai a ESPERANDO_DADO", CS.phaseOf("atk_1_1") === "ESPERANDO_DADO");
CS.tick(1250 + 3499);
check("ainda espera o dado antes de waitDieMs", CS.phaseOf("atk_1_1") === "ESPERANDO_DADO");
CS.tick(1250 + 3500);
check("sem dado por waitDieMs → GOLPE", CS.phaseOf("atk_1_1") === "GOLPE");
const cmdsA = CS.tick(1250 + 3500 + 110);
check("fim do golpe emite comando impact", cmdsA.some(c => c.cmd === "impact" && c.targetKey === "m:id_9"));
check("acerto normal vai a RECUPERANDO", CS.phaseOf("atk_1_1") === "RECUPERANDO");
CS.tick(1250 + 3500 + 110 + 260);
check("sem hand-off após recuperar fica AGUARDANDO_HANDOFF", CS.phaseOf("atk_1_1") === "AGUARDANDO_HANDOFF");

console.log("\n[2] configure() mescla só o que foi passado");
CS.reset(); CS.configure({ cfg: { windup: { ms: 50 } } });
check("windup.ms sobrescrito", CS.cfg().windup.ms === 50);
check("windup.dist preservado", perto(CS.cfg().windup.dist, 0.15));
check("waitDieMs preservado", CS.cfg().waitDieMs === 3500);
CS.configure({});

console.log("\n" + "=".repeat(50));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
