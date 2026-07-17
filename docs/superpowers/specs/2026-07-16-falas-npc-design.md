# Falas de NPC (design)

**Data:** 2026-07-16
**Escopo:** última sub-feature da Camada B do Modo Mestre — marcadores de fala
colocados no editor que exibem um popup leve em jogo, com 3 gatilhos (proximidade,
entrada de sala, manual do mestre).

## Contexto

O design original (item 8) pede um sistema de fala **leve** (popup tipo balão),
distinto do log de narração (`gm_say`→`gm_narration`, no chat) e da **story/slides**
da campanha (tela cheia). Sem custo de recurso. Três gatilhos, todos pré-escritos no
editor. Sem mestre humano (CPU no papel), as falas automáticas (proximidade/sala)
disparam normalmente; a manual só com mestre humano (é uma ação deliberada).

Não há nada de fala hoje: `gm_say` é chat; `renderStory` é tela cheia; monstros/
decorações não têm campo de texto.

### Decisões do brainstorm (confirmadas pelo usuário)

1. **Portador:** um **marcador de fala** próprio (entidade nova), colocado numa casa.
2. **Gatilhos (os 3):** `proximidade` (raio), `sala` (entrar na sala do marcador),
   `manual` (botão do mestre no HUD).
3. **Conteúdo:** falante (nome + emoji) + texto.
4. **Gatilho de evento = entrar na sala** do marcador (hook existente); amarrar a
   baú/alavanca fica para depois.
5. Cada fala dispara **uma vez** (flag `disparada`).

## Estado atual relevante (verificado)

- `gm_say(text)` → broadcast `{type:"gm_narration", text}` (o cliente mostra no log).
- Entidades autoradas carregadas do defn em `enter_dungeon` (`self.armadilhas`,
  `self.decorations`, `self.secret_passages`, monstros, `self.master_reserve`,
  `self.expected_party`, `salas_visitadas`). `self.falas` segue o mesmo padrão.
- Entrada de sala: `handle_move` computa `entered = player_room(...)` e chama
  `_on_enter_room(pid, entered)` quando a sala não está limpa — ponto natural p/ o
  gatilho `sala` (e o `entered` também serve p/ proximidade, que roda no move).
- HUD do mestre: `renderMasterHud(state)` (game.js) — ponto p/ a seção "Falas".
- Editor: sistema de ferramentas (`S.tool`), entidades com painel de propriedades
  (`S.sel`), serialização no `save()`/load, validação (`const e = []`). A entidade
  "fala" segue o padrão de `traps`/`chests`.
- `validar_dungeon` (server) valida os campos autorados.

## Componentes

### 1. Editor — entidade "fala"

- Nova ferramenta `fala` (na paleta de ferramentas) que coloca um marcador numa casa
  de chão.
- Estado: `S.falas = [{ id, pos:[x,y], falante:{nome, emoji}, texto, trigger }]`.
  `trigger` = `{tipo, raio?}` onde `tipo ∈ {"proximidade","sala","manual"}` e `raio`
  (default 2) só p/ proximidade.
- Painel da fala selecionada: textarea do `texto`, inputs de falante (nome + emoji),
  select do `tipo`, input de `raio` (quando proximidade). Botão deletar.
- Serialização `falas: [...]` no `save()`/load. Render no mapa: um ícone (💬) na casa.
- Validação (editor + `validar_dungeon`): `texto` não-vazio; `tipo` válido; `pos` em
  chão; `raio` ≥ 1 quando proximidade.

### 2. Servidor — carga + gatilhos + disparo

- Carga: `self.falas = [ {..., "disparada": False} for f in defn.get("falas", []) ]`
  em `enter_dungeon`; resetado por masmorra nova.
- **Disparo** `_disparar_fala(fala)` (idempotente via `disparada`): marca
  `disparada=True` e faz `broadcast {type:"fala", falante, texto, pos}`.
- **Proximidade:** em `handle_move`, após o passo, para cada fala `proximidade` não
  disparada, se algum herói vivo está a ≤ `raio` (Chebyshev) do `pos` → dispara.
- **Sala:** no ponto de `entered = player_room(...)` (mesmo do rastreio de visita),
  disparar as falas `sala` cujo `pos` cai na sala `entered`.
- **Manual:** mensagem `disparar_fala {fala_id}` → handler `handle_disparar_fala`
  (guarda: `pid == master_pid`, `_mestre_ativo()`, a fala existe, é `manual`, não
  disparada) → `_disparar_fala`. Sem mestre humano, falas manuais nunca disparam
  (ninguém clica) — ok.
- `self.falas` (as manuais não-disparadas) vão no `game_state` p/ o HUD do mestre.

### 3. Cliente — popup + HUD do mestre

- **Popup (balão):** um evento `fala` abre `#fala-popup` (canto/centro-inferior) com
  `💬 emoji nome: texto`, some após ~5s ou ao clicar; fila simples p/ falas em
  sequência. Estilo leve, distinto do log e da story. `GS.on('fala', …)`.
- **HUD do mestre:** seção "💬 Falas" em `renderMasterHud` listando as falas `manual`
  não-disparadas (de `game_state.falas`) → botão que envia `GS.dispararFala(id)`.
- `src/gameState.js`: sender `dispararFala(falaId)` + evento `fala`.

### 4. Fronteiras de módulo

- `server.py`: `self.falas`, `_disparar_fala`, hooks em `handle_move`/entrada de sala,
  `handle_disparar_fala` + dispatch, serialização, validação.
- `tools/editor.js`: ferramenta + entidade + painel + serialização + validação.
- `game.js`: popup `#fala-popup` + seção no HUD do mestre.
- `src/gameState.js`: sender + evento.

## Testes

- **Servidor** (`tools/test_modo_mestre.py` ou dedicado):
  - `_disparar_fala` marca `disparada` e não repete.
  - proximidade dispara quando herói ≤ raio; não antes; uma vez.
  - `sala` dispara ao entrar na sala do marcador.
  - `handle_disparar_fala`: só mestre, só `manual`, não-disparada.
- **Editor/jogo:** `node --check`; verificação manual (colocar falas dos 3 tipos, ver
  os popups; botão manual no HUD do mestre).

## Fora de escopo

- Gatilho de evento além de "entrar na sala" (amarrar a baú/alavanca) — depois.
- Falas repetíveis (cada uma dispara uma vez).
- Retrato/imagem do falante (só nome + emoji).
- Geração dinâmica pela CPU (conteúdo é 100% pré-escrito, como o design pede).
- Custo de recurso (V2).
