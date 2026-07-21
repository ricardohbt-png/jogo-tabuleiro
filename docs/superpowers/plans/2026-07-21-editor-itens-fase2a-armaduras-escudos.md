# Editor de Itens — Fase 2a: Armaduras + Escudos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Habilitar as sub-abas Armaduras e Escudos no Editor de Itens, criando peças de defesa custom (CA + PV/velocidade via multi-efeito, material/corrosão N/M generalizada para os slots de defesa, disponibilidade, metadados) que funcionam no jogo.

**Architecture:** Generaliza a infra de itens custom da Fase 1 (validação/merge por `item_type`), adiciona um motor de multi-efeito (`bonuses`) na pipeline de equipar, e generaliza a corrosão de "só armadura de corpo + arma" para os slots de defesa (armadura/escudo/arma/elmo/botas) com o modelo N/M das armas, mantendo peças base byte-idênticas.

**Tech Stack:** Python (`server.py`), JS vanilla (`tools/editor_*`), testes `tools/test_editor_itens.py` (Python) + `tools/test_editor_items_logic.js` (Node).

**IMPORTANTE (WIP em paralelo):** o usuário edita outros arquivos ao mesmo tempo. Ancore edições pelo CÓDIGO ao redor, não por número de linha. `git add` SÓ os arquivos nomeados em cada commit; NUNCA `git add -A`. Rode testes da raiz.

**Spec:** `docs/superpowers/specs/2026-07-21-editor-itens-fase2a-armaduras-escudos-design.md`

---

## Contrato de dados — registro de armadura/escudo

```json
{
  "id": "cota_encantada", "name": "Cota Encantada", "emoji": "🛡️",
  "item_type": "armor", "custom": true, "kind": "armor",
  "ac_bonus": 4,
  "armor_category": "media",
  "corrosion_materials": ["metal"],
  "corrosao_resistente": 0,
  "corrosao_niveis_penalidade": 2,
  "bonuses": [{"effect": "maxhp", "value": 5}, {"effect": "spd", "value": -1}],
  "granted_ability": null,
  "allowed_classes": ["warrior", "paladin"],
  "price": 120,
  "disponibilidade": {"loja": true, "baus": false, "loot_monstro": false}
}
```
Escudo: `item_type:"shield"`, sem `armor_category` (zerado); tem `corrosion_materials`+N/M.

---

## Task 1: Servidor — validação por item_type (armadura/escudo)

