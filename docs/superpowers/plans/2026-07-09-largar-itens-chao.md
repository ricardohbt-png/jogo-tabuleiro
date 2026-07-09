# Largar/pegar itens no chão — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir largar itens no chão (numa das 8 casas adjacentes) e pegá-los de volta — inclusive por outro jogador — na masmorra, persistindo como os baús.

**Architecture:** Estado autoritativo em `server.py` (`self.ground_items`, espelhando `self.chests`), senders/getters puros em `src/gameState.js`, render 2D/3D + gesto em `game.js`. Pegar reusa `_route_acquired_item` (Sub-projeto B, bolsa-primeiro).

**Tech Stack:** Python (servidor WebSocket), Vanilla JS (cliente), Three.js r128 (3D). Testes: scripts `tools/test_*.py` que stubam a rede do `GameRoom` e chamam handlers direto.

**Spec:** `docs/superpowers/specs/2026-07-09-largar-itens-chao-design.md`

---

### Task 1: Estado `ground_items` + helper de casa livre

**Files:**
- Modify: `server.py` — `__init__` (~L3949, junto de `self.chests = {}`), bloco `if nova:` (~L5185), `push_state` (~L4850), e adicionar `_free_drop_tile_near` (perto de `_free_tile_near`, ~L5782).
- Test: `tools/test_ground_items.py` (criar).

- [ ] **Step 1: Escrever o teste que falha (setup + casa livre)**

Criar `tools/test_ground_items.py`:

```python
"""Teste de largar/pegar itens no chão — Sub-projeto C.
Roda da raiz: python tools/test_ground_items.py
Stuba a rede do GameRoom e monta um mapa de chão manualmente."""
import asyncio, sys, os
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, WALL, WEAPONS, SHOP_ARMORS

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=7, h=7):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    # mapa: tudo chão
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def armor_item(iid):
    return deepcopy(next(a for a in SHOP_ARMORS if a["id"] == iid))

async def main():
    # ── [1] _free_drop_tile_near acha casa livre / respeita ocupação ────────────
    print("\n[1] _free_drop_tile_near")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    tile = r._free_drop_tile_near([3, 3])
    check("achou uma casa adjacente livre", tile is not None and max(abs(tile[0]-3), abs(tile[1]-3)) == 1)
    check("ground_items inicia vazio", r.ground_items == {})
    # cerca o jogador de paredes → sem casa livre
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                r.tiles[3+dy][3+dx] = WALL
    check("sem casa livre → None", r._free_drop_tile_near([3, 3]) is None)

    print(f"\n===== GROUND ITEMS: {PASS} OK, {FAIL} XX =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_ground_items.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute 'ground_items'` (ou `_free_drop_tile_near`).

- [ ] **Step 3: Adicionar estado e helper no `server.py`**

Em `__init__`, logo após `self.chests  = {}` (~L3949):

```python
        self.ground_items = {}  # gid -> {"id","item","pos":[x,y]} — itens largados no chão (persistem como chests)
```

No bloco `if nova:` (~L5185), junto de `self.chests = {}`:

```python
            self.ground_items = {}   # itens no chão não persistem numa masmorra NOVA (após encerrar a missão)
```

Adicionar o helper perto de `_free_tile_near` (~L5798):

```python
    def _free_drop_tile_near(self, pos):
        """1ª casa de chão adjacente (8-dir) a `pos` livre de parede/porta/decoração
        sólida (via _blocks_tile), monstro vivo, jogador vivo, baú e outro item no
        chão. Ordem determinística (dy,dx de -1 a 1). Retorna [x,y] ou None."""
        cx, cy = pos
        occupied = {tuple(m["pos"]) for m in self.monsters.values() if m["hp"] > 0}
        occupied |= {tuple(c["pos"]) for c in self.chests.values()}
        occupied |= {tuple(g["pos"]) for g in self.ground_items.values()}
        occupied |= {tuple(pp["pos"]) for pp in self.players.values() if pp.get("alive")}
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = cx + dx, cy + dy
                if not self._blocks_tile(nx, ny) and (nx, ny) not in occupied:
                    return [nx, ny]
        return None
```

Em `push_state`, junto de `"chests": list(self.chests.values()),` (~L4850):

