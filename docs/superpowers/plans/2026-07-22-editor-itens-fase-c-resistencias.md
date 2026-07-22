# Editor de Itens — Fase C: Resistências de dano do herói — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar funcional a resistência a tipos de dano concedida por equipamentos: um efeito `resist` na lista `bonuses` adiciona/remove uma entrada em `p["resistances"]`, que o já-genérico `_apply_damage_types` aplica nos caminhos de dano do jogador.

**Architecture:** Novo efeito `resist` (com um campo `type`) tratado por `_apply_resistance` no laço de `bonuses` de `_apply_gear_effect`; validação e editor ganham a opção + o dropdown de tipo. Zero mudança nos ~24 sites de dano (o `_apply_damage_types` já lê `target["resistances"]`).

**Tech Stack:** Python (`server.py`), JS vanilla (`tools/editor_*`), testes `tools/test_editor_itens.py` (Python) + `tools/test_editor_items_logic.js` (Node).

**IMPORTANTE (WIP em paralelo):** o usuário reworka `server.py` ao mesmo tempo (Barreira Arcana). Tasks de `server.py` (T1, T2): NÃO use `git add server.py`/`-A`; STAGE APENAS SEUS HUNKS (patch + `git apply --cached`, ou `git add -p`), depois confirme `git diff --cached` só contém suas mudanças + o teste. Ancore por código ao redor. Arquivos de cliente (`editor_items_logic.js`, `editor_items_editor.js`) NÃO estão no WIP → `git add` do arquivo nomeado é seguro (confirme com `git status --short`).

**Spec:** `docs/superpowers/specs/2026-07-22-editor-itens-fase-c-resistencias-design.md`

---

## Contexto (verificado)

- Constantes: `DMG_PHYSICAL="physical"`, `DMG_WATER="water"`, `DMG_FIRE="fire"`, `DMG_COLD="cold"`, `DMG_LIGHTNING="lightning"`, `DMG_HOLY="holy"`, `DMG_POISON="poison"`, `DMG_MAGIC="magic"`, `DMG_ACID="acid"` (server.py:1669-1677).
- `_apply_damage_types(raw_dmg, damage_types, target, weapon=None, …)` (server.py:16115) aplica `target.get("resistances", [])`: cada resistência é `{type, mode:"half"}` (→ `(total+1)//2`) ou `{type, reduction:N}` (→ `total-=N`). Referencia `self.round_num` no laço → o teste deve setar `r.round_num`.
- `_apply_gear_effect(p, item, equipping)` chama `_apply_single_effect` p/ o primário + cada `bonuses`.
- `_validate_custom_armor` normaliza `bonuses`:
  ```python
      for b in raw.get("bonuses", []) or []:
          if isinstance(b, dict) and b.get("effect") in _ITEM_BONUS_EFFECTS:
              bonuses.append({"effect": b["effect"], "value": _int0(b.get("value"))})
  ```
  `_ITEM_BONUS_EFFECTS = {"def_","maxhp","spd","str_","dex","con_","int_"}`.
- Editor: `renderArmorForm` tem o template `#ie-abonus-tpl` com `.ie-abonus-eff` (select) + um input `type=number`. `currentArmorDraftFromForm` mapeia cada `.ie-elem-row` para `{effect, value}`. `serializeArmor` (editor_items_logic.js) filtra `bonuses` por `BONUS_EFFECTS`.

---

## Task 1: Servidor — aplicação da resistência (`_apply_resistance`)