**Files:** Modify `server.py` (funções `_validate_custom_item` e vizinhas, criadas na Fase 1); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_itens.py` (antes de `if __name__`):

```python
def armor_sample(**over):
    base = {"id": "cota_teste", "name": "Cota Teste", "emoji": "🛡️", "item_type": "armor",
            "ac_bonus": 4, "armor_category": "media", "corrosion_materials": ["metal"],
            "corrosao_resistente": 0, "corrosao_niveis_penalidade": 2,
            "bonuses": [{"effect": "maxhp", "value": 5}], "allowed_classes": ["warrior"],
            "price": 120, "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_armadura():
    print("\n[A1] Validacao de armadura/escudo")
    ok, it = S._validate_custom_item(armor_sample())
    check("aceita armadura valida", ok)
    check("kind = armor", ok and it.get("kind") == "armor")
    check("ac_bonus preservado", ok and it.get("ac_bonus") == 4)
    check("categoria preservada", ok and it.get("armor_category") == "media")
    check("materiais preservados", ok and it.get("corrosion_materials") == ["metal"])
    check("N/M preservados", ok and it.get("corrosao_resistente") == 0 and it.get("corrosao_niveis_penalidade") == 2)
    check("bonuses preservados", ok and it.get("bonuses") == [{"effect": "maxhp", "value": 5}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="esc_teste", item_type="shield",
        armor_category="media", corrosion_materials=["metal"]))
    check("aceita escudo", ok2 and it2.get("kind") == "shield")
    check("escudo zera categoria", ok2 and it2.get("armor_category") is None)
    check("escudo mantem material", ok2 and it2.get("corrosion_materials") == ["metal"])
    ok3, _ = S._validate_custom_item(armor_sample(armor_category="ultra"))
    check("rejeita categoria invalida", not ok3)
    ok4, it4 = S._validate_custom_item(armor_sample(corrosion_materials=["metal", "trevas"]))
    check("filtra material desconhecido", ok4 and it4.get("corrosion_materials") == ["metal"])
    ok5, it5 = S._validate_custom_item(armor_sample(bonuses=[{"effect": "atk", "value": 3}]))
    check("filtra efeito nao permitido em bonuses", ok5 and it5.get("bonuses") == [])
    # arma continua validando (regressao)
    okw, _ = S._validate_custom_item(sample())
    check("arma ainda valida", okw)
```

E chame `test_validacao_armadura()` no bloco `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_editor_itens.py` → FAIL (armadura rejeitada: hoje `_validate_custom_item` só aceita weapon).

- [ ] **Step 3: Implementar** — Localize `def _validate_custom_item(raw):` em `server.py`. **Renomeie o corpo atual** para `_validate_custom_weapon(raw)` (o conteúdo que valida `item_type=="weapon"` — mantenha idêntico, só o nome muda) e crie um novo despachante + a validação de armadura:

```python
_ITEM_ARMOR_CATS = {"leve", "media", "pesada"}
_ITEM_MATERIAIS = {"organic", "metal"}
_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd"}

def _validate_custom_item(raw):
    """Despacha por item_type: weapon | armor | shield."""
    if not isinstance(raw, dict):
        return False, "ficha inválida"
    it = raw.get("item_type", "weapon")
    if it == "weapon":
        return _validate_custom_weapon(raw)
    if it in ("armor", "shield"):
        return _validate_custom_armor(raw)
    return False, "tipo de item não suportado"

def _validate_custom_armor(raw):
    """Valida armadura/escudo custom (Fase 2a)."""
    kind = raw.get("item_type")
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome da peça"
    native = {a["id"] for a in SHOP_ARMORS if not a.get("custom")}
    if iid in native:
        return False, "o id não pode substituir uma peça nativa"
    def _int0(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    ac_bonus = max(0, _int0(raw.get("ac_bonus")))
    cat = raw.get("armor_category")
    if kind == "shield":
        cat = None
    elif cat not in _ITEM_ARMOR_CATS:
        if cat not in (None, ""):
            return False, "categoria de armadura inválida"
        cat = None
    materiais = [m for m in (raw.get("corrosion_materials") or []) if m in _ITEM_MATERIAIS]
    bonuses = []
    for b in raw.get("bonuses", []) or []:
        if isinstance(b, dict) and b.get("effect") in _ITEM_BONUS_EFFECTS:
            bonuses.append({"effect": b["effect"], "value": _int0(b.get("value"))})
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    item = {
        "id": iid, "name": name, "emoji": str(raw.get("emoji") or "🛡️")[:8],
        "item_type": kind, "kind": kind, "custom": True,
        "ac_bonus": ac_bonus, "armor_category": cat,
        "corrosion_materials": materiais,
        "corrosao_resistente": max(0, _int0(raw.get("corrosao_resistente"))),
        "corrosao_niveis_penalidade": max(1, _int0(raw.get("corrosao_niveis_penalidade", 2))),
        "bonuses": bonuses,
        "granted_ability": (str(raw["granted_ability"]) if raw.get("granted_ability") else None),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    return True, item
```
`_ITEM_CLASSES` já existe (Fase 1). `SHOP_ARMORS` já existe.

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS (inclui [A1]).

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): validação de armadura/escudo custom (despacho por item_type)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — merge de armadura/escudo nos catálogos

**Files:** Modify `server.py` (`_apply_custom_items` e helpers); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def test_merge_armadura():
    print("\n[A2] Merge de armadura/escudo")
    arm = S._validate_custom_item(armor_sample(id="cota_m", corrosion_materials=["metal"]))[1]
    org = S._validate_custom_item(armor_sample(id="couro_o", corrosion_materials=["organic"]))[1]
    esc = S._validate_custom_item(armor_sample(id="esc_m", item_type="shield", corrosion_materials=["metal"]))[1]
    S._apply_custom_items([arm, org, esc])
    check("armadura entra em SHOP_ARMORS", any(a["id"] == "cota_m" for a in S.SHOP_ARMORS))
    check("escudo entra em SHOP_ARMORS", any(a["id"] == "esc_m" for a in S.SHOP_ARMORS))
    check("SHOP_ARMORS carrega ac_bonus", next(a for a in S.SHOP_ARMORS if a["id"] == "cota_m")["ac_bonus"] == 4)
    check("metal armadura -> CORROSAO_ARMADURA_METAL", "cota_m" in S.CORROSAO_ARMADURA_METAL)
    check("organic armadura -> CORROSAO_ARMADURA_ORGANICA", "couro_o" in S.CORROSAO_ARMADURA_ORGANICA)
    check("escudo metal -> CORROSAO_ARMADURA_METAL", "esc_m" in S.CORROSAO_ARMADURA_METAL)
    # disponibilidade baus/loot em armadura
    arm2 = S._validate_custom_item(armor_sample(id="cota_bau",
        disponibilidade={"loja": False, "baus": True, "loot_monstro": True}))[1]
    S._apply_custom_items([arm, org, esc, arm2])
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "cota_bau" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "cota_bau" in S.LOOT_POOL_PROCEDURAL)
    check("catalogo de baus e equipavel (item_slot armor + effect def_)",
          S._DUNGEON_ITEM_CATALOG["cota_bau"].get("item_slot") == "armor"
          and S._DUNGEON_ITEM_CATALOG["cota_bau"].get("effect") == "def_")
    # cleanup idempotente
    S._apply_custom_items([])
    check("cleanup remove de SHOP_ARMORS", not any(a.get("custom") for a in S.SHOP_ARMORS))
    check("cleanup remove de CORROSAO_ARMADURA_METAL", "cota_m" not in S.CORROSAO_ARMADURA_METAL)
    check("cleanup remove de CORROSAO_ARMADURA_ORGANICA", "couro_o" not in S.CORROSAO_ARMADURA_ORGANICA)
    check("base leather intacto em SHOP_ARMORS", any(a["id"] == "leather" for a in S.SHOP_ARMORS))
    check("base leather intacto em CORROSAO_ARMADURA_ORGANICA", "leather" in S.CORROSAO_ARMADURA_ORGANICA)
```

E chame `test_merge_armadura()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (armadura não entra em SHOP_ARMORS; `_apply_custom_items` só trata weapon).

- [ ] **Step 3: Implementar** — Adicione helpers perto de `_custom_weapon_inventory_dict` (server.py):

```python
def _custom_armor_shop_dict(item):
    """Entrada de SHOP_ARMORS para uma peça custom."""
    out = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "ac_bonus": item["ac_bonus"], "kind": item["kind"], "price": item["price"],
           "corrosion_materials": list(item["corrosion_materials"]),
           "corrosao_resistente": item["corrosao_resistente"],
           "corrosao_niveis_penalidade": item["corrosao_niveis_penalidade"],
           "bonuses": [dict(b) for b in item["bonuses"]],
           "granted_ability": item["granted_ability"], "custom": True}
    if item["kind"] == "armor" and item.get("armor_category"):
        out["armor_category"] = item["armor_category"]
    if item["allowed_classes"]:
        out["allowed_classes"] = list(item["allowed_classes"])
    return out

def _custom_armor_inventory_dict(item):
    """Peça equipável (baús/loot) — vai pra bolsa e equipa via effect def_."""
    slot = "shield" if item["kind"] == "shield" else "armor"
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": slot, "effect": "def_", "value": item["ac_bonus"],
           "kind": item["kind"], "custom": True, "price": item["price"],
           "corrosion_materials": list(item["corrosion_materials"]),
           "corrosao_resistente": item["corrosao_resistente"],
           "corrosao_niveis_penalidade": item["corrosao_niveis_penalidade"],
           "bonuses": [dict(b) for b in item["bonuses"]],
           "granted_ability": item["granted_ability"]}
    if item["kind"] == "armor" and item.get("armor_category"):
        inv["armor_category"] = item["armor_category"]
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv
```

Em `_apply_custom_items(records)`, no bloco de **limpeza** (onde já limpa WEAPONS/SHOP_WEAPONS/RANGED_AMMO/sets de arma), adicione a limpeza idempotente de defesa ANTES do laço de add. Os ids custom de defesa são derivados de `SHOP_ARMORS` (por `custom`) e do `_DUNGEON_ITEM_CATALOG` (por `custom` + `kind`):

```python
    # Peças de defesa custom: limpar SHOP_ARMORS, catálogo de baús e sets de corrosão.
    prev_def_ids = {a["id"] for a in SHOP_ARMORS if a.get("custom")}
    prev_def_ids |= {k for k, v in _DUNGEON_ITEM_CATALOG.items()
                     if v.get("custom") and v.get("kind") in ("armor", "shield")}
    SHOP_ARMORS[:] = [a for a in SHOP_ARMORS if not a.get("custom")]
    for k in prev_def_ids:
        CORROSAO_ARMADURA_METAL.discard(k)
        CORROSAO_ARMADURA_ORGANICA.discard(k)
        _DUNGEON_ITEM_CATALOG.pop(k, None)
    LOOT_POOL_PROCEDURAL[:] = [i for i in LOOT_POOL_PROCEDURAL if i not in prev_def_ids]
```
O `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL` de ARMAS já são limpos via `prev_custom_ids` (weapon) no código da Fase 1; os ids de defesa são disjuntos, então as duas limpezas coexistem.

No **laço de add** de `_apply_custom_items`, no início do corpo do `for raw in records:`, troque a validação de tipo para aceitar defesa e roteie:

```python
    for raw in records:
        if not isinstance(raw, dict):
            continue
        it = raw.get("item_type", "weapon")
        ok, item = _validate_custom_item(raw)
        if not ok:
            continue
        if it in ("armor", "shield"):
            disp = item["disponibilidade"]
            if disp["loja"]:
                SHOP_ARMORS.append(_custom_armor_shop_dict(item))
            inv = _custom_armor_inventory_dict(item)
            if disp["baus"] or disp["loot_monstro"]:
                _DUNGEON_ITEM_CATALOG[item["id"]] = inv
            if disp["loot_monstro"]:
                LOOT_POOL_PROCEDURAL.append(item["id"])
            mats = item["corrosion_materials"]
            if "metal" in mats:   CORROSAO_ARMADURA_METAL.add(item["id"])
            if "organic" in mats: CORROSAO_ARMADURA_ORGANICA.add(item["id"])
            continue
        # ... (bloco existente de weapon segue aqui inalterado) ...
```
(O bloco `WEAPONS[item["id"]] = _custom_weapon_combat_dict(item)` etc. da Fase 1 fica logo abaixo, para `it == "weapon"`.)

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS. Rode também `python tools/test_roteamento_itens.py` (deve seguir verde).

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): merge de armadura/escudo (SHOP_ARMORS, baús, loot, sets de corrosão)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — motor de multi-efeito (`bonuses`)

**Files:** Modify `server.py` (`_apply_gear_effect`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def test_multi_efeito():
    print("\n[A3] Motor de multi-efeito (bonuses)")
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    hp0, spd0, ac0 = p["max_hp"], p["spd"], p["ac"]
    item = {"id": "x", "name": "X", "item_slot": "armor", "effect": "def_", "value": 3,
            "bonuses": [{"effect": "maxhp", "value": 5}, {"effect": "spd", "value": -1},
                        {"effect": "def_", "value": 1}]}
    r._apply_gear_effect(p, item, True)
    check("def_ primario aplicado (+3 CA)", p["ac"] == ac0 + 3 + 1)  # primario +3, bonus +1
    check("maxhp bonus aplicado (+5)", p["max_hp"] == hp0 + 5)
    check("spd bonus aplicado (-1)", p["spd"] == spd0 - 1)
    r._apply_gear_effect(p, item, False)
    check("desequipar reverte CA", p["ac"] == ac0)
    check("desequipar reverte maxhp", p["max_hp"] == hp0)
    check("desequipar reverte spd", p["spd"] == spd0)
```

Chame `test_multi_efeito()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (bonuses ignorados; só o efeito primário aplica).

- [ ] **Step 3: Implementar** — Localize `def _apply_gear_effect(self, p, item, equipping):`. **Extraia** o corpo (o `if/elif` de efeitos) para `_apply_single_effect(self, p, effect, value)` e faça `_apply_gear_effect` chamar o primário + cada bônus:

```python
    def _apply_single_effect(self, p, effect, value, equipping):
        e, v = effect, value * (1 if equipping else -1)
        if e in ("atk", "atk_bonus"):
            p["atk_bonus"] += v; p["base_atk_bonus"] += v
        elif e in ("def_", "ac_bonus"):
            p["ac"] += v
            p["ac_base"] = p.get("ac_base", 10) + v
        elif e == "maxhp":
            p["max_hp"] += v
            if equipping and not p.get("ultimo_esforco_ativo"):
                p["hp"] = min(p["max_hp"], p["hp"] + v)
        elif e == "spd":
            p["spd"] += v
        elif e == "bagslots":
            p["bag_size"] = max(1, p.get("bag_size", 6) + v)

    def _apply_gear_effect(self, p, item, equipping):
        self._apply_single_effect(p, item.get("effect"), item.get("value", 0), equipping)
        for b in item.get("bonuses", []) or []:
            if isinstance(b, dict):
                self._apply_single_effect(p, b.get("effect"), int(b.get("value", 0) or 0), equipping)
```
(O corpo de `_apply_single_effect` é **idêntico** ao antigo `_apply_gear_effect`, só recebe `effect`/`value` como parâmetros em vez de lê-los do item.)

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS. Rode `python tools/test_roteamento_itens.py` (verde — itens sem `bonuses` têm laço vazio, comportamento idêntico).

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): motor de multi-efeito (lista bonuses) no equipar/desequipar

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Servidor — compra/equipar preservam campos de defesa

**Files:** Modify `server.py` (ramo `ferreiro_armor` de `handle_shop_buy`; sync de `p["gear"]`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def test_compra_armadura():
    print("\n[A4] Comprar armadura custom preserva campos")
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="cota_cmp",
        corrosion_materials=["metal"], bonuses=[{"effect": "maxhp", "value": 5}]))[1]])
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True; r.phase = "city"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["gold"] = 9999; p["bag"] = []; p["gear"]["armor"] = None
    asyncio.run(r.handle_shop_buy("p1", "ferreiro_armor", "cota_cmp"))
    comprada = next((it for it in p["bag"] if it and it.get("id") == "cota_cmp"), None)
    check("armadura foi pra bolsa", comprada is not None)
    check("bolsa preserva bonuses", comprada and comprada.get("bonuses"))
    check("bolsa preserva material", comprada and comprada.get("corrosion_materials") == ["metal"])
    check("bolsa preserva N/M", comprada and comprada.get("corrosao_niveis_penalidade") == 2)
    S._apply_custom_items([])
```

Chame `test_compra_armadura()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (o `gear_item` de `ferreiro_armor` não copia `bonuses`/materiais/N/M).

- [ ] **Step 3: Implementar** — No ramo `elif shop == "ferreiro_armor":` de `handle_shop_buy`, localize a construção de `gear_item`:

```python
            gear_item = {
                "id": item_id, "name": item["name"],
                "emoji": item.get("emoji", "🛡️"),
                "item_slot": slot_disp, "effect": "def_", "value": ac_bonus,
                "buy_price": price,
            }
            if kind == "armor":
                gear_item["armor_category"] = item.get("armor_category")
                gear_item["corrosion_materials"] = list(item.get("corrosion_materials", []))
```
Adicione (após o bloco `if kind == "armor":`), copiando os campos custom quando presentes:

```python
            for _k in ("corrosion_materials", "corrosao_resistente", "corrosao_niveis_penalidade",
                       "bonuses", "granted_ability", "kind"):
                if _k in item and _k not in gear_item:
                    gear_item[_k] = deepcopy(item[_k])
```
(`deepcopy` já está importado no server.) Isso garante que escudo (que não entra no `if kind=="armor"`) também leve materiais/N/M, e que a armadura leve bonuses/N/M.

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS.

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): compra de armadura/escudo preserva material/N-M/bonuses

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Servidor — corrosão generalizada (armadura N/M + escudo + prioridade)

Generaliza `_corr`, `_corroer_equipamento` e `_corrosao_ca_pen` para incluir o **escudo** e o modelo **N/M**, mantendo a armadura de corpo byte-idêntica.

**Files:** Modify `server.py` (`_corr`, `_corroer_equipamento`, `_corrosao_ca_pen`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def _corr_setup():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r._devorador_cura = noop
    p = S.make_player("p1", "Victor", "warrior", 0)
    return r, p

def test_corrosao_armadura_nm():
    print("\n[A5] Corrosão de armadura byte-idêntica + escudo + prioridade")
    # (a) armadura base (leather, sem N/M) mantém comportamento: quebra no 3º nível
    r, p = _corr_setup()
    p["gear"]["armor"] = {"id": "leather", "name": "Couro"}
    m = {"id": "d", "name": "Devorador", "hp": 10, "max_hp": 10}
    for _ in range(2):
        asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("armadura viva após 2 níveis", p["gear"]["armor"] is not None)
    check("penalidade de CA = 2 no nível 2", r._corrosao_ca_pen(p) == 2)
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("armadura destruída no 3º nível", p["gear"]["armor"] is None)
    # (b) escudo custom com material metal corrói e quebra em N+M+1 (N=1,M=2 → 4)
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="esc_c", item_type="shield",
        corrosion_materials=["metal"], corrosao_resistente=1, corrosao_niveis_penalidade=2))[1]])
    r, p = _corr_setup()
    p["gear"]["off_hand"] = deepcopy(S._DUNGEON_ITEM_CATALOG.get("esc_c") or
        next(a for a in S.SHOP_ARMORS if a["id"] == "esc_c"))
    for _ in range(3):
        asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("escudo vivo após 3 níveis (N=1,M=2)", p["gear"]["off_hand"] is not None)
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("escudo destruído no 4º nível", p["gear"]["off_hand"] is None)
    # (c) prioridade: armadura (metal) corrói antes do escudo
    r, p = _corr_setup()
    p["gear"]["armor"] = {"id": "chainmail", "name": "Cota"}
    p["gear"]["off_hand"] = {"id": "esc_c", "name": "Esc", "kind": "shield",
                             "corrosion_materials": ["metal"]}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_METAL, S.CORROSAO_ARMA_METAL, "1d6", "M"))
    check("prioridade: armadura corroída antes do escudo", r._corr(p)["armadura_lvl"] == 1 and r._corr(p).get("escudo_lvl", 0) == 0)
    S._apply_custom_items([])
```

Chame `test_corrosao_armadura_nm()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (escudo não corrói; `_corr` não tem `escudo_lvl`; `_corroer_equipamento` só vê armor/weapon).

- [ ] **Step 3: Implementar `_corr`** — Em `def _corr(self, p):`, adicione as trilhas novas junto das existentes:

```python
        c.setdefault("escudo_lvl", 0); c.setdefault("escudo_destruido", False)
        c.setdefault("elmo_lvl", 0);   c.setdefault("elmo_destruido", False)
        c.setdefault("botas_lvl", 0);  c.setdefault("botas_destruido", False)
```

- [ ] **Step 4: Implementar helper de corrodibilidade e N/M** — Adicione perto de `_corroer_equipamento`:

```python
    @staticmethod
    def _peca_corroivel(piece, ids_slot, materiais_devorador):
        """Uma peça corrói se o id está no set nativo do devorador OU se declara um
        material compatível (peça custom). `materiais_devorador`: {'metal'} ou {'organic'}."""
        if not piece:
            return False
        if piece.get("id") in ids_slot:
            return True
        return bool(set(piece.get("corrosion_materials", [])) & materiais_devorador)

    @staticmethod
    def _corrosao_nm_quebra(piece, lvl):
        """(quebrou?, nivel_penalidade) para o modelo N/M. Base sem N/M → N=0,M=2."""
        extra = int(piece.get("corrosao_resistente", 0) or 0)
        pen = int(piece.get("corrosao_niveis_penalidade", 2) or 2)
        if lvl >= extra + pen + 1:
            return True, 0
        return False, max(0, min(lvl - extra, pen))
```

- [ ] **Step 5: Reescrever `_corroer_equipamento`** — Substitua a assinatura para receber os sets de defesa por slot e generalize a prioridade. A assinatura atual é `(self, m, p, armaduras_ids, armas_ids, cura, label)`. **Mantenha-a** (os dois Devoradores já a chamam assim) e derive o material do devorador a partir de qual set foi passado:

```python
    async def _corroer_equipamento(self, m, p, armaduras_ids, armas_ids, cura="1d4", label="Corrosão"):
        """Degrada UMA peça na prioridade armadura → escudo → arma → elmo → botas.
        `armaduras_ids`/`armas_ids` são os sets nativos do devorador (metal ou orgânico);
        peças custom corroem por corrosion_materials. Destruição é permanente e cura o devorador."""
        c = self._corr(p)
        # material do devorador inferido pelo set nativo recebido
        material = "metal" if armaduras_ids is CORROSAO_ARMADURA_METAL else "organic"
        mats = {material}
        gear = p["gear"]
        alvos = [
            ("armor",    "armadura", armaduras_ids, "def_"),
            ("off_hand", "escudo",   armaduras_ids, "def_"),
            ("weapon",   "arma",     armas_ids,     "weapon"),
            ("head",     "elmo",     armaduras_ids, "def_"),
            ("boots",    "botas",    armaduras_ids, "def_"),
        ]
        for slot, pref, ids_slot, tipo in alvos:
            peca = p.get("weapon") if slot == "weapon" else gear.get(slot)
            # escudo só conta se for realmente escudo (off_hand pode ter arma/instrumento)
            if slot == "off_hand" and not (peca and (peca.get("kind") == "shield" or peca.get("item_slot") == "shield")):
                continue
            if c.get(f"{pref}_destruido"):
                continue
            if not self._peca_corroivel(peca, ids_slot, mats):
                continue
            c[f"{pref}_lvl"] = c.get(f"{pref}_lvl", 0) + 1
            lvl = c[f"{pref}_lvl"]
            if slot == "armor":
                c["armadura_com_ca"] = (peca.get("id") != "cloak")
            quebrou, nivel_pen = self._corrosao_nm_quebra(peca, lvl)
            nome_peca = peca.get("name", pref)
            if quebrou:
                c[f"{pref}_destruido"] = True
                if slot == "weapon":
                    p["weapon"] = {**WEAPONS["unarmed"]}; gear["weapon"] = None
                else:
                    gear[slot] = None
                await self.gm_say(f"💥 {nome_peca} de **{p['name']}** foi **destruída permanentemente**!")
                await self._devorador_cura(m, cura)
            elif nivel_pen <= 0:
                await self.gm_say(f"🦷 **{label}**: {nome_peca} de **{p['name']}** resistiu ao golpe sem sofrer dano!")
            else:
                rot = CORROSAO_NIVEL_NOME.get(nivel_pen, "muito danificado")
                await self.gm_say(f"🦷 **{label}**: {nome_peca} de **{p['name']}** está **{rot}** (-{nivel_pen})!")
            return
```
> **Regressão importante:** a armadura de corpo base (leather etc.) tem `id` no set e SEM N/M → `_corrosao_nm_quebra` usa N=0/M=2 → quebra no lvl 3, penalidade 1,2 — idêntico ao anterior. O `armadura_com_ca` continua sendo setado. O teste [A5](a) prova isso.

- [ ] **Step 6: Generalizar `_corrosao_ca_pen`** — Some a penalidade das peças de defesa que dão CA (armadura + escudo + elmo-def). A penalidade **persiste após a destruição** (o modelo é frouxo: a CA da peça continua embutida em `p["ac"]` mesmo com a peça removida, então a penalidade a cancela — mesmo comportamento da armadura base hoje). Fórmula por peça: `max(0, min(lvl − N, M))` (respeita os N níveis livres e o teto M):

```python
    def _corrosao_ca_pen(self, p):
        """Penalidade de CA por corrosão das peças de defesa que concedem CA.
        Persiste após a destruição (a CA da peça segue embutida em p['ac'])."""
        c = self._corr(p)
        gear = p["gear"]
        def _pen(piece, lvl):
            extra = int((piece or {}).get("corrosao_resistente", 0) or 0)
            m = int((piece or {}).get("corrosao_niveis_penalidade", 2) or 2)
            return max(0, min(lvl - extra, m))
        total = 0
        if c.get("armadura_com_ca"):        # manto (cloak) não dá CA → armadura_com_ca False
            total += _pen(gear.get("armor"), c.get("armadura_lvl", 0))
        off = gear.get("off_hand") or {}
        if off.get("kind") == "shield" or off.get("item_slot") == "shield":
            total += _pen(off, c.get("escudo_lvl", 0))
        head = gear.get("head") or {}
        if head.get("effect") == "def_":
            total += _pen(head, c.get("elmo_lvl", 0))
        return total
```
> **Byte-idêntico p/ base + correção intencional na destruição:** armadura base (N=0/M=2) dá pen `min(lvl,2)` — nível 1→1, 2→2, **idêntico** ao antigo `min(lvl,3)` nos níveis vivos. Na **destruição** (lvl 3): o antigo dava −3 (deixando a armadura em `base−1`, um leve over-penalty); o novo dá −2 → `base` (armadura destruída = CA base, mais correto). Isso é uma **mudança intencional só no momento da destruição**. Rode `tools/test_devorador.py` (se existir): se ele afirmar o valor de CA da armadura destruída, ajuste APENAS essa asserção e documente a correção. **Limitação conhecida (aceita nesta fase):** a destruição por corrosão NÃO reverte os `bonuses` (maxhp/spd) da peça custom (fica consistente com o modelo frouxo da armadura base, que também não reverte a CA embutida); tratar numa limpeza futura.

- [ ] **Step 7: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS ([A5]). Rode `python tools/test_devorador.py` se existir, e `python tools/test_roteamento_itens.py` — confirme que nada regrediu (a corrosão de armadura base deve seguir idêntica).

- [ ] **Step 8: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): corrosão generalizada de defesa (armadura N/M + escudo + prioridade)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Servidor — elmo/botas engine-ready (trilhas + penalidade de velocidade)

O laço de `_corroer_equipamento` já cobre `head`/`boots` (Task 5). Falta a **penalidade de velocidade** das botas corroídas. Elmo (def) já entra no `_corrosao_ca_pen`; elmo-maxhp fica para a fase da sub-aba dele.

**Files:** Modify `server.py` (`_moves_base` ou onde `spd` vira movimento); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Localizar o cálculo de movimento** — `grep -n "_moves_base\|def _moves_base" server.py`. `_moves_base(p)` é o cálculo autoritativo de casas de movimento (usado no reset de turno; ver nota do Grito de Guerra no CLAUDE.md).

- [ ] **Step 2: Teste que falha** — adicione:

```python
def test_corrosao_botas():
    print("\n[A6] Botas custom corroem e penalizam velocidade")
    S._apply_custom_items([S._validate_custom_item(armor_sample(id="botas_c", item_type="armor",
        armor_category="leve", corrosion_materials=["organic"],
        bonuses=[{"effect": "spd", "value": 1}]))[1]])
    r, p = _corr_setup()
    base = r._moves_base(p)
    # equipa como se fosse botas (slot boots) com material orgânico
    p["gear"]["boots"] = {"id": "botas_c", "name": "Botas", "corrosion_materials": ["organic"]}
    m = {"id": "d", "name": "Dev", "hp": 10, "max_hp": 10}
    asyncio.run(r._corroer_equipamento(m, p, S.CORROSAO_ARMADURA_ORGANICA, S.CORROSAO_ARMA_MADEIRA, "1d4", "T"))
    check("botas corroídas (nível 1)", r._corr(p)["botas_lvl"] == 1)
    check("movimento cai 1 com botas corroídas", r._moves_base(p) == base - 1)
    S._apply_custom_items([])
```

Chame `test_corrosao_botas()` no `if __name__`.

- [ ] **Step 3: Implementar `_corrosao_spd_pen` + hook** — Adicione:

```python
    def _corrosao_spd_pen(self, p):
        """Penalidade de velocidade por botas corroídas (persiste após destruição,
        cancelando o bônus de velocidade que ficou embutido em p['spd'])."""
        c = self._corr(p)
        boots = p["gear"].get("boots") or {}
        extra = int(boots.get("corrosao_resistente", 0) or 0)
        m = int(boots.get("corrosao_niveis_penalidade", 2) or 2)
        return max(0, min(c.get("botas_lvl", 0) - extra, m))
```
Em `_moves_base(p)`, subtraia `self._corrosao_spd_pen(p)` do total (mantendo o piso existente). Ex., se o retorno é `max(0, base + bonus)`, passe a ser `max(0, base + bonus - self._corrosao_spd_pen(p))`. **Ajuste ao código real** de `_moves_base` (localizado no Step 1). Botas base não têm material → `botas_lvl` sempre 0 → penalidade 0, sem regressão.

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS. Regressão: `python tools/test_roteamento_itens.py` verde (botas base não têm material → `_corrosao_spd_pen` = 0 sempre).

- [ ] **Step 5: Commit**
```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): botas/elmo engine-ready na corrosão (penalidade de velocidade)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Cliente — lógica pura de armadura (serialize/validate/preço) + teste node