```python
            "ground_items": list(self.ground_items.values()),
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_ground_items.py`
Expected: PASS — `1 OK, 0 XX`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_ground_items.py
git commit -m "feat(chao): estado ground_items + _free_drop_tile_near"
```

---

### Task 2: `handle_drop_item` (bolsa e slot equipado) + dispatch

**Files:**
- Modify: `server.py` — adicionar `handle_drop_item` (perto de `handle_take_from_chest`, ~L8482) e o dispatch (perto de `elif t == "sell_item":`, ~L15169).
- Test: `tools/test_ground_items.py` (adicionar seções [2]-[4]).

- [ ] **Step 1: Escrever os testes que falham (adicionar antes do bloco RESULTADO)**

```python
    # ── [2] Largar da BOLSA ─────────────────────────────────────────────────────
    print("\n[2] Largar item da bolsa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather")]
    await r.handle_drop_item("p1", "bag", 0, None)
    check("item saiu da bolsa", len(p["bag"]) == 0)
    check("item apareceu no chão", len(r.ground_items) == 1)
    gi = list(r.ground_items.values())[0]
    check("item no chão é a leather", gi["item"]["id"] == "leather")
    check("casa do item é adjacente ao jogador", max(abs(gi["pos"][0]-3), abs(gi["pos"][1]-3)) == 1)

    # ── [3] Largar de um SLOT EQUIPADO (arma) → desequipa ───────────────────────
    print("\n[3] Largar arma equipada → desequipa e cai no chão")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    arma0 = p["gear"]["weapon"]["id"]
    await r.handle_drop_item("p1", "gear", None, "weapon")
    check("slot de arma ficou vazio", p["gear"].get("weapon") is None)
    check("p['weapon'] voltou a desarmado", p["weapon"]["id"] == "unarmed")
    check("arma foi para o chão", any(g["item"]["id"] == arma0 for g in r.ground_items.values()))

    # ── [4] Sem casa livre → recusa, item permanece ─────────────────────────────
    print("\n[4] Sem casa adjacente livre → recusa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather")]
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy: r.tiles[3+dy][3+dx] = WALL
    await r.handle_drop_item("p1", "bag", 0, None)
    check("item permanece na bolsa", len(p["bag"]) == 1)
    check("nada no chão", len(r.ground_items) == 0)
    check("erro enviado", any("espaço" in e.lower() for e in r._errs))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_ground_items.py`
Expected: FAIL — `handle_drop_item` não existe.

- [ ] **Step 3: Implementar `handle_drop_item` + dispatch**

Adicionar em `server.py` (perto de `handle_take_from_chest`):

```python
    async def handle_drop_item(self, pid, source, index=None, slot_key=None):
        """Larga um item no chão (1ª casa adjacente livre). Ação LIVRE, a qualquer
        momento (sem _is_turn). Origem: bolsa (index) ou slot equipado (slot_key —
        desequipa na hora)."""
        p = self.players.get(pid)
        if not p or not p.get("alive") or self.phase != "playing":
            return
        # localiza o item sem removê-lo ainda (só remove se houver casa)
        if source == "bag":
            if index is None or index < 0 or index >= len(p["bag"]):
                await self.send_to(pid, {"type": "error", "msg": "Slot de inventário inválido."}); return
            item = p["bag"][index]
        elif source == "gear":
            if slot_key not in GEAR_SLOTS or not p["gear"].get(slot_key):
                await self.send_to(pid, {"type": "error", "msg": "Nada equipado nesse slot."}); return
            item = p["gear"][slot_key]
        else:
            return
        tile = self._free_drop_tile_near(p["pos"])
        if tile is None:
            await self.send_to(pid, {"type": "error", "msg": "Sem espaço adjacente para largar."}); return
        # remove da origem
        if source == "bag":
            p["bag"].pop(index)
        else:
            p["gear"][slot_key] = None
            self._apply_gear_effect(p, item, False)
            if slot_key == "weapon":
                p["weapon"] = {**WEAPONS["unarmed"]}
        gid = new_id()   # UM id só — usado como chave e como campo "id"
        self.ground_items[gid] = {"id": gid, "item": item, "pos": tile}
        await self.gm_say(f"🎒 **{p['name']}** largou **{item['name']}** no chão.")
        await self.push_state()
