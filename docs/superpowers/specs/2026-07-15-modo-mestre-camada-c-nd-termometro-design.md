# Modo Mestre Jogador — Camada C: ND unificado + Termômetro (design)

**Data:** 2026-07-15
**Escopo:** primeiro subprojeto da Camada C do Modo Mestre Jogador — dar a todo
monstro um Nível de Desafio (`cr`) unificado e um **termômetro de dificuldade** no
editor de masmorras, que mede a soma de ND contra um grupo esperado definido pelo
autor.

## Contexto

A Camada A (controle), a fase de combate e a Camada B (reforços) já estão
implementadas em `feat/instrumentos-bardo-fase5`. A Camada C são **auxílios de
autoria em tempo de design** (no editor), não mecânicas de jogo. Este subprojeto é o
par acoplado **ND unificado + Termômetro** — a base numérica sobre a qual as demais
sub-features da Camada C (ND/XP de armadilha, salas obrigatórias, validador) vão
assentar em specs futuras.

Diferença fundamental em relação às camadas A/B: **nada aqui roda em partida.** É
puramente uma ferramenta de editor. O campo `expected_party` é gravado na masmorra
apenas como referência de design; o servidor não o usa em runtime.

### Decisões do brainstorm (confirmadas pelo usuário)

1. **1º subprojeto:** ND unificado + Termômetro (par acoplado).
2. **Referência de dificuldade:** grupo definido pelo autor (nº de heróis + nível).
3. **Agregação:** mostra **total** (soma de todos os monstros) **e pior sala**
   (maior soma de `cr` num único cômodo).
4. **Fórmula/faixas (ponto de partida ajustável):** `poder_grupo = heróis × nível`;
   razão `ND / poder_grupo` → **Fácil** < 0,4 · **Equilibrada** 0,4–0,8 ·
   **Difícil** 0,8–1,2 · **Mortal** > 1,2.
5. **`expected_party`:** só referência de design; sem efeito em runtime (escala de
   loot/spawn fica para depois).

## Estado atual relevante do código (verificado)

- **`cr` já existe na maioria dos monstros:** as fichas novas de `MONSTER_DEFS`
  (server.py) têm `cr`; faltam os **6 legados** (`goblin`/`skeleton`/`orc`/
  `dark_mage`/`troll`/`dragon`, linhas ~1436-1441), que só têm `tier`.
- **O catálogo do editor já exporta `cr`:** `tools/export_catalog.py` já inclui
  `"cr"` na lista de campos copiados por monstro (~linha 16). Portanto, ao dar `cr`
  aos 6 legados, o `editor_catalog.js` regenerado passa a ter `cr` para todos —
  nenhuma mudança no exportador é necessária além de regenerá-lo.
- **`cr` fracionário já é usado em jogo:** `corpse["nd"]` (Reviver os Mortos) já lê
  `cr` real e cai para `tier` quando ausente — o mesmo padrão de fallback que o
  helper `monster_cr` vai centralizar.
- **Editor sem nada de dificuldade:** `tools/editor.js`/`.html` não têm ND,
  termômetro ou grupo esperado hoje. O painel de nível de masmorra é o ramo `!S.sel`
  de `renderPanel()` (onde já vivem objetivos e os Reforços do Mestre da Camada B).
- **Monstros colocados no editor** guardam `type`, `pos`, `room_id` em `S.monsters`
  (o `room_id` permite agrupar por sala para o "pior sala").
- **`validar_dungeon`** (server.py) valida campos autorados e retorna `(ok, msg)`.

## Componentes

### 1. ND unificado (servidor — dado)

- **Preencher `cr` nos 6 legados** em `MONSTER_DEFS`: `goblin` 0.25, `skeleton` 0.5,
  `orc` 0.75, `dark_mage` 0.5, `troll` 1.5, `dragon` 5.0 (valores da análise já
  registrada em memória).
- **Helper `monster_cr(mdef)`** (função module-level, fonte única da verdade):
  retorna `float(mdef["cr"])` se presente, senão um fallback por `tier`
  (`{1:0.5, 2:1, 3:2, 4:5}.get(tier, 1)`). Usado por qualquer código que precise do
  ND de um monstro (e reusável pela linha do `corpse["nd"]`, sem alterá-la nesta
  spec).
