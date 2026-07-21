# Editor de Itens — Fase 2a: Armaduras + Escudos (design)

Data: 2026-07-21
Status: aprovado (aguardando revisão da spec escrita)

## Objetivo

Habilitar no "Editor de itens" (aba do editor de masmorras) as sub-abas
**Armaduras** e **Escudos**, criando peças de defesa personalizadas que entram no
catálogo global vivo e funcionam no jogo. Esta é a **Fase 2a**: entrega o editor +
os bônus que o motor de equipamento **já suporta** (CA, PV máximo, velocidade) + um
**motor de corrosão de peças de defesa generalizado** (armadura/escudo/elmo/botas,
com N/M como as armas) + metadados. As capacidades de motor novas — bônus de **atributo**
(B), **resistências** de dano (C) e **iniciativa** (D) — são incrementos seguintes,
cada um ligando seus campos no editor quando chegar.

## Decisões de brainstorming (fixadas)

1. **Fatiamento:** A (este design) primeiro; B/C/D depois como incrementos focados.
2. **Bônus de atributo:** serão funcionais (Fase B), NÃO nesta fase. Os campos de
   atributo/resistência/iniciativa **não** aparecem na UI de A (evita controle morto).
3. **Bônus adicionais em A:** CA extra, PV máximo, velocidade (efeitos que o motor já
   conhece), via um **motor de multi-efeito** novo (lista `bonuses`).
4. **Corrosão generalizada:** o sistema de quebra por corrosão+material passa a valer
   para **armadura, escudo, elmo e botas** (não só armadura de corpo), com o modelo
   **N/M** das armas; peças base permanecem byte-idênticas (N=0/M=2). Editor expõe
   material+N/M para armadura e escudo agora; botas/elmos ficam engine-ready.
5. Carrega da Fase 1 (Armas), sem re-perguntar: catálogo global vivo (mesmo
   `itens_personalizados.json`, com `item_type` `"armor"`/`"shield"`), efeitos passivos
   funcionais + `granted_ability` só metadado, copiar-como-modelo, upload PNG,
   disponibilidade (loja/baús/loot), preço sugerido.

## Contexto do motor (explorado)

- **Armaduras/escudos base** (`SHOP_ARMORS`, server.py): `ac_bonus`, `kind`
  (`armor`/`shield`), `armor_category` (`leve`/`media`/`pesada` — hoje só autoral,
  prepara penalidade de peso futura), `corrosion_materials` (lista `organic`/`metal`;
  híbrido sofre os dois), `allowed_classes`. Escudos base **não** têm material (não
  corroem).
- **Compra** (`handle_shop_buy`, ramo `ferreiro_armor`): converte `ac_bonus` num
  `gear_item` com `item_slot` (`armor`/`shield`), `effect:"def_"`, `value:ac_bonus`,
  e, para armadura, copia `armor_category`/`corrosion_materials`. Roteia por
  `_route_acquired_item` (bolsa-primeiro).
- **Aplicação de efeito** (`_apply_gear_effect`): trata **um** efeito por item —
  `def_`/`ac_bonus` (CA), `maxhp`, `spd`, `atk`, `bagslots`. Há também
  `_recalculate_ac(p)` (recomputa CA de armadura + slots `def_` + mod(DES)). **O plano
  deve confirmar qual mecanismo é autoritativo no equipar para não duplicar a CA** ao
  adicionar a lista `bonuses`.
- **Corrosão de armadura**: id-sets `CORROSAO_ARMADURA_METAL` /
  `CORROSAO_ARMADURA_ORGANICA`; modelo de 3 níveis (danificado −1 CA, quebrado −2,
  destruído no 3º). Como nas armas, **armadura custom só corrói se declarar material**
  (registra o id no set certo no merge).
- **Infra da Fase 1** (server.py): `_validate_custom_item`, `_apply_custom_items`,
  `_custom_weapon_combat_dict`/`_custom_weapon_inventory_dict`, `_save_custom_item`,
  `_read/_regen_custom_items_*`, handlers WS `upload_custom_item`/`upload_item_art`,
  merge idempotente. A Fase 2a **generaliza** essa infra para despachar por `item_type`.

## Contrato de dados — registro de armadura/escudo

