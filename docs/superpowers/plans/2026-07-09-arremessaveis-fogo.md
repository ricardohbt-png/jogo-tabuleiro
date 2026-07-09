# Arremessáveis de Fogo (Sub-projeto A) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar um framework de itens arremessáveis de bolsa (usados por clique direito, com mira de alvo), e os dois primeiros itens — Frasco de Óleo Incendiário e Fogo Grego — que causam dano de fogo e aplicam o status "em chamas".

**Architecture:** Segue a separação estrita do projeto (server autoritativo + `gameState.js` lógico + `game.js` render). Novo catálogo declarativo `ARREMESSAVEIS` no servidor (estilo `ARMADILHAS`/`GRIMORIO`), nova mensagem `throw_item` resolvida em `handle_throw_item` (teste de ataque por DES, espelhando `_executar_arremesso`), status `em_chamas_rodadas` com tick 1×/rodada no mesmo ponto da incendiária, e apagar via água (ação livre) ou ação (`apagar_chamas`). No cliente, o clique direito vira "usar/ativar" universal e a mira dos arremessáveis espelha os modos de arremesso de adaga já existentes (`_modoArremesso*`).

**Tech Stack:** Python 3 + `websockets` (server.py, sem libs novas); Vanilla JS (src/gameState.js, src/ui/inventoryModal.js, game.js); testes com o harness caseiro de `tools/test_*.py` (asyncio, stubs de rede).

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | Catálogo `ARREMESSAVEIS`, itens na `SHOP_MERCHANT`, `handle_throw_item`, `_aplicar_em_chamas`, `_processar_em_chamas_turno`, `handle_apagar_chamas`, ramo de água em `handle_use_item`, serialização de `em_chamas_rodadas`, dispatch WS |
| `src/gameState.js` | Modificar | `CATALOGO_ITENS` (2 itens), senders `throwItem`/`apagarChamas`, estado `pendingThrow`, ramo em `resolveTileClick`, API pública |
| `src/ui/inventoryModal.js` | Modificar | Clique direito = usar/ativar (migra poção/pergaminho); throwables entram no modo-alvo |
| `game.js` | Modificar | Render da mira (tiles vermelhos, 2D+3D) espelhando `_modoArremesso`, indicador 🔥 no peão, botão "Apagar chamas" no HUD |
| `tools/test_arremessaveis.py` | Criar | Testes do servidor (catálogo, throw, chamas, tick, apagar) |

> **Nota de arquitetura:** todo cálculo (alcance, LOS, acerto, dano, tick) fica no servidor; `gameState.js` só decide o alvo do clique e envia; `game.js` só desenha. Não colocar lógica de jogo em `game.js`.

---

### Task 1: Catálogo `ARREMESSAVEIS` + itens na loja

**Files:**
- Modify: `server.py` — inserir catálogo logo após `SHOP_AMMO` (após a linha 2202) e itens em `SHOP_MERCHANT` (após a linha 2186, antes do `]` da lista)
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Criar o arquivo de teste com o harness e o 1º teste (catálogo)**

Crie `tools/test_arremessaveis.py`:

```python
"""Testes dos arremessáveis de fogo (Sub-projeto A).
Roda da raiz: python tools/test_arremessaveis.py
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

def setup(w=9, h=9):
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
    m = {"id": mid, "name": "Alvo", "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo e itens de loja ───────────────────────────────────────────
    print("\n[1] Catálogo ARREMESSAVEIS + loja")
    check("frasco_oleo no catálogo", "frasco_oleo" in ARREMESSAVEIS)
    check("fogo_grego no catálogo", "fogo_grego" in ARREMESSAVEIS)
    oleo = ARREMESSAVEIS["frasco_oleo"]
    check("óleo: alcance 4", oleo["alcance"] == 4)
    check("óleo: dano 1d6", oleo["dano"] == "1d6")
    check("óleo: água apaga", oleo["chamas_agua_apaga"] is True)
    grego = ARREMESSAVEIS["fogo_grego"]
    check("grego: dano 2d6", grego["dano"] == "2d6")
    check("grego: água NÃO apaga", grego["chamas_agua_apaga"] is False)
    check("óleo vendável na loja", any(i["id"] == "frasco_oleo" for i in SHOP_MERCHANT))
    check("loja: óleo effect=throwable",
          throwable("frasco_oleo")["effect"] == "throwable")

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — `ImportError: cannot import name 'ARREMESSAVEIS'`

- [ ] **Step 3: Adicionar o catálogo `ARREMESSAVEIS` no server.py**

Logo após o bloco `SHOP_AMMO = [ ... ]` (a lista termina na linha 2202), insira:

```python
# ─── ARREMESSÁVEIS ────────────────────────────────────────────────────────────
# Consumíveis de bolsa arremessados numa casa/alvo (não são armas equipadas).
# Usados por `throw_item` → handle_throw_item. Catálogo declarativo, estilo
# ARMADILHAS/GRIMORIO. Sub-projeto A implementa só o modo single-target de fogo;
# o modo "area" já é reconhecido pelo campo `alvo` (Sub-projeto B).
ARREMESSAVEIS = {
    "frasco_oleo": {
        "id": "frasco_oleo", "name": "Frasco de Óleo Incendiário", "emoji": "🔥",
        "alcance": 4, "alvo": "ataque_alvo", "dano": "1d6", "elemento": "fogo",
        "em_chamas": True, "chamas_dur": "1d4", "chamas_agua_apaga": True,
    },
    "fogo_grego": {
        "id": "fogo_grego", "name": "Fogo Grego", "emoji": "🟢",
        "alcance": 4, "alvo": "ataque_alvo", "dano": "2d6", "elemento": "fogo",
        "em_chamas": True, "chamas_dur": "1d4", "chamas_agua_apaga": False,
    },
}
```

- [ ] **Step 4: Adicionar os dois itens em `SHOP_MERCHANT`**

Na lista `SHOP_MERCHANT`, logo após a linha do `veneno_polvo_abissal` (linha 2186) e antes do `]`, adicione:

```python
    # ── Arremessáveis de fogo (consumíveis de bolsa; ver ARREMESSAVEIS) ──
    {"id": "frasco_oleo", "name": "Frasco de Óleo Incendiário", "emoji": "🔥", "price": 15, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "fogo_grego",  "name": "Fogo Grego",                 "emoji": "🟢", "price": 40, "item_slot": "bag", "effect": "throwable", "value": 0},
```

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seção [1] toda OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): catalogo ARREMESSAVEIS + itens de fogo na loja"
```

---

### Task 2: Status "em chamas" — aplicação e refresh

**Files:**
- Modify: `server.py` — novo método `_aplicar_em_chamas` (colocar perto de `_dano_em_alvo`, ~linha 11109)
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Adicionar o teste [2] (aplicação + refresh)**

Antes do `print(f"\n=== ...")` final, adicione:

```python
    # ── [2] Status em chamas: aplicar e refresh (max, não soma) ─────────────────
    print("\n[2] _aplicar_em_chamas")
    r = setup()
    m = make_monster(r, "m1", 4, 4)
    r._aplicar_em_chamas(m, 3, True)
    check("aplicou 3 rodadas", m.get("em_chamas_rodadas") == 3)
    check("gravou flag de água", m.get("chamas_agua_apaga") is True)
    r._aplicar_em_chamas(m, 2, True)   # menor → não reduz
    check("refresh usa o MAIOR (não reduz p/ 2)", m["em_chamas_rodadas"] == 3)
    r._aplicar_em_chamas(m, 5, False)  # maior → sobe e troca a flag
    check("refresh sobe p/ 5", m["em_chamas_rodadas"] == 5)
    check("flag de água atualizada p/ False", m["chamas_agua_apaga"] is False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute '_aplicar_em_chamas'`

- [ ] **Step 3: Implementar `_aplicar_em_chamas`**

Logo após o método `_dano_em_alvo` (termina na linha 11108), adicione:

```python
    def _aplicar_em_chamas(self, alvo, rodadas, agua_apaga):
        """Coloca (ou renova) o status 'em chamas' num ente (herói ou monstro).
        Renovar usa o MAIOR valor de duração (refresh), nunca soma dano.
        `agua_apaga`=False (Fogo Grego) prevalece: beber água não apaga."""
        atual = alvo.get("em_chamas_rodadas", 0)
        alvo["em_chamas_rodadas"] = max(atual, int(rodadas))
        alvo["chamas_agua_apaga"] = bool(agua_apaga)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seções [1] e [2] OK.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): status em_chamas com refresh por max"
```

---

### Task 3: Tick de fogo por rodada

**Files:**
- Modify: `server.py` — novo `_processar_em_chamas_turno` (perto de `_processar_efeitos_armadilha_turno`, ~linha 11404) + chamada no fim de rodada (linha 11837)
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Adicionar o teste [3] (tick em herói e monstro)**

