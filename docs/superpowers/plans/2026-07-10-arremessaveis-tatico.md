# Arremessáveis Táticos (Sub-projeto D) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar dois arremessáveis táticos de controle — Cola Alquímica (reduz o movimento do monstro à metade por 2 rodadas se falhar num Reflexos) e Rede (prende o monstro até ele gastar o turno passando num Fortitude para escapar).

**Architecture:** Reusa o caminho single-target `_throw_item_alvo` do Sub-projeto A, tornando o dano **opcional** (itens de controle não causam dano) e plugando um campo declarativo `controle`. O status `mov_reduzido` corta `m["movement"]` na aplicação e o restaura na expiração (ticado em `_status_monstro_turno`), sem tocar nos ~20 sites que leem `m["movement"]`. O status `enredado` é resolvido num helper `_processar_enredado_turno` chamado no loop de turno do monstro (espelha `_processar_paralisacao_turno`).

**Tech Stack:** Python 3 + `websockets` (server.py); Vanilla JS (src/gameState.js — só catálogo); testes com o harness caseiro de `tools/test_*.py`.

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | 2 itens em `ARREMESSAVEIS`/`SHOP_MERCHANT`; `_aplicar_controle_arremesso`; tick de `mov_reduzido` em `_status_monstro_turno`; `_processar_enredado_turno` + chamada no loop de turno; dano opcional + dispatch de `controle` em `_throw_item_alvo` |
| `src/gameState.js` | Modificar | 2 entradas em `CATALOGO_ITENS` (reusa a mira single-target de A) |
| `tools/test_arremessaveis_tatico.py` | Criar | Testes (cola/mov_reduzido/expiração/rede/enredado/escape/erro) |

---

### Task 1: Dois itens táticos no catálogo + loja

**Files:**
- Modify: `server.py` — dict `ARREMESSAVEIS` (após `vidro_acido_grande`) e `SHOP_MERCHANT` (após os itens de ácido)
- Test: `tools/test_arremessaveis_tatico.py`

- [ ] **Step 1: Criar o arquivo de teste com harness + teste [1]**

Crie `tools/test_arremessaveis_tatico.py`:

```python
"""Testes dos arremessáveis TÁTICOS (Sub-projeto D: Cola e Rede).
Roda da raiz: python tools/test_arremessaveis_tatico.py"""
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

def make_monster(r, mid, x, y, hp=40, ac=1, movement=6):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True, "movement": movement}
    r.monsters[mid] = m
    return m

# Save determinístico: substitui _save_mostrado por um que sempre passa/falha.
def _mk_save(passou):
    async def _s(alvo, tipo, cd, *a, **k):
        return (passou, 1, 0, 1)   # (passou, d20, bonus, total)
    return _s

# d20 fixo no arremesso; dados de dano usam o RNG real.
_REAL_RANDINT = random.randint
def _fixed_d20(value):
    def fake(a, b):
        return value if (a, b) == (1, 20) else _REAL_RANDINT(a, b)
    return fake

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo tático + loja")
    for iid in ("cola_alquimica", "rede_arremesso"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=ataque_alvo", ARREMESSAVEIS.get(iid, {}).get("alvo") == "ataque_alvo")
        check(f"{iid} sem dano", "dano" not in ARREMESSAVEIS.get(iid, {}))
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    cola = ARREMESSAVEIS["cola_alquimica"]["controle"]
    check("cola: mov_reduzido", cola["tipo"] == "mov_reduzido")
    check("cola: resist Reflexos CD12", cola["resist_save"] == {"tipo": "reflexos", "cd": 12})
    check("cola: duracao 2", cola["duracao"] == 2)
    rede = ARREMESSAVEIS["rede_arremesso"]["controle"]
    check("rede: enredado", rede["tipo"] == "enredado")
    check("rede: escape Fortitude CD12", rede["escape_save"] == {"tipo": "fortitude", "cd": 12})

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: FAIL — `KeyError: 'cola_alquimica'`.

- [ ] **Step 3: Adicionar as 2 entradas no `ARREMESSAVEIS`**

Dentro do dict `ARREMESSAVEIS`, após a entrada `"vidro_acido_grande": {…},` e antes
do `}` que fecha o dict, adicione:

```python
    "cola_alquimica": {
        "id": "cola_alquimica", "name": "Cola Alquímica", "emoji": "🟢",
        "alcance": 4, "alvo": "ataque_alvo",
        "controle": {"tipo": "mov_reduzido",
                     "resist_save": {"tipo": "reflexos", "cd": 12}, "duracao": 2},
    },
    "rede_arremesso": {
        "id": "rede_arremesso", "name": "Rede", "emoji": "🕸️",
        "alcance": 4, "alvo": "ataque_alvo",
        "controle": {"tipo": "enredado",
                     "escape_save": {"tipo": "fortitude", "cd": 12}},
    },
