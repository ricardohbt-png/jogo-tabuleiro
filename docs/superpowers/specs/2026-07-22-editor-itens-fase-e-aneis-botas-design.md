# Editor de Itens — Fase E: Anéis + Botas

**Data:** 2026-07-22
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessoras:** Fase 1 (armas), 2a (armaduras+escudos), B (atributos), C (resistências), D (iniciativa)

## Objetivo

Destravar as sub-abas **Anéis** e **Botas** do Editor de Itens (hoje aparecem com 🔒),
permitindo criar acessórios personalizados que reusam o **motor de multi-efeito** já
existente (`bonuses:[{effect,value}]`). Escopo desta fase: só anéis e botas. Elmo (`head`),
poções, arremessáveis e venenos ficam para fases futuras.

## Contexto (o que já funciona)

O **equip** de anéis/botas já é totalmente funcional no servidor:

- `_slot_category_for_item` mapeia `item_slot:"ring"` → categoria `ring` (slots `ring1`/`ring2`)
  e `item_slot:"boots"` → categoria `boots` (slot dedicado `boots`).
- `_equip_into_pair` (anéis) e `_equip_into_slot` (botas) equipam.
- `_apply_gear_effect` aplica/reverte o `effect`/`value` escalar E a lista `bonuses`
  (motor multi-efeito: `def_`/`maxhp`/`spd`/`str_`/`dex`/`con_`/`int_`/`initiative`/`resist`).
- O paperdoll do cliente já renderiza os slots **Anel 1 / Bota / Anel 2**
  (`src/ui/inventoryModal.js`).
- A compra no **mercador** roteia qualquer acessório (item_slot ≠ ammo/bag) pelo ramo
  genérico (`handle_shop_buy`, ~linha 6973) via `_route_acquired_item`, carregando `bonuses`
  no spread `{**item}`.

**Falta apenas o pipeline do Editor de Itens**: validar/normalizar, mesclar no catálogo
vivo e a UI das sub-abas. Nenhuma mudança no motor de combate/equip é necessária.

### Quirk conhecido (não alterado)

A "Botas Velozes" **nativa** usa `item_slot:"item"` (vai para `item1`/`item2`); o slot
dedicado `boots` existe em `GEAR_SLOTS` mas está vazio hoje. As botas **custom** desta
fase usam o slot dedicado `boots` (decisão de design abaixo), sem tocar na nativa.

## Decisões de design (aprovadas)

1. **Botas custom usam o slot dedicado `boots`** (`item_slot:"boots"`), não o slot `item`.
   Mais limpo; botas + 2 itens coexistem; usa o slot que já existe no paperdoll.
2. **Botas têm corrosão** (material orgânico/metal + níveis N/M), reusando a UI de armadura.
   Anéis **nunca** corroem.
3. **Adicionar `atk_bonus` (Bônus de acerto)** à lista de efeitos do motor. Habilita anéis
   de +acerto universais (paridade com o `ring_str` nativo). Como o motor é compartilhado,
   o efeito passa a valer também para armaduras/escudos (aceito).

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana"). Ao commitar, **nunca**
`git add server.py`/`-A`; stage só os hunks desta fase (via `git apply --cached` de um
patch ou `git add -p`) e confirme com `git diff --cached`.

Mudanças:

- **`_ITEM_BONUS_EFFECTS`** (linha ~21216): adicionar `"atk_bonus"` ao set.
  `_apply_single_effect` já trata `("atk","atk_bonus")` (linha ~11427) — sem código novo no motor.
- **`_validate_custom_item`** (linha ~21227): no dispatch, `it in ("ring","boots")` →
  `_validate_custom_accessory(raw)`.
- **`_validate_custom_accessory(raw)`** (novo): espelha `_validate_custom_armor`.
  - id/nome com o mesmo padrão de validação; **protege ids nativos** do `SHOP_MERCHANT`
    (`native = {i["id"] for i in SHOP_MERCHANT if not i.get("custom")}`).
  - `kind = raw["item_type"]` (`"ring"`|`"boots"`); `item_slot = kind`.
  - Lista `bonuses` normalizada com a mesma lógica do armor (incluindo `resist` com `type`).
  - `granted_ability` (metadado), `allowed_classes`, `price`, `disponibilidade`.
  - **Só botas**: `corrosion_materials` (filtrado por `_ITEM_MATERIAIS`),
    `corrosao_resistente` (≥0), `corrosao_niveis_penalidade` (≥1, default 2).
  - **Anéis**: sem campos de corrosão.
  - Retorna dict normalizado.
- **`_custom_accessory_inventory_dict(item)`** (novo): um único dict serve loja **e**
  bolsa/baú (como os anéis nativos). Campos: `id`, `name`, `emoji`, `item_slot` (ring/boots),
  `kind`, `custom:True`, `bonuses`, `granted_ability`, `price`, `allowed_classes` (se houver).
  **Sem** `effect`/`value` escalar — todo o efeito vem de `bonuses`. Botas incluem
  `corrosion_materials`/`corrosao_resistente`/`corrosao_niveis_penalidade`.
- **`_apply_custom_items`** (linha ~21407):
  - Rastrear ids custom anteriores de acessório: `SHOP_MERCHANT` (custom) +
    `_DUNGEON_ITEM_CATALOG` (custom, `kind in ("ring","boots")`). Limpar antes do merge
    (idempotente).
  - `SHOP_MERCHANT[:] = [i for i in SHOP_MERCHANT if not i.get("custom")]` (novo cleanup).
  - Merge por item: `disp["loja"]`→`SHOP_MERCHANT.append(dict)`;
    `disp["baus"] or disp["loot_monstro"]`→`_DUNGEON_ITEM_CATALOG[id]=dict`;
    `disp["loot_monstro"]`→`LOOT_POOL_PROCEDURAL.append(id)`.

