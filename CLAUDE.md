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
| `libertar_prisioneiro` | — (herói adjacente liberta o prisioneiro; grava `rescuer_pid`). O prisioneiro (`prisoner`: CA10/mov6/7HP) é **controlado pelo resgatador**, não anda sozinho. |
| `mover_prisioneiro` | `dx`, `dy` — controle manual do prisioneiro liberto (1 passo, só movimento). Habilitado na **janela pós-turno** do controlador (mesma do turno dos servos, `animados_phase_pid`): encerrar o turno abre a janela e dá `moves_left=6`; encerrar de novo avança. Se o resgatador morre, o controle passa ao herói vivo mais próximo. Dano vs CA10 dos monstros adjacentes continua na fase inimiga (`_processar_prisioneiro_turno`). O prisioneiro também **sofre armadilhas colocáveis** ao pisar nelas, como os heróis (saves a +0 em reflexos/fortitude); morte por qualquer fonte → `_prisioneiro_morre`/`rescue_failed`. |
| `encerrar_missao` | — (herói encerra a fase **após** o objetivo principal cumprido; só habilitado quando `game_state.mission_complete_pending`). Concluir o principal **não** encerra mais automaticamente: o servidor concede a recompensa, larga um baú e liga `mission_complete_pending`; o cliente mostra o botão "🏁 Encerrar missão" (com confirmação) que dispara esta mensagem. Recusa `pid` fora de `self.players`. |
| `open_chest` | — |
| `open_door` | `tx`, `ty` — herói abre uma porta adjacente (Chebyshev ≤1). Ação **gratuita** (não gasta movimento/ação). Destranca a(s) sala(s) ligada(s) à porta, revela seu interior e **desperta** os monstros (que passam a perseguir). Salas começam trancadas (exceto a entrada); monstros em sala trancada ficam dormentes e o interior fica oculto pela névoa. **Clarividência** (`magia`, `alvoLivre`): alcance = mapa inteiro (mira em qualquer casa, mesmo na névoa — no 3D via `get3DTilePlane`); revela a área, os monstros ali (visibilidade ao vivo por 2 rodadas via `magic_reveal`) e as armadilhas do local, sem abrir a porta nem despertar os monstros. |
| `use_item` | `item_id` |
| `throw_item` | `item_id`, `target_id` — arremessa um consumível de bolsa (id em `ARREMESSAVEIS`) num monstro-alvo. Ação principal; teste de ataque por DES vs CA; consome o item em acerto E erro; dano de fogo + status `em_chamas_rodadas` (tica 1/rodada). |
| `apagar_chamas` | — (herói em chamas gasta a ação principal para se apagar; única via contra o Fogo Grego, que ignora água). |
| `end_turn` | — |
| `enter_dungeon` | — |
| `buy_item` | `shop_id`, `item_id` |
| `magia` | `magia_id` (id em `GRIMORIO`) + alvo conforme o tipo: `target_id` (alvo/aliado), `tx`/`ty` (área), `dir:[dx,dy]` (Relâmpago — linha), ou nenhum (auto-centrado). Pedro (mage)/Lewis (cleric) lançam (ação principal). Nenhuma classe usa MP: o custo é um **slot de magia do círculo** (Lewis: `CLERIC_SLOTS`; Pedro: `MAGE_SLOTS_POR_NIVEL`, progressão por nível, resetam por turno via `slots_por_circulo`) + 🍖-1/💧-1. Conjuráveis (`GRIMORIO_IMPLEMENTADAS`): `manto_escuridao`, `visao_escuro`, `bola_fogo`, `relampago`, `raio_congelante`; o resto retorna "em desenvolvimento". O servidor anima dados via broadcast `dice_roll` (dano + d20 de save). |
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
| `interagir_decor` | `decor_id` — herói adjacente interage com uma decoração: fonte → recebe uma garrafa de água (consome 1 carga); container com loot → abre o painel de loot. Ação livre. |
| `take_from_decor` | `decor_id`, `kind` (`gold`/`item`), `index` — pega ouro/item de uma decoração-container (espelha `take_from_chest`; sem restrição de turno). |
| `guild_buy` | `item_id` — compra uma especialização/técnica na **Guilda dos Heróis** (id em `GUILD_CATALOG`). Só na cidade; valida classe, pré-requisito, posse e ouro; grava o save do personagem. |
| `guild_equip` | `slot` (`tecnica`\|`tecnica_exclusiva`), `item_id` (ou `null` p/ desequipar) — equipa uma técnica possuída no 4º slot. Só na cidade. `tecnica_exclusiva` só para mago/clérigo e só técnicas `exclusiva:true`. |
| `usar_tecnica` | `tecnica_id`, `target_id` opcional — ativa a técnica equipada na masmorra (no turno do herói). Valida equipada/fora de recarga/fome-sede; aplica efeito, debita 🍖/💧 e entra em recarga (`round_num + recarga_rodadas`). |

### Server → Client
`lobby_state`, `game_start`, `city_state`, `shop_result`, `enter_dungeon`,
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`,
`decor_loot`, `trap_result`

> `game_state` inclui `corpses` (cadáveres) e `armadilhas` (colocáveis — ver
> abaixo). `animar_result` traz
> `resultado`/`rolagem`/`d10_dezena`/`d10_unidade`/`chance`/`zona_hostil`/`animados`.
> Cada jogador em `game_state.players[]` também traz `facing` (`[dx,dy]`,
> ausente até o 1º passo — ver "Peão vira na direção do movimento" abaixo).

> **Popup de resultado de armadilha:** ao cair numa armadilha (buraco
> procedural genérico de `self.traps` ou qualquer uma das 8 do catálogo
> `ARMADILHAS`), o servidor manda `trap_result` (`send_to`, nunca broadcast —
> só quem foi afetado recebe) com `nome`/`icone`/`sucesso`/`dano`/`metade`/
> `descricao`/`efeitos_extra`/`tick`. Disparado em 4 pontos:
> `_verificar_trap_procedural` (buraco de sala), `_disparar_armadilha`
> (armadilha de 1 alvo), `_aplicar_armadilha_area` (Mina Terrestre/Nuvem de
> Gás — cada alvo atingido recebe o seu), e `_processar_efeitos_armadilha_turno`
> (tick de dano progressivo da Incendiária, com `tick:true`). Roteamento vai
> pro próprio jogador, ou pro `rescuer_pid` se o alvo for o prisioneiro
> (monstros/servos animados não recebem — sem cliente). Cliente: `game.js`
> abre `#trap-overlay` ~1,2s depois do evento (dá tempo da animação do dado
> terminar), com fila simples pra disparos simultâneos; fecha por botão, clique
> fora, ou Esc; tema de perigo (borda vermelha), com som curto só na falha.

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