```

- [ ] **Step 4: Adicionar os 2 itens em `SHOP_MERCHANT`**

Logo após os itens de ácido em `SHOP_MERCHANT`, adicione:

```python
    {"id": "cola_alquimica", "name": "Cola Alquímica", "emoji": "🟢", "price": 15, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "rede_arremesso", "name": "Rede",          "emoji": "🕸️", "price": 18, "item_slot": "bag", "effect": "throwable", "value": 0},
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: PASS — seção [1] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_tatico.py
git commit -m "feat(arremessaveis): 2 itens taticos (cola/rede) no catalogo + loja"
```

---

### Task 2: Helper `_aplicar_controle_arremesso`

**Files:**
- Modify: `server.py` — novo método (perto de `_acido_corroer`)
- Test: `tools/test_arremessaveis_tatico.py`

- [ ] **Step 1: Adicionar o teste [2]**

Antes do `print(f"\n=== ...")` final:

```python
    # ── [2] _aplicar_controle_arremesso ────────────────────────────────────────
    print("\n[2] _aplicar_controle_arremesso")
    cola_ctrl = ARREMESSAVEIS["cola_alquimica"]["controle"]
    rede_ctrl = ARREMESSAVEIS["rede_arremesso"]["controle"]

    # cola: falha no Reflexos → corta movimento à metade
    r = setup(); r._save_mostrado = _mk_save(False)
    m = make_monster(r, "m1", 4, 4, movement=6)
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola: movement 6→3", m["movement"] == 3)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    check("cola: guardou original 6", m.get("mov_reduzido_orig") == 6)

    # cola: sucesso no Reflexos → sem efeito
    r._save_mostrado = _mk_save(True)
    m2 = make_monster(r, "m2", 5, 5, movement=6)
    await r._aplicar_controle_arremesso(m2, cola_ctrl)
    check("cola resist: movement intacto", m2["movement"] == 6 and not m2.get("mov_reduzido_rodadas"))

    # cola: reaplicar renova duração sem cortar de novo
    r._save_mostrado = _mk_save(False)
    m["mov_reduzido_rodadas"] = 1
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola reaplicar: movement fica 3 (não corta de novo)", m["movement"] == 3)
    check("cola reaplicar: renova p/ 2", m["mov_reduzido_rodadas"] == 2)

    # rede: marca enredado + guarda o save de escape
    r = setup()
    m3 = make_monster(r, "m3", 6, 6)
    await r._aplicar_controle_arremesso(m3, rede_ctrl)
    check("rede: enredado", m3.get("enredado") is True)
    check("rede: enredado_save fortitude", m3.get("enredado_save") == "fortitude")
    check("rede: enredado_cd 12", m3.get("enredado_cd") == 12)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: FAIL — `AttributeError: ... '_aplicar_controle_arremesso'`.

- [ ] **Step 3: Implementar `_aplicar_controle_arremesso`**

Logo após o método `_acido_corroer` (server.py), adicione:

```python
    async def _aplicar_controle_arremesso(self, alvo, ctrl):
        """Aplica o efeito de controle de um arremessável tático a um monstro.
        `ctrl` vem do campo `controle` do catálogo ARREMESSAVEIS."""
        nome = alvo.get("name") or alvo.get("nome", "alvo")
        tipo = ctrl.get("tipo")
        if tipo == "mov_reduzido":
            rs = ctrl.get("resist_save")
            if rs:
                ok, *_ = await self._save_mostrado(alvo, rs["tipo"], rs["cd"])
                if ok:
                    await self.gm_say(f"🟢 **{nome}** se esquiva da cola — sem efeito!")
                    return
            dur = ctrl.get("duracao", 2)
            if not alvo.get("mov_reduzido_rodadas"):     # 1ª aplicação: corta pela metade
                alvo["mov_reduzido_orig"] = alvo.get("movement", 5)
                alvo["movement"] = max(1, alvo["mov_reduzido_orig"] // 2)
            alvo["mov_reduzido_rodadas"] = max(alvo.get("mov_reduzido_rodadas", 0), dur)
            await self.gm_say(
                f"🟢 **{nome}** fica preso na cola — movimento reduzido à metade "
                f"por {alvo['mov_reduzido_rodadas']} rodada(s)!")
        elif tipo == "enredado":
            es = ctrl.get("escape_save", {"tipo": "fortitude", "cd": 12})
            alvo["enredado"]      = True
            alvo["enredado_save"] = es["tipo"]
            alvo["enredado_cd"]   = es["cd"]
            await self.gm_say(
                f"🕸️ **{nome}** fica preso na rede! (escapar: {es['tipo']} CD {es['cd']})")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: PASS — seções [1]-[2] OK.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_arremessaveis_tatico.py
git commit -m "feat(arremessaveis): _aplicar_controle_arremesso (cola/rede)"
```

---

### Task 3: Tick/expiração de `mov_reduzido` em `_status_monstro_turno`

**Files:**
- Modify: `server.py` — `_status_monstro_turno` (antes do `return None` final, ~server.py:9610)
- Test: `tools/test_arremessaveis_tatico.py`

- [ ] **Step 1: Adicionar o teste [3]**

