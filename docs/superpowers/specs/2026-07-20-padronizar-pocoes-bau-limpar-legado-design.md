# Padronizar poções de baú + limpar itens legados de `CHEST_ITEMS`

**Data:** 2026-07-20
**Status:** Aprovado (brainstorming)

## Problema

`CHEST_ITEMS` (server.py) é uma lista legada usada em duas frentes:

1. **Baús procedurais** (`_spawn_chest_from_room`) sorteiam via `random.choice(CHEST_ITEMS)`. Como a lista é antiga, esses baús só largam os itens legados — inclusive uma `health_potion` "Poção de Vida" que **duplica** a poção de loja `health_potion` "Poção de Cura" (mesmo efeito/valor), com nome divergente. As poções realmente vendidas (Cura Pequena/Aprimorada/Concentrada, Regeneração) **nunca** aparecem em baús procedurais.

2. **Baús autorados** e o **editor** resolvem itens pelo catálogo mesclado `_DUNGEON_ITEM_CATALOG` (`_criar_catalogo_loot_masmorra` = `CHEST_ITEMS` + as 6 lojas, com a loja vencendo em conflito de id). Esse catálogo (139 itens) já cobre quase todo o repertório do jogo; a única lacuna é pergaminho (gerado dinamicamente — **fora do escopo**).

Objetivo: baús passam a usar as **mesmas poções das lojas**, e os itens de equipamento legados exclusivos de `CHEST_ITEMS` são removidos do jogo (serão substituídos por itens mágicos próprios no futuro).

## Decisões (do brainstorming)

- Baús procedurais sorteiam **poções de cura + suporte + comida**: `health_potion`, `health_potion_small`, `health_potion_improved`, `health_potion_concentrated`, `regeneration_potion`, `antidote`, `elixir`, `racao_viagem`, `garrafa_vinho` — todos resolvidos pelas **definições de loja** (fonte única).
- `CHEST_ITEMS` fica com **apenas** a Espada Curta de Ferro Serrilhado (`sword`), agora com `price = 32` (Espada Curta 12 + 20). Ela permanece como loot **autorado** referenciável no editor; **não** entra no pool procedural (que passa a ser só consumível).
- Equipamento legado removido de `CHEST_ITEMS`: `magic_sword`, `bow`, `staff`, `shield`, `chainmail`, `leather`, `amulet`, `boots`, `ring`, `cloak`, e os consumíveis duplicados `health_potion`(Poção de Vida), `elixir`, `antidote`, `garrafa_vinho`, `racao`. Os que também existem em loja continuam no catálogo (autorados intactos); só somem do catálogo os exclusivos de `CHEST_ITEMS`: `magic_sword`, `bow`, `shield`, `ring`, `racao`.
- Pergaminhos no editor: **fora do escopo** (projeto próprio).

## Mudanças

### 1. Pool de loot procedural (server.py)

Novo, próximo de `CHEST_ITEMS`:

```python
# IDs sorteados em baús procedurais. Fonte única: definições de loja
# (resolvidas por _DUNGEON_ITEM_CATALOG). Extensível quando itens mágicos
# ganharem regras de colocação.
LOOT_POOL_PROCEDURAL = [
    "health_potion", "health_potion_small", "health_potion_improved",
    "health_potion_concentrated", "regeneration_potion", "antidote", "elixir",
    "racao_viagem", "garrafa_vinho",
]
```

`_spawn_chest_from_room` passa a sortear ids desse pool e hidratar pelo catálogo
(via `hidratar_itens_bau([{"id": x}])` ou `deepcopy(_DUNGEON_ITEM_CATALOG[x])`),
mantendo a lógica de "1 item + 45% de um 2º distinto". Como o pool é definido
**depois** de `_DUNGEON_ITEM_CATALOG` na ordem do módulo, a resolução usa o
catálogo já pronto.

### 2. Podar `CHEST_ITEMS` (server.py)

```python
CHEST_ITEMS = [
    {"id": "sword", "name": "Espada Curta de Ferro Serrilhado", "emoji": "⚔️",
     "item_slot": "weapon", "die": "1d6", "stat": "str_", "categoria": "cortante",
     "dmg_bonus": 2, "corrosao_resistente": 1, "price": 32},
]
```

`_criar_catalogo_loot_masmorra` continua igual; o catálogo passa a ser
`{sword}` ∪ lojas. Os ids exclusivos removidos (`magic_sword`, `bow`, `shield`,
`ring`, `racao`) somem do catálogo e, por consequência, do editor — correto, pois
saem do repertório.

### 3. Repontar `_necromante_loot` (server.py, ~17375)

Trocar as buscas em `CHEST_ITEMS` por resolução via catálogo/loja:
- `garrafa_vinho` → `_DUNGEON_ITEM_CATALOG.get("garrafa_vinho")` (def da taverna).
- `racao` → `_DUNGEON_ITEM_CATALOG.get("racao_viagem")` (equivalente de viagem da taverna).

### 4. Migrar referências aos ids que somem

- `tools/test_objetivos.py` (linhas ~332/343/363/376): item de recompensa de
  exemplo `magic_sword` → `shortsword` (item de loja válido). Ajustar as
  asserções que casam `id == "magic_sword"`.
- `dungeons/test_fase1.json`: baú com `magic_sword` → `shortsword`.
- `dungeons/teste_basico.json`: baú com `shield` → `escudo_p`. (`leather` fica —
  existe em loja.)

### 5. Regenerar catálogo do editor

`python tools/export_catalog.py` → regenera `tools/editor_catalog.js` a partir do
`_DUNGEON_ITEM_CATALOG` novo (remove os ids apagados da lista do editor, mantém
todos os itens atuais).

## Fora do escopo

- Pergaminhos no editor (geração dinâmica — projeto próprio).
- Criar os itens mágicos que substituirão o equipamento legado (o usuário fará
  depois, com regras de colocação em baús / equipar monstros).
- Editar quais itens cada loja/cidade vende (mencionado pelo usuário como futuro).

## Impacto de gameplay

- Baús procedurais deixam de largar armas/armaduras (só consumíveis: poções +
  comida) até os itens mágicos existirem. Baús autorados seguem colocando
  qualquer item do catálogo (incluindo a serrilhada, com preço).
- A "Poção de Vida" some do jogo; loot de poção passa a ser as poções de loja.

## Testes / verificação

- `test_objetivos.py` volta a 59/0 com a recompensa migrada.
- `test_dungeon_loader.py` segue 59/0 (não assere conteúdo de baú de fase1).
- `test_devorador.py` / `test_prata.py`: `sword` (serrilhada) permanece; o dict
  literal `{"id": "magic_sword"}` de test_prata não depende do catálogo.
- Novo teste sugerido: os ids de `LOOT_POOL_PROCEDURAL` resolvem no catálogo, e um
  baú procedural (`_spawn_chest_from_room`) só contém itens desse pool.
- `python tools/export_catalog.py` roda sem erro e `editor_catalog.js` não
  contém mais `magic_sword`/`bow`/`shield`/`ring`/`racao`.
- Regressão: `validar_dungeon` aceita todas as masmorras autoradas após a
  migração (nenhuma referencia id apagado).
