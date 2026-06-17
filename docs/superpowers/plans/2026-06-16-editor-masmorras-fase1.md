# Editor de Masmorras — Fase 1 (Fundação) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o `server.py` carregar e jogar uma masmorra autorada (JSON) com grid de tamanho variável, selecionável no lobby, sem quebrar o modo procedural.

**Architecture:** O esquema JSON é definido por completo, mas o carregador só instancia o que o motor já entende (tiles, salas, portas, monstros, baús, armadilhas, entrada). `exit`/`prisoner`/`objectives` são validados e guardados (`self.dungeon_def`), inertes até a Fase 3. O tamanho do mapa vira `self.map_w`/`self.map_h` (default 30); o procedural continua 30×30. Toda a lógica nova é server-side; o cliente já deriva dimensões de `state.tiles`.

**Tech Stack:** Python 3.x + `websockets` (server autoritativo). Testes = scripts standalone em `tools/test_*.py` que stubam a rede e usam um helper `check()` (NÃO pytest). Cliente = Vanilla JS (`src/gameState.js` lógica, `game.js` render).

**Spec:** `docs/superpowers/specs/2026-06-16-editor-masmorras-fase1-design.md`

---

## Notas de design (ler antes de começar)

- **Convenção de teste:** ver `tools/test_persistencia_masmorra.py`. Cada teste: `sys.path.insert` da raiz, `import server`, `GameRoom("TEST")`, stuba `gm_say/broadcast/push_state/send_to/broadcast_city_state` com `noop`, helper `check(nome, cond)`, `sys.exit(1 if FAIL else 0)`. Rodar da raiz: `python tools/test_x.py`.
- **Catálogo de itens de baú (Fase 1):** apenas `CHEST_ITEMS` (server, `server.py:1447`). Itens de loja/equipamento ricos ficam para fase futura. Construímos `_DUNGEON_ITEM_CATALOG = {it["id"]: it for it in CHEST_ITEMS}`.
- **Armadilhas autoradas:** reaproveitam `ARMADILHAS` (`server.py:1644`). O dict de uma armadilha viva segue o template de `_gerar_armadilhas_kobold` (`server.py:9590`): `aliada:False`, `visivel:False`, `ativada:False`, `so_luccas:False`, `efeitos_ativos:[]`, e `veneno_id` se aplicável.
- **Flag `boss` (decisão importante):** matar um monstro com `m["boss"]` truthy dispara `end_game(victory=True)` HOJE (`server.py:11339, 11434`). Isso é **conclusão por objetivo**, que pertence à Fase 3. Portanto, na Fase 1, o carregador grava o marcador autorado em `m["authored_boss"]` (inerte) e **mantém `m["boss"]=False`**. Assim a masmorra autorada se comporta como dungeon normal (sai pela escada). Idem `target`/`key_objective`: guardados, sem efeito.
- **Coordenadas:** tile em `(x,y)` é `tiles[y][x]`. `WALL=0, FLOOR=1, DOOR=2`.
- **Regra de arquitetura (CLAUDE.md):** lógica fica em `server.py`/`gameState.js`; render em `game.js`. O cliente fala com o estado só via `GS.*`. Editar `game.js` pelo tool de Edit (memória do projeto: nunca via PowerShell).

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | Constantes/helpers de masmorra, `validar_dungeon`, `load_authored_dungeon`, branch em `enter_dungeon`, `handle_select_dungeon`, grid dinâmico, payload do lobby, dispatch |
| `dungeons/test_fase1.json` | Criar | Masmorra autorada de exemplo (grid 16×12) para teste manual e de integração |
| `tools/test_dungeon_loader.py` | Criar | Testes da validação + carregador + seleção |
| `src/gameState.js` | Modificar | Guardar lista/seleção de masmorras do lobby; sender `selectDungeon(file)`; getters |
| `game.js` | Modificar | Dropdown de seleção no lobby (render + onchange → `GS.selectDungeon`) |

---

## Task 1: Constantes de masmorra + `validar_dungeon`

**Files:**
- Modify: `server.py` (após o bloco de `VENENOS`, antes de `# Sistema de armadilhas COLOCÁVEIS`, ~`server.py:1627`)
- Test: `tools/test_dungeon_loader.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_dungeon_loader.py`:

```python
"""Testes da Fase 1 do editor de masmorras: validação + carregador + seleção.
Roda da raiz: python tools/test_dungeon_loader.py"""
import asyncio, copy, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL, FLOOR, DOOR, validar_dungeon

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sample_dungeon():
    """Masmorra mínima 8×6: 1 sala 'entrance' (4×4) com 1 porta.
    Layout (x→, y↓), 0=WALL 1=FLOOR 2=DOOR:
      linha 0: 0 0 0 0 0 0 0 0
      linha 1: 0 1 1 1 1 0 0 0
      linha 2: 0 1 1 1 1 2 1 0
      linha 3: 0 1 1 1 1 0 0 0
      linha 4: 0 1 1 1 1 0 0 0
      linha 5: 0 0 0 0 0 0 0 0
    """
    W, H = 8, 6
    tiles = [[0]*W for _ in range(H)]
    for y in range(1, 5):
        for x in range(1, 5):
            tiles[y][x] = FLOOR
    tiles[2][5] = DOOR
    tiles[2][6] = FLOOR
    return {
        "schema_version": 1, "id": "amostra", "name": "Amostra",
        "grid": {"w": W, "h": H}, "tiles": tiles,
        "rooms": [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4,
                   "role": "entrance", "locked": False, "doors": [[5, 2]]}],
        "entrance": {"x": 2, "y": 2},
        "exit": {"x": 6, "y": 2},
        "monsters": [{"type": "goblin", "pos": [3, 3], "room_id": 0,
                      "boss": False, "target": False}],
        "chests": [{"pos": [2, 3], "gold": 20,
                    "items": [{"id": "health_potion"}], "key_objective": False}],
        "traps": [{"tipo": "fosso_estacas", "pos": [4, 1]}],
        "prisoner": {"pos": [4, 4], "room_id": 0},
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

def test_validacao():
    print("\n[1] validar_dungeon")
    ok, msg = validar_dungeon(sample_dungeon())
    check("masmorra válida passa", ok is True)

    d = sample_dungeon(); d["schema_version"] = 99
    ok, _ = validar_dungeon(d); check("schema_version inválido recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["type"] = "inexistente"
    ok, _ = validar_dungeon(d); check("monstro tipo desconhecido recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["pos"] = [0, 0]   # WALL
    ok, _ = validar_dungeon(d); check("monstro em parede recusa", ok is False)

    d = sample_dungeon(); d["monsters"][0]["room_id"] = 99
    ok, _ = validar_dungeon(d); check("room_id inexistente recusa", ok is False)

    d = sample_dungeon(); d["chests"][0]["items"][0]["id"] = "naoexiste"
    ok, _ = validar_dungeon(d); check("item de baú desconhecido recusa", ok is False)

    d = sample_dungeon(); d["rooms"][0]["doors"] = [[1, 1]]   # FLOOR, não DOOR
    ok, _ = validar_dungeon(d); check("porta que não é DOOR recusa", ok is False)

    d = sample_dungeon(); d["traps"][0] = {"tipo": "fosso_envenenado", "pos": [4, 1]}
    ok, _ = validar_dungeon(d); check("fosso_envenenado sem veneno_id recusa", ok is False)

    d = sample_dungeon(); d["tiles"] = d["tiles"][:-1]   # 5 linhas, grid.h=6
    ok, _ = validar_dungeon(d); check("tiles com nº de linhas errado recusa", ok is False)

async def main():
    test_validacao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL — `ImportError: cannot import name 'validar_dungeon' from 'server'`.

- [ ] **Step 3: Implementar `validar_dungeon` e as constantes**

Inserir em `server.py` logo após o dict `VENENOS` (fecha em ~`server.py:1627`) e antes do comentário `# Sistema de armadilhas COLOCÁVEIS`:

```python
# ─── MASMORRAS AUTORADAS (Fase 1 do editor) ───────────────────────────────────
import os as _os
DUNGEONS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "dungeons")
# Catálogo de itens que um baú autorado pode conter (Fase 1: só CHEST_ITEMS).
_DUNGEON_ITEM_CATALOG = {it["id"]: it for it in CHEST_ITEMS}

def _bfs_chao_alcancavel(tiles, w, h, start, limite):
    """Conta casas caminháveis (FLOOR/DOOR) alcançáveis a partir de `start`,
    parando ao atingir `limite` (otimização). Usado p/ garantir spawn dos heróis."""
    sx, sy = start
    if not (0 <= sx < w and 0 <= sy < h) or tiles[sy][sx] == WALL:
        return 0
    visto = {(sx, sy)}; pilha = [(sx, sy)]; conta = 0
    while pilha:
        x, y = pilha.pop()
        conta += 1
        if conta >= limite:
            return conta
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (0 <= nx < w and 0 <= ny < h and (nx, ny) not in visto
                    and tiles[ny][nx] != WALL):
                visto.add((nx, ny)); pilha.append((nx, ny))
    return conta

def validar_dungeon(defn):
    """Valida um dict de masmorra autorada. Retorna (ok: bool, msg: str)."""
    if not isinstance(defn, dict):
        return False, "Masmorra não é um objeto JSON."
    if defn.get("schema_version") != 1:
        return False, f"schema_version não suportado: {defn.get('schema_version')!r} (esperado 1)."
    grid = defn.get("grid") or {}
    w, h = grid.get("w"), grid.get("h")
    if not (isinstance(w, int) and isinstance(h, int) and 1 <= w <= 60 and 1 <= h <= 60):
        return False, "grid.w/grid.h ausentes ou fora de 1..60."
    tiles = defn.get("tiles")
    if not (isinstance(tiles, list) and len(tiles) == h):
        return False, f"tiles deve ter {h} linhas (grid.h)."
    for y, row in enumerate(tiles):
        if not (isinstance(row, list) and len(row) == w):
            return False, f"linha {y} de tiles deve ter {w} colunas (grid.w)."
        for x, v in enumerate(row):
            if v not in (0, 1, 2):
                return False, f"tile inválido em ({x},{y}): {v!r} (use 0/1/2)."

    def in_grid(p):
        return (isinstance(p, (list, tuple)) and len(p) == 2
                and isinstance(p[0], int) and isinstance(p[1], int)
                and 0 <= p[0] < w and 0 <= p[1] < h)

    def tile_at(p):
        return tiles[p[1]][p[0]]

    ent = defn.get("entrance")
    if not (isinstance(ent, dict) and in_grid([ent.get("x"), ent.get("y")])):
        return False, "entrance ausente ou fora do grid."
    if tile_at([ent["x"], ent["y"]]) != FLOOR:
        return False, "entrance precisa estar em FLOOR (1)."

    rooms = defn.get("rooms") or []
    room_ids = {r.get("id") for r in rooms}
    for r in rooms:
        for d in r.get("doors", []):
            if not in_grid(d) or tile_at(d) != DOOR:
                return False, f"porta {d} da sala {r.get('id')} não é um tile DOOR (2)."

    tipos_monstro = {m["type"] for m in MONSTER_DEFS}
    for mo in defn.get("monsters", []):
        if mo.get("type") not in tipos_monstro:
            return False, f"monstro tipo desconhecido: {mo.get('type')!r}."
        if not in_grid(mo.get("pos")) or tile_at(mo["pos"]) == WALL:
            return False, f"monstro em casa inválida: {mo.get('pos')}."
        if mo.get("room_id") not in room_ids:
            return False, f"monstro com room_id inexistente: {mo.get('room_id')!r}."

    for ch in defn.get("chests", []):
        if not in_grid(ch.get("pos")) or tile_at(ch["pos"]) == WALL:
            return False, f"baú em casa inválida: {ch.get('pos')}."
        if int(ch.get("gold", 0)) < 0:
            return False, "baú com gold negativo."
        for it in ch.get("items", []):
            if it.get("id") not in _DUNGEON_ITEM_CATALOG:
                return False, f"item de baú desconhecido: {it.get('id')!r}."

    for tr in defn.get("traps", []):
        if tr.get("tipo") not in ARMADILHAS:
            return False, f"armadilha tipo desconhecido: {tr.get('tipo')!r}."
        if not in_grid(tr.get("pos")) or tile_at(tr["pos"]) == WALL:
            return False, f"armadilha em casa inválida: {tr.get('pos')}."
        if tr["tipo"] == "fosso_envenenado" and tr.get("veneno_id") not in VENENOS:
            return False, f"fosso_envenenado exige veneno_id válido: {tr.get('veneno_id')!r}."

    pr = defn.get("prisoner")
    if pr is not None:
        if not in_grid(pr.get("pos")) or tile_at(pr["pos"]) == WALL:
            return False, f"prisioneiro em casa inválida: {pr.get('pos')}."
        if pr.get("room_id") not in room_ids:
            return False, f"prisioneiro com room_id inexistente: {pr.get('room_id')!r}."

    ex = defn.get("exit")
    if ex is not None and not in_grid([ex.get("x"), ex.get("y")]):
        return False, "exit fora do grid."

    if _bfs_chao_alcancavel(tiles, w, h, [ent["x"], ent["y"]], limite=6) < 6:
        return False, "menos de 6 casas de chão alcançáveis a partir da entrada."

    return True, "ok"
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — `=== 9 passou, 0 falhou ===`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_dungeon_loader.py
git commit -m "feat: validar_dungeon + catalogo de itens de masmorra autorada (Fase 1)"
```

