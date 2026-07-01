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
`decor_loot`

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
