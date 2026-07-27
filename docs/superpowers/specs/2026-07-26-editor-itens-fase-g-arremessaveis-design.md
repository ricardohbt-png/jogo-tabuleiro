# Editor de Itens — Fase G: Arremessáveis

**Data:** 2026-07-26
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessoras:** Fase 1 (armas), 2a (armaduras+escudos), B/C/D (atributos/resistências/iniciativa), E (anéis+botas), F (poções)

## Objetivo

Destravar a sub-aba **Arremessáveis** do Editor de Itens (hoje 🔒), permitindo criar frascos/
bombas personalizados. Escopo: os dois modos de mira do subsistema (`ataque_alvo` — mirado num
monstro, e `area` — raio com save de Reflexos), com dano elemental e o status "em chamas".
Efeitos bespoke do catálogo nativo (ácido residual/corrosão, controle, zonas, água benta) ficam
fora desta fase.

## Contexto (o que já funciona)

Arremessáveis são consumíveis de bolsa (`item_slot:"bag"`, `effect:"throwable"`) com o
comportamento definido no dict `ARREMESSAVEIS` (server.py ~3477) e resolvido por
`handle_throw_item` (~9734), que despacha por `defn["alvo"]`:

- **`_throw_item_alvo`** (~9761): teste de ataque por DES vs CA do alvo (nat1 falha, 20 crítico),
  consome o item em acerto E erro, marca `action_done` + custo de sobrevivência, aplica
  `dano`/`elemento` via `_aplicar_dano_alvo`, e opcionalmente `em_chamas`
  (`_aplicar_em_chamas` com `chamas_dur`/`chamas_agua_apaga`), `residual`, `corrosao_ac`,
  `controle`.
- **`_throw_item_area`** (~9845): sem jogada de ataque; atinge todos no raio (fogo amigo) com
  save de Reflexos (metade no sucesso) via `_save_mostrado`, respeitando sombra de parede
  (`_tem_linha_de_visao` do centro), com `em_chamas` opcional e `zona` (fumaça).

**Nenhuma mudança nesses handlers é necessária** — eles leem tudo do `defn`. O trabalho do
servidor é validar/normalizar o item custom, registrá-lo em `ARREMESSAVEIS` e mesclá-lo nos
catálogos de loja/baús/loot.

### O problema do cliente (por que esta fase toca no cliente)

A **mira** é decidida no cliente por `CATALOGO_ITENS[item.id]` — um catálogo **estático** em
`src/gameState.js` (~514), que não conhece itens custom. Dois consumidores:

- `game.js:10763-10766` (`_iniciarMiraArremesso`): lê `catDef.alcance`, `catDef.alvo === 'area'`,
  `catDef.areaRaio` para montar o realce e a legenda.
- `src/gameState.js:2023` (`resolveTileClick`, ramo `pendingThrow`): lê
  `(CATALOGO_ITENS[th.id] || {}).alvo || 'ataque_alvo'` para decidir entre `throw` (monstro) e
  `throw_area` (casa).

Com os defaults atuais, um arremessável custom **single-target de alcance 4** já funcionaria sem
tocar no cliente. Mas **área** (e alcance ≠ 4) exige que o cliente conheça os metadados — daí as
duas edições cirúrgicas abaixo.

## Decisões de design (aprovadas)

1. **Escopo = single-target + área** (os dois modos de mira do subsistema).
2. **Metadados de mira viajam no próprio item de bolsa** (`alvo`/`alcance`/`area_raio`), e os dois
   consumidores do cliente caem para os campos do item quando o id não está no `CATALOGO_ITENS`.
   Descartado: enviar o `ARREMESSAVEIS` inteiro no `game_start` (mais dados + novo ponto de
   sincronia) e espelhar um catálogo custom no cliente (duplicação que desatualiza).
3. **Efeitos bespoke fora de escopo** (ácido residual/corrosão, controle cola/rede, zonas de
   fumaça, água benta): são campos de comportamento específico do catálogo nativo.

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana"). **Nunca** `git add server.py`/
`-A`; stage só os hunks desta fase via `git apply --cached` (as funções ficam na região contígua
de itens custom, ~21200–21500, longe do WIP). Confirme com `git diff --cached -- server.py`.

- **`_ITEM_THROW_TARGETS = {"ataque_alvo", "area"}`** e
  **`_ITEM_THROW_ELEMENTS = {"fogo", "frio", "eletrico", "acido", "sagrado", "explosao"}`**
  (novos sets module-level, junto de `_ITEM_POTION_EFFECTS`).
