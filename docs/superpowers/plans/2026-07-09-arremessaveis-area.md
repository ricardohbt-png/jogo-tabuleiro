# Arremessáveis de Área (Sub-projeto B) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar quatro itens arremessáveis de **área** ao mercado — Bomba Incendiária, Granada Explosiva, Granada Superior e Bomba de Fumaça — que atingem todos no raio (fogo amigo) com save de Reflexos, ou criam uma zona de escuridão.

**Architecture:** Estende o framework de arremessáveis do Sub-projeto A (catálogo `ARREMESSAVEIS`, mensagem `throw_item`, mira por clique direito) para o modo `alvo:"area"`. O servidor reusa `_alvos_na_area`/`_save_mostrado`/`_aplicar_em_chamas`/`_aplicar_escuridao` (exatamente como a Bola de Fogo); o cliente reusa a prévia de área verde das magias (`_recomputarAreaMagia`/`_spellHL.area`). `handle_throw_item` passa a receber o dict da mensagem e despacha por tipo de alvo.

**Tech Stack:** Python 3 + `websockets` (server.py); Vanilla JS (src/gameState.js, game.js); testes com o harness caseiro de `tools/test_*.py` (asyncio + stubs de rede).

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | 4 itens em `ARREMESSAVEIS`/`SHOP_MERCHANT`; `_aplicar_escuridao(pos=…)`; refactor `handle_throw_item(pid, data)` + `_throw_item_alvo`; novo `_throw_item_area`; dispatch WS |
| `src/gameState.js` | Modificar | `CATALOGO_ITENS` (4 itens); ramo de área em `resolveTileClick`; sender `throwItemArea`; API |
| `game.js` | Modificar | `_iniciarMiraArremesso` ramifica p/ área (prévia verde que segue o cursor); roteamento do clique de área 2D+3D |
| `tools/test_arremessaveis.py` | Modificar | Atualizar as 4 chamadas de `handle_throw_item` p/ a nova assinatura (dict) |
| `tools/test_arremessaveis_area.py` | Criar | Testes do modo de área (dano/save/fogo amigo/incendiária/fumaça/alcance/LOS) |

> **Arquitetura:** toda decisão (alcance/LOS/área/save/dano) fica no servidor; `gameState.js` só decide o clique e envia; `game.js` só desenha a prévia e roteia. Não colocar lógica de jogo em `game.js`.

---

### Task 1: Quatro itens de área no catálogo + loja

**Files:**
- Modify: `server.py` — dentro do dict `ARREMESSAVEIS` (após a entrada `fogo_grego`, ~linha 2224) e em `SHOP_MERCHANT` (após os itens `frasco_oleo`/`fogo_grego`)
- Test: `tools/test_arremessaveis_area.py`

- [ ] **Step 1: Criar o arquivo de teste com harness + o teste [1] (catálogo/loja)**

Crie `tools/test_arremessaveis_area.py`:

```python
"""Testes dos arremessáveis de ÁREA (Sub-projeto B).
Roda da raiz: python tools/test_arremessaveis_area.py
Stuba a rede do GameRoom e monta um mapa de chão manualmente."""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, WALL, ARREMESSAVEIS, SHOP_MERCHANT

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=11, h=11):
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
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def throwable(iid):
    return deepcopy(next(i for i in SHOP_MERCHANT if i["id"] == iid))

def make_monster(r, mid, x, y, hp=30, ac=1):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo de área + loja")
    for iid in ("bomba_incendiaria", "granada", "granada_superior", "bomba_fumaca"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=area", ARREMESSAVEIS.get(iid, {}).get("alvo") == "area")
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    check("incendiária: 2d6", ARREMESSAVEIS["bomba_incendiaria"]["dano"] == "2d6")
    check("incendiária: CD 12", ARREMESSAVEIS["bomba_incendiaria"]["save"]["cd"] == 12)
    check("incendiária: em_chamas", ARREMESSAVEIS["bomba_incendiaria"]["em_chamas"] is True)
    check("superior: 3d6", ARREMESSAVEIS["granada_superior"]["dano"] == "3d6")
    check("superior: CD 15", ARREMESSAVEIS["granada_superior"]["save"]["cd"] == 15)
    check("fumaça: zona escuridao", ARREMESSAVEIS["bomba_fumaca"]["zona"]["tipo"] == "escuridao")
    check("fumaça: sem dano", "dano" not in ARREMESSAVEIS["bomba_fumaca"])

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_area.py`
Expected: FAIL — `KeyError: 'bomba_incendiaria'` (itens ainda não existem).

