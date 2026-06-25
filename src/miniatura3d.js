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

    // Segmentos direcionados (inside à esquerda) por célula (x,y) da grade preenchida.
    // Os quatro pontos de meio-aresta são calculados no espaço de CANTOS da grade
    // preenchida (não da máscara original). O padding de 1 célula faz com que a
    // coordenada original = coordenada preenchida − 1, de modo que o laço final já
    // sai no espaço da máscara original sem conversão explícita.
    //
    // Rótulos e coordenadas reais (espaço preenchido, canto superior-esquerdo da
    // célula em (x, y)):
    //   eTopLeft    = (x,     y−0.5)  — meio da aresta vertical entre esta célula e a de cima
    //   eTopRight   = (x+0.5, y    )  — meio da aresta horizontal superior desta célula
    //   eBotLeft    = (x,     y+0.5)  — meio da aresta vertical esquerda desta célula
    //   eBotRight   = (x−0.5, y    )  — meio da aresta horizontal entre esta célula e a da esquerda
    //
    // ATENÇÃO: os nomes foram escolhidos pelo vértice do quadrado de marching que
    // cada ponto separa, NÃO pela aresta geométrica convencional (top/right/bottom/left).
    // A tabela switch abaixo usa esses rótulos de forma consistente internamente.
    const segs = [];
    const key = p => p[0] + "," + p[1];
    for (let y = 0; y < H - 1; y++) {
      for (let x = 0; x < W - 1; x++) {
        const tl = at(x, y), tr = at(x + 1, y), br = at(x + 1, y + 1), bl = at(x, y + 1);
        const c = (tl << 3) | (tr << 2) | (br << 1) | bl;
        if (c === 0 || c === 15) continue;
        // eTopLeft=T, eTopRight=R, eBotLeft=B, eBotRight=L (aliases curtos para a tabela abaixo)
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
  // Profundidade-1: um shape aninhado DENTRO de um buraco vira buraco do externo (não re-emerge como novo shape). Suficiente para silhuetas de decoração (1 externo + 0/1 buracos).
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

  const api = { marchingSquares: marchingSquares, simplifyPath: simplifyPath, classifyLoops: classifyLoops, edgeColorHex: edgeColorHex, imageToMask: imageToMask, build: build };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.Miniatura3D = api;
})(typeof window !== "undefined" ? window : null);
