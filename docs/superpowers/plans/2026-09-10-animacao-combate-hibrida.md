# Animação de combate híbrida (3D) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** no 3D, o atacante arma, espera o d20 assentar e golpeia; o alvo balança/esquiva; crítico e morte ganham flash, empurrão maior, hit-stop, shake de câmera e partículas; o peão morto tomba antes de virar lápide.

**Architecture:** um módulo puro `src/combatScene.js` (`window.CombatScene`, sem DOM/THREE) mantém uma cena por `attack_id` e devolve poses por chave de entidade e comandos (`impact`/`end`); `game.js` alimenta a cena com `attack_feedback`, o assentamento do d20 e o diff de HP (hand-off), e aplica as poses no laço por peão de `startLoop3D`. Sem mudança de servidor.

**Tech Stack:** Vanilla JS (IIFE, padrão de `src/difficulty.js`), Three.js r128, testes em node (`tools/test_combat_scene.js`, padrão de `tools/test_vocabulario_cliente.js`).

**Spec:** `docs/superpowers/specs/2026-09-10-animacao-combate-hibrida-design.md`.

---

## Avisos ao executor

1. **`game.js` e `server.py` têm WIP não commitado do autor** (+981 linhas em 2026-09-10). Execute num **worktree** a partir de `HEAD` (skill `superpowers:using-git-worktrees`). Todas as referências abaixo são a **funções por nome** (`grep -n "^function nome"`), nunca a linhas. Nunca `git add game.js` fora do worktree.
2. **Ordem dos scripts:** `src/combatScene.js` precisa carregar **antes** de `game.js` (é no `index.html`, Task 6).
3. **Não crie função de módulo com `t()`/`VC` no nível de topo antes da definição** (TDZ — lição da etapa 5 de i18n). A configuração da cena é chamada no fim do `game.js`, junto dos `GS.on(...)`.
4. **Prova no navegador exige servidor reiniciado e cache-buster** (o `index.html` já injeta `?v=Date.now()`; ainda assim recarregue com Ctrl+F5).
5. Rode `node tools/test_combat_scene.js` após cada task do módulo, e `node --check game.js` após cada task do cliente.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `src/combatScene.js` (novo) | máquina de estados pura: cenas, poses, comandos, shake |
| `src/visualConfig.js` | bloco `feedback.combat.scene` (números) |
| `index.html` | carrega `src/combatScene.js` |
| `game.js` | fiação: `attack_feedback` → cena; gancho do d20; hand-off no diff de HP; aplicação da pose no laço; shake; partículas; morte |
| `tools/test_combat_scene.js` (novo) | testes do módulo + checagens estáticas do `game.js`/`index.html` |

---

### Task 1: Módulo `CombatScene` — esqueleto, configuração e linha do tempo sem dado

**Files:**
- Create: `src/combatScene.js`
- Create: `tools/test_combat_scene.js`

- [ ] **Step 1: Escrever o teste falhando**

```js
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
```

- [ ] **Step 2: Rodar o teste para vê-lo falhar**

Run: `node tools/test_combat_scene.js`
Expected: erro `ENOENT ... src/combatScene.js` (o módulo não existe).

- [ ] **Step 3: Escrever o módulo mínimo**

