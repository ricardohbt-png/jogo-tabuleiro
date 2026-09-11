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

console.log("\n[12] Hand-off antes do golpe: número sai só no impacto");
CS.reset(); CS.configure({});
CS.start(START, 0); CS.tick(0); CS.result(RESULT_HIT, 1); CS.tick(180);
check("pendingFor acha a cena do alvo", CS.pendingFor("m:id_9") === "atk_1_1");
check("pendingFor de outro alvo é null", CS.pendingFor("m:id_8") === null);
const FB = { feedback: { text: "7", kind: "damage" }, death: false, onImpact: [] };
check("handoff antes do impacto devolve null (guardado)", CS.handoff("m:id_9", FB, 200) === null);
check("depois do hand-off deixa de ser pendente", CS.pendingFor("m:id_9") === null);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500);
const cmdsH = CS.tick(610);
const imp = cmdsH.find(c => c.cmd === "impact");
check("impact carrega o feedback guardado", imp && imp.feedback && imp.feedback.text === "7");
CS.tick(610 + 260);
check("com hand-off já feito, RECUPERANDO → fecha (phase null)", CS.phaseOf("atk_1_1") === null);

console.log("\n[13] Hand-off DEPOIS do golpe: dispara na hora");
CS.reset();
CS.start(START, 0); CS.tick(0); CS.result(RESULT_HIT, 1); CS.tick(180);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500); CS.tick(610);   // impacto sem número
const tardio = CS.handoff("m:id_9", FB, 700);
check("handoff tardio devolve o comando impact", tardio && tardio.cmd === "impact" && tardio.feedback.text === "7");
CS.tick(610 + 260);
check("cena fecha após recuperar", CS.phaseOf("atk_1_1") === null);

console.log("\n[14] Alvo: acerto empurra e inclina para longe do atacante");
CS.reset();
CS.start(START, 0); CS.tick(0); CS.result(RESULT_HIT, 1); CS.tick(180);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500); CS.tick(610);   // impacto em 610
let pt = CS.poseFor("m:id_9", 610 + 130);      // p=0.5 → pico
check("empurrão de hit.push no pico", pt && perto(pt.dx, 0.12) && perto(pt.dz, 0));
check("inclina hit.angle no pico", pt && perto(pt.tilt, 0.14));
check("sem flash em acerto normal", pt && !pt.flash);
check("antes do impacto o alvo não tem pose", CS.poseFor("m:id_9", 600) === null);
pt = CS.poseFor("m:id_9", 610 + 260);
check("reação termina em hit.ms", pt === null || Math.abs(pt.dx) < 1e-6);

console.log("\n[15] Alvo: erro = esquiva sem empurrão");
CS.reset();
CS.start(START, 0); CS.tick(0); CS.result({ ...RESULT_HIT, hit: false }, 1); CS.tick(180);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500);
const cmdsM = CS.tick(610);
check("impact de erro tem hit=false", cmdsM.find(c => c.cmd === "impact").hit === false);
pt = CS.poseFor("m:id_9", 610 + 100);
check("esquiva não desloca", pt && perto(pt.dx, 0) && perto(pt.dz, 0));
check("esquiva inclina dodge.angle no pico", pt && perto(pt.tilt, 0.08));
CS.tick(610 + 260);
check("erro fecha sem esperar hand-off", CS.phaseOf("atk_1_1") === null);

