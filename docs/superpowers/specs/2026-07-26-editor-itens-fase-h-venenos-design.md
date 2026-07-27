# Editor de Itens — Fase H: Venenos

**Data:** 2026-07-26
**Branch:** feat/instrumentos-bardo-fase5 (não mergeada)
**Antecessoras:** Fase 1 (armas), 2a (armaduras+escudos), B/C/D (atributos/resistências/iniciativa), E (anéis+botas), F (poções), G (arremessáveis)

## Objetivo

Destravar a sub-aba **Venenos** — a última sub-aba 🔒 do Editor de Itens. Cobre as **5
operações** do subsistema `VENENOS`: `dano`, `reduzir`, `penalidade`, `petrificar` e `cegar`.
Com isso o conjunto de sub-abas do editor fica completo.

## Contexto (o que já funciona)

Um veneno vive em **duas estruturas**:

1. **`VENENOS`** (server.py ~3556): dict module-level com a definição do efeito.
2. **Um item de bolsa** com `item_slot:"bag"`, `effect:"coat_poison"` e `veneno_id` apontando
   para a chave em `VENENOS` (ex.: `SHOP_MERCHANT` tem `veneno_fungo_acre`).

Nos nativos, o **id do item e a chave do veneno são o mesmo string**. Esta fase mantém essa
convenção: um id serve aos dois.

**Fluxo de uso:** `handle_use_item` (efeito `coat_poison`, ação bônus) → `_aplicar_veneno_na_arma`
grava cargas em `poison_slots` da arma equipada → ao acertar, `handle_attack` consome uma carga e
chama `_aplicar_veneno(alvo, veneno_id)`.

**`_aplicar_veneno` (~14902) é totalmente data-driven** nas 5 operações — lê tudo do dict do
veneno. Nenhuma mudança no motor é necessária.

### As 5 operações e seus campos

Comuns a todas: `nome`, `icone`, `save` (`fortitude`|`reflexos`|`vontade`), `dificuldade`,
`anula` (bool — se o sucesso no save cancela), `duracao` (dado `NdX` ou int; `_rolar_dado`
aceita ambos).

| Operação | Campos próprios |
|---|---|
| `dano` | `dano` (int **ou** `NdX`); modelo de save: `save_aplicacao` (testa 1× ao aplicar) **ou** `save_neutraliza_por_rodada` (testa a cada rodada) |
| `reduzir` | `atributo` (`forca`\|`constituicao`\|`destreza`\|`inteligencia` — via `_VENENO_ATTR_MAP`), `valor` (`NdX`). CON recalcula `max_hp`/`fort` automaticamente |
| `penalidade` | `atributos`: lista de pares `[chave, valor]`, chave em `ataque`/`movimento`/`dano`/`ca`/`percepcao` |
| `petrificar` | `duracao` (na falha) + `duracao_falha`/`penalidade_falha` (sucesso parcial) |
| `cegar` | `duracao`, `penalidade_ataque` (default −4), `bloqueia_distancia` (bool) + `duracao_falha`/`penalidade_falha` |

Nota: pares em JSON viram listas; o código faz `for attr, val in ...`, que desempacota listas de
2 elementos igualmente. JSON-safe.

### Cliente: nada a fazer

Diferente da Fase G (arremessáveis), o cliente trata `coat_poison` **genericamente**:

- Loja: agrupa/filtra por `item.effect === 'coat_poison'` (`game.js` ~2087/2093).
- Tooltip (`game.js` ~3807): lê `item.descricao` e `item.efeito = {save, dificuldade, anula}`
  **do próprio item** — não há lookup por id num catálogo estático.
- Uso pela bolsa: caminho genérico de `use_item` (`coat_poison` já está em `BONUS_ACTION_EFFECTS`).

Portanto, incluindo `descricao` e `efeito` no dict de inventário, o veneno custom ganha tooltip
completo sem tocar em `game.js`/`src/gameState.js`.

## Decisões de design (aprovadas)

1. **As 5 operações** (incluindo `petrificar` e `cegar`, apesar dos campos bespoke).
2. **Um id serve item e veneno** (convenção dos nativos).
3. **Retoque da mensagem de `penalidade`**: hoje `_aplicar_veneno` (~15037) imprime literalmente
   "−1 ataque e −1 movimento", hardcoded. Com valores custom isso mentiria, então a mensagem
   passa a ser montada a partir da lista real de `atributos`. É a **única** mudança fora da
   região de itens custom.

## Arquitetura