**Files:** Modify `server.py` (constante + helper + laço de `_apply_gear_effect`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_itens.py` (antes de `if __name__`; `_gear_room` já existe da Fase B):

```python
def _resist_item(dtype, value):
    return {"id": "r", "name": "R", "item_slot": "armor", "effect": "def_", "value": 0,
            "bonuses": [{"effect": "resist", "type": dtype, "value": value}]}

def test_resistencia_aplica():
    print("\n[C1] Resistência: aplica/remove entrada + efeito no dano")
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    # metade (value 0)
    it = _resist_item("fire", 0)
    r._apply_gear_effect(p, it, True)
    check("equipar adiciona resistência de metade",
          {"type": "fire", "mode": "half"} in p.get("resistances", []))
    check("dano de fogo cai pela metade", r._apply_damage_types(10, ["fire"], p) == 5)
    check("outro tipo não é reduzido", r._apply_damage_types(10, ["cold"], p) == 10)
    r._apply_gear_effect(p, it, False)
    check("desequipar remove a resistência", {"type": "fire", "mode": "half"} not in p.get("resistances", []))
    check("sem resistência, fogo volta ao cheio", r._apply_damage_types(10, ["fire"], p) == 10)
    # redução fixa (value 3)
    it3 = _resist_item("cold", 3)
    r._apply_gear_effect(p, it3, True)
    check("redução fixa entra como reduction", {"type": "cold", "reduction": 3} in p.get("resistances", []))
    check("dano de frio -3", r._apply_damage_types(10, ["cold"], p) == 7)
    r._apply_gear_effect(p, it3, False)

def test_resistencia_empilha():
    print("\n[C2] Resistência: empilhamento")
    r = _gear_room(); r.round_num = 1
    p = S.make_player("p1", "Victor", "warrior", 0)
    it = _resist_item("fire", 0)
    r._apply_gear_effect(p, it, True); r._apply_gear_effect(p, it, True)
    check("dois itens = duas entradas",
          sum(1 for e in p["resistances"] if e == {"type": "fire", "mode": "half"}) == 2)
    r._apply_gear_effect(p, it, False)
    check("remover um deixa uma",
          sum(1 for e in p["resistances"] if e == {"type": "fire", "mode": "half"}) == 1)
    r._apply_gear_effect(p, it, False)
    # tipo desconhecido é ignorado na aplicação
    r._apply_gear_effect(p, _resist_item("trevas", 0), True)
    check("tipo desconhecido não entra em resistances",
          not any(e.get("type") == "trevas" for e in p.get("resistances", [])))
```

Adicione `test_resistencia_aplica(); test_resistencia_empilha()` ao `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_editor_itens.py` → FAIL (o efeito `resist` cai no `_apply_single_effect` escalar, que não conhece `resist` → nada acontece).

- [ ] **Step 3: Implementar** — Adicione a constante module-level perto de `_ITEM_BONUS_EFFECTS`:

```python
_RESIST_TYPES = {DMG_PHYSICAL, DMG_FIRE, DMG_COLD, DMG_LIGHTNING, DMG_ACID,
                 DMG_HOLY, DMG_POISON, DMG_MAGIC, DMG_WATER}
```

Adicione o helper na classe `GameRoom` (perto de `_apply_single_effect`):

```python
    def _apply_resistance(self, p, bonus, equipping):
        """Bônus de resistência (Fase C): adiciona/remove uma entrada em
        p['resistances'] (lida por _apply_damage_types). value<=0 → metade
        (mode:half); value>0 → redução fixa. Empilha (uma entrada por item)."""
        dtype = bonus.get("type")
        if dtype not in _RESIST_TYPES:
            return
        val = int(bonus.get("value", 0) or 0)
        entry = {"type": dtype, "mode": "half"} if val <= 0 else {"type": dtype, "reduction": val}
        lst = p.setdefault("resistances", [])
        if equipping:
            lst.append(entry)
        else:
            for i, e in enumerate(lst):
                if e == entry:
                    lst.pop(i)
                    break
```

Em `_apply_gear_effect`, no laço de `bonuses`, roteie `resist` para o helper:

```python
    def _apply_gear_effect(self, p, item, equipping):
        self._apply_single_effect(p, item.get("effect"), item.get("value", 0), equipping)
        for b in item.get("bonuses", []) or []:
            if not isinstance(b, dict):
                continue
            if b.get("effect") == "resist":
                self._apply_resistance(p, b, equipping)
            else:
                self._apply_single_effect(p, b.get("effect"), int(b.get("value", 0) or 0), equipping)
```
(Preserve a chamada do efeito PRIMÁRIO — só o laço de `bonuses` muda.)

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS (incl [C1]/[C2]). Rode `python tools/test_roteamento_itens.py` (deve seguir igual).

- [ ] **Step 5: Commit (PARTIAL STAGE — só seus hunks + o teste)**
```bash
git commit -m "feat(itens): motor de resistência de dano do herói (efeito resist)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação preserva o `type` de resist

**Files:** Modify `server.py` (`_ITEM_BONUS_EFFECTS` + laço de `bonuses` em `_validate_custom_armor`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def test_validacao_resist():
    print("\n[C3] Validação de bônus resist (preserva type)")
    ok, it = S._validate_custom_item(armor_sample(id="cota_res",
        bonuses=[{"effect": "resist", "type": "fire", "value": 0},
                 {"effect": "resist", "type": "cold", "value": 3}]))
    check("resist preservado com type e value", ok and it.get("bonuses") ==
          [{"effect": "resist", "type": "fire", "value": 0},
           {"effect": "resist", "type": "cold", "value": 3}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="cota_res_bad",
        bonuses=[{"effect": "resist", "type": "trevas", "value": 0}]))
    check("resist com type inválido é descartado", ok2 and it2.get("bonuses") == [])
    ok3, it3 = S._validate_custom_item(armor_sample(id="cota_res_semtipo",
        bonuses=[{"effect": "resist", "value": 0}]))
    check("resist sem type é descartado", ok3 and it3.get("bonuses") == [])
    # bônus escalar continua igual
    ok4, it4 = S._validate_custom_item(armor_sample(id="cota_spd",
        bonuses=[{"effect": "spd", "value": -1}]))
    check("bônus escalar segue {effect,value}", ok4 and it4.get("bonuses") == [{"effect": "spd", "value": -1}])
```

Chame `test_validacao_resist()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (resist não está em `_ITEM_BONUS_EFFECTS`; e o `type` não é preservado).

- [ ] **Step 3: Implementar** — Adicione `"resist"` ao `_ITEM_BONUS_EFFECTS`:

```python
_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd", "str_", "dex", "con_", "int_", "resist"}
```

E troque o laço de `bonuses` em `_validate_custom_armor`:

```python
    for b in raw.get("bonuses", []) or []:
        if not (isinstance(b, dict) and b.get("effect") in _ITEM_BONUS_EFFECTS):
            continue
        if b.get("effect") == "resist":
            if b.get("type") not in _RESIST_TYPES:
                continue
            bonuses.append({"effect": "resist", "type": b["type"], "value": _int0(b.get("value"))})
        else:
            bonuses.append({"effect": b["effect"], "value": _int0(b.get("value"))})
```
`_RESIST_TYPES` (Task 1) já existe. `_int0` é o helper local já usado nesse validador.

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS (incl [C3]).

- [ ] **Step 5: Commit (PARTIAL STAGE)**
```bash
git commit -m "feat(itens): validação de armadura preserva bônus de resistência (type)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Cliente — serializeArmor preserva o `type` de resist

**Files:** Modify `tools/editor_items_logic.js`; Test `tools/test_editor_items_logic.js`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_items_logic.js` (antes do `console.log` final):

```javascript
// bônus resist preserva type; type inválido descartado (Fase C)
const aitemR = L.serializeArmor(Object.assign({}, adraft, {bonuses:[
  {effect:"resist", type:"fire", value:0},
  {effect:"resist", type:"cold", value:3},
  {effect:"resist", type:"trevas", value:0},
  {effect:"spd", value:-1}]}));
check("serializeArmor mantém resist com type/value",
  JSON.stringify(aitemR.bonuses.filter(function(b){return b.effect==="resist";}))
  === JSON.stringify([{effect:"resist",type:"fire",value:0},{effect:"resist",type:"cold",value:3}]));
check("serializeArmor descarta resist de tipo inválido",
  !aitemR.bonuses.some(function(b){return b.type==="trevas";}));
check("serializeArmor mantém bônus escalar junto do resist",
  aitemR.bonuses.some(function(b){return b.effect==="spd" && b.value===-1;}));
```

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_editor_items_logic.js` → FAIL (`resist` filtrado por `BONUS_EFFECTS`; `type` não preservado).

- [ ] **Step 3: Implementar** — Em `tools/editor_items_logic.js`:
1) Adicione `"resist"` a `BONUS_EFFECTS`:
```javascript
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "str_", "dex", "con_", "int_", "resist"];
```
2) Adicione a constante de tipos (perto de `ARMOR_CATS`):
```javascript
  var RESIST_TYPES = ["physical", "fire", "cold", "lightning", "acid", "holy", "poison", "magic", "water"];
```
3) No `serializeArmor`, troque o `.filter(...).map(...)` de `bonuses` por:
```javascript
      bonuses: (d.bonuses || []).filter(function (b) {
        if (!b || BONUS_EFFECTS.indexOf(b.effect) < 0) return false;
        if (b.effect === "resist" && RESIST_TYPES.indexOf(b.type) < 0) return false;
        return true;
      }).map(function (b) {
        return b.effect === "resist"
          ? { effect: "resist", type: b.type, value: +b.value || 0 }
          : { effect: b.effect, value: +b.value || 0 };
      }),
```
4) Exporte `RESIST_TYPES` no objeto `api` (junto de `BONUS_EFFECTS`).

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_editor_items_logic.js` → PASS.

- [ ] **Step 5: Commit**
```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): serializeArmor preserva bônus de resistência (type)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Cliente — dropdown de tipo de resistência no editor

**Files:** Modify `tools/editor_items_editor.js`.

- [ ] **Step 1: Adicionar a opção "Resistência" + o select de tipo no template** — No `renderArmorForm`, no template `#ie-abonus-tpl`, o `.ie-abonus-eff` recebe uma nova opção e ganha um `.ie-abonus-type` (oculto por padrão). Localize o `<select class="ie-abonus-eff">…</select>` (com as opções def_/maxhp/spd/str_/dex/con_/int_) e:
  1) acrescente `<option value="resist">Resistência</option>` ao final das opções;
  2) logo após o `</select>` do `.ie-abonus-eff`, insira o select de tipo:
```html
<select class="ie-abonus-type" style="display:none"><option value="physical">Físico</option><option value="fire">Fogo</option><option value="cold">Frio</option><option value="lightning">Elétrico</option><option value="acid">Ácido</option><option value="holy">Sagrado</option><option value="poison">Veneno</option><option value="magic">Mágico</option><option value="water">Água</option></select>
```
  (Mantenha o input `type=number` e o botão `.ie-abonus-del` na linha; o número vira "0 = metade / >0 = redução fixa".)

- [ ] **Step 2: Mostrar/ocultar o select de tipo conforme o efeito** — Em `addArmorBonusRow(b)` (onde a linha é clonada e os handlers ligados), adicione:
```javascript
    var effSel = node.querySelector(".ie-abonus-eff");
    var typeSel = node.querySelector(".ie-abonus-type");
    function _syncType() { typeSel.style.display = (effSel.value === "resist") ? "" : "none"; }
    effSel.addEventListener("change", _syncType);
    if (b) {
      if (b.effect) effSel.value = b.effect;
      if (b.effect === "resist" && b.type) typeSel.value = b.type;
    }
    _syncType();
```
(Integre com o código de restauração já existente de `addArmorBonusRow` — não duplique a definição de `effSel`/`typeSel` se já houver; ajuste ao real. Mantenha o `onchange`→`renderArmorPreview` já ligado aos inputs/selects da linha, para o `.ie-abonus-type` também disparar o preview.)