---

## Task 2: Helpers de hidratação, armadilha autorada e descoberta de arquivos

**Files:**
- Modify: `server.py` (logo após `validar_dungeon`)
- Test: `tools/test_dungeon_loader.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `tools/test_dungeon_loader.py`, importando os novos símbolos no topo:

```python
from server import (hidratar_itens_bau, make_authored_trap,
                    listar_dungeons, carregar_dungeon)
```

E uma função de teste, chamada dentro de `main()` após `test_validacao()`:

```python
def test_helpers():
    print("\n[2] helpers (hidratação / trap / arquivos)")
    itens = hidratar_itens_bau([{"id": "health_potion"}])
    check("hidratação devolve dict completo", itens and itens[0]["name"] == "Poção de Vida")
    check("hidratação ignora id inexistente", hidratar_itens_bau([{"id": "x"}]) == [])

    arm = make_authored_trap({"tipo": "fosso_estacas", "pos": [4, 1]})
    check("trap autorada: tipo certo", arm["tipo"] == "fosso_estacas")
    check("trap autorada: hostil e oculta",
          arm["aliada"] is False and arm["visivel"] is False
          and arm["ativada"] is False and arm["so_luccas"] is False)
    arm2 = make_authored_trap({"tipo": "fosso_envenenado", "pos": [4, 1],
                               "veneno_id": "veneno_aranha_sombria"})
    check("trap envenenada guarda veneno_id", arm2.get("veneno_id") == "veneno_aranha_sombria")
```

E em `main()`:

```python
    test_helpers()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL — `ImportError: cannot import name 'hidratar_itens_bau'`.

- [ ] **Step 3: Implementar os helpers**

Inserir em `server.py` logo após `validar_dungeon`:

```python
def hidratar_itens_bau(items):
    """Resolve [{'id': ...}] nos dicts completos de CHEST_ITEMS. Ignora ids
    desconhecidos (a validação já recusa antes de chegar aqui)."""
    out = []
    for it in items or []:
        base = _DUNGEON_ITEM_CATALOG.get(it.get("id"))
        if base:
            out.append(deepcopy(base))
    return out

def make_authored_trap(tdef):
    """Cria o dict de uma armadilha de masmorra autorada (hostil, oculta),
    no formato de self.armadilhas. Espelha _gerar_armadilhas_kobold."""
    tipo = tdef["tipo"]
    meta = ARMADILHAS[tipo]
    arm = {
        "id":            new_id(),
        "tipo":          tipo,
        "pos":           [tdef["pos"][0], tdef["pos"][1]],
        "icone":         meta["icone"],
        "nome":          meta["nome"],
        "visivel":       False,
        "ativada":       False,
        "aliada":        False,
        "so_luccas":     False,
        "efeitos_ativos": [],
    }
    if tipo == "fosso_envenenado":
        arm["veneno_id"] = tdef.get("veneno_id")
    return arm

def carregar_dungeon(file):
    """Lê e parseia um arquivo de DUNGEONS_DIR. Retorna dict ou None."""
    if not isinstance(file, str) or not file or file != os.path.basename(file):
        return None  # proteção contra path traversal (sem componente de diretório)
    caminho = os.path.join(DUNGEONS_DIR, file)
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def listar_dungeons():
    """Varre DUNGEONS_DIR e devolve [{id, name, file}] das masmorras válidas."""
    out = []
    try:
        arquivos = sorted(f for f in os.listdir(DUNGEONS_DIR) if f.endswith(".json"))
    except Exception:
        return out
    for file in arquivos:
        defn = carregar_dungeon(file)
        if not defn:
            continue
        ok, _ = validar_dungeon(defn)
        if ok:
            out.append({"id": defn.get("id", file), "name": defn.get("name", file), "file": file})
    return out
```

> Verificar que `deepcopy` e `json` já estão importados no topo de `server.py` (estão — `_spawn_chest` usa `deepcopy`; o servidor usa `json`).

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — `=== 14 passou, 0 falhou ===`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_dungeon_loader.py
git commit -m "feat: helpers de hidratacao, armadilha autorada e descoberta de masmorras (Fase 1)"
```

---

## Task 3: Grid dinâmico (`self.map_w`/`self.map_h`) + atributos de modo

**Files:**
- Modify: `server.py:2646` (`GameRoom.__init__`)
- Modify: `server.py` (todas as ocorrências de `MAP_W`/`MAP_H` dentro de métodos de `GameRoom`)
- Test: `tools/test_dungeon_loader.py`

- [ ] **Step 1: Escrever o teste que falha (regressão procedural + atributos)**

Adicionar a `tools/test_dungeon_loader.py`:

```python
def setup_room(cls_list=(("p1", "Victor", "warrior"), ("p2", "Pedro", "mage"))):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in cls_list:
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"; r.phase = "city"
    return r

def monstros_em_parede(r):
    return [m for m in r.monsters.values()
            if r.tiles[m["pos"][1]][m["pos"][0]] == WALL]

async def test_grid_procedural():
    print("\n[3] grid dinâmico — regressão procedural")
    r = setup_room()
    check("default map_w/map_h = 30",
          getattr(r, "map_w", None) == 30 and getattr(r, "map_h", None) == 30)
    check("modo default = procedural", getattr(r, "mode", None) == "procedural")
    await r.enter_dungeon("p1")
    check("procedural ainda gera 30×30",
          len(r.tiles) == 30 and len(r.tiles[0]) == 30)
    check("map_w/map_h batem com tiles após procedural",
          r.map_w == len(r.tiles[0]) and r.map_h == len(r.tiles))
    check("procedural: nenhum monstro em parede", monstros_em_parede(r) == [])
