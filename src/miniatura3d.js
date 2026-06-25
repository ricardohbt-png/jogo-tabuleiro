"use strict";
// src/miniatura3d.js — pipeline PURO de silhueta PNG → contornos → Mesh extrudado.
// Helpers geométricos não tocam DOM/THREE (testáveis em Node). build() recebe THREE
// por injeção (não importa) para respeitar a regra de renderização do projeto.
(function (root) {

  // ── Marching squares: máscara binária (1=opaco) → laços fechados de cantos. ──
  // Retorna array de laços; cada laço é array de [x,y] (cantos), fechado (1º=último).
  function marchingSquares(mask, w, h) {
    const W = w + 2, H = h + 2;                 // padding transparente (fecha contornos)
    const g = new Uint8Array(W * H);
    for (let y = 0; y < h; y++)
      for (let x = 0; x < w; x++)
        g[(y + 1) * W + (x + 1)] = mask[y * w + x] ? 1 : 0;
    const at = (x, y) => (x < 0 || y < 0 || x >= W || y >= H) ? 0 : g[y * W + x];

    // Segmentos direcionados (inside à esquerda) por célula de cantos (x,y).
    // Edges: T=(x+.5,y) R=(x+1,y+.5) B=(x+.5,y+1) L=(x,y+.5). Coords no espaço de
    // cantos da máscara ORIGINAL → subtrai 1 do padding ao emitir.
    const segs = [];
    const key = p => p[0] + "," + p[1];
    for (let y = 0; y < H - 1; y++) {
      for (let x = 0; x < W - 1; x++) {
        const tl = at(x, y), tr = at(x + 1, y), br = at(x + 1, y + 1), bl = at(x, y + 1);
        const c = (tl << 3) | (tr << 2) | (br << 1) | bl;
        if (c === 0 || c === 15) continue;
        const T = [x, y - 0.5], R = [x + 0.5, y],
              B = [x, y + 0.5], L = [x - 0.5, y];
        const push = (a, b) => segs.push([a, b]);
        switch (c) {
          case 1:  push(L, B); break;            // bl
          case 2:  push(B, R); break;            // br
          case 3:  push(L, R); break;            // bl+br
          case 4:  push(R, T); break;            // tr
          case 5:  push(L, T); push(R, B); break; // tr+bl (sela: separa)
          case 6:  push(B, T); break;            // br+tr
          case 7:  push(L, T); break;            // tr+br+bl
          case 8:  push(T, L); break;            // tl
          case 9:  push(T, B); break;            // tl+bl
          case 10: push(T, R); push(B, L); break; // tl+br (sela)
          case 11: push(T, R); break;            // tl+br+bl
          case 12: push(R, L); break;            // tl+tr
          case 13: push(R, B); break;            // tl+tr+bl
          case 14: push(B, L); break;            // tl+tr+br
        }
      }
    }

    // Encadeia segmentos em laços fechados, seguindo start→end.
    const fromStart = new Map();
    for (const s of segs) {
      const k = key(s[0]);
      if (!fromStart.has(k)) fromStart.set(k, []);
      fromStart.get(k).push(s);
    }
    const used = new Set();
    const loops = [];
    for (const s0 of segs) {
      if (used.has(s0)) continue;
      const loop = [s0[0].slice()];
      let cur = s0; used.add(cur);
      for (let guard = 0; guard < segs.length + 5; guard++) {
        loop.push(cur[1].slice());
        const cand = (fromStart.get(key(cur[1])) || []).find(s => !used.has(s));
        if (!cand) break;
        used.add(cand); cur = cand;
        if (key(cur[1]) === key(loop[0])) { loop.push(cur[1].slice()); break; }
      }
      if (loop.length >= 4) loops.push(loop);
    }
    return loops;
  }

  const api = { marchingSquares: marchingSquares };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.Miniatura3D = api;
})(typeof window !== "undefined" ? window : null);
