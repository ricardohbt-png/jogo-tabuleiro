# Editor de Itens — Fase F: Poções — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Destravar a sub-aba Poções do Editor de Itens, criando poções consumíveis custom (efeitos `heal`/`regeneration`/`atk_bonus`) mescladas na loja do mercador.

**Architecture:** Poções são consumíveis de bolsa (`item_slot:"bag"`) despachados por `effect` no `handle_use_item` — os três efeitos já existem no motor. Esta fase só adiciona o pipeline do editor: validação/normalização no servidor (`_validate_custom_potion` + merge em `SHOP_MERCHANT`/baús/loot), lógica pura no cliente (`serializePotion`) e a UI da sub-aba. Nenhuma mudança no `handle_use_item`.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py` e `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging (server.py) — LER ANTES DAS TASKS 2 e 3

O usuário reworka `server.py` em paralelo (WIP não commitado — "Barreira Arcana"). **NUNCA** `git add server.py` nem `git add -A`. As mudanças desta fase são blocos aditivos na região contígua de itens custom (~linhas 21200–21500), longe do WIP (cujos hunks mais próximos ficam em ~20195 e ~21518). Os hunks do `git diff` são separáveis.

Ao commitar uma task de servidor:

```bash
git add tools/test_editor_itens.py                 # teste é seguro (fora do WIP)
git diff -- server.py > /tmp/all.patch             # contém SEUS hunks + o WIP
# Leia /tmp/all.patch e monte /tmp/mine.patch com o header (4 linhas: diff/index/---/+++)
# + APENAS os @@ hunks que VOCÊ escreveu (as funções de poção desta fase).
git apply --cached /tmp/mine.patch
git diff --cached --stat
git diff --cached -- server.py                     # confira a olho: só código de poção
```

Se aparecer qualquer linha do WIP no staged, `git reset server.py` e refaça a extração. `git add -p` é interativo e **não funciona** aqui — use sempre `git apply --cached`. Arquivos de cliente (`tools/editor_items_*.js`), `CLAUDE.md` e docs **não** estão no WIP → `git add <arquivo>` direto é seguro.

---

## File Structure

- **Modify:** `tools/editor_items_logic.js` — `POTION_EFFECTS`, `serializePotion`/`validatePotionDraft`/`suggestPricePotion`.
- **Modify:** `tools/test_editor_items_logic.js` — casos node de poção.
- **Modify:** `server.py` — `_ITEM_POTION_EFFECTS`, `_validate_custom_potion` + dispatch, `_custom_potion_inventory_dict`, ramo de merge em `_apply_custom_items`.
- **Modify:** `tools/test_editor_itens.py` — seção `[F1]`–`[F4]`.
- **Modify:** `tools/editor_items_editor.js` — destravar sub-aba, form de poção.
- **Modify:** `CLAUDE.md` — nota da Fase F.

---

## Task 1: Lógica pura (cliente) — serializePotion

**Files:**
- Modify: `tools/editor_items_logic.js`
- Test: `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever os testes node que falham**

Acrescente ANTES da linha final `console.log(...)` em `tools/test_editor_items_logic.js`:

```javascript
// Fase F — poções
check("POTION_EFFECTS tem os 3 efeitos",
  L.POTION_EFFECTS.indexOf("heal") >= 0 && L.POTION_EFFECTS.indexOf("regeneration") >= 0
  && L.POTION_EFFECTS.indexOf("atk_bonus") >= 0);