- **Catálogo do editor:** regenerar `tools/editor_catalog.js` (via
  `python tools/export_catalog.py`) para que `cr` apareça em `CAT.monsters`. O editor
  usa `cr` direto do catálogo, com o mesmo fallback por `tier` no cliente para
  robustez (monstro custom sem `cr`).

### 2. Grupo esperado (campo da masmorra + editor)

- **Formato:** novo campo opcional `expected_party: { "heroes": N, "level": L }`
  (default `{heroes: 4, level: 1}` quando ausente). `heroes` 1–6; `level` ≥ 1.
- **Editor:** dois inputs numéricos (heróis, nível) no painel de nível de masmorra
  (ramo `!S.sel` de `renderPanel`), gravados/lidos no `save()`/load como os demais
  campos.
- **Validação** (`validar_dungeon`): se presente, `expected_party` é objeto com
  `heroes` inteiro 1–6 e `level` inteiro ≥ 1; caso contrário, erro claro.

### 3. Termômetro (editor — 100% client-side)

- **Cálculo** (JS puro em `editor.js`), rodando a cada `renderPanel`:
  - `crDe(type)` = `cr` do tipo no `CAT.monsters` (ou fallback por `tier`).
  - `total_ND` = Σ `crDe(m.type)` sobre `S.monsters`.
  - `pior_sala_ND` = máximo, sobre os grupos de `S.monsters` agrupados por
    `room_id` (monstros com `room_id` nulo formam um grupo "sem sala"), da soma de
    `cr` do grupo.
  - `poder = max(1, heroes × level)`.
  - `faixa(nd)` a partir de `nd / poder`: <0,4 Fácil · <0,8 Equilibrada ·
    <1,2 Difícil · senão Mortal. Constantes nomeadas no topo do módulo (fáceis de
    calibrar).
- **UI:** no painel de nível de masmorra, duas linhas de termômetro — "Total" e
  "Pior sala" — cada uma com o valor de ND, o rótulo da faixa e uma barra colorida
  (verde→amarelo→laranja→vermelho conforme a faixa). Atualiza ao vivo conforme
  monstros são colocados/removidos (o `renderPanel` já re-renderiza nessas ações).
- **Sem servidor:** o termômetro nunca chama o servidor; lê tudo do estado do editor
  + catálogo.

## Fronteiras de módulo

- **`server.py`**: só os dados (`cr` nos legados) + o helper `monster_cr` + a
  validação de `expected_party`. Nenhuma lógica de termômetro no servidor.
- **`tools/export_catalog.py` / `editor_catalog.js`**: apenas regeneração (o campo
  `cr` já está na lista de export).
- **`tools/editor.js`**: estado (`expectedParty`), serialização, o cálculo de ND e a
  UI do termômetro. É o grosso do trabalho e vive todo aqui.
- **`tools/editor.css`**: estilos das barras (se necessário; pode-se usar estilo
  inline como a Camada B fez).

## Testes

- **Servidor** (`tools/test_modo_mestre.py` ou um teste dedicado pequeno):
  - `monster_cr` retorna o `cr` quando presente e o fallback por `tier` quando
    ausente.
  - todo `MONSTER_DEFS` resolve para um `cr` > 0 via `monster_cr` (garante que os
    legados foram preenchidos).
  - `validar_dungeon` aceita `expected_party` válido e rejeita `heroes`/`level` fora
    de faixa ou tipo errado.
- **Editor:** `node --check tools/editor.js`. O cálculo de dificuldade é JS de
  cliente sem harness automatizado — verificação manual: colocar monstros e conferir
  que Total/Pior-sala e as faixas atualizam corretamente ao mudar heróis/nível.
- **Regenerar o catálogo:** rodar `python tools/export_catalog.py` e confirmar que
  `editor_catalog.js` passou a ter `cr` nos 6 legados (commitar o catálogo
  regenerado — exceção consciente à regra de "não commitar o catálogo": aqui a
  regeneração É a mudança pretendida).

## Fora de escopo

- ND/XP de armadilha, salas obrigatórias, validador de 6 regras — specs futuras da
  Camada C.
- Qualquer efeito de `expected_party` em runtime (escala de loot/inimigos/recompensa).
- Termômetro no cliente de jogo (é ferramenta de editor).
- Rebalancear os `cr` das fichas novas (só preenche os legados que faltam).
- Calibração fina das faixas/fórmula (os valores são um ponto de partida ajustável).