```js
// src/combatScene.js
// Cena de combate do 3D: uma máquina de estados por attack_id que decide
// QUANDO o atacante golpeia (sincronizado com o d20) e devolve poses por
// chave de entidade. Puro: sem DOM, sem THREE. Exposto como window.CombatScene
// (browser) / global.CombatScene (node). Spec:
// docs/superpowers/specs/2026-09-10-animacao-combate-hibrida-design.md
(function (root) {
  'use strict';

  const DEFAULT_CFG = {
    enabled: true,
    meleeRange: 1.5,
    windup:   { dist: 0.15, ms: 180 },
    strike:   { dist: 0.35, ms: 110, tiltX: 0.12 },
    recover:  { ms: 220, overshoot: 0.03 },
    ranged:   { recoil: 0.10, msOut: 90, msBack: 200 },
    fumble:   { dist: 0.50, wobbleCycles: 2 },
    hit:      { angle: 0.14, ms: 260, push: 0.12 },
    dodge:    { angle: 0.08, ms: 200 },
    crit:     { push: 0.30, flashMs: 140, flashPeak: 0.9, hitStopMs: 80,
                shakeMs: 140, shakeAmp: 0.06, particles: 18 },
    death:    { fallMs: 380, bounceDeg: 4, darken: 0.35, fadeMs: 200, squashY: 0.85 },
    waitDieMs: 3500,
    expireMs:  6000,
  };

  function mergeCfg(base, extra) {
    const out = {};
    for (const k in base) {
      const b = base[k];
      if (b && typeof b === 'object' && !Array.isArray(b))
        out[k] = Object.assign({}, b, (extra && extra[k]) || {});
      else
        out[k] = (extra && extra[k] !== undefined) ? extra[k] : b;
    }
    return out;
  }

  let cfg = mergeCfg(DEFAULT_CFG, {});
  let durationFn = ms => ms;        // game.js injeta _animationProgressDuration
  let instantFn  = () => false;     // game.js injeta () => _animationSpeedMode === 'instant'
  const scenes = [];                // ordem de chegada
  const shakes = [];

  const D = ms => durationFn(ms);
  const clamp01 = v => Math.max(0, Math.min(1, v));
  const easeOut = t => 1 - Math.pow(1 - t, 2);
  const easeIn  = t => t * t;

  function configure(opts) {
    opts = opts || {};
    if (opts.cfg) cfg = mergeCfg(DEFAULT_CFG, opts.cfg);
    if (typeof opts.duration === 'function') durationFn = opts.duration;
    if (typeof opts.instant === 'function') instantFn = opts.instant;
  }
  function reset() { scenes.length = 0; shakes.length = 0; }

  function novaCena(msg, soImpacto, now) {
    const ap = msg.attacker_pos || [0, 0], tp = msg.target_pos || [0, 0];
    const ax = Number(ap[0]) || 0, az = Number(ap[1]) || 0;
    const tx = Number(tp[0]) || 0, tz = Number(tp[1]) || 0;
    const ddx = tx - ax, ddz = tz - az, len = Math.hypot(ddx, ddz) || 1;
    const s = {
      id: String(msg.attack_id),
      attackerKey: msg.attacker_key || null,
      targetKey: msg.target_key || null,
      aPos: [ax, az], tPos: [tx, tz],
      dir: [ddx / len, ddz / len],
      melee: Math.max(Math.abs(ddx), Math.abs(ddz)) <= cfg.meleeRange,
      soImpacto: !!soImpacto,
      phase: 'FILA', phaseAt: now, createdAt: now,
      result: null, resultAt: null, dieAt: null,
      impactAt: null, holdUntil: null,
      impact: null, feedbackEmitido: false, deathAt: null,
      done: false,
    };
    scenes.push(s);
    return s;
  }

  function start(msg, now) {
    if (!cfg.enabled || !msg || msg.attack_id == null) return null;
    if (scenes.some(s => s.id === String(msg.attack_id) && !s.done)) return null;
    return novaCena(msg, false, now);
  }

  function result(msg, now) {
    if (!cfg.enabled || !msg || msg.attack_id == null) return null;
    let s = scenes.find(x => x.id === String(msg.attack_id) && !x.done);
    if (!s) s = novaCena(msg, true, now);          // result sem start: só impacto
    s.result = {
      hit: !!msg.hit,
      crit: !!(msg.crit || msg.natural_critical),
      fumble: !!msg.natural_fumble,
    };
    s.resultAt = now;
    return s;
  }

  function entrar(s, phase, now) { s.phase = phase; s.phaseAt = now; }

  function emitirImpacto(s, cmds, now) {
    const c = {
      cmd: 'impact', id: s.id,
      attackerKey: s.attackerKey, targetKey: s.targetKey,
      targetPos: s.tPos.slice(), dir: s.dir.slice(),
      hit: !!(s.result && s.result.hit), crit: !!(s.result && s.result.crit),
      fumble: !!(s.result && s.result.fumble),
      feedback: s.impact ? s.impact.feedback || null : null,
      death: !!(s.impact && s.impact.death),
      onImpact: s.impact ? s.impact.onImpact || [] : [],
    };
    if (s.impact) s.feedbackEmitido = true;
    cmds.push(c);
    return c;
  }

  function irParaImpacto(s, now, cmds) {
    s.impactAt = now;
    const crit = !!(s.result && s.result.crit);
    if (s.impact && s.impact.death && s.deathAt == null) s.deathAt = now;
    if (crit) { s.holdUntil = now + D(cfg.crit.hitStopMs); entrar(s, 'HOLD', now); }
    else entrar(s, 'RECUPERANDO', now);
    return emitirImpacto(s, cmds, now);
  }

  function finalizar(s, cmds, now) {
    if (s.done) return;
    if (s.impact && !s.feedbackEmitido) {      // expirou antes do golpe: não perde o número
      if (s.impactAt == null) s.impactAt = now;
      emitirImpacto(s, cmds, now);
    }
    s.done = true;
    cmds.push({ cmd: 'end', id: s.id, attackerKey: s.attackerKey, targetKey: s.targetKey,
                death: !!(s.impact && s.impact.death) });
  }

  function deathTotalMs() { return D(cfg.death.fallMs) * 1.25; }

  function tick(now) {
    const cmds = [];
    for (const s of scenes) {
      if (s.done) continue;
      if (now - s.createdAt > D(cfg.expireMs)) { finalizar(s, cmds, now); continue; }
      switch (s.phase) {
        case 'FILA': {
          const ocupado = scenes.some(o => o !== s && !o.done && o.attackerKey
            && o.attackerKey === s.attackerKey && o.createdAt < s.createdAt
            && o.phase !== 'AGUARDANDO_HANDOFF' && o.phase !== 'MORRENDO');
          if (ocupado) break;
          entrar(s, s.soImpacto ? 'ESPERANDO_DADO' : 'ARMANDO', now);
          break;
        }
        case 'ARMANDO':
          if (s.result && instantFn()) { irParaImpacto(s, now, cmds); break; }
          if (s.result && now - s.phaseAt >= D(cfg.windup.ms))
            entrar(s, s.dieAt != null ? 'GOLPE' : 'ESPERANDO_DADO', now);
          break;
        case 'ESPERANDO_DADO':
          if (!s.result) break;
          if (instantFn()) { irParaImpacto(s, now, cmds); break; }
          if (s.dieAt != null || now - s.resultAt >= D(cfg.waitDieMs)) entrar(s, 'GOLPE', now);
          break;
        case 'GOLPE': {
          const dur = s.melee ? D(cfg.strike.ms) : D(cfg.ranged.msOut);
          if (now - s.phaseAt >= dur) irParaImpacto(s, now, cmds);
          break;
        }
        case 'HOLD':
          if (now >= s.holdUntil) entrar(s, 'RECUPERANDO', now);
          break;
        case 'RECUPERANDO': {
          const volta = s.melee ? D(cfg.recover.ms) : D(cfg.ranged.msBack);
          const reacao = s.result && s.result.hit ? D(cfg.hit.ms) : D(cfg.dodge.ms);
          if (now - s.phaseAt >= Math.max(volta, reacao)) {
            if (s.impact && s.impact.death) entrar(s, 'MORRENDO', now);
            else if (s.impact || !(s.result && s.result.hit)) finalizar(s, cmds, now);
            else entrar(s, 'AGUARDANDO_HANDOFF', now);
          }
          break;
        }
        case 'AGUARDANDO_HANDOFF':
          if (s.impact) {
            if (s.impact.death) entrar(s, 'MORRENDO', now);
            else finalizar(s, cmds, now);
          }
          break;
        case 'MORRENDO':
          if (s.deathAt != null && now - s.deathAt >= deathTotalMs()) finalizar(s, cmds, now);
          break;
      }
    }
    for (let i = scenes.length - 1; i >= 0; i--) if (scenes[i].done) scenes.splice(i, 1);
    return cmds;
  }

  function phaseOf(id) { const s = scenes.find(x => x.id === String(id) && !x.done); return s ? s.phase : null; }

  root.CombatScene = {
    configure, reset, start, result, tick, phaseOf,
    cfg: () => cfg,
    _scenes: scenes,     // só para testes
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
```

- [ ] **Step 4: Rodar o teste para vê-lo passar**

Run: `node tools/test_combat_scene.js`
Expected: `14 passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(combate): modulo CombatScene — linha do tempo da cena de ataque

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Sincronia com o dado, `instant`, `result` sem `start`, fila e expiração

**Files:**
- Modify: `src/combatScene.js`
- Modify: `tools/test_combat_scene.js`

- [ ] **Step 1: Acrescentar os testes (antes do bloco final de placar)**

```js
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
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_combat_scene.js`
Expected: `TypeError: CS.dieSettled is not a function`.

- [ ] **Step 3: Implementar `dieSettled` e um `poseFor` provisório**

Em `src/combatScene.js`, antes de `function phaseOf`:

```js
  // O primeiro d20 que assenta vai para a cena MAIS ANTIGA que já tem result
  // e ainda não recebeu dado — independe da fase (a 2ª cena da Fúria pode
  // receber o dado ainda em FILA). Devolve a cena ou null (dado ignorado).
  function dieSettled(info, now) {
    if (info && info.die && info.die !== 'd20') return null;
    const s = scenes.find(x => !x.done && x.result && x.dieAt == null && x.impactAt == null);
    if (!s) return null;
    s.dieAt = now;
    return s;
  }

  function poseFor(key, now) { return null; }   // Task 3
```

E exporte: `configure, reset, start, result, dieSettled, tick, phaseOf, poseFor,`.

- [ ] **Step 4: Rodar para ver passar**

Run: `node tools/test_combat_scene.js`
Expected: `30 passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(combate): CombatScene sincroniza o golpe com o d20; fila, instant e expiracao

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Poses do atacante (corpo a corpo, à distância, fumble)

**Files:**
- Modify: `src/combatScene.js`
- Modify: `tools/test_combat_scene.js`

- [ ] **Step 1: Acrescentar os testes**

```js
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
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_combat_scene.js`
Expected: falhas em `[9]` (`poseFor` devolve null).

- [ ] **Step 3: Implementar a pose do atacante**

Substitua o `poseFor` provisório por:

```js
  function poseAtacante(s, now) {
    if (s.soImpacto) return null;
    const d = s.dir;
    const w = cfg.windup.dist;
    const st = (s.result && s.result.fumble) ? cfg.fumble.dist : cfg.strike.dist;
    let dist = 0, tilt = 0;
    if (!s.melee) {
      if (s.phase === 'GOLPE')            dist = -cfg.ranged.recoil * easeOut(clamp01((now - s.phaseAt) / D(cfg.ranged.msOut)));
      else if (s.phase === 'HOLD')        dist = -cfg.ranged.recoil;
      else if (s.phase === 'RECUPERANDO') dist = -cfg.ranged.recoil * (1 - easeOut(clamp01((now - s.phaseAt) / D(cfg.ranged.msBack))));
      else return null;
      return { dx: d[0] * dist, dz: d[1] * dist, tilt: 0, tiltDir: d };
    }
    switch (s.phase) {
      case 'ARMANDO':        dist = -w * easeOut(clamp01((now - s.phaseAt) / D(cfg.windup.ms))); break;
      case 'ESPERANDO_DADO': dist = -w; break;
      case 'GOLPE': {
        const p = easeIn(clamp01((now - s.phaseAt) / D(cfg.strike.ms)));
        dist = -w + (st + w) * p; tilt = cfg.strike.tiltX * p; break;
      }
      case 'HOLD': dist = st; tilt = cfg.strike.tiltX; break;
      case 'RECUPERANDO': {
        const p = clamp01((now - s.phaseAt) / D(cfg.recover.ms)), e = easeOut(p);
        dist = st * (1 - e) - cfg.recover.overshoot * Math.sin(p * Math.PI);
        tilt = cfg.strike.tiltX * (1 - e);
        if (s.result && s.result.fumble)
          tilt += cfg.hit.angle * Math.sin(p * Math.PI * 2 * cfg.fumble.wobbleCycles) * (1 - p);
        break;
      }
      default: return null;
    }
    return { dx: d[0] * dist, dz: d[1] * dist, tilt, tiltDir: d };
  }

  function poseAlvo(s, now) { return null; }    // Task 4

  function somar(a, b) {
    if (!a) return b; if (!b) return a;
    return {
      dx: a.dx + b.dx, dz: a.dz + b.dz,
      tilt: Math.abs(a.tilt) >= Math.abs(b.tilt) ? a.tilt : b.tilt,
      tiltDir: Math.abs(a.tilt) >= Math.abs(b.tilt) ? a.tiltDir : b.tiltDir,
      scaleY: Math.min(a.scaleY == null ? 1 : a.scaleY, b.scaleY == null ? 1 : b.scaleY),
      flash: Math.max(a.flash || 0, b.flash || 0),
      opacity: Math.min(a.opacity == null ? 1 : a.opacity, b.opacity == null ? 1 : b.opacity),
      darken: Math.min(a.darken == null ? 1 : a.darken, b.darken == null ? 1 : b.darken),
      dying: !!(a.dying || b.dying),
    };
  }

  // Pose visual de uma entidade AGORA: soma o que ela faz como atacante e o
  // que sofre como alvo (uma criatura pode ser as duas coisas em cenas
  // distintas). null = nenhuma cena a toca → o laço não escreve nada.
  function poseFor(key, now) {
    if (!key) return null;
    let pose = null;
    for (const s of scenes) {
      if (s.done) continue;
      if (s.attackerKey === key) pose = somar(pose, poseAtacante(s, now));
      if (s.targetKey === key)   pose = somar(pose, poseAlvo(s, now));
    }
    return pose;
  }
```

- [ ] **Step 4: Rodar para ver passar**

Run: `node tools/test_combat_scene.js`
Expected: `46 passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(combate): pose do atacante — investida, coice a distancia e fumble

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Hand-off, `pendingFor`, poses do alvo (acerto/esquiva/crítico), hit-stop e shake

**Files:**
- Modify: `src/combatScene.js`
- Modify: `tools/test_combat_scene.js`

- [ ] **Step 1: Acrescentar os testes**

```js
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
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_combat_scene.js`
Expected: `TypeError: CS.pendingFor is not a function`.

- [ ] **Step 3: Implementar hand-off, pose do alvo e shake**

Substitua `function poseAlvo(s, now) { return null; }` e acrescente antes de `phaseOf`:

```js
  function pendingFor(targetKey) {
    const s = scenes.find(x => !x.done && x.targetKey === targetKey && !x.impact);
    return s ? s.id : null;
  }

  // Entrega o feedback de dano à cena pendente do alvo. Devolve o comando
  // `impact` quando o golpe JÁ aconteceu (rede lenta) — o chamador executa na
  // hora; senão null (guardado para o IMPACTO).
  function handoff(targetKey, data, now) {
    const s = scenes.find(x => !x.done && x.targetKey === targetKey && !x.impact);
    if (!s) return null;
    s.impact = { feedback: data.feedback || null, death: !!data.death, onImpact: data.onImpact || [] };
    if (s.impactAt == null) return null;
    if (s.impact.death && s.deathAt == null) { s.deathAt = now; agitar(now); }
    const cmds = [];
    emitirImpacto(s, cmds, now);
    return cmds[0];
  }

  function agitar(now) {
    shakes.push({ start: now, ms: D(cfg.crit.shakeMs), amp: cfg.crit.shakeAmp, seed: Math.random() * 6.28 });
  }

  function shake(now) {
    let x = 0, y = 0, any = false;
    for (let i = shakes.length - 1; i >= 0; i--) {
      const sh = shakes[i], p = (now - sh.start) / Math.max(1e-6, sh.ms);
      if (p >= 1) { shakes.splice(i, 1); continue; }
      any = true;
      const env = (1 - p) * (1 - p);
      x += Math.sin(now * 0.11 + sh.seed) * sh.amp * env;
      y += Math.sin(now * 0.17 + sh.seed * 1.3) * sh.amp * 0.6 * env;
    }
    return any ? { x, y } : null;
  }

  // Progresso da reação do alvo em [0,1]: sem crítico é linear em hit/dodge.ms;
  // com crítico o impacto entra direto no pico (0,5), congela pelo hit-stop e
  // completa a segunda metade depois.
  function progressoReacao(s, now) {
    const dur = (s.result && s.result.hit) ? D(cfg.hit.ms) : D(cfg.dodge.ms);
    const t = now - s.impactAt;
    if (!(s.result && s.result.crit)) return clamp01(t / dur);
    const hold = D(cfg.crit.hitStopMs);
    if (t < hold) return 0.5;
    return 0.5 + 0.5 * clamp01((t - hold) / (dur * 0.5));
  }

  function poseAlvo(s, now) {
    if (s.impactAt == null || !s.result || now < s.impactAt) return null;
    if (s.impact && s.impact.death && s.deathAt != null) return poseMorte(s, now);
    const d = s.dir, p = progressoReacao(s, now);
    if (p >= 1) return null;
    const wave = Math.sin(p * Math.PI);
    if (!s.result.hit) return { dx: 0, dz: 0, tilt: cfg.dodge.angle * wave, tiltDir: d };
    const crit = s.result.crit;
    const push = (crit ? cfg.crit.push : cfg.hit.push) * wave;
    let flash = 0;
    if (crit) {
      const tf = now - s.impactAt, fm = D(cfg.crit.flashMs);
      if (tf < fm) flash = cfg.crit.flashPeak * (1 - Math.abs(2 * tf / fm - 1));
    }
    return { dx: d[0] * push, dz: d[1] * push, tilt: cfg.hit.angle * wave, tiltDir: d, flash };
  }

  function poseMorte(s, now) { return null; }   // Task 5
```

Em `irParaImpacto`, logo após `s.impactAt = now;`, acrescente o shake do crítico/morte:

```js
    if ((s.result && s.result.crit) || (s.impact && s.impact.death)) agitar(now);
```

Exporte também `pendingFor, handoff, shake`.

- [ ] **Step 4: Rodar para ver passar**

Run: `node tools/test_combat_scene.js`
Expected: `73 passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(combate): hand-off do dano, reacao do alvo, hit-stop e shake

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Morte — `isDying` e a pose do tombo

