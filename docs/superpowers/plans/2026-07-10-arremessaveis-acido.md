# Arremessáveis de Ácido (Sub-projeto C) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar dois itens arremessáveis de ácido — Frasco de Ácido e Vidro de Ácido Grande — que causam dano single-target, dano residual (metade na rodada seguinte) e corroem a CA do monstro-alvo.

**Architecture:** Reusa o caminho single-target `_throw_item_alvo` do Sub-projeto A (teste de ataque por DES), plugando dois efeitos declarativos por campo do catálogo: `residual` (dano meio na rodada seguinte, ticado num método irmão do "em chamas") e `corrosao_ac` (redução de CA do monstro via um helper único `_acido_corroer`, com piso de CA e um ponto de extensão dormant para equipamento de monstro futuro).

**Tech Stack:** Python 3 + `websockets` (server.py); Vanilla JS (src/gameState.js — só duas entradas de catálogo, sem UI nova); testes com o harness caseiro de `tools/test_*.py`.

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | 2 itens em `ARREMESSAVEIS`/`SHOP_MERCHANT`; constante `_ACIDO_AC_MIN`; helper `_acido_corroer`; `_processar_acido_residual_turno` + chamada no fim de rodada; efeitos de ácido no ramo de acerto de `_throw_item_alvo` |
| `src/gameState.js` | Modificar | 2 entradas em `CATALOGO_ITENS` (reusa a mira vermelha single-target de A — sem UI nova) |
| `tools/test_arremessaveis_acido.py` | Criar | Testes (dano/residual/corrosão de CA/piso/erro) |

> **Arquitetura:** todo cálculo fica no servidor; o cliente só ganha as entradas de catálogo (a mira single-target já existe do Sub-projeto A). Não há mudança em `game.js`.

---

### Task 1: Dois itens de ácido no catálogo + loja

**Files:**
- Modify: `server.py` — dict `ARREMESSAVEIS` (após a última entrada de B, `bomba_fumaca`) e `SHOP_MERCHANT` (após os itens de B)
- Test: `tools/test_arremessaveis_acido.py`

- [ ] **Step 1: Criar o arquivo de teste com harness + teste [1]**

Crie `tools/test_arremessaveis_acido.py`:

```python
"""Testes dos arremessáveis de ÁCIDO (Sub-projeto C).
Roda da raiz: python tools/test_arremessaveis_acido.py"""
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

def make_monster(r, mid, x, y, hp=40, ac=1):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True}
    r.monsters[mid] = m
    return m

# Força o d20 do arremesso a um valor fixo (para acerto/erro determinístico),
# deixando os dados de DANO (roll_dice) usarem o RNG real.
_REAL_RANDINT = random.randint
def _fixed_d20(value):
    def fake(a, b):
        return value if (a, b) == (1, 20) else _REAL_RANDINT(a, b)
    return fake

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo de ácido + loja")
    for iid in ("frasco_acido", "vidro_acido_grande"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=ataque_alvo", ARREMESSAVEIS.get(iid, {}).get("alvo") == "ataque_alvo")
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    check("frasco: 1d6", ARREMESSAVEIS["frasco_acido"]["dano"] == "1d6")
    check("frasco: residual", ARREMESSAVEIS["frasco_acido"]["residual"] is True)
    check("frasco: corrosao 1", ARREMESSAVEIS["frasco_acido"]["corrosao_ac"] == 1)
    check("grande: 2d6", ARREMESSAVEIS["vidro_acido_grande"]["dano"] == "2d6")
    check("grande: corrosao 2", ARREMESSAVEIS["vidro_acido_grande"]["corrosao_ac"] == 2)
    check("elemento acido", ARREMESSAVEIS["frasco_acido"]["elemento"] == "acido")

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: FAIL — `KeyError: 'frasco_acido'`.

- [ ] **Step 3: Adicionar as 2 entradas no `ARREMESSAVEIS`**

Dentro do dict `ARREMESSAVEIS`, após a entrada `"bomba_fumaca": {…},` e antes do
`}` que fecha o dict, adicione:

```python
    "frasco_acido": {
        "id": "frasco_acido", "name": "Frasco de Ácido", "emoji": "🧪",
        "alcance": 4, "alvo": "ataque_alvo", "dano": "1d6", "elemento": "acido",
        "residual": True, "corrosao_ac": 1,
    },
    "vidro_acido_grande": {
        "id": "vidro_acido_grande", "name": "Vidro de Ácido Grande", "emoji": "🫙",
        "alcance": 4, "alvo": "ataque_alvo", "dano": "2d6", "elemento": "acido",
        "residual": True, "corrosao_ac": 2,
    },
