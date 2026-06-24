# Decorações de Masmorra — Design

**Data:** 2026-06-23
**Branch sugerida:** `feat/decoracoes-masmorra`

## Visão geral

Nova categoria de entidade — **decorações** — colocável no editor de masmorras.
Cada decoração ocupa 1, 2 ou 4 casas do grid, **bloqueia passagem** (e, nos objetos
"altos", também a **linha de visão / névoa**), pode ser **girada em 90°** durante o
posicionamento, e opcionalmente pode **conter loot** (abre como um baú). Dois objetos
têm comportamento especial:

- **Fonte:** ao ser clicada por um herói adjacente, entrega uma **garrafa de água**
  (item que repõe sede, já existente nas lojas). Limitada por **cargas** configuráveis.
- **Fogueira:** é **pisável**; qualquer criatura (herói **ou** monstro) que **entra**
  na casa sofre **1d4 de dano de fogo** (automático, sem teste de save).

O design reaproveita sistemas já existentes no projeto:
- footprint multi-tile + facing dos monstros (`_monster_tiles_at`, `size`, `oriented`/`facing`);
- bloqueio de tile (`_blocks_tile`) e de visão/névoa;
- baús (`_spawn_chest`, `handle_take_from_chest`, `hidratar_itens_bau`) e o painel de baú no cliente;
- sistema de sobrevivência (garrafa de água repõe sede);
- catálogo do editor exportado (`tools/export_catalog.py` → `editor_catalog.js`).

Seguindo o `CLAUDE.md` ("**estado primeiro, visual depois**"), a implementação é
dividida em 3 fases: **A) servidor/estado → B) editor → C) renderização/cliente**.

## Catálogo dos 22 objetos

`size` = `[w,h]` (footprint com facing canônico). `gira` = pode ser rotacionado 90°.
`alto` = bloqueia LOS/névoa. `pisável` = não bloqueia movimento (só a fogueira).
Todos exceto a fogueira aceitam o **toggle de loot** no editor.

| # | id | Nome | size | gira | alto | pisável | especial |
|---|---|---|---|---|---|---|---|
| 1 | `cama` | Cama | [1,2] | ✔ | — | — | — |
| 2 | `lareira` | Lareira | [1,2] | ✔ | — | — | — |
| 3 | `fonte` | Fonte | [2,2] | — | — | — | `fountain` (cargas) |
| 4 | `fogueira` | Fogueira | [1,1] | — | — | ✔ | `campfire` (1d4 fogo ao entrar) |
| 5 | `tumba` | Tumba | [1,2] | ✔ | — | — | — |
| 6 | `mesa_cadeiras` | Mesa com cadeiras | [1,2] | ✔ | — | — | — |
| 7 | `estante` | Estante | [1,2] | ✔ | ✔ | — | — |
| 8 | `carroca` | Carroça | [2,2] | ✔ | — | — | — |
| 10 | `coluna` | Coluna de pedra | [1,1] | — | ✔ | — | — |
| 11 | `barril` | Barril | [1,1] | — | — | — | — |
| 12 | `arca_tesouros` | Arca de tesouros | [1,1] | — | — | — | loot ligado por padrão |
| 13 | `cama_casal` | Cama de casal | [2,2] | ✔ | — | — | — |
| 14 | `estante_livros` | Estante de livros | [1,2] | ✔ | ✔ | — | — |
| 15 | `altar` | Altar ritualístico | [2,2] | ✔ | — | — | — |
| 16 | `trono` | Trono de rei | [1,1] | ✔ | — | — | — |
| 17 | `gaiola` | Gaiola com esqueleto | [1,1] | — | — | — | — |
| 18 | `grades_prisao` | Grades de prisão | [1,1] | ✔ | — | — | — |
| 19 | `estante_armas` | Estante de armas | [1,2] | ✔ | ✔ | — | — |
| 20 | `mesa_tortura` | Mesa de tortura | [1,2] | ✔ | — | — | — |
| 21 | `mesa_quimica` | Mesa de equipamentos de química | [1,2] | ✔ | — | — | — |
| 23 | `arvore` | Árvore | [1,1] | — | ✔ | — | — |
| 24 | `arvore_grande` | Árvore grande | [2,2] | — | ✔ | — | — |

> Os números 9 e 22 não existem (saltos de numeração na descrição original). São 22 objetos.

