# Miniaturas PNG para decorações (pseudo-3D extrudado) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir, no editor, atribuir a cada decoração um PNG de `assets/objetos/`, renderizado no jogo como uma miniatura pseudo-3D extrudada (silhueta por canal alfa) no 3D, e como imagem plana no 2D e no preview do editor.

**Architecture:** O pipeline PNG→silhueta→`ExtrudeGeometry` vive num módulo de renderização puro/reutilizável `src/miniatura3d.js`, validado primeiro por um demo isolado (`tools/test_miniatura.html`) e depois consumido por `game.js`. O campo `image` é **dado** persistido na decoração (editor → JSON da dungeon → servidor autoritativo → `game_state`). O servidor ganha `objeto_upload`/`list_objetos` espelhando o upload de história/prisioneiro. Decorações sem `image` mantêm 100% o render procedural atual (emoji 2D / box-cyl 3D).

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS + Three.js r128 (cliente/editor/demo); Node.js + `assert` (testes unitários das funções geométricas puras); pytest-style scripts em `tools/test_*.py` (testes do servidor).

---

## Estrutura de arquivos

| Arquivo | Papel | Ação |
|---|---|---|
| `src/miniatura3d.js` | Pipeline puro PNG→silhueta→Mesh extrudado + helpers geométricos puros. `window.Miniatura3D` + `module.exports`. | Criar |
| `tools/test_miniatura3d.test.js` | Testes Node (`assert`) das funções puras (marching squares, simplify, classificação, cor de borda). | Criar |
| `tools/test_miniatura.html` | Demo standalone (Three.js via CDN) que valida a árvore visualmente. | Criar |
| `server.py` | `_OBJETOS_DIR`, `_save_objeto_upload`, `_listar_objetos`, handlers `objeto_upload`/`list_objetos`; `image` em `validar_dungeon`, no load da sala e em `_serializar_decoracoes`. | Modificar |
| `tools/test_objeto_upload.py` | Testes do servidor: upload/listagem/sanitização/path traversal. | Criar |
| `tools/test_decor_image_validar.py` | Testes de `validar_dungeon` p/ o campo `image`. | Criar |
| `tools/story_upload.js` | `uploadObjeto()` e `listObjetos()`; expõe `window.OBJETO_UPLOAD`. | Modificar |
| `tools/editor.js` | Seção "Imagem" no painel da decoração; `image` em place/serialize; preview 2D. | Modificar |
| `index.html` | Carregar `src/miniatura3d.js`. | Modificar |
| `game.js` | Render 2D (PNG no footprint) e 3D (`Miniatura3D.build`) quando `d.image`. | Modificar |
| `tools/test_decor_roundtrip.py` | Estender round-trip p/ incluir `image`. | Modificar |

**Convenção de caminho da imagem:** o campo `image` guarda **apenas o basename** (ex.: `"arvore.png"`), análogo a `prisoner.image`. A URL completa é montada no cliente como `assets/objetos/<image>`.

---

## Pré-checagem do ambiente

- [ ] **Confirmar Node disponível** (para os testes das funções puras)

Run: `node --version`
Expected: imprime uma versão (ex.: `v18...`). Se não houver Node, os testes das Tasks 1–4 não rodam — pare e avise o usuário antes de prosseguir.

---

## Fase 0 — Módulo puro + demo

### Task 1: Marching squares (silhueta → contornos)

**Files:**
- Create: `src/miniatura3d.js`
- Test: `tools/test_miniatura3d.test.js`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_miniatura3d.test.js`:

```js
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

console.log("Task 1 OK");
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `node tools/test_miniatura3d.test.js`
Expected: FAIL — `Cannot find module '../src/miniatura3d.js'`.

- [ ] **Step 3: Implementação mínima**

Criar `src/miniatura3d.js` com o tracer. O módulo expõe via `module.exports` (Node) e via `window.Miniatura3D` (browser). Coordenadas em grade de **cantos** (0..w em X, 0..h em Y); a máscara é padronizada com borda transparente para fechar todos os contornos.

```js
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
        const T = [x + 0.5 - 1, y - 1], R = [x + 1 - 1, y + 0.5 - 1],
              B = [x + 0.5 - 1, y + 1 - 1], L = [x - 1, y + 0.5 - 1];
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_miniatura3d.test.js`
Expected: PASS — imprime `Task 1 OK`.

- [ ] **Step 5: Commit**

```bash
git add src/miniatura3d.js tools/test_miniatura3d.test.js
git commit -m "feat(miniatura): marching squares puro p/ silhueta PNG"
```

---

### Task 2: Simplificação de contorno (Douglas–Peucker)

**Files:**
- Modify: `src/miniatura3d.js`
- Test: `tools/test_miniatura3d.test.js`

- [ ] **Step 1: Acrescentar teste que falha**

Adicionar ao final de `tools/test_miniatura3d.test.js` (antes do `console.log` final mova-o para o fim):

```js
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_miniatura3d.test.js`
Expected: FAIL — `M.simplifyPath is not a function`.

- [ ] **Step 3: Implementar `simplifyPath`**

No `src/miniatura3d.js`, dentro do IIFE antes da linha `const api = {`:

```js
  // Douglas–Peucker para uma POLILINHA aberta (preserva extremos).
  function _dpOpen(pts, tol) {
    if (pts.length < 3) return pts.slice();
    const a = pts[0], b = pts[pts.length - 1];
    let idx = -1, dmax = 0;
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const len2 = dx * dx + dy * dy || 1e-12;
    for (let i = 1; i < pts.length - 1; i++) {
      const px = pts[i][0] - a[0], py = pts[i][1] - a[1];
      const t = (px * dx + py * dy) / len2;
      const cx = px - t * dx, cy = py - t * dy;
      const d = cx * cx + cy * cy;
      if (d > dmax) { dmax = d; idx = i; }
    }
    if (dmax > tol * tol && idx > 0) {
      const left = _dpOpen(pts.slice(0, idx + 1), tol);
      const right = _dpOpen(pts.slice(idx), tol);
      return left.slice(0, -1).concat(right);
    }
    return [a, b];
  }

  // Simplifica um laço FECHADO (1º==último). Mantém o fechamento.
  function simplifyPath(loop, tol) {
    if (loop.length < 4) return loop.slice();
    const open = loop.slice(0, -1);                  // tira o ponto duplicado de fecho
    const simplified = _dpOpen(open.concat([open[0]]), tol || 0.75);
    return simplified;                               // já volta com 1º==último
  }
```

E acrescentar à `api`: `simplifyPath: simplifyPath,`.

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_miniatura3d.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/miniatura3d.js tools/test_miniatura3d.test.js
git commit -m "feat(miniatura): simplificação Douglas-Peucker de contorno"
```

---

### Task 3: Classificar laços (externo vs buraco) e cor de borda

**Files:**
- Modify: `src/miniatura3d.js`
- Test: `tools/test_miniatura3d.test.js`

- [ ] **Step 1: Acrescentar teste que falha**

```js
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_miniatura3d.test.js`
Expected: FAIL — `M.classifyLoops is not a function`.

- [ ] **Step 3: Implementar `classifyLoops` e `edgeColorHex`**

```js
  function _area(loop) {                  // área com sinal (shoelace)
    let a = 0;
    for (let i = 0; i < loop.length - 1; i++)
      a += loop[i][0] * loop[i + 1][1] - loop[i + 1][0] * loop[i][1];
    return a / 2;
  }
  function _pointInLoop(pt, loop) {
    let inside = false;
    for (let i = 0, j = loop.length - 2; i < loop.length - 1; j = i++) {
      const xi = loop[i][0], yi = loop[i][1], xj = loop[j][0], yj = loop[j][1];
      const hit = ((yi > pt[1]) !== (yj > pt[1])) &&
        (pt[0] < (xj - xi) * (pt[1] - yi) / ((yj - yi) || 1e-12) + xi);
      if (hit) inside = !inside;
    }
    return inside;
  }
  // Agrupa laços em shapes {outer, holes}. Buraco = laço contido em outro de maior área.
  function classifyLoops(loops) {
    const sorted = loops.slice().sort((a, b) => Math.abs(_area(b)) - Math.abs(_area(a)));
    const shapes = [];
    for (const lp of sorted) {
      const probe = lp[0];
      const parent = shapes.find(s => _pointInLoop(probe, s.outer));
      if (parent) parent.holes.push(lp);
      else shapes.push({ outer: lp, holes: [] });
    }
    return shapes;
  }
  // Cor média (hex 0xRRGGBB) dos pixels opacos — base p/ as laterais "plástico".
  function edgeColorHex(imageData) {
    const d = imageData.data; let r = 0, g = 0, b = 0, n = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] > 128) { r += d[i]; g += d[i + 1]; b += d[i + 2]; n++; }
    }
    if (!n) return 0x888888;
    r = (r / n) | 0; g = (g / n) | 0; b = (b / n) | 0;
    // escurece ~30% p/ dar leitura de "lateral"
    r = (r * 0.7) | 0; g = (g * 0.7) | 0; b = (b * 0.7) | 0;
    return (r << 16) | (g << 8) | b;
  }
```

E acrescentar à `api`: `classifyLoops: classifyLoops, edgeColorHex: edgeColorHex,`.

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_miniatura3d.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/miniatura3d.js tools/test_miniatura3d.test.js
git commit -m "feat(miniatura): classificação externo/buraco + cor de borda"
```

---

### Task 4: `build()` — silhueta → Mesh extrudado (THREE injetado)

**Files:**
- Modify: `src/miniatura3d.js`

> Render puro: validado visualmente na Task 5 (sem teste unitário — depende de canvas/THREE).

- [ ] **Step 1: Implementar `imageToMask` e `build`**

No `src/miniatura3d.js`, antes da `api`:

```js
  // PNG (HTMLImageElement já carregado) → {mask,w,h,imageData} reduzido a maxSide.
  function imageToMask(image, opts) {
    const maxSide = (opts && opts.maxSide) || 128;
    const alphaThresh = (opts && opts.alphaThresh) || 128;
    const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
    const w = Math.max(1, Math.round(image.width * scale));
    const h = Math.max(1, Math.round(image.height * scale));
    const cv = document.createElement("canvas");
    cv.width = w; cv.height = h;
    const cx = cv.getContext("2d");
    cx.drawImage(image, 0, 0, w, h);
    const imageData = cx.getImageData(0, 0, w, h);
    const mask = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i++) mask[i] = imageData.data[i * 4 + 3] > alphaThresh ? 1 : 0;
    return { mask, w, h, imageData };
  }

  // Constrói o Group da miniatura. THREE injetado. opts:
  //  { image, tileSize=1, thickness(0.05–0.08*tileSize), maxSide, alphaThresh, simplifyTol }
  // Orientação: largura→X, altura→Y(cima), espessura→Z. Origem no CENTRO DA BASE.
  function build(THREE, opts) {
    const image = opts.image;
    const tileSize = opts.tileSize || 1;
    const thickness = opts.thickness != null ? opts.thickness : tileSize * 0.06;
    const { mask, w, h, imageData } = imageToMask(image, opts);
    const tol = opts.simplifyTol != null ? opts.simplifyTol : 0.75;

    const loopsRaw = marchingSquares(mask, w, h).map(l => simplifyPath(l, tol));
    const shapes = classifyLoops(loopsRaw);
    const sideColor = edgeColorHex(imageData);

    const group = new THREE.Group();
    if (!shapes.length) return group;

    // Escala: encaixar a silhueta em ~0.9*tileSize de largura; Y para cima.
    const worldW = tileSize * 0.9;
    const s = worldW / w;
    const toShape = (loop) => {
      const sh = new THREE.Shape();
      loop.forEach((p, i) => {
        const X = p[0] * s, Y = (h - p[1]) * s;   // inverte Y (imagem desce, mundo sobe)
        i === 0 ? sh.moveTo(X, Y) : sh.lineTo(X, Y);
      });
      return sh;
    };

    const silhouette = [];
    for (const sp of shapes) {
      const sh = toShape(sp.outer);
      sh.holes = sp.holes.map(holeLoop => {
        const hp = new THREE.Path();
        holeLoop.forEach((p, i) => {
          const X = p[0] * s, Y = (h - p[1]) * s;
          i === 0 ? hp.moveTo(X, Y) : hp.lineTo(X, Y);
        });
        return hp;
      });
      silhouette.push(sh);
    }

    const geo = new THREE.ExtrudeGeometry(silhouette, {
      depth: thickness, bevelEnabled: true, bevelThickness: thickness * 0.25,
      bevelSize: thickness * 0.25, bevelSegments: 1, steps: 1,
    });
    // UV da frente/verso pelo bounding box (textura = a arte do PNG).
    geo.computeBoundingBox();
    const bb = geo.boundingBox, sx = 1 / (bb.max.x - bb.min.x || 1), sy = 1 / (bb.max.y - bb.min.y || 1);
    const pos = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pos.count; i++) {
      uv.setXY(i, (pos.getX(i) - bb.min.x) * sx, (pos.getY(i) - bb.min.y) * sy);
    }
    uv.needsUpdate = true;

    // Materiais: grupo 0 = faces (ExtrudeGeometry separa front/back de side via groups).
    // ExtrudeGeometry cria 2 groups: 0 = tampas(frente/verso), 1 = laterais.
    const tex = new THREE.Texture(imageData2Canvas(imageData));
    tex.needsUpdate = true;
    const faceMat = new THREE.MeshStandardMaterial({
      map: tex, transparent: true, alphaTest: 0.5, roughness: 0.85, metalness: 0,
    });
    const sideMat = new THREE.MeshStandardMaterial({ color: sideColor, roughness: 0.9, metalness: 0 });
    const mesh = new THREE.Mesh(geo, [faceMat, sideMat]);
    mesh.castShadow = true; mesh.receiveShadow = true;

    // Centraliza em X e apoia a base em Y=baseTop; espessura ao longo de Z.
    geo.computeBoundingBox();
    const cx2 = (geo.boundingBox.max.x + geo.boundingBox.min.x) / 2;
    const minY = geo.boundingBox.min.y;
    mesh.position.set(-cx2, -minY, 0);          // pés na base, centrado em X
    mesh.rotation.x = 0;                         // fica em PÉ (plano XY, espessura Z)

    // Base oval integrada no chão.
    const baseGeo = new THREE.CylinderGeometry(worldW * 0.5, worldW * 0.55, thickness * 1.5, 24);
    const baseMat = new THREE.MeshStandardMaterial({ color: sideColor, roughness: 0.95, metalness: 0 });
    const base = new THREE.Mesh(baseGeo, baseMat);
    base.scale.set(1, 1, 0.6);                   // oval (achata em Z)
    base.position.set(0, thickness * 0.75, 0);
    base.castShadow = true; base.receiveShadow = true;

    group.add(base); group.add(mesh);
    return group;
  }

  // ImageData → <canvas> (textura usável pelo THREE no browser).
  function imageData2Canvas(imageData) {
    const cv = document.createElement("canvas");
    cv.width = imageData.width; cv.height = imageData.height;
    cv.getContext("2d").putImageData(imageData, 0, 0);
    return cv;
  }
```

E acrescentar à `api`: `imageToMask: imageToMask, build: build,`.

- [ ] **Step 2: Sanidade (sintaxe)**

Run: `node -e "require('./src/miniatura3d.js'); console.log('load ok')"`
Expected: imprime `load ok` (carrega sem erro de sintaxe; `build`/`imageToMask` só rodam no browser).

- [ ] **Step 3: Commit**

```bash
git add src/miniatura3d.js
git commit -m "feat(miniatura): build() extrusao + materiais + base (THREE injetado)"
```

---

### Task 5: Demo standalone (validação visual da árvore)

**Files:**
- Create: `tools/test_miniatura.html`

- [ ] **Step 1: Criar o demo**

