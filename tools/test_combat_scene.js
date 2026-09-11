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

console.log("\n[3] O d20 assentado dispara o golpe");
CS.reset(); CS.configure({});
CS.start(START, 0); CS.tick(0);
CS.result(RESULT_HIT, 50); CS.tick(180);
check("ESPERANDO_DADO após windup+result", CS.phaseOf("atk_1_1") === "ESPERANDO_DADO");
CS.dieSettled({ die: "d20", value: 17 }, 900);
CS.tick(900);
check("dado assentado → GOLPE", CS.phaseOf("atk_1_1") === "GOLPE");
check("dado sem cena esperando é ignorado (não lança)", CS.dieSettled({ die: "d20", value: 3 }, 901) === null);

console.log("\n[4] Dado que assenta ANTES do windup terminar");
CS.reset();
CS.start(START, 0); CS.tick(0);
CS.result(RESULT_HIT, 10); CS.dieSettled({ die: "d20", value: 12 }, 20);
CS.tick(100);
check("ainda ARMANDO (windup não acabou)", CS.phaseOf("atk_1_1") === "ARMANDO");
CS.tick(180);
check("windup acabou com dado já assentado → GOLPE direto", CS.phaseOf("atk_1_1") === "GOLPE");

console.log("\n[5] Modo instant colapsa no result");
CS.reset(); CS.configure({ instant: () => true });
CS.start(START, 0); CS.tick(0);
CS.result(RESULT_HIT, 5);
const cmdsI = CS.tick(5);
check("impact emitido no mesmo tick do result", cmdsI.some(c => c.cmd === "impact"));
CS.configure({ instant: () => false });

console.log("\n[6] result sem start → só impacto");
CS.reset();
CS.result(RESULT_HIT, 0); CS.tick(0);
check("cena órfã entra direto em ESPERANDO_DADO", CS.phaseOf("atk_1_1") === "ESPERANDO_DADO");
CS.dieSettled({ die: "d20", value: 9 }, 10); CS.tick(10);
check("recebe o dado e vai a GOLPE", CS.phaseOf("atk_1_1") === "GOLPE");
check("atacante de cena órfã não tem pose", CS.poseFor("p:id_1", 50) === null);

console.log("\n[7] Fila: 2º ataque do mesmo atacante espera o 1º terminar");
CS.reset();
CS.start(START, 0); CS.tick(0);
CS.start({ ...START, attack_id: "atk_1_2" }, 1); CS.tick(1);
check("2ª cena fica em FILA", CS.phaseOf("atk_1_2") === "FILA");
CS.result(RESULT_HIT, 2); CS.result({ ...RESULT_HIT, attack_id: "atk_1_2" }, 3);
CS.dieSettled({ die: "d20", value: 11 }, 4); CS.dieSettled({ die: "d20", value: 15 }, 5);
CS.tick(180);                                  // 1ª: windup pronto + dado → GOLPE
check("1ª cena em GOLPE", CS.phaseOf("atk_1_1") === "GOLPE");
CS.tick(180 + 110);                            // impacto da 1ª
CS.tick(180 + 110 + 260);                      // recuperou sem hand-off → AGUARDANDO_HANDOFF
check("1ª aguarda hand-off", CS.phaseOf("atk_1_1") === "AGUARDANDO_HANDOFF");
CS.tick(180 + 110 + 261);
check("2ª cena saiu da FILA quando a 1ª deixou de ocupar o atacante", CS.phaseOf("atk_1_2") === "ARMANDO");
CS.tick(180 + 110 + 261 + 180);
check("2ª usa o 2º dado, já assentado → GOLPE", CS.phaseOf("atk_1_2") === "GOLPE");

console.log("\n[8] Expiração fecha cena órfã e restaura");
CS.reset();
CS.start(START, 0); CS.tick(0);
const cmdsE = CS.tick(6001);
check("cena expirada emite end", cmdsE.some(c => c.cmd === "end" && c.id === "atk_1_1"));
check("phaseOf devolve null após expirar", CS.phaseOf("atk_1_1") === null);