```

E em `main()`:

```python
    await test_grid_procedural()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL no `[3]` — `map_w` é `None` (atributo ainda não existe).

- [ ] **Step 3: Adicionar atributos ao `__init__`**

Em `server.py`, dentro de `GameRoom.__init__`, logo após a linha `self.dungeon_generated = False` (`server.py:2659`), inserir:

```python
        # Tamanho do tabuleiro (procedural = 30×30; masmorra autorada define o seu).
        self.map_w = MAP_W
        self.map_h = MAP_H
        # Seleção de masmorra no lobby (Fase 1 do editor).
        self.mode = "procedural"          # "procedural" | "authored"
        self.selected_dungeon = None      # nome do arquivo em dungeons/ (modo authored)
        self.dungeon_def = None           # dict cru da masmorra autorada carregada
```

- [ ] **Step 4: Trocar `MAP_W`/`MAP_H` por `self.map_w`/`self.map_h` nos métodos de `GameRoom`**

Localizar todas as ocorrências:

Run: `python -c "import re;[print(i+1,l.rstrip()) for i,l in enumerate(open('server.py',encoding='utf-8')) if 'MAP_W' in l or 'MAP_H' in l]"`

Para CADA linha que está **dentro de um método de `GameRoom`** (corpo indentado sob `class GameRoom`, tipicamente checagens `0 <= x < MAP_W` / `0 <= y < MAP_H`), trocar `MAP_W` → `self.map_w` e `MAP_H` → `self.map_h`. Isto inclui `_gerar_armadilhas_kobold` (`server.py:9577`).

**NÃO alterar** as ocorrências em funções de módulo (fora da classe):
- `MAP_W = 30` / `MAP_H = 30` (definição, `server.py:29-30`)
- `generate_dungeon()` (`server.py:1747+`) — o procedural permanece 30×30
- a linha que adicionaremos no `__init__` (`self.map_w = MAP_W`)

> Dica para distinguir: se a linha usa `self.` em algum ponto ou está claramente indentada sob um `def` de método, é método de `GameRoom`. As funções de módulo (`generate_dungeon`, `make_trap`, `spawn_monsters_for_room`, `make_monster`) não recebem `self`.

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — bloco `[3]` todo verde.

- [ ] **Step 6: Rodar a regressão de persistência (garante que nada quebrou)**

Run: `python tools/test_persistencia_masmorra.py`
Expected: PASS — `=== N passou, 0 falhou ===` (mesmo resultado de antes da mudança).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_dungeon_loader.py
git commit -m "feat: grid dinamico (self.map_w/map_h) + atributos de modo de masmorra (Fase 1)"
```

---

## Task 4: `load_authored_dungeon` + branch em `enter_dungeon`

**Files:**
- Modify: `server.py` (novo método em `GameRoom`, perto de `enter_dungeon`, ~`server.py:3115`)
- Modify: `server.py:3132-3178` (bloco `nova` de `enter_dungeon`)
- Test: `tools/test_dungeon_loader.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_dungeon_loader.py`:

```python
async def test_load_authored():
    print("\n[4] load_authored_dungeon")
    r = setup_room()
    r.mode = "authored"
    r.dungeon_def = sample_dungeon()      # injeta direto (Task 5 faz via arquivo)
    r.selected_dungeon = "amostra.json"
    # patch: enter_dungeon usará r.dungeon_def quando authored (ver Step 3)
    await r.enter_dungeon("p1")

    check("grid autorado aplicado (8×6)", r.map_w == 8 and r.map_h == 6)
    check("tiles têm as dimensões do grid",
          len(r.tiles) == 6 and len(r.tiles[0]) == 8)
    check("1 monstro carregado", len(r.monsters) == 1)
    m = next(iter(r.monsters.values()))
    check("monstro na casa exata autorada", m["pos"] == [3, 3])
    check("monstro vinculado à sala 0", m["room_id"] == 0)
    check("authored_boss inerte (m['boss'] falsy)", not m.get("boss"))
    check("1 baú carregado com item hidratado",
          len(r.chests) == 1 and
          next(iter(r.chests.values()))["items"][0]["name"] == "Poção de Vida")
    check("baú com ouro exato", next(iter(r.chests.values()))["gold"] == 20)
    check("1 armadilha carregada", len(r.armadilhas) == 1 and
          r.armadilhas[0]["tipo"] == "fosso_estacas")
    check("nenhum monstro em parede", monstros_em_parede(r) == [])
    # heróis: todos em casas de chão (não parede), próximos à entrada
    casas = [tuple(p["pos"]) for p in r.players.values()]
    check("heróis em casas de chão", all(r.tiles[y][x] != WALL for x, y in casas))
    check("stairs na entrada", r.stairs_pos == [2, 2])
    check("dungeon_def guardado p/ Fase 3", r.dungeon_def is not None
          and r.dungeon_def.get("prisoner") is not None)
    check("entrada revelada (névoa)", (2, 2) in r.explored)
```

E em `main()`:

```python
    await test_load_authored()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL no `[4]` — `enter_dungeon` ainda gera procedural (grid 30×30), não usa `r.dungeon_def`.

- [ ] **Step 3: Implementar `load_authored_dungeon`**

Inserir como método de `GameRoom`, imediatamente ANTES de `async def enter_dungeon` (`server.py:3115`):

