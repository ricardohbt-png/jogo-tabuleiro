# Editor de Itens — Fase 1: Armas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar ao editor de masmorras uma aba "Editor de itens" cuja sub-aba **Armas** cria armas personalizadas, salvas num catálogo global vivo, com efeitos passivos funcionais em combate e disponibilidade escolhível (loja/baús/loot).

**Architecture:** Espelha o "Editor de criaturas": o cliente monta um rascunho e envia por WebSocket; o servidor valida, grava `itens_personalizados.json`, regenera o índice `tools/editor_items_custom.js` e mescla os itens nos catálogos vivos (`WEAPONS`, `SHOP_WEAPONS`, `_DUNGEON_ITEM_CATALOG`, `LOOT_POOL_PROCEDURAL`). O combate lê os campos passivos direto de `p["weapon"]`.

**Tech Stack:** Python (`server.py`, `websockets`), JS vanilla (editor em `tools/`), testes: `tools/test_editor_itens.py` (Python) + `tools/test_editor_items_logic.js` (Node).

**IMPORTANTE (WIP em paralelo):** o usuário edita `server.py`/`game.js` ao mesmo tempo. Ancore cada edição pelo **código ao redor** mostrado, não por número de linha — as linhas vão mudar. Nunca use `git add -A`; adicione apenas os arquivos listados em cada Step de commit.

---

## Contrato de dados — registro de arma personalizada

Toda arma custom (em `itens_personalizados.json`, no índice JS, e mesclada nos catálogos) tem esta forma canônica:

```json
{
  "id": "espada_flamejante",
  "name": "Espada Flamejante",
  "emoji": "⚔️",
  "item_type": "weapon",
  "custom": true,
  "die": "1d8",
  "stat": "str_",
  "categoria": "cortante",
  "finesse": false,
  "reach": null,
  "range": null,
  "throw_range": null,
  "two_handed": false,
  "atk_bonus": 0,
  "damage_bonus": 1,
  "extra_damages": [{"die": "1d6", "type": "fire"}],
  "granted_ability": null,
  "allowed_classes": [],
  "price": 40,
  "disponibilidade": {"loja": true, "baus": true, "loot_monstro": false}
}
```

Regras: `reach ∈ {"lanca","cajado", null}`, `range` inteiro só quando manejo=distância, `throw_range` inteiro só quando arremessável, `extra_damages[i].type ∈ {fire,cold,lightning,acid,holy}`, `allowed_classes ⊆ {warrior,mage,rogue,cleric,ranger,paladin,bard}` (vazio = todas), `granted_ability` só metadado nesta fase.

---

## Task 1: Servidor — persistência, validação e merge nos catálogos

**Files:**
- Modify: `server.py` (bloco de persistência de monstros custom, perto de `CUSTOM_MONSTERS_FILE` / `_save_custom_monster` / `_apply_custom_monsters`)
- Create: `tools/editor_items_custom.js` (índice inicial vazio)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_editor_itens.py`:

```python
"""Editor de Itens — Fase 1 (Armas). Roda da raiz: python tools/test_editor_itens.py"""
import sys, os, json, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sample(**over):
    base = {"id": "espada_flamejante", "name": "Espada Flamejante", "emoji": "⚔️",
            "item_type": "weapon", "die": "1d8", "stat": "str_", "categoria": "cortante",
            "damage_bonus": 1, "extra_damages": [{"die": "1d6", "type": "fire"}],
            "allowed_classes": [], "price": 40,
            "disponibilidade": {"loja": True, "baus": True, "loot_monstro": True}}
    base.update(over); return base

def test_validacao():
    print("\n[1] Validação")
    ok, item = S._validate_custom_item(sample())
    check("aceita arma válida", ok)
    check("normaliza die", ok and item["die"] == "1d8")
    ok2, _ = S._validate_custom_item(sample(die="1d7"))
    check("rejeita dado inválido (1d7)", not ok2)
    ok3, _ = S._validate_custom_item(sample(categoria="magico"))
    check("rejeita categoria inválida", not ok3)
    ok4, _ = S._validate_custom_item(sample(extra_damages=[{"die": "1d6", "type": "trevas"}]))
    check("rejeita tipo elemental desconhecido", not ok4)
    native = {w["id"] for w in S.SHOP_WEAPONS}
    ok5, _ = S._validate_custom_item(sample(id="longsword"))
    check("rejeita id que colide com arma nativa", (not ok5) or ("longsword" not in native))

def test_merge():
    print("\n[2] Merge nos catálogos vivos")
    ok, item = S._validate_custom_item(sample())
    S._apply_custom_items([item])
    check("entra em WEAPONS", "espada_flamejante" in S.WEAPONS)
    check("WEAPONS carrega extra_damages", S.WEAPONS["espada_flamejante"].get("extra_damages"))
    check("loja: entra em SHOP_WEAPONS", any(w["id"] == "espada_flamejante" for w in S.SHOP_WEAPONS))
    check("baús: entra em _DUNGEON_ITEM_CATALOG", "espada_flamejante" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "espada_flamejante" in S.LOOT_POOL_PROCEDURAL)
    # Reaplicar não duplica
    S._apply_custom_items([item])
    check("reaplicar não duplica em SHOP_WEAPONS",
          sum(1 for w in S.SHOP_WEAPONS if w["id"] == "espada_flamejante") == 1)
    # Remover: aplicar lista vazia limpa os customs
    S._apply_custom_items([])
    check("lista vazia remove de WEAPONS", "espada_flamejante" not in S.WEAPONS)
    check("lista vazia remove de SHOP_WEAPONS", not any(w["id"] == "espada_flamejante" for w in S.SHOP_WEAPONS))

def test_base_intacta():
    print("\n[3] Itens base intocados")
    antes = dict(S.WEAPONS["longsword"])
    S._apply_custom_items([S._validate_custom_item(sample(id="nova_arma"))[1]])
    check("longsword base inalterada", S.WEAPONS["longsword"] == antes)
    S._apply_custom_items([])