### 1. Servidor (`server.py`) — *partial staging* obrigatório

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana" + lojas por cidade). **Nunca**
`git add server.py`/`-A`; stage só os hunks desta fase via `git apply --cached`, conferindo com
`git diff --cached -- server.py`. As funções novas ficam na região contígua de itens custom
(~22150–22500); o retoque da mensagem de `penalidade` fica isolado em `_aplicar_veneno` (~15037)
— conferir a vizinhança de hunks do WIP antes de extrair.

- **`_ITEM_POISON_OPS = {"dano", "reduzir", "penalidade", "petrificar", "cegar"}`**,
  **`_ITEM_POISON_ATTRS = {"forca", "constituicao", "destreza", "inteligencia"}`**,
  **`_ITEM_POISON_PENS = {"ataque", "movimento", "dano", "ca", "percepcao"}`**,
  **`_ITEM_POISON_SAVES = {"fortitude", "reflexos", "vontade"}`** (novos sets module-level, junto
  de `_ITEM_THROW_TARGETS`).
- **`_validate_custom_item`**: dispatch `it == "poison"` → `_validate_custom_poison(raw)`.
- **`_validate_custom_poison(raw)`** (novo): espelha `_validate_custom_throwable`.
  - id/nome no padrão; **protege ids nativos** da união
    `SHOP_MERCHANT ∪ SHOP_TEMPLE ∪ SHOP_TAVERN ∪ VENENOS`.
  - `operacao` ∈ `_ITEM_POISON_OPS` (senão rejeita); `save` ∈ `_ITEM_POISON_SAVES` (default
    `fortitude`); `dificuldade` clamp 1–40 (default 10); `anula` (bool); `duracao` = dado válido
    (`_die_ok`) ou int ≥1 (default `1d4`).
  - `dano`: `dano` = int ≥1 **ou** dado válido (default 1); flags de save mutuamente exclusivas —
    se `save_neutraliza_por_rodada` for verdadeiro, grava só ele; senão grava `save_aplicacao`
    (default True, o modelo dos venenos compráveis).
  - `reduzir`: `atributo` ∈ `_ITEM_POISON_ATTRS` (senão rejeita); `valor` = dado válido
    (default `1d4`).
  - `penalidade`: `atributos` = lista de pares `[chave, valor]` filtrados por `_ITEM_POISON_PENS`
    (valor int, normalizado para negativo); rejeita se a lista ficar vazia.
  - `petrificar`/`cegar`: `duracao_falha` (dado/int, default 1) e `penalidade_falha` (lista de
    pares, mesmo filtro; pode ser vazia). `cegar` também: `penalidade_ataque` (int, default −4) e
    `bloqueia_distancia` (bool).
  - `descricao` (texto livre ≤160 chars, opcional — vai no tooltip).
  - `emoji`/`icone` (default ☠️), `allowed_classes`, `price`, `disponibilidade`.
  - Fixos: `item_type:"poison"`, `item_slot:"bag"`, `effect:"coat_poison"`, `custom:True`.
- **`_custom_poison_defn(item)`** (novo): entrada de `VENENOS` no formato nativo
  (`nome`, `icone`, `operacao`, `save`, `dificuldade`, `anula`, `duracao` + os campos da operação),
  marcada `custom:True` para o cleanup.
- **`_custom_poison_inventory_dict(item)`** (novo): item de bolsa/loja — `id`, `name`, `emoji`,
  `item_slot:"bag"`, `effect:"coat_poison"`, `value:0`, `veneno_id: id`, `price`, `custom:True`,
  **+ `descricao`** e **+ `efeito: {save, dificuldade, anula}`** (lidos pelo tooltip do cliente);
  `allowed_classes` se houver.
- **`_apply_custom_items`**: cleanup dos venenos custom (espelha o de `ARREMESSAVEIS` da Fase G:
  `for k in [k for k, v in VENENOS.items() if v.get("custom")]: VENENOS.pop(k, None)`) + ramo
  `if it == "poison"` registrando `VENENOS[id] = _custom_poison_defn(item)` e mesclando o item em
  `SHOP_MERCHANT` (loja) / `_DUNGEON_ITEM_CATALOG` (baús/loot) / `LOOT_POOL_PROCEDURAL` (loot).
- **Retoque da mensagem de `penalidade`** em `_aplicar_veneno` (~15037): trocar o texto fixo por
  um montado a partir de `atribs` (ex.: "−2 ataque, −1 movimento"), preservando o formato geral
  da frase.

### 2. Lógica pura (`tools/editor_items_logic.js`)

- `POISON_OPS = ["dano","reduzir","penalidade","petrificar","cegar"]`,
  `POISON_ATTRS = ["forca","constituicao","destreza","inteligencia"]`,
  `POISON_PENS = ["ataque","movimento","dano","ca","percepcao"]`,
  `POISON_SAVES = ["fortitude","reflexos","vontade"]`.
