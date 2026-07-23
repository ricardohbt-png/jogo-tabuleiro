# Editor de Itens — Fase E: Anéis + Botas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Destravar as sub-abas Anéis e Botas do Editor de Itens, criando acessórios custom que reusam o motor de multi-efeito existente, mesclados na loja do mercador.

**Architecture:** O equip de anéis/botas já é funcional no servidor (`_slot_category_for_item`/`_apply_gear_effect`). Esta fase só adiciona o pipeline do editor: validação/normalização no servidor (`_validate_custom_accessory` + merge em `SHOP_MERCHANT`), lógica pura no cliente (`serializeAccessory`) e a UI das duas sub-abas. Botas corroem via `corrosion_materials` (motor de defesa já engine-ready); anéis não corroem. Adiciona `atk_bonus` à lista de efeitos do motor (compartilhado com armaduras/escudos).

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py` e `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging (server.py) — LER ANTES DAS TASKS 2 e 3

O usuário reworka `server.py` em paralelo (WIP não commitado — "Barreira Arcana"). **NUNCA** `git add server.py` nem `git add -A`. As mudanças desta fase são blocos aditivos em locais distintos do WIP, então os hunks do `git diff` são separáveis.

Ao commitar uma task de servidor:

```bash
# 1) Stage o arquivo de teste (seguro — não está no WIP):
git add tools/test_editor_itens.py

# 2) Gere o diff completo de server.py (contém SEUS hunks + o WIP do usuário):
git diff -- server.py > /tmp/server_all.patch

# 3) Leia /tmp/server_all.patch e monte /tmp/server_mine.patch contendo APENAS os hunks
#    que VOCÊ escreveu nesta task (as funções/edições de acessório desta fase).
#    Mantenha o cabeçalho "diff --git ... / --- / +++" e só os @@ hunks seus.

# 4) Aplique só os seus hunks ao índice:
git apply --cached /tmp/server_mine.patch

# 5) CONFIRME que só suas mudanças + o teste estão staged:
git diff --cached --stat
git diff --cached -- server.py   # confira a olho: só código de acessório desta fase
```

Se o `git diff --cached -- server.py` mostrar qualquer linha do WIP do usuário, faça `git reset server.py` e refaça o passo 3. `git add -p` é interativo e **não funciona** neste ambiente — use sempre `git apply --cached`.

Arquivos de cliente (`tools/editor_items_*.js`), `CLAUDE.md` e docs **não** estão no WIP → `git add <arquivo>` direto é seguro (confirme com `git status --short`).

---

## File Structure

- **Modify:** `tools/editor_items_logic.js` — `+atk_bonus`, `filterBonuses` (extraído), `serializeAccessory`/`validateAccessoryDraft`/`suggestPriceAccessory`.
- **Modify:** `tools/test_editor_items_logic.js` — casos node de acessório.
- **Modify:** `server.py` — `+atk_bonus` em `_ITEM_BONUS_EFFECTS`, `_validate_custom_accessory` + dispatch, `_custom_accessory_inventory_dict`, merge em `_apply_custom_items`.
- **Modify:** `tools/test_editor_itens.py` — seção `[E1]`–`[E5]`.
- **Modify:** `tools/editor_items_editor.js` — destravar sub-abas, forms de acessório, `abonusTemplate` compartilhado.
- **Modify:** `CLAUDE.md` — nota da Fase E.

---

## Task 1: Lógica pura (cliente) — serializeAccessory + atk_bonus

**Files:**
- Modify: `tools/editor_items_logic.js`
- Test: `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever os testes node que falham**

Acrescente ANTES da linha final `console.log(...)` em `tools/test_editor_items_logic.js`:

```javascript
// Fase E — acessórios (anéis + botas)
check("BONUS_EFFECTS inclui atk_bonus", L.BONUS_EFFECTS.indexOf("atk_bonus") >= 0);
const ring = L.serializeAccessory({name:"Anel de Vigor", item_type:"ring",
  bonuses:[{effect:"maxhp",value:5},{effect:"atk_bonus",value:1},{effect:"atk",value:9}],
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:30});
check("serializeAccessory gera id+slot ring",
  ring.id === "anel_de_vigor" && ring.item_slot === "ring" && ring.kind === "ring");