> **Objetivos com recompensa:** cada objetivo (`objectives.primary` e cada
> `objectives.secondary[i]`) aceita `xp` (int — total dividido igualmente entre os
> heróis vivos, `max(1, xp//vivos)`) e `reward { gold, items:[{id}] }` (ouro
> dividido; itens largados num único baú via `_spawn_chest` em casa livre perto do
> grupo). Campos ausentes usam o padrão antigo (secundário 50 XP/25 ouro; principal
> sem extra). As recompensas são concedidas ao cumprir o objetivo **principal**
> (`_conceder_objetivo_reward`); a fase só termina quando um herói clica em
> "Encerrar missão" (`encerrar_missao` → `handle_encerrar_missao`).
> `game_state.mission_complete_pending` sinaliza esse estado. No editor: é possível
> **deletar salas** (mantendo ou limpando o chão) e definir XP/recompensa por
> objetivo (principal e secundários).

> **Decorações (`game_state.decorations`):** objetos colocáveis no editor que
> ocupam 1/2/4 casas (footprint `size:[w,h]` + `facing`, giro 90°). Catálogo
> autoritativo `DECOR_TYPES` (server.py, 22 tipos) com `alto`/`pisavel`/`loot_capaz`/
> `special`. Decorações sólidas bloqueiam movimento (entram em `_blocks_tile` via
> `_decor_block_tiles`); as **altas** ocluem a revelação de névoa por raycast
> (`_tall_oclui_caminho` em `_reveal_around`). **Fogueira** (`special:campfire`,
> pisável): 1d4 de fogo a quem entra (heróis e monstros — `_aplicar_fogueira_se_pisar`
> após cada commit de passo). **Fonte** (`special:fountain`): `interagir_decor` dá
> `garrafa_agua` e gasta 1 `charges`. **Containers** (`loot:{gold,items}`, qualquer
> tipo exceto fogueira): `interagir_decor`→`decor_loot`→`take_from_decor` (reusa o
> painel de baú via `abrirPainelLoot`; servidor re-envia `decor_loot` após cada take
> p/ atualizar o painel). Footprint resolvido por `_decor_tiles`/`_decor_tiles_at`
> (espelhado no cliente `GS.decorTilesOf` e no editor `decorTilesAt`). Render: 2D
> emoji + 3D geometria procedural (`DECOR_3D`/`decorMeshes`, preparado p/ GLB).
> Validação em `validar_dungeon`; catálogo exportado p/ o editor via
> `export_catalog.py`. Testes: `tools/test_decoracoes.py`, `tools/test_decor_roundtrip.py`.

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

> **Ficha na cidade (autoritativa):** cada card de herói em `screen-city` mostra a
> foto do rosto (3:4, `HERO_PORTRAIT_PATHS`). Clicar abre `abrirFichaCidade(pid)` —
> painel lateral ESQUERDO deslizante (`#ficha-cidade-panel`) com atributos
> (`renderConteudoAtributosFichaJogo`) + equipamento (8 slots de `player.gear`) +
> inventário (`player.bag`). O próprio herói equipa/desequipa (botão/clique) e
> organiza a bolsa por **arrastar-e-soltar** (reordenar; arrastar item p/ um slot
> equipa; arrastar do slot p/ a bolsa desequipa); outros heróis abrem em
> **só-leitura**. Usa o modelo AUTORITATIVO do servidor:
> `equip_from_bag`/`equip_offhand`/`unequip`/`reorder_bag`, com broadcast ciente da
> fase (`push_state_or_city` → `broadcast_city_state` na cidade,
> `push_state`/`game_state` na masmorra). Cliente: `_updateCityHeroBar` (fotos +
> clique), `renderFichaCidadeBody`, `_refreshFichaCidadePanel` (re-render ao chegar
> `city_state`), `_fcDropOnGear`/`_fcDropOnBag` (drag-and-drop). Teste do servidor:
> `tools/test_ficha_cidade.py`.

> **Cidade × masmorra são exclusivos no cliente:** o handler de `city_state`
> (`gameState.js`) limpa `gameState = null` (espelhando o `enter_dungeon`, que limpa
> `cityState`). Sem isso, leitores que preferem `gameState` — como o modal de
> inventário (`InventoryModal._currentPlayer`, que lê `GS.gameState` e só cai para
> `GS.cityState`) — mostravam o paperdoll/bolsa **congelados** da última masmorra na
> cidade (bug: armadura recém-comprada aparecia ao vender, que lê `cityState`, mas
> não no boneco). Ao adicionar um novo leitor de estado, lembre que na cidade só o
> `cityState` está preenchido e na masmorra só o `gameState`.

> **Aquisição de itens — bolsa-primeiro (`_route_acquired_item`):** todo item
> adquirido por compra OU loot passa por `_route_acquired_item(p, item)` (server.py),
> que retorna `'bag' | 'equipped' | 'full'`: (1) bolsa com espaço → **bolsa** (NÃO
> auto-equipa, mesmo com o slot livre); (2) bolsa cheia + slot correspondente livre e
> compatível → **resgate-equipa** (`_rescue_equip`, que espelha `handle_equip_from_bag`
> — aplica `_apply_gear_effect` e, p/ arma, sincroniza a cópia de combate
> `p["weapon"]`); (3) bolsa cheia + slots ocupados/inequipável → `'full'` (compra
> estorna ouro; loot fica no baú/container). `_free_equip_slot_for` mapeia a categoria
> (`_slot_category_for_item`) ao slot livre e respeita restrição de classe e conflito
> de arma de 2 mãos × escudo/2ª arma. **Exceções:** munição (empilhamento próprio em
> off_hand/bolsa) e consumíveis (categoria `bag` → só a bolsa) não usam o passo 2.
> Pontos de chamada: `handle_shop_buy` (arma/armadura/escudo/anel/acessório/provisão),
> `handle_take_from_chest`, `handle_take_from_decor`. Como comprar não auto-equipa
> mais no slot vazio, o bloqueio pré-compra de arma-2-mãos × escudo foi removido (o
> item vai pra bolsa; o conflito é validado só ao equipar). Teste do servidor:
> `tools/test_roteamento_itens.py`.