- **`_validate_custom_item`**: dispatch `it == "throwable"` → `_validate_custom_throwable(raw)`.
- **`_validate_custom_throwable(raw)`** (novo): espelha `_validate_custom_potion`.
  - id/nome no padrão; **protege ids nativos** da união
    `SHOP_MERCHANT ∪ SHOP_TEMPLE ∪ SHOP_TAVERN ∪ ARREMESSAVEIS`.
  - `alvo` ∈ `_ITEM_THROW_TARGETS` (senão rejeita); `alcance` clamp 1–12 (default 4).
  - `dano`: opcional; se presente deve passar em `_die_ok` (senão rejeita). `elemento` ∈
    `_ITEM_THROW_ELEMENTS` (default `fogo`); só gravado quando há dano.
  - **Só `alvo=="area"`**: `area_raio` clamp 1–3 (default 1); `save` = `{"tipo":"reflexos",
    "cd": clamp 5–25}` quando `save_cd` informado (sem CD → sem save, dano cheio).
  - `em_chamas` (bool); quando true grava `chamas_dur` (`NdX` válido, default `1d4`) e
    `chamas_agua_apaga` (bool, default True).
  - `emoji` (default 💥), `allowed_classes`, `price`, `disponibilidade`.
  - Fixos: `item_type:"throwable"`, `item_slot:"bag"`, `effect:"throwable"`, `custom:True`.
- **`_custom_throwable_defn(item)`** (novo): entrada no formato nativo de `ARREMESSAVEIS`
  (`id`, `name`, `emoji`, `alcance`, `alvo`, + `dano`/`elemento`, + `area_raio`/`save`,
  + `em_chamas`/`chamas_dur`/`chamas_agua_apaga`).
- **`_custom_throwable_inventory_dict(item)`** (novo): dict de bolsa/loja —
  `id`, `name`, `emoji`, `item_slot:"bag"`, `effect:"throwable"`, `price`, `custom:True`,
  **+ metadados de mira** `alvo`, `alcance`, `area_raio` (só área) para o cliente;
  `allowed_classes` se houver.
- **`_apply_custom_items`**: ramo `if it == "throwable"` → registra
  `ARREMESSAVEIS[id] = _custom_throwable_defn(item)`; loja→`SHOP_MERCHANT`;
  baús/loot→`_DUNGEON_ITEM_CATALOG`; loot→`LOOT_POOL_PROCEDURAL`.
  **Cleanup novo**: no bloco de limpeza, remover os ids custom anteriores de `ARREMESSAVEIS`
  (espelhando o `prev_weapon_ids` de `WEAPONS`):
  `prev_throw_ids = {k for k, v in ARREMESSAVEIS.items() if v.get("custom")}` → `.pop(k)`.
  Para isso o `defn` carrega `"custom": True`. A limpeza de loja/baús/loot é **herdada**
  (linha do `SHOP_MERCHANT` da Fase E + bloco genérico `prev_custom_ids`).

### 2. Cliente — duas edições cirúrgicas (*partial staging*)

Ambos os arquivos têm WIP do usuário, mas **nenhum hunk do WIP fica próximo** dos pontos de
edição (game.js: nenhum entre 10400–11100; gameState.js: os mais próximos em 2173+, ~150 linhas
depois do alvo 2023). Hunks separáveis.

- **`src/gameState.js`** (~2023, ramo `pendingThrow` de `resolveTileClick`):
  `const alvo = (CATALOGO_ITENS[th.id] || {}).alvo || th.alvo || 'ataque_alvo';`
  (cai para o `alvo` carregado no `pendingThrow`).
- **`game.js`** (~10763, `_iniciarMiraArremesso`):
  - `catDef` ganha fallback do próprio item:
    `const alcance = catDef.alcance || item.alcance || 4;`
    `const isArea = (catDef.alvo || item.alvo) === 'area';`
    `const areaRaio = isArea ? (catDef.areaRaio || item.area_raio || 1) : 0;`
  - `GS.pendingThrow` passa a incluir o alvo:
    `GS.pendingThrow = { id: item.id, alcance, alvo: (catDef.alvo || item.alvo || 'ataque_alvo') };`
  - A legenda usa `catDef.emoji || item.emoji` e `catDef.nome || item.name`.

Itens **nativos** continuam resolvendo pelo `CATALOGO_ITENS` (precedência inalterada) → sem
mudança de comportamento para eles.

### 3. Lógica pura (`tools/editor_items_logic.js`)

- `THROW_TARGETS = ["ataque_alvo", "area"]`, `THROW_ELEMENTS = ["fogo","frio","eletrico","acido","sagrado","explosao"]`.
- `serializeThrowable(d)`: `item_type:"throwable"`, `item_slot:"bag"`, `effect:"throwable"`,
  `alvo` (validado, default `ataque_alvo`), `alcance` clamp 1–12, dano (`buildDie` a partir de
  `die_qtd`/`die_faces`) + `elemento` quando `tem_dano`, `area_raio`/`save_cd` só para área,
  `em_chamas`+`chamas_dur`+`chamas_agua_apaga`, emoji default 💥, `allowed_classes`, `price`,
  `disponibilidade`.