```html
<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8"><title>Demo miniatura</title>
<style>html,body{margin:0;height:100%;background:#1a1410;color:#e8d8b8;font-family:sans-serif}
#ui{position:fixed;top:8px;left:8px;z-index:2;font-size:13px}
input{width:60px}</style></head>
<body>
<div id="ui">
  PNG: <input id="url" style="width:260px" value="../assets/objetos/arvore.png"> 
  alfa<input id="alpha" type="number" value="128"> 
  maxSide<input id="max" type="number" value="128"> 
  tol<input id="tol" type="number" step="0.1" value="0.75">
  <button id="go">gerar</button>
</div>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="../src/miniatura3d.js"></script>
<script>
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x1a1410);
const cam = new THREE.PerspectiveCamera(45, innerWidth/innerHeight, 0.01, 100);
cam.position.set(1.4, 1.2, 1.8);
const rndr = new THREE.WebGLRenderer({antialias:true}); rndr.setSize(innerWidth,innerHeight);
rndr.shadowMap.enabled = true; rndr.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(rndr.domElement);
const ctrl = new THREE.OrbitControls(cam, rndr.domElement); ctrl.enableDamping = true;
scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const dir = new THREE.DirectionalLight(0xffffff, 0.9); dir.position.set(2,3,2);
dir.castShadow = true; dir.shadow.mapSize.set(1024,1024); scene.add(dir);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(4,4),
  new THREE.MeshStandardMaterial({color:0x2a2018}));
ground.rotation.x = -Math.PI/2; ground.receiveShadow = true; scene.add(ground);
let current = null;
function gerar(){
  const img = new Image(); img.crossOrigin = "anonymous";
  img.onload = () => {
    if (current) scene.remove(current);
    current = Miniatura3D.build(THREE, {
      image: img, tileSize: 1,
      alphaThresh: +document.getElementById("alpha").value,
      maxSide: +document.getElementById("max").value,
      simplifyTol: +document.getElementById("tol").value,
    });
    scene.add(current);
  };
  img.onerror = () => alert("falha ao carregar PNG (rode via http://localhost:8765/tools/test_miniatura.html)");
  img.src = document.getElementById("url").value;
}
document.getElementById("go").onclick = gerar;
(function loop(){ requestAnimationFrame(loop); ctrl.update(); rndr.render(scene,cam); })();
gerar();
</script>
</body></html>
```

- [ ] **Step 2: Validação visual manual**

Garanta o servidor rodando (`python server.py`) e abra `http://localhost:8765/tools/test_miniatura.html`.
Expected: a árvore aparece em pé sobre uma base oval, com a arte do PNG na frente, laterais foscas escuras, sombra no chão, e gira junto ao orbitar a câmera (não é sprite). Ajuste alfa/maxSide/tol e clique "gerar" até o recorte ficar bom. **Confirme com o usuário antes de seguir** para a integração.

- [ ] **Step 3: Commit**

```bash
git add tools/test_miniatura.html
git commit -m "feat(miniatura): demo standalone de validacao visual"
```

---

## Fase 1 — Servidor (dados, upload, listagem)

### Task 6: Upload de objeto (`objeto_upload`)

**Files:**
- Modify: `server.py` (perto de `_save_prisoner_upload`, ~13189; handler perto de `upload_prisoner`, ~12845)
- Test: `tools/test_objeto_upload.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_objeto_upload.py` (espelha `tools/test_story_upload.py`):

```python
import base64, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

def test_aceita_png():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, res = server._save_objeto_upload("teste_obj.png", b64)
    assert ok, res
    assert res == "teste_obj.png"
    p = os.path.join(server._OBJETOS_DIR, "teste_obj.png")
    assert os.path.isfile(p)
    os.remove(p)

def test_rejeita_nao_png():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, _ = server._save_objeto_upload("x.jpg", b64)
    assert not ok

def test_path_traversal():
    b64 = base64.b64encode(PNG_1x1).decode()
    ok, res = server._save_objeto_upload("../server.py", b64)
    # basename neutraliza o diretório; resultado deve ser "server.py" mas .py é rejeitado
    assert not ok

if __name__ == "__main__":
    test_aceita_png(); test_rejeita_nao_png(); test_path_traversal()
    print("test_objeto_upload OK")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_objeto_upload.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute '_save_objeto_upload'`.

- [ ] **Step 3: Implementar no `server.py`**

Após `_save_prisoner_upload` (~13217), adicionar:

```python
OBJETOS_DIR = os.path.join(BASE_DIR, "assets", "objetos")
_OBJETOS_DIR = OBJETOS_DIR
_OBJETOS_OK_EXT = {".png"}

def _save_objeto_upload(name, data_b64):
    """Grava um PNG de objeto em assets/objetos/. Só .png. Mesma proteção
    (path-traversal via basename, tamanho) do _save_story_upload.
    Retorna (ok: bool, basename_salvo | mensagem_de_erro)."""
    base = os.path.basename(name or "")
    if not base or "\x00" in base:
        return False, "nome inválido"
    ext = os.path.splitext(base)[1].lower()
    if ext not in _OBJETOS_OK_EXT:
        return False, "envie um arquivo .png"
    if not isinstance(data_b64, str) or not data_b64:
        return False, "dados inválidos"
    if (len(data_b64) * 3) // 4 > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except Exception:
        return False, "dados inválidos"
    if len(raw) > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        os.makedirs(OBJETOS_DIR, exist_ok=True)
        with open(os.path.join(OBJETOS_DIR, base), "wb") as f:
            f.write(raw)
    except OSError:
        return False, "falha ao gravar"
    return True, base

def _listar_objetos():
    """Lista os basenames .png de assets/objetos/ (ordenado)."""
    try:
        return sorted(n for n in os.listdir(OBJETOS_DIR)
                      if n.lower().endswith(".png"))
    except OSError:
        return []
```

E o handler, junto aos outros uploads (após o bloco `if t == "upload_prisoner":`, ~12854):

