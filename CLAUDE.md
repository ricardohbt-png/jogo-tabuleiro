# Legends for Hire — Regras de Arquitetura

## Visão Geral

RPG de tabuleiro multiplayer online (estilo HeroQuest / D&D) para até 6 jogadores.
Servidor WebSocket Python + cliente HTML/JS com renderização Three.js.

---

## Estrutura de Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | Servidor WebSocket (porta 8765) — toda lógica de jogo autoritativa |
| `index.html` | Shell HTML: CDNs do Three.js + scripts com cache-buster |
| `game.js` | Renderização e UI: 2D (canvas) e 3D (Three.js) — substitui o antigo `game.html` |
| `game.css` | Estilos do cliente |
| `src/gameState.js` | Módulo de estado do cliente — ZERO referências a DOM/canvas/Three.js |
| `src/visualConfig.js` | `window.VC` — fonte única de cores/intensidades/fontes do visual |
| `src/main.js`, `src/ui/theme.js` | Bootstrap e injeção de CSS custom properties |
| `assets/` | Peões (PNG), modelos 3D (GLB), retratos, fontes |
| `tools/` | Scripts DEV do pipeline de miniaturas (rodar da raiz: `python tools/<x>.py`) — desnecessários para jogar |
| `iniciar.bat` | Script de inicialização: mata porta antiga, sobe o servidor (porta única 8765), abre browser |
| `online.py` / `iniciar-online.bat` | Sobe servidor + túnel HTTPS (cloudflared/ngrok) e imprime UM link público para jogar pela internet |

---

## Regras de Arquitetura (OBRIGATÓRIAS)

### 1. Separação estrita: lógica vs. renderização

- **`gameState.js`** é o único lugar para lógica de jogo no cliente:
  - Estado do jogo (`gameState`, `lobbyState`, `cityState`)
  - BFS (pathfinding, alcance de movimento)
  - Decisores puros (`resolveAttack`, `resolveTileClick`, `activateSkill`)
  - Camada WebSocket (`connect`, `send`, `move`, `endTurn`, etc.)
  - **NUNCA** importar ou referenciar `document`, `canvas`, `THREE`, `window` aqui

- **`game.js`** é o único lugar para renderização:
  - Canvas 2D e Three.js 3D ficam aqui
  - Lê estado via `GS.*` (getters)
  - Registra callbacks via `GS.on(evento, fn)`
  - **NUNCA** implementar lógica de jogo ou cálculos de BFS aqui

### 2. Ordem de implementação de features

> **Estado primeiro, visual depois.**

Para qualquer nova feature:
1. Atualizar `gameState.js` — adicionar estado, getters/setters e/ou lógica pura
2. Atualizar `server.py` se necessário — novo protocolo de mensagem
3. Atualizar `game.js` — refletir o novo estado visualmente

### 3. Comunicação renderer → estado

O renderer (`game.js`) se comunica com `gameState.js` **apenas** via:
- `GS.on(evento, fn)` — registrar callbacks para eventos do servidor
- `GS.setter = valor` — mutar estado de UI (`pendingSkill`, `activeShop`, etc.)
- `GS.método()` — chamar action senders ou resolvers

O renderer **nunca** escreve diretamente em variáveis internas do módulo GS.

---

## Stack Técnica

### Servidor (`server.py`)
- Python 3.x + biblioteca `websockets`
- Porta: `ws://0.0.0.0:8765`
- Lógica autoritativa: mapa procedural, combate, monstros, XP/level, loja