console.log("\n[16] Crítico: hold, flash, empurrão maior e shake");
CS.reset();
CS.start(START, 0); CS.tick(0); CS.result({ ...RESULT_HIT, natural_critical: true }, 1); CS.tick(180);
CS.dieSettled({ die: "d20", value: 20 }, 500); CS.tick(500); CS.tick(610);
check("crítico entra em HOLD", CS.phaseOf("atk_1_1") === "HOLD");
pt = CS.poseFor("m:id_9", 640);                  // dentro do hold (80 ms)
check("durante o hold o alvo está no pico (crit.push)", pt && perto(pt.dx, 0.30));
check("atacante congelado no apex durante o hold", perto(CS.poseFor("p:id_1", 640).dx, 0.35));
check("flash no meio do flashMs", CS.poseFor("m:id_9", 610 + 70).flash > 0.8);
check("flash zera após flashMs", !CS.poseFor("m:id_9", 610 + 141).flash);
check("shake ativo logo após o impacto", CS.shake(620) !== null);
check("shake acaba após shakeMs", CS.shake(610 + 141) === null);
CS.tick(690);
check("após o hold vai a RECUPERANDO", CS.phaseOf("atk_1_1") === "RECUPERANDO");
pt = CS.poseFor("m:id_9", 690 + 60);            // meio da segunda metade da reação (p≈0,73)
check("depois do hold a reação continua e decai", pt && pt.dx < 0.30);
check("acerto normal não gera shake", (CS.reset(), CS.start(START, 0), CS.tick(0), CS.result(RESULT_HIT, 1), CS.tick(180), CS.dieSettled({die:"d20"}, 500), CS.tick(500), CS.tick(610), CS.shake(620) === null));

console.log("\n[17] Morte: isDying, tombo, fade e fechamento");
CS.reset(); CS.configure({});
CS.start(START, 0); CS.tick(0); CS.result(RESULT_HIT, 1); CS.tick(180);
check("não está morrendo antes do hand-off", CS.isDying("m:id_9") === false);
CS.handoff("m:id_9", { feedback: { text: "☠ DERROTADO", kind: "death" }, death: true, onImpact: [] }, 200);
check("isDying vira true no hand-off (antes do golpe)", CS.isDying("m:id_9") === true);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500);
const cmdsD = CS.tick(610);
const impD = cmdsD.find(c => c.cmd === "impact");
check("impact traz death=true", impD && impD.death === true);
check("morte gera shake mesmo sem crítico", CS.shake(615) !== null);
let pm = CS.poseFor("m:id_9", 610 + 190);        // metade da queda
check("meio da queda: inclinação entre 0 e 90°", pm && pm.tilt > 0 && pm.tilt < Math.PI / 2);
check("cai para longe do atacante", pm && perto(pm.tiltDir[0], 1));
check("escurece durante a queda", pm && pm.darken < 1);
check("pose de morte marca dying", pm && pm.dying === true);
pm = CS.poseFor("m:id_9", 610 + 380);
check("no chão = 90°", pm && perto(pm.tilt, Math.PI / 2, 1e-3));
pm = CS.poseFor("m:id_9", 610 + 380 + 47);       // meio do quique
check("quique reduz um pouco o ângulo", pm && pm.tilt < Math.PI / 2);
check("squash no quique", pm && pm.scaleY < 1);
pm = CS.poseFor("m:id_9", 610 + 475 - 50);
check("fade nos últimos fadeMs", pm && pm.opacity < 1 && pm.opacity > 0);
CS.tick(610 + 260);
check("após recuperar vai a MORRENDO", CS.phaseOf("atk_1_1") === "MORRENDO");
check("ainda morrendo", CS.isDying("m:id_9") === true);
const cmdsFim = CS.tick(610 + 475);
check("fim da morte emite end com death=true", cmdsFim.some(c => c.cmd === "end" && c.death === true));
check("deixa de estar morrendo", CS.isDying("m:id_9") === false);
check("sem pose depois do fim", CS.poseFor("m:id_9", 2000) === null);

console.log("\n[18] Morte com hand-off tardio (após o golpe)");
CS.reset();
CS.start(START, 0); CS.tick(0); CS.result(RESULT_HIT, 1); CS.tick(180);
CS.dieSettled({ die: "d20" }, 500); CS.tick(500); CS.tick(610); CS.tick(610 + 260);   // AGUARDANDO_HANDOFF
const cmdT = CS.handoff("m:id_9", { feedback: null, death: true, onImpact: [] }, 900);
check("hand-off tardio de morte devolve impact com death", cmdT && cmdT.death === true);
CS.tick(901);
check("vai a MORRENDO", CS.phaseOf("atk_1_1") === "MORRENDO");
check("tombo começa no hand-off (t=900)", CS.poseFor("m:id_9", 900 + 380).tilt > 1.5);

console.log("\n" + "=".repeat(50));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