const potHeal = L.serializePotion({name:"Poção Robusta", item_type:"potion",
  effect:"heal", value:25, max_uses:3,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializePotion gera id + item_slot bag + item_type potion",
  potHeal.id === "pocao_robusta" && potHeal.item_slot === "bag" && potHeal.item_type === "potion");
check("serializePotion heal grava value", potHeal.value === 25);
check("serializePotion heal multi-dose grava max_uses+uses_left",
  potHeal.max_uses === 3 && potHeal.uses_left === 3);
check("serializePotion emoji default 🧪", L.serializePotion({name:"X",effect:"heal"}).emoji === "🧪");
const potRegen = L.serializePotion({name:"Regen", item_type:"potion", effect:"regeneration", value:10,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:16});
check("serializePotion regen sem doses", potRegen.effect === "regeneration" && potRegen.max_uses === undefined);
const potElix = L.serializePotion({name:"Elixir", item_type:"potion", effect:"atk_bonus", value:3, max_uses:5,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:12});
check("serializePotion não-heal ignora doses", potElix.max_uses === undefined && potElix.uses_left === undefined);
const potBad = L.serializePotion({name:"Ruim", item_type:"potion", effect:"teleporte", value:1,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:1});
check("serializePotion normaliza efeito inválido p/ heal", potBad.effect === "heal");
check("validatePotionDraft aceita heal", L.validatePotionDraft({name:"X", effect:"heal"}).ok);
check("validatePotionDraft rejeita sem nome", !L.validatePotionDraft({name:"", effect:"heal"}).ok);
check("validatePotionDraft rejeita efeito inválido", !L.validatePotionDraft({name:"X", effect:"voar"}).ok);
check("suggestPricePotion cresce com value", L.suggestPricePotion({value:20,max_uses:1}) > L.suggestPricePotion({value:5,max_uses:1}));
check("suggestPricePotion cresce com doses", L.suggestPricePotion({value:10,max_uses:3}) > L.suggestPricePotion({value:10,max_uses:1}));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_items_logic.js`
Expected: FAIL (`L.serializePotion is not a function` / `POTION_EFFECTS` indefinido).

- [ ] **Step 3: Implementar em `tools/editor_items_logic.js`**

3a. Adicione a constante de preço junto das outras constantes `K_*` no topo (perto de `var K_DIE = 4, ...`):

```javascript
  var K_POTION = 2;
```

3b. Adicione `POTION_EFFECTS` perto de `BONUS_EFFECTS`/`RESIST_TYPES`:

```javascript
  var POTION_EFFECTS = ["heal", "regeneration", "atk_bonus"];
```

3c. Adicione as três funções logo após `suggestPriceAccessory` (perto do bloco de acessório):

```javascript
  function serializePotion(d) {
    var effect = POTION_EFFECTS.indexOf(d.effect) >= 0 ? d.effect : "heal";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "🧪", item_type: "potion", item_slot: "bag", custom: true,
      effect: effect, value: Math.max(0, +d.value || 0),
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (effect === "heal") {
      var mu = Math.max(1, +d.max_uses || 1);
      if (mu > 1) { item.max_uses = mu; item.uses_left = mu; }
    }
    return item;
  }
  function validatePotionDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (POTION_EFFECTS.indexOf(d.effect) < 0) return { ok: false, msg: "efeito inválido" };
    return { ok: true };
  }
  function suggestPricePotion(item) {
    var mu = Math.max(1, +item.max_uses || 1);
    return Math.max(1, Math.round(K_POTION * (+item.value || 0) * mu));
  }
```
Note: `slugify` e `K_POTION` (3a) e `POTION_EFFECTS` (3b) já estão no módulo — use-os.

3d. Adicione os quatro nomes ao objeto `api` (junto de `serializeAccessory` etc.):

```javascript
              serializePotion: serializePotion,
              validatePotionDraft: validatePotionDraft,
              suggestPricePotion: suggestPricePotion,
              POTION_EFFECTS: POTION_EFFECTS,
```

- [ ] **Step 4: Rodar e ver passar (sem regressão)**

Run: `node tools/test_editor_items_logic.js`
Expected: PASS — todos verdes, incluindo os casos de arma/armadura/acessório pré-existentes.

- [ ] **Step 5: Commit (arquivos de cliente — seguros)**

```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): lógica de poções custom (heal/regeneration/atk_bonus)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação de poção

