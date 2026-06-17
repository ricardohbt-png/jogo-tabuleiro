# Editor de Masmorras — Fase 2 (Editor Visual) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Um editor visual offline (`tools/editor.html`) que desenha masmorras e salva/carrega o JSON no formato da Fase 1, com catálogos gerados do `server.py`.

**Architecture:** Tudo em `tools/`, aberto no navegador. Um gerador Python (`export_catalog.py`) extrai os catálogos do `server.py` para `editor_catalog.js` (global, sem `fetch`). `editor.html` + `editor.css` + `editor.js` (scripts simples, sem ES modules) implementam grid, ferramentas, painel, validação em JS e IO por download/upload. Zero mudança no `server.py`.

**Tech Stack:** Python 3 (gerador + teste estilo `tools/test_*.py` com `check()`), Vanilla JS + `<canvas>` 2D (editor). Sem Node, sem bundler. Verificação do editor: servir o repo com `python -m http.server 8077` (config "http" em `.claude/launch.json`) e dirigir o navegador.

**Spec:** `docs/superpowers/specs/2026-06-17-editor-masmorras-fase2-design.md`

---

## Notas de design (ler antes de começar)

- **Formato-alvo:** idêntico ao da Fase 1. Referência viva: `dungeons/test_fase1.json` e a função `server.validar_dungeon` / `server.load_authored_dungeon`. WALL=0, FLOOR=1, DOOR=2. Tile `(x,y)` = `tiles[y][x]`.
- **Catálogos no `server.py`** (campos confirmados): `MONSTER_DEFS` (30 itens; cada um com `type`,`name`,`emoji`; só `dragon` tem `boss:True`), `CHEST_ITEMS` (todos com `id`,`name`,`emoji`), `ARMADILHAS` (dict por `tipo`; cada meta tem `nome`,`icone`; `fosso_envenenado` tem `custo_veneno`), `VENENOS` (dict por id; cada um com `nome`).
- **Sem ES modules:** `editor.html` carrega `editor_catalog.js` e `editor.js` por `<script src>`. Use globais (`window.EDITOR_CATALOG`, `window.EDITOR`). `import`/`type=module` quebra em `file://`.
- **Verificação JS sem Node:** não há `node`. Para checar sintaxe/comportamento, sirva o repo (`python -m http.server 8077`, já em `.claude/launch.json` como "http") e abra `http://localhost:8077/tools/editor.html`; cheque o console e dirija a lógica pura via `EDITOR.*` no console. O `editor.js` deve expor `window.EDITOR = { S, validarEditor, buildJSON, loadJSON, doorLink, doorUnlink, placeEntity, render, initGrid }` para isso.
- **Convenção de teste Python:** ver `tools/test_persistencia_masmorra.py` — `sys.path.insert` da raiz, `import server`, helper `check(nome,cond)`, `sys.exit(1 if FAIL else 0)`, e `sys.stdout.reconfigure(encoding="utf-8")` no topo (Windows).
- **Commits:** cada task termina com `git add <arquivos exatos>` (nunca `git add -A`).

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `tools/export_catalog.py` | Gera `editor_catalog.js` a partir dos catálogos do `server.py` |
| `tools/editor_catalog.js` | (gerado) `window.EDITOR_CATALOG = {monsters, items, traps, venoms}` |
| `tools/test_export_catalog.py` | Teste: coerência catálogo↔servidor + arquivo escrito |
| `tools/editor.html` | Shell: barra, `<canvas>`, painel; inclui os dois `.js` |
| `tools/editor.css` | Estilos do editor |
| `tools/editor.js` | Estado, render, ferramentas, painel, validação, IO |

---

## Task 1: Gerador de catálogo + teste (Python, TDD)