> **Largar/pegar itens no chão (`game_state.ground_items`):** na masmorra, o herói
> larga um item numa das 8 casas adjacentes e pega de volta — inclusive item largado
> por OUTRO herói (forma de passar itens e de descartar sem ir à cidade). Estado
> `self.ground_items` (`gid -> {id, item, pos}`) **persiste como `self.chests`**: fica
> na memória do `GameRoom` ao ir/voltar da cidade (mesmo lugar) e só é limpo no bloco
> de masmorra nova (`if nova:`, junto de corpses/chests), ou seja, após encerrar a
> missão. **Largar** (`drop_item {source:'bag'|'gear', index|slot_key}`): ação LIVRE
> a qualquer momento (sem `_is_turn`); da bolsa ou de um slot equipado (desequipa na
> hora — reverte `_apply_gear_effect` e reseta `p["weapon"]`); o servidor escolhe a
> 1ª casa livre via `_free_drop_tile_near` (chão livre de parede/porta/decoração
> sólida via `_blocks_tile`, monstro/jogador vivo, baú e outro item); sem casa → recusa.
> **Pegar** (`pickup_item {ground_id}`): ação livre, qualquer jogador, adjacente
> (Chebyshev ≤1), roteia pelo `_route_acquired_item` (bolsa-primeiro; bolsa+slot cheios
> → recusa, fica no chão). Cliente: `GS.groundItems`/`dropItem`/`pickupItem`/
> `groundItemPickable`; largar = arrastar o item pra FORA do modal (backdrop) na
> masmorra; render 2D (emoji + brilho) e 3D (`buildGroundItem3D`, sprite + brilho,
> `g3.groundItemMeshes`) espelham os baús; pegar = clicar na casa (hook unificado
> `handleTileClick`, cobre 2D e 3D). Teste do servidor: `tools/test_ground_items.py`.

> **Guilda dos Heróis (Fase 0):** novo prédio na cidade (hotspot `guilda` →
> `openGuild`) onde cada personagem compra aprimoramentos **permanentes**:
> **Especializações** (upgrades sempre-ativos das habilidades-base — conteúdo nas
> Fases 1+) e **Técnicas da Guilda** (habilidades ativas num **4º slot**; só 1
> equipada por vez, mago/clérigo têm 1 genérica + 1 exclusiva). Catálogo declarativo
> `GUILD_CATALOG` (server.py, estilo `GRIMORIO`/`DECOR_TYPES`); Fase 0 traz a técnica
> de referência **Brutalidade** (+2 dano de arma até o fim do turno; recarga 3
> rodadas; 🍖-2/💧-2). Dados no jogador: `guild_owned`/`guild_equip` (persistidos),
> `technique_cooldowns` (runtime). **Persistência:** save por personagem em
> `saves/<class_id>.json` (`load_guild_save`/`write_guild_save`/`apply_guild_save`,
> carregado no `start_game`; `saves/` é gitignored). **Trava de em-uso:**
> `CHARACTERS_IN_USE` impede escolher em duas salas o mesmo personagem — implicação:
> só um grupo joga cada personagem por vez no servidor (`select_class` trava;
> `release_character`/`_release_all_locks` liberam na desconexão). **Recarga:**
> `pronta_em = round_num + recarga_rodadas`; zera ao voltar à cidade
> (`_voltar_para_cidade`). Compra `handle_guild_buy` (bloco `guild` no `city_state`);
> equipar `handle_guild_equip` (na ficha); usar `handle_usar_tecnica` (4º botão no
> HUD). Cliente: `GS.guildBuy/guildEquip/usarTecnica` +
> `guildCatalogFor/guildOwnedOf/guildEquipOf/tecnicaRestante` (os getters caem para
> o player do `game_state` na masmorra, onde `cityState=null`; catálogo cacheado).
> Teste do servidor: `tools/test_guilda.py`.

> **Especializações do Guerreiro (Fase 1a):** upgrades permanentes sempre-ativos
> (não ocupam slot; sempre válidos) que aprimoram as 3 habilidades-base. **Baseline
> enfraquecido (grátis):** Mira +2 acerto, **Golpe ×1,5** (era ×2 — mudança de
> gameplay; Golpe III restaura ×2), Fúria +1 ataque extra, e **só 1 habilidade
> armada por turno**. **Compras** (`categoria:"especializacao"`, `classe:"warrior"`
> no `GUILD_CATALOG`): `guerreiro_combinar_2` (150, portão — arma 2/turno),
> `guerreiro_mestre_combate` (300, arma 3/turno), `guerreiro_mira_3` (+2 dano),
> `guerreiro_golpe_3` (×2), `guerreiro_furia_3` (2 ataques extras) — os quatro
> exigem `guerreiro_combinar_2`. Ouro é o único custo. Efeitos em `handle_attack`
> via `tem_espec` + helpers `_teto_combinacao`/`_golpe_raw`/`_furia_extras`/
> `_mira_dano_bonus`; o servidor **trunca** os `buffs` ao teto (autoritativo).
> Refactor: Fúria virou contador `skill_ataques_extras` (antes 2 booleanos);
> `skill_bonus_dano` novo (Mira III). Cliente: `GS.warriorComboCap()` limita a
> armação e as descrições dos botões refletem o nível possuído. Teste:
> `tools/test_guerreiro_espec.py`.

> **Especializações do Clérigo (Fase 1b):** gateiam os 4 milagres do Lewis
> (baseline enfraquecido — **mudança de gameplay**: Cura 3d8→**1d8**, Cura em Massa
> raio 5→**2**). **Compras** (`categoria:"especializacao"`, `classe:"cleric"`; II=150,
> III=200, III exige II por linha): `clerigo_cura_2/3` (máx 2d8/3d8),
> `clerigo_massa_2/3` (2d8 raio 4 / 3d8 raio 6), `clerigo_purif_2/3` (+doenças /
> +maldições **e petrificação**), `clerigo_ressur_2/3` (metade PV 🍖15💧15 / PV cheio
> 🍖20💧20). Gating em `handle_cura`/`handle_cura_area`/`handle_purificacao`/
> `handle_ressurreicao` via `_cura_teto`/`_massa_nivel`/`_purif_tipos`/`_ressur_nivel`
> (+`tem_espec`). O "custo crescente" do design já vem da escala existente (💧/dado,
> 🍖4💧4/dado, custo por tipo); a Ressurreição usa custo por nível 10/15/20. Cliente:
> `GS.clericCuraTeto/clericMassaNivel/clericPurifTipos/clericRessurNivel` limitam os
> painéis do Lewis. Teste: `tools/test_clerigo_espec.py`.