- [ ] **Step 3: Adicionar as 4 entradas no `ARREMESSAVEIS`**

Dentro do dict `ARREMESSAVEIS` (server.py), após a entrada `"fogo_grego": {…},`
e antes do `}` que fecha o dict, adicione:

```python
    "bomba_incendiaria": {
        "id": "bomba_incendiaria", "name": "Bomba Incendiária", "emoji": "💣",
        "alcance": 4, "alvo": "area", "area_raio": 1, "dano": "2d6", "elemento": "fogo",
        "save": {"tipo": "reflexos", "cd": 12},
        "em_chamas": True, "chamas_dur": "1d4", "chamas_agua_apaga": True,
    },
    "granada": {
        "id": "granada", "name": "Granada Explosiva", "emoji": "💣",
        "alcance": 4, "alvo": "area", "area_raio": 1, "dano": "2d6", "elemento": "explosao",
        "save": {"tipo": "reflexos", "cd": 12},
    },
    "granada_superior": {
        "id": "granada_superior", "name": "Granada Superior", "emoji": "💥",
        "alcance": 4, "alvo": "area", "area_raio": 1, "dano": "3d6", "elemento": "explosao",
        "save": {"tipo": "reflexos", "cd": 15},
    },
    "bomba_fumaca": {
        "id": "bomba_fumaca", "name": "Bomba de Fumaça", "emoji": "💨",
        "alcance": 4, "alvo": "area", "area_raio": 1,
        "zona": {"tipo": "escuridao", "duracao": 2},
    },
```

- [ ] **Step 4: Adicionar os 4 itens em `SHOP_MERCHANT`**

Logo após as linhas de `frasco_oleo`/`fogo_grego` em `SHOP_MERCHANT`, adicione:

```python
    {"id": "bomba_incendiaria", "name": "Bomba Incendiária", "emoji": "💣", "price": 45, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "granada",           "name": "Granada Explosiva", "emoji": "💣", "price": 40, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "granada_superior",  "name": "Granada Superior",  "emoji": "💥", "price": 70, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "bomba_fumaca",      "name": "Bomba de Fumaça",   "emoji": "💨", "price": 30, "item_slot": "bag", "effect": "throwable", "value": 0},
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_area.py`
Expected: PASS — seção [1] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_area.py
git commit -m "feat(arremessaveis): 4 itens de area no catalogo + loja"
```

---

### Task 2: `_aplicar_escuridao` aceita um centro

**Files:**
- Modify: `server.py:10681` — `_aplicar_escuridao`
- Test: `tools/test_arremessaveis_area.py`

- [ ] **Step 1: Adicionar o teste [2] (zona no tile escolhido)**

Antes do `print(f"\n=== ...")` final:

```python
    # ── [2] _aplicar_escuridao com centro explícito ────────────────────────────
    print("\n[2] _aplicar_escuridao(pos=...)")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    r.zonas_especiais = []
    await r._aplicar_escuridao(p, raio=1, duracao=2, pos=[5, 6])
    z = r.zonas_especiais[-1]
    check("zona criada no centro escolhido", z["cx"] == 5 and z["cy"] == 6)
    check("zona tipo escuridao", z["tipo"] == "escuridao")
    check("zona duracao 2", z["duracao"] == 2)
    # Sem pos → cai na casa do caster (compatibilidade com o Manto de Escuridão)
    await r._aplicar_escuridao(p, raio=1, duracao=1)
    check("sem pos usa a casa do caster", r.zonas_especiais[-1]["cx"] == 1)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_area.py`
Expected: FAIL — `TypeError: _aplicar_escuridao() got an unexpected keyword argument 'pos'`

- [ ] **Step 3: Generalizar `_aplicar_escuridao`**

Substitua a assinatura e a extração de `x, y` (server.py:10681-10683):

```python
    async def _aplicar_escuridao(self, caster, raio, duracao, pos=None):
        """Cria uma zona de escuridão. `pos` (default = casa do caster) permite
        centrar num tile arbitrário (ex.: Bomba de Fumaça)."""
        x, y = pos if pos is not None else caster.get("pos", [0, 0])
