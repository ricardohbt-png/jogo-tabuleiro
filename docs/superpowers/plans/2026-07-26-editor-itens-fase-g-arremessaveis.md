# Editor de Itens — Fase G: Arremessáveis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Destravar a sub-aba Arremessáveis do Editor de Itens, criando frascos/bombas custom nos dois modos de mira (mirado num monstro e área com save), mesclados no mercador/baús/loot.

**Architecture:** O servidor resolve o arremesso por `ARREMESSAVEIS[item_id]` e o cliente decide a mira por `CATALOGO_ITENS[item.id]` (catálogo estático). Esta fase valida/normaliza o item custom, registra o `defn` em `ARREMESSAVEIS` e carrega os metadados de mira (`alvo`/`alcance`/`area_raio`) no próprio item de bolsa — com duas edições cirúrgicas no cliente que caem para esses campos quando o id não está no catálogo estático. Os handlers `handle_throw_item`/`_throw_item_alvo`/`_throw_item_area` não mudam.

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`game.js`, `src/gameState.js`, `tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py` e `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging — LER ANTES DAS TASKS 2, 3 e 4

O usuário reworka `server.py`, `game.js` e `src/gameState.js` em paralelo (WIP não commitado — "Barreira Arcana"). **NUNCA** `git add server.py` / `game.js` / `src/gameState.js` / `git add -A`.

Proximidade verificada (os hunks do WIP não encostam nos pontos desta fase):
- `server.py`: edições na região contígua de itens custom (~22150–22400); WIP mais próximo em ~20195 e ~21636.
- `game.js`: edição em ~10763; **nenhum** hunk do WIP entre 10400–11100.
- `src/gameState.js`: edição em ~2023; WIP mais próximo em ~2173.

Ao commitar uma task que toca um desses arquivos:

```bash
git add <arquivos de teste / editor_items_*.js>     # seguros, fora do WIP
git diff -- <arquivo> > /tmp/all.patch              # contém SEUS hunks + o WIP
# Leia /tmp/all.patch, identifique os @@ hunks QUE VOCÊ escreveu e monte
# /tmp/mine.patch = header (4 linhas: diff/index/---/+++) + APENAS esses hunks.
git apply --cached /tmp/mine.patch
git diff --cached -- <arquivo>                      # confira a olho: só o seu código
git diff --cached --stat
```

Se vazar qualquer linha do WIP: `git reset <arquivo>` e refaça. `git add -p` é interativo e **não funciona** aqui — use sempre `git apply --cached`. Um arquivo por patch (repita para game.js e gameState.js na Task 4).

---

## File Structure

- **Modify:** `tools/editor_items_logic.js` — `THROW_TARGETS`/`THROW_ELEMENTS`, `serializeThrowable`/`validateThrowableDraft`/`suggestPriceThrowable`.
- **Modify:** `tools/test_editor_items_logic.js` — casos node de arremessável.
- **Modify:** `server.py` — sets de validação, `_validate_custom_throwable`, `_custom_throwable_defn`, `_custom_throwable_inventory_dict`, cleanup + ramo de merge em `_apply_custom_items`.
- **Modify:** `tools/test_editor_itens.py` — seção `[G1]`–`[G4]`.
- **Modify:** `src/gameState.js` (1 linha, ~2023) e `game.js` (~10763-10768) — fallback de mira.
- **Modify:** `tools/editor_items_editor.js` — destravar sub-aba, form de arremessável.
- **Modify:** `CLAUDE.md` — nota da Fase G.

---

## Task 1: Lógica pura (cliente) — serializeThrowable

**Files:**
- Modify: `tools/editor_items_logic.js`
- Test: `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever os testes node que falham**

Acrescente ANTES da linha final `console.log(...)` em `tools/test_editor_items_logic.js`:

```javascript
// Fase G — arremessáveis
check("THROW_TARGETS tem os 2 modos",
  L.THROW_TARGETS.indexOf("ataque_alvo") >= 0 && L.THROW_TARGETS.indexOf("area") >= 0);
check("THROW_ELEMENTS tem fogo e acido",
  L.THROW_ELEMENTS.indexOf("fogo") >= 0 && L.THROW_ELEMENTS.indexOf("acido") >= 0);
const thAlvo = L.serializeThrowable({name:"Frasco Ardente", alvo:"ataque_alvo", alcance:5,
  tem_dano:true, die_qtd:2, die_faces:6, elemento:"fogo",
  em_chamas:true, chamas_qtd:1, chamas_faces:4, chamas_agua_apaga:true,
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:25});
check("serializeThrowable id/slot/effect",
  thAlvo.id === "frasco_ardente" && thAlvo.item_slot === "bag"
  && thAlvo.effect === "throwable" && thAlvo.item_type === "throwable");
check("serializeThrowable alvo/alcance", thAlvo.alvo === "ataque_alvo" && thAlvo.alcance === 5);
check("serializeThrowable dano/elemento", thAlvo.dano === "2d6" && thAlvo.elemento === "fogo");
check("serializeThrowable em chamas", thAlvo.em_chamas === true
  && thAlvo.chamas_dur === "1d4" && thAlvo.chamas_agua_apaga === true);
check("single-target não grava area_raio/save_cd",
  thAlvo.area_raio === undefined && thAlvo.save_cd === undefined);
const thArea = L.serializeThrowable({name:"Bomba X", alvo:"area", alcance:4, area_raio:2, save_cd:13,
  tem_dano:true, die_qtd:3, die_faces:6, elemento:"explosao",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:60});
check("area grava raio e save_cd", thArea.alvo === "area" && thArea.area_raio === 2 && thArea.save_cd === 13);
check("area sem chamas nao grava chamas_dur", thArea.chamas_dur === undefined);
const thSemDano = L.serializeThrowable({name:"Frasco Vazio", alvo:"ataque_alvo",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:5});
check("sem dano nao grava dano/elemento",
  thSemDano.dano === undefined && thSemDano.elemento === undefined);
check("alcance default 4", thSemDano.alcance === 4);
check("emoji default 💥", thSemDano.emoji === "💥");
check("alvo invalido normaliza p/ ataque_alvo",
  L.serializeThrowable({name:"Y", alvo:"parede"}).alvo === "ataque_alvo");
check("alcance clampado em 12", L.serializeThrowable({name:"Y", alcance:99}).alcance === 12);
check("validateThrowableDraft aceita valido",
  L.validateThrowableDraft({name:"X", alvo:"area", tem_dano:true, die_faces:6}).ok);
check("validateThrowableDraft rejeita sem nome",
  !L.validateThrowableDraft({name:"", alvo:"area"}).ok);
check("validateThrowableDraft rejeita dado invalido",
  !L.validateThrowableDraft({name:"X", alvo:"area", tem_dano:true, die_faces:7}).ok);
check("suggestPriceThrowable cresce com o dado",
  L.suggestPriceThrowable({dano:"3d6"}) > L.suggestPriceThrowable({dano:"1d6"}));
check("suggestPriceThrowable cresce com area",
  L.suggestPriceThrowable({dano:"2d6", alvo:"area", area_raio:2}) > L.suggestPriceThrowable({dano:"2d6"}));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_items_logic.js`
Expected: FAIL (`L.THROW_TARGETS` indefinido / `serializeThrowable is not a function`).

- [ ] **Step 3: Implementar em `tools/editor_items_logic.js`**

3a. Adicione a constante de preço à linha de constantes `K_*` existente (hoje `var K_DIE = 4, K_BONUS = 6, K_ELEM = 5, K_2M = 4, K_POTION = 2;`), acrescentando `, K_THROW = 5`.

3b. Adicione os dois catálogos perto de `POTION_EFFECTS`:

```javascript
  var THROW_TARGETS = ["ataque_alvo", "area"];
  var THROW_ELEMENTS = ["fogo", "frio", "eletrico", "acido", "sagrado", "explosao"];
```

3c. Adicione as três funções logo após `suggestPricePotion`:

```javascript
  function serializeThrowable(d) {
    var alvo = THROW_TARGETS.indexOf(d.alvo) >= 0 ? d.alvo : "ataque_alvo";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "💥", item_type: "throwable", item_slot: "bag",
      effect: "throwable", custom: true,
      alvo: alvo, alcance: Math.max(1, Math.min(12, +d.alcance || 4)),
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (d.tem_dano) {
      item.dano = buildDie(d.die_qtd, d.die_faces);
      item.elemento = THROW_ELEMENTS.indexOf(d.elemento) >= 0 ? d.elemento : "fogo";
    }
    if (alvo === "area") {
      item.area_raio = Math.max(1, Math.min(3, +d.area_raio || 1));
      if (+d.save_cd) item.save_cd = Math.max(5, Math.min(25, +d.save_cd));
    }
    if (d.em_chamas) {
      item.em_chamas = true;
      item.chamas_dur = buildDie(d.chamas_qtd, d.chamas_faces || 4);
      item.chamas_agua_apaga = d.chamas_agua_apaga !== false;
    }
    return item;
  }
  function validateThrowableDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (d.alvo && THROW_TARGETS.indexOf(d.alvo) < 0) return { ok: false, msg: "alvo inválido" };
    if (d.tem_dano && FACES.indexOf(+d.die_faces) < 0) return { ok: false, msg: "dado de dano inválido" };
    return { ok: true };
  }
  function suggestPriceThrowable(item) {
    var p = K_THROW * dieAvg(item.dano);
    if (item.alvo === "area") p *= (1 + 0.5 * Math.max(1, +item.area_raio || 1));
    if (item.em_chamas) p += 10;
    return Math.max(1, Math.round(p));
  }
```
Note: `slugify`, `buildDie`, `dieAvg`, `FACES` e `K_THROW` (3a) já estão no módulo.

3d. Adicione ao objeto `api` (junto de `serializePotion` etc.):

```javascript
              serializeThrowable: serializeThrowable,
              validateThrowableDraft: validateThrowableDraft,
              suggestPriceThrowable: suggestPriceThrowable,
              THROW_TARGETS: THROW_TARGETS, THROW_ELEMENTS: THROW_ELEMENTS,
```