> **Especializações do Paladino (Fase 1c):** gateiam as 5 habilidades de Richard
> (baseline enfraquecido — **mudança de gameplay**: Guerreiro da Luz 4→**2**
> atributos simultâneos, Cura pelas Mãos 2d6→**1d6**, Golpe Sagrado 2d8→**1d8**,
> Defensor 50/50 fixo, Regeneração só cura o próprio Richard). **Compras**
> (`categoria:"especializacao"`, `classe:"paladin"`; II=150, III=200, III exige II
> por linha, exceto `ataque_sagrado` que só tem II): `paladino_cura_maos_2/3` (2d6;
> opção +1d6 por +2🍖+2💧, até 3×), `paladino_ataque_sagrado_2` (+2d8 sagrado),
> `paladino_luz_2/3` (3/4 atributos + **detecta armadilhas** em raio 2/3 — feature
> nova, quando Visão ativa), `paladino_defensor_2/3` (raio 5; split 40%/40%, 20%
> mitigado — era 50/50), `paladino_regen_2/3` (cura +1 HP também aliados em raio
> 1/2). Gating em `handle_imposicao_maos`/`handle_attack` (bloco Golpe Sagrado)/
> `_ativar_guerreiro_luz`/`handle_protetor`+`_processar_dano_protetor`+upkeep/
> `_processar_manutencao_richard` via `tem_espec` + helpers `_cura_maos_dados`/
> `_ataque_sagrado_dados`/`_gdl_max_atributos`/`_gdl_trap_raio`/`_defensor_raio`/
> `_defensor_split`/`_regen_raio`. A detecção de armadilhas do Guerreiro da Luz
> reusa `_revelar_armadilhas_raio` — generalização de `_revelar_armadilhas_luccas`
> (Ladino) por raio parametrizado; o Ladino mantém comportamento idêntico (chama o
> mesmo método com seu próprio raio de visão). Cliente:
> `GS.paladinCuraMaosDados/paladinCuraMaosExtra/paladinAtaqueSagradoDados/
> paladinLuzMaxAtributos/paladinDefensorRaio/paladinDefensorSplit/paladinRegenRaio`
> limitam os painéis de Richard (o teto de atributos do Guerreiro da Luz é
> bloqueado no cliente E recusado pelo servidor — autoritativo). Teste:
> `tools/test_paladino_espec.py`.

