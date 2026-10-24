/* Cinemáticas cartum do jogo: peças de tabuleiro que "atuam sozinhas" num canvas 2D.
 *
 * Módulo sem dependências (nem THREE, nem GS): `Cinematica.desenhar(ctx, w, h, t, textos, id)` pinta o quadro do
 * instante `t` (segundos) — função pura do tempo, então dá para pular, rever e testar em qualquer ponto — e
 * `Cinematica.iniciar(canvas, id, opts)` toca em tempo real. Cada cinemática é um id em `CENAS`.
 *
 * Cena `gilo_morte`: o Gilo Dedos Sujos, cercado pelos escorpiões da praça, derruba a moeda de prata sem cunho que
 * liga a caravana ao assassino, tenta alcançá-la e diz as últimas palavras (a dica da serra). Não mostra o Olho:
 * quem o tem, em cada ramo da campanha, já foi decidido em outro lugar. */
(function (root) {
  'use strict';
  const W = 1280, H = 720;
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const eo = t => 1 - Math.pow(1 - clamp(t), 3);
  const eio = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const TINTA = '#1d130c';
  const FONTE = '"Comic Sans MS","Chalkboard SE","Trebuchet MS",sans-serif';

  const PADRAO = {
    falas: ['Calma, bichinhos... eu só queria ir embora.',
            'Ah, desgraça! A minha moeda!',
            'A caravana... já levou o Olho...',
            '...serra acima.'],
    tec: 'TEC!'
  };

  // ── Peças ────────────────────────────────────────────────────────────────
  function base(ctx, rx) {
    ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.beginPath(); ctx.ellipse(4, 6, rx + 6, 17, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#2b2220'; ctx.strokeStyle = TINTA; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.ellipse(0, 0, rx, 16, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#4a3a33'; ctx.beginPath(); ctx.ellipse(0, -3, rx - 8, 11, 0, 0, 7); ctx.fill();
  }

  function chapeu(ctx) {
    ctx.fillStyle = '#5b3a22'; ctx.strokeStyle = TINTA; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-17, -4); ctx.quadraticCurveTo(-12, -48, 4, -52); ctx.quadraticCurveTo(14, -30, 17, -4);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(0, -2, 40, 10, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#c8a24a'; ctx.fillRect(-16, -14, 32, 6); ctx.strokeRect(-16, -14, 32, 6);
  }

  // olhar: -1..1 ; rosto: 'normal' | 'medo' | 'morto'
  function gilo(ctx, o) {
    ctx.save();
    ctx.translate(o.x, o.y); ctx.scale(o.s * (o.sx || 1), o.s * (o.sy || 1));
    if (o.rot) { ctx.translate(42, 0); ctx.rotate(o.rot); ctx.translate(-42, 0); }
    base(ctx, 46);
    // capa
    ctx.fillStyle = '#7a4a2a'; ctx.strokeStyle = TINTA; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-36, -8);
    for (let i = 0; i <= 6; i++) ctx.lineTo(-36 + i * 12, -8 + (i % 2 ? -10 : 4));
    ctx.lineTo(28, -92); ctx.quadraticCurveTo(0, -104, -28, -92); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#9a6a3f'; ctx.beginPath(); ctx.moveTo(-8, -92); ctx.lineTo(8, -92); ctx.lineTo(4, -30); ctx.lineTo(-4, -30);
    ctx.closePath(); ctx.fill();
    // cinto e bolsa de moedas
    ctx.fillStyle = '#3a2414'; ctx.fillRect(-30, -52, 60, 9); ctx.strokeRect(-30, -52, 60, 9);
    if (!o.semBolsa) {
      ctx.fillStyle = '#c8a24a'; ctx.beginPath(); ctx.arc(22, -40, 9, 0, 7); ctx.fill(); ctx.stroke();
    }
    // cabeça, barba, olhos
    ctx.fillStyle = '#e0a77a'; ctx.beginPath(); ctx.arc(0, -112, 25, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#2a1a12'; ctx.beginPath(); ctx.arc(0, -108, 25, .15, Math.PI - .15); ctx.quadraticCurveTo(0, -78, 0, -78);
    ctx.fill(); ctx.stroke();
    const medo = o.rosto === 'medo', morto = o.rosto === 'morto', ol = (o.olhar || 0) * 4;
    for (const dx of [-10, 10]) {
      if (morto) {
        ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(dx - 5, -122); ctx.lineTo(dx + 5, -112);
        ctx.moveTo(dx + 5, -122); ctx.lineTo(dx - 5, -112); ctx.stroke(); ctx.lineWidth = 4;
      } else {
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(dx, -118, medo ? 8 : 6, medo ? 10 : 7, 0, 0, 7); ctx.fill(); ctx.stroke();
        ctx.fillStyle = TINTA; ctx.beginPath(); ctx.arc(dx + ol, -118, medo ? 2.5 : 3.4, 0, 7); ctx.fill();
        ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(dx - 7, medo ? -132 : -131 + (dx < 0 ? 0 : 0)); ctx.lineTo(dx + 7, medo ? -134 : -127 - (dx < 0 ? -3 : 3) + 3);
        ctx.stroke(); ctx.lineWidth = 4;
      }
    }
    // balestra
    if (o.arma) {
      ctx.save(); ctx.translate(34, -62); ctx.rotate(o.armaRot || 0);
      ctx.fillStyle = '#8a5a30'; ctx.fillRect(0, -4, 34, 8); ctx.strokeRect(0, -4, 34, 8);
      ctx.beginPath(); ctx.moveTo(26, -16); ctx.quadraticCurveTo(38, 0, 26, 16); ctx.lineWidth = 5; ctx.stroke();
      if (o.clarao) {
        ctx.fillStyle = '#ffe36b'; ctx.beginPath();
        for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2, r = i % 2 ? 12 : 26; ctx.lineTo(44 + Math.cos(a) * r, Math.sin(a) * r); }
        ctx.closePath(); ctx.fill(); ctx.lineWidth = 3; ctx.stroke();
      }
      ctx.restore();
    }
    if (!o.semChapeu) { ctx.save(); ctx.translate(0, -130); chapeu(ctx); ctx.restore(); }
    ctx.restore();
  }

  function escorpiao(ctx, o) {
    const T = o.t || 0, bate = Math.abs(Math.sin(T * (o.nervoso ? 14 : 5))) * (o.nervoso ? 14 : 6);
    ctx.save();
    ctx.translate(o.x, o.y); ctx.scale(o.s * (o.flip ? 1 : (o.dir || 1)) * (o.sx || 1), o.s * (o.sy || 1));
    if (o.rot) ctx.rotate(o.rot);
    base(ctx, 54);
    ctx.strokeStyle = TINTA; ctx.lineWidth = 3.5;
    // pernas
    for (const d of [-1, 1]) for (let i = 0; i < 3; i++) {
      const bx = d * (14 + i * 11), ex = d * (34 + i * 12), ey = -2 + Math.sin(T * 9 + i + d) * 3;
      ctx.beginPath(); ctx.moveTo(bx, -22); ctx.lineTo(ex, ey - 10); ctx.lineTo(ex + d * 6, ey); ctx.stroke();
    }
    // cauda (segmentos) com ferrão
    const bal = Math.sin(T * 3 + (o.fase || 0)) * 0.12 + (o.ataque || 0);
    ctx.fillStyle = '#8b6b4a';
    let px = -24, py = -40, ang = Math.PI * 1.12 + bal;
    for (let i = 0; i < 6; i++) {
      ang += 0.34; px += Math.cos(ang) * 17; py += Math.sin(ang) * 17;
      ctx.beginPath(); ctx.arc(px, py, 10 - i * 0.7, 0, 7); ctx.fill(); ctx.stroke();
    }
    ctx.fillStyle = '#d6453a'; ctx.beginPath();
    ctx.moveTo(px - 7, py - 2); ctx.lineTo(px + 6, py + 24 + (o.ataque || 0) * 30); ctx.lineTo(px + 9, py - 4);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    // corpo
    ctx.fillStyle = '#9a7a56'; ctx.beginPath(); ctx.ellipse(0, -28, 38, 24, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#7d5f40'; ctx.beginPath(); ctx.ellipse(-4, -34, 22, 11, 0, 0, 7); ctx.fill();
    // garras (abrem e fecham)
    for (const d of [-1, 1]) {
      const gx = d * 46 + d * bate * 0.4, gy = -34 - Math.abs(d) * 4;
      ctx.fillStyle = '#9a7a56';
      ctx.beginPath(); ctx.moveTo(d * 28, -30); ctx.lineTo(gx - d * 4, gy); ctx.lineWidth = 8; ctx.stroke(); ctx.lineWidth = 3.5;
      ctx.beginPath(); ctx.arc(gx, gy, 15, 0, 7); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#1d130c'; ctx.beginPath(); ctx.moveTo(gx + d * 8, gy - 3 - bate * 0.3); ctx.lineTo(gx + d * 26, gy);
      ctx.lineTo(gx + d * 8, gy + 3 + bate * 0.3); ctx.closePath(); ctx.fill();
    }
    // olhos zangados
    for (const d of [-1, 1]) {
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(d * 11, -44, 7, 8, 0, 0, 7); ctx.fill(); ctx.stroke();
      ctx.fillStyle = TINTA; ctx.beginPath(); ctx.arc(d * 11 + (o.olhar || 0) * 3, -43, 3, 0, 7); ctx.fill();
      ctx.beginPath(); ctx.moveTo(d * 11 - d * 9, -55 + (d < 0 ? 0 : 0)); ctx.lineTo(d * 11 + d * 3, -50); ctx.stroke();
    }
    ctx.restore();
  }

  function moeda(ctx, x, y, r, rot, brilho) {
    ctx.save(); ctx.translate(x, y);
    if (brilho > 0) {
      const g = ctx.createRadialGradient(0, 0, 2, 0, 0, 50 * brilho); g.addColorStop(0, 'rgba(255,248,200,.9)'); g.addColorStop(1, 'rgba(255,248,200,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, 50 * brilho, 0, 7); ctx.fill();
    }
    ctx.scale(Math.abs(Math.cos(rot)) * 0.85 + 0.15, 1);
    ctx.fillStyle = '#d9dde2'; ctx.strokeStyle = TINTA; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = '#9aa0a8'; ctx.beginPath(); ctx.arc(0, 0, r * 0.6, 0, 7); ctx.stroke();
    ctx.restore();
  }

  function estrela(ctx, x, y, r, rot) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = '#ffe36b'; ctx.strokeStyle = TINTA; ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? r * 0.45 : r; ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
    ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
  }

  function balao(ctx, texto, x, y, quem, p) {
    if (p <= 0) return;
    const sc = eo(p * 2.2);
    ctx.save(); ctx.font = 'bold 27px ' + FONTE;
    const max = 360, palavras = String(texto).split(' '), linhas = [];
    let l = '';
    for (const w of palavras) { const t = l ? l + ' ' + w : w; if (ctx.measureText(t).width > max && l) { linhas.push(l); l = w; } else l = t; }
    if (l) linhas.push(l);
    const wBox = Math.min(max, Math.max(...linhas.map(s => ctx.measureText(s).width))) + 34, hBox = linhas.length * 34 + 22;
    ctx.translate(x, y); ctx.scale(sc, sc);
    ctx.fillStyle = '#fffdf4'; ctx.strokeStyle = TINTA; ctx.lineWidth = 4;
    const bx = -wBox / 2, by = -hBox - 26, r = 20;
    ctx.beginPath(); ctx.moveTo(bx + r, by); ctx.arcTo(bx + wBox, by, bx + wBox, by + hBox, r); ctx.arcTo(bx + wBox, by + hBox, bx, by + hBox, r);
    ctx.lineTo(8, by + hBox); ctx.lineTo(0, by + hBox + 24 + (quem === 'g' ? 0 : 0)); ctx.lineTo(-10, by + hBox);
    ctx.arcTo(bx, by + hBox, bx, by, r); ctx.arcTo(bx, by, bx + wBox, by, r); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = TINTA; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    linhas.forEach((s, i) => ctx.fillText(s, 0, by + 28 + i * 34));
    ctx.restore();
  }

  function onomatopeia(ctx, texto, x, y, p) {
    if (p <= 0 || p >= 1) return;
    const sc = 0.6 + eo(p * 4) * 0.7;
    ctx.save(); ctx.translate(x, y); ctx.rotate(-0.15); ctx.scale(sc, sc); ctx.globalAlpha = 1 - seg(p, 0.6, 1);
    ctx.font = '900 64px ' + FONTE; ctx.textAlign = 'center'; ctx.lineJoin = 'round';
    ctx.strokeStyle = TINTA; ctx.lineWidth = 12; ctx.strokeText(texto, 0, 0);
    ctx.fillStyle = '#ffd23a'; ctx.fillText(texto, 0, 0); ctx.restore();
  }

  // ── Cenário ──────────────────────────────────────────────────────────────
  function cenario(ctx) {
    const c = ctx.createLinearGradient(0, 0, 0, 300);
    c.addColorStop(0, '#5a3a6a'); c.addColorStop(.6, '#d9784f'); c.addColorStop(1, '#f2b25f');
    ctx.fillStyle = c; ctx.fillRect(0, 0, W, 300);
    ctx.fillStyle = '#ffe9a8'; ctx.beginPath(); ctx.arc(1010, 215, 52, 0, 7); ctx.fill();
    // casario ao fundo
    ctx.strokeStyle = TINTA; ctx.lineWidth = 4;
    const casas = [[20, 170, 150, 130], [180, 120, 120, 180], [310, 190, 170, 110], [500, 140, 130, 160], [660, 200, 150, 100],
                   [830, 130, 120, 170], [970, 180, 140, 120], [1120, 110, 150, 190]];
    casas.forEach(([x, y, w, h], i) => {
      ctx.fillStyle = i % 2 ? '#3b2a45' : '#4a3350'; ctx.fillRect(x, y, w, 300 - y); ctx.strokeRect(x, y, w, 300 - y);
      ctx.fillStyle = '#ffd477';
      for (let j = 0; j < 3; j++) if ((i + j) % 2 === 0) ctx.fillRect(x + 16 + j * 38, y + 26, 18, 24);
    });
    // chão: lajotas
    const g = ctx.createLinearGradient(0, 300, 0, H); g.addColorStop(0, '#7a6475'); g.addColorStop(1, '#2d2433');
    ctx.fillStyle = g; ctx.fillRect(0, 300, W, H - 300); ctx.strokeStyle = TINTA; ctx.beginPath(); ctx.moveTo(0, 300); ctx.lineTo(W, 300); ctx.stroke();
    ctx.strokeStyle = 'rgba(29,19,12,.45)'; ctx.lineWidth = 3;
    for (let r = 0; r < 9; r++) {
      const y = 300 + Math.pow(r / 9, 1.5) * (H - 300) + 10;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    for (let c2 = -8; c2 <= 8; c2++) { ctx.beginPath(); ctx.moveTo(W / 2 + c2 * 36, 300); ctx.lineTo(W / 2 + c2 * 150, H); ctx.stroke(); }
    // emblema da praça
    ctx.strokeStyle = '#b79a6e'; ctx.lineWidth = 7; ctx.beginPath(); ctx.ellipse(640, 480, 400, 150, 0, 0, 7); ctx.stroke();
    ctx.strokeStyle = 'rgba(183,154,110,.5)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(640, 480, 330, 118, 0, 0, 7); ctx.stroke();
  }

  // ── Roteiro ──────────────────────────────────────────────────────────────
  const DUR = 22;
  const G0 = { x: 640, y: 470 };
  const CASA = [{ x: 330, y: 470, d: 1, in: [-140, 500] }, { x: 470, y: 372, d: 1, in: [250, 250] },
                { x: 820, y: 372, d: -1, in: [1420, 330] }, { x: 960, y: 480, d: -1, in: [1420, 580] },
                { x: 660, y: 610, d: 1, in: [700, 860] }];

  function cenaGilo(ctx, t, tx) {
    const f = Object.assign({}, PADRAO, tx || {}), F = f.falas;
    // câmera: aproxima devagar e treme na hora do ataque
    const z = 1 + 0.10 * eio(t / DUR);
    const tremor = (t > 15.2 && t < 17.4) ? Math.sin(t * 60) * 6 : (t > 6.95 && t < 7.15 ? Math.sin(t * 90) * 5 : 0);
    ctx.save(); ctx.translate(W / 2 + tremor, 470); ctx.scale(z, z); ctx.translate(-W / 2, -470);
    cenario(ctx);

    // Gilo
    const G = { x: G0.x, y: G0.y, s: 1.3, olhar: Math.sin(t * 1.3) * 0.8, rosto: 'normal', arma: t > 6.2 && t < 8.4, armaRot: 0, rot: 0 };
    const pass = seg(t, 2.2, 4);
    G.sy = 1 + Math.sin(t * 3) * 0.015;
    if (t > 6.2 && t < 8.4) { G.rosto = 'normal'; G.armaRot = -0.05 - 0.3 * Math.max(0, 1 - (t - 6.9) * 6); G.clarao = t > 6.9 && t < 7.1; }
    if (t > 8.1) G.rosto = 'medo';
    // recuo, tropeço e queda
    const recuo = eio(seg(t, 8.0, 9.0));
    G.x -= recuo * 50;
    if (t > 8.8) G.rot = eio(seg(t, 8.8, 9.7)) * (Math.PI / 2 - 0.12);
    // arrasta-se até a moeda
    const arrasta = eio(seg(t, 10.3, 15.0));
    G.x += arrasta * 260;
    if (t > 10.3 && t < 15.0) G.y += Math.abs(Math.sin(t * 5)) * -5 + 0;
    G.semBolsa = t > 9.0;
    const morte = t > 15.9;
    if (morte) G.rosto = 'morto';
    G.semChapeu = t > 15.5;
    const dir = 1;

    // moeda: arco da bolsa até o chão, quica e fica brilhando
    const mC = { x: 960, y: 566 };
    let mx = null, my = 0, mrot = 0, mbri = 0;
    if (t > 9.0) {
      const p = seg(t, 9.0, 10.2);
      mx = lerp(G0.x - 28, mC.x, eo(p)); my = lerp(G0.y - 40, mC.y, p) - Math.sin(p * Math.PI) * 190 + (p >= 1 ? -Math.abs(Math.sin((t - 10.2) * 9)) * 18 * Math.max(0, 1 - (t - 10.2) * 1.6) : 0);
      mrot = t * 14 * (1 - seg(t, 9.9, 11)); mbri = t > 10.6 ? 0.5 + 0.2 * Math.sin(t * 4) : 0;
    }

    // escorpiões (z-order por y)
    const peças = [];
    CASA.forEach((c, i) => {
      const ent = eo(seg(t, 1.8 + i * 0.25, 4.0 + i * 0.25));
      let x = lerp(c.in[0], c.x, ent), y = lerp(c.in[1], c.y, ent);
      let o = { t, x, y, s: 1.2, dir: c.d, fase: i, olhar: Math.sin(t + i), nervoso: false };
      // aproximam-se aos poucos
      const apert = eio(seg(t, 4.0, 6.8)) * 0.18 + eio(seg(t, 8.0, 9.4)) * 0.45 + eio(seg(t, 14.6, 15.8)) * 0.35;
      const cx = G.x + (G.rot ? 100 : 0), alvoG = { x: cx + c.d * (G.rot ? 150 : 70) * (i === 4 ? 0.3 : 1) + (i - 2) * 6, y: G.y + [-40, -14, -60, 14, 44][i] };
      x = lerp(x, alvoG.x, apert); y = lerp(y, alvoG.y, apert * 0.9);
      if (t > 15.8) { x += Math.sin(t * 40 + i) * 6; o.nervoso = true; }
      if (t > 8.0 && t < 15.8) o.nervoso = i % 2 === 0;
      o.ataque = (t > 9.4 && t < 15.8) ? Math.max(0, Math.sin(t * 6 + i * 2)) * 0.5 : 0;
      // recuam, saciados
      const rec = eio(seg(t, 17.6, 20.2));
      x = lerp(x, c.x + (c.x < G.x ? -120 : 120), rec * 0.8); y = lerp(y, c.y + 20, rec);
      o.x = x; o.y = y;
      // o escorpião 2 leva o virote e sai voando
      if (i === 2 && t > 7.0) {
        const p = seg(t, 7.0, 8.4);
        o.x = lerp(c.x - 60, 1230, eo(p)); o.y = lerp(c.y, 95, eo(p)) - Math.sin(p * Math.PI) * 120;
        o.rot = p * 14; o.flip = true; o.s = lerp(1, 0.5, p); o.dir = 1;
        if (p >= 1) return;
      }
      peças.push({ y: o.y, f: () => escorpiao(ctx, o) });
    });
    peças.push({ y: G.rot ? G.y + 60 : G.y, f: () => gilo(ctx, G) });
    if (mx !== null) peças.push({ y: my + 200, f: () => moeda(ctx, mx, my, 22, mrot, mbri) });
    peças.sort((a, b) => a.y - b.y).forEach(p => p.f());

    // chapéu voa
    if (t > 15.5) {
      const p = seg(t, 15.5, 17.2);
      const hx = lerp(G.x + 10, G.x - 160, p), hy = lerp(G.y - 130, G.y - 10, p) - Math.sin(Math.min(1, p) * Math.PI) * 130;
      ctx.save(); ctx.translate(hx, hy); ctx.rotate(p * 9); ctx.scale(1.05, 1.05); chapeu(ctx); ctx.restore();
    }
    // estrelinhas no escorpião atingido
    if (t > 7.0 && t < 8.6) for (let k = 0; k < 3; k++) {
      const a = t * 6 + k * 2.1, p = seg(t, 7.0, 8.4);
      estrela(ctx, lerp(CASA[2].x - 60, 1230, eo(p)) + Math.cos(a) * 34, lerp(CASA[2].y, 95, eo(p)) - Math.sin(p * Math.PI) * 120 - 30 + Math.sin(a) * 10, 10, a);
    }
    // poeira da briga
    if (t > 15.8 && t < 17.8) for (let k = 0; k < 7; k++) {
      const p = seg(t, 15.8 + k * 0.18, 17.0 + k * 0.18);
      if (p > 0 && p < 1) { ctx.fillStyle = 'rgba(255,255,255,' + (0.7 * (1 - p)) + ')'; ctx.strokeStyle = 'rgba(29,19,12,' + (0.5 * (1 - p)) + ')'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(G.x - 70 + k * 24, G.y - 30 - p * 50, 18 + p * 30, 0, 7); ctx.fill(); ctx.stroke(); }
    }
    ctx.restore();

    // balões e onomatopeia (em coordenadas de tela, sem câmera)
    const gx = (G.rot ? G.x + 110 : G.x), gy = G.y - (G.rot ? 120 : 250);
    if (t > 4.6 && t < 6.6) balao(ctx, F[0], gx, gy, 'g', seg(t, 4.6, 4.9));
    if (t > 9.3 && t < 11.0) balao(ctx, F[1], gx, gy, 'g', seg(t, 9.3, 9.6));
    if (t > 11.6 && t < 14.0) balao(ctx, F[2], gx, gy, 'g', seg(t, 11.6, 11.9));
    if (t > 14.1 && t < 15.7) balao(ctx, F[3], gx, gy, 'g', seg(t, 14.1, 14.4));
    onomatopeia(ctx, f.tec, G.x + 190, G.y - 170, seg(t, 6.9, 7.8));

    // vinheta e fade
    const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
    const esc = 0.35 + 0.35 * seg(t, 15.8, 19);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(10,5,15,' + esc + ')');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
    const fade = Math.max(1 - seg(t, 0, 1), seg(t, DUR - 1.2, DUR));
    if (fade > 0) { ctx.fillStyle = 'rgba(0,0,0,' + fade + ')'; ctx.fillRect(0, 0, W, H); }
  }

  const CENAS = { gilo_morte: { dur: DUR, desenhar: cenaGilo } };

  function desenhar(ctx, w, h, t, textos, id) {
    const c = CENAS[id || 'gilo_morte']; if (!c) return;
    // Enquadramento: cobre a tela, mas nunca corta mais de ~28% da largura (a ação cabe nesse miolo); em telas muito
    // quadradas sobram faixas escuras em cima e embaixo. O foco fica um pouco à direita (a vítima rasteja para lá).
    const cobrir = Math.max(w / W, h / H), conter = Math.min(w / W, h / H);
    const sc = Math.max(conter, Math.min(cobrir, w / (W * 0.72)));
    const tx = W * sc <= w ? (w - W * sc) / 2 : Math.min(0, Math.max(w - W * sc, w / 2 - 665 * sc));
    ctx.save(); ctx.setTransform(sc, 0, 0, sc, tx, (h - H * sc) / 2);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    c.desenhar(ctx, clamp(t, 0, c.dur), textos); ctx.restore();
  }

  // ── Execução em tempo real ───────────────────────────────────────────────
  function iniciar(canvas, id, opts) {
    opts = opts || {};
    const cena = CENAS[id]; if (!cena || !canvas) return null;
    const ctx = canvas.getContext('2d');
    let t0 = performance.now(), raf = 0, parado = false, fim = false;
    function ajustar() {
      const r = canvas.getBoundingClientRect(), d = Math.min(2, root.devicePixelRatio || 1);
      const w = Math.max(2, Math.round(r.width * d)), h = Math.max(2, Math.round(r.height * d));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    }
    function quadro(agora) {
      if (parado) return;
      if (!canvas.isConnected || canvas.offsetParent === null) { parado = true; return; }   // overlay fechado
      ajustar();
      const t = (agora - t0) / 1000;
      desenhar(ctx, canvas.width, canvas.height, t, opts.textos, id);
      if (t >= cena.dur && !fim) { fim = true; if (opts.onFim) opts.onFim(); }
      if (t < cena.dur + 0.05) raf = requestAnimationFrame(quadro);
    }
    raf = requestAnimationFrame(quadro);
    return {
      parar() { parado = true; cancelAnimationFrame(raf); },
      reiniciar() { t0 = performance.now(); fim = false; if (parado) { parado = false; } cancelAnimationFrame(raf); raf = requestAnimationFrame(quadro); },
      terminou() { return fim; }
    };
  }

  root.Cinematica = { iniciar, desenhar, ids: Object.keys(CENAS), duracao: id => (CENAS[id] || {}).dur || 0 };
})(typeof window !== 'undefined' ? window : globalThis);