```

(O resto do método — o `append` da zona — fica igual.)

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_area.py`
Expected: PASS — seções [1]-[2] OK.

- [ ] **Step 5: Confirmar que a magia Manto de Escuridão não quebrou**

Run: `python -c "import server; print('OK')"`
Expected: `OK` (a chamada em server.py:9159 usa só args posicionais; `pos` fica default).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_area.py
git commit -m "feat(arremessaveis): _aplicar_escuridao aceita centro explicito"
```

---

### Task 3: Refactor `handle_throw_item(pid, data)` + preservar o modo de A

**Files:**
- Modify: `server.py` — `handle_throw_item` (6513) vira despachante; extrai `_throw_item_alvo`; dispatch WS (15316)
- Modify: `tools/test_arremessaveis.py` — 4 chamadas (linhas 105, 116, 128, 137)
- Test: `tools/test_arremessaveis.py` (regressão de A) + novo teste de dispatch no de área

- [ ] **Step 1: Atualizar as 4 chamadas no teste de A para a nova assinatura**

Em `tools/test_arremessaveis.py`, troque cada uma das 4 chamadas
`await r.handle_throw_item("p1", "<item>", "<target>")` pela forma com dict:

```python
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})   # linha 105
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})   # linha 116
    await r.handle_throw_item("p1", {"item_id": "fogo_grego",  "target_id": "m1"})   # linha 128
    await r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"})   # linha 137