**Files:** Modify `tools/editor_items_logic.js`; Test `tools/test_editor_items_logic.js`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_items_logic.js` (antes do `console.log` final):

```javascript
// ── Armadura/Escudo ──
const adraft = {name:"Cota Teste", emoji:"🛡️", item_type:"armor", ac_bonus:4,
  armor_category:"media", materiais:{organic:false, metal:true},
  corrosao_livres:0, corrosao_penalidade:2,
  bonuses:[{effect:"maxhp", value:5}], allowed_classes:[],
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:120};
const aitem = L.serializeArmor(adraft);
check("serializeArmor gera id", aitem.id === "cota_teste");
check("serializeArmor item_type armor", aitem.item_type === "armor");
check("serializeArmor ac_bonus", aitem.ac_bonus === 4);
check("serializeArmor materiais lista", JSON.stringify(aitem.corrosion_materials) === JSON.stringify(["metal"]));
check("serializeArmor N/M", aitem.corrosao_resistente === 0 && aitem.corrosao_niveis_penalidade === 2);
check("serializeArmor bonuses", aitem.bonuses.length === 1 && aitem.bonuses[0].effect === "maxhp");
const sdraft = Object.assign({}, adraft, {name:"Escudo T", item_type:"shield", armor_category:"media"});
const sitem = L.serializeArmor(sdraft);
check("escudo item_type shield", sitem.item_type === "shield");
check("escudo zera categoria", sitem.armor_category == null);
check("escudo mantém material", JSON.stringify(sitem.corrosion_materials) === JSON.stringify(["metal"]));
check("validateArmorDraft aceita válido", L.validateArmorDraft(adraft).ok);
check("validateArmorDraft rejeita sem nome", !L.validateArmorDraft(Object.assign({}, adraft, {name:""})).ok);
check("suggestPriceArmor cresce com CA", L.suggestPriceArmor({ac_bonus:6}) > L.suggestPriceArmor({ac_bonus:2}));
```

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_editor_items_logic.js` → FAIL (`L.serializeArmor is not a function`).