if __name__ == "__main__":
    test_validacao(); test_merge(); test_base_intacta()
    print(f"\n{PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute '_validate_custom_item'`.

- [ ] **Step 3: Implementar no `server.py`**

Localize o bloco de persistência de monstros custom (procure `CUSTOM_MONSTERS_FILE = os.path.join(BASE_DIR, "monstros_personalizados.json")`). **Logo depois** desse bloco (após a linha `_apply_custom_monsters(_read_custom_monsters())`), adicione:

```python
# ─── ITENS PERSONALIZADOS (Editor de Itens — Fase 1: Armas) ───────────────
CUSTOM_ITEMS_FILE  = os.path.join(BASE_DIR, "itens_personalizados.json")
CUSTOM_ITEMS_INDEX = os.path.join(BASE_DIR, "tools", "editor_items_custom.js")

_ITEM_CLASSES = {"warrior", "mage", "rogue", "cleric", "ranger", "paladin", "bard"}
_ITEM_DIE_FACES = {4, 6, 8, 10, 12}
_ITEM_ELEM_TYPES = {DMG_FIRE, DMG_COLD, DMG_LIGHTNING, DMG_ACID, DMG_HOLY}
_ITEM_CATEGORIAS = {"cortante", "contundente", "perfurante"}

def _die_ok(txt):
    try:
        n, faces = str(txt).lower().split("d"); return int(n) >= 1 and int(faces) in _ITEM_DIE_FACES
    except (ValueError, AttributeError):
        return False

def _read_custom_items():
    try:
        with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []

def _validate_custom_item(raw):
    """Normaliza/valida uma arma personalizada. Só o item_type 'weapon' nesta fase."""
    if not isinstance(raw, dict):
        return False, "ficha inválida"
    if raw.get("item_type", "weapon") != "weapon":
        return False, "só armas nesta fase"
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome da arma"
    native = {w["id"] for w in SHOP_WEAPONS if not w.get("custom")} | \
             {k for k, v in WEAPONS.items() if not v.get("custom")}
    if iid in native:
        return False, "o id não pode substituir uma arma nativa"
    die = str(raw.get("die") or "")
    if not _die_ok(die):
        return False, "dado de dano inválido (use NdX, X em 4/6/8/10/12)"
    categoria = raw.get("categoria")
    if categoria not in _ITEM_CATEGORIAS:
        return False, "categoria inválida"
    stat = raw.get("stat") if raw.get("stat") in ("str_", "dex") else "str_"
    reach = raw.get("reach") if raw.get("reach") in ("lanca", "cajado") else None
    def _pos_int(v):
        try: return max(1, int(v))
        except (TypeError, ValueError): return None
    rng = _pos_int(raw.get("range")) if raw.get("range") not in (None, "", 0) else None
    throw = _pos_int(raw.get("throw_range")) if raw.get("throw_range") not in (None, "", 0) else None
    extra = []
    for xd in raw.get("extra_damages", []) or []:
        if isinstance(xd, dict) and _die_ok(xd.get("die")) and xd.get("type") in _ITEM_ELEM_TYPES:
            extra.append({"die": str(xd["die"]).lower(), "type": xd["type"]})
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    item = {
        "id": iid, "name": name, "emoji": str(raw.get("emoji") or "⚔️")[:8],
        "item_type": "weapon", "custom": True,
        "die": die.lower(), "stat": stat, "categoria": categoria,
        "finesse": bool(raw.get("finesse")), "two_handed": bool(raw.get("two_handed")),
        "atk_bonus": int(raw.get("atk_bonus", 0) or 0),
        "damage_bonus": int(raw.get("damage_bonus", 0) or 0),
        "extra_damages": extra,
        "granted_ability": (str(raw["granted_ability"]) if raw.get("granted_ability") else None),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    if reach: item["reach"] = reach
    if rng:   item["range"] = rng
    if throw: item["throw_range"] = throw
    return True, item

def _custom_weapon_combat_dict(item):
    """Cópia da arma para WEAPONS[id] (mesmo estilo dos dicts base)."""
    out = {k: item[k] for k in ("id", "name", "die", "stat", "categoria", "finesse",
            "two_handed", "atk_bonus", "damage_bonus", "extra_damages",
            "granted_ability", "reach", "range", "throw_range") if k in item}
    out["custom"] = True
    return out

def _custom_weapon_inventory_dict(item):
    """Item equipável (baús/loot/loja) — arma que entra na bolsa e equipa."""
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": "weapon", "effect": "atk", "value": 0, "custom": True,
           "price": item["price"]}
    inv.update(_custom_weapon_combat_dict(item))
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv

def _apply_custom_items(records):
    """Mescla armas custom nos catálogos vivos (idempotente: remove os customs antes)."""
    global SHOP_WEAPONS, LOOT_POOL_PROCEDURAL
    for k in [k for k, v in WEAPONS.items() if v.get("custom")]:
        WEAPONS.pop(k, None)
    SHOP_WEAPONS[:] = [w for w in SHOP_WEAPONS if not w.get("custom")]
    for k in [k for k, v in _DUNGEON_ITEM_CATALOG.items() if v.get("custom")]:
        _DUNGEON_ITEM_CATALOG.pop(k, None)
    LOOT_POOL_PROCEDURAL[:] = [i for i in LOOT_POOL_PROCEDURAL
                               if not (i in _DUNGEON_ITEM_CATALOG and _DUNGEON_ITEM_CATALOG[i].get("custom"))]
    for raw in records:
        if not isinstance(raw, dict) or raw.get("item_type", "weapon") != "weapon":
            continue
        ok, item = _validate_custom_item(raw)
        if not ok:
            continue
        WEAPONS[item["id"]] = _custom_weapon_combat_dict(item)
        disp = item["disponibilidade"]
        inv = _custom_weapon_inventory_dict(item)
        if disp["loja"]:
            SHOP_WEAPONS.append(inv)
        if disp["baus"] or disp["loot_monstro"]:
            _DUNGEON_ITEM_CATALOG[item["id"]] = inv
        if disp["loot_monstro"]:
            LOOT_POOL_PROCEDURAL.append(item["id"])

def _regen_custom_items_index(records):
    try:
        os.makedirs(os.path.dirname(CUSTOM_ITEMS_INDEX), exist_ok=True)
        payload = json.dumps(records, ensure_ascii=False, indent=2)
        with open(CUSTOM_ITEMS_INDEX, "w", encoding="utf-8") as f:
            f.write("window.EDITOR_CUSTOM_ITEMS = " + payload + ";\n"
                    "// GERADO pelo servidor ao salvar no Editor de itens.\n")
    except OSError:
        pass

def _save_custom_item(raw):
    ok, item = _validate_custom_item(raw)
    if not ok:
        return False, item
    records = [r for r in _read_custom_items()
               if isinstance(r, dict) and r.get("id") not in {item["id"], str(raw.get("original_id") or "")}]
    records.append(item)
    ok2, message = _gravar_def(records, os.path.dirname(CUSTOM_ITEMS_FILE),
                               os.path.basename(CUSTOM_ITEMS_FILE))
    if not ok2:
        return False, message
    _apply_custom_items(records)
    _regen_custom_items_index(records)
    return True, item

_apply_custom_items(_read_custom_items())
```

**Pré-requisitos que já existem** (confirme os nomes ao integrar): `DMG_FIRE/DMG_COLD/DMG_LIGHTNING/DMG_ACID/DMG_HOLY`, `WEAPONS`, `SHOP_WEAPONS`, `_DUNGEON_ITEM_CATALOG`, `LOOT_POOL_PROCEDURAL`, `_gravar_def`, `BASE_DIR`. Todos já estão definidos **acima** deste ponto no arquivo (o bloco de monstros usa `_gravar_def` e `BASE_DIR`).

- [ ] **Step 4: Criar o índice inicial vazio**

Criar `tools/editor_items_custom.js`:

```javascript
window.EDITOR_CUSTOM_ITEMS = [];
// GERADO pelo servidor ao salvar no Editor de itens.
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS (todos os checks de [1], [2], [3]).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/editor_items_custom.js tools/test_editor_itens.py
git commit -m "feat(itens): persistência+merge de armas personalizadas no catálogo vivo

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — handlers WebSocket (salvar item + upload de arte)

**Files:**
- Modify: `server.py` (dispatch WS perto de `if t == "upload_custom_monster":` e definição perto de `def _save_monster_art`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `tools/test_editor_itens.py` (antes do `if __name__`):

```python
def test_upload_art():
    print("\n[4] Upload de arte do item")
    import base64
    PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()
    ok, key = S._save_item_art("espada_flamejante.png", PNG)
    check("salva PNG válido", ok)
    dest = os.path.join(S.BASE_DIR, "assets", "itens", "espada_flamejante.png")
    check("gravou em assets/itens/<id>.png", ok and os.path.exists(dest))
    if ok and os.path.exists(dest):
        os.remove(dest)
    ok2, _ = S._save_item_art("x.gif", PNG)
    check("rejeita extensão não-png", not ok2)
    ok3, _ = S._save_item_art("y.png", base64.b64encode(b"not a png").decode())
    check("rejeita conteúdo não-PNG", not ok3)

def test_save_item():
    print("\n[5] Salvar item (fluxo completo)")
    ok, item = S._save_custom_item(sample(id="teste_persist"))
    check("save retorna ok", ok)
    check("consta no arquivo JSON", any(r.get("id") == "teste_persist" for r in S._read_custom_items()))
    check("mesclado em WEAPONS", "teste_persist" in S.WEAPONS)
    # limpa o registro de teste
    recs = [r for r in S._read_custom_items() if r.get("id") != "teste_persist"]
    S._gravar_def(recs, os.path.dirname(S.CUSTOM_ITEMS_FILE), os.path.basename(S.CUSTOM_ITEMS_FILE))
    S._apply_custom_items(recs); S._regen_custom_items_index(recs)
```

E no bloco `if __name__`, acrescente as chamadas: `test_upload_art(); test_save_item()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL — `module 'server' has no attribute '_save_item_art'`.

- [ ] **Step 3: Implementar `_save_item_art` no `server.py`**

Procure `def _save_monster_art(kind, name, data_b64):` e adicione **logo antes ou depois** dela:

```python
ITENS_DIR = os.path.join(BASE_DIR, "assets", "itens")

def _save_item_art(name, data_b64):
    """Grava o PNG de um item custom em assets/itens/<basename>. Só .png; valida a
    assinatura PNG (mesma proteção de _save_monster_art)."""
    base = os.path.basename(name or "")
    if not base or "\x00" in base or os.path.splitext(base)[1].lower() != ".png":
        return False, "envie um arquivo .png"
    if not isinstance(data_b64, str) or not data_b64:
        return False, "arquivo inválido"
    if (len(data_b64) * 3) // 4 > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except Exception:
        return False, "dados inválidos"
    if len(raw) > STORY_UPLOAD_MAX or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return False, "envie uma imagem PNG válida"
    try:
        os.makedirs(ITENS_DIR, exist_ok=True)
        with open(os.path.join(ITENS_DIR, base), "wb") as f:
            f.write(raw)
    except OSError:
        return False, "falha ao gravar"
    return True, base
```

`STORY_UPLOAD_MAX` já existe (usado por `_save_monster_art`).

- [ ] **Step 4: Adicionar os handlers WS no `server.py`**

Procure `if t == "upload_custom_monster":` e adicione **logo depois** do bloco `continue` dele:

```python
                if t == "upload_custom_item":
                    ok, res = _save_custom_item(msg.get("item"))
                    payload = {"type": "upload_result", "kind": "custom_item",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok: payload["item"] = res
                    else:  payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue

                if t == "upload_item_art":
                    ok, res = _save_item_art(msg.get("name"), msg.get("data"))
                    payload = {"type": "upload_result", "kind": "item_art",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok: payload["name"] = res
                    else:  payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS (checks [1]–[5]).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): handlers WS upload_custom_item e upload_item_art

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — efeitos passivos funcionais no combate

Liga `atk_bonus`, `damage_bonus` e `extra_damages` da arma equipada dentro de `handle_attack` (jogador).

**Files:**
- Modify: `server.py` (dentro de `async def handle_attack`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `tools/test_editor_itens.py`:

```python
import asyncio
from copy import deepcopy

def _room_com_alvo():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = "playing"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["pos"] = [1, 1]; p["atk_bonus"] = 50   # garante acerto
    r.monsters["m1"] = {"id": "m1", "name": "Alvo", "type": "orc", "hp": 999, "ac": 1,
                        "pos": [2, 1], "alive": True, "special_abilities": []}
    return r, p

def _dano_de_um_ataque(weapon):
    r, p = _room_com_alvo()
    p["weapon"] = deepcopy(weapon)
    import random; random.seed(1234)
    hp0 = r.monsters["m1"]["hp"]
    asyncio.run(r.handle_attack("p1", "m1"))
    return hp0 - r.monsters["m1"]["hp"]

def test_combate_passivo():
    print("\n[6] Efeitos passivos no combate")
    plain = {"id": "wt", "name": "T", "die": "1d8", "stat": "str_", "categoria": "cortante"}
    with_elem = dict(plain, extra_damages=[{"die": "1d6", "type": "fire"}])
    with_dmg  = dict(plain, damage_bonus=5)
    check("dano elemental soma dano extra", _dano_de_um_ataque(with_elem) > _dano_de_um_ataque(plain))
    check("damage_bonus +5 soma exatamente 5", _dano_de_um_ataque(with_dmg) - _dano_de_um_ataque(plain) == 5)

    # atk_bonus chega no eff_atk: captura o eff_atk passado a _rolar_ataque e
    # compara a diferença entre arma com bônus 7 e com bônus 0 (robusto a outros termos).
    def cap_eff(bonus):
        r, p = _room_com_alvo(); p["atk_bonus"] = 0
        p["weapon"] = {"id": "wt", "name": "T", "die": "1d8", "stat": "str_",
                       "categoria": "cortante", "atk_bonus": bonus}
        cap = {}
        orig = r._rolar_ataque
        def spy(eff_atk, *a, **k):
            cap["e"] = eff_atk; return orig(eff_atk, *a, **k)
        r._rolar_ataque = spy
        asyncio.run(r.handle_attack("p1", "m1"))
        return cap["e"]
    check("atk_bonus da arma soma +7 no eff_atk", cap_eff(7) - cap_eff(0) == 7)
```

E chame `test_combate_passivo()` no `if __name__`.

> Nota: `make_player`/`GameRoom`/`handle_attack` são o mesmo harness de `tools/test_roteamento_itens.py`. Se `make_player` exigir outros campos para `handle_attack` rodar (ex.: `fome`, `gear`), ele já os cria — o teste de roteamento usa exatamente esse setup.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL no check "dano elemental soma dano extra" (o combate ainda ignora `extra_damages`).

- [ ] **Step 3: `atk_bonus` no eff_atk**

Em `handle_attack`, localize a atribuição de `eff_atk` (procure `eff_atk = (p["atk_bonus"] + p.get("skill_bonus_acerto", 0)`). Adicione um termo ao somatório:

```python
                       + int((p.get("weapon") or {}).get("atk_bonus", 0) or 0)  # arma custom
```

(coloque junto dos outros `+ ...` do mesmo parêntese, ex.: logo após `+ self._mod_magia(p, "ataque")`).

- [ ] **Step 4: `damage_bonus` no cálculo de dano**

Localize a chamada `dmg, weapon_name, dmg_detail, raw_dmg, die_str = self._resolver_dano_ataque_basico(` e o argumento `bonus_extra=_bonus_extra + _ammo_damage_bonus,`. Troque por:

```python
                    bonus_extra=_bonus_extra + _ammo_damage_bonus
                                + int((p.get("weapon") or {}).get("damage_bonus", 0) or 0),
```

- [ ] **Step 5: `extra_damages` (dano elemental) após o dano base**

Localize o bloco do dano extra de projétil incendiário:

```python
                if _ammo_extra_dmg and target.get("hp", 1) > 0:
                    xdmg = roll_dice(_ammo_extra_dmg)
                    xdmg = self._apply_damage_types(xdmg, _ammo_extra_types, target)
                    target["hp"] = max(0, target["hp"] - xdmg)
                    await self.gm_say(f"🔥 Projétil incendiário: +{xdmg} de dano de fogo!")
```

**Logo depois** desse bloco, adicione o dano elemental da arma custom:

```python
                # ── Dano elemental adicional da arma (Editor de Itens) ──
                for _xd in (p.get("weapon") or {}).get("extra_damages", []) or []:
                    if not isinstance(_xd, dict) or target.get("hp", 1) <= 0:
                        continue
                    _xr = roll_dice(_xd.get("die", "0"))
                    if _xr <= 0:
                        continue
                    _xr = self._apply_damage_types(_xr, [_xd.get("type")], target)
                    target["hp"] = max(0, target["hp"] - _xr)
                    await self.gm_say(f"✨ Dano elemental (+{_xr} {_xd.get('type')})!")
```

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS (checks [1]–[6]).

- [ ] **Step 7: Rodar a regressão de combate existente**

Run: `python tools/test_roteamento_itens.py`
Expected: mesmo resultado de antes (sem novas falhas — as mudanças são aditivas e guardadas por `.get(...)`).

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): armas custom aplicam atk/damage bonus e dano elemental no combate

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Servidor — preservar campos custom ao comprar/equipar

Os 3 sites que reconstroem `p["weapon"]`/o item comprado usam uma whitelist de campos. Sem `extra_damages`/`atk_bonus`/`damage_bonus`/`granted_ability`, os efeitos somem ao comprar/equipar.

**Files:**
- Modify: `server.py` (3 whitelists: compra em `handle_shop_buy`; 2 syncs de `p["weapon"]`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `tools/test_editor_itens.py`:

```python
def test_compra_equipa_preserva():
    print("\n[7] Comprar+equipar preserva campos custom")
    S._apply_custom_items([S._validate_custom_item(sample(id="lamina_gelo",
        extra_damages=[{"die": "1d6", "type": "cold"}], damage_bonus=2))[1]])
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True; r.phase = "city"
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["gold"] = 9999; p["bag"] = []; p["gear"]["weapon"] = None
    asyncio.run(r.handle_shop_buy("p1", "ferreiro_weapon", "lamina_gelo"))
    comprada = next((it for it in p["bag"] if it and it.get("id") == "lamina_gelo"), None)
    check("comprada foi pra bolsa", comprada is not None)
    check("bolsa preserva extra_damages", comprada and comprada.get("extra_damages"))
    check("bolsa preserva damage_bonus", comprada and comprada.get("damage_bonus") == 2)
    # equipar da bolsa sincroniza p["weapon"]
    idx = p["bag"].index(comprada)
    asyncio.run(r._executar_equip_from_bag("p1", idx))
    check("equipar sincroniza extra_damages em p['weapon']", p["weapon"].get("extra_damages"))
    S._apply_custom_items([])
```

Chame `test_compra_equipa_preserva()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_editor_itens.py`
Expected: FAIL em "bolsa preserva extra_damages" (a whitelist de compra não copia esse campo).

- [ ] **Step 3: Estender a whitelist da compra**

Em `handle_shop_buy`, no ramo `if shop == "ferreiro_weapon":`, localize:

```python
                **{k: w[k] for k in ("die", "stat", "range", "reach",
                                     "finesse", "throw_range", "categoria",
                                     "two_handed", "dmg_bonus", "corrosao_resistente") if k in w},
```

Acrescente os campos custom à tupla:

```python
                **{k: w[k] for k in ("die", "stat", "range", "reach",
                                     "finesse", "throw_range", "categoria",
                                     "two_handed", "dmg_bonus", "corrosao_resistente",
                                     "atk_bonus", "damage_bonus", "extra_damages",
                                     "granted_ability") if k in w},
```

- [ ] **Step 4: Estender as 2 whitelists de sync de `p["weapon"]`**

Há **dois** trechos idênticos com `combat_fields = (...)` seguidos de `p["weapon"] = {k: item[k] for k in combat_fields if k in item}` (um em `_apply_gear_effect`/equip direto, outro em `_executar_equip_from_bag`). Em **ambos**, troque a tupla:

```python
            combat_fields = ("id", "name", "die", "stat", "range", "reach",
                             "finesse", "throw_range", "categoria", "two_handed",
                             "dmg_bonus", "corrosao_resistente")
```

por:

```python
            combat_fields = ("id", "name", "die", "stat", "range", "reach",
                             "finesse", "throw_range", "categoria", "two_handed",
                             "dmg_bonus", "corrosao_resistente",
                             "atk_bonus", "damage_bonus", "extra_damages", "granted_ability")
```

(mantenha a indentação de cada site.)

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_editor_itens.py`
Expected: PASS (checks [1]–[7]).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_editor_itens.py
git commit -m "feat(itens): compra/equipar preservam campos passivos das armas custom

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Cliente — módulo de lógica pura + teste Node

Lógica testável (sem DOM) partilhada pelo editor e pelo teste: slug, montagem do dado, preço sugerido, serialização e validação-espelho.

**Files:**
- Create: `tools/editor_items_logic.js`
- Test: `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_editor_items_logic.js`:

```javascript
// Roda da raiz: node tools/test_editor_items_logic.js
const L = require("./editor_items_logic.js");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

check("slugify remove acentos e espaços", L.slugify("Espada Flamejante!") === "espada_flamejante");
check("buildDie monta NdX", L.buildDie(2, 6) === "2d6");
check("suggestPrice cresce com o dado", L.suggestPrice({die:"1d10"}) > L.suggestPrice({die:"1d4"}));
check("suggestPrice soma dano elemental",
      L.suggestPrice({die:"1d6", extra_damages:[{die:"1d6",type:"fire"}]}) > L.suggestPrice({die:"1d6"}));

const draft = {name:"Espada Flamejante", emoji:"⚔️", die_qtd:1, die_faces:8,
               categoria:"cortante", stat:"str_", manejo:"corpo",
               damage_bonus:1, extra_damages:[{die:"1d6", type:"fire"}],
               allowed_classes:[], disponibilidade:{loja:true,baus:true,loot_monstro:false}, price:40};
const item = L.serializeWeapon(draft);
check("serializeWeapon gera id", item.id === "espada_flamejante");
check("serializeWeapon monta die", item.die === "1d8");
check("serializeWeapon marca item_type weapon", item.item_type === "weapon");
check("validateDraft aceita válido", L.validateDraft(draft).ok);
check("validateDraft rejeita sem nome", !L.validateDraft(Object.assign({}, draft, {name:""})).ok);

console.log(`\n${PASS} passaram, ${FAIL} falharam`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_items_logic.js`
Expected: FAIL — `Cannot find module './editor_items_logic.js'`.

- [ ] **Step 3: Implementar `tools/editor_items_logic.js`**

```javascript
/* Lógica pura do Editor de Itens (sem DOM). Carregável no browser (window) e no
   Node (module.exports) para teste. */
(function (root) {
  "use strict";
  var ELEM = ["fire", "cold", "lightning", "acid", "holy"];
  var CATS = ["cortante", "contundente", "perfurante"];
  var FACES = [4, 6, 8, 10, 12];

  function slugify(v) {
    return String(v || "").normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "arma";
  }
  function buildDie(qtd, faces) { return Math.max(1, +qtd || 1) + "d" + (+faces || 6); }
  function dieAvg(txt) {
    var m = /^(\d+)d(\d+)$/.exec(String(txt || "")); if (!m) return 0;
    return (+m[1]) * ((+m[2]) + 1) / 2;
  }
  // Preço sugerido: transparente e recalibrável (constantes no topo).
  var K_DIE = 4, K_BONUS = 6, K_ELEM = 5, K_2M = 4;
  function suggestPrice(item) {
    var p = K_DIE * dieAvg(item.die);
    p += K_BONUS * (Math.abs(+item.atk_bonus || 0) + Math.abs(+item.damage_bonus || 0));
    (item.extra_damages || []).forEach(function (x) { p += K_ELEM * dieAvg(x.die); });
    if (item.two_handed) p += K_2M;
    return Math.max(1, Math.round(p));
  }
  function serializeWeapon(d) {
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "⚔️", item_type: "weapon", custom: true,
      die: buildDie(d.die_qtd, d.die_faces),
      stat: d.stat === "dex" ? "dex" : "str_",
      categoria: CATS.indexOf(d.categoria) >= 0 ? d.categoria : "cortante",
      finesse: !!d.finesse, two_handed: !!d.two_handed,
      atk_bonus: +d.atk_bonus || 0, damage_bonus: +d.damage_bonus || 0,
      extra_damages: (d.extra_damages || []).filter(function (x) {
        return x && /^\d+d\d+$/.test(x.die) && ELEM.indexOf(x.type) >= 0;
      }).map(function (x) { return { die: x.die, type: x.type }; }),
      granted_ability: d.granted_ability || null,
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    if (d.manejo === "lanca") item.reach = "lanca";
    else if (d.manejo === "cajado") item.reach = "cajado";
    else if (d.manejo === "distancia") item.range = Math.max(1, +d.range || 4);
    if (d.manejo === "arremessavel" || d.throw_range) item.throw_range = Math.max(1, +d.throw_range || 3);
    return item;
  }
  function validateDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (FACES.indexOf(+d.die_faces) < 0) return { ok: false, msg: "dado inválido" };
    if (CATS.indexOf(d.categoria) < 0) return { ok: false, msg: "categoria inválida" };
    return { ok: true };
  }
  var api = { slugify: slugify, buildDie: buildDie, dieAvg: dieAvg,
              suggestPrice: suggestPrice, serializeWeapon: serializeWeapon,
              validateDraft: validateDraft, ELEM: ELEM, CATS: CATS, FACES: FACES };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.EDITOR_ITEMS_LOGIC = api;
})(typeof window !== "undefined" ? window : null);
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_editor_items_logic.js`
Expected: PASS (todos os checks).

- [ ] **Step 5: Commit**

```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): módulo de lógica pura do editor (slug/preço/serialização) + teste node

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Cliente — a view "Editor de itens" (sub-aba Armas)

Monta a UI, espelhando `tools/editor_monster_editor.js`. Usa `EDITOR_ITEMS_LOGIC` (Task 5) para serializar/validar/preço, `window.EDITOR_SAVE` para persistir e `EDITOR_CATALOG` para "copiar de base" e listar habilidades.

**Files:**
- Modify: `tools/editor.html` (aba, view div, script)
- Modify: `tools/editor.js` (`setTab`)
- Modify: `tools/story_upload.js` (expõe `saveCustomItem`/`uploadItemArt`)
- Create: `tools/editor_items_editor.js`

- [ ] **Step 1: Registrar aba, view e scripts em `tools/editor.html`**

No `<span id="tabs">`, após o botão `tab-editor-monstros`, adicione:

```html
      <button id="tab-editor-itens" class="tab">Editor de itens</button>
```

Antes de `<footer id="statusbar">`, adicione a view:

```html
  <div id="items-editor-view" style="display:none"></div>
```

Na lista de scripts (linha com `document.write`), inclua os dois novos módulos **antes** de `editor.js` para `editor_items_logic.js` e depois dos demais para o editor. Troque o array `s=[...]` para conter também `"editor_items_logic.js"` (logo após `"../src/difficulty.js"`) e `"editor_items_editor.js"` (ao final, junto de `"editor_campaign.js"`).

- [ ] **Step 2: Ligar a aba no `setTab` de `tools/editor.js`**

Na função `setTab(tab)`, adicione:

```javascript
    const itemsEditor = tab === "editor_itens";
    document.getElementById("items-editor-view").style.display = itemsEditor ? "" : "none";
    document.getElementById("tab-editor-itens").classList.toggle("active", itemsEditor);
```

e no encadeamento de renderização, adicione um ramo:

```javascript
    else if (itemsEditor && window.EDITOR_ITEMS_EDITOR) window.EDITOR_ITEMS_EDITOR.render();
```

e o handler de clique, junto dos outros `onclick`:

```javascript
  document.getElementById("tab-editor-itens").onclick = () => setTab("editor_itens");
```

- [ ] **Step 3: Expor `saveCustomItem`/`uploadItemArt` em `tools/story_upload.js`**

Após `function saveCustomMonster(...) {...}`, adicione:

```javascript
  function saveCustomItem(item) {
    return request("upload_custom_item", { item: item }).then((m) => m.item);
  }
  async function uploadItemArt(file, itemId) {
    if (extOf(file.name) !== ".png") throw new Error("envie um arquivo .png");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    // salva como <itemId>.png para casar com itemIconHTML (assets/itens/<id>.png)
    const m = await request("upload_item_art", { name: itemId + ".png", data: data });
    return m.name;
  }
```

E acrescente ambos ao objeto exportado `window.EDITOR_SAVE = { ... }`:

```javascript
  window.EDITOR_SAVE = { saveDungeon: saveDungeon, saveCampaign: saveCampaign,
    saveCustomMonster: saveCustomMonster, uploadMonsterArt: uploadMonsterArt,
    saveCustomItem: saveCustomItem, uploadItemArt: uploadItemArt };
```

- [ ] **Step 4: Criar `tools/editor_items_editor.js`**

Estrutura (mesmos padrões de `editor_monster_editor.js`: `esc`, sub-abas por tipo, painel de formulário). A sub-aba **Armas** é a única ativa; as outras 7 aparecem desabilitadas.

```javascript
/* Editor de Itens — Fase 1: Armas. Espelha editor_monster_editor.js. */
(function () {
  "use strict";
  var root = document.getElementById("items-editor-view");
  var L = window.EDITOR_ITEMS_LOGIC;
  var esc = function (v) { return String(v == null ? "" : v).replace(/[&<>"']/g,
    function (c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];}); };
  var TYPES = [["armas","Armas",true],["armaduras","Armaduras",false],["escudos","Escudos",false],
    ["aneis","Anéis",false],["botas","Botas",false],["pocoes","Poções",false],
    ["arremessaveis","Arremessáveis",false],["venenos","Venenos",false]];
  var CLASSES = [["warrior","Guerreiro"],["mage","Mago"],["rogue","Ladino"],
    ["cleric","Clérigo"],["ranger","Patrulheiro"],["paladin","Paladino"],["bard","Bardo"]];

  // Rascunho vivo da arma.
  var draft = null, artFile = null;
  function novoDraft() {
    return { name:"", emoji:"⚔️", die_qtd:1, die_faces:8, categoria:"cortante",
      stat:"str_", finesse:false, manejo:"corpo", range:4, throw_range:3, two_handed:false,
      atk_bonus:0, damage_bonus:0, bonus_alvo:"dano", extra_damages:[],
      granted_ability:"", allowed_classes:[],
      disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }

  function baseWeapons() {
    return ((window.EDITOR_CATALOG || {}).items || []).filter(function (i) { return i.die && i.stat; });
  }
  function abilityOptions() {
    var libs = ((window.EDITOR_CATALOG || {}).monster_abilities || [])
      .filter(function (a) { return a.source === "heroi" || a.source === "guilda"; });
    return libs.map(function (a) { return { id: a.id, name: a.name }; });
  }

  // Preenche o rascunho a partir de uma arma base (copiar-como-modelo).
  function fromBase(item) {
    var d = novoDraft();
    var m = /^(\d+)d(\d+)$/.exec(item.die || "1d6");
    if (m) { d.die_qtd = +m[1]; d.die_faces = +m[2]; }
    d.name = (item.name || "") + " (cópia)";
    d.categoria = item.categoria || "cortante";
    d.stat = item.stat === "dex" ? "dex" : "str_";
    d.finesse = !!item.finesse; d.two_handed = !!item.two_handed;
    if (item.reach === "lanca" || item.reach === "cajado") d.manejo = item.reach;
    else if (item.range) { d.manejo = "distancia"; d.range = item.range; }
    return d;
  }

  function render() {
    if (!draft) draft = novoDraft();
    var subtabs = TYPES.map(function (t) {
      return '<button class="ie-subtab' + (t[0] === "armas" ? " active" : "") + '"' +
        (t[2] ? "" : " disabled title='em breve'") + ' data-type="' + t[0] + '">' +
        esc(t[1]) + (t[2] ? "" : " 🔒") + "</button>";
    }).join("");
    root.innerHTML =
      '<div class="ie-subtabs">' + subtabs + '</div>' +
      '<div class="ie-body"><div class="ie-form" id="ie-form"></div>' +
      '<aside class="ie-preview" id="ie-preview"></aside></div>';
    root.querySelectorAll(".ie-subtab").forEach(function (b) {
      if (!b.disabled) b.onclick = function () { /* só armas nesta fase */ renderForm(); };
    });
    renderForm();
  }

  function renderForm() {
    var f = root.querySelector("#ie-form");
    var elemTypes = L.ELEM.map(function (e) { return '<option value="' + e + '">' + e + '</option>'; }).join("");
    var abil = abilityOptions();
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Emoji", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">') +
        campo("Basear em", selectBase())),
      seccao("Dano base",
        campo("Quantidade", numInput("ie-dieq", draft.die_qtd, 1, 10)) +
        campo("Dado", selectFaces()) +
        campo("Categoria", selectOpts("ie-cat", L.CATS, draft.categoria))),
      seccao("Atributo / manejo",
        campo("Atributo", selectOpts("ie-stat", ["str_","dex"], draft.stat)) +
        campo("Acuidade (finesse)", chk("ie-finesse", draft.finesse)) +
        campo("Manejo", selectOpts("ie-manejo",
          ["corpo","lanca","cajado","distancia","arremessavel"], draft.manejo)) +
        campo("Duas mãos", chk("ie-2m", draft.two_handed))),
      seccao("Bônus fixo",
        campo("Aplica em", selectOpts("ie-bonusalvo", ["ataque","dano"], draft.bonus_alvo)) +
        campo("Valor", numInput("ie-bonusval", 0, -5, 10))),
      seccao("Dano elemental adicional",
        '<div id="ie-elems"></div><button id="ie-add-elem">+ linha</button>' +
        '<template id="ie-elem-tpl"><span class="ie-elem-row">' +
        numInput("", 1, 1, 10) + ' d' +
        '<select class="ie-elem-faces">' + [4,6,8,10,12].map(function(x){return "<option>"+x+"</option>";}).join("") + '</select>' +
        ' <select class="ie-elem-type">' + elemTypes + '</select>' +
        ' <button class="ie-elem-del">✕</button></span></template>'),
      seccao("Habilidade concedida (liga em fase futura)",
        campo("Habilidade", '<select id="ie-abil"><option value="">— nenhuma —</option>' +
          abil.map(function (a) { return '<option value="' + esc(a.id) + '">' + esc(a.name) + '</option>'; }).join("") + '</select>')),
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Ferreiro)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar arma</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    bindForm();
    renderElems();
    renderPreview();
  }

  // Helpers de HTML (curtos, estilo do editor de criaturas).
  function seccao(t, body) { return '<fieldset class="ie-sec"><legend>' + esc(t) + '</legend>' + body + '</fieldset>'; }
  function campo(l, ctrl) { return '<label class="ie-field"><span>' + esc(l) + '</span>' + ctrl + '</label>'; }
  function numInput(id, v, lo, hi) { return '<input type="number"' + (id ? ' id="' + id + '"' : ' class="ie-num"') +
    ' value="' + (+v || 0) + '" min="' + lo + '" max="' + hi + '">'; }
  function chk(id, on) { return '<input type="checkbox" id="' + id + '"' + (on ? " checked" : "") + '>'; }
  function chkLbl(id, l, on) { return '<label class="ie-field">' + chk(id, on) + ' ' + esc(l) + '</label>'; }
  function selectOpts(id, arr, sel) {
    return '<select id="' + id + '">' + arr.map(function (o) {
      return '<option value="' + esc(o) + '"' + (o === sel ? " selected" : "") + '>' + esc(o) + '</option>'; }).join("") + '</select>'; }
  function selectFaces() { return '<select id="ie-dief">' + [4,6,8,10,12].map(function (x) {
      return '<option' + (x === draft.die_faces ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>'; }
  function selectBase() {
    return '<select id="ie-base"><option value="">— do zero —</option>' + baseWeapons().map(function (w) {
      return '<option value="' + esc(w.id) + '">' + esc(w.name) + '</option>'; }).join("") + '</select>'; }

  function currentDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.die_qtd = +g("ie-dieq").value; draft.die_faces = +g("ie-dief").value;
    draft.categoria = g("ie-cat").value; draft.stat = g("ie-stat").value;
    draft.finesse = g("ie-finesse").checked; draft.manejo = g("ie-manejo").value;
    draft.two_handed = g("ie-2m").checked;
    draft.bonus_alvo = g("ie-bonusalvo").value;
    var bv = +g("ie-bonusval").value || 0;
    draft.atk_bonus = draft.bonus_alvo === "ataque" ? bv : 0;
    draft.damage_bonus = draft.bonus_alvo === "dano" ? bv : 0;
    draft.granted_ability = g("ie-abil").value;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    draft.extra_damages = Array.prototype.map.call(root.querySelectorAll("#ie-elems .ie-elem-row"), function (r) {
      return { die: r.querySelector(".ie-num").value + "d" + r.querySelector(".ie-elem-faces").value, type: r.querySelector(".ie-elem-type").value }; });
    return draft;
  }

  function renderElems() {
    var box = root.querySelector("#ie-elems"); box.innerHTML = "";
    (draft.extra_damages || []).forEach(function (xd) { addElemRow(xd); });
  }
  function addElemRow(xd) {
    var tpl = root.querySelector("#ie-elem-tpl");
    var node = tpl.content.firstElementChild.cloneNode(true);
    if (xd) { var m = /^(\d+)d(\d+)$/.exec(xd.die || "1d6");
      if (m) { node.querySelector(".ie-num").value = m[1]; node.querySelector(".ie-elem-faces").value = m[2]; }
      node.querySelector(".ie-elem-type").value = xd.type || "fire"; }
    node.querySelector(".ie-elem-del").onclick = function () { node.remove(); renderPreview(); };
    node.querySelectorAll("input,select").forEach(function (el) { el.onchange = renderPreview; });
    root.querySelector("#ie-elems").appendChild(node);
  }

  function renderPreview() {
    currentDraftFromForm();
    var item = L.serializeWeapon(draft);
    var sug = L.suggestPrice(item);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + sug + " 🪙";
    var parts = [item.die + " " + item.categoria];
    (item.extra_damages || []).forEach(function (x) { parts.push("+" + x.die + " " + x.type); });
    if (item.damage_bonus) parts.push("+" + item.damage_bonus + " dano");
    if (item.atk_bonus) parts.push("+" + item.atk_bonus + " acerto");
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card"><div class="ie-card-emoji">' + esc(item.emoji) + '</div>' +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindForm() {
    root.querySelector("#ie-base").onchange = function () {
      var id = this.value;
      var w = baseWeapons().filter(function (x) { return x.id === id; })[0];
      if (w) { draft = fromBase(w); renderForm(); }
    };
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-base" || el.id === "ie-art") return;
      el.onchange = renderPreview; el.oninput = renderPreview;
    });
    // marca as classes já selecionadas
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-add-elem").onclick = function () { addElemRow(null); renderPreview(); };
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
    };
    root.querySelector("#ie-save").onclick = onSave;
  }

  async function onSave() {
    currentDraftFromForm();
    var v = L.validateDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializeWeapon(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item);
      status.textContent = "✅ salvo: " + saved.id;
      // reflete no índice em memória para o próximo "basear em"
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }

  window.EDITOR_ITEMS_EDITOR = { render: render };
})();
```

- [ ] **Step 5: Estilo mínimo (opcional, reusa `editor.css`)**

Se as seções ficarem sem espaçamento, acrescente ao fim de `tools/editor.css` regras simples para `.ie-subtabs`, `.ie-sec`, `.ie-field`, `.ie-card`. (Não é bloqueante; a funcionalidade independe do CSS.)

- [ ] **Step 6: Verificação manual no app (o editor não roda no MCP)**

O editor abre por arquivo/servidor estático, não pelo harness de testes. Verifique manualmente:
1. Suba o servidor: `python server.py` e abra `http://localhost:8765/tools/editor.html`.
2. Clique na aba **Editor de itens** → sub-aba **Armas** aparece ativa; as outras 7 aparecem com 🔒 e desabilitadas.
3. Preencha nome "Espada Flamejante", dado 1×d8, categoria cortante, adicione 1 linha de dano elemental (1d6 fogo), marque **Loja**. A **prévia** e o **preço sugerido** atualizam ao vivo.
4. (Opcional) selecione um PNG em **Imagem**.
5. Clique **💾 Salvar arma** → status "✅ salvo: espada_flamejante".
6. Confirme que `itens_personalizados.json` foi criado na raiz e `tools/editor_items_custom.js` foi regenerado com o item.

- [ ] **Step 7: Commit**

```bash
git add tools/editor.html tools/editor.js tools/story_upload.js tools/editor_items_editor.js tools/editor.css
git commit -m "feat(itens): aba Editor de itens no editor de masmorras (sub-aba Armas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Cliente — armas custom disponíveis no seletor de baús/recompensas

As armas com `disponibilidade.baus=true` devem aparecer no seletor de itens de baú/recompensa do editor de masmorras. O servidor já as coloca em `_DUNGEON_ITEM_CATALOG` (Task 1); falta o **cliente** do editor de masmorras oferecer os customs na lista.

**Files:**
- Modify: `tools/editor.js` (ou o módulo que monta a lista de itens de baú — procure onde `EDITOR_CATALOG.items` é usado para popular o seletor de baú/recompensa)

- [ ] **Step 1: Localizar o seletor de itens de baú**

Run: `grep -n "EDITOR_CATALOG" tools/editor.js tools/editor_dungeons.js` e identifique o ponto que lista `(window.EDITOR_CATALOG||{}).items` para o baú/recompensa.

- [ ] **Step 2: Mesclar os customs com `baus=true`**

No ponto identificado, componha a lista de itens candidatos assim (adaptando ao código real):

```javascript
    var baseItems = (window.EDITOR_CATALOG || {}).items || [];
    var customBaus = (window.EDITOR_CUSTOM_ITEMS || [])
      .filter(function (i) { return i.disponibilidade && i.disponibilidade.baus; })
      .map(function (i) { return { id: i.id, name: i.name, emoji: i.emoji, die: i.die,
                                   stat: i.stat, categoria: i.categoria, custom: true }; });
    var itensDoBau = baseItems.concat(customBaus);
```

Use `itensDoBau` onde antes se usava só `baseItems`.

- [ ] **Step 3: Verificação manual no app**

1. Com uma arma custom salva com **Baús** marcado, abra o editor, coloque um baú numa masmorra e abra o seletor de itens: a arma custom aparece na lista.
2. Salve a masmorra, jogue-a, abra o baú: a arma custom é obtida e pode ser equipada (o combate aplica os efeitos passivos — validado nas Tasks 3–4).

- [ ] **Step 4: Commit**

```bash
git add tools/editor.js
git commit -m "feat(itens): armas custom aparecem no seletor de baús do editor de masmorras

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Documentação e verificação final

**Files:**
- Modify: `CLAUDE.md`
- Test: rodar toda a suíte relevante

- [ ] **Step 1: Nota no `CLAUDE.md`**

Adicione um parágrafo `>` no estilo dos demais, resumindo: aba "Editor de itens" (Fase 1: Armas), catálogo global vivo (`itens_personalizados.json` + `tools/editor_items_custom.js`), campos passivos funcionais (dado/categoria/stat/manejo/`atk_bonus`/`damage_bonus`/`extra_damages`), `granted_ability` só metadado, upload PNG (`upload_item_art` → `assets/itens/<id>.png`), disponibilidade (loja/baús/loot via `_apply_custom_items` em `WEAPONS`/`SHOP_WEAPONS`/`_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL`), preço sugerido (`editor_items_logic.js`). Testes: `tools/test_editor_itens.py` e `tools/test_editor_items_logic.js`. Fases seguintes: as outras 7 abas + habilidades ativáveis funcionais.

- [ ] **Step 2: Rodar todos os testes tocados**

Run:
```bash
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
python tools/test_roteamento_itens.py
```
Expected: todos verdes (0 falhas). O de roteamento confirma que o combate/compra não regrediu.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(itens): registra o Editor de Itens Fase 1 (Armas) no CLAUDE.md

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de verificação (self-review deste plano)

- **Cobertura da spec:** persistência/merge (T1), upload PNG (T2), passivos funcionais (T3), preservação compra/equipar (T4), preço/serialização testável (T5), UI da aba+sub-abas desabilitadas (T6), disponibilidade loja (T1)/baús (T1+T7)/loot (T1), imagem (T2+T6), validação (T1+T5), `granted_ability` só metadado (T1, não lido no combate).
- **Loot de monstro:** ligado por caminho simples (append em `LOOT_POOL_PROCEDURAL` + entrada em `_DUNGEON_ITEM_CATALOG`), conforme aprovado.
- **Risco principal (dano elemental no combate):** coberto pelo teste `[6]` com comparação sob mesma seed.
- **Itens base intocados:** teste `[3]`.
- **WIP em paralelo:** todas as edições em `server.py`/`editor.js` estão ancoradas por código ao redor; commits adicionam só os arquivos nomeados.
