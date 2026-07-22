# Editor de Itens — Fase C: Resistências de dano do herói (design)

Data: 2026-07-22
Status: aprovado (aguardando revisão da spec escrita)

## Objetivo

Tornar funcional a **resistência a tipos de dano** que equipamentos podem conceder
ao herói. Adiciona um efeito `resist` à lista `bonuses` do motor de multi-efeito
(Fase 2a/B): ao equipar, acrescenta uma entrada em `p["resistances"]`; ao desequipar,
remove a correspondente. Como `_apply_damage_types` já lê `target.get("resistances")`
e é chamado com o **jogador** como alvo nos caminhos de dano tipado, a redução passa a
valer automaticamente — sem tocar nos ~24 call sites de dano.

## Decisões de brainstorming (fixadas)

1. **Modelos suportados:** metade (`mode:"half"`) **e** redução fixa (`reduction:N`),
   escolhidos por item via a convenção do `value` (abaixo).
2. **Tipos resistíveis:** todos — `physical, fire, cold, lightning, acid, holy,
   poison, magic, water`.
3. **Convenção do `value`:** `value = 0 → metade`; `value > 0 → redução fixa de N`
   (evita um 3º controle "modo" no editor).
4. **A entrada `resist` carrega um `type`** — estende a forma `{effect,value}` do bônus
   com um campo `type`.

## Contexto do motor (explorado)

- `_apply_damage_types(raw_dmg, damage_types, target, weapon=None, …)` (server.py:16115)
  já aplica `target.get("resistances", [])`, `immunities`, `weaknesses`, `subtipo`.
  Cada resistência é `{type, mode:"half"}` **ou** `{type, reduction:N}` (redução antes da
  vulnerabilidade). Para `target` = jogador, `subtipo` cai em `raca_padrao` (sem regras
  especiais) e as listas ausentes são `[]` → hoje aplica nada.
- É chamado com o JOGADOR como alvo em vários caminhos (ataque de monstro, elementais,
  armadilhas, gás/ácido, fogo, retaliação). Dar ao herói uma lista `resistances` faz a
  redução valer nesses caminhos sem novos hooks.
- Motor de multi-efeito (Fase 2a/B): `_apply_gear_effect(p, item, equipping)` chama
  `_apply_single_effect(p, item.get("effect"), item.get("value",0), equipping)` para o
  efeito primário e para cada entrada de `item.get("bonuses", [])`. `_apply_single_effect`
  é **escalar** (só effect+value) — não comporta um `type`.
- Validação: `_validate_custom_armor` filtra `bonuses` a `{effect, value}` com
  `effect in _ITEM_BONUS_EFFECTS` (`{"def_","maxhp","spd","str_","dex","con_","int_"}`).
- Cliente: `BONUS_EFFECTS` (editor_items_logic.js) + dropdown de bônus em
  `editor_items_editor.js` (`.ie-abonus-eff` select + input numérico por linha).

## Contrato — entrada de bônus de resistência

```json
{"effect": "resist", "type": "fire", "value": 0}
```
- `value = 0` → resistência de **metade** (`{"type":"fire","mode":"half"}` em `resistances`).
- `value > 0` → **redução fixa** (`{"type":"fire","reduction":N}`).
- `type ∈ {physical, fire, cold, lightning, acid, holy, poison, magic, water}`.

## Componentes

### 1. Servidor — aplicação da resistência (`_apply_resistance`)
- Helper novo `_apply_resistance(self, p, bonus, equipping)`:
  - `dtype = bonus.get("type")`; se `dtype not in _RESIST_TYPES` → retorna (ignora).
  - `val = int(bonus.get("value", 0) or 0)`;
    `entry = {"type": dtype, "mode": "half"}` se `val <= 0`, senão `{"type": dtype, "reduction": val}`.
  - `lst = p.setdefault("resistances", [])`; equipar → `lst.append(entry)`; desequipar →
    remove a **primeira** entrada igual (`==`) — empilhamento correto (dois itens do
    mesmo tipo/valor somam duas entradas; remover um tira uma).