```

Adicionar o dispatch em `handle_message` (perto de `elif t == "sell_item":`):

```python
                elif t == "drop_item":
                    if room: await room.handle_drop_item(pid, msg.get("source"), msg.get("index"), msg.get("slot_key"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_ground_items.py`
Expected: PASS — `[1]..[4]` verdes.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_ground_items.py
git commit -m "feat(chao): handle_drop_item (bolsa e slot equipado)"
```

---

### Task 3: `handle_pickup_item` + dispatch

**Files:**
- Modify: `server.py` — `handle_pickup_item` (perto de `handle_drop_item`) e dispatch.
- Test: `tools/test_ground_items.py` (seções [5]-[7]).

- [ ] **Step 1: Escrever os testes que falham**

```python
    # ── [5] Pegar por OUTRO jogador adjacente → vai pro inventário ──────────────
    print("\n[5] Pegar item por outro jogador adjacente")
    r = setup()
    p1 = make_player("p1", "V", "warrior", 0); p1["pos"] = [3, 3]; r.players["p1"] = p1
    p2 = make_player("p2", "L", "rogue", 1);   p2["pos"] = [5, 5]; r.players["p2"] = p2
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("leather"), "pos": [5, 4]}
    await r.handle_pickup_item("p2", gid)   # p2 em [5,5], item em [5,4] → adjacente
    check("item saiu do chão", gid not in r.ground_items)
    check("item entrou na bolsa do p2", any((it or {}).get("id") == "leather" for it in p2["bag"]))

    # ── [6] Pegar LONGE → erro, item permanece ─────────────────────────────────
    print("\n[6] Pegar longe → erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("leather"), "pos": [5, 5]}
    await r.handle_pickup_item("p1", gid)
    check("item permanece no chão", gid in r.ground_items)
    check("erro de longe", any("longe" in e.lower() for e in r._errs))

    # ── [7] Bolsa cheia + slot ocupado → recusa (fica no chão) ──────────────────
    print("\n[7] Bolsa cheia + slot ocupado → recusa")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [3, 3]; r.players["p1"] = p
    p["bag"] = [armor_item("leather")] * 6        # bolsa cheia
    p["gear"]["armor"] = armor_item("leather")    # slot de armadura ocupado
    gid = "g1"; r.ground_items[gid] = {"id": gid, "item": armor_item("plate"), "pos": [3, 4]}
    await r.handle_pickup_item("p1", gid)
    check("item permanece no chão (recusado)", gid in r.ground_items)
    check("erro de cheio", any("cheio" in e.lower() for e in r._errs))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_ground_items.py`
Expected: FAIL — `handle_pickup_item` não existe.

- [ ] **Step 3: Implementar `handle_pickup_item` + dispatch**

```python
    async def handle_pickup_item(self, pid, ground_id):
        """Pega um item do chão (adjacente, Chebyshev ≤1) para o inventário. Ação
        LIVRE, a qualquer momento. Roteia por _route_acquired_item (bolsa-primeiro)."""
        p = self.players.get(pid)
        if not p or not p.get("alive") or self.phase != "playing":
            return
        gi = self.ground_items.get(ground_id)
        if not gi:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado."}); return
        gx, gy = gi["pos"]; px, py = p["pos"]
        if max(abs(px - gx), abs(py - gy)) > 1:
            await self.send_to(pid, {"type": "error", "msg": "Muito longe do item!"}); return
        res = self._route_acquired_item(p, gi["item"])
        if res == "full":
            await self.send_to(pid, {"type": "error",
                "msg": "Inventário cheio e slot ocupado — abra espaço primeiro."}); return
        del self.ground_items[ground_id]
        extra = " (equipado — bolsa cheia)" if res == "equipped" else ""
        await self.gm_say(f"🎒 **{p['name']}** pegou **{gi['item']['name']}** do chão{extra}!")
        await self.push_state()
```

Dispatch (perto do `drop_item`):

```python
                elif t == "pickup_item":
                    if room: await room.handle_pickup_item(pid, msg.get("ground_id"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_ground_items.py`
Expected: PASS — `[1]..[7]` verdes.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_ground_items.py
git commit -m "feat(chao): handle_pickup_item (adjacente, roteia por B)"
```

---

### Task 4: Persistência (voltar da cidade mantém; masmorra nova limpa)

**Files:**
- Test: `tools/test_ground_items.py` (seção [8]).

- [ ] **Step 1: Escrever o teste de persistência**

Espelha `tools/test_persistencia_masmorra.py` (usa o `enter_dungeon` procedural real). Adicionar:

```python
    # ── [8] Persistência: some ao gerar masmorra nova, fica ao voltar da cidade ──
    print("\n[8] Persistência dos itens no chão")
    r2 = GameRoom("TEST2")
    async def noop(*a, **k): pass
    r2.gm_say = noop; r2.broadcast = noop; r2.push_state = noop
    r2.send_to = noop; r2.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "V", "warrior"), ("p2", "P", "mage")):
        r2.players[pid] = make_player(pid, nome, cls, 0)
    r2.player_order = list(r2.players.keys()); r2.host_pid = "p1"; r2.phase = "city"
    await r2.enter_dungeon("p1")                 # 1ª entrada: nova=True
    check("ground_items vazio na masmorra nova", r2.ground_items == {})
    # larga um item manualmente
    r2.ground_items["gX"] = {"id": "gX", "item": armor_item("leather"), "pos": list(r2.players["p1"]["pos"])}
    await r2._voltar_para_cidade()               # sai pela escada
    check("item persiste ao ir pra cidade", "gX" in r2.ground_items)
    await r2.enter_dungeon("p1")                  # reentra a MESMA masmorra: nova=False
    check("item persiste ao reentrar (mesmo lugar)", "gX" in r2.ground_items)
    r2.dungeon_generated = False                  # força masmorra nova
    await r2.enter_dungeon("p1")
    check("item some ao gerar masmorra nova", "gX" not in r2.ground_items)