> **Especializações do Ladino (Fase 1d):** gateiam as 5 linhas de Luccas —
> inclui um **redesign real** (não só números) do Ataque Furtivo e um catálogo
> **extensível** de Fórmulas de Armadilha. **Ataque Furtivo:** baseline
> enfraquecido — hoje disparava com "aliado adjacente" de graça; isso vira
> `ladino_furtivo_2` (compra); o base fica só oculto/invisível
> (`invisivel_sombras`/`oculto_vela`). `ladino_furtivo_3` (Supremo) é uma
> **mecânica nova**: reação automática — quando qualquer aliado que não seja
> Luccas acerta um inimigo vivo, Luccas desfere um furtivo nele também
> (1×/inimigo/rodada, bloqueado se Luccas estiver petrificado/paralisado/
> imobilizado). Hookado em `handle_attack` e `handle_throw` via
> `_furtivo_reativo`; **fora de escopo**: ataque de mão secundária, arremesso de
> lança, animados controlados. **Fórmulas de Armadilha:** hoje todas as 8
> armadilhas de `ARMADILHAS` eram fabricáveis de graça — agora `buraco`
> continua sempre livre e as outras 7 exigem a fórmula correspondente. O
> catálogo é **gerado dinamicamente**: cada tipo em `ARMADILHAS` ganha campos
> opcionais `formula_guild_id`/`formula_preco`; `_gerar_catalogo_formulas_armadilha()`
> lê esses campos e popula `GUILD_CATALOG.update(...)` — armadilhas futuras só
> precisam desses 2 campos para aparecerem na Guilda automaticamente, sem tocar
> em mais nada. Gate em `handle_criar_armadilha` via `_armadilhas_desbloqueadas`.
> **Desarme:** `ladino_desarme_2/3` dão +2 no teste (não soma mais no III);
> `_3` também adiciona um 2º teste que, em sucesso, devolve o `custo_ouro` da
> armadilha. **Veneno Rápido:** refactor de campo escalar para 2 slots —
> `ladino_veneno_2` faz o veneno melee durar 2 golpes (era 1); `ladino_veneno_3`
> permite manter 2 venenos diferentes na arma ao mesmo tempo
> (`weapon_poison`/`weapon_poison_2`, cada um decrementando independente); só
> afeta corpo a corpo — à distância e o efeito genérico de item `coat_poison`
> ficam inalterados. **Esconder nas Sombras:** `ladino_esconder_2/3` dão +2 no
> teste; `_3` também faz a ativação **deixar de gastar a ação bônus** e, ao
> quebrar a invisibilidade (`_quebrar_invisibilidade`), concede +2 de CA por 1
> rodada via `self.temp_def` (mecanismo já existente que expira sozinho).
> Cliente: `GS.ladinoArmadilhasDesbloqueadas/ladinoFurtivoNivel/
> ladinoDesarmeBonus/ladinoDesarmeRecupera/ladinoVenenoMaxHits/
> ladinoVeneno2Slots/ladinoEsconderBonus/ladinoEsconderLivre` — o painel de
> criar armadilha filtra por fórmula destravada (com dica "🔒 Compre a fórmula
> na Guilda"). Teste: `tools/test_ladino_espec.py`.

> **Especializações do Bardo (Fase 1e):** gateiam as 3 linhas de Henrique.
> **Canção Heroica:** 5 nós `bardo_cancao_{acerto,dano,ca,movimento,resistencia}`
> (100 cada) sobem aquele atributo de +1 para +2 (`_cancao_nivel_atributo` em
> `_aplicar_buffs_cancao`); `bardo_cancao_suprema` (200) reduz a manutenção em
> -1🍖/-1💧 mín 0 (`_cancao_custo_reducao`, aplicado na ativação; `cancao_custo`
> guarda o valor já reduzido, então o upkeep herda a redução). **Provocação:**
> `bardo_provocacao_2` (150) faz a desvantagem durar toda a provocação (o reset de
> `provocado_turno_efeito` nos 2 sites de ataque de monstro é pulado enquanto o
> provocador tem a espec), dá +2 CA ao bardo (`_provocacao_ca_bonus` somado à
> `effective_ac` nos 2 sites) e vantagem ao bardo contra o alvo; `bardo_provocacao_3`
> (200, requer _2) estende a vantagem a todos os aliados por 1 rodada
> (`provocado_aliados_vantagem_round == round_num`). Vantagem via
> `_provocacao_atk_vantagem` em `handle_attack`. Helpers: `_provocador` (bardo vivo
> que provocou). **Lendas:** catálogo **gerado** de `MONSTER_DEFS`
> (`_gerar_catalogo_lendas` + `GUILD_CATALOG.update`, preço por tier T1 60/T2 90/T3
> 120/T4 200) — cada `lenda_<tipo>` dá +1 de ataque (`_lenda_atk_bonus` em `eff_atk`)
> e +1 de resistência (`_lenda_resist_bonus` via novo param `fonte` de `_testar_save`,
> passado nos 6 sites de habilidade de monstro vs jogador — modular, derrubar,
> agarrar, constrição, infecção, força descomunal — e no save de escape de agarrão;
> demais saves ficam inertes com `fonte=None`) contra a espécie; só Henrique na base.
> `bardo_lendas_supremas` (300) estende ambos os bônus a todo o grupo enquanto
> Henrique vive (`_bardo_lendas`). Cliente: `GS.bardoCancaoNivel/bardoCancaoSuprema/
> bardoProvocacaoNivel/bardoLendasSupremas` — o painel da Canção mostra +1/+2 por
> atributo e a manutenção reduzida; a descrição da Provocação reflete II/III. Teste:
> `tools/test_bardo_espec.py`.

> **Especializações do Mago (Fase 1f):** gateiam a **Metamagia** de Pedro
> (Aprimorar/Estender/Fortalecer). Baseline enfraquecido (**mudança de gameplay**):
> hoje as 3 metamagias empilhavam ilimitado → **1 por lançamento**; **Fortalecer**
> ×1,5 → **×1,25**. **Compras** (`categoria:"especializacao"`, `classe:"mage"`; III
> exige II): `mago_tecelagem_2/3` (empilhar 2/3 — 150/300), `mago_fortalecer_2/3`
> (×1,5/×2 — 200/250), `mago_aprimorar_2/3` (+2/+3 CD — 150/200), `mago_estender_2/3`
> (+2/+3 rodadas — 150/200). O núcleo é `_resolver_metamagia(p, magia)` — helper puro
> que substituiu o bloco inline de `handle_magia`: reúne as metamagias armadas E
> aplicáveis (dano/duração/save), trunca ao `_teto_metamagia(p)` na ordem
> Fortalecer→Estender→Aprimorar (as excedentes não aplicam nem cobram), e aplica as
> magnitudes via `_fortalecer_mult`/`_aprimorar_bonus`/`_estender_bonus`. A metamagia
> gravada em **pergaminho** (`gerar_pergaminho`) fica inalterada (+1/×1,5/+1).
> Cliente: `GS.magoTecelagemCap/magoFortalecerMult/magoAprimorarBonus/
> magoEstenderBonus` — as descrições dos botões refletem magnitude + teto de
> empilhamento. Teste: `tools/test_mago_espec.py`.

> **Técnicas de Recarga Curta (Fase 2a):** 1º lote das **Técnicas da Guilda** (4º
> slot, genéricas — `categoria:"tecnica"`, `classe:None`, recarga 3, preço 100).
> Fase 2 organizada por **faixa de recarga** (3/5/8/10 rodadas — quanto maior a
> recarga, mais forte/cara a técnica); a aba de Técnicas da Guilda é agrupada por
> faixa (`_renderGuild`). 4 técnicas, despachadas por `efeito.tipo` em
> `handle_usar_tecnica` (que já centraliza turno/recarga/custo e **não** consome a
> ação — "buff-and-act"): **Mira Perfeita** (`mira_perfeita` — próximo ataque à
> distância com vantagem +2 dano; flag `tecnica_mira_perfeita` capturada em
> `_mira_ranged` no `handle_attack`, consumida no ataque à distância mesmo em erro,
> expira no fim do turno), **Espírito Indomável** (`remove_status`, ação livre —
> limpa medo/atordoamento/lentidão + 1 rodada `imune_silencio_ate`, lido em
> `_em_silencio`), **Grito de Guerra** (`buff_aliados_mov` — +2 movimento a todos os
> aliados: bump imediato + `mov_bonus_ate`/`mov_bonus_val` somados dentro de
> `_moves_base` via `_grito_mov_bonus`, o cálculo autoritativo usado no reset de
> turno), **Pressa** (`mov_self_dobrar` — `moves_left += spd`; custo 4/4). Teste:
> `tools/test_tecnicas_espec.py`. Próximos lotes: 2b (5r), 2c reações
> (Contra-Ataque/Ataque Coordenado/Oportunidade/Sangue Frio — exigem framework de
> reação), 2d passivas (Último Esforço); Fase 3 exclusivas Mago/Clérigo.

> **Técnicas de Recarga Média (Fase 2b):** 2º lote das Técnicas da Guilda (recarga 5,
> preço 180, +4🍖/+4💧). **Investida Heroica** (`investida` — dobra movimento; se a
> carga for reta ≥2 casas desde a ativação e o ataque for corpo a corpo, vantagem +2
> dano; `_investida_tecnica_bonus` consumido em `handle_attack` — nome distinto do
> `_investida_bonus` do Ogro), **Defesa Impecável** (`defesa_impecavel` — até o próximo
> turno, ataques contra você com desvantagem via `_defesa_impecavel_ativa` nos 2 sites
> de ataque de monstro; + imune a furtivo em `_verificar_ataque_furtivo` — inerte hoje,
> nenhum monstro dá furtivo a jogador), **Pressão Constante** (`debuff_ca_alvo` —
> inimigo **adjacente** −2 CA por 2 rodadas via `_pressao_ca_pen` no `eff_target_ac`),
> **Tática Defensiva** (`tatica_defensiva` — aliado em raio 4, 1d4 rodadas, split 50/50
> generalizando `_processar_dano_protetor`: protetor genérico além do Protetor do
> paladino), **Passo Fantasma** (`passo_fantasma` — 1d4 rodadas: +2 movimento
> [compartilha `mov_bonus_*` com o Grito] + atravessa objetos em `handle_move`,
> mantendo paredes/portas/criaturas). Cliente: técnicas com campo `alvo`
> (`monstro_adjacente`/`aliado_raio4`) abrem `openTargetModal` no botão do 4º slot.
> Teste: `tools/test_tecnicas_espec.py`. **Foco Absoluto** adiado (vira reação
> "Resistência Absoluta" no lote de reações — resolver conflito de nome com a de 8r).

> **Técnicas de Reação (Fase 2c):** 3º lote das Técnicas da Guilda — **reações**
> que **auto-disparam** dentro de hooks de evento (sem prompt) e aplicam efeito
> **direto** (nunca re-chamam `handle_attack` → sem recursão), espelhando o
> `_furtivo_reativo` do Ladino (Fase 1d). Núcleo compartilhado
> `_ataque_basico_reativo(atacante, alvo)`: ataque fora-de-turno via `_rolar_ataque`
> vs CA do alvo, dano `roll_dice(die)+mod(stat)` (crít ×2), e — se o atacante for o
> **Ladino** e `_verificar_ataque_furtivo` passar — soma os d4 de furtivo
> (`_dados_furtivo`); mata via `_monster_dies`. 4 técnicas (recarga 5, preço 180,
> +4🍖/+4💧, salvo indicado): **Resistência Absoluta** (`buff_saves` — +2 em **todos**
> os saves por 2 rodadas; `resistencia_saves_ate`/`_val`, somado em `_testar_save`
> junto ao `_lenda_resist_bonus`), **Sangue Frio** (`sangue_frio` — arma a re-rolagem
> do **1º erro** de ataque do turno; `sangue_frio_armado` consumido em `handle_attack`
> logo após o `_rolar_ataque` do jogador, antes de limpar os flags de Mira/Investida —
> 2🍖/2💧), **Ataque Coordenado** (`ataque_coordenado`, `alvo:"aliado"` — marca um
> aliado vivo como par [`coordenado_alvo`/`coordenado_turno`]; quando **você** acerta
> um monstro no seu turno, o par desfere um `_ataque_basico_reativo` se o alvo estiver
> no alcance da arma dele [`_alvo_no_alcance_arma`]; disparado em `handle_attack` após
> o custo de sobrevivência; reset no fim do turno), **Contra-Ataque**
> (`contra_ataque`, recarga **8**, preço 280, +6🍖/+6💧 — `contra_ataque_ate =
> round_num+1`; quando um monstro **erra** um ataque contra você, revida com
> `_ataque_basico_reativo` a **cada** erro na janela; **só armas corpo a corpo** via
> `_arma_contra_ataque_ok` [exclui arco/besta pesada de `RANGED_AMMO`, mas **inclui a
> besta de mão** `hand_crossbow`] e o alvo precisa estar no alcance de ameaça da arma
> [`_alvo_no_alcance_arma` respeita `range`/`reach:lanca`/`reach:cajado`/adjacência];
> hookado nos **2 sites de erro de monstro** — `_execute_one_monster_attack` e o loop
> legado). Cliente: técnica com `alvo:"aliado"` abre `openTargetModal` (par, qualquer
> distância) no 4º slot. Teste: `tools/test_tecnicas_espec.py` (seções [12]-[17]).
> **Oportunidade** (adiada desta fase) virou um mini-lote próprio — ver Fase 2d abaixo;
> deixou de ser uma reação de ordem-de-turno.

> **Oportunidade (Fase 2d):** mini-lote adiado da 2c — **redesenhado em
> brainstorming**: não é mais uma reação, é uma técnica de suporte. Tier **10**
> (novo, acima do 8 do Contra-Ataque): 350 ouro, +6🍖/+6💧, recarga 10, `alvo:"aliado"`
> (nunca você mesmo). Concede um **crédito de ação extra** reservado para o PRÓPRIO
> turno do aliado (não imediato) — expira sozinho se `round_num` avançar antes de ser
> usado (`oportunidade_credito`/`oportunidade_round`, comparado no momento do uso, sem
> precisar de reset explícito). Duas vias mutuamente exclusivas para o mesmo crédito
> booleano: **(1) ação principal extra** — unificado com o mecanismo já existente da
> magia Velocidade dentro do helper `_acao_bloqueada` (2 branches paralelos: Velocidade
> e Oportunidade, cada um consome seu próprio crédito e libera a ação); **(2) movimento
> extra** — novo handler `handle_usar_oportunidade_movimento` (`+spd` em `moves_left`).
> Para a via 1 cobrir TODAS as ações principais (não só ataque/magia, que já usavam
> `_acao_bloqueada`), migrou 9 handlers que faziam checagem crua de `action_done`
> (`handle_animar_mortos/cura/cura_area/purificacao/ressurreicao/imposicao_maos/
> criar_armadilha/desarmar_armadilha/libertar_prisioneiro`) para usar `_acao_bloqueada`
> — efeito colateral aceito: a Velocidade agora também vale nessas 9 (antes só valia em
> ataque/magia), tratado como correção de inconsistência pré-existente. Cliente:
> `GS.usarOportunidadeMovimento()` + botão no HUD condicionado a
> `me.oportunidade_credito && me.oportunidade_round === state.round` (o round-check
> foi um catch de code-review — sem ele o botão apareceria com crédito já expirado).
> Teste: `tools/test_tecnicas_espec.py` (seções [18]-[22]).

> **Reviver os Mortos (Fase 1g):** gateia a habilidade de classe de Pedro (não
> mexida nas Fases 1a–1f). Slots de Controle = mod(INT) + nível_Pedro÷2 (mín. 1;
> **mantido** o termo de nível de Pedro, ao contrário do padrão "baseline
> enfraquecido" das outras linhas). **Compras** (`categoria:"especializacao"`,
> `classe:"mage"`; III exige II): `mago_reviver_2` (200, ND passa a ocupar Slots
> fracionários **exatos** — antes toda criatura ocupava sempre 1 Slot — e chance
> de sucesso 100%−ND×15%), `mago_reviver_3` (300, +2 Slots de Controle e chance
> 100%−ND×10%). Nível I (baseline) mantém 1 Slot fixo por criatura e chance
> 100%−ND×20%. **Bônus de nível de Pedro:** todos os Níveis da Guilda somam
> +5% de chance por nível de Pedro (`p["level"]×5`, antes do teto/piso 1–99%) —
> ex. Pedro nível 3 animando ND1 no Nível II: 85%+15% = 100%→clamp 99%. **Zona hostil preservada e inalterada pelos Níveis:** a falha
> catastrófica (cadáver ressuscita vivo e hostil) continua a fórmula original —
> só existe risco quando o ND do monstro excede o teto "seguro" pro nível de
> Pedro (`nivel_max` 2/4/5 conforme nível 1-2/3-4/5+; `zona_hostil = max(0,
> (ND−nivel_max)×10)`); comprar a Guilda só melhora a chance de sucesso "normal",
> não reduz esse risco. ND agora é o CR fracionário real do monstro (`corpse["nd"]`,
> gravado em `_monster_dies`; monstros sem `cr` caem para `tier` como ND inteiro),
> distinto do `corpse["nivel"]` (inteiro, ≥1, usado só como bônus de ataque do
> animado). Helpers: `_reviver_nivel`/`_reviver_slots_max`/`_reviver_slot_custo`/
> `_reviver_chance`, usados em `handle_animar_mortos`. Cliente:
> `GS.magoReviverNivel/magoReviverSlotsExtra/magoReviverSlotCusto/magoReviverChance`
> — o duplicado de `HERO_DATA.pedro.habilidadeClasse` em `game.js` (ficha/tooltip,
> não autoritativo) chama esses getters em vez de recalcular. Teste:
> `tools/test_reviver_mortos.py`.

> **Técnicas de Recarga Longa (Fase 2e):** 4º lote das Técnicas da Guilda, tier
> **10** (350 ouro, recarga 10; +6🍖/+6💧 em três delas — **Sorte** é a exceção, só
> +2🍖/+2💧). **Instinto de Sobrevivência** (`passiva_evitar_morte`) é automática:
> segue o padrão já existente do `_player_dies` (mesmo ramo da Regeneração do
> Paladino) — se o dano zeraria o HP, sobrevive com 1 e entra em recarga. **Último
> Esforço** (`passiva_ultimo_esforco`) também é automática e sobrevive com 1 HP,
> mas além disso abre uma sub-fase de **2 mini-turnos** ("last stand"): mecanismo
> final usa `self.last_stand_pid`/`self.last_stand_event` (`asyncio.Event`),
> `_is_turn` alargado para aceitar `last_stand_pid == pid` (espelhado no cliente,
> ver abaixo), `_abrir_ultimo_esforco` (que aguarda o Event antes de deixar
> `_player_dies` prosseguir para a finalização normal da morte — não há mais
> `return` antecipado nesse ramo), e `_fechar_mini_turno_ultimo_esforco` (decrementa
> os turnos restantes e fecha o Event no fim, hookado em `handle_end_turn` e em
> `handle_disconnect_em_jogo`), com um timer de segurança dedicado
> (`_iniciar_timer_ultimo_esforco`/`_cancelar_timer_ultimo_esforco`/
> `_ultimo_esforco_timer_expira`) que espelha o timer de turno normal já existente,
> **incluindo a mesma guarda de auto-cancelamento** (`t is not
> asyncio.current_task()`) do `_cancelar_timer_turno` pré-existente. Dois
> reforços de concorrência que NÃO estavam no plano original e só surgiram em
> revisão: (a) o ramo do `_player_dies` só abre uma nova janela se
> `self.last_stand_pid is None` — evita que uma segunda morte simultânea corrompa
> uma janela já aberta (o segundo jogador simplesmente não recebe o efeito da
> técnica dessa vez, sem gastar a recarga); (b) o `_cancelar_timer_ultimo_esforco`
> tem a mesma guarda de auto-cancelamento do `_cancelar_timer_turno`. **Golpe
> Decisivo** (`golpe_decisivo`) é manual (arma-e-age): força o próximo ataque
> básico a ser crítico automático no acerto, e triplica (em vez de dobrar) num
> natural 20 enquanto armado. Isso generalizou o multiplicador de crítico de
> `handle_attack` — antes um `dmg *= 2` fixo, agora `dmg *= 3 if (_forca_critico and
> roll == 20) else 2`, onde `_forca_critico = golpe_decisivo_armado OR
> ultimo_esforco_ativo`; sem nenhuma das duas técnicas ativas o comportamento é
> byte-idêntico ao anterior (risco real de regressão, testado explicitamente).
> **Sorte** (`sorte`) é reativa — mas **diferente** do Sangue Frio (Fase 2c, que
> arma a re-rolagem ANTES do ataque): o jogador só decide gastar a Sorte DEPOIS de
> ver o erro, e a re-rolagem usa os modificadores **congelados** do ataque
> original (`ultimo_ataque_perdido`: `eff_atk`/`eff_target_ac`/`vantagem`/
> `desvantagem`/`surv_mod`/`cancao_dano`/`gl_dano`), não os recomputados ao vivo —
> distinção provada por teste dedicado (muda `atk_bonus` do jogador entre o erro e
> o reroll e confirma que o reroll ignora a mudança). O dano do reroll e do ataque
> normal agora passam pelo helper extraído `_resolver_dano_ataque_basico`, que
> preserva uma assimetria real pré-existente entre as fórmulas de dano armado/
> desarmado (o rascunho do próprio plano tinha errado esse detalhe; o
> implementador percebeu e corrigiu durante o Passo). **Auto-cura bloqueada
> durante o Último Esforço:** `handle_use_item` (poção, `effect == "heal"`),
> `handle_cura` (recusa alvo = o próprio caster) e `handle_cura_area` (pula o
> próprio caster no loop de aliados). Lacuna real encontrada e fechada em
> revisão: itens de equipamento com efeito `"maxhp"` (ex. `ring_vita`) davam
> top-up instantâneo de HP ao equipar via `_apply_gear_effect` — como equipar é
> uma ação livre e sempre disponível (nem passa por `_is_turn`), isso furava a
> regra "não pode se curar"; o fix suprime só o bump imediato de HP enquanto
> `ultimo_esforco_ativo` (o aumento de `max_hp` em si continua valendo). Também
> corrigido: uma tentativa de poção de cura recusada não gasta mais a ação
> bônus/recursos do jogador à toa. **Recusa de ativação manual de técnicas
> automáticas:** `handle_usar_tecnica` agora rejeita técnicas com
> `item.get("automatica")` antes de rodar o rodapé comum (recarga/custo) —
> corrigindo um bug pré-existente real em que tentar ativar manualmente uma
> técnica automática gastava fome/sede/recarga à toa, sem nenhum efeito. Cliente:
> `isMyTurn` (em `src/gameState.js`) alargado para aceitar `last_stand_pid ===
> myPid` (espelha o `_is_turn` do servidor); o botão do 4º slot desabilita
> técnicas `automatica` (continua visível, só não clicável) e rotula "AUTOMÁTICA" em vez de "GUILDA"; um banner de
> status ("🔥 ÚLTIMO ESFORÇO — N turno(s) restante(s)") em `renderMyPanel`,
> estilizado como a família já existente de banners de status (regeneração/
> saciado/exaustão) — colocado deliberadamente em `renderMyPanel` (agnóstico de
> classe) em vez de perto do indicador de `animados_turn` sugerido no plano
> original, porque esse indicador só aparece em painéis específicos de classe
> (Pedro/Lewis) e não seria visível para as outras classes. Teste:
> `tools/test_tecnicas_espec.py`, seções `[23]`-`[29]` (com subseções extras
> `[27b]`/`[27c]`/`[28b]`/`[28c]`/`[28d]` adicionadas em ciclos de revisão,
> incluindo um teste ponta-a-ponta do ciclo completo do Último Esforço e a prova
> congelado-vs-ao-vivo da Sorte).

> **Técnicas Exclusivas (Fase 3 — Mago/Clérigo):** primeiro uso real do 2º slot
> (`tecnica_exclusiva`), reservado desde a Fase 0 mas nunca ocupado até agora.
> 7 técnicas (`categoria:"tecnica"`, `classe:["mage","cleric"]`, `exclusiva:True`)
> que aprimoram a **próxima magia** lançada — mesmo padrão "arma e age" das
> demais técnicas, mas rodando dentro de `handle_magia` em vez de `handle_attack`.
> **Recarga 5 (180🪙/2🍖2💧, exceto Canalização Arcana 4🍖4💧):** Aprimorar Magia
> (+1 CD do save), Estender Magia (+1 duração se a magia tiver `duracao`, senão +1
> alcance), Canalização Arcana (ignora Silêncio — "não pode ser interrompida" fica
> inerte, sem mecanismo de interrupção de magia no jogo). **Recarga 8 (280🪙/4🍖4💧,
> exceto Geminada 6🍖6💧):** Empoderar Magia (×1,5 dano ofensivo), Magia Geminada
> (2º alvo escolhido **na ativação** — modal combinado aliado+monstro, `alvo:
> "qualquer_vivo"` — reexecuta o mesmo efeito nele se elegível: vivo, no alcance,
> e do tipo certo pro `tipo` da magia), Canalização Perfeita (o alvo testa
> resistência com desvantagem). **Recarga 10 (350🪙/6🍖6💧):** Magia Acelerada (a
> magia não marca `action_done` — libera a ação principal do turno). Todas
> **independentes** da Metamagia do Mago (Fase 1f, toggle permanente e gratuito):
> os bônus de Aprimorar/Estender se somam e os multiplicadores de dano
> (Empoderar/Fortalecer) multiplicam em cadeia se ambos estiverem ativos no mesmo
> lançamento — decisão de brainstorming, para não duplicar a lógica dos toggles
> existentes nem criar uma relação de exclusividade sem necessidade real de
> design. Nota: Empoderar e Geminada nunca coexistem no mesmo personagem (as duas
> são `exclusiva:True`, disputando o mesmo slot único); a combinação realmente
> alcançável em jogo — e a testada — é Fortalecer (Metamagia, sem slot) +
> Geminada, provando que a bonificação ×1,25 se aplica aos DOIS alvos. Duas
> generalizações retrocompatíveis: `classe` no catálogo passa a aceitar lista
> (`_guild_classe_ok`, usado em `guild_items_for_class`/`handle_guild_buy`;
> `guildCatalogFor` no cliente ganha o mesmo `Array.isArray`); `_testar_save`/
> `_save_mostrado` ganham `desvantagem` (rola 2d20, usa o pior — só chega a
> `_executar_raio_congelante` hoje, a única magia de alvo único com save
> implementada; os próximos executores de alvo único devem seguir o mesmo
> padrão). Interação com o Último Esforço (Fase 2e): decidido em brainstorming
> **não bloquear** — o TODO deixado em `game.js` foi resolvido sem nova
> restrição, já que `GS.isMyTurn` já cobre a janela do Último Esforço. Cliente:
> badge "★ Exclusiva Mago/Clérigo" em `_guildItemRow`; nenhuma seção nova na UI
> (as 7 técnicas caem nas faixas de recarga já existentes). Teste:
> `tools/test_guilda_fase3_espec.py`.

> **Peão vira na direção do movimento:** o peão GLB 3D (hoje só `paladin`)
> agora encara o lado do último passo dado, em incrementos de 90°. Servidor:
> `handle_move` grava `p["facing"] = [dx, dy]` a cada passo válido (mesmo
> formato/mecanismo que `m["facing"]` já usava pros monstros orientados —
> crocodilo/lagarto); `enter_dungeon` limpa esse campo ao (re)posicionar os
> jogadores na entrada, então toda masmorra começa com o peão olhando pro
> Sul. Vai automaticamente no `game_state` (serialização crua do dicionário
> do jogador, sem view filtrada). Cliente: `_facingToRotY` (`game.js`)
> converte o vetor num ângulo múltiplo de 90°; `build3DFig` reaproveita o
> parâmetro `mFacing` (já existente pros monstros orientados) pra também
> carregar a direção do peão de herói, já que nenhum herói passa pelo ramo
> de monstro orientado. Sem animação — a rotação encaixa instantaneamente a
> cada passo confirmado. Teste: `tools/test_peao_facing.py`.
