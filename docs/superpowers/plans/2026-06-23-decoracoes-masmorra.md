# Decorações de Masmorra — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 22 objetos de decoração colocáveis no editor de masmorras, que ocupam 1/2/4 casas, bloqueiam passagem (e visão nos "altos"), giram 90°, podem conter loot (abrem como baú), com fonte (dá garrafa de água) e fogueira (1d4 de fogo ao entrar).

**Architecture:** Reaproveita os sistemas existentes — footprint multi-tile dos monstros, `_blocks_tile`, baús (`_spawn_chest`/`handle_take_from_chest`), sobrevivência (garrafa de água) e o catálogo exportado do editor. Estado/servidor primeiro, depois editor, depois renderização (regra do `CLAUDE.md`).

**Tech Stack:** Python (`server.py`, sem framework de teste — scripts em `tools/test_*.py` que importam `server`), JS vanilla (`tools/editor.js`, `src/gameState.js`, `game.js`), Three.js r128.

**Spec:** `docs/superpowers/specs/2026-06-23-decoracoes-masmorra-design.md`

---

## Estrutura de arquivos

| Arquivo | Mudança |
|---|---|
| `server.py` | `DECOR_TYPES`, carga/reset, footprint, bloqueio, fogueira, fonte, container, oclusão de visão, `game_state`, validação, dispatch de mensagens |
| `tools/export_catalog.py` | exportar `decorations` para o editor |
| `tools/editor_catalog.js` | regenerado (rodar o export) |
| `tools/editor.js` | ferramenta/seletor, rotação, painel (loot/cargas), footprint, validação, JSON |
| `src/gameState.js` | getter `decorations`, `decorTiles`, senders |
| `game.js` | render 2D (emoji) + 3D (geometria procedural), clique → interação |
| `tools/test_decoracoes.py` | **novo** — testes do servidor |
| `tools/test_export_catalog.py` | + checagem de `decorations` |
| `dungeons/test_decoracoes.json` | **novo** — masmorra de amostra p/ roundtrip |

## Convenções desta base

- Testes são scripts: `python tools/test_decoracoes.py`, com helper `check(name, cond)` e `sys.exit(1 if FAIL else 0)`.
- O editor JS **não** tem runner; valida-se o **contrato** (JSON produzido valida em `server.validar_dungeon`) e a exportação do catálogo, em Python.
- Footprint (mesma fórmula em server/editor/cliente): âncora = canto superior-esquerdo; `facing` horizontal (`[±1,0]`) troca `w↔h`; vertical/`null` mantém `[w,h]`.

---

# FASE A — Servidor e estado

## Task A1: Catálogo `DECOR_TYPES`

**Files:**
- Modify: `server.py` (logo após o bloco de `ARMADILHAS`/catálogos; antes das funções de validação ~linha 1630)
- Test: `tools/test_decoracoes.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_decoracoes.py`:

```python
"""Testes das decorações de masmorra.
Roda da raiz: python tools/test_decoracoes.py"""
import sys, os, asyncio, copy
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, WALL, FLOOR, DOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_catalog():
    print("\n[A1] DECOR_TYPES")
    d = server.DECOR_TYPES
    check("22 tipos", len(d) == 22)
    check("ids esperados presentes", all(k in d for k in (
        "cama", "lareira", "fonte", "fogueira", "tumba", "mesa_cadeiras",
        "estante", "carroca", "coluna", "barril", "arca_tesouros", "cama_casal",
        "estante_livros", "altar", "trono", "gaiola", "grades_prisao",
        "estante_armas", "mesa_tortura", "mesa_quimica", "arvore", "arvore_grande")))
    check("fonte é fountain", d["fonte"]["special"] == "fountain")
    check("fogueira é campfire e pisável", d["fogueira"]["special"] == "campfire" and d["fogueira"]["pisavel"])
    check("fonte size 2x2", d["fonte"]["size"] == [2, 2])
    check("cama size 1x2", d["cama"]["size"] == [1, 2])
    check("coluna alta", d["coluna"]["alto"] is True)
    check("grades não-alta", d["grades_prisao"]["alto"] is False)
    check("todo tipo tem emoji/nome/gira/loot_capaz", all(
        set(("nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(v)
        for v in d.values()))
    check("só fogueira é pisável", [k for k, v in d.items() if v["pisavel"]] == ["fogueira"])

def main():
    test_catalog()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute 'DECOR_TYPES'`

- [ ] **Step 3: Implementar `DECOR_TYPES`**

Em `server.py`, logo após a definição de `ARMADILHAS` (procure `ARMADILHAS = {` e insira após o fechamento do dict), adicionar:

```python
# ─── DECORAÇÕES DE MASMORRA ──────────────────────────────────────────────────
# Objetos colocáveis no editor. size=[w,h] no facing canônico (vertical).
# gira: rotação 90°. alto: oclui a revelação de névoa (raycast). pisavel: não
# bloqueia movimento (só a fogueira). loot_capaz: pode conter ouro/itens (abre
# como baú). special: None|"fountain"|"campfire".
def _decor(nome, emoji, size, gira=False, alto=False, pisavel=False,
           loot_capaz=True, special=None):
    return {"nome": nome, "emoji": emoji, "size": size, "gira": gira,
            "alto": alto, "pisavel": pisavel, "loot_capaz": loot_capaz,
            "special": special}

DECOR_TYPES = {
    "cama":           _decor("Cama", "🛏️", [1, 2], gira=True),
    "lareira":        _decor("Lareira", "🪵", [1, 2], gira=True),
    "fonte":          _decor("Fonte", "⛲", [2, 2], special="fountain"),
    "fogueira":       _decor("Fogueira", "🔥", [1, 1], pisavel=True, loot_capaz=False, special="campfire"),
    "tumba":          _decor("Tumba", "⚰️", [1, 2], gira=True),
    "mesa_cadeiras":  _decor("Mesa com cadeiras", "🪑", [1, 2], gira=True),
    "estante":        _decor("Estante", "🗄️", [1, 2], gira=True, alto=True),
    "carroca":        _decor("Carroça", "🛒", [2, 2], gira=True),
    "coluna":         _decor("Coluna de pedra", "🏛️", [1, 1], alto=True),
    "barril":         _decor("Barril", "🛢️", [1, 1]),
    "arca_tesouros":  _decor("Arca de tesouros", "💰", [1, 1]),
    "cama_casal":     _decor("Cama de casal", "🛌", [2, 2], gira=True),
    "estante_livros": _decor("Estante de livros", "📚", [1, 2], gira=True, alto=True),
    "altar":          _decor("Altar ritualístico", "🛐", [2, 2], gira=True),
    "trono":          _decor("Trono de rei", "👑", [1, 1], gira=True),
    "gaiola":         _decor("Gaiola com esqueleto", "⛓️", [1, 1]),
    "grades_prisao":  _decor("Grades de prisão", "🚧", [1, 1], gira=True),
    "estante_armas":  _decor("Estante de armas", "⚔️", [1, 2], gira=True, alto=True),
    "mesa_tortura":   _decor("Mesa de tortura", "🔪", [1, 2], gira=True),
    "mesa_quimica":   _decor("Mesa de química", "🧪", [1, 2], gira=True),
    "arvore":         _decor("Árvore", "🌳", [1, 1], alto=True),
    "arvore_grande":  _decor("Árvore grande", "🌲", [2, 2], alto=True),
}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS (todos os checks de `[A1]`).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): catálogo DECOR_TYPES dos 22 objetos de decoração"
```

---

## Task A2: Footprint e rotação

**Files:**
- Modify: `server.py` (métodos de `GameRoom`, perto de `_monster_tiles_at` ~linha 9929)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar em `tools/test_decoracoes.py`:

```python
async def _noop(*a, **k): pass

def _room():
    r = GameRoom("TEST")
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop; r.push_state = _noop
    r.map_w, r.map_h = 12, 12
    r.tiles = [[FLOOR] * 12 for _ in range(12)]
    r.rooms = []
    r.players = {}
    r.decorations = []
    r._rebuild_decor_index()
    return r

def test_footprint():
    print("\n[A2] footprint/rotação")
    r = _room()
    # cama 1x2 vertical (facing default [0,1]) ancorada em (3,3)
    t = r._decor_tiles_at("cama", 3, 3, [0, 1])
    check("cama vertical ocupa (3,3) e (3,4)", sorted(map(tuple, t)) == [(3, 3), (3, 4)])
    # cama girada 90° (facing horizontal) ocupa 2x1
    t = r._decor_tiles_at("cama", 3, 3, [1, 0])
    check("cama horizontal ocupa (3,3) e (4,3)", sorted(map(tuple, t)) == [(3, 3), (4, 3)])
    # fonte 2x2 é igual em qualquer facing
    t = r._decor_tiles_at("fonte", 5, 5, [1, 0])
    check("fonte 2x2", sorted(map(tuple, t)) == [(5, 5), (5, 6), (6, 5), (6, 6)])
    # 1x1
    t = r._decor_tiles_at("coluna", 2, 2, [1, 0])
    check("coluna 1x1", sorted(map(tuple, t)) == [(2, 2)])
```

E chamar `test_footprint()` em `main()` (antes do print final).

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `GameRoom` não tem `_decor_tiles_at` / `_rebuild_decor_index`.

- [ ] **Step 3: Implementar**

Em `server.py`, dentro da classe `GameRoom`, perto de `_monster_tiles_at`, adicionar:

```python
    # ── DECORAÇÕES ─────────────────────────────────────────────────────────
    def _decor_eff_size(self, dtype, facing):
        """(ew,eh) efetivos: facing horizontal troca w↔h; vertical/None mantém."""
        w, h = DECOR_TYPES[dtype]["size"]
        if facing and facing[0] != 0:
            return h, w
        return w, h

    def _decor_tiles_at(self, dtype, ax, ay, facing=None):
        """Casas [x,y] ocupadas pela decoração `dtype` ancorada em (ax,ay)."""
        ew, eh = self._decor_eff_size(dtype, facing)
        return [[ax + i, ay + j] for i in range(ew) for j in range(eh)]

    def _decor_tiles(self, d):
        return self._decor_tiles_at(d["type"], d["pos"][0], d["pos"][1], d.get("facing"))

    def _rebuild_decor_index(self):
        """Recalcula os índices rápidos de bloqueio/visão das decorações."""
        self._decor_block_tiles = set()
        self._decor_tall_tiles = set()
        self._campfire_tiles = set()
        for d in getattr(self, "decorations", []):
            meta = DECOR_TYPES[d["type"]]
            for tx, ty in self._decor_tiles(d):
                if not meta["pisavel"]:
                    self._decor_block_tiles.add((tx, ty))
                if meta["alto"]:
                    self._decor_tall_tiles.add((tx, ty))
                if meta["special"] == "campfire":
                    self._campfire_tiles.add((tx, ty))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A2]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): footprint, rotação e índices de bloqueio/visão"
```

---

## Task A3: Carga no defn + reset

**Files:**
- Modify: `server.py` — `__init__` de `GameRoom` (inicializar atributos), `load_authored_dungeon` (~linha 3638), bloco `nova` do reset (~linha 3710)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_carga():
    print("\n[A3] carga de decorações")
    r = _room()
    defn = {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 12, "h": 12},
        "tiles": [[FLOOR] * 12 for _ in range(12)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": None, "prisoner": None,
        "monsters": [], "chests": [], "traps": [],
        "decorations": [
            {"type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": {"gold": 5, "items": [{"id": "health_potion"}]}},
            {"type": "fonte", "pos": [6, 6], "facing": [0, 1], "loot": None, "charges": 3},
        ],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    r.load_authored_dungeon(defn)
    check("2 decorações carregadas", len(r.decorations) == 2)
    check("loot da cama hidratado (item tem name)", r.decorations[0]["loot"]["items"][0].get("name") is not None)
    check("fonte com charges", r.decorations[1]["charges"] == 3)
    check("índice de bloqueio inclui (3,4)", (3, 4) in r._decor_block_tiles)
```

E chamar `test_carga()` em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `load_authored_dungeon` não popula `r.decorations`.

- [ ] **Step 3: Implementar**

3a. No `__init__` de `GameRoom` (onde `self.chests = {}` é inicializado, ~linha 3075), adicionar:

```python
        self.decorations = []
        self._decor_block_tiles = set()
        self._decor_tall_tiles = set()
        self._campfire_tiles = set()
```

3b. Em `load_authored_dungeon`, logo após o bloco de carga de `chests` (após as linhas que fazem `self._spawn_chest(...)` no laço de `defn.get("chests", [])`, ~linha 3641), adicionar:

```python
        # Decorações autoradas (itens de loot hidratados do catálogo do servidor).
        self.decorations = []
        for d in defn.get("decorations", []):
            meta = DECOR_TYPES.get(d.get("type"))
            if not meta:
                continue
            dec = {
                "id": f"dec_{len(self.decorations)}",
                "type": d["type"],
                "pos": [d["pos"][0], d["pos"][1]],
                "facing": list(d.get("facing") or [0, 1]),
                "loot": None,
                "tem_loot": False,
            }
            loot = d.get("loot")
            if loot and meta["loot_capaz"]:
                dec["loot"] = {"gold": int(loot.get("gold", 0)),
                               "items": hidratar_itens_bau(loot.get("items", []))}
                dec["tem_loot"] = (dec["loot"]["gold"] > 0 or bool(dec["loot"]["items"]))
            if meta["special"] == "fountain":
                dec["charges"] = int(d.get("charges", 0))
            self.decorations.append(dec)
        self._rebuild_decor_index()
```

3c. No bloco `nova` do reset (onde `self.chests = {}` é zerado, ~linha 3711), adicionar:

```python
            self.decorations = []
            self._rebuild_decor_index()
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A3]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): carregar decorações do defn e zerar no reset"
```

---

## Task A4: Bloqueio de movimento

**Files:**
- Modify: `server.py` — `_blocks_tile` (~linha 3965)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_bloqueio():
    print("\n[A4] bloqueio de movimento")
    r = _room()
    r.decorations = [{"id": "d0", "type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    check("casa da cama bloqueia", r._blocks_tile(3, 3) is True)
    check("casa vizinha da cama bloqueia", r._blocks_tile(3, 4) is True)
    check("casa livre não bloqueia", r._blocks_tile(0, 0) is False)
    # fogueira é pisável → não bloqueia
    r.decorations = [{"id": "d1", "type": "fogueira", "pos": [2, 2], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    check("fogueira não bloqueia (pisável)", r._blocks_tile(2, 2) is False)
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `_blocks_tile(3,3)` retorna False (decoração não considerada).

- [ ] **Step 3: Implementar**

Em `server.py`, no método `_blocks_tile`, alterar o `return` final:

```python
    def _blocks_tile(self, x, y):
        """Tile intransponível: parede, porta fechada ou decoração sólida."""
        if not (0 <= x < self.map_w and 0 <= y < self.map_h):
            return True
        if self.tiles[y][x] == WALL or self._is_closed_door(x, y):
            return True
        return (x, y) in self._decor_block_tiles