**Files:**
- Modify: `src/combatScene.js`
- Modify: `tools/test_combat_scene.js`

- [ ] **Step 1: Acrescentar os testes**

```js
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
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_combat_scene.js`
Expected: `TypeError: CS.isDying is not a function`.

- [ ] **Step 3: Implementar**

Substitua `function poseMorte(s, now) { return null; }` por:

```js
  function isDying(key) {
    return scenes.some(s => !s.done && s.targetKey === key && s.impact && s.impact.death);
  }

  // Tombo: gira 90° em torno do eixo horizontal perpendicular ao golpe (cai para
  // longe do atacante), quica, escurece e desvanece. Pivô = base do peão (a raiz
  // do Group fica no chão), então a peça "tomba" apoiada nos pés.
  function poseMorte(s, now) {
    const t = now - s.deathAt, fall = D(cfg.death.fallMs), total = deathTotalMs();
    if (t < 0 || t >= total) return null;
    const p = t / fall;
    let tilt, scaleY = 1;
    if (p < 1) tilt = (Math.PI / 2) * easeIn(p);
    else {
      const q = clamp01((t - fall) / Math.max(1e-6, total - fall)), b = Math.sin(q * Math.PI);
      tilt = Math.PI / 2 - (cfg.death.bounceDeg * Math.PI / 180) * b;
      scaleY = 1 - (1 - cfg.death.squashY) * b;
    }
    const fade = D(cfg.death.fadeMs);
    const opacity = t > total - fade ? clamp01((total - t) / Math.max(1e-6, fade)) : 1;
    const darken = 1 - (1 - cfg.death.darken) * easeIn(clamp01(p));
    return { dx: 0, dz: 0, tilt, tiltDir: s.dir, scaleY, opacity, darken, dying: true };
  }
```

Exporte `isDying`.

- [ ] **Step 4: Rodar para ver passar**

