# Validador de Masmorra — grafo + 5 regras (design)

**Data:** 2026-07-16
**Escopo:** sub-feature da Camada C — um validador de design no editor que avisa
(não bloqueia) sobre violações de boas-práticas, usando um grafo de salas e o ND.
1ª spec: infra (grafo) + regras **2, 3, 4, 5, 6**. A regra **1** (≥2 caminhos
disjuntos até o boss) fica para uma 2ª spec (algoritmo mais complexo).

## Contexto

O design original ("Modo Mestre — Design Revisado", item 9) lista 6 regras
obrigatórias. Hoje o editor tem uma validação de save (`const e = []` em
`tools/editor.js` ~1355) que verifica campos básicos (entrada, salas, tipos). Não há
grafo de salas nem BFS. Roles `boss`/`entrance` existem; salas têm `doors`; o grid é
`S.tiles` (FLOOR/WALL). Já temos `src/difficulty.js` (faixas de ND), `expected_party`
(grupo esperado) e `required`/`required_mode` (salas obrigatórias = rota crítica).

### Decisões do brainstorm (confirmadas pelo usuário)

1. **Escopo:** infra + regras 2/3/4/5/6 agora; regra 1 depois.
2. **Só avisa** — mostra os problemas mas nunca bloqueia o save.
3. **Rota crítica = salas obrigatórias** (`required`). Sem salas marcadas, R3/R6 são
   puladas com um aviso ("marque a rota crítica").
4. **R6 usa a média** do ND da rota crítica (vs um teto por-sala).

## Estado atual relevante (verificado)

- Validação de save: `tools/editor.js` monta `const e = []` e empurra erros; esses
  bloqueiam/avisam no save. O validador de design é uma lista SEPARADA de **avisos**
  (nunca bloqueia).
- `S.tiles` (grid FLOOR/WALL), `S.rooms` (`{id,x,y,w,h,role,locked,doors,required?,
  required_mode?}`), `S.grid.{w,h}`. `role` inclui `"entrance"` e `"boss"`.
- ND por sala: a lógica de `_ndPorSala` (soma de `cr` de monstros via `CAT.monsters` +
  `cr` de armadilhas via `CAT.traps`, agrupados por sala) já existe — será extraída em
  um mapa `{room_id: nd}` reusável pelo validador. (Nota: sem multiplicador de
  quantidade — divergência registrada; o validador usa o ND como está.)
- `src/difficulty.js`: `Difficulty.poder(heroes, level)` para os tetos relativos ao
  grupo. `expected_party` no estado do editor (`S.expectedParty`).

## Componentes (100% editor — `tools/editor.js`, sem servidor)

### 1. Grafo de salas (infra)

- `_tileRoom(x, y)` → a sala cujo retângulo contém (x,y), ou `null` (corredor/parede).
- **Conectividade (BFS de tiles):** flood-fill 4-dir sobre tiles de chão a partir da
  entrada; um tile é da entrada se está na sala `role="entrance"` (ou na casa
  `S.entrance`). Uma sala está **alcançável** se ao menos um de seus tiles foi
  atingido.
- **Grafo de adjacência de salas:** para cada sala, BFS sobre chão a partir dos seus
  tiles, atravessando corredores mas **parando** ao entrar no retângulo de outra sala
  (marca essa sala como vizinha, sem atravessá-la). Resultado: `adj[roomId] = Set(roomIds)`.
- **Distância entrada→boss:** BFS no grafo de adjacência (nº de salas no menor
  caminho). Boss = sala `role="boss"`.
- `_ndSalaMap()` → `{roomId: nd}` (ND por sala, da lógica de `_ndPorSala`).

### 2. Regras (cada uma vira 0+ avisos)

- **R4 Conectividade total:** para cada sala não alcançável da entrada →
  `"sala #N isolada do mapa principal"`.
- **R2 Distância spawn–boss:** se há sala boss e `dist(entrada, boss) < MIN_SALAS`
  (default 3) → `"boss muito perto do spawn (N salas; mín M)"`. Sem boss → aviso
  informativo `"sem sala com role 'boss' — R2/R5 puladas"`.
- **R5 Descanso antes do boss:** entre as salas vizinhas do boss no grafo, se nenhuma
  tem ND baixo (`nd ≤ REST_ND_MAX`, default `Difficulty.poder(...) × 0.3`) nem
  `role="empty"` → `"sem sala de descanso logo antes do boss"`. Sem boss → pulada.
- **R6 Teto de ND na rota crítica:** `req = salas com required`; se `req` vazio →
  aviso `"objetivo/rota crítica: nenhuma sala marcada como obrigatória"`. Senão, se
  `média(nd das req) > TETO` (default `Difficulty.poder(heroes, level) × FATOR_R6`,
  ex.: 0.9) → `"rota crítica pesada (ND médio X > teto Y)"`.
- **R3 Sem picos consecutivos:** `req` ordenadas por distância da entrada; para cada
  par consecutivo, se `|nd_a − nd_b| > MAX_PICO` (default 1.0) → `"pico de ND entre
  salas #A e #B (Δ=Z)"`. `<2` req → pulada.

Constantes (`MIN_SALAS`, `REST_ND_MAX` fator, `FATOR_R6`, `MAX_PICO`) nomeadas no topo
do módulo — ponto único de calibração, tunáveis.

### 3. UI

- Uma seção **"⚠️ Avisos de design (N)"** no painel de nível de masmorra (`!S.sel` de
  `renderPanel`, perto do termômetro) + um botão **"Validar"** que recomputa e lista os
  avisos. Cada aviso é uma linha de texto.
- No **save**, os avisos são anexados à mensagem de save (informativo, não bloqueia) —
  o autor vê que há N avisos de design, mas salva normalmente.
- Zero avisos → "✅ Sem avisos de design".

## Fronteiras de módulo

- Tudo em `tools/editor.js` (grafo, regras, UI). Reusa `window.Difficulty` e a lógica
  de ND por sala. Nenhuma mudança em `server.py`/`game.js`.
- As constantes de limiar ficam no topo do módulo do validador.

## Testes

- Sem harness JS para o editor → verificação por `node --check tools/editor.js` +
  teste manual: montar masmorras que violem cada regra e conferir os avisos
  (sala isolada, boss colado no spawn, sem descanso, rota crítica pesada, pico entre
  obrigatórias) e uma masmorra "boa" sem avisos.
- (Opcional) extrair as funções puras do grafo/regras de forma que possam ser testadas
  via `node -e` com um `S` sintético, se viável sem DOM.

## Regra 1 (adicionada 2026-07-16)

- **R1 Rota alternativa** (≥2 caminhos distintos até o boss): implementada como
  **detecção de gargalo (cut vertex)** — para cada sala intermediária alcançável
  (≠ entrada, ≠ boss), remove-a do grafo (`_alcancaSemSala`) e testa se o boss ainda
  é alcançável da entrada; se alguma remoção desconecta o boss, ela é gargalo e R1
  avisa listando as salas-gargalo. Por Menger, "sem cut vertex" ⇔ ≥2 caminhos
  vértice-disjuntos. O caso boss-colado-no-spawn (1 rota curta) é coberto por R2.

## Fora de escopo
- Bloquear o save; thresholds editáveis pelo autor na UI (usa defaults no código).
- Multiplicador de quantidade no ND (divergência registrada; o validador usa o ND atual).
- Distância em tiles (usa distância em nº de salas no grafo).
