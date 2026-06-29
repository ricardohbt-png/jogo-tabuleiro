# Materiais de chão e parede (cenários temáticos) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir pintar, por casa, o material de chão (cinza/terra/grama/pedra negra) e de parede (normal/enegrecida/caverna/desmoronada), além de um entulho que bloqueia movimento e visão — em 2D e 3D, com modelo de dados pronto para efeitos futuros (água etc.).

**Architecture:** Uma única camada esparsa `materiais` (`{"x,y": id}`) paralela a `tiles`, governada por um catálogo autoritativo `MATERIAIS` no `server.py`. Pisos coloridos são cosméticos; só `entulho` (`solido`+`oclui`) tem efeito, reusando os caminhos de bloqueio/oclusão já existentes das decorações. O cliente espelha solidez/opacidade no BFS/LOS para não divergir do servidor. Render (2D canvas + 3D Three.js) escolhe paleta por material. O editor ganha um pincel + balde de material.

**Tech Stack:** Python (`server.py`, `websockets`), Vanilla JS (`src/gameState.js`, `game.js`), Three.js r128, editor HTML/JS (`tools/editor.*`).

**Spec:** `docs/superpowers/specs/2026-06-29-materiais-piso-parede-design.md`

**Convenções de teste:** os testes do projeto são scripts próprios (sem pytest) rodados da raiz: `python tools/test_materiais.py`. Cada `check(nome, cond)` imprime ✅/❌ e conta PASS/FAIL. Os comandos `python ...` neste plano rodam **da raiz do worktree**.

---

## Fase 1 — Modelo de dados, catálogo, validação e payload (servidor)

### Task 1: Catálogo `MATERIAIS` no servidor

**Files:**
- Modify: `server.py` (logo após o bloco `DECOR_TYPES`, que termina na linha ~2163)
- Test: `tools/test_materiais.py` (Create)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_materiais.py`:

```python
"""Testes da camada de materiais de chão/parede.
Roda da raiz: python tools/test_materiais.py"""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, WALL, FLOOR, DOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_catalog():
    print("\n[M1] catálogo MATERIAIS")
    m = server.MATERIAIS
    for k in ("pedra_cinza", "terra", "grama", "pedra_negra", "entulho",
              "pedra_normal", "enegrecida", "pedra_caverna", "desmoronada"):
        check(f"{k} presente", k in m)
    check("pisos são categoria piso", all(m[k]["categoria"] == "piso"
          for k in ("pedra_cinza", "terra", "grama", "pedra_negra", "entulho")))
    check("paredes são categoria parede", all(m[k]["categoria"] == "parede"
          for k in ("pedra_normal", "enegrecida", "pedra_caverna", "desmoronada")))
    check("entulho é sólido e oclui", m["entulho"]["solido"] and m["entulho"]["oclui"])
    check("grama é cosmética (não sólida/oclui)",
          not m["grama"]["solido"] and not m["grama"]["oclui"])
    check("todo material tem nome/categoria/cor/solido/oclui", all(
          set(("nome", "categoria", "cor", "solido", "oclui")) <= set(v) for v in m.values()))
    check("defaults expostos",
          server.MATERIAIS_PISO_DEFAULT == "pedra_cinza"
          and server.MATERIAIS_PAREDE_DEFAULT == "pedra_normal")

if __name__ == "__main__":
    test_catalog()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_materiais.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute 'MATERIAIS'`.

- [ ] **Step 3: Implementar o catálogo**

Em `server.py`, logo após o fechamento de `DECOR_TYPES` (depois da linha `}` em ~2163), inserir:

```python
# ─── MATERIAIS DE CHÃO E PAREDE ──────────────────────────────────────────────
# Camada por-casa pintável no editor (game_state.materiais, mapa "x,y"->id).
# categoria: "piso" (válido em FLOOR/DOOR) ou "parede" (válido em WALL).
# solido: bloqueia movimento (espelhado no cliente). oclui: barra visão/névoa.
# cor: swatch do editor (a paleta rica de render vive no cliente). Pisos
# coloridos são cosméticos; só "entulho" tem efeito. Campos de efeito futuros
# (custo_mov, save_ao_entrar) entram aqui sem mudar o schema.
def _mat(nome, categoria, cor, solido=False, oclui=False):
    return {"nome": nome, "categoria": categoria, "cor": cor,
            "solido": solido, "oclui": oclui}

MATERIAIS = {
    "pedra_cinza":   _mat("Pedra cinza", "piso", "#6f6f78"),
    "terra":         _mat("Terra", "piso", "#6b4f33"),
    "grama":         _mat("Grama", "piso", "#3f6b2f"),
    "pedra_negra":   _mat("Pedra negra", "piso", "#23232a"),
    "entulho":       _mat("Entulho", "piso", "#4a4640", solido=True, oclui=True),
    "pedra_normal":  _mat("Pedra normal", "parede", "#5a5a6a"),
    "enegrecida":    _mat("Pedra enegrecida", "parede", "#2c2b30"),
    "pedra_caverna": _mat("Pedra de caverna", "parede", "#4d4338"),
    "desmoronada":   _mat("Parede desmoronada", "parede", "#534b40"),
}
MATERIAIS_PISO_DEFAULT = "pedra_cinza"
MATERIAIS_PAREDE_DEFAULT = "pedra_normal"
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_materiais.py`
Expected: PASS (todos ✅, exit 0).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_materiais.py
git commit -m "feat(materiais): catálogo autoritativo MATERIAIS (piso/parede) + teste"
```

---

### Task 2: Validação de `materiais` em `validar_dungeon`

**Files:**
- Modify: `server.py` — `validar_dungeon`, inserir antes de `return True, "ok"` (linha ~1845)
- Test: `tools/test_materiais.py` (adicionar `test_validacao`)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_materiais.py` (antes do bloco `if __name__`):

```python
def _defn_base():
    """Masmorra mínima válida 6x3 toda de chão com 1 sala de entrada."""
    return {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 6, "h": 3},
        "tiles": [[FLOOR] * 6 for _ in range(3)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 6, "h": 3, "role": "entrance",
                   "locked": False, "doors": []}],
        "entrance": {"x": 0, "y": 0},
    }

