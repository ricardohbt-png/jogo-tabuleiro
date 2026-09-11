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
    cfg = mergeCfg(DEFAULT_CFG, opts.cfg || {});   // não cumulativo: cada chamada recomeça do DEFAULT_CFG
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

  function phaseOf(id) { const s = scenes.find(x => x.id === String(id) && !x.done); return s ? s.phase : null; }

  root.CombatScene = {
    configure, reset, start, result, dieSettled, tick, phaseOf, poseFor,
    cfg: () => cfg,
    _scenes: scenes,     // só para testes
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