check("serializeAccessory mantém atk_bonus",
  ring.bonuses.some(function(b){return b.effect==="atk_bonus"&&b.value===1;}));
check("serializeAccessory filtra efeito atk cru",
  !ring.bonuses.some(function(b){return b.effect==="atk";}));
check("anel não tem corrosão", ring.corrosion_materials === undefined);
const boot = L.serializeAccessory({name:"Botas de Ferro", item_type:"boots",
  bonuses:[{effect:"spd",value:1}], materiais:{metal:true,organic:false},
  corrosao_livres:1, corrosao_penalidade:3,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:20});
check("botas slot boots + material metal",
  boot.item_slot === "boots" && boot.corrosion_materials.indexOf("metal") >= 0);
check("botas N/M gravados",
  boot.corrosao_resistente === 1 && boot.corrosao_niveis_penalidade === 3);
check("botas emoji default 👢", boot.emoji === "👢");
check("validateAccessoryDraft aceita com nome", L.validateAccessoryDraft({name:"X"}).ok);
check("validateAccessoryDraft rejeita sem nome", !L.validateAccessoryDraft({name:""}).ok);
check("suggestPriceAccessory soma bonuses",
  L.suggestPriceAccessory({bonuses:[{value:2},{value:3}]}) > 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_items_logic.js`
Expected: FAIL (`L.serializeAccessory is not a function` / `BONUS_EFFECTS` sem atk_bonus).

- [ ] **Step 3: Implementar em `tools/editor_items_logic.js`**

3a. Adicione `"atk_bonus"` ao array `BONUS_EFFECTS` (linha ~69):

```javascript
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "atk_bonus", "str_", "dex", "con_", "int_", "resist", "initiative"];
```

3b. Extraia o filtro de bônus para uma função pura (DRY — reusada por armadura e acessório). Adicione logo após a linha `var RESIST_TYPES = [...]`:

```javascript
  function filterBonuses(list) {
    return (list || []).filter(function (b) {
      if (!b || BONUS_EFFECTS.indexOf(b.effect) < 0) return false;
      if (b.effect === "resist" && RESIST_TYPES.indexOf(b.type) < 0) return false;
      return true;
    }).map(function (b) {
      return b.effect === "resist"
        ? { effect: "resist", type: b.type, value: +b.value || 0 }
        : { effect: b.effect, value: +b.value || 0 };
    });
  }
```

3c. Em `serializeArmor`, troque o bloco inline `bonuses: (d.bonuses || []).filter(...).map(...)` por:

```javascript
      bonuses: filterBonuses(d.bonuses),
```

3d. Adicione as três funções de acessório logo após `validateArmorDraft`:

```javascript
  function serializeAccessory(d) {
    var kind = d.item_type === "boots" ? "boots" : "ring";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || (kind === "boots" ? "👢" : "💍"),
      item_type: kind, kind: kind, item_slot: kind, custom: true,
      bonuses: filterBonuses(d.bonuses),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (kind === "boots") {
      var mats = [];
      var mm = d.materiais || {};
      if (mm.organic) mats.push("organic");
      if (mm.metal) mats.push("metal");
      item.corrosion_materials = mats;
      item.corrosao_resistente = Math.max(0, +d.corrosao_livres || 0);
      item.corrosao_niveis_penalidade = Math.max(1, +d.corrosao_penalidade || 2);
    }
    return item;
  }
  function validateAccessoryDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    return { ok: true };
  }
  function suggestPriceAccessory(item) {
    var p = 0;
    (item.bonuses || []).forEach(function (b) { p += KA_BONUS * Math.abs(+b.value || 0); });
    return Math.max(1, Math.round(p));
  }
```

3e. Adicione os três ao objeto `api` (junto de `serializeArmor` etc.):

```javascript
              serializeAccessory: serializeAccessory,
              validateAccessoryDraft: validateAccessoryDraft,
              suggestPriceAccessory: suggestPriceAccessory,