- [ ] **Step 4: Rodar e ver passar (sem regressão)**

Run: `node tools/test_editor_items_logic.js`
Expected: PASS — todos verdes, incluindo arma/armadura/acessório/poção pré-existentes.

- [ ] **Step 5: Commit (arquivos de cliente — seguros)**

```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): lógica de arremessáveis custom (mirado + área)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação de arremessável

**Files:**
- Modify: `server.py` (sets novos; `_validate_custom_item`; nova `_validate_custom_throwable`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_itens.py`, adicione logo após `potion_sample` (busque `def potion_sample`):

```python
def throwable_sample(**over):
    base = {"id": "frasco_teste", "name": "Frasco Teste", "emoji": "💥",
            "item_type": "throwable", "alvo": "ataque_alvo", "alcance": 4,
            "dano": "2d6", "elemento": "fogo", "allowed_classes": [], "price": 25,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_arremessavel():
    print("\n[G1] Validacao de arremessável")
    ok, it = S._validate_custom_item(throwable_sample())
    check("aceita arremessável mirado", ok)
    check("item_type = throwable", ok and it.get("item_type") == "throwable")
    check("item_slot = bag + effect throwable",
          ok and it.get("item_slot") == "bag" and it.get("effect") == "throwable")
    check("alvo/alcance/dano preservados",
          ok and it.get("alvo") == "ataque_alvo" and it.get("alcance") == 4 and it.get("dano") == "2d6")
    check("mirado nao grava area_raio/save", ok and "area_raio" not in it and "save" not in it)
    oka, ita = S._validate_custom_item(throwable_sample(id="bomba_teste", alvo="area",
        area_raio=2, save_cd=13, dano="3d6", elemento="explosao"))
    check("aceita área com raio", oka and ita.get("alvo") == "area" and ita.get("area_raio") == 2)
    check("área grava save reflexos+cd",
          oka and ita.get("save") == {"tipo": "reflexos", "cd": 13})
    okc, itc = S._validate_custom_item(throwable_sample(id="frasco_chamas",
        em_chamas=True, chamas_dur="1d6", chamas_agua_apaga=False))
    check("em_chamas grava duracao e agua_apaga",
          okc and itc.get("em_chamas") is True and itc.get("chamas_dur") == "1d6"
          and itc.get("chamas_agua_apaga") is False)
    oks, its = S._validate_custom_item(throwable_sample(id="frasco_seco", dano=None))
    check("sem dano nao grava dano/elemento", oks and "dano" not in its and "elemento" not in its)
    okb, _ = S._validate_custom_item(throwable_sample(alvo="parede"))
    check("rejeita alvo invalido", not okb)
    okd, _ = S._validate_custom_item(throwable_sample(dano="2d7"))
    check("rejeita dado de dano invalido", not okd)
    okn, _ = S._validate_custom_item(throwable_sample(id="frasco_oleo"))
    check("rejeita id nativo de ARREMESSAVEIS (frasco_oleo)", not okn)
    oke, _ = S._validate_custom_item(throwable_sample(id="elixir"))
    check("rejeita id nativo de loja (elixir)", not oke)
```

Registre no `if __name__ == "__main__":`, logo APÓS a linha `test_pocao_merge(); test_pocao_uso(); test_pocao_multidose()`:

```python
    test_validacao_arremessavel()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: `[G1]` FALHA (`_validate_custom_item` retorna "tipo de item não suportado" para `throwable`). Nenhuma seção anterior afetada.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione os dois sets logo após a linha `_ITEM_POTION_EFFECTS = {...}`:

```python
# Modos de mira e elementos válidos p/ arremessável custom (Fase G).
_ITEM_THROW_TARGETS = {"ataque_alvo", "area"}
_ITEM_THROW_ELEMENTS = {"fogo", "frio", "eletrico", "acido", "sagrado", "explosao"}
```

3b. Em `_validate_custom_item`, adicione o dispatch. A função termina hoje com:
```python
    if it == "potion":
        return _validate_custom_potion(raw)
    return False, "tipo de item não suportado"
```
Mude para:
```python
    if it == "potion":
        return _validate_custom_potion(raw)
    if it == "throwable":
        return _validate_custom_throwable(raw)
    return False, "tipo de item não suportado"
