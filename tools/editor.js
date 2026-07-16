"use strict";
(function () {
  const WALL = 0, FLOOR = 1, DOOR = 2, CELL = 28;
  const BASE_CAT = window.EDITOR_CATALOG || { monsters: [], items: [], traps: [], venoms: [], decorations: [], materiais: [] };
  const CAT = Object.assign({}, BASE_CAT, { monsters: (BASE_CAT.monsters || []).concat(window.EDITOR_CUSTOM_MONSTERS || []) });
  const MAT = (CAT.materiais || []);
  const matMeta = (id) => MAT.find(m => m.id === id) || null;
  // Default por categoria: pintar o default limpa a casa (mantém JSON esparso e
  // serve de borracha de material). Espelha MATERIAIS_*_DEFAULT do servidor.
  const MAT_DEFAULT = { piso: "pedra_cinza", parede: "pedra_normal" };

  const S = {
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra", ambiente: "masmorra" },
    grid: { w: 16, h: 12 },
    tiles: [],
    rooms: [], nextRoomId: 0,
    entrance: null, exit: null, prisoner: null,
    monsters: [], chests: [], traps: [], decorations: [], secretPassages: [], nextDecorId: 0, nextPassageId: 0,
    masterReinforcements: [],
    expectedParty: { heroes: 4, level: 1 },
    objectives: { primary: { type: "kill_all" }, secondary: [] },
    tool: "wall", sel: null,
    teleportExitPick: null,      // referência da armadilha aguardando clique no mapa
    decorType: (CAT.decorations[0] || {}).type || "cama",
    decorFacing: [0, 1],
    materiais: {},                 // {"x,y": id}
    matFloor: "pedra_cinza",       // material atual da ferramenta "chão"
    matWall: "pedra_normal",       // material atual da ferramenta "parede"
    matFill: false,                // false = pincel; true = balde (preenchimento)
  };
  // Área de transferência exclusiva de objetos decorativos. Guarda uma cópia
  // profunda para que loot, escala, imagem e demais ajustes nunca sejam
  // compartilhados acidentalmente com o objeto de origem.
  let decorClipboard = null;
  let lastPointerCell = null;

  function initGrid(w, h) {
    S.grid = { w, h };
    S.tiles = [];
    for (let y = 0; y < h; y++) S.tiles.push(new Array(w).fill(WALL));
  }

  function decorMeta(type) { return CAT.decorations.find(d => d.type === type) || null; }
  function decorEffSize(type, facing) {
    const m = decorMeta(type); if (!m) return [1, 1];
    const [w, h] = m.size;
    return (facing && facing[0] !== 0) ? [h, w] : [w, h];
  }
  function decorTilesAt(type, ax, ay, facing) {
    const [ew, eh] = decorEffSize(type, facing);
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([ax + i, ay + j]);
    return out;
  }
  // Tamanho "natural" (pré-facing) de uma decoração: usa o override por-objeto
  // d.size se presente, senão o tamanho do catálogo do tipo.
  function decorBaseSize(d) {
    if (d && Array.isArray(d.size) && d.size.length === 2) return [d.size[0], d.size[1]];
    const m = decorMeta(d && d.type ? d.type : d);
    return m ? m.size.slice() : [1, 1];
  }
  // Tamanho efetivo (já com a troca por facing) de uma decoração específica.
  function decorEffSizeOf(d) {
    const [w, h] = decorBaseSize(d);
    return (d.facing && d.facing[0] !== 0) ? [h, w] : [w, h];
  }
  // Casas ocupadas a partir de pos/size(natural)/facing explícitos.
  function tilesFor(pos, size, facing) {
    const [w, h] = size;
    const [ew, eh] = (facing && facing[0] !== 0) ? [h, w] : [w, h];
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([pos[0] + i, pos[1] + j]);
    return out;
  }
  function decorTiles(d) {
    const [ew, eh] = decorEffSizeOf(d);
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([d.pos[0] + i, d.pos[1] + j]);
    return out;
  }

  function rotateFacing(f) {
    // cicla 4 facings: [0,1]→[1,0]→[0,-1]→[-1,0]→[0,1]
    const order = [[0, 1], [1, 0], [0, -1], [-1, 0]];
    const i = order.findIndex(o => o[0] === f[0] && o[1] === f[1]);
    return order[(i + 1) % 4];
  }
  // facing → ângulo (rad) p/ o giro 90° da imagem no preview 2D. Espelha game.js.
  function facingAngle2D(f) {
    if (!f) return 0;
    if (f[0] === 1 && f[1] === 0) return Math.PI / 2;
    if (f[0] === 0 && f[1] === -1) return Math.PI;
    if (f[0] === -1 && f[1] === 0) return -Math.PI / 2;
    return 0;
  }
  function rotateDecorPending() {
    if (S.sel && S.sel.kind === "decor") {
      const m = decorMeta(S.sel.ref.type);
      if (m && m.gira) {
        if (m.special === "wall") {
          const faces = wallFacesAt(S.sel.ref.pos[0], S.sel.ref.pos[1]);
          const i = faces.findIndex(f => sameFace(f, S.sel.ref.facing));
          if (faces.length) S.sel.ref.facing = faces[(i + 1 + faces.length) % faces.length];
        } else S.sel.ref.facing = rotateFacing(S.sel.ref.facing);
        render();
      }
    } else {
      const m = decorMeta(S.decorType);
      if (m && m.gira) S.decorFacing = rotateFacing(S.decorFacing);
    }
  }
  function editingText(ev) {
    return /^(INPUT|TEXTAREA|SELECT)$/.test((ev.target && ev.target.tagName) || "");
  }
  window.addEventListener("keydown", (ev) => {
    if (editingText(ev)) return;
    const modifier = ev.ctrlKey || ev.metaKey;
    if (modifier && ev.key.toLowerCase() === "c") {
      if (copySelectedDecor()) ev.preventDefault();
      return;
    }
    if (modifier && ev.key.toLowerCase() === "v") {
      if (lastPointerCell && pasteDecorAt(lastPointerCell[0], lastPointerCell[1])) ev.preventDefault();
      return;
    }
    if (ev.key === "r" || ev.key === "R") rotateDecorPending();
  });

  // Chão (special:floor) é camada de PISO: sobrepõe qualquer objeto e é ignorado
  // como ocupação quando se posiciona outro objeto. Dois objetos não-piso ainda
  // não podem se sobrepor.
  function isFloorDecor(d) { const m = decorMeta(d && d.type ? d.type : d); return !!(m && m.special === "floor"); }
  function isWallDecor(d) { const m = decorMeta(d && d.type ? d.type : d); return !!(m && m.special === "wall"); }
  const CARDINAL_FACES = [[0,1],[1,0],[0,-1],[-1,0]];
  function wallFacesAt(x, y) {
    return CARDINAL_FACES.filter(([dx,dy]) => {
      const nx=x+dx, ny=y+dy;
      // Uma decoração de parede sempre olha para uma casa de chão. Não a
      // colocamos voltada para o exterior, outra parede ou uma porta.
      return nx>=0 && ny>=0 && nx<S.grid.w && ny<S.grid.h && S.tiles[ny][nx] === FLOOR;
    });
  }
  function sameFace(a,b) { return a && b && a[0] === b[0] && a[1] === b[1]; }
  // Aceita o clique diretamente na parede ou no chão que toca essa parede.
  // O JSON continua armazenando a posição da PAREDE e a face voltada ao chão.
  function wallPlacementAt(x, y, preferredFacing) {
    if (x < 0 || y < 0 || x >= S.grid.w || y >= S.grid.h) return null;
    if (S.tiles[y][x] === WALL) {
      const faces = wallFacesAt(x, y);
      const facing = faces.find(f => sameFace(f, preferredFacing)) || faces[0];
      return facing ? { pos: [x, y], facing: facing.slice() } : null;
    }
    if (S.tiles[y][x] !== FLOOR) return null;
    const candidates = CARDINAL_FACES.map(f => ({
      pos: [x - f[0], y - f[1]], facing: f,
    })).filter(c => c.pos[0] >= 0 && c.pos[1] >= 0
      && c.pos[0] < S.grid.w && c.pos[1] < S.grid.h
      && S.tiles[c.pos[1]][c.pos[0]] === WALL
      && wallFacesAt(c.pos[0], c.pos[1]).some(face => sameFace(face, c.facing)));
    const chosen = candidates.find(c => sameFace(c.facing, preferredFacing)) || candidates[0];
    return chosen ? { pos: chosen.pos, facing: chosen.facing.slice() } : null;
  }
  function decorFits(type, ax, ay, facing, ignore) {
    if (isWallDecor(type)) {
      if (ax < 0 || ay < 0 || ax >= S.grid.w || ay >= S.grid.h || S.tiles[ay][ax] !== WALL) return false;
      const faces = wallFacesAt(ax, ay);
      if (!faces.some(f => sameFace(f, facing))) return false;
      return !S.decorations.some(d => d !== ignore && isWallDecor(d)
        && d.pos[0] === ax && d.pos[1] === ay && sameFace(d.facing, facing));
    }
    if (isFloorDecor(type)) {  // piso cabe em qualquer chão livre, sobre outros objetos
      for (const [tx, ty] of decorTilesAt(type, ax, ay, facing)) {
        if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) return false;
        if (S.tiles[ty][tx] !== FLOOR) return false;
      }
      return true;
    }
    for (const [tx, ty] of decorTilesAt(type, ax, ay, facing)) {
      if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) return false;
      if (S.tiles[ty][tx] !== FLOOR) return false;
      for (const d of S.decorations) {
        if (d === ignore || isFloorDecor(d)) continue;
        if (decorTiles(d).some(c => c[0] === tx && c[1] === ty)) return false;
      }
    }
    return true;
  }
  // Encaixe genérico para arrasto/redimensionamento: a decoração `ignore` (a que
  // está sendo movida/redimensionada) é desconsiderada na checagem de sobreposição.
  function decorWouldFit(ignore, pos, size, facing) {
    if (isWallDecor(ignore)) return decorFits(ignore.type, pos[0], pos[1], facing, ignore);
    const movingFloor = isFloorDecor(ignore);
    for (const [tx, ty] of tilesFor(pos, size, facing)) {
      if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) return false;
      if (S.tiles[ty][tx] !== FLOOR) return false;
      if (movingFloor) continue;   // piso sobrepõe qualquer coisa
      for (const d of S.decorations) {
        if (d === ignore || isFloorDecor(d)) continue;
        if (decorTiles(d).some(c => c[0] === tx && c[1] === ty)) return false;
      }
    }
    return true;
  }
  function placeDecor(x, y) {
    const m = decorMeta(S.decorType);
    const wallPlacement = m && m.special === "wall" ? wallPlacementAt(x, y, S.decorFacing) : null;
    const pos = wallPlacement ? wallPlacement.pos : [x, y];
    const facing = wallPlacement ? wallPlacement.facing : S.decorFacing.slice();
    if (!wallPlacement && m && m.special === "wall") return;
    if (!decorFits(S.decorType, pos[0], pos[1], facing)) return;
    const d = { id: "decor_" + S.nextDecorId++, type: S.decorType, pos, facing,
                loot: (m && m.loot_capaz && S.decorType === "arca_tesouros") ? { gold: 0, items: [] } : null,
                key_objective: false };
    if (m && m.special === "fountain") d.charges = 3;
    if (m && m.special === "floor") d.image = "chaograma1.png";   // grama por padrão (trocável no picker)
    if (m && m.image) d.image = m.image;
    S.decorations.push(d);
    S.sel = { kind: "decor", ref: d, pos: pos.slice() };
  }

  function cloneDecor(source) { return JSON.parse(JSON.stringify(source)); }
  function copySelectedDecor() {
    if (!S.sel || S.sel.kind !== "decor" || !S.sel.ref) return false;
    decorClipboard = cloneDecor(S.sel.ref);
    render();
    return true;
  }
  function pasteDecorAt(x, y) {
    if (!decorClipboard) return false;
    const d = cloneDecor(decorClipboard);
    d.id = "decor_" + S.nextDecorId++;
    d.facing = Array.isArray(d.facing) ? d.facing.slice() : [0, 1];
    if (isWallDecor(d)) {
      const placement = wallPlacementAt(x, y, d.facing);
      if (!placement) return false;
      d.pos = placement.pos;
      d.facing = placement.facing;
    } else d.pos = [x, y];
    const size = decorBaseSize(d);
    if (!decorWouldFit(d, d.pos, size, d.facing)) return false;
    S.decorations.push(d);
    S.sel = { kind: "decor", ref: d, pos: d.pos.slice() };
    renderPanel(); render();
    return true;
  }
  function duplicateDecorAdjacent(source) {
    if (!source) return false;
    const [ew, eh] = decorEffSizeOf(source);
    // Primeiro as quatro faces; diagonais são alternativas para objetos grandes
    // ou quando a parede/um objeto bloqueia todos os lados imediatos.
    const offsets = [[ew, 0], [-ew, 0], [0, eh], [0, -eh], [ew, eh], [ew, -eh], [-ew, eh], [-ew, -eh]];
    for (const [dx, dy] of offsets) {
      const d = cloneDecor(source);
      d.id = "decor_" + S.nextDecorId++;
      d.pos = [source.pos[0] + dx, source.pos[1] + dy];
      d.facing = Array.isArray(d.facing) ? d.facing.slice() : [0, 1];
      if (!decorWouldFit(d, d.pos, decorBaseSize(d), d.facing)) continue;
      S.decorations.push(d);
      S.sel = { kind: "decor", ref: d, pos: d.pos.slice() };
      return true;
    }
    return false;
  }

  const board = document.getElementById("board");
  const ctx = board.getContext("2d");
  const copyMenu = document.createElement("div");
  copyMenu.id = "editor-copy-menu";
  copyMenu.innerHTML = `<button type="button" data-action="copy">Copiar objeto <kbd>Ctrl+C</kbd></button><button type="button" data-action="paste">Colar objeto aqui <kbd>Ctrl+V</kbd></button>`;
  document.body.appendChild(copyMenu);
  function hideCopyMenu() { copyMenu.classList.remove("open"); }
  function showCopyMenu(ev, cell) {
    const selected = entityAt(cell[0], cell[1]);
    if (selected) { S.sel = selected; renderPanel(); render(); }
    const copyButton = copyMenu.querySelector('[data-action="copy"]');
    const pasteButton = copyMenu.querySelector('[data-action="paste"]');
    copyButton.disabled = !(S.sel && S.sel.kind === "decor");
    pasteButton.disabled = !decorClipboard;
    copyMenu.dataset.x = String(cell[0]); copyMenu.dataset.y = String(cell[1]);
    copyMenu.style.left = `${Math.min(ev.clientX, window.innerWidth - 190)}px`;
    copyMenu.style.top = `${Math.min(ev.clientY, window.innerHeight - 76)}px`;
    copyMenu.classList.add("open");
  }
  copyMenu.addEventListener("click", ev => {
    const button = ev.target.closest("button[data-action]"); if (!button || button.disabled) return;
    const x = Number(copyMenu.dataset.x), y = Number(copyMenu.dataset.y);
    if (button.dataset.action === "copy") copySelectedDecor();
    else pasteDecorAt(x, y);
    hideCopyMenu();
  });
  document.addEventListener("mousedown", ev => { if (!copyMenu.contains(ev.target)) hideCopyMenu(); });
  window.addEventListener("keydown", ev => { if (ev.key === "Escape") hideCopyMenu(); });

  // Cache de imagens de objetos para o preview 2D do editor.
  const _objImgCache = {};
  function objImg(name) {
    if (!name) return null;
    let im = _objImgCache[name];
    if (im === undefined) {
      im = new Image();
      im.onload = () => render();
      im.src = "../assets/objetos/" + name;
      _objImgCache[name] = im;
    }
    return (im.complete && im.naturalWidth) ? im : null;
  }

  // As artes de parede recebidas podem vir com fundo preto opaco. Mantemos o
  // PNG original e apenas tratamos os pixels quase pretos como transparentes
  // no preview, tal como o renderer 3D faz no jogo.
  const _wallImgCache = {};
  function wallImg(name) {
    const source = objImg(name);
    if (!source) return null;
    if (_wallImgCache[name]) return _wallImgCache[name];
    const canvas = document.createElement("canvas");
    canvas.width = source.naturalWidth;
    canvas.height = source.naturalHeight;
    const c = canvas.getContext("2d");
    c.drawImage(source, 0, 0);
    const pixels = c.getImageData(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < pixels.data.length; i += 4) {
      const high = Math.max(pixels.data[i], pixels.data[i + 1], pixels.data[i + 2]);
      if (high <= 10) pixels.data[i + 3] = 0;
      else if (high < 32) pixels.data[i + 3] = Math.round(pixels.data[i + 3] * (high - 10) / 22);
    }
    c.putImageData(pixels, 0, 0);
    _wallImgCache[name] = canvas;
    return canvas;
  }

  function emojiForCell(x, y) {
    const at = (arr) => arr.find(e => e.pos && e.pos[0] === x && e.pos[1] === y);
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return "🚪";
    if (S.exit && S.exit.x === x && S.exit.y === y) return "🏁";
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return "🧍";
    const mo = at(S.monsters);
    if (mo) { const d = CAT.monsters.find(c => c.type === mo.type); return d ? d.emoji : "👹"; }
    if (at(S.chests)) return "🧰";
    const tr = at(S.traps);
    if (tr) {
      // Com imagem carregada, o PNG cobre a casa (desenhado à parte) — suprime o emoji.
      if (tr.image && objImg(tr.image)) return null;
      const d = CAT.traps.find(c => c.tipo === tr.tipo); return d ? d.icone : "⚠️";
    }
    // Empilhamento: o chão (piso) fica embaixo — mostra o emoji do objeto de CIMA.
    const _decsAt = S.decorations.filter(e => e.pos[0] === x && e.pos[1] === y);
    const dec = _decsAt.find(e => !isFloorDecor(e)) || _decsAt[0];
    if (dec) {
      // Se a decoração tem imagem e ela já carregou, não retorna emoji (a imagem cobre o footprint).
      if (dec.image && (isWallDecor(dec) ? wallImg(dec.image) : objImg(dec.image))) return null;
      // Decorações com escala visual são desenhadas à parte (ancoradas/escaladas).
      const vs = dec.vscale;
      if (Array.isArray(vs) && (vs[0] !== 1 || vs[1] !== 1)) return null;
      const m = decorMeta(dec.type); return m ? m.emoji : "🪑";
    }
    return null;
  }

  function render() {
    board.width = S.grid.w * CELL;
    board.height = S.grid.h * CELL;
    for (let y = 0; y < S.grid.h; y++) {
      for (let x = 0; x < S.grid.w; x++) {
        const t = S.tiles[y][x];
        const mid = S.materiais[x + "," + y];
        const mm = mid ? matMeta(mid) : null;
        ctx.fillStyle = mm ? mm.cor : (t === WALL ? "#1d1812" : (t === DOOR ? "#c8841f" : "#5a4a32"));
        ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        if (mid === "entulho") {            // marca de obstáculo
          ctx.fillStyle = "rgba(0,0,0,0.45)";
          ctx.fillRect(x * CELL + CELL * 0.3, y * CELL + CELL * 0.3, CELL * 0.4, CELL * 0.4);
        }
      }
    }
    for (const r of S.rooms) {
      ctx.strokeStyle = r.locked ? "#e0683c" : "#8fb0e0";
      ctx.lineWidth = 2;
      ctx.strokeRect(r.x * CELL + 1, r.y * CELL + 1, r.w * CELL - 2, r.h * CELL - 2);
      ctx.fillStyle = "#9fb8d8"; ctx.font = "10px sans-serif"; ctx.textBaseline = "top";
      ctx.fillText((r.locked ? "🔒" : "") + r.role + "#" + r.id, r.x * CELL + 3, r.y * CELL + 3);
    }
    // Passagens ficam deliberadamente explícitas no editor (nunca no jogo normal).
    for (const sp of S.secretPassages) {
      const [sx, sy] = sp.pos;
      ctx.fillStyle = sp.type === "illusion" ? "rgba(80,210,255,.42)" : "rgba(185,100,255,.42)";
      ctx.fillRect(sx * CELL + 2, sy * CELL + 2, CELL - 4, CELL - 4);
      ctx.fillStyle = "#fff"; ctx.font = "15px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(sp.type === "illusion" ? "◌" : "⚙", sx * CELL + CELL / 2, sy * CELL + CELL / 2);
    }
    for (const d of S.decorations) {
      ctx.strokeStyle = "#6ad0a0"; ctx.lineWidth = 1;
      for (const [tx, ty] of decorTiles(d)) ctx.strokeRect(tx * CELL + 2, ty * CELL + 2, CELL - 5, CELL - 5);
    }
    // Preview 2D: desenha o PNG da decoração cobrindo o footprint (se d.image disponível).
    // Chão (piso) primeiro → fica EMBAIXO; objetos empilhados desenham por cima.
    const _decorDrawOrder = [...S.decorations].sort((a, b) => (isFloorDecor(a) ? 0 : 1) - (isFloorDecor(b) ? 0 : 1));
    for (const d of _decorDrawOrder) {
      if (!d.image) continue;
      const im = isWallDecor(d) ? wallImg(d.image) : objImg(d.image);
      if (!im) continue;
      const tiles = decorTiles(d);
      const _dm = decorMeta(d.type);
      if (_dm && _dm.special === "floor") {
        // Chão: preenche cada casa borda-a-borda (sem manter proporção).
        for (const [tx, ty] of tiles) ctx.drawImage(im, tx * CELL, ty * CELL, CELL, CELL);
        continue;
      }
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      const px = minX * CELL + 2, py = minY * CELL + 2;
      const pw = (maxX - minX + 1) * CELL - 4, ph = (maxY - minY + 1) * CELL - 4;
      const vs = Array.isArray(d.vscale) ? d.vscale : [1, 1];
      const ang = facingAngle2D(d.facing);
      if (ang === 0) {
        // Escala visual: altura cresce para cima (âncora na base), largura centralizada.
        const dw = pw * vs[0], dh = ph * vs[1];
        ctx.drawImage(im, px + pw / 2 - dw / 2, py + ph - dh, dw, dh);
      } else {
        // Girado: encaixa no frame local (caixa trocada p/ 90°/270°), proporção do PNG,
        // e gira sobre o centro do footprint.
        const rot90 = (ang === Math.PI / 2 || ang === -Math.PI / 2);
        const boxW = rot90 ? ph : pw, boxH = rot90 ? pw : ph;
        const ar = im.naturalWidth / im.naturalHeight;
        let dw = boxW, dh = boxW / ar;
        if (dh > boxH) { dh = boxH; dw = boxH * ar; }
        dw *= vs[0]; dh *= vs[1];
        ctx.save();
        ctx.translate(px + pw / 2, py + ph / 2);
        ctx.rotate(ang);
        ctx.drawImage(im, -dw / 2, -dh / 2, dw, dh);
        ctx.restore();
      }
    }
    // Preview 2D: PNG da armadilha (se houver) cobrindo a casa, proporção preservada.
    for (const t of S.traps) {
      if (!t.image) continue;
      const im = objImg(t.image);
      if (!im) continue;
      const px = t.pos[0] * CELL + 2, py = t.pos[1] * CELL + 2, sz = CELL - 4;
      const ar = im.naturalWidth / im.naturalHeight;
      let dw = sz, dh = sz / ar;
      if (dh > sz) { dh = sz; dw = sz * ar; }
      ctx.drawImage(im, px + (sz - dw) / 2, py + (sz - dh) / 2, dw, dh);
    }
    ctx.font = "16px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (let y = 0; y < S.grid.h; y++) {
      for (let x = 0; x < S.grid.w; x++) {
        const e = emojiForCell(x, y);
        if (e) ctx.fillText(e, x * CELL + CELL / 2, y * CELL + CELL / 2);
      }
    }
    // Saídas das armadilhas de teletransporte: visíveis apenas no editor para
    // facilitar conferir o ponto configurado antes de salvar a masmorra.
    ctx.fillStyle = "#78d9ff"; ctx.font = "bold 15px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (const t of S.traps) {
      if (t.tipo !== "armadilha_teletransporte" || !Array.isArray(t.saida)) continue;
      ctx.fillText("⇱", t.saida[0] * CELL + CELL / 2, t.saida[1] * CELL + CELL / 2);
    }
    ctx.textAlign = "start";
    // Emojis de decorações com escala visual: desenhados à parte, ancorados na
    // base-centro do footprint e crescendo para cima.
    for (const d of S.decorations) {
      const vs = Array.isArray(d.vscale) ? d.vscale : null;
      if (!vs || (vs[0] === 1 && vs[1] === 1)) continue;
      if (d.image && (isWallDecor(d) ? wallImg(d.image) : objImg(d.image))) continue;
      const m = decorMeta(d.type); const emoji = m ? m.emoji : "🪑";
      const tiles = decorTiles(d);
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const maxY = Math.max(...tiles.map(t => t[1]));
      const cx = (minX + (maxX - minX + 1) / 2) * CELL;
      const baseY = (maxY + 1) * CELL - 4;
      ctx.save();
      ctx.font = (16 * Math.max(vs[0], vs[1])) + "px sans-serif";
      ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
      ctx.fillText(emoji, cx, baseY);
      ctx.restore();
    }
    if (S.sel && S.sel.kind === "decor" && S.sel.ref) {
      // Referência: contorno do footprint realçado + rótulo W×H (casas efetivas).
      const tiles = decorTiles(S.sel.ref);
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 2;
      ctx.strokeRect(minX * CELL + 1.5, minY * CELL + 1.5, (maxX - minX + 1) * CELL - 3, (maxY - minY + 1) * CELL - 3);
      const [ew, eh] = decorEffSizeOf(S.sel.ref);
      const label = ew + "×" + eh;
      ctx.font = "11px sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "top";
      const lx = minX * CELL + 3, ly = minY * CELL + 3;
      const tw = ctx.measureText(label).width;
      ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(lx - 1, ly - 1, tw + 4, 13);
      ctx.fillStyle = "#ffd86a"; ctx.fillText(label, lx + 1, ly);
      ctx.textAlign = "start";
    } else if (S.sel && S.sel.pos) {
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 2;
      ctx.strokeRect(S.sel.pos[0] * CELL + 1, S.sel.pos[1] * CELL + 1, CELL - 3, CELL - 3);
    }
    if (decorClipboard && lastPointerCell && !_drag) drawClipboardPreview();
    if (_drag && _drag.candidate) drawDragPreview();
    if (document.getElementById("status")) updateStatus();
  }

  function drawClipboardPreview() {
    const d = cloneDecor(decorClipboard);
    d.pos = lastPointerCell.slice();
    const valid = decorWouldFit(d, d.pos, decorBaseSize(d), d.facing || [0, 1]);
    ctx.save();
    ctx.setLineDash([4, 3]); ctx.lineWidth = 2;
    ctx.strokeStyle = valid ? "#72e6a1" : "#ed7777";
    ctx.fillStyle = valid ? "rgba(67,180,111,0.16)" : "rgba(210,75,75,0.16)";
    for (const [tx, ty] of decorTiles(d)) {
      if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) continue;
      ctx.fillRect(tx * CELL + 2, ty * CELL + 2, CELL - 4, CELL - 4);
      ctx.strokeRect(tx * CELL + 2, ty * CELL + 2, CELL - 4, CELL - 4);
    }
    ctx.setLineDash([]); ctx.restore();
  }

  // Preview do destino durante o arrasto: contorno verde (válido) / vermelho.
  function drawDragPreview() {
    if (!_drag || !_drag.candidate) return;
    const [ax, ay] = _drag.candidate;
    const tiles = _drag.sel.kind === "decor"
      ? tilesFor([ax, ay], decorBaseSize(_drag.sel.ref), _drag.sel.ref.facing)
      : [[ax, ay]];
    ctx.strokeStyle = _drag.valid ? "#6ad06a" : "#d05a5a"; ctx.lineWidth = 2;
    for (const [tx, ty] of tiles) {
      if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) continue;
      ctx.strokeRect(tx * CELL + 1, ty * CELL + 1, CELL - 2, CELL - 2);
    }
  }

  const TOOLS = [
    { id: "wall", label: "parede", group: "tiles" },
    { id: "floor", label: "chão", group: "tiles" },
    { id: "door", label: "porta", group: "tiles" },
    { id: "entrance", label: "entrada", group: "entidades" },
    { id: "exit", label: "saída", group: "entidades" },
    { id: "monster", label: "monstro", group: "entidades" },
    { id: "chest", label: "baú", group: "entidades" },
    { id: "trap", label: "armadilha", group: "entidades" },
    { id: "prisoner", label: "prisioneiro", group: "entidades" },
    { id: "decor", label: "decoração", group: "entidades" },
    { id: "secret_mechanism", label: "passagem secreta", group: "entidades" },
    { id: "illusion_wall", label: "parede ilusória", group: "entidades" },
    { id: "room", label: "sala", group: "ações" },
    { id: "select", label: "selecionar", group: "ações" },
    { id: "erase", label: "apagar", group: "ações" },
  ];

  function buildToolbar() {
    const tb = document.getElementById("toolbar");
    tb.innerHTML = "";
    let lastGroup = null;
    for (const t of TOOLS) {
      if (t.group !== lastGroup) {
        if (lastGroup) { const s = document.createElement("span"); s.className = "sep"; tb.appendChild(s); }
        const g = document.createElement("span"); g.className = "group-label"; g.textContent = t.group; tb.appendChild(g);
        lastGroup = t.group;
      }
      const b = document.createElement("button");
      b.textContent = t.label; b.dataset.tool = t.id;
      if (t.id === S.tool) b.classList.add("active");
      b.onclick = () => { S.tool = t.id; buildToolbar(); };
      tb.appendChild(b);
    }
    if (S.tool === "decor") {
      const sel = document.createElement("select");
      sel.id = "decor-type";
      const floor = CAT.decorations.filter(d => d.special !== "wall");
      const walls = CAT.decorations.filter(d => d.special === "wall");
      sel.innerHTML = `<optgroup label="Decorações de chão">${floor.map(d =>
        `<option value="${d.type}"${d.type === S.decorType ? " selected" : ""}>${d.emoji} ${d.nome}</option>`).join("")}</optgroup><optgroup label="Decorações de parede">${walls.map(d =>
        `<option value="${d.type}"${d.type === S.decorType ? " selected" : ""}>${d.emoji} ${d.nome}</option>`).join("")}</optgroup>`;
      sel.onchange = e => { S.decorType = e.target.value; S.decorFacing = [0, 1]; };
      tb.appendChild(sel);
      const rot = document.createElement("button");
      rot.textContent = "girar 90° (R)";
      rot.onclick = () => { rotateDecorPending(); };
      tb.appendChild(rot);
    }
    if (S.tool === "floor" || S.tool === "wall") {
      const isWall = S.tool === "wall";
      const opts = MAT.filter(m => isWall
        ? (m.categoria === "parede" || m.id === "entulho")
        : (m.categoria === "piso" && m.id !== "entulho"));
      const cur = isWall ? S.matWall : S.matFloor;
      const sel = document.createElement("select");
      sel.id = "mat-id";
      sel.innerHTML = opts.map(m =>
        `<option value="${m.id}"${m.id === cur ? " selected" : ""}>${m.categoria === "parede" ? "🧱" : (m.id === "entulho" ? "⛰️" : "▦")} ${m.nome}</option>`).join("");
      sel.onchange = e => { if (isWall) S.matWall = e.target.value; else S.matFloor = e.target.value; };
      tb.appendChild(sel);
      const fill = document.createElement("button");
      fill.textContent = S.matFill ? "balde: ON" : "balde: OFF";
      fill.title = "Preenche a região contígua de mesma estrutura";
      fill.onclick = () => { S.matFill = !S.matFill; buildToolbar(); };
      tb.appendChild(fill);
    }
  }

  function cellFromEvent(ev) {
    const r = board.getBoundingClientRect();
    const x = Math.floor((ev.clientX - r.left) / (r.width / S.grid.w));
    const y = Math.floor((ev.clientY - r.top) / (r.height / S.grid.h));
    if (x < 0 || y < 0 || x >= S.grid.w || y >= S.grid.h) return null;
    return [x, y];
  }

  function roomBorderTouches(r, x, y) {
    // (x,y) é casa de porta válida para a sala r se for adjacente (ortogonal) a
    // uma casa da borda do retângulo da sala, ou estiver na própria borda.
    for (const [dx, dy] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const bx = x + dx, by = y + dy;
      const onEdge = (bx === r.x || bx === r.x + r.w - 1 || by === r.y || by === r.y + r.h - 1);
      const inside = bx >= r.x && bx < r.x + r.w && by >= r.y && by < r.y + r.h;
      if (inside && onEdge) return true;
    }
    return false;
  }
  function doorLink(x, y) {
    for (const r of S.rooms) {
      if (roomBorderTouches(r, x, y) && !r.doors.some(d => d[0] === x && d[1] === y))
        r.doors.push([x, y]);
    }
  }
  function doorUnlink(x, y) {
    for (const r of S.rooms) r.doors = r.doors.filter(d => !(d[0] === x && d[1] === y));
  }

  function paintTile(x, y) {
    if (S.tool === "wall") {
      if (S.matWall === "entulho") { S.tiles[y][x] = FLOOR; S.materiais[x + "," + y] = "entulho"; return; }
      S.tiles[y][x] = WALL;
      _applyMat(x, y, S.matWall, "parede");
    } else if (S.tool === "floor") {
      S.tiles[y][x] = FLOOR;
      _applyMat(x, y, S.matFloor, "piso");
    } else if (S.tool === "door") {
      S.tiles[y][x] = DOOR; doorLink(x, y);
      const mid = S.materiais[x + "," + y];
      if (mid && !matCompat(mid, x, y)) delete S.materiais[x + "," + y];
    }
  }

  // Categoria do material compatível com a estrutura do tile?
  function matCompat(id, x, y) {
    const meta = matMeta(id); if (!meta) return false;
    const t = S.tiles[y][x];
    if (meta.categoria === "parede") return t === WALL;
    return t === FLOOR || t === DOOR;   // piso (inclui entulho)
  }
  // Estrutura "pintável junta" p/ balde: parede vs. não-parede.
  function _structKind(x, y) { return S.tiles[y][x] === WALL ? "wall" : "floor"; }
  // Aplica material M na casa (limpa se for o default da categoria → JSON esparso).
  function _applyMat(x, y, M, cat) {
    if (M === MAT_DEFAULT[cat]) delete S.materiais[x + "," + y];
    else S.materiais[x + "," + y] = M;
  }
  // Balde: preenche a região 4-conexa de mesma estrutura aplicando o tool atual.
  function paintMaterial(x, y) {
    if (!S.matFill) { paintTile(x, y); return; }
    const kind = _structKind(x, y);
    const seen = new Set([x + "," + y]); const st = [[x, y]];
    while (st.length) {
      const [cx, cy] = st.pop();
      if (_structKind(cx, cy) === kind) paintTile(cx, cy);
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = cx + dx, ny = cy + dy, k = nx + "," + ny;
        if (nx >= 0 && ny >= 0 && nx < S.grid.w && ny < S.grid.h && !seen.has(k)
            && _structKind(nx, ny) === kind) { seen.add(k); st.push([nx, ny]); }
      }
    }
  }

  let painting = false;
  let roomDrag = null;
  let _drag = null;  // arrasto na ferramenta "selecionar"

  // Casa de destino válida para soltar a entidade `sel` ancorada em (ax,ay).
  function dropValid(sel, ax, ay) {
    if (sel.kind === "decor" && isWallDecor(sel.ref)) {
      const placement = wallPlacementAt(ax, ay, sel.ref.facing);
      return !!placement && decorFits(sel.ref.type, placement.pos[0], placement.pos[1], placement.facing, sel.ref);
    }
    if (sel.kind === "decor")
      return decorWouldFit(sel.ref, [ax, ay], decorBaseSize(sel.ref), sel.ref.facing);
    return ax >= 0 && ay >= 0 && ax < S.grid.w && ay < S.grid.h && S.tiles[ay][ax] !== WALL;
  }
  // Move a entidade selecionada para (nx,ny), conforme o tipo.
  function moveSelTo(sel, nx, ny) {
    const k = sel.kind;
    if (k === "entrance") { S.entrance.x = nx; S.entrance.y = ny; }
    else if (k === "exit") { S.exit.x = nx; S.exit.y = ny; }
    else if (sel.ref) {
      if (k === "decor" && isWallDecor(sel.ref)) {
        const placement = wallPlacementAt(nx, ny, sel.ref.facing);
        if (!placement) return;
        sel.ref.pos = placement.pos;
        sel.ref.facing = placement.facing;
      } else sel.ref.pos = [nx, ny];  // prisoner/monster/chest/trap/decor
    }
    sel.pos = sel.ref && sel.ref.pos ? sel.ref.pos.slice() : [nx, ny];
  }

  function entityAt(x, y) {
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return { kind: "entrance", pos: [x, y] };
    if (S.exit && S.exit.x === x && S.exit.y === y) return { kind: "exit", pos: [x, y] };
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return { kind: "prisoner", ref: S.prisoner, pos: [x, y] };
    const secret = S.secretPassages.find(p => p.pos[0] === x && p.pos[1] === y);
    if (secret) return { kind: "secret_passage", ref: secret, pos: [x, y] };
    const find = (arr, kind) => { const r = arr.find(e => e.pos[0] === x && e.pos[1] === y); return r ? { kind, ref: r, pos: [x, y] } : null; };
    // Empilhamento: seleciona o objeto de CIMA (não-piso) antes do chão.
    const _decsHere = S.decorations.filter(d => decorTiles(d).some(c => c[0] === x && c[1] === y));
    const dec = _decsHere.find(d => !isFloorDecor(d)) || _decsHere[0];
    if (dec) return { kind: "decor", ref: dec, pos: dec.pos.slice() };
    return find(S.monsters, "monster") || find(S.chests, "chest") || find(S.traps, "trap") || null;
  }

  function roomIdAt(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? r.id : null;
  }

  function placeEntity(x, y) {
    const rid = roomIdAt(x, y);
    switch (S.tool) {
      case "entrance": S.entrance = { x, y }; break;
      case "exit": S.exit = { x, y }; break;
      case "prisoner": S.prisoner = { pos: [x, y], room_id: rid }; break;
      case "monster": S.monsters.push({ type: (CAT.monsters[0] || {}).type || "goblin", pos: [x, y], room_id: rid, boss: false, target: false }); break;
      case "chest": S.chests.push({ pos: [x, y], gold: 0, items: [], key_objective: false }); break;
      case "trap": S.traps.push({ tipo: (CAT.traps[0] || {}).tipo || "fosso_estacas", pos: [x, y] }); break;
      case "decor": placeDecor(x, y); break;
      case "secret_mechanism":
        if (S.tiles[y][x] === WALL && !S.secretPassages.some(p => p.pos[0] === x && p.pos[1] === y))
          S.secretPassages.push({ id: "passage_" + S.nextPassageId++, pos: [x, y], type: "mechanism", key_decor_ids: [], keys_mode: "any" });
        break;
      case "illusion_wall":
        if (S.tiles[y][x] === WALL && !S.secretPassages.some(p => p.pos[0] === x && p.pos[1] === y))
          S.secretPassages.push({ id: "passage_" + S.nextPassageId++, pos: [x, y], type: "illusion", key_decor_ids: [], keys_mode: "any" });
        break;
    }
  }

  function eraseAt(x, y) {
    if (S.tiles[y][x] === DOOR) doorUnlink(x, y);
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) S.entrance = null;
    if (S.exit && S.exit.x === x && S.exit.y === y) S.exit = null;
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) S.prisoner = null;
    S.monsters = S.monsters.filter(e => !(e.pos[0] === x && e.pos[1] === y));
    S.chests = S.chests.filter(e => !(e.pos[0] === x && e.pos[1] === y));
    S.traps = S.traps.filter(e => !(e.pos[0] === x && e.pos[1] === y));
    S.decorations = S.decorations.filter(d => !decorTiles(d).some(c => c[0] === x && c[1] === y));
    S.secretPassages = S.secretPassages.filter(p => !(p.pos[0] === x && p.pos[1] === y));
    delete S.materiais[x + "," + y];
    S.tiles[y][x] = WALL;
  }

  function deleteRoom(room, clearFloor) {
    const idx = S.rooms.indexOf(room);
    if (idx >= 0) S.rooms.splice(idx, 1);
    if (clearFloor) {
      for (let j = room.y; j < room.y + room.h; j++) {
        for (let i = room.x; i < room.x + room.w; i++) {
          if (S.tiles[j] && S.tiles[j][i] !== undefined) {
            if (S.tiles[j][i] === DOOR) doorUnlink(i, j);
            S.tiles[j][i] = WALL;
          }
        }
      }
    }
    // Entidades que apontavam para esta sala ficam sem sala (não são apagadas).
    for (const m of S.monsters) if (m.room_id === room.id) m.room_id = null;
    if (S.prisoner && S.prisoner.room_id === room.id) S.prisoner.room_id = null;
    S.sel = null; renderPanel(); render();
  }

  const panel = document.getElementById("panel");
  function opt(list, val, fmt) { return list.map(o => `<option value="${o.v}"${o.v === val ? " selected" : ""}>${fmt(o)}</option>`).join(""); }

  function objDefaults(isPrimary) {
    return { xp: isPrimary ? 0 : 50, reward: { gold: isPrimary ? 0 : 25, items: [] } };
  }
  function normalizeObjective(obj, isPrimary) {
    const d = objDefaults(isPrimary);
    if (typeof obj.xp !== "number") obj.xp = d.xp;
    if (!obj.reward || typeof obj.reward !== "object") obj.reward = { gold: d.reward.gold, items: [] };
    if (typeof obj.reward.gold !== "number") obj.reward.gold = d.reward.gold;
    if (!Array.isArray(obj.reward.items)) obj.reward.items = [];
    return obj;
  }
  // HTML dos campos de recompensa de um objetivo. `pfx` é um prefixo único de ids.
  function rewardFieldsHTML(obj, pfx) {
    return `<label>XP (total, dividido entre os vivos) <input id="${pfx}-xp" type="number" min="0" value="${obj.xp}"></label>
      <label>ouro (total, dividido) <input id="${pfx}-gold" type="number" min="0" value="${obj.reward.gold}"></label>
      <label>itens de recompensa</label>
      <div id="${pfx}-items">${obj.reward.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="${pfx}-rm">×</button></div>`).join("")}</div>
      <select id="${pfx}-add">${opt(CAT.items.map(it => ({ v: it.id, name: it.name })), "", o => o.v + " — " + o.name)}</select>
      <button id="${pfx}-additem">+ item</button>`;
  }
  function wireRewardFields(obj, pfx) {
    document.getElementById(`${pfx}-xp`).onchange = e => { obj.xp = Math.max(0, Number(e.target.value) | 0); };
    document.getElementById(`${pfx}-gold`).onchange = e => { obj.reward.gold = Math.max(0, Number(e.target.value) | 0); };
    document.getElementById(`${pfx}-additem`).onclick = () => { const id = document.getElementById(`${pfx}-add`).value; if (id) obj.reward.items.push({ id }); renderPanel(); };
    panel.querySelectorAll(`.${pfx}-rm`).forEach(b => b.onclick = () => { obj.reward.items.splice(Number(b.dataset.i), 1); renderPanel(); });
  }

  var _ndPreviewHeroes = null;   // null = usa S.expectedParty.heroes; 2/4/6 = preview

  function _ndPorSala() {
    // Soma de cr por room_id (null vira grupo "sem sala"). Retorna {total, pior}.
    var porSala = {}, total = 0;
    (S.monsters || []).forEach(function (m) {
      var entry = (CAT.monsters || []).find(function (c) { return c.type === m.type; });
      var cr = window.Difficulty ? window.Difficulty.crFromEntry(entry) : 0;
      total += cr;
      var key = (m.room_id == null) ? "__none__" : m.room_id;
      porSala[key] = (porSala[key] || 0) + cr;
    });
    // Armadilhas autoradas: cr do catálogo; agrupadas por sala via pos (não têm room_id).
    (S.traps || []).forEach(function (t) {
      var meta = (CAT.traps || []).find(function (c) { return c.tipo === t.tipo; });
      var cr = meta ? (meta.cr || 0) : 0;
      if (!cr || !t.pos) return;
      total += cr;
      var r = (S.rooms || []).find(function (rm) {
        return t.pos[0] >= rm.x && t.pos[0] < rm.x + rm.w && t.pos[1] >= rm.y && t.pos[1] < rm.y + rm.h;
      });
      var key = r ? r.id : "__none__";
      porSala[key] = (porSala[key] || 0) + cr;
    });
    var pior = 0;
    Object.keys(porSala).forEach(function (k) { if (porSala[k] > pior) pior = porSala[k]; });
    return { total: total, pior: pior };
  }

  function _termometroHTML() {
    if (!window.Difficulty) return "";
    var heroes = (_ndPreviewHeroes != null) ? _ndPreviewHeroes : S.expectedParty.heroes;
    var pod = window.Difficulty.poder(heroes, S.expectedParty.level);
    var nd = _ndPorSala();
    function linha(rot, valor) {
      var f = window.Difficulty.faixa(valor, pod);
      var pct = Math.max(4, Math.min(100, (valor / (pod * 1.5)) * 100));
      return '<div style="margin-top:4px"><span>' + rot + ': <b>' + valor.toFixed(2) + '</b> — ' +
        '<span style="color:' + f.color + '">' + f.label + '</span></span>' +
        '<div style="height:8px;background:#241d14;border-radius:4px;overflow:hidden;margin-top:2px">' +
        '<div style="height:100%;width:' + pct + '%;background:' + f.color + '"></div></div></div>';
    }
    var atual = (_ndPreviewHeroes != null ? _ndPreviewHeroes : S.expectedParty.heroes);
    var sel = [2, 4, 6].map(function (n) {
      return '<button data-ndprev="' + n + '" class="ndprev' + (atual === n ? ' on' : '') + '">' + n + '</button>';
    }).join("");
    return '<hr style="border-color:#3a3022;margin:10px 0"><label>🌡️ termômetro (poder ' + pod + ')</label>' +
      linha("Total", nd.total) + linha("Pior sala", nd.pior) +
      '<div style="margin-top:6px;display:flex;gap:4px;align-items:center"><span>preview jogadores:</span>' + sel + '</div>';
  }

  function renderPanel() {
    if (!S.sel) {
      const OBJ = ["kill_target", "kill_all", "reach_exit", "open_key_chest", "rescue_prisoner"];
      const o = S.objectives;
      normalizeObjective(o.primary, true);
      o.secondary.forEach(s => normalizeObjective(s, false));
      panel.innerHTML = `<b>🗺️ Masmorra</b>
        <label>objetivo principal</label>
        <select id="o-prim">${OBJ.map(t => `<option value="${t}"${o.primary.type === t ? " selected" : ""}>${t}</option>`).join("")}</select>
        ${rewardFieldsHTML(o.primary, "o-prim-rw")}
        <hr style="border-color:#3a3022;margin:10px 0">
        <label>objetivos secundários</label>
        <div id="o-sec">${o.secondary.map((s, i) => `<div class="o-sec-item" style="border-top:1px solid #3a3022;padding-top:6px;margin-top:6px">
          <select data-i="${i}" class="o-secsel">${OBJ.map(t => `<option value="${t}"${s.type === t ? " selected" : ""}>${t}</option>`).join("")}</select>
          <button data-i="${i}" class="o-rm">× remover</button>
          ${rewardFieldsHTML(s, "o-sec" + i + "-rw")}
        </div>`).join("")}</div>
        <button id="o-add">+ secundário</button>
        <hr style="border-color:#3a3022;margin:10px 0">
        <label>⚠️ reforços do mestre</label>
        <div id="reinforce-list">${S.masterReinforcements.map((r, i) => {
          const meta = CAT.monsters.find(m => m.type === r.type) || {};
          return `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span>${meta.emoji || "👾"} ${meta.name || r.type} ×${r.count}</span>
            <button data-i="${i}" class="reinforce-rm">×</button>
          </div>`;
        }).join("") || '<small style="color:#8a7a5a">Nenhum reforço cadastrado.</small>'}</div>
        <div style="display:flex;gap:4px;align-items:flex-end;margin-top:6px">
          <select id="reinforce-type" style="flex:1">${opt(CAT.monsters.map(m => ({ v: m.type, name: m.name })), "", o => o.v + " — " + o.name)}</select>
          <input id="reinforce-count" type="number" min="1" value="1" style="width:56px">
          <button id="reinforce-add-btn">+</button>
        </div>
        <hr style="border-color:#3a3022;margin:10px 0">
        <label>👥 grupo esperado</label>
        <div style="display:flex;gap:6px;align-items:center;margin-top:4px">
          <span>heróis</span><input id="ep-heroes" type="number" min="1" max="6" value="${S.expectedParty.heroes}" style="width:48px">
          <span>nível</span><input id="ep-level" type="number" min="1" value="${S.expectedParty.level}" style="width:48px">
        </div>
        ${_termometroHTML()}`;
      document.getElementById("o-prim").onchange = e => { o.primary.type = e.target.value; };
      wireRewardFields(o.primary, "o-prim-rw");
      document.getElementById("o-add").onclick = () => { o.secondary.push({ type: "rescue_prisoner", ...objDefaults(false) }); renderPanel(); };
      panel.querySelectorAll(".o-secsel").forEach(sel => sel.onchange = e => { o.secondary[Number(e.target.dataset.i)].type = e.target.value; });
      panel.querySelectorAll(".o-rm").forEach(b => b.onclick = () => { o.secondary.splice(Number(b.dataset.i), 1); renderPanel(); });
      o.secondary.forEach((s, i) => wireRewardFields(s, "o-sec" + i + "-rw"));
      document.getElementById("reinforce-add-btn").onclick = () => {
        const type = document.getElementById("reinforce-type").value;
        const count = Math.max(1, Number(document.getElementById("reinforce-count").value) | 0);
        if (!type) return;
        const existing = S.masterReinforcements.find(r => r.type === type);
        if (existing) existing.count += count; else S.masterReinforcements.push({ type, count });
        renderPanel();
      };
      panel.querySelectorAll(".reinforce-rm").forEach(b => b.onclick = () => { S.masterReinforcements.splice(Number(b.dataset.i), 1); renderPanel(); });
      var epH = document.getElementById("ep-heroes");
      var epL = document.getElementById("ep-level");
      if (epH) epH.onchange = e => { S.expectedParty.heroes = Math.max(1, Math.min(6, parseInt(e.target.value, 10) || 4)); renderPanel(); };
      if (epL) epL.onchange = e => { S.expectedParty.level = Math.max(1, parseInt(e.target.value, 10) || 1); renderPanel(); };
      panel.querySelectorAll(".ndprev").forEach(function (b) {
        b.onclick = function () {
          var n = parseInt(b.dataset.ndprev, 10);
          _ndPreviewHeroes = (_ndPreviewHeroes === n) ? null : n;
          renderPanel();
        };
      });
      return;
    }
    const k = S.sel.kind, ref = S.sel.ref;
    if (k === "monster") {
      panel.innerHTML = `<b>👹 Monstro</b>
        <label>tipo</label><select id="p-type">${opt(CAT.monsters.map(m => ({ v: m.type, name: m.name })), ref.type, o => o.v + " — " + o.name)}</select>
        <label>room_id <input id="p-room" value="${ref.room_id ?? ""}"></label>
        <label><input type="checkbox" id="p-boss" ${ref.boss ? "checked" : ""}> chefe (boss)</label>
        <label><input type="checkbox" id="p-target" ${ref.target ? "checked" : ""}> alvo do objetivo</label>`;
      document.getElementById("p-type").onchange = e => { ref.type = e.target.value; render(); };
      document.getElementById("p-room").onchange = e => { ref.room_id = e.target.value === "" ? null : Number(e.target.value); };
      document.getElementById("p-boss").onchange = e => { ref.boss = e.target.checked; };
      document.getElementById("p-target").onchange = e => { ref.target = e.target.checked; };
    } else if (k === "chest") {
      panel.innerHTML = `<b>🧰 Baú</b>
        <label>ouro <input id="p-gold" type="number" value="${ref.gold}"></label>
        <label><input type="checkbox" id="p-key" ${ref.key_objective ? "checked" : ""}> baú-chave</label>
        <label>itens</label>
        <div id="p-items">${ref.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="rm-item">×</button></div>`).join("")}</div>
        <select id="p-add">${opt(CAT.items.map(it => ({ v: it.id, name: it.name })), "", o => o.v + " — " + o.name)}</select>
        <button id="p-additem">+ item</button>`;
      document.getElementById("p-gold").onchange = e => { ref.gold = Math.max(0, Number(e.target.value) | 0); };
      document.getElementById("p-key").onchange = e => { ref.key_objective = e.target.checked; };
      document.getElementById("p-additem").onclick = () => { const id = document.getElementById("p-add").value; if (id) ref.items.push({ id }); renderPanel(); };
      panel.querySelectorAll(".rm-item").forEach(b => b.onclick = () => { ref.items.splice(Number(b.dataset.i), 1); renderPanel(); });
    } else if (k === "trap") {
      const meta = CAT.traps.find(t => t.tipo === ref.tipo) || {};
      panel.innerHTML = `<b>⚠️ Armadilha</b>
        <label>tipo</label><select id="p-tt">${opt(CAT.traps.map(t => ({ v: t.tipo, name: t.nome })), ref.tipo, o => o.v + " — " + o.name)}</select>
        ${meta.precisa_veneno ? `<label>veneno</label><select id="p-ven">${opt(CAT.venoms.map(v => ({ v: v.id, name: v.name })), ref.veneno_id || "", o => o.v + " — " + o.name)}</select>` : ""}
        ${ref.tipo === "armadilha_teletransporte" ? `<label>ponto de saída (x, y)</label><div style="display:flex;gap:4px"><input id="p-out-x" type="number" min="0" max="${S.grid.w - 1}" value="${ref.saida ? ref.saida[0] : ref.pos[0]}"><input id="p-out-y" type="number" min="0" max="${S.grid.h - 1}" value="${ref.saida ? ref.saida[1] : ref.pos[1]}"></div><button id="p-pick-out" style="margin-top:5px">📍 Selecionar saída no mapa</button><small id="p-out-help" style="color:#8a7a5a">Casa de chão; se ocupada no jogo, usa a adjacente livre mais próxima.</small>` : ""}
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>Imagem</b>
          <div style="font-size:11px;color:#8a7a5a">PNG de assets/objetos — visível no jogo só quando a armadilha for revelada.</div>
          <div style="margin-top:4px">
            <select id="t-img-sel"></select>
            <button id="t-img-refresh" title="recarregar lista">↻</button>
          </div>
          <div style="margin-top:4px">
            <input id="t-img-file" type="file" accept="image/png" style="font-size:11px">
            <span id="t-img-st" style="font-size:11px;color:#8a7a5a"></span>
          </div>
        </div>`;
      document.getElementById("p-tt").onchange = e => { ref.tipo = e.target.value; if (!CAT.traps.find(t => t.tipo === ref.tipo).precisa_veneno) delete ref.veneno_id; if (ref.tipo !== "armadilha_teletransporte") delete ref.saida; renderPanel(); render(); };
      if (meta.precisa_veneno) document.getElementById("p-ven").onchange = e => { ref.veneno_id = e.target.value; };
      if (ref.tipo === "armadilha_teletransporte") {
        const setSaida = () => { ref.saida = [Number(document.getElementById("p-out-x").value) | 0, Number(document.getElementById("p-out-y").value) | 0]; render(); };
        document.getElementById("p-out-x").onchange = setSaida;
        document.getElementById("p-out-y").onchange = setSaida;
        document.getElementById("p-pick-out").onclick = () => {
          S.teleportExitPick = ref;
          document.getElementById("p-out-help").textContent = "Clique agora em uma casa de chão no mapa para definir a saída.";
        };
      }
      // Seletor de imagem (espelha o das decorações — pasta assets/objetos via OBJETO_UPLOAD).
      const tImgSel = document.getElementById("t-img-sel");
      const tImgSt = document.getElementById("t-img-st");
      function fillTrapImg(list) {
        const opts = ['<option value="">(nenhuma — ícone padrão)</option>']
          .concat(list.map(n => `<option value="${n}" ${ref.image === n ? "selected" : ""}>${n}</option>`));
        if (ref.image && list.indexOf(ref.image) < 0)
          opts.push(`<option value="${ref.image}" selected>${ref.image} (atual)</option>`);
        tImgSel.innerHTML = opts.join("");
      }
      fillTrapImg([]);
      function loadTrapImgList() {
        if (!window.OBJETO_UPLOAD) { tImgSt.textContent = "(offline: lista/upload indisponível)"; return; }
        window.OBJETO_UPLOAD.list()
          .then(list => fillTrapImg(list))
          .catch(() => { tImgSt.textContent = "servidor offline"; });
      }
      loadTrapImgList();
      tImgSel.onchange = e => { ref.image = e.target.value || null; render(); };
      document.getElementById("t-img-refresh").onclick = loadTrapImgList;
      document.getElementById("t-img-file").onchange = async e => {
        const file = e.target.files[0]; if (!file) return;
        if (!window.OBJETO_UPLOAD) { tImgSt.textContent = "servidor offline"; return; }
        tImgSt.textContent = "enviando…";
        try {
          const name = await window.OBJETO_UPLOAD.upload(file);
          ref.image = name;
          tImgSt.textContent = "enviada ✓";
          loadTrapImgList(); render();
        } catch (err) { tImgSt.textContent = "falha: " + err.message; }
      };
    } else if (k === "room") {
      panel.innerHTML = `<b>▦ Sala #${ref.id}</b>
        <label>role</label><select id="p-role">${opt(["entrance", "monster", "chest", "trap", "boss", "empty"].map(r => ({ v: r })), ref.role, o => o.v)}</select>
        <label><input type="checkbox" id="p-locked" ${ref.locked ? "checked" : ""}> trancada</label>
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">portas: ${ref.doors.length}</div>
        <button id="p-del-room" style="margin-top:10px">🗑 Deletar sala</button>
        <div id="p-del-confirm" style="display:none;margin-top:6px">
          <div style="font-size:11px;color:#d8a0a0;margin-bottom:4px">Deletar a sala #${ref.id}?</div>
          <button id="p-del-keep">Deletar (manter chão)</button>
          <button id="p-del-clear">Deletar (limpar chão)</button>
        </div>`;
      document.getElementById("p-role").onchange = e => { ref.role = e.target.value; render(); };
      document.getElementById("p-locked").onchange = e => { ref.locked = e.target.checked; render(); };
      document.getElementById("p-del-room").onclick = () => {
        document.getElementById("p-del-confirm").style.display = "";
      };
      document.getElementById("p-del-keep").onclick = () => deleteRoom(ref, false);
      document.getElementById("p-del-clear").onclick = () => deleteRoom(ref, true);
    } else if (k === "prisoner") {
      const img = ref.image
        ? `<img src="../assets/pawns/prisioneiros/${ref.image}" style="max-width:64px;max-height:64px;display:block;margin:6px 0;border:1px solid #5a4a2a">`
        : `<div style="color:#8a7a5a;font-size:11px;margin:6px 0">sem imagem — usará o emoji padrão</div>`;
      panel.innerHTML = `<b>🧍 Prisioneiro</b>
        <div style="color:#8a7a5a;font-size:11px">sala ${ref.room_id ?? "—"}</div>
        ${img}
        <label>miniatura</label>
        <input type="file" id="p-pris-img" accept="image/png,image/jpeg,image/webp,image/gif">
        <div id="p-pris-status" style="color:#8a7a5a;font-size:11px;margin-top:4px"></div>`;
      const inp = document.getElementById("p-pris-img");
      const st = document.getElementById("p-pris-status");
      inp.onchange = async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;
        st.textContent = "enviando…";
        try {
          const name = await window.PRISONER_UPLOAD.upload(file);
          ref.image = name;
          st.textContent = "enviada ✓";
          renderPanel(); render();
        } catch (err) {
          st.textContent = "falha: " + err.message;
        }
      };
    } else if (k === "secret_passage") {
      const keys = S.decorations.filter(d => d.key_objective);
      panel.innerHTML = `<b>${ref.type === "illusion" ? "Parede ilusória" : "Passagem secreta"}</b>
        <div style="font-size:11px;color:#8a7a5a;margin:6px 0">${ref.type === "illusion" ? "Atravessável desde o início; somente o ladino a identifica durante Encontrar Armadilhas." : "Abre permanentemente quando suas decorações-chave forem ativadas."}</div>
        ${ref.type === "mechanism" ? `<label>ativação</label><select id="sp-mode"><option value="any"${ref.keys_mode === "any" ? " selected" : ""}>qualquer chave</option><option value="all"${ref.keys_mode === "all" ? " selected" : ""}>todas as chaves</option></select><label>decorações-chave</label><div id="sp-keys">${keys.length ? keys.map(d => `<label style="display:block"><input type="checkbox" value="${d.id}"${ref.key_decor_ids.includes(d.id) ? " checked" : ""}> ${decorMeta(d.type)?.nome || d.type} (${d.pos[0]},${d.pos[1]})</label>`).join("") : '<small>Marque uma decoração como objeto-chave primeiro.</small>'}</div>` : ""}`;
      if (ref.type === "mechanism") {
        document.getElementById("sp-mode").onchange = e => { ref.keys_mode = e.target.value; };
        panel.querySelectorAll("#sp-keys input").forEach(el => el.onchange = () => {
          ref.key_decor_ids = [...panel.querySelectorAll("#sp-keys input:checked")].map(i => i.value); render();
        });
      }
    } else if (k === "decor") {
      const m = decorMeta(ref.type) || {};
      const isWall = m.special === "wall";
      const hasLoot = !!ref.loot;
      const [bw, bh] = decorBaseSize(ref);
      const vs0 = Array.isArray(ref.vscale) ? ref.vscale : [1, 1];
      panel.innerHTML = `<b>${m.emoji || "🪑"} ${m.nome || ref.type}</b>
        <div style="color:#8a7a5a;font-size:11px">${m.size ? m.size[0] + "×" + m.size[1] : ""} ${m.alto ? "· alto (oclui visão)" : ""} ${m.pisavel ? "· pisável" : ""}</div>
        ${isWall ? `<div style="color:#8a7a5a;font-size:11px;margin-top:6px">Decoração de parede: clique em uma parede; girar troca a face voltada para uma área jogável.</div>` : ""}
        ${m.gira ? `<button id="d-rot">${isWall ? "trocar face" : "girar 90°"}</button>` : ""}
        ${!isWall ? `<button id="d-duplicate" style="margin-top:7px">⧉ Duplicar em casa adjacente</button>` : ""}
        <div id="d-duplicate-msg" style="font-size:11px;min-height:14px;color:#d8a0a0"></div>
        ${m.special === "fountain" ? `<label>cargas <input id="d-charges" type="number" min="0" value="${ref.charges ?? 0}"></label>` : ""}
        ${m.loot_capaz ? `<label style="display:block;margin-top:8px"><input type="checkbox" id="d-haslook" ${hasLoot ? "checked" : ""}> contém loot</label>` : ""}
        <label style="display:block;margin-top:8px"><input type="checkbox" id="d-chest-trap" ${ref.chest_trap_monster_type ? "checked" : ""}> baú-armadilha</label>
        ${ref.chest_trap_monster_type ? `<label>monstro que surge</label><select id="d-chest-monster">${opt(CAT.monsters.map(x => ({v:x.type,name:x.name})), ref.chest_trap_monster_type, o => o.v + " — " + o.name)}</select><small style="color:#8a7a5a">No primeiro clique, Reflexos CD 12; o loot só abre no próximo clique.</small>` : ""}
        <label style="display:block;margin-top:8px"><input type="checkbox" id="d-key" ${ref.key_objective ? "checked" : ""}> objeto-chave <small>(conclui “Abrir o baú-chave” ao interagir)</small></label>
        <div id="d-loot" style="${hasLoot ? "" : "display:none"}">
          <label>ouro <input id="d-gold" type="number" min="0" value="${hasLoot ? (ref.loot.gold | 0) : 0}"></label>
          <label>itens</label>
          <div id="d-items">${hasLoot ? ref.loot.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="d-rm">×</button></div>`).join("") : ""}</div>
          <select id="d-add">${opt(CAT.items.map(it => ({ v: it.id, name: it.name })), "", o => o.v + " — " + o.name)}</select>
          <button id="d-additem">+ item</button>
        </div>
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          ${!isWall ? `<b>Tamanho</b>
          <div style="font-size:11px;color:#8a7a5a">footprint em casas (quadrados ocupados)</div>
          <label>largura <input id="d-fw" type="number" min="1" max="${S.grid.w}" value="${bw}"></label>
          <label>altura <input id="d-fh" type="number" min="1" max="${S.grid.h}" value="${bh}"></label>
          <div id="d-size-msg" style="font-size:11px;color:#d8a0a0;min-height:14px"></div>` : `<b>Tamanho visual</b>
          <div style="font-size:11px;color:#8a7a5a">fica presa a uma única face da parede.</div>`}
          <div style="font-size:11px;color:#8a7a5a;margin-top:4px">tamanho visual (não muda casas; altura cresce p/ cima)</div>
          <label>escala largura <input id="d-vsx" type="number" min="0.2" max="4" step="0.1" value="${vs0[0]}"></label>
          <label>escala altura <input id="d-vsy" type="number" min="0.2" max="4" step="0.1" value="${vs0[1]}"></label>
        </div>
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
      if (m.gira) document.getElementById("d-rot").onclick = () => { rotateDecorPending(); renderPanel(); };
      const duplicate = document.getElementById("d-duplicate"); if (duplicate) duplicate.onclick = () => {
        if (duplicateDecorAdjacent(ref)) { renderPanel(); render(); }
        else document.getElementById("d-duplicate-msg").textContent = "Não há uma casa adjacente livre para esta cópia.";
      };
      if (m.special === "fountain") document.getElementById("d-charges").onchange = e => { ref.charges = Math.max(0, Number(e.target.value) | 0); };
      document.getElementById("d-key").onchange = e => { ref.key_objective = e.target.checked; };
      document.getElementById("d-chest-trap").onchange = e => { if (e.target.checked) ref.chest_trap_monster_type = (CAT.monsters[0] || {}).type; else delete ref.chest_trap_monster_type; renderPanel(); };
      if (ref.chest_trap_monster_type) document.getElementById("d-chest-monster").onchange = e => { ref.chest_trap_monster_type = e.target.value; };
      if (m.loot_capaz) document.getElementById("d-haslook").onchange = e => {
        ref.loot = e.target.checked ? { gold: 0, items: [] } : null; renderPanel();
      };
      if (hasLoot) {
        document.getElementById("d-gold").onchange = e => { ref.loot.gold = Math.max(0, Number(e.target.value) | 0); };
        document.getElementById("d-additem").onclick = () => { const id = document.getElementById("d-add").value; if (id) ref.loot.items.push({ id }); renderPanel(); };
        panel.querySelectorAll(".d-rm").forEach(b => b.onclick = () => { ref.loot.items.splice(Number(b.dataset.i), 1); renderPanel(); });
      }
      // Footprint (casas): aplica com bloqueio — reverte se não couber.
      function applyFootprint() {
        const nw = Math.max(1, Number(document.getElementById("d-fw").value) | 0);
        const nh = Math.max(1, Number(document.getElementById("d-fh").value) | 0);
        const msg = document.getElementById("d-size-msg");
        if (decorWouldFit(ref, ref.pos, [nw, nh], ref.facing)) {
          const def = decorMeta(ref.type);
          if (def && def.size[0] === nw && def.size[1] === nh) delete ref.size;
          else ref.size = [nw, nh];
          msg.textContent = ""; render();
        } else {
          msg.textContent = "não cabe (parede/fora/sobreposição) — revertido";
          const [cw, ch] = decorBaseSize(ref);
          document.getElementById("d-fw").value = cw;
          document.getElementById("d-fh").value = ch;
        }
      }
      const footprintWidth = document.getElementById("d-fw");
      const footprintHeight = document.getElementById("d-fh");
      if (footprintWidth && footprintHeight) {
        footprintWidth.onchange = applyFootprint;
        footprintHeight.onchange = applyFootprint;
      }
      // Escala visual: sem bloqueio (não ocupa casas).
      function applyVScale() {
        const sx = Math.max(0.2, Math.min(4, Number(document.getElementById("d-vsx").value) || 1));
        const sy = Math.max(0.2, Math.min(4, Number(document.getElementById("d-vsy").value) || 1));
        if (sx === 1 && sy === 1) delete ref.vscale; else ref.vscale = [sx, sy];
        render();
      }
      document.getElementById("d-vsx").onchange = applyVScale;
      document.getElementById("d-vsy").onchange = applyVScale;
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
    } else {
      panel.innerHTML = `<b>${k}</b>`;
    }
  }

  board.addEventListener("mousedown", (ev) => {
    if (ev.button !== 0) return;
    const c = cellFromEvent(ev); if (!c) return;
    lastPointerCell = c;
    const [x, y] = c;
    if (S.teleportExitPick) {
      if (S.tiles[y][x] !== FLOOR) {
        const help = document.getElementById("p-out-help");
        if (help) help.textContent = "A saída precisa ser escolhida em uma casa de chão.";
        return;
      }
      S.teleportExitPick.saida = [x, y];
      S.teleportExitPick = null;
      renderPanel(); render(); updateStatus();
      return;
    }
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; (S.matFill && S.tool !== "door" ? paintMaterial : paintTile)(x, y); render(); updateStatus(); }
    else if (S.tool === "room") { roomDrag = { x0: x, y0: y, x1: x, y1: y }; }
    else if (["entrance", "exit", "prisoner", "monster", "chest", "trap", "decor", "secret_mechanism", "illusion_wall"].includes(S.tool)) { placeEntity(x, y); if (S.tool !== "decor") S.sel = entityAt(x, y); renderPanel(); render(); }
    else if (S.tool === "erase") { eraseAt(x, y); S.sel = null; renderPanel(); render(); }
    else if (S.tool === "select") {
      S.sel = entityAt(x, y) || roomSel(x, y);
      // Entidades pontuais/decorações entram em modo arrasto (sala não).
      if (S.sel && S.sel.kind !== "room" && S.sel.pos) {
        const anchor = S.sel.pos;
        _drag = { sel: S.sel, offX: x - anchor[0], offY: y - anchor[1],
                  origin: anchor.slice(), candidate: null, valid: true, moved: false };
      } else { _drag = null; }
      renderPanel(); render();
    }
  });

  function roomSel(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? { kind: "room", ref: r } : null;
  }
  board.addEventListener("mousemove", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    lastPointerCell = c;
    if (_drag) {
      const ax = c[0] - _drag.offX, ay = c[1] - _drag.offY;
      _drag.candidate = [ax, ay];
      if (ax !== _drag.origin[0] || ay !== _drag.origin[1]) _drag.moved = true;
      _drag.valid = dropValid(_drag.sel, ax, ay);
      render();  // render() já desenha o preview via drawDragPreview()
      return;
    }
    if (painting) {
      if ((S.tool === "floor" || S.tool === "wall") && S.matFill) { paintMaterial(c[0], c[1]); updateStatus(); }
      else { paintTile(c[0], c[1]); updateStatus(); }
      render(); return;
    }
    if (roomDrag) {
      roomDrag.x1 = c[0]; roomDrag.y1 = c[1];
      render();
      const x = Math.min(roomDrag.x0, roomDrag.x1), y = Math.min(roomDrag.y0, roomDrag.y1);
      const w = Math.abs(roomDrag.x1 - roomDrag.x0) + 1, h = Math.abs(roomDrag.y1 - roomDrag.y0) + 1;
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 1;
      ctx.strokeRect(x * CELL + 1, y * CELL + 1, w * CELL - 2, h * CELL - 2);
      return;
    }
    if (decorClipboard) render();
  });
  board.addEventListener("contextmenu", ev => {
    ev.preventDefault();
    const c = cellFromEvent(ev); if (!c) return;
    lastPointerCell = c;
    showCopyMenu(ev, c);
  });
  window.addEventListener("mouseup", () => {
    painting = false;
    if (_drag) {
      if (_drag.moved && _drag.valid && _drag.candidate)
        moveSelTo(_drag.sel, _drag.candidate[0], _drag.candidate[1]);
      _drag = null; renderPanel(); render();
    }
    if (roomDrag) {
      const x = Math.min(roomDrag.x0, roomDrag.x1), y = Math.min(roomDrag.y0, roomDrag.y1);
      const w = Math.abs(roomDrag.x1 - roomDrag.x0) + 1, h = Math.abs(roomDrag.y1 - roomDrag.y0) + 1;
      if (w >= 2 && h >= 2) {
        for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) S.tiles[j][i] = FLOOR;
        const role = S.rooms.length === 0 ? "entrance" : "monster";
        S.rooms.push({ id: S.nextRoomId++, x, y, w, h, role, locked: role !== "entrance", doors: [] });
      }
      roomDrag = null; render();
    }
  });

  function buildJSON() {
    if (!S.objectives.primary) S.objectives.primary = { type: "kill_all" };
    if (!Array.isArray(S.objectives.secondary)) S.objectives.secondary = [];
    normalizeObjective(S.objectives.primary, true);
    S.objectives.secondary.forEach(s => normalizeObjective(s, false));
    return {
      schema_version: 1, id: S.meta.id, name: S.meta.name, ambiente: S.meta.ambiente || "masmorra",
      grid: { w: S.grid.w, h: S.grid.h },
      tiles: S.tiles.map(row => row.slice()),
      rooms: S.rooms.map(r => ({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: r.locked, doors: r.doors.map(d => d.slice()) })),
      entrance: S.entrance ? { x: S.entrance.x, y: S.entrance.y } : null,
      exit: S.exit ? { x: S.exit.x, y: S.exit.y } : null,
      monsters: S.monsters.map(m => ({ type: m.type, pos: m.pos.slice(), room_id: m.room_id, boss: !!m.boss, target: !!m.target })),
      chests: S.chests.map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: c.items.map(i => ({ id: i.id })), key_objective: !!c.key_objective })),
      traps: S.traps.map(t => { const o = { tipo: t.tipo, pos: t.pos.slice() }; if (t.veneno_id) o.veneno_id = t.veneno_id; if (t.saida) o.saida = t.saida.slice(); if (t.image) o.image = t.image; return o; }),
      decorations: S.decorations.map(d => {
        const o = { id: d.id, type: d.type, pos: d.pos.slice(), facing: d.facing.slice() };
        o.loot = d.loot ? { gold: d.loot.gold | 0, items: d.loot.items.map(i => ({ id: i.id })) } : null;
        o.key_objective = !!d.key_objective;
        if (d.chest_trap_monster_type) o.chest_trap_monster_type = d.chest_trap_monster_type;
        const m = decorMeta(d.type);
        if (m && m.special === "fountain") o.charges = d.charges | 0;
        if (d.image) o.image = d.image;
        // Override de tamanho por-objeto (editor-only; o servidor ignora estes campos).
        if (Array.isArray(d.size) && d.size.length === 2) o.size = [d.size[0] | 0, d.size[1] | 0];
        if (Array.isArray(d.vscale) && (d.vscale[0] !== 1 || d.vscale[1] !== 1)) o.vscale = [d.vscale[0], d.vscale[1]];
        return o;
      }),
      secret_passages: S.secretPassages.map(p => ({ id: p.id, type: p.type, pos: p.pos.slice(), key_decor_ids: p.key_decor_ids.slice(), keys_mode: p.keys_mode })),
      master_reinforcements: S.masterReinforcements.map(r => ({ type: r.type, count: r.count })),
      expected_party: { heroes: S.expectedParty.heroes, level: S.expectedParty.level },
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id, ...(S.prisoner.image ? { image: S.prisoner.image } : {}) } : null,
      materiais: { ...S.materiais },
      objectives: {
        primary: { type: S.objectives.primary.type, xp: S.objectives.primary.xp | 0,
                   reward: { gold: (S.objectives.primary.reward.gold | 0), items: S.objectives.primary.reward.items.map(i => ({ id: i.id })) } },
        secondary: S.objectives.secondary.map(s => ({ type: s.type, xp: s.xp | 0,
                   reward: { gold: (s.reward.gold | 0), items: s.reward.items.map(i => ({ id: i.id })) } })),
      },
    };
  }

  function reachableFloors(limit) {
    if (!S.entrance) return 0;
    const { x, y } = S.entrance;
    if (S.tiles[y][x] === WALL) return 0;
    const seen = new Set([x + "," + y]); const st = [[x, y]]; let n = 0;
    while (st.length) {
      const [cx, cy] = st.pop(); n++; if (n >= limit) return n;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = cx + dx, ny = cy + dy, k = nx + "," + ny;
        if (nx >= 0 && ny >= 0 && nx < S.grid.w && ny < S.grid.h && !seen.has(k) && S.tiles[ny][nx] !== WALL) { seen.add(k); st.push([nx, ny]); }
      }
    }
    return n;
  }

  function validarEditor() {
    const e = [];
    const types = new Set(CAT.monsters.map(m => m.type));
    const items = new Set(CAT.items.map(i => i.id));
    const traps = new Set(CAT.traps.map(t => t.tipo));
    const venoms = new Set(CAT.venoms.map(v => v.id));
    const roomIds = new Set(S.rooms.map(r => r.id));
    const isWall = (p) => !p || S.tiles[p[1]]?.[p[0]] === WALL || S.tiles[p[1]]?.[p[0]] === undefined;
    if (!S.entrance) e.push("falta a entrada");
    else if (S.tiles[S.entrance.y][S.entrance.x] !== FLOOR) e.push("entrada precisa estar em chão");
    if (S.rooms.length === 0) e.push("precisa de ao menos uma sala");
    if (!S.rooms.some(r => r.role === "entrance")) e.push("nenhuma sala com role 'entrance'");
    for (const m of S.monsters) {
      if (!types.has(m.type)) e.push(`monstro tipo inválido: ${m.type}`);
      if (isWall(m.pos)) e.push(`monstro em parede: ${m.pos}`);
      if (m.room_id != null && !roomIds.has(m.room_id)) e.push(`monstro room_id inexistente: ${m.room_id}`);
    }
    for (const c of S.chests) {
      if (isWall(c.pos)) e.push(`baú em parede: ${c.pos}`);
      for (const it of c.items) if (!items.has(it.id)) e.push(`item inválido: ${it.id}`);
    }
    for (const t of S.traps) {
      if (!traps.has(t.tipo)) e.push(`armadilha tipo inválido: ${t.tipo}`);
      if (isWall(t.pos)) e.push(`armadilha em parede: ${t.pos}`);
      if ((t.tipo === "fosso_envenenado" || t.tipo === "armadilha_dardos_envenenados") && !venoms.has(t.veneno_id)) e.push(`${t.tipo} sem veneno válido`);
      if (t.tipo === "armadilha_teletransporte" && (!Array.isArray(t.saida) || S.tiles[t.saida[1]]?.[t.saida[0]] !== FLOOR)) e.push("armadilha de teletransporte sem saída em chão");
    }
    if (S.prisoner && isWall(S.prisoner.pos)) e.push("prisioneiro em parede");
    for (const r of S.rooms) for (const d of r.doors) if (S.tiles[d[1]]?.[d[0]] !== DOOR) e.push(`porta declarada não é tile DOOR: ${d}`);
    if (reachableFloors(6) < 6) e.push("menos de 6 casas de chão alcançáveis da entrada");
    const decTypes = new Set(CAT.decorations.map(d => d.type));
    const decOcc = new Set();
    const wallDecOcc = new Set();
    for (const d of S.decorations) {
      if (!decTypes.has(d.type)) { e.push(`decoração tipo inválido: ${d.type}`); continue; }
      if (isWallDecor(d)) {
        const [wx, wy] = d.pos;
        const validFace = wallFacesAt(wx, wy).some(face => sameFace(face, d.facing));
        if (S.tiles[wy]?.[wx] !== WALL) e.push(`decoração de parede ${d.type} precisa estar em uma parede em ${wx},${wy}`);
        else if (!validFace) e.push(`decoração de parede ${d.type} precisa apontar para um chão adjacente em ${wx},${wy}`);
        const wallKey = `${wx},${wy}:${(d.facing || []).join(",")}`;
        if (wallDecOcc.has(wallKey)) e.push(`decorações sobrepostas na mesma face de parede em ${wx},${wy}`);
        wallDecOcc.add(wallKey);
        if (d.loot) for (const it of d.loot.items) if (!items.has(it.id)) e.push(`item de loot inválido: ${it.id}`);
        continue;
      }
      for (const [tx, ty] of decorTiles(d)) {
        if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h || S.tiles[ty]?.[tx] !== FLOOR)
          e.push(`decoração ${d.type} fora do chão em ${tx},${ty}`);
        const key = tx + "," + ty;
        if (decOcc.has(key)) e.push(`decorações sobrepostas em ${tx},${ty}`);
        decOcc.add(key);
      }
      if (d.loot) for (const it of d.loot.items) if (!items.has(it.id)) e.push(`item de loot inválido: ${it.id}`);
      if (d.chest_trap_monster_type && !types.has(d.chest_trap_monster_type)) e.push("baú-armadilha com monstro inválido");
    }
    const decorIds = new Set(S.decorations.map(d => d.id));
    const passageIds = new Set();
    for (const p of S.secretPassages) {
      if (!p.id || passageIds.has(p.id)) e.push("id de passagem secreta duplicado ou vazio");
      passageIds.add(p.id);
      if (!p.pos || S.tiles[p.pos[1]]?.[p.pos[0]] !== WALL) e.push("passagem secreta deve ficar em uma parede");
      if (!Array.isArray(p.key_decor_ids) || p.key_decor_ids.some(id => !decorIds.has(id))) e.push("passagem com decoração-chave inválida");
      if (p.type === "mechanism" && !p.key_decor_ids.length) e.push("passagem secreta sem decoração-chave");
    }
    const matIds = new Set(MAT.map(m => m.id));
    for (const [key, mid] of Object.entries(S.materiais)) {
      if (!matIds.has(mid)) { e.push(`material inválido: ${mid}`); continue; }
      const p = key.split(",").map(Number);
      const t = S.tiles[p[1]]?.[p[0]];
      const cat = matMeta(mid).categoria;
      if (cat === "parede" && t !== WALL) e.push(`material de parede ${mid} fora de parede em ${key}`);
      if (cat === "piso" && !(t === FLOOR || t === DOOR)) e.push(`material de piso ${mid} fora de chão em ${key}`);
    }
    return { ok: e.length === 0, erros: e };
  }

  function updateStatus() {
    const v = validarEditor();
    const el = document.getElementById("status");
    if (v.ok) { el.className = "status-ok"; el.textContent = "✓ válida — pronta para salvar"; }
    else { el.className = "status-err"; el.textContent = "✗ " + v.erros.length + " problema(s): " + v.erros.slice(0, 4).join("; ") + (v.erros.length > 4 ? " …" : ""); }
    return v;
  }

  function loadJSON(obj) {
    S.meta = { schema_version: 1, id: obj.id || "masmorra", name: obj.name || "Masmorra",
               ambiente: ["penumbra", "masmorra", "ar_livre"].includes(obj.ambiente) ? obj.ambiente : "masmorra" };
    S.grid = { w: obj.grid.w, h: obj.grid.h };
    S.tiles = obj.tiles.map(row => row.slice());
    S.rooms = (obj.rooms || []).map(r => ({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: !!r.locked, doors: (r.doors || []).map(d => d.slice()) }));
    S.nextRoomId = S.rooms.reduce((m, r) => Math.max(m, r.id + 1), 0);
    S.entrance = obj.entrance || null;
    S.exit = obj.exit || null;
    S.prisoner = obj.prisoner || null;
    S.monsters = (obj.monsters || []).map(m => ({ type: m.type, pos: m.pos.slice(), room_id: m.room_id ?? null, boss: !!m.boss, target: !!m.target }));
    S.chests = (obj.chests || []).map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: (c.items || []).map(i => ({ id: i.id })), key_objective: !!c.key_objective }));
    S.traps = (obj.traps || []).map(t => { const o = { tipo: t.tipo, pos: t.pos.slice() }; if (t.veneno_id) o.veneno_id = t.veneno_id; if (t.saida) o.saida = t.saida.slice(); if (t.image) o.image = t.image; return o; });
    S.decorations = (obj.decorations || []).map((d, i) => ({
      id: d.id || ("decor_" + i),
      type: d.type, pos: d.pos.slice(), facing: (d.facing || [0, 1]).slice(),
      loot: d.loot ? { gold: d.loot.gold | 0, items: (d.loot.items || []).map(i => ({ id: i.id })) } : null,
      key_objective: !!d.key_objective,
      ...(d.chest_trap_monster_type ? { chest_trap_monster_type: d.chest_trap_monster_type } : {}),
      ...(d.charges !== undefined ? { charges: d.charges | 0 } : {}),
      // Decorações catalogadas de parede sempre recuperam sua arte padrão,
      // inclusive em arquivos antigos que ainda não guardavam `image`.
      ...((d.image || decorMeta(d.type)?.image) ? { image: d.image || decorMeta(d.type).image } : {}),
      ...(Array.isArray(d.size) && d.size.length === 2 ? { size: [d.size[0] | 0, d.size[1] | 0] } : {}),
      ...(Array.isArray(d.vscale) && d.vscale.length === 2 ? { vscale: [Number(d.vscale[0]), Number(d.vscale[1])] } : {}),
    }));
    S.nextDecorId = S.decorations.length;
    S.secretPassages = (obj.secret_passages || []).map((p, i) => ({ id: p.id || ("passage_" + i), type: p.type === "illusion" ? "illusion" : "mechanism", pos: p.pos.slice(), key_decor_ids: (p.key_decor_ids || []).slice(), keys_mode: p.keys_mode === "all" ? "all" : "any" }));
    S.nextPassageId = S.secretPassages.length;
    S.masterReinforcements = (obj.master_reinforcements || [])
      .filter(r => r && r.type)
      .map(r => ({ type: r.type, count: Math.max(1, parseInt(r.count, 10) || 1) }));
    S.expectedParty = (function (ep) {
      ep = ep || {};
      return { heroes: Math.max(1, Math.min(6, parseInt(ep.heroes, 10) || 4)),
               level:  Math.max(1, parseInt(ep.level, 10) || 1) };
    })(obj.expected_party);
    S.materiais = (obj.materiais && typeof obj.materiais === "object") ? { ...obj.materiais } : {};
    S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };
    if (!S.objectives.primary) S.objectives.primary = { type: "kill_all" };
    if (!Array.isArray(S.objectives.secondary)) S.objectives.secondary = [];
    normalizeObjective(S.objectives.primary, true);
    S.objectives.secondary.forEach(s => normalizeObjective(s, false));
    S.sel = null;
    document.getElementById("m-id").value = S.meta.id;
    document.getElementById("m-name").value = S.meta.name;
    document.getElementById("m-ambiente").value = S.meta.ambiente || "masmorra";
    document.getElementById("g-w").value = S.grid.w;
    document.getElementById("g-h").value = S.grid.h;
    render(); renderPanel();
  }

  function setSaveMsg(cls, msg) {
    const el = document.getElementById("status");
    if (el) { el.className = cls; el.textContent = msg; }
  }

  function baixarMasmorra(defn) {
    const blob = new Blob([JSON.stringify(defn, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = S.meta.id + ".json";
    document.body.appendChild(a); a.click(); a.remove();
  }

  // Injeta/atualiza a masmorra no catálogo em memória para que a aba de campanha
  // a enxergue imediatamente (mutação in-place: editor_campaign.js guarda a mesma
  // referência do array). NÃO reatribuir window.EDITOR_DUNGEONS.
  function injetarNoCatalogo(entry) {
    const arr = window.EDITOR_DUNGEONS;
    if (!Array.isArray(arr) || !entry) return;
    const i = arr.findIndex(d => d.file === entry.file);
    if (i >= 0) arr[i] = entry; else arr.push(entry);
  }

  function save() {
    S.meta.id = document.getElementById("m-id").value.trim() || "masmorra";
    S.meta.name = document.getElementById("m-name").value.trim() || "Masmorra";
    S.meta.ambiente = document.getElementById("m-ambiente").value || "masmorra";
    const v = updateStatus();
    if (!v.ok) { alert("Masmorra inválida:\n- " + v.erros.join("\n- ")); return; }
    const defn = buildJSON();
    if (window.EDITOR_SAVE && window.EDITOR_SAVE.saveDungeon) {
      setSaveMsg("status-ok", "Salvando em dungeons/…");
      window.EDITOR_SAVE.saveDungeon(defn).then((res) => {
        injetarNoCatalogo(res.entry);
        setSaveMsg("status-ok", "✓ salva em dungeons/" + res.file + " — disponível na aba Campanha");
      }).catch((err) => {
        baixarMasmorra(defn);
        setSaveMsg("status-err", "⚠ servidor offline (" + err.message + ") — baixada em Downloads");
      });
    } else {
      baixarMasmorra(defn);
    }
  }

  document.getElementById("btn-save").onclick = save;
  document.getElementById("btn-load").onclick = () => document.getElementById("file-input").click();
  document.getElementById("file-input").onchange = (ev) => {
    const f = ev.target.files[0]; if (!f) return;
    const fr = new FileReader();
    fr.onload = () => { try { loadJSON(JSON.parse(fr.result)); } catch (e) { alert("JSON inválido: " + e.message); } };
    fr.readAsText(f); ev.target.value = "";
  };
  document.getElementById("btn-resize").onclick = () => {
    const w = Math.max(1, Math.min(60, Number(document.getElementById("g-w").value) | 0));
    const h = Math.max(1, Math.min(60, Number(document.getElementById("g-h").value) | 0));
    const old = S.tiles, ow = S.grid.w, oh = S.grid.h;
    initGrid(w, h);
    for (let y = 0; y < Math.min(h, oh); y++) for (let x = 0; x < Math.min(w, ow); x++) S.tiles[y][x] = old[y][x];
    render();
  };

  function setTab(tab) {
    const dung = tab === "masmorra";
    const bestiary = tab === "bestiario";
    const monsterEditor = tab === "editor_monstros";
    document.getElementById("dungeon-controls").style.display = dung ? "" : "none";
    document.getElementById("toolbar").style.display = dung ? "" : "none";
    document.getElementById("workspace").style.display = dung ? "" : "none";
    document.getElementById("campaign-controls").style.display = tab === "campanha" ? "" : "none";
    document.getElementById("campaign-view").style.display = tab === "campanha" ? "" : "none";
    document.getElementById("bestiary-view").style.display = bestiary ? "" : "none";
    document.getElementById("monster-editor-view").style.display = monsterEditor ? "" : "none";
    document.getElementById("tab-masmorra").classList.toggle("active", dung);
    document.getElementById("tab-bestiario").classList.toggle("active", bestiary);
    document.getElementById("tab-editor-monstros").classList.toggle("active", monsterEditor);
    document.getElementById("tab-campanha").classList.toggle("active", tab === "campanha");
    if (dung) { render(); renderPanel(); }
    else if (bestiary && window.EDITOR_BESTIARY) window.EDITOR_BESTIARY.render();
    else if (monsterEditor && window.EDITOR_MONSTER_EDITOR) window.EDITOR_MONSTER_EDITOR.render();
    else if (tab === "campanha" && window.EDITOR_CAMPAIGN) window.EDITOR_CAMPAIGN.renderCampaign();
  }
  window.setTab = setTab;
  document.getElementById("tab-masmorra").onclick = () => setTab("masmorra");
  document.getElementById("tab-bestiario").onclick = () => setTab("bestiario");
  document.getElementById("tab-editor-monstros").onclick = () => setTab("editor_monstros");
  document.getElementById("tab-campanha").onclick = () => setTab("campanha");

  // Expor para verificação no console / tasks seguintes.
  window.EDITOR = { S, catalog: CAT, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, deleteRoom, entityAt, doorLink, doorUnlink, validarEditor, buildJSON, loadJSON, save, updateStatus, WALL, FLOOR, DOOR, decorMeta, decorEffSize, decorTilesAt, decorTiles, rotateFacing, rotateDecorPending, decorFits, placeDecor, decorBaseSize, decorEffSizeOf, decorWouldFit, tilesFor, dropValid, moveSelTo, copySelectedDecor, pasteDecorAt, duplicateDecorAdjacent };

  initGrid(S.grid.w, S.grid.h);
  buildToolbar();
  render();
  renderPanel();
})();
