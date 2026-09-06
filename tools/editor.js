"use strict";
(function () {
  const WALL = 0, FLOOR = 1, DOOR = 2, CELL = 28;
  const ELEVACAO_MIN = -1, ELEVACAO_MAX = 2;
  const BASE_CAT = window.EDITOR_CATALOG || { monsters: [], items: [], traps: [], venoms: [], curses: [], decorations: [], materiais: [] };
  // Itens customizados (arma/armadura/escudo/…) marcados disponibilidade.baus=true
  // entram no seletor de baús/recompensas ao lado dos itens base. Forma mínima
  // genérica (id/name/emoji/item_type) — o seletor só usa id/name/emoji.
  const customBaus = (window.EDITOR_CUSTOM_ITEMS || [])
    .filter(function (i) { return i && i.disponibilidade && i.disponibilidade.baus; })
    .map(function (i) { return { id: i.id, name: i.name, emoji: i.emoji, item_type: i.item_type, custom: true }; });
  const CAT = Object.assign({}, BASE_CAT, {
    monsters: (BASE_CAT.monsters || []).concat(window.EDITOR_CUSTOM_MONSTERS || []),
    items: (BASE_CAT.items || []).concat(customBaus),
  });
  // Compatibilidade com uma cópia antiga do editor_catalog.js em cache: a
  // Fonte de parede continua aparecendo na lista mesmo antes de o navegador
  // recarregar o catálogo gerado pelo servidor.
  if (!(CAT.decorations || []).some(d => d && d.type === "fonte_de_parede")) {
    CAT.decorations = (CAT.decorations || []).concat({
      type: "fonte_de_parede", nome: "Fonte de parede", emoji: "⛲",
      size: [1, 1], gira: true, alto: true, pisavel: false,
      loot_capaz: false, special: null, image: "fonte_de_parede.png",
    });
  }
  if (!(CAT.decorations || []).some(d => d && d.type === "armadura")) {
    CAT.decorations = (CAT.decorations || []).concat({
      type: "armadura", nome: "Armadura", emoji: "🛡️",
      size: [1, 1], gira: true, alto: true, pisavel: false,
      loot_capaz: false, special: null, image: "armadura.png",
    });
  }
  // Compatibilidade com uma cópia antiga do catálogo: a Chama Viva precisa
  // continuar disponível nas decorações de chão mesmo antes do recarregamento.
  if (!(CAT.decorations || []).some(d => d && d.type === "chama_viva")) {
    CAT.decorations = (CAT.decorations || []).concat({
      type: "chama_viva", nome: "Chama viva", emoji: "🔥",
      size: [1, 1], gira: false, alto: false, pisavel: true,
      loot_capaz: false, special: "living_flame", image: null,
    });
  }
  const MAT = (CAT.materiais || []);
  const matMeta = (id) => MAT.find(m => m.id === id) || null;
  const WALL_MATERIALS = MAT.filter(m => m && m.categoria === "parede");
  const WALL_MATERIAL_IDS = new Set(WALL_MATERIALS.map(m => m.id));
  function secretPassageAt(x, y) {
    return S.secretPassages.find(p => p.pos[0] === x && p.pos[1] === y) || null;
  }
  function wallMaterialAt(x, y) {
    const passage = secretPassageAt(x, y);
    return (passage && WALL_MATERIAL_IDS.has(passage.wall_material))
      ? passage.wall_material : S.materiais[x + "," + y];
  }
  // Default por categoria: pintar o default limpa a casa (mantém JSON esparso e
  // serve de borracha de material). Espelha MATERIAIS_*_DEFAULT do servidor.
  const MAT_DEFAULT = { piso: "pedra_cinza", parede: "pedra_normal" };
  const HERO_SPAWN_META = [
    { id: "warrior", name: "Guerreiro", emoji: "⚔️", mark: "G" },
    { id: "mage", name: "Mago", emoji: "🔮", mark: "M" },
    { id: "rogue", name: "Ladino", emoji: "🗡️", mark: "L" },
    { id: "cleric", name: "Clérigo", emoji: "✚", mark: "C" },
    { id: "bard", name: "Bardo", emoji: "🎻", mark: "B" },
    { id: "paladin", name: "Paladino", emoji: "🛡️", mark: "P" },
  ];
  // Tutorial: verbos que uma tarefa de lição pode cobrar. Espelha
  // LICAO_VERBOS no server.py — mudar um exige mudar o outro.
  const LICAO_VERBOS = [
    { v: "mover_ate", nome: "chegar a uma casa" },
    { v: "abrir_porta", nome: "abrir uma porta" },
    { v: "atacar", nome: "acertar um ataque" },
    { v: "matar", nome: "derrotar um monstro" },
    { v: "pegar_item", nome: "pegar um item" },
    { v: "equipar", nome: "equipar um item" },
    { v: "encerrar_turno", nome: "encerrar o turno" },
    { v: "usar_item", nome: "usar um item (comer, beber, poção)" },
    { v: "usar_magia", nome: "lançar uma magia" },
    { v: "usar_habilidade", nome: "usar uma habilidade de classe" },
    { v: "usar_tecnica", nome: "usar uma técnica da Guilda" },
    { v: "usar_instrumento", nome: "tocar o instrumento (bardo)" },
    { v: "arremessar_item", nome: "arremessar um item (óleo, bomba)" },
    { v: "desarmar_armadilha", nome: "desarmar uma armadilha" },
  ];
  const LICAO_VERBOS_CASA = new Set(["mover_ate", "abrir_porta"]);
  const heroSpawnMeta = (id) => HERO_SPAWN_META.find(h => h.id === id) || { name: id, emoji: "⚔️", mark: "H" };

  const S = {
    meta: { schema_version: 1, id: "nova_masmorra", name: "Nova Masmorra", ambiente: "masmorra", saida_permitida: true },
    grid: { w: 16, h: 12 },
    tiles: [],
    rooms: [], nextRoomId: 0,
    startMode: "entrance", entrance: null, heroSpawns: [], exit: null, prisoner: null,
    heroSpawnClass: "warrior",
    monsters: [], chests: [], traps: [], decorations: [], secretPassages: [], doorConditions: {}, falas: [], nextDecorId: 0, nextPassageId: 0, nextFalaId: 0,
    masterReinforcements: [],
    expectedParty: { heroes: 4, level: 1 },
    objectives: { primary: { type: "kill_all" }, secondary: [] },
    tool: "wall", sel: null,
    trapType: ((CAT.traps.find(t => !t.apenas_objeto) || CAT.traps[0]) || {}).tipo || "fosso_estacas",
    teleportExitPick: null,      // referência da armadilha aguardando clique no mapa
    decorType: (CAT.decorations[0] || {}).type || "cama",
    decorFacing: [0, 1],
    materiais: {},                 // {"x,y": id}
    elevacoes: {},                 // {"x,y": nível visual (-1..2)}
    transicaoAltura: "rampa",      // transição visual entre níveis diferentes
    elevacaoValor: 1,              // nível aplicado pela ferramenta de altura
    doorRotations: {},              // {"x,y": giros de 90° relativos à orientação da parede}
    matFloor: "pedra_cinza",       // material atual da ferramenta "chão"
    matWall: "pedra_normal",       // material atual da ferramenta "parede"
    matFill: false,                // false = pincel; true = balde (preenchimento)
  };
  // Área de transferência exclusiva de objetos decorativos. Guarda uma cópia
  // profunda para que loot, escala, imagem e demais ajustes nunca sejam
  // compartilhados acidentalmente com o objeto de origem.
  let decorClipboard = null;
  // O pincel só é ativado explicitamente: copiar (Ctrl+C) continua servindo
  // para colar uma peça isolada sem transformar todo clique em preenchimento.
  let decorBrushActive = false;
  let decorAreaPaint = null;
  let lastPointerCell = null;

  function initGrid(w, h) {
    S.grid = { w, h };
    S.tiles = [];
    S.doorRotations = {};
    S.elevacoes = {};
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
  function monsterMeta(monsterOrType) {
    const type = typeof monsterOrType === "string" ? monsterOrType : monsterOrType && monsterOrType.type;
    return CAT.monsters.find(m => m.type === type) || null;
  }
  function monsterFlightMeta(monsterOrType) {
    const meta = monsterMeta(monsterOrType);
    return meta && (meta.voo || (meta.special_abilities || []).some(a => a && a.id === "voo")) ? meta : null;
  }
  function monsterCanFly(monsterOrType) {
    const meta = monsterFlightMeta(monsterOrType);
    return !!(meta || (monsterOrType && typeof monsterOrType !== "string" && monsterOrType.voo));
  }
  function altitudeClamp(value, fallback) {
    const n = Number(value);
    const base = Number.isFinite(n) ? Math.trunc(n) : fallback;
    return Math.max(0, Math.min(10, base));
  }
  function monsterSize(monster) {
    const meta = monsterMeta(monster);
    const raw = monster && Array.isArray(monster.size) ? monster.size : meta && meta.size;
    const w = Math.max(1, Math.min(4, Number(raw && raw[0]) || 1));
    const h = Math.max(1, Math.min(4, Number(raw && raw[1]) || 1));
    return [w, h];
  }
  function monsterOriented(monster) {
    const meta = monsterMeta(monster);
    return !!(monster && monster.oriented != null ? monster.oriented : meta && meta.oriented);
  }
  function monsterTiles(monster, pos) {
    const p = pos || (monster && monster.pos) || [0, 0];
    const size = monsterSize(monster);
    if (monsterOriented(monster)) {
      const f = monster.facing || [0, 1];
      const [w, h] = size;
      const [width, length] = h === 1 ? [1, w] : [w, h];
      const [px, py] = [-f[1], f[0]], out = [];
      // A âncora é a fileira frontal; o corpo cresce para trás, como no jogo.
      for (let depth = 0; depth < length; depth++) {
        for (let lane = 0; lane < width; lane++) {
          out.push([p[0] - f[0] * depth + px * lane,
                    p[1] - f[1] * depth + py * lane]);
        }
      }
      return out;
    }
    return tilesFor(p, size, null);
  }
  function monsterImageName(monster) {
    const meta = monsterMeta(monster);
    return (monster && monster.image) || (meta && meta.image) || (monster && monster.type) || "";
  }
  function decorTiles(d) {
    const [ew, eh] = decorEffSizeOf(d);
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([d.pos[0] + i, d.pos[1] + j]);
    return out;
  }

  function rotateFacing(f) {
    // A sequência acompanha facingAngle2D: cada passo equivale a ctx.rotate(+90°),
    // isto é, um giro visual HORÁRIO no canvas.
    const order = [[0, 1], [1, 0], [0, -1], [-1, 0]];
    const i = order.findIndex(o => o[0] === f[0] && o[1] === f[1]);
    return order[(i < 0 ? 0 : i + 1) % 4];
  }
  function doorKey(x, y) { return x + "," + y; }
  function doorRotationAt(x, y) {
    const n = Number(S.doorRotations[doorKey(x, y)]);
    return Number.isFinite(n) ? ((Math.round(n) % 4) + 4) % 4 : 0;
  }
  // Giro zero preserva o alinhamento automático existente. Assim, mapas
  // antigos continuam iguais e o editor só grava a diferença escolhida.
  function doorBaseAngle(x, y) {
    const isWall = (tx, ty) => ty < 0 || tx < 0 || ty >= S.grid.h || tx >= S.grid.w || S.tiles[ty][tx] === WALL;
    return isWall(x - 1, y) && isWall(x + 1, y) ? 0 : Math.PI / 2;
  }
  function doorFrontLabel(x, y) {
    const quarter = ((Math.round((doorBaseAngle(x, y) + doorRotationAt(x, y) * Math.PI / 2) / (Math.PI / 2)) % 4) + 4) % 4;
    return ["↑ norte", "→ leste", "↓ sul", "← oeste"][quarter];
  }
  function rotateDoorAt(x, y) {
    const k = doorKey(x, y);
    S.doorRotations[k] = (doorRotationAt(x, y) + 1) % 4;
    renderPanel(); render();
  }
  function rotateDoorSelected() {
    if (S.sel && S.sel.kind === "door" && S.sel.ref) rotateDoorAt(S.sel.ref.x, S.sel.ref.y);
  }
  // Para paredes, algumas faces não são válidas. Ainda assim, procura a próxima
  // face disponível seguindo a mesma ordem horária, nunca a ordem acidental da lista.
  function nextWallFaceClockwise(current, validFaces) {
    for (let turns = 1, face = rotateFacing(current); turns <= 4; turns++, face = rotateFacing(face)) {
      if (validFaces.some(f => sameFace(f, face))) return face;
    }
    return validFaces[0] || current;
  }
  // facing → ângulo (rad) p/ o giro 90° da imagem no preview 2D. Espelha game.js.
  function facingAngle2D(f, type, imageName) {
    let angle = 0;
    if (f && f[0] === 1 && f[1] === 0) angle = Math.PI / 2;
    else if (f && f[0] === 0 && f[1] === -1) angle = Math.PI;
    else if (f && f[0] === -1 && f[1] === 0) angle = -Math.PI / 2;
    // Estes modelos foram exportados com a frente no eixo oposto ao facing
    // padrão do editor. Corrige a arte e o marcador sem alterar o facing salvo.
    if (type === "prisao" || type === "estante_livros" || type === "fonte_de_parede"
        || imageName === "fonte_de_parede.png" || imageName === "fontedecanto.png") {
      angle += Math.PI;
    }
    return angle;
  }
  function rotateDecorPending() {
    if (S.sel && S.sel.kind === "decor") {
      const m = decorMeta(S.sel.ref.type);
      if (m && m.gira) {
        if (m.special === "wall") {
          const faces = wallFacesAt(S.sel.ref.pos[0], S.sel.ref.pos[1]);
          if (faces.length) S.sel.ref.facing = nextWallFaceClockwise(S.sel.ref.facing, faces);
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
    if (ev.key === "Delete") {
      if (deleteSelectedEntity()) ev.preventDefault();
      return;
    }
    const modifier = ev.ctrlKey || ev.metaKey;
    if (modifier && ev.key.toLowerCase() === "c") {
      if (copySelectedDecor()) ev.preventDefault();
      return;
    }
    if (modifier && ev.key.toLowerCase() === "v") {
      if (lastPointerCell && pasteDecorAt(lastPointerCell[0], lastPointerCell[1])) ev.preventDefault();
      return;
    }
    if (ev.key === "Escape" && decorBrushActive) {
      decorBrushActive = false; decorAreaPaint = null; buildToolbar(); render(); ev.preventDefault(); return;
    }
    if (ev.key === "r" || ev.key === "R") {
      if (S.sel && S.sel.kind === "door") rotateDoorSelected();
      else rotateDecorPending();
    }
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
    const d = { id: nextDecorId(), type: S.decorType, pos, facing,
                loot: (m && m.loot_capaz && S.decorType === "arca_tesouros") ? { gold: 0, items: [] } : null,
                key_objective: false };
    if (m && m.special === "fountain") d.charges = (m.charges ?? 3);
    if (m && m.special === "floor") d.image = "chaograma1.png";   // grama por padrão (trocável no picker)
    if (m && m.image) d.image = m.image;
    S.decorations.push(d);
    S.sel = { kind: "decor", ref: d, pos: pos.slice() };
  }

  function cloneDecor(source) { return JSON.parse(JSON.stringify(source)); }
  function nextDecorId() {
    const used = new Set(S.decorations.map(d => d.id));
    while (used.has("decor_" + S.nextDecorId)) S.nextDecorId++;
    return "decor_" + S.nextDecorId++;
  }
  function copySelectedDecor() {
    if (!S.sel || S.sel.kind !== "decor" || !S.sel.ref) return false;
    decorClipboard = cloneDecor(S.sel.ref);
    render();
    return true;
  }
  function activateDecorBrush() {
    // Se há uma decoração selecionada, ela sempre é a fonte mais recente do
    // pincel; uma cópia antiga só é usada quando nada está selecionado.
    if (S.sel && S.sel.kind === "decor") copySelectedDecor();
    if (!decorClipboard) return false;
    decorBrushActive = true;
    S.tool = "decor";
    S.decorType = decorClipboard.type;
    S.decorFacing = Array.isArray(decorClipboard.facing) ? decorClipboard.facing.slice() : [0, 1];
    buildToolbar(); renderPanel(); render();
    return true;
  }
  function pasteDecorAt(x, y, selectCopy = true) {
    if (!decorClipboard) return false;
    const d = cloneDecor(decorClipboard);
    d.facing = Array.isArray(d.facing) ? d.facing.slice() : [0, 1];
    if (isWallDecor(d)) {
      const placement = wallPlacementAt(x, y, d.facing);
      if (!placement) return false;
      d.pos = placement.pos;
      d.facing = placement.facing;
    } else d.pos = [x, y];
    const size = decorBaseSize(d);
    if (!decorWouldFit(d, d.pos, size, d.facing)) return false;
    d.id = nextDecorId();
    S.decorations.push(d);
    if (selectCopy) S.sel = { kind: "decor", ref: d, pos: d.pos.slice() };
    if (selectCopy) { renderPanel(); render(); }
    return true;
  }
  function pasteDecorArea(area) {
    if (!decorClipboard || !area) return 0;
    const d = decorClipboard;
    const [ew, eh] = decorEffSizeOf(d);
    const minX = Math.min(area.x0, area.x1), maxX = Math.max(area.x0, area.x1);
    const minY = Math.min(area.y0, area.y1), maxY = Math.max(area.y0, area.y1);
    if (minX === maxX && minY === maxY) {
      return pasteDecorAt(minX, minY, true) ? 1 : 0;
    }
    let placed = 0, last = null;
    // Objetos maiores avançam pelo próprio footprint: uma caverna 2×2, por
    // exemplo, preenche a área sem sobrepor suas cópias nem ultrapassar a seleção.
    const dx = isWallDecor(d) ? 1 : ew, dy = isWallDecor(d) ? 1 : eh;
    for (let y = minY; y + (isWallDecor(d) ? 0 : eh - 1) <= maxY; y += dy) {
      for (let x = minX; x + (isWallDecor(d) ? 0 : ew - 1) <= maxX; x += dx) {
        if (pasteDecorAt(x, y, false)) { placed++; last = S.decorations[S.decorations.length - 1]; }
      }
    }
    if (last) S.sel = { kind: "decor", ref: last, pos: last.pos.slice() };
    return placed;
  }
  function duplicateDecorAdjacent(source) {
    if (!source) return false;
    const [ew, eh] = decorEffSizeOf(source);
    // Primeiro as quatro faces; diagonais são alternativas para objetos grandes
    // ou quando a parede/um objeto bloqueia todos os lados imediatos.
    const offsets = [[ew, 0], [-ew, 0], [0, eh], [0, -eh], [ew, eh], [ew, -eh], [-ew, eh], [-ew, -eh]];
    for (const [dx, dy] of offsets) {
      const d = cloneDecor(source);
      d.pos = [source.pos[0] + dx, source.pos[1] + dy];
      d.facing = Array.isArray(d.facing) ? d.facing.slice() : [0, 1];
      if (!decorWouldFit(d, d.pos, decorBaseSize(d), d.facing)) continue;
      d.id = nextDecorId();
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
  copyMenu.innerHTML = `<button type="button" data-action="copy">Copiar objeto <kbd>Ctrl+C</kbd></button><button type="button" data-action="brush">Usar como pincel de área</button><button type="button" data-action="paste">Colar objeto aqui <kbd>Ctrl+V</kbd></button>`;
  document.body.appendChild(copyMenu);
  function hideCopyMenu() { copyMenu.classList.remove("open"); }
  function showCopyMenu(ev, cell) {
    const selected = entityAt(cell[0], cell[1]);
    if (selected) { S.sel = selected; renderPanel(); render(); }
    const copyButton = copyMenu.querySelector('[data-action="copy"]');
    const brushButton = copyMenu.querySelector('[data-action="brush"]');
    const pasteButton = copyMenu.querySelector('[data-action="paste"]');
    copyButton.disabled = !(S.sel && S.sel.kind === "decor");
    brushButton.disabled = !(S.sel && S.sel.kind === "decor") && !decorClipboard;
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
    else if (button.dataset.action === "brush") activateDecorBrush();
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

  // Miniaturas dos monstros no preview do editor. A mesma imagem PNG usada
  // pelo mapa 2D é centralizada no footprint real da criatura.
  const _monsterImgCache = {};
  function monsterImg(name) {
    if (!name) return null;
    let im = _monsterImgCache[name];
    if (im === undefined) {
      im = new Image();
      im.onload = () => render();
      im.onerror = () => render();
      im.src = "../assets/pawns/monstros/" + name + "/" + name + ".png";
      _monsterImgCache[name] = im;
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
    const hs = S.heroSpawns.find(e => e.pos && e.pos[0] === x && e.pos[1] === y);
    if (hs) return heroSpawnMeta(hs.class_id).emoji;
    if (S.exit && S.exit.x === x && S.exit.y === y) return "🏁";
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return "🧍";
    const mo = at(S.monsters);
    if (mo) {
      // Monstros são desenhados no passe próprio abaixo, onde o centro e o
      // tamanho do footprint podem ser respeitados (inclusive 2×2).
      return null;
    }
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

  // Marcadores de edição: não dependem de emoji, PNG, GLB ou do catálogo. Eles
  // ficam por cima da arte e garantem que cada entidade colocada seja visível.
  function drawEntityMarkers() {
    const byCell = new Map();
    const add = (x, y, label, color) => {
      const key = x + "," + y;
      if (!byCell.has(key)) byCell.set(key, []);
      byCell.get(key).push({ label, color });
    };
    if (S.entrance) add(S.entrance.x, S.entrance.y, "↑", "#468fc6");
    for (const hs of S.heroSpawns) {
      const meta = heroSpawnMeta(hs.class_id);
      add(hs.pos[0], hs.pos[1], meta.mark, "#7c65c9");
    }
    if (S.exit) add(S.exit.x, S.exit.y, "↓", "#c99a3c");
    for (const m of S.monsters) add(m.pos[0], m.pos[1], "M", "#bc4a5a");
    for (const c of S.chests) add(c.pos[0], c.pos[1], "$", "#bd9130");
    for (const t of S.traps) add(t.pos[0], t.pos[1], "!", "#cf6c3b");
    for (const d of S.decorations) add(d.pos[0], d.pos[1], "D", "#348d72");
    if (S.prisoner) add(S.prisoner.pos[0], S.prisoner.pos[1], "P", "#5c88c7");
    for (const f of S.falas) add(f.pos[0], f.pos[1], "…", "#8065ac");
    for (const p of S.secretPassages) add(p.pos[0], p.pos[1], "S", "#5b9fbe");
    for (const [key, markers] of byCell) {
      const [x, y] = key.split(",").map(Number);
      markers.forEach((marker, i) => {
        const col = i % 2, row = Math.floor(i / 2);
        const cx = x * CELL + CELL - 6 - col * 11;
        const cy = y * CELL + 6 + row * 11;
        ctx.save();
        ctx.fillStyle = marker.color;
        ctx.strokeStyle = "#16120d";
        ctx.lineWidth = 1.25;
        ctx.beginPath(); ctx.arc(cx, cy, 5.2, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        ctx.fillStyle = "#fff"; ctx.font = "bold 7px sans-serif";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(marker.label, cx, cy + .2);
        ctx.restore();
      });
    }
  }

  // Marcador explícito de orientação: aparece somente na decoração selecionada
  // para não poluir o mapa. A ponta e o texto indicam exatamente a sua frente.
  function drawDecorFrontMarker(d) {
    if (!d || !d.facing) return;
    const tiles = decorTiles(d);
    if (!tiles.length) return;
    const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
    const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
    const vo = Array.isArray(d.voffset) ? d.voffset : [0, 0];
    const cx = (minX + maxX + 1) * CELL / 2 + Math.max(-.45, Math.min(.45, Number(vo[0]) || 0)) * CELL;
    const cy = (minY + maxY + 1) * CELL / 2 + Math.max(-.45, Math.min(.45, Number(vo[1]) || 0)) * CELL;
    // A seta usa exatamente a mesma transformação aplicada ao sprite: começa
    // apontando para cima e gira no sentido horário a cada clique.
    // A arte da lareira foi modelada com a frente invertida em relação às demais.
    const angle = facingAngle2D(d.facing, d.type, d.image) + (d.type === "lareira" ? Math.PI : 0);
    const dx = Math.sin(angle), dy = -Math.cos(angle);
    const reach = Math.max((maxX - minX + 1) * CELL, (maxY - minY + 1) * CELL) * .42;
    const tipX = cx + dx * reach, tipY = cy + dy * reach;
    const sideX = -dy, sideY = dx;
    ctx.save();
    ctx.fillStyle = "#ffd45a"; ctx.strokeStyle = "#3a2405"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(tipX + dx * 8, tipY + dy * 8);
    ctx.lineTo(tipX - dx * 7 + sideX * 6, tipY - dy * 7 + sideY * 6);
    ctx.lineTo(tipX - dx * 7 - sideX * 6, tipY - dy * 7 - sideY * 6);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.font = "bold 9px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillStyle = "#ffe9a3"; ctx.strokeStyle = "#271600"; ctx.lineWidth = 3;
    const tx = cx + dx * (reach + 14), ty = cy + dy * (reach + 14);
    ctx.strokeText("FRENTE", tx, ty); ctx.fillText("FRENTE", tx, ty);
    ctx.restore();
  }

  // Escadas do editor são desenhadas no canvas, sem depender de fonte/emoji.
  // Assim a entrada e a saída permanecem reconhecíveis até em navegadores que
  // não renderizam corretamente os símbolos usados no mapa.
  function drawStairs(x, y, color, sobe) {
    const px = x * CELL, py = y * CELL;
    ctx.save();
    ctx.fillStyle = color;
    ctx.strokeStyle = "#17120e";
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {
      const step = sobe ? i : 3 - i;
      const w = 8 + step * 3;
      const sx = px + (CELL - w) / 2;
      const sy = py + 20 - i * 4;
      ctx.fillRect(sx, sy, w, 4);
      ctx.strokeRect(sx, sy, w, 4);
    }
    ctx.restore();
  }

  function drawDunePreview(x, y) {
    const px = x * CELL, py = y * CELL, s = CELL - 1;
    ctx.fillStyle = "#5f3a1d";
    ctx.fillRect(px, py, s, s);
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(px + s * .5, py + s * .53, s * .55, s * .57, 0, 0, Math.PI * 2);
    ctx.clip();
    const g = ctx.createLinearGradient(px, py, px + s, py + s);
    g.addColorStop(0, "#d7b66f"); g.addColorStop(.55, "#c39a55"); g.addColorStop(1, "#9f6e32");
    ctx.fillStyle = g; ctx.fillRect(px, py, s, s);
    ctx.strokeStyle = "rgba(255,226,154,.55)"; ctx.lineWidth = 1;
    for (let row = 0; row < 3; row++) {
      const yy = py + s * (.28 + row * .22);
      ctx.beginPath(); ctx.moveTo(px - 2, yy);
      ctx.quadraticCurveTo(px + s * .45, yy - 2, px + s + 2, yy + 1); ctx.stroke();
    }
    ctx.restore();
  }

  function drawElevationEditor(x, y) {
    const level = elevationAt(x, y);
    if (!level) return;
    const X = x * CELL, Y = y * CELL;
    const depth = 2 + Math.abs(level) * 3;
    const neighborLevel = (nx, ny) =>
      nx >= 0 && ny >= 0 && nx < S.grid.w && ny < S.grid.h
        ? elevationAt(nx, ny) : 0;
    ctx.save();
    if (level > 0) {
      ctx.fillStyle = "rgba(8, 7, 12, .42)";
      if (neighborLevel(x + 1, y) < level) ctx.fillRect(X + CELL - depth, Y + 1, depth, CELL - 1);
      if (neighborLevel(x, y + 1) < level) ctx.fillRect(X + 1, Y + CELL - depth, CELL - 1, depth);
      ctx.fillStyle = "rgba(255, 255, 255, .22)";
      ctx.fillRect(X + 1, Y + 1, CELL - 2, 2);
      ctx.fillRect(X + 1, Y + 1, 2, CELL - 2);
      if (S.transicaoAltura === "rampa") {
        ctx.fillStyle = "rgba(235, 211, 137, .18)";
        if (neighborLevel(x + 1, y) < level) {
          ctx.beginPath(); ctx.moveTo(X + CELL - depth, Y + 2);
          ctx.lineTo(X + CELL - 2, Y + CELL - 2); ctx.lineTo(X + CELL - 2, Y + 2);
          ctx.closePath(); ctx.fill();
        }
        if (neighborLevel(x, y + 1) < level) {
          ctx.beginPath(); ctx.moveTo(X + 2, Y + CELL - depth);
          ctx.lineTo(X + CELL - 2, Y + CELL - 2); ctx.lineTo(X + 2, Y + CELL - 2);
          ctx.closePath(); ctx.fill();
        }
      }
    } else {
      ctx.fillStyle = "rgba(0, 0, 0, .32)";
      ctx.fillRect(X + 2, Y + 2, CELL - 4, CELL - 4);
      ctx.strokeStyle = "rgba(90, 210, 255, .45)"; ctx.lineWidth = 1;
      ctx.strokeRect(X + 2, Y + 2, CELL - 4, CELL - 4);
    }
    if (S.tool === "altura") {
      ctx.fillStyle = "rgba(12, 10, 18, .86)";
      ctx.fillRect(X + 3, Y + 3, 15, 12);
      ctx.fillStyle = level > 0 ? "#ffe18b" : "#87dfff";
      ctx.font = "bold 10px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText((level > 0 ? "+" : "") + level, X + 10.5, Y + 9);
    }
    ctx.restore();
  }

  function render() {
    board.width = S.grid.w * CELL;
    board.height = S.grid.h * CELL;
    for (let y = 0; y < S.grid.h; y++) {
      for (let x = 0; x < S.grid.w; x++) {
        const t = S.tiles[y][x];
        const mid = wallMaterialAt(x, y);
        const mm = mid ? matMeta(mid) : null;
        if (mm && mm.id === "duna_deserto") drawDunePreview(x, y);
        else {
          ctx.fillStyle = mm ? mm.cor : (t === WALL ? "#1d1812" : (t === DOOR ? "#c8841f" : "#5a4a32"));
          ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        }
        if (t === DOOR) {
          // A folha e a seta dourada giram sobre o centro. A seta indica a
          // frente da imagem e continua clara nas quatro orientações.
          const px = x * CELL, py = y * CELL, s = CELL - 1;
          const angle = doorBaseAngle(x, y) + doorRotationAt(x, y) * Math.PI / 2;
          ctx.save();
          ctx.translate(px + s / 2, py + s / 2); ctx.rotate(angle);
          const dw = s * .68, dh = s * .88;
          ctx.fillStyle = "#5c3319"; ctx.fillRect(-dw / 2, -dh / 2, dw, dh);
          ctx.strokeStyle = "#d7a34b"; ctx.lineWidth = Math.max(1, s * .055);
          ctx.strokeRect(-dw / 2, -dh / 2, dw, dh);
          ctx.beginPath(); ctx.moveTo(-dw / 2, -dh * .18); ctx.lineTo(dw / 2, -dh * .18); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(-dw / 2, dh * .18); ctx.lineTo(dw / 2, dh * .18); ctx.stroke();
          ctx.fillStyle = "#f0c867"; ctx.beginPath(); ctx.arc(dw * .24, 0, Math.max(1, s * .055), 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = "#ffe27a"; ctx.strokeStyle = "#3a2405"; ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(0, -s * .43); ctx.lineTo(-s * .12, -s * .25); ctx.lineTo(s * .12, -s * .25); ctx.closePath(); ctx.fill(); ctx.stroke();
          ctx.restore();
        }
        if (mid === "entulho") {            // marca de obstáculo
          ctx.fillStyle = "rgba(0,0,0,0.45)";
          ctx.fillRect(x * CELL + CELL * 0.3, y * CELL + CELL * 0.3, CELL * 0.4, CELL * 0.4);
        }
      }
    }
    for (let y = 0; y < S.grid.h; y++)
      for (let x = 0; x < S.grid.w; x++)
        if (S.tiles[y][x] === FLOOR || S.tiles[y][x] === DOOR) drawElevationEditor(x, y);
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
      const vo = Array.isArray(d.voffset) ? d.voffset : [0, 0];
      const ox = Math.max(-.45, Math.min(.45, Number(vo[0]) || 0)) * CELL;
      const oy = Math.max(-.45, Math.min(.45, Number(vo[1]) || 0)) * CELL;
      const ang = facingAngle2D(d.facing, d.type, d.image);
      if (ang === 0) {
        // Escala visual: altura cresce para cima (âncora na base), largura centralizada.
        const dw = pw * vs[0], dh = ph * vs[1];
        ctx.drawImage(im, px + ox + pw / 2 - dw / 2, py + oy + ph - dh, dw, dh);
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
        ctx.translate(px + ox + pw / 2, py + oy + ph / 2);
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
    for (const d of S.decorations) {
      const t = d.trap;
      if (!t || t.tipo !== "armadilha_teletransporte" || !Array.isArray(t.saida)) continue;
      ctx.fillText("⇱", t.saida[0] * CELL + CELL / 2, t.saida[1] * CELL + CELL / 2);
    }
    ctx.textAlign = "start";
    // Marcadores de fala de NPC: pequeno 💬 no canto superior-esquerdo da casa
    // (não conflita com o emoji central de monstro/baú que possa dividir a casa).
    ctx.font = "11px sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "top";
    for (const f of S.falas) {
      ctx.fillText("💬", f.pos[0] * CELL + 2, f.pos[1] * CELL + 1);
    }
    ctx.textAlign = "start"; ctx.textBaseline = "middle";
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
      const vo = Array.isArray(d.voffset) ? d.voffset : [0, 0];
      const cx = (minX + (maxX - minX + 1) / 2) * CELL + Math.max(-.45, Math.min(.45, Number(vo[0]) || 0)) * CELL;
      const baseY = (maxY + 1) * CELL - 4 + Math.max(-.45, Math.min(.45, Number(vo[1]) || 0)) * CELL;
      ctx.save();
      ctx.font = (16 * Math.max(vs[0], vs[1])) + "px sans-serif";
      ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
      ctx.fillText(emoji, cx, baseY);
      ctx.restore();
    }
    // Preview da miniatura e do footprint dos monstros. A posição salva é a
    // âncora do monstro; a imagem fica no centro geométrico das casas ocupadas.
    for (const m of S.monsters) {
      const tiles = monsterTiles(m);
      if (!tiles.length) continue;
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      const fw = maxX - minX + 1, fh = maxY - minY + 1;
      const cx = (minX + fw / 2) * CELL, cy = (minY + fh / 2) * CELL;
      const vs = Array.isArray(m.vscale) ? m.vscale : null;
      const sx = Math.max(.2, Math.min(4, Number(vs && vs[0]) || 1));
      const sy = Math.max(.2, Math.min(4, Number(vs && vs[1]) || 1));
      if (fw > 1 || fh > 1) {
        ctx.save();
        ctx.fillStyle = "rgba(188,74,90,.14)";
        ctx.strokeStyle = "rgba(255,166,132,.82)";
        ctx.lineWidth = 1.5;
        for (const [tx, ty] of tiles) {
          ctx.fillRect(tx * CELL + 2, ty * CELL + 2, CELL - 4, CELL - 4);
          ctx.strokeRect(tx * CELL + 2, ty * CELL + 2, CELL - 4, CELL - 4);
        }
        ctx.restore();
      }
      const im = monsterImg(monsterImageName(m));
      ctx.save();
      if (im) {
        const ar = im.naturalWidth / im.naturalHeight;
        const maxW = fw * CELL * .90 * sx, maxH = fh * CELL * .90 * sy;
        let dw = maxW, dh = dw / ar;
        if (dh > maxH) { dh = maxH; dw = dh * ar; }
        const baseY = (minY + fh) * CELL - 4;
        ctx.drawImage(im, cx - dw / 2, baseY - dh, dw, dh);
      } else {
        const meta = monsterMeta(m);
        const emoji = meta ? meta.emoji : "👹";
        ctx.translate(cx, (minY + fh) * CELL - 5);
        ctx.scale(sx, sy); ctx.font = `${Math.min(30, 16 * Math.max(fw, fh))}px sans-serif`;
        ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
        ctx.fillText(emoji, 0, 0);
      }
      ctx.restore();
      if (monsterCanFly(m)) {
        const meta = monsterFlightMeta(m) || {};
        const altitude = altitudeClamp(m.altura, altitudeClamp(meta.altura_inicial, 2));
        ctx.save();
        ctx.fillStyle = "#8ed8ff"; ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center"; ctx.textBaseline = "bottom";
        ctx.fillText("↑" + altitude, cx, (minY + fh) * CELL - 6 - Math.max(0, sy - 1) * CELL * .25);
        ctx.restore();
      }
    }
    drawEntityMarkers();
    if (S.entrance) drawStairs(S.entrance.x, S.entrance.y, "#69bde9", true);
    if (S.exit) drawStairs(S.exit.x, S.exit.y, "#e5b653", false);
    if (S.sel && S.sel.kind === "monster" && S.sel.ref) {
      const tiles = monsterTiles(S.sel.ref);
      const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
      const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 2;
      ctx.strokeRect(minX * CELL + 1.5, minY * CELL + 1.5, (maxX - minX + 1) * CELL - 3, (maxY - minY + 1) * CELL - 3);
      const label = (maxX - minX + 1) + "×" + (maxY - minY + 1);
      ctx.font = "11px sans-serif"; ctx.textAlign = "left"; ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(minX * CELL + 2, minY * CELL + 2, ctx.measureText(label).width + 5, 13);
      ctx.fillStyle = "#ffd86a"; ctx.fillText(label, minX * CELL + 4, minY * CELL + 3);
      ctx.textAlign = "start";
    } else if (S.sel && S.sel.kind === "decor" && S.sel.ref) {
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
      drawDecorFrontMarker(S.sel.ref);
    } else if (S.sel && S.sel.pos) {
      ctx.strokeStyle = "#ffd86a"; ctx.lineWidth = 2;
      ctx.strokeRect(S.sel.pos[0] * CELL + 1, S.sel.pos[1] * CELL + 1, CELL - 3, CELL - 3);
    }
    if (decorClipboard && lastPointerCell && !_drag) drawClipboardPreview();
    if (decorAreaPaint) drawDecorAreaPreview(decorAreaPaint);
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

  function drawDecorAreaPreview(area) {
    if (!area || !decorClipboard) return;
    const minX = Math.min(area.x0, area.x1), minY = Math.min(area.y0, area.y1);
    const w = Math.abs(area.x1 - area.x0) + 1, h = Math.abs(area.y1 - area.y0) + 1;
    ctx.save();
    ctx.setLineDash([5, 3]); ctx.lineWidth = 2; ctx.strokeStyle = "#72e6a1";
    ctx.fillStyle = "rgba(67,180,111,.10)";
    ctx.fillRect(minX * CELL + 1, minY * CELL + 1, w * CELL - 2, h * CELL - 2);
    ctx.strokeRect(minX * CELL + 1, minY * CELL + 1, w * CELL - 2, h * CELL - 2);
    ctx.setLineDash([]); ctx.restore();
  }

  // Preview do destino durante o arrasto: contorno verde (válido) / vermelho.
  function drawDragPreview() {
    if (!_drag || !_drag.candidate) return;
    const [ax, ay] = _drag.candidate;
    const tiles = _drag.sel.kind === "decor"
      ? tilesFor([ax, ay], decorBaseSize(_drag.sel.ref), _drag.sel.ref.facing)
      : _drag.sel.kind === "monster"
        ? monsterTiles(_drag.sel.ref, [ax, ay])
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
    { id: "altura", label: "altura", group: "tiles" },
    { id: "entrance", label: "entrada", group: "entidades" },
    { id: "hero_spawn", label: "início herói", group: "entidades" },
    { id: "exit", label: "saída", group: "entidades" },
    { id: "monster", label: "monstro", group: "entidades" },
    { id: "chest", label: "baú", group: "entidades" },
    { id: "trap", label: "armadilha", group: "entidades" },
    { id: "prisoner", label: "prisioneiro", group: "entidades" },
    { id: "decor", label: "decoração", group: "entidades" },
    { id: "secret_mechanism", label: "passagem secreta", group: "entidades" },
    { id: "illusion_wall", label: "parede ilusória", group: "entidades" },
    { id: "fala", label: "fala NPC", group: "entidades" },
    { id: "room", label: "sala", group: "ações" },
    { id: "select", label: "selecionar", group: "ações" },
    { id: "erase", label: "apagar", group: "ações" },
  ];

  function buildToolbar() {
    const tb = document.getElementById("toolbar");
    tb.innerHTML = "";
    let lastGroup = null;
    const visibleTools = TOOLS.filter(t => !(S.startMode === "hero_spawns" && t.id === "entrance"));
    for (const t of visibleTools) {
      if (t.group !== lastGroup) {
        if (lastGroup) { const s = document.createElement("span"); s.className = "sep"; tb.appendChild(s); }
        const g = document.createElement("span"); g.className = "group-label"; g.textContent = t.group; tb.appendChild(g);
        lastGroup = t.group;
      }
      const b = document.createElement("button");
      b.textContent = t.label; b.dataset.tool = t.id;
      if (t.id === S.tool) b.classList.add("active");
      b.onclick = () => {
        S.tool = t.id;
        if (t.id === "hero_spawn") { S.startMode = "hero_spawns"; S.entrance = null; }
        if (t.id === "entrance") S.startMode = "entrance";
        buildToolbar(); renderPanel(); render(); updateStatus();
      };
      tb.appendChild(b);
    }
    if (S.tool === "hero_spawn") {
      const sel = document.createElement("select");
      sel.id = "hero-spawn-class";
      sel.innerHTML = HERO_SPAWN_META.map(h =>
        `<option value="${h.id}"${h.id === S.heroSpawnClass ? " selected" : ""}>${h.emoji} ${h.name}</option>`).join("");
      sel.onchange = e => { S.heroSpawnClass = e.target.value; renderPanel(); };
      tb.appendChild(sel);
      const hint = document.createElement("small");
      hint.textContent = "Clique no mapa para posicionar ou mover este herói.";
      hint.style.color = "#b9a87f";
      hint.style.marginLeft = "6px";
      tb.appendChild(hint);
    }
    if (S.tool === "trap") {
      const trapSelect = document.createElement("select");
      trapSelect.id = "trap-type-tool";
      trapSelect.innerHTML = CAT.traps.filter(t => !t.apenas_objeto).map(t =>
        `<option value="${t.tipo}"${t.tipo === S.trapType ? " selected" : ""}>${t.icone || "⚠️"} ${t.nome}</option>`).join("");
      trapSelect.onchange = e => {
        S.trapType = e.target.value;
        const info = document.getElementById("trap-tool-info");
        if (info) info.innerHTML = trapCharacteristicsHTML(CAT.traps.find(t => t.tipo === S.trapType), true);
      };
      tb.appendChild(trapSelect);
      const info = document.createElement("div");
      info.id = "trap-tool-info";
      info.innerHTML = trapCharacteristicsHTML(CAT.traps.find(t => t.tipo === S.trapType), true);
      tb.appendChild(info);
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
      const brush = document.createElement("button");
      brush.textContent = decorBrushActive ? "🖌️ pincel de área ativo" : "🖌️ usar cópia como pincel";
      brush.disabled = !decorClipboard && !(S.sel && S.sel.kind === "decor");
      brush.title = "Com o pincel ativo, arraste no mapa para preencher a área com cópias.";
      brush.onclick = () => { activateDecorBrush(); };
      tb.appendChild(brush);
      if (decorBrushActive) {
        const hint = document.createElement("small");
        hint.textContent = "Arraste para preencher; casas inválidas são ignoradas.";
        hint.style.color = "#b9a87f";
        tb.appendChild(hint);
      }
    }
    if (S.sel && S.sel.kind === "door") {
      const rot = document.createElement("button");
      rot.textContent = "↻ porta 90° (R)";
      rot.title = "Girar a imagem da porta selecionada";
      rot.onclick = rotateDoorSelected;
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
        `<option value="${m.id}"${m.id === cur ? " selected" : ""}>${m.categoria === "parede" ? "🧱" : (m.id === "entulho" ? "⛰️" : "▦")} ${m.nome}${Number(m.custo_mov) > 1 ? ` (−${Number(m.custo_mov) - 1} movimento)` : ""}</option>`).join("");
      sel.onchange = e => { if (isWall) S.matWall = e.target.value; else S.matFloor = e.target.value; };
      tb.appendChild(sel);
      const fill = document.createElement("button");
      fill.textContent = S.matFill ? "balde: ON" : "balde: OFF";
      fill.title = "Preenche a região contígua de mesma estrutura";
      fill.onclick = () => { S.matFill = !S.matFill; buildToolbar(); };
      tb.appendChild(fill);
    }
    if (S.tool === "altura") {
      const level = document.createElement("select");
      level.id = "terrain-height-value";
      level.innerHTML = [
        [-1, "−1 · depressão"], [0, "0 · nivelar"],
        [1, "+1 · elevado"], [2, "+2 · muito elevado"],
      ].map(([value, label]) => `<option value="${value}"${Number(value) === Number(S.elevacaoValor) ? " selected" : ""}>${label}</option>`).join("");
      level.onchange = e => { S.elevacaoValor = Number(e.target.value); render(); };
      tb.appendChild(level);
      const transition = document.createElement("select");
      transition.id = "terrain-height-transition";
      transition.title = "Escolhe a aparência das transições entre níveis diferentes";
      transition.innerHTML = `<option value="rampa"${S.transicaoAltura === "rampa" ? " selected" : ""}>transição: rampa</option><option value="declive"${S.transicaoAltura === "declive" ? " selected" : ""}>transição: declive</option>`;
      transition.onchange = e => { S.transicaoAltura = e.target.value === "declive" ? "declive" : "rampa"; render(); };
      tb.appendChild(transition);
      const hint = document.createElement("small");
      hint.textContent = "Clique e arraste no chão; a altura é apenas visual nesta fase.";
      hint.style.color = "#b9a87f"; hint.style.marginLeft = "6px";
      tb.appendChild(hint);
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
  function doorConditionAt(x, y) {
    return S.doorConditions[doorKey(x, y)] || null;
  }
  function doorUnlink(x, y) {
    for (const r of S.rooms) r.doors = r.doors.filter(d => !(d[0] === x && d[1] === y));
    delete S.doorRotations[doorKey(x, y)];
    delete S.doorConditions[doorKey(x, y)];
  }

  function paintTile(x, y) {
    if (S.tool === "wall") {
      if (S.tiles[y][x] === DOOR) doorUnlink(x, y);
      if (S.matWall === "entulho") { S.tiles[y][x] = FLOOR; S.materiais[x + "," + y] = "entulho"; return; }
      S.tiles[y][x] = WALL;
      _applyMat(x, y, S.matWall, "parede");
    } else if (S.tool === "floor") {
      if (S.tiles[y][x] === DOOR) doorUnlink(x, y);
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

  function elevationAt(x, y) {
    const n = Number(S.elevacoes[x + "," + y]);
    return Number.isInteger(n) ? Math.max(ELEVACAO_MIN, Math.min(ELEVACAO_MAX, n)) : 0;
  }

  function paintElevation(x, y) {
    if (!S.tiles[y] || ![FLOOR, DOOR].includes(S.tiles[y][x])) return;
    const value = Math.max(ELEVACAO_MIN, Math.min(ELEVACAO_MAX, Number(S.elevacaoValor) || 0));
    const key = x + "," + y;
    if (value === 0) delete S.elevacoes[key];
    else S.elevacoes[key] = value;
  }

  let painting = false;
  let materialAreaPaint = null;
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
    if (sel.kind === "monster")
      return monsterTiles(sel.ref, [ax, ay]).every(([tx, ty]) =>
        tx >= 0 && ty >= 0 && tx < S.grid.w && ty < S.grid.h && S.tiles[ty][tx] !== WALL);
    return ax >= 0 && ay >= 0 && ax < S.grid.w && ay < S.grid.h && S.tiles[ay][ax] !== WALL;
  }
  // Move a entidade selecionada para (nx,ny), conforme o tipo.
  function moveSelTo(sel, nx, ny) {
    const k = sel.kind;
    if (k === "entrance") { S.entrance.x = nx; S.entrance.y = ny; }
    else if (k === "hero_spawn" && sel.ref) { sel.ref.pos = [nx, ny]; sel.ref.room_id = roomIdAt(nx, ny); }
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

  function legacyEntityAt(x, y) {
    if (S.tiles[y]?.[x] === DOOR) return { kind: "door", ref: { x, y }, pos: [x, y] };
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return { kind: "entrance", pos: [x, y] };
    const hs = S.heroSpawns.find(e => e.pos[0] === x && e.pos[1] === y);
    if (hs) return { kind: "hero_spawn", ref: hs, pos: hs.pos.slice() };
    if (S.exit && S.exit.x === x && S.exit.y === y) return { kind: "exit", pos: [x, y] };
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return { kind: "prisoner", ref: S.prisoner, pos: [x, y] };
    const secret = S.secretPassages.find(p => p.pos[0] === x && p.pos[1] === y);
    if (secret) return { kind: "secret_passage", ref: secret, pos: [x, y] };
    const find = (arr, kind) => { const r = arr.find(e => e.pos[0] === x && e.pos[1] === y); return r ? { kind, ref: r, pos: [x, y] } : null; };
    // Empilhamento: seleciona o objeto de CIMA (não-piso) antes do chão.
    const _decsHere = S.decorations.filter(d => decorTiles(d).some(c => c[0] === x && c[1] === y));
    const dec = _decsHere.find(d => !isFloorDecor(d)) || _decsHere[0];
    if (dec) return { kind: "decor", ref: dec, pos: dec.pos.slice() };
    const mon = S.monsters.find(e => monsterTiles(e).some(c => c[0] === x && c[1] === y));
    return (mon ? { kind: "monster", ref: mon, pos: mon.pos.slice() } : null)
      || find(S.chests, "chest") || find(S.traps, "trap") || find(S.falas, "fala") || null;
  }

  // Lista todas as entidades em uma casa. A versão antiga retornava apenas a
  // primeira e escondia as demais quando havia sobreposição.
  function entitiesAt(x, y) {
    const found = [];
    if (S.tiles[y]?.[x] === DOOR) found.push({ kind: "door", ref: { x, y }, pos: [x, y] });
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) found.push({ kind: "entrance", pos: [x, y] });
    for (const hs of S.heroSpawns) if (hs.pos[0] === x && hs.pos[1] === y)
      found.push({ kind: "hero_spawn", ref: hs, pos: hs.pos.slice() });
    if (S.exit && S.exit.x === x && S.exit.y === y) found.push({ kind: "exit", pos: [x, y] });
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) found.push({ kind: "prisoner", ref: S.prisoner, pos: S.prisoner.pos.slice() });
    for (const p of S.secretPassages) if (p.pos[0] === x && p.pos[1] === y)
      found.push({ kind: "secret_passage", ref: p, pos: p.pos.slice() });
    const decs = S.decorations.filter(d => decorTiles(d).some(c => c[0] === x && c[1] === y));
    for (const d of decs.filter(d => !isFloorDecor(d)).concat(decs.filter(isFloorDecor)))
      found.push({ kind: "decor", ref: d, pos: d.pos.slice() });
    for (const m of S.monsters) if (monsterTiles(m).some(c => c[0] === x && c[1] === y))
      found.push({ kind: "monster", ref: m, pos: m.pos.slice() });
    for (const c of S.chests) if (c.pos[0] === x && c.pos[1] === y)
      found.push({ kind: "chest", ref: c, pos: c.pos.slice() });
    for (const t of S.traps) if (t.pos[0] === x && t.pos[1] === y)
      found.push({ kind: "trap", ref: t, pos: t.pos.slice() });
    for (const f of S.falas) if (f.pos[0] === x && f.pos[1] === y)
      found.push({ kind: "fala", ref: f, pos: f.pos.slice() });
    return found;
  }

  let _selectionCycle = { key: null, index: 0 };
  function entityAt(x, y, cycle) {
    const found = entitiesAt(x, y);
    if (!found.length) { _selectionCycle = { key: null, index: 0 }; return null; }
    if (!cycle) return found[0];
    const key = x + "," + y;
    if (_selectionCycle.key !== key) _selectionCycle = { key, index: 0 };
    else _selectionCycle.index = (_selectionCycle.index + 1) % found.length;
    return found[_selectionCycle.index];
  }

  function roomIdAt(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? r.id : null;
  }

  function placeEntity(x, y) {
    const rid = roomIdAt(x, y);
    switch (S.tool) {
      case "entrance": S.entrance = { x, y }; break;
      case "hero_spawn": {
        const existing = S.heroSpawns.find(s => s.class_id === S.heroSpawnClass);
        if (existing) { existing.pos = [x, y]; existing.room_id = rid; }
        else S.heroSpawns.push({ class_id: S.heroSpawnClass, pos: [x, y], room_id: rid });
        break;
      }
      case "exit": S.exit = { x, y }; break;
      case "prisoner": S.prisoner = { pos: [x, y], room_id: rid }; break;
      case "monster": {
        const type = (CAT.monsters[0] || {}).type || "goblin";
        const monster = { type, pos: [x, y], room_id: rid, boss: false, target: false };
        if (dropValid({ kind: "monster", ref: monster }, x, y)) S.monsters.push(monster);
        break;
      }
      case "chest": S.chests.push({ pos: [x, y], gold: 0, items: [], key_objective: false }); break;
      case "trap": S.traps.push({ tipo: S.trapType || ((CAT.traps.find(t => !t.apenas_objeto) || CAT.traps[0]) || {}).tipo || "fosso_estacas", pos: [x, y] }); break;
      case "fala": S.falas.push({ id: "fala_" + S.nextFalaId++, pos: [x, y], falante: { nome: "", emoji: "🧙" }, texto: "", trigger: { tipo: "proximidade", raio: 2 }, classe: null, ordem: null, tarefa: null }); break;
      case "decor": placeDecor(x, y); break;
      case "secret_mechanism":
        if (S.tiles[y][x] === WALL && !S.secretPassages.some(p => p.pos[0] === x && p.pos[1] === y))
          S.secretPassages.push({ id: "passage_" + S.nextPassageId++, pos: [x, y], type: "mechanism", wall_material: wallMaterialAt(x, y) || MAT_DEFAULT.parede, key_decor_ids: [], keys_mode: "any" });
        break;
      case "illusion_wall":
        if (S.tiles[y][x] === WALL && !S.secretPassages.some(p => p.pos[0] === x && p.pos[1] === y))
          S.secretPassages.push({ id: "passage_" + S.nextPassageId++, pos: [x, y], type: "illusion", wall_material: wallMaterialAt(x, y) || MAT_DEFAULT.parede, key_decor_ids: [], keys_mode: "any" });
        break;
    }
  }

  function eraseAt(x, y) {
    if (S.tiles[y][x] === DOOR) doorUnlink(x, y);
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) S.entrance = null;
    S.heroSpawns = S.heroSpawns.filter(s => !(s.pos[0] === x && s.pos[1] === y));
    if (S.exit && S.exit.x === x && S.exit.y === y) S.exit = null;
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) S.prisoner = null;
    S.monsters = S.monsters.filter(e => !monsterTiles(e).some(c => c[0] === x && c[1] === y));
    S.chests = S.chests.filter(e => !(e.pos[0] === x && e.pos[1] === y));
    S.traps = S.traps.filter(e => !(e.pos[0] === x && e.pos[1] === y));
    S.decorations = S.decorations.filter(d => !decorTiles(d).some(c => c[0] === x && c[1] === y));
    S.secretPassages = S.secretPassages.filter(p => !(p.pos[0] === x && p.pos[1] === y));
    S.falas = S.falas.filter(f => !(f.pos[0] === x && f.pos[1] === y));
    delete S.materiais[x + "," + y];
    S.tiles[y][x] = WALL;
  }

  // Remove somente a entidade selecionada. Diferente da ferramenta "apagar",
  // isto nunca altera o tile nem o material de chão sob o objeto.
  function deleteSelectedEntity() {
    if (!S.sel || !S.sel.ref) return false;
    const { kind, ref } = S.sel;
    if (kind === "monster") {
      const before = S.monsters.length;
      S.monsters = S.monsters.filter(m => m !== ref);
      if (S.monsters.length === before) return false;
    } else if (kind === "decor") {
      const before = S.decorations.length;
      S.decorations = S.decorations.filter(d => d !== ref);
      if (S.decorations.length === before) return false;
    } else if (kind === "chest") {
      const before = S.chests.length;
      S.chests = S.chests.filter(c => c !== ref);
      if (S.chests.length === before) return false;
    } else {
      return false;
    }
    S.sel = null;
    renderPanel(); render(); updateStatus();
    return true;
  }

  function deleteRoom(room, clearFloor) {
    const idx = S.rooms.indexOf(room);
    if (idx >= 0) S.rooms.splice(idx, 1);
    for (const d of (room.doors || [])) {
      if (!S.rooms.some(r => (r.doors || []).some(other => other[0] === d[0] && other[1] === d[1])))
        delete S.doorRotations[doorKey(d[0], d[1])];
    }
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
    for (const s of S.heroSpawns) if (s.room_id === room.id) s.room_id = null;
    S.sel = null; renderPanel(); render();
  }

  const panel = document.getElementById("panel");
  function opt(list, val, fmt) { return list.map(o => `<option value="${o.v}"${o.v === val ? " selected" : ""}>${fmt(o)}</option>`).join(""); }

  function trapText(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  }

  function trapEffectLabel(effect) {
    if (!effect) return "";
    const tipo = effect.tipo;
    if (tipo === "dano") {
      const elemento = effect.elemento && effect.elemento !== "fisico" ? ` (${trapText(effect.elemento)})` : "";
      const rodada = effect.rodada ? ` — rodada ${effect.rodada}` : "";
      return `${trapText(effect.valor || "dano")} de dano${elemento}${rodada}${effect.area ? " em área" : ""}`;
    }
    if (tipo === "perder_movimento") return "Perde o movimento";
    if (tipo === "perder_rodada") return "Perde a rodada";
    if (tipo === "veneno") return "Aplica o veneno escolhido";
    if (tipo === "reduzir_con") return `${trapText(effect.valor || "redução")} CON por ${trapText(effect.duracao || "algumas")} rodadas${effect.area ? " em área" : ""}`;
    return trapText(tipo || "efeito especial");
  }

  function trapPrimaryDamage(meta) {
    if (!meta) return "";
    if (meta.dano != null) return meta.dano;
    const effect = (meta.efeitos || []).find(e => e && e.tipo === "dano");
    return effect ? (effect.valor || "") : "";
  }

  function validTrapDamage(value) {
    return /^(?:\d*d\d+|\d+)(?:[+-](?:\d*d\d+|\d+))*$/i.test(String(value || "").replace(/\s/g, ""));
  }

  function trapCharacteristicsHTML(meta, compact, instance) {
    if (!meta || !meta.nome) return "";
    const difficulty = instance && instance.dificuldade != null ? instance.dificuldade : meta.dificuldade;
    const damage = instance && instance.dano != null ? instance.dano : trapPrimaryDamage(meta);
    const save = meta.save ? `${trapText(meta.save).replace(/^./, c => c.toUpperCase())}${difficulty ? ` CD ${difficulty}` : ""}` : "Sem teste padrão";
    const scope = meta.area_sala ? "Sala inteira" : meta.area ? `Área: ${meta.area} casa${meta.area === 1 ? "" : "s"}` : "Alvo na casa";
    const duration = meta.duracao_rodadas ? `${meta.duracao_rodadas} rodadas` : (meta.persiste ? "Permanece ativa" : "Uso único");
    const flags = [
      `🎲 ${save}`, `🎯 ${scope}`, `⏱️ ${duration}`,
      damage ? `💥 Dano: ${trapText(damage)}` : "",
      meta.custo_ouro != null ? `🪙 Custo: ${meta.custo_ouro} ouro` : "",
      meta.save_reduz ? "🛡️ Sucesso reduz o dano" : "",
      meta.precisa_veneno ? "☠️ Exige veneno" : (meta.permite_veneno ? "☠️ Veneno opcional" : ""),
      meta.visivel_apos ? "👁️ Revela após ativar" : "",
      meta.escape_save ? `↗️ Escape: ${trapText(meta.escape_save)}${meta.escape_dificuldade ? ` CD ${meta.escape_dificuldade}` : ""}` : "",
      meta.apenas_objeto ? "📦 Só em objeto/decoração" : "",
    ].filter(Boolean);
    const effects = (meta.efeitos || []).map((effect, index) => {
      if (damage && index === (meta.efeitos || []).findIndex(e => e && e.tipo === "dano")) return { ...effect, valor: damage };
      return effect;
    }).map(trapEffectLabel).filter(Boolean);
    return `<div class="trap-characteristics${compact ? " compact" : ""}">
      <div class="trap-characteristics-title">${trapText(meta.icone || "⚠️")} ${trapText(meta.nome)}</div>
      <div class="trap-characteristics-flags">${flags.map(flag => `<span>${flag}</span>`).join("")}</div>
      ${effects.length ? `<div class="trap-characteristics-effects"><b>Efeitos</b>${effects.map(effect => `<div>• ${effect}</div>`).join("")}</div>` : ""}
      ${meta.descricao ? `<div class="trap-characteristics-desc">${trapText(meta.descricao)}</div>` : ""}
    </div>`;
  }

  // Organização visual exclusiva dos seletores de loot de baús e decorações.
  // O item continua sendo salvo pelo mesmo ID; esta camada só agrupa e ordena
  // as opções para facilitar a busca no editor.
  const LOOT_ITEM_GROUPS = [
    "Armas", "Armaduras", "Escudos", "Venenos", "Arremessáveis",
    "Instrumentos", "Munições", "Poções e consumíveis", "Anéis e acessórios", "Outros",
  ];
  function lootItemCategory(item) {
    const id = String(item.id || "").toLowerCase();
    const type = String(item.tipo_item || item.item_type || item.type || "").toLowerCase();
    const slot = String(item.item_slot || "").toLowerCase();
    const effect = String(item.effect || "").toLowerCase();
    if (item.kind === "armor" || ["armor", "armadura", "helmet", "head", "body"].includes(type) || ["armor", "head"].includes(slot)) return "Armaduras";
    if (item.kind === "shield" || ["shield", "escudo"].includes(type) || slot === "shield") return "Escudos";
    if (item.veneno_id || effect === "coat_poison" || id.startsWith("veneno_")) return "Venenos";
    if (effect === "throwable" || ["throwable", "arremessavel", "arremessável"].includes(type)) return "Arremessáveis";
    if (type === "instrumento" || slot === "instrumento" || id.startsWith("instrumento_")) return "Instrumentos";
    if (item.ammo_type || item.ammo_count != null || ["ammo", "municao", "munição"].includes(type)) return "Munições";
    if (item.die || item.range != null || item.reach || item.throw_range != null || item.categoria || ["weapon", "arma"].includes(type)) return "Armas";
    if (item.kind === "accessory" || ["ring", "anel", "accessory", "acessorio", "acessório"].includes(type) || ["ring", "item", "accessory", "acessorio", "acessório"].includes(slot)) return "Anéis e acessórios";
    if (slot === "bag" || effect || type === "consumable" || type === "consumivel" || type === "consumível") return "Poções e consumíveis";
    return "Outros";
  }
  function lootItemSelectHTML(id) {
    const groups = new Map(LOOT_ITEM_GROUPS.map(name => [name, []]));
    for (const item of CAT.items) groups.get(lootItemCategory(item)).push(item);
    return `<select id="${id}">${LOOT_ITEM_GROUPS.map(group => {
      const items = groups.get(group).slice().sort((a, b) => String(a.name || a.id).localeCompare(String(b.name || b.id), "pt-BR"));
      return items.length ? `<optgroup label="${group}">${items.map(item => `<option value="${item.id}">${item.emoji ? item.emoji + " " : ""}${item.name || item.id}</option>`).join("")}</optgroup>` : "";
    }).join("")}</select>`;
  }

  const CURSE_CATEGORIES = [
    { v: "leve", name: "Leve" },
    { v: "media", name: "Média" },
    { v: "grave", name: "Grave" },
  ];
  function curseCatalog() { return CAT.curses || []; }
  function curseFieldsHTML(trap, prefix) {
    if (!trap || trap.tipo !== "armadilha_maldicao") return "";
    const curses = curseCatalog();
    const mode = trap.curse_mode || "aleatoria";
    const firstId = (curses[0] && curses[0].id) || "maos_tremulas";
    const curseId = trap.curse_id || firstId;
    const selected = curses.find(c => c.id === curseId);
    return `<div style="margin-top:8px;border-top:1px solid #4a3a2a;padding-top:8px">
      <label>maldição aplicada</label>
      <select id="${prefix}-curse-mode">
        <option value="especifica"${mode === "especifica" ? " selected" : ""}>Maldição escolhida</option>
        <option value="aleatoria"${mode !== "especifica" ? " selected" : ""}>Aleatória por gravidade</option>
      </select>
      ${mode === "especifica"
        ? `<select id="${prefix}-curse-id">${opt(curses.map(c => ({ v: c.id, name: c.name })), curseId, o => o.name)}</select>
           <small id="${prefix}-curse-desc" style="display:block;color:#b9a87f">${selected ? (selected.description || "") : ""}</small>`
        : `<select id="${prefix}-curse-category">${opt(CURSE_CATEGORIES, trap.curse_category || "leve", o => o.name)}</select>
           <small style="display:block;color:#b9a87f">Escolhe uma maldição não progressiva desta gravidade.</small>`}
    </div>`;
  }
  function prepareCurseTrap(trap, fresh) {
    if (!trap || trap.tipo !== "armadilha_maldicao") {
      if (trap) { delete trap.curse_mode; delete trap.curse_id; delete trap.curse_category; }
      return;
    }
    if (fresh) {
      trap.curse_mode = "especifica";
      trap.curse_id = (curseCatalog()[0] && curseCatalog()[0].id) || "maos_tremulas";
      trap.curse_category = "leve";
    }
  }
  function wireCurseFields(trap, prefix, rerender) {
    if (!trap || trap.tipo !== "armadilha_maldicao") return;
    const mode = document.getElementById(`${prefix}-curse-mode`);
    if (mode) mode.onchange = e => {
      trap.curse_mode = e.target.value;
      if (trap.curse_mode === "especifica" && !trap.curse_id)
        trap.curse_id = (curseCatalog()[0] && curseCatalog()[0].id) || "maos_tremulas";
      rerender();
    };
    const id = document.getElementById(`${prefix}-curse-id`);
    if (id) id.onchange = e => { trap.curse_id = e.target.value; rerender(); };
    const category = document.getElementById(`${prefix}-curse-category`);
    if (category) category.onchange = e => { trap.curse_category = e.target.value; };
  }

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
    // Armadilhas autoradas: cr do catálogo; agrupadas pela sala que contém a pos, ou
    // (corredor) pela sala mais próxima (centro).
    (S.traps || []).forEach(function (t) {
      var meta = (CAT.traps || []).find(function (c) { return c.tipo === t.tipo; });
      var cr = meta ? (meta.cr || 0) : 0;
      if (!cr || !t.pos) return;
      total += cr;
      var dentro = (S.rooms || []).find(function (rm) {
        return t.pos[0] >= rm.x && t.pos[0] < rm.x + rm.w && t.pos[1] >= rm.y && t.pos[1] < rm.y + rm.h;
      });
      var r = dentro;
      if (!r && (S.rooms || []).length) {
        var bestD = Infinity;
        S.rooms.forEach(function (rm) {
          var d = Math.abs(t.pos[0] - (rm.x + rm.w / 2)) + Math.abs(t.pos[1] - (rm.y + rm.h / 2));
          if (d < bestD) { bestD = d; r = rm; }
        });
      }
      var key = r ? r.id : "__none__";
      porSala[key] = (porSala[key] || 0) + cr;
    });
    var pior = 0;
    Object.keys(porSala).forEach(function (k) { if (porSala[k] > pior) pior = porSala[k]; });
    return { total: total, pior: pior };
  }

  // ── Validador de design (Camada C): grafo de salas + 5 regras (só avisa) ──
  var VALID_MIN_SALAS = 3;      // R2: distância mín. spawn→boss (nº de salas)
  var VALID_REST_FATOR = 0.3;   // R5: ND "baixo" = poder × fator
  var VALID_R6_FATOR = 0.9;     // R6: teto do ND médio da rota crítica = poder × fator
  var VALID_MAX_PICO = 1.0;     // R3: Δ máx. de ND entre salas obrigatórias consecutivas

  function _tileRoom(x, y) {
    return (S.rooms || []).find(function (r) { return x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h; }) || null;
  }

  function _ndSalaMap() {
    var m = {};
    (S.rooms || []).forEach(function (r) { m[r.id] = 0; });
    (S.monsters || []).forEach(function (mo) {
      var e = (CAT.monsters || []).find(function (c) { return c.type === mo.type; });
      var cr = window.Difficulty ? window.Difficulty.crFromEntry(e) : 0;
      if (mo.room_id != null && m[mo.room_id] != null) m[mo.room_id] += cr;
    });
    (S.traps || []).forEach(function (t) {
      var meta = (CAT.traps || []).find(function (c) { return c.tipo === t.tipo; });
      var cr = meta ? (meta.cr || 0) : 0; if (!cr || !t.pos) return;
      var r = _tileRoom(t.pos[0], t.pos[1]);
      if (!r && (S.rooms || []).length) {
        var bestD = Infinity;
        S.rooms.forEach(function (rm) { var d = Math.abs(t.pos[0]-(rm.x+rm.w/2))+Math.abs(t.pos[1]-(rm.y+rm.h/2)); if (d < bestD) { bestD = d; r = rm; } });
      }
      if (r && m[r.id] != null) m[r.id] += cr;
    });
    return m;
  }

  function _grafoSalas() {
    var W = S.grid.w, H = S.grid.h;
    var floor = function (x, y) { return x >= 0 && y >= 0 && x < W && y < H && S.tiles[y][x] !== WALL; };
    var entradaSala = (S.rooms || []).find(function (r) { return r.role === "entrance"; });
    if (!entradaSala && S.startMode === "hero_spawns" && S.heroSpawns.length) {
      var firstSpawn = S.heroSpawns[0];
      entradaSala = (S.rooms || []).find(function (r) { return r.id === firstSpawn.room_id; }) ||
        (S.rooms || []).find(function (r) {
          return firstSpawn.pos[0] >= r.x && firstSpawn.pos[0] < r.x + r.w &&
                 firstSpawn.pos[1] >= r.y && firstSpawn.pos[1] < r.y + r.h;
        });
    }
    var bossSala = (S.rooms || []).find(function (r) { return r.role === "boss"; });
    var adj = {};
    (S.rooms || []).forEach(function (r) {
      adj[r.id] = new Set();
      var seen = {}, q = [];
      for (var yy = r.y; yy < r.y + r.h; yy++) for (var xx = r.x; xx < r.x + r.w; xx++) { seen[xx + "," + yy] = 1; q.push([xx, yy]); }
      while (q.length) {
        var c = q.shift();
        [[1,0],[-1,0],[0,1],[0,-1]].forEach(function (d) {
          var nx = c[0]+d[0], ny = c[1]+d[1], k = nx+","+ny;
          if (seen[k] || !floor(nx, ny)) return;
          var other = _tileRoom(nx, ny);
          if (other && other.id !== r.id) { adj[r.id].add(other.id); return; }   // vizinha; não atravessa outra sala
          seen[k] = 1; q.push([nx, ny]);
        });
      }
    });
    var reach = new Set();
    if (entradaSala) {
      var st = [entradaSala.id]; reach.add(entradaSala.id);
      while (st.length) { var id = st.pop(); adj[id].forEach(function (n) { if (!reach.has(n)) { reach.add(n); st.push(n); } }); }
    }
    return { adj: adj, reach: reach, entradaId: entradaSala && entradaSala.id, bossId: bossSala && bossSala.id };
  }

  function _distSalas(adj, fromId, toId) {
    if (fromId == null || toId == null) return Infinity;
    var dist = {}; dist[fromId] = 0; var q = [fromId];
    while (q.length) { var id = q.shift(); if (id === toId) return dist[id]; (adj[id] || new Set()).forEach(function (n) { if (dist[n] == null) { dist[n] = dist[id] + 1; q.push(n); } }); }
    return Infinity;
  }

  function _alcancaSemSala(adj, fromId, toId, excluirId) {
    // toId é alcançável de fromId no grafo IGNORANDO a sala excluirId?
    if (fromId == null || toId == null) return false;
    var seen = {}; seen[fromId] = 1; var q = [fromId];
    while (q.length) {
      var id = q.shift();
      var vizinhos = adj[id] || new Set();
      var achou = false;
      vizinhos.forEach(function (n) {
        if (n === excluirId || seen[n]) return;
        if (n === toId) achou = true;
        seen[n] = 1; q.push(n);
      });
      if (achou) return true;
    }
    return !!seen[toId];
  }

  function _validarDesign() {
    var avisos = [];
    if (!S.rooms || !S.rooms.length) return avisos;
    var g = _grafoSalas(), nd = _ndSalaMap();
    var pod = window.Difficulty ? window.Difficulty.poder(S.expectedParty.heroes, S.expectedParty.level) : Math.max(1, S.expectedParty.heroes * S.expectedParty.level);
    S.rooms.forEach(function (r) { if (!g.reach.has(r.id)) avisos.push("R4: sala #" + r.id + " isolada do mapa principal."); });
    if (g.bossId == null) { avisos.push("R2/R5: sem sala com role 'boss' (regras puladas)."); }
    else {
      var dist = _distSalas(g.adj, g.entradaId, g.bossId);
      if (dist !== Infinity && dist < VALID_MIN_SALAS) avisos.push("R2: boss a só " + dist + " sala(s) do spawn (mín " + VALID_MIN_SALAS + ").");
      var viz = Array.from(g.adj[g.bossId] || []);
      var temDescanso = viz.some(function (id) { var rm = S.rooms.find(function (x) { return x.id === id; }); return rm && (rm.role === "empty" || (nd[id] || 0) <= pod * VALID_REST_FATOR); });
      if (viz.length && !temDescanso) avisos.push("R5: sem sala de descanso (ND baixo) logo antes do boss.");
      // R1: gargalos (cut vertices) — salas cuja remoção isola o boss do spawn.
      if (dist !== Infinity) {
        var gargalos = S.rooms.filter(function (r) {
          return r.id !== g.entradaId && r.id !== g.bossId && g.reach.has(r.id) &&
                 !_alcancaSemSala(g.adj, g.entradaId, g.bossId, r.id);
        }).map(function (r) { return "#" + r.id; });
        if (gargalos.length) avisos.push("R1: rota única — sem caminho alternativo até o boss (gargalo em " + gargalos.join(", ") + ").");
      }
    }
    var req = S.rooms.filter(function (r) { return r.required; });
    if (!req.length) { avisos.push("R3/R6: nenhuma sala marcada como obrigatória (rota crítica)."); }
    else {
      var media = req.reduce(function (a, r) { return a + (nd[r.id] || 0); }, 0) / req.length;
      var teto = pod * VALID_R6_FATOR;
      if (media > teto) avisos.push("R6: rota crítica pesada (ND médio " + media.toFixed(2) + " > teto " + teto.toFixed(2) + ").");
      var ord = req.slice().sort(function (a, b) { return _distSalas(g.adj, g.entradaId, a.id) - _distSalas(g.adj, g.entradaId, b.id); });
      for (var i = 1; i < ord.length; i++) {
        var delta = Math.abs((nd[ord[i-1].id] || 0) - (nd[ord[i].id] || 0));
        if (delta > VALID_MAX_PICO) avisos.push("R3: pico de ND entre salas #" + ord[i-1].id + " e #" + ord[i].id + " (Δ=" + delta.toFixed(2) + ").");
      }
    }
    return avisos;
  }

  function _avisosDesignHTML() {
    var av = _validarDesign();
    if (!av.length) return '<hr style="border-color:#3a3022;margin:10px 0"><div style="color:#7ea87e;font-size:12px">✅ Sem avisos de design.</div>';
    return '<hr style="border-color:#3a3022;margin:10px 0"><label>⚠️ Avisos de design (' + av.length + ')</label>' +
      av.map(function (a) { return '<div style="color:#d8b06a;font-size:11px;margin-top:2px">• ' + a + '</div>'; }).join("");
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
      const OBJ = ["kill_target", "kill_all", "reach_exit", "all_heroes_at_exit", "open_key_chest", "rescue_prisoner", "salas_obrigatorias"];
      const o = S.objectives;
      normalizeObjective(o.primary, true);
      o.secondary.forEach(s => normalizeObjective(s, false));
      const spawnList = S.heroSpawns.map((s, i) => {
        const h = heroSpawnMeta(s.class_id);
        return `<div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px">
          <span>${h.emoji} ${h.name} <small>(${s.pos[0]},${s.pos[1]})</small></span>
          <button class="hero-spawn-rm" data-i="${i}">×</button>
        </div>`;
      }).join("") || '<small style="color:#8a7a5a">Nenhuma posição inicial definida.</small>';
      panel.innerHTML = `<b>🗺️ Masmorra</b>
        <label>modo de início</label>
        <select id="start-mode">
          <option value="entrance"${S.startMode === "entrance" ? " selected" : ""}>Entrada tradicional</option>
          <option value="hero_spawns"${S.startMode === "hero_spawns" ? " selected" : ""}>Heróis separados</option>
        </select>
        ${S.startMode === "hero_spawns" ? `<div style="margin-top:6px;color:#b9a87f;font-size:11px">Posicione cada classe com a ferramenta <b>início herói</b>. A masmorra não terá escada de entrada.</div><div id="hero-spawn-list">${spawnList}</div>` : ""}
        <hr style="border-color:#3a3022;margin:10px 0">
        <label>objetivo principal</label>
        <select id="o-prim">${OBJ.map(t => `<option value="${t}"${o.primary.type === t ? " selected" : ""}>${t === "all_heroes_at_exit" ? "todos os heróis na saída" : t}</option>`).join("")}</select>
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
        ${_termometroHTML()}
        ${_avisosDesignHTML()}`;
      document.getElementById("start-mode").onchange = e => {
        S.startMode = e.target.value;
        if (S.startMode === "hero_spawns") { S.entrance = null; S.meta.saida_permitida = false; }
        else if (S.tool === "hero_spawn") S.tool = "select";
        buildToolbar(); renderPanel(); render(); updateStatus();
      };
      const exitToggle = document.getElementById("m-saida");
      if (exitToggle) {
        exitToggle.disabled = S.startMode === "hero_spawns";
        exitToggle.checked = S.startMode === "hero_spawns" ? false : S.meta.saida_permitida !== false;
      }
      panel.querySelectorAll(".hero-spawn-rm").forEach(b => b.onclick = () => {
        S.heroSpawns.splice(Number(b.dataset.i), 1); renderPanel(); render(); updateStatus();
      });
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
    if (k === "door") {
      const rot = doorRotationAt(ref.x, ref.y);
      const conditionKey = doorKey(ref.x, ref.y);
      const condition = doorConditionAt(ref.x, ref.y);
      const keyItems = CAT.items.map(it => ({ v: it.id, name: it.name }));
      const keyDecors = S.decorations.filter(d => d.key_objective);
      const selectedDecorKeys = new Set(condition?.key_decor_ids || []);
      panel.innerHTML = `<b>🚪 Porta</b>
        <div style="margin-top:6px;color:#b9a87f">Posição: (${ref.x},${ref.y})</div>
        <div style="margin-top:6px;color:#f0c867"><b>Frente da imagem: ${doorFrontLabel(ref.x, ref.y)}</b></div>
        <div style="font-size:11px;color:#8a7a5a;margin-top:4px">Giros aplicados: ${rot} × 90°</div>
        <button id="door-rotate" style="margin-top:8px">↻ Girar 90° (R)</button>
        <small style="display:block;color:#8a7a5a;margin-top:6px">A seta dourada no mapa mostra a frente. A orientação é salva nesta porta.</small>
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>🔐 Condição opcional de abertura</b>
          <select id="door-condition-type">
            <option value="none"${!condition ? " selected" : ""}>Sem condição</option>
            <option value="item"${condition?.type === "item" ? " selected" : ""}>Item-chave</option>
            <option value="decor"${condition?.type === "decor" ? " selected" : ""}>Objeto-chave ativado</option>
            <option value="licao"${condition?.type === "licao" ? " selected" : ""}>Lição cumprida</option>
          </select>
          ${condition?.type === "licao" ? (() => {
            const licoes = S.falas.filter(f => f.tarefa && f.tarefa.tipo);
            if (!licoes.length) return '<small style="color:#d8a0a0">Crie primeiro uma fala com tarefa.</small>';
            return `<label>lição necessária</label><select id="door-condition-licao">${licoes.map(l => `<option value="${l.id}"${condition.licao_id === l.id ? " selected" : ""}>${l.id} — ${(l.tarefa.texto_curto || "").slice(0, 30)}</option>`).join("")}</select>`;
          })() : ""}
          ${condition?.type === "item" ? `<label>item necessário</label><select id="door-condition-item">${opt(keyItems, condition.item_id || "", o => o.v + " — " + o.name)}</select>` : ""}
          ${condition?.type === "decor" ? `<label>modo das ativações</label><select id="door-condition-mode">
              <option value="any"${condition.keys_mode !== "all" ? " selected" : ""}>qualquer objeto</option>
              <option value="all"${condition.keys_mode === "all" ? " selected" : ""}>todos os objetos</option>
            </select>
            <label>objetos-chave</label>
            ${keyDecors.length ? keyDecors.map(d => `<label style="display:block"><input type="checkbox" class="door-condition-key" data-id="${d.id}"${selectedDecorKeys.has(d.id) ? " checked" : ""}> ${d.type} — (${d.pos[0]},${d.pos[1]})</label>`).join("") : '<small style="color:#d8a0a0">Marque primeiro uma decoração como objeto-chave.</small>'}` : ""}
        </div>`;
      document.getElementById("door-rotate").onclick = rotateDoorSelected;
      document.getElementById("door-condition-type").onchange = e => {
        if (e.target.value === "none") delete S.doorConditions[conditionKey];
        else if (e.target.value === "item") S.doorConditions[conditionKey] = { type: "item", item_id: keyItems[0]?.v || "" };
        else if (e.target.value === "licao") S.doorConditions[conditionKey] = { type: "licao", licao_id: (S.falas.find(f => f.tarefa && f.tarefa.tipo) || {}).id || "" };
        else S.doorConditions[conditionKey] = { type: "decor", key_decor_ids: [], keys_mode: "any" };
        renderPanel(); render();
      };
      const conditionLicao = document.getElementById("door-condition-licao");
      if (conditionLicao) conditionLicao.onchange = e => { S.doorConditions[conditionKey].licao_id = e.target.value; };
      const conditionItem = document.getElementById("door-condition-item");
      if (conditionItem) conditionItem.onchange = e => { S.doorConditions[conditionKey].item_id = e.target.value; };
      const conditionMode = document.getElementById("door-condition-mode");
      if (conditionMode) conditionMode.onchange = e => { S.doorConditions[conditionKey].keys_mode = e.target.value === "all" ? "all" : "any"; };
      panel.querySelectorAll(".door-condition-key").forEach(box => box.onchange = e => {
        const ids = S.doorConditions[conditionKey].key_decor_ids || (S.doorConditions[conditionKey].key_decor_ids = []);
        if (e.target.checked) { if (!ids.includes(e.target.dataset.id)) ids.push(e.target.dataset.id); }
        else S.doorConditions[conditionKey].key_decor_ids = ids.filter(id => id !== e.target.dataset.id);
      });
    } else if (k === "hero_spawn") {
      const h = heroSpawnMeta(ref.class_id);
      panel.innerHTML = `<b>${h.emoji} Início: ${h.name}</b>
        <div style="margin-top:6px;color:#b9a87f">Posição: (${ref.pos[0]},${ref.pos[1]})</div>
        <small>Para trocar de herói, selecione a ferramenta "início herói" e escolha outra classe.</small>`;
    } else if (k === "monster") {
      const vs = Array.isArray(ref.vscale) ? ref.vscale : [1, 1];
      const flightMeta = monsterFlightMeta(ref);
      const isFlying = monsterCanFly(ref);
      const defaultAltitude = altitudeClamp(flightMeta && flightMeta.altura_inicial, 2);
      const defaultMaxAltitude = altitudeClamp(flightMeta && flightMeta.altura_max, 10);
      const defaultCanChangeAltitude = flightMeta && flightMeta.pode_alterar_altura !== undefined
        ? !!flightMeta.pode_alterar_altura : true;
      const defaultAltitudeMoveCost = Math.max(1, Math.min(10, Number(flightMeta && flightMeta.custo_mov_altura) || 1));
      const defaultIgnoreFlightObstacles = !!(flightMeta && flightMeta.ignora_obstaculos_voo);
      const altitude = altitudeClamp(ref.altura, defaultAltitude);
      const maxAltitude = Math.max(altitude, altitudeClamp(ref.altura_max, defaultMaxAltitude));
      panel.innerHTML = `<b>👹 Monstro</b>
        <label>tipo</label><select id="p-type">${opt(CAT.monsters.map(m => ({ v: m.type, name: m.name })), ref.type, o => o.v + " — " + o.name)}</select>
        <label>room_id <input id="p-room" value="${ref.room_id ?? ""}"></label>
        <label><input type="checkbox" id="p-boss" ${ref.boss ? "checked" : ""}> chefe (boss)</label>
        <label><input type="checkbox" id="p-target" ${ref.target ? "checked" : ""}> alvo do objetivo</label>
        ${isFlying ? `<div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>🪽 Voo e altitude</b>
          <div style="font-size:11px;color:#8a7a5a">A altura usa a escala 0–10 e afeta o alcance das armas.</div>
          <label>altura inicial <input id="p-altitude" type="number" min="0" max="10" step="1" value="${altitude}"></label>
          <label>altura máxima <input id="p-altitude-max" type="number" min="0" max="10" step="1" value="${maxAltitude}"></label>
          <label><input type="checkbox" id="p-altitude-change"${(ref.pode_alterar_altura ?? defaultCanChangeAltitude) ? " checked" : ""}> pode subir/descer</label>
          <label>custo vertical <input id="p-altitude-cost" type="number" min="1" max="10" step="1" value="${Math.max(1, Math.min(10, Number(ref.custo_mov_altura) || defaultAltitudeMoveCost))}"> movimento por ponto</label>
          <label><input type="checkbox" id="p-flight-obstacles"${(ref.ignora_obstaculos_voo ?? defaultIgnoreFlightObstacles) ? " checked" : ""}> ignora obstáculos no voo</label>
        </div>` : `<small style="display:block;margin-top:8px;color:#8a7a5a">Este tipo não possui a habilidade Voo.</small>`}
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>Tamanho visual do sprite</b>
          <div style="font-size:11px;color:#8a7a5a">não muda as casas ocupadas nem as regras de combate.</div>
          <label>escala largura <input id="p-vsx" type="number" min="0.2" max="4" step="0.1" value="${vs[0]}"></label>
          <label>escala altura <input id="p-vsy" type="number" min="0.2" max="4" step="0.1" value="${vs[1]}"></label>
        </div>`;
      document.getElementById("p-type").onchange = e => {
        ref.type = e.target.value;
        if (!monsterCanFly(ref)) {
          delete ref.altura; delete ref.altura_max;
          delete ref.pode_alterar_altura; delete ref.custo_mov_altura;
          delete ref.ignora_obstaculos_voo;
        }
        renderPanel(); render();
      };
      document.getElementById("p-room").onchange = e => { ref.room_id = e.target.value === "" ? null : Number(e.target.value); };
      document.getElementById("p-boss").onchange = e => { ref.boss = e.target.checked; };
      document.getElementById("p-target").onchange = e => { ref.target = e.target.checked; };
      const applyMonsterScale = () => {
        const sx = Math.max(0.2, Math.min(4, Number(document.getElementById("p-vsx").value) || 1));
        const sy = Math.max(0.2, Math.min(4, Number(document.getElementById("p-vsy").value) || 1));
        if (sx === 1 && sy === 1) delete ref.vscale; else ref.vscale = [sx, sy];
        render();
      };
      document.getElementById("p-vsx").onchange = applyMonsterScale;
      document.getElementById("p-vsy").onchange = applyMonsterScale;
      if (isFlying) {
        const applyAltitude = () => {
          const n = altitudeClamp(document.getElementById("p-altitude").value, defaultAltitude);
          if (n === defaultAltitude) delete ref.altura; else ref.altura = n;
          const maxEl = document.getElementById("p-altitude-max");
          const max = Math.max(n, altitudeClamp(maxEl.value, defaultMaxAltitude));
          maxEl.value = max;
          if (max === defaultMaxAltitude) delete ref.altura_max; else ref.altura_max = max;
          render();
        };
        const applyAltitudeMax = () => {
          const n = altitudeClamp(document.getElementById("p-altitude").value, defaultAltitude);
          const max = Math.max(n, altitudeClamp(document.getElementById("p-altitude-max").value, defaultMaxAltitude));
          document.getElementById("p-altitude-max").value = max;
          if (max === defaultMaxAltitude) delete ref.altura_max; else ref.altura_max = max;
          if (altitudeClamp(ref.altura, defaultAltitude) > max) ref.altura = max === defaultAltitude ? undefined : max;
          if (ref.altura === undefined) delete ref.altura;
          render();
        };
        const altitudeChange = document.getElementById("p-altitude-change");
        const altitudeCost = document.getElementById("p-altitude-cost");
        const flightObstacles = document.getElementById("p-flight-obstacles");
        document.getElementById("p-altitude").onchange = applyAltitude;
        document.getElementById("p-altitude-max").onchange = applyAltitudeMax;
        altitudeChange.onchange = e => {
          if (e.target.checked === defaultCanChangeAltitude) delete ref.pode_alterar_altura;
          else ref.pode_alterar_altura = e.target.checked;
        };
        altitudeCost.onchange = e => {
          const n = Math.max(1, Math.min(10, Number(e.target.value) | 0));
          e.target.value = n;
          if (n === defaultAltitudeMoveCost) delete ref.custo_mov_altura; else ref.custo_mov_altura = n;
        };
        flightObstacles.onchange = e => {
          if (e.target.checked === defaultIgnoreFlightObstacles) delete ref.ignora_obstaculos_voo;
          else ref.ignora_obstaculos_voo = e.target.checked;
        };
      }
    } else if (k === "chest") {
      panel.innerHTML = `<b>🧰 Baú</b>
        <label>ouro <input id="p-gold" type="number" value="${ref.gold}"></label>
        <label><input type="checkbox" id="p-key" ${ref.key_objective ? "checked" : ""}> baú-chave</label>
        <label>itens</label>
        <div id="p-items">${ref.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="rm-item">×</button></div>`).join("")}</div>
        ${lootItemSelectHTML("p-add")}
        <button id="p-additem">+ item</button>`;
      document.getElementById("p-gold").onchange = e => { ref.gold = Math.max(0, Number(e.target.value) | 0); };
      document.getElementById("p-key").onchange = e => { ref.key_objective = e.target.checked; };
      document.getElementById("p-additem").onclick = () => { const id = document.getElementById("p-add").value; if (id) ref.items.push({ id }); renderPanel(); };
      panel.querySelectorAll(".rm-item").forEach(b => b.onclick = () => { ref.items.splice(Number(b.dataset.i), 1); renderPanel(); });
    } else if (k === "trap") {
      const meta = CAT.traps.find(t => t.tipo === ref.tipo) || {};
      const defaultDamage = trapPrimaryDamage(meta);
      const defaultDifficulty = meta.dificuldade || "";
      panel.innerHTML = `<b>⚠️ Armadilha</b>
        <label>tipo</label><select id="p-tt">${opt(CAT.traps.filter(t => !t.apenas_objeto).map(t => ({ v: t.tipo, name: t.nome })), ref.tipo, o => o.v + " — " + o.name)}</select>
        ${trapCharacteristicsHTML(meta, false, ref)}
        <div class="trap-overrides">
          <b>⚙️ Ajustes desta armadilha</b>
          <label>CD do teste <input id="p-trap-cd" type="number" min="1" max="40" value="${ref.dificuldade ?? defaultDifficulty}"></label>
          ${defaultDamage ? `<label>dano principal <input id="p-trap-damage" value="${trapText(ref.dano ?? defaultDamage)}" placeholder="ex.: 2d6"></label><small id="p-trap-damage-help">Formato: 1d6, 2d8+2 ou 3.</small>` : `<small>Esta armadilha não possui dano direto configurável.</small>`}
          <small>Apague o valor para voltar ao padrão do catálogo.</small>
        </div>
        ${meta.precisa_veneno || meta.permite_veneno ? `<label>veneno${meta.permite_veneno && !meta.precisa_veneno ? " (opcional)" : ""}</label><select id="p-ven">${opt(CAT.venoms.map(v => ({ v: v.id, name: v.name })), ref.veneno_id || "", o => o.v + " — " + o.name)}</select>` : ""}
        ${curseFieldsHTML(ref, "p")}
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
      document.getElementById("p-tt").onchange = e => {
        ref.tipo = e.target.value;
        delete ref.dificuldade;
        delete ref.dano;
        const nextMeta = CAT.traps.find(t => t.tipo === ref.tipo) || {};
        if (!(nextMeta.precisa_veneno || nextMeta.permite_veneno)) delete ref.veneno_id;
        if (ref.tipo !== "armadilha_teletransporte") delete ref.saida;
        prepareCurseTrap(ref, true);
        renderPanel(); render();
      };
      const trapCdInput = document.getElementById("p-trap-cd");
      if (trapCdInput) trapCdInput.onchange = e => {
        const raw = e.target.value.trim();
        if (!raw) delete ref.dificuldade;
        else ref.dificuldade = Math.max(1, Math.min(40, Number(raw) | 0));
        renderPanel(); render(); updateStatus();
      };
      const trapDamageInput = document.getElementById("p-trap-damage");
      if (trapDamageInput) trapDamageInput.onchange = e => {
        const raw = e.target.value.trim().replace(/\s/g, "");
        const help = document.getElementById("p-trap-damage-help");
        if (!raw) { delete ref.dano; renderPanel(); render(); updateStatus(); return; }
        if (!validTrapDamage(raw)) { if (help) help.textContent = "Valor inválido. Use 1d6, 2d8+2 ou 3."; e.target.focus(); return; }
        ref.dano = raw; renderPanel(); render(); updateStatus();
      };
      if (meta.precisa_veneno || meta.permite_veneno) document.getElementById("p-ven").onchange = e => { ref.veneno_id = e.target.value || null; };
      wireCurseFields(ref, "p", () => { renderPanel(); render(); });
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
    } else if (k === "fala") {
      const tg = ref.trigger || (ref.trigger = { tipo: "proximidade", raio: 2 });
      const fal = ref.falante || (ref.falante = { nome: "", emoji: "🧙" });
      const tar = ref.tarefa || null;
      const ehCasa = tar && LICAO_VERBOS_CASA.has(tar.tipo);
      panel.innerHTML = `<b>💬 Fala / lição</b>
        <label>emoji do falante</label><input id="f-emoji" value="${(fal.emoji || "").replace(/"/g, "&quot;")}" maxlength="4" style="width:60px">
        <label>nome do falante</label><input id="f-nome" value="${(fal.nome || "").replace(/"/g, "&quot;")}" placeholder="(opcional)">
        <label>texto</label><textarea id="f-texto" rows="3" style="width:100%">${(ref.texto || "").replace(/</g, "&lt;")}</textarea>
        <label>gatilho</label><select id="f-tipo">
          <option value="proximidade"${tg.tipo === "proximidade" ? " selected" : ""}>proximidade (raio)</option>
          <option value="sala"${tg.tipo === "sala" ? " selected" : ""}>entrar na sala</option>
          <option value="manual"${tg.tipo === "manual" ? " selected" : ""}>manual (mestre)</option>
        </select>
        ${tg.tipo === "proximidade" ? `<label>raio (casas)</label><input id="f-raio" type="number" min="1" max="20" value="${tg.raio || 2}" style="width:60px">` : ""}
        <div style="margin-top:10px;border-top:1px solid #4a3a2a;padding-top:8px">
          <b>🎓 Lição de tutorial</b>
          <label>para a classe</label>
          <select id="f-classe">
            <option value=""${!ref.classe ? " selected" : ""}>todas as classes</option>
            ${HERO_SPAWN_META.map(h => `<option value="${h.id}"${ref.classe === h.id ? " selected" : ""}>${h.emoji} ${h.name}</option>`).join("")}
          </select>
          <label>ordem na trilha (vazio = sem ordem)</label>
          <input id="f-ordem" type="number" min="1" value="${ref.ordem ?? ""}" style="width:70px">
          <label><input type="checkbox" id="f-tem-tarefa"${tar ? " checked" : ""}> cobra uma tarefa</label>
          ${tar ? `
            <label>tarefa</label>
            <select id="f-tarefa-tipo">${LICAO_VERBOS.map(o => `<option value="${o.v}"${tar.tipo === o.v ? " selected" : ""}>${o.nome}</option>`).join("")}</select>
            <label>alvo ${ehCasa ? "(casa x,y — vazio = qualquer)" : "(tipo do monstro ou id do item — vazio = qualquer)"}</label>
            <input id="f-tarefa-alvo" value="${ehCasa ? (Array.isArray(tar.alvo) ? tar.alvo.join(",") : "") : (typeof tar.alvo === "string" ? tar.alvo : "")}" placeholder="${ehCasa ? "12,5" : "goblin"}">
            <label>vezes</label><input id="f-tarefa-vezes" type="number" min="1" value="${tar.vezes || 1}" style="width:70px">
            <label>texto curto (aparece no HUD)</label>
            <input id="f-tarefa-curto" value="${(tar.texto_curto || "").replace(/"/g, "&quot;")}" placeholder="Ataque o boneco de treino">
          ` : ""}
          <label style="display:block;margin-top:8px"><input type="checkbox" id="f-tem-efeito"${ref.efeito ? " checked" : ""}> a lição altera fome/sede ao disparar</label>
          ${ref.efeito ? `
            <small style="display:block;color:#8a7a5a">Para o jogador SENTIR a regra: chegar esfomeado à sala de provisões.</small>
            <label>fome (0–100, vazio = não mexer)</label>
            <input id="f-ef-fome" type="number" min="0" max="100" value="${ref.efeito.fome ?? ""}" style="width:80px">
            <label>sede (0–100, vazio = não mexer)</label>
            <input id="f-ef-sede" type="number" min="0" max="100" value="${ref.efeito.sede ?? ""}" style="width:80px">
          ` : ""}
        </div>
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">Dispara uma vez por herói. Lição não aceita gatilho manual.</div>`;
      document.getElementById("f-emoji").onchange = e => { fal.emoji = e.target.value; render(); };
      document.getElementById("f-nome").onchange = e => { fal.nome = e.target.value; };
      document.getElementById("f-texto").onchange = e => { ref.texto = e.target.value; };
      document.getElementById("f-tipo").onchange = e => { tg.tipo = e.target.value; if (tg.tipo === "proximidade" && !tg.raio) tg.raio = 2; renderPanel(); };
      const fr = document.getElementById("f-raio");
      if (fr) fr.onchange = e => { tg.raio = Math.max(1, parseInt(e.target.value, 10) || 2); };
      document.getElementById("f-classe").onchange = e => { ref.classe = e.target.value || null; renderPanel(); };
      document.getElementById("f-ordem").onchange = e => {
        const n = parseInt(e.target.value, 10);
        ref.ordem = Number.isFinite(n) && n >= 1 ? n : null;
      };
      document.getElementById("f-tem-tarefa").onchange = e => {
        ref.tarefa = e.target.checked
          ? { tipo: "encerrar_turno", alvo: null, vezes: 1, texto_curto: "" }
          : null;
        renderPanel();
      };
      const tt = document.getElementById("f-tarefa-tipo");
      if (tt) tt.onchange = e => { ref.tarefa.tipo = e.target.value; ref.tarefa.alvo = null; renderPanel(); };
      const ta = document.getElementById("f-tarefa-alvo");
      if (ta) ta.onchange = e => {
        const v = e.target.value.trim();
        if (!v) { ref.tarefa.alvo = null; return; }
        ref.tarefa.alvo = LICAO_VERBOS_CASA.has(ref.tarefa.tipo)
          ? v.split(",").map(n => parseInt(n, 10) || 0).slice(0, 2)
          : v;
      };
      const tv = document.getElementById("f-tarefa-vezes");
      if (tv) tv.onchange = e => { ref.tarefa.vezes = Math.max(1, parseInt(e.target.value, 10) || 1); };
      document.getElementById("f-tem-efeito").onchange = e => {
        ref.efeito = e.target.checked ? { fome: 0, sede: 0 } : null;
        renderPanel();
      };
      for (const k of ["fome", "sede"]) {
        const el = document.getElementById("f-ef-" + k);
        if (el) el.onchange = e => {
          const v = e.target.value.trim();
          if (v === "") delete ref.efeito[k];
          else ref.efeito[k] = Math.max(0, Math.min(100, parseInt(v, 10) || 0));
        };
      }
      const tc = document.getElementById("f-tarefa-curto");
      if (tc) tc.onchange = e => { ref.tarefa.texto_curto = e.target.value; };
    } else if (k === "room") {
      panel.innerHTML = `<b>▦ Sala #${ref.id}</b>
        <label>role</label><select id="p-role">${opt(["entrance", "monster", "chest", "trap", "boss", "empty"].map(r => ({ v: r })), ref.role, o => o.v)}</select>
        <label><input type="checkbox" id="p-locked" ${ref.locked ? "checked" : ""}> trancada</label>
        <label style="display:block;margin-top:6px"><input type="checkbox" id="p-required" ${ref.required ? "checked" : ""}> sala obrigatória</label>
        ${ref.required ? `<label>modo</label><select id="p-reqmode"><option value="clear"${(ref.required_mode||"clear")==="clear"?" selected":""}>limpar (matar monstros)</option><option value="visit"${ref.required_mode==="visit"?" selected":""}>visitar (entrar)</option></select>` : ""}
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">portas: ${ref.doors.length}</div>
        <button id="p-del-room" style="margin-top:10px">🗑 Deletar sala</button>
        <div id="p-del-confirm" style="display:none;margin-top:6px">
          <div style="font-size:11px;color:#d8a0a0;margin-bottom:4px">Deletar a sala #${ref.id}?</div>
          <button id="p-del-keep">Deletar (manter chão)</button>
          <button id="p-del-clear">Deletar (limpar chão)</button>
        </div>`;
      document.getElementById("p-role").onchange = e => { ref.role = e.target.value; render(); };
      document.getElementById("p-locked").onchange = e => { ref.locked = e.target.checked; render(); };
      document.getElementById("p-required").onchange = e => { if (e.target.checked) { ref.required = true; if (!ref.required_mode) ref.required_mode = "clear"; } else { delete ref.required; delete ref.required_mode; } renderPanel(); };
      if (ref.required) { const _rm = document.getElementById("p-reqmode"); if (_rm) _rm.onchange = e => { ref.required_mode = e.target.value; }; }
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
      const wallMaterial = WALL_MATERIAL_IDS.has(ref.wall_material)
        ? ref.wall_material : (S.materiais[ref.pos[0] + "," + ref.pos[1]] || MAT_DEFAULT.parede);
      const wallMaterialOptions = WALL_MATERIALS.map(m =>
        `<option value="${m.id}"${m.id === wallMaterial ? " selected" : ""}>🧱 ${m.nome}</option>`).join("");
      panel.innerHTML = `<b>${ref.type === "illusion" ? "Parede ilusória" : "Passagem secreta"}</b>
        <div style="font-size:11px;color:#8a7a5a;margin:6px 0">${ref.type === "illusion" ? "Atravessável desde o início; somente o ladino a identifica durante Encontrar Armadilhas." : "Abre permanentemente quando suas decorações-chave forem ativadas."}</div>
        <label>textura da parede<select id="sp-wall-material">${wallMaterialOptions}</select></label>
        ${ref.type === "mechanism" ? `<label>ativação</label><select id="sp-mode"><option value="any"${ref.keys_mode === "any" ? " selected" : ""}>qualquer chave</option><option value="all"${ref.keys_mode === "all" ? " selected" : ""}>todas as chaves</option></select><label>decorações-chave</label><div id="sp-keys">${keys.length ? keys.map(d => `<label style="display:block"><input type="checkbox" value="${d.id}"${ref.key_decor_ids.includes(d.id) ? " checked" : ""}> ${decorMeta(d.type)?.nome || d.type} (${d.pos[0]},${d.pos[1]})</label>`).join("") : '<small>Marque uma decoração como objeto-chave primeiro.</small>'}</div>` : ""}`;
      document.getElementById("sp-wall-material").onchange = e => { ref.wall_material = e.target.value; render(); };
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
      const decorTrap = ref.trap || null;
      const trapOptions = (CAT.traps || []).map(t => ({ v: t.tipo, name: `${t.icone || '🪤'} ${t.nome || t.tipo}` }));
      const decorTrapMeta = decorTrap ? (CAT.traps.find(t => t.tipo === decorTrap.tipo) || {}) : null;
      const decorTrapDefaultDamage = trapPrimaryDamage(decorTrapMeta);
      const decorTrapDefaultDifficulty = decorTrapMeta?.dificuldade || "";
      const venomOptions = (CAT.venoms || []).map(v => ({ v: v.id, name: v.name || v.nome || v.id }));
      const [bw, bh] = decorBaseSize(ref);
      const vs0 = Array.isArray(ref.vscale) ? ref.vscale : [1, 1];
      const vo0 = Array.isArray(ref.voffset) ? ref.voffset : [0, 0];
      panel.innerHTML = `<b>${m.emoji || "🪑"} ${m.nome || ref.type}</b>
        <div style="color:#8a7a5a;font-size:11px">${m.size ? m.size[0] + "×" + m.size[1] : ""} ${m.alto ? "· alto (oclui visão)" : ""} ${m.pisavel ? "· pisável" : ""}</div>
        ${isWall ? `<div style="color:#8a7a5a;font-size:11px;margin-top:6px">Decoração de parede: clique em uma parede; girar troca a face voltada para uma área jogável.</div>` : ""}
        ${m.gira ? `<button id="d-rot">${isWall ? "trocar face" : "girar 90°"}</button>` : ""}
        ${!isWall ? `<button id="d-duplicate" style="margin-top:7px">⧉ Duplicar em casa adjacente</button>` : ""}
        <button id="d-brush" style="margin-top:7px">🖌️ Copiar e preencher área</button>
        <small style="display:block;color:#8a7a5a;margin-top:3px">Depois, arraste no mapa. Esc desativa o pincel.</small>
        <div id="d-duplicate-msg" style="font-size:11px;min-height:14px;color:#d8a0a0"></div>
        ${m.special === "fountain" ? `<label>cargas <input id="d-charges" type="number" min="0" value="${ref.charges ?? 0}"></label>` : ""}
        ${m.loot_capaz ? `<label style="display:block;margin-top:8px"><input type="checkbox" id="d-haslook" ${hasLoot ? "checked" : ""}> contém loot</label>` : ""}
        <label style="display:block;margin-top:8px"><input type="checkbox" id="d-chest-trap" ${ref.chest_trap_monster_type ? "checked" : ""}> baú-armadilha</label>
        ${ref.chest_trap_monster_type ? `<label>monstro que surge</label><select id="d-chest-monster">${opt(CAT.monsters.map(x => ({v:x.type,name:x.name})), ref.chest_trap_monster_type, o => o.v + " — " + o.name)}</select><small style="color:#8a7a5a">No primeiro clique, Reflexos CD 12; o loot só abre no próximo clique.</small>` : ""}
        <label style="display:block;margin-top:8px"><input type="checkbox" id="d-trap" ${decorTrap ? "checked" : ""}> contém armadilha</label>
        ${decorTrap ? `<label>armadilha</label><select id="d-trap-type">${opt(trapOptions, decorTrap.tipo, o => o.name)}</select>
          ${trapCharacteristicsHTML(decorTrapMeta, true, decorTrap)}
          <div class="trap-overrides compact">
            <b>⚙️ Ajustes desta armadilha</b>
            <label>CD do teste <input id="d-trap-cd" type="number" min="1" max="40" value="${decorTrap.dificuldade ?? decorTrapDefaultDifficulty}"></label>
            ${decorTrapDefaultDamage ? `<label>dano principal <input id="d-trap-damage" value="${trapText(decorTrap.dano ?? decorTrapDefaultDamage)}" placeholder="ex.: 2d6"></label><small id="d-trap-damage-help">Formato: 1d6, 2d8+2 ou 3.</small>` : `<small>Esta armadilha não possui dano direto configurável.</small>`}
            <small>Apague o valor para voltar ao padrão do catálogo.</small>
          </div>
          ${((CAT.traps.find(t => t.tipo === decorTrap.tipo) || {}).precisa_veneno || (CAT.traps.find(t => t.tipo === decorTrap.tipo) || {}).permite_veneno) ? `<label>veneno${(CAT.traps.find(t => t.tipo === decorTrap.tipo) || {}).permite_veneno && !(CAT.traps.find(t => t.tipo === decorTrap.tipo) || {}).precisa_veneno ? " (opcional)" : ""}</label><select id="d-trap-venom">${opt(venomOptions, decorTrap.veneno_id || "", o => o.name)}</select>` : ""}
          ${curseFieldsHTML(decorTrap, "d")}
          ${decorTrap.tipo === "armadilha_teletransporte" ? `<label>local de saída</label><div style="display:flex;gap:4px"><input id="d-trap-exit-x" type="number" min="0" max="${S.grid.w-1}" value="${decorTrap.saida?.[0] ?? ref.pos[0]}"><input id="d-trap-exit-y" type="number" min="0" max="${S.grid.h-1}" value="${decorTrap.saida?.[1] ?? ref.pos[1]}"></div><button id="d-pick-trap-out" style="margin-top:5px">📍 Selecionar saída no mapa</button><small id="d-trap-out-help" style="color:#8a7a5a">Escolha uma casa de chão no mapa.</small>` : ""}
          <small style="color:#8a7a5a">Dispara ao investigar. Encontrar Armadilhas revela o objeto e permite desarmá-lo.</small>` : ""}
        <label style="display:block;margin-top:8px"><input type="checkbox" id="d-key" ${ref.key_objective ? "checked" : ""}> objeto-chave <small>(conclui “Abrir o baú-chave” ao interagir)</small></label>
        <div id="d-loot" style="${hasLoot ? "" : "display:none"}">
          <label>ouro <input id="d-gold" type="number" min="0" value="${hasLoot ? (ref.loot.gold | 0) : 0}"></label>
          <label>itens</label>
          <div id="d-items">${hasLoot ? ref.loot.items.map((it, i) => `<div>${it.id} <button data-i="${i}" class="d-rm">×</button></div>`).join("") : ""}</div>
          ${lootItemSelectHTML("d-add")}
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
          <div style="font-size:11px;color:#8a7a5a;margin-top:8px">posição visual (não muda casas; use ±0,45 para encostar na parede)</div>
          <label>deslocamento X <input id="d-vox" type="number" min="-0.45" max="0.45" step="0.05" value="${vo0[0]}"></label>
          <label>deslocamento Y <input id="d-voy" type="number" min="-0.45" max="0.45" step="0.05" value="${vo0[1]}"></label>
          <button id="d-voreset" type="button" style="margin-top:5px">Centralizar objeto</button>
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
      document.getElementById("d-brush").onclick = () => { copySelectedDecor(); activateDecorBrush(); };
      if (m.special === "fountain") document.getElementById("d-charges").onchange = e => { ref.charges = Math.max(0, Number(e.target.value) | 0); };
      document.getElementById("d-key").onchange = e => { ref.key_objective = e.target.checked; };
      document.getElementById("d-chest-trap").onchange = e => { if (e.target.checked) ref.chest_trap_monster_type = (CAT.monsters[0] || {}).type; else delete ref.chest_trap_monster_type; renderPanel(); };
      if (ref.chest_trap_monster_type) document.getElementById("d-chest-monster").onchange = e => { ref.chest_trap_monster_type = e.target.value; };
      document.getElementById("d-trap").onchange = e => {
        if (e.target.checked) ref.trap = { tipo: (CAT.traps[0] || {}).tipo || "buraco" };
        else delete ref.trap;
        renderPanel();
      };
      if (decorTrap) {
        document.getElementById("d-trap-type").onchange = e => {
          ref.trap = { tipo: e.target.value };
          prepareCurseTrap(ref.trap, true);
          renderPanel();
        };
        const decorTrapCdInput = document.getElementById("d-trap-cd");
        if (decorTrapCdInput) decorTrapCdInput.onchange = e => {
          const raw = e.target.value.trim();
          if (!raw) delete ref.trap.dificuldade;
          else ref.trap.dificuldade = Math.max(1, Math.min(40, Number(raw) | 0));
          renderPanel(); render(); updateStatus();
        };
        const decorTrapDamageInput = document.getElementById("d-trap-damage");
        if (decorTrapDamageInput) decorTrapDamageInput.onchange = e => {
          const raw = e.target.value.trim().replace(/\s/g, "");
          const help = document.getElementById("d-trap-damage-help");
          if (!raw) { delete ref.trap.dano; renderPanel(); render(); updateStatus(); return; }
          if (!validTrapDamage(raw)) { if (help) help.textContent = "Valor inválido. Use 1d6, 2d8+2 ou 3."; e.target.focus(); return; }
          ref.trap.dano = raw; renderPanel(); render(); updateStatus();
        };
        const venom = document.getElementById("d-trap-venom"); if (venom) venom.onchange = e => { ref.trap.veneno_id = e.target.value; };
        wireCurseFields(ref.trap, "d", () => { renderPanel(); render(); });
        const exitX = document.getElementById("d-trap-exit-x"), exitY = document.getElementById("d-trap-exit-y");
        const updateExit = () => { ref.trap.saida = [Math.max(0, Number(exitX.value) | 0), Math.max(0, Number(exitY.value) | 0)]; };
        if (exitX && exitY) { exitX.onchange = updateExit; exitY.onchange = updateExit; }
        const pickTrapExit = document.getElementById("d-pick-trap-out");
        if (pickTrapExit) pickTrapExit.onclick = () => {
          S.teleportExitPick = ref.trap;
          const help = document.getElementById("d-trap-out-help");
          if (help) help.textContent = "Clique agora em uma casa de chão no mapa para definir a saída.";
        };
      }
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
      function applyVOffset() {
        const ox = Math.max(-.45, Math.min(.45, Number(document.getElementById("d-vox").value) || 0));
        const oy = Math.max(-.45, Math.min(.45, Number(document.getElementById("d-voy").value) || 0));
        if (ox === 0 && oy === 0) delete ref.voffset; else ref.voffset = [ox, oy];
        render();
      }
      document.getElementById("d-vox").onchange = applyVOffset;
      document.getElementById("d-voy").onchange = applyVOffset;
      document.getElementById("d-voreset").onclick = () => { delete ref.voffset; renderPanel(); render(); };
      const imgSel = document.getElementById("d-img-sel");
      const imgSt = document.getElementById("d-img-st");
      function fillImgOptions(list) {
        // O catálogo já conhece as artes nativas das decorações. Mesclá-las
        // aqui garante que a imagem continue disponível mesmo se a consulta
        // de PNGs do servidor estiver atrasada ou indisponível.
        const catalogImages = (CAT.decorations || [])
          .map(d => d && d.image).filter(Boolean);
        list = [...new Set([...(list || []), ...catalogImages])].sort();
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
        const help = document.getElementById("p-out-help") || document.getElementById("d-trap-out-help");
        if (help) help.textContent = "A saída precisa ser escolhida em uma casa de chão.";
        return;
      }
      S.teleportExitPick.saida = [x, y];
      S.teleportExitPick = null;
      renderPanel(); render(); updateStatus();
      return;
    }
    if (S.tool === "decor" && decorBrushActive && decorClipboard) {
      decorAreaPaint = { x0: x, y0: y, x1: x, y1: y };
      render();
    }
    else if (S.tool === "altura") {
      painting = true;
      paintElevation(x, y);
      render(); updateStatus();
    }
    else if (["wall", "floor", "door"].includes(S.tool)) {
      const areaMat = S.tool === "floor" ? S.matFloor : S.matWall;
      if (S.tool === "floor"
          && (areaMat === "rodamoinho" || areaMat === "rodamoinho_profundo")) {
        materialAreaPaint = { x0: x, y0: y, x1: x, y1: y, mat: areaMat };
        render(); drawMaterialAreaPreview(materialAreaPaint);
      } else {
        painting = true;
        (S.matFill && S.tool !== "door" ? paintMaterial : paintTile)(x, y);
        render(); updateStatus();
      }
    }
    else if (S.tool === "room") { roomDrag = { x0: x, y0: y, x1: x, y1: y }; }
    else if (["entrance", "hero_spawn", "exit", "prisoner", "monster", "chest", "trap", "decor", "secret_mechanism", "illusion_wall", "fala"].includes(S.tool)) { placeEntity(x, y); if (S.tool !== "decor") S.sel = entityAt(x, y); renderPanel(); render(); updateStatus(); }
    else if (S.tool === "erase") { eraseAt(x, y); S.sel = null; renderPanel(); render(); }
    else if (S.tool === "select") {
      // Clique repetido na mesma casa alterna entre as entidades empilhadas.
      S.sel = entityAt(x, y, true) || roomSel(x, y);
      // Entidades pontuais/decorações entram em modo arrasto (sala não).
       if (S.sel && S.sel.kind !== "room" && S.sel.kind !== "door" && S.sel.pos) {
        const anchor = S.sel.pos;
        _drag = { sel: S.sel, offX: x - anchor[0], offY: y - anchor[1],
                  origin: anchor.slice(), candidate: null, valid: true, moved: false };
      } else { _drag = null; }
      buildToolbar(); renderPanel(); render();
    }
  });

  function roomSel(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? { kind: "room", ref: r } : null;
  }

  function drawMaterialAreaPreview(area) {
    const x0 = Math.min(area.x0, area.x1), y0 = Math.min(area.y0, area.y1);
    const x1 = Math.max(area.x0, area.x1), y1 = Math.max(area.y0, area.y1);
    ctx.save();
    ctx.fillStyle = area.mat === "rodamoinho_profundo"
      ? "rgba(35, 100, 210, .30)" : "rgba(40, 190, 235, .30)";
    ctx.strokeStyle = area.mat === "rodamoinho_profundo"
      ? "#6fa8ed" : "#b8f5ff";
    ctx.lineWidth = 2;
    ctx.fillRect(x0 * CELL + 1, y0 * CELL + 1,
      (x1 - x0 + 1) * CELL - 2, (y1 - y0 + 1) * CELL - 2);
    ctx.strokeRect(x0 * CELL + 1, y0 * CELL + 1,
      (x1 - x0 + 1) * CELL - 2, (y1 - y0 + 1) * CELL - 2);
    ctx.restore();
  }

  board.addEventListener("mousemove", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    lastPointerCell = c;
    if (decorAreaPaint) {
      decorAreaPaint.x1 = c[0]; decorAreaPaint.y1 = c[1]; render(); return;
    }
    if (materialAreaPaint) {
      materialAreaPaint.x1 = c[0]; materialAreaPaint.y1 = c[1];
      render(); drawMaterialAreaPreview(materialAreaPaint); return;
    }
    if (_drag) {
      const ax = c[0] - _drag.offX, ay = c[1] - _drag.offY;
      _drag.candidate = [ax, ay];
      if (ax !== _drag.origin[0] || ay !== _drag.origin[1]) _drag.moved = true;
      _drag.valid = dropValid(_drag.sel, ax, ay);
      render();  // render() já desenha o preview via drawDragPreview()
      return;
    }
    if (painting) {
      if (S.tool === "altura") { paintElevation(c[0], c[1]); updateStatus(); }
      else if ((S.tool === "floor" || S.tool === "wall") && S.matFill) { paintMaterial(c[0], c[1]); updateStatus(); }
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
    if (materialAreaPaint) {
      const area = materialAreaPaint;
      materialAreaPaint = null;
      const x0 = Math.max(0, Math.min(area.x0, area.x1));
      const y0 = Math.max(0, Math.min(area.y0, area.y1));
      const x1 = Math.min(S.grid.w - 1, Math.max(area.x0, area.x1));
      const y1 = Math.min(S.grid.h - 1, Math.max(area.y0, area.y1));
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++)
        paintTile(x, y);
      renderPanel(); render(); updateStatus();
    }
    if (decorAreaPaint) {
      const area = decorAreaPaint;
      decorAreaPaint = null;
      pasteDecorArea(area);
      renderPanel(); render(); updateStatus();
    }
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
      saida_permitida: S.startMode !== "hero_spawns" && S.meta.saida_permitida !== false,
      start_mode: S.startMode,
      grid: { w: S.grid.w, h: S.grid.h },
      tiles: S.tiles.map(row => row.slice()),
      rooms: S.rooms.map(r => {
        const out = Object.assign({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: r.locked, doors: r.doors.map(d => d.slice()) }, r.required ? { required: true, required_mode: r.required_mode || "clear" } : {});
        const orientations = {};
        for (const d of r.doors) {
          const rot = doorRotationAt(d[0], d[1]);
          if (rot) orientations[doorKey(d[0], d[1])] = rot;
        }
        if (Object.keys(orientations).length) out.door_orientations = orientations;
        else delete out.door_orientations;
        return out;
      }),
      door_conditions: Object.fromEntries(Object.entries(S.doorConditions).map(([key, c]) => [key,
        c.type === "item" ? { type: "item", item_id: c.item_id || "" }
        : c.type === "licao" ? { type: "licao", licao_id: c.licao_id || "" }
        : { type: "decor", key_decor_ids: (c.key_decor_ids || []).slice(), keys_mode: c.keys_mode === "all" ? "all" : "any" }])),
      entrance: S.startMode === "entrance" && S.entrance ? { x: S.entrance.x, y: S.entrance.y } : null,
      hero_spawns: S.heroSpawns.map(s => ({ class_id: s.class_id, pos: s.pos.slice(), room_id: s.room_id ?? null })),
      exit: S.exit ? { x: S.exit.x, y: S.exit.y } : null,
      monsters: S.monsters.map(m => {
        const o = { type: m.type, pos: m.pos.slice(), room_id: m.room_id, boss: !!m.boss, target: !!m.target };
        if (Array.isArray(m.vscale) && (m.vscale[0] !== 1 || m.vscale[1] !== 1)) o.vscale = [m.vscale[0], m.vscale[1]];
        if (monsterCanFly(m)) {
          const meta = monsterFlightMeta(m) || {};
          const defaultAltitude = altitudeClamp(meta.altura_inicial, 2);
          const defaultMaxAltitude = altitudeClamp(meta.altura_max, 10);
          const defaultCanChangeAltitude = meta.pode_alterar_altura !== undefined ? !!meta.pode_alterar_altura : true;
          const defaultAltitudeMoveCost = Math.max(1, Math.min(10, Number(meta.custo_mov_altura) || 1));
          const defaultIgnoreFlightObstacles = !!meta.ignora_obstaculos_voo;
          const altitude = altitudeClamp(m.altura, defaultAltitude);
          const maxAltitude = Math.max(altitude, altitudeClamp(m.altura_max, defaultMaxAltitude));
          if (altitude !== defaultAltitude) o.altura = altitude;
          if (maxAltitude !== defaultMaxAltitude) o.altura_max = maxAltitude;
          if (m.pode_alterar_altura !== undefined && !!m.pode_alterar_altura !== defaultCanChangeAltitude)
            o.pode_alterar_altura = !!m.pode_alterar_altura;
          if (m.custo_mov_altura !== undefined && Number(m.custo_mov_altura) !== defaultAltitudeMoveCost)
            o.custo_mov_altura = Math.max(1, Math.min(10, Number(m.custo_mov_altura) | 0));
          if (m.ignora_obstaculos_voo !== undefined && !!m.ignora_obstaculos_voo !== defaultIgnoreFlightObstacles)
            o.ignora_obstaculos_voo = !!m.ignora_obstaculos_voo;
        }
        return o;
      }),
      chests: S.chests.map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: c.items.map(i => ({ id: i.id })), key_objective: !!c.key_objective })),
      traps: S.traps.map(t => {
        const o = { tipo: t.tipo, pos: t.pos.slice() };
        if (t.dificuldade != null) o.dificuldade = Math.max(1, Math.min(40, t.dificuldade | 0));
        if (t.dano != null && validTrapDamage(t.dano)) o.dano = String(t.dano).replace(/\s/g, "");
        if (t.veneno_id) o.veneno_id = t.veneno_id;
        if (t.saida) o.saida = t.saida.slice();
        if (t.tipo === "armadilha_maldicao") {
          o.curse_mode = t.curse_mode || "aleatoria";
          if (o.curse_mode === "especifica" && t.curse_id) o.curse_id = t.curse_id;
          if (o.curse_mode === "aleatoria") o.curse_category = t.curse_category || "leve";
        }
        if (t.image) o.image = t.image;
        return o;
      }),
      decorations: S.decorations.map(d => {
        const o = { id: d.id, type: d.type, pos: d.pos.slice(), facing: d.facing.slice() };
        o.loot = d.loot ? { gold: d.loot.gold | 0, items: d.loot.items.map(i => ({ id: i.id })) } : null;
        o.key_objective = !!d.key_objective;
        if (d.chest_trap_monster_type) o.chest_trap_monster_type = d.chest_trap_monster_type;
        if (d.trap?.tipo) {
          o.trap = { tipo: d.trap.tipo };
          if (d.trap.dificuldade != null) o.trap.dificuldade = Math.max(1, Math.min(40, d.trap.dificuldade | 0));
          if (d.trap.dano != null && validTrapDamage(d.trap.dano)) o.trap.dano = String(d.trap.dano).replace(/\s/g, "");
          if (d.trap.veneno_id) o.trap.veneno_id = d.trap.veneno_id;
          if (Array.isArray(d.trap.saida)) o.trap.saida = d.trap.saida.slice();
          if (d.trap.tipo === "armadilha_maldicao") {
            o.trap.curse_mode = d.trap.curse_mode || "aleatoria";
            if (o.trap.curse_mode === "especifica" && d.trap.curse_id) o.trap.curse_id = d.trap.curse_id;
            if (o.trap.curse_mode === "aleatoria") o.trap.curse_category = d.trap.curse_category || "leve";
          }
        }
        const m = decorMeta(d.type);
        if (m && m.special === "fountain") o.charges = d.charges | 0;
        if (d.image) o.image = d.image;
        // Override de tamanho por-objeto (editor-only; o servidor ignora estes campos).
        if (Array.isArray(d.size) && d.size.length === 2) o.size = [d.size[0] | 0, d.size[1] | 0];
        if (Array.isArray(d.vscale) && (d.vscale[0] !== 1 || d.vscale[1] !== 1)) o.vscale = [d.vscale[0], d.vscale[1]];
        if (Array.isArray(d.voffset) && (d.voffset[0] !== 0 || d.voffset[1] !== 0)) o.voffset = [d.voffset[0], d.voffset[1]];
        return o;
      }),
      secret_passages: S.secretPassages.map(p => ({
        id: p.id, type: p.type, pos: p.pos.slice(),
        ...(WALL_MATERIAL_IDS.has(p.wall_material) ? { wall_material: p.wall_material } : {}),
        key_decor_ids: p.key_decor_ids.slice(), keys_mode: p.keys_mode,
      })),
      falas: S.falas.map(f => {
        const tg = f.trigger || {};
        const t = { tipo: tg.tipo || "proximidade" };
        if (t.tipo === "proximidade") t.raio = tg.raio || 2;
        const out = { id: f.id, pos: f.pos.slice(), falante: { nome: (f.falante || {}).nome || "", emoji: (f.falante || {}).emoji || "" }, texto: f.texto || "", trigger: t };
        if (f.classe) out.classe = f.classe;
        if (f.ordem != null) out.ordem = f.ordem;
        if (f.tarefa && f.tarefa.tipo) out.tarefa = {
          tipo: f.tarefa.tipo,
          ...(f.tarefa.alvo != null && f.tarefa.alvo !== "" ? { alvo: f.tarefa.alvo } : {}),
          vezes: Math.max(1, parseInt(f.tarefa.vezes, 10) || 1),
          texto_curto: f.tarefa.texto_curto || "",
        };
        const ef = {};
        for (const k of ["fome", "sede"])
          if (f.efeito && f.efeito[k] != null && f.efeito[k] !== "")
            ef[k] = Math.max(0, Math.min(100, parseInt(f.efeito[k], 10) || 0));
        if (Object.keys(ef).length) out.efeito = ef;
        return out;
      }),
      master_reinforcements: S.masterReinforcements.map(r => ({ type: r.type, count: r.count })),
      expected_party: { heroes: S.expectedParty.heroes, level: S.expectedParty.level },
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id, ...(S.prisoner.image ? { image: S.prisoner.image } : {}) } : null,
      materiais: { ...S.materiais },
      elevacoes: Object.fromEntries(Object.entries(S.elevacoes)
        .filter(([key, value]) => value && Number.isInteger(value))
        .map(([key, value]) => [key, Math.max(ELEVACAO_MIN, Math.min(ELEVACAO_MAX, value))])),
      transicao_altura: S.transicaoAltura === "declive" ? "declive" : "rampa",
      objectives: {
        primary: { type: S.objectives.primary.type, xp: S.objectives.primary.xp | 0,
                   reward: { gold: (S.objectives.primary.reward.gold | 0), items: S.objectives.primary.reward.items.map(i => ({ id: i.id })) } },
        secondary: S.objectives.secondary.map(s => ({ type: s.type, xp: s.xp | 0,
                   reward: { gold: (s.reward.gold | 0), items: s.reward.items.map(i => ({ id: i.id })) } })),
      },
    };
  }

  function reachableFloors(limit, start) {
    const origin = start || (S.entrance && [S.entrance.x, S.entrance.y]);
    if (!origin) return 0;
    const [x, y] = origin;
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
    const curses = new Set((CAT.curses || []).map(c => c.id));
    const venoms = new Set(CAT.venoms.map(v => v.id));
    const roomIds = new Set(S.rooms.map(r => r.id));
    const isWall = (p) => !p || S.tiles[p[1]]?.[p[0]] === WALL || S.tiles[p[1]]?.[p[0]] === undefined;
    if (S.startMode === "entrance") {
      if (!S.entrance) e.push("falta a entrada");
      else if (S.tiles[S.entrance.y][S.entrance.x] !== FLOOR) e.push("entrada precisa estar em chão");
    } else {
      if (!S.heroSpawns.length) e.push("falta ao menos uma posição inicial de herói");
      const classes = new Set();
      for (const s of S.heroSpawns) {
        if (!HERO_SPAWN_META.some(h => h.id === s.class_id)) e.push(`classe inicial inválida: ${s.class_id}`);
        if (classes.has(s.class_id)) e.push(`classe inicial duplicada: ${s.class_id}`);
        classes.add(s.class_id);
        if (isWall(s.pos)) e.push(`posição inicial em parede: ${s.pos}`);
      }
    }
    if (S.rooms.length === 0) e.push("precisa de ao menos uma sala");
    if (S.startMode === "entrance" && !S.rooms.some(r => r.role === "entrance")) e.push("nenhuma sala com role 'entrance'");
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
      if (CAT.traps.find(c => c.tipo === t.tipo)?.apenas_objeto) e.push(`${t.tipo} só pode ser colocado em uma decoração/objeto`);
      if (isWall(t.pos)) e.push(`armadilha em parede: ${t.pos}`);
      if (t.dificuldade != null && (!Number.isInteger(t.dificuldade) || t.dificuldade < 1 || t.dificuldade > 40)) e.push(`${t.tipo} com CD inválida: ${t.dificuldade}`);
      if (t.dano != null && !validTrapDamage(t.dano)) e.push(`${t.tipo} com dano inválido: ${t.dano}`);
      if ((t.tipo === "fosso_envenenado" || t.tipo === "armadilha_dardos_envenenados") && !venoms.has(t.veneno_id)) e.push(`${t.tipo} sem veneno válido`);
      if (t.tipo === "armadilha_teletransporte" && (!Array.isArray(t.saida) || S.tiles[t.saida[1]]?.[t.saida[0]] !== FLOOR)) e.push("armadilha de teletransporte sem saída em chão");
      if (t.tipo === "armadilha_maldicao") {
        const mode = t.curse_mode || "aleatoria";
        if (!["especifica", "aleatoria"].includes(mode)) e.push("armadilha_maldicao com modo inválido");
        if (mode === "especifica" && !curses.has(t.curse_id)) e.push("armadilha_maldicao sem maldição válida");
        if (mode === "aleatoria" && !["leve", "media", "grave"].includes(t.curse_category || "leve")) e.push("armadilha_maldicao com gravidade inválida");
      }
    }
    if (S.prisoner && isWall(S.prisoner.pos)) e.push("prisioneiro em parede");
    for (const r of S.rooms) for (const d of r.doors) if (S.tiles[d[1]]?.[d[0]] !== DOOR) e.push(`porta declarada não é tile DOOR: ${d}`);
    if (S.startMode === "entrance") {
      if (reachableFloors(6) < 6) e.push("menos de 6 casas de chão alcançáveis da entrada");
    } else {
      for (const s of S.heroSpawns) if (reachableFloors(1, s.pos) < 1) e.push(`posição inicial inacessível: ${s.class_id}`);
    }
    if (S.objectives.primary.type === "all_heroes_at_exit" && !S.exit)
      e.push("o objetivo all_heroes_at_exit exige uma saída");
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
      if (d.trap) {
        if (!traps.has(d.trap.tipo)) e.push("armadilha de decoração inválida");
        if (d.trap.dificuldade != null && (!Number.isInteger(d.trap.dificuldade) || d.trap.dificuldade < 1 || d.trap.dificuldade > 40)) e.push(`${d.trap.tipo} na decoração com CD inválida`);
        if (d.trap.dano != null && !validTrapDamage(d.trap.dano)) e.push(`${d.trap.tipo} na decoração com dano inválido`);
        if (["fosso_envenenado", "armadilha_dardos_envenenados"].includes(d.trap.tipo) && !venoms.has(d.trap.veneno_id)) e.push(`${d.trap.tipo} na decoração sem veneno válido`);
        if (d.trap.tipo === "armadilha_teletransporte" && (!Array.isArray(d.trap.saida) || S.tiles[d.trap.saida[1]]?.[d.trap.saida[0]] !== FLOOR)) e.push("armadilha de teletransporte na decoração sem saída em chão");
        if (d.trap.tipo === "armadilha_maldicao") {
          const mode = d.trap.curse_mode || "aleatoria";
          if (!["especifica", "aleatoria"].includes(mode)) e.push("armadilha de decoração com modo de maldição inválido");
          if (mode === "especifica" && !curses.has(d.trap.curse_id)) e.push("armadilha de decoração sem maldição válida");
          if (mode === "aleatoria" && !["leve", "media", "grave"].includes(d.trap.curse_category || "leve")) e.push("armadilha de decoração com gravidade inválida");
        }
      }
    }
    const decorIds = new Set(S.decorations.map(d => d.id));
    for (const [key, c] of Object.entries(S.doorConditions || {})) {
      const pos = key.split(",").map(Number);
      if (pos.length !== 2 || !Number.isInteger(pos[0]) || !Number.isInteger(pos[1]) || S.tiles[pos[1]]?.[pos[0]] !== DOOR) {
        e.push(`condição de abertura em porta inválida: ${key}`); continue;
      }
      if (!c || !["item", "decor", "licao"].includes(c.type)) { e.push(`tipo de condição de porta inválido em ${key}`); continue; }
      if (c.type === "item" && !items.has(c.item_id)) e.push(`item-chave inválido na porta ${key}: ${c.item_id}`);
      if (c.type === "licao" && !S.falas.some(f => f.id === c.licao_id && f.tarefa && f.tarefa.tipo))
        e.push(`porta ${key} aponta para uma lição que não existe ou não tem tarefa`);
      if (c.type === "decor") {
        if (!Array.isArray(c.key_decor_ids) || !c.key_decor_ids.length || c.key_decor_ids.some(id => !decorIds.has(id)))
          e.push(`porta ${key} sem objetos-chave válidos`);
        if (Array.isArray(c.key_decor_ids) && new Set(c.key_decor_ids).size !== c.key_decor_ids.length)
          e.push(`porta ${key} repete um objeto-chave`);
        if (!["any", "all"].includes(c.keys_mode || "any")) e.push(`modo de objetos-chave inválido na porta ${key}`);
        if (Array.isArray(c.key_decor_ids)) for (const id of c.key_decor_ids) {
          const d = S.decorations.find(x => x.id === id);
          if (d && !d.key_objective) e.push(`objeto ${id} da porta ${key} precisa estar marcado como objeto-chave`);
        }
      }
    }
    const passageIds = new Set();
    for (const p of S.secretPassages) {
      if (!p.id || passageIds.has(p.id)) e.push("id de passagem secreta duplicado ou vazio");
      passageIds.add(p.id);
      if (!p.pos || S.tiles[p.pos[1]]?.[p.pos[0]] !== WALL) e.push("passagem secreta deve ficar em uma parede");
      if (p.wall_material != null && !WALL_MATERIAL_IDS.has(p.wall_material)) e.push("textura de passagem secreta inválida");
      if (!Array.isArray(p.key_decor_ids) || p.key_decor_ids.some(id => !decorIds.has(id))) e.push("passagem com decoração-chave inválida");
      if (p.type === "mechanism" && !p.key_decor_ids.length) e.push("passagem secreta sem decoração-chave");
    }
    const ordensLicao = new Set();
    for (const f of S.falas) {
      if (isWall(f.pos)) e.push(`fala de NPC em parede: ${f.pos}`);
      if (!(f.texto || "").trim()) e.push("fala de NPC sem texto");
      const tipo = (f.trigger || {}).tipo;
      if (!["proximidade", "sala", "manual"].includes(tipo)) e.push(`fala de NPC com gatilho inválido: ${tipo}`);
      const ehLicao = !!(f.classe || f.tarefa || f.efeito || f.ordem != null);
      if (!ehLicao) continue;
      if (tipo === "manual") e.push(`lição ${f.id} não pode ter gatilho manual`);
      if (f.classe && !HERO_SPAWN_META.some(h => h.id === f.classe)) e.push(`lição ${f.id} com classe inválida: ${f.classe}`);
      if (f.ordem != null) {
        const chave = `${f.classe || ""}#${f.ordem}`;
        if (ordensLicao.has(chave)) e.push(`duas lições com a mesma ordem ${f.ordem} para ${f.classe || "todas as classes"}`);
        ordensLicao.add(chave);
      }
      if (f.tarefa) {
        if (!LICAO_VERBOS.some(o => o.v === f.tarefa.tipo)) e.push(`lição ${f.id} com tarefa inválida: ${f.tarefa.tipo}`);
        if (!(f.tarefa.texto_curto || "").trim()) e.push(`lição ${f.id} sem texto curto`);
        if (LICAO_VERBOS_CASA.has(f.tarefa.tipo) && f.tarefa.alvo && !Array.isArray(f.tarefa.alvo)) e.push(`lição ${f.id}: alvo deveria ser uma casa x,y`);
      }
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
    const profundo = new Set(Object.entries(S.materiais)
      .filter(([, mid]) => mid === "rodamoinho_profundo")
      .map(([key]) => key));
    if (profundo.size && ![...profundo].some(key => {
      const [x, y] = key.split(",").map(Number);
      return profundo.has(`${x + 1},${y}`)
        && profundo.has(`${x},${y + 1}`)
        && profundo.has(`${x + 1},${y + 1}`);
    })) e.push("rodamoinho profundo precisa ocupar no mínimo uma área contínua de 2x2 casas");
    for (const [key, value] of Object.entries(S.elevacoes)) {
      const p = key.split(",").map(Number);
      if (p.length !== 2 || !Number.isInteger(p[0]) || !Number.isInteger(p[1])
          || p[0] < 0 || p[1] < 0 || p[0] >= S.grid.w || p[1] >= S.grid.h) {
        e.push(`elevação fora do grid em ${key}`); continue;
      }
      if (![FLOOR, DOOR].includes(S.tiles[p[1]]?.[p[0]]))
        e.push(`elevação em casa que não é chão: ${key}`);
      if (!Number.isInteger(value) || value < ELEVACAO_MIN || value > ELEVACAO_MAX)
        e.push(`elevação inválida em ${key}`);
    }
    if (!["rampa", "declive"].includes(S.transicaoAltura))
      e.push("transição de altura inválida");
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
               ambiente: ["penumbra", "masmorra", "ar_livre"].includes(obj.ambiente) ? obj.ambiente : "masmorra",
               // Ausente = permitida: masmorras salvas antes deste campo não mudam de comportamento.
               saida_permitida: obj.saida_permitida !== false };
    S.grid = { w: obj.grid.w, h: obj.grid.h };
    S.tiles = obj.tiles.map(row => row.slice());
    S.rooms = (obj.rooms || []).map(r => Object.assign({ id: r.id, x: r.x, y: r.y, w: r.w, h: r.h, role: r.role, locked: !!r.locked, doors: (r.doors || []).map(d => d.slice()) }, r.required ? { required: true, required_mode: r.required_mode === "visit" ? "visit" : "clear" } : {}));
    S.doorConditions = {};
    for (const [key, c] of Object.entries(obj.door_conditions || {})) {
      if (!/^\d+,\d+$/.test(key) || !c || typeof c !== "object") continue;
      if (c.type === "item" && typeof c.item_id === "string") S.doorConditions[key] = { type: "item", item_id: c.item_id };
      else if (c.type === "licao" && typeof c.licao_id === "string") S.doorConditions[key] = { type: "licao", licao_id: c.licao_id };
      else if (c.type === "decor") S.doorConditions[key] = { type: "decor", key_decor_ids: Array.isArray(c.key_decor_ids) ? c.key_decor_ids.slice() : [], keys_mode: c.keys_mode === "all" ? "all" : "any" };
    }
    S.doorRotations = {};
    const loadDoorRotations = (source) => {
      if (!source || typeof source !== "object") return;
      for (const [key, value] of Object.entries(source)) {
        const n = Number(value);
        if (/^\d+,\d+$/.test(key) && Number.isFinite(n)) S.doorRotations[key] = ((Math.round(n) % 4) + 4) % 4;
      }
    };
    loadDoorRotations(obj.door_orientations);
    for (const r of (obj.rooms || [])) loadDoorRotations(r.door_orientations);
    S.nextRoomId = S.rooms.reduce((m, r) => Math.max(m, r.id + 1), 0);
    S.startMode = obj.start_mode === "hero_spawns" || (!obj.entrance && Array.isArray(obj.hero_spawns) && obj.hero_spawns.length)
      ? "hero_spawns" : "entrance";
    S.entrance = obj.entrance || null;
    S.heroSpawns = (obj.hero_spawns || []).map(s => ({
      class_id: s.class_id, pos: Array.isArray(s.pos) ? s.pos.slice() : [0, 0], room_id: s.room_id ?? null,
    }));
    if (S.startMode === "hero_spawns") S.entrance = null;
    S.exit = obj.exit || null;
    S.prisoner = obj.prisoner || null;
    S.monsters = (obj.monsters || []).map(m => ({
      type: m.type, pos: m.pos.slice(), room_id: m.room_id ?? null, boss: !!m.boss, target: !!m.target,
      ...(Array.isArray(m.vscale) && m.vscale.length === 2 ? { vscale: [Number(m.vscale[0]), Number(m.vscale[1])] } : {}),
      ...(m.altura !== undefined ? { altura: altitudeClamp(m.altura, 2) } : {}),
      ...(m.altura_max !== undefined ? { altura_max: altitudeClamp(m.altura_max, 10) } : {}),
      ...(m.pode_alterar_altura !== undefined ? { pode_alterar_altura: !!m.pode_alterar_altura } : {}),
      ...(m.custo_mov_altura !== undefined ? { custo_mov_altura: Math.max(1, Math.min(10, Number(m.custo_mov_altura) | 0)) } : {}),
      ...(m.ignora_obstaculos_voo !== undefined ? { ignora_obstaculos_voo: !!m.ignora_obstaculos_voo } : {}),
    }));
    S.chests = (obj.chests || []).map(c => ({ pos: c.pos.slice(), gold: c.gold | 0, items: (c.items || []).map(i => ({ id: i.id })), key_objective: !!c.key_objective }));
    S.traps = (obj.traps || []).map(t => {
      const o = { tipo: t.tipo, pos: t.pos.slice() };
      if (t.dificuldade != null) o.dificuldade = Number(t.dificuldade) | 0;
      if (t.dano != null && validTrapDamage(t.dano)) o.dano = String(t.dano).replace(/\s/g, "");
      if (t.veneno_id) o.veneno_id = t.veneno_id;
      if (t.saida) o.saida = t.saida.slice();
      if (t.tipo === "armadilha_maldicao") {
        o.curse_mode = t.curse_mode || "aleatoria";
        if (t.curse_id) o.curse_id = t.curse_id;
        if (t.curse_category) o.curse_category = t.curse_category;
      }
      if (t.image) o.image = t.image;
      return o;
    });
    // Mapas criados por versões anteriores podiam ter IDs repetidos após
    // apagar/colar objetos. Repara somente a identidade interna ao abrir —
    // posição, tipo e todas as configurações da decoração são preservados.
    const rawDecors = obj.decorations || [];
    const usedDecorIds = new Set();
    let loadNextDecorId = rawDecors.reduce((next, d) => {
      const m = /^decor_(\d+)$/.exec((d && d.id) || "");
      return m ? Math.max(next, Number(m[1]) + 1) : next;
    }, 0);
    const uniqueLoadedDecorId = (id) => {
      if (typeof id === "string" && id && !usedDecorIds.has(id)) {
        usedDecorIds.add(id); return id;
      }
      while (usedDecorIds.has("decor_" + loadNextDecorId)) loadNextDecorId++;
      const generated = "decor_" + loadNextDecorId++;
      usedDecorIds.add(generated); return generated;
    };
    S.decorations = rawDecors.map((d, i) => ({
      id: uniqueLoadedDecorId(d.id || ("decor_" + i)),
      type: d.type, pos: d.pos.slice(), facing: (d.facing || [0, 1]).slice(),
      loot: d.loot ? { gold: d.loot.gold | 0, items: (d.loot.items || []).map(i => ({ id: i.id })) } : null,
      key_objective: !!d.key_objective,
      ...(d.chest_trap_monster_type ? { chest_trap_monster_type: d.chest_trap_monster_type } : {}),
      ...(d.trap?.tipo ? { trap: {
        tipo: d.trap.tipo,
        ...(d.trap.dificuldade != null ? { dificuldade: Number(d.trap.dificuldade) | 0 } : {}),
        ...(d.trap.dano != null && validTrapDamage(d.trap.dano) ? { dano: String(d.trap.dano).replace(/\s/g, "") } : {}),
        ...(d.trap.veneno_id ? { veneno_id: d.trap.veneno_id } : {}),
        ...(Array.isArray(d.trap.saida) ? { saida: d.trap.saida.slice() } : {}),
        ...(d.trap.tipo === "armadilha_maldicao" ? {
          curse_mode: d.trap.curse_mode || "aleatoria",
          ...(d.trap.curse_id ? { curse_id: d.trap.curse_id } : {}),
          ...(d.trap.curse_category ? { curse_category: d.trap.curse_category } : {}),
        } : {}),
      } } : {}),
      ...(d.charges !== undefined ? { charges: d.charges | 0 } : {}),
      // Decorações catalogadas de parede sempre recuperam sua arte padrão,
      // inclusive em arquivos antigos que ainda não guardavam `image`.
      ...((d.image || decorMeta(d.type)?.image) ? { image: d.image || decorMeta(d.type).image } : {}),
      ...(Array.isArray(d.size) && d.size.length === 2 ? { size: [d.size[0] | 0, d.size[1] | 0] } : {}),
      ...(Array.isArray(d.vscale) && d.vscale.length === 2 ? { vscale: [Number(d.vscale[0]), Number(d.vscale[1])] } : {}),
      ...(Array.isArray(d.voffset) && d.voffset.length === 2 ? { voffset: [Number(d.voffset[0]), Number(d.voffset[1])] } : {}),
    }));
    // O maior sufixo existente, e não o tamanho da lista, define o próximo ID.
    // Depois de apagar ou colar em um mapa antigo, os dois valores podem divergir.
    S.nextDecorId = S.decorations.reduce((next, d) => {
      const m = /^decor_(\d+)$/.exec(d.id || "");
      return m ? Math.max(next, Number(m[1]) + 1) : next;
    }, 0);
    S.secretPassages = (obj.secret_passages || []).map((p, i) => ({
      id: p.id || ("passage_" + i),
      type: p.type === "illusion" ? "illusion" : "mechanism",
      pos: p.pos.slice(),
      ...(WALL_MATERIAL_IDS.has(p.wall_material) ? { wall_material: p.wall_material } : {}),
      key_decor_ids: (p.key_decor_ids || []).slice(),
      keys_mode: p.keys_mode === "all" ? "all" : "any",
    }));
    S.nextPassageId = S.secretPassages.length;
    S.falas = (obj.falas || []).map((f, i) => {
      const tg = f.trigger || {};
      const tipo = ["proximidade", "sala", "manual"].includes(tg.tipo) ? tg.tipo : "proximidade";
      const trigger = { tipo };
      if (tipo === "proximidade") trigger.raio = Math.max(1, parseInt(tg.raio, 10) || 2);
      const tar = f.tarefa && f.tarefa.tipo ? {
        tipo: f.tarefa.tipo,
        alvo: f.tarefa.alvo ?? null,
        vezes: Math.max(1, parseInt(f.tarefa.vezes, 10) || 1),
        texto_curto: f.tarefa.texto_curto || "",
      } : null;
      return { id: f.id || ("fala_" + i), pos: f.pos.slice(), falante: { nome: (f.falante || {}).nome || "", emoji: (f.falante || {}).emoji || "🧙" }, texto: f.texto || "", trigger,
               classe: f.classe || null, ordem: f.ordem ?? null, tarefa: tar,
               efeito: (f.efeito && typeof f.efeito === "object") ? { ...f.efeito } : null };
    });
    S.nextFalaId = S.falas.length;
    S.masterReinforcements = (obj.master_reinforcements || [])
      .filter(r => r && r.type)
      .map(r => ({ type: r.type, count: Math.max(1, parseInt(r.count, 10) || 1) }));
    S.expectedParty = (function (ep) {
      ep = ep || {};
      return { heroes: Math.max(1, Math.min(6, parseInt(ep.heroes, 10) || 4)),
               level:  Math.max(1, parseInt(ep.level, 10) || 1) };
    })(obj.expected_party);
    S.materiais = (obj.materiais && typeof obj.materiais === "object") ? { ...obj.materiais } : {};
    S.elevacoes = {};
    for (const [key, value] of Object.entries((obj.elevacoes && typeof obj.elevacoes === "object") ? obj.elevacoes : {})) {
      const p = key.split(",").map(Number), n = Number(value);
      if (p.length === 2 && p.every(Number.isInteger) && p[0] >= 0 && p[1] >= 0
          && p[0] < S.grid.w && p[1] < S.grid.h && [FLOOR, DOOR].includes(S.tiles[p[1]]?.[p[0]])
          && Number.isInteger(n) && n >= ELEVACAO_MIN && n <= ELEVACAO_MAX && n !== 0)
        S.elevacoes[key] = n;
    }
    S.transicaoAltura = obj.transicao_altura === "declive" ? "declive" : "rampa";
    S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };
    if (!S.objectives.primary) S.objectives.primary = { type: "kill_all" };
    if (!Array.isArray(S.objectives.secondary)) S.objectives.secondary = [];
    normalizeObjective(S.objectives.primary, true);
    S.objectives.secondary.forEach(s => normalizeObjective(s, false));
    S.sel = null;
    document.getElementById("m-id").value = S.meta.id;
    document.getElementById("m-name").value = S.meta.name;
    document.getElementById("m-ambiente").value = S.meta.ambiente || "masmorra";
    document.getElementById("m-saida").checked = S.meta.saida_permitida !== false;
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
    S.meta.saida_permitida = document.getElementById("m-saida").checked;
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
  document.getElementById("btn-test-dungeon").onclick = async () => {
    if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.createTestDungeon) {
      alert("Inicie o servidor para testar a masmorra."); return;
    }
    const valid = updateStatus();
    if (!valid.ok) { alert("Corrija a masmorra antes de testar:\n- " + valid.erros.join("\n- ")); return; }
    // Abre durante o gesto de clique; abrir só depois do await é bloqueado como
    // popup pela maioria dos navegadores.
    const abaTeste = window.open("about:blank", "_blank");
    const btn = document.getElementById("btn-test-dungeon"); btn.disabled = true; btn.textContent = "🧪 Abrindo teste…";
    try {
      const test = await window.EDITOR_SAVE.createTestDungeon(buildJSON());
      // Mesmo motivo da prévia: em file:// o cliente não consegue baixar .glb
      // (XHR bloqueado) e todo monstro vira peão genérico.
      const query = "?teste_masmorra=" + encodeURIComponent(test.token);
      const destino = window.EDITOR_CLIENTE ? window.EDITOR_CLIENTE.url(query)
                                            : "../index.html" + query;
      if (abaTeste) abaTeste.location.href = destino;
      else window.location.assign(destino);
    } catch (err) {
      if (abaTeste) abaTeste.close();
      alert("Não foi possível iniciar o teste: " + err.message);
    }
    finally { btn.disabled = false; btn.textContent = "🧪 Testar como Mestre"; }
  };
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
    const oldElevacoes = { ...S.elevacoes };
    initGrid(w, h);
    for (let y = 0; y < Math.min(h, oh); y++) for (let x = 0; x < Math.min(w, ow); x++) S.tiles[y][x] = old[y][x];
    for (const [key, value] of Object.entries(oldElevacoes)) {
      const [x, y] = key.split(",").map(Number);
      if (x >= 0 && y >= 0 && x < w && y < h && [FLOOR, DOOR].includes(S.tiles[y][x])) S.elevacoes[key] = value;
    }
    render();
  };

  function setTab(tab) {
    const dung = tab === "masmorra";
    const bestiary = tab === "bestiario";
    const monsterEditor = tab === "editor_monstros";
    const itemsEditor = tab === "editor_itens";
    const cityEditor = tab === "cidade";
    const worldEditor = tab === "mapa_mundi";
    const scenesEditor = tab === "cenas";
    document.getElementById("dungeon-controls").style.display = dung ? "" : "none";
    document.getElementById("toolbar").style.display = dung ? "" : "none";
    document.getElementById("workspace").style.display = dung ? "" : "none";
    document.getElementById("campaign-controls").style.display = tab === "campanha" ? "" : "none";
    document.getElementById("campaign-view").style.display = tab === "campanha" ? "" : "none";
    document.getElementById("bestiary-view").style.display = bestiary ? "" : "none";
    document.getElementById("monster-editor-view").style.display = monsterEditor ? "" : "none";
    document.getElementById("items-editor-view").style.display = itemsEditor ? "" : "none";
    document.getElementById("city-editor-view").style.display = cityEditor ? "" : "none";
    document.getElementById("world-editor-view").style.display = worldEditor ? "" : "none";
    document.getElementById("scenes-editor-view").style.display = scenesEditor ? "" : "none";
    document.getElementById("tab-masmorra").classList.toggle("active", dung);
    document.getElementById("tab-bestiario").classList.toggle("active", bestiary);
    document.getElementById("tab-editor-monstros").classList.toggle("active", monsterEditor);
    document.getElementById("tab-editor-itens").classList.toggle("active", itemsEditor);
    document.getElementById("tab-cidade").classList.toggle("active", cityEditor);
    document.getElementById("tab-mapa-mundi").classList.toggle("active", worldEditor);
    document.getElementById("tab-campanha").classList.toggle("active", tab === "campanha");
    document.getElementById("tab-cenas").classList.toggle("active", scenesEditor);
    if (dung) { render(); renderPanel(); }
    else if (bestiary && window.EDITOR_BESTIARY) window.EDITOR_BESTIARY.render();
    else if (monsterEditor && window.EDITOR_MONSTER_EDITOR) window.EDITOR_MONSTER_EDITOR.render();
    else if (itemsEditor && window.EDITOR_ITEMS_EDITOR) window.EDITOR_ITEMS_EDITOR.render();
    else if (cityEditor && window.EDITOR_CITY) window.EDITOR_CITY.render();
    else if (worldEditor && window.EDITOR_WORLD) window.EDITOR_WORLD.render();
    else if (tab === "campanha" && window.EDITOR_CAMPAIGN) window.EDITOR_CAMPAIGN.renderCampaign();
    else if (scenesEditor && window.EDITOR_SCENES) window.EDITOR_SCENES.load();
  }
  window.setTab = setTab;
  document.getElementById("tab-masmorra").onclick = () => setTab("masmorra");
  document.getElementById("tab-bestiario").onclick = () => setTab("bestiario");
  document.getElementById("tab-editor-monstros").onclick = () => setTab("editor_monstros");
  document.getElementById("tab-editor-itens").onclick = () => setTab("editor_itens");
  document.getElementById("tab-cidade").onclick = () => setTab("cidade");
  document.getElementById("tab-mapa-mundi").onclick = () => setTab("mapa_mundi");
  document.getElementById("tab-campanha").onclick = () => setTab("campanha");
  document.getElementById("tab-cenas").onclick = () => setTab("cenas");

  // Expor para verificação no console / tasks seguintes.
  window.EDITOR = { S, catalog: CAT, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, deleteRoom, entityAt, doorLink, doorUnlink, validarEditor, buildJSON, loadJSON, save, updateStatus, WALL, FLOOR, DOOR, decorMeta, decorEffSize, decorTilesAt, decorTiles, rotateFacing, rotateDecorPending, doorRotationAt, rotateDoorAt, rotateDoorSelected, decorFits, placeDecor, decorBaseSize, decorEffSizeOf, decorWouldFit, tilesFor, dropValid, moveSelTo, copySelectedDecor, pasteDecorAt, duplicateDecorAdjacent };

  initGrid(S.grid.w, S.grid.h);
  buildToolbar();
  render();
  renderPanel();
})();