```

3c. Adicione a nova função imediatamente após `_validate_custom_potion` (após o seu `return True, item`):

```python
def _validate_custom_throwable(raw):
    """Valida arremessável custom (Fase G). Consumível de bolsa (effect 'throwable')
    cujo comportamento é resolvido por ARREMESSAVEIS em handle_throw_item:
    'ataque_alvo' (teste de ataque por DES) ou 'area' (raio + save de Reflexos)."""
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome do arremessável"
    native = {i["id"] for shop in (SHOP_MERCHANT, SHOP_TEMPLE, SHOP_TAVERN)
              for i in shop if not i.get("custom")}
    native |= {k for k, v in ARREMESSAVEIS.items() if not v.get("custom")}
    if iid in native:
        return False, "o id não pode substituir um item nativo"
    alvo = raw.get("alvo")
    if alvo not in _ITEM_THROW_TARGETS:
        return False, "alvo de arremesso inválido"
    def _int0(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    dano = raw.get("dano")
    if dano not in (None, "") and not _die_ok(dano):
        return False, "dado de dano inválido (use NdX, X em 4/6/8/10/12)"
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    item = {
        "id": iid, "name": name, "emoji": str(raw.get("emoji") or "💥")[:8],
        "item_type": "throwable", "item_slot": "bag", "effect": "throwable", "custom": True,
        "alvo": alvo, "alcance": max(1, min(12, _int0(raw.get("alcance", 4)) or 4)),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    if dano:
        item["dano"] = str(dano).lower()
        el = raw.get("elemento")
        item["elemento"] = el if el in _ITEM_THROW_ELEMENTS else "fogo"
    if alvo == "area":
        item["area_raio"] = max(1, min(3, _int0(raw.get("area_raio", 1)) or 1))
        cd = _int0(raw.get("save_cd"))
        if cd:
            item["save"] = {"tipo": "reflexos", "cd": max(5, min(25, cd))}
    if raw.get("em_chamas"):
        dur = raw.get("chamas_dur") or "1d4"
        item["em_chamas"] = True
        item["chamas_dur"] = str(dur).lower() if _die_ok(dur) else "1d4"
        item["chamas_agua_apaga"] = bool(raw.get("chamas_agua_apaga", True))
    return True, item
```
Note: `SHOP_MERCHANT`, `SHOP_TEMPLE`, `SHOP_TAVERN`, `ARREMESSAVEIS`, `_ITEM_CLASSES`, `_die_ok` e os sets de 3a já são module-level. Confirme antes de usar; se algum faltar, pare e reporte NEEDS_CONTEXT.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: `[G1]` totalmente verde; nenhuma seção anterior regride.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks desta task em `server.py`: os 2 sets novos, o ramo em `_validate_custom_item`, e a função `_validate_custom_throwable`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com esses hunks, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py   # confirmar: só código de arremessável
git commit -m "feat(itens): validação de arremessáveis custom

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — merge em ARREMESSAVEIS + uso ponta-a-ponta

**Files:**
- Modify: `server.py` (`_custom_throwable_defn`, `_custom_throwable_inventory_dict`, cleanup + ramo em `_apply_custom_items`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione após `test_validacao_arremessavel`:

```python
def test_arremessavel_merge():
    print("\n[G2] Merge de arremessável (ARREMESSAVEIS + lojas)")
    ok, it = S._validate_custom_item(throwable_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("entra em ARREMESSAVEIS", "frasco_teste" in S.ARREMESSAVEIS)
    check("defn carrega alvo/dano",
          S.ARREMESSAVEIS.get("frasco_teste", {}).get("alvo") == "ataque_alvo"
          and S.ARREMESSAVEIS["frasco_teste"].get("dano") == "2d6")
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "frasco_teste" for i in S.SHOP_MERCHANT))
    check("item de bolsa carrega metadados de mira",
          next(i for i in S.SHOP_MERCHANT if i["id"] == "frasco_teste").get("alvo") == "ataque_alvo")
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "frasco_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "frasco_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo ARREMESSAVEIS (frasco_oleo) intacto", "frasco_oleo" in S.ARREMESSAVEIS)
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "frasco_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de ARREMESSAVEIS", "frasco_teste" not in S.ARREMESSAVEIS)
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "frasco_teste" for i in S.SHOP_MERCHANT))
    check("lista vazia remove de _DUNGEON_ITEM_CATALOG", "frasco_teste" not in S._DUNGEON_ITEM_CATALOG)
    check("nativos de ARREMESSAVEIS sobrevivem ao clear", "frasco_oleo" in S.ARREMESSAVEIS)

def test_arremessavel_uso_alvo():
    print("\n[G3] Arremesso mirado ponta-a-ponta")
    ok, it = S._validate_custom_item(throwable_sample(dano="2d6", em_chamas=True))
    S._apply_custom_items([it])
    r, p = _room_com_alvo()          # turno forçado, LOS livre, atk_bonus 50, monstro ac 1
    p["bag"] = [dict(S._custom_throwable_inventory_dict(it))]
    hp0 = r.monsters["m1"]["hp"]
    asyncio.run(r.handle_throw_item("p1", {"item_id": "frasco_teste", "target_id": "m1"}))
    check("alvo sofre dano", r.monsters["m1"]["hp"] < hp0)
    check("item consumido da bolsa", not any(i["id"] == "frasco_teste" for i in p["bag"]))
    check("gastou a ação principal", p.get("action_done") is True)
    check("alvo pegou fogo", r.monsters["m1"].get("em_chamas_rodadas", 0) > 0)
    S._apply_custom_items([])