```python
                if t == "objeto_upload":
                    ok, res = _save_objeto_upload(msg.get("name"), msg.get("data"))
                    payload = {"type": "upload_result",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok:
                        payload["name"] = res
                    else:
                        payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue

                if t == "list_objetos":
                    await ws.send(json.dumps({"type": "objetos_list",
                                              "upload_id": msg.get("upload_id"),
                                              "objetos": _listar_objetos()}))
                    continue
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_objeto_upload.py`
Expected: PASS — `test_objeto_upload OK`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_objeto_upload.py
git commit -m "feat(server): objeto_upload + list_objetos (assets/objetos)"
```

---

### Task 7: `image` em validar_dungeon / load / serialização

**Files:**
- Modify: `server.py` (`validar_dungeon` ~1785; load da sala ~3742; `_serializar_decoracoes` ~10241)
- Test: `tools/test_decor_image_validar.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_decor_image_validar.py`:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def _base_dungeon(decor):
    return {
        "id": "t", "name": "t",
        "grid": {"w": 6, "h": 6},
        "tiles": [[1]*6 for _ in range(6)],   # tudo chão (FLOOR=1)
        "entrance": {"x": 0, "y": 0},
        "rooms": [], "monsters": [], "chests": [], "traps": [],
        "decorations": [decor],
        "objectives": {"primary": {"type": "matar_todos"}, "secondary": []},
    }

def test_image_existente_passa(tmp_png="arvore.png"):
    p = os.path.join(server.OBJETOS_DIR, tmp_png)
    os.makedirs(server.OBJETOS_DIR, exist_ok=True)
    novo = not os.path.exists(p)
    if novo: open(p, "wb").close()
    try:
        d = _base_dungeon({"type": "arvore", "pos": [1, 1], "facing": [0, 1], "image": tmp_png})
        ok, msg = server.validar_dungeon(d)
        assert ok, msg
    finally:
        if novo: os.remove(p)

def test_image_traversal_rejeitada():
    d = _base_dungeon({"type": "arvore", "pos": [1, 1], "facing": [0, 1],
                       "image": "../../server.py"})
    ok, _ = server.validar_dungeon(d)
    assert not ok

if __name__ == "__main__":
    test_image_existente_passa(); test_image_traversal_rejeitada()
    print("test_decor_image_validar OK")
```

> Antes de implementar, confira que `validar_dungeon` usa `FLOOR=1` e os campos do dict de exemplo (`tiles`, `rooms`, `objectives`) batem com o formato real — ajuste o `_base_dungeon` se a validação reclamar de outro campo. Leia `validar_dungeon` (server.py:1657) para os requisitos exatos.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decor_image_validar.py`
Expected: FAIL — `test_image_traversal_rejeitada` falha (campo `image` ainda não é validado, então traversal "passa").

- [ ] **Step 3: Implementar a validação**

Em `validar_dungeon`, dentro do laço `for de in decors:` (após o bloco de `loot`, antes do fim do laço, ~1822), adicionar:

```python
        img = de.get("image")
        if img is not None:
            if not isinstance(img, str) or os.path.basename(img) != img \
               or not img.lower().endswith(".png") or "\x00" in img:
                return False, f"decoração com image inválida: {img!r}."
            if not os.path.isfile(os.path.join(OBJETOS_DIR, img)):
                return False, f"image inexistente em assets/objetos: {img!r}."
```

No load da sala (~3742), acrescentar `image` ao dict `dec`:

```python
            dec = {
                "id": f"dec_{len(self.decorations)}",
                "type": d["type"],
                "pos": [d["pos"][0], d["pos"][1]],
                "facing": list(d.get("facing") or [0, 1]),
                "loot": None,
                "tem_loot": False,
                "image": (d.get("image") if isinstance(d.get("image"), str) else None),
            }
```

Em `_serializar_decoracoes` (~10241), incluir `image` no dict de saída:

```python
            out.append({
                "id": d["id"], "type": d["type"], "pos": d["pos"],
                "facing": d.get("facing", [0, 1]),
                "tiles": self._decor_tiles(d),
                "tem_loot": bool(d.get("tem_loot")),
                "charges": d.get("charges"),
                "alto": meta["alto"], "pisavel": meta["pisavel"],
                "special": meta["special"], "emoji": meta["emoji"],
                "size": meta["size"],
                "image": d.get("image"),
            })
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decor_image_validar.py`
Expected: PASS — `test_decor_image_validar OK`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decor_image_validar.py
git commit -m "feat(server): campo image em decoracao (validar/load/serializar)"
```

---

## Fase 2 — Editor

### Task 8: Cliente de upload/listagem de objetos

**Files:**
- Modify: `tools/story_upload.js`

- [ ] **Step 1: Adicionar `uploadObjeto` e `listObjetos`**

Em `tools/story_upload.js`, antes de `window.STORY_UPLOAD = ...` (~124):

```js
  async function uploadObjeto(file) {
    if (extOf(file.name) !== ".png")
      throw new Error("envie um arquivo .png");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("objeto_upload", { name: file.name, data: data });
    return m.name;
  }

  // Lista os PNGs de assets/objetos. Resolve com array de basenames (ou rejeita
  // se o servidor estiver fora — chamador cai no fallback de digitação).
  async function listObjetos() {
    const sock = await connect();
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const to = setTimeout(() => { pending.delete(id); reject(new Error("tempo esgotado")); }, 15000);
      pending.set(id, {
        resolve: (v) => { clearTimeout(to); resolve(v); },
        reject: (e) => { clearTimeout(to); reject(e); },
      });
      try {
        sock.send(JSON.stringify({ type: "list_objetos", upload_id: id }));
      } catch (e) { clearTimeout(to); pending.delete(id); reject(new Error("falha ao enviar")); }
    });
  }
```

> A resposta de `list_objetos` tem `type:"objetos_list"`, não `"upload_result"`. Ajuste o `onmessage` (~36) para também resolver esse tipo:

Substituir em `sock.onmessage`:

```js
        if (m.type !== "upload_result" && m.type !== "objetos_list") return;
        const p = pending.get(m.upload_id);
        if (!p) return;
        pending.delete(m.upload_id);
        if (m.type === "objetos_list") { p.resolve(m.objetos || []); return; }
        if (m.ok) p.resolve(m);
        else p.reject(new Error(m.error || "falha no upload"));
```

E expor:

```js
  window.OBJETO_UPLOAD = { upload: uploadObjeto, list: listObjetos };
```

- [ ] **Step 2: Sanidade de sintaxe**

