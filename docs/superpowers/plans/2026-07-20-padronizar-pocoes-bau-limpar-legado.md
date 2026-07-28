# Padronizar poções de baú + limpar legado — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Baús procedurais passam a largar as poções/consumíveis vendidos nas lojas; o `CHEST_ITEMS` legado é reduzido à Espada Curta de Ferro Serrilhado (com preço), e as referências aos ids removidos são migradas.

**Architecture:** Novo `LOOT_POOL_PROCEDURAL` (lista de ids) resolvido pelo catálogo autoritativo `_DUNGEON_ITEM_CATALOG` (já mescla `CHEST_ITEMS` + as 6 lojas, loja vencendo). `_spawn_chest_from_room` sorteia desse pool. `CHEST_ITEMS` é podado; `_necromante_loot` e as fixtures/testes que citavam ids removidos são repontados para ids de loja válidos. O catálogo do editor é regenerado.

**Tech Stack:** Python 3 (server.py, sem framework), testes ad-hoc em `tools/test_*.py` (rodados com `python tools/<x>.py`), gerador `tools/export_catalog.py`.

**Ordem sem quebra transitória entre commits:** pool novo → repontar necromante → migrar refs → podar `CHEST_ITEMS` → regenerar editor → regressão. Cada commit deixa a suíte verde.

**Spec:** `docs/superpowers/specs/2026-07-20-padronizar-pocoes-bau-limpar-legado-design.md`

---

### Task 1: Pool de loot procedural + `_spawn_chest_from_room`

**Files:**
- Create: `tools/test_loot_bau.py`
- Modify: `server.py` (adicionar `LOOT_POOL_PROCEDURAL` perto de `CHEST_ITEMS` ~2867; alterar `_spawn_chest_from_room` em ~11735)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_loot_bau.py`:

```python
"""Testa o loot de baú procedural: sorteia só do pool de poções/consumíveis das
lojas, e todos os ids do pool resolvem no catálogo autoritativo.
Roda da raiz: python tools/test_loot_bau.py"""
import asyncio, sys, os, random
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import (GameRoom, LOOT_POOL_PROCEDURAL, _DUNGEON_ITEM_CATALOG)

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    return r

async def main():
    random.seed(3)
    print("\n[1] ids do pool resolvem no catálogo")
    for iid in LOOT_POOL_PROCEDURAL:
        check(f"'{iid}' está no catálogo", iid in _DUNGEON_ITEM_CATALOG)

    print("\n[2] baú procedural só contém itens do pool")
    r = setup()
    fora = []
    for i in range(200):
        await r._spawn_chest_from_room({"cx": 5, "cy": 5, "looted": False})
    for chest in r.chests.values():
        for it in chest["items"]:
            if it["id"] not in LOOT_POOL_PROCEDURAL:
                fora.append(it["id"])
    check("nenhum item fora do pool em 200 baús", fora == [], f"fora: {set(fora)}")
    check("todo baú tem ao menos 1 item", all(c["items"] for c in r.chests.values()))

    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_loot_bau.py`
Expected: FAIL — `ImportError: cannot import name 'LOOT_POOL_PROCEDURAL'` (ainda não existe).

- [ ] **Step 3: Adicionar `LOOT_POOL_PROCEDURAL`**

Em `server.py`, logo **após** o bloco `CHEST_ITEMS = [ ... ]` (~linha 2890), adicionar:

```python
# IDs sorteados em baús PROCEDURAIS (os que surgem ao limpar salas). Fonte única:
# definições de loja, resolvidas por _DUNGEON_ITEM_CATALOG (montado mais abaixo no
# módulo; já está pronto quando _spawn_chest_from_room roda). Extensível quando os
# itens mágicos ganharem regras de colocação.
LOOT_POOL_PROCEDURAL = [
    "health_potion", "health_potion_small", "health_potion_improved",
    "health_potion_concentrated", "regeneration_potion", "antidote", "elixir",
    "racao_viagem", "garrafa_vinho",
]
```

- [ ] **Step 4: Alterar `_spawn_chest_from_room`**

Em `server.py` ~11735, substituir o corpo que sorteia de `CHEST_ITEMS`:

```python
    async def _spawn_chest_from_room(self, room):
        """Spawn a physical chest at room centre (replaces _auto_pickup_chest)."""
        room["looted"] = True
        gold  = random.randint(10, 35)
        items = [deepcopy(_DUNGEON_ITEM_CATALOG[random.choice(LOOT_POOL_PROCEDURAL)])]
        if random.random() < 0.45:                            # 45 % chance for 2nd item
            extra = deepcopy(_DUNGEON_ITEM_CATALOG[random.choice(LOOT_POOL_PROCEDURAL)])
            if extra["id"] != items[0]["id"]:
                items.append(extra)
        self._spawn_chest([room["cx"], room["cy"]], gold, items)
        await self.gm_say("🎁 Um **baú** apareceu no centro da sala! Aproxime-se e clique nele para coletar.")