- [ ] **Step 3: Implementar** — Em `tools/editor_items_logic.js`, antes do objeto `api`, adicione:

```javascript
  var ARMOR_CATS = ["leve", "media", "pesada"];
  var BONUS_EFFECTS = ["def_", "maxhp", "spd"];
  function serializeArmor(d) {
    var kind = d.item_type === "shield" ? "shield" : "armor";
    var mats = [];
    var mm = d.materiais || {};
    if (mm.organic) mats.push("organic");
    if (mm.metal) mats.push("metal");
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "🛡️", item_type: kind, kind: kind, custom: true,
      ac_bonus: Math.max(0, +d.ac_bonus || 0),
      armor_category: (kind === "armor" && ARMOR_CATS.indexOf(d.armor_category) >= 0) ? d.armor_category : null,
      corrosion_materials: mats,
      corrosao_resistente: Math.max(0, +d.corrosao_livres || 0),
      corrosao_niveis_penalidade: Math.max(1, +d.corrosao_penalidade || 2),
      bonuses: (d.bonuses || []).filter(function (b) {
        return b && BONUS_EFFECTS.indexOf(b.effect) >= 0;
      }).map(function (b) { return { effect: b.effect, value: +b.value || 0 }; }),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    return item;
  }
  var KA_CA = 20, KA_BONUS = 6;
  function suggestPriceArmor(item) {
    var p = KA_CA * (+item.ac_bonus || 0);
    (item.bonuses || []).forEach(function (b) { p += KA_BONUS * Math.abs(+b.value || 0); });
    return Math.max(1, Math.round(p));
  }
  function validateArmorDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if ((+d.ac_bonus || 0) < 0) return { ok: false, msg: "CA inválida" };
    return { ok: true };
  }
```
E acrescente `serializeArmor`, `suggestPriceArmor`, `validateArmorDraft`, `ARMOR_CATS`, `BONUS_EFFECTS` ao objeto `api`.

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_editor_items_logic.js` → PASS.

- [ ] **Step 5: Commit**
```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): lógica pura de armadura/escudo (serialize/validate/preço) + teste node

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Cliente — editor das sub-abas Armaduras/Escudos