```python
    def load_authored_dungeon(self, defn):
        """Carrega uma masmorra autorada (dict já validado) no estado da sala.
        Instancia só o que o motor entende; exit/prisoner/objectives ficam em
        self.dungeon_def (inertes até a Fase 3)."""
        self.dungeon_def = defn
        self.map_w = defn["grid"]["w"]
        self.map_h = defn["grid"]["h"]
        self.tiles = deepcopy(defn["tiles"])

        # Salas no mesmo formato de generate_dungeon.
        self.rooms = []
        for r in defn.get("rooms", []):
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            role = r.get("role", "empty")
            self.rooms.append({
                "id": r["id"], "x": x, "y": y, "w": w, "h": h,
                "cx": x + w // 2, "cy": y + h // 2, "role": role,
                "cleared": role in ("entrance", "empty"),
                "looted": False,
                "locked": bool(r.get("locked", role != "entrance")),
                "doors": [list(d) for d in r.get("doors", [])],
            })

        # Mapa porta -> salas que ela destranca.
        self.door_rooms = {}
        for room in self.rooms:
            for dx, dy in room.get("doors", []):
                self.door_rooms.setdefault((dx, dy), []).append(room["id"])

        # Monstros em casa exata (sem distribuição/companheiros automáticos).
        self.monsters = {}
        for mo in defn.get("monsters", []):
            mdef = next(d for d in MONSTER_DEFS if d["type"] == mo["type"])
            room = self._room_by_id(mo.get("room_id")) or self.rooms[0]
            m = make_monster(mdef, room)
            m["pos"] = [mo["pos"][0], mo["pos"][1]]
            m["room_id"] = mo.get("room_id")
            m["boss"] = False                       # Fase 1: end_game-on-boss é da Fase 3
            m["authored_boss"] = bool(mo.get("boss"))
            m["authored_target"] = bool(mo.get("target"))
            self.monsters[m["id"]] = m

        # Baús com conteúdo exato (itens hidratados do catálogo do servidor).
        self.chests = {}
        for ch in defn.get("chests", []):
            self._spawn_chest(ch["pos"], int(ch.get("gold", 0)),
                              hidratar_itens_bau(ch.get("items", [])))

        # Armadilhas de masmorra autoradas (hostis, ocultas).
        self.traps = []
        self.armadilhas = [make_authored_trap(t) for t in defn.get("traps", [])]

        # Stairs = ponto de entrada.
        ent = defn["entrance"]
        self.stairs_pos = [ent["x"], ent["y"]]

    def _spawn_tiles_near(self, start, n):
        """Devolve até `n` casas de CHÃO (FLOOR/DOOR) mais próximas de `start`
        por BFS, na ordem de proximidade. Usado p/ posicionar heróis."""
        sx, sy = start
        out = []; visto = {(sx, sy)}; fila = [(sx, sy)]
        while fila and len(out) < n:
            x, y = fila.pop(0)
            if self.tiles[y][x] != WALL:
                out.append([x, y])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.map_w and 0 <= ny < self.map_h
                        and (nx, ny) not in visto and self.tiles[ny][nx] != WALL):
                    visto.add((nx, ny)); fila.append((nx, ny))
        return out
```

- [ ] **Step 4: Ramificar `enter_dungeon` para o modo autorado**

Em `server.py`, no bloco `if nova:` de `enter_dungeon` (`server.py:3132`), o código atual limpa o mundo e chama `generate_dungeon()` + spawns por role. Substituir a ramificação para tratar o modo autorado.

Localizar (`server.py:3129-3141`):

```python
        nova = not self.dungeon_generated
        pids = list(self.players.keys())

        if nova:
            self.corpses = {}        # cadáveres não persistem entre masmorras distintas
            self.chests  = {}        # baús do andar anterior não persistem no novo mapa
            self.monsters = {}       # zera monstros da expedição anterior (senão reaparecem em paredes do novo mapa)
            self.traps = []          # idem armadilhas de masmorra
            self.armadilhas = []     # idem armadilhas colocáveis
            self.zonas_especiais = []
            self.explored = set()    # névoa volta ao início no mapa novo
            self.magic_reveal = {}
            self.tiles, self.rooms = generate_dungeon()
```

Substituir esse trecho por:

```python
        nova = not self.dungeon_generated
        pids = list(self.players.keys())
        autorada = self.mode == "authored" and self.dungeon_def is not None

        if nova:
            self.corpses = {}        # cadáveres não persistem entre masmorras distintas
            self.chests  = {}        # baús do andar anterior não persistem no novo mapa
            self.monsters = {}       # zera monstros da expedição anterior (senão reaparecem em paredes do novo mapa)
            self.traps = []          # idem armadilhas de masmorra
            self.armadilhas = []     # idem armadilhas colocáveis
            self.zonas_especiais = []
            self.explored = set()    # névoa volta ao início no mapa novo
            self.magic_reveal = {}
            if autorada:
                self.load_authored_dungeon(self.dungeon_def)
            else:
                self.map_w, self.map_h = MAP_W, MAP_H
                self.tiles, self.rooms = generate_dungeon()
```

Em seguida, o bloco logo abaixo monta `self.door_rooms` e (mais adiante) faz os spawns por role. Esses só devem rodar no procedural. Localizar (`server.py:3143-3147`):

```python
            # Mapa porta -> salas que ela destranca (uma porta pode servir 2 salas)
            self.door_rooms = {}
            for room in self.rooms:
                for dx, dy in room.get("doors", []):
                    self.door_rooms.setdefault((dx, dy), []).append(room["id"])
```

Envolver com `if not autorada:` (no autorado, `load_authored_dungeon` já montou `door_rooms`):

```python
            if not autorada:
                # Mapa porta -> salas que ela destranca (uma porta pode servir 2 salas)
                self.door_rooms = {}
                for room in self.rooms:
                    for dx, dy in room.get("doors", []):
                        self.door_rooms.setdefault((dx, dy), []).append(room["id"])
```

Localizar o bloco de spawn por role (`server.py:3163-3178`, dentro de `if nova:`):

```python
        if nova:
            # Spawn monsters & traps
            for room in self.rooms:
                if room["role"] == "monster":
                    spawned = self._distribuir_monstros(spawn_monsters_for_room(room, len(pids)), room)
                    for m in spawned:
                        self.monsters[m["id"]] = m
                    if any("kobold" in m.get("type", "") for m in spawned):
                        self._gerar_armadilhas_kobold(room)
                if room["role"] == "boss":
                    boss_def = next(m for m in MONSTER_DEFS if m.get("boss"))
                    for m in self._distribuir_monstros([make_monster(boss_def, room)], room):
                        self.monsters[m["id"]] = m
                if room["role"] == "trap":
                    self.traps.append(make_trap(room, self.tiles))
            self.dungeon_generated = True   # marca: próximas voltas da cidade retomam esta masmorra
```

Trocar a condição da varredura de spawn para `if nova and not autorada:` (mantendo `self.dungeon_generated = True` SEMPRE no `nova`):