```

- [ ] **Step 5: Rodar o teste e ver passar**

Run: `python tools/test_loot_bau.py`
Expected: PASS — `X passaram, 0 falharam` (todos os ids resolvem; 200 baús só com itens do pool).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_loot_bau.py
git commit -m "feat(loot): baus procedurais sorteiam pocoes/consumiveis das lojas"
```

---

### Task 2: Repontar `_necromante_loot` para defs de loja

**Files:**
- Modify: `server.py` (`_necromante_loot` ~17375)

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `tools/test_loot_bau.py`, dentro de `main()` antes do print final de resultado, um bloco novo:

```python
    print("\n[3] _necromante_loot usa defs de loja (vinho/ração de viagem)")
    from server import make_monster, MONSTER_DEFS
    r = setup()
    ndef = next(d for d in MONSTER_DEFS if d.get("type") == "dark_mage")
    # rola 71..90 -> vinho ; 91..95 -> ração
    for alvo_roll, esperado in ((80, "garrafa_vinho"), (93, "racao_viagem")):
        m = make_monster(ndef, {"id": 1, "cx": 2, "cy": 2})
        m["pos"] = [2, 2]
        m["usou_dominar"] = True   # evita o pergaminho de dominar no fim
        _orig = random.randint
        random.randint = lambda a, b: alvo_roll if (a, b) == (1, 100) else _orig(a, b)
        try:
            await r._necromante_loot(m)
        finally:
            random.randint = _orig
        # o loot vai para um baú spawnado; procura o item esperado
        achou = any(it["id"] == esperado
                    for c in r.chests.values() for it in c["items"])
        check(f"necromante larga '{esperado}'", achou)
        r.chests.clear()
```