def test_validacao():
    print("\n[M2] validação de materiais")
    import copy
    base = _defn_base()
    ok, _ = server.validar_dungeon(copy.deepcopy(base))
    check("base válida (sem materiais)", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "grama"}
    ok, _ = server.validar_dungeon(d)
    check("piso em chão é válido", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "inexistente"}
    ok, msg = server.validar_dungeon(d)
    check("material desconhecido recusado", not ok and "material" in msg.lower())

    d = copy.deepcopy(base); d["materiais"] = {"9,9": "grama"}
    ok, _ = server.validar_dungeon(d)
    check("material fora do grid recusado", not ok)

    d = copy.deepcopy(base)
    d["tiles"][1][1] = WALL
    d["materiais"] = {"1,1": "grama"}   # piso em parede
    ok, _ = server.validar_dungeon(d)
    check("piso em casa de parede recusado", not ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "pedra_normal"}  # parede em chão
    ok, _ = server.validar_dungeon(d)
    check("parede em casa de chão recusada", not ok)

    d = copy.deepcopy(base)
    d["tiles"][1][1] = WALL
    d["materiais"] = {"1,1": "enegrecida"}
    # entrada (0,0) ainda é chão e há ≥6 chão? grid 6x3=18, menos 1 parede = 17 ok
    ok, _ = server.validar_dungeon(d)
    check("parede em casa de parede é válida", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "entulho"}  # entulho é piso sólido em chão
    ok, _ = server.validar_dungeon(d)
    check("entulho em chão é válido", ok)

    d = copy.deepcopy(base); d["materiais"] = "naoeobjeto"
    ok, _ = server.validar_dungeon(d)
    check("materiais não-objeto recusado", not ok)
```

E no `__main__`, adicionar `test_validacao()` após `test_catalog()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_materiais.py`
Expected: FAIL — "material desconhecido recusado", "piso em casa de parede recusado" etc. falham (validação ainda não existe; o campo é ignorado).

- [ ] **Step 3: Implementar a validação**

Em `server.py`, dentro de `validar_dungeon`, **imediatamente antes** de `    return True, "ok"` (linha ~1845), inserir:

```python
    mats = defn.get("materiais")
    if mats is not None:
        if not isinstance(mats, dict):
            return False, "materiais deve ser um objeto (mapa 'x,y' -> id)."
        for key, mid in mats.items():
            meta = MATERIAIS.get(mid)
            if meta is None:
                return False, f"material desconhecido: {mid!r}."
            if not isinstance(key, str):
                return False, f"chave de material inválida: {key!r}."
            partes = key.split(",")
            if len(partes) != 2:
                return False, f"chave de material inválida: {key!r} (esperado 'x,y')."
            try:
                mx, my = int(partes[0]), int(partes[1])
            except ValueError:
                return False, f"chave de material inválida: {key!r} (esperado 'x,y')."
            if not (0 <= mx < w and 0 <= my < h):
                return False, f"material fora do grid em {key!r}."
            t = tiles[my][mx]
            if meta["categoria"] == "piso" and t not in (FLOOR, DOOR):
                return False, f"material de piso {mid!r} em casa não-chão ({mx},{my})."
            if meta["categoria"] == "parede" and t != WALL:
                return False, f"material de parede {mid!r} em casa não-parede ({mx},{my})."
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_materiais.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_materiais.py
git commit -m "feat(materiais): validação de materiais em validar_dungeon"
```

---

### Task 3: Carga, índices e payload de `materiais` no `GameRoom`

**Files:**
- Modify: `server.py` — `__init__` (~3185), `load_authored_dungeon` (~3716), `enter_dungeon` reset `nova` (~3863), novo método `_rebuild_materiais_index` (junto de `_rebuild_decor_index` ~10182), `_serializar_materiais` + `push_state` (~12828)
- Test: `tools/test_materiais.py` (adicionar `test_carga`)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_materiais.py`:

```python
def _room():
    async def _noop(*a, **k): pass
    r = GameRoom("TEST")
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop; r.push_state = _noop
    return r

def _defn_full():
    """6x3, chão todo, com entulho em (2,1) e grama em (3,1)."""
    d = _defn_base()
    d["materiais"] = {"2,1": "entulho", "3,1": "grama"}
    return d

def test_carga():
    print("\n[M3] carga/índices/payload de materiais")
    r = _room()
    r.load_authored_dungeon(_defn_full())
    check("materiais carregado com chave-tupla", r.materiais.get((2, 1)) == "entulho")
    check("índice sólido tem entulho", (2, 1) in r._mat_solid_tiles)
    check("índice opaco tem entulho", (2, 1) in r._mat_oclui_tiles)
    check("grama não é sólida nem opaca",
          (3, 1) not in r._mat_solid_tiles and (3, 1) not in r._mat_oclui_tiles)
    ser = r._serializar_materiais()
    check("serializa como 'x,y'->id", ser.get("2,1") == "entulho" and ser.get("3,1") == "grama")

    # compat retroativa: defn sem materiais
    r2 = _room()
    d2 = _defn_base()
    r2.load_authored_dungeon(d2)
    check("sem campo materiais → dict vazio", r2.materiais == {})
    check("sem materiais → índices vazios",
          r2._mat_solid_tiles == set() and r2._mat_oclui_tiles == set())
```

E no `__main__`, adicionar `test_carga()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_materiais.py`
Expected: FAIL — `AttributeError`/`r.materiais` ausente ou `_serializar_materiais` indefinido.

- [ ] **Step 3: Implementar carga, índices e payload**

3a. Em `__init__`, logo após `self._decor_tall_tiles = set()` (linha ~3186), inserir:

```python
        self.materiais = {}            # {(x,y): material_id} — camada de piso/parede
        self._mat_solid_tiles = set()  # casas de material sólido (entulho) — bloqueia
        self._mat_oclui_tiles = set()  # casas de material opaco (entulho) — barra visão
```

3b. Em `load_authored_dungeon`, logo após o bloco do `self.ambiente = ...` (linha ~3716), inserir:

```python
        # Camada de materiais (piso/parede pintável). Chaves "x,y"->id; descarta
        # entradas malformadas/desconhecidas (a validação já recusou antes).
        self.materiais = {}
        for key, mid in (defn.get("materiais") or {}).items():
            if mid not in MATERIAIS or not isinstance(key, str):
                continue
            partes = key.split(",")
            if len(partes) != 2:
                continue
            try:
                mx, my = int(partes[0]), int(partes[1])
            except ValueError:
                continue
            self.materiais[(mx, my)] = mid
        self._rebuild_materiais_index()
```

3c. Em `enter_dungeon`, no bloco `if nova:`, logo após `self._rebuild_decor_index()` (linha ~3864), inserir:

```python
            self.materiais = {}
            self._rebuild_materiais_index()
```

3d. Adicionar o método `_rebuild_materiais_index`, logo após `_rebuild_decor_index` (após a linha ~10195):

```python
    def _rebuild_materiais_index(self):
        """Recalcula os índices de bloqueio/visão da camada de materiais."""
        self._mat_solid_tiles = set()
        self._mat_oclui_tiles = set()
        for (x, y), mid in getattr(self, "materiais", {}).items():
            meta = MATERIAIS.get(mid)
            if not meta:
                continue
            if meta["solido"]:
                self._mat_solid_tiles.add((x, y))
            if meta["oclui"]:
                self._mat_oclui_tiles.add((x, y))
```

