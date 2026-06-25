"use strict";
const assert = require("assert");
const M = require("../src/miniatura3d.js");

// 4x4 totalmente opaco → um único laço externo cobrindo a borda externa.
{
  const mask = new Uint8Array(16).fill(1);
  const loops = M.marchingSquares(mask, 4, 4);
  assert.strictEqual(loops.length, 1, "quadrado sólido = 1 laço");
  // laço fechado: primeiro ponto == último
  const lp = loops[0];
  assert.ok(lp.length >= 4, "laço tem >=4 vértices");
  const a = lp[0], b = lp[lp.length - 1];
  assert.ok(Math.abs(a[0] - b[0]) < 1e-9 && Math.abs(a[1] - b[1]) < 1e-9, "laço fechado");
  // bounding box do laço cobre [0..4]x[0..4]
  const xs = lp.map(p => p[0]), ys = lp.map(p => p[1]);
  assert.strictEqual(Math.min(...xs), 0); assert.strictEqual(Math.max(...xs), 4);
  assert.strictEqual(Math.min(...ys), 0); assert.strictEqual(Math.max(...ys), 4);
}

// Anel 5x5 (borda opaca, centro 3x3 vazado) → 2 laços (externo + buraco).
{
  const w = 5, h = 5, mask = new Uint8Array(w * h).fill(1);
  for (let y = 1; y < 4; y++) for (let x = 1; x < 4; x++) mask[y * w + x] = 0;
  const loops = M.marchingSquares(mask, w, h);
  assert.strictEqual(loops.length, 2, "anel = 2 laços (externo + interno)");
}

// Empty mask → 0 loops
{
  const loops = M.marchingSquares(new Uint8Array(4), 2, 2);
  assert.strictEqual(loops.length, 0, "empty mask = 0 loops");
}
// Single opaque pixel → 1 closed loop
{
  const loops = M.marchingSquares(new Uint8Array([1]), 1, 1);
  assert.strictEqual(loops.length, 1, "1x1 pixel = 1 loop");
  const lp = loops[0];
  const a = lp[0], b = lp[lp.length - 1];
  assert.ok(Math.abs(a[0]-b[0]) < 1e-9 && Math.abs(a[1]-b[1]) < 1e-9, "1x1 loop closed");
}

// simplifyPath: um quadrado denso vira ~4-5 vértices.
{
  const square = [];
  for (let i = 0; i <= 10; i++) square.push([i, 0]);
  for (let i = 1; i <= 10; i++) square.push([10, i]);
  for (let i = 9; i >= 0; i--) square.push([i, 10]);
  for (let i = 9; i >= 0; i--) square.push([0, i]);
  square.push([0, 0]);
  const s = M.simplifyPath(square, 0.5);
  assert.ok(s.length <= 6, "quadrado simplificado <=6 vértices, veio " + s.length);
  assert.ok(s.length >= 4, "quadrado mantém >=4 vértices");
}

// classifyLoops: anel → 1 externo + 1 buraco.
{
  const outer = [[0,0],[10,0],[10,10],[0,10],[0,0]];
  const hole  = [[3,3],[7,3],[7,7],[3,7],[3,3]];
  const cls = M.classifyLoops([outer, hole]);
  assert.strictEqual(cls.length, 1, "1 shape externo");
  assert.strictEqual(cls[0].holes.length, 1, "com 1 buraco");
}
// edgeColorHex: imageData só com pixels vermelhos opacos → ~vermelho.
{
  const w = 4, h = 4, data = new Uint8ClampedArray(w * h * 4);
  for (let i = 0; i < w * h; i++) { data[i*4]=200; data[i*4+1]=30; data[i*4+2]=30; data[i*4+3]=255; }
  const hex = M.edgeColorHex({ data, width: w, height: h });
  assert.strictEqual(typeof hex, "number");
  assert.ok((hex >> 16 & 255) > (hex >> 8 & 255), "componente vermelho domina");
}

// cleanMask: remove ilhas de ruído e preenche buracos → 1 blob sólido.
{
  // 10x10: bloco 6x6 sólido (1..6) + 1 pixel de ruído isolado no canto + 1
  // buraco interno no centro do bloco.
  const w = 10, h = 10, m = new Uint8Array(w * h);
  for (let y = 2; y <= 7; y++) for (let x = 2; x <= 7; x++) m[y * w + x] = 1;
  m[4 * w + 4] = 0;              // buraco interno
  m[0] = 1;                      // ilha de ruído isolada no canto
  const c = M.cleanMask(m, w, h);
  assert.strictEqual(c[0], 0, "ilha de ruído removida");
  assert.strictEqual(c[4 * w + 4], 1, "buraco interno preenchido");
  assert.strictEqual(c[2 * w + 2], 1, "bloco principal preservado");
  // o resultado é um único componente 4-conexo
  const loops = M.marchingSquares(c, w, h);
  assert.strictEqual(loops.length, 1, "blob limpo = 1 contorno");
}
// cleanMask: NÃO faz "tecido" num checkerboard (mantém só 1 célula = maior comp.)
{
  const w = 10, h = 10, c = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) { const x = i % w, y = (i / w) | 0; if ((x + y) % 2 === 0) c[i] = 1; }
  const cleaned = M.cleanMask(c, w, h);
  let count = 0; for (let i = 0; i < cleaned.length; i++) count += cleaned[i];
  assert.ok(count <= 4, "checkerboard reduz a um único pixel (maior comp.), veio " + count);
}

console.log("miniatura3d OK (todos os testes)");