```json
{
  "id": "cota_encantada", "name": "Cota Encantada", "emoji": "🛡️",
  "item_type": "armor", "custom": true,
  "kind": "armor",
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

Regras:
- `item_type ∈ {"armor","shield"}`; `kind` = `item_type` (mantido para o motor).
- `ac_bonus` inteiro ≥ 0 (defesa base da peça).
- `armor_category ∈ {"leve","media","pesada", null}` **só para `armor`** (escudo ignora).
- `corrosion_materials ⊆ {"organic","metal"}` para **armor E shield** (ambos corroem);
  `corrosao_resistente` (N níveis sem penalidade, ≥0) + `corrosao_niveis_penalidade`
  (M níveis com penalidade, ≥1, default 2) — mesmo modelo N/M das armas.
- `bonuses[i].effect ∈ {"def_","maxhp","spd"}` nesta fase (CA extra / PV máx /
  velocidade); `value` inteiro (pode ser negativo, ex.: penalidade de velocidade).
- `granted_ability` só metadado; `allowed_classes ⊆ 6 classes`; `price ≥ 0`;
  `disponibilidade` booleanos.

## Componentes

### 1. Servidor — validação e merge (generalização da Fase 1)
- `_validate_custom_item(raw)` passa a **despachar por `item_type`**: `weapon` →
  validação atual (extraída para `_validate_custom_weapon`); `armor`/`shield` → nova
  `_validate_custom_armor` (normaliza os campos acima; escudo zera só a categoria —
  material/corrosão valem para escudo também).
- `_apply_custom_items(records)` passa a **rotear por `item_type`**:
  - armadura/escudo → registra em `SHOP_ARMORS` (se `loja`), `_DUNGEON_ITEM_CATALOG`
    (se `baus`/`loot`), `LOOT_POOL_PROCEDURAL` (se `loot`);
  - material → sets de corrosão do slot certo (ver Componente 3), armadura E escudo;
  - **limpeza idempotente**: além de WEAPONS/SHOP_WEAPONS/RANGED_AMMO/sets de arma,
    remover os ids custom de `SHOP_ARMORS` e dos sets de corrosão de defesa antes de
    re-adicionar.
- Helpers novos `_custom_armor_shop_dict(item)` (entrada de `SHOP_ARMORS`: id, name,
  emoji, ac_bonus, kind, price, armor_category, corrosion_materials, allowed_classes,
  bonuses, granted_ability, custom) e `_custom_armor_inventory_dict(item)` (peça
  equipável para baús/loot: `item_slot` armor/shield, `effect:"def_"`, `value:ac_bonus`,
  armor_category, corrosion_materials, bonuses, granted_ability, custom).

### 2. Servidor — motor de multi-efeito (`bonuses`)
- Extrair a lógica por-efeito de `_apply_gear_effect` para `_apply_single_effect(p,
  effect, value, equipping)`; `_apply_gear_effect` chama-a para o efeito primário do
  item **e** para cada entrada de `item.get("bonuses", [])`.
- Simétrico no desequipar (reverte cada bônus). Preservar a trava do top-up de HP do
  `maxhp` (Último Esforço) já existente.
- Garantir que os `bonuses` sobrevivem em `gear_item` no ramo `ferreiro_armor` de
  `handle_shop_buy` e nas whitelists de equipar de armadura/escudo.

### 3. Servidor — motor de corrosão de peças de defesa (generalizado, N/M)
Hoje a corrosão cobre só a **armadura de corpo** e a **arma**. Passa a cobrir os
**quatro slots de defesa** — armadura (`armor`), escudo (`off_hand` shield), elmo
(`head`) e botas (`boots`) — cada peça com `corrosion_materials` + `corrosao_resistente`
(N) + `corrosao_niveis_penalidade` (M), espelhando o modelo N/M das armas (penalidade
escala −1/nível até −M, quebra em N+M+1).
- **Generalizar** `_corr` (uma trilha `lvl`/`destruido` por slot de defesa, além da
  arma), `_corroer_equipamento` (alvos por slot; a ordem de prioridade fica no plano) e
  as penalidades: cada peça corroída **reduz o bônus que concede** por −nível — CA para
  armadura/escudo/elmo-`def_`, PV para elmo-`maxhp`, velocidade para botas-`spd` — e ao
  quebrar é **removida do slot** (perde todo o bônus).
- **Material → Devorador:** `metal` entra no set de metal do slot, `organic` no
  orgânico; híbrido nos dois. Registro/limpeza idempotentes no merge.
- **Backward-compat (crítico):** peças base sem N/M usam N=0/M=2 → comportamento
  **byte-idêntico** ao atual (armadura de corpo quebra no 3º nível com −1/−2 CA). O
  plano deve provar isso por teste, como foi feito nas armas.
- **Botas/elmos base NÃO** recebem material automaticamente (mudaria o balanceamento):
  só corroem se forem peças **custom** que declararem material. Nesta fase o editor
  expõe material+N/M para **armadura e escudo**; botas/elmos ficam *engine-ready* (os
  campos entram no editor quando a sub-aba deles for construída).

### 4. Cliente — editor (sub-abas Armaduras/Escudos)
- Generalizar `tools/editor_items_editor.js` para renderizar um formulário **por
  tipo** de item (arma/armadura/escudo), com um esqueleto compartilhado (Identidade,
  Restrição de classe, Disponibilidade, Preço, Imagem, Habilidade concedida, Prévia)
  + seções específicas do tipo.
- **Armadura:** Bônus de CA, categoria (leve/média/pesada), material (checkboxes
  orgânico/metal — pode marcar os dois), corrosão N/M (níveis sem/com penalidade),
  bônus adicionais (lista {efeito PV/velocidade/CA extra, valor}).
- **Escudo:** Bônus de CA, material (orgânico/metal), corrosão N/M, bônus adicionais;
  sem categoria.
- `tools/editor_items_logic.js` ganha `serializeArmor(draft)`, `validateArmorDraft`,
  e um `suggestPriceArmor` (a partir de ac_bonus + bônus adicionais).
- Habilitar as sub-abas `armaduras`/`escudos` (remover o `disabled`); as outras 5
  seguem 🔒.

### 5. Disponibilidade & integração
- **Loja:** peças com `loja=true` entram na lista de armaduras do Ferreiro
  (`SHOP_ARMORS` mesclado), respeitando `allowed_classes` (filtro já existe).
- **Baús/recompensas:** `baus=true` → entram em `_DUNGEON_ITEM_CATALOG` e no seletor
  do editor (`CAT.items` já concatena `EDITOR_CUSTOM_ITEMS`; incluir armaduras/escudos
  além das armas).
- **Loot de monstro:** `loot_monstro=true` → `LOOT_POOL_PROCEDURAL`.
- Compra/equipar preservam os campos (ramo `ferreiro_armor` + whitelists de equipar de
  armadura/escudo, incluindo `bonuses`/`granted_ability`).

### 6. Imagem, preço, validação
Espelham a Fase 1: upload `upload_item_art` (PNG → `assets/itens/<id>.png`), preço
sugerido no `editor_items_logic.js`, validação no servidor com mensagens amigáveis.

## Testes

`tools/test_editor_itens.py` (servidor):
- validação aceita/rejeita armadura e escudo (campos, categoria, material, N/M);
- merge: armadura/escudo entram em `SHOP_ARMORS`, catálogo de baús e loot; material →
  set de corrosão do slot; **cleanup idempotente** remove dos sets e de `SHOP_ARMORS`;
  itens base (ex.: `leather`, `escudo_p`) e sets nativos permanecem intactos;
- **multi-efeito**: equipar uma armadura com `bonuses` (maxhp/spd/def_ extra) aplica os
  três e desequipar reverte exatamente (CA/PV/velocidade voltam ao valor original);
- **corrosão generalizada**: armadura base sem N/M continua byte-idêntica (quebra no 3º,
  −1/−2 CA); um escudo custom com material corrói (penalidade de CA por nível) e quebra
  em N+M+1; botas/elmos base **não** corroem (sem material);
- compra→bolsa→equipar preserva `bonuses`/N/M/campos.

`tools/test_editor_items_logic.js` (node): `serializeArmor`/`validateArmorDraft`/
`suggestPriceArmor` (shape, defaults, escudo sem categoria mas com material/N/M, bônus
adicionais).

## Fora de escopo (Fases seguintes)

- **B** — motor de bônus de **atributo** (For/Des/Con/Int → cascata CA/ataque/PV/saves,
  espelhando o padrão delta de `_reduzir_con_temporario`);
- **C** — **resistências** de dano do herói (novo ramo em `_apply_damage_types` p/
  jogadores);
- **D** — bônus de **iniciativa** (campo lido em `initiative_value`);
- as outras 5 sub-abas (anéis/botas/poções/arremessáveis/venenos) — **a corrosão de
  botas/elmos já fica no motor nesta fase**, mas os campos de material/N/M deles no
  editor só aparecem quando a sub-aba for construída;
- habilidades **ativáveis** concedidas por item;
- balanceador automático.