```

- [ ] **Step 4: Adicionar os 2 itens em `SHOP_MERCHANT`**

Logo após os itens de área (Sub-projeto B) em `SHOP_MERCHANT`, adicione:

```python
    {"id": "frasco_acido",       "name": "Frasco de Ácido",       "emoji": "🧪", "price": 20, "item_slot": "bag", "effect": "throwable", "value": 0},
    {"id": "vidro_acido_grande", "name": "Vidro de Ácido Grande", "emoji": "🫙", "price": 50, "item_slot": "bag", "effect": "throwable", "value": 0},
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: PASS — seção [1] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_acido.py
git commit -m "feat(arremessaveis): 2 itens de acido no catalogo + loja"
```

---

### Task 2: Helper `_acido_corroer` (corrosão de CA)

**Files:**
- Modify: `server.py` — constante `_ACIDO_AC_MIN` (perto do dict `ARREMESSAVEIS`) + método `_acido_corroer` (perto de `_corroer_equipamento`, ~linha 12264)
- Test: `tools/test_arremessaveis_acido.py`

- [ ] **Step 1: Adicionar o teste [2] (redução de CA, piso, cumulativo)**

Antes do `print(f"\n=== ...")` final:

```python
    # ── [2] _acido_corroer: reduz CA, cumulativo, com piso ─────────────────────
    print("\n[2] _acido_corroer")
    r = setup()
    m = make_monster(r, "m1", 4, 4, ac=15)
    await r._acido_corroer(m, 1)
    check("CA cai 1 (15→14)", m["ac"] == 14)
    check("ac_corroida acumula", m.get("ac_corroida") == 1)
    await r._acido_corroer(m, 2)
    check("CA cai +2 (14→12)", m["ac"] == 12)
    check("ac_corroida total 3", m.get("ac_corroida") == 3)
    # piso 5: uma CA baixa não desce abaixo de 5
    m2 = make_monster(r, "m2", 5, 5, ac=6)
    await r._acido_corroer(m2, 2)
    check("piso: CA 6 → 5 (não 4)", m2["ac"] == 5)
    await r._acido_corroer(m2, 2)
    check("piso: já em 5, permanece 5", m2["ac"] == 5)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: FAIL — `AttributeError: ... '_acido_corroer'`.

- [ ] **Step 3: Adicionar a constante `_ACIDO_AC_MIN`**

Logo após o fechamento do dict `ARREMESSAVEIS` (antes ou depois, no mesmo bloco de
constantes de módulo), adicione:

```python
_ACIDO_AC_MIN = 5    # piso da CA corroída por ácido (não vira acerto automático)
```

- [ ] **Step 4: Implementar `_acido_corroer`**

Logo antes do método `_corroer_equipamento` (server.py:~12264), adicione:

```python
    async def _acido_corroer(self, alvo, pontos):
        """Corrói a defesa do alvo. Ramo ATIVO: reduz a CA do monstro (piso
        _ACIDO_AC_MIN). PONTO DE EXTENSÃO (dormant): quando monstros tiverem
        equipamento corroível (`alvo['equipamento_corroivel']`), é aqui que se
        pluga a corrosão estilo-herói (ver _corroer_equipamento) — nenhum monstro
        tem esse campo hoje."""
        base = alvo.get("ac", 10)
        novo = max(_ACIDO_AC_MIN, base - pontos)
        nome = alvo.get("name") or alvo.get("nome", "alvo")
        if novo < base:
            alvo["ac"] = novo
            alvo["ac_corroida"] = alvo.get("ac_corroida", 0) + (base - novo)
            await self.gm_say(f"🧪 O ácido corrói a defesa de **{nome}**: CA {base} → {novo}!")
        else:
            await self.gm_say(f"🧪 A defesa de **{nome}** já está corroída ao máximo (CA {base}).")
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: PASS — seções [1]-[2] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_acido.py
git commit -m "feat(arremessaveis): _acido_corroer (reduz CA do monstro, piso 5)"
```

---

### Task 3: Tick do dano residual

**Files:**
- Modify: `server.py` — `_processar_acido_residual_turno` (após `_processar_em_chamas_turno`, ~linha 11648) + chamada no `handle_end_turn` (após a linha 12103)
- Test: `tools/test_arremessaveis_acido.py`

- [ ] **Step 1: Adicionar o teste [3] (tick residual aplica metade e limpa)**