```python
        if nova:
            if not autorada:
                # Spawn monsters & traps (só procedural; autorada já posicionou tudo)
                for room in self.rooms:
                    if room["role"] == "monster":
                        spawned = self._distribuir_monstros(spawn_monsters_for_room(room, len(pids)), room)
                        for m in spawned:
                            self.monsters[m["id"]] = m
                        if any("kobold" in m.get("type", "") for m in spawned):
                            self._gerar_armadilhas_kobold(room)
                    if room["role"] == "boss":
                        boss_def = next(m for m in MONSTER_DEFS if m.get("boss"))
                        for m in self._distribuir_monstros([make_monster(boss_def, room)], room):
                            self.monsters[m["id"]] = m
                    if room["role"] == "trap":
                        self.traps.append(make_trap(room, self.tiles))
            self.dungeon_generated = True   # marca: próximas voltas da cidade retomam esta masmorra
```

Por fim, o posicionamento dos heróis. Localizar (`server.py:3149-3161`):

```python
        # Place players at entrance (reentram pela mesma escada que usaram p/ sair).
        entrance = next((r for r in self.rooms if r["role"] == "entrance"), self.rooms[0])
        offsets = [(0,0),(1,0),(-1,0),(0,1),(1,1),(-1,1)]
        for i, pid2 in enumerate(pids):
            ox, oy = offsets[i % len(offsets)]
            self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
```

Substituir o cálculo de posição por um que use casas de chão livres no modo autorado (mantendo os offsets no procedural):

```python
        # Place players at entrance (reentram pela mesma escada que usaram p/ sair).
        entrance = next((r for r in self.rooms if r["role"] == "entrance"), self.rooms[0])
        if autorada:
            ent_pt = [self.dungeon_def["entrance"]["x"], self.dungeon_def["entrance"]["y"]]
            spawn_tiles = self._spawn_tiles_near(ent_pt, len(pids))
        else:
            spawn_tiles = None
        offsets = [(0,0),(1,0),(-1,0),(0,1),(1,1),(-1,1)]
        for i, pid2 in enumerate(pids):
            if spawn_tiles is not None:
                self.players[pid2]["pos"] = list(spawn_tiles[i % len(spawn_tiles)])
            else:
                ox, oy = offsets[i % len(offsets)]
                self.players[pid2]["pos"] = [entrance["cx"] + ox, entrance["cy"] + oy]
```

> O resto de `enter_dungeon` (reset de `moves_left`/`action_done`, `self.stairs_pos`, `_reveal_room(entrance)`, timer, `push_state`) permanece. No autorado, `entrance` é a sala com `role=="entrance"`, então `_reveal_room(entrance)` já revela a entrada.

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — bloco `[4]` todo verde.

- [ ] **Step 6: Regressão**

Run: `python tools/test_persistencia_masmorra.py`
Expected: PASS — inalterado.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_dungeon_loader.py
git commit -m "feat: load_authored_dungeon + branch autorado em enter_dungeon (Fase 1)"
```

---

## Task 5: Seleção no lobby (`handle_select_dungeon` + payload + dispatch)

**Files:**
- Modify: `server.py:2755` (`broadcast_lobby`)
- Modify: `server.py` (novo método `handle_select_dungeon` em `GameRoom`)
- Modify: `server.py:11596+` (switch de mensagens)
- Test: `tools/test_dungeon_loader.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_dungeon_loader.py`:

```python
async def test_select_dungeon():
    print("\n[5] handle_select_dungeon")
    r = setup_room(); r.phase = "lobby"
    captura = {}
    async def cap_lobby(): captura["called"] = True
    r.broadcast_lobby = cap_lobby

    await r.handle_select_dungeon("p1", "amostra.json")
    check("modo vira authored", r.mode == "authored")
    check("arquivo selecionado guardado", r.selected_dungeon == "amostra.json")
    check("rebroadcast do lobby", captura.get("called") is True)

    await r.handle_select_dungeon("p1", None)
    check("None volta para procedural", r.mode == "procedural" and r.selected_dungeon is None)

    # não-host não altera
    r.mode = "procedural"
    await r.handle_select_dungeon("p2", "amostra.json")
    check("não-host é ignorado", r.mode == "procedural")
```

E em `main()`:

```python
    await test_select_dungeon()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL no `[5]` — `AttributeError: 'GameRoom' object has no attribute 'handle_select_dungeon'`.

- [ ] **Step 3: Implementar `handle_select_dungeon`**

Inserir como método de `GameRoom`, logo após `broadcast_lobby` (`server.py:2766`):

```python
    async def handle_select_dungeon(self, pid, file):
        """Host escolhe a masmorra do lobby. file=None → procedural."""
        if pid != self.host_pid:
            return
        if self.phase != "lobby":
            return
        if not file:
            self.mode = "procedural"; self.selected_dungeon = None
        else:
            defn = carregar_dungeon(file)
            ok, msg = (False, "Masmorra não encontrada.") if defn is None else validar_dungeon(defn)
            if not ok:
                await self.send_to(pid, {"type": "error", "msg": f"Masmorra inválida: {msg}"})
                return
            self.mode = "authored"; self.selected_dungeon = file
        await self.broadcast_lobby()
```

- [ ] **Step 4: Incluir as masmorras no payload do lobby**

Em `server.py`, no `broadcast_lobby` (`server.py:2756-2766`), adicionar três campos ao dict. Localizar:

```python
            "can_start": (
                len(self.players) >= 1 and
                all(p["class_id"] for p in self.players.values())
            )
        })
```

Trocar por:

```python
            "can_start": (
                len(self.players) >= 1 and
                all(p["class_id"] for p in self.players.values())
            ),
            "dungeons": listar_dungeons(),
            "mode": self.mode,
            "selected_dungeon": self.selected_dungeon,
        })
```

- [ ] **Step 5: Rotear a mensagem `select_dungeon`**

Em `server.py`, no switch de mensagens, após o ramo `elif t == "select_class":` (`server.py:11658-11659`), inserir:

```python
                elif t == "select_dungeon":
                    if room: await room.handle_select_dungeon(pid, msg.get("file"))
```