### Regras de footprint e rotação
- **[1,2]** (2 casas): facing canônico ocupa 1×2; girar 90° → 2×1.
- **[2,2]** (4 casas): footprint é o mesmo em qualquer facing; girar só rotaciona a arte.
- **[1,1]** (1 casa): girar só muda a direção/arte (ex.: trono, grades).
- Rotação em 4 facings (0/90/180/270). Itens com `gira: false` não rotacionam.
- A âncora (`pos`) é o canto/frente; as demais casas derivam do facing (espelha
  `_monster_tiles_at`).

## Modelo de dados (JSON da masmorra)

Novo array de topo `decorations`:

```json
"decorations": [
  {
    "type": "cama",
    "pos": [4, 3],
    "facing": [0, 1],
    "loot": { "gold": 0, "items": [{ "id": "health_potion" }] },
    "charges": 3
  }
]
```

- `type` — id do `DECOR_TYPES`.
- `pos` — âncora `[x,y]`.
- `facing` — `[dx,dy]` cardinal (default conforme o tipo; ignorado se `gira: false`).
- `loot` — `null` se a decoração não contém nada; senão `{ gold, items:[{id}] }`
  (mesma forma do baú). Ausente/`null` ⇒ não-container.
- `charges` — só para `fonte`; nº de garrafas restantes.

`arca_tesouros` nasce com `loot` ligado por padrão no editor (mas editável).

## Fase A — Servidor (`server.py`) + estado

1. **`DECOR_TYPES`** (dict autoritativo): por tipo →
   `{ nome, emoji, size:[w,h], gira, alto, pisavel, loot_capaz, special }`.
   `special ∈ {None, "fountain", "campfire"}`.
2. **Carregamento/reset:** ao montar a dungeon (junto de `chests`), instanciar
   `self.decorations` a partir de `defn.get("decorations", [])`, hidratando itens de
   loot via `hidratar_itens_bau`. Persistência igual à dos baús: recarrega do defn a
   cada entrada de dungeon; estado de "loot retirado"/"cargas" vive durante a sessão
   da dungeon.
3. **Footprint:** `_decor_tiles(d)` / `_decor_tiles_at(d, ax, ay, facing)` espelhando
   `_monster_tiles_at` (1×2 gira com facing; 2×2 fixo; 1×1 só facing visual).
4. **Bloqueio de movimento:** casas de decoração **não-pisável** passam a bloquear em
   `_blocks_tile` (ou helper equivalente consultado pelos mesmos pontos). Isso cobre
   automaticamente: movimento de heróis (`handle_move`), pathfinding e ocupação de
   monstros (`_monster_can_occupy`, `_entity_blocks`), animados, prisioneiro.
   - A fogueira (`pisavel: true`) **não** bloqueia.
5. **Bloqueio de visão/névoa (oclusão por raio nos altos):** a névoa atual revela por
   **raio** (`_reveal_around`), sem linha de visão — paredes não ocluem. Para os objetos
   **`alto`**, adicionar **oclusão por raycast**: ao revelar o raio em torno do herói,
   traçar uma linha (Bresenham/DDA) do herói até cada casa do raio; se a linha cruzar a
   casa de uma decoração **`alto`** antes de chegar ao destino, o destino **não** é
   revelado (fica oculto atrás do objeto). Vale **só** para decorações altas — paredes
   continuam com o comportamento atual (não ocluem), para não alterar masmorras
   existentes. A própria casa do objeto alto é revelada.
6. **Fogueira (`campfire`):** ao uma criatura **entrar** numa casa de fogueira (heróis
   em `handle_move`; monstros/animados no respectivo movimento), aplicar **1d4** de
   dano de fogo, com broadcast de dado (`dice_roll`) e narração. Sem teste de save.
7. **Fonte (`fountain`):** mensagem de interação de um herói **adjacente** (Chebyshev
   ≤ footprint) entrega uma `garrafa de água` ao inventário e decrementa `charges`;
   recusa se `charges <= 0`. Ação **livre** (não gasta turno) — o equilíbrio vem das
   cargas.
8. **Containers (loot):** interação espelha `handle_take_from_chest`
   (distância ≤ adjacente ao footprint, **sem** restrição de turno). Reusa o **painel
   de baú** do cliente: pegar ouro / pegar item por índice. Quando vazio, fica inerte.
9. **`game_state`** passa a incluir `decorations`: por decoração, `type`, `pos`,
   `facing`, `tiles` (footprint resolvido), `tem_loot` (bool), `charges` (se fonte),
   `alto`/`pisavel` (para render). Loot detalhado vai no payload do painel ao interagir
   (ou já embutido, como os baús — seguir o padrão dos baús).
