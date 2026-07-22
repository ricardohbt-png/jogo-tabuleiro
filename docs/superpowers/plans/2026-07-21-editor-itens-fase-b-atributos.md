# Editor de Itens — Fase B: Motor de bônus de atributo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar funcionais os bônus de atributo (For/Des/Con/Int) que equipamentos concedem, estendendo o motor de multi-efeito da Fase 2a com uma cascata delta que ajusta acerto/CA/saves/PV (visão/iniciativa/dano se atualizam sozinhos).

**Architecture:** Novos tipos de efeito `str_`/`dex`/`con_`/`int_` na lista `bonuses`, aplicados por `_apply_single_effect` via um helper `_apply_attribute_delta(p, attr, delta)` que muda o atributo bruto e ajusta os derivados armazenados por delta do modificador (espelha `_reduzir_con_temporario`). Validação e editor ganham as 4 opções.

**Tech Stack:** Python (`server.py`), JS vanilla (`tools/editor_*`), testes `tools/test_editor_itens.py` (Python) + `tools/test_editor_items_logic.js` (Node).

**IMPORTANTE (WIP em paralelo):** o usuário reworka `server.py`/`game.js`/`test_roteamento_itens.py` ao mesmo tempo (WIP grande, Barreira Arcana). Para tasks de `server.py`: NÃO use `git add server.py`/`git add -A`; STAGE APENAS SEUS HUNKS (ex.: construa um patch dos seus hunks e `git apply --cached`, ou `git add -p` só dos seus), depois confirme `git diff --cached` só contém suas mudanças + o arquivo de teste. Ancore edições pelo código ao redor, não por número de linha. Arquivos de cliente (`editor_items_logic.js`, `editor_items_editor.js`) NÃO estão no WIP do usuário → `git add` direto do arquivo nomeado é seguro (mas confirme com `git status --short`).

**Spec:** `docs/superpowers/specs/2026-07-21-editor-itens-fase-b-atributos-design.md`

---

## Contexto (verificado)

- `mod(score) = (score − 10)//2` (server.py:47). `get_bonus_constituicao(con)` tabela (server.py:49).
- `_apply_single_effect(self, p, effect, value, equipping)` (server.py ~11382): computa `mult = 1 if equipping else -1; v = value*mult` e trata `atk`/`atk_bonus`, `def_`/`ac_bonus`, `maxhp` (com trava `ultimo_esforco_ativo` no top-up de HP), `spd`, `bagslots`. `_apply_gear_effect` chama-o p/ o efeito primário + cada `bonuses`.
- Atributo de ataque por classe (dos comentários de `atk_bonus` em CLASSES): warrior/mage/cleric/paladin → Força; rogue/bard → Destreza (ranger → Destreza por convenção).
- Saves: `fort = base + get_bonus_constituicao(con) + nível`; `ref_ = base + mod(dex) + nível`; `will = base + mod(int) + nível`. CA: `ac_base = 10 + mod(dex) + armadura`. `max_hp`: CON embutido.
- **Ao vivo (automáticos):** dano (`mod(p[arma.stat])`), visão (`_get_raio_visao` lê int/dex/spd), iniciativa (`initiative_value` lê dex/int). Nada a ajustar — só alterar o bruto.
- `_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd"}` (server, validação de `bonuses`). Cliente: `BONUS_EFFECTS = ["def_", "maxhp", "spd"]` (editor_items_logic.js) + dropdown no `editor_items_editor.js`.

---

## Task 1: Servidor — motor de cascata de atributo

**Files:** Modify `server.py` (`_apply_single_effect` + novo helper + constante); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_itens.py` (antes de `if __name__`):

```python
def _gear_room():
    r = S.GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop; r.send_to = noop
    return r

def _bonus_item(effect, value):
    return {"id": "x", "name": "X", "item_slot": "armor", "effect": "def_", "value": 0,
            "bonuses": [{"effect": effect, "value": value}]}