```

> Isso cobre automaticamente `handle_move` (heróis), `_monster_can_occupy`/pathfinding (monstros), animados e mira de magias em linha, pois todos consultam `_blocks_tile`. **Atenção:** `handle_move` cita explicitamente `self.tiles[ny][nx] == WALL` antes de `_is_closed_door`; uma decoração sólida sobre FLOOR não cai nesse `WALL`, então adicionar uma checagem logo após o bloco de porta em `handle_move`.

3b. Em `handle_move`, logo após o bloco `if self._is_closed_door(nx, ny):` (que envia "A porta está fechada"), adicionar:

```python
        if (nx, ny) in self._decor_block_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Há um objeto bloqueando o caminho."})
            return
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A4]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): decorações sólidas bloqueiam movimento e pathfinding"
```

---

## Task A5: Fogueira — 1d4 ao entrar

**Files:**
- Modify: `server.py` — helper novo + `handle_move` (herói) + 3 commits de passo de monstro (~7201, ~10024, ~11860)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_fogueira():
    print("\n[A5] fogueira 1d4")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "fogueira", "pos": [4, 4], "facing": [0, 1], "loot": None, "tem_loot": False}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0)
        p["pos"] = [4, 4]; p["hp"] = 20; p["max_hp"] = 20; p["alive"] = True
        await r._aplicar_fogueira_se_pisar(p)
        check("herói perdeu entre 1 e 4 HP", 16 <= p["hp"] <= 19)
        # fora da fogueira: sem dano
        p["pos"] = [0, 0]; hp0 = p["hp"]
        await r._aplicar_fogueira_se_pisar(p)
        check("sem dano fora da fogueira", p["hp"] == hp0)
    asyncio.run(run())
```

E chamar em `main()`.

> O `_room()` da Task A2 já stuba `gm_say`/`broadcast`/`send_to`/`push_state` como no-ops (padrão de `tools/test_persistencia_masmorra.py`), então os handlers assíncronos rodam sem rede.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `_aplicar_fogueira_se_pisar` não existe.

- [ ] **Step 3: Implementar**

3a. Helper na classe `GameRoom` (perto de `_decor_tiles`):

```python
    async def _aplicar_fogueira_se_pisar(self, criatura):
        """Se a criatura está numa casa de fogueira, sofre 1d4 de fogo (sem save)."""
        pos = criatura.get("pos")
        if not pos or (pos[0], pos[1]) not in self._campfire_tiles:
            return
        dano = roll_dice("1d4")
        nome = criatura.get("name") or criatura.get("nome", "Alguém")
        await self.broadcast({"type": "dice_roll", "die": "d4", "value": dano, "label": "Fogueira"})
        await self.gm_say(f"🔥 **{nome}** pisou na fogueira e sofre **{dano}** de fogo!")
        await self._dano_em_alvo(criatura, dano, "fogo")

    async def _commit_monster_step(self, m, nx, ny):
        """Move o monstro 1 passo e aplica efeitos de pisar (fogueira)."""
        m["pos"] = [nx, ny]
        await self._aplicar_fogueira_se_pisar(m)
```

3b. Em `handle_move` (herói), logo após `p["pos"] = [nx, ny]` e o decremento de movimento, adicionar:

```python
        await self._aplicar_fogueira_se_pisar(p)
```

3c. Nos três commits de passo de monstro, substituir `m["pos"] = [nx, ny]` por `await self._commit_monster_step(m, nx, ny)`:
- `server.py:7201` (perseguição)
- `server.py:10024`
- `server.py:11860`

> Verifique que cada um dos três está dentro de um método `async def` (os turnos de monstro são assíncronos). Se algum não for async, mantenha `m["pos"]=[nx,ny]` e chame `await self._aplicar_fogueira_se_pisar(m)` no laço async que processa o turno daquele monstro.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A5]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): fogueira causa 1d4 de fogo a quem entra (heróis e monstros)"
```

---

## Task A6: Fonte — entrega garrafa de água (cargas)

**Files:**
- Modify: `server.py` — helper `_TAVERN_BY_ID` (módulo) + `handle_interagir_decor` (parte fonte)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_fonte():
    print("\n[A6] fonte → garrafa de água")
    async def run():
        r = _room()
        r.decorations = [{"id": "d0", "type": "fonte", "pos": [5, 5], "facing": [0, 1], "loot": None, "tem_loot": False, "charges": 2}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["bag"] = []; p["bag_size"] = 6; p["alive"] = True
        r.players = {"p1": p}
        await r.handle_interagir_decor("p1", "d0")
        check("ganhou garrafa de água", any(i["id"] == "garrafa_agua" for i in p["bag"]))
        check("carga decrementou p/ 1", r.decorations[0]["charges"] == 1)
        await r.handle_interagir_decor("p1", "d0")
        await r.handle_interagir_decor("p1", "d0")   # 3ª vez: sem cargas
        check("não passou de 2 garrafas", sum(1 for i in p["bag"] if i["id"] == "garrafa_agua") == 2)
        check("cargas zeradas", r.decorations[0]["charges"] == 0)
    asyncio.run(run())
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `handle_interagir_decor` não existe.

- [ ] **Step 3: Implementar**

3a. No nível de módulo (perto de `_DUNGEON_ITEM_CATALOG`, ~linha 1636):

```python
_TAVERN_BY_ID = {i["id"]: i for i in SHOP_TAVERN}
```

3b. Helpers de localização + handler na classe `GameRoom`:

```python
    def _decor_by_id(self, decor_id):
        return next((d for d in self.decorations if d["id"] == decor_id), None)

    def _adjacente_a_decor(self, pos, d):
        """True se `pos` está a ≤1 casa (Chebyshev) de qualquer casa do footprint."""
        for tx, ty in self._decor_tiles(d):
            if max(abs(pos[0] - tx), abs(pos[1] - ty)) <= 1:
                return True
        return False

    async def handle_interagir_decor(self, pid, decor_id):
        """Herói adjacente interage: fonte → bebe; container → abre painel de loot."""
        p = self.players.get(pid)
        if not p or not p.get("alive"):
            return
        d = self._decor_by_id(decor_id)
        if not d:
            await self.send_to(pid, {"type": "error", "msg": "Objeto não encontrado."}); return
        if not self._adjacente_a_decor(p["pos"], d):
            await self.send_to(pid, {"type": "error", "msg": "Muito longe do objeto!"}); return
        meta = DECOR_TYPES[d["type"]]
        if meta["special"] == "fountain":
            if d.get("charges", 0) <= 0:
                await self.send_to(pid, {"type": "error", "msg": "💧 A fonte está seca."}); return
            item = copy.deepcopy(_TAVERN_BY_ID["garrafa_agua"])
            if self._add_to_inventory(p, item) == "full":
                await self.send_to(pid, {"type": "error", "msg": "Inventário cheio!"}); return
            d["charges"] -= 1
            await self.gm_say(f"💧 **{p['name']}** encheu uma **Garrafa de Água** na fonte ({d['charges']} restantes).")
            await self.push_state()
            return
        # container (loot) → tratado na Task A7
        await self._abrir_decor_loot(pid, d)