```python
    # ── [3] mov_reduzido tica e expira (restaura movement) ─────────────────────
    print("\n[3] tick de mov_reduzido em _status_monstro_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4, movement=6)
    m["movement"] = 3; m["mov_reduzido_orig"] = 6; m["mov_reduzido_rodadas"] = 2
    res = await r._status_monstro_turno(m, [m])
    check("mov_reduzido não pula o turno", res != "pulou")
    check("tica p/ 1", m["mov_reduzido_rodadas"] == 1)
    check("ainda reduzido (3)", m["movement"] == 3)
    await r._status_monstro_turno(m, [m])
    check("expira: movement restaurado p/ 6", m["movement"] == 6)
    check("flag e backup limpos", m.get("mov_reduzido_rodadas", 0) == 0 and "mov_reduzido_orig" not in m)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: FAIL — o `movement` não é restaurado (o tick ainda não existe).

- [ ] **Step 3: Adicionar o bloco de tick no `_status_monstro_turno`**

Em `_status_monstro_turno`, logo antes do `return None` final (server.py:~9610),
adicione:

```python
        # Movimento reduzido (Cola Alquímica): NÃO pula o turno — só reduz o passo.
        if m.get("mov_reduzido_rodadas", 0) > 0:
            m["mov_reduzido_rodadas"] -= 1
            if m["mov_reduzido_rodadas"] <= 0 and "mov_reduzido_orig" in m:
                m["movement"] = m.pop("mov_reduzido_orig")
                await self.gm_say(f"🟢 A cola em **{m['name']}** seca — movimento normal.")
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: PASS — seções [1]-[3] OK.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_arremessaveis_tatico.py
git commit -m "feat(arremessaveis): mov_reduzido tica e restaura movement na expiracao"
```

---

### Task 4: `_processar_enredado_turno` (escape da Rede)

**Files:**
- Modify: `server.py` — novo helper (perto de `_processar_paralisacao_turno`) + chamada no loop de turno do monstro (~server.py:14473, logo após o bloco `perde_turno`)
- Test: `tools/test_arremessaveis_tatico.py`

- [ ] **Step 1: Adicionar o teste [4]**

```python
    # ── [4] _processar_enredado_turno (escape) ─────────────────────────────────
    print("\n[4] _processar_enredado_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4)
    m["enredado"] = True; m["enredado_save"] = "fortitude"; m["enredado_cd"] = 12

    r._save_mostrado = _mk_save(False)   # falha → continua preso, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("falha: turno consumido", consumiu is True)
    check("falha: continua preso", m.get("enredado") is True)

    r._save_mostrado = _mk_save(True)    # sucesso → solta, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("sucesso: turno consumido", consumiu is True)
    check("sucesso: soltou", not m.get("enredado"))
    check("sucesso: limpou save/cd", "enredado_cd" not in m and "enredado_save" not in m)

    m2 = make_monster(r, "m2", 5, 5)     # não enredado → não consome
    check("não enredado → False", (await r._processar_enredado_turno(m2)) is False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: FAIL — `AttributeError: ... '_processar_enredado_turno'`.

- [ ] **Step 3: Implementar `_processar_enredado_turno`**

Logo após `_processar_paralisacao_turno` (server.py), adicione:

```python
    async def _processar_enredado_turno(self, m):
        """Rede (item): monstro preso GASTA o turno tentando escapar (save de
        escape configurado no monstro). Retorna True se o turno foi consumido
        (preso ou escapou nesta rodada); False se não está enredado."""
        if not m.get("enredado"):
            return False
        passou, *_ = await self._save_mostrado(
            m, m.get("enredado_save", "fortitude"), m.get("enredado_cd", 12))
        if passou:
            m["enredado"] = False
            m.pop("enredado_save", None); m.pop("enredado_cd", None)
            await self.gm_say(f"🕸️ **{m['name']}** se solta da rede!")
        else:
            await self.gm_say(f"🕸️ **{m['name']}** continua preso na rede e perde o turno!")
        return True
```

- [ ] **Step 4: Ligar a chamada no loop de turno do monstro**

No loop de turno do monstro, logo após o bloco `perde_turno` (server.py:~14470-14473,
o `if m.get("perde_turno"): … continue`) e ANTES da chamada de
`_status_monstro_turno`, adicione:

```python
            # Enredado (Rede): gasta o turno tentando escapar.
            if await self._processar_enredado_turno(m):
                continue
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: PASS — seções [1]-[4] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_tatico.py
git commit -m "feat(arremessaveis): _processar_enredado_turno (escape da rede no turno)"
```

---

### Task 5: Dano opcional + dispatch de `controle` em `_throw_item_alvo`

**Files:**
- Modify: `server.py` — ramo `if hit:` de `_throw_item_alvo` (server.py:6613-6635)
- Test: `tools/test_arremessaveis_tatico.py`

- [ ] **Step 1: Adicionar os testes [5]-[6]**

```python
    # ── [5] Arremesso da Cola e da Rede (acerto) ───────────────────────────────
    print("\n[5] handle_throw_item (cola/rede) — acerto")
    S.random.randint = _fixed_d20(15)   # acerto não-crítico, não-nat1

    r = setup(); r._save_mostrado = _mk_save(False)   # falha no Reflexos → cola pega
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=1, movement=6)
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("cola: movement reduzido (6→3)", m["movement"] == 3)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    check("cola: item consumido", len(p["bag"]) == 0)
    check("cola: sem dano (hp intacto)", m["hp"] == 40)

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("rede_arremesso")]
    m = make_monster(r, "m1", 4, 6, ac=1)
    await r.handle_throw_item("p1", {"item_id": "rede_arremesso", "target_id": "m1"})
    check("rede: enredado", m.get("enredado") is True)
    check("rede: item consumido", len(p["bag"]) == 0)

    # ── [6] Erro: item consumido, sem efeito ───────────────────────────────────
    print("\n[6] handle_throw_item (tático) — erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=99, movement=6)   # 15+5 < 99 → erro
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("erro: movement intacto", m["movement"] == 6)
    check("erro: sem mov_reduzido", not m.get("mov_reduzido_rodadas"))
    check("erro: item consumido", len(p["bag"]) == 0)
    S.random.randint = _REAL_RANDINT
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: FAIL — `KeyError: 'dano'` (o ramo de acerto ainda exige `defn["dano"]`,
que os itens táticos não têm).

- [ ] **Step 3: Tornar o dano opcional e despachar o controle**

Em `_throw_item_alvo`, substitua o bloco do ramo `if hit:` que hoje começa em
`raw = roll_dice(defn["dano"])` e vai até a chamada `await self._aplicar_dano_alvo(...)`
(server.py:6614-6624) por:

```python
            if defn.get("dano"):
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
                await self._aplicar_dano_alvo(target, dmg, defn["elemento"], pid)
            else:
                await self.gm_say(
                    f"{defn['emoji']} **{p['name']}** acerta **{defn['name']}** em "
                    f"**{target['name']}** (d20={roll}+{p['atk_bonus']}={total} vs CA {target['ac']})!")
```

(Os blocos seguintes de `em_chamas`/`residual`/`corrosao_ac` ficam iguais — eles já
são guardados por `defn.get(...)` e só rodam para itens com dano.) Logo após o bloco
`corrosao_ac` (server.py:6634-6635), ainda dentro do `if hit:`, adicione:

```python
            ctrl = defn.get("controle")
            if ctrl and target.get("hp", 0) > 0:
                await self._aplicar_controle_arremesso(target, ctrl)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_tatico.py`
Expected: PASS — seções [1]-[6] OK.

- [ ] **Step 5: Rodar as regressões (o dano opcional não pode quebrar A/B/C)**

Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_arremessaveis_area.py`
Run: `python tools/test_arremessaveis_acido.py`
Run: `python tools/test_ground_items.py`
Expected: todos passam (`46/0`, `41/0`, `32/0`, `23/0`).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_tatico.py
git commit -m "feat(arremessaveis): dano opcional + dispatch de controle em _throw_item_alvo"
```

---

### Task 6: Cliente — entradas de catálogo

**Files:**
- Modify: `src/gameState.js` — `CATALOGO_ITENS`
- Test: manual

- [ ] **Step 1: Adicionar as 2 entradas no `CATALOGO_ITENS`**

Junto das entradas de arremessáveis já existentes (A/B/C), adicione (mira
single-target, com `permitidoPara:['todos']`):

```javascript
    cola_alquimica: {
      id: 'cola_alquimica', nome: 'Cola Alquímica', emoji: '🟢',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). O alvo testa Reflexos CD 12; ' +
                 'se falhar, fica com o movimento reduzido à metade por 2 rodadas.',
    },
    rede_arremesso: {
      id: 'rede_arremesso', nome: 'Rede', emoji: '🕸️',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). O alvo fica preso; para ' +
                 'escapar gasta o turno num teste de Fortitude CD 12.',
    },
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(arremessaveis): cliente — entradas de catalogo cola/rede"
```

---

### Task 7: Verificação end-to-end

**Files:** nenhum

- [ ] **Step 1: Suíte completa do servidor**

Run: `python tools/test_arremessaveis_tatico.py`
Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_arremessaveis_area.py`
Run: `python tools/test_arremessaveis_acido.py`
Run: `python tools/test_ground_items.py`
Expected: todos `0 FALHAS` / `0 XX`.