- [ ] **Step 3: Ler o `type` no draft** — Em `currentArmorDraftFromForm`, troque o `.map` de `#ie-abonus .ie-elem-row` por:
```javascript
    draft.bonuses = Array.prototype.map.call(root.querySelectorAll("#ie-abonus .ie-elem-row"), function (r) {
      var eff = r.querySelector(".ie-abonus-eff").value;
      var o = { effect: eff, value: +r.querySelector("input[type=number]").value || 0 };
      if (eff === "resist") { var t = r.querySelector(".ie-abonus-type"); o.type = t ? t.value : "fire"; }
      return o;
    });
```

- [ ] **Step 4: Verificação estática**
- `node --check tools/editor_items_editor.js` → OK.
- `grep -n 'ie-abonus-type\|value="resist"' tools/editor_items_editor.js` → confirma o select de tipo + a opção resist.
- Cross-check: `addArmorBonusRow` e `currentArmorDraftFromForm` referenciam `.ie-abonus-type`, que o template emite. Live smoke test do editor é follow-up manual.

- [ ] **Step 5: Commit**
```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor de armadura oferece resistência com tipo no dropdown

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Docs + verificação final

**Files:** Modify `CLAUDE.md`; rodar a suíte.

- [ ] **Step 1: Nota no `CLAUDE.md`** — Acrescente um parágrafo `>` no estilo dos demais resumindo a Fase C: efeito `resist` na lista `bonuses` (via `_apply_resistance` no laço de `_apply_gear_effect`) adiciona/remove `{type, mode:"half"}` (value≤0) ou `{type, reduction:N}` (value>0) em `p["resistances"]`; `_apply_damage_types` (já genérico pelo alvo) aplica a redução nos caminhos de dano do jogador — sem tocar nos ~24 sites. Tipos: `_RESIST_TYPES` (9). Validação (`_ITEM_BONUS_EFFECTS`) preserva `type`; editor (`BONUS_EFFECTS`/`RESIST_TYPES` + dropdown de tipo condicional). Testes: `tools/test_editor_itens.py` [C1]-[C3] + node. Fase seguinte: D (iniciativa como campo próprio).

- [ ] **Step 2: Suíte completa**
```bash
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
python tools/test_devorador.py
```
Todos verdes (0 falhas). (`test_roteamento_itens.py` no estado commitado tem a falha PRÉ-EXISTENTE de `health_potion`, não relacionada.)

- [ ] **Step 3: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(itens): registra as resistências de dano do herói (Fase C)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de auto-revisão (self-review deste plano)

- **Cobertura da spec:** motor `_apply_resistance` + laço (T1), validação com `type` (T2), serializeArmor cliente (T3), dropdown de tipo (T4), docs (T5). Efeito no dano coberto por [C1] via `_apply_damage_types`; empilhamento e tipo-inválido por [C1]/[C2]/[C3].
- **`r.round_num`** setado nos testes de resistência (o `_apply_damage_types` referencia `self.round_num`).
- **Convenção value 0=metade / >0=redução:** implementada em `_apply_resistance` (`val <= 0`) e provada por [C1].
- **WIP em paralelo:** T1/T2 (server.py) usam PARTIAL STAGE; T3/T4 (cliente) e T5 (docs) fazem `git add` do arquivo nomeado, confirmando `git status --short`.
- **Consistência:** `_RESIST_TYPES` (server) e `RESIST_TYPES` (cliente) listam os mesmos 9 tipos; `_apply_resistance`/`_apply_gear_effect`/validação usam `"resist"` e o campo `type` de forma consistente.
