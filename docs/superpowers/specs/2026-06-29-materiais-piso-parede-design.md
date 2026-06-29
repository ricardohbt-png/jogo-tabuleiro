# Materiais de chão e parede (cenários temáticos) — Design

**Data:** 2026-06-29
**Branch:** `worktree-feat+materiais-piso-parede`, baseada no HEAD de
`feat/miniatura-png-objetos` (6e1ad50) — onde vive o código real do jogo
(decorações, ambiente etc.). O `master` está 140 commits atrás e não serve de base.
**Status:** aprovado para escrever o plano de implementação

## Objetivo

Diversificar a coloração e decoração de chão e paredes da masmorra para permitir
mais cenários (caverna, floresta, cripta etc.), **pintáveis por casa** no editor, em
2D e 3D, com um modelo de dados já preparado para futuros efeitos de jogo
(ex.: água que reduz movimento) sem reescrever a base.

## Decisões de produto (confirmadas com o usuário)

1. **Escopo:** pintável **por casa** (sem material-base de masmorra). Mitigação:
   o editor terá **balde de preenchimento por área**.
2. **"Pedras desmoronadas":** existem como **estilo visual de parede** (em casas de
   parede) **e** como **entulho colocável** (em casas de chão) que bloqueia.
3. **Entulho bloqueia movimento E visão** (pilha alta), igual a uma parede.
4. **Pisos coloridos são 100% visuais nesta entrega** — não alteram a lógica de
   movimento do servidor. Apenas o `entulho` tem efeito (bloqueio). O catálogo já
   nasce orientado a dados para acomodar efeitos futuros (água etc.).
5. **Vistas:** 2D (canvas top-down) **e** 3D (Three.js).
6. **Catálogo inicial** (nomes confirmados):
   - Pisos (categoria `piso`, casas de chão): `pedra_cinza` (atual/padrão),
     `terra`, `grama`, `pedra_negra`, `entulho` (`solido`+`oclui`).
   - Paredes (categoria `parede`, casas de parede): `pedra_normal` (atual/padrão),
     `enegrecida`, `pedra_caverna`, `desmoronada`.

## Abordagem escolhida

**Uma única camada de "materiais" por casa, orientada a dados.** Em vez de três
sistemas separados (cor de chão / estilo de parede / entulho), um único conceito:
cada casa pode ter um `material` (id de um catálogo autoritativo). Isso casa com o
"pintar por casa" e deixa o gancho de efeitos futuros pronto.

Alternativas descartadas:
- **Reusar decorações para o entulho + enum cosmético só-cliente para pisos/paredes:**
  vira dois sistemas paralelos; o piso cosmético "só-cliente" teria que ser refeito
  quando a água precisar do servidor.
- **Novos tipos estruturais de tile (TILE_ENTULHO):** mexe no enum de tiles usado no
  jogo inteiro; risco alto.

## Modelo de dados

Novo campo **`materiais`** no JSON da masmorra e no `game_state`, **esparso**:

```json
"materiais": { "3,4": "grama", "7,2": "entulho", "10,5": "desmoronada" }
```

- Chave `"x,y"`; valor = id do catálogo.
- Casa ausente = padrão por tipo estrutural: chão (`FLOOR`/`DOOR`) → `pedra_cinza`;
  parede (`WALL`) → `pedra_normal`.
- **Compat retroativa:** masmorra sem o campo `materiais` renderiza idêntica a hoje.

## Catálogo autoritativo (`MATERIAIS` em `server.py`)

Dict de materiais, cada um:

```python
{ "id": "grama", "nome": "Grama", "categoria": "piso",
  "solido": False, "oclui": False, "cor": "#3f6b2f" }
```

- `categoria`: `piso` (válido em chão/porta) ou `parede` (válido em parede).
- `solido`: bloqueia movimento (server + cliente BFS).
- `oclui`: bloqueia visão/névoa (server + cliente LOS).
- `cor`: hex usado como **swatch do editor** (a paleta rica de render vive no cliente).
- Campos de efeito futuros (não usados agora, mas previstos): `custo_mov`,
  `save_ao_entrar`, etc.

Constante mínima espelhada no cliente: `MATERIAIS_SOLIDOS` / `MATERIAIS_OPACOS`
(hoje `{ "entulho" }` em ambos) — para o BFS/LOS do cliente sem precisar do catálogo
inteiro. Deriva do `MATERIAIS` autoritativo no servidor.