```

> `copy` já está importado no topo de `server.py` (usado por `deepcopy`). Se for `from copy import deepcopy`, troque por `deepcopy(_TAVERN_BY_ID["garrafa_agua"])`.

3c. Stub temporário para `_abrir_decor_loot` (será preenchido na A7), para o arquivo importar:

```python
    async def _abrir_decor_loot(self, pid, d):
        pass
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A6]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): fonte entrega garrafa de água com cargas limitadas"
```

---

## Task A7: Container — pegar loot (espelha baú)

**Files:**
- Modify: `server.py` — `_abrir_decor_loot` + `handle_take_from_decor`
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_container():
    print("\n[A7] container de loot")
    async def run():
        r = _room()
        loot = {"gold": 7, "items": server.hidratar_itens_bau([{"id": "health_potion"}])}
        r.decorations = [{"id": "d0", "type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": loot, "tem_loot": True}]
        r._rebuild_decor_index()
        p = make_player("p1", "Herói", "warrior", 0); p["pos"] = [4, 5]; p["gold"] = 0; p["bag"] = []; p["bag_size"] = 6; p["alive"] = True
        r.players = {"p1": p}
        await r.handle_take_from_decor("p1", "d0", "gold", 0)
        check("pegou 7 de ouro", p["gold"] == 7 and r.decorations[0]["loot"]["gold"] == 0)
        await r.handle_take_from_decor("p1", "d0", "item", 0)
        check("pegou o item", any(i["id"] == "health_potion" for i in p["bag"]))
        check("loot esvaziado → tem_loot False", r.decorations[0]["tem_loot"] is False)
    asyncio.run(run())
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `handle_take_from_decor` não existe.

- [ ] **Step 3: Implementar**

Substituir o stub `_abrir_decor_loot` e adicionar `handle_take_from_decor`:

```python
    async def _abrir_decor_loot(self, pid, d):
        """Abre o painel de loot da decoração (reusa o painel de baú no cliente)."""
        if not d.get("loot") or not d.get("tem_loot"):
            await self.send_to(pid, {"type": "error", "msg": "O objeto está vazio."}); return
        await self.send_to(pid, {"type": "decor_loot", "decor_id": d["id"],
                                  "gold": d["loot"]["gold"], "items": d["loot"]["items"]})

    def _decor_atualiza_tem_loot(self, d):
        l = d.get("loot")
        d["tem_loot"] = bool(l and (l["gold"] > 0 or l["items"]))

    async def handle_take_from_decor(self, pid, decor_id, kind, index):
        """Pega ouro/item de uma decoração-container (sem restrição de turno)."""
        p = self.players.get(pid)
        if not p or not p.get("alive"):
            return
        d = self._decor_by_id(decor_id)
        if not d or not d.get("loot"):
            await self.send_to(pid, {"type": "error", "msg": "Objeto sem loot."}); return
        if not self._adjacente_a_decor(p["pos"], d):
            await self.send_to(pid, {"type": "error", "msg": "Muito longe do objeto!"}); return
        loot = d["loot"]
        if kind == "gold":
            amount = loot["gold"]
            if amount <= 0:
                await self.send_to(pid, {"type": "error", "msg": "Sem ouro aqui."}); return
            p["gold"] += amount
            loot["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{amount}** ouros do objeto!")
        elif kind == "item":
            idx = int(index)
            if idx < 0 or idx >= len(loot["items"]):
                await self.send_to(pid, {"type": "error", "msg": "Item inválido."}); return
            item = loot["items"][idx]
            if self._add_to_inventory(p, item) == "full":
                await self.send_to(pid, {"type": "error", "msg": "Inventário cheio!"}); return
            loot["items"].pop(idx)
            await self.gm_say(f"🎒 **{p['name']}** pegou **{item['name']}** do objeto!")
        self._decor_atualiza_tem_loot(d)
        await self.push_state()
```

> **Nota de simplificação:** o cliente reaproveita o painel de baú existente, mas com `decor_id` em vez de `chest_id` e a mensagem `take_from_decor`. A munição empilhável (`effect == "ammo"`) usa a inserção simples aqui (`_add_to_inventory`); a lógica de empilhar do baú não é replicada (YAGNI — decorações raramente guardam munição).

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A7]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): containers de decoração entregam ouro/itens como baú"
```

---

## Task A8: Oclusão de visão (raycast nos altos)

**Files:**
- Modify: `server.py` — `_reveal_around` (~linha 3933) + helper de linha
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_visao():
    print("\n[A8] oclusão de visão dos altos")
    r = _room()
    # coluna (alta) em (4,2); herói em (2,2) revelando raio 3
    r.decorations = [{"id": "d0", "type": "coluna", "pos": [4, 2], "facing": [0, 1], "loot": None, "tem_loot": False}]
    r._rebuild_decor_index()
    r.explored = set()
    r._reveal_around(2, 2, radius=3)
    check("a própria coluna é revelada", (4, 2) in r.explored)
    check("casa atrás da coluna fica oculta", (5, 2) not in r.explored)
    check("casa ao lado (não ocluída) é revelada", (2, 4) in r.explored)
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `(5,2)` está em `explored` (sem oclusão).

- [ ] **Step 3: Implementar**

Substituir o corpo de `_reveal_around` por uma versão com raycast nos tiles altos:

```python
    def _tall_oclui_caminho(self, x0, y0, x1, y1):
        """True se a linha (x0,y0)→(x1,y1) cruza uma casa de decoração ALTA
        antes do destino (a própria casa-destino não conta)."""
        if not self._decor_tall_tiles:
            return False
        dx = x1 - x0; dy = y1 - y0
        passos = max(abs(dx), abs(dy))
        if passos == 0:
            return False
        for s in range(1, passos):   # casas intermediárias (exclui origem e destino)
            cx = round(x0 + dx * s / passos)
            cy = round(y0 + dy * s / passos)
            if (cx, cy) in self._decor_tall_tiles:
                return True
        return False

    def _reveal_around(self, px, py, radius=1):
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                x, y = px+dx, py+dy
                if self._tile_in_locked_room(x, y):
                    continue
                if self._tall_oclui_caminho(px, py, x, y):
                    continue
                self.explored.add((x, y))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A8]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): objetos altos ocluem a revelação de névoa (raycast)"
```

---

## Task A9: Serialização no `game_state`

**Files:**
- Modify: `server.py` — `push_state` (~linha 12458)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def test_serial():
    print("\n[A9] serialização game_state")
    r = _room()
    r.decorations = [{"id": "d0", "type": "estante", "pos": [3, 3], "facing": [1, 0],
                      "loot": {"gold": 0, "items": []}, "tem_loot": False}]
    r._rebuild_decor_index()
    payload = r._serializar_decoracoes()
    check("1 item serializado", len(payload) == 1)
    d0 = payload[0]
    check("tem type/pos/facing/tiles/tem_loot/alto/pisavel",
          all(k in d0 for k in ("id", "type", "pos", "facing", "tiles", "tem_loot", "alto", "pisavel", "special")))
    check("tiles resolvidos (2 casas, horizontal)", sorted(map(tuple, d0["tiles"])) == [(3, 3), (4, 3)])
    check("não vaza loot detalhado", "loot" not in d0)
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — `_serializar_decoracoes` não existe.

- [ ] **Step 3: Implementar**

3a. Helper na classe `GameRoom`:

```python
    def _serializar_decoracoes(self):
        """Payload de render do cliente (sem vazar o conteúdo do loot)."""
        out = []
        for d in self.decorations:
            meta = DECOR_TYPES[d["type"]]
            out.append({
                "id": d["id"], "type": d["type"], "pos": d["pos"],
                "facing": d.get("facing", [0, 1]),
                "tiles": self._decor_tiles(d),
                "tem_loot": bool(d.get("tem_loot")),
                "charges": d.get("charges"),
                "alto": meta["alto"], "pisavel": meta["pisavel"],
                "special": meta["special"], "emoji": meta["emoji"],
                "size": meta["size"],
            })
        return out
```

3b. Em `push_state`, na construção do dict, adicionar (perto de `"chests": list(self.chests.values()),`):

```python
            "decorations": self._serializar_decoracoes(),
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A9]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): incluir decorações no payload game_state"
```

---

## Task A10: Validação no `validar_dungeon`

**Files:**
- Modify: `server.py` — `validar_dungeon` (após o bloco de `traps`, ~linha 1762)
- Test: `tools/test_decoracoes.py`

- [ ] **Step 1: Escrever o teste**

Adicionar:

```python
def _defn_base():
    return {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 12, "h": 12},
        "tiles": [[FLOOR] * 12 for _ in range(12)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": None, "prisoner": None,
        "monsters": [], "chests": [], "traps": [], "decorations": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }

def test_validacao():
    print("\n[A10] validação")
    d = _defn_base()
    d["decorations"] = [{"type": "cama", "pos": [3, 3], "facing": [0, 1], "loot": None}]
    ok, msg = server.validar_dungeon(d)
    check(f"válida com cama em chão ({msg})", ok is True)
    # tipo inválido
    d["decorations"] = [{"type": "xyz", "pos": [3, 3], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d); check("rejeita tipo desconhecido", ok is False)
    # footprint em parede
    d2 = _defn_base()
    d2["tiles"][4][3] = WALL
    d2["decorations"] = [{"type": "cama", "pos": [3, 3], "facing": [0, 1]}]  # ocupa (3,3) e (3,4)→parede
    ok, _ = server.validar_dungeon(d2); check("rejeita footprint sobre parede", ok is False)
    # sobreposição entre decorações
    d3 = _defn_base()
    d3["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1]},
                         {"type": "barril", "pos": [5, 5], "facing": [0, 1]}]
    ok, _ = server.validar_dungeon(d3); check("rejeita sobreposição", ok is False)
    # item de loot inválido
    d4 = _defn_base()
    d4["decorations"] = [{"type": "barril", "pos": [5, 5], "facing": [0, 1], "loot": {"gold": 0, "items": [{"id": "nope"}]}}]
    ok, _ = server.validar_dungeon(d4); check("rejeita item de loot inválido", ok is False)
    # fora do grid
    d5 = _defn_base()
    d5["decorations"] = [{"type": "fonte", "pos": [11, 11], "facing": [0, 1]}]  # 2x2 sai do grid
    ok, _ = server.validar_dungeon(d5); check("rejeita footprint fora do grid", ok is False)
```

E chamar em `main()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_decoracoes.py`
Expected: FAIL — validação ainda não checa `decorations` (alguns casos passam indevidamente).

- [ ] **Step 3: Implementar**

3a. Em `validar_dungeon`, **antes** do `return True, "ok"` final, mas após o bloco de `traps`/`prisoner`, adicionar:

```python
    decors = defn.get("decorations", [])
    if not isinstance(decors, list):
        return False, "decorations deve ser uma lista."
    grid_w = defn["grid"]["w"]; grid_h = defn["grid"]["h"]
    ocupadas = set()
    for de in decors:
        if not isinstance(de, dict):
            return False, "cada decoração deve ser um objeto JSON."
        dtype = de.get("type")
        meta = DECOR_TYPES.get(dtype)
        if not meta:
            return False, f"decoração tipo desconhecido: {dtype!r}."
        pos = de.get("pos")
        if not (isinstance(pos, list) and len(pos) == 2):
            return False, f"decoração com pos inválida: {pos!r}."
        facing = de.get("facing") or [0, 1]
        w, h = meta["size"]
        ew, eh = (h, w) if (facing and facing[0] != 0) else (w, h)
        for i in range(ew):
            for j in range(eh):
                tx, ty = pos[0] + i, pos[1] + j
                if not (0 <= tx < grid_w and 0 <= ty < grid_h):
                    return False, f"decoração {dtype} fora do grid em ({tx},{ty})."
                if tile_at([tx, ty]) != FLOOR:
                    return False, f"decoração {dtype} precisa estar sobre chão em ({tx},{ty})."
                if (tx, ty) in ocupadas:
                    return False, f"decorações sobrepostas em ({tx},{ty})."
                ocupadas.add((tx, ty))
        loot = de.get("loot")
        if loot is not None:
            if not meta["loot_capaz"]:
                return False, f"decoração {dtype} não pode conter loot."
            for it in (loot.get("items") or []):
                if not isinstance(it, dict) or it.get("id") not in _DUNGEON_ITEM_CATALOG:
                    return False, f"item de loot inválido: {it!r}."
        if meta["special"] == "fountain":
            ch = de.get("charges", 0)
            if isinstance(ch, bool) or not isinstance(ch, int) or ch < 0:
                return False, "fonte com charges inválido."
```

> Verifique que `tile_at`, `FLOOR`, `_DUNGEON_ITEM_CATALOG` e `DECOR_TYPES` estão no escopo de `validar_dungeon` (todos são módulo-nível ou já usados na função — `tile_at` é definido internamente; confirme lendo o início da função).

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_decoracoes.py`
Expected: PASS em `[A10]`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_decoracoes.py
git commit -m "feat(decor): validar decorações (tipo, footprint em chão, loot, cargas)"
```

---

## Task A11: Dispatch das mensagens

**Files:**
- Modify: `server.py` — bloco de dispatch (perto de `take_from_chest`, ~linha 12757)
- Test: manual (handlers já testados nas A6/A7)

- [ ] **Step 1: Implementar**

No bloco `elif t == ...` do handler de conexão, perto de `take_from_chest`, adicionar:

```python
                elif t == "interagir_decor":
                    if room: await room.handle_interagir_decor(pid, msg.get("decor_id"))

                elif t == "take_from_decor":
                    if room: await room.handle_take_from_decor(
                        pid, msg.get("decor_id"), msg.get("kind"), msg.get("index", 0))
```

- [ ] **Step 2: Verificar import OK**

Run: `python -c "import server; print('ok')"`
Expected: `ok` (sem erro de sintaxe).

- [ ] **Step 3: Rodar a suíte inteira**

Run: `python tools/test_decoracoes.py`
Expected: `=== N passou, 0 falhou ===`

- [ ] **Step 4: Commit**

```bash
git add server.py
git commit -m "feat(decor): rotear mensagens interagir_decor e take_from_decor"
```

---

# FASE B — Editor

## Task B1: Exportar `decorations` para o catálogo

**Files:**
- Modify: `tools/export_catalog.py` — `build_catalog`
- Modify: `tools/test_export_catalog.py`
- Regenerate: `tools/editor_catalog.js`

- [ ] **Step 1: Escrever o teste**

Em `tools/test_export_catalog.py`, dentro de `main()` (após as checagens existentes), adicionar:

```python
    print("\n[decor] decorações exportadas")
    check("catálogo tem 'decorations'", "decorations" in cat)
    check("22 decorações", len(cat.get("decorations", [])) == 22)
    check("toda decoração tem type/nome/emoji/size/gira/alto/pisavel/loot_capaz/special",
          all(set(("type", "nome", "emoji", "size", "gira", "alto", "pisavel", "loot_capaz", "special")) <= set(d)
              for d in cat.get("decorations", [])))
    check("fonte exportada como fountain",
          any(d["type"] == "fonte" and d["special"] == "fountain" for d in cat["decorations"]))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_export_catalog.py`
Expected: FAIL — `cat` não tem `decorations`.

- [ ] **Step 3: Implementar**

Em `tools/export_catalog.py`, dentro de `build_catalog`, antes do `return`, adicionar:

```python
    decorations = []
    for dtype, meta in server.DECOR_TYPES.items():
        decorations.append({
            "type": dtype, "nome": meta["nome"], "emoji": meta["emoji"],
            "size": meta["size"], "gira": meta["gira"], "alto": meta["alto"],
            "pisavel": meta["pisavel"], "loot_capaz": meta["loot_capaz"],
            "special": meta["special"],
        })
```

E mudar o `return` para incluir a chave:

```python
    return {"monsters": monsters, "items": items, "traps": traps,
            "venoms": venoms, "decorations": decorations}
```

- [ ] **Step 4: Regenerar e ver passar**

Run: `python tools/export_catalog.py`
Run: `python tools/test_export_catalog.py`
Expected: PASS, incluindo `[decor]`.

- [ ] **Step 5: Commit**

```bash
git add tools/export_catalog.py tools/test_export_catalog.py tools/editor_catalog.js tools/editor_dungeons.js
git commit -m "feat(editor): exportar catálogo de decorações"
```

---

## Task B2: Estado e ferramenta de decoração no editor

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Adicionar estado e default do catálogo**

No objeto `CAT` default (linha 4), incluir `decorations: []`:

```javascript
  const CAT = window.EDITOR_CATALOG || { monsters: [], items: [], traps: [], venoms: [], decorations: [] };
```

No objeto de estado `S` (linha 6-15), adicionar campos:

```javascript
    monsters: [], chests: [], traps: [], decorations: [],
```
```javascript
    tool: "wall", sel: null,
    decorType: (CAT.decorations[0] || {}).type || "cama",
    decorFacing: [0, 1],
```

- [ ] **Step 2: Helper de footprint (espelha o servidor)**

Adicionar perto do topo do IIFE (após `initGrid`):

