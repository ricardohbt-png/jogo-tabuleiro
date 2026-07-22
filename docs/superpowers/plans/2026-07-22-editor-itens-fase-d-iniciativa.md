# Editor de Itens — Fase D: Bônus de iniciativa — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que equipamentos concedam um bônus fixo de iniciativa ao herói, via um efeito escalar `initiative` no motor de multi-efeito (campo `p["initiative_bonus"]`, lido em `initiative_value`).

**Architecture:** `initiative` é um efeito escalar puro (igual a `spd`): `_apply_single_effect` soma/reverte `p["initiative_bonus"]`; `initiative_value` passa a somar esse campo. Validação e editor ganham a opção. Fecha o trio B/C/D.

**Tech Stack:** Python (`server.py`), JS vanilla (`tools/editor_*`), testes `tools/test_editor_itens.py` (Python) + `tools/test_editor_items_logic.js` (Node).

**IMPORTANTE (WIP em paralelo):** o usuário reworka `server.py` (Barreira Arcana). Task de `server.py` (T1): NÃO use `git add server.py`/`-A`; STAGE APENAS SEUS HUNKS (patch + `git apply --cached`, ou `git add -p`), confirme `git diff --cached` só contém suas mudanças + o teste. Arquivos de cliente (`editor_items_logic.js`, `editor_items_editor.js`) NÃO estão no WIP → `git add` do arquivo nomeado é seguro (confirme com `git status --short`).

**Spec:** `docs/superpowers/specs/2026-07-22-editor-itens-fase-d-iniciativa-design.md`

---

## Contexto (verificado)

- `initiative_value(self, entity) = self._initiative_attribute(entity,"dex") + mod(self._initiative_attribute(entity,"int_"))` (server.py:7419). `_initiative_attribute` só recebe `dex`/`int_` → um campo `initiative_bonus` novo não colide.
- `_apply_single_effect(self, p, effect, value, equipping)`: `v = value * (1 if equipping else -1)`; ramos `atk`/`def_`/`maxhp`/`spd` (`p["spd"] += v`)/`bagslots`/`str_`/`dex`/`con_`/`int_`.
- `_ITEM_BONUS_EFFECTS = {"def_","maxhp","spd","str_","dex","con_","int_","resist"}`.
- Cliente: `BONUS_EFFECTS` (editor_items_logic.js) — o `.map` de `bonuses` em `serializeArmor` já cobre escalares (só `resist` tem caminho especial); `.ie-abonus-eff` no editor (`editor_items_editor.js`) lista as opções.

---

## Task 1: Servidor — efeito `initiative` + leitura + validação