- `serializePoison(d)`: monta o item com os campos comuns + os da operação escolhida (duração e
  valores como dados via `buildDie`; `dano` fixo quando o autor escolher "valor fixo").
- `validatePoisonDraft(d)`: nome obrigatório; `operacao` válida; para `reduzir`, `atributo`
  válido; para `penalidade`, ao menos um par; faces de dado em `FACES` quando usadas.
- `suggestPricePoison(item)`: heurística por CD e magnitude (`K_POISON` constante no topo).

### 3. UI (`tools/editor_items_editor.js`)

- Destravar `["venenos","Venenos",true]`.
- `novoDraftPoison()` + `renderPoisonForm(f)`: Identidade (nome/ícone/descrição) → **Efeito**
  (select de operação) → **Resistência** (save, CD, "sucesso anula") → **Duração** →
  bloco específico da operação → Restrição de classe → Disponibilidade ("Loja (Mercador)") →
  Preço → Imagem.
- Blocos por operação: `dano` (valor fixo × dado + modelo de save); `reduzir` (atributo + dado);
  `penalidade` (linhas dinâmicas chave+valor, reusando o padrão das linhas de bônus/elemento);
  `petrificar` (duração da falha + penalidades do sucesso parcial); `cegar` (idem + penalidade de
  ataque + bloqueia à distância).
- Trocar a operação re-renderiza o form (padrão do `ie-manejo`/`ie-effect`/`ie-alvo`).

### 4. Testes

- **`tools/test_editor_itens.py`** — seção `[H1]`–`[H5]`:
  - [H1] validação das 5 operações (campos preservados por operação); rejeita operação inválida,
    atributo inválido em `reduzir`, `penalidade` sem pares, e id nativo (`veneno_fungo_acre`).
  - [H2] merge: entra em `VENENOS` + `SHOP_MERCHANT` + `_DUNGEON_ITEM_CATALOG` +
    `LOOT_POOL_PROCEDURAL`; item carrega `veneno_id`/`descricao`/`efeito`; idempotência; lista
    vazia limpa tudo, inclusive `VENENOS`, preservando os nativos.
  - [H3] uso ponta-a-ponta: usar o frasco (`handle_use_item`, `coat_poison`) grava cargas em
    `poison_slots` da arma; o ataque seguinte aplica o veneno no monstro (`efeitos_veneno`
    populado). Reusa `_room_com_alvo`.
  - [H4] efeitos: `reduzir` abaixa o atributo do alvo; `cegar` liga `cego`/`cego_rodadas` e a
    penalidade de ataque (forçando a falha no save com CD alto).
  - [H5] a mensagem de `penalidade` reflete os valores reais (captura o `gm_say`).
- **`tools/test_editor_items_logic.js`**: `serializePoison` por operação, `validatePoisonDraft`,
  `suggestPricePoison`, catálogos exportados.

Rodar da raiz. Verificar o estado **committado** em worktree isolado
(`git worktree add --detach <tmp> HEAD`).

**Estado conhecido do working tree (NÃO é regressão desta fase):** com o WIP do usuário,
`tools/test_editor_itens.py` aborta na seção `[7]` por causa das lojas por cidade
(`_city_shop_items`); no HEAD commitado a suíte roda inteira. Para verificar seções novas no
working tree, importar o módulo de teste e chamar as funções diretamente. Também pré-existentes:
`tools/test_roteamento_itens.py` e 1 teste flaky em `tools/test_devorador.py`.

## Fora de escopo

- Venenos usados por **monstros** (`on_hit` aceita qualquer chave de `VENENOS`, então customs
  passam a funcionar de graça — mas não é testado aqui).
- Interação com as especializações do Ladino (`ladino_veneno_2/3` são **capacidade** de cargas e
  valem automaticamente para qualquer veneno).
- Cura/antídoto de veneno custom (a Purificação do clérigo já reverte via
  `_reverter_efeito_veneno`, genérico).
- O checkbox "Loja" segue afetado pelo WIP de lojas por cidade (ver decisão pendente do seletor
  de cidade) — baús/loot não são afetados.

## Critérios de aceite

- Sub-aba Venenos ativa; formulário com as 5 operações e seus campos condicionais; preview e
  preço sugerido.
- Veneno custom salvo entra em `VENENOS` e nos catálogos; ao ser usado, unta a arma e envenena o
  alvo no acerto, com o efeito correto da operação.
- Tooltip do cliente mostra descrição e resistência (sem mudanças no cliente).
- Testes `[H1]`–`[H5]` (servidor) e node (lógica) verdes no estado committado isolado.
- **Todas as 8 sub-abas do Editor de Itens destravadas.**