Run: `node -e "global.window={};global.WebSocket=function(){};require('./tools/story_upload.js');console.log(!!window.OBJETO_UPLOAD)"`
Expected: imprime `true`.

- [ ] **Step 3: Commit**

```bash
git add tools/story_upload.js
git commit -m "feat(editor): cliente uploadObjeto + listObjetos"
```

---

### Task 9: Seção "Imagem" no painel da decoração + serialização + preview 2D

**Files:**
- Modify: `tools/editor.js` (painel decor ~404; serialização ~489)

- [ ] **Step 1: Adicionar a UI no painel da decoração**

Em `tools/editor.js`, no ramo `else if (k === "decor") {` (~404), acrescentar a seção de imagem ao `panel.innerHTML` (logo após o bloco `</div>` do loot, antes de fechar a template string) — incluir um marcador e controles:

```js
      panel.innerHTML += `
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>Imagem (miniatura 3D)</b>
          <div style="font-size:11px;color:#8a7a5a">PNG de assets/objetos — silhueta extrudada no jogo.</div>
          <div style="margin-top:4px">
            <select id="d-img-sel"></select>
            <button id="d-img-refresh" title="recarregar lista">↻</button>
          </div>
          <div style="margin-top:4px">
            <input id="d-img-file" type="file" accept="image/png" style="font-size:11px">
            <span id="d-img-st" style="font-size:11px;color:#8a7a5a"></span>
          </div>
        </div>`;

      const imgSel = document.getElementById("d-img-sel");
      const imgSt = document.getElementById("d-img-st");
      function fillImgOptions(list) {
        const opts = ['<option value="">(nenhuma — procedural)</option>']
          .concat(list.map(n => `<option value="${n}" ${ref.image === n ? "selected" : ""}>${n}</option>`));
        // garante a imagem atual visível mesmo se a lista falhar
        if (ref.image && list.indexOf(ref.image) < 0)
          opts.push(`<option value="${ref.image}" selected>${ref.image} (atual)</option>`);
        imgSel.innerHTML = opts.join("");
      }
      fillImgOptions([]);
      function loadImgList() {
        if (!window.OBJETO_UPLOAD) { imgSt.textContent = "(offline: digite/upload indisponível)"; return; }
        window.OBJETO_UPLOAD.list()
          .then(list => fillImgOptions(list))
          .catch(() => { imgSt.textContent = "servidor offline"; });
      }
      loadImgList();
      imgSel.onchange = e => { ref.image = e.target.value || null; render(); };
      document.getElementById("d-img-refresh").onclick = loadImgList;
      document.getElementById("d-img-file").onchange = async e => {
        const file = e.target.files[0]; if (!file) return;
        if (!window.OBJETO_UPLOAD) { imgSt.textContent = "servidor offline"; return; }
        imgSt.textContent = "enviando…";
        try {
          const name = await window.OBJETO_UPLOAD.upload(file);
          ref.image = name;
          imgSt.textContent = "enviada ✓";
          loadImgList(); render();
        } catch (err) { imgSt.textContent = "falha: " + err.message; }
      };
```

> O `placeDecor` (~69) cria a decoração sem `image`; isso é correto (default null). Nada a mudar lá.

- [ ] **Step 2: Serializar `image` no save**

Na montagem de `decorations` para salvar (~489), incluir `image` quando presente:

```js
      decorations: S.decorations.map(d => {
        const o = { type: d.type, pos: d.pos.slice(), facing: d.facing.slice() };
        o.loot = d.loot ? { gold: d.loot.gold | 0, items: d.loot.items.map(i => ({ id: i.id })) } : null;
        const m = decorMeta(d.type);
        if (m && m.special === "fountain") o.charges = d.charges | 0;
        if (d.image) o.image = d.image;
        return o;
      }),
```

> Verifique se há um **segundo** ponto de serialização de decorações por perto (a busca da Task mostrou `loot` também em ~588). Se ~588 também monta o objeto salvo da decoração, aplique o mesmo `if (d.image) o.image = d.image;` lá. Leia ambos antes de editar.

- [ ] **Step 3: Preview 2D no editor**

Localize o desenho 2D das decorações no editor (a função `render()` que desenha emoji por decoração — busque por `m.emoji` / o helper `emojiAt` em editor.js, ~92). No ponto onde desenha o emoji da decoração, anteponha: se `d.image`, desenhar a imagem cobrindo o footprint; senão, emoji (comportamento atual). Use um cache simples:

```js
  // cache de imagens de objetos para o preview do editor
  const _objImgCache = {};
  function objImg(name) {
    if (!name) return null;
    let im = _objImgCache[name];
    if (im === undefined) {
      im = new Image();
      im.onload = () => render();
      im.src = "../assets/objetos/" + name;   // editor roda em file://; ajuste p/ http se servido
      _objImgCache[name] = im;
    }
    return (im.complete && im.naturalWidth) ? im : null;
  }
```

E no desenho da decoração (onde hoje faz `fillText(emoji…)`): se `objImg(d.image)` retornar imagem pronta, `ctx.drawImage(img, x0, y0, wpx, hpx)` cobrindo o footprint; caso contrário, mantém o emoji.

> **Implemente conforme o código real de `render()` em editor.js** (a localização exata do desenho da decoração). Não invente nomes: leia a função e insira o ramo de imagem no mesmo lugar do emoji.

- [ ] **Step 4: Validação manual**

Abra o editor servido em `http://localhost:8765/tools/editor.html` (para o `OBJETO_UPLOAD` conectar). Coloque uma árvore, selecione-a, escolha `arvore.png` no dropdown (ou faça upload). Confirme:
- o preview 2D do editor troca o 🌳 pela imagem;
- "Salvar" grava a dungeon (o JSON contém `"image": "arvore.png"` na decoração).

