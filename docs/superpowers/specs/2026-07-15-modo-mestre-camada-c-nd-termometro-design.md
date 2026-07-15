# Modo Mestre Jogador — Camada C: ND unificado, Termômetro (editor) e Minimapa de CR (mestre) — design

**Data:** 2026-07-15
**Escopo:** primeiro subprojeto da Camada C — dar a todo monstro um Nível de Desafio
(`cr`) unificado, um **termômetro de dificuldade no editor**, e um **minimapa de CR
em jogo, exclusivo do mestre**, ambos medindo o CR contra um grupo esperado, com
preview de 2/4/6 jogadores.

## Contexto

Camadas A (controle), combate e B (reforços) já implementadas em
`feat/instrumentos-bardo-fase5`. A Camada C são auxílios de autoria e de leitura de
dificuldade. Este subprojeto entrega três coisas acopladas por uma mesma base
numérica (o `cr`):

1. **ND unificado** — todo monstro com `cr` real + helper único `monster_cr`.
2. **Termômetro no editor** — mede a dificuldade da masmorra em tempo de design.
3. **Minimapa de CR em jogo (só mestre)** — o mestre abre um mapa esquemático das
   salas com o CR e a faixa de dificuldade de cada uma, o CR médio no topo, e um
   seletor de 2/4/6 jogadores. **Nunca visível para os jogadores.**

### Restrição (só-mestre em runtime)

O minimapa e qualquer número de dificuldade em jogo aparecem **exclusivamente para o
mestre** (`GS.isMaster()`). Os jogadores nunca veem o termômetro/minimapa nem o CR. O
editor é ferramenta de design (sem jogadores). Nenhuma mecânica de jogo muda: é tudo
leitura/visualização. `expected_party` é gravada como referência; o servidor não a usa
para alterar a partida.

### Decisões do brainstorm (confirmadas pelo usuário)

1. 1º subprojeto: ND unificado + Termômetro (editor) + Minimapa (mestre).
2. Referência de dificuldade: grupo definido pelo autor (heróis + nível).
3. Agregação no editor: **total** (soma de todos) **e pior sala** (maior soma por sala).
4. Fórmula/faixas (ponto de partida ajustável): `poder = heróis × nível`; razão
   `CR/poder` → **Fácil** <0,4 · **Equilibrada** 0,4–0,8 · **Difícil** 0,8–1,2 ·
   **Mortal** >1,2.
5. `expected_party`: só referência (sem efeito em runtime).
6. **Minimapa do mestre:** repurposar o ícone de inventário (o mestre não equipa
   itens) para abrir o minimapa; CR + faixa colorida por sala; **CR médio = média das
   salas** (Σ CR das salas ÷ nº de salas) no topo; seletor **2/4/6** jogadores.
7. Preview 2/4/6: **nos dois** (editor e minimapa).
8. Minimapa mostra **CR + faixa colorida** por sala (não só números).

## Estado atual relevante do código (verificado)

- `cr` já existe na maioria dos `MONSTER_DEFS`; faltam os **6 legados**
  (`goblin`/`skeleton`/`orc`/`dark_mage`/`troll`/`dragon`, ~linhas 1436-1441 de
  server.py), que só têm `tier`.
- `tools/export_catalog.py` já inclui `"cr"` na lista de campos exportados por
  monstro (~linha 16) — dar `cr` aos legados + regenerar `editor_catalog.js` basta.
- **Não existe minimapa hoje** (nada de `minimap` em game.js/index.html).
- O **ícone de inventário em jogo** é `#ficha-fab` (game.js ~linha 189):
  `<button id="ficha-fab" onclick="InventoryModal.toggle(GS.myPid)" title="Inventário
  (tecla I)">🎒</button>`. É esse ícone que vira "Mapa de CR" para o mestre.
- O mestre já tem **visão total** (sem névoa) e já há vários ramos
  `if(GS.isMaster())` em game.js para UI só-do-mestre.
- **`game_state.monsters`** é serializado com `dict(m, …)` (push_state) — inclui todos
  os campos do monstro (`cr` após preencher os legados, `room_id`, `type`). O cliente
  do mestre recebe **todos** os monstros (a névoa é aplicada só no cliente). Logo, o
  minimapa calcula CR por sala 100% no cliente, a partir de `game_state`.
- **`game_state.rooms`** já vai no payload (usado no desenho do tabuleiro) — o
  minimapa reusa a geometria das salas dali.
- `index.html` carrega, em ordem: `src/gameState.js`, `src/main.js`,
  `src/miniatura3d.js`, `game.js`, `src/ui/inventoryModal.js`. `editor.html` carrega
  `editor.js` + módulos. Um módulo compartilhado precisa ser incluído nos **dois**.

## Componentes

### 1. ND unificado (servidor — dado)

- Preencher `cr` nos 6 legados em `MONSTER_DEFS`: `goblin` 0.25, `skeleton` 0.5,
  `orc` 0.75, `dark_mage` 0.5, `troll` 1.5, `dragon` 5.0.
- Helper module-level `monster_cr(mdef)` = `float(mdef["cr"])` se presente, senão
  fallback por `tier` (`{1:0.5, 2:1, 3:2, 4:5}.get(tier, 1)`). Fonte única da verdade
  no servidor.
- Regenerar `tools/editor_catalog.js` (via `python tools/export_catalog.py`) para
  levar `cr` a `CAT.monsters` (commitar o catálogo regenerado — exceção consciente à
  regra de não commitá-lo: aqui a regeneração É a mudança).

### 2. Grupo esperado (campo da masmorra + servidor)

- Campo opcional `expected_party: { "heroes": N, "level": L }` (default
  `{heroes:4, level:1}` quando ausente). `heroes` 1–6; `level` ≥ 1.