3e. Adicionar o método `_serializar_materiais`, logo após `_serializar_decoracoes` (procure por `def _serializar_decoracoes` ~10291 e insira depois dela):

```python
    def _serializar_materiais(self):
        """Camada de materiais como {"x,y": id} para o cliente."""
        return {f"{x},{y}": mid for (x, y), mid in getattr(self, "materiais", {}).items()}
```

3f. Em `push_state`, no dict de `game_state`, logo após a linha `"decorations": self._serializar_decoracoes(),` (linha ~12828), inserir:

```python
            "materiais": self._serializar_materiais(),
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_materiais.py`
Expected: PASS (todos os blocos M1–M3).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_materiais.py
git commit -m "feat(materiais): carga, índices e payload de materiais no GameRoom"
```

---

## Fase 2 — Gameplay do entulho (servidor) + lógica do cliente

### Task 4: Entulho bloqueia movimento e visão (servidor)

**Files:**
- Modify: `server.py` — `_blocks_tile` (~4139), `handle_move` (~4194), `_tall_oclui_caminho` (~4083), `_tem_linha_de_visao` (~4361)
- Test: `tools/test_materiais.py` (adicionar `test_entulho_servidor`)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_materiais.py`:

```python
def test_entulho_servidor():
    print("\n[M4] entulho bloqueia no servidor")
    r = _room()
    r.load_authored_dungeon(_defn_full())   # entulho em (2,1)
    check("_blocks_tile bloqueia entulho", r._blocks_tile(2, 1) is True)
    check("_blocks_tile não bloqueia grama", r._blocks_tile(3, 1) is False)
    # LOS horizontal cruzando o entulho em (2,1): de (0,1) a (4,1) deve falhar
    check("entulho barra LOS", r._tem_linha_de_visao([0, 1], [4, 1]) is False)
    # LOS numa linha sem entulho passa
    check("LOS livre na linha de cima", r._tem_linha_de_visao([0, 0], [4, 0]) is True)
    # Névoa: revelar a partir de (0,1) NÃO revela atrás do entulho na mesma linha
    r.explored = set()
    r._reveal_around(0, 1, radius=5)
    check("entulho oclui revelação atrás dele", (4, 1) not in r.explored)
    check("casa antes do entulho é revelada", (1, 1) in r.explored)
```

E no `__main__`, adicionar `test_entulho_servidor()`.

> Nota: `_reveal_around`/`_tem_linha_de_visao` exigem `self.rooms` (presente via `load_authored_dungeon`) e `self.map_w/map_h` (idem). `_tile_in_locked_room` percorre `self.rooms`; a sala única é `locked: False`, então não interfere.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_materiais.py`
Expected: FAIL — "entulho barra LOS", "_blocks_tile bloqueia entulho", "entulho oclui revelação" falham.

- [ ] **Step 3: Implementar o bloqueio/oclusão**

3a. `_blocks_tile` (linha ~4139): trocar
```python
        return (x, y) in self._decor_block_tiles
```
por
```python
        return (x, y) in self._decor_block_tiles or (x, y) in self._mat_solid_tiles
```

3b. `handle_move` — logo após o bloco que recusa `_decor_block_tiles` (linha ~4194-4196), inserir:
```python
        if (nx, ny) in self._mat_solid_tiles:
            await self.send_to(pid, {"type": "error", "msg": "Escombros bloqueiam o caminho."})
            return
```

3c. `_tall_oclui_caminho` (linhas ~4086 e ~4095): trocar o guard
```python
        if not self._decor_tall_tiles:
            return False
```
por
```python
        if not self._decor_tall_tiles and not self._mat_oclui_tiles:
            return False
```
e a checagem interna
```python
            if (cx, cy) in self._decor_tall_tiles:
                return True
```
por
```python
            if (cx, cy) in self._decor_tall_tiles or (cx, cy) in self._mat_oclui_tiles:
                return True
```

3d. `_tem_linha_de_visao` (linha ~4361): trocar
```python
            if self.tiles[y][x] == WALL or self._is_closed_door(x, y):
                return False
```
por
```python
            if (self.tiles[y][x] == WALL or self._is_closed_door(x, y)
                    or (x, y) in self._mat_oclui_tiles):
                return False
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_materiais.py`
Expected: PASS (M1–M4).

- [ ] **Step 5: Rodar a suíte vizinha para garantir não-regressão**

Run: `python tools/test_decoracoes.py`
Expected: PASS (decorações inalteradas).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_materiais.py
git commit -m "feat(materiais): entulho bloqueia movimento, LOS e revelação de névoa"
```

---

### Task 5: Cliente espelha solidez/opacidade no BFS/LOS

**Files:**
- Modify: `src/gameState.js` — constantes (~15), helpers + `_walkable` (~726), `_losBlocks` (~773), getter (~1367)

- [ ] **Step 1: Adicionar constantes espelhadas**

Em `src/gameState.js`, logo após `const TILE_WALL  = 0;` (linha ~15) e as demais constantes de tile, inserir:

```js
  // Espelha server.MATERIAIS (campos solido/oclui). Mantido mínimo de propósito:
  // só ids com efeito precisam constar. Atualize junto com o catálogo do servidor.
  const MATERIAIS_SOLIDOS = new Set(['entulho']);
  const MATERIAIS_OPACOS  = new Set(['entulho']);
```

- [ ] **Step 2: Adicionar helpers e usar em `_walkable`**

Logo acima de `function _walkable(` (linha ~726), inserir:

```js
  // Material sólido/opaco na casa (x,y), lido do game_state mais recente.
  function _matSolido(x, y) {
    const m = gameState && gameState.materiais;
    return !!(m && MATERIAIS_SOLIDOS.has(m[`${x},${y}`]));
  }
  function _matOpaco(x, y) {
    const m = gameState && gameState.materiais;
    return !!(m && MATERIAIS_OPACOS.has(m[`${x},${y}`]));
  }
```

Dentro de `_walkable`, logo após `if (!onFloor) return false;` (linha ~729), inserir:

```js
    if (_matSolido(x, y)) return false;   // entulho: intransponível como parede
```

- [ ] **Step 3: Usar em `_losBlocks`**

Em `_losBlocks` (linha ~773-776), trocar
```js
    return tiles[y][x] === TILE_WALL || closed.has(`${x},${y}`);
```
por
```js
    return tiles[y][x] === TILE_WALL || closed.has(`${x},${y}`) || _matOpaco(x, y);
```

- [ ] **Step 4: Expor getter**

No objeto de retorno do módulo, logo após `get decorations()     { return (gameState && gameState.decorations) || []; },` (linha ~1367), inserir:

```js
    get materiais()       { return (gameState && gameState.materiais) || {}; },
```