- [ ] **Step 2: Syntax check do cliente**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Verificação manual (`iniciar.bat`)**

Compre uma Cola Alquímica e uma Rede e, numa masmorra:
1. Clique direito na Cola → mira **vermelha single-target**
2. Acertar um monstro (que falhe o Reflexos) → ele passa a se aproximar **mais devagar** (metade dos passos) por 2 rodadas, mas ainda ataca; depois volta ao normal
3. Acertar com a Rede → o monstro fica **preso**; no turno dele, gasta a ação tentando escapar (Fortitude CD 12); enquanto preso não anda nem ataca; ao passar, se solta
4. Passar o mouse sobre os itens na bolsa → tooltip sem erro
5. Errar (alvo com CA alta) → item gasto, sem efeito; fora do alcance → toast; ESC cancela
6. A/B/C (óleo, bombas, ácido) seguem funcionando

- [ ] **Step 4: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(arremessaveis): ajustes da verificacao tatica"
```

---

## Self-review (cobertura do spec)

- ✅ 2 itens no catálogo/loja (`controle`, sem `dano`) → Task 1.
- ✅ Cola → `mov_reduzido`: resist Reflexos, corta `movement` à metade, renova sem empilhar → Task 2.
- ✅ `mov_reduzido` tica e restaura o `movement` na expiração → Task 3.
- ✅ Rede → `enredado`: escape por Fortitude gastando o turno → Tasks 2, 4.
- ✅ Dano opcional em `_throw_item_alvo` + dispatch de `controle` (sem quebrar A/B/C) → Task 5.
- ✅ Força→Fortitude (save de escape configurável no catálogo/monstro) → Tasks 1, 2, 4.
- ✅ Cliente reusa a mira single-target de A (só catálogo, com `permitidoPara`) → Task 6.
- ✅ Testes + regressões A/B/C → Tasks 1-5, 7.

**Fora de escopo (confirmado):** veneno Agonia Sufocante (Sub-projeto E), indicador
visual do status sobre o monstro, efeito em jogadores, save de Força cru.
```