```python
    # ── [3] _processar_acido_residual_turno: aplica metade e limpa ─────────────
    print("\n[3] tick residual")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["acido_residual"] = 3
    await r._processar_acido_residual_turno()
    check("residual aplicou 3 de dano", m["hp"] == 37)
    check("residual limpo após o tick", m.get("acido_residual", 0) == 0)
    await r._processar_acido_residual_turno()
    check("sem residual → sem dano extra", m["hp"] == 37)
    # não tica em alvo morto
    m2 = make_monster(r, "m2", 5, 5, hp=0); m2["alive"] = False
    m2["acido_residual"] = 5
    await r._processar_acido_residual_turno()
    check("alvo morto: residual limpo sem dano", m2.get("acido_residual", 0) == 0 and m2["hp"] == 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: FAIL — `AttributeError: ... '_processar_acido_residual_turno'`.

- [ ] **Step 3: Implementar `_processar_acido_residual_turno`**

Logo após `_processar_em_chamas_turno` (server.py:~11648, antes de
`_serializar_armadilhas`), adicione:

```python
    async def _processar_acido_residual_turno(self):
        """Aplica o dano residual do ácido (metade do inicial) UMA vez, na rodada
        seguinte ao acerto, e limpa. Varre jogadores + monstros + prisioneiro."""
        entes = list(self.players.values()) + list(self.monsters.values())
        if self.prisoner is not None:
            entes.append(self.prisoner)
        for alvo in entes:
            d = alvo.get("acido_residual", 0)
            if d <= 0:
                continue
            alvo["acido_residual"] = 0
            if not (alvo.get("alive") or alvo.get("hp", 0) > 0):
                continue
            nome = alvo.get("name") or alvo.get("nome", "alvo")
            await self.gm_say(f"🧪 O ácido continua corroendo **{nome}**: **{d}** de dano!")
            await self._dano_em_alvo(alvo, d, "acido", None)
```

- [ ] **Step 4: Ligar a chamada no fim da rodada**

No `handle_end_turn`, logo após a linha 12103
(`await self._processar_em_chamas_turno()`), adicione:

```python
            await self._processar_acido_residual_turno()       # tick do dano residual de ácido
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: PASS — seções [1]-[3] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_acido.py
git commit -m "feat(arremessaveis): tick do dano residual de acido por rodada"
```

---

### Task 4: Efeitos de ácido no acerto de `_throw_item_alvo`

**Files:**
- Modify: `server.py` — ramo `if hit:` de `_throw_item_alvo`, logo após o bloco `em_chamas` (server.py:~6614)
- Test: `tools/test_arremessaveis_acido.py`

- [ ] **Step 1: Adicionar os testes [4]-[5] (acerto aplica residual + corrosão; erro não)**

```python
    # ── [4] Acerto: dano + residual guardado + CA corroída ─────────────────────
    # d20 fixo em 15 (acerto não-crítico, não-nat1); atk_bonus alto garante o acerto.
    # CAs acima do piso 5 para que a corrosão registre.
    print("\n[4] handle_throw_item (ácido) — acerto")
    S.random.randint = _fixed_d20(15)
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("frasco_acido")]
    m = make_monster(r, "m1", 4, 6, hp=40, ac=15)   # 15+5 ≥ 15 → acerto
    await r.handle_throw_item("p1", {"item_id": "frasco_acido", "target_id": "m1"})
    check("dano de ácido aplicado", m["hp"] < 40)
    dano_inicial = 40 - m["hp"]
    check("residual guardado = dano//2", m.get("acido_residual", 0) == dano_inicial // 2)
    check("CA corroída -1 (15→14)", m["ac"] == 14)
    check("item consumido", len(p["bag"]) == 0)

    # Vidro Grande: -2 CA (15→13)
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("vidro_acido_grande")]
    m = make_monster(r, "m1", 4, 6, hp=60, ac=15)
    await r.handle_throw_item("p1", {"item_id": "vidro_acido_grande", "target_id": "m1"})
    check("Vidro Grande corrói -2 CA (15→13)", m["ac"] == 13)

    # ── [5] Erro: sem dano/residual/corrosão, item consumido ───────────────────
    # d20 fixo em 15, mas CA 99 → 15+5 < 99 → erro determinístico.
    print("\n[5] handle_throw_item (ácido) — erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["dex"] = 14
    p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("frasco_acido")]
    m = make_monster(r, "m1", 4, 6, hp=40, ac=99)
    await r.handle_throw_item("p1", {"item_id": "frasco_acido", "target_id": "m1"})
    check("erro: sem dano", m["hp"] == 40)
    check("erro: sem residual", m.get("acido_residual", 0) == 0)
    check("erro: CA intacta", m["ac"] == 99)
    check("erro: item consumido", len(p["bag"]) == 0)
    S.random.randint = _REAL_RANDINT   # restaura o RNG
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: FAIL — `acido_residual` não é guardado e a CA não muda (efeitos ainda não plugados).

- [ ] **Step 3: Plugar os efeitos de ácido no ramo de acerto**