(`_necromante_loot` termina chamando `self._spawn_chest(list(m["pos"]), gold, itens)`,
então o loot sempre cai em `r.chests` — a verificação acima é direta.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_loot_bau.py`
Expected: FAIL na seção [3] — hoje o necromante busca `racao` (id que será removido) e usa `garrafa_vinho` do `CHEST_ITEMS`; após o próximo passo o teste passa. (Se já passar para `garrafa_vinho`, o de `racao_viagem` ainda falha.)

- [ ] **Step 3: Repontar as buscas**

Em `server.py` `_necromante_loot` (~17375), trocar as duas buscas em `CHEST_ITEMS` por resolução no catálogo:

```python
        elif roll <= 90:                                              # 20% 2 moedas + vinho
            gold = 2
            v = _DUNGEON_ITEM_CATALOG.get("garrafa_vinho")
            if v: itens.append(deepcopy(v))
        elif roll <= 95:                                             # 5% 2 moedas + ração
            gold = 2
            r = _DUNGEON_ITEM_CATALOG.get("racao_viagem")
            if r: itens.append(deepcopy(r))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_loot_bau.py`
Expected: PASS — seção [3] verde.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_loot_bau.py
git commit -m "refactor(necromante): loot de vinho/racao vem das defs de loja"
```

---

### Task 3: Migrar referências aos ids que serão removidos

**Files:**
- Modify: `tools/test_objetivos.py` (linhas ~332, 343, 363, 376)
- Modify: `dungeons/test_fase1.json` (baú com `magic_sword`)
- Modify: `dungeons/teste_basico.json` (baú com `shield`)

- [ ] **Step 1: Migrar `test_objetivos.py`**

Substituir todas as ocorrências do id de recompensa `magic_sword` por `shortsword`
nesse arquivo (4 pontos: 2 na definição do `reward.items`, 2 nas asserções
`id == "magic_sword"`). Comando de verificação:

Run: `grep -n "magic_sword" tools/test_objetivos.py`
Expected após editar: nenhuma ocorrência.

- [ ] **Step 2: Rodar `test_objetivos.py`**

Run: `python tools/test_objetivos.py`
Expected: PASS — `59 passou, 0 falhou` (recompensa agora usa `shortsword`, que resolve no catálogo).

- [ ] **Step 3: Migrar as fixtures autoradas**

Em `dungeons/test_fase1.json`, localizar o item de baú `{"id": "magic_sword"}` e trocar por `{"id": "shortsword"}`.
Em `dungeons/teste_basico.json`, localizar `{"id": "shield"}` e trocar por `{"id": "escudo_p"}`.

Verificação (nenhum id removido nas fixtures):

Run: `grep -lE "\"(magic_sword|shield|bow|ring|racao)\"" dungeons/test_fase1.json dungeons/teste_basico.json`
Expected: nenhuma saída (ou só arquivos que não contêm os ids alvo).

- [ ] **Step 4: Validar as fixtures no servidor**

Run:
```bash
python -c "import sys;sys.path.insert(0,'.');import server,json; \
d=json.load(open('dungeons/test_fase1.json',encoding='utf-8')); print(server.validar_dungeon(d)); \
d2=json.load(open('dungeons/teste_basico.json',encoding='utf-8')); print(server.validar_dungeon(d2))"
```
Expected: `(True, ...)` para ambas.

- [ ] **Step 5: Commit**

```bash
git add tools/test_objetivos.py dungeons/test_fase1.json dungeons/teste_basico.json
git commit -m "chore(loot): migra refs de magic_sword/shield para itens de loja"
```

---

### Task 4: Podar `CHEST_ITEMS` para a serrilhada (com preço)

**Files:**
- Modify: `server.py` (`CHEST_ITEMS` ~2867–2890)
- Modify: `tools/test_loot_bau.py` (adicionar asserções do catálogo)

- [ ] **Step 1: Escrever as asserções que falham**

Adicionar ao `tools/test_loot_bau.py`, em `main()` antes do print final:

```python
    print("\n[4] CHEST_ITEMS podado + catálogo consistente")
    from server import CHEST_ITEMS
    ids_chest = [i["id"] for i in CHEST_ITEMS]
    check("CHEST_ITEMS só tem a serrilhada", ids_chest == ["sword"], f"tem: {ids_chest}")
    sword = CHEST_ITEMS[0]
    check("serrilhada com price 32", sword.get("price") == 32)
    check("serrilhada mantém corrosao_resistente", sword.get("corrosao_resistente") == 1)
    # ids exclusivos de CHEST_ITEMS somem do catálogo
    for iid in ("magic_sword", "bow", "shield", "ring", "racao"):
        check(f"'{iid}' saiu do catálogo", iid not in _DUNGEON_ITEM_CATALOG)
    # ids que também existem em loja permanecem
    for iid in ("health_potion", "elixir", "antidote", "garrafa_vinho",
                "staff", "chainmail", "leather", "amulet", "boots", "cloak"):
        check(f"'{iid}' permanece no catálogo (loja)", iid in _DUNGEON_ITEM_CATALOG)
    check("health_potion resolve p/ 'Poção de Cura'",
          _DUNGEON_ITEM_CATALOG["health_potion"]["name"] == "Poção de Cura")
    check("sword permanece no catálogo", "sword" in _DUNGEON_ITEM_CATALOG)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_loot_bau.py`
Expected: FAIL na seção [4] — `CHEST_ITEMS` ainda tem 16 itens e os ids exclusivos ainda estão no catálogo.

- [ ] **Step 3: Podar `CHEST_ITEMS`**

Em `server.py`, substituir todo o literal `CHEST_ITEMS = [ ... ]` (~2867–2890) por:

```python
CHEST_ITEMS = [
    # Loot AUTORADO especial (referenciável no editor). Os consumíveis e o
    # equipamento genérico saíram daqui — baús procedurais usam LOOT_POOL_PROCEDURAL
    # (defs de loja) e os autorados resolvem pelo catálogo mesclado. A serrilhada
    # fica: é uma arma única (tolera +1 golpe do Devorador de Metal antes de corroer).
    {"id": "sword", "name": "Espada Curta de Ferro Serrilhado", "emoji": "⚔️",
     "item_slot": "weapon", "die": "1d6", "stat": "str_", "categoria": "cortante",
     "dmg_bonus": 2, "corrosao_resistente": 1, "price": 32},   # Espada Curta (12) + 20
]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_loot_bau.py`
Expected: PASS — todas as seções verdes.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_loot_bau.py
git commit -m "feat(loot): poda CHEST_ITEMS para a serrilhada (price 32); remove legado"
```

---

### Task 5: Regenerar o catálogo do editor

**Files:**
- Modify: `tools/editor_catalog.js` (gerado)

- [ ] **Step 1: Regenerar**

Run: `python tools/export_catalog.py`
Expected: `editor_catalog.js gerado em ...` (sem erro).

- [ ] **Step 2: Verificar que os ids removidos saíram do editor**

Run: `grep -oE "\"(magic_sword|bow|shield|ring|racao)\"" tools/editor_catalog.js`
Expected: nenhuma saída (os ids exclusivos removidos não aparecem).

Run: `grep -oE "\"sword\"|\"health_potion\"|\"shortsword\"" tools/editor_catalog.js | sort -u`
Expected: `"health_potion"`, `"shortsword"`, `"sword"` presentes (itens atuais mantidos).

- [ ] **Step 3: Commit**

```bash
git add tools/editor_catalog.js
git commit -m "chore(editor): regenera editor_catalog.js apos limpeza de itens"
```

---

### Task 6: Regressão final

**Files:** nenhum (só verificação)

- [ ] **Step 1: Rodar as suítes afetadas**

Run:
```bash
for t in test_loot_bau test_objetivos test_dungeon_loader test_devorador test_prata test_roteamento_itens test_export_catalog; do \
  echo "== $t =="; python "tools/$t.py" 2>&1 | tail -1; done
```
Expected: todas verdes (0 falhas). `test_devorador` pode ter 1 falha *flaky* pré-existente ("sucesso: magia teve efeito"); se aparecer, rodar de novo para confirmar que alterna — não é regressão.

- [ ] **Step 2: Confirmar validação de todas as masmorras autoradas**

Run:
```bash
python -c "import sys,glob,json;sys.path.insert(0,'.');import server; \
[print(f, server.validar_dungeon(json.load(open(f,encoding='utf-8')))[0]) for f in glob.glob('dungeons/*.json')]"
```
Expected: `True` para toda masmorra (nenhuma referencia id removido).

- [ ] **Step 3: (sem commit se nada mudou)**

Se algum ajuste foi necessário, commitar com mensagem descritiva; senão, encerrar.

---

## Notas de verificação manual (opcional, in-app)

- Entrar numa masmorra procedural, limpar uma sala e abrir o baú: deve conter
  poção(ões)/comida das lojas (nunca arma/armadura).
- No editor, abrir um baú e conferir que a lista de itens não tem mais
  `magic_sword`/`bow`/`shield`/`ring`/`racao`, mas mantém as poções e a serrilhada.