Run (após salvar): inspecione o arquivo salvo em `dungeons/` e confirme o campo `image`.
Expected: `image` presente na decoração da árvore.

- [ ] **Step 5: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): selecionar/enviar PNG da decoracao + preview 2D"
```

---

## Fase 3 — Render no jogo

### Task 10: Render 2D do jogo (PNG no footprint)

**Files:**
- Modify: `game.js` (helper perto de `_getPrisoner2DImg` ~4397; desenho decor 2D ~4950)

- [ ] **Step 1: Helper de imagem de objeto (2D)**

Em `game.js`, perto de `_getPrisoner2DImg` (~4397), adicionar:

```js
// Miniatura 2D de objeto de decoração (PNG editável em assets/objetos).
const _obj2DImg = {};
function _getObjeto2DImg(imageName){
  if(!imageName) return null;
  let img = _obj2DImg[imageName];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/objetos/${imageName}`);
    _obj2DImg[imageName] = img;
  }
  return (img.complete && img.naturalWidth) ? img : null;
}
```

- [ ] **Step 2: Usar a imagem no desenho 2D da decoração**

No bloco "Decorations (2D overlay)" (~4961), substituir o desenho do emoji por: se `d.image` e a imagem estiver pronta, desenhar a imagem cobrindo o footprint (mantendo o fill sutil e o badge de loot); senão, emoji como hoje.

```js
      const _oImg = d.image ? _getObjeto2DImg(d.image) : null;
      if (_oImg) {
        const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
        const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
        const px = minX * CELL, py = minY * CELL;
        const pw = (maxX - minX + 1) * CELL, ph = (maxY - minY + 1) * CELL;
        // ajusta mantendo proporção, ancorado embaixo
        const ar = _oImg.naturalWidth / _oImg.naturalHeight;
        let dw = pw, dh = pw / ar;
        if (dh > ph) { dh = ph; dw = ph * ar; }
        ctx.drawImage(_oImg, px + (pw - dw) / 2, py + (ph - dh), dw, dh);
      } else {
        ctx.font = `${Math.floor(CELL * 0.8)}px serif`;
        ctx.fillText(d.emoji || '🪑', ecx, ecy);
      }
```

(Manter o cálculo de `ecx`/`ecy` acima para o fallback emoji e o badge de loot.)

- [ ] **Step 3: Validação manual**

Carregue a dungeon com a árvore (com `image`), entre no jogo em **2D**.
Expected: a árvore aparece como a imagem PNG no footprint, no lugar do 🌳; decorações sem `image` continuam emoji.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(jogo): decoracao com image desenha PNG no 2D"
```

---

### Task 11: Render 3D do jogo (miniatura extrudada)

**Files:**
- Modify: `index.html` (carregar `src/miniatura3d.js`); `game.js` (bloco decor 3D ~12885)

- [ ] **Step 1: Carregar o módulo no `index.html`**

Em `index.html`, junto aos outros `<script src="src/...">` (com o mesmo padrão de cache-buster usado no projeto), adicionar:

```html
<script src="src/miniatura3d.js?v=1"></script>
```

> Confira como os outros `src/*.js` são incluídos e use o mesmo cache-buster/ordem. `miniatura3d.js` não depende de THREE no load (THREE é injetado em `build`), então a ordem relativa ao three.min.js não é crítica, mas mantenha-o antes de `game.js`.

- [ ] **Step 2: Usar `Miniatura3D.build` no bloco decor 3D**

No bloco "Decoration 3D meshes" (~12885), antes de cair no caminho procedural (`DECOR_3D[d.type]`), tratar `d.image`. Como a construção é assíncrona (precisa do `Image` carregado), use um cache por nome de imagem e (re)posicione a cada frame. Estrutura:

```js
    for (const d of decors) {
      vistosDec.add(d.id);
      const tiles = GS.decorTilesOf(d);
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      const wCells = maxX - minX + 1, hCells = maxY - minY + 1;
      const worldX = (minX + maxX) / 2, worldZ = (minY + maxY) / 2;
      const visivel = tiles.some(([tx2, ty2]) => exploredSet.has(`${tx2},${ty2}`));

      if (d.image && window.Miniatura3D) {
        let mesh = g3.decorMeshes[d.id];
        // (re)constrói se ainda não existe OU se a imagem mudou
        if (!mesh || mesh.userData.imageName !== d.image) {
          if (mesh) { g3.scene.remove(mesh); _disposeDecorMesh(mesh); }
          const placeholder = new T.Group();
          placeholder.userData = { isDecor: true, decorId: d.id, imageName: d.image, pending: true };
          g3.scene.add(placeholder);
          g3.decorMeshes[d.id] = placeholder;
          mesh = placeholder;
          _buildObjetoMini(d.id, d.image, Math.max(wCells, hCells));   // assíncrono
        }
        mesh.position.set(worldX, 0, worldZ);
        mesh.visible = visivel;
        continue;
      }

      // ── caminho procedural existente (sem image) ──
      const spec = DECOR_3D[d.type] || { shape: 'box', h: 0.6, color: 0x999999 };
      let mesh = g3.decorMeshes[d.id];
      if (!mesh || mesh.userData.imageName) {
        if (mesh) { g3.scene.remove(mesh); _disposeDecorMesh(mesh); }
        const geo = spec.shape === 'cyl'
          ? new T.CylinderGeometry(0.4, 0.4, spec.h, 16)
          : new T.BoxGeometry(1, spec.h, 1);
        mesh = new T.Mesh(geo, new T.MeshStandardMaterial({ color: spec.color }));
        mesh.userData.isDecor = true; mesh.userData.decorId = d.id;
        g3.scene.add(mesh);
        g3.decorMeshes[d.id] = mesh;
      }
      mesh.position.set(worldX, spec.h / 2, worldZ);
      if (spec.shape === 'box') mesh.scale.set(wCells * 0.9, 1, hCells * 0.9);
      mesh.visible = visivel;
    }
```

Adicionar, fora do laço (perto do bloco), os helpers:

```js
  // Cache de Image() para objetos 3D e construção assíncrona da miniatura.
  function _disposeDecorMesh(obj){
    obj.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach(mm => { if (mm.map) mm.map.dispose(); mm.dispose(); });
      }
    });
  }
  const _objImg3D = {};
  function _buildObjetoMini(decorId, imageName, cells){
    const make = (img) => {
      const slot = g3.decorMeshes[decorId];
      // a decoração pode ter sido removida/trocada enquanto carregava
      if (!slot || slot.userData.imageName !== imageName) return;
      const grp = window.Miniatura3D.build(T, { image: img, tileSize: Math.max(1, cells) * 0.9 });
      grp.userData = { isDecor: true, decorId: decorId, imageName: imageName };
      grp.position.copy(slot.position);
      grp.visible = slot.visible;
      g3.scene.remove(slot); _disposeDecorMesh(slot);
      g3.scene.add(grp);
      g3.decorMeshes[decorId] = grp;
    };
    let img = _objImg3D[imageName];
    if (img && img.complete && img.naturalWidth) { make(img); return; }
    if (!img) {
      img = new Image();
      img.src = _assetURL(`assets/objetos/${imageName}`);
      _objImg3D[imageName] = img;
    }
    img.onload = () => make(img);
  }
```

> A remoção de meshes órfãos (~12921) já existe; garanta que ela use `_disposeDecorMesh` em vez de só `scene.remove` (para liberar geometria/textura das miniaturas). Ajuste esse laço:

```js
    for (const id of Object.keys(g3.decorMeshes)) {
      if (!vistosDec.has(id)) {
        const m = g3.decorMeshes[id];
        g3.scene.remove(m); _disposeDecorMesh(m);
        delete g3.decorMeshes[id];
      }
    }
```

- [ ] **Step 3: Validação manual (visual)**

Entre no jogo em **3D** com a dungeon da árvore (`image: arvore.png`).
Expected: no lugar do cilindro verde, a árvore extrudada (silhueta do PNG, frente com arte, base oval, sombra) em pé sobre o tile; gira junto ao orbitar a câmera; fog/visibilidade idênticos. Decorações sem `image` seguem box/cyl. Sem vazamento perceptível ao reabrir/trocar dungeons (cheque o FPS estável).

- [ ] **Step 4: Commit**

```bash
git add index.html game.js
git commit -m "feat(jogo): decoracao com image vira miniatura extrudada no 3D"
```

---

### Task 12: Round-trip do `image` (regressão)

**Files:**
- Modify: `tools/test_decor_roundtrip.py`

- [ ] **Step 1: Estender o round-trip**

Leia `tools/test_decor_roundtrip.py` e acrescente um caso: uma decoração com `image: "arvore.png"` (garanta o arquivo presente em `assets/objetos/`, criando um stub vazio se necessário como na Task 7) deve sobreviver a salvar→carregar com `image` preservado em `_serializar_decoracoes`. Siga o estilo/asserções já usadas no arquivo.

- [ ] **Step 2: Rodar e ver passar**

Run: `python tools/test_decor_roundtrip.py`
Expected: PASS (incluindo o novo caso de `image`).

- [ ] **Step 3: Rodar a suíte de decorações para garantir não-regressão**

Run: `python tools/test_decoracoes.py && python tools/test_decor_image_validar.py && python tools/test_objeto_upload.py && node tools/test_miniatura3d.test.js`
Expected: todos PASS.

- [ ] **Step 4: Commit**

```bash
git add tools/test_decor_roundtrip.py
git commit -m "test(decor): round-trip preserva campo image"
```

---

## Self-review (cobertura do spec)

- **Associação por instância:** campo `image` em cada decoração — Tasks 7 (server), 9 (editor save/place).
- **Render 3D extrudado (silhueta alfa):** Tasks 1–5 (pipeline + demo), 11 (integração).
- **Render 2D do jogo:** Task 10.
- **Preview no editor:** Task 9 (Step 3).
- **Técnica silhueta real (alfa→contorno):** Tasks 1 (marching squares), 2 (simplify), 3 (classificar/cor), 4 (extrude).
- **Faces: frente com arte, laterais lisas:** Task 4 (`faceMat` texturizado + `sideMat` cor de borda).
- **Demo standalone primeiro:** Task 5 (gate de confirmação com o usuário antes de integrar).
- **Seletor: lista automática + upload:** Tasks 6 (`list_objetos`/`objeto_upload`), 8 (cliente), 9 (UI).
- **Escopo só decorações:** nenhuma task toca monstros/baús.
- **Validação/sanitização (PNG, path traversal):** Tasks 6 e 7.
- **Conformidade arquitetura:** pipeline em `src/miniatura3d.js` (render puro, THREE injetado, sem tocar `gameState.js`); `image` é dado no servidor autoritativo e no JSON.
- **Testes:** Tasks 1–4 (Node), 6–7 (server), 12 (round-trip).

Consistência de nomes verificada: `_save_objeto_upload`/`_listar_objetos`/`OBJETOS_DIR` (server), `objeto_upload`/`list_objetos`/`objetos_list` (protocolo), `window.OBJETO_UPLOAD.{upload,list}` (cliente), `Miniatura3D.{marchingSquares,simplifyPath,classifyLoops,edgeColorHex,imageToMask,build}` (módulo), `_getObjeto2DImg`/`_buildObjetoMini`/`_disposeDecorMesh` (game.js).