def test_atributo_forca():
    print("\n[B1] Bônus de Força (acerto por classe + simetria)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)   # warrior: ataca por Força, str_=18 (mod 4)
    atk0, str0 = p["atk_bonus"], p["str_"]
    it = _bonus_item("str_", 2)
    r._apply_gear_effect(p, it, True)
    check("str_ sobe 2", p["str_"] == str0 + 2)
    check("guerreiro: acerto sobe Δmod (+1)", p["atk_bonus"] == atk0 + 1)  # mod(20)-mod(18)=1
    r._apply_gear_effect(p, it, False)
    check("desequipar reverte str_", p["str_"] == str0)
    check("desequipar reverte acerto", p["atk_bonus"] == atk0)
    # ladino: Força NÃO muda o acerto (ataca por Destreza)
    pr = S.make_player("p2", "Luccas", "rogue", 0)
    atkr = pr["atk_bonus"]
    r._apply_gear_effect(pr, it, True)
    check("ladino: Força não muda o acerto", pr["atk_bonus"] == atkr)
    check("ladino: str_ ainda sobe (dano lê ao vivo)", pr["str_"] > 0)
    r._apply_gear_effect(pr, it, False)

def test_atributo_destreza():
    print("\n[B2] Bônus de Destreza (CA/Reflexos/acerto)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)   # dex 10 (mod 0)
    ac0, acb0, ref0, atk0 = p["ac"], p["ac_base"], p["ref_"], p["atk_bonus"]
    it = _bonus_item("dex", 2)
    r._apply_gear_effect(p, it, True)
    check("CA sobe Δmod (+1)", p["ac"] == ac0 + 1 and p["ac_base"] == acb0 + 1)
    check("Reflexos sobe (+1)", p["ref_"] == ref0 + 1)
    check("guerreiro: Destreza não muda o acerto", p["atk_bonus"] == atk0)
    r._apply_gear_effect(p, it, False)
    check("reverte CA/Reflexos", p["ac"] == ac0 and p["ref_"] == ref0)
    # ladino: Destreza muda o acerto
    pr = S.make_player("p2", "Luccas", "rogue", 0)   # dex 18 (mod 4)
    atkr = pr["atk_bonus"]
    r._apply_gear_effect(pr, it, True)
    check("ladino: Destreza sobe o acerto (+1)", pr["atk_bonus"] == atkr + 1)  # mod(20)-mod(18)=1
    r._apply_gear_effect(pr, it, False)

def test_atributo_con_int():
    print("\n[B3] Constituição (PV+Fortitude) e Inteligência (Vontade)")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)   # con 14 (cb 2), int 8 (mod -1), nível 1
    hp0, max0, fort0, will0 = p["hp"], p["max_hp"], p["fort"], p["will"]
    itc = _bonus_item("con_", 2)
    r._apply_gear_effect(p, itc, True)
    dcb = S.get_bonus_constituicao(16) - S.get_bonus_constituicao(14)   # =1
    check("max_hp sobe Δcb × nível", p["max_hp"] == max0 + dcb * p["level"])
    check("Fortitude sobe Δcb", p["fort"] == fort0 + dcb)
    check("HP atual sobe no equipar", p["hp"] == min(p["max_hp"], hp0 + dcb * p["level"]))
    r._apply_gear_effect(p, itc, False)
    check("reverte max_hp", p["max_hp"] == max0)
    check("reverte Fortitude", p["fort"] == fort0)
    iti = _bonus_item("int_", 2)
    r._apply_gear_effect(p, iti, True)
    check("Vontade sobe Δmod (+1)", p["will"] == will0 + 1)   # mod(10)-mod(8)=1
    r._apply_gear_effect(p, iti, False)
    check("reverte Vontade", p["will"] == will0)

def test_atributo_empilha_e_aovivo():
    print("\n[B4] Empilhamento simétrico + visão/iniciativa ao vivo")
    r = _gear_room()
    p = S.make_player("p1", "Victor", "warrior", 0)
    atk0, str0 = p["atk_bonus"], p["str_"]
    a = _bonus_item("str_", 2); b = dict(_bonus_item("str_", 2), id="y")
    r._apply_gear_effect(p, a, True); r._apply_gear_effect(p, b, True)
    check("dois +2 FOR: str_ +4", p["str_"] == str0 + 4)
    # remove em ordem inversa da aplicação
    r._apply_gear_effect(p, a, False); r._apply_gear_effect(p, b, False)
    check("remover ambos volta str_ ao inicial", p["str_"] == str0)
    check("remover ambos volta acerto ao inicial", p["atk_bonus"] == atk0)
    # visão e iniciativa refletem o novo DES/INT ao vivo (sem cascata explícita)
    p2 = S.make_player("p2", "Luccas", "rogue", 0); r.players["p2"] = p2
    vis0 = r._get_raio_visao(p2); ini0 = r.initiative_value(p2)
    r._apply_gear_effect(p2, _bonus_item("dex", 2), True)
    check("visão aumenta com +Destreza (ao vivo)", r._get_raio_visao(p2) >= vis0)
    check("iniciativa aumenta com +Destreza (ao vivo)", r.initiative_value(p2) == ini0 + 2)
```

Adicione `test_atributo_forca(); test_atributo_destreza(); test_atributo_con_int(); test_atributo_empilha_e_aovivo()` ao bloco `if __name__`.

> Nota: `initiative_value(p) = _initiative_attribute(dex) + mod(_initiative_attribute(int_))`. +2 DES (sem mudar INT) → +2 na iniciativa (o DES entra cru, não pelo mod). Por isso o teste espera `ini0 + 2`.

- [ ] **Step 2: Rodar e ver falhar** — `python tools/test_editor_itens.py` → FAIL (efeitos `str_`/`dex`/`con_`/`int_` são ignorados por `_apply_single_effect`).

- [ ] **Step 3: Implementar** — Adicione a constante module-level perto das outras constantes de item (ex.: perto de `_ITEM_BONUS_EFFECTS`):

```python
# Atributo que rege a jogada de ATAQUE (acerto) de cada classe — embutido no
# atk_bonus inicial de CLASSES. Usado pela cascata de bônus de atributo (Fase B).
_CLASS_ATK_ATTR = {"warrior": "str_", "mage": "str_", "cleric": "str_", "paladin": "str_",
                   "rogue": "dex", "bard": "dex", "ranger": "dex"}
```

Em `_apply_single_effect`, adicione UM ramo novo (depois do `bagslots`, antes do fim do método):

```python
        elif e in ("str_", "dex", "con_", "int_"):
            self._apply_attribute_delta(p, e, v)
```
(`v` já é o delta com sinal — `value*mult`.)

E adicione o helper (logo após `_apply_single_effect`):

```python
    def _apply_attribute_delta(self, p, attr, delta):
        """Bônus de atributo bruto (Fase B): muda p[attr] e ajusta os derivados
        ARMAZENADOS por delta do modificador. Dano/visão/iniciativa são lidos ao
        vivo do bruto e se atualizam sozinhos. Simétrico (apply/reverse exatos)."""
        antes = int(p.get(attr, 10))
        depois = max(1, antes + int(delta))
        p[attr] = depois
        if attr == "con_":
            dm = get_bonus_constituicao(depois) - get_bonus_constituicao(antes)
        else:
            dm = mod(depois) - mod(antes)
        if dm == 0:
            return
        atk_attr = _CLASS_ATK_ATTR.get(p.get("class_id"), "str_")
        if attr == "str_":
            if atk_attr == "str_":
                p["atk_bonus"] += dm; p["base_atk_bonus"] += dm
        elif attr == "dex":
            p["ac"] += dm; p["ac_base"] = p.get("ac_base", 10) + dm
            p["ref_"] = p.get("ref_", 0) + dm
            if atk_attr == "dex":
                p["atk_bonus"] += dm; p["base_atk_bonus"] += dm
        elif attr == "con_":
            level = int(p.get("level", 1))
            p["max_hp"] = max(1, p["max_hp"] + dm * level)
            if dm > 0 and not p.get("ultimo_esforco_ativo"):
                p["hp"] = min(p["max_hp"], p["hp"] + dm * level)
            elif dm < 0:
                p["hp"] = min(p["hp"], p["max_hp"])
            p["fort"] = p.get("fort", 0) + dm
        elif attr == "int_":
            p["will"] = p.get("will", 0) + dm
```

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS (incl [B1]-[B4]). Rode também `python tools/test_roteamento_itens.py` (deve seguir igual — itens sem bônus de atributo não acionam o ramo novo).

- [ ] **Step 5: Commit (PARTIAL STAGE — só seus hunks + o teste)**
```bash
# stage só suas mudanças em server.py + tools/test_editor_itens.py, verifique git diff --cached, então:
git commit -m "feat(itens): motor de bônus de atributo (cascata For/Des/Con/Int)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação aceita bônus de atributo

**Files:** Modify `server.py` (`_ITEM_BONUS_EFFECTS`); Test `tools/test_editor_itens.py`.

- [ ] **Step 1: Teste que falha** — adicione:

```python
def test_validacao_bonus_atributo():
    print("\n[B5] Validação aceita bônus de atributo")
    ok, it = S._validate_custom_item(armor_sample(id="cota_atr",
        bonuses=[{"effect": "str_", "value": 2}, {"effect": "int_", "value": 1}]))
    check("bonuses de atributo preservados", ok and it.get("bonuses") ==
          [{"effect": "str_", "value": 2}, {"effect": "int_", "value": 1}])
    ok2, it2 = S._validate_custom_item(armor_sample(id="cota_bad",
        bonuses=[{"effect": "atk", "value": 3}]))
    check("efeito fora do allowlist ainda é filtrado", ok2 and it2.get("bonuses") == [])
```

Chame `test_validacao_bonus_atributo()` no `if __name__`.

- [ ] **Step 2: Rodar e ver falhar** — FAIL (`str_`/`int_` filtrados por `_ITEM_BONUS_EFFECTS`).

- [ ] **Step 3: Implementar** — Localize `_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd"}` e troque por:

```python
_ITEM_BONUS_EFFECTS = {"def_", "maxhp", "spd", "str_", "dex", "con_", "int_"}
```

- [ ] **Step 4: Rodar e ver passar** — `python tools/test_editor_itens.py` → PASS.

- [ ] **Step 5: Commit (PARTIAL STAGE)**
```bash
git commit -m "feat(itens): validação de armadura aceita bônus de atributo

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Cliente — lógica pura aceita bônus de atributo

**Files:** Modify `tools/editor_items_logic.js`; Test `tools/test_editor_items_logic.js`.

- [ ] **Step 1: Teste que falha** — adicione ao `tools/test_editor_items_logic.js` (antes do `console.log` final):

```javascript
// bônus de atributo passam por serializeArmor
const aitem2 = L.serializeArmor(Object.assign({}, adraft, {
  bonuses:[{effect:"str_", value:2}, {effect:"con_", value:1}, {effect:"atk", value:9}]}));
check("serializeArmor mantém bônus de atributo", aitem2.bonuses.length === 2
  && aitem2.bonuses[0].effect === "str_" && aitem2.bonuses[1].effect === "con_");
check("serializeArmor filtra efeito não permitido", !aitem2.bonuses.some(function(b){return b.effect==="atk";}));
```
(`adraft` já existe no teste da Fase 2a.)

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_editor_items_logic.js` → FAIL (str_/con_ filtrados por `BONUS_EFFECTS`).

- [ ] **Step 3: Implementar** — Localize `var BONUS_EFFECTS = ["def_", "maxhp", "spd"];` e troque por:

```javascript
  var BONUS_EFFECTS = ["def_", "maxhp", "spd", "str_", "dex", "con_", "int_"];
```

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_editor_items_logic.js` → PASS.

- [ ] **Step 5: Commit**
```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): serializeArmor aceita bônus de atributo (str/dex/con/int)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Cliente — opções de atributo no dropdown do editor