```

- [ ] **Step 2: Rodar**

Run: `python tools/test_ground_items.py`
Expected: PASS se o reset de `ground_items` estiver no bloco `if nova:` (Task 1). Se falhar em "item persiste ao reentrar", verificar que `ground_items` NÃO é resetado fora do bloco `nova` (ex.: não colocar no ramo de carregamento autorado L5073). Corrigir a posição do reset.

- [ ] **Step 3: Rodar as suites relacionadas (sem regressão)**

Run: `python tools/test_persistencia_masmorra.py && python tools/test_roteamento_itens.py`
Expected: ambas PASS.

- [ ] **Step 4: Commit**

```bash
git add tools/test_ground_items.py
git commit -m "test(chao): persistência dos itens no chão (cidade x masmorra nova)"
```

---

### Task 5: Cliente — `gameState.js` (getter, senders, resolver)

**Files:**
- Modify: `src/gameState.js` — getter `groundItems`, resolver `groundItemPickable`, senders `dropItem`/`pickupItem`, e exportá-los no objeto de retorno (~L1698+).

- [ ] **Step 1: Adicionar a lógica pura e os senders**

Perto dos outros senders de ação (ex.: `equipFromBag`/`unequip`, ~L1090):

```javascript
  function dropItem(source, ref) {
    // source: 'bag' → ref = index; 'gear' → ref = slotKey
    if (source === 'bag') send({ type: 'drop_item', source: 'bag', index: ref });
    else                  send({ type: 'drop_item', source: 'gear', slot_key: ref });
  }
  function pickupItem(id) { send({ type: 'pickup_item', ground_id: id }); }

  // Resolver puro: item do chão é pegável por `player` (adjacência Chebyshev ≤1)?
  function groundItemPickable(gi, player) {
    if (!gi || !player || !player.pos) return false;
    return Math.max(Math.abs(player.pos[0] - gi.pos[0]),
                    Math.abs(player.pos[1] - gi.pos[1])) <= 1;
  }
```

No objeto de retorno (perto de `get cityState()`), adicionar o getter:

```javascript
    get groundItems()     { return (gameState && gameState.ground_items) || []; },
```

E na seção de Actions (perto de `unequip,`), exportar:

```javascript
    dropItem,
    pickupItem,
    groundItemPickable,
```

- [ ] **Step 2: Verificar sintaxe e o resolver**

Run:
```bash
node --check src/gameState.js && node -e '
const a = {pos:[3,3]}; const gi=(x,y)=>({pos:[x,y]});
const adj = Math.max(Math.abs(3-4),Math.abs(3-3))<=1;
const far = Math.max(Math.abs(3-5),Math.abs(3-5))<=1;
console.log("adj", adj===true, "far", far===false);
'
```
Expected: `src/gameState.js` sem erro; `adj true far true`.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(chao): gameState.js — groundItems + dropItem/pickupItem/pickable"
```

---

### Task 6: Cliente — `game.js` render 2D/3D + gesto de largar + clique-pra-pegar

**Files:**
- Modify: `game.js` — render de `GS.groundItems` no 2D (dentro do desenho de baús) e 3D (padrão `chestMeshes`); drop no backdrop do `InventoryModal`; clique-pra-pegar (2D `resolveTileClick`/hit-test e 3D raycast).
- Modify: `src/ui/inventoryModal.js` — no `_ensureDom`, tratar drop sobre o overlay (fora do frame) chamando `GS.dropItem`.

- [ ] **Step 1: Gesto de largar (soltar fora do modal)**

Em `src/ui/inventoryModal.js`, dentro de `_ensureDom()` (onde o overlay é criado), o overlay já fecha ao clicar fora. Adicionar handlers de drag para o overlay tratar um item solto fora do frame:

```javascript
    overlay.addEventListener('dragover', (e) => { if (_selected) e.preventDefault(); });
    overlay.addEventListener('drop', (e) => {
      if (!_selected || e.target !== overlay) return;   // só quando solto no backdrop
      e.preventDefault();
      const sel = _selected; _selected = null;
      const gsNow = (typeof GS !== 'undefined') ? GS.gameState : null;
      const naMasmorra = gsNow && gsNow.phase === 'playing';
      if (!naMasmorra) { refresh(); return; }            // largar no chão só na masmorra
      if (sel.kind === 'bag')  GS.dropItem('bag', sel.index);
      else                     GS.dropItem('gear', sel.slotKey);
      close();
    });
```

- [ ] **Step 2: Render 2D dos itens no chão**

No `game.js`, dentro da função que desenha os baús no canvas 2D (procurar por onde `state.chests`/`GS`+baús são desenhados — grep `chest` em `game.js`), após desenhar os baús, desenhar os itens do chão:

```javascript
  // Itens largados no chão (2D)
  (GS.groundItems || []).forEach(gi => {
    const [gx, gy] = gi.pos;
    // usa a mesma projeção de casa→pixel dos baús (ex.: cx = ox + gx*TILE ...)
    const cx = /* projeção X da casa */, cy = /* projeção Y da casa */;
    drawItemIconAt(ctx, gi.item, cx, cy);   // reusa itemIconHTML/emoji já existente
  });
```

Implementar `drawItemIconAt` reusando o carregamento de ícone já usado nos baús/inventário (imagem `assets/itens/<id>.png` com fallback para `item.emoji`). Se o projeto já tiver um helper de desenhar emoji/ícone numa casa (grep `fillText` perto do desenho de baús), reusá-lo.

- [ ] **Step 3: Clique-pra-pegar 2D**

No handler de clique de casa do 2D (grep `resolveTileClick`/onde um clique em casa é tratado), antes/depois da lógica de baú, testar se há item do chão na casa clicada:

```javascript
    const gi = (GS.groundItems || []).find(g => g.pos[0] === tileX && g.pos[1] === tileY);
    if (gi) {
      const me = GS.me;
      if (me && GS.groundItemPickable(gi, me)) { GS.pickupItem(gi.id); return; }
      toast('Muito longe do item.', 'var(--text2)'); return;
    }
```

- [ ] **Step 4: Render 3D + clique-pra-pegar (raycast)**

No `game.js`, onde os baús 3D são construídos (grep `chestMeshes`), criar `groundItemMeshes` no mesmo padrão: para cada `GS.groundItems`, um mesh/sprite pequeno (ex.: `PlaneGeometry` com textura do ícone, ou uma `BoxGeometry` achatada) posicionado na casa. No raycast de clique 3D (onde `chestMeshes` são testados), adicionar `groundItemMeshes`: ao acertar, `GS.pickupItem(id)` se `GS.groundItemPickable`, senão toast.

- [ ] **Step 5: Verificar no browser (preview)**

Subir o servidor e dirigir o cliente:
1. `preview_start` name `game`.
2. Confirmar `preview_console_logs level:error` sem erros após carregar.
3. (Verificação visual manual, pois o fluxo pede entrar na masmorra): abrir o inventário, arrastar um item pro backdrop → deve sumir do inventário; confirmar `ground_items` no estado via `preview_eval`: `GS.groundItems.length`.

Como o fluxo até a masmorra exige jogar, a verificação mínima automatizável: `node --check`-equivalente já feito; confirmar que o cliente carrega sem erro de console com o novo código. Verificação funcional completa: manual pelo usuário no jogo.

- [ ] **Step 6: Commit**

```bash
git add game.js src/ui/inventoryModal.js
git commit -m "feat(chao): render 2D/3D dos itens no chão + gesto de largar + pegar"
```

---

## Notas de integração / riscos

- **`GEAR_SLOTS`** já existe (usado em `handle_unequip`) — reusar em `handle_drop_item`.
- **`new_id`** e **`self.map_w/map_h`** já existem (usados por `_spawn_chest`/`_free_tile_near`).
- **Largar de slot equipado** espelha `handle_unequip` (reverte efeito + reseta `p["weapon"]`); NÃO usa o modal de "duas mãos" (largar só remove).
- **Render 2D/3D** deve reusar o helper de ícone já existente dos baús/inventário (`itemIconHTML` no cliente é para DOM; no canvas 2D use o mesmo carregamento de `assets/itens/<id>.png` com fallback emoji).
- **Sem gating de névoa** (itens em áreas exploradas), consistente com os baús.