### Cliente (`game.js` + `src/gameState.js`)
- Vanilla JS — sem frameworks, sem bundler
- Three.js `r128` (única versão com `examples/js/` disponível no jsDelivr)
- OrbitControls: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`
- **ATENÇÃO**: versões r148+ do Three.js removeram `examples/js/` — usar SEMPRE r128

### CDN (em `<head>` de `index.html`)
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

---

## Protocolo WebSocket

### Client → Server
| Mensagem | Campos |
|---|---|
| `create_room` | `name` |
| `join_room` | `name`, `code` |
| `rejoin` | `name`, `code` — religa um jogador desconectado em partida (recusa se ainda conectado). O cliente (`gameState.js`) salva a sessão em `localStorage` (`lfh_session`) e tenta sozinho 8× a cada 2,5 s; tela inicial tem botão "Reconectar". Move: o servidor sanitiza `dx`/`dy` para -1/0/+1 (1 casa ortogonal). |
| `select_class` | `class_id` |
| `start_game` | — |
| `move` | `dx`, `dy` |
| `attack` | `target_id` |
| `skill` | `skill_id`, `target_id` |
| `animar_mortos` | `cadaver_id` (Pedro anima cadáver adjacente) |
| `comandar_animados` | — (só no turno dos servos: todos os animados movem+atacam o monstro mais próximo automaticamente) |
| `mover_animado` | `animado_id`, `dx`, `dy` (controle manual — 1 passo) |
| `atacar_animado` | `animado_id`, `target_id` (controle manual — ataque) |
| `open_chest` | — |
| `open_door` | `tx`, `ty` — herói abre uma porta adjacente (Chebyshev ≤1). Ação **gratuita** (não gasta movimento/ação). Destranca a(s) sala(s) ligada(s) à porta, revela seu interior e **desperta** os monstros (que passam a perseguir). Salas começam trancadas (exceto a entrada); monstros em sala trancada ficam dormentes e o interior fica oculto pela névoa. **Clarividência** (`magia`, `alvoLivre`): alcance = mapa inteiro (mira em qualquer casa, mesmo na névoa — no 3D via `get3DTilePlane`); revela a área, os monstros ali (visibilidade ao vivo por 2 rodadas via `magic_reveal`) e as armadilhas do local, sem abrir a porta nem despertar os monstros. |
| `use_item` | `item_id` |
| `end_turn` | — |
| `enter_dungeon` | — |
| `buy_item` | `shop_id`, `item_id` |
| `magia` | `magia_id` (id em `GRIMORIO`) + alvo conforme o tipo: `target_id` (alvo/aliado), `tx`/`ty` (área), `dir:[dx,dy]` (Relâmpago — linha), ou nenhum (auto-centrado). Pedro (mage)/Lewis (cleric) lançam (ação principal). Custo: MP do círculo (`CIRCULO_MP`) + 🍖-1/💧-1. Conjuráveis (`GRIMORIO_IMPLEMENTADAS`): `manto_escuridao`, `visao_escuro`, `bola_fogo`, `relampago`, `raio_congelante`; o resto retorna "em desenvolvimento". O servidor anima dados via broadcast `dice_roll` (dano + d20 de save). |
| `ativar_cancao` | `atributos` (Henrique liga a Canção Heroica com os atributos escolhidos) |
| `desativar_cancao` | — (Henrique encerra a Canção Heroica) |
| `provocacao` | `target_id` (Henrique provoca um inimigo — ação bônus) |
| `cura` | `target_id`, `num_dados` (1–3), `alcance_extra` (0–2) — Lewis cura 1–3d8+INT um aliado; 💧-1/dado, 🍖-1/alcance (1/4/7q) — ação principal |
| `cura_area` | `num_dados` (1–3) — Lewis cura 1–3d8+INT todos os aliados no raio 5; 🍖-4 💧-4 por dado — ação principal |
| `purificacao` | `tipo` (`veneno`/`doenca`/`maldicao`/`petrificacao`), `target_id` — Lewis remove o efeito de um aliado adjacente — ação principal |
| `ressurreicao` | `target_id` — Lewis revive um aliado morto adjacente com 1 HP; 🍖-10 💧-10 — ação principal |
| `imposicao_maos` | `target_id` (Richard cura aliado adjacente — ação principal) |
| `golpe_sagrado` | — (Richard ativa +1d8 sagrado por ataque — ação bônus) |
| `desativar_golpe_sagrado` | — (Richard encerra o Golpe Sagrado) |
| `protetor` | `target_id` (Richard divide o dano de um aliado — ação bônus) |
| `desativar_protetor` | — (Richard encerra o Protetor) |
| `acao_livre_richard` | `habilidade_id` (`regeneracao_divina`/`guerreiro_luz`), `bonus` opcional |
| `criar_armadilha` | `tipo` (id em `ARMADILHAS`), `tx`/`ty` opcionais (default = casa do Luccas), `veneno_id` (só `fosso_envenenado`) — Luccas coloca uma armadilha (ação principal) |
| `desarmar_armadilha` | — (Luccas desarma armadilha na própria casa/adjacente; teste de DES; nat1 dispara nele) |

### Server → Client
`lobby_state`, `game_start`, `city_state`, `shop_result`, `enter_dungeon`,
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`

> `game_state` inclui `corpses` (cadáveres) e `armadilhas` (colocáveis — ver
> abaixo). `animar_result` traz
> `resultado`/`rolagem`/`d10_dezena`/`d10_unidade`/`chance`/`zona_hostil`/`animados`.

> **História (slides):** os campos `intro`/`outro` da campanha e de cada fase
> aceitam string (legado) **ou** objeto `{slides:[{text?,image?,fit}], audio?}`.
> O servidor normaliza (`_story_norm`/`_story_beat`) e envia o beat
> `{key, slides, audio}` em `game_state.campaign.story` (abertura),
> `city_state.campaign.story` (encerramento) e `game_over.story` (final).
> Imagens/áudios ficam em `assets/story/` (servida) e são referenciados por
> caminho. Cliente: `renderStory` (slideshow layout A + áudio em loop).