**Files:**
- Create: `tools/export_catalog.py`
- Create: `tools/test_export_catalog.py`
- Gera: `tools/editor_catalog.js`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_export_catalog.py`:

```python
"""Teste do gerador de catálogo do editor (Fase 2).
Roda da raiz: python tools/test_export_catalog.py"""
import sys, os, json, re
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
import tools.export_catalog as ec

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    print("\n[1] build_catalog")
    cat = ec.build_catalog()
    tipos_srv = {m["type"] for m in server.MONSTER_DEFS}
    ids_srv   = {i["id"] for i in server.CHEST_ITEMS}
    check("todo monstro exportado existe no servidor",
          all(m["type"] in tipos_srv for m in cat["monsters"]))
    check("exporta todos os monstros", len(cat["monsters"]) == len(server.MONSTER_DEFS))
    check("monstro tem type/name/emoji",
          all(all(k in m for k in ("type", "name", "emoji")) for m in cat["monsters"]))
    check("dragon marcado como boss",
          any(m["type"] == "dragon" and m.get("boss") for m in cat["monsters"]))
    check("todo item exportado existe no servidor",
          all(i["id"] in ids_srv for i in cat["items"]))
    check("toda armadilha exportada existe no servidor",
          all(t["tipo"] in server.ARMADILHAS for t in cat["traps"]))
    check("fosso_envenenado precisa_veneno=True",
          any(t["tipo"] == "fosso_envenenado" and t["precisa_veneno"] for t in cat["traps"]))
    check("todo veneno exportado existe no servidor",
          all(v["id"] in server.VENENOS for v in cat["venoms"]))
    check("veneno tem name", all(v.get("name") for v in cat["venoms"]))

    print("\n[2] write_catalog_js")
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_catalog.js")
    ec.write_catalog_js(destino)
    with open(destino, encoding="utf-8") as f:
        txt = f.read()
    check("arquivo começa com a atribuição global",
          txt.lstrip().startswith("window.EDITOR_CATALOG"))
    m = re.search(r"window\.EDITOR_CATALOG\s*=\s*(\{.*\});", txt, re.S)
    check("payload é JSON válido", bool(m) and isinstance(json.loads(m.group(1)), dict))

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_export_catalog.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.export_catalog'` (ou `tools` sem `__init__`). Se aparecer erro de import de `tools`, crie `tools/__init__.py` vazio no Step 3.

- [ ] **Step 3: Implementar o gerador**

Criar `tools/export_catalog.py`:

```python
"""Gera tools/editor_catalog.js a partir dos catálogos autoritativos do server.py.
Rode da raiz quando os catálogos do servidor mudarem:  python tools/export_catalog.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def build_catalog():
    """Extrai só os campos que o editor precisa. Retorna dict serializável."""
    monsters = []
    for m in server.MONSTER_DEFS:
        entry = {"type": m["type"], "name": m["name"], "emoji": m.get("emoji", "")}
        if m.get("boss"):
            entry["boss"] = True
        monsters.append(entry)
    items = [{"id": i["id"], "name": i["name"], "emoji": i.get("emoji", "")}
             for i in server.CHEST_ITEMS]
    traps = []
    for tipo, meta in server.ARMADILHAS.items():
        traps.append({
            "tipo": tipo, "nome": meta["nome"], "icone": meta.get("icone", ""),
            "precisa_veneno": tipo == "fosso_envenenado" or bool(meta.get("custo_veneno")),
        })
    venoms = [{"id": vid, "name": meta["nome"]} for vid, meta in server.VENENOS.items()]
    return {"monsters": monsters, "items": items, "traps": traps, "venoms": venoms}

def write_catalog_js(destino):
    """Escreve o catálogo como atribuição JS (carregável via <script> em file://)."""
    cat = build_catalog()
    payload = json.dumps(cat, ensure_ascii=False, indent=2)
    txt = ("// GERADO por tools/export_catalog.py — não editar à mão.\n"
           "// Rode `python tools/export_catalog.py` para regenerar.\n"
           "window.EDITOR_CATALOG = " + payload + ";\n")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(txt)
    return destino

if __name__ == "__main__":
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor_catalog.js")
    write_catalog_js(destino)
    print(f"editor_catalog.js gerado em {destino}")
```

Se o Step 2 acusou falta de `tools` como pacote, criar também `tools/__init__.py` vazio:

```python
```