- Constante module-level `_RESIST_TYPES = {DMG_PHYSICAL, DMG_FIRE, DMG_COLD,
  DMG_LIGHTNING, DMG_ACID, DMG_HOLY, DMG_POISON, DMG_MAGIC, DMG_WATER}`.
- Em `_apply_gear_effect`, no laço de `bonuses`: se `b.get("effect") == "resist"` →
  `self._apply_resistance(p, b, equipping)`; senão o caminho escalar existente
  (`_apply_single_effect(p, b.get("effect"), int(b.get("value",0) or 0), equipping)`).
  `resist` nunca é efeito primário (o primário da armadura é `def_`), então só o laço
  muda.

### 2. Servidor — validação preserva o `type`
- Adicionar `"resist"` a `_ITEM_BONUS_EFFECTS`.
- Na normalização de `bonuses` em `_validate_custom_armor`: para uma entrada com
  `effect == "resist"`, validar `type` contra `_RESIST_TYPES` (descartar a entrada se o
  tipo for desconhecido) e emitir `{"effect":"resist","type":<dtype>,"value":<int>}`;
  para os demais efeitos, manter `{"effect","value"}` como hoje.

### 3. Cliente — lógica pura (`serializeArmor`)
- `BONUS_EFFECTS` (editor_items_logic.js) ganha `"resist"`.
- O `.map` de `bonuses` em `serializeArmor` preserva o `type` quando `effect === "resist"`
  (filtrando por um `RESIST_TYPES` no cliente): emite `{effect:"resist", type, value}`;
  para os demais, `{effect, value}` como hoje.

### 4. Cliente — editor (dropdown de tipo condicional)
- Na linha de bônus (`renderArmorForm`/template `#ie-abonus-tpl`), adicionar a opção
  **"Resistência"** (`value="resist"`) ao `.ie-abonus-eff` e um `.ie-abonus-type` select
  com os 9 tipos, **visível só quando o efeito é `resist`** (toggle por `onchange` do
  `.ie-abonus-eff`, ou sempre presente porém só lido quando resist).
- `currentArmorDraftFromForm`/`addArmorBonusRow`: ler/gravar `type` da linha quando o
  efeito é `resist` (para os demais, `type` ausente).
- Dica de UX: label do valor ("0 = metade; >0 = redução fixa").

### 5. Testes
`tools/test_editor_itens.py`:
- **Aplicação**: equipar item com `{effect:"resist",type:"fire",value:0}` →
  `p["resistances"]` contém `{"type":"fire","mode":"half"}`; desequipar remove.
  Com `value:3` → `{"type":"fire","reduction":3}`.
- **Efeito no dano**: com resistência-metade, `_apply_damage_types(10, ["fire"], jog)` == 5;
  com `reduction:3`, == 7; outro tipo (`["cold"]`) inalterado (== 10).
- **Empilhamento**: dois `resist fire` → 2 entradas; remover um deixa 1.
- **Validação**: `bonuses` com `resist`+`type` válido preservado; `type` desconhecido
  descartado; `resist` sem `type` descartado.

`tools/test_editor_items_logic.js` (node): `serializeArmor` preserva `type` em bônus
`resist` e descarta tipo inválido.

## Fora de escopo

- **Imunidade total** e **vulnerabilidade (fraqueza)** do herói (só resistência aqui);
- Fase D (iniciativa como campo próprio);
- as outras sub-abas (anéis/botas/poções/arremessáveis/venenos) — o motor já fica pronto
  para elas usarem `resist`;
- garantir que 100% dos caminhos de dano tipam o dano do jogador — a resistência vale
  onde o motor já chama `_apply_damage_types` com o jogador; caminhos que hoje não tipam
  o dano (se houver) ficam como estão (não é regressão).