Generaliza `tools/editor_items_editor.js` para renderizar um formulário por tipo. Como o editor não roda headless, verifique com `node --check` + grep de ids.

**Files:** Modify `tools/editor_items_editor.js`.

- [ ] **Step 1: Habilitar as sub-abas** — No array `TYPES`, troque `["armaduras","Armaduras",false]` e `["escudos","Escudos",false]` para `true` (habilitadas). Mantenha as outras 5 `false`.

- [ ] **Step 2: Roteamento por tipo** — Hoje o editor é weapon-only. Introduza estado `var activeType = "armas";` e, no clique da sub-aba, troque `activeType` e re-renderize. Em `render()`, o `onclick` das sub-tabs habilitadas passa a: `activeType = b.dataset.type; draft = novoDraftFor(activeType); renderForm();`.

- [ ] **Step 3: Draft por tipo** — Adicione `novoDraftFor(type)` que retorna `novoDraft()` (arma, existente) para `"armas"`, e para `"armaduras"`/`"escudos"`:

```javascript
  function novoDraftArmor(kind) {
    return { name:"", emoji:"🛡️", item_type:(kind === "escudos" ? "shield" : "armor"),
      ac_bonus: 2, armor_category:"leve",
      materiais:{organic:false, metal:true}, corrosao_livres:0, corrosao_penalidade:2,
      bonuses:[], granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
  function novoDraftFor(type) {
    return (type === "armaduras" || type === "escudos") ? novoDraftArmor(type) : novoDraft();
  }
```