**Files:** Modify `server.py` (`_apply_single_effect`, `initiative_value`, `_ITEM_BONUS_EFFECTS`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_itens.py` (antes de `if __name__`; `_gear_room` já existe):

```python
def test_iniciativa_bonus():
    print("\n[D1] Bônus de iniciativa (escalar + validação)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    ini0 = r.initiative_value(p)
    it = {"id": "i", "name": "I", "item_slot": "armor", "effect": "def_", "value": 0,
          "bonuses": [{"effect": "initiative", "value": 3}]}
    r._apply_gear_effect(p, it, True)
    check("equipar +3 iniciativa", r.initiative_value(p) == ini0 + 3)
    r._apply_gear_effect(p, it, True)
    check("empilhar dois = +6", r.initiative_value(p) == ini0 + 6)
    r._apply_gear_effect(p, it, False)
    check("remover um = +3", r.initiative_value(p) == ini0 + 3)
    r._apply_gear_effect(p, it, False)
    check("remover ambos volta ao inicial", r.initiative_value(p) == ini0)
    itn = {"id": "j", "name": "J", "item_slot": "armor", "effect": "def_", "value": 0,
           "bonuses": [{"effect": "initiative", "value": -2}]}
    r._apply_gear_effect(p, itn, True)
    check("valor negativo reduz", r.initiative_value(p) == ini0 - 2)
    r._apply_gear_effect(p, itn, False)
    # validação preserva o bônus escalar
    ok, itv = S._validate_custom_item(armor_sample(id="cota_ini",
        bonuses=[{"effect": "initiative", "value": 3}]))
    check("validação preserva initiative", ok and itv.get("bonuses") == [{"effect": "initiative", "value": 3}])
```

Adicione `test_iniciativa_bonus()` ao `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_editor_itens.py` → FAIL (o efeito `initiative` cai no `_apply_single_effect` e não tem ramo → nada; e a validação o descarta pois não está no allowlist).

- [ ] **Step 3: Implementar** — Três edições em `server.py`:

1) Ramo novo em `_apply_single_effect` (junto de `spd`):
```python
        elif e == "initiative":
            p["initiative_bonus"] = p.get("initiative_bonus", 0) + v
```

2) `initiative_value` soma o campo:
```python
    def initiative_value(self, entity):
        return (self._initiative_attribute(entity, "dex")
                + mod(self._initiative_attribute(entity, "int_"))
                + int(entity.get("initiative_bonus", 0) or 0))
```

3) `initiative` no allowlist de validação:
```python
_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd", "str_", "dex", "con_", "int_", "resist", "initiative"}
```

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS (incl [D1]). Rode `python tools/test_roteamento_itens.py` (deve seguir igual).

- [ ] **Step 5: Commit (PARTIAL STAGE — só seus hunks + o teste)**
```bash
git commit -m "feat(itens): bônus fixo de iniciativa (efeito escalar initiative)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Cliente — `initiative` no serialize + dropdown do editor

**Files:** Modify `tools/editor_items_logic.js`, `tools/editor_items_editor.js`; Test `tools/test_editor_items_logic.js`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_items_logic.js` (antes do `console.log` final):

```javascript
// bônus escalar initiative passa por serializeArmor (Fase D)
const aitemI = L.serializeArmor(Object.assign({}, adraft, {bonuses:[{effect:"initiative", value:3}]}));
check("serializeArmor mantém initiative", aitemI.bonuses.length === 1
  && aitemI.bonuses[0].effect === "initiative" && aitemI.bonuses[0].value === 3);
```

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_editor_items_logic.js` → FAIL (`initiative` filtrado por `BONUS_EFFECTS`).

- [ ] **Step 3: Implementar**
1) Em `tools/editor_items_logic.js`, adicione `"initiative"` a `BONUS_EFFECTS`:
```javascript
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "str_", "dex", "con_", "int_", "resist", "initiative"];
```
(O `.map` escalar já cobre — só `resist` tem caminho especial. Nenhuma outra mudança na lógica.)

2) Em `tools/editor_items_editor.js`, no `.ie-abonus-eff` do template `#ie-abonus-tpl`, adicione a opção **antes** da opção `resist` (para manter os escalares juntos). Localize `'<option value="con_">Constituição</option><option value="int_">Inteligência</option>'` e troque por:
```javascript
        '<option value="con_">Constituição</option><option value="int_">Inteligência</option>' +
        '<option value="initiative">Iniciativa</option>' +
```
(A opção `resist` continua logo depois; o input numérico da linha serve para o valor da iniciativa, positivo ou negativo.)

- [ ] **Step 4: Rodar e ver passar / verificar**
- `node tools/test_editor_items_logic.js` → PASS.
- `node --check tools/editor_items_editor.js` → OK.
- `grep -n 'value="initiative"' tools/editor_items_editor.js` → confirma a opção. Live smoke test do editor é follow-up manual.

- [ ] **Step 5: Commit**
```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js tools/editor_items_editor.js
git commit -m "feat(itens): editor/serialize aceitam bônus de iniciativa

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Docs + verificação final

**Files:** Modify `CLAUDE.md`; rodar a suíte.

- [ ] **Step 1: Nota no `CLAUDE.md`** — Acrescente um parágrafo `>` no estilo dos demais resumindo a Fase D: efeito escalar `initiative` no motor de multi-efeito (`_apply_single_effect`, como `spd`) → `p["initiative_bonus"]`, somado em `initiative_value`; vale a partir do próximo `_rebuild_initiative` (por encontro). Validação (`_ITEM_BONUS_EFFECTS`) + cliente (`BONUS_EFFECTS` + opção "Iniciativa" no dropdown) ganharam o efeito; valor pode ser negativo. Testes: `tools/test_editor_itens.py` [D1] + node. Fecha o trio B/C/D; próximas: as outras sub-abas (anéis/botas/poções/arremessáveis/venenos) + habilidades ativáveis.

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
git commit -m "docs(itens): registra o bônus de iniciativa (Fase D)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de auto-revisão (self-review deste plano)

- **Cobertura da spec:** efeito escalar + leitura + validação (T1), cliente serialize + dropdown (T2), docs (T3). Empilhamento/negativo cobertos por [D1].
- **Consistência:** efeito `initiative` e campo `p["initiative_bonus"]` usados de forma consistente entre `_apply_single_effect`, `initiative_value`, validação e cliente. `BONUS_EFFECTS` (cliente) e `_ITEM_BONUS_EFFECTS` (server) ambos ganham `"initiative"`.
- **WIP em paralelo:** T1 (server.py) usa PARTIAL STAGE; T2 (cliente) e T3 (docs) fazem `git add` do arquivo nomeado, confirmando `git status --short`.
- **Sem colisão:** `_initiative_attribute` só recebe `dex`/`int_`, então o novo campo `initiative_bonus` é distinto do padrão `<key>_bonus` que ele soma.