**Files:**
- Modify: `server.py` (`_validate_custom_item`; nova `_validate_custom_potion`; novo set `_ITEM_POTION_EFFECTS`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_itens.py`, adicione a factory + teste logo após `accessory_sample` (busque `def accessory_sample`):

```python
def potion_sample(**over):
    base = {"id": "pocao_teste", "name": "Poção Teste", "emoji": "🧪", "item_type": "potion",
            "effect": "heal", "value": 15, "allowed_classes": [], "price": 20,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_pocao():
    print("\n[F1] Validacao de poção")
    ok, it = S._validate_custom_item(potion_sample())
    check("aceita poção heal valida", ok)
    check("item_type = potion", ok and it.get("item_type") == "potion")
    check("item_slot = bag", ok and it.get("item_slot") == "bag")
    check("effect/value preservados", ok and it.get("effect") == "heal" and it.get("value") == 15)
    check("single-dose nao grava uses_left", ok and "uses_left" not in it)
    okd, itd = S._validate_custom_item(potion_sample(id="pocao_doses", max_uses=3))
    check("heal multi-dose grava max_uses+uses_left",
          okd and itd.get("max_uses") == 3 and itd.get("uses_left") == 3)
    okr, itr = S._validate_custom_item(potion_sample(id="pocao_regen", effect="regeneration", value=10))
    check("aceita regeneration", okr and itr.get("effect") == "regeneration")
    oka, ita = S._validate_custom_item(potion_sample(id="pocao_elixir", effect="atk_bonus", value=3, max_uses=5))
    check("atk_bonus ignora doses", oka and "max_uses" not in ita)
    okb, _ = S._validate_custom_item(potion_sample(effect="teleporte"))
    check("rejeita effect invalido", not okb)
    okn, _ = S._validate_custom_item(potion_sample(id="health_potion"))
    check("rejeita id nativo (health_potion)", not okn)
    oke, _ = S._validate_custom_item(potion_sample(id="elixir"))
    check("rejeita id nativo do mercador (elixir)", not oke)
```

Registre no `if __name__ == "__main__":`, logo APÓS a linha `test_acessorio_botas_corrosao(); test_acessorio_merge()`:

```python
    test_validacao_pocao()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL em `[F1]` (`_validate_custom_item` retorna "tipo de item não suportado" para `potion`). Nenhuma seção anterior afetada.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione o set de efeitos junto de `_ITEM_BONUS_EFFECTS`/`_RESIST_TYPES` (região ~21216):

```python
_ITEM_POTION_EFFECTS = {"heal", "regeneration", "atk_bonus"}
```

3b. Em `_validate_custom_item`, adicione o dispatch de poção. A função hoje termina com:
```python
    if it in ("ring", "boots"):
        return _validate_custom_accessory(raw)
    return False, "tipo de item não suportado"
```
Mude para:
```python
    if it in ("ring", "boots"):
        return _validate_custom_accessory(raw)
    if it == "potion":
        return _validate_custom_potion(raw)
    return False, "tipo de item não suportado"
```

3c. Adicione a nova função imediatamente após `_validate_custom_accessory` (depois do seu `return True, item`):

```python
def _validate_custom_potion(raw):
    """Valida poção custom (Fase F). Consumível de bolsa despachado por effect em
    handle_use_item (heal/regeneration/atk_bonus — todos já implementados)."""
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome da poção"
    native = {i["id"] for shop in (SHOP_MERCHANT, SHOP_TEMPLE, SHOP_TAVERN)
              for i in shop if not i.get("custom")}
    if iid in native:
        return False, "o id não pode substituir um item nativo"
    effect = raw.get("effect")
    if effect not in _ITEM_POTION_EFFECTS:
        return False, "efeito de poção inválido"
    def _int0(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    item = {
        "id": iid, "name": name, "emoji": str(raw.get("emoji") or "🧪")[:8],
        "item_type": "potion", "item_slot": "bag", "custom": True,
        "effect": effect, "value": max(0, _int0(raw.get("value"))),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    if effect == "heal":
        mu = max(1, _int0(raw.get("max_uses", 1)))
        if mu > 1:
            item["max_uses"] = mu
            item["uses_left"] = mu
    return True, item
```
Note: `SHOP_MERCHANT`, `SHOP_TEMPLE`, `SHOP_TAVERN`, `_ITEM_CLASSES`, `_ITEM_POTION_EFFECTS` (3a) já são module-level.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: `[F1]` totalmente verde; nenhuma seção anterior regride.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks desta task: `_ITEM_POTION_EFFECTS`, o ramo em `_validate_custom_item`, a função `_validate_custom_potion`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com os 3 hunks acima, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py   # confirmar: só código de poção
git commit -m "feat(itens): validação de poções custom

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — merge + uso ponta-a-ponta

**Files:**
- Modify: `server.py` (nova `_custom_potion_inventory_dict`; `_apply_custom_items`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione após `test_validacao_pocao`:

```python
def test_pocao_merge():
    print("\n[F2] Merge de poção no mercador/baús/loot")
    ok, it = S._validate_custom_item(potion_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "pocao_teste" for i in S.SHOP_MERCHANT))
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "pocao_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "pocao_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT (elixir) intacto", any(i["id"] == "elixir" for i in S.SHOP_MERCHANT))
    check("nativo SHOP_TEMPLE (health_potion) intacto", any(i["id"] == "health_potion" for i in S.SHOP_TEMPLE))
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "pocao_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "pocao_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "pocao_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("lista vazia remove de LOOT_POOL_PROCEDURAL", "pocao_teste" not in S.LOOT_POOL_PROCEDURAL)

def _turn_room():
    """Sala mínima com um herói cujo turno está ativo (para handle_use_item)."""
    r = _gear_room()
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]; r.turn_index = 0
    r.current_actor = lambda: None   # força o caminho player_order em current_pid
    return r, p

def test_pocao_uso():
    print("\n[F3] Uso ponta-a-ponta via handle_use_item")
    # Cura
    r, p = _turn_room()
    inv = S._custom_potion_inventory_dict(S._validate_custom_item(potion_sample(value=15))[1])
    p["hp"] = 1
    p["bag"] = [dict(inv)]
    asyncio.run(r.handle_use_item("p1", "pocao_teste"))
    check("cura sobe o HP", p["hp"] == min(p["max_hp"], 16))
    check("poção consumida da bolsa", not any(i["id"] == "pocao_teste" for i in p["bag"]))
    # Regeneração
    r, p = _turn_room()
    invr = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_regen", effect="regeneration", value=10))[1])
    p["bag"] = [dict(invr)]
    pool0 = p.get("potion_regen_pool", 0)
    asyncio.run(r.handle_use_item("p1", "pocao_regen"))
    check("regeneração soma ao pool", p.get("potion_regen_pool", 0) == pool0 + 10)
    # Buff de ataque
    r, p = _turn_room()
    inva = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_elixir", effect="atk_bonus", value=3))[1])
    p["bag"] = [dict(inva)]
    atk0 = p["atk_bonus"]
    asyncio.run(r.handle_use_item("p1", "pocao_elixir"))
    check("atk_bonus buff aplicado", p["atk_bonus"] == atk0 + 3)

def test_pocao_multidose():
    print("\n[F4] Multi-dose consome uma dose por uso")
    r, p = _turn_room()
    inv = S._custom_potion_inventory_dict(S._validate_custom_item(
        potion_sample(id="pocao_doses", value=8, max_uses=2))[1])
    p["hp"] = 1
    p["bag"] = [dict(inv)]
    asyncio.run(r.handle_use_item("p1", "pocao_doses"))
    check("dose 1: fica na bolsa", any(i["id"] == "pocao_doses" for i in p["bag"]))
    check("dose 1: uses_left = 1", next(i for i in p["bag"] if i["id"] == "pocao_doses")["uses_left"] == 1)
    p["bonus_action_used"] = False   # novo turno (libera a ação bônus)
    asyncio.run(r.handle_use_item("p1", "pocao_doses"))
    check("dose 2: sai da bolsa ao zerar", not any(i["id"] == "pocao_doses" for i in p["bag"]))
```

Registre no `if __name__ == "__main__":`, logo APÓS `test_validacao_pocao()`:

```python
    test_pocao_merge(); test_pocao_uso(); test_pocao_multidose()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL — `_custom_potion_inventory_dict` não existe; poção não entra em `SHOP_MERCHANT`.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione a nova função imediatamente após `_custom_accessory_inventory_dict` (após o seu `return inv`):

```python
def _custom_potion_inventory_dict(item):
    """Poção custom — dict plano p/ loja (SHOP_MERCHANT) E bolsa/baú. Consumível
    de bolsa despachado por effect em handle_use_item."""
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": "bag", "effect": item["effect"], "value": item["value"],
           "custom": True, "price": item["price"]}
    if "max_uses" in item:
        inv["max_uses"] = item["max_uses"]
        inv["uses_left"] = item.get("uses_left", item["max_uses"])
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv
```

3b. No laço `for raw in records:` de `_apply_custom_items`, adicione um ramo de poção imediatamente APÓS o ramo de acessório (`if it in ("ring", "boots"): ... continue`):

```python
        if it == "potion":
            disp = item["disponibilidade"]
            inv = _custom_potion_inventory_dict(item)
            if disp["loja"]:
                SHOP_MERCHANT.append(inv)
            if disp["baus"] or disp["loot_monstro"]:
                _DUNGEON_ITEM_CATALOG[item["id"]] = inv
            if disp["loot_monstro"]:
                LOOT_POOL_PROCEDURAL.append(item["id"])
            continue
```
Note: a limpeza de poções custom já é coberta pela linha `SHOP_MERCHANT[:] = [...]` (Fase E) + o bloco genérico `prev_custom_ids` (`_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL`) — não adicione cleanup novo.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: `[F2]`–`[F4]` verdes; nenhuma seção anterior regride.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks desta task: `_custom_potion_inventory_dict` (nova) e o ramo `if it == "potion"` em `_apply_custom_items`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com os hunks acima, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py   # confirmar: só código de poção
git commit -m "feat(itens): merge de poções custom no mercador

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Editor — destravar sub-aba Poções

**Files:**
- Modify: `tools/editor_items_editor.js`

Sem teste headless (o editor não roda no MCP). Verificação: parse + `node tools/test_editor_items_logic.js` verde. Cada passo mostra o código exato. Leia o arquivo primeiro para confirmar os nomes reusados (`novoDraftFor`, `renderForm`, `seccao`/`campo`/`numInput`/`selectOpts`/`chkLbl`/`esc`, `CLASSES`, `previewFn`, `root`, `draft`, `artFile`, `artURL`, `L`).

- [ ] **Step 1: Destravar a sub-aba na tabela `TYPES`**

Troque:
```javascript
    ["aneis","Anéis",true],["botas","Botas",true],["pocoes","Poções",false],
```
por:
```javascript
    ["aneis","Anéis",true],["botas","Botas",true],["pocoes","Poções",true],
```

- [ ] **Step 2: Draft + roteamento**

2a. Adicione `novoDraftPotion` após `novoDraftAccessory`:
```javascript
  function novoDraftPotion() {
    return { name:"", emoji:"🧪", item_type:"potion", effect:"heal", value:10, max_uses:1,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
```
2b. Em `novoDraftFor`, adicione o roteamento de poção (antes do `return novoDraft();`):
```javascript
    if (type === "pocoes") return novoDraftPotion();
```

- [ ] **Step 3: Dispatch em `renderForm`**

Após o bloco que despacha `aneis`/`botas` para `renderAccessoryForm`, adicione:
```javascript
    if (activeType === "pocoes") { renderPotionForm(f); return; }
```

- [ ] **Step 4: Formulário, leitura, preview, bind e save de poção**

Adicione estas funções perto de `renderAccessoryForm`. `POTION_LABELS` mapeia o rótulo amigável do efeito:
```javascript
  var POTION_LABELS = { heal:"Cura (+HP)", regeneration:"Regeneração (pool +1/rodada)", atk_bonus:"Elixir (+ataque no turno)" };

  function renderPotionForm(f) {
    var isHeal = draft.effect === "heal";
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Efeito",
        campo("Tipo", '<select id="ie-effect">' + (L.POTION_EFFECTS || ["heal","regeneration","atk_bonus"]).map(function (e) {
          return '<option value="' + e + '"' + (e === draft.effect ? " selected" : "") + '>' + esc(POTION_LABELS[e] || e) + '</option>'; }).join("") + '</select>') +
        campo("Valor", numInput("ie-value", draft.value, 0, 999)) +
        (isHeal ? campo("Doses (garrafa)", numInput("ie-maxuses", draft.max_uses, 1, 20)) :
          '<span class="ie-hint">Doses só se aplicam a poções de Cura.</span>')),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar poção</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderPotionPreview;
    bindPotionForm();
    renderPotionPreview();
  }

  function currentPotionDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.effect = g("ie-effect").value;
    draft.value = Math.max(0, +g("ie-value").value || 0);
    var mu = g("ie-maxuses"); if (mu) draft.max_uses = Math.max(1, +mu.value || 1);
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderPotionPreview() {
    currentPotionDraftFromForm();
    var item = L.serializePotion(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPricePotion(item) + " 🪙";
    var parts = [POTION_LABELS[item.effect] || item.effect, "valor " + item.value];
    if (item.max_uses) parts.push(item.max_uses + " doses");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindPotionForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderPotionPreview; el.oninput = renderPotionPreview;
    });
    // Trocar o efeito troca o form (o campo Doses só existe para Cura).
    root.querySelector("#ie-effect").onchange = function () { currentPotionDraftFromForm(); renderPotionForm(root.querySelector("#ie-form")); };
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderPotionPreview();
    };
    root.querySelector("#ie-save").onclick = onSavePotion;
  }

  async function onSavePotion() {
    currentPotionDraftFromForm();
    var v = L.validatePotionDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializePotion(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item);
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }
```
Nota sobre o `onchange` do efeito: como trocar de/para `heal` muda quais campos existem (Doses), o handler re-renderiza o form inteiro — mesmo padrão do `ie-manejo` das armas. `renderForm` passa `f` (o `#ie-form`); aqui reusa `root.querySelector("#ie-form")` para o mesmo elemento.

- [ ] **Step 5: Verificar (parse + node) e commit**

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('parse OK')"`
Expected: `parse OK`.

Run: `node tools/test_editor_items_logic.js`
Expected: PASS (inalterado).

```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor destrava sub-aba Poções

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória em `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\`

- [ ] **Step 1: Rodar a suíte completa no estado COMMITADO isolado**

```bash
git worktree add --detach /tmp/lfh_verify_f HEAD
cd /tmp/lfh_verify_f
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify_f --force
```
Expected: `[F1]`–`[F4]` verdes e node verde; nenhuma seção anterior de `test_editor_itens.py` quebrada. Falhas pré-existentes que **não** são regressão: `tools/test_roteamento_itens.py` (por `health_potion`, WIP do usuário), `tools/test_devorador.py` (1 teste flaky).

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase E (final do arquivo), resumindo a Fase F: sub-aba Poções, 3 efeitos consumíveis (`heal` com multi-dose, `regeneration`, `atk_bonus`) já implementados no `handle_use_item` (sem mudança no motor), `_validate_custom_potion` + `_custom_potion_inventory_dict` + merge no `SHOP_MERCHANT`/baús/loot (cleanup herdado da Fase E), UI da sub-aba com seletor de efeito e doses só p/ Cura. Cite os arquivos e o teste `[F1]`–`[F4]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-23-editor-itens-fase-f-pocoes.md
git commit -m "docs(itens): registra o Editor de Itens — Fase F (poções)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/editor-itens-fase-f-pocoes.md` (tipo `project`) resumindo o que foi feito, o estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), quantos checks passaram e o follow-up de smoke in-app. Adicione a linha-índice no topo de `MEMORY.md`. Linke `[[editor-itens-fase-e-aneis-botas]]`.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app (o editor não roda headless): `python server.py` → `tools/editor.html` → aba "Editor de itens" → sub-aba Poções: criar poção de Cura (com doses), Regeneração e Elixir; salvar. Em jogo: comprar no mercador, usar da bolsa (ação bônus) e conferir o efeito (HP / reserva de regeneração / +ataque no turno).

---

## Self-Review (autor do plano)

- **Cobertura do spec:** `_validate_custom_potion` + dispatch (T2) ✓; `_ITEM_POTION_EFFECTS` (T2) ✓; native-id via SHOP_MERCHANT∪TEMPLE∪TAVERN (T2) ✓; multi-dose só heal (T2/T4) ✓; `_custom_potion_inventory_dict` + merge SHOP_MERCHANT/baús/loot (T3) ✓; uso ponta-a-ponta via handle_use_item (T3, [F3]) ✓; serializePotion/validate/suggestPrice + POTION_EFFECTS (T1) ✓; UI sub-aba + seletor de efeito + doses só heal + "Loja (Mercador)" (T4) ✓; testes [F1]–[F4] + node ✓; verificação isolada + docs + memória (T5) ✓.
- **Setup de turno do [F3]:** `_is_turn` exige `phase=="playing"` + `current_pid()==pid`; `current_pid` cai em `player_order[turn_index]` quando `current_actor()` é None. O helper `_turn_room` seta exatamente isso (`current_actor = lambda: None`). Cada uso consome a ação bônus (`bonus_action_used`), por isso o [F4] reseta o flag entre doses e o [F3] usa sala/jogador frescos por efeito.
- **atk_bonus (poção vs gear):** a poção usa `effect:"atk_bonus"` (consumível de bolsa → buff temporário em handle_use_item); distinto do efeito de gear homônimo da Fase E (lista `bonuses`). Sem colisão.
- **Consistência de tipos:** `serializePotion`/`validatePotionDraft`/`suggestPricePotion`/`POTION_EFFECTS` (T1) casam com as chamadas em T4; `_custom_potion_inventory_dict` (T3) casa com [F3]/[F4]; `previewFn` (Fase E) reusado em T4.
- **Sem placeholders:** todos os passos têm código/comando concreto.