- [ ] **Step 4: Formulário de armadura/escudo** — Em `renderForm()`, ramifique por `activeType`. Para armas mantém o form atual. Para armadura/escudo, monte (reusando os helpers `seccao`/`campo`/`numInput`/`chk`/`selectOpts`/`chkLbl` já existentes):

```javascript
    if (activeType === "armaduras" || activeType === "escudos") {
      var isShield = activeType === "escudos";
      f.innerHTML = [
        seccao("Identidade",
          campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
          campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
        seccao("Defesa",
          campo("Bônus de CA", numInput("ie-ac", draft.ac_bonus, 0, 20)) +
          (isShield ? "" : campo("Categoria", selectOpts("ie-cat", ["leve","media","pesada"], draft.armor_category)))),
        seccao("Bônus adicionais",
          '<div id="ie-abonus"></div><button id="ie-add-abonus">+ bônus</button>' +
          '<template id="ie-abonus-tpl"><span class="ie-elem-row">' +
          '<select class="ie-abonus-eff"><option value="def_">CA extra</option>' +
          '<option value="maxhp">PV máx</option><option value="spd">Velocidade</option></select> ' +
          numInput("", 0, -10, 20) + ' <button class="ie-abonus-del">✕</button></span></template>'),
        seccao("Durabilidade (corrosão)",
          campo("Níveis sem penalidade", numInput("ie-corrlivre", draft.corrosao_livres, 0, 12)) +
          campo("Níveis com penalidade", numInput("ie-corrpen", draft.corrosao_penalidade, 1, 12)) +
          '<label class="ie-field"><input type="checkbox" id="ie-mat-organic"' + (draft.materiais.organic ? " checked" : "") + '> Orgânico (Devorador Orgânico)</label>' +
          '<label class="ie-field"><input type="checkbox" id="ie-mat-metal"' + (draft.materiais.metal ? " checked" : "") + '> Metal (Devorador de Metal)</label>' +
          '<span class="ie-hint">Sem material marcado, a peça não corrói. Quebra em N+M+1.</span>'),
        seccao("Restrição de classe (vazio = todas)",
          CLASSES.map(function (c) { return '<label class="ie-cls"><input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
        seccao("Disponibilidade",
          chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
          chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
          chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
        seccao("Preço", campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) + '<span id="ie-price-sug" class="ie-hint"></span>'),
        seccao("Imagem", '<input type="file" id="ie-art" accept="image/png"> <span id="ie-art-name" class="ie-hint"></span>'),
        '<div class="ie-actions"><button id="ie-save">💾 Salvar peça</button><span id="ie-status" class="ie-hint"></span></div>',
      ].join("");
      bindArmorForm();
      renderArmorBonuses();
      renderArmorPreview();
      return;
    }
    // ... (form de arma existente segue abaixo) ...
```