```javascript
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
```

- [ ] **Step 3: Ferramenta na toolbar + seletor de tipo**

Em `TOOLS` (linha 71), adicionar na lista do grupo `entidades`:

```javascript
    { id: "decor", label: "decoração", group: "entidades" },
```

Em `buildToolbar`, ao final (após o laço), inserir um `<select>` de tipo quando a ferramenta for `decor`:

```javascript
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
```

- [ ] **Step 4: Verificação manual**

Abrir `tools/editor.html` no browser (via `python server.py` → `http://localhost:8765/tools/editor.html`, ou abrir o arquivo conforme o fluxo atual do editor). Selecionar a ferramenta "decoração": deve aparecer o `<select>` com os 22 tipos e o botão "girar 90°".

- [ ] **Step 5: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): ferramenta de decoração + seletor de tipo e botão girar"
```

---

## Task B3: Colocar, girar e desenhar decorações

**Files:**
- Modify: `tools/editor.js`

- [ ] **Step 1: Rotação (botão + tecla R)**

Adicionar funções:

```javascript
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
```

- [ ] **Step 2: Colocar (footprint cabe em chão, sem sobrepor)**

Adicionar helper de checagem e o caso de colocação:

```javascript
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
                loot: (m && m.type === "arca_tesouros") ? { gold: 0, items: [] } : null };
    if (m && m.special === "fountain") d.charges = 3;
    S.decorations.push(d);
    S.sel = { kind: "decor", ref: d, pos: [x, y] };
  }
```

Em `placeEntity` (linha 154), adicionar um `case`:

```javascript
      case "decor": placeDecor(x, y); break;
```

E no `mousedown` (linha 335), incluir `"decor"` na lista de ferramentas que colocam:

```javascript
    else if (["entrance", "exit", "prisoner", "monster", "chest", "trap", "decor"].includes(S.tool)) { placeEntity(x, y); if (S.tool !== "decor") S.sel = entityAt(x, y); renderPanel(); render(); }
```

> Para `decor`, `placeDecor` já define `S.sel`; por isso o `if` evita sobrescrever com `entityAt`.

- [ ] **Step 3: `entityAt`/`eraseAt` reconhecem decorações por footprint**

Em `entityAt` (linha 141), antes do `return ... || null;` final, adicionar:

```javascript
    const dec = S.decorations.find(d => decorTiles(d).some(c => c[0] === x && c[1] === y));
    if (dec) return { kind: "decor", ref: dec, pos: dec.pos.slice() };
```

Em `eraseAt` (linha 166), adicionar:

```javascript
    S.decorations = S.decorations.filter(d => !decorTiles(d).some(c => c[0] === x && c[1] === y));
```

- [ ] **Step 4: Desenhar no canvas**

Em `emojiForCell` (linha 26), antes do `return null;`, adicionar (emoji na âncora do footprint):

```javascript
    const dec = S.decorations.find(e => e.pos[0] === x && e.pos[1] === y);
    if (dec) { const m = decorMeta(dec.type); return m ? m.emoji : "🪑"; }
```

Em `render`, após o laço que desenha as salas e antes/depois dos emojis, desenhar o contorno do footprint de cada decoração (para mostrar a área ocupada). Adicionar logo após o bloco `for (const r of S.rooms) {...}`:

```javascript
    for (const d of S.decorations) {
      ctx.strokeStyle = "#6ad0a0"; ctx.lineWidth = 1;
      for (const [tx, ty] of decorTiles(d)) ctx.strokeRect(tx * CELL + 2, ty * CELL + 2, CELL - 5, CELL - 5);
    }
```

- [ ] **Step 5: Verificação manual**

No editor: escolher "Cama", girar com R (footprint alterna 1×2 ↔ 2×1), clicar para colocar (só cola em chão, sem sobrepor). Apagar remove a decoração inteira clicando em qualquer casa dela.

- [ ] **Step 6: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): colocar/girar/desenhar/apagar decorações com footprint"
```

---

## Task B4: Painel da decoração (loot + cargas)

**Files:**
- Modify: `tools/editor.js` — `renderPanel`

- [ ] **Step 1: Adicionar o ramo `decor` em `renderPanel`**

Em `renderPanel`, junto aos outros `else if (k === ...)`, adicionar antes do `else { panel.innerHTML = ... }` final:

```javascript
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
```

- [ ] **Step 2: Verificação manual**

Selecionar uma decoração colocada: o painel mostra tamanho/flags, botão girar (se aplicável), cargas (só fonte), e o toggle "contém loot" que revela ouro + itens. A arca de tesouros já vem com loot ligado.

- [ ] **Step 3: Commit**

```bash
git add tools/editor.js
git commit -m "feat(editor): painel de decoração com loot e cargas"
```

---

## Task B5: JSON roundtrip + validação do editor

**Files:**
- Modify: `tools/editor.js` — `buildJSON`, `loadJSON`, `validarEditor`
- Create: `dungeons/test_decoracoes.json`
- Create: `tools/test_decor_roundtrip.py`

- [ ] **Step 1: `buildJSON` emite `decorations`**

Em `buildJSON` (linha 375), adicionar ao objeto retornado (depois de `traps:`):

```javascript
      decorations: S.decorations.map(d => {
        const o = { type: d.type, pos: d.pos.slice(), facing: d.facing.slice() };
        o.loot = d.loot ? { gold: d.loot.gold | 0, items: d.loot.items.map(i => ({ id: i.id })) } : null;
        const m = decorMeta(d.type);
        if (m && m.special === "fountain") o.charges = d.charges | 0;
        return o;
      }),
```

- [ ] **Step 2: `loadJSON` lê `decorations`**

Em `loadJSON` (linha 450), após `S.traps = ...`, adicionar:

```javascript
    S.decorations = (obj.decorations || []).map(d => ({
      type: d.type, pos: d.pos.slice(), facing: (d.facing || [0, 1]).slice(),
      loot: d.loot ? { gold: d.loot.gold | 0, items: (d.loot.items || []).map(i => ({ id: i.id })) } : null,
      ...(d.charges !== undefined ? { charges: d.charges | 0 } : {}),
    }));
```

- [ ] **Step 3: `validarEditor` checa decorações**

Em `validarEditor` (linha 410), antes do `return { ok: ... }`, adicionar:

```javascript
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
```

> `items` já é o `Set` de ids de itens definido no início de `validarEditor`.

- [ ] **Step 4: Criar masmorra de amostra**

Criar `dungeons/test_decoracoes.json` (12×12, tudo chão dentro de uma sala, com algumas decorações):

```json
{
  "schema_version": 1,
  "id": "test_decoracoes",
  "name": "Teste de Decorações",
  "grid": { "w": 12, "h": 12 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [{ "id": 0, "x": 1, "y": 1, "w": 10, "h": 10, "role": "entrance", "locked": false, "doors": [] }],
  "entrance": { "x": 1, "y": 1 },
  "exit": null,
  "prisoner": null,
  "monsters": [],
  "chests": [],
  "traps": [],
  "decorations": [
    { "type": "cama", "pos": [2, 2], "facing": [0, 1], "loot": null },
    { "type": "fonte", "pos": [5, 5], "facing": [0, 1], "loot": null, "charges": 3 },
    { "type": "fogueira", "pos": [8, 3], "facing": [0, 1], "loot": null },
    { "type": "arca_tesouros", "pos": [3, 8], "facing": [0, 1], "loot": { "gold": 20, "items": [{ "id": "health_potion" }] } },
    { "type": "coluna", "pos": [7, 7], "facing": [0, 1], "loot": null }
  ],
  "objectives": { "primary": { "type": "kill_all" }, "secondary": [] }
}
```

- [ ] **Step 5: Teste de roundtrip**

Criar `tools/test_decor_roundtrip.py`:

```python
"""Roundtrip: a masmorra de amostra com decorações valida no servidor.
Roda da raiz: python tools/test_decor_roundtrip.py"""
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
    with open(os.path.join(base, "dungeons", "test_decoracoes.json"), encoding="utf-8") as f:
        d = json.load(f)
    ok, msg = server.validar_dungeon(d)
    check(f"amostra válida ({msg})", ok is True)
    check("tem 5 decorações", len(d["decorations"]) == 5)
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_decor_roundtrip.py`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/editor.js dungeons/test_decoracoes.json tools/test_decor_roundtrip.py
git commit -m "feat(editor): JSON roundtrip + validação de decorações"
```

---

# FASE C — Renderização e cliente

## Task C1: Estado do cliente (`gameState.js`)

**Files:**
- Modify: `src/gameState.js`

- [ ] **Step 1: Localizar o padrão existente**

Run: `grep -n "chests\|get chests\|decorations" src/gameState.js`
Expected: ver como `chests` é exposto (getter sobre `gameState`) e replicar para `decorations`.

- [ ] **Step 2: Adicionar getter + helper + senders**

Onde os getters de estado são definidos (junto de `chests`), adicionar um getter `decorations` que lê `gameState.decorations` (default `[]`).

Adicionar helper puro (espelha o servidor):

```javascript
  function decorTilesOf(d) {
    // o servidor já manda d.tiles resolvido; se faltar, calcula pelo size/facing
    if (Array.isArray(d.tiles)) return d.tiles;
    const [w, h] = d.size || [1, 1];
    const [ew, eh] = (d.facing && d.facing[0] !== 0) ? [h, w] : [w, h];
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([d.pos[0] + i, d.pos[1] + j]);
    return out;
  }
```

Adicionar senders (junto dos demais action senders, ex.: o que envia `take_from_chest`):

```javascript
  function interagirDecor(decorId) { send({ type: "interagir_decor", decor_id: decorId }); }
  function takeFromDecor(decorId, kind, index) { send({ type: "take_from_decor", decor_id: decorId, kind, index }); }
```

Expor no objeto público `GS` (junto de `decorations`, `decorTilesOf`, `interagirDecor`, `takeFromDecor`).

> Siga exatamente o estilo de export do módulo (como `chests`, `move`, etc. são expostos). **Não** referenciar DOM/THREE aqui (regra do `CLAUDE.md`).

- [ ] **Step 3: Verificação**

Run: `python -c "print('js sem runner; checagem manual no browser')"`
No browser (jogo rodando com a masmorra de amostra), no console: `GS.decorations` retorna o array; `GS.decorTilesOf(GS.decorations[0])` retorna as casas.

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js
git commit -m "feat(decor): estado de decorações no cliente (getter + senders)"
```

---

## Task C2: Render 2D (`game.js`)

**Files:**
- Modify: `game.js` — função de desenho 2D do canvas

- [ ] **Step 1: Localizar o desenho 2D de baús**

Run: `grep -n "chests\|drawChest\|🧰\|function draw2D\|drawBoard2D" game.js`
Expected: achar onde os baús/entidades são desenhados no canvas 2D.

- [ ] **Step 2: Desenhar decorações**

No mesmo laço/local onde baús são desenhados no 2D, adicionar o desenho das decorações: para cada `d` em `GS.decorations`, desenhar o emoji (`d.emoji`) no centro do footprint (média das casas de `GS.decorTilesOf(d)`), e um leve preenchimento/contorno nas casas ocupadas. Use a mesma API de canvas (cellSize, offset) já usada para baús. Exemplo de trecho (adapte aos nomes locais `ctx`, `CELL`, `ox`, `oy`):

```javascript
  for (const d of GS.decorations) {
    const tiles = GS.decorTilesOf(d);
    // preenchimento sutil das casas
    ctx.fillStyle = "rgba(120,200,160,0.12)";
    for (const [tx, ty] of tiles) ctx.fillRect(ox + tx * CELL, oy + ty * CELL, CELL, CELL);
    // emoji no centro do footprint
    const cx = ox + (tiles.reduce((s, t) => s + t[0], 0) / tiles.length + 0.5) * CELL;
    const cy = oy + (tiles.reduce((s, t) => s + t[1], 0) / tiles.length + 0.5) * CELL;
    ctx.font = `${Math.floor(CELL * 0.8)}px sans-serif`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(d.emoji || "🪑", cx, cy);
  }
```

- [ ] **Step 3: Verificação manual (preview)**

Subir o jogo (`python server.py`), entrar com a masmorra de amostra `test_decoracoes` e confirmar no modo 2D que cama/fonte/fogueira/arca/coluna aparecem nas casas certas, com a cama ocupando 2 casas e a fonte 4.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(decor): render 2D das decorações (emoji + footprint)"
```

---

## Task C3: Render 3D procedural (`game.js`)

**Files:**
- Modify: `game.js` — sincronização de meshes 3D

- [ ] **Step 1: Localizar a sincronização de meshes (baús/monstros)**

Run: `grep -n "chestMeshes\|doorMeshes\|function sync3D\|THREE.BoxGeometry\|scene.add" game.js`
Expected: achar o ponto onde meshes são criados/atualizados por frame a partir do estado (ex.: `doorMeshes`, `chestMeshes`).

- [ ] **Step 2: Mapa de geometria procedural por tipo**

Adicionar uma tabela que descreve a forma 3D de cada tipo (altura e cor; caixa por padrão, cilindro para coluna/barril/fonte):

```javascript
  const DECOR_3D = {
    cama:           { shape: "box", h: 0.5,  color: 0x8a5a3c },
    lareira:        { shape: "box", h: 0.8,  color: 0x6b6b6b },
    fonte:          { shape: "cyl", h: 0.6,  color: 0x5a8fb0 },
    fogueira:       { shape: "cyl", h: 0.25, color: 0xd2691e },
    tumba:          { shape: "box", h: 0.6,  color: 0x777777 },
    mesa_cadeiras:  { shape: "box", h: 0.6,  color: 0x9a6b3c },
    estante:        { shape: "box", h: 1.6,  color: 0x6b4a2a },
    carroca:        { shape: "box", h: 0.7,  color: 0x7a5230 },
    coluna:         { shape: "cyl", h: 1.8,  color: 0xaaaaaa },
    barril:         { shape: "cyl", h: 0.8,  color: 0x8a5a2a },
    arca_tesouros:  { shape: "box", h: 0.6,  color: 0xc8a23a },
    cama_casal:     { shape: "box", h: 0.5,  color: 0x8a5a3c },
    estante_livros: { shape: "box", h: 1.6,  color: 0x5a3a1a },
    altar:          { shape: "box", h: 0.9,  color: 0x9a9aae },
    trono:          { shape: "box", h: 1.2,  color: 0xc8a23a },
    gaiola:         { shape: "box", h: 1.5,  color: 0x555555 },
    grades_prisao:  { shape: "box", h: 1.5,  color: 0x555555 },
    estante_armas:  { shape: "box", h: 1.6,  color: 0x6b4a2a },
    mesa_tortura:   { shape: "box", h: 0.6,  color: 0x7a4a4a },
    mesa_quimica:   { shape: "box", h: 0.7,  color: 0x4a7a6a },
    arvore:         { shape: "cyl", h: 1.8,  color: 0x2e7d32 },
    arvore_grande:  { shape: "cyl", h: 2.6,  color: 0x1b5e20 },
  };