```

- [ ] **Step 4: Rodar e ver passar (sem regressão nos casos de armadura)**

Run: `node tools/test_editor_items_logic.js`
Expected: PASS — todos verdes, incluindo os casos pré-existentes de arma/armadura (o `filterBonuses` extraído preserva o comportamento).

- [ ] **Step 5: Commit (arquivos de cliente — seguros)**

```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): lógica de acessórios (anel/bota) + atk_bonus no motor

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação de acessório

**Files:**
- Modify: `server.py` (`_ITEM_BONUS_EFFECTS` ~21216; `_validate_custom_item` ~21227; nova `_validate_custom_accessory`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione em `tools/test_editor_itens.py`, logo após `armor_sample` (ou junto das outras factories):

```python
def accessory_sample(**over):
    base = {"id": "anel_teste", "name": "Anel Teste", "emoji": "💍", "item_type": "ring",
            "bonuses": [{"effect": "maxhp", "value": 5}, {"effect": "atk_bonus", "value": 1}],
            "allowed_classes": [], "price": 30,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_acessorio():
    print("\n[E1] Validacao de anel/bota")
    ok, it = S._validate_custom_item(accessory_sample())
    check("aceita anel valido", ok)
    check("kind = ring", ok and it.get("kind") == "ring")
    check("item_slot = ring", ok and it.get("item_slot") == "ring")
    check("bonuses preservados (maxhp+atk_bonus)",
          ok and it.get("bonuses") == [{"effect": "maxhp", "value": 5}, {"effect": "atk_bonus", "value": 1}])
    check("anel nao tem corrosao", ok and "corrosion_materials" not in it)
    okb, itb = S._validate_custom_item(accessory_sample(id="botas_ferro", item_type="boots",
        emoji="👢", corrosion_materials=["metal"], corrosao_resistente=1,
        corrosao_niveis_penalidade=3, bonuses=[{"effect": "spd", "value": 1}]))
    check("aceita bota", okb and itb.get("kind") == "boots")
    check("bota item_slot = boots", okb and itb.get("item_slot") == "boots")
    check("bota mantem material e N/M", okb and itb.get("corrosion_materials") == ["metal"]
          and itb.get("corrosao_resistente") == 1 and itb.get("corrosao_niveis_penalidade") == 3)
    okr, _ = S._validate_custom_item(accessory_sample(id="ring_str"))
    check("rejeita id nativo (ring_str)", not okr)
    okt, _ = S._validate_custom_item(accessory_sample(item_type="colar"))
    check("rejeita item_type nao suportado", not okt)
    okf, itf = S._validate_custom_item(accessory_sample(bonuses=[{"effect": "atk", "value": 3}]))
    check("filtra efeito atk cru (usar atk_bonus)", okf and itf.get("bonuses") == [])
    oka, ita = S._validate_custom_item(accessory_sample(bonuses=[{"effect": "atk_bonus", "value": 2}]))
    check("aceita atk_bonus", oka and ita.get("bonuses") == [{"effect": "atk_bonus", "value": 2}])
```

E registre a chamada no bloco `if __name__ == "__main__":`, logo após `test_iniciativa_bonus()`:

```python
    test_validacao_acessorio()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL nos checks de `[E1]` (kind/item_slot ausentes; `_validate_custom_item` trata "ring"/"boots" como não suportado).

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione `"atk_bonus"` ao set `_ITEM_BONUS_EFFECTS` (linha ~21216):

```python
_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd", "atk_bonus", "str_", "dex", "con_", "int_", "resist", "initiative"}
```

3b. No `_validate_custom_item` (~21227), adicione o ramo de acessório antes do `return False`:

```python
    if it in ("ring", "boots"):
        return _validate_custom_accessory(raw)
    return False, "tipo de item não suportado"
```

3c. Adicione a nova função logo após `_validate_custom_armor`:

```python
def _validate_custom_accessory(raw):
    """Valida anel/bota custom (Fase E). Efeito só via o motor de multi-efeito (bonuses).
    Anel = slot ring1/ring2; bota = slot dedicado boots (corrói por corrosion_materials)."""
    kind = raw.get("item_type")   # "ring" | "boots"
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome do acessório"
    native = {i["id"] for i in SHOP_MERCHANT if not i.get("custom")}
    if iid in native:
        return False, "o id não pode substituir um item nativo"
    def _int0(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    bonuses = []
    for b in raw.get("bonuses", []) or []:
        if not (isinstance(b, dict) and b.get("effect") in _ITEM_BONUS_EFFECTS):
            continue
        if b.get("effect") == "resist":
            if b.get("type") not in _RESIST_TYPES:
                continue
            bonuses.append({"effect": "resist", "type": b["type"], "value": _int0(b.get("value"))})
        else:
            bonuses.append({"effect": b["effect"], "value": _int0(b.get("value"))})
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    item = {
        "id": iid, "name": name,
        "emoji": str(raw.get("emoji") or ("👢" if kind == "boots" else "💍"))[:8],
        "item_type": kind, "kind": kind, "item_slot": kind, "custom": True,
        "bonuses": bonuses,
        "granted_ability": (str(raw["granted_ability"]) if raw.get("granted_ability") else None),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    if kind == "boots":
        item["corrosion_materials"] = [m for m in (raw.get("corrosion_materials") or []) if m in _ITEM_MATERIAIS]
        item["corrosao_resistente"] = max(0, _int0(raw.get("corrosao_resistente")))
        item["corrosao_niveis_penalidade"] = max(1, _int0(raw.get("corrosao_niveis_penalidade", 2)))
    return True, item
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS em `[E1]` e nenhuma regressão nas seções anteriores. (Ignore falha pré-existente/flaky fora de `[E1]` se surgir — ver nota no fim.)

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Use a receita de partial staging. Hunks desta task: `_ITEM_BONUS_EFFECTS`, o ramo em `_validate_custom_item`, e a função `_validate_custom_accessory`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/server_all.patch
# montar /tmp/server_mine.patch só com os 3 hunks acima, então:
git apply --cached /tmp/server_mine.patch
git diff --cached -- server.py   # confirmar: só código de acessório
git commit -m "feat(itens): validação de acessórios (anel/bota) + atk_bonus

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — merge no mercador + efeitos/corrosão

**Files:**
- Modify: `server.py` (nova `_custom_accessory_inventory_dict`; `_apply_custom_items` ~21407)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicione em `tools/test_editor_itens.py` (após `test_validacao_acessorio`):

```python
def test_acessorio_equip_efeitos():
    print("\n[E2] Anel aplica/reverte efeitos do motor multi-efeito")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ok, it = S._validate_custom_item(accessory_sample())   # maxhp+5, atk_bonus+1
    inv = S._custom_accessory_inventory_dict(it)
    hp0, atk0 = p["max_hp"], p["atk_bonus"]
    r._apply_gear_effect(p, inv, True)
    check("equipar +5 PV máx", p["max_hp"] == hp0 + 5)
    check("equipar +1 acerto (atk_bonus)", p["atk_bonus"] == atk0 + 1)
    r._apply_gear_effect(p, inv, False)
    check("desequipar reverte PV", p["max_hp"] == hp0)
    check("desequipar reverte acerto", p["atk_bonus"] == atk0)

def test_acessorio_resist():
    print("\n[E3] Anel de resistência entra/sai de resistances")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ok, it = S._validate_custom_item(accessory_sample(id="anel_fogo",
        bonuses=[{"effect": "resist", "type": "fire", "value": 0}]))
    inv = S._custom_accessory_inventory_dict(it)
    r._apply_gear_effect(p, inv, True)
    check("resist fire adicionado", {"type": "fire", "mode": "half"} in p.get("resistances", []))
    r._apply_gear_effect(p, inv, False)
    check("resist fire removido", {"type": "fire", "mode": "half"} not in p.get("resistances", []))

def test_acessorio_botas_corrosao():
    print("\n[E4] Botas custom corroem por material (N/M)")
    S._apply_custom_items([S._validate_custom_item(accessory_sample(id="botas_metal",
        item_type="boots", emoji="👢", corrosion_materials=["metal"],
        corrosao_resistente=0, corrosao_niveis_penalidade=2,
        bonuses=[{"effect": "spd", "value": 1}]))[1]])
    r, p = _corr_setup()
    base = r._moves_base(p)
    p["gear"]["armor"] = None  # isola a corrosão nas botas
    p["gear"]["boots"] = {"id": "botas_metal", "name": "Botas de Metal",
                          "corrosion_materials": ["metal"],
                          "corrosao_resistente": 0, "corrosao_niveis_penalidade": 2}
    m = {"id": "d", "name": "Dev", "hp": 10, "max_hp": 10}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d4", "T"))
    check("botas corroídas (nível 1)", r._corr(p)["botas_lvl"] == 1)
    check("movimento cai 1 com botas corroídas", r._moves_base(p) == base - 1)
    S._apply_custom_items([])

def test_acessorio_merge():
    print("\n[E5] Merge de acessório no mercador/baús/loot")
    ok, it = S._validate_custom_item(accessory_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "anel_teste" for i in S.SHOP_MERCHANT))
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "anel_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "anel_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT intacto", any(i["id"] == "ring_str" for i in S.SHOP_MERCHANT))
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "anel_teste") == 1)
    check("reaplicar nao duplica em LOOT_POOL_PROCEDURAL",
          S.LOOT_POOL_PROCEDURAL.count("anel_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "anel_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "anel_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("lista vazia remove de LOOT_POOL_PROCEDURAL", "anel_teste" not in S.LOOT_POOL_PROCEDURAL)
    check("nativo SHOP_MERCHANT sobrevive ao clear", any(i["id"] == "ring_str" for i in S.SHOP_MERCHANT))
```

Registre no `if __name__ == "__main__":`, após `test_validacao_acessorio()`:

```python
    test_acessorio_equip_efeitos(); test_acessorio_resist()
    test_acessorio_botas_corrosao(); test_acessorio_merge()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL — `_custom_accessory_inventory_dict` não existe; acessório não entra em `SHOP_MERCHANT`.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione a nova função logo após `_custom_armor_inventory_dict`:

```python
def _custom_accessory_inventory_dict(item):
    """Anel/bota custom — dict único p/ loja (SHOP_MERCHANT) E bolsa/baú (como os
    anéis nativos). Efeito só via bonuses (sem effect/value escalar)."""
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": item["item_slot"], "kind": item["kind"], "custom": True,
           "price": item["price"], "bonuses": [dict(b) for b in item["bonuses"]],
           "granted_ability": item["granted_ability"]}
    if item["kind"] == "boots":
        inv["corrosion_materials"] = list(item.get("corrosion_materials", []))
        inv["corrosao_resistente"] = item.get("corrosao_resistente", 0)
        inv["corrosao_niveis_penalidade"] = item.get("corrosao_niveis_penalidade", 2)
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv
```

3b. Em `_apply_custom_items`, adicione a limpeza de acessório de `SHOP_MERCHANT` (os customs em `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL` já são limpos pelo bloco genérico `prev_custom_ids`). Coloque logo após a linha `SHOP_ARMORS[:] = [a for a in SHOP_ARMORS if not a.get("custom")]`:

```python
    # Acessórios custom (anel/bota) vivem no mercador — nenhum outro bloco limpa SHOP_MERCHANT.
    SHOP_MERCHANT[:] = [i for i in SHOP_MERCHANT if not i.get("custom")]
```

3c. No laço `for raw in records:`, adicione o ramo de acessório junto do ramo `if it in ("armor", "shield"):` (antes dele ou depois — antes do código de arma). Coloque logo após o `continue` do ramo de armadura:

```python
        if it in ("ring", "boots"):
            disp = item["disponibilidade"]
            inv = _custom_accessory_inventory_dict(item)
            if disp["loja"]:
                SHOP_MERCHANT.append(inv)
            if disp["baus"] or disp["loot_monstro"]:
                _DUNGEON_ITEM_CATALOG[item["id"]] = inv
            if disp["loot_monstro"]:
                LOOT_POOL_PROCEDURAL.append(item["id"])
            continue
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS em `[E2]`–`[E5]`, sem regressão nas seções anteriores.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks desta task: `_custom_accessory_inventory_dict` (nova), a linha de limpeza de `SHOP_MERCHANT` e o ramo `if it in ("ring","boots")` em `_apply_custom_items`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/server_all.patch
# montar /tmp/server_mine.patch só com os hunks acima, então:
git apply --cached /tmp/server_mine.patch
git diff --cached -- server.py   # confirmar: só código de acessório
git commit -m "feat(itens): merge de acessórios (anel/bota) no mercador

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Editor — destravar sub-abas Anéis + Botas

**Files:**
- Modify: `tools/editor_items_editor.js`

Sem teste headless (o editor não roda no MCP). Verificação: `node tools/test_editor_items_logic.js` continua verde e smoke test manual (Task 5 / follow-up do usuário). Cada passo mostra o código exato.

- [ ] **Step 1: Destravar as sub-abas na tabela `TYPES`**

Troque (linhas ~8-10):

```javascript
    ["aneis","Anéis",false],["botas","Botas",false],["pocoes","Poções",false],
```

por:

```javascript
    ["aneis","Anéis",true],["botas","Botas",true],["pocoes","Poções",false],
```

- [ ] **Step 2: Draft e roteamento de acessório**

2a. Adicione `novoDraftAccessory` logo após `novoDraftArmor`:

```javascript
  function novoDraftAccessory(kind) {
    return { name:"", emoji:(kind === "botas" ? "👢" : "💍"),
      item_type:(kind === "botas" ? "boots" : "ring"),
      bonuses:[], materiais:{organic:false, metal:true}, corrosao_livres:0, corrosao_penalidade:2,
      granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
```

2b. Em `novoDraftFor`, roteie os novos tipos:

```javascript
  function novoDraftFor(type) {
    if (type === "armaduras" || type === "escudos") return novoDraftArmor(type);
    if (type === "aneis" || type === "botas") return novoDraftAccessory(type);
    return novoDraft();
  }
```

- [ ] **Step 3: Despacho em `renderForm`**

No início de `renderForm`, após a checagem de armadura/escudo, adicione:

```javascript
    if (activeType === "aneis" || activeType === "botas") {
      renderAccessoryForm(f, activeType === "botas" ? "boots" : "ring");
      return;
    }
```

- [ ] **Step 4: Template de bônus compartilhado (com atk_bonus)**

4a. Adicione a função `abonusTemplate` (perto de `seccao`/`campo`):

```javascript
  function abonusTemplate() {
    return '<template id="ie-abonus-tpl"><span class="ie-elem-row">' +
      '<select class="ie-abonus-eff"><option value="def_">CA extra</option>' +
      '<option value="maxhp">PV máx</option><option value="spd">Velocidade</option>' +
      '<option value="atk_bonus">Bônus de acerto</option>' +
      '<option value="str_">Força</option><option value="dex">Destreza</option>' +
      '<option value="con_">Constituição</option><option value="int_">Inteligência</option>' +
      '<option value="initiative">Iniciativa</option>' +
      '<option value="resist">Resistência</option></select> ' +
      '<select class="ie-abonus-type" style="display:none"><option value="physical">Físico</option>' +
      '<option value="fire">Fogo</option><option value="cold">Frio</option><option value="lightning">Elétrico</option>' +
      '<option value="acid">Ácido</option><option value="holy">Sagrado</option><option value="poison">Veneno</option>' +
      '<option value="magic">Mágico</option><option value="water">Água</option></select> ' +
      numInput("", 0, -10, 20) + ' <button class="ie-abonus-del">✕</button></span></template>';
  }
```

4b. Em `renderArmorForm`, troque o bloco literal do `<template id="ie-abonus-tpl">...</template>` (dentro da `seccao("Bônus adicionais", ...)`) por `abonusTemplate()`. O corpo da seção passa a ser:

```javascript
      seccao("Bônus adicionais",
        '<div id="ie-abonus"></div><button id="ie-add-abonus">+ bônus</button>' +
        abonusTemplate()),
```

- [ ] **Step 5: Preview de acessório usa `previewFn` (para os bônus dinâmicos)**

`addArmorBonusRow` liga os eventos de linha a `renderArmorPreview`, que lê campos de armadura inexistentes num acessório. Torne o preview roteável por um ponteiro de módulo.

5a. Declare no topo do IIFE (perto de `var activeType`):

```javascript
  var previewFn = function () {};
```

5b. Em `addArmorBonusRow`, troque as duas referências a `renderArmorPreview` por `previewFn`:

```javascript
    node.querySelector(".ie-abonus-del").onclick = function () { node.remove(); previewFn(); };
    node.querySelectorAll("input,select").forEach(function (el) { el.onchange = previewFn; });
```

5c. Em `renderArmorForm`, logo antes de `bindArmorForm();`, fixe o ponteiro:

```javascript
    previewFn = renderArmorPreview;
```

- [ ] **Step 6: Formulário, leitura, preview, bind e save de acessório**

Adicione estas funções (perto de `renderArmorForm`/`renderArmorPreview`):

```javascript
  function renderAccessoryForm(f, kind) {
    var isBoots = kind === "boots";
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Bônus (motor de efeitos)",
        '<div id="ie-abonus"></div><button id="ie-add-abonus">+ bônus</button>' +
        abonusTemplate()),
      isBoots ? seccao("Durabilidade (corrosão)",
        campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
        campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-organic"' + (draft.materiais.organic ? " checked" : "") + '> Orgânico (Devorador Orgânico)</label>' +
        '<label class="ie-field"><input type="checkbox" id="ie-mat-metal"' + (draft.materiais.metal ? " checked" : "") + '> Metal (Devorador de Metal)</label>' +
        '<span class="ie-hint">Sem material marcado, a peça não corrói. Quebra em N+M+1.</span>') : "",
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
      '<div class="ie-actions"><button id="ie-save">💾 Salvar ' + (isBoots ? "botas" : "anel") + '</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderAccessoryPreview;
    bindAccessoryForm();
    renderArmorBonuses();          // popula #ie-abonus a partir de draft.bonuses (genérico)
    renderAccessoryPreview();
  }

  function currentAccessoryDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.bonuses = Array.prototype.map.call(root.querySelectorAll("#ie-abonus .ie-elem-row"), function (r) {
      var eff = r.querySelector(".ie-abonus-eff").value;
      var o = { effect: eff, value: +r.querySelector("input[type=number]").value || 0 };
      if (eff === "resist") { var t = r.querySelector(".ie-abonus-type"); o.type = t ? t.value : "fire"; }
      return o; });
    if (draft.item_type === "boots") {
      draft.corrosao_livres = Math.max(0, +g("ie-corrlivre").value || 0);
      draft.corrosao_penalidade = Math.max(1, +g("ie-corrpen").value || 2);
      draft.materiais = { organic: g("ie-mat-organic").checked, metal: g("ie-mat-metal").checked };
    }
    return draft;
  }

  function renderAccessoryPreview() {
    currentAccessoryDraftFromForm();
    var item = L.serializeAccessory(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPriceAccessory(item) + " 🪙";
    var LBL = { def_:"CA", maxhp:"PV máx", spd:"velocidade", atk_bonus:"acerto",
      str_:"Força", dex:"Destreza", con_:"CON", int_:"INT", initiative:"iniciativa" };
    var parts = [];
    (item.bonuses || []).forEach(function (b) {
      var lbl = b.effect === "resist" ? ("resist " + (b.type || "")) : (LBL[b.effect] || b.effect);
      parts.push((b.value >= 0 ? "+" : "") + b.value + " " + lbl);
    });
    if (item.corrosion_materials) {
      var matsLabel = item.corrosion_materials.length ? item.corrosion_materials.join("+") : "nenhum";
      parts.push("🛡️ corrosão " + (item.corrosao_resistente || 0) + "+" + (item.corrosao_niveis_penalidade || 2) + " (" + matsLabel + ")");
    }
    if (!parts.length) parts.push("(sem bônus)");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindAccessoryForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderAccessoryPreview; el.oninput = renderAccessoryPreview;
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-abonus").onclick = function () { addArmorBonusRow(null); renderAccessoryPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderAccessoryPreview();
    };
    root.querySelector("#ie-save").onclick = onSaveAccessory;
  }

  async function onSaveAccessory() {
    currentAccessoryDraftFromForm();
    var v = L.validateAccessoryDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeAccessory(draft);
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

- [ ] **Step 7: Sanidade estática + commit**

Verifique que o arquivo não tem erro de sintaxe (parse rápido via Node):

Run: `node -e "require('fs').readFileSync('tools/editor_items_editor.js','utf8'); new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('parse OK')"`
Expected: `parse OK` (o corpo referencia `document`, mas `new Function` só faz o parse, não executa).

Run: `node tools/test_editor_items_logic.js`
Expected: PASS (sem regressão).

```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor destrava sub-abas Anéis + Botas

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória em `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\`

- [ ] **Step 1: Rodar a suíte completa no estado COMMITADO isolado**

O working tree roda com o WIP do usuário; verifique o estado committado num worktree limpo:

```bash
git worktree add --detach /tmp/lfh_verify HEAD
cd /tmp/lfh_verify
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify
```

Expected: `[E1]`–`[E5]` verdes e node verde. Falhas pré-existentes que **não** são regressão desta fase: `tools/test_roteamento_itens.py` (por `health_potion`, WIP do usuário conserta), `tools/test_devorador.py` (1 teste flaky de rolagem). Confirme que nenhuma seção anterior de `test_editor_itens.py` quebrou.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase D (final do arquivo), resumindo a Fase E: sub-abas Anéis/Botas, motor multi-efeito reusado, `atk_bonus` novo, merge no `SHOP_MERCHANT`, botas corroem só via `corrosion_materials` (sem tocar nos sets de metal dos monstros), anéis sem corrosão. Cite os arquivos e o teste `[E1]`–`[E5]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-22-editor-itens-fase-e-aneis-botas.md
git commit -m "docs(itens): registra o Editor de Itens — Fase E (anéis + botas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/editor-itens-fase-e-aneis-botas.md` (tipo `project`) resumindo o que foi feito, o estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), quantos checks passaram e o follow-up de smoke in-app. Adicione a linha-índice em `MEMORY.md`. Atualize a linha da Fase D se necessário para apontar a Fase E como próxima concluída.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app (o editor não roda headless): `python server.py` → `tools/editor.html` → aba "Editor de itens" → sub-aba Anéis: criar anel com PV+acerto+resistência, salvar; sub-aba Botas: criar botas com velocidade+iniciativa+corrosão metal, salvar. Em jogo: comprar no mercador, equipar nos slots Anel 1/Bota/Anel 2, conferir efeitos e (botas) corrosão pelo Devorador.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** atk_bonus (T1/T2/T4) ✓; `_validate_custom_accessory` (T2) ✓; `_custom_accessory_inventory_dict` + merge SHOP_MERCHANT/catálogo/loot (T3) ✓; botas corroem via material sem tocar sets de metal (T3, testado em E4) ✓; serializeAccessory/validate/suggestPrice (T1) ✓; UI sub-abas + form parametrizado + corrosão só botas + rótulo "Loja (Mercador)" (T4) ✓; testes servidor [E1]–[E5] + node (T1/T2/T3) ✓; verificação isolada + docs + memória (T5) ✓.
- **atk vs atk_bonus:** só `atk_bonus` é adicionado; `{"effect":"atk"}` continua filtrado — os checks pré-existentes ([A1] servidor e node armor) permanecem verdes.
- **Consistência de tipos:** `serializeAccessory`/`validateAccessoryDraft`/`suggestPriceAccessory` (T1) casam com as chamadas em T4; `_custom_accessory_inventory_dict` (T3) casa com as chamadas em T3-tests; `previewFn` (T4) declarado antes do uso em `addArmorBonusRow`.
- **Sem placeholders:** todos os passos têm código/comando concreto.