**Corrosão de botas — decisão importante:** botas custom corroem **exclusivamente via
`corrosion_materials`** no dict. `_peca_corroivel` (linha ~15953) corrói peça custom pela
interseção de material (id-set só vale para nativos); o slot `boots` já está no laço de
`_corroer_equipamento` (linha ~15987). **NÃO** registrar botas nos sets
`CORROSAO_ARMADURA_METAL`/`_ORGANICA` — isso poluiria a lógica de detecção de metal dos
monstros (linhas ~18096/18131). Portanto o cleanup de acessório também não toca nesses sets.

### 2. Lógica pura (`tools/editor_items_logic.js`) — arquivo de cliente, testável por node

- `BONUS_EFFECTS`: adicionar `"atk_bonus"`.
- `serializeAccessory(d)` (novo): `kind` = `"ring"`|`"boots"` (de `d.item_type`),
  `item_slot = kind`, `emoji` default `💍`/`👢`, lista `bonuses` (reusa o filtro/normalização
  do `serializeArmor`, agora com `atk_bonus`), `granted_ability`, `allowed_classes`, `price`,
  `disponibilidade`. **Botas**: `corrosion_materials`/`corrosao_resistente`/
  `corrosao_niveis_penalidade`. **Sem** `ac_bonus`/`armor_category`.
- `validateAccessoryDraft(d)` (novo): nome obrigatório.
- `suggestPriceAccessory(item)` (novo): `KA_BONUS × Σ|valor dos bonuses|`.
- Exportar os três no `api`.

### 3. UI (`tools/editor_items_editor.js`) — arquivo de cliente, `git add` direto

- Na tabela `TYPES`, mudar `["aneis","Anéis",false]`→`true` e `["botas","Botas",false]`→`true`.
- `novoDraftAccessory(kind)` (novo): `{ name, emoji (💍/👢), item_type ("ring"/"boots"),
  bonuses:[], corrosao_livres/penalidade + materiais (só botas), granted_ability,
  allowed_classes, disponibilidade, price, id }`.
- `novoDraftFor(type)`: rotear `aneis`→`novoDraftAccessory("ring")`,
  `botas`→`novoDraftAccessory("boots")`.
- `renderAccessoryForm(f, kind)` (novo, parametrizado): Identidade → Bônus adicionais
  (reusa o template de linha de bônus, com a nova opção `<option value="atk_bonus">Bônus de
  acerto</option>`) → [só botas] Durabilidade/corrosão (reusa o bloco da armadura) →
  Restrição de classe → Disponibilidade (rótulo "Loja (Mercador)") → Preço → Imagem.
- `renderForm`: despachar `aneis`/`botas` para `renderAccessoryForm`.
- Reusar `currentArmorDraftFromForm`/`renderArmorBonuses`/`addArmorBonusRow` onde possível
  (a lista de bônus é idêntica); a seção de corrosão só aparece para botas.

### 4. Testes

- **`tools/test_editor_itens.py`** — nova seção `[E1]`–`[E…]`:
  - [E1] anel com `bonuses` (ex.: `maxhp`+`atk_bonus`) aplica/reverte no equip (`ring1`).
  - [E2] anel de atributo (ex.: `str_`) cascata no acerto (reusa lógica da Fase B).
  - [E3] anel de resistência (`resist`) entra/sai de `p["resistances"]`.
  - [E4] botas com `spd`/`initiative` aplicam; corrosão N/M por material degrada e quebra.
  - [E5] merge: `disp.loja`→`SHOP_MERCHANT`; `disp.baus/loot`→`_DUNGEON_ITEM_CATALOG`;
    `loot`→`LOOT_POOL_PROCEDURAL`. Idempotência (`_apply_custom_items` 2×).
  - [E6] rejeição de id nativo (`ring_str`) e de `item_type` inválido.
- **`tools/test_editor_items_logic.js`** — casos node para `serializeAccessory` (ring/boots),
  `validateAccessoryDraft`, `suggestPriceAccessory`, e `atk_bonus` na lista `BONUS_EFFECTS`.

Rodar da raiz. Verificar o estado **committado** num worktree isolado
(`git worktree add --detach /tmp/x HEAD`), pois o working tree roda com o WIP do usuário.

**Falhas pré-existentes (NÃO são regressão):** `tools/test_roteamento_itens.py` falha por
`health_potion` no estado committado (WIP do usuário conserta); `tools/test_devorador.py`
tem 1 teste flaky de rolagem aleatória.

## Fora de escopo

- `granted_ability` continua metadado (habilidades ativáveis = Direção C, fase futura).
- Elmo (`head`), poções, arremessáveis, venenos — fases seguintes.
- Smoke test in-app é follow-up manual do usuário (o editor não roda headless).

## Critérios de aceite

- Sub-abas Anéis e Botas ativas no editor; formulários funcionais com preview e preço sugerido.
- Anel/botas custom salvos aparecem na loja do mercador e/ou baús/loot conforme a
  disponibilidade, equipam nos slots corretos e aplicam todos os efeitos do motor multi-efeito.
- Botas corroem via material declarado (modelo N/M); anéis não corroem.
- `atk_bonus` disponível na lista de bônus (anéis, botas, armaduras, escudos).
- Testes `[E*]` (servidor) e node (lógica) verdes no estado committado isolado.