- [ ] **Step 5: Verificar carregamento sem erro de sintaxe**

Run: `python -c "import re,sys; s=open('src/gameState.js',encoding='utf-8').read(); print('MATERIAIS_SOLIDOS' in s and 'get materiais()' in s)"`
Expected: `True`

Verificação funcional acontece na Fase 3/4 com o app rodando (o preview de movimento não deve oferecer entrada em casa de entulho).

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js
git commit -m "feat(materiais): cliente trata entulho como parede no BFS e na LOS"
```

---

## Fase 3 — Render 2D (canvas top-down)

> O 2D usa funções procedurais por casa: `drawFloor3D` (linha ~5254), `drawWallTop3D` (~5481) e `drawWallSouthFace` (~5420). Vamos parametrizá-las por **paleta de material**. As paletas vivem numa tabela única no cliente.

### Task 6: Tabela de paletas 2D + piso colorido

**Files:**
- Modify: `game.js` — nova tabela `MAT_PALETTE_2D` (perto de `drawFloor3D`, antes da linha ~5253); `drawFloor3D` assinatura+uso; call site (~4766)

- [ ] **Step 1: Adicionar a tabela de paletas 2D**

Em `game.js`, imediatamente antes de `// ── DIABLO-STYLE FLOOR TILE` (linha ~5253), inserir:

```js
// ── PALETAS 2D DOS MATERIAIS ─────────────────────────────────────────────────
// base [r,g,b] da pedra/superfície; accent decide os detalhes procedurais.
// Espelha os ids de server.MATERIAIS. Pisos coloridos são cosméticos.
const MAT_PALETTE_2D = {
  // pisos
  pedra_cinza: { base: [44, 42, 50],  accent: 'stone' },
  terra:       { base: [74, 56, 38],  accent: 'dirt'  },
  grama:       { base: [46, 78, 40],  accent: 'grass' },
  pedra_negra: { base: [26, 25, 30],  accent: 'stone' },
  entulho:     { base: [70, 66, 58],  accent: 'rubble' },
  // paredes (topo)
  pedra_normal:  { base: [132, 130, 140], accent: 'wallStone' },
  enegrecida:    { base: [58, 56, 62],   accent: 'wallStone' },
  pedra_caverna: { base: [104, 92, 74],  accent: 'wallRough' },
  desmoronada:   { base: [96, 88, 76],   accent: 'wallRubble' },
};
// Resolve o material de uma casa para render (default por estrutura do tile).
function matDaCasa(state, x, y) {
  const m = state && state.materiais;
  const id = m && m[`${x},${y}`];
  if (id && MAT_PALETTE_2D[id]) return id;
  return (state.tiles[y][x] === TILE_WALL) ? 'pedra_normal' : 'pedra_cinza';
}
```

- [ ] **Step 2: Parametrizar `drawFloor3D` pela base do material**

Trocar a assinatura (linha ~5254):
```js
function drawFloor3D(ctx, x, y, isReachable, isAttackable, isWeaponPreview){
```
por
```js
function drawFloor3D(ctx, x, y, isReachable, isAttackable, isWeaponPreview, matId){
```

Logo no início do corpo (após `const h=...;` na linha ~5256), inserir:
```js
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_cinza;
  const [BR, BG, BB] = pal.base;
```

Trocar a linha que fixa a cor da pedra (linha ~5272):
```js
    const r0=Math.min(255,44+v), g0=Math.min(255,42+v), b0=Math.min(255,50+Math.floor(v*0.6));
```
por
```js
    const r0=Math.min(255,BR+v), g0=Math.min(255,BG+v), b0=Math.min(255,BB+Math.floor(v*0.6));
```

Logo após o bloco `// Dark moss patch` (depois da linha ~5312, ainda dentro do `for` de sub-slabs), inserir os detalhes específicos de grama/terra:
```js
    if(pal.accent==='grass' && ((sh%5)===2)){
      ctx.fillStyle='rgba(70,120,46,0.45)';
      const gx=bx+3+(sh%Math.max(1,bw-8|0)), gy=by+4+((sh>>2)%Math.max(1,bh-8|0));
      ctx.fillRect(gx, gy, 1.4, 4+(sh%3));        // tufo de grama
      ctx.fillRect(gx+2, gy+1, 1.2, 3+(sh%2));
    }
    if(pal.accent==='dirt' && ((sh%7)===1)){
      ctx.fillStyle='rgba(40,28,16,0.40)';
      ctx.beginPath(); ctx.arc(bx+5+(sh%Math.max(1,bw-10|0)),
        by+5+((sh>>3)%Math.max(1,bh-10|0)), 1.6+(sh%2), 0, Math.PI*2); ctx.fill();  // seixo
    }
```

- [ ] **Step 3: Passar o material no call site do PASS 1**

Em `renderMap3D` (PASS 1, linha ~4765-4766), trocar:
```js
    if(t===TILE_FLOOR || t===TILE_DOOR)
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`), attackable.has(`${x},${y}`), weaponRangeTiles.has(`${x},${y}`));
```
por
```js
    if(t===TILE_FLOOR || t===TILE_DOOR)
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`), attackable.has(`${x},${y}`), weaponRangeTiles.has(`${x},${y}`), matDaCasa(state, x, y));
```

- [ ] **Step 4: Verificar no app (2D)**

Iniciar o preview do app, entrar numa masmorra de teste e alternar para 2D. Como ainda não há editor de material, criar uma masmorra de teste com `materiais` à mão (ver Task 12 para o fluxo final) ou usar este atalho de verificação temporário no console do preview:
- `GS` não expõe setter de materiais; em vez disso, valide visualmente que o piso padrão continua **idêntico** ao atual (compat) — nenhuma casa pintada ainda.