- [ ] **Step 6: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — bloco `[5]` verde.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_dungeon_loader.py
git commit -m "feat: select_dungeon no lobby + masmorras no lobby_state (Fase 1)"
```

---

## Task 6: Masmorra de exemplo em disco + teste de integração

**Files:**
- Create: `dungeons/test_fase1.json`
- Test: `tools/test_dungeon_loader.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_dungeon_loader.py`:

```python
async def test_arquivo_disco():
    print("\n[6] integração via arquivo em dungeons/")
    listadas = listar_dungeons()
    check("test_fase1.json aparece em listar_dungeons",
          any(d["file"] == "test_fase1.json" for d in listadas))
    defn = carregar_dungeon("test_fase1.json")
    check("carrega o arquivo", defn is not None)
    ok, msg = validar_dungeon(defn)
    check(f"arquivo é válido ({msg})", ok is True)
    # path traversal é barrado
    check("path traversal recusado", carregar_dungeon("../server.py") is None)

    r = setup_room(); r.mode = "authored"; r.dungeon_def = defn
    r.selected_dungeon = "test_fase1.json"
    await r.enter_dungeon("p1")
    check("grid do arquivo aplicado",
          r.map_w == defn["grid"]["w"] and r.map_h == defn["grid"]["h"])
    check("nenhum monstro em parede (arquivo)", monstros_em_parede(r) == [])