**Files:** Modify `tools/editor_items_editor.js`.

- [ ] **Step 1: Localizar o dropdown** — Em `tools/editor_items_editor.js`, o form de armadura/escudo (`renderArmorForm`) tem o template de bônus com um `<select class="ie-abonus-eff">` que hoje lista `def_`/`maxhp`/`spd`. `grep -n "ie-abonus-eff" tools/editor_items_editor.js`.

- [ ] **Step 2: Adicionar as 4 opções** — No `<select class="ie-abonus-eff">…</select>`, acrescente após as opções existentes (`<option value="def_">CA extra</option><option value="maxhp">PV máx</option><option value="spd">Velocidade</option>`):

```html
<option value="str_">Força</option><option value="dex">Destreza</option><option value="con_">Constituição</option><option value="int_">Inteligência</option>
```
(Insira dentro da string HTML do template; mantenha o resto igual.)

- [ ] **Step 3: Verificação estática**
- `node --check tools/editor_items_editor.js` → OK.
- `grep -n 'value="str_"\|value="con_"' tools/editor_items_editor.js` → confirma as opções novas no select de bônus.
- O `currentArmorDraftFromForm` já lê `.ie-abonus-eff` genericamente (`r.querySelector(".ie-abonus-eff").value`), então nenhuma mudança de handler é necessária. Live smoke test do editor é follow-up manual.