(arquivo vazio)

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_export_catalog.py`
Expected: PASS — `=== 11 passou, 0 falhou ===`. Confirme que `tools/editor_catalog.js` foi criado.

- [ ] **Step 5: Commit**

```bash
git add tools/export_catalog.py tools/test_export_catalog.py tools/editor_catalog.js
git commit -m "feat: gerador de catalogo do editor (export_catalog -> editor_catalog.js) (Fase 2)"
```

> Se criou `tools/__init__.py`, inclua-o no `git add`.

---

## Task 2: Shell do editor (HTML + CSS)

**Files:**
- Create: `tools/editor.html`
- Create: `tools/editor.css`

> Verificação é visual (sem teste automatizado). Sirva o repo e abra a página.

- [ ] **Step 1: Criar `tools/editor.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Editor de Masmorras — Legends for Hire</title>
<link rel="stylesheet" href="editor.css">
</head>
<body>
  <header id="topbar">
    <span class="brand">🗺️ Editor de Masmorras</span>
    <label>id <input id="m-id" value="nova_masmorra" size="14"></label>
    <label>nome <input id="m-name" value="Nova Masmorra" size="16"></label>
    <label>grid
      <input id="g-w" type="number" min="1" max="60" value="16" style="width:48px">×
      <input id="g-h" type="number" min="1" max="60" value="12" style="width:48px">
    </label>
    <button id="btn-resize">Aplicar grid</button>
    <span class="spacer"></span>
    <button id="btn-load">Carregar</button>
    <input id="file-input" type="file" accept="application/json,.json" hidden>
    <button id="btn-save">Salvar</button>
  </header>

  <div id="toolbar"></div>

  <main id="workspace">
    <div id="canvas-wrap">
      <canvas id="board" width="448" height="336"></canvas>
    </div>
    <aside id="panel"><em>Selecione uma ferramenta e desenhe.</em></aside>
  </main>

  <footer id="statusbar"><span id="status"></span></footer>

  <script src="editor_catalog.js"></script>
  <script src="editor.js"></script>