- [ ] **Step 5: Handlers de armadura** — Adicione `currentArmorDraftFromForm()` (lê ie-name/emoji/ie-ac/ie-cat/ie-corrlivre/ie-corrpen/ie-mat-organic/ie-mat-metal/classes/disponibilidade/price + a lista `#ie-abonus .ie-elem-row`), `renderArmorBonuses()`/`addArmorBonusRow(b)` (espelham `renderElems`/`addElemRow`), `renderArmorPreview()` (usa `L.serializeArmor` + `L.suggestPriceArmor`, mostra CA/bônus/corrosão/material + a foto no topo como no form de arma), e `bindArmorForm()` (liga inputs→`renderArmorPreview`, `#ie-add-abonus`, `#ie-art` com objectURL, `#ie-save`→`onSaveArmor`). Reutilize `artURL`/`artFile` e o padrão de `onSave` da arma; `onSaveArmor` chama `L.validateArmorDraft` + `L.serializeArmor` + `window.EDITOR_SAVE.saveCustomItem` (o mesmo handler WS serve armadura, pois valida por `item_type`) e `uploadItemArt`.

  Código de `currentArmorDraftFromForm` (guarde os ids opcionais):
```javascript
  function currentArmorDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.ac_bonus = +g("ie-ac").value || 0;
    if (g("ie-cat")) draft.armor_category = g("ie-cat").value;
    draft.corrosao_livres = Math.max(0, +g("ie-corrlivre").value || 0);
    draft.corrosao_penalidade = Math.max(1, +g("ie-corrpen").value || 2);
    draft.materiais = { organic: g("ie-mat-organic").checked, metal: g("ie-mat-metal").checked };
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.bonuses = Array.prototype.map.call(root.querySelectorAll("#ie-abonus .ie-elem-row"), function (r) {
      return { effect: r.querySelector(".ie-abonus-eff").value, value: +r.querySelector(".ie-num").value || 0 }; });
    return draft;
  }
```