```

E em `main()`:

```python
    await test_arquivo_disco()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_dungeon_loader.py`
Expected: FAIL no `[6]` — arquivo não existe.

- [ ] **Step 3: Criar a masmorra de exemplo**

Criar `dungeons/test_fase1.json`. Grid 16×12: duas salas (entrada 5×4 destrancada à esquerda; sala trancada 5×4 à direita) ligadas por um corredor com uma porta. Monstros dormentes na sala trancada, baú e armadilha.

```json
{
  "schema_version": 1,
  "id": "test_fase1",
  "name": "Teste Fase 1 — Duas Salas",
  "grid": { "w": 16, "h": 12 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,1,1,1,1,1,2,1,1,2,1,1,1,1,1,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [
    { "id": 0, "x": 1, "y": 1, "w": 5, "h": 4, "role": "entrance", "locked": false, "doors": [[6,3]] },
    { "id": 1, "x": 10, "y": 1, "w": 5, "h": 4, "role": "monster", "locked": true, "doors": [[9,3]] }
  ],
  "entrance": { "x": 3, "y": 2 },
  "exit": { "x": 12, "y": 2 },
  "monsters": [
    { "type": "goblin", "pos": [12,2], "room_id": 1, "boss": false, "target": false },
    { "type": "skeleton", "pos": [13,3], "room_id": 1, "boss": false, "target": false }
  ],
  "chests": [
    { "pos": [11,4], "gold": 25, "items": [ {"id":"health_potion"}, {"id":"magic_sword"} ], "key_objective": false }
  ],
  "traps": [
    { "tipo": "fosso_estacas", "pos": [7,3] }
  ],
  "prisoner": { "pos": [14,4], "room_id": 1 },
  "objectives": {
    "primary": { "type": "kill_all" },
    "secondary": [ { "type": "rescue_prisoner" } ]
  }
}
```

> Conferência rápida do layout: a porta `[6,3]` (sala 0) e `[9,3]` (sala 1) são tiles `2`; o corredor `y=3` liga `x=6..9`. Todas as `pos` de monstro/baú/armadilha/prisioneiro caem em `1`/`2`. A entrada `[3,2]` tem ≥6 casas de chão (sala 5×4 = 20).

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_dungeon_loader.py`
Expected: PASS — `[6]` verde e total geral `0 falhou`.

- [ ] **Step 5: Commit**

```bash
git add dungeons/test_fase1.json tools/test_dungeon_loader.py
git commit -m "feat: masmorra de exemplo test_fase1.json + teste de integracao (Fase 1)"
```

---

## Task 7: Cliente — estado e sender de seleção (`gameState.js`)

**Files:**
- Modify: `src/gameState.js`
- Modify: `src/main.js` (se necessário, expor o novo método em `window`/`GS` — seguir o padrão existente)

> Sem teste automatizado (não há harness JS no projeto). Verificação é manual no Task 9.

- [ ] **Step 1: Localizar como `lobby_state` é tratado e como senders são definidos**

Run: `python -c "import re;[print(i+1,l.rstrip()) for i,l in enumerate(open('src/gameState.js',encoding='utf-8')) if 'lobby_state' in l or 'select_class' in l or 'lobbyState' in l]"`

- [ ] **Step 2: Guardar os campos novos do lobby e expor getters**

No handler de `lobby_state` (onde hoje `lobbyState` é atualizado), garantir que `dungeons`, `mode` e `selected_dungeon` do payload sejam preservados em `lobbyState` (se o handler já faz `lobbyState = msg`, nada a fazer; se copia campo a campo, adicionar os três). Adicionar getters análogos aos existentes, por exemplo:

```javascript
  function lobbyDungeons()      { return (lobbyState && lobbyState.dungeons) || []; }
  function lobbyMode()          { return (lobbyState && lobbyState.mode) || 'procedural'; }
  function lobbySelectedDungeon(){ return (lobbyState && lobbyState.selected_dungeon) || null; }
```

- [ ] **Step 3: Adicionar o sender `selectDungeon`**

Seguindo o padrão dos outros senders (ex.: o que envia `select_class`), adicionar:

```javascript
  function selectDungeon(file) {
    send({ type: 'select_dungeon', file: file || null });
  }
```

- [ ] **Step 4: Exportar no objeto público `GS`**

No objeto retornado/`return { ... }` do módulo (onde `selectClass`, `move`, etc. são expostos), adicionar:

```javascript
    selectDungeon,
    lobbyDungeons,
    lobbyMode,
    lobbySelectedDungeon,
```

Se `src/main.js` espelha métodos em `window` (ver `window.CATALOGO_ITENS = GS.CATALOGO_ITENS;`), nenhum espelhamento extra é necessário — o render usará `GS.selectDungeon(...)`.

- [ ] **Step 5: Sanidade de carregamento (sem erro de sintaxe)**

Run: `python -c "import server"` não cobre JS; em vez disso, subir o servidor e abrir o cliente no Task 9 valida o JS. Por ora, revisar visualmente que o `return { ... }` continua com vírgulas corretas.

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js src/main.js
git commit -m "feat: estado de selecao de masmorra e sender selectDungeon no cliente (Fase 1)"
```

---

## Task 8: Cliente — dropdown de seleção no lobby (`game.js`)

**Files:**
- Modify: `game.js` (tela de lobby)

> Editar `game.js` apenas pelo tool de Edit (memória do projeto: nunca via PowerShell). Sem teste automatizado; verificação no Task 9.

- [ ] **Step 1: Localizar a render da tela de lobby**

Run: `python -c "import re;[print(i+1,l.rstrip()) for i,l in enumerate(open('game.js',encoding='utf-8')) if 'lobby' in l.lower() and ('render' in l.lower() or 'innerHTML' in l.lower() or 'start_game' in l.lower() or 'can_start' in l.lower())]"`

Identificar a função que desenha o lobby (lista de jogadores + botão iniciar), que lê de `GS.*`.

- [ ] **Step 2: Renderizar o dropdown (apenas para o host)**

Na render do lobby, antes do botão "Iniciar", inserir um seletor preenchido com `GS.lobbyDungeons()`, marcando `GS.lobbySelectedDungeon()`. Exemplo de construção do HTML (adaptar ao estilo/markup existente do arquivo):

```javascript
  const dungeons = GS.lobbyDungeons();
  const sel = GS.lobbySelectedDungeon();
  const opts = ['<option value="">Procedural (aleatória)</option>']
    .concat(dungeons.map(d =>
      `<option value="${d.file}"${d.file === sel ? ' selected' : ''}>${d.name}</option>`))
    .join('');
  const dungeonPicker =
    `<div class="lobby-dungeon">
       <label>Masmorra:</label>
       <select id="dungeonSelect"${isHost ? '' : ' disabled'}>${opts}</select>
     </div>`;
```

Incluir `dungeonPicker` no HTML do lobby. `isHost` deve usar a mesma checagem de host já existente na render (comparar pid local com `lobbyState.host`).

- [ ] **Step 3: Ligar o onchange ao sender**

Após inserir o HTML no DOM, registrar o handler (no mesmo ponto onde outros listeners do lobby são ligados):

```javascript
  const dsel = document.getElementById('dungeonSelect');
  if (dsel) dsel.onchange = () => GS.selectDungeon(dsel.value || null);
```

- [ ] **Step 4: Exibir o modo atual (feedback)**

Opcional, mas recomendado: ao lado do seletor, mostrar `GS.lobbyMode() === 'authored' ? 'Modo: Campanha' : 'Modo: Procedural'` para todos os jogadores verem a escolha do host (o `lobby_state` é broadcast a todos).

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat: dropdown de selecao de masmorra no lobby (Fase 1)"
```

---

## Task 9: Verificação end-to-end no navegador

**Files:** nenhum (verificação manual com o servidor real).

> Usar os preview_* tools. NÃO pedir ao usuário para testar manualmente — verificar e relatar.

- [ ] **Step 1: Subir o servidor**

Run (background): `python server.py`
Abrir `http://localhost:8765/index.html`.

- [ ] **Step 2: Caminho feliz — masmorra autorada**

Criar sala (host) → escolher classe → no dropdown selecionar "Teste Fase 1 — Duas Salas" → Iniciar → entrar na masmorra. Verificar via snapshot/screenshot:
- tabuleiro 16×12 (não 30×30);
- duas salas + corredor com porta como no JSON;
- heróis na sala de entrada (esquerda), em chão;
- baú e armadilha presentes;
- sala da direita coberta por névoa, monstros dormentes; abrir a porta `[9,3]` revela e desperta goblin+esqueleto.

- [ ] **Step 3: Recusa de inválida**

Editar `dungeons/test_fase1.json` introduzindo um erro (ex.: trocar `"type":"goblin"` por `"type":"xyz"`), recarregar o lobby, tentar selecionar/iniciar. Verificar que o host recebe erro claro e a partida não inicia. Reverter a edição.

- [ ] **Step 4: Regressão procedural**

Em uma nova sala, deixar "Procedural (aleatória)" e entrar. Verificar mapa 30×30 e spawns por role, idêntico ao comportamento atual.

- [ ] **Step 5: Console limpo**

Conferir `preview_console_logs` sem erros JS no lobby e na masmorra.

- [ ] **Step 6: Parar o servidor e relatar**

Encerrar o servidor de teste. Relatar evidências (screenshots/snapshots) ao usuário.

---

## Self-Review (cobertura do spec)

- **Esquema JSON completo + campos ativos/guardados** → Tasks 1, 4, 6 (schema validado; `exit`/`prisoner`/`objectives`/`boss`/`target` guardados inertes; `authored_boss`/`authored_target` em monstros).
- **Grid dinâmico** → Task 3 (atributos + refactor) e Task 4 (aplica do JSON).
- **Carregador** → Task 4 (`load_authored_dungeon`): tiles, salas, `door_rooms`, monstros exatos, baús hidratados, armadilhas, stairs, spawn BFS, reveal via `enter_dungeon`.
- **Validação com erro claro** → Task 1 (`validar_dungeon`) + Task 5 (erro ao host na seleção).
- **Itens só do catálogo do servidor** → Tasks 1/2 (`_DUNGEON_ITEM_CATALOG` = `CHEST_ITEMS`; hidratação).
- **Armadilhas (8 tipos) + `veneno_id`** → Task 2 (`make_authored_trap`) + validação Task 1.
- **`room_id` governa dormir/despertar** → Task 4 (monstros recebem `room_id` autorado; validação confere existência).
- **Spawn de heróis sem cair em parede** → Task 4 (`_spawn_tiles_near` BFS) + validação ≥6 (Task 1).
- **Seleção no lobby + protocolo `select_dungeon`** → Task 5 (handler, payload, dispatch) + Tasks 7/8 (cliente).
- **Pasta `dungeons/` + exemplo** → Task 6.
- **Sem conclusão por objetivo / boss inerte** → Task 4 (`m["boss"]=False`) + Task 9 (sai pela escada).
- **Sem regressão procedural** → Tasks 3/4/9 + `tools/test_persistencia_masmorra.py`.

**Sem placeholders:** todos os steps de servidor trazem código completo; steps de cliente trazem snippets concretos + comandos de localização (game.js/gameState.js são arquivos grandes e variáveis; a localização exata é resolvida pelo engenheiro com o grep indicado).

**Consistência de nomes:** `validar_dungeon`, `carregar_dungeon`, `listar_dungeons`, `hidratar_itens_bau`, `make_authored_trap`, `load_authored_dungeon`, `_spawn_tiles_near`, `handle_select_dungeon`, `_DUNGEON_ITEM_CATALOG`, `DUNGEONS_DIR`, `self.map_w/self.map_h/self.mode/self.selected_dungeon/self.dungeon_def` — usados de forma idêntica em todas as tasks.
