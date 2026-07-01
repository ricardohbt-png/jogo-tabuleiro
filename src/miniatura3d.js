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

  // Limpa uma máscara binária: mantém só o maior componente 4-conexo (descarta
  // ilhas de ruído pontilhado) e preenche os buracos internos cercados (vãos de
  // folha). Resultado: um blob sólido → marchingSquares traça UM contorno limpo
  // (sem o "tecido" que o pontilhado gera no encadeamento). Pura/testável.
  function cleanMask(mask, w, h) {
    const n = w * h;
    const lab = new Int32Array(n);
    let best = 0, bestCount = 0, cur = 0;
    const st = [];
    for (let i = 0; i < n; i++) {
      if (mask[i] && !lab[i]) {
        cur++; let count = 0; st.length = 0; st.push(i); lab[i] = cur;
        while (st.length) {
          const p = st.pop(); count++;
          const x = p % w, y = (p / w) | 0;
          if (x > 0 && mask[p - 1] && !lab[p - 1]) { lab[p - 1] = cur; st.push(p - 1); }
          if (x < w - 1 && mask[p + 1] && !lab[p + 1]) { lab[p + 1] = cur; st.push(p + 1); }
          if (y > 0 && mask[p - w] && !lab[p - w]) { lab[p - w] = cur; st.push(p - w); }
          if (y < h - 1 && mask[p + w] && !lab[p + w]) { lab[p + w] = cur; st.push(p + w); }
        }
        if (count > bestCount) { bestCount = count; best = cur; }
      }
    }
    const out = new Uint8Array(n);
    for (let i = 0; i < n; i++) out[i] = lab[i] === best ? 1 : 0;
    // Inunda o fundo a partir da borda; o que NÃO foi alcançado e não é frente é
    // buraco interno cercado → preenche.
    const bg = new Uint8Array(n);
    st.length = 0;
    const seed = (i) => { if (!out[i] && !bg[i]) { bg[i] = 1; st.push(i); } };
    for (let x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x); }
    for (let y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1); }
    while (st.length) {
      const p = st.pop(), x = p % w, y = (p / w) | 0;
      if (x > 0) seed(p - 1);
      if (x < w - 1) seed(p + 1);
      if (y > 0) seed(p - w);
      if (y < h - 1) seed(p + w);
    }
    for (let i = 0; i < n; i++) if (!out[i] && !bg[i]) out[i] = 1;
    return out;
  }

  // PNG (HTMLImageElement já carregado) → {mask,w,h,imageData} reduzido a maxSide.
  // Redução por HALVING em etapas (média de área de verdade): nem o NEAREST (que
  // sobre-solidifica e cria halo pontilhado nas bordas rendadas), nem o bilinear
  // de um passo só (que sub-amostra em reduções grandes). Cada metade faz média
  // 2×2 → alfa fiel; aí o limiar dá uma silhueta sólida e limpa.
  function imageToMask(image, opts) {
    const maxSide = (opts && opts.maxSide) || 128;
    const alphaThresh = (opts && opts.alphaThresh) || 128;
    let cw = image.width, ch = image.height;
    let src = document.createElement("canvas");
    src.width = cw; src.height = ch;
    src.getContext("2d").drawImage(image, 0, 0);
    const scale = Math.min(1, maxSide / Math.max(cw, ch));
    const w = Math.max(1, Math.round(cw * scale));
    const h = Math.max(1, Math.round(ch * scale));
    while (cw > w * 2 || ch > h * 2) {
      const nw = Math.max(w, Math.floor(cw / 2)), nh = Math.max(h, Math.floor(ch / 2));
      const dst = document.createElement("canvas");
      dst.width = nw; dst.height = nh;
      const dctx = dst.getContext("2d");
      dctx.imageSmoothingEnabled = true; dctx.imageSmoothingQuality = "high";
      dctx.drawImage(src, 0, 0, nw, nh);
      src = dst; cw = nw; ch = nh;
    }
    const cv = document.createElement("canvas");
    cv.width = w; cv.height = h;
    const cx = cv.getContext("2d");
    cx.imageSmoothingEnabled = true; cx.imageSmoothingQuality = "high";
    cx.drawImage(src, 0, 0, w, h);
    const imageData = cx.getImageData(0, 0, w, h);
    let mask = new Uint8Array(w * h);
    for (let i = 0; i < w * h; i++) mask[i] = imageData.data[i * 4 + 3] > alphaThresh ? 1 : 0;
    // Limpeza: maior componente + preenche buracos (a menos que opts.cleanMask===false).
    if (!opts || opts.cleanMask !== false) mask = cleanMask(mask, w, h);
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

    let loopsRaw = marchingSquares(mask, w, h).map(l => simplifyPath(l, tol));
    // Descarta laços minúsculos (ilhas/buracos de ruído de borda) — mantém a
    // silhueta principal e seus buracos relevantes. Se o filtro zerar tudo,
    // mantém só o maior laço.
    const minArea = (opts.minLoopAreaFrac != null ? opts.minLoopAreaFrac : 0.004) * w * h;
    const filtered = loopsRaw.filter(l => Math.abs(_area(l)) >= minArea);
    if (filtered.length) loopsRaw = filtered;
    else loopsRaw = [loopsRaw.reduce((a, b) => Math.abs(_area(b)) > Math.abs(_area(a)) ? b : a)];
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
    // UV pela EXTENSÃO DA IMAGEM (não pelo bbox da geometria): a silhueta e a
    // textura vêm do MESMO PNG, então mapear cada vértice pela sua coord. de
    // imagem alinha a arte exatamente com o recorte. worldW = w*s; altura = h*s.
    // (flipY padrão da textura faz uv.y=0 amostrar a base da imagem, que é onde
    // worldY=0 cai — consistente.)
    const imgWx = w * s, imgHy = h * s;
    const pos = geo.attributes.position, uv = geo.attributes.uv;
    for (let i = 0; i < pos.count; i++) {
      uv.setXY(i, pos.getX(i) / imgWx, pos.getY(i) / imgHy);
    }
    uv.needsUpdate = true;

    // Materiais: grupo 0 = faces (ExtrudeGeometry separa front/back de side via groups).
    // ExtrudeGeometry cria 2 groups: 0 = tampas(frente/verso), 1 = laterais.
    // Textura da face: desenha o PNG ORIGINAL com suavização (arte nítida),
    // desacoplada da máscara (que é baixa-res e nearest p/ geometria limpa).
    const texMax = (opts && opts.texMax) || 512;
    const tscale = Math.min(1, texMax / Math.max(image.width, image.height));
    const texCanvas = document.createElement("canvas");
    texCanvas.width = Math.max(1, Math.round(image.width * tscale));
    texCanvas.height = Math.max(1, Math.round(image.height * tscale));
    const tctx = texCanvas.getContext("2d");
    // Preenche o fundo com a cor da borda ANTES de desenhar a arte: os vãos
    // internos (que o cleanMask fechou na silhueta) e qualquer fundo do PNG
    // ficam com essa cor sólida em vez do xadrez de transparência embutido.
    tctx.fillStyle = "#" + ("000000" + (sideColor >>> 0).toString(16)).slice(-6);
    tctx.fillRect(0, 0, texCanvas.width, texCanvas.height);
    tctx.drawImage(image, 0, 0, texCanvas.width, texCanvas.height);
    const tex = new THREE.Texture(texCanvas);
    tex.needsUpdate = true;
    // Face OPACA: a própria geometria (silhueta) define o recorte, então não há
    // alphaTest (que abriria furos nos vãos preenchidos pelo cleanMask). A arte
    // do PNG só colore a face.
    const faceMat = new THREE.MeshStandardMaterial({
      map: tex, roughness: 0.85, metalness: 0,
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

  const api = { marchingSquares: marchingSquares, simplifyPath: simplifyPath, classifyLoops: classifyLoops, edgeColorHex: edgeColorHex, cleanMask: cleanMask, imageToMask: imageToMask, build: build };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.Miniatura3D = api;
})(typeof window !== "undefined" ? window : null);