def test_arremessavel_uso_area():
    print("\n[G4] Arremesso de área ponta-a-ponta")
    ok, it = S._validate_custom_item(throwable_sample(id="bomba_teste", alvo="area",
        area_raio=1, save_cd=99, dano="3d6", elemento="explosao"))   # cd 99 → save sempre falha
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    p["pos"] = [9, 9]                # herói fora do raio (a área não discrimina aliados)
    r.monsters["m1"]["pos"] = [2, 1]
    hp0 = r.monsters["m1"]["hp"]
    asyncio.run(r.handle_throw_item("p1", {"item_id": "bomba_teste", "tx": 2, "ty": 1}))
    check("alvo na área sofre dano", r.monsters["m1"]["hp"] < hp0)
    check("item de área consumido", not any(i["id"] == "bomba_teste" for i in p["bag"]))
    check("herói fora do raio ileso", p["hp"] == p["max_hp"])
    S._apply_custom_items([])
```

Nota sobre o `[G4]`: `p["bag"]` é populado dentro do teste — antes do `handle_throw_item`, adicione a linha:
```python
    p["bag"] = [dict(S._custom_throwable_inventory_dict(it))]
```
logo após `r.monsters["m1"]["pos"] = [2, 1]`.

Registre no `if __name__ == "__main__":`, logo APÓS `test_validacao_arremessavel()`:

```python
    test_arremessavel_merge(); test_arremessavel_uso_alvo(); test_arremessavel_uso_area()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: `[G2]`–`[G4]` FALHAM (`_custom_throwable_inventory_dict` não existe; item não entra em `ARREMESSAVEIS`).

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione as duas funções imediatamente após `_custom_potion_inventory_dict` (após o seu `return inv`):

```python
def _custom_throwable_defn(item):
    """Entrada de ARREMESSAVEIS para um arremessável custom (formato nativo).
    'custom' marca o registro p/ o cleanup idempotente em _apply_custom_items."""
    defn = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
            "alcance": item["alcance"], "alvo": item["alvo"], "custom": True}
    if "dano" in item:
        defn["dano"] = item["dano"]
        defn["elemento"] = item["elemento"]
    if item["alvo"] == "area":
        defn["area_raio"] = item["area_raio"]
        if "save" in item:
            defn["save"] = dict(item["save"])
    if item.get("em_chamas"):
        defn["em_chamas"] = True
        defn["chamas_dur"] = item["chamas_dur"]
        defn["chamas_agua_apaga"] = item["chamas_agua_apaga"]
    return defn

def _custom_throwable_inventory_dict(item):
    """Arremessável custom — dict de bolsa/loja. Carrega os metadados de mira
    (alvo/alcance/area_raio) porque o cliente decide a mira pelo item quando o id
    não está no CATALOGO_ITENS estático."""
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": "bag", "effect": "throwable", "value": 0,
           "custom": True, "price": item["price"],
           "alvo": item["alvo"], "alcance": item["alcance"]}
    if item["alvo"] == "area":
        inv["area_raio"] = item["area_raio"]
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv
```

3b. Em `_apply_custom_items`, adicione o cleanup dos arremessáveis custom. Localize a linha existente:
```python
    SHOP_MERCHANT[:] = [i for i in SHOP_MERCHANT if not i.get("custom")]
```
e insira imediatamente APÓS ela:
```python
    # Arremessáveis custom vivem no dict ARREMESSAVEIS (espelha o cleanup de WEAPONS).
    for k in [k for k, v in ARREMESSAVEIS.items() if v.get("custom")]:
        ARREMESSAVEIS.pop(k, None)
```