</body>
</html>
```

- [ ] **Step 2: Criar `tools/editor.css`**

```css
* { box-sizing: border-box; }
body { margin:0; font-family: system-ui, Arial, sans-serif; background:#2a2118; color:#e8dcc0; }
#topbar { display:flex; align-items:center; gap:10px; padding:8px 12px; background:#1d1812; border-bottom:1px solid #4a3c28; flex-wrap:wrap; }
#topbar .brand { font-weight:bold; color:#d9b061; }
#topbar .spacer { flex:1; }
#topbar label { font-size:12px; color:#b9a87f; }
#topbar input { background:#33291c; color:#e8dcc0; border:1px solid #4a3c28; border-radius:4px; padding:3px 5px; }
button { background:#33291c; color:#e8dcc0; border:1px solid #5a4830; border-radius:5px; padding:5px 9px; cursor:pointer; font-size:12px; }
button:hover { background:#4a3c28; }
button.active { background:#d9b061; color:#1d1812; border-color:#d9b061; }
#toolbar { display:flex; gap:5px; padding:8px 12px; background:#241d14; border-bottom:1px solid #4a3c28; flex-wrap:wrap; align-items:center; }
#toolbar .group-label { font-size:11px; color:#8a7a5a; margin:0 2px; }
#toolbar .sep { width:1px; align-self:stretch; background:#4a3c28; margin:0 4px; }
#workspace { display:flex; gap:12px; padding:12px; align-items:flex-start; }
#canvas-wrap { background:#1d1812; border:1px solid #4a3c28; border-radius:6px; padding:6px; }
#board { display:block; image-rendering:pixelated; cursor:crosshair; }
#panel { width:240px; min-height:200px; background:#1d1812; border:1px solid #4a3c28; border-radius:6px; padding:10px 12px; font-size:13px; }
#panel label { display:block; font-size:11px; color:#b9a87f; margin-top:8px; }
#panel select, #panel input { width:100%; background:#33291c; color:#e8dcc0; border:1px solid #4a3c28; border-radius:4px; padding:4px; margin-top:2px; }
#panel input[type=checkbox] { width:auto; }
#statusbar { padding:6px 12px; background:#1d1812; border-top:1px solid #4a3c28; font-size:12px; min-height:26px; }
.status-ok { color:#7ec86a; }
.status-err { color:#e08a6a; }
```

- [ ] **Step 3: Servir e abrir**

Run (background): `python -m http.server 8077` (da raiz do repo).
Abrir `http://localhost:8077/tools/editor.html`. Confirme: a barra de topo, a (vazia ainda) toolbar, o canvas e o painel aparecem; o console acusa só o erro esperado de `editor.js` ainda não existir (se você ainda não o criou) — neste ponto `editor.js` não existe, então um 404 dele é aceitável. O importante: `editor_catalog.js` carrega sem erro (`window.EDITOR_CATALOG` definido — verifique no console).

- [ ] **Step 4: Commit**

```bash
git add tools/editor.html tools/editor.css
git commit -m "feat: shell do editor de masmorras (HTML+CSS) (Fase 2)"
```

---

## Task 3: Núcleo do `editor.js` — estado, grid, render

**Files:**
- Create: `tools/editor.js`

- [ ] **Step 1: Criar `tools/editor.js` com estado + render + toolbar**

```javascript
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
```

- [ ] **Step 2: Verificar no navegador**

Garanta que `python -m http.server 8077` está rodando. Abra `http://localhost:8077/tools/editor.html`.
Verifique: a toolbar mostra os botões agrupados (tiles / entidades / ações); o canvas mostra um grid 16×12 todo escuro (paredes); o console **sem erros**; no console, `EDITOR.S.grid` retorna `{w:16,h:12}` e `EDITOR.S.tiles.length` é 12.

- [ ] **Step 3: Commit**

```bash
git add tools/editor.js
git commit -m "feat: nucleo do editor.js (estado, grid, render, toolbar) (Fase 2)"
```

---

## Task 4: Pintura de tiles (parede / chão / porta)

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Adicionar manuseio de mouse e pintura**

Em `tools/editor.js`, ANTES da linha `window.EDITOR = {`, inserir:

```javascript
  function cellFromEvent(ev) {
    const r = board.getBoundingClientRect();
    const x = Math.floor((ev.clientX - r.left) / (r.width / S.grid.w));
    const y = Math.floor((ev.clientY - r.top) / (r.height / S.grid.h));
    if (x < 0 || y < 0 || x >= S.grid.w || y >= S.grid.h) return null;
    return [x, y];
  }

  function paintTile(x, y) {
    if (S.tool === "wall") S.tiles[y][x] = WALL;
    else if (S.tool === "floor") S.tiles[y][x] = FLOOR;
    else if (S.tool === "door") { S.tiles[y][x] = DOOR; doorLink(x, y); }
  }

  let painting = false;
  board.addEventListener("mousedown", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    if (["wall", "floor", "door"].includes(S.tool)) {
      painting = true; paintTile(c[0], c[1]); render();
    }
  });
  board.addEventListener("mousemove", (ev) => {
    if (!painting) return;
    const c = cellFromEvent(ev); if (!c) return;
    paintTile(c[0], c[1]); render();
  });
  window.addEventListener("mouseup", () => { painting = false; });
```

> `doorLink` será definido na Task 5; por ora, adicione um stub temporário logo acima de `paintTile` para o arquivo não quebrar:
> ```javascript
>   function doorLink(x, y) {}
>   function doorUnlink(x, y) {}
> ```
> A Task 5 substitui esses stubs pela implementação real.

- [ ] **Step 2: Expor `cellFromEvent`/`paintTile` no objeto EDITOR**

Substituir a linha `window.EDITOR = { S, initGrid, render, buildToolbar, WALL, FLOOR, DOOR };` por:

```javascript
  window.EDITOR = { S, initGrid, render, buildToolbar, cellFromEvent, paintTile, doorLink, doorUnlink, WALL, FLOOR, DOOR };
```

- [ ] **Step 3: Verificar no navegador**

Recarregue `http://localhost:8077/tools/editor.html`. Selecione "chão" e arraste no grid → células ficam claras. Selecione "parede" → voltam a escuro. Selecione "porta" → fica âmbar. Console sem erros. No console: após pintar, `EDITOR.S.tiles` reflete os valores.

- [ ] **Step 4: Commit**

```bash
git add tools/editor.js
git commit -m "feat: pintura de tiles (parede/chao/porta) no editor (Fase 2)"
```

---

## Task 5: Ferramenta de sala + porta com vínculo automático

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Implementar salas (drag-rect) e vínculo porta↔sala**

Em `tools/editor.js`, SUBSTITUIR os stubs `function doorLink(x,y){}` e `function doorUnlink(x,y){}` por:

```javascript
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
```

- [ ] **Step 2: Adicionar criação de sala por arraste**

Em `tools/editor.js`, dentro do bloco de mouse, ESTENDER os handlers. Substituir o handler `mousedown` existente por:

```javascript
  let roomDrag = null;
  board.addEventListener("mousedown", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    if (["wall", "floor", "door"].includes(S.tool)) {
      painting = true; paintTile(c[0], c[1]); render();
    } else if (S.tool === "room") {
      roomDrag = { x0: c[0], y0: c[1], x1: c[0], y1: c[1] };
    }
  });
```

E ESTENDER o `mousemove` (substituir o handler por):

```javascript
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
```

E ESTENDER o `mouseup` (substituir o handler `window ... mouseup` por):

```javascript
  window.addEventListener("mouseup", () => {
    painting = false;
    if (roomDrag) {
      const x = Math.min(roomDrag.x0, roomDrag.x1), y = Math.min(roomDrag.y0, roomDrag.y1);
      const w = Math.abs(roomDrag.x1 - roomDrag.x0) + 1, h = Math.abs(roomDrag.y1 - roomDrag.y0) + 1;
      if (w >= 2 && h >= 2) {
        const role = S.rooms.length === 0 ? "entrance" : "monster";
        S.rooms.push({ id: S.nextRoomId++, x, y, w, h, role, locked: role !== "entrance", doors: [] });
      }
      roomDrag = null; render();
    }
  });
```

- [ ] **Step 2b: Adicionar o pintar-chão automático da sala (opcional mas útil)**

Dentro do `if (w >= 2 && h >= 2) {` acima, ANTES do `S.rooms.push`, preencher a sala com chão:

```javascript
        for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) S.tiles[j][i] = FLOOR;
```

- [ ] **Step 3: Verificar no navegador (vínculo porta↔sala)**

Recarregue. Selecione "sala", arraste um retângulo 5×4 → aparece o contorno + miolo vira chão + rótulo `entrance#0`. Selecione "porta", clique numa casa da borda da sala → vira âmbar. No console:
`EDITOR.S.rooms[0].doors` deve conter a casa que você clicou (vínculo automático).
Teste o desfazer: selecione "apagar"… (apagar de porta vem na Task 6; por ora valide só o link via console chamando `EDITOR.doorUnlink(x,y)` e conferindo que sai de `rooms[0].doors`).

- [ ] **Step 4: Commit**

```bash
git add tools/editor.js
git commit -m "feat: ferramenta de sala + porta com vinculo automatico (Fase 2)"
```

---

## Task 6: Entidades + seleção + painel de propriedades

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Implementar colocação de entidades, seleção e apagar**

Em `tools/editor.js`, ANTES de `window.EDITOR = {`, inserir:

```javascript
  function entityAt(x, y) {
    if (S.entrance && S.entrance.x === x && S.entrance.y === y) return { kind: "entrance", pos: [x, y] };
    if (S.exit && S.exit.x === x && S.exit.y === y) return { kind: "exit", pos: [x, y] };
    if (S.prisoner && S.prisoner.pos[0] === x && S.prisoner.pos[1] === y) return { kind: "prisoner", ref: S.prisoner, pos: [x, y] };
    const find = (arr, kind) => { const r = arr.find(e => e.pos[0] === x && e.pos[1] === y); return r ? { kind, ref: r, pos: [x, y] } : null; };
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
    S.tiles[y][x] = WALL;
  }
```

- [ ] **Step 2: Ligar essas ações no `mousedown`**

Substituir o handler `mousedown` (de novo) por:

```javascript
  board.addEventListener("mousedown", (ev) => {
    const c = cellFromEvent(ev); if (!c) return;
    const [x, y] = c;
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; paintTile(x, y); render(); }
    else if (S.tool === "room") { roomDrag = { x0: x, y0: y, x1: x, y1: y }; }
    else if (["entrance", "exit", "prisoner", "monster", "chest", "trap"].includes(S.tool)) { placeEntity(x, y); S.sel = entityAt(x, y); renderPanel(); render(); }
    else if (S.tool === "erase") { eraseAt(x, y); S.sel = null; renderPanel(); render(); }
    else if (S.tool === "select") { S.sel = entityAt(x, y) || roomSel(x, y); renderPanel(); render(); }
  });

  function roomSel(x, y) {
    const r = S.rooms.find(r => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
    return r ? { kind: "room", ref: r } : null;
  }
```

- [ ] **Step 3: Implementar o painel de propriedades**

ANTES de `window.EDITOR = {`, inserir:

```javascript
  const panel = document.getElementById("panel");
  function opt(list, val, fmt) { return list.map(o => `<option value="${o.v}"${o.v === val ? " selected" : ""}>${fmt(o)}</option>`).join(""); }

  function renderPanel() {
    if (!S.sel) { panel.innerHTML = "<em>Nada selecionado. Escolha uma ferramenta e desenhe.</em>"; return; }
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
        <div style="margin-top:8px;color:#8a7a5a;font-size:11px">portas: ${ref.doors.length}</div>`;
      document.getElementById("p-role").onchange = e => { ref.role = e.target.value; render(); };
      document.getElementById("p-locked").onchange = e => { ref.locked = e.target.checked; render(); };
    } else if (k === "prisoner") {
      panel.innerHTML = `<b>🧍 Prisioneiro</b><div style="color:#8a7a5a;font-size:11px">sala ${ref.room_id ?? "—"}</div>`;
    } else {
      panel.innerHTML = `<b>${k}</b>`;
    }
  }
```

- [ ] **Step 4: Atualizar o objeto EDITOR e a init**

Substituir a linha do `window.EDITOR = {...}` por:

```javascript
  window.EDITOR = { S, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, entityAt, doorLink, doorUnlink, WALL, FLOOR, DOOR };
```

E logo após `render();` no final do IIFE, adicionar `renderPanel();`.

- [ ] **Step 5: Verificar no navegador**

Recarregue. Desenhe uma sala, pinte chão, selecione "monstro" e clique numa casa de chão → emoji aparece e o painel mostra o select de tipo (povoado pelo catálogo). Troque o tipo → emoji muda. Coloque um baú, adicione um item pelo select. Coloque "armadilha", troque para `fosso_envenenado` → aparece o select de veneno. "selecionar" numa sala mostra role/locked. "apagar" remove. Console sem erros.

- [ ] **Step 6: Commit**

```bash
git add tools/editor.js
git commit -m "feat: entidades + selecao + painel de propriedades no editor (Fase 2)"
```

---

## Task 7: Validação em JS + status ao vivo

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Implementar `validarEditor` + `buildJSON`**

ANTES de `window.EDITOR = {`, inserir:

```javascript
  function buildJSON() {
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
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id } : null,
      objectives: S.objectives,
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
    return { ok: e.length === 0, erros: e };
  }

  function updateStatus() {
    const v = validarEditor();
    const el = document.getElementById("status");
    if (v.ok) { el.className = "status-ok"; el.textContent = "✓ válida — pronta para salvar"; }
    else { el.className = "status-err"; el.textContent = "✗ " + v.erros.length + " problema(s): " + v.erros.slice(0, 4).join("; ") + (v.erros.length > 4 ? " …" : ""); }
    return v;
  }
```

- [ ] **Step 2: Chamar `updateStatus()` após cada mutação**

No final de cada handler que muta o estado, já chamamos `render()`. Para centralizar, ENVOLVER: substituir a função `render` final por uma que também atualiza o status — adicionar ao FIM da função `render()` (antes de fechar `}`):

```javascript
    if (document.getElementById("status")) updateStatus();
```

- [ ] **Step 3: Atualizar EDITOR e init**

Substituir a linha `window.EDITOR = {...}` por:

```javascript
  window.EDITOR = { S, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, entityAt, doorLink, doorUnlink, validarEditor, buildJSON, updateStatus, WALL, FLOOR, DOOR };
```

- [ ] **Step 4: Verificar no navegador**

Recarregue. A barra de status mostra problemas (sem entrada, sem sala…). Desenhe uma sala `entrance`, pinte chão, ponha a entrada numa casa de chão → o status deve virar verde "✓ válida". Coloque um monstro em parede → status vermelho aponta. No console: `EDITOR.validarEditor()` retorna `{ok, erros}` coerente; `EDITOR.buildJSON()` retorna o dict do esquema.

- [ ] **Step 5: Commit**

```bash
git add tools/editor.js
git commit -m "feat: validacao em JS + status ao vivo no editor (Fase 2)"
```

---

## Task 8: Salvar (download) + carregar (upload) + meta/objetivos

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Implementar IO e ligação dos controles de topo**

ANTES de `window.EDITOR = {`, inserir:

```javascript
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
    S.objectives = obj.objectives || { primary: { type: "kill_all" }, secondary: [] };
    S.sel = null;
    document.getElementById("m-id").value = S.meta.id;
    document.getElementById("m-name").value = S.meta.name;
    document.getElementById("g-w").value = S.grid.w;
    document.getElementById("g-h").value = S.grid.h;
    render(); renderPanel();
  }

  function save() {
    S.meta.id = document.getElementById("m-id").value.trim() || "masmorra";
    S.meta.name = document.getElementById("m-name").value.trim() || "Masmorra";
    const v = updateStatus();
    if (!v.ok) { alert("Masmorra inválida:\n- " + v.erros.join("\n- ")); return; }
    const blob = new Blob([JSON.stringify(buildJSON(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = S.meta.id + ".json";
    document.body.appendChild(a); a.click(); a.remove();
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
```

- [ ] **Step 1b: Painel da masmorra (meta + objetivos) quando nada está selecionado**

Em `tools/editor.js`, na função `renderPanel` (Task 6), SUBSTITUIR a linha do ramo sem seleção
`if (!S.sel) { panel.innerHTML = "<em>Nada selecionado. Escolha uma ferramenta e desenhe.</em>"; return; }`
por:

```javascript
    if (!S.sel) {
      const OBJ = ["kill_target", "kill_all", "reach_exit", "open_key_chest", "rescue_prisoner"];
      const o = S.objectives;
      panel.innerHTML = `<b>🗺️ Masmorra</b>
        <label>objetivo principal</label>
        <select id="o-prim">${OBJ.map(t => `<option value="${t}"${o.primary.type === t ? " selected" : ""}>${t}</option>`).join("")}</select>
        <label>objetivos secundários</label>
        <div id="o-sec">${o.secondary.map((s, i) => `<div><select data-i="${i}" class="o-secsel">${OBJ.map(t => `<option value="${t}"${s.type === t ? " selected" : ""}>${t}</option>`).join("")}</select> <button data-i="${i}" class="o-rm">×</button></div>`).join("")}</div>
        <button id="o-add">+ secundário</button>`;
      document.getElementById("o-prim").onchange = e => { o.primary.type = e.target.value; };
      document.getElementById("o-add").onclick = () => { o.secondary.push({ type: "rescue_prisoner" }); renderPanel(); };
      panel.querySelectorAll(".o-secsel").forEach(sel => sel.onchange = e => { o.secondary[Number(e.target.dataset.i)].type = e.target.value; });
      panel.querySelectorAll(".o-rm").forEach(b => b.onclick = () => { o.secondary.splice(Number(b.dataset.i), 1); renderPanel(); });
      return;
    }
```

Isso dá a UI dos objetivos (que `buildJSON`/`loadJSON` já serializam). Recarregue e confirme
que, sem nada selecionado, o painel mostra o select do objetivo principal e o +/− dos secundários.

- [ ] **Step 2: Atualizar EDITOR**

Substituir a linha `window.EDITOR = {...}` por:

```javascript
  window.EDITOR = { S, initGrid, render, renderPanel, buildToolbar, cellFromEvent, paintTile, placeEntity, eraseAt, entityAt, doorLink, doorUnlink, validarEditor, buildJSON, loadJSON, save, updateStatus, WALL, FLOOR, DOOR };
```

- [ ] **Step 3: Verificar ida-e-volta no navegador**

Recarregue. Clique "Carregar" e escolha `dungeons/test_fase1.json` → o editor desenha as duas salas, corredor, porta, monstros (goblin/esqueleto), baú, armadilha, entrada. O status fica verde. Clique "Salvar" → baixa `test_fase1.json`. Console sem erros.

No console, teste o round-trip do build:
```js
EDITOR.loadJSON(await (await fetch('/dungeons/test_fase1.json')).json());
JSON.stringify(EDITOR.buildJSON()).length > 0;
```
(à página servida em :8077 o fetch de `/dungeons/...` funciona.)

- [ ] **Step 4: Commit**

```bash
git add tools/editor.js
git commit -m "feat: salvar/carregar (download/upload) + resize de grid no editor (Fase 2)"
```

---

## Task 9: Verificação ponta-a-ponta (round-trip com o jogo) + teste do formato

**Files:**
- Create: `tools/test_roundtrip_editor.py`

- [ ] **Step 1: Teste de formato — um JSON do editor passa em validar_dungeon**

Criar `tools/test_roundtrip_editor.py`:

```python
"""Ida-e-volta: o formato que o editor produz é aceito pelo servidor.
Usa dungeons/test_fase1.json como referência do formato do editor.
Roda da raiz: python tools/test_roundtrip_editor.py"""
import sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase1.json"), encoding="utf-8") as f:
        d = json.load(f)
    ok, msg = server.validar_dungeon(d)
    check(f"masmorra de referência valida ({msg})", ok is True)
    # campos que o editor sempre emite estão presentes
    for k in ("schema_version", "grid", "tiles", "rooms", "entrance",
              "monsters", "chests", "traps", "objectives"):
        check(f"campo '{k}' presente", k in d)
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste**

Run: `python tools/test_roundtrip_editor.py`
Expected: PASS — `=== 10 passou, 0 falhou ===`.

- [ ] **Step 3: Verificação ponta-a-ponta no navegador (manual via preview)**

1. Servir o repo: `python -m http.server 8077` (e, em separado, `python server.py` para o jogo na 8765).
2. Abrir `http://localhost:8077/tools/editor.html`. Desenhar uma masmorra NOVA pequena: uma sala `entrance` (5×4) destrancada com a entrada dentro; uma sala `monster` trancada ligada por um corredor com uma porta; 1 monstro, 1 baú, 1 armadilha. Status verde. Salvar → baixa `<id>.json`.
3. Copiar o arquivo baixado para `dungeons/`.
4. Abrir o jogo em `http://localhost:8765/index.html`, criar sala, no dropdown selecionar a masmorra nova, escolher classe, iniciar, entrar. Confirmar que ela carrega com o grid/entidades desenhados (fechando o ciclo com a Fase 1).
5. Console do editor e do jogo sem erros.

- [ ] **Step 4: Commit**

```bash
git add tools/test_roundtrip_editor.py
git commit -m "test: ida-e-volta do formato do editor com validar_dungeon (Fase 2)"
```

---

## Self-Review (cobertura do spec)

- **Gerador de catálogo (fonte única)** → Task 1 (`export_catalog.py` + `editor_catalog.js` + teste de coerência).
- **Shell/layout offline** → Task 2 (`editor.html`/`editor.css`).
- **Estado = esquema da Fase 1 + render** → Task 3.
- **Pintura de tiles** → Task 4. **Salas + porta com vínculo automático** → Task 5. **Entidades + seleção + painel (com catálogo)** → Task 6. **Objetivos/meta** → painel da masmorra (Task 6/8: id/name/grid no topo; objetivos em `S.objectives` com default — nota: a UI de editar objetivos secundários fica no painel da masmorra; ver abaixo).
- **Validação em JS espelhando validar_dungeon + bloqueio do salvar** → Task 7 + Task 8 (`save` aborta se inválida).
- **Salvar (download)/carregar (upload) + resize** → Task 8.
- **Teste de coerência + ida-e-volta + e2e com o jogo** → Tasks 1, 9.

**Edição de objetivos (principal + secundários):** Task 8, Step 1b — o painel da masmorra (quando `S.sel` é null) traz o select do objetivo principal e o +/− dos secundários, ligados a `S.objectives`. `buildJSON` (Task 7) serializa e `loadJSON` (Task 8) repovoa `S.objectives`.

**Sem placeholders de código:** cada Step traz o código real. As verificações de JS usam o navegador servido em :8077 (não há Node) + asserts via `EDITOR.*` no console — honesto para o ambiente.

**Consistência de nomes:** `EDITOR_CATALOG`, `EDITOR`, `S`, `initGrid`, `render`, `renderPanel`, `buildToolbar`, `cellFromEvent`, `paintTile`, `doorLink`/`doorUnlink`, `placeEntity`, `eraseAt`, `entityAt`, `validarEditor`, `buildJSON`, `loadJSON`, `save`, `updateStatus` — usados de forma idêntica entre as tasks. WALL/FLOOR/DOOR = 0/1/2; CELL=28.
