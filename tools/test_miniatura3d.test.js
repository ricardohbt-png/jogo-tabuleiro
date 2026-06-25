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

console.log("Task 1 OK");