3c. No laço `for raw in records:`, adicione o ramo de arremessável imediatamente APÓS o ramo de poção (`if it == "potion": ... continue`):
```python
        if it == "throwable":
            disp = item["disponibilidade"]
            ARREMESSAVEIS[item["id"]] = _custom_throwable_defn(item)
            inv = _custom_throwable_inventory_dict(item)
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
Expected: `[G2]`–`[G4]` verdes; `[G1]` e todas as seções anteriores continuam verdes.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks: as 2 funções novas, o cleanup de `ARREMESSAVEIS` e o ramo `if it == "throwable"`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com esses hunks, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): merge de arremessáveis custom em ARREMESSAVEIS e no mercador

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Cliente — mira de arremessáveis custom (2 edições cirúrgicas)

**Files:**
- Modify: `src/gameState.js` (~2023, ramo `pendingThrow` de `resolveTileClick`)
- Modify: `game.js` (~10763-10768 e a legenda, em `_iniciarMiraArremesso`)

Sem teste headless (precisa de DOM/partida). Verificação: parse dos dois arquivos + `node tools/test_editor_items_logic.js`. **Ambos os arquivos têm WIP do usuário** — leia a receita de partial staging no topo e faça **um patch por arquivo**.

- [ ] **Step 1: Fallback do alvo em `src/gameState.js`**

Localize (dentro do ramo `if (pendingThrow) {`):
```javascript
      const alvo = (CATALOGO_ITENS[th.id] || {}).alvo || 'ataque_alvo';
```
Substitua por:
```javascript
      // Itens custom (Editor de Itens) não estão no CATALOGO_ITENS estático:
      // o alvo vem no próprio pendingThrow (carregado do item de bolsa).
      const alvo = (CATALOGO_ITENS[th.id] || {}).alvo || th.alvo || 'ataque_alvo';
```

- [ ] **Step 2: Fallback dos metadados de mira em `game.js`**

Localize em `_iniciarMiraArremesso`:
```javascript
  const catDef  = (GS.CATALOGO_ITENS && GS.CATALOGO_ITENS[item.id]) || {};
  const alcance = catDef.alcance || 4;
  const isArea  = catDef.alvo === 'area';
  const areaRaio = isArea ? (catDef.areaRaio || 1) : 0;
  window._modoThrowItem = { id: item.id, alcance, area: areaRaio };
  GS.pendingThrow = { id: item.id, alcance };   // habilita o ramo de throw em resolveTileClick
```
Substitua por:
```javascript
  const catDef  = (GS.CATALOGO_ITENS && GS.CATALOGO_ITENS[item.id]) || {};
  // Itens custom (Editor de Itens) não estão no CATALOGO_ITENS estático — a mira
  // cai para os metadados que o servidor carrega no próprio item de bolsa.
  const alvoTipo = catDef.alvo || item.alvo || 'ataque_alvo';
  const alcance = catDef.alcance || item.alcance || 4;
  const isArea  = alvoTipo === 'area';
  const areaRaio = isArea ? (catDef.areaRaio || item.area_raio || 1) : 0;
  window._modoThrowItem = { id: item.id, alcance, area: areaRaio };
  GS.pendingThrow = { id: item.id, alcance, alvo: alvoTipo };   // habilita o ramo de throw em resolveTileClick
```

- [ ] **Step 3: Legenda com fallback (mesmo arquivo, poucas linhas abaixo)**

Localize:
```javascript
  leg.innerHTML = `${catDef.emoji || '🔥'} ${(catDef.nome || 'ARREMESSAR').toUpperCase()} — ${_alvoTxt} &nbsp;|&nbsp; ESC cancela`;
```
Substitua por:
```javascript
  leg.innerHTML = `${catDef.emoji || item.emoji || '🔥'} ${(catDef.nome || item.name || 'ARREMESSAR').toUpperCase()} — ${_alvoTxt} &nbsp;|&nbsp; ESC cancela`;
```

- [ ] **Step 4: Verificar (parse dos dois arquivos + node)**

Run: `node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js parse OK')"`
Expected: `game.js parse OK`

Run: `node -e "new Function(require('fs').readFileSync('src/gameState.js','utf8')); console.log('gameState.js parse OK')"`
Expected: `gameState.js parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS (inalterado).

- [ ] **Step 5: Commit (partial staging — DOIS patches, um por arquivo)**

```bash
git diff -- src/gameState.js > /tmp/gs_all.patch
# montar /tmp/gs_mine.patch com o header + APENAS o hunk da linha do `const alvo`
git apply --cached /tmp/gs_mine.patch
git diff -- game.js > /tmp/gj_all.patch
# montar /tmp/gj_mine.patch com o header + APENAS os hunks de _iniciarMiraArremesso
git apply --cached /tmp/gj_mine.patch
git diff --cached -- src/gameState.js game.js   # conferir: só as edições de mira
git commit -m "feat(itens): mira de arremessáveis custom no cliente (alvo/alcance/raio do item)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Editor — destravar sub-aba Arremessáveis

**Files:**
- Modify: `tools/editor_items_editor.js`

Sem teste headless. Verificação: parse + node verde. Leia o arquivo primeiro para confirmar os nomes reusados (`TYPES`, `novoDraftPotion`, `novoDraftFor`, `renderForm`, `seccao`/`campo`/`numInput`/`selectOpts`/`chk`/`chkLbl`/`esc`, `CLASSES`, `previewFn`, `root`, `draft`, `artFile`, `artURL`, `L`). Se algum diferir, pare e reporte NEEDS_CONTEXT.

- [ ] **Step 1: Destravar a sub-aba em `TYPES`**

Troque:
```javascript
    ["arremessaveis","Arremessáveis",false],["venenos","Venenos",false]];
```
por:
```javascript
    ["arremessaveis","Arremessáveis",true],["venenos","Venenos",false]];
```

- [ ] **Step 2: Draft + roteamento**

2a. Adicione após `novoDraftPotion`:
```javascript
  function novoDraftThrowable() {
    return { name:"", emoji:"💥", item_type:"throwable", alvo:"ataque_alvo", alcance:4,
      area_raio:1, save_cd:12, tem_dano:true, die_qtd:2, die_faces:6, elemento:"fogo",
      em_chamas:false, chamas_qtd:1, chamas_faces:4, chamas_agua_apaga:true,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
```
2b. Em `novoDraftFor`, antes do `return novoDraft();`, adicione:
```javascript
    if (type === "arremessaveis") return novoDraftThrowable();
```

- [ ] **Step 3: Dispatch em `renderForm`**

Após o dispatch de `pocoes`, adicione:
```javascript
    if (activeType === "arremessaveis") { renderThrowableForm(f); return; }
```

- [ ] **Step 4: Form + leitura + preview + bind + save**

Adicione após `onSavePotion`:
```javascript
  var THROW_ALVO_LABELS = { ataque_alvo:"Mirado (teste de ataque por Destreza)", area:"Área (save de Reflexos)" };
  var THROW_ELEM_LABELS = { fogo:"Fogo", frio:"Frio", eletrico:"Elétrico", acido:"Ácido", sagrado:"Sagrado", explosao:"Explosão" };

  function renderThrowableForm(f) {
    var isArea = draft.alvo === "area";
    var faces = [4,6,8,10,12];
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">')),
      seccao("Mira",
        campo("Alvo", '<select id="ie-alvo">' + (L.THROW_TARGETS || ["ataque_alvo","area"]).map(function (a) {
          return '<option value="' + a + '"' + (a === draft.alvo ? " selected" : "") + '>' + esc(THROW_ALVO_LABELS[a] || a) + '</option>'; }).join("") + '</select>') +
        campo("Alcance (quadrados)", numInput("ie-alcance", draft.alcance, 1, 12)) +
        (isArea ? campo("Raio da área", numInput("ie-raio", draft.area_raio, 1, 3)) +
                  campo("CD do save (0 = sem save)", numInput("ie-savecd", draft.save_cd, 0, 25)) : "")),
      seccao("Dano",
        campo("Causa dano", chk("ie-temdano", draft.tem_dano)) +
        (draft.tem_dano ?
          campo("Quantidade", numInput("ie-dieq", draft.die_qtd, 1, 10)) +
          campo("Dado", '<select id="ie-dief">' + faces.map(function (x) {
            return '<option' + (x === draft.die_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
          campo("Elemento", '<select id="ie-elemento">' + (L.THROW_ELEMENTS || ["fogo"]).map(function (e) {
            return '<option value="' + e + '"' + (e === draft.elemento ? " selected" : "") + '>' + esc(THROW_ELEM_LABELS[e] || e) + '</option>'; }).join("") + '</select>')
          : '<span class="ie-hint">Sem dano: use para itens de efeito puro.</span>')),
      seccao("Incêndio",
        campo("Coloca o alvo em chamas", chk("ie-chamas", draft.em_chamas)) +
        (draft.em_chamas ?
          campo("Duração (quantidade)", numInput("ie-chamasq", draft.chamas_qtd, 1, 5)) +
          campo("Duração (dado)", '<select id="ie-chamasf">' + faces.map(function (x) {
            return '<option' + (x === draft.chamas_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>') +
          campo("Água apaga", chk("ie-chamasagua", draft.chamas_agua_apaga))
          : '<span class="ie-hint">Marque para aplicar o status "em chamas" no acerto.</span>')),
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
      '<div class="ie-actions"><button id="ie-save">💾 Salvar arremessável</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    previewFn = renderThrowablePreview;
    bindThrowableForm();
    renderThrowablePreview();
  }

  function currentThrowableDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.alvo = g("ie-alvo").value;
    draft.alcance = Math.max(1, Math.min(12, +g("ie-alcance").value || 4));
    var raio = g("ie-raio"); if (raio) draft.area_raio = Math.max(1, Math.min(3, +raio.value || 1));
    var scd = g("ie-savecd"); if (scd) draft.save_cd = Math.max(0, +scd.value || 0);
    draft.tem_dano = g("ie-temdano").checked;
    var dq = g("ie-dieq"); if (dq) draft.die_qtd = Math.max(1, +dq.value || 1);
    var df = g("ie-dief"); if (df) draft.die_faces = +df.value || 6;
    var el = g("ie-elemento"); if (el) draft.elemento = el.value;
    draft.em_chamas = g("ie-chamas").checked;
    var cq = g("ie-chamasq"); if (cq) draft.chamas_qtd = Math.max(1, +cq.value || 1);
    var cf = g("ie-chamasf"); if (cf) draft.chamas_faces = +cf.value || 4;
    var ca = g("ie-chamasagua"); if (ca) draft.chamas_agua_apaga = ca.checked;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderThrowablePreview() {
    currentThrowableDraftFromForm();
    var item = L.serializeThrowable(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPriceThrowable(item) + " 🪙";
    var parts = [item.alvo === "area" ? ("área raio " + item.area_raio) : "mirado",
                 "alcance " + item.alcance];
    if (item.dano) parts.push(item.dano + " " + (THROW_ELEM_LABELS[item.elemento] || item.elemento));
    if (item.save_cd) parts.push("Reflexos CD " + item.save_cd);
    if (item.em_chamas) parts.push("🔥 chamas " + item.chamas_dur + (item.chamas_agua_apaga ? "" : " (água não apaga)"));
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindThrowableForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderThrowablePreview; el.oninput = renderThrowablePreview;
    });
    // Alvo/dano/chamas mudam QUAIS campos existem — re-renderiza o form (padrão do ie-manejo).
    ["ie-alvo", "ie-temdano", "ie-chamas"].forEach(function (id) {
      var el = root.querySelector("#" + id);
      if (el) el.onchange = function () { currentThrowableDraftFromForm(); renderThrowableForm(root.querySelector("#ie-form")); };
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderThrowablePreview();
    };
    root.querySelector("#ie-save").onclick = onSaveThrowable;
  }

  async function onSaveThrowable() {
    currentThrowableDraftFromForm();
    var v = L.validateThrowableDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeThrowable(draft);
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

- [ ] **Step 5: Verificar e commitar**

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('parse OK')"`
Expected: `parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS.

```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor destrava sub-aba Arremessáveis

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória em `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\`

- [ ] **Step 1: Rodar a suíte no estado COMMITADO isolado**

```bash
git worktree add --detach /tmp/lfh_verify_g HEAD
cd /tmp/lfh_verify_g
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
node -e "new Function(require('fs').readFileSync('game.js','utf8')); console.log('game.js OK')"
node -e "new Function(require('fs').readFileSync('src/gameState.js','utf8')); console.log('gameState.js OK')"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify_g --force
```
Expected: `[G1]`–`[G4]` verdes, node verde, ambos os parses OK; nenhuma seção anterior quebrada. Falhas pré-existentes que **não** são regressão: `tools/test_roteamento_itens.py` (por `health_potion`, WIP do usuário), `tools/test_devorador.py` (1 teste flaky).

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase F (final do arquivo) resumindo a Fase G: sub-aba Arremessáveis, dois modos de mira (`ataque_alvo` DES vs CA / `area` com save de Reflexos), dano+elemento e "em chamas"; `_validate_custom_throwable` + `_custom_throwable_defn` (registra em `ARREMESSAVEIS`, com cleanup próprio via `custom:True` espelhando `WEAPONS`) + `_custom_throwable_inventory_dict` (carrega `alvo`/`alcance`/`area_raio` no item de bolsa); handlers de arremesso intocados; **cliente**: fallback de mira em `game.js`/`src/gameState.js` (nativos mantêm precedência do `CATALOGO_ITENS`); fora de escopo: ácido residual/corrosão, controle (cola/rede), zonas (fumaça), água benta. Cite os arquivos e o teste `[G1]`–`[G4]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-26-editor-itens-fase-g-arremessaveis.md
git commit -m "docs(itens): registra o Editor de Itens — Fase G (arremessáveis)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/editor-itens-fase-g-arremessaveis.md` (tipo `project`) resumindo: o que foi feito, o estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), contagem de checks, que esta foi a **primeira fase do Editor de Itens a tocar o cliente de jogo** (game.js/gameState.js) via partial staging, e o follow-up de smoke in-app. Adicione a linha-índice no topo de `MEMORY.md`. Linke `[[editor-itens-fase-f-pocoes]]`.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app: `python server.py` → `tools/editor.html` → aba "Editor de itens" → sub-aba Arremessáveis: criar um mirado (2d6 fogo + chamas) e uma bomba de área (3d6 explosão, raio 1, CD 13); salvar. Em jogo: comprar no mercador, e na masmorra arremessar cada um (o mirado pede clique num inimigo; o de área pede clique numa casa, com área verde no cursor) e conferir dano/save/chamas.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** sets `_ITEM_THROW_TARGETS`/`_ITEM_THROW_ELEMENTS` (T2) ✓; `_validate_custom_throwable` com alvo/alcance/dano/elemento/save-só-área/chamas + native-id incluindo `ARREMESSAVEIS` (T2) ✓; `_custom_throwable_defn` com `custom:True` (T3) ✓; `_custom_throwable_inventory_dict` com metadados de mira (T3) ✓; cleanup de `ARREMESSAVEIS` + ramo de merge (T3) ✓; duas edições cirúrgicas no cliente com precedência nativa (T4) ✓; lógica pura + UI (T1/T5) ✓; testes [G1]–[G4] incluindo uso mirado e de área (T2/T3) ✓; verificação isolada + docs + memória (T6) ✓.
- **Testes de uso:** `_room_com_alvo` (já existente) dá turno forçado, LOS livre, `atk_bonus:50` e monstro `ac:1` → o arremesso mirado sempre acerta (exceto nat1; o `atk_bonus` alto não evita nat1, mas a chance é 5% — o teste checa `hp < hp0`, e uma falha esporádica seria visível; se o revisor preferir determinismo, `random.seed` antes da chamada resolve). No `[G4]`, o CD 99 garante falha do save (dano cheio) e o herói é movido para [9,9] porque `_alvos_na_area` **inclui jogadores** (fogo amigo).
- **Consistência de tipos:** `serializeThrowable` (T1) grava `save_cd` (plano do cliente) e o servidor converte para `save:{tipo,cd}` (T2) — a UI envia `save_cd`, a validação normaliza; os testes [G1]/[G4] usam `save_cd` na entrada e checam `save` na saída. `alvo`/`alcance`/`area_raio` têm o mesmo nome em cliente e servidor.
- **Sem placeholders:** todos os passos têm código/comando concreto.
