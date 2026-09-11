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
    // Não cumulativo: cada chamada recomeça do DEFAULT_CFG e dos defaults de
    // duration/instant — configure({}) é um reset completo, não um no-op.
    cfg = mergeCfg(DEFAULT_CFG, opts.cfg || {});
    durationFn = (typeof opts.duration === 'function') ? opts.duration : (ms => ms);
    instantFn  = (typeof opts.instant  === 'function') ? opts.instant  : (() => false);
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

  // `tardio` marca um comando `impact` emitido por um hand-off que chegou
  // DEPOIS do golpe (ver handoff) — o consumidor usa isso para não repetir
  // partículas/callbacks já disparados no impact do golpe em si.
  function emitirImpacto(s, cmds, tardio) {
    const c = {
      cmd: 'impact', id: s.id,
      attackerKey: s.attackerKey, targetKey: s.targetKey,
      targetPos: s.tPos.slice(), dir: s.dir.slice(),
      hit: !!(s.result && s.result.hit), crit: !!(s.result && s.result.crit),
      fumble: !!(s.result && s.result.fumble),
      feedback: s.impact ? s.impact.feedback || null : null,
      death: !!(s.impact && s.impact.death),
      onImpact: s.impact ? s.impact.onImpact || [] : [],
      tardio: !!tardio,
    };
    if (s.impact) s.feedbackEmitido = true;
    cmds.push(c);
    return c;
  }

  function irParaImpacto(s, now, cmds) {
    s.impactAt = now;
    const crit = !!(s.result && s.result.crit);
    const death = !!(s.impact && s.impact.death);
    if (death && s.deathAt == null) s.deathAt = now;
    if (crit || death) agitar(now);
    if (crit) { s.holdUntil = now + D(cfg.crit.hitStopMs); entrar(s, 'HOLD', now); }
    else entrar(s, 'RECUPERANDO', now);
    return emitirImpacto(s, cmds, false);
  }

  function finalizar(s, cmds, now) {
    if (s.done) return;
    if (s.impact && !s.feedbackEmitido) {      // expirou antes do golpe: não perde o número
      if (s.impactAt == null) s.impactAt = now;
      emitirImpacto(s, cmds, false);
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
      if (now - s.createdAt > cfg.expireMs) { finalizar(s, cmds, now); continue; }   // timeout: NÃO passa por D()
      switch (s.phase) {
        case 'FILA': {
          const ocupado = scenes.some(o => o !== s && !o.done && o.attackerKey
            && o.attackerKey === s.attackerKey && scenes.indexOf(o) < scenes.indexOf(s)
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
          if (s.dieAt != null || now - s.resultAt >= cfg.waitDieMs) entrar(s, 'GOLPE', now);   // timeout: NÃO passa por D()
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
    const s = scenes.find(x => !x.done && x.result && x.dieAt == null && x.impactAt == null
      && now - x.createdAt <= cfg.expireMs);   // rAF pode ter pausado: ignora cena já expirada
    if (!s) return null;
    s.dieAt = now;
    return s;
  }

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

  // Acha a cena certa do alvo para receber o hand-off de dano: prioriza a
  // cena que AINDA NÃO golpeou (impactAt==null) — senão, uma cena atrasada
  // (ex.: dano líquido zero) em AGUARDANDO_HANDOFF roubaria o número de um
  // 2º ataque mais novo no mesmo alvo. Só cai para a "já golpeou" (fallback)
  // quando não há nenhuma pendente. `now`, se informado, ignora cena expirada
  // (rAF pode ter pausado numa aba oculta enquanto mensagens de WS chegavam).
  function cenaParaHandoff(targetKey, now) {
    let semImpacto = null, comImpacto = null;
    for (const s of scenes) {
      if (s.done || s.targetKey !== targetKey || s.impact) continue;
      if (now != null && now - s.createdAt > cfg.expireMs) continue;
      if (s.impactAt == null) { if (!semImpacto) semImpacto = s; }
      else { if (!comImpacto) comImpacto = s; }
    }
    return semImpacto || comImpacto;
  }

  function pendingFor(targetKey, now) {
    const s = cenaParaHandoff(targetKey, now);
    return s ? s.id : null;
  }

  // Entrega o feedback de dano à cena pendente do alvo. Devolve o comando
  // `impact` (com `tardio:true`) quando o golpe JÁ aconteceu (rede lenta) —
  // o chamador executa na hora; senão null (guardado para o IMPACTO).
  function handoff(targetKey, data, now) {
    data = data || {};
    const s = cenaParaHandoff(targetKey, now);
    if (!s) return null;
    s.impact = { feedback: data.feedback || null, death: !!data.death, onImpact: data.onImpact || [] };
    if (s.impactAt == null) return null;
    const jaEraCrit = !!(s.result && s.result.crit);
    if (s.impact.death && s.deathAt == null) {
      s.deathAt = now;
      if (!jaEraCrit) agitar(now);   // crítico já agitou no golpe; não duplicar
    }
    const cmds = [];
    emitirImpacto(s, cmds, true);
    return cmds[0];
  }

  function agitar(now) {
    shakes.push({ start: now, ms: D(cfg.crit.shakeMs), amp: cfg.crit.shakeAmp, seed: Math.random() * 6.28 });
  }

  function shake(now) {
    let x = 0, y = 0, any = false;
    for (let i = shakes.length - 1; i >= 0; i--) {
      const sh = shakes[i], p = Math.max(0, (now - sh.start) / Math.max(1e-6, sh.ms));
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

  function isDying(key) {
    return scenes.some(s => !s.done && s.targetKey === key && s.impact && s.impact.death);
  }

  // Tombo: gira 90° em torno do eixo horizontal perpendicular ao golpe (cai para
  // longe do atacante), quica, escurece e desvanece. Pivô = base do peão (a raiz
  // do Group fica no chão), então a peça "tomba" apoiada nos pés.
  function poseMorte(s, now) {
    const t = now - s.deathAt, fall = D(cfg.death.fallMs), total = deathTotalMs();
    if (t < 0) return null;
    if (t >= total)   // pose terminal congelada: nunca "pisca" de volta antes do end da cena
      return { dx: 0, dz: 0, tilt: Math.PI / 2, tiltDir: s.dir, scaleY: 1, opacity: 0, darken: cfg.death.darken, dying: true };
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

  function phaseOf(id) { const s = scenes.find(x => x.id === String(id) && !x.done); return s ? s.phase : null; }

  root.CombatScene = {
    configure, reset, start, result, dieSettled, tick, phaseOf, poseFor,
    pendingFor, handoff, shake, isDying,
    cfg: () => cfg,
    _scenes: scenes,     // só para testes
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
