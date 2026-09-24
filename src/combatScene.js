// src/combatScene.js
// Cena de combate do 3D: uma máquina de estados por attack_id que decide
// QUANDO o atacante golpeia (sincronizado com o d20) e devolve poses por
// chave de entidade. Puro: sem DOM, sem THREE. Exposto como window.CombatScene
// (browser) / global.CombatScene (node). Spec:
// docs/superpowers/specs/2026-09-10-animacao-combate-hibrida-design.md
(function (root) {
  'use strict';

  // Som do golpe (spec 2026-09-23-sons): só viaja da mensagem até o `impact`.
  const IMPACTOS = ['cortante', 'perfurante', 'contundente', 'natural'];

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
    // O runtime pode sincronizar o golpe com a chegada do resultado do ataque,
    // que ocorre junto da emissão do d20. Mantemos desligado por padrão para
    // preservar a linha do tempo legada dos testes/consumidores externos.
    syncOnResult: false,
    expireMs:  6000,
    projectile: {
      enabled: true,
      msPerTile: { arrow: 55, bolt: 45, spear: 75, item: 90 },
      travelMinMs: 220, travelMaxMs: 900,
      missOvershootTiles: 1,
      fumbleFraction: 0.5,
    },
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
  function reset() {
    scenes.length = 0; shakes.length = 0;
    if (root.CombatScene) root.CombatScene._ultimoLaunch = null;
  }

  // ms por casa do projétil. `mergeCfg` só funde um nível: um override parcial
  // de `msPerTile` (ex.: só `bolt`) substitui o mapa inteiro, e um `kind` fora
  // dele daria NaN → travelMs NaN → GOLPE nunca termina. Cai no default.
  function msPorCasa(kind) {
    const pc = cfg.projectile || {}, mp = pc.msPerTile;
    return (mp && mp[kind]) || (mp && mp.arrow) || DEFAULT_CFG.projectile.msPerTile[kind] || 55;
  }

  // Campo `projectile` do attack_feedback → dict normalizado ou null.
  // `enabled:false` no cfg ignora o campo (o servidor continua mandando).
  function normalizarProjetil(p) {
    if (!p || typeof p !== 'object' || !cfg.projectile || cfg.projectile.enabled === false) return null;
    const kind = ['arrow', 'bolt', 'spear', 'item'].includes(p.kind) ? p.kind : null;
    if (!kind) return null;
    return {
      kind, item_id: p.item_id || null, item_emoji: p.item_emoji || null, item_elemento: p.item_elemento || null,
      area: !!p.area, area_raio: Math.max(0, Number(p.area_raio) || 0), sem_dado: !!p.sem_dado,
    };
  }
  function travelMsDe(kind, distCasas) {
    const pc = cfg.projectile;
    const ms = Math.max(1, distCasas) * msPorCasa(kind);
    return D(Math.max(pc.travelMinMs, Math.min(pc.travelMaxMs, ms)));
  }

  function novaCena(msg, soImpacto, now) {
    // Sem posição → null (nunca [0,0]): `pose.base` nulo deixa o peão onde o
    // render o pôs, em vez de teleportá-lo para a casa (0,0). O servidor sempre
    // manda as duas; isto é cinto-e-suspensório.
    const ap = Array.isArray(msg.attacker_pos) ? msg.attacker_pos : null;
    const tp = Array.isArray(msg.target_pos) ? msg.target_pos : null;
    const aPos = ap ? [Number(ap[0]) || 0, Number(ap[1]) || 0] : null;
    const tPos = tp ? [Number(tp[0]) || 0, Number(tp[1]) || 0] : null;
    let dir = [1, 0], melee = true;
    if (aPos && tPos) {
      const ddx = tPos[0] - aPos[0], ddz = tPos[1] - aPos[1], len = Math.hypot(ddx, ddz) || 1;
      dir = [ddx / len, ddz / len];
      melee = Math.max(Math.abs(ddx), Math.abs(ddz)) <= cfg.meleeRange;
    }
    const pj = normalizarProjetil(msg.projectile);
    if (pj) melee = false;                         // projétil nunca é corpo a corpo
    const distCasas = (aPos && tPos) ? Math.max(Math.abs(tPos[0] - aPos[0]), Math.abs(tPos[1] - aPos[1])) : 1;
    const s = {
      id: String(msg.attack_id),
      attackerKey: msg.attacker_key || null,
      targetKey: msg.target_key || null,
      aPos, tPos,
      dir,
      melee,
      projectile: pj, distCasas,
      impacto: IMPACTOS.indexOf(msg.impacto) >= 0 ? msg.impacto : null,
      travelMs: pj ? travelMsDe(pj.kind, distCasas) : 0,
      launchAt: null,
      soImpacto: !!soImpacto,
      phase: 'FILA', phaseAt: now, createdAt: now,
      result: null, resultAt: null, dieAt: null,
      impactAt: null, holdUntil: null,
      // Hand-offs ACUMULAM (morte + número do mesmo golpe chegam em mensagens
      // separadas): feedbacks/onImpact são drenados (splice) a cada impact emitido.
      impact: { feedbacks: [], onImpact: [], death: false }, handoffs: 0, deathAt: null,
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
    // O servidor envia o resultado imediatamente antes do dice_roll. Quando
    // habilitado pelo runtime, isso libera o golpe durante a animação do d20,
    // sem esperar o dado visual terminar de assentar.
    if (cfg.syncOnResult && s.dieAt == null) s.dieAt = now;
    return s;
  }

  function entrar(s, phase, now) { s.phase = phase; s.phaseAt = now; }

  // GOLPE = lançamento quando há projétil: emite `launch` com o destino já
  // resolvido (erro passa reto 1 casa além; natural 1 cai a meio caminho) e o
  // impacto fica para a CHEGADA (travelMs). Sem projétil, o GOLPE é o de sempre.
  function entrarGolpe(s, now, cmds) {
    entrar(s, 'GOLPE', now);
    if (!s.projectile) return;
    const pc = cfg.projectile, hit = !!(s.result && s.result.hit), fumble = !!(s.result && s.result.fumble);
    const from = s.aPos ? s.aPos.slice() : [0, 0];
    let to = s.tPos ? s.tPos.slice() : from.slice();
    let travelMs = s.travelMs, flightMs = s.travelMs;
    if (fumble) {
      to = [from[0] + (to[0] - from[0]) * pc.fumbleFraction, from[1] + (to[1] - from[1]) * pc.fumbleFraction];
      travelMs = flightMs = Math.round(s.travelMs * pc.fumbleFraction);
      s.travelMs = travelMs;                          // o impacto (sem esquiva) fecha no fim do voo curto
    } else if (!hit) {
      to = [to[0] + s.dir[0] * pc.missOvershootTiles, to[1] + s.dir[1] * pc.missOvershootTiles];
      // A casa a mais voa na velocidade EFETIVA (travelMs já passou pelo clamp
      // e pela duration): o render anda uniforme de from→to em flightMs, então
      // só assim ele cruza o alvo exatamente em travelMs.
      const dist = Math.max(1, s.distCasas);
      flightMs = Math.round(travelMs * (dist + pc.missOvershootTiles) / dist);
    }
    s.launchAt = now;
    const c = {
      cmd: 'launch', id: s.id, attackerKey: s.attackerKey, targetKey: s.targetKey,
      kind: s.projectile.kind, item_id: s.projectile.item_id, item_emoji: s.projectile.item_emoji, item_elemento: s.projectile.item_elemento,
      from, to, dir: s.dir.slice(), travelMs, flightMs, hit, fumble,
      crit: !!(s.result && s.result.crit), area: s.projectile.area, area_raio: s.projectile.area_raio,
    };
    if (root.CombatScene) root.CombatScene._ultimoLaunch = c;   // só para testes
    cmds.push(c);
  }

  // Um `impact` pode carregar `projectile` SEM ter havido um `launch` antes:
  // a cena expira (finalizar) com hand-off guardado e ainda em ARMANDO/
  // ESPERANDO_DADO, ou o modo instant colapsa direto para o impacto. O
  // consumidor tolera isso (não há projétil em voo para retirar).
  // `tardio` marca um comando `impact` emitido por um hand-off que chegou
  // DEPOIS do golpe (ver handoff) — o consumidor usa isso para não repetir
  // partículas/callbacks já disparados no impact do golpe em si.
  function emitirImpacto(s, cmds, tardio) {
    const c = {
      cmd: 'impact', id: s.id,
      attackerKey: s.attackerKey, targetKey: s.targetKey,
      targetPos: s.tPos ? s.tPos.slice() : null, dir: s.dir.slice(),
      hit: !!(s.result && s.result.hit), crit: !!(s.result && s.result.crit),
      fumble: !!(s.result && s.result.fumble),
      projectile: s.projectile ? s.projectile.kind : null,
      impacto: s.impacto,
      area: !!(s.projectile && s.projectile.area),
      area_raio: s.projectile ? s.projectile.area_raio : 0,
      feedbacks: s.impact.feedbacks.splice(0),   // emitido UMA vez
      death: !!s.impact.death,
      onImpact: s.impact.onImpact.splice(0),
      tardio: !!tardio,
    };
    cmds.push(c);
    return c;
  }

  function irParaImpacto(s, now, cmds) {
    s.impactAt = now;
    const crit = !!(s.result && s.result.crit);
    const death = !!s.impact.death;
    if (death && s.deathAt == null) s.deathAt = now;
    if (crit || death) agitar(now);
    if (crit) { s.holdUntil = now + D(cfg.crit.hitStopMs); entrar(s, 'HOLD', now); }
    else entrar(s, 'RECUPERANDO', now);
    return emitirImpacto(s, cmds, false);
  }

  function finalizar(s, cmds, now) {
    if (s.done) return;
    if (s.impactAt == null && s.handoffs > 0) {      // expirou antes do golpe: não perde o número
      s.impactAt = now;
      emitirImpacto(s, cmds, false);
    }
    s.done = true;
    cmds.push({ cmd: 'end', id: s.id, attackerKey: s.attackerKey, targetKey: s.targetKey,
                death: !!s.impact.death });
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
          if (s.result && now - s.phaseAt >= D(cfg.windup.ms)) {
            if (s.dieAt != null || (s.projectile && s.projectile.sem_dado)) entrarGolpe(s, now, cmds);
            else entrar(s, 'ESPERANDO_DADO', now);
          }
          break;
        case 'ESPERANDO_DADO':
          if (!s.result) break;
          if (instantFn()) { irParaImpacto(s, now, cmds); break; }
          if (s.dieAt != null || (s.projectile && s.projectile.sem_dado) || now - s.resultAt >= cfg.waitDieMs)   // timeout: NÃO passa por D()
            entrarGolpe(s, now, cmds);
          break;
        case 'GOLPE': {
          const dur = s.projectile ? s.travelMs : (s.melee ? D(cfg.strike.ms) : D(cfg.ranged.msOut));
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
            if (s.impact.death) entrar(s, 'MORRENDO', now);
            else if (s.handoffs > 0 || !(s.result && s.result.hit) || (s.projectile && s.projectile.area)) finalizar(s, cmds, now);
            else entrar(s, 'AGUARDANDO_HANDOFF', now);
          }
          break;
        }
        case 'AGUARDANDO_HANDOFF':
          if (s.handoffs > 0) {
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
      && !(x.projectile && x.projectile.sem_dado)   // área não rola d20: o dado é de outra cena
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
      return { dx: d[0] * dist, dz: d[1] * dist, tilt: 0, tiltDir: d, base: s.aPos };
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
    return { dx: d[0] * dist, dz: d[1] * dist, tilt, tiltDir: d, base: s.aPos };
  }

  // Acha a cena certa do alvo para receber o hand-off de dano: prioriza a
  // cena que AINDA NÃO golpeou (impactAt==null), não importa quantos hand-offs
  // já acumulou (a morte e o número do mesmo golpe chegam separados) — senão,
  // uma cena atrasada (ex.: dano líquido zero) em AGUARDANDO_HANDOFF roubaria
  // o número de um 2º ataque mais novo no mesmo alvo. Só cai para a "já
  // golpeou" (fallback) quando não há nenhuma pendente, e só se ela ainda
  // espera o SEU número (acertou e nunca recebeu hand-off). `now`, se
  // informado, ignora cena expirada (rAF pode ter pausado numa aba oculta
  // enquanto mensagens de WS chegavam).
  // Entre as cenas que ainda não golpearam, prefere a primeira SEM hand-off
  // (Fúria com 2 golpes no mesmo alvo → cada golpe ganha o seu número);
  // exceção: a primeira que já carrega `impact.death` continua recebendo —
  // a morte e o número do mesmo game_state ficam no mesmo golpe.
  // Cena cujo result JÁ É ERRO nunca é candidata (um erro não tem número a
  // receber): sem isso, o erro absorveria o hand-off do próximo acerto no
  // mesmo alvo. Result desconhecido (null) continua candidato.
  function cenaParaHandoff(targetKey, now) {
    let semImpacto = null, semImpactoLivre = null, comImpacto = null;
    for (const s of scenes) {
      if (s.done || s.targetKey == null || s.targetKey !== targetKey) continue;   // área (sem alvo) nunca recebe hand-off
      if (now != null && now - s.createdAt > cfg.expireMs) continue;
      if (s.impactAt == null) {
        if (s.result && !s.result.hit) continue;
        if (!semImpacto) semImpacto = s;
        if (!semImpactoLivre && s.handoffs === 0) semImpactoLivre = s;
      }
      else if (s.handoffs === 0 && s.result && s.result.hit) { if (!comImpacto) comImpacto = s; }
    }
    if (semImpacto && semImpacto.impact.death) return semImpacto;
    return semImpactoLivre || semImpacto || comImpacto;
  }

  function pendingFor(targetKey, now) {
    const s = cenaParaHandoff(targetKey, now);
    return s ? s.id : null;
  }

  // Instante estimado da CHEGADA de um arremesso de ÁREA que cobre `pos` (null se nenhum).
  // Consultado pelo diff de HP, que roda ANTES de a cena emitir o `launch` (o game_state
  // chega na mesma rajada do start): estima pelo windup + travelMs enquanto não lançou.
  function areaImpactAt(pos, now) {
    if (!Array.isArray(pos)) return null;
    let t = null;
    for (const s of scenes) {
      const pj = s.projectile;
      if (s.done || !pj || !pj.area || !s.tPos) continue;
      if (s.impactAt != null && now >= s.impactAt) continue;      // já chegou
      const d = Math.max(Math.abs(s.tPos[0] - pos[0]), Math.abs(s.tPos[1] - pos[1]));
      if (d > pj.area_raio) continue;
      const eta = s.launchAt != null ? s.launchAt + s.travelMs
                : (s.phaseAt != null && s.phase === 'ARMANDO' ? s.phaseAt : now) + D(cfg.windup.ms) + s.travelMs;
      t = t == null ? eta : Math.max(t, eta);
    }
    return t;
  }

  // Entrega o feedback de dano à cena pendente do alvo. Hand-offs ACUMULAM:
  // feedbacks e callbacks são empilhados e `death` é OR — a morte
  // (_capturarDerrotasERessurreicoes) e o número (_detectHpChanges) do mesmo
  // golpe chegam em chamadas separadas. Devolve o comando `impact` (com
  // `tardio:true`) quando o golpe JÁ aconteceu (rede lenta) — o chamador
  // executa na hora; senão null (guardado para o IMPACTO).
  function handoff(targetKey, data, now) {
    data = data || {};
    const s = cenaParaHandoff(targetKey, now);
    if (!s) return null;
    if (data.feedback) s.impact.feedbacks.push(data.feedback);
    if (Array.isArray(data.onImpact) && data.onImpact.length) s.impact.onImpact.push(...data.onImpact);
    const novaMorte = !!data.death && !s.impact.death;
    s.impact.death = s.impact.death || !!data.death;
    s.handoffs++;
    if (s.impactAt == null) return null;
    const jaEraCrit = !!(s.result && s.result.crit);
    if (novaMorte && s.deathAt == null) {
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

  function pulseShake(now, ms = 160, amp = 0.025, seed = Math.random() * 6.28) {
    if (!Number.isFinite(now)) return;
    shakes.push({ start: now, ms: Math.max(1, Number(ms) || 160),
      amp: Math.max(0, Number(amp) || 0), seed: Number.isFinite(seed) ? seed : 0 });
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
    if (s.impact.death && s.deathAt != null) return poseMorte(s, now);
    const d = s.dir, p = progressoReacao(s, now);
    if (p >= 1) return null;
    const wave = Math.sin(p * Math.PI);
    if (!s.result.hit) {
      if (s.projectile && s.result.fumble) return null;   // o projétil caiu antes: o alvo nem esquiva
      return { dx: 0, dz: 0, tilt: cfg.dodge.angle * wave, tiltDir: d, base: s.tPos };
    }
    const crit = s.result.crit;
    const push = (crit ? cfg.crit.push : cfg.hit.push) * wave;
    let flash = 0;
    if (crit) {
      const tf = now - s.impactAt, fm = D(cfg.crit.flashMs);
      if (tf < fm) flash = cfg.crit.flashPeak * (1 - Math.abs(2 * tf / fm - 1));
    }
    return { dx: d[0] * push, dz: d[1] * push, tilt: cfg.hit.angle * wave, tiltDir: d, flash, base: s.tPos };
  }

  function isDying(key) {
    return scenes.some(s => !s.done && s.targetKey === key && s.impact.death);
  }

  // Tombo: gira 90° em torno do eixo horizontal perpendicular ao golpe (cai para
  // longe do atacante), quica, escurece e desvanece. Pivô = base do peão (a raiz
  // do Group fica no chão), então a peça "tomba" apoiada nos pés.
  function poseMorte(s, now) {
    const t = now - s.deathAt, fall = D(cfg.death.fallMs), total = deathTotalMs();
    if (t < 0) return null;
    if (t >= total)   // pose terminal congelada: nunca "pisca" de volta antes do end da cena
      return { dx: 0, dz: 0, tilt: Math.PI / 2, tiltDir: s.dir, scaleY: 1, opacity: 0, darken: cfg.death.darken, dying: true, base: s.tPos };
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
    return { dx: 0, dz: 0, tilt, tiltDir: s.dir, scaleY, opacity, darken, dying: true, base: s.tPos };
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
      base: a.base || b.base,
    };
  }

  // Toda pose carrega `base:[x,z]` — a casa AUTORITATIVA vinda do servidor no
  // attack_feedback (aPos/tPos). O consumidor deve partir dela, não da casa que
  // tinha em cache: um monstro que anda (entity_step) e ataca no mesmo turno
  // não recebe game_state entre o passo e o golpe.
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
    pendingFor, handoff, shake, pulseShake, isDying, areaImpactAt,
    cfg: () => cfg,
    _scenes: scenes,     // só para testes
    _ultimoLaunch: null, // só para testes: último comando `launch` emitido
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