```python
    # ── [3] Tick de fogo: 1 dano/rodada, decrementa, expira ─────────────────────
    print("\n[3] _processar_em_chamas_turno")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    m = make_monster(r, "m1", 5, 5, hp=10)
    r._aplicar_em_chamas(p, 2, True)
    r._aplicar_em_chamas(m, 2, False)
    hp_p0, hp_m0 = p["hp"], m["hp"]
    await r._processar_em_chamas_turno()
    check("herói perde 1 HP no tick", p["hp"] == hp_p0 - 1)
    check("monstro perde 1 HP no tick", m["hp"] == hp_m0 - 1)
    check("duração do herói caiu p/ 1", p["em_chamas_rodadas"] == 1)
    await r._processar_em_chamas_turno()
    check("status do herói expira (0)", p.get("em_chamas_rodadas", 0) == 0)
    hp_p1 = p["hp"]
    await r._processar_em_chamas_turno()
    check("sem status → sem dano extra", p["hp"] == hp_p1)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — `AttributeError: ... '_processar_em_chamas_turno'`

- [ ] **Step 3: Implementar `_processar_em_chamas_turno`**

Logo após `_processar_efeitos_armadilha_turno` (termina na linha 11404), adicione:

```python
    async def _processar_em_chamas_turno(self):
        """Tica 1 de dano de fogo em cada ente 'em chamas', 1×/rodada. Decrementa
        a duração e limpa em 0. Manda popup de tick (trap_result) ao jogador
        afetado (ou ao rescuer do prisioneiro); monstros não recebem cliente."""
        entes = list(self.players.values()) + list(self.monsters.values())
        if self.prisoner is not None:
            entes.append(self.prisoner)
        for alvo in entes:
            if alvo.get("em_chamas_rodadas", 0) <= 0:
                continue
            if not (alvo.get("alive") or alvo.get("hp", 0) > 0):
                alvo["em_chamas_rodadas"] = 0
                continue
            await self._dano_em_alvo(alvo, 1, "fogo", None)
            if self._eh_jogador(alvo) or alvo is self.prisoner:
                await self._enviar_trap_result(
                    alvo, "Em Chamas", "🔥", sucesso=False, dano=1, metade=False,
                    descricao="As chamas continuam queimando.",
                    efeitos_extra=[], tick=True)
            alvo["em_chamas_rodadas"] = max(0, alvo.get("em_chamas_rodadas", 0) - 1)