```

(Use os mesmos `item_id`/`target_id` que já estavam em cada chamada — confira caso
a linha exata tenha mudado.)

- [ ] **Step 2: Rodar o teste de A e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — a nova assinatura ainda não existe (`handle_throw_item` só aceita 3 args posicionais), então as chamadas com dict quebram.

- [ ] **Step 3: Refatorar `handle_throw_item` para despachar por tipo de alvo**

Substitua TODO o método `handle_throw_item` (server.py:6513-6588) por um
despachante + o helper `_throw_item_alvo` com a lógica original de A:

```python
    async def handle_throw_item(self, pid, data):
        """Arremessa um consumível de bolsa (ARREMESSAVEIS). AÇÃO PRINCIPAL.
        Despacha por defn['alvo']: 'ataque_alvo' (single-target, teste de ataque)
        ou 'area' (área com save). `data` é o dict da mensagem (item_id +
        target_id OU tx/ty)."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        data = data or {}
        item_id = data.get("item_id")
        item = next((i for i in p["bag"] if i["id"] == item_id), None)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado na bolsa."}); return
        defn = ARREMESSAVEIS.get(item_id)
        if not defn:
            await self.send_to(pid, {"type": "error", "msg": "Item não arremessável."}); return
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        alvo_tipo = defn.get("alvo")
        if alvo_tipo == "ataque_alvo":
            await self._throw_item_alvo(p, defn, item, data.get("target_id"))
        elif alvo_tipo == "area":
            await self._throw_item_area(p, defn, item, data.get("tx"), data.get("ty"))
        else:
            await self.send_to(pid, {"type": "error", "msg": "Item não arremessável."}); return

    async def _throw_item_alvo(self, p, defn, item, target_id):
        """Arremesso single-target: teste de ataque por DES vs CA (espelha
        _executar_arremesso). Consome o item em acerto E erro."""
        pid = p["id"]
        if target_id not in self.monsters:
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
        target = self.monsters[target_id]
        if target.get("hp", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Alvo já está morto."}); return

        rng = defn["alcance"]
        dx = abs(p["pos"][0] - target["pos"][0]); dy = abs(p["pos"][1] - target["pos"][1])
        if max(dx, dy) > rng:
            await self.send_to(pid, {"type": "error",
                "msg": f"⚠ {target['name']} fora de alcance (máx {rng} quadrados)."}); return
        if not self._tem_linha_de_visao(p["pos"], target["pos"]):
            await self.send_to(pid, {"type": "error",
                "msg": f"🧱 Uma parede bloqueia o arremesso até {target['name']}!"}); return

        dex_mod = mod(p.get("dex", 12))
        roll = random.randint(1, 20)
        total = roll + p["atk_bonus"]
        nat1 = (roll == 1); crit = (roll == 20)
        hit = (not nat1) and (crit or total >= target["ac"])
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                              "label": f"Arremesso ({defn['name']})", "hit": hit, "crit": crit})

        p["bag"].remove(item)
        p["action_done"] = True
        self._consumir_recursos(p, 'apenas_acao')

        if hit:
            raw = roll_dice(defn["dano"])
            dmg = max(1, (raw + dex_mod) * (2 if crit else 1))
            die_type = "d" + defn["dano"].split("d")[1]
            await self.broadcast({"type": "dice_roll", "die": die_type,
                                  "value": raw, "label": "Dano (arremesso)"})
            crit_str = " **CRÍTICO!**" if crit else ""
            await self.gm_say(
                f"{defn['emoji']} **{p['name']}** arremessa **{defn['name']}** em "
                f"**{target['name']}** (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}):"
                f"{crit_str} **{dmg}** de {defn['elemento']}!")
            await self._dano_em_alvo(target, dmg, defn["elemento"], pid)
            if defn.get("em_chamas") and target.get("hp", 0) > 0:
                dur = self._rolar_dado(defn.get("chamas_dur", "1d4"))
                self._aplicar_em_chamas(target, dur, defn.get("chamas_agua_apaga", True))
                await self.gm_say(f"🔥 **{target['name']}** pega fogo por {dur} rodada(s)!")
        elif nat1:
            await self.gm_say(
                f"{defn['emoji']} **{p['name']}** arremessa **{defn['name']}** mas rola "
                f"**1 natural** — o frasco se espatifa longe do alvo!")
        else:
            await self.gm_say(
                f"{defn['emoji']} **{p['name']}** arremessa **{defn['name']}** em "
                f"**{target['name']}** (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']}): **ERROU!**")

        await self.push_state()

    async def _throw_item_area(self, p, defn, item, tx, ty):
        """Placeholder — implementado na Task 4."""
        await self.send_to(p["id"], {"type": "error",
            "msg": f"{defn['name']} ainda está em desenvolvimento."})
```

- [ ] **Step 4: Atualizar o dispatch WS**

Em server.py:15316, troque:

```python
                    if room: await room.handle_throw_item(pid, msg.get("item_id"), msg.get("target_id"))
```
por:
```python
                    if room: await room.handle_throw_item(pid, msg)
```

- [ ] **Step 5: Rodar o teste de A e ver passar (regressão)**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — `46 OK / 0 FALHAS` (o modo `ataque_alvo` continua idêntico via a nova assinatura).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "refactor(arremessaveis): handle_throw_item(pid, data) + dispatch por alvo"
```

---

### Task 4: `_throw_item_area` — dano de área, save, fogo amigo, fumaça

**Files:**
- Modify: `server.py` — substituir o placeholder `_throw_item_area` pela implementação real
- Test: `tools/test_arremessaveis_area.py`

- [ ] **Step 1: Adicionar os testes [3]-[6] (dano/save/incendiária/fumaça/alcance)**

```python
    # ── [3] Dano de área a TODOS (fogo amigo), save = metade ────────────────────
    print("\n[3] Granada: dano de área + fogo amigo + save")
    r = setup(); random.seed(3)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    ally = make_player("p2", "A", "cleric", 0); ally["pos"] = [5, 5]; r.players["p2"] = ally
    m = make_monster(r, "m1", 5, 6, hp=40)   # adjacente ao centro (5,5)
    # saves sempre falham → dano cheio (patch determinístico)
    r._save_mostrado = _mk_save(False)
    hp_ally0, hp_m0 = ally["hp"], m["hp"]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 5, "ty": 5})
    check("monstro no raio sofreu dano", m["hp"] < hp_m0)
    check("ALIADO no raio sofreu dano (fogo amigo)", ally["hp"] < hp_ally0)
    check("item consumido", len(p["bag"]) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    # save com sucesso → metade
    r = setup(); random.seed(3)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    m = make_monster(r, "m1", 5, 5, hp=40)
    r._save_mostrado = _mk_save(True)
    hp0 = m["hp"]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 5, "ty": 5})
    dano_meio = hp0 - m["hp"]
    check("save reduz o dano (metade)", 0 < dano_meio <= (12 // 2))  # 2d6 máx 12 → ≤6

    # ── [4] Bomba Incendiária: quem sofre dano fica em chamas ───────────────────
    print("\n[4] Incendiária: em chamas nos atingidos")
    r = setup(); random.seed(4)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("bomba_incendiaria")]
    m = make_monster(r, "m1", 5, 5, hp=40)
    r._save_mostrado = _mk_save(False)
    await r.handle_throw_item("p1", {"item_id": "bomba_incendiaria", "tx": 5, "ty": 5})
    check("atingido ficou em chamas", m.get("em_chamas_rodadas", 0) > 0)
    check("chamas apagáveis por água", m.get("chamas_agua_apaga") is True)

    # ── [5] Granada Superior: 3d6 / CD 15 aplicados ─────────────────────────────
    print("\n[5] Granada Superior")
    r = setup(); random.seed(5)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("granada_superior")]
    m = make_monster(r, "m1", 5, 5, hp=60)
    saves = []
    async def cap_save(alvo, tipo, cd, *a, **k):
        saves.append(cd); return (False, 1, 0, 1)
    r._save_mostrado = cap_save
    await r.handle_throw_item("p1", {"item_id": "granada_superior", "tx": 5, "ty": 5})
    check("save usou CD 15", 15 in saves)
    check("dano de 3d6 aplicado (>0)", m["hp"] < 60)

    # ── [6] Bomba de Fumaça: zona de escuridão que expira em 2 rodadas ──────────
    print("\n[6] Fumaça")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [1, 1]; r.players["p1"] = p
    p["bag"] = [throwable("bomba_fumaca")]
    r.zonas_especiais = []
    await r.handle_throw_item("p1", {"item_id": "bomba_fumaca", "tx": 6, "ty": 6})
    z = [z for z in r.zonas_especiais if z.get("tipo") == "escuridao"]
    check("criou zona de escuridão no tile", len(z) == 1 and z[0]["cx"] == 6 and z[0]["cy"] == 6)
    check("fumaça consumida", len(p["bag"]) == 0)
    await r._processar_zonas_turno(); await r._processar_zonas_turno()
    check("zona expira após 2 rodadas",
          not any(z.get("tipo") == "escuridao" and z.get("ativa") for z in r.zonas_especiais))

    # ── [7] Alcance / LOS até o centro ──────────────────────────────────────────
    print("\n[7] Alcance/LOS")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [0, 0]; r.players["p1"] = p
    p["bag"] = [throwable("granada")]
    await r.handle_throw_item("p1", {"item_id": "granada", "tx": 9, "ty": 9})  # >4
    check("fora de alcance: item mantido", len(p["bag"]) == 1)
    check("fora de alcance: ação não gasta", not p.get("action_done"))
```

Adicione também o helper `_mk_save` no topo do arquivo (após `make_monster`):

```python
def _mk_save(passou):
    async def _s(alvo, tipo, cd, *a, **k):
        return (passou, 1, 0, 1)   # (passou, d20, bonus, total)
    return _s
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_area.py`
Expected: FAIL — o `_throw_item_area` ainda é o placeholder ("em desenvolvimento").

- [ ] **Step 3: Implementar `_throw_item_area`**

Substitua o placeholder `_throw_item_area` (Task 3, Step 3) por:

```python
    async def _throw_item_area(self, p, defn, item, tx, ty):
        """Arremesso de ÁREA: sem jogada de ataque. Atinge TODOS no raio (fogo
        amigo, como a Bola de Fogo) com save de Reflexos (metade no sucesso);
        opcionalmente aplica 'em chamas' e/ou cria uma zona (fumaça=escuridão)."""
        pid = p["id"]
        if tx is None or ty is None:
            await self.send_to(pid, {"type": "error", "msg": "Alvo de área inválido."}); return
        cx, cy = int(tx), int(ty)
        rng = defn["alcance"]
        if max(abs(p["pos"][0] - cx), abs(p["pos"][1] - cy)) > rng:
            await self.send_to(pid, {"type": "error",
                "msg": f"⚠ Centro fora de alcance (máx {rng} quadrados)."}); return
        if not self._tem_linha_de_visao(p["pos"], [cx, cy]):
            await self.send_to(pid, {"type": "error",
                "msg": "🧱 Uma parede bloqueia a trajetória do arremesso!"}); return

        # Consome o item + gasta a ação principal.
        p["bag"].remove(item)
        p["action_done"] = True
        self._consumir_recursos(p, 'apenas_acao')
        raio = defn.get("area_raio", 1)
        await self.gm_say(f"{defn['emoji']} **{p['name']}** arremessa **{defn['name']}** em ({cx},{cy})!")

        # Dano de área com save de Reflexos (metade no sucesso).
        if defn.get("dano"):
            raw = roll_dice(defn["dano"])
            die_type = "d" + defn["dano"].split("d")[1]
            await self.broadcast({"type": "dice_roll", "die": die_type,
                                  "value": raw, "label": f"Dano ({defn['name']})"})
            save = defn.get("save") or {}
            cd = save.get("cd")
            for alvo in self._alvos_na_area(cx, cy, raio):
                # Sombra de parede: quem está atrás de parede a partir do centro escapa.
                if not self._tem_linha_de_visao([cx, cy], alvo["pos"]):
                    continue
                d = raw
                if cd:
                    save_ok, *_ = await self._save_mostrado(alvo, save.get("tipo", "reflexos"), cd)
                    if save_ok:
                        d = raw // 2
                if d <= 0:
                    continue
                nome = alvo.get("name") or alvo.get("nome", "Alvo")
                await self.gm_say(f"{defn['emoji']} **{nome}** sofre {d} de {defn['elemento']}.")
                await self._dano_em_alvo(alvo, d, defn["elemento"], pid)
                if defn.get("em_chamas") and self._vivo(alvo):
                    dur = self._rolar_dado(defn.get("chamas_dur", "1d4"))
                    self._aplicar_em_chamas(alvo, dur, defn.get("chamas_agua_apaga", True))

        # Zona (Bomba de Fumaça = escuridão centrada no tile).
        zona = defn.get("zona")
        if zona and zona.get("tipo") == "escuridao":
            await self._aplicar_escuridao(p, raio=raio, duracao=zona.get("duracao", 2), pos=[cx, cy])

        await self.push_state()
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_area.py`
Expected: PASS — seções [1]-[7] OK.

- [ ] **Step 5: Rodar a regressão de A e vizinhos**

Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_ground_items.py`
Expected: ambos passam.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_area.py
git commit -m "feat(arremessaveis): _throw_item_area (dano+save, fogo amigo, chamas, fumaca)"
```

---

### Task 5: Cliente — catálogo, sender e clique de área (`gameState.js`)

**Files:**
- Modify: `src/gameState.js` — `CATALOGO_ITENS`, `resolveTileClick`, sender `throwItemArea`, API pública
- Test: manual

- [ ] **Step 1: Adicionar as 4 entradas no `CATALOGO_ITENS`**

Junto das entradas `frasco_oleo`/`fogo_grego` (Sub-projeto A), adicione:

```javascript
    bomba_incendiaria: {
      id: 'bomba_incendiaria', nome: 'Bomba Incendiária', emoji: '💣',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1,
      descricao: 'Área (raio 1, alcance 4). 2d6 de fogo, Reflexos CD 12 (metade). ' +
                 'Todos os atingidos pegam fogo. ACERTA ALIADOS — cuidado com o posicionamento.',
    },
    granada: {
      id: 'granada', nome: 'Granada Explosiva', emoji: '💣',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1,
      descricao: 'Área (raio 1, alcance 4). 2d6 de explosão, Reflexos CD 12 (metade). ' +
                 'ACERTA ALIADOS.',
    },
    granada_superior: {
      id: 'granada_superior', nome: 'Granada Superior', emoji: '💥',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1,
      descricao: 'Área (raio 1, alcance 4). 3d6 de explosão, Reflexos CD 15 (metade). ' +
                 'ACERTA ALIADOS.',
    },
    bomba_fumaca: {
      id: 'bomba_fumaca', nome: 'Bomba de Fumaça', emoji: '💨',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1,
      descricao: 'Área (raio 1, alcance 4). Cria escuridão por 2 rodadas — bloqueia ' +
                 'a visão e cobre o recuo. Sem dano.',
    },
```

- [ ] **Step 2: Adicionar o sender `throwItemArea`**

Junto de `throwItem`/`apagarChamas` (Sub-projeto A):

```javascript
  function throwItemArea(id, tx, ty) { send({ type: 'throw_item', item_id: id, tx, ty }); }
```

- [ ] **Step 3: Tratar o modo de área em `resolveTileClick`**

No ramo `if (pendingThrow) { ... }` (adicionado no Sub-projeto A), passe a
distinguir o tipo de alvo. Substitua o corpo do ramo por:

```javascript
    if (pendingThrow) {
      const th   = pendingThrow;
      const alvo = (CATALOGO_ITENS[th.id] || {}).alvo || 'ataque_alvo';
      const ddx  = Math.abs(myP.pos[0] - tx);
      const ddy  = Math.abs(myP.pos[1] - ty);
      const inRange = Math.max(ddx, ddy) <= th.alcance;
      const losOk   = hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty);
      if (alvo === 'area') {
        // Área: mira numa CASA (não precisa de monstro), valida alcance + LOS ao centro.
        if (inRange && losOk) return { type: 'throw_area', itemId: th.id, tx, ty };
        return { type: 'throw_blocked' };
      }
      // ataque_alvo (Sub-projeto A): precisa de um monstro na casa.
      const m = gameState.monsters.find(m => m.hp > 0 &&
        monsterTiles(m).some(([bx, by]) => bx === tx && by === ty));
      if (m) {
        if (inRange && losOk) return { type: 'throw', itemId: th.id, targetId: m.id };
        return { type: 'throw_blocked' };
      }
      return null; // consome o clique, permanece na mira (ESC cancela)
    }
```

- [ ] **Step 4: Expor `throwItemArea` na API pública**

Junto de `throwItem`/`apagarChamas`:

```javascript
    throwItemArea,
```

- [ ] **Step 5: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js
git commit -m "feat(arremessaveis): cliente area — catalogo, throwItemArea, resolveTileClick"
```

---

### Task 6: Cliente — prévia de área verde na mira (`game.js`)

**Files:**
- Modify: `game.js` — `_iniciarMiraArremesso` (ramifica p/ área), roteamento do clique de área
- Test: manual (visual)

> Trecho com instruções de espelhamento (a maquinaria de prévia de área verde já
> existe nas magias). Leia primeiro e reuse — não reinvente.

- [ ] **Step 1: Ler a prévia de área das magias (referência)**

Leia em game.js: `_recomputarAreaMagia` (~9503), `window._spellHL.area`,
`_aplicarSpellHL` (~9549), e como o mousemove das magias chama `_recomputarAreaMagia`
(2D ~11065; 3D no mousemove de `_modoMagia`). Esse é o molde da prévia de área verde
que segue o cursor.

- [ ] **Step 2: Ramificar `_iniciarMiraArremesso` para o modo de área**

Em `_iniciarMiraArremesso` (Sub-projeto A, ~9285), após montar
`window._modoThrowItem`/`GS.pendingThrow`, leia `catDef.alvo`:
- Se `'area'`: além de pintar o **alcance** vermelho (`_spellHL.range`, como hoje),
  marque `window._modoThrowItem.area = catDef.areaRaio || 1` e deixe a **prévia de
  área verde** ser recalculada no hover (Step 3). Ajuste a legenda para "Clique numa
  CASA (área raio N)".
- Se `'ataque_alvo'`: comportamento atual (inalterado).

- [ ] **Step 3: Recalcular a prévia verde no hover (2D e 3D)**

Onde o mousemove já trata `window._modoMagia` chamando `_recomputarAreaMagia(tx, ty)`
(2D ~11065 e o equivalente 3D), adicione um ramo irmão para o arremesso de área:
quando `window._modoThrowItem && window._modoThrowItem.area`, chame
`_recomputarAreaMagia(tx, ty)` com o raio do item (passe/adapte o raio, já que a
função hoje lê o raio da magia ativa — a forma mais simples é setar um
`window._spellHL.area` com `_addCheb(tx, ty, raio, area)` diretamente no handler de
hover do arremesso, seguindo o corpo de `_recomputarAreaMagia`). Reaproveite
`_aplicarSpellHL()` para desenhar.

- [ ] **Step 4: Rotear o clique de área (2D e 3D)**

No `_clickTileThrow` (Sub-projeto A), o `GS.resolveTileClick` agora pode retornar
`{type:'throw_area', ...}`. Trate-o:

```javascript
function _clickTileThrow(tx, ty){
  if(!window._modoThrowItem) return;
  const r = GS.resolveTileClick(tx, ty);
  if(r && r.type === 'throw'){
    GS.throwItem(r.itemId, r.targetId);
    _encerrarMiraArremesso();
  } else if(r && r.type === 'throw_area'){
    GS.throwItemArea(r.itemId, r.tx, r.ty);
    _encerrarMiraArremesso();
  } else if(r && r.type === 'throw_blocked'){
    toast('Fora de alcance ou parede no caminho.', 'var(--gold)');
  }
}
```

- [ ] **Step 5: Garantir limpeza da prévia de área ao encerrar**

Confirme que `_encerrarMiraArremesso` (Sub-projeto A) já zera `window._spellHL.area`
(ele zera `range`/`area`/`double` e chama `_aplicarSpellHL`). Se não estiver zerando
`area`, adicione `window._spellHL.area = new Set();` lá.

- [ ] **Step 6: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem erros.

- [ ] **Step 7: Commit**

```bash
git add game.js
git commit -m "feat(arremessaveis): mira de area (previa verde) no cliente"
```

---

### Task 7: Verificação end-to-end

**Files:** nenhum

- [ ] **Step 1: Suíte completa do servidor**

Run: `python tools/test_arremessaveis_area.py`
Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_ground_items.py`
Run: `python tools/test_roteamento_itens.py`
Expected: todos `0 FALHAS` / `0 XX` / `0 falharam`.

- [ ] **Step 2: Syntax check do cliente**

Run: `node --check src/gameState.js && node --check game.js`
Expected: sem erros.

- [ ] **Step 3: Verificação manual (`iniciar.bat`)**

Compre as 4 bombas na loja e, numa masmorra:
1. Clique direito na Granada → mira com **alcance** e **área verde** que segue o cursor
2. Jogar numa casa com monstro + aliado por perto → ambos rolam Reflexos e tomam dano (fogo amigo)
3. Bomba Incendiária → atingidos ficam 🔥 (indicador de A) e tomam tick nas rodadas
4. Granada Superior → dano maior (3d6), save mais difícil (CD 15)
5. Bomba de Fumaça → cria escuridão na área por 2 rodadas (bloqueia visão), sem dano
6. Fora do alcance / atrás de parede → toast, item não gasto; ESC cancela
7. Óleo/Fogo Grego (Sub-projeto A) continuam funcionando (mira single-target vermelha)

- [ ] **Step 4: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(arremessaveis): ajustes da verificacao de area"
```

---

## Self-review (cobertura do spec)

- ✅ Mira de área (alcance + prévia verde) → Tasks 5, 6.
- ✅ `resolveTileClick` ramo de área + `throw_area` → Task 5.
- ✅ 4 itens no catálogo/loja → Task 1.
- ✅ `handle_throw_item(pid, data)` despacha por `alvo` (refactor + regressão de A) → Task 3.
- ✅ `_throw_item_area`: dano de área, fogo amigo, save de Reflexos (metade), em chamas nos atingidos → Task 4.
- ✅ Bomba de Fumaça = escuridão no tile (`_aplicar_escuridao(pos=…)`) → Tasks 2, 4.
- ✅ Granada Superior 3d6/CD15 → Tasks 1, 4.
- ✅ Alcance/LOS até o centro → Task 4.
- ✅ Testes → `tools/test_arremessaveis_area.py` (Tasks 1-4) + regressão de A (Task 3) + manual (Task 7).

**Fora de escopo (confirmado):** corrosão/ácido (C), cola/rede (D), veneno Agonia
Sufocante (E), zona de dano persistente no chão, subsistema de furtividade,
animação 3D elaborada de explosão.
```