Run (preview): recarregar a página, abrir masmorra existente, conferir 2D inalterado.
Expected: piso 2D idêntico ao de antes (regressão zero); nenhum erro no console.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(materiais): paletas 2D e piso colorido por material (drawFloor3D)"
```

---

### Task 7: Paredes 2D por material + entulho como escombro

**Files:**
- Modify: `game.js` — `drawWallTop3D` (~5481) e `drawWallSouthFace` (~5420) parametrizadas; call sites (PASS 2 ~4795, PASS 3 ~4803); entulho desenhado no PASS 1

- [ ] **Step 1: Parametrizar `drawWallTop3D`**

Trocar assinatura (linha ~5481):
```js
function drawWallTop3D(ctx, x, y){
```
por
```js
function drawWallTop3D(ctx, x, y, matId){
```
Após `const v=(h%18)-9;` (linha ~5484), inserir:
```js
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_normal;
  const [BR, BG, BB] = pal.base;
```
Trocar a cor fixa da pedra (linha ~5491):
```js
  const r0=Math.min(255,132+v), g0=Math.min(255,130+v), b0=Math.min(255,140+Math.floor(v*0.5));
```
por
```js
  const r0=Math.min(255,BR+v), g0=Math.min(255,BG+v), b0=Math.min(255,BB+Math.floor(v*0.5));
```
Imediatamente antes do fechamento `}` de `drawWallTop3D`, inserir o detalhe de "desmoronada" (juntas extras quebradas):
```js
  if(pal.accent==='wallRubble'){
    ctx.strokeStyle='rgba(0,0,0,0.45)'; ctx.lineWidth=1;
    for(let k=0;k<3;k++){
      const rx=X+4+((h>>(k*3))%Math.max(1,CELL-8)), ry=Y+4+((h>>(k*2))%Math.max(1,CELL-8));
      ctx.beginPath(); ctx.moveTo(rx,ry); ctx.lineTo(rx+5+(h%5), ry+3+(h%4)); ctx.stroke();
    }
  }
```

- [ ] **Step 2: Parametrizar `drawWallSouthFace` (cor base)**

Trocar assinatura (linha ~5420):
```js
function drawWallSouthFace(ctx, x, y){
```
por
```js
function drawWallSouthFace(ctx, x, y, matId){
```
Após `const h=...;` (linha ~5424), inserir:
```js
  const pal = MAT_PALETTE_2D[matId] || MAT_PALETTE_2D.pedra_normal;
  const [BR, BG, BB] = pal.base;
  const cmix=(dr,dg,db,a)=>`rgba(${Math.max(0,Math.min(255,BR+dr))},${Math.max(0,Math.min(255,BG+dg))},${Math.max(0,Math.min(255,BB+db))},${a})`;
```
Trocar as 3 paradas do gradiente da face (linhas ~5428-5430):
```js
  wfG.addColorStop(0,   'rgba(148,142,134,0.99)'); // top — lit face (light gray)
  wfG.addColorStop(0.30,'rgba(110,106,100,0.99)'); // mid
  wfG.addColorStop(0.68,'rgba(58,54,50,0.97)');    // lower — in shadow
```
por
```js
  wfG.addColorStop(0,    cmix(28, 26, 18, 0.99)); // top — lit face
  wfG.addColorStop(0.30, cmix(-6, -8, -14, 0.99)); // mid
  wfG.addColorStop(0.68, cmix(-50, -52, -54, 0.97)); // lower — shadow
```

- [ ] **Step 3: Passar material nos call sites das paredes**

PASS 2 (linha ~4794-4795):
```js
      if(sy<H && state.tiles[sy][x]===TILE_FLOOR && terrainSet.has(`${x},${sy}`))
        drawWallSouthFace(ctx, x, y);
```
→
```js
      if(sy<H && state.tiles[sy][x]===TILE_FLOOR && terrainSet.has(`${x},${sy}`))
        drawWallSouthFace(ctx, x, y, matDaCasa(state, x, y));
```
PASS 3 (linha ~4802-4803):
```js
    if(state.tiles[y][x]===TILE_WALL)
      drawWallTop3D(ctx, x, y);
```
→
```js
    if(state.tiles[y][x]===TILE_WALL)
      drawWallTop3D(ctx, x, y, matDaCasa(state, x, y));
```

- [ ] **Step 4: Desenhar entulho (em casa de chão) como escombro no PASS 1**

O entulho está numa casa **de chão**, então cai no PASS 1. Após desenhar o piso, sobrepor um monte de escombros. Em `renderMap3D`, no laço do PASS 1 (linha ~4762-4766), trocar:
```js
    if(t===TILE_FLOOR || t===TILE_DOOR)
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`), attackable.has(`${x},${y}`), weaponRangeTiles.has(`${x},${y}`), matDaCasa(state, x, y));
```
por
```js
    if(t===TILE_FLOOR || t===TILE_DOOR){
      const mid = matDaCasa(state, x, y);
      drawFloor3D(ctx, x, y, reachable.has(`${x},${y}`), attackable.has(`${x},${y}`), weaponRangeTiles.has(`${x},${y}`), mid);
      if(mid==='entulho') drawEntulho2D(ctx, x, y);
    }
```

E adicionar a função `drawEntulho2D`, logo após `drawFloor3D` (antes de `drawDoor2D`, linha ~5360):
```js
// ── ENTULHO 2D — monte de pedras desmoronadas (bloqueia movimento e visão) ───
function drawEntulho2D(ctx, x, y){
  const X=x*CELL, Y=y*CELL, h=((x*8161)^(y*5101))&0xFFFF;
  // base sombreada sob o monte
  ctx.fillStyle='rgba(0,0,0,0.35)';
  ctx.fillRect(X+2, Y+2, CELL-4, CELL-4);
  // pedras empilhadas
  const pedras=6;
  for(let i=0;i<pedras;i++){
    const sh=(h^(i*2917))&0xFFFF;
    const px=X+4+(sh%Math.max(1,CELL-12)), py=Y+5+((sh>>4)%Math.max(1,CELL-12));
    const rw=5+(sh%6), rh=4+((sh>>3)%5);
    const tone=70+((sh>>6)%40);
    ctx.fillStyle=`rgb(${tone},${tone-6},${tone-14})`;
    ctx.beginPath(); ctx.ellipse(px,py,rw,rh,(sh%6)*0.3,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=1; ctx.stroke();
    ctx.fillStyle='rgba(255,235,200,0.10)';  // brilho de tocha no topo
    ctx.fillRect(px-rw*0.5, py-rh*0.7, rw, 1.5);
  }
}
```

- [ ] **Step 5: Verificar no app (2D)**

Preview: abrir uma masmorra com material pintado à mão (ver Task 12) ou — se o editor ainda não existe — criar `dungeons/_teste_materiais.json` copiando uma masmorra válida e adicionando `"materiais": {"X,Y":"grama", "A,B":"entulho", "P,Q":"enegrecida"}` em casas coerentes. Entrar e alternar para 2D.
Expected: piso de grama esverdeado, parede enegrecida escura, e o entulho como monte de pedras; o preview de movimento não deixa andar sobre o entulho (Task 5); a névoa não revela atrás do entulho.

- [ ] **Step 6: Commit**

```bash
git add game.js
git commit -m "feat(materiais): paredes 2D por material + entulho como escombro (2D)"
```

---

## Fase 4 — Render 3D (Three.js)

> O 3D constrói uma `floorBaseMat`/`wallBaseMat` compartilhada e clona por casa, tingindo via `mat.color` (linhas ~10874, ~11074-11098). Vamos: (a) escolher cor base por material; (b) gerar uma textura por material (cache); (c) renderizar entulho como bloco altura-de-parede.

### Task 8: Cor 3D por material (piso e parede)

**Files:**
- Modify: `game.js` — `src/visualConfig.js` ganha `VC.materiais` (cores 3D); laço de construção de tiles 3D (~11073-11098)

- [ ] **Step 1: Adicionar cores 3D ao `VC`**

Em `src/visualConfig.js`, dentro de `window.VC = { ... }`, logo após o bloco `wall: { ... }` (linha ~77), inserir:

```js
  // ── Materiais de chão/parede (cores 3D por id; espelha server.MATERIAIS) ────
  // r,g,b em 0..1. Pisos coloridos cosméticos; entulho usa cor de parede-escombro.
  materiais: {
    pedra_cinza:   { color: [0.533, 0.533, 0.533] },
    terra:         { color: [0.42, 0.31, 0.20] },
    grama:         { color: [0.25, 0.42, 0.22] },
    pedra_negra:   { color: [0.14, 0.14, 0.16] },
    entulho:       { color: [0.34, 0.31, 0.27] },
    pedra_normal:  { color: [0.353, 0.353, 0.416] },
    enegrecida:    { color: [0.17, 0.17, 0.19] },
    pedra_caverna: { color: [0.30, 0.26, 0.21] },
    desmoronada:   { color: [0.33, 0.30, 0.25] },
  },
```

- [ ] **Step 2: Usar a cor do material no piso 3D**

No laço de construção (bloco do `if(state.tiles[y][x] === TILE_FLOOR || ... TILE_DOOR){`, linha ~11073), trocar:
```js
        const mat = floorBaseMat.clone();
        // VC.floor.baseR (#888888) — clearly lighter than walls; emissive prevents pitch-black
        const fR = VC.floor.baseR + vf*VC.floor.baseVariance;
        mat.color.setRGB(fR, fR, fR);
```
por
```js
        const mat = floorBaseMat.clone();
        const mid3 = (state.materiais && state.materiais[key]) || 'pedra_cinza';
        const mc = (VC.materiais[mid3] || VC.materiais.pedra_cinza).color;
        const jit = vf*VC.floor.baseVariance;
        mat.color.setRGB(mc[0]+jit, mc[1]+jit, mc[2]+jit);
```

- [ ] **Step 3: Usar a cor do material na parede 3D**

No `else` (parede, linha ~11088), trocar:
```js
        const mat = wallBaseMat.clone();
        // VC.wall.baseR (#5a5a6a) — blue-gray stone, darker than floor; emissive keeps detail
        mat.color.setRGB(VC.wall.baseR+vw*VC.wall.variance, VC.wall.baseR+vw*VC.wall.variance, VC.wall.baseB+vw*VC.wall.varianceB);
```
por
```js
        const matId3 = (state.materiais && state.materiais[key]) || 'pedra_normal';
        const wc = (VC.materiais[matId3] || VC.materiais.pedra_normal).color;
        const mat = wallBaseMat.clone();
        const jw = vw*VC.wall.variance;
        mat.color.setRGB(wc[0]+jw, wc[1]+jw, wc[2]+jw);
```

> `key` é `${x},${y}` (definido na linha ~11067). Mantém a textura compartilhada (`floorBaseMat`/`wallBaseMat`) — só a cor muda por casa, então a contagem de luzes/materiais base é estável.

- [ ] **Step 4: Verificar no app (3D)**

Preview: com `dungeons/_teste_materiais.json` (grama/terra/pedra_negra/enegrecida), entrar e ficar no 3D.
Expected: chão esverdeado/terroso/escuro e paredes mais escuras nas casas pintadas; casas não pintadas idênticas ao atual; sem erro no console; FPS normal.

- [ ] **Step 5: Commit**

```bash
git add src/visualConfig.js game.js
git commit -m "feat(materiais): cor 3D por material no chão e na parede"
```

---

### Task 9: Entulho 3D como bloco que oclui

**Files:**
- Modify: `game.js` — no laço de tiles (piso), quando a casa de chão tem material `entulho`, adicionar um bloco altura-de-parede de escombros (~11080)

- [ ] **Step 1: Renderizar o bloco de entulho**

No bloco do piso (após criar e posicionar o `mesh` de chão, logo antes do fechamento do `if` em ~11086), inserir:

```js
        if((state.materiais && state.materiais[key]) === 'entulho'){
          // Entulho oclui visão → bloco altura-de-parede de escombros sobre o chão.
          const ec = VC.materiais.entulho.color;
          const eMat = wallBaseMat.clone();
          eMat.color.setRGB(ec[0], ec[1], ec[2]);
          eMat.emissive.set(VC.wall.emissive); eMat.emissiveIntensity = 1.0;
          const eMesh = new T.Mesh(wallGeo, eMat);
          eMesh.position.set(x, WH/2, y);
          eMesh.scale.y = 0.7;                 // pilha um pouco mais baixa que a parede
          eMesh.castShadow = eMesh.receiveShadow = true;
          eMesh.visible = false;
          eMesh.userData.gridX = x; eMesh.userData.gridY = y;
          scene.add(eMesh);
          tileMeshes[`entulho:${key}`] = eMesh;   // revelado junto com a casa (ver renderMap3D)
        }
```

- [ ] **Step 2: Tornar o bloco visível junto com a casa**

O laço de visibilidade de tiles 3D está em `game.js` linhas ~12910-12917:
```js
  // ── Tile visibility
  for(let y=0; y<H; y++){
    for(let x=0; x<W; x++){
      const key  = `${x},${y}`;
      const mesh = tileMeshes[key];
      if(!mesh) continue;
      mesh.visible = terrainSet.has(key);
    }
  }
```
Trocar a linha `      mesh.visible = terrainSet.has(key);` por:
```js
      mesh.visible = terrainSet.has(key);
      const ent3 = tileMeshes[`entulho:${key}`];
      if(ent3) ent3.visible = mesh.visible;
```

- [ ] **Step 3: Verificar no app (3D)**

Preview: na casa de entulho do `_teste_materiais.json`, no 3D.
Expected: um monte/bloco de escombros ocupando a casa; bloqueia a passagem; a névoa atrás dele não é revelada (vindo do servidor) — o bloco aparece só quando a casa é explorada.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(materiais): entulho 3D como bloco de escombros que oclui"
```

---

## Fase 5 — Editor (pintar materiais)

### Task 10: Exportar `MATERIAIS` para o editor

**Files:**
- Modify: `tools/export_catalog.py` — incluir `materiais` no catálogo
- Regenera: `tools/editor_catalog.js`

- [ ] **Step 1: Incluir materiais no catálogo exportado**

Em `tools/export_catalog.py`, dentro de `build_catalog`, antes do `return`, adicionar:

```python
    materiais = []
    for mid, meta in server.MATERIAIS.items():
        materiais.append({
            "id": mid, "nome": meta["nome"], "categoria": meta["categoria"],
            "cor": meta["cor"], "solido": meta["solido"], "oclui": meta["oclui"],
        })
```

E trocar o `return` para incluir `"materiais": materiais`:
```python
    return {"monsters": monsters, "items": items, "traps": traps,
            "venoms": venoms, "decorations": decorations, "materiais": materiais}
```

- [ ] **Step 2: Regenerar o catálogo do editor**

Run: `python tools/export_catalog.py`
Expected: imprime "editor_catalog.js gerado…" e "editor_dungeons.js gerado…".

- [ ] **Step 3: Conferir o conteúdo**

Run: `python -c "import json,re; s=open('tools/editor_catalog.js',encoding='utf-8').read(); s=s[s.index('=')+1:s.rindex(';')]; d=json.loads(s); print('materiais' in d, len(d['materiais']))"`
Expected: `True 9`

- [ ] **Step 4: Commit**

```bash
git add tools/export_catalog.py tools/editor_catalog.js tools/editor_dungeons.js
git commit -m "feat(materiais): exporta catálogo MATERIAIS para o editor"
```

---

### Task 11: Ferramenta de pintura de material no editor

**Files:**
- Modify: `tools/editor.js` — estado `S` (~6-17), `TOOLS` (~295), `buildToolbar` (~327), pintura (`paintTile`/handler), `render` swatch (~174), `buildJSON` (~806), `loadJSON` (~905), `validarEditor` (~852)

- [ ] **Step 1: Estado do material no editor**

Em `tools/editor.js`, no objeto `S` (linha ~6-17), adicionar campos:
```js
    materiais: {},                 // {"x,y": id}
    matId: (CAT.materiais && CAT.materiais[0] ? CAT.materiais[0].id : "grama"),
    matFill: false,                // false = pincel; true = balde (preenchimento)
```
E logo após `const CAT = ...` (linha ~4), adicionar um índice por id e helper de meta:
```js
  const MAT = (CAT.materiais || []);
  const matMeta = (id) => MAT.find(m => m.id === id) || null;
  // Default por categoria: pintar o default limpa a casa (mantém JSON esparso e
  // serve de borracha de material). Espelha MATERIAIS_*_DEFAULT do servidor.
  const MAT_DEFAULT = { piso: "pedra_cinza", parede: "pedra_normal" };
```

- [ ] **Step 2: Registrar a ferramenta**

Em `TOOLS` (linha ~295), após `{ id: "door", ... }`, adicionar:
```js
    { id: "material", label: "material", group: "tiles" },
```

- [ ] **Step 3: UI da ferramenta (paleta + balde) em `buildToolbar`**

Em `buildToolbar`, após o bloco `if (S.tool === "decor") { ... }` (linha ~327-338), adicionar:
```js
    if (S.tool === "material") {
      const sel = document.createElement("select");
      sel.id = "mat-id";
      sel.innerHTML = MAT.map(m =>
        `<option value="${m.id}"${m.id === S.matId ? " selected" : ""}>${m.categoria === "parede" ? "🧱" : (m.id === "entulho" ? "⛰️" : "▦")} ${m.nome}</option>`).join("");
      sel.onchange = e => { S.matId = e.target.value; };
      tb.appendChild(sel);
      const fill = document.createElement("button");
      fill.textContent = S.matFill ? "balde: ON" : "balde: OFF";
      fill.title = "Preenche a região contígua de mesma estrutura (chão↔chão / parede↔parede)";
      fill.onclick = () => { S.matFill = !S.matFill; buildToolbar(); };
      tb.appendChild(fill);
    }
```

- [ ] **Step 4: Lógica de pintura (pincel + balde + categoria)**

Adicionar helpers e a ação de pintar. Logo após `function paintTile(x, y) { ... }` (linha ~374), inserir:
```js
  // Categoria do material compatível com a estrutura do tile?
  function matCompat(id, x, y) {
    const meta = matMeta(id); if (!meta) return false;
    const t = S.tiles[y][x];
    if (meta.categoria === "parede") return t === WALL;
    return t === FLOOR || t === DOOR;   // piso (inclui entulho)
  }
  // Estrutura "pintável junta" p/ balde: parede vs. não-parede.
  function _structKind(x, y) { return S.tiles[y][x] === WALL ? "wall" : "floor"; }
  // Aplica o material atual a uma casa (ou limpa se for o default da categoria).
  function _setMat(x, y) {
    const meta = matMeta(S.matId); if (!meta) return;
    if (S.matId === MAT_DEFAULT[meta.categoria]) delete S.materiais[x + "," + y];
    else S.materiais[x + "," + y] = S.matId;
  }
  function paintMaterial(x, y) {
    if (!matCompat(S.matId, x, y)) return;     // ignora casa incompatível
    if (!S.matFill) { _setMat(x, y); return; }
    // Balde: preenche a região 4-conexa de mesma estrutura.
    const kind = _structKind(x, y);
    const seen = new Set([x + "," + y]); const st = [[x, y]];
    while (st.length) {
      const [cx, cy] = st.pop();
      if (matCompat(S.matId, cx, cy)) _setMat(cx, cy);
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = cx + dx, ny = cy + dy, k = nx + "," + ny;
        if (nx >= 0 && ny >= 0 && nx < S.grid.w && ny < S.grid.h && !seen.has(k)
            && _structKind(nx, ny) === kind) { seen.add(k); st.push([nx, ny]); }
      }
    }
  }
```

Ligar ao input. Os handlers estão em `tools/editor.js`:

Mousedown (linha ~742):
```js
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; paintTile(x, y); render(); }
```
Trocar por (adiciona o ramo `material`; `painting=true` permite pintar arrastando):
```js
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; paintTile(x, y); render(); }
    else if (S.tool === "material") { painting = true; paintMaterial(x, y); render(); updateStatus(); }