- `validateThrowableDraft(d)`: nome obrigatório; `alvo` válido; se `tem_dano`, faces ∈ `FACES`.
- `suggestPriceThrowable(item)`: `K_THROW × dieAvg(dano)` + acréscimo por área (`×area_raio`) e
  por `em_chamas` — `K_THROW` constante no topo, transparente.

### 4. UI (`tools/editor_items_editor.js`)

- Destravar `["arremessaveis","Arremessáveis",true]`.
- `novoDraftThrowable()` + `renderThrowableForm(f)`: Identidade → **Alvo** (`Mirado (DES vs CA)` /
  `Área (save de Reflexos)`) → Alcance → [só área] Raio + CD do save → **Dano** (checkbox
  "tem dano" + quantidade/faces + elemento) → **Em chamas** (checkbox + duração + "apaga com
  água") → Restrição de classe → Disponibilidade ("Loja (Mercador)") → Preço → Imagem.
- Campos condicionais (área, dano, chamas) re-renderizam o form no `onchange` do respectivo
  seletor/checkbox — mesmo padrão do `ie-manejo` (armas) e do `ie-effect` (poções).
- `currentThrowableDraftFromForm`/`renderThrowablePreview`/`bindThrowableForm`/`onSaveThrowable`
  espelham os de poção; `previewFn = renderThrowablePreview`.

### 5. Testes

- **`tools/test_editor_itens.py`** — seção `[G1]`–`[G4]`:
  - [G1] validação: aceita single-target e área; grava `save` só na área; `em_chamas` com
    `chamas_dur`/`chamas_agua_apaga`; rejeita `alvo` inválido, dano malformado e id nativo
    (`frasco_oleo`).
  - [G2] merge: entra em `ARREMESSAVEIS` + `SHOP_MERCHANT` + `_DUNGEON_ITEM_CATALOG` +
    `LOOT_POOL_PROCEDURAL`; idempotência (2× `_apply_custom_items`); lista vazia limpa todos,
    inclusive `ARREMESSAVEIS`, preservando os nativos (`frasco_oleo`).
  - [G3] uso single-target via `handle_throw_item`: monstro adjacente sofre dano (forçando o
    acerto com `random.seed` ou monkeypatch de `random.randint`), item sai da bolsa, `action_done`
    marcado. Reusa o helper de turno `_turn_room` (Fase F) + um monstro injetado em `r.monsters`.
  - [G4] uso de área via `handle_throw_item` (`tx`/`ty`): todos os alvos no raio sofrem dano;
    com save de Reflexos bem-sucedido o dano é metade.
- **`tools/test_editor_items_logic.js`**: `serializeThrowable` (single/área/chamas),
  `validateThrowableDraft`, `suggestPriceThrowable`, `THROW_TARGETS`/`THROW_ELEMENTS`.

Rodar da raiz. Verificar o estado **committado** em worktree isolado
(`git worktree add --detach <tmp> HEAD`), pois o working tree roda com o WIP do usuário.

**Falhas pré-existentes (NÃO são regressão):** `tools/test_roteamento_itens.py` (por
`health_potion`, WIP do usuário); `tools/test_devorador.py` (1 teste flaky).

## Fora de escopo

- Efeitos bespoke do catálogo nativo: ácido residual (`residual`/`corrosao_ac`), controle
  (`controle` — cola/rede), zonas (`zona` — fumaça/escuridão), água benta (`holy_water`/
  `zona_sagrada`).
- Arremessáveis usáveis por monstros pelo mestre (o `_monster_throw_item` já filtra por
  `id in ARREMESSAVEIS`, então customs passam a funcionar lá **de graça** — mas não é testado
  nesta fase).
- Sub-aba Venenos (fase seguinte) e `granted_ability` ativável.

## Critérios de aceite

- Sub-aba Arremessáveis ativa; formulário com alvo, alcance, área/save, dano/elemento e chamas;
  preview e preço sugerido.
- Arremessável custom salvo aparece na loja do mercador e/ou baús/loot, vai para a bolsa, e ao ser
  arremessado aplica o comportamento correto (mirado com teste de ataque; área com save).
- A mira do cliente funciona para os dois modos (monstro vs casa), com alcance e raio corretos;
  itens nativos inalterados.
- Testes `[G1]`–`[G4]` (servidor) e node (lógica) verdes no estado committado isolado.