> **Portas/salas trancadas:** `game_state.tiles` usa `DOOR=2` nas entradas das
> salas; cada `room` traz `locked` (bool) e `doors` (`[[x,y],…]`). Porta fechada
> bloqueia movimento, LOS e a revelação de névoa do interior. `game_state.revealed`
> lista tiles revelados temporariamente por Clarividência (visibilidade ao vivo de
> monstros, mesmo através de portas fechadas). Servidor: `_is_closed_door`,
> `_blocks_tile`, `_tile_in_locked_room`, `door_rooms`, `magic_reveal`,
> `handle_open_door`; cliente: `GS.doorSets(state)`, `TILE_DOOR`, `drawDoor2D`,
> `doorMeshes` (3D).

### Armadilhas colocáveis (`game_state.armadilhas`)
Sistema distinto das `traps` de masmorra. Cada item: `id`, `tipo`, `pos:[x,y]`,
`icone`, `nome`, `visivel`, `ativada`, `aliada` (criador é jogador), `so_luccas`.
8 tipos em `ARMADILHAS` (server.py): `buraco`, `armadilha_urso`, `fosso_estacas`,
`rede`, `armadilha_incendiaria`, `mina_terrestre`, `fosso_envenenado`, `nuvem_gas`.
Save de Reflexos (gás = Fortitude); persistência/visibilidade por tipo; dano
progressivo (incendiária) tica em `_processar_efeitos_armadilha_turno`; `fosso_envenenado`
reusa `_aplicar_veneno`; `nuvem_gas` reduz CON via `_reduzir_con_temporario`.

---

## Classes de Personagem

`warrior`, `mage`, `rogue`, `cleric`, `ranger`, `paladin` — cada uma com 3 habilidades únicas.

---

## Renderização 3D (Three.js)

### Técnicas implementadas
- **Outline escuro** — clone BackSide escalonado ×1.075 (`isOutline:true`)
- **Blob shadow** — `CircleGeometry` com `depthWrite:false`, achatado em Z (`isGroundDecal:true`)
- **Halo pulsante** — `TorusGeometry` (`isPulseRing:true`) + `PointLight` (`isHaloLight:true`), animados em `startLoop3D`
- **OrbitControls** — esq: orbitar, dir: pan, scroll: zoom; `enableDamping=true` requer `controls.update()` a cada frame
- **Reset de câmera** — botão `⌂` + tecla `R`; vista isométrica SW 225°/52°

### Limites da câmera
```javascript
controls.minZoom        = 0.28;
controls.maxZoom        = 4.0;
controls.minPolarAngle  = 8  * Math.PI / 180;   // nunca abaixo do tabuleiro
controls.maxPolarAngle  = 82 * Math.PI / 180;
```

### Drag guard
`_orbitDragMoved` — previne clique em tile após arrastar câmera.

---

## Como Rodar

```bat
iniciar.bat          # encerra porta antiga, sobe o servidor, abre index.html no browser
```

Ou manualmente:
```bash
python server.py                  # serve PÁGINA + WebSocket em 0.0.0.0:8765
# abrir http://localhost:8765/index.html
```

> **Porta única:** `server.py` serve os arquivos do cliente (index.html, game.js,
> `src/`, `assets/`) na MESMA porta 8765 via `process_request` (allow-list +
> proteção contra path traversal) — não há mais `http.server` separado. Assim um
> único túnel HTTPS cobre página + `wss` no mesmo domínio (sem mixed content). O
> cliente infere o endereço de onde a página foi servida (`defaultServerUrl()` em
> `game.js`): `wss://<host>` se https, senão `ws://localhost:8765`.

Para jogar pela **internet** (link único para os amigos):
```bat
iniciar-online.bat   # ou: python online.py
```
Sobe o servidor + um túnel HTTPS (`cloudflared` recomendado, ou `ngrok http 8765`)
e imprime UM link `https://…/index.html` para compartilhar.

---

## Estado do Projeto (2026-05-26)

- Jogo totalmente funcional: mapa procedural, fog of war, combate, habilidades, baús, armadilhas, XP/level up, narração do GM
- Visualização 2D (canvas) e 3D (Three.js) com alternância em tempo real
- Peões 3D com geometrias custom, outline, sombra blob, halo pulsante para turno ativo
- OrbitControls com limites, reset de câmera (botão + tecla R)
- Sistema de cidade e loja de itens entre dungeons