```

Mousemove (linha ~772):
```js
    if (painting) { paintTile(c[0], c[1]); render(); return; }
```
Trocar por (despacha o pintor certo conforme a ferramenta):
```js
    if (painting) {
      if (S.tool === "material") { paintMaterial(c[0], c[1]); updateStatus(); }
      else paintTile(c[0], c[1]);
      render(); return;
    }
```
> A pintura por material não muda estrutura nem cria entidades; o arraste pinta casa a casa. Com o balde (`S.matFill`) ligado, cada casa arrastada re-preenche sua região — inofensivo.

- [ ] **Step 5: Swatch no `render`**

Em `render`, no laço de tiles (linhas ~171-177), trocar:
```js
        const t = S.tiles[y][x];
        ctx.fillStyle = t === WALL ? "#1d1812" : (t === DOOR ? "#c8841f" : "#5a4a32");
        ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
```
por
```js
        const t = S.tiles[y][x];
        const mid = S.materiais[x + "," + y];
        const mm = mid ? matMeta(mid) : null;
        ctx.fillStyle = mm ? mm.cor : (t === WALL ? "#1d1812" : (t === DOOR ? "#c8841f" : "#5a4a32"));
        ctx.fillRect(x * CELL, y * CELL, CELL - 1, CELL - 1);
        if (mid === "entulho") {            // marca de obstáculo
          ctx.fillStyle = "rgba(0,0,0,0.45)";
          ctx.fillRect(x * CELL + CELL * 0.3, y * CELL + CELL * 0.3, CELL * 0.4, CELL * 0.4);
        }