Run: `node tools/test_combat_scene.js`
Expected: `93 passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(combate): pose de morte (tombo, quique, fade) e isDying

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Configuração em `visualConfig.js`, carga no `index.html` e checagens estáticas

**Files:**
- Modify: `src/visualConfig.js` (bloco `feedback.combat`, logo após `hitReaction`)
- Modify: `index.html` (segundo `document.write` de scripts)
- Modify: `tools/test_combat_scene.js`

- [ ] **Step 1: Acrescentar as checagens estáticas ao teste**

```js
console.log("\n[33] Fiação estática (index.html, visualConfig, game.js)");
const indexHtml = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
const iCS = indexHtml.indexOf("src/combatScene.js"), iGame = indexHtml.indexOf('"game.js?v=');
check("index.html carrega src/combatScene.js", iCS > 0);
check("combatScene.js vem ANTES de game.js", iCS > 0 && iGame > iCS);
const vcSrc = fs.readFileSync(path.join(raiz, "src", "visualConfig.js"), "utf8");
check("visualConfig tem feedback.combat.scene", /scene:\s*\{/.test(vcSrc) && /waitDieMs/.test(vcSrc));
const gameSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
function corpoDaFuncao(nome) {
  const i = gameSrc.indexOf("\nfunction " + nome + "(");
  if (i < 0) return "";
  const j = gameSrc.indexOf("\n}\n", i);
  return gameSrc.slice(i, j);
}
const diff = corpoDaFuncao("_detectHpChanges");
check("_detectHpChanges existe", diff.length > 0);
check("diff de HP consulta CombatScene.pendingFor ANTES de _spawnCombatFeedback",
  diff.indexOf("CombatScene.pendingFor") > 0 && diff.indexOf("CombatScene.pendingFor") < diff.indexOf("_spawnCombatFeedback("));
check("diff de HP consulta CombatScene.pendingFor ANTES de _triggerHitReaction",
  diff.indexOf("CombatScene.pendingFor") > 0 && diff.indexOf("CombatScene.pendingFor") < diff.indexOf("_triggerHitReaction("));
check("gancho do d20 chama CombatScene.dieSettled", gameSrc.includes("CombatScene.dieSettled("));
check("laço 3D aplica a pose (_aplicarPoseCena)", gameSrc.includes("_aplicarPoseCena(fig"));
check("shake subtrai antes de controls.update", gameSrc.indexOf("_desfazerShakeCamera();") > 0 && gameSrc.indexOf("_desfazerShakeCamera();") < gameSrc.indexOf("if(!configCamera.seguindoPeao) g3.controls.update();"));
check("configure é chamado no game.js", gameSrc.includes("CombatScene.configure("));
```

- [ ] **Step 2: Rodar — as checagens de `game.js` devem falhar (as de index/visualConfig também, por ora)**

Run: `node tools/test_combat_scene.js`
Expected: `[33]` com ❌ em todas exceto `_detectHpChanges existe`.

- [ ] **Step 3: `visualConfig.js` — acrescentar o bloco depois de `hitReaction: { ... },`**

```js
      // Cena de combate do 3D (investida sincronizada com o d20; crítico e
      // morte exagerados). Lido por CombatScene.configure em game.js.
      scene: {
        enabled: true,
        meleeRange: 1.5,
        windup:   { dist: 0.15, ms: 180 },
        strike:   { dist: 0.35, ms: 110, tiltX: 0.12 },
        recover:  { ms: 220, overshoot: 0.03 },
        ranged:   { recoil: 0.10, msOut: 90, msBack: 200 },
        fumble:   { dist: 0.50, wobbleCycles: 2 },
        hit:      { angle: 0.14, ms: 260, push: 0.12 },
        dodge:    { angle: 0.08, ms: 200 },
        crit:     { push: 0.30, flashMs: 140, flashPeak: 0.9, hitStopMs: 80,
                    shakeMs: 140, shakeAmp: 0.06, particles: 18 },
        death:    { fallMs: 380, bounceDeg: 4, darken: 0.35, fadeMs: 200, squashY: 0.85 },
        waitDieMs: 3500,
        expireMs:  6000,
      },
```

- [ ] **Step 4: `index.html` — carregar o módulo antes de `game.js`**

No segundo `document.write(...)` (o que carrega `src/gameState.js`, `src/difficulty.js`, ...), insira logo após a entrada de `src/difficulty.js`:

```js
document.write('<script src="src/combatScene.js?v='+v+'"><\/script>');
```

- [ ] **Step 5: Rodar**

Run: `node tools/test_combat_scene.js`
Expected: em `[33]`, index.html e visualConfig ✅; as 6 de `game.js` ainda ❌ (fecham nas Tasks 7–10).

- [ ] **Step 6: Commit**

```bash
git add src/visualConfig.js index.html tools/test_combat_scene.js
git commit -m "feat(combate): config feedback.combat.scene + carga do CombatScene no index

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: `game.js` — alimentar a cena (attack_feedback, d20, configure, tick, comandos, partículas)

**Files:**
- Modify: `game.js` — funções `_receiveAttackFeedback`, `_spawnGoldParticles`, `startLoop3D`, `init3D`, o bloco `obj.phase='settling'; obj.settleT=0; playSettle();` do d20 3D, e o rodapé de `GS.on(...)`.

- [ ] **Step 1: Helper de chave e executor de comandos** — inserir logo **antes** de `function _receiveAttackFeedback(msg){`:

```js
// ── Cena de combate (CombatScene) — fiação no cliente 3D ─────────────────────
// Os ids de attack_feedback vêm de new_id() (únicos entre heróis e monstros);
// a chave de entidade é a mesma dos _hitReactions / _gatherHpEntries.
function _entityKeyById(id){
  const st = GS.gameState;
  if(!st || id == null) return null;
  const sid = String(id);
  if((st.players || []).some(p => String(p.id) === sid)) return `p:${id}`;
  if((st.monsters || []).some(m => String(m.id) === sid)) return `m:${id}`;
  for(const p of (st.players || []))
    if((p.animados || []).some(a => String(a.id) === sid)) return `a:${id}`;
  if(st.prisoner && st.prisoner.id != null && String(st.prisoner.id) === sid) return 'pr:singleton';
  return null;
}

function _cenaAtiva(){ return !!(mode3D && g3 && window.CombatScene); }

// Executa um comando devolvido por CombatScene.tick/handoff. O `impact` é o
// único que desenha: número flutuante, cue de dano, callbacks (anel/som de
// derrota) e partículas de crítico/morte.
function _executarComandoCena(c){
  if(!c) return;
  if(c.cmd === 'end'){ if(c.death) _renderizarEstadoAtual(); return; }
  if(c.cmd !== 'impact') return;
  const now = performance.now();
  const fb = c.feedback;
  if(fb){
    if(fb.cue) _playCombatCue('damage', fb.cue);
    _spawnCombatFeedback(fb.entry, fb.text, fb.kind, now, fb.damageType, fb.options || {});
  }
  for(const fn of (c.onImpact || [])){
    try{ fn(); }catch(e){ console.warn('combatScene onImpact:', e); }
  }
  // `tardio` = hand-off que chegou DEPOIS do golpe: o burst do crítico já saiu no comando do golpe; só a morte (informação nova) ainda merece partículas.
  if(g3 && c.hit && ((c.crit && !c.tardio) || c.death)){
    const tipo = fb && fb.damageType ? _combatPrimaryDamageType(fb.damageType) : 'physical';
    const corHex = (_combatDamageTypeInfo(tipo).color || '#f4eee2').replace('#', '');
    _spawnBurstParticles(g3.T, g3.scene,
      { x: c.targetPos[0], y: 0.35, z: c.targetPos[1] },
      parseInt(corHex, 16), VC.feedback?.combat?.scene?.crit?.particles ?? 18);
  }
}

function _tickCombatScene(now){
  if(!window.CombatScene) return;
  for(const c of CombatScene.tick(now)) _executarComandoCena(c);
}
```

- [ ] **Step 2: Em `_receiveAttackFeedback`**, logo após `_registrarHistoricoAtaque(msg);` e a linha `const id=String(msg.attack_id), now=performance.now();`, inserir:

```js
  if(_cenaAtiva()){
    const base = {attack_id:id, attacker_key:_entityKeyById(msg.attacker_id), target_key:_entityKeyById(msg.target_id),
      attacker_pos:msg.attacker_pos, target_pos:msg.target_pos};
    if(msg.phase==='start') CombatScene.start(base, now);
    else if(msg.phase==='result') CombatScene.result({...base, hit:!!msg.hit, crit:!!msg.crit,
      natural_critical:!!msg.natural_critical, natural_fumble:!!msg.natural_fumble}, now);
  }
```

- [ ] **Step 3: Gancho do d20** — no d20 3D, localizar o bloco exato:

```js
      obj.phase='settling'; obj.settleT=0;
      playSettle();
```

e inserir logo depois de `playSettle();`:

```js
      if(window.CombatScene) CombatScene.dieSettled({die: obj.dieType, value: obj.value}, performance.now());
```

- [ ] **Step 4: Partículas generalizadas** — substituir `function _spawnGoldParticles(T, scene, pos){ ... }` inteira por:

```js
function _spawnBurstParticles(T, scene, pos, color, n){
  const N = Math.max(1, n | 0);
  const posArr = new Float32Array(N * 3);
  const vels   = [];
  for(let i = 0; i < N; i++){
    posArr[i*3]   = pos.x + (Math.random()-.5)*0.3;
    posArr[i*3+1] = pos.y;
    posArr[i*3+2] = pos.z + (Math.random()-.5)*0.3;
    vels.push({ x:(Math.random()-.5)*1.2, y:1.6+Math.random()*2.0, z:(Math.random()-.5)*1.2 });
  }
  const pGeo = new T.BufferGeometry();
  pGeo.setAttribute('position', new T.BufferAttribute(posArr, 3));
  const pMat = new T.PointsMaterial({
    color, size:0.10,
    transparent:true, opacity:1.0,
    sizeAttenuation:true, depthWrite:false,
  });
  const pts = new T.Points(pGeo, pMat);
  scene.add(pts);
  _particleSystems.push({ pts, pGeo, pMat, vels, N, elapsed:0, duration:800 });
}

// Dourado do dado: começa logo acima da face superior.
function _spawnGoldParticles(T, scene, pos){
  _spawnBurstParticles(T, scene, { x:pos.x, y:pos.y + 0.45, z:pos.z }, 0xffd700, 20);
}
```

- [ ] **Step 5: Tick e shake em `startLoop3D`** — dentro de `function tick(){`, logo após `_updateDiceLoop3D(now);`, inserir `_tickCombatScene(now);`. Depois, substituir as duas linhas

```js
    if(!configCamera.seguindoPeao) g3.controls.update();
    atualizarCamera();   // seguimento suave do peão (quando ativo)
```

por

```js
    _desfazerShakeCamera();   // o offset do frame anterior não pode ser absorvido pelo OrbitControls
    if(!configCamera.seguindoPeao) g3.controls.update();
    atualizarCamera();   // seguimento suave do peão (quando ativo)
    _aplicarShakeCamera(now);
```

e inserir, antes de `function startLoop3D(){`:

```js
// Shake de câmera do crítico/morte. OrbitControls recalcula a câmera a partir de
// position − target a cada update(): o offset precisa ser retirado ANTES e
// posto de volta DEPOIS, senão vira deriva permanente.
function _desfazerShakeCamera(){
  if(g3 && g3._shakeOffset){ g3.camera.position.sub(g3._shakeOffset); g3._shakeOffset = null; }
}
function _reduzMovimento(){
  try{ return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); }
  catch(e){ return false; }
}
function _aplicarShakeCamera(now){
  if(!g3 || !window.CombatScene || _reduzMovimento()) return;
  const sh = CombatScene.shake(now);
  if(!sh) return;
  const T = g3.T, q = g3.camera.quaternion;
  const off = new T.Vector3(1,0,0).applyQuaternion(q).multiplyScalar(sh.x)
    .add(new T.Vector3(0,1,0).applyQuaternion(q).multiplyScalar(sh.y));
  g3.camera.position.add(off);
  g3._shakeOffset = off;
}
```

- [ ] **Step 6: Reset ao (re)criar a cena 3D** — em `function init3D(state){`, logo após `if(g3) dispose3D();`, inserir `if(window.CombatScene) CombatScene.reset();`. E em `function _limparMortesVisuais(){`, no início, `if(window.CombatScene) CombatScene.reset();`.

- [ ] **Step 7: Configurar no rodapé** — logo após a linha `GS.on('diceRoll',    msg  => _receberDadoVisual(msg));`, inserir:

```js
// Cena de combate: números em VC; durações respeitam o modo de animação da
// acessibilidade (instant colapsa a cena — sem investida, número na hora).
if(window.CombatScene) CombatScene.configure({
  cfg: VC.feedback?.combat?.scene,
  duration: _animationProgressDuration,
  instant: () => _animationSpeedMode === 'instant',
});
```

- [ ] **Step 8: Verificar sintaxe e checagens estáticas**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: `game.js` sem erro; em `[33]` passam agora `dieSettled`, `shake subtrai antes`, `configure`; seguem ❌ `pendingFor` (×2) e `_aplicarPoseCena` (Tasks 8 e 9).

- [ ] **Step 9: Commit**

```bash
git add game.js
git commit -m "feat(combate): game.js alimenta a CombatScene (attack_feedback, d20, tick, shake, particulas)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: `game.js` — hand-off do dano no diff de HP

**Files:**
- Modify: `game.js` — função `_detectHpChanges`, ramo `if(hp < prev){`.

- [ ] **Step 1: Substituir o ramo de dano.** Localize dentro de `_detectHpChanges`:

```js
      if(hp < prev){
        if(isMine) heroHurt = true; else creatureHurt = true;
        const amount = Math.max(1, Math.round(prev - hp));
        const damageEvents = damageEventsByKey.get(key) || [];
        const primaryDamageType = _combatPrimaryDamageType(damageTypesByKey.get(key) || ['physical']);
        _playCombatCue('damage', {
          damageType: primaryDamageType,
          repeatKey: `damage:${primaryDamageType}`,
          volume: isMine ? .95 : .72,
        });
        const statuses = [...new Set(damageEvents.map(e => String(e.status || '').trim()).filter(Boolean))];
        const impact = damageEvents.find(e => Array.isArray(e.pos))?.pos;
```

e troque por:

```js
      if(hp < prev){
        if(isMine) heroHurt = true; else creatureHurt = true;
        const amount = Math.max(1, Math.round(prev - hp));
        const damageEvents = damageEventsByKey.get(key) || [];
        const primaryDamageType = _combatPrimaryDamageType(damageTypesByKey.get(key) || ['physical']);
        const cue = {
          damageType: primaryDamageType,
          repeatKey: `damage:${primaryDamageType}`,
          volume: isMine ? .95 : .72,
        };
        const statuses = [...new Set(damageEvents.map(e => String(e.status || '').trim()).filter(Boolean))];
        const impact = damageEvents.find(e => Array.isArray(e.pos))?.pos;
        // Hand-off: se há uma cena de ataque pendente para este alvo, ela é a
        // dona do instante do impacto — número, cue e reação saem no golpe,
        // sincronizados com o d20. Sem cena (magia, armadilha, veneno…), o
        // comportamento abaixo segue intocado.
        if(_cenaAtiva() && CombatScene.pendingFor(key, now)){
          const cmd = CombatScene.handoff(key, {
            feedback: {
              entry: impact ? {...entry, pos: impact} : entry,
              text: `${amount}`, kind: isMine ? 'hero_damage' : 'damage',
              damageType: damageTypesByKey.get(key) || 'physical',
              options: {status: statuses.join(' • '), critical: damageEvents.some(e => e.critical)},
              cue,
            },
            death: false, onImpact: [],
          }, now);
          if(cmd) _executarComandoCena(cmd);
          continue;
        }
        _playCombatCue('damage', cue);
```

(O restante do ramo — `damageIndex`, `fireStart`, `startAt`, `_triggerHitReaction`, `_spawnCombatFeedback` — fica como está.)

- [ ] **Step 2: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: em `[33]` passam as duas de `pendingFor`; só `_aplicarPoseCena` segue ❌.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(combate): diff de HP entrega o dano a cena pendente (hand-off)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: `game.js` — aplicar a pose no laço por peão, materiais do flash, deslize

**Files:**
- Modify: `game.js` — `startLoop3D` (callback `g3.entityGroup.children.forEach(fig => {`), `_disposeEntityTree`, bloco "Deslize fiel (entity_step)" de `renderMap3D`.

- [ ] **Step 1: Funções de aplicação** — inserir antes de `function _desfazerShakeCamera(){`:

```js
// ── Aplicação da pose da cena de combate no peão ─────────────────────────────
// Por CHAVE (o Group pode ser reconstruído no meio da cena). Idempotente: a
// base é gridX/gridY + footprint; ao terminar, restaura uma vez e não escreve
// mais. A inclinação usa rotateOnWorldAxis porque rotation é Euler XYZ e o
// facing (rotation.y) misturaria os eixos.
const _sceneAxis = new (window.THREE ? window.THREE.Vector3 : Object)();
function _figSceneKey(fig){
  const u = fig.userData || {};
  return u.pid != null ? `p:${u.pid}`
    : u.monId != null ? `m:${u.monId}`
    : u.animadoId != null ? `a:${u.animadoId}`
    : u.prisoner ? 'pr:singleton' : null;
}
function _materiaisCena(fig){
  const u = fig.userData;
  if(u._sceneMats) return u._sceneMats;
  const lista = [];
  fig.traverse(o => {
    if(!(o.isMesh || o.isSprite) || !o.material) return;
    const ud = o.userData || {};
    if(ud.isOutline || ud.isGroundDecal || ud.isPulseRing || ud.isSelectionRing) return;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    const clones = mats.map(m => { const c = m.clone(); c.userData._sceneOwned = true; return c; });
    o.material = Array.isArray(o.material) ? clones : clones[0];
    for(const c of clones) lista.push({
      mat: c,
      color: c.color ? c.color.clone() : null,
      emissive: c.emissive ? c.emissive.clone() : null,
      opacity: c.opacity, transparent: c.transparent,
    });
  });
  u._sceneMats = lista;
  return lista;
}
function _pintarMateriaisCena(fig, pose){
  for(const e of _materiaisCena(fig)){
    const m = e.mat, flash = pose.flash || 0;
    if(e.emissive){
      if(flash) m.emissive.setRGB(flash, flash, flash); else m.emissive.copy(e.emissive);
    }
    if(e.color){
      m.color.copy(e.color);
      if(flash && !e.emissive) m.color.addScalar(flash);        // sprites: clareia
      if(pose.darken !== undefined) m.color.multiplyScalar(pose.darken);
    }
    if(pose.opacity !== undefined){ m.transparent = true; m.opacity = e.opacity * pose.opacity; }
    else { m.transparent = e.transparent; m.opacity = e.opacity; }
  }
}
function _restaurarMateriaisCena(fig){
  for(const e of (fig.userData._sceneMats || [])){
    const m = e.mat;
    if(e.color) m.color.copy(e.color);
    if(e.emissive) m.emissive.copy(e.emissive);
    m.opacity = e.opacity; m.transparent = e.transparent;
  }
}
function _aplicarPoseCena(fig, now){
  if(!window.CombatScene) return;
  const key = _figSceneKey(fig);
  if(!key) return;
  const pose = CombatScene.poseFor(key, now);
  const u = fig.userData;
  if(!pose){
    if(u._scenePoseAtiva){
      u._scenePoseAtiva = false;
      fig.position.x = u.gridX + (Number(u.footprintOffsetX) || 0);
      fig.position.z = u.gridY + (Number(u.footprintOffsetZ) || 0);
      fig.rotation.set(0, u._sceneBaseRotY || 0, u._hitBaseRotationZ || 0);
      if(u._sceneBaseScale) fig.scale.copy(u._sceneBaseScale);
      _restaurarMateriaisCena(fig);
    }
    return;
  }
  if(!u._scenePoseAtiva){
    u._scenePoseAtiva = true;
    u._sceneBaseRotY = fig.rotation.y || 0;
    u._sceneBaseScale = fig.scale.clone();
  }
  fig.position.x = u.gridX + (Number(u.footprintOffsetX) || 0) + pose.dx;
  fig.position.z = u.gridY + (Number(u.footprintOffsetZ) || 0) + pose.dz;
  fig.rotation.set(0, u._sceneBaseRotY, 0);
  if(pose.tilt){
    const d = pose.tiltDir;
    _sceneAxis.set(d[1], 0, -d[0]).normalize();      // eixo ⟂ à direção: y × d
    fig.rotateOnWorldAxis(_sceneAxis, pose.tilt);
  }
  const b = u._sceneBaseScale;
  fig.scale.set(b.x, b.y * (pose.scaleY == null ? 1 : pose.scaleY), b.z);
  if(pose.flash || pose.opacity !== undefined || pose.darken !== undefined) _pintarMateriaisCena(fig, pose);
  else if(u._sceneMats) _restaurarMateriaisCena(fig);
}
```

- [ ] **Step 2: Chamar no laço** — em `startLoop3D`, dentro de `g3.entityGroup.children.forEach(fig => {`, localizar a linha `if(isSel) fig.rotation.y += 0.008;` (último statement do callback) e inserir logo depois dela, ainda dentro do callback:

```js
      _aplicarPoseCena(fig, now);
```

- [ ] **Step 3: Descartar os materiais clonados** — em `function _disposeEntityTree(root){`, inserir como primeira linha do corpo:

```js
  for(const e of ((root.userData && root.userData._sceneMats) || [])) e.mat.dispose();   // clones do flash (Material.dispose não toca texturas)
```

- [ ] **Step 4: O deslize pula peões com pose** — no bloco `// ── Deslize fiel (entity_step)` de `renderMap3D`, logo após `if(!mesh) continue;`, inserir:

```js
      if(window.CombatScene && CombatScene.poseFor(_figSceneKey(mesh), performance.now())) continue;
```

- [ ] **Step 5: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: `[33]` toda ✅. Placar: `131 + 11 = 142 passaram, 0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add game.js
git commit -m "feat(combate): laco 3D aplica a pose da cena (investida, reacao, flash)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: `game.js` — morte: hand-off, espera do tombo, herói e cadáver

**Files:**
- Modify: `game.js` — `_capturarMortesVisuais`, `_agendarFimMorteVisual`, `_estadoComMortosVisuais`, `_capturarDerrotasERessurreicoes`, laços de `corp:`/`hero-corpse:` em `renderMap3D`.

- [ ] **Step 1: Hand-off da morte do monstro** — em `_capturarMortesVisuais`, localizar o trecho:

```js
    const kind = _defeatVisualKind(anterior,
      _visualTemAnimacaoDeMagia() ? 'magic' : 'common');
    _spawnDefeatVisual(anterior, kind);
    _playDefeatSound(kind);
```

e trocar por:

```js
    const kind = _defeatVisualKind(anterior,
      _visualTemAnimacaoDeMagia() ? 'magic' : 'common');
    const chaveCena = `m:${id}`;
    const comCena = _cenaAtiva() && !!CombatScene.pendingFor(chaveCena, agora);
    if(!comCena){
      _spawnDefeatVisual(anterior, kind);
      _playDefeatSound(kind);
    }
```

Em seguida, no `_mortesVisuaisPendentes.set(id, { ... })` do mesmo laço, trocar

```js
      maxAte: agora + (aguardarMagia ? MORTE_VISUAL_MAX_MS : MORTE_VISUAL_MIN_MS),
```

por

```js
      maxAte: agora + (comCena ? (VC.feedback?.combat?.scene?.expireMs ?? 6000)
        : aguardarMagia ? MORTE_VISUAL_MAX_MS : MORTE_VISUAL_MIN_MS),
```

E substituir a chamada `_spawnCombatFeedback(anterior, '☠ DERROTADO', 'death', (() => { ... })());` inteira por:

```js
    if(comCena){
      // A cena solta texto, anel e som no golpe (sincronizados com o d20) e
      // segura a cópia visual até o tombo terminar (ver _agendarFimMorteVisual).
      const cmd = CombatScene.handoff(chaveCena, {
        feedback: {entry: anterior, text: '☠ DERROTADO', kind: 'death', damageType: null, options: {}},
        death: true,
        onImpact: [() => { _spawnDefeatVisual(anterior, kind); _playDefeatSound(kind); }],
      }, agora);
      if(cmd) _executarComandoCena(cmd);
    } else {
      _spawnCombatFeedback(
        anterior, '☠ DERROTADO', 'death',
        (() => {
          const inicio = _bolaFogoFeedbackStartAt(anterior);
          return inicio != null ? inicio + (mortesPotenciais > 1 ? morteIndex * 120 : 0)
            : (mortesPotenciais > 1 ? agora + morteIndex * 120 : null);
        })()
      );
    }
```

- [ ] **Step 2: Esperar o tombo** — em `_agendarFimMorteVisual`, dentro de `verificar`, trocar

```js
    if(aguardarMinimo || aguardarAnimacao){
```

por

```js
    const aguardarCena = !!(window.CombatScene && CombatScene.isDying(`m:${id}`)) && agora < atual.maxAte;
    if(aguardarMinimo || aguardarAnimacao || aguardarCena){
```

- [ ] **Step 3: Herói morto continua no tabuleiro enquanto tomba** — substituir `function _estadoComMortosVisuais(state){ ... }` inteira por:

```js
function _estadoComMortosVisuais(state){
  if(!state) return state;
  let out = state;
  // Herói: enquanto a cena o faz tombar, o peão vivo precisa continuar
  // existindo (renderMap3D pula !p.alive). Cópia rasa com alive:true.
  if(window.CombatScene && Array.isArray(state.players)){
    let mudou = false;
    const players = state.players.map(p => {
      if(p && p.alive === false && CombatScene.isDying(`p:${p.id}`)){ mudou = true; return {...p, alive: true, hp: 1}; }
      return p;
    });
    if(mudou) out = { ...out, players };
  }
  if(!Array.isArray(state.monsters) || !_mortesVisuaisPendentes.size)
    return out;
  const agora = performance.now();
  const vivos = state.monsters.filter(m => m && m.hp > 0);
  const presentes = new Set(vivos.map(m => String(m.id)));
  const pendentes = [];
  for(const [id, rec] of _mortesVisuaisPendentes){
    if(agora >= rec.maxAte){
      _mortesVisuaisPendentes.delete(id);
      continue;
    }
    if(!presentes.has(id)) pendentes.push(rec.monster);
  }
  if(!pendentes.length) return out;
  return { ...out, monsters: vivos.concat(pendentes) };
}
```

- [ ] **Step 4: Hand-off da morte do herói** — em `_capturarDerrotasERessurreicoes`, trocar

```js
    if(anterior.alive && !atual.alive){
      _spawnDefeatVisual(atual, 'hero');
      _playDefeatSound('hero');
      _spawnCombatFeedback({pos:atual.pos}, '☠ MORTE DEFINITIVA', 'death', performance.now());
    } else if(!anterior.alive && atual.alive){
```

por

```js
    if(anterior.alive && !atual.alive){
      const chaveCena = `p:${id}`;
      if(_cenaAtiva() && CombatScene.pendingFor(chaveCena, performance.now())){
        const cmd = CombatScene.handoff(chaveCena, {
          feedback: {entry: {pos: atual.pos}, text: '☠ MORTE DEFINITIVA', kind: 'death', damageType: null, options: {}},
          death: true,
          onImpact: [() => { _spawnDefeatVisual(atual, 'hero'); _playDefeatSound('hero'); }],
        }, performance.now());
        if(cmd) _executarComandoCena(cmd);
      } else {
        _spawnDefeatVisual(atual, 'hero');
        _playDefeatSound('hero');
        _spawnCombatFeedback({pos:atual.pos}, '☠ MORTE DEFINITIVA', 'death', performance.now());
      }
    } else if(!anterior.alive && atual.alive){
```

- [ ] **Step 5: Cadáver só aparece quando o tombo acaba** — em `renderMap3D`, trocar

```js
    obterFig(`corp:${c.id}`, JSON.stringify(c), () => build3DCorpse(c));
```

por

```js
    const corpFig = obterFig(`corp:${c.id}`, JSON.stringify(c), () => build3DCorpse(c));
    corpFig.visible = !(window.CombatScene && CombatScene.isDying(`m:${c.id}`));
```

e, no laço de `hero_corpses`, trocar

```js
    obterFig(`hero-corpse:${c.hero_id || c.id}`, JSON.stringify(c), () => build3DCorpse(c), hx, hy);
```

por

```js
    const heroCorpFig = obterFig(`hero-corpse:${c.hero_id || c.id}`, JSON.stringify(c), () => build3DCorpse(c), hx, hy);
    heroCorpFig.visible = !(window.CombatScene && CombatScene.isDying(`p:${c.hero_id || c.id}`));
```

(O comando `end` com `death:true` chama `_renderizarEstadoAtual()` — Task 7 — e o `entitySig` muda porque a cópia sai de `monsters`/`alive` volta a false, então o cadáver é reconstruído visível.)

- [ ] **Step 6: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: tudo ✅.

- [ ] **Step 7: Commit**

```bash
git add game.js
git commit -m "feat(combate): morte tomba antes da lapide — hand-off, espera e heroi

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Prova no navegador

**Files:** nenhum (verificação). Se algo for corrigido, commit próprio.

- [ ] **Step 1: Subir o servidor reiniciado** (`preview_start {name:"game"}` — mata o anterior se estiver rodando: `iniciar.bat` faz isso; pelo Browser pane use `preview_stop` + `preview_start`). Abrir `http://localhost:8765/index.html`, Ctrl+F5.

- [ ] **Step 2: Confirmar que o módulo carregou** — no console (`javascript_tool`): `typeof window.CombatScene` → `"object"`; `CombatScene.cfg().waitDieMs` → `3500`.

- [ ] **Step 3: Partida de teste** — criar sala, escolher Guerreiro, iniciar, entrar na masmorra em modo 3D. Andar até um goblin (7 HP) e atacar.
  - Esperado a olho: o peão recua (~0,15 casa), fica armado enquanto o d20 rola, avança quando o dado assenta, o goblin balança e o número aparece **nesse** instante (não antes). Screenshot no impacto (`computer{action:"screenshot"}` — o tick é curto; tirar 2–3 e ficar com a melhor).
  - Console sem erros (`read_console_messages onlyErrors:true`).

- [ ] **Step 4: Erro** — repetir até um ataque errar: o goblin deve inclinar 0,08 rad sem se deslocar e sem número.

- [ ] **Step 5: Morte** — continuar até o goblin morrer: tomba para longe do guerreiro, escurece, some; só então a lápide aparece; shake e partículas.

- [ ] **Step 6: Crítico** — repetir ataques até um natural 20 (ou usar um alvo `dormindo`, se houver magia de sono disponível): flash branco, empurrão maior, hit-stop e shake. Se em 15 ataques não sair, registrar como "não observado" no resumo — a lógica está coberta pelo teste `[16]`.

- [ ] **Step 7: Ataque de monstro** — deixar o goblin atacar: o mesmo ciclo com o goblin como atacante (o `attack_feedback` do monstro passa pelo mesmo caminho).

- [ ] **Step 8: Modo `instant`** — no painel ⚙️, velocidade de animação = instantânea: ataque sem investida, número na hora, sem shake. Voltar para normal.

- [ ] **Step 9: FPS** — com o medidor de FPS aberto, confirmar que fora do golpe o custo é zero (mesmo FPS de antes; `CombatScene.tick` com lista vazia é um laço vazio).

- [ ] **Step 10: Sinal da inclinação** — se o peão tombar/inclinar **em direção** ao atacante em vez de para longe, o eixo em `_aplicarPoseCena` está invertido: trocar `_sceneAxis.set(d[1], 0, -d[0])` por `_sceneAxis.set(-d[1], 0, d[0])` e re-testar. (Derivação: eixo = y × d = (d.z, 0, −d.x) tomba o topo rumo a d; d aponta do atacante ao alvo, logo "para longe do atacante".)

- [ ] **Step 11: Commit de ajustes (se houver)**

```bash
git add game.js src/combatScene.js src/visualConfig.js
git commit -m "fix(combate): ajustes da prova em navegador

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Documentação (CLAUDE.md)

**Files:**
- Modify: `CLAUDE.md` — acrescentar um bloco `>` no fim da seção "Estado do Projeto", no estilo dos demais.

- [ ] **Step 1: Escrever o bloco**

```markdown
> **Animação de combate híbrida (3D):** o atacante **arma, espera o d20 assentar e
> golpeia**; o alvo balança (acerto) ou esquiva (erro); **crítico e morte** ganham flash
> emissivo, empurrão maior, hit-stop, shake de câmera e partículas; o peão morto **tomba**
> antes de virar lápide. Núcleo: módulo puro `src/combatScene.js` (`window.CombatScene`,
> sem DOM/THREE, testável em node) com **uma cena por `attack_id`** — fases
> `FILA→ARMANDO→ESPERANDO_DADO→GOLPE→(HOLD)→RECUPERANDO→AGUARDANDO_HANDOFF/MORRENDO→FIM`
> — que devolve **poses por chave de entidade** (`poseFor(key, now)` → `{dx,dz,tilt,tiltDir,
> scaleY,flash,opacity,darken}`) e comandos (`impact`/`end`). **Sem mudança de servidor:**
> `attack_feedback` (start/result) já traz tudo. Sincronia: o d20 3D chama
> `CombatScene.dieSettled` ao assentar (`obj.phase='settling'`) e a cena mais antiga com
> `result` consome o primeiro dado; fallbacks `waitDieMs` (3,5 s), `instant` (colapsa),
> `result` sem `start` (só impacto), `expireMs` (6 s). **Hand-off:** `_detectHpChanges`
> entrega o dano (`CombatScene.pendingFor` → `handoff`) à cena, que solta número/cue no
> golpe; sem cena (magia, armadilha, veneno) o caminho antigo segue intocado; 2D não muda.
> **Aplicação** em `_aplicarPoseCena` (fim do laço por peão de `startLoop3D`): base =
> `gridX/gridY + footprintOffset`, inclinação por `rotateOnWorldAxis` (Euler XYZ + facing
> misturaria eixos), materiais **clonados por peão** no primeiro flash (`_sceneMats`,
> descartados em `_disposeEntityTree`). **Shake**: subtrai o offset antes de
> `controls.update()` e soma depois (senão o OrbitControls absorve). **Morte** reusa
> `_mortesVisuaisPendentes` (`_agendarFimMorteVisual` espera `isDying`; herói é reinjetado
> `alive:true` em `_estadoComMortosVisuais`; cadáver `visible=false` até o fim). Números em
> `VC.feedback.combat.scene`. Teste: `tools/test_combat_scene.js` (módulo + checagens
> estáticas de fiação). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-10-animacao-combate-hibrida*`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: animacao de combate hibrida no CLAUDE.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
