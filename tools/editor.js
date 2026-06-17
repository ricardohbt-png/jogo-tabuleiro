"use strict";
(function () {
  const WALL = 0, FLOOR = 1, DOOR = 2, CELL = 28;
  const CAT = window.EDITOR_CATALOG || { monsters: [], items: [], traps: [], venoms: [] };

  const S = {
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra" },
    grid: { w: 16, h: 12 },
    tiles: [],
    rooms: [], nextRoomId: 0,
    entrance: null, exit: null, prisoner: null,
    monsters: [], chests: [], traps: [],
    objectives: { primary: { type: "kill_all" }, secondary: [] },
    tool: "wall", sel: null,
  };

  function initGrid(w, h) {
    S.grid = { w, h };
    S.tiles = [];
    for (let y = 0; y < h; y++) S.tiles.push(new Array(w).fill(WALL));
  }

  const board = document.getElementById("board");
  const ctx = board.getContext("2d");

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
  }

  // Expor para verificação no console / tasks seguintes.
  window.EDITOR = { S, initGrid, render, buildToolbar, WALL, FLOOR, DOOR };

  initGrid(S.grid.w, S.grid.h);
  buildToolbar();
  render();
})();