```

- [ ] **Step 6: Apagar material junto da estrutura**

Em `eraseAt` (linha ~423-433), antes de `S.tiles[y][x] = WALL;`, adicionar:
```js
    delete S.materiais[x + "," + y];
```
E em `paintTile` (linha ~370): ao trocar a estrutura de uma casa, materiais incompatíveis devem cair. Trocar o corpo por:
```js
  function paintTile(x, y) {
    if (S.tool === "wall") S.tiles[y][x] = WALL;
    else if (S.tool === "floor") S.tiles[y][x] = FLOOR;
    else if (S.tool === "door") { S.tiles[y][x] = DOOR; doorLink(x, y); }
    // Material que não combina mais com a nova estrutura é descartado.
    const mid = S.materiais[x + "," + y];
    if (mid && !matCompat(mid, x, y)) delete S.materiais[x + "," + y];
  }
```
> `matCompat` é definido na Task 11 Step 4 (mesmo arquivo) — garantir que sua definição apareça **antes** de `paintTile` ou que ambas sejam funções içadas (declaração `function`, que é içada). Ambas são `function` declarations, então a ordem textual não quebra.

- [ ] **Step 7: Serializar no save e carregar no load**

Em `buildJSON` (linha ~806-834), adicionar ao objeto retornado (após `decorations: ...,` ou antes de `prisoner:`):
```js
      materiais: { ...S.materiais },
