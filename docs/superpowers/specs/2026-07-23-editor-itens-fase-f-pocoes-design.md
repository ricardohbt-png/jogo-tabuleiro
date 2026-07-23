# Editor de Itens — Fase F: Poções

**Data:** 2026-07-23
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessoras:** Fase 1 (armas), 2a (armaduras+escudos), B/C/D (atributos/resistências/iniciativa), E (anéis+botas)

## Objetivo

Destravar a sub-aba **Poções** do Editor de Itens (hoje 🔒), permitindo criar poções
consumíveis personalizadas. Escopo desta fase: os **três efeitos que já funcionam** para o
jogador — `heal` (cura, com multi-dose opcional), `regeneration` (reserva de regeneração) e
`atk_bonus` (buff temporário de ataque, estilo Elixir). Antídoto/cura de status, arremessáveis
e venenos ficam para fases futuras.

## Contexto (o que já funciona)

Poções são **consumíveis de bolsa** (`item_slot:"bag"`) despachados por `effect` em
`handle_use_item` (server.py ~15222). Os três efeitos do escopo já estão implementados para o
jogador:

- **`heal`** (~15289): `p["hp"] = min(max_hp, hp+value)`. Suporta multi-dose via
  `max_uses`/`uses_left` (ex.: Poção de Cura Concentrada nativa): decrementa `uses_left`,
  remove o item só quando zera.
- **`regeneration`** (~15301): soma `value` a `p["potion_regen_pool"]` (+1 HP/rodada, fica no
  herói, não se perde com HP cheio).
- **`atk_bonus`** (~15309): `+value` de ataque **neste turno** (via `self.blessed`) — buff
  temporário, distinto do `atk_bonus` **permanente** de gear (Fase E). Como a poção é um
  consumível de bolsa (dispatch por `effect`), não há conflito com o efeito de gear homônimo.

Todos os três são **ações bônus** (`BONUS_ACTION_EFFECTS = {"heal", "regeneration",
"atk_bonus", ...}`). O `handle_use_item` já cobre a economia de ação bônus, o bloqueio do
Último Esforço para `heal`, e o multi-dose.

Poções nativas vivem no `SHOP_TEMPLE` (health_potion*, regeneration_potion) e no
`SHOP_MERCHANT` (elixir, `atk_bonus`). A compra no **mercador** roteia consumíveis de bolsa
(`slot == "bag"`, ~6966) por `_route_acquired_item` (bolsa-primeiro). O equip não se aplica
(consumível). **Nenhuma mudança no motor de combate é necessária** — o trabalho é só o
pipeline do editor (validar/mesclar/UI), espelhando a Fase E mas mais enxuto (sem equip, sem
corrosão, sem lista `bonuses`).

## Decisões de design (aprovadas)

1. **Escopo = 3 efeitos já implementados** (`heal`/`regeneration`/`atk_bonus`). Sem tocar em
   `handle_use_item` (que fica numa região com WIP ativo do usuário).
2. **Custom vão só para o mercador** (`SHOP_MERCHANT`) na loja, como a Fase E — não para o
   Templo. Mais baús/loot via `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL`.
3. **Multi-dose** (`max_uses`) exposto só para `heal` (o único efeito nativo que o usa).

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana"). Ao commitar, **nunca**
`git add server.py`/`-A`; stage só os hunks desta fase via `git apply --cached` de um patch
dos hunks isolados (as funções desta fase ficam na região contígua de itens custom, ~linhas
21200–21480, longe do WIP). Confirme com `git diff --cached -- server.py`.

Mudanças:

- **`_validate_custom_item`**: no dispatch, `it == "potion"` → `_validate_custom_potion(raw)`.
- **`_validate_custom_potion(raw)`** (novo): espelha `_validate_custom_accessory`.
  - id/nome com o padrão de validação; **protege ids nativos** da união
    `SHOP_MERCHANT ∪ SHOP_TEMPLE ∪ SHOP_TAVERN` (`{i["id"] for shop in (...) for i in shop
    if not i.get("custom")}`).
  - `effect` deve estar em `_ITEM_POTION_EFFECTS = {"heal", "regeneration", "atk_bonus"}`
    (novo set module-level); senão rejeita.
  - `value = max(0, int(...))`.
  - **Só `heal`**: `max_uses = max(1, int(raw.get("max_uses", 1)))`; se `max_uses > 1`,
    grava também `uses_left = max_uses`. Outros efeitos ignoram doses.
  - `emoji` (default 🧪), `allowed_classes`, `price`, `disponibilidade`.
  - Fixos: `item_slot:"bag"`, `item_type:"potion"`, `custom:True`.
  - Retorna dict normalizado.
- **`_custom_potion_inventory_dict(item)`** (novo): dict plano único p/ loja **e** bolsa/baú
  (`id`, `name`, `emoji`, `item_slot:"bag"`, `effect`, `value`, `custom:True`, `price`;
  `max_uses`/`uses_left` se `heal` multi-dose; `allowed_classes` se houver).
- **`_apply_custom_items`**: ramo `if it == "potion"` no laço `for raw in records:` →
  `disp["loja"]`→`SHOP_MERCHANT.append(dict)`;
  `disp["baus"] or disp["loot_monstro"]`→`_DUNGEON_ITEM_CATALOG[id]=dict`;
  `disp["loot_monstro"]`→`LOOT_POOL_PROCEDURAL.append(id)`; `continue`.
  - **Cleanup já existe** (Fase E): a linha `SHOP_MERCHANT[:] = [i for i in SHOP_MERCHANT if
    not i.get("custom")]` + o bloco genérico `prev_custom_ids` (limpa `_DUNGEON_ITEM_CATALOG`
    e `LOOT_POOL_PROCEDURAL`) cobrem poções sem código de limpeza novo.