## Servidor (`server.py`)

- **`validar_dungeon`:** valida ids ∈ catálogo, coords no grid, e categoria coerente
  com o tile (piso só em chão/porta; parede só em parede). `entulho` é `piso` sólido,
  permitido em chão.
- **`_blocks_tile`:** bloqueia também casas cujo material seja `solido` (entulho) —
  mesmo caminho já usado pelas decorações sólidas (`_decor_block_tiles`).
- **Oclusão de névoa** (`_reveal_around` / `_tall_oclui_caminho`): material `oclui`
  (entulho) passa a ser oclusor, como parede/decoração alta.
- **LOS de ataque/magia** (`_tem_linha_de_visao`): material `oclui` barra a linha.
- **`game_state`:** passa a incluir `materiais`.

## Estado do cliente (`src/gameState.js`)

Sem render (regra de arquitetura). Para o preview de movimento/mira **não divergir**
do servidor:

- Armazena `gameState.materiais`.
- `_walkable`: retorna `false` se o material da casa for sólido.
- `_losBlocks` (e o supercover de LOS): trata material opaco como bloqueio.
- Getter para o render ler o material por casa (ex.: `materialAt(x,y)` / expor
  `materiais`).

## Render (`game.js`) — 2D e 3D

- **2D:** `drawFloor3D` / `drawWallTop3D` / `drawWallSouthFace` passam a receber o id
  do material e escolher uma **paleta** (cor base + detalhes específicos: tufos de
  grama, seixos/terra, pedra escura, escombros). Entulho desenhado como pilha de
  escombros (oclui → tratado visualmente como bloqueio).
- **3D:** **uma textura/cor por material, com cache** (nunca por casa — mantém a
  contagem de luzes/perf estável). Casa de chão escolhe o material de piso; casa de
  parede escolhe o skin de parede. **Entulho** em casa de chão = bloco altura-de-parede
  com textura de escombros (porque oclui visão).
- Paletas ricas de render vivem no cliente (`VC` em `src/visualConfig.js` e/ou tabela
  em `game.js`); o catálogo do servidor só carrega `cor` (swatch do editor).

## Editor (`tools/editor.html`, `editor.js`, `export_catalog.py`)

- Nova ferramenta **Materiais** com paleta (pisos / paredes / entulho).
- **Pincel** pinta `materiais[casa]` respeitando categoria (piso só em chão, parede só
  em parede, entulho em chão).
- **Balde de preenchimento por área** (preenche região contígua de mesma estrutura) —
  mitigação obrigatória da escolha "sem material-base".
- **Borracha** remove a entrada (volta ao padrão).
- Load/save incluem `materiais`.
- Preview no canvas do editor usa o swatch `cor` do catálogo (fill simples + rótulo),
  evitando duplicar a paleta procedural do jogo.
- Catálogo exportado para `editor_catalog.js` via `export_catalog.py` (como decorações).

## Testes

`tools/test_materiais.py`:
- Validação de `materiais` (ids válidos, categoria coerente com o tile, coords).
- Entulho: bloqueio de movimento (`_blocks_tile`), oclusão de névoa e de LOS.
- `game_state` inclui `materiais`.
- **Compat retroativa:** masmorra sem o campo carrega e roda como hoje.

## Faseamento (para o plano de implementação)

1. **Dados + catálogo + validação + payload + compat** (server) + teste.
2. **Gameplay do entulho:** server (`_blocks_tile`, oclusão, LOS) + cliente
   (`gameState.js` BFS/LOS + getter) + teste.
3. **Render 2D** (paletas de piso/parede/entulho).
4. **Render 3D** (texturas/cores por material + bloco de entulho).
5. **Editor** (paleta, pincel, balde, borracha, load/save, swatches, `export_catalog`).

## Riscos / pontos de atenção

- **Divergência cliente↔servidor no entulho:** o bloqueio+oclusão precisa entrar em
  TODOS os caminhos (server `_blocks_tile`/névoa/LOS e cliente `_walkable`/`_losBlocks`),
  senão o cliente oferece movimento/mira que o servidor recusa. É o requisito de
  correção central.
- **Compat retroativa:** ausência de `materiais` deve render idêntico ao atual.
- **Perf 3D:** texturas por material (cache), nunca por casa.
- **Superfície de risco mínima:** pisos coloridos não tocam a lógica de movimento;
  só o entulho tem efeito autoritativo nesta entrega.