- [ ] **Step 4: Commit**
```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor de armadura oferece bônus de atributo no dropdown

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Docs + verificação final

**Files:** Modify `CLAUDE.md`; rodar a suíte.

- [ ] **Step 1: Nota no `CLAUDE.md`** — Acrescente um parágrafo `>` no estilo dos demais resumindo a Fase B: efeitos `str_`/`dex`/`con_`/`int_` na lista `bonuses` do motor de multi-efeito, via `_apply_attribute_delta` (muda o atributo bruto + ajusta derivados armazenados por Δmod: acerto por classe [`_CLASS_ATK_ATTR`], CA/Reflexos [DES], Vontade [INT], Fortitude/PV [CON×nível]); dano/visão/iniciativa se atualizam sozinhos (lidos ao vivo do bruto); simétrico e independente de ordem. Validação (`_ITEM_BONUS_EFFECTS`) + editor (`BONUS_EFFECTS`/dropdown) ganham as 4 opções. Testes: `tools/test_editor_itens.py` [B1]-[B5]. Fases seguintes: C (resistências), D (iniciativa como campo próprio).

- [ ] **Step 2: Suíte completa**
```bash
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
python tools/test_devorador.py
```
Todos verdes (0 falhas). (`test_roteamento_itens.py` no estado commitado tem uma falha PRÉ-EXISTENTE de `health_potion`, não relacionada — não confundir com regressão desta fase.)

- [ ] **Step 3: Commit**
```bash
git add CLAUDE.md
git commit -m "docs(itens): registra o motor de bônus de atributo (Fase B)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Notas de auto-revisão (self-review deste plano)

- **Cobertura da spec:** helper de cascata + `_apply_single_effect` (T1), validação (T2), lógica pura cliente (T3), dropdown do editor (T4), docs (T5). Visão/iniciativa/dano ao vivo cobertos por [B4] (sem código extra). Simetria/empilhamento por [B4].
- **Mapa de classe:** `_CLASS_ATK_ATTR` derivado dos comentários de CLASSES (warrior/mage/cleric/paladin→str_, rogue/bard/ranger→dex). O teste [B1]/[B2] prova o comportamento por classe (guerreiro vs ladino).
- **Simetria:** [B1]-[B4] provam apply/reverse exatos; [B4] prova empilhamento independente de ordem.
- **WIP em paralelo:** tasks de `server.py` (T1, T2) usam PARTIAL STAGE; tasks de cliente (T3, T4) e docs (T5) fazem `git add` do arquivo nomeado (não estão no WIP), sempre confirmando `git status --short` antes.
- **Valores de Δ nos testes:** escolhidos para dar Δmod=1 limpo (Victor str 18→20, dex 10→12, con 14→16, int 8→10; Luccas dex 18→20) — reduz fragilidade.