```
Em `loadJSON` (linha ~905-938), após `S.decorations = ...` (linha ~925), adicionar:
```js
    S.materiais = (obj.materiais && typeof obj.materiais === "object") ? { ...obj.materiais } : {};
```

- [ ] **Step 8: Validar no editor (`validarEditor`)**

Em `validarEditor` (linha ~852-895), antes de `return { ok: ... }`, adicionar:
```js
    const matIds = new Set(MAT.map(m => m.id));
    for (const [key, mid] of Object.entries(S.materiais)) {
      if (!matIds.has(mid)) { e.push(`material inválido: ${mid}`); continue; }
      const p = key.split(",").map(Number);
      const t = S.tiles[p[1]]?.[p[0]];
      const cat = matMeta(mid).categoria;
      if (cat === "parede" && t !== WALL) e.push(`material de parede ${mid} fora de parede em ${key}`);
      if (cat === "piso" && !(t === FLOOR || t === DOOR)) e.push(`material de piso ${mid} fora de chão em ${key}`);
    }
```

- [ ] **Step 9: Verificar o editor manualmente**

Abrir `tools/editor.html` no navegador (ou via app). Selecionar "material", escolher "Grama", pintar; ligar "balde" e clicar numa região de chão; pintar uma parede com "enegrecida"; pintar "entulho" numa casa de chão. Tentar pintar parede em chão (deve ser ignorado). Salvar.
Expected: swatches coloridos no canvas; balde preenche a sala; entulho com marca central; status "válida"; o JSON salvo contém `materiais`.

- [ ] **Step 10: Commit**

```bash
git add tools/editor.js
git commit -m "feat(materiais): ferramenta de pintura de material no editor (pincel+balde)"
```

---

### Task 12: Round-trip de ponta a ponta + verificação integrada

**Files:**
- Test: `tools/test_materiais.py` (adicionar `test_roundtrip`)
- Verify: app (server + cliente) com uma masmorra pintada

- [ ] **Step 1: Teste de round-trip servidor**

Adicionar a `tools/test_materiais.py`:
```python
def test_roundtrip():
    print("\n[M5] round-trip materiais")
    import copy, json
    d = _defn_full()
    ok, msg = server.validar_dungeon(copy.deepcopy(d))
    check("defn com materiais valida", ok)
    # serializa->json->carrega no GameRoom
    d2 = json.loads(json.dumps(d))
    r = _room(); r.load_authored_dungeon(d2)
    ser = r._serializar_materiais()
    check("round-trip preserva entulho", ser.get("2,1") == "entulho")
    check("round-trip preserva grama", ser.get("3,1") == "grama")
```
E no `__main__`, adicionar `test_roundtrip()`.

- [ ] **Step 2: Rodar a suíte completa**

Run: `python tools/test_materiais.py`
Expected: PASS em M1–M5.

- [ ] **Step 3: Verificação integrada no app**

Iniciar o servidor (`python server.py`), abrir o cliente, criar/entrar numa masmorra pintada (via editor da Task 11 ou um JSON em `dungeons/`). Conferir:
- 2D e 3D mostram grama/terra/pedra negra/enegrecida/caverna/desmoronada corretamente.
- Andar até o entulho: o servidor recusa ("Escombros bloqueiam o caminho") e o preview de movimento (cliente) não oferece a casa.
- A névoa não revela atrás do entulho.
- Mirar magia/ataque à distância através do entulho é recusado (LOS).
- Masmorra antiga (sem `materiais`) carrega e renderiza idêntica.

Expected: todos os itens acima conferem; sem erros no console.

- [ ] **Step 4: Regenerar índice de masmorras do editor (se houve masmorra de teste salva)**

Run: `python tools/export_catalog.py`
Expected: catálogo + índice regenerados sem erro.

- [ ] **Step 5: Commit**

```bash
git add tools/test_materiais.py
git commit -m "test(materiais): round-trip de ponta a ponta da camada de materiais"
```

---

## Verificação final (antes de finalizar a branch)

- [ ] `python tools/test_materiais.py` → tudo ✅
- [ ] `python tools/test_decoracoes.py` → sem regressão
- [ ] App 2D e 3D: materiais corretos, entulho bloqueia mov/visão/LOS, compat retroativa
- [ ] Editor: pintar/baldear/apagar material; save/load preservam `materiais`

## Riscos / lembretes

- **Divergência cliente↔servidor:** o entulho precisa bloquear nos DOIS lados (Tasks 4 e 5). Se um preview oferecer uma casa que o servidor recusa, o bug é aqui.
- **Compat retroativa:** ausência de `materiais` deve renderizar idêntico (verificado em M3 e na Task 12).
- **Perf 3D:** cor por casa (clone de material já existente), textura base compartilhada — não gerar textura por casa.
- **`CELL` em `drawEntulho2D`:** usa a constante global do 2D já em uso por `drawFloor3D` (mesma escala).