```

- [ ] **Step 4: Ligar a chamada no fim da rodada**

No `handle_end_turn`, logo após a linha 11837
(`await self._processar_efeitos_armadilha_turno()`), adicione:

```python
            await self._processar_em_chamas_turno()            # tick do status "em chamas"
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seções [1]–[3] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): tick de dano do status em_chamas por rodada"
```

---

### Task 4: `handle_throw_item` — arremesso com teste de ataque

**Files:**
- Modify: `server.py` — novo `handle_throw_item` (colocar após `_executar_arremesso`, ~linha 6540) + dispatch WS
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Adicionar o teste [4] (acerto / erro / alcance / LOS / consumo)**

```python
    # ── [4] handle_throw_item: acerto, consumo, chamas, alcance, LOS ────────────
    print("\n[4] handle_throw_item")

    # (4a) Acerto garantido (CA baixa) → dano + em chamas + item consumido
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    r.players["p1"] = p; p["bag"] = [throwable("frasco_oleo")]
    m = make_monster(r, "m1", 4, 6, hp=30, ac=1)   # 2 casas, LOS livre
    hp0 = m["hp"]
    await r.handle_throw_item("p1", "frasco_oleo", "m1")
    check("acerto causou dano", m["hp"] < hp0)
    check("alvo ficou em chamas", m.get("em_chamas_rodadas", 0) > 0)
    check("item consumido da bolsa", len(p["bag"]) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    # (4b) Fora de alcance → recusa, item NÃO consumido, ação livre
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [0, 0]; r.players["p1"] = p
    p["bag"] = [throwable("frasco_oleo")]
    m = make_monster(r, "m1", 8, 8, ac=1)   # >4 casas
    await r.handle_throw_item("p1", "frasco_oleo", "m1")
    check("fora de alcance: item mantido", len(p["bag"]) == 1)
    check("fora de alcance: ação NÃO gasta", not p.get("action_done"))
    check("fora de alcance: erro enviado", any("alcance" in e.lower() for e in r._errs))

    # (4c) Parede bloqueia LOS → recusa
    r = setup(); random.seed(2)
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [throwable("fogo_grego")]
    r.tiles[4][5] = WALL   # parede entre (4,4) e (4,6) na coluna? ver orientação abaixo
    r.tiles[5][4] = WALL   # bloqueia a coluna x=4 em y=5
    m = make_monster(r, "m1", 4, 6, ac=1)
    await r.handle_throw_item("p1", "fogo_grego", "m1")
    check("LOS bloqueada: item mantido", len(p["bag"]) == 1)
```

> Nota: `r.tiles[y][x]` (linha=y, coluna=x). O par de paredes garante bloqueio; se
> o `_tem_linha_de_visao` do projeto usar amostragem, a parede em `(4,5)` basta.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — `AttributeError: ... 'handle_throw_item'`

- [ ] **Step 3: Implementar `handle_throw_item`**

Logo após o método `_executar_arremesso` (por volta da linha 6540, antes de
`_calcular_ataque_lanca_arremesso`), adicione:

```python
    async def handle_throw_item(self, pid, item_id, target_id):
        """Arremessa um consumível de bolsa (ARREMESSAVEIS) num monstro-alvo.
        AÇÃO PRINCIPAL. Teste de ataque por DES vs CA (espelha _executar_arremesso).
        Consome o item em acerto E erro (o frasco se espatifa). Só o modo
        single-target ('ataque_alvo') é tratado aqui (Sub-projeto A)."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return

        item = next((i for i in p["bag"] if i["id"] == item_id), None)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item não encontrado na bolsa."}); return
        defn = ARREMESSAVEIS.get(item_id)
        if not defn or defn.get("alvo") != "ataque_alvo":
            await self.send_to(pid, {"type": "error", "msg": "Item não arremessável."}); return

        # Ação principal (cobre Velocidade/Oportunidade via _acao_bloqueada).
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

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

        # Rolagem por DESTREZA (1 natural = falha; 20 = crítico).
        dex_mod = mod(p.get("dex", 12))
        roll = random.randint(1, 20)
        total = roll + p["atk_bonus"]
        nat1 = (roll == 1); crit = (roll == 20)
        hit = (not nat1) and (crit or total >= target["ac"])
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                              "label": f"Arremesso ({defn['name']})", "hit": hit, "crit": crit})

        # Consome o item (espatifa) — em acerto ou erro.
        p["bag"].remove(item)
        # Marca a ação e cobra sobrevivência (mesma cadência de um ataque).
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
```

- [ ] **Step 4: Ligar o dispatch WS**

Encontre o bloco de dispatch onde `handle_throw` é roteado (linha ~15143:
`if room: await room.handle_throw(pid, msg.get("target_id"), msg.get("slot"))`).
Logo após esse `elif`/`if`, adicione um novo ramo espelhando os vizinhos
(confirme o nome da variável `mtype`/`msg["type"]` olhando as linhas ao redor):

```python
                elif mtype == "throw_item":
                    if room: await room.handle_throw_item(pid, msg.get("item_id"), msg.get("target_id"))
```

> Se o dispatch usar `msg.get("type")` direto num `if/elif`, siga o mesmo estilo
> local. O importante: mapear `type:"throw_item"` → `handle_throw_item(pid, item_id, target_id)`.

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seções [1]–[4] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): handle_throw_item (ataque DES, dano, em chamas)"
```

---

### Task 5: Apagar chamas bebendo Água (ação livre)

**Files:**
- Modify: `server.py` — ramo `food` em `handle_use_item` (linha 11502) e/ou pré-checagem no topo
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Adicionar o teste [5] (água apaga óleo, mas não Fogo Grego)**

```python
    # ── [5] Beber água apaga chamas (ação livre); Fogo Grego ignora ─────────────
    print("\n[5] Água apaga chamas")
    from server import _TAVERN_BY_ID  # garrafa_agua vive aqui
    def agua():
        return deepcopy(_TAVERN_BY_ID["garrafa_agua"])

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [agua()]
    r._aplicar_em_chamas(p, 3, True)   # óleo → água apaga
    await r.handle_use_item("p1", "garrafa_agua")
    check("óleo: água apagou as chamas", p.get("em_chamas_rodadas", 0) == 0)
    check("óleo: garrafa consumida", len(p["bag"]) == 0)
    check("óleo: ação NÃO gasta (livre)", not p.get("action_done"))

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    p["bag"] = [agua()]
    r._aplicar_em_chamas(p, 3, False)  # Fogo Grego → água NÃO apaga
    await r.handle_use_item("p1", "garrafa_agua")
    check("grego: chamas continuam", p.get("em_chamas_rodadas", 0) == 3)
    check("grego: garrafa NÃO consumida", len(p["bag"]) == 1)
    check("grego: erro explicativo", any("água" in e.lower() or "grego" in e.lower() for e in r._errs))
```

> Confirme o nome do dict de itens de taverna (`_TAVERN_BY_ID`) — foi visto em
> `server.py:12290`. Se for outro, ajuste o import.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — óleo não apaga (a água só mata sede hoje).

- [ ] **Step 3: Implementar a checagem de água no `handle_use_item`**

No `handle_use_item`, logo após a linha que resolve `effect, val = item["effect"], item.get("value", 0)` (linha 11435) e ANTES de qualquer consumo de ação, insira:

```python
        # ── Apagar "em chamas" bebendo água (ação LIVRE) ────────────────────────
        # Só água (effect food com sede>0) e só se as chamas forem apagáveis por
        # água (Óleo sim; Fogo Grego não). Não gasta ação; consome 1 água.
        if effect == "food" and item.get("sede", 0) > 0 and p.get("em_chamas_rodadas", 0) > 0:
            if not p.get("chamas_agua_apaga", True):
                await self.send_to(pid, {"type": "error",
                    "msg": "🟢 Estas chamas (Fogo Grego) não se apagam com água — gaste sua ação para apagá-las!"})
                return
            p["em_chamas_rodadas"] = 0
            p["bag"].remove(item)
            await self.gm_say(f"💧 **{p['name']}** joga **{item['name']}** sobre si e apaga as chamas!")
            await self.push_state()
            return
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seções [1]–[5] OK.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): beber agua apaga chamas (livre); Fogo Grego ignora"
```

---

### Task 6: Apagar chamas gastando a ação (`apagar_chamas`)

**Files:**
- Modify: `server.py` — novo `handle_apagar_chamas` (perto de `handle_throw_item`) + dispatch WS
- Test: `tools/test_arremessaveis.py`

- [ ] **Step 1: Adicionar o teste [6]**

```python
    # ── [6] Apagar batendo (gasta ação principal) — funciona p/ Fogo Grego ──────
    print("\n[6] handle_apagar_chamas")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    r._aplicar_em_chamas(p, 3, False)  # Fogo Grego
    await r.handle_apagar_chamas("p1")
    check("chamas apagadas", p.get("em_chamas_rodadas", 0) == 0)
    check("ação principal gasta", p.get("action_done") is True)

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; r.players["p1"] = p
    await r.handle_apagar_chamas("p1")   # não está em chamas
    check("sem chamas: erro", any("chama" in e.lower() for e in r._errs))
    check("sem chamas: ação NÃO gasta", not p.get("action_done"))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis.py`
Expected: FAIL — `AttributeError: ... 'handle_apagar_chamas'`

- [ ] **Step 3: Implementar `handle_apagar_chamas`**

Logo após `handle_throw_item`, adicione:

```python
    async def handle_apagar_chamas(self, pid):
        """Gasta a AÇÃO PRINCIPAL do turno para apagar o status 'em chamas'
        (única via que funciona contra o Fogo Grego)."""
        if not self._is_turn(pid): return
        p = self.players.get(pid)
        if not p or not p["alive"]: return
        if p.get("em_chamas_rodadas", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Você não está em chamas."}); return
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return
        p["em_chamas_rodadas"] = 0
        p["action_done"] = True
        self._consumir_recursos(p, 'apenas_acao')
        await self.gm_say(f"🔥 **{p['name']}** se joga no chão e apaga as chamas!")
        await self.push_state()
```

- [ ] **Step 4: Ligar o dispatch WS**

Junto ao ramo de `throw_item` (Task 4, Step 4), adicione:

```python
                elif mtype == "apagar_chamas":
                    if room: await room.handle_apagar_chamas(pid)
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis.py`
Expected: PASS — seções [1]–[6] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis.py
git commit -m "feat(arremessaveis): handle_apagar_chamas (gasta acao principal)"
```

---

### Task 7: Serializar `em_chamas_rodadas` no `game_state`

**Files:**
- Modify: `server.py` — serialização de jogadores e monstros no `game_state`
- Test: manual (o campo já vai cru na serialização de jogador; monstros precisam de checagem)

- [ ] **Step 1: Verificar a serialização de jogador**

Jogadores são serializados crus (o dicionário inteiro vai no `game_state`, como
`facing` no exemplo do CLAUDE.md), então `em_chamas_rodadas` já chega ao cliente.
Confirme lendo a função que monta `players[]` do `game_state` (procure por
`"players":` na montagem do estado). Se ela filtrar campos por allow-list,
adicione `"em_chamas_rodadas"` à lista. Se serializa cru, nenhuma mudança.

- [ ] **Step 2: Garantir `em_chamas_rodadas` na view de monstro**

Procure a função que serializa monstros para o cliente (ex.: `_serializar_monstros`
ou similar; procure por `"pos"` e `"hp"` na montagem de `monsters[]`). Adicione o
campo à saída:

```python
            "em_chamas_rodadas": m.get("em_chamas_rodadas", 0),
```

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat(arremessaveis): expoe em_chamas_rodadas no game_state (monstros)"
```

---

### Task 8: Cliente — estado, senders e resolução de clique (`gameState.js`)

**Files:**
- Modify: `src/gameState.js` — `CATALOGO_ITENS` (~linha 509), estado `pendingThrow` (~linha 32), senders (~linha 1097), ramo em `resolveTileClick` (~linha 1651), API pública (~linha 1711+)
- Test: manual (no jogo) — sem harness de cliente

- [ ] **Step 1: Adicionar `pendingThrow` ao estado de UI**

Perto de `let pendingSkill = null;` (linha 32), adicione:

```javascript
  let pendingThrow    = null;   // arremessável aguardando alvo no mapa: {id, alcance}
```

- [ ] **Step 2: Adicionar os itens ao `CATALOGO_ITENS`**

Abra `CATALOGO_ITENS` (linha 509) e adicione duas entradas seguindo o formato dos
vizinhos (confira as chaves de um item de bolsa existente, ex. `vela_escuridao`,
para casar `tipo`/`emoji`/`descricao`). Inclua os campos que o render/tooltip usam
(`alcance`) e uma flag `arremessavel`:

```javascript
    frasco_oleo: {
      id: 'frasco_oleo', nome: 'Frasco de Óleo Incendiário', emoji: '🔥',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4,
      descricao: 'Arremesse (4 quad., ataque por DES). 1d6 de fogo e o alvo pega ' +
                 'fogo (1/rodada por 1d4 rodadas). Apaga com Água ou gastando a ação.',
    },
    fogo_grego: {
      id: 'fogo_grego', nome: 'Fogo Grego', emoji: '🟢',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4,
      descricao: 'Arremesse (4 quad., ataque por DES). 2d6 de fogo e o alvo pega ' +
                 'fogo (1/rodada por 1d4 rodadas). Só a ação apaga — água não funciona.',
    },
```

- [ ] **Step 3: Adicionar os senders `throwItem` e `apagarChamas`**

Perto de `function useItem(id) { ... }` (linha 1097), adicione:

```javascript
  function throwItem(id, targetId) { send({ type: 'throw_item', item_id: id, target_id: targetId }); }
  function apagarChamas()          { send({ type: 'apagar_chamas' }); }
```

- [ ] **Step 4: Tratar `pendingThrow` em `resolveTileClick`**

No início de `resolveTileClick` (logo após o bloco `if (pendingSkill) { ... }`,
linha 1672), adicione um ramo paralelo:

```javascript
    // ── Pending-throw targeting (arremessável de bolsa) ──────────────────────
    if (pendingThrow) {
      const th = pendingThrow;
      const m = gameState.monsters.find(m => m.hp > 0 &&
        monsterTiles(m).some(([bx, by]) => bx === tx && by === ty));
      if (m) {
        const ddx = Math.abs(myP.pos[0] - tx);
        const ddy = Math.abs(myP.pos[1] - ty);
        if (Math.max(ddx, ddy) <= th.alcance &&
            hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty)) {
          return { type: 'throw', itemId: th.id, targetId: m.id };
        }
        return { type: 'throw_blocked' };   // fora de alcance / parede
      }
      return null; // consome o clique, permanece na mira (ESC cancela)
    }
```

- [ ] **Step 5: Expor `pendingThrow`, senders na API pública**

No bloco `return { ... }` da API pública (linha 1711+), junto de
`get pendingSkill()`/`set pendingSkill(v)` e de `useItem`, adicione:

```javascript
    get pendingThrow()   { return pendingThrow; },
    set pendingThrow(v)  { pendingThrow  = v; },
    throwItem,
    apagarChamas,
```

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js
git commit -m "feat(arremessaveis): estado pendingThrow, senders e resolveTileClick (cliente)"
```

---

### Task 9: Cliente — clique direito = usar/ativar (`inventoryModal.js`)

**Files:**
- Modify: `src/ui/inventoryModal.js` — handler de slot da bolsa (linha 253-286)
- Test: manual

- [ ] **Step 1: Mover "usar" para o clique direito e migrar throwables**

Em `_renderBag`, hoje o `slot.onclick` (linha 264-268) faz `castarPergaminho`/
`useItem`. Substitua esse bloco para: (a) o clique ESQUERDO só seleciona/move
(`_onBagSlotClick`), e (b) um listener de `contextmenu` (clique direito) faz o
"usar/ativar" — incluindo os arremessáveis, que entram no modo-alvo.

Troque o bloco `if(!_readOnly){ slot.onclick = () => { ... }; }` (linhas 263-269)
por:

```javascript
      const catDef = (typeof GS !== 'undefined' && GS.CATALOGO_ITENS)
        ? GS.CATALOGO_ITENS[item && item.id] : null;
      const isArremessavel = !!(catDef && catDef.arremessavel);
      const podeArremessar = isMyOwnDungeonTurn && isArremessavel && !player.action_done;
      if(item){
        if(podeArremessar) slot.classList.add('usable');
      }
      if(!_readOnly){
        // Esquerdo: só seleciona/move (arrastar continua abaixo).
        slot.onclick = () => { _onBagSlotClick(i); };
        // Direito: usar/ativar (regra única). preventDefault tira o menu do browser.
        slot.addEventListener('contextmenu', (e) => {
          e.preventDefault();
          if(!item) return;
          if(podeArremessar){ close(); _iniciarMiraArremesso(item, player); return; }
          if(podeConjurar){ close(); castarPergaminho(item); return; }
          if(podeUsar){ useItem(item.id); return; }
        });
      }
```

> `_iniciarMiraArremesso` é implementado na Task 10 (em game.js). Se `inventoryModal.js`
> não enxergar a função direto, exponha-a em `window._iniciarMiraArremesso` na Task 10
> e chame `window._iniciarMiraArremesso(item, player)` aqui.

- [ ] **Step 2: Verificação manual rápida**

Suba o jogo (`iniciar.bat`), entre numa masmorra com um `frasco_oleo` na bolsa.
- Clique ESQUERDO no item: deve só selecionar (não beber/arremessar).
- Clique DIREITO numa poção: deve beber (comportamento antigo do esquerdo).
Expected: usar migrou pro direito; nada quebrou no arrastar.

- [ ] **Step 3: Commit**

```bash
git add src/ui/inventoryModal.js
git commit -m "feat(arremessaveis): clique direito = usar/ativar; throwable entra na mira"
```

---

### Task 10: Cliente — mira (tiles vermelhos), 🔥 no peão e botão "Apagar chamas" (`game.js`)

**Files:**
- Modify: `game.js` — novo modo de mira espelhando `_modoArremesso*`, resolução de clique 2D/3D, indicador de chamas, botão de HUD
- Test: manual (visual)

> Este é o único trecho sem código completo: a maquinaria de highlight/3D é
> extensa e deve ser **espelhada** do arremesso de adaga já existente. Leia primeiro
> as funções abaixo e copie o padrão delas — NÃO reinvente.

- [ ] **Step 1: Ler o arremesso de adaga existente (referência)**

Leia em `game.js`: `_modoArremessoPrincipal`/`_modoArremessoAtivo` (linhas
~19246-19700), incluindo `onMouseMoveArremesso*`, o realce de alcance, e como o
clique 2D/3D resolve o alvo. Esse é o molde EXATO para o novo modo de item.

- [ ] **Step 2: Implementar `_iniciarMiraArremesso(item, player)`**

Adicione uma função que entra no modo-alvo do item. Espelhe o setup de
`_modoArremessoPrincipal` (que também é single-target com alcance e LOS), mas:
- guarda `window._modoThrowItem = { id: item.id, alcance: (GS.CATALOGO_ITENS[item.id].alcance) }`
- pinta o **alcance em tiles vermelhos** a partir da casa do jogador (reuse o mesmo
  helper de realce de alcance do arremesso de adaga — a cor vermelha já é a usada lá).
- registra ESC / clique fora para cancelar (`window._modoThrowItem = null` + re-render).
- exponha `window._iniciarMiraArremesso = _iniciarMiraArremesso;` para o modal chamar.

- [ ] **Step 3: Resolver o clique no alvo (2D e 3D)**

No handler unificado de clique de tile (o mesmo ponto onde `resolveTileClick` é
consumido — procure por `resolveTileClick(` e pelos hooks `_modoMagia`/
`_modoArremessoPrincipal` em `on3DClick`/clique 2D), adicione o tratamento do novo
modo ANTES do fluxo normal:

```javascript
  if (window._modoThrowItem) {
    const r = GS.resolveTileClick(tx, ty);   // pendingThrow deve estar setado (ver abaixo)
    if (r && r.type === 'throw') {
      GS.throwItem(r.itemId, r.targetId);
      window._modoThrowItem = null; GS.pendingThrow = null;
      // limpar realces e re-render
    } else if (r && r.type === 'throw_blocked') {
      toast('Fora de alcance ou parede no caminho.', 'var(--gold)');
    }
    return;
  }
```

Para `resolveTileClick` reconhecer o modo, `_iniciarMiraArremesso` deve também
setar `GS.pendingThrow = { id: item.id, alcance }` (o mesmo objeto). Assim a lógica
de alvo fica no `gameState.js` (Task 8) e o `game.js` só desenha/roteia.

- [ ] **Step 4: Indicador 🔥 no ente em chamas (2D e 3D)**

No desenho do peão/monstro, quando `entidade.em_chamas_rodadas > 0`, desenhe um 🔥
sobreposto. No 2D, procure onde nomes/ícones de status são desenhados sobre o peão
(ex.: perto de onde HP/efeitos aparecem) e some o emoji. No 3D, adicione um sprite
🔥 acima do peão (espelhe como outros indicadores de status flutuam sobre a figura).

- [ ] **Step 5: Botão "🔥 Apagar chamas" no HUD**

Em `renderMyPanel` (o painel agnóstico de classe — mesma função onde o CLAUDE.md
diz que o banner do Último Esforço vive), quando o meu jogador tem
`em_chamas_rodadas > 0` e é meu turno e a ação não foi usada, mostre um botão que
chama `GS.apagarChamas()`:

```javascript
  if (me.em_chamas_rodadas > 0 && GS.isMyTurn && !me.action_done) {
    // <button> "🔥 Apagar chamas (ação)" onclick=GS.apagarChamas()
  }
```

- [ ] **Step 6: Verificação manual completa (ver Task 11)**

- [ ] **Step 7: Commit**

```bash
git add game.js
git commit -m "feat(arremessaveis): mira de item (tiles vermelhos), 🔥 no peao, botao apagar chamas"
```

---

### Task 11: Verificação end-to-end e suíte completa

**Files:** nenhum (verificação)

- [ ] **Step 1: Rodar toda a suíte de testes do servidor**

Run: `python tools/test_arremessaveis.py`
Expected: `=== N OK / 0 FALHAS ===`

Rode também os testes vizinhos que tocam combate/uso de item para garantir que nada
regrediu:

Run: `python tools/test_ground_items.py`
Run: `python tools/test_roteamento_itens.py`
Expected: ambos passam.

- [ ] **Step 2: Verificação manual no jogo (`iniciar.bat`)**

Compre um Frasco de Óleo e um Fogo Grego na loja (SHOP_MERCHANT), entre numa
masmorra e confirme:
1. Clique direito no óleo → abre a mira com **tiles vermelhos** (alcance 4).
2. Clicar num monstro no alcance → dado de ataque, dano de fogo, monstro fica 🔥.
3. Passar a rodada → monstro perde 1 HP por rodada (popup de tick) até acabar.
4. Ficar em chamas (mande um monstro/friendly-fire ou teste com dois clientes) →
   botão "🔥 Apagar chamas" aparece; clicar gasta a ação e apaga.
5. Beber Água (clique direito) enquanto em chamas de **óleo** → apaga de graça.
6. Em chamas de **Fogo Grego** → beber água mostra erro; só o botão apaga.
7. Clicar fora do alcance / atrás de parede → toast de bloqueio, item não gasto.
8. ESC durante a mira → cancela sem gastar nada.

- [ ] **Step 3: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(arremessaveis): ajustes da verificacao end-to-end"
```

---

## Self-review (cobertura do spec)

- ✅ Interação clique direito universal → Task 9.
- ✅ Framework `ARREMESSAVEIS` + mensagem `throw_item` → Tasks 1, 4.
- ✅ Ação principal → Task 4 (`_acao_bloqueada` + `action_done`).
- ✅ Teste de ataque DES + alcance + LOS + consumo em acerto/erro → Task 4.
- ✅ Status "em chamas" (refresh=max) → Task 2.
- ✅ Tick 1/rodada no ponto da incendiária, herói+monstro, popup → Task 3.
- ✅ Apagar com água (livre, só se `chamas_agua_apaga`) → Task 5.
- ✅ Apagar com ação (`apagar_chamas`), Fogo Grego só por aqui → Task 6.
- ✅ Serialização p/ render → Task 7.
- ✅ Render: tiles vermelhos, 🔥 no peão, botão HUD → Task 10.
- ✅ Itens na loja com preço → Task 1.
- ✅ Testes → `tools/test_arremessaveis.py` (Tasks 1-6) + verificação manual (Task 11).

**Fora de escopo (confirmado):** área/tiles verdes/save de Reflexos (Sub-projeto B),
corrosão (C), controle cola/rede (D), veneno Agonia Sufocante (E), animação 3D
elaborada do projétil.
```