- Carga: `self.expected_party = defn.get("expected_party") or {"heroes":4,"level":1}`
  no bloco de carga da dungeon. Vai no `game_state` (para o minimapa do mestre usar
  como baseline do seletor).
- Validação (`validar_dungeon`): se presente, objeto com `heroes` inteiro 1–6 e
  `level` inteiro ≥ 1; senão erro claro.

### 3. Módulo de dificuldade compartilhado (`src/difficulty.js`)

Funções puras, sem DOM, reusadas pelo editor E pelo cliente de jogo (DRY entre os dois
contextos). Incluído em `index.html` e em `editor.html`.

- `window.Difficulty = { ... }` com:
  - `crFromEntry(entry)` — `cr` do dict do monstro (ou fallback por `tier`), usado
    tanto para `CAT.monsters` (editor) quanto para `game_state.monsters` (jogo).
  - `poder(heroes, level)` = `max(1, heroes * level)`.
  - `faixa(nd, poder)` — retorna `{key, label, color}` a partir de `nd/poder`,
    usando os limiares/cores nomeados no topo do módulo (Fácil/Equilibrada/Difícil/
    Mortal; verde/amarelo/laranja/vermelho). Ponto único de calibração.

### 4. Termômetro no editor (`tools/editor.js`)

- **Grupo esperado:** dois inputs (heróis, nível) no painel de nível de masmorra
  (ramo `!S.sel` de `renderPanel`), gravados/lidos como `S.expectedParty`.
- **Cálculo:** `total = Σ Difficulty.crFromEntry(catMonstro(m.type))` sobre
  `S.monsters`; `pior_sala = max` por grupo de `S.monsters` agrupado por `room_id`.
- **Preview 2/4/6:** três botões que recalculam usando aquele nº de heróis (o
  `level` vem de `S.expectedParty`), sem alterar o valor salvo. Default = heróis
  salvos.
- **UI:** duas linhas de termômetro (Total, Pior sala) com valor + faixa
  (`Difficulty.faixa`) + barra colorida; atualiza ao vivo no `renderPanel`.

### 5. Minimapa de CR do mestre (em jogo, `game.js`)

- **Repurpose do ícone:** quando `GS.isMaster()`, o `#ficha-fab` vira o botão do
  minimapa — emoji 🗺️, título "Mapa de CR", `onclick` abre o minimapa em vez de
  `InventoryModal.toggle`. Para não-mestres, permanece o inventário 🎒 intacto. (O
  mestre não equipa itens.)
- **Overlay do minimapa** (só-mestre): um painel/modal com um **mapa esquemático das
  salas** (desenhadas a partir de `game_state.rooms`), cada sala rotulada com seu
  **CR** (Σ `Difficulty.crFromEntry` dos monstros vivos com aquele `room_id`) e
  colorida pela **faixa** (`Difficulty.faixa` vs o poder do grupo selecionado). No
  **topo:** "CR médio: X" = **média das salas** (Σ CR das salas ÷ nº de salas). Um
  **seletor 2/4/6** recomputa as faixas (nível vindo de `game_state.expected_party`;
  default = `expected_party.heroes`). Fecha por botão/Esc/clique fora.
- **Interação:** clicar numa sala do minimapa a destaca (e pode centralizar/realçar
  no tabuleiro — opcional; o núcleo é a leitura de CR por sala).
- **Só-mestre e sem vazamento:** o botão-minimapa e o overlay só existem sob
  `GS.isMaster()`; jogadores nunca os veem. (Os dados de `cr` já trafegam em
  `game_state` para todos, como todo o resto do estado — a restrição é de UI.)

## Fronteiras de módulo

- `server.py`: dados (`cr` legados) + `monster_cr` + carga/serialização de
  `expected_party` + validação. Nenhuma lógica de termômetro/minimapa.
- `src/difficulty.js`: matemática pura de dificuldade (faixas/limiares/cores),
  compartilhada. Ponto único de calibração.
- `tools/editor.js`: estado + serialização de `expected_party` + termômetro + preview
  2/4/6 (usa `Difficulty`).
- `game.js`: repurpose do `#ficha-fab` + overlay do minimapa (usa `Difficulty`).
- `index.html` / `editor.html`: incluir `src/difficulty.js`.

## Testes

- **Servidor** (`tools/test_modo_mestre.py` ou dedicado):
  - `monster_cr` devolve o `cr` presente e o fallback por `tier` quando ausente;
    todo `MONSTER_DEFS` resolve para `cr > 0`.
  - carga de `expected_party` (default quando ausente) e presença no `game_state`.
  - `validar_dungeon` aceita `expected_party` válido; rejeita fora de faixa/tipo.
- **Módulo** `src/difficulty.js`: `node --check`; um teste JS mínimo (se houver
  harness) ou verificação por asserts inline de `faixa()` nos 4 limiares.
- **Editor / jogo:** `node --check editor.js game.js`. Cálculo de dificuldade e
  minimapa são JS de cliente — verificação manual: no editor, colocar monstros e
  conferir Total/Pior-sala/faixas e o preview 2/4/6; em jogo como mestre, abrir o
  minimapa e conferir CR por sala, CR médio, cores e o seletor 2/4/6; confirmar que um
  cliente-jogador **não** vê botão nem overlay.
- Regenerar e commitar `editor_catalog.js` com `cr` nos legados.

## Fora de escopo

- ND/XP de armadilha, salas obrigatórias, validador de 6 regras — specs futuras.
- Qualquer efeito de `expected_party`/CR em runtime (loot/spawn/recompensa).
- Rebalancear os `cr` das fichas novas (só preenche os legados).
- Calibração fina das faixas/fórmula (valores iniciais ajustáveis).
- Minimapa navegável/roteável ou com informação além de CR/faixa por sala.