Em `_throw_item_alvo`, logo após o bloco `em_chamas` (o `if defn.get("em_chamas")…`
que termina no `gm_say` de "pega fogo", server.py:~6614) e ainda DENTRO do `if hit:`,
adicione:

```python
            if defn.get("residual") and target.get("hp", 0) > 0:
                target["acido_residual"] = max(target.get("acido_residual", 0), dmg // 2)
                await self.gm_say(
                    f"🧪 O ácido gruda em **{target['name']}** — **{dmg // 2}** de dano "
                    f"residual na próxima rodada!")
            if defn.get("corrosao_ac"):
                await self._acido_corroer(target, defn["corrosao_ac"])
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_arremessaveis_acido.py`
Expected: PASS — seções [1]-[5] OK.

- [ ] **Step 5: Rodar as regressões**

Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_arremessaveis_area.py`
Run: `python tools/test_ground_items.py`
Expected: todos passam (`46/0`, `41/0`, `23/0`).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_arremessaveis_acido.py
git commit -m "feat(arremessaveis): acido aplica residual + corrosao de CA no acerto"
```

---

### Task 5: Cliente — entradas de catálogo

**Files:**
- Modify: `src/gameState.js` — `CATALOGO_ITENS`
- Test: manual

- [ ] **Step 1: Adicionar as 2 entradas no `CATALOGO_ITENS`**

Junto das entradas de arremessáveis já existentes (A/B), adicione (mesma forma dos
itens `ataque_alvo` como `frasco_oleo` — sem `alvo:'area'`):

```javascript
    frasco_acido: {
      id: 'frasco_acido', nome: 'Frasco de Ácido', emoji: '🧪',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4,
      descricao: 'Arremesse (4 quad., ataque por DES). 1d6 de ácido + metade na ' +
                 'rodada seguinte. Corrói a defesa do alvo (−1 CA por acerto).',
    },
    vidro_acido_grande: {
      id: 'vidro_acido_grande', nome: 'Vidro de Ácido Grande', emoji: '🫙',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4,
      descricao: 'Arremesse (4 quad., ataque por DES). 2d6 de ácido + metade na ' +
                 'rodada seguinte. Corrói a defesa do alvo (−2 CA por acerto).',
    },
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(arremessaveis): cliente — entradas de catalogo dos acidos"
```

---

### Task 6: Verificação end-to-end

**Files:** nenhum

- [ ] **Step 1: Suíte completa do servidor**

Run: `python tools/test_arremessaveis_acido.py`
Run: `python tools/test_arremessaveis.py`
Run: `python tools/test_arremessaveis_area.py`
Run: `python tools/test_ground_items.py`
Expected: todos `0 FALHAS` / `0 XX`.

- [ ] **Step 2: Syntax check do cliente**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Verificação manual (`iniciar.bat`)**

Compre um Frasco de Ácido e um Vidro de Ácido Grande e, numa masmorra:
1. Clique direito no Frasco → mira **vermelha single-target** (igual ao Óleo)
2. Acertar um monstro → dano de ácido; na **rodada seguinte** ele toma metade de novo
3. A **CA do monstro cai** a cada acerto (−1 Frasco / −2 Vidro Grande); vários acertos acumulam, sem descer de 5
4. Vidro Grande → 2d6 e −2 CA
5. Errar (alvo com CA alta) → item gasto, sem dano/residual/corrosão
6. Fora do alcance / atrás de parede → toast, item não gasto; ESC cancela
7. Óleo/Fogo Grego (A) e bombas/granadas (B) seguem funcionando

- [ ] **Step 4: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(arremessaveis): ajustes da verificacao de acido"
```

---

## Self-review (cobertura do spec)

- ✅ 2 itens no catálogo/loja (`residual`/`corrosao_ac`) → Task 1.
- ✅ Corrosão de CA com piso 5, cumulativa, helper único com gancho dormant → Task 2.
- ✅ Dano residual (metade, um tick na rodada seguinte) → Task 3.
- ✅ Efeitos no acerto de `_throw_item_alvo` (residual + corrosão), só no acerto, item consumido em acerto/erro → Task 4.
- ✅ Cliente reusa a mira single-target de A (só entradas de catálogo) → Task 5.
- ✅ Elemento `"acido"`; ação principal (herdado de `_throw_item_alvo`) → Tasks 1, 4.
- ✅ Testes + regressões de A/B → Tasks 1-4, 6.

**Fora de escopo (confirmado):** equipamento corroível de monstros (ramo dormant),
cola/rede (Sub-projeto D), veneno Agonia Sufocante (Sub-projeto E), exibir a CA
corroída no tooltip do monstro.
```