### 2. Lógica pura (`tools/editor_items_logic.js`) — arquivo de cliente, testável por node

- `POTION_EFFECTS = ["heal", "regeneration", "atk_bonus"]` (novo).
- `serializePotion(d)` (novo): `item_type:"potion"`, `item_slot:"bag"`, `effect` (validado
  contra `POTION_EFFECTS`, default `heal`), `value = max(0, +d.value||0)`, emoji default 🧪,
  `allowed_classes`, `price`, `disponibilidade`. Se `effect === "heal"` e `d.max_uses > 1`:
  grava `max_uses` e `uses_left = max_uses`.
- `validatePotionDraft(d)` (novo): nome obrigatório; `POTION_EFFECTS.indexOf(d.effect) >= 0`.
- `suggestPricePotion(item)` (novo): `Math.max(1, Math.round(K_POTION * (value) *
  (max_uses||1)))` — `K_POTION` constante no topo (≈1), transparente/recalibrável.
- Exportar os quatro no `api`.

### 3. UI (`tools/editor_items_editor.js`) — arquivo de cliente, `git add` direto

- Na tabela `TYPES`, `["pocoes","Poções",false]`→`true`.
- `novoDraftPotion()` (novo): `{ name, emoji:"🧪", item_type:"potion", effect:"heal", value:10,
  max_uses:1, allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false},
  price:0, id:"" }`.
- `novoDraftFor(type)`: rotear `pocoes`→`novoDraftPotion()`.
- `renderForm`: despachar `pocoes` para `renderPotionForm`.
- `renderPotionForm(f)` (novo): Identidade → **Efeito** (`selectOpts` com os 3 efeitos, rótulos
  amigáveis via um pequeno mapa) → **Valor** (`numInput`) → **Doses (`max_uses`)** — só visível
  quando `effect === "heal"` (troca o form no `onchange` do seletor de efeito, como o `ie-manejo`
  das armas) → Restrição de classe → Disponibilidade (rótulo "Loja (Mercador)") → Preço → Imagem.
- `currentPotionDraftFromForm`, `renderPotionPreview`, `bindPotionForm`, `onSavePotion` —
  espelham os de acessório (sem corrosão/bônus). Usam `previewFn = renderPotionPreview`.

### 4. Testes

- **`tools/test_editor_itens.py`** — nova seção `[F1]`–`[F…]`:
  - [F1] validação: aceita os 3 efeitos; `heal` grava `uses_left` quando `max_uses>1`;
    rejeita `effect` inválido; rejeita id nativo (`health_potion`); `item_slot=="bag"`.
  - [F2] merge: `disp.loja`→`SHOP_MERCHANT`; `disp.baus/loot`→`_DUNGEON_ITEM_CATALOG`;
    `loot`→`LOOT_POOL_PROCEDURAL`; idempotência (`_apply_custom_items` 2×); nativo do
    `SHOP_MERCHANT`/`SHOP_TEMPLE` intacto após clear.
  - [F3] uso ponta-a-ponta via `handle_use_item`: poção custom de `heal` na bolsa cura o HP e
    é consumida; `regeneration` enche `potion_regen_pool`; `atk_bonus` aplica o buff temporário.
    Reusa o setup de sala/turno existente (ver os testes que já exercitam turno; garantir
    `_is_turn` verdadeiro para o pid — inicializar iniciativa/turno como os testes de combate
    fazem, ou setar o estado mínimo que `_is_turn`/`_executar_acao_bonus` exigem).
  - [F4] multi-dose: `heal` com `max_uses=2` decrementa `uses_left` e só remove ao zerar.
- **`tools/test_editor_items_logic.js`**: `serializePotion` (heal com doses / regen / atk_bonus),
  `validatePotionDraft` (rejeita sem nome e efeito inválido), `suggestPricePotion` (cresce com
  value e doses), `POTION_EFFECTS`.

Rodar da raiz. Verificar o estado **committado** num worktree isolado
(`git worktree add --detach <tmp> HEAD`), pois o working tree roda com o WIP do usuário.

**Falhas pré-existentes (NÃO são regressão):** `tools/test_roteamento_itens.py` (por
`health_potion`, WIP do usuário conserta); `tools/test_devorador.py` (1 teste flaky).

## Fora de escopo

- Antídoto/cura de status (veneno/doença) — exige ramo `antidote` novo no `handle_use_item`
  (fase futura; primitivos `_reverter_efeito_veneno`/`_curar_doenca` já existem).
- Venda no Templo (só mercador, como a Fase E).
- `full_heal`/`bless`/`cleanse` (serviços de templo, não itens de bolsa).
- Novos efeitos de poção (CA/velocidade temporários) — exigiriam handlers novos no motor.
- Arremessáveis e venenos (sub-abas próprias, fases futuras).

## Critérios de aceite

- Sub-aba Poções ativa; formulário com seletor de efeito, valor, doses (só heal), preview e
  preço sugerido.
- Poção custom salva aparece na loja do mercador e/ou baús/loot conforme a disponibilidade, vai
  para a bolsa na compra/loot, e ao ser usada aplica o efeito correto (cura/regeneração/buff).
- Multi-dose (`heal` com `max_uses>1`) funciona (doses decrementam; item some ao zerar).
- Testes `[F*]` (servidor) e node (lógica) verdes no estado committado isolado.