console.log("\n[9] Pose do atacante corpo a corpo");
CS.reset(); CS.configure({});
CS.start(START, 0); CS.tick(0);                 // ARMANDO em t=0, alvo a leste (dir = [1,0])
let pa = CS.poseFor("p:id_1", 90);
check("armando recua para longe do alvo (dx negativo)", pa && pa.dx < 0);
check("armando não inclina", pa && pa.tilt === 0);
pa = CS.poseFor("p:id_1", 180);
check("windup completo = -windup.dist", pa && perto(pa.dx, -0.15) && perto(pa.dz, 0));
CS.result(RESULT_HIT, 1); CS.tick(180);         // ESPERANDO_DADO
check("esperando o dado mantém a pose armada", perto(CS.poseFor("p:id_1", 1000).dx, -0.15));
CS.dieSettled({ die: "d20" }, 1000); CS.tick(1000);   // GOLPE em t=1000
pa = CS.poseFor("p:id_1", 1110);
check("fim do golpe = +strike.dist rumo ao alvo", pa && perto(pa.dx, 0.35));
check("golpe inclina para frente (tilt = strike.tiltX)", pa && perto(pa.tilt, 0.12));
check("tiltDir aponta para o alvo", pa && perto(pa.tiltDir[0], 1) && perto(pa.tiltDir[1], 0));
CS.tick(1110);                                  // impacto → RECUPERANDO em 1110
pa = CS.poseFor("p:id_1", 1110 + 220);
check("recuperado volta a ~0 (sem overshoot no fim)", pa && Math.abs(pa.dx) < 1e-6);
CS.tick(1110 + 260);                            // AGUARDANDO_HANDOFF
check("aguardando hand-off não tem pose", CS.poseFor("p:id_1", 1500) === null);
check("chave desconhecida devolve null", CS.poseFor("m:nao", 1500) === null);

console.log("\n[10] Pose do atacante à distância (coice)");
CS.reset();
const LONGE = { ...START, attacker_pos: [0, 0], target_pos: [4, 0] };
CS.start(LONGE, 0); CS.tick(0);
check("não é melee", CS._scenes[0].melee === false);
check("à distância não arma (pose null em ARMANDO)", CS.poseFor("p:id_1", 100) === null);
CS.result({ ...LONGE, hit: true }, 1); CS.tick(180); CS.dieSettled({ die: "d20" }, 500); CS.tick(500);
pa = CS.poseFor("p:id_1", 590);
check("coice recua recoil no fim de msOut", pa && perto(pa.dx, -0.10));
CS.tick(590);                                   // impacto (msOut=90) → RECUPERANDO
pa = CS.poseFor("p:id_1", 590 + 200);
check("coice volta a 0 em msBack", pa && Math.abs(pa.dx) < 1e-6);

console.log("\n[11] Fumble: golpe passa direto e oscila na volta");
CS.reset();
CS.start(START, 0); CS.tick(0);
CS.result({ ...RESULT_HIT, hit: false, natural_fumble: true }, 1); CS.tick(180);
CS.dieSettled({ die: "d20", value: 1 }, 500); CS.tick(500);
pa = CS.poseFor("p:id_1", 610);
check("fumble avança fumble.dist", pa && perto(pa.dx, 0.50));
CS.tick(610);                                   // RECUPERANDO
const pb = CS.poseFor("p:id_1", 610 + 27);      // p≈0.123 → sin(2π·2·0.123)≈sin(1.55)≈1
check("na volta do fumble há oscilação extra além do tilt do golpe", pb && pb.tilt > 0.12 * (1 - easeOutT(27 / 220)) + 0.05);

function easeOutT(t) { return 1 - Math.pow(1 - t, 2); }

console.log("\n" + "=".repeat(50));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