10. **Mensagens de protocolo (Client→Server):**
    - `interagir_decor` — `decor_id` (fonte: bebe; container: abre painel).
    - `take_from_decor` — `decor_id`, `kind` (`gold`/`item`), `index` — espelha
      `take_from_chest` (ou, se mais simples, reutilizar o fluxo de baú apontando para
      a decoração).
11. **Validação** (`validar_masmorra`, ~linha 1700): array `decorations` é lista; cada
    `type` ∈ `DECOR_TYPES`; footprint inteiro dentro do mapa e **todo sobre FLOOR**;
    sem sobrepor parede/porta/entrada/saída/outra decoração/baú/monstro/prisioneiro;
    itens de `loot` ∈ catálogo; `charges >= 0` só faz sentido em `fonte`.

## Fase B — Editor (`tools/editor.js`, `tools/export_catalog.py`)

1. **Export:** `export_catalog.py` emite nova chave `decorations` em `editor_catalog.js`
   (campos que o editor precisa: `type`, `nome`, `emoji`, `size`, `gira`, `alto`,
   `pisavel`, `loot_capaz`, `special`). Atualizar `test_export_catalog.py`.
2. **Ferramenta "decoração":** novo grupo na toolbar. Como há 22 tipos, usar **um
   `<select>` de tipo** (estado `S.decorType`) — clicar coloca o tipo escolhido com o
   facing atual.
3. **Rotação:** botão **"girar 90°"** e atalho de teclado **R** que ciclam o facing
   da peça pendente e da decoração selecionada (só se `gira`).
4. **Colocação/preview:** mostrar as casas do footprint; recusar se não couber em chão
   ou sobrepor entidade existente.
5. **Painel da decoração selecionada:** tipo (read-only), botão girar, **toggle
   "contém loot"** + editor de ouro/itens (UI análoga à de recompensa de objetivo),
   e campo **cargas** (só `fonte`). `arca_tesouros` já vem com loot ligado.
6. **`buildJSON`/`loadJSON`:** incluir/normalizar `decorations`.
7. **`validarEditor`:** footprint em chão, sem sobreposição, itens de loot válidos.
8. **Render no canvas do editor:** emoji no centro do footprint + contorno das casas
   ocupadas; indicação do facing.
9. **Apagar/selecionar:** `eraseAt`/`entityAt` reconhecem decorações por footprint.

## Fase C — Renderização e cliente (`game.js`, `src/gameState.js`)

1. **`gameState.js` (lógica pura):** getter `decorations`, helper `decorTiles(d)`
   (espelha o servidor), e senders `interagirDecor(id)` / `takeFromDecor(...)`.
   Zero DOM/THREE.
2. **`game.js` 2D:** desenhar emoji da decoração no centro do footprint.
3. **`game.js` 3D:** **geometria procedural** por tipo (caixas/cilindros coloridos
   dimensionados ao footprint, posicionados/rotacionados pelo facing). Estrutura
   preparada para trocar por **GLB** depois (carregamento de `assets/models3d/decor/`).
4. **Interação:** clicar numa decoração com herói adjacente → `interagirDecor`
   (fonte: bebe; container: abre o painel de baú existente). Decorações puras não
   reagem ao clique.
5. **Névoa/visão:** o cliente apenas renderiza a névoa a partir do que o servidor
   revela; o bloqueio de visão por objetos `alto` é resolvido no servidor.

## Decisões assumidas (confirmadas)

1. Beber da fonte e abrir container são **ação livre** (não gastam turno), como o baú
   hoje; a fonte é limitada por **cargas**.
2. **Grades de prisão** e **gaiola** bloqueiam **movimento** mas **não** a visão
   (são vazadas) — `alto: false`. Objetos `alto` (coluna, árvores, estantes) **ocluem**
   a revelação de névoa via raycast (ver Fase A, item 5).
3. **Fogueira** sem teste de save — dano **automático** de 1d4 ao entrar, para todos.
4. Decorações só podem ser colocadas sobre **chão** (FLOOR), nunca em parede, porta,
   entrada ou saída, e o footprint não pode sobrepor outra entidade.
5. Visual inicial em **3D procedural**; GLB é uma evolução posterior. 2D e editor usam
   **emoji**.

## Fora de escopo (YAGNI)

- Modelos GLB reais (fase futura; a estrutura 3D fica preparada).
- Upload de modelos/imagens por decoração.
- Efeitos especiais além de fonte/fogueira (ex.: altar com ritual, trono com buff).
- Decorações que se movem ou são destrutíveis em combate.