- [ ] **Step 6: Verificação estática** — `node --check tools/editor_items_editor.js` → OK. Grep confirma os ids novos (`ie-ac`, `ie-mat-metal`, `ie-abonus`, `ie-corrpen`). O teste in-app (abrir o editor com `server.py`, criar uma armadura, salvar, ver na loja) é **follow-up manual** (o editor não roda headless).

- [ ] **Step 7: Commit**
```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): sub-abas Armaduras e Escudos no Editor de Itens

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Cliente — armaduras/escudos custom no seletor de baús

O `CAT.items` do editor de masmorras já concatena `EDITOR_CUSTOM_ITEMS` filtrando `disponibilidade.baus` (Fase 1). Como agora há itens `item_type` armor/shield, garanta que a lista os inclui (o filtro é por `baus`, não por tipo — deve funcionar), mas o mapeamento minimal precisa cobrir os campos que o seletor lê.

**Files:** Modify `tools/editor.js` (bloco `customBaus` da Fase 1).

- [ ] **Step 1: Revisar o mapeamento** — Localize o bloco `customBaus` em `tools/editor.js` (`grep -n "customBaus" tools/editor.js`). Ele mapeia `{id,name,emoji,die,stat,categoria,custom}` — campos de arma. Para armadura/escudo, `die`/`stat` são `undefined` (ok, o seletor só usa `id`/`name`). Garanta que o filtro NÃO exige `die` (senão exclui armaduras):

```javascript
    var customBaus = (window.EDITOR_CUSTOM_ITEMS || [])
      .filter(function (i) { return i && i.disponibilidade && i.disponibilidade.baus; })
      .map(function (i) { return { id: i.id, name: i.name, emoji: i.emoji,
                                   item_type: i.item_type, custom: true }; });
```
(Remova `die/stat/categoria` do map — o seletor de baú só precisa de `id`/`name`/`emoji`; manter genérico cobre arma E armadura.)

- [ ] **Step 2: Verificação estática** — `node --check tools/editor.js` → OK. `grep -n "EDITOR_CUSTOM_ITEMS" tools/editor.js` confirma o uso.

- [ ] **Step 3: Commit**
```bash
git add tools/editor.js
git commit -m "feat(itens): armaduras/escudos custom aparecem no seletor de baús

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Docs + verificação final

**Files:** Modify `CLAUDE.md`; rodar toda a suíte.

- [ ] **Step 1: Nota no `CLAUDE.md`** — Acrescente um parágrafo `>` no estilo dos demais resumindo a Fase 2a: sub-abas Armaduras/Escudos; `item_type` armor/shield; `ac_bonus`+multi-efeito `bonuses` (def_/maxhp/spd via `_apply_single_effect`); material/corrosão **generalizada** para os slots de defesa (armadura→escudo→arma→elmo→botas) com N/M (peças base byte-idênticas, `_corroer_equipamento`/`_corrosao_ca_pen`/`_corrosao_spd_pen` generalizados); merge em `SHOP_ARMORS`/`_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL` + sets `CORROSAO_ARMADURA_*`; compra/equipar preservam os campos; botas/elmos engine-ready (UI na sub-aba deles). Testes: `tools/test_editor_itens.py` + `tools/test_editor_items_logic.js`. Fases seguintes: B (atributos), C (resistências), D (iniciativa).

- [ ] **Step 2: Suíte completa**
```bash
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
python tools/test_roteamento_itens.py
```
Todos verdes (0 falhas). Se existir `tools/test_devorador.py`, rode-o também (corrosão base intocada).

- [ ] **Step 3: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(itens): registra o Editor de Itens Fase 2a (Armaduras + Escudos)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de auto-revisão (self-review deste plano)

- **Cobertura da spec:** validação (T1), merge+catálogos+sets (T2), multi-efeito (T3), compra/equipar preservação (T4), corrosão generalizada armadura N/M+escudo+prioridade (T5), elmo/botas engine-ready+velocidade (T6), lógica pura+node (T7), UI sub-abas (T8), seletor de baús (T9), docs (T10).
- **Prioridade de corrosão** armadura→escudo→arma→elmo→botas: codificada na lista `alvos` de `_corroer_equipamento` (T5, Step 5).
- **Byte-idêntico** para peças base: `_corrosao_nm_quebra` com N=0/M=2 reproduz o modelo de 3 níveis; provado por [A5](a). Rodar `test_devorador.py`/`test_roteamento_itens.py` como rede de segurança.
- **Risco principal** (corrosão compartilhada): T5/T6 são os pontos sensíveis; testes exercitam armadura base + escudo custom + prioridade + botas.
- **WIP em paralelo:** edições ancoradas por código; commits só com arquivos nomeados.
- **Escudo no off_hand:** o laço filtra o off_hand para só corroer se for realmente escudo (não arma secundária/instrumento).