```

- [ ] **Step 3: Sincronizar meshes por id**

No mesmo padrão de `chestMeshes`/`doorMeshes`, adicionar um dicionário `decorMeshes = {}` (declarar junto dos outros) e, no laço de sincronização por frame, criar/atualizar uma mesh por decoração. Use o footprint para dimensionar e centralizar (mesma conversão grid→mundo usada pelas outras meshes; aqui chamada `tileToWorld(x,y)`):

```javascript
  // dentro da função de sync 3D:
  const vistos = new Set();
  for (const d of GS.decorations) {
    vistos.add(d.id);
    const tiles = GS.decorTilesOf(d);
    const minX = Math.min(...tiles.map(t => t[0])), maxX = Math.max(...tiles.map(t => t[0]));
    const minY = Math.min(...tiles.map(t => t[1])), maxY = Math.max(...tiles.map(t => t[1]));
    const wCells = maxX - minX + 1, hCells = maxY - minY + 1;
    const spec = DECOR_3D[d.type] || { shape: "box", h: 0.6, color: 0x999999 };
    let mesh = decorMeshes[d.id];
    if (!mesh) {
      const geo = spec.shape === "cyl"
        ? new THREE.CylinderGeometry(0.4, 0.4, spec.h, 16)
        : new THREE.BoxGeometry(1, spec.h, 1);
      mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: spec.color }));
      mesh.userData.isDecor = true;
      mesh.userData.decorId = d.id;
      scene.add(mesh);
      decorMeshes[d.id] = mesh;
    }
    // centro do footprint em mundo
    const c = tileToWorld((minX + maxX) / 2, (minY + maxY) / 2);
    mesh.position.set(c.x, spec.h / 2, c.z);
    // escala para cobrir o footprint (box); cilindros mantêm raio fixo
    if (spec.shape === "box") mesh.scale.set(wCells * 0.9, 1, hCells * 0.9);
  }
  // remover meshes de decorações que sumiram
  for (const id of Object.keys(decorMeshes)) {
    if (!vistos.has(id)) { scene.remove(decorMeshes[id]); delete decorMeshes[id]; }
  }
```

> Ajuste `tileToWorld` para o nome real do helper grid→mundo no `game.js` (procure como as meshes de baú/porta convertem tile em coordenada). Não esqueça de declarar `const decorMeshes = {};` no mesmo escopo de `chestMeshes`.

- [ ] **Step 4: Verificação manual (preview)**

No modo 3D, confirmar blocos/cilindros nas casas certas; coluna/árvores altas; fonte/fogueira como cilindros baixos; cama/arca como caixas.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(decor): render 3D procedural das decorações"
```

---

## Task C4: Interação por clique (fonte/loot)

**Files:**
- Modify: `game.js` — handlers de clique 2D e 3D + reuso do painel de baú

- [ ] **Step 1: Localizar clique em tile/baú e o painel de baú**

Run: `grep -n "take_from_chest\|chest_id\|openChestPanel\|onTileClick\|raycaster\|isDecor" game.js`
Expected: achar o handler de clique (2D e 3D) e o painel que lista ouro/itens do baú (reage à mensagem do servidor).

- [ ] **Step 2: Reagir à mensagem `decor_loot`**

Onde o cliente registra callbacks (`GS.on(...)`), registrar o painel de loot da decoração reusando o **mesmo** componente do baú, mas chamando `GS.takeFromDecor(decorId, kind, index)` em vez de `take_from_chest`. Adicionar:

```javascript
  GS.on("decor_loot", (msg) => {
    // reaproveita o painel de baú: msg.gold, msg.items, e decor_id
    abrirPainelLoot({
      titulo: "Objeto",
      gold: msg.gold,
      items: msg.items,
      onPegarOuro: () => GS.takeFromDecor(msg.decor_id, "gold", 0),
      onPegarItem: (i) => GS.takeFromDecor(msg.decor_id, "item", i),
    });
  });
```

> Se o painel de baú atual não estiver fatorado em `abrirPainelLoot`, extraia-o para essa função reutilizável (parametrizando os callbacks e o título) e faça o baú e a decoração usarem a mesma função. Esse refactor pequeno mantém DRY.

- [ ] **Step 3: Clique numa decoração dispara a interação**

No handler de clique (2D: a partir do tile; 3D: a partir do raycast que detecta `mesh.userData.isDecor`/`decorId`), quando o alvo for uma decoração:
- Encontrar `d` em `GS.decorations` cujo footprint contém o tile clicado (2D) ou cujo `id === mesh.userData.decorId` (3D).
- Verificar adjacência do herói ativo (o servidor revalida; aqui é só UX). Chamar `GS.interagirDecor(d.id)`.

Trecho 2D (dentro do handler de clique de tile, antes do fallback de movimento):

```javascript
    const decClick = GS.decorations.find(d => GS.decorTilesOf(d).some(t => t[0] === tileX && t[1] === tileY));
    if (decClick) { GS.interagirDecor(decClick.id); return; }
```

Trecho 3D (no raycast, ao detectar a mesh de decoração):

```javascript
    if (hit.object.userData.isDecor) { GS.interagirDecor(hit.object.userData.decorId); return; }
```

> Para a **fonte**, `interagir_decor` já entrega a garrafa (sem abrir painel). Para **containers**, o servidor responde `decor_loot` e o painel abre. Decorações sem loot e não-fonte: o servidor responde "objeto vazio" (erro benigno) — opcional: no cliente, só chamar `interagirDecor` se `d.tem_loot || d.special === "fountain"`.

Refinar para evitar erro à toa:

```javascript
    const decClick = GS.decorations.find(d => GS.decorTilesOf(d).some(t => t[0] === tileX && t[1] === tileY));
    if (decClick) {
      if (decClick.tem_loot || decClick.special === "fountain") GS.interagirDecor(decClick.id);
      return;
    }
```

- [ ] **Step 4: Verificação manual (preview)**

Com a masmorra de amostra: andar até a fonte e clicar → recebe Garrafa de Água (cargas caem de 3 a 0); clicar na arca → abre o painel e permite pegar 20 de ouro + poção; pisar na fogueira → toma 1d4 (dado animado); a cama/coluna bloqueiam a passagem; atrás da coluna a névoa não revela.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(decor): clique interage com fonte (bebe) e containers (loot)"
```

---

# Encerramento

- [ ] **Rodar toda a suíte relacionada**

```bash
python tools/test_decoracoes.py
python tools/test_decor_roundtrip.py
python tools/test_export_catalog.py
python tools/test_roundtrip_editor.py
```
Expected: todos `0 falhou`.

- [ ] **Atualizar documentação**

Adicionar uma linha na seção de protocolo do `CLAUDE.md` (Client→Server) para `interagir_decor` e `take_from_decor`, e em Server→Client para `decor_loot`; e mencionar `game_state.decorations` e o sistema de decorações no parágrafo de estado. Commitar.

- [ ] **Verificação final no app**

Subir o jogo, jogar a masmorra de amostra e confirmar: footprint/rotação no editor, bloqueio, fogueira, fonte, container, oclusão de visão e render 2D/3D.

---

## Notas de revisão (self-review)

- **Cobertura do spec:** Fase A cobre catálogo (A1), footprint/rotação (A2), carga/reset (A3), bloqueio (A4), fogueira (A5), fonte (A6), container (A7), oclusão de visão (A8), game_state (A9), validação (A10), dispatch (A11). Fase B cobre export (B1), ferramenta/seletor (B2), colocar/girar/desenhar (B3), painel loot/cargas (B4), JSON+validação (B5). Fase C cobre estado (C1), 2D (C2), 3D (C3), interação (C4). Todos os requisitos do spec têm task.
- **GLB:** fora de escopo (3D procedural agora; estrutura `DECOR_3D`/`decorMeshes` pronta para trocar por loader GLB depois).
- **Consistência de tipos:** `_decor_tiles_at(dtype, ax, ay, facing)`, `_rebuild_decor_index`, `handle_interagir_decor`, `handle_take_from_decor`, `_serializar_decoracoes`, `GS.decorTilesOf`, `GS.interagirDecor`, `GS.takeFromDecor`, `decorMeshes`, `DECOR_3D` — nomes usados de forma idêntica entre tasks.
- **Pontos a confirmar durante a execução (não-bloqueantes):** os 3 commits de passo de monstro (A5) devem estar em contexto `async`; o nome real do helper grid→mundo no 3D (C3); a fatoração do painel de baú em `abrirPainelLoot` (C4). Cada task indica como verificar.
