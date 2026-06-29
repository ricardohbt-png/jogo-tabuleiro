"use strict";
(function () {
  const WALL = 0, FLOOR = 1, DOOR = 2, CELL = 28;
  const CAT = window.EDITOR_CATALOG || { monsters: [], items: [], traps: [], venoms: [], decorations: [] };

  const S = {
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra" },
    grid: { w: 16, h: 12 },
    tiles: [],
    rooms: [], nextRoomId: 0,
    entrance: null, exit: null, prisoner: null,
    monsters: [], chests: [], traps: [], decorations: [],
    objectives: { primary: { type: "kill_all" }, secondary: [] },
    tool: "wall", sel: null,
    decorType: (CAT.decorations[0] || {}).type || "cama",
    decorFacing: [0, 1],
  };

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
  function decorTiles(d) { return decorTilesAt(d.type, d.pos[0], d.pos[1], d.facing); }

  function rotateFacing(f) {
    // cicla 4 facings: [0,1]→[1,0]→[0,-1]→[-1,0]→[0,1]
    const order = [[0, 1], [1, 0], [0, -1], [-1, 0]];
    const i = order.findIndex(o => o[0] === f[0] && o[1] === f[1]);
    return order[(i + 1) % 4];
  }
  function rotateDecorPending() {
    if (S.sel && S.sel.kind === "decor") {
      const m = decorMeta(S.sel.ref.type);
      if (m && m.gira) { S.sel.ref.facing = rotateFacing(S.sel.ref.facing); render(); }
    } else {
      const m = decorMeta(S.decorType);
      if (m && m.gira) S.decorFacing = rotateFacing(S.decorFacing);
    }
  }
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "r" || ev.key === "R") rotateDecorPending();
  });

  function decorFits(type, ax, ay, facing, ignore) {
    for (const [tx, ty] of decorTilesAt(type, ax, ay, facing)) {
      if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h) return false;
      if (S.tiles[ty][tx] !== FLOOR) return false;
      for (const d of S.decorations) {
        if (d === ignore) continue;
        if (decorTiles(d).some(c => c[0] === tx && c[1] === ty)) return false;
      }
    }
    return true;
  }
  function placeDecor(x, y) {
    if (!decorFits(S.decorType, x, y, S.decorFacing)) return;
    const m = decorMeta(S.decorType);
    const d = { type: S.decorType, pos: [x, y], facing: S.decorFacing.slice(),
                loot: (m && m.loot_capaz && S.decorType === "arca_tesouros") ? { gold: 0, items: [] } : null };
    if (m && m.special === "fountain") d.charges = 3;
    S.decorations.push(d);
    S.sel = { kind: "decor", ref: d, pos: [x, y] };
  }

  const board = document.getElementById("board");
  const ctx = board.getContext("2d");

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

  function emojiForCell(x, y) {
    const at = (arr) => arr.find(e => e.pos && e.pos[0] === x && e.pos[1] === y);
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return "🚪";
    if (S.exit && S.exit.x === x && S.exit.y === y) return "🏁";
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return "🧍";
    const mo = at(S.monsters);
    if (mo) { const d = CAT.monsters.find(c => c.type === mo.type); return d ? d.emoji : "👹"; }
    if (at(S.chests)) return "🧰";
    const tr = at(S.traps);
    if (tr) { const d = CAT.traps.find(c => c.tipo === tr.tipo); return d ? d.icone : "⚠️"; }
    const dec = S.decorations.find(e => e.pos[0] === x && e.pos[1] === y);
    if (dec) {
      // Se a decoração tem imagem e ela já carregou, não retorna emoji (a imagem cobre o footprint).
      if (dec.image && objImg(dec.image)) return null;
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
        ctx.fillStyle = t === WALL ? "#1d1812" : (t === DOOR ? "#c8841f" : "#5a4a32");
        ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
      }
    }
    for (const r of S.rooms) {
      ctx.strokeStyle = r.locked ? "#e0683c" : "#8fb0e0";
      ctx.lineWidth = 2;
      ctx.strokeRect(r.x * CELL + 1, r.y * CELL + 1, r.w * CELL - 2, r.h * CELL - 2);
      ctx.fillStyle = "#9fb8d8"; ctx.font = "10px sans-serif"; ctx.textBaseline = "top";
      ctx.fillText((r.locked ? "🔒" : "") + r.role + "#" + r.id, r.x * CELL + 3, r.y * CELL + 3);
    }
    for (const d of S.decorations) {
      ctx.strokeStyle = "#6ad0a0"; ctx.lineWidth = 1;
      for (const [tx, ty] of decorTiles(d)) ctx.strokeRect(tx * CELL + 2, ty * CELL + 2, CELL - 5, CELL - 5);
    }
    // Preview 2D: desenha o PNG da decoração cobrindo o footprint (se d.image disponível).
    for (const d of S.decorations) {
      if (!d.image) continue;
      const im = objImg(d.image);
      if (!im) continue;
      const tiles = decorTiles(d);
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      const px = minX * CELL + 2, py = minY * CELL + 2;
      const pw = (maxX - minX + 1) * CELL - 4, ph = (maxY - minY + 1) * CELL - 4;
      ctx.drawImage(im, px, py, pw, ph);
    }
    ctx.font = "16px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    for (let y = 0; y < S.grid.h; y++) {
      for (let x = 0; x < S.grid.w; x++) {
        const e = emojiForCell(x, y);
        if (e) ctx.fillText(e, x * CELL + CELL / 2, y * CELL + CELL / 2);
      }
    }
    ctx.textAlign = "start";
    if (S.sel && S.sel.pos) {
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 2;
      ctx.strokeRect(S.sel.pos[0] * CELL + 1, S.sel.pos[1] * CELL + 1, CELL - 3, CELL - 3);
    }
    if (document.getElementById("status")) updateStatus();
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
      sel.innerHTML = CAT.decorations.map(d =>
        `<option value="${d.type}"${d.type === S.decorType ? " selected" : ""}>${d.emoji} ${d.nome}</option>`).join("");
      sel.onchange = e => { S.decorType = e.target.value; S.decorFacing = [0, 1]; };
      tb.appendChild(sel);
      const rot = document.createElement("button");
      rot.textContent = "girar 90° (R)";
      rot.onclick = () => { rotateDecorPending(); };
      tb.appendChild(rot);
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
    if (S.tool === "wall") S.tiles[y][x] = WALL;
    else if (S.tool === "floor") S.tiles[y][x] = FLOOR;
    else if (S.tool === "door") { S.tiles[y][x] = DOOR; doorLink(x, y); }
  }

  let painting = false;
  let roomDrag = null;
  function entityAt(x, y) {
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return { kind: "entrance", pos: [x, y] };
    if (S.exit && S.exit.x === x && S.exit.y === y) return { kind: "exit", pos: [x, y] };
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return { kind: "prisoner", ref: S.prisoner, pos: [x, y] };
    const find = (arr, kind) => { const r = arr.find(e => e.pos[0] === x && e.pos[1] === y); return r ? { kind, ref: r, pos: [x, y] } : null; };
    const dec = S.decorations.find(d => decorTiles(d).some(c => c[0] === x && c[1] === y));
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
        <button id="o-add">+ secundário</button>`;
      document.getElementById("o-prim").onchange = e => { o.primary.type = e.target.value; };
      wireRewardFields(o.primary, "o-prim-rw");
      document.getElementById("o-add").onclick = () => { o.secondary.push({ type: "rescue_prisoner", ...objDefaults(false) }); renderPanel(); };
      panel.querySelectorAll(".o-secsel").forEach(sel => sel.onchange = e => { o.secondary[Number(e.target.dataset.i)].type = e.target.value; });
      panel.querySelectorAll(".o-rm").forEach(b => b.onclick = () => { o.secondary.splice(Number(b.dataset.i), 1); renderPanel(); });
      o.secondary.forEach((s, i) => wireRewardFields(s, "o-sec" + i + "-rw"));
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
        ${meta.precisa_veneno ? `<label>veneno</label><select id="p-ven">${opt(CAT.venoms.map(v => ({ v: v.id, name: v.name })), ref.veneno_id || "", o => o.v + " — " + o.name)}</select>` : ""}`;
      document.getElementById("p-tt").onchange = e => { ref.tipo = e.target.value; if (!CAT.traps.find(t => t.tipo === ref.tipo).precisa_veneno) delete ref.veneno_id; renderPanel(); render(); };
      if (meta.precisa_veneno) document.getElementById("p-ven").onchange = e => { ref.veneno_id = e.target.value; };
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
    } else if (k === "decor") {
      const m = decorMeta(ref.type) || {};
      const hasLoot = !!ref.loot;
      panel.innerHTML = `<b>${m.emoji || "🪑"} ${m.nome || ref.type}</b>
        <div style="color:#8a7a5a;font-size:11px">${m.size ? m.size[0] + "×" + m.size[1] : ""} ${m.alto ? "· alto (oclui visão)" : ""} ${m.pisavel ? "· pisável" : ""}</div>
        ${m.gira ? `<button id="d-rot">girar 90°</button>` : ""}
        ${m.special === "fountain" ? `<label>cargas <input id="d-charges" type="number" min="0" value="${ref.charges ?? 0}"></label>` : ""}
        ${m.loot_capaz ? `<label style="display:block;margin-top:8px"><input type="checkbox" id="d-haslook" ${hasLoot ? "checked" : ""}> contém loot</label>` : ""}
        <div id="d-loot" style="${hasLoot ? "" : "display:none"}">
          <label>ouro <input id="d-gold" type="number" min="0" value="${hasLoot ? (ref.loot.gold | 0) : 0}"></label>
          <label>itens</label>
          <div id="d-items">${hasLoot ? ref.loot.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="d-rm">×</button></div>`).join("") : ""}</div>
          <select id="d-add">${opt(CAT.items.map(it => ({ v: it.id, name: it.name })), "", o => o.v + " — " + o.name)}</select>
          <button id="d-additem">+ item</button>
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
      if (m.gira) document.getElementById("d-rot").onclick = () => { ref.facing = rotateFacing(ref.facing); render(); };
      if (m.special === "fountain") document.getElementById("d-charges").onchange = e => { ref.charges = Math.max(0, Number(e.target.value) | 0); };
      if (m.loot_capaz) document.getElementById("d-haslook").onchange = e => {
        ref.loot = e.target.checked ? { gold: 0, items: [] } : null; renderPanel();
      };
      if (hasLoot) {
        document.getElementById("d-gold").onchange = e => { ref.loot.gold = Math.max(0, Number(e.target.value) | 0); };
        document.getElementById("d-additem").onclick = () => { const id = document.getElementById("d-add").value; if (id) ref.loot.items.push({ id }); renderPanel(); };
        panel.querySelectorAll(".d-rm").forEach(b => b.onclick = () => { ref.loot.items.splice(Number(b.dataset.i), 1); renderPanel(); });
      }
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
    const c = cellFromEvent(ev); if (!c) return;
    const [x, y] = c;
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; paintTile(x, y); render(); }
    else if (S.tool === "room") { roomDrag = { x0: x, y0: y, x1: x, y1: y }; }
    else if (["entrance", "exit", "prisoner", "monster", "chest", "trap", "decor"].includes(S.tool)) { placeEntity(x, y); if (S.tool !== "decor") S.sel = entityAt(x, y); renderPanel(); render(); }
    else if (S.tool === "erase") { eraseAt(x, y); S.sel = null; renderPanel(); render(); }
    else if (S.tool === "select") { S.sel = entityAt(x, y) || roomSel(x, y); renderPanel(); render(); }
  });

  function roomSel(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? { kind: "room", ref: r } : null;
  }
  board.addEventListener("mousemove", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    if (painting) { paintTile(c[0], c[1]); render(); return; }
    if (roomDrag) {
      roomDrag.x1 = c[0]; roomDrag.y1 = c[1];
      render();
      const x = Math.min(roomDrag.x0, roomDrag.x1), y = Math.min(roomDrag.y0, roomDrag.y1);
      const w = Math.abs(roomDrag.x1 - roomDrag.x0) + 1, h = Math.abs(roomDrag.y1 - roomDrag.y0) + 1;
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 1;
      ctx.strokeRect(x * CELL + 1, y * CELL + 1, w * CELL - 2, h * CELL - 2);
    }
  });
  window.addEventListener("mouseup", () => {
    painting = false;
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
      schema_version: 1, id: S.meta.id, name: S.meta.name,
      grid: { w: S.grid.w, h: S.grid.h },
      tiles: S.tiles.map(row => row.slice()),
      rooms: S.rooms.map(r => ({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: r.locked, doors: r.doors.map(d => d.slice()) })),
      entrance: S.entrance ? { x: S.entrance.x, y: S.entrance.y } : null,
      exit: S.exit ? { x: S.exit.x, y: S.exit.y } : null,
      monsters: S.monsters.map(m => ({ type: m.type, pos: m.pos.slice(), room_id: m.room_id, boss: !!m.boss, target: !!m.target })),
      chests: S.chests.map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: c.items.map(i => ({ id: i.id })), key_objective: !!c.key_objective })),
      traps: S.traps.map(t => { const o = { tipo: t.tipo, pos: t.pos.slice() }; if (t.veneno_id) o.veneno_id = t.veneno_id; return o; }),
      decorations: S.decorations.map(d => {
        const o = { type: d.type, pos: d.pos.slice(), facing: d.facing.slice() };
        o.loot = d.loot ? { gold: d.loot.gold | 0, items: d.loot.items.map(i => ({ id: i.id })) } : null;
        const m = decorMeta(d.type);
        if (m && m.special === "fountain") o.charges = d.charges | 0;
        if (d.image) o.image = d.image;
        return o;
      }),
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id, ...(S.prisoner.image ? { image: S.prisoner.image } : {}) } : null,
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
      if (t.tipo === "fosso_envenenado" && !venoms.has(t.veneno_id)) e.push("fosso_envenenado sem veneno válido");
    }
    if (S.prisoner && isWall(S.prisoner.pos)) e.push("prisioneiro em parede");
    for (const r of S.rooms) for (const d of r.doors) if (S.tiles[d[1]]?.[d[0]] !== DOOR) e.push(`porta declarada não é tile DOOR: ${d}`);
    if (reachableFloors(6) < 6) e.push("menos de 6 casas de chão alcançáveis da entrada");
    const decTypes = new Set(CAT.decorations.map(d => d.type));
    const decOcc = new Set();
    for (const d of S.decorations) {
      if (!decTypes.has(d.type)) { e.push(`decoração tipo inválido: ${d.type}`); continue; }
      for (const [tx, ty] of decorTiles(d)) {
        if (tx < 0 || ty < 0 || tx >= S.grid.w || ty >= S.grid.h || S.tiles[ty]?.[tx] !== FLOOR)
          e.push(`decoração ${d.type} fora do chão em ${tx},${ty}`);
        const key = tx + "," + ty;
        if (decOcc.has(key)) e.push(`decorações sobrepostas em ${tx},${ty}`);
        decOcc.add(key);
      }
      if (d.loot) for (const it of d.loot.items) if (!items.has(it.id)) e.push(`item de loot inválido: ${it.id}`);
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
    S.meta = { schema_version: 1, id: obj.id || "masmorra", name: obj.name || "Masmorra" };
    S.grid = { w: obj.grid.w, h: obj.grid.h };
    S.tiles = obj.tiles.map(row => row.slice());
    S.rooms = (obj.rooms || []).map(r => ({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: !!r.locked, doors: (r.doors || []).map(d => d.slice()) }));
    S.nextRoomId = S.rooms.reduce((m, r) => Math.max(m, r.id + 1), 0);
    S.entrance = obj.entrance || null;
    S.exit = obj.exit || null;
    S.prisoner = obj.prisoner || null;
    S.monsters = (obj.monsters || []).map(m => ({ type: m.type, pos: m.pos.slice(), room_id: m.room_id ?? null, boss: !!m.boss, target: !!m.target }));
    S.chests = (obj.chests || []).map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: (c.items || []).map(i => ({ id: i.id })), key_objective: !!c.key_objective }));
    S.traps = (obj.traps || []).map(t => { const o = { tipo: t.tipo, pos: t.pos.slice() }; if (t.veneno_id) o.veneno_id = t.veneno_id; return o; });
    S.decorations = (obj.decorations || []).map(d => ({
      type: d.type, pos: d.pos.slice(), facing: (d.facing || [0, 1]).slice(),
      loot: d.loot ? { gold: d.loot.gold | 0, items: (d.loot.items || []).map(i => ({ id: i.id })) } : null,
      ...(d.charges !== undefined ? { charges: d.charges | 0 } : {}),
      ...(d.image ? { image: d.image } : {}),
    }));
    S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };
    if (!S.objectives.primary) S.objectives.primary = { type: "kill_all" };
    if (!Array.isArray(S.objectives.secondary)) S.objectives.secondary = [];
    normalizeObjective(S.objectives.primary, true);
    S.objectives.secondary.forEach(s => normalizeObjective(s, false));
    S.sel = null;
    document.getElementById("m-id").value = S.meta.id;
    document.getElementById("m-name").value = S.meta.name;
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
    const dung = tab !== "campanha";
    document.getElementById("dungeon-controls").style.display = dung ? "" : "none";
    document.getElementById("toolbar").style.display = dung ? "" : "none";
    document.getElementById("workspace").style.display = dung ? "" : "none";
    document.getElementById("campaign-controls").style.display = dung ? "none" : "";
    document.getElementById("campaign-view").style.display = dung ? "none" : "";
    document.getElementById("tab-masmorra").classList.toggle("active", dung);
    document.getElementById("tab-campanha").classList.toggle("active", !dung);
    if (dung) { render(); renderPanel(); }
    else if (window.EDITOR_CAMPAIGN) window.EDITOR_CAMPAIGN.renderCampaign();
  }
  window.setTab = setTab;
  document.getElementById("tab-masmorra").onclick = () => setTab("masmorra");
  document.getElementById("tab-campanha").onclick = () => setTab("campanha");

  // Expor para verificação no console / tasks seguintes.
  window.EDITOR = { S, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, deleteRoom, entityAt, doorLink, doorUnlink, validarEditor, buildJSON, loadJSON, save, updateStatus, WALL, FLOOR, DOOR, decorMeta, decorEffSize, decorTilesAt, decorTiles, rotateFacing, rotateDecorPending, decorFits, placeDecor };

  initGrid(S.grid.w, S.grid.h);
  buildToolbar();
  render();
  renderPanel();
})();
