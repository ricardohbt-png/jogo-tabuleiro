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
| `exit_dungeon` | — (saída **individual** pela escada de entrada: exige turno próprio, estar em cima de `stairs_pos` e `saida_permitida` da masmorra; cobra ida+volta de 🍖/💧 da aventura e marca `fora_masmorra`. A masmorra continua para os demais.) |
| `voltar_masmorra` | — (o herói na cidade volta à masmorra assim que a espera zera; senão ele volta sozinho na rodada seguinte) |
| `open_chest` | — |
| `open_door` | `tx`, `ty` — herói abre uma porta adjacente (Chebyshev ≤1). Ação **gratuita** (não gasta movimento/ação). Destranca a(s) sala(s) ligada(s) à porta, revela seu interior e **desperta** os monstros (que passam a perseguir). Salas começam trancadas (exceto a entrada); monstros em sala trancada ficam dormentes e o interior fica oculto pela névoa. **Com mestre**, além de abrir porta, os monstros também acordam por **avistamento** (o herói ganha linha de visão a um deles — `_verificar_avistamento`): o herói que avista acorda a **sala inteira** do monstro (flag `alertado`), narra "⚔️ Combate!" e coloca esses monstros em **Manual** por padrão (o mestre passa a dirigi-los); sem mestre a dormência é só por sala-trancada (byte-idêntica). **Clarividência** (`magia`, `alvoLivre`): alcance = mapa inteiro (mira em qualquer casa, mesmo na névoa — no 3D via `get3DTilePlane`); revela a área, os monstros ali (visibilidade ao vivo por 2 rodadas via `magic_reveal`) e as armadilhas do local, sem abrir a porta nem despertar os monstros. |
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
| `scene_npc` | `scene_id`, `npc_id`, `conversation_id` — conversa com um NPC de uma **cena de conversa** da cidade (substitui `tavern_npc`). Concede renome/fato/item; conversa de uso único entra em `scene_conversations_done` (chave `cidade:cena:npc:conversa`) e some do payload. |
| `guild_buy` | `item_id` — compra uma especialização/técnica na **Guilda dos Heróis** (id em `GUILD_CATALOG`). Só na cidade; valida classe, pré-requisito, posse e ouro; grava o save do personagem. |
| `guild_equip` | `slot` (`tecnica`\|`tecnica_exclusiva`), `item_id` (ou `null` p/ desequipar) — equipa uma técnica possuída no 4º slot. Só na cidade. `tecnica_exclusiva` só para mago/clérigo e só técnicas `exclusiva:true`. |
| `usar_tecnica` | `tecnica_id`, `target_id` opcional — ativa a técnica equipada na masmorra (no turno do herói). Valida equipada/fora de recarga/fome-sede; aplica efeito, debita 🍖/💧 e entra em recarga (`round_num + recarga_rodadas`). |
| `usar_instrumento` | `target_id` opcional — o bardo (Henrique) ativa a habilidade do instrumento equipado na **mão do escudo** (`off_hand`; só se `tipo_item=="instrumento"` e `modo:"ativada"`). Nota Cortante (Harpa) mira 1 monstro; Acorde Trovejante (Tambor) e Ecos Dolorosos (Sino) são auto-centrados; Sinfonia Heroica (Alaúde) é passiva (sem mensagem — reforça a Canção). Economia de ação: 2 mãos = atacar OU tocar; 1 mão = atacar E tocar; máx. 1 instrumento/turno (`instrumento_usado`, resetado no fim do turno). Custo em 🍖/💧 dos stats derivados; sem recarga. Gaita (Improviso): rola 2d6 numa cascata que invoca a habilidade de outro instrumento; passos que exigem alvo/direção (Nota Cortante, Réquiem, Chamado) ficam enfileirados até o cliente responder com `improviso_alvo`. |
| `improviso_alvo` | `target_id` opcional, `dir` opcional — resolve um passo pendente do Improviso (Gaita) que precisa de alvo/direção: mira um monstro (Nota Cortante/Réquiem) ou escolhe direção (Chamado); o servidor processa a fila FIFO (`improviso_pendente`). |
| `claim_role` | `role` (`"master"`\|`"hero"`) — no lobby, um jogador assume/solta o papel de **Mestre** (Modo Mestre Jogador). Mestre: `class_id=None`, não conta no teto de 6 heróis, não escolhe classe. |
| `mestre_set_modo` | `monster_ids[]`, `modo` (`auto`\|`semi`\|`manual`) — o mestre troca o modo de controle de 1+ monstros (base da Seleção em Lote). Só na masmorra. |
| `mestre_set_alvo` | `monster_ids[]`, `target_id` — atribui um alvo (herói) a monstros em modo Semi. |
| `mestre_mover_monstro` | `monster_id`, `dx`, `dy` — Manual: move o monstro da janela 1 passo ortogonal. |
| `mestre_atacar_monstro` | `monster_id`, `target_id` — Manual: o monstro ataca um herói adjacente/no alcance (1×/turno). |
| `mestre_encerrar_monstro` | `monster_id` — Manual: encerra a vez do monstro e libera o laço de iniciativa. |
| `mestre_implantar_reforco` | `monster_type`, `tx`, `ty` — o mestre implanta um monstro da **reserva de reforços** (`master_reinforcements` da masmorra) numa casa livre. Ação livre, a qualquer momento; nasce `alertado`+`manual` e entra na iniciativa da próxima rodada. Só com mestre ativo. |
| `disparar_fala` | `fala_id` — o mestre dispara manualmente uma **fala de NPC** de gatilho `manual` (marcador autorado no editor). Só com mestre ativo; recusa falas não-manuais ou já disparadas. As falas `proximidade`/`sala` disparam sozinhas no `handle_move` (sem/com mestre). |
| `set_lang` | `lang` (`"pt"`\|`"en"`) — idioma desta conexão. Enviada no `onopen` e a cada troca no painel ⚙️. Guardada em `LANG_BY_PID` (módulo, chaveada pelo `pid` do `new_id()`), não na sala — vale antes de entrar em qualquer sala e cobre o Mestre, que sai de `self.players` no `start_game`. O servidor reenvia o estado ao recebê-la, para o log de narração reaparecer traduzido. Valor fora da lista cai em `pt`. |

### Server → Client
`lobby_state`, `game_start`, `city_state`, `shop_result`, `enter_dungeon`,
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`,
`decor_loot`, `trap_result`, `fala`

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
> armadilha. **Veneno Rápido:** o veneno mora na **arma equipada** como uma lista
> de cargas `poison_slots` (viaja com a arma ao trocar/desequipar; consumida por
> `pop(0)` no acerto) — helpers `_weapon_poison_slots`/`_set_weapon_poison_slots`/
> `_aplicar_veneno_na_arma`. Melee tem **1 marcador por padrão**; o teto sobe pelas
> specs via `_capacidade_poison_melee`: `ladino_veneno_2` → 2 cargas do mesmo veneno
> (dura 2 golpes); `ladino_veneno_3` → soma um 2º veneno DIFERENTE mantendo o
> anterior (máx. 2 distintos, FIFO — o antigo é gasto primeiro; reaplicar o mesmo
> recarrega e o move ao fim); combinadas: 2 venenos × 2 cargas = 4. À distância
> (arco/besta) usa `VENENO_CARGAS` projéteis (substitui). O efeito genérico de item
> `coat_poison` fica inalterado. **Esconder nas Sombras:** `ladino_esconder_2/3` dão +2 no
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

> **Instrumentos do Bardo (Fase 1):** equipamento exclusivo do bardo (Henrique)
> que concede uma habilidade de assinatura escalável por qualidade. **Modelo
> 3-eixos:** `INSTRUMENTOS_BASE` (server.py) define 4 bases — `harpa`/`tambor`/`sino`/
> `alaude` — com `maos` (1/2, só economia de ação), `modo` (`ativada`/`passiva`),
> `habilidade_nome`, `desc`, `efeito`, custo-base e stats por qualidade
> (`velho`/`rustico`/`padrao`). Uma instância é criada por `criar_instrumento(base,
> qualidade, origem, encantamento, refinado_bonus, origem_bonus)` (item com
> `tipo_item:"instrumento"`, `name`/`emoji`/`item_slot`, `allowed_classes:["bard"]`) —
> guarda só os atributos; os números efetivos são derivados por `_instrumento_stats`
> (camadas Qualidade→Refinado→Origem→Encantamento; Origem/Encantamento plumbados mas
> não gerados na Fase 1). CD do save = `_instrumento_cd` = `8 + mod(DES)`. "Lendário"
> é só o rótulo do máximo dos 3 eixos. **Slot — mão do escudo:** o instrumento vive
> no `off_hand` (sem slot dedicado; compete com escudo/2ª arma). `_slot_category_for_item`
> mapeia `tipo_item=="instrumento"` → `off_hand`; o equipar reusa o pipeline de gear
> (`_executar_equip_from_bag`, ramo `off_hand`), com bard-only garantido por
> `allowed_classes`. Aquisição bolsa-primeiro (`_route_acquired_item`, sem
> auto-equipar); loja via `instrumento_sku` em `SHOP_MERCHANT`; loot reusa o pipeline
> de item. **Ativação:** `handle_usar_instrumento` (msg `usar_instrumento`) lê o
> `off_hand` (checando `tipo_item`), valida turno + economia de ação (flag
> `instrumento_usado`, resetada no fim do turno: 2 mãos = atacar OU tocar; 1 mão =
> atacar E tocar; máx. 1/turno) + custo 🍖/💧, e despacha por efeito:
> `_instr_nota_cortante` (Harpa, alvo único, save Reflexos meia), `_instr_acorde_trovejante`
> (Tambor, AoE raio, save + empurrão; `push=0` grava `mov_pen_*` — leitura no
> movimento do monstro é lacuna aceita da Fase 1), `_instr_ecos_dolorosos` (Sino, aura
> ativada por `duracao` rodadas; retaliação `_instr_ecos_retaliar` hookada em
> `_execute_one_monster_attack`, só melee via `not atk_def.get("range")`). **Sinfonia
> Heroica** (Alaúde) é passiva: `_cancao_nivel_atributo`/`_sinfonia_bonus` somam +1 aos
> atributos cobertos da Canção conforme a qualidade do Alaúde no `off_hand` (empilha
> com a espec. da Canção da Fase 1e). **Loadout de Henrique:** adaga real na mão
> principal + Alaúde Velho no `off_hand` (passiva → +1 Acerto na Canção);
> `test_bardo_espec` limpa o `off_hand` para isolar a base da Canção. **Cliente:**
> `game.js` `_bardInstrumentoBtn`/`acionarInstrumento` (botão no HUD só p/ instrumento
> ativado; Nota Cortante abre `openTargetModal`) + `aplicarTooltipInstrumento`/
> `_tooltipInstrumentoHTML` (quadro de hover com habilidade, `desc`, custo e stats —
> no botão do HUD e nos slots do paperdoll/bolsa, já que instrumentos não estão em
> `CATALOGO_ITENS`); `src/gameState.js` exporta `usarInstrumento`/`instrumentoBase`/
> `instrumentoEquipadoDe`/`instrumentoStatsClient`/`instrumentoDisponivel` (lêem o
> `off_hand`) e mapeia a categoria em `canPlaceItem`/`_slotCategoryForItem`; a tabela
> `INSTRUMENTOS_BASE` é enviada no `game_start`. **Fases 2–5 pendentes:** 2 Trompa/
> Lira/Flauta, 3 Réquiem Final (Violino), 4 Origens Élfica/Anã + Rúnico + Lendário +
> loot procedural, 5 Improviso/Gaita. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-10-instrumentos-bardo-fase1*`. Teste:
> `tools/test_instrumentos_bardo.py`.

> **Fase 2 (Trompa/Lira/Flauta):** Chamado do General (Trompa, `chamado_general`) —
> cone direcional (`dir:[dx,dy]`, reusa `_cone_tiles`), Vontade → falha: medo
> (`com_medo`/`medo_rodadas`, reusa `_fugir_monstro`) + penalidade de movimento; sucesso:
> penalidade menor. A penalidade usa `_reduzir_mov_monstro`, que reusa o mecanismo da Cola
> (`mov_reduzido_orig`/`mov_reduzido_rodadas`, restaurado em `_processar_*_turno`) e **fecha
> a lacuna** do Tambor Velho da Fase 1 (o ramo `push=0` agora reduz o movimento de verdade).
> Dueto Marcial (Lira, `dueto_marcial`) — buff `dueto_marcial_ate`; o hook
> `_reacoes_instrumento_apos_ataque` (em `handle_attack`, site principal do acerto) faz o
> bardo revidar `_ataque_basico_reativo` quando um aliado adjacente ao bardo acerta um
> inimigo também adjacente; cota `_dueto_marcial_cap` = 1/rodada (2 se Rúnico — plumbado
> p/ Fase 4). Dueto Fantasma (Flauta, `dueto_fantasma`) — buff `dueto_fantasma_ate`/`_fracao`;
> o mesmo hook ecoa uma fração do dano do ataque básico do bardo no mesmo alvo (sem novo
> teste, sem recursão, só quando acerta). Guardas do Ecos (bardo vivo + instrumento ainda
> no `off_hand`) valem p/ Lira e Flauta. Cliente: `usarInstrumento(target, dir)` repassa
> direção; `acionarInstrumento` abre um seletor de 8 direções (`escolherDirecaoInstrumento`)
> p/ o Chamado; Lira/Flauta são auto-centrados. Loja: SKUs em `SHOP_MERCHANT`. Fases 3–5
> pendentes. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 3 (Réquiem Final / Violino):** habilidade sustentada de alvo único (2 mãos,
> `requiem_final`). Ativação `_instr_requiem_final` (alvo com LOS + `alcance` por qualidade;
> grava `requiem_alvo`/`requiem_contador` no bardo e `requiem_por` no monstro); toggle-off
> tratado cedo em `handle_usar_instrumento` (grátis, sempre disponível, mesmo após agir). DoT
> `_processar_requiem_turno` (no turno do alvo, junto de paralisia/veneno): contador sobe até
> o teto por qualidade (velho 3 / rústico 4 / padrão 5), Vontade → falha `contador×dado`
> (d2/d4/d6), sucesso sem dano; matar o alvo encerra. Taunt `_requiem_forca_bardo` (o alvo +
> monstros a ≤3 do bardo são forçados a atacá-lo — integrado em `_get_monster_primary_target`
> e nos 3 booleanos `forcado`). Concentração `_concentracao_requiem` (Vontade CD 8+dano ao
> sofrer dano; falha encerra) hookada no ataque de monstro + ticks de veneno/chamas/armadilha
> (todos via `_dano_em_alvo`); Origem Anã +2 plumbada p/ Fase 4. Manutenção
> `_cobrar_manutencao_requiem` (-2🍖/-2💧 no turno do bardo; sem recursos encerra).
> `_encerrar_requiem` (idempotente) chamado em morte do alvo/bardo, quebra de concentração,
> sem recursos, desequipar, recast e toggle. Cliente: mira como Nota Cortante (ou toggle-off
> se já ativo) + banner de status roxo em `renderMyPanel`. Fase 4 Rúnico: Violino Rúnico dá
> -1 Vontade ao alvo. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4a (Origens Élfica/Anã):** popula o eixo Origem (plumbado desde a Fase 1). Afixos por
> origem — Élfica {`cd`,`alcance`,`duracao`}, Anã {`fome_sede`(−1🍖−1💧),`duracao`,
> `concentracao`(+2 no Réquiem, lido em `_concentracao_requiem`)} — pré-rolados e filtrados por
> `_afixo_aplicavel`/`_afixos_validos_origem` (Élfica sem afixo aplicável, ex.: Alaúde, rebaixa
> p/ Humana). `_aplicar_afixo` ganhou `fome_sede`. `_instrumento_nome` acrescenta o adjetivo de
> origem com concordância de gênero (Élfica/Élfico, Anã/Anão). Roller procedural
> `gerar_instrumento_aleatorio` (ponderado: qualidade 35/30/25/10, origem 70/15/15; base sem
> afixo Élfico aplicável vira Humana). Loot: token autoral `{"tipo":"instrumento_aleatorio"}`
> resolvido por `_resolver_loot_instrumento` em `hidratar_itens_bau` (baús/recompensas) e na
> cadeia de loot de `_monster_dies` (drop) — designers posicionam o token; placement de
> referência no Bugbear das Sombras (3%). Loja: SKUs de origem (`instrumento_sku` com
> `origem`/`origem_bonus`; id `instrumento_{base}_{qualidade}_{origem}`) adicionados **para
> teste**. Cliente: `instrumentoStatsClient` espelha `fome_sede`/`cone`. Fase 4b: Encantamento
> Rúnico (8 efeitos) + Lendário + Rúnico no roller. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4b (Encantamento Rúnico — framework + efeitos simples):** popula o 3º eixo. Camada
> Rúnica em `_instrumento_stats` (`_aplicar_runico` lê o dict `runico` do base quando
> `encantamento=="runico"`): Sino `dano→1d6`, Flauta `duracao +2` (3/4/5), Trompa `medo +1`
> (Amedrontado 2r). Violino Rúnico: `_processar_requiem_turno` passa `extra_mod=-1` no save de
> Vontade do alvo. Lira Rúnica: 2×/rodada (já plumbado em `_dueto_marcial_cap`). Nome
> (`_instrumento_nome`): sufixo "Rúnico/a"; **Lendário** (Refinado + origem≠Humana + Rúnico)
> substitui por "Lendária/o {Origem}" (ex.: "Harpa Lendária Élfica"). Roller sorteia Rúnico
> ~4% (independente de origem/qualidade). `instrumento_sku` ganhou `encantamento` (id
> `..._runico`); SKUs Rúnicos + 1 Lendário na loja **para teste**. Cliente:
> `instrumentoStatsClient` espelha a camada Rúnica. Fase 4c (efeitos Rúnicos bespoke): Harpa
> (Nota Cortante em linha), Tambor (Atordoa/−1 Ataque), Alaúde (+resistências na Canção) —
> uma Rúnica dessas 3 bases já pode ser gerada/comprada, mas seu efeito dedicado só chega na
> 4c. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4c (Encantamento Rúnico — efeitos bespoke):** fecha os 8 efeitos Rúnicos. **Harpa**
> Rúnica: Nota Cortante vira reta direcional (`_nota_cortante_linha`, reusa `_caminho_relampago`;
> cada alvo Reflexos-meia); o cliente usa o seletor de direção do Chamado quando a Harpa é Rúnica.
> **Tambor** Rúnico: no Acorde, falha → `perde_turno` (Atordoado), sucesso → −1 Ataque até o
> próximo turno (`acorde_atk_pen_ate` lido por `_acorde_atk_pen`, somado ao `m_atk` no ataque
> modular `_execute_one_monster_attack` E no loop legado). **Alaúde** Rúnico:
> `_alaude_runico_resist` soma +1 em Fortitude/Vontade aos aliados sob a Canção (via `_testar_save`,
> escopo amplo; "sob a Canção" = chave `buffs_cancao` presente). Fase 5: Improviso/Gaita. Testes:
> `tools/test_instrumentos_bardo.py`.

> **Fase 5 (Improviso/Gaita):** fecha o roadmap dos instrumentos. Base nova `gaita` (🪗, 1 mão,
> ativada, custo 3🍖/3💧) com a habilidade **Improviso**: `_instr_improviso` rola uma cascata 2d6
> (`_improviso_rolar_cascata`) numa **tabela meta** que invoca a habilidade de assinatura de outro
> instrumento **no tier da qualidade da Gaita** — sintetizando um instrumento virtual
> (`_improviso_virt_st`) e reusando os `_instr_*` existentes. Tabela: 2 Desafinado (bardo -1
> ataque/CD, `desafinado_ate`), 3 Falha, 4 Ecos/5 Dueto Marcial/6 Dueto Fantasma/10 Sinfonia
> (forçados a 1 rodada; Sinfonia via `sinfonia_temp_ate`), 8 Acorde (auto), 7 Nota Cortante/9
> Réquiem-1ª-rodada (`_improviso_requiem_tick`)/11 Chamado (enfileirados em `improviso_pendente`,
> mirados pelo cliente via `improviso_alvo`). **12 = Encore:** rola +2×; 2º 12 → **Encore Menor**
> (`_aplicar_encore_menor`: aliados em raio 5 gastam -1🍖/💧 por 1 rodada + Mago/Clérigo 1 magia
> grátis); a Gaita **Rúnica** recursa em cada 12 e um 3º 12 → **Grande Encore**
> (`_aplicar_grande_encore`: 1d4 rodadas — todos sob a Canção agem sem custo, Mago/Clérigo magias
> ilimitadas). O desconto de custo passa por um **helper central novo**
> `_pagar_fome_sede`/`_custo_fome_sede_efetivo`, para o qual os débitos de fome/sede das ações
> ativas (magia, curas, imposição, técnica, armadilha, instrumentos, manutenções Canção/Réquiem)
> foram migrados. Hooks de aura (`_instr_ecos_retaliar`, `_bardo_dueto_marcial`, Dueto Fantasma,
> `_sinfonia_bonus`) passam a aceitar `off base=="gaita"`. Aquisição: SKUs na loja + `gaita` em
> `_ROLLER_BASES` (loot procedural). Cliente: `game.js` `renderImprovisoQuadro` (quadro da
> cascata) + fila de mira; `src/gameState.js` `improvisoAlvo` + evento `improvisoResultado`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-12-instrumentos-bardo-fase5*`. Teste:
> `tools/test_instrumentos_bardo.py`.

> **Modo Mestre Jogador (Fase A — núcleo de controle):** modo opcional em que um
> humano assume o papel de **mestre** (7º participante, sem herói) e controla os
> monstros já colocados. Rastreado por `self.master_pid`/`self.master_name` (NÃO
> fica em `self.players` durante a partida — extraído em `start_game` —, então todo
> laço que itera heróis segue intocado; a conexão fica em `self.connections`, então
> os broadcasts o alcançam). Assento no lobby via `claim_role` (`is_master`; teto 6
> heróis + 1 mestre; `_can_start` ignora o mestre). Cada monstro tem `control_mode`
> (`auto`/`semi`/`manual`, lido via `.get(...,"auto")`); `_mestre_ativo()` (mestre
> conectado) — quando False, todo monstro é tratado como `auto` e a partida é
> **byte-idêntica** à do jogo sem mestre. Despacho no ramo de monstro de
> `_activate_initiative_actor` (`monster_step`): **auto/semi** → `gm_phase(monster)`
> (o Semi força o alvo em `_get_monster_primary_target`, abaixo de
> réquiem/provocação/taunt); **manual** → `_master_manual_window` (janela bloqueante
> via `asyncio.Event` + timer anti-AFK de 60s que resolve via IA, espelhando o
> Último Esforço). Handlers `handle_mestre_set_modo`/`set_alvo` (guarda de fase
> `playing`) e `handle_mestre_mover_monstro`/`atacar_monstro`/`encerrar_monstro`
> (guarda `pid==master_pid` + `monster_id==master_manual_mid`; move reusa
> `_commit_monster_step`, ataque reusa `_execute_one_monster_attack` com alcance
> melee/ranged). `master_pid`/`master_manual_mid` vão nos payloads city/game_state.
> Desconexão do mestre: `_on_master_disconnect` fecha a janela Manual aberta (o
> monstro interrompido age via IA) e os monstros voltam ao auto; reconexão pelo
> `rejoin` (casado por `master_name`). Vitória/derrota do mestre saem de graça dos
> fluxos existentes (TPK / objetivo cumprido); sem métrica de Tensão (Camada D).
> Cliente da Fase A: lobby toggle + HUD do mestre + visão sem névoa. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-13-modo-mestre-jogador-fase-a*`.
> Teste do servidor: `tools/test_modo_mestre.py`.

> **Modo Mestre — Combate ao avistar, controle manual e ficha do monstro:** camada
> seguinte à Fase A (só ativa com `_mestre_ativo()`; sem mestre, tudo byte-idêntico).
> **Despertar por avistamento:** `_verificar_avistamento` (idempotente, chamado após
> `handle_move` e `handle_open_door`) — se um herói vivo (`_ativo`) tem linha de visão
> a um monstro dormente (`_heroi_enxerga_monstro`: raio de visão do HERÓI +
> `_tem_linha_de_visao` + oclusão por objetos altos `_tall_oclui_caminho`), acorda a
> **sala inteira** dele: seta `alertado=True` e `control_mode="manual"` em cada
> monstro do grupo (por `room_id`; sem sala → só ele) e narra "⚔️ Combate!" uma vez
> por sala. **Dormência generalizada:** `_monstro_ativo_em_combate(m)` é o predicado
> único que decide se um monstro age / é controlável / é alvo — COM mestre: só se
> `alertado`; SEM mestre: ativo a menos que a sala esteja trancada (comportamento
> antigo). O despacho de iniciativa (`monster_step` em `_activate_initiative_actor`)
> e o alvo de habilidades pulam o monstro quando o predicado é falso — um monstro
> ainda não avistado fica parado e **não** abre a janela Manual quando sua iniciativa
> chega. **Cliente (puro, sem servidor):** a tela de seleção troca o carrossel de
> peões pela **imagem do mestre** (`assets/portraits/mestre_do_jogo.jpeg`) quando você
> assume o papel (`_csApplyMasterMode` cria `#cs-master-portrait`); e o mestre abre a
> **ficha do monstro** (`renderFichaMonstro` → painel `#ficha-monstro` no canto
> inferior-esquerdo: HP/CA/movimento, atributos, ataques e habilidades) clicando num
> monstro no tabuleiro (ramo de mestre em `handleTileClick` via `_monstroEmCasa`) ou
> numa linha do HUD do mestre; a ficha some ao sair da masmorra e para não-mestres.
> Os dados vêm do dict completo do monstro serializado em `game_state.monsters`
> (`push_state` faz `dict(m,…)`), cobrindo monstros de ficha nova (`attacks`/
> `special_abilities`) e legados (`atk_bonus`/`damage`). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-14-modo-mestre-combate-controle*`.
> Teste do servidor: `tools/test_modo_mestre.py` (75 checks).

> **Modo Mestre — Camada B: Reforços do Mestre:** o autor grava
> `master_reinforcements: [{type,count}]` na masmorra (editor, seção "Reforços do
> Mestre" no painel de nível de masmorra; validado em `validar_dungeon`). Ao entrar
> na dungeon o servidor materializa `self.master_reserve` (`type→count`, via
> `_carregar_master_reserve`; inerte sem mestre). A mensagem `mestre_implantar_reforco`
> (`handle_mestre_implantar_reforco`) cria o monstro via `make_monster` numa casa livre
> (`_tile_livre_para_reforco`, espelha `_free_drop_tile_near`), `alertado`+`manual`;
> ele entra sozinho na iniciativa da próxima rodada (`_rebuild_initiative` itera
> `self.monsters` fresco). `master_reserve` vai no `game_state` enriquecido com
> name/emoji para o HUD. Cliente: `GS.mestreImplantarReforco` + seção "Reforços" no
> `renderMasterHud` com modo de clique-para-implantar (`window._modoImplantarReforco`,
> tratado no ramo de mestre de `handleTileClick`; Esc cancela). Só-mestre; sem mestre,
> byte-idêntico. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-15-modo-mestre-camada-b-reforcos*`.
> Teste: `tools/test_modo_mestre.py`.

> **Modo Mestre — Camada C: ND unificado + Termômetro (editor) + Minimapa (mestre):**
> auxílios de dificuldade — design-time no editor + leitura só-mestre em jogo; **nada
> muda no runtime** (o `expected_party` é só referência). **ND unificado:** todo
> monstro tem `cr`; helper module-level `monster_cr(mdef)` (cr explícito, senão
> fallback `_CR_POR_TIER` por `tier`; sem tier→tier1). Os 6 legados ganharam `cr`
> (goblin .25/skeleton .5/orc .75/dark_mage .5/troll 1.5/dragon 5). **Grupo esperado:**
> campo `expected_party {heroes 1-6, level ≥1}` da masmorra (`_norm_expected_party`,
> `validar_dungeon`, default {4,1}), serializado em `game_state`. **Módulo compartilhado
> `src/difficulty.js`** (`window.Difficulty`): `crFromEntry`/`poder(h,l)=h×l`/
> `faixa(nd,pod)` (Fácil<0.4 / Equilibrada<0.8 / Difícil<1.2 / Mortal, cores) — ponto
> ÚNICO de calibração; incluído em `index.html` e `tools/editor.html`. **Termômetro no
> editor** (`tools/editor.js`, painel `!S.sel`): total + pior sala (por `room_id`) +
> preview 2/4/6. **Minimapa de CR do mestre em jogo** (`game.js`, só `GS.isMaster()`):
> o `#ficha-fab` (🎒 Inventário) vira 🗺️ "Mapa de CR" (`_atualizarFichaFab` no hook de
> `gameState`); `abrirMinimapaCR`/`renderMinimapaCR` desenham as salas de
> `game_state.rooms` coloridas pela faixa, CR por sala (`_crPorSalaMapa` de
> `monsters[].cr`/`room_id`), **CR médio = média das salas** no topo, seletor 2/4/6;
> nunca visível aos jogadores (só UI). Spec/planos em
> `docs/superpowers/{specs,plans}/2026-07-15-modo-mestre-camada-c*`. Teste servidor:
> `tools/test_modo_mestre.py` (seções [19]/[20]).

> **Camada C — ND/XP de armadilha:** cada tipo de `ARMADILHAS` tem `cr`; helpers
> module-level `trap_cr(meta)` (cr explícito, senão derivado da `dificuldade`, senão
> 0.3) e `trap_xp(cr)=round(cr×TRAP_XP_POR_CR)` (=20). Só armadilhas **autoradas**
> (não as `aliada` do Luccas nem os buracos procedurais). **XP:** `_conceder_xp_armadilha`
> concede uma vez (flag `xp_concedido`), dividido entre os heróis vivos (com
> `_check_level_up`), ao **desarmar** (`handle_desarmar_armadilha`, sucesso) OU ao
> **disparar e o herói-alvo sobreviver** (`_disparar_armadilha`, nos 3 pontos de saída:
> alvo-único, teletransporte e dardos). **cr no termômetro/minimapa:** o `cr` das
> autoradas vai em `game_state.armadilhas` (`_serializar_armadilhas`; `aliada`→0) e no
> catálogo do editor (`export_catalog.py` → `editor_catalog.js`); `_crPorSalaMapa`
> (game.js) e `_ndPorSala` (editor.js) somam as armadilhas por sala (casando `pos` à
> sala que a contém). Teste: `tools/test_modo_mestre.py` (seções [21]/[22]).

> **Camada C — Salas obrigatórias:** cada sala aceita `required` (bool) +
> `required_mode` (`visit`|`clear`, default `clear`), marcado no painel da sala do
> editor. Novo tipo de objetivo `salas_obrigatorias` (principal/secundário no dropdown
> `OBJ`): cumprido quando TODAS as salas `required` atendem sua condição — `clear` =
> sem monstros vivos com aquele `room_id` (sala vazia já conta); `visit` = um herói
> entrou (rastreado em `self.salas_visitadas`, populado em `handle_move` reusando o
> `entered = player_room(...)`). Helpers `_sala_obrigatoria_ok`/
> `_salas_obrigatorias_progresso`; o payload de status (`_objetivo_payload`) inclui
> `progresso {feitas,total}` → o HUD (`_objRow` em game.js) mostra "N/M salas".
> `validar_dungeon` rejeita `salas_obrigatorias` sem salas marcadas e `required_mode`
> inválido. Só design-time/objetivo (sem trava de encerramento extra). Teste:
> `tools/test_modo_mestre.py` (seção [23]).

> **Camada C — Validador de design (editor):** só-avisa (nunca bloqueia). Em
> `tools/editor.js`, funções `_grafoSalas` (grafo de salas via BFS nos tiles de chão:
> conectividade da entrada + adjacência parando ao entrar noutra sala + distância) +
> `_ndSalaMap` (ND por sala, reusa a lógica do termômetro) + `_validarDesign`. 5 regras
> viram avisos: **R4** conectividade (sala isolada), **R2** distância spawn→boss (nº de
> salas, mín. `VALID_MIN_SALAS`=3), **R5** descanso antes do boss (vizinha com ND ≤
> `poder×VALID_REST_FATOR` ou role `empty`), **R6** teto do ND **médio** da rota crítica
> (=salas `required`; > `poder×VALID_R6_FATOR`), **R3** picos entre salas obrigatórias
> consecutivas (Δ > `VALID_MAX_PICO`). Boss/entrada por `role`. UI: seção "⚠️ Avisos de
> design" no painel de nível de masmorra (`_avisosDesignHTML` após o termômetro), live.
> Limiares = constantes no topo do módulo (tunáveis). **R1** rota alternativa: detecção de
> gargalo/cut-vertex (`_alcancaSemSala` — remove cada sala intermediária e vê se o boss ainda
> alcança a entrada; por Menger ⇔ ≥2 caminhos vértice-disjuntos). Editor não roda no MCP (arquivos externos viram snapshot) — grafo
> validado por teste node sintético. Spec: `docs/superpowers/specs/2026-07-16-validador-masmorra-design.md`.

> **Modo Mestre — Camada B: Falas de NPC:** marcadores de fala autorados no editor
> que exibem um **balão leve** em jogo (`#fala-popup`, distinto do log `gm_narration`
> e da story de tela cheia). Cada fala = `{id, pos, falante:{nome,emoji}, texto,
> trigger}`; **3 gatilhos** (`trigger.tipo`): `proximidade` (herói a ≤`raio` Chebyshev
> do marcador), `sala` (herói entra na sala do marcador) e `manual` (botão do mestre
> no HUD). Cada uma dispara **uma vez** (flag `disparada`). Servidor: `self.falas`
> carregado na entrada da masmorra (`disparada=False`); `_verificar_falas(p, entered)`
> hookado em `handle_move` (proximidade + sala, reusa o `entered=player_room` do
> rastreio de visita); `_disparar_fala` (idempotente) → broadcast `{type:"fala",
> falante, texto, pos}`; `handle_disparar_fala`+dispatch `disparar_fala` (guarda
> `pid==master_pid` + `_mestre_ativo()` + só `manual` + não-disparada). As
> `proximidade`/`sala` disparam **com ou sem mestre** (CPU no papel); a `manual` só
> com mestre humano (ninguém clica sem ele). `push_state` serializa as `manual`
> não-disparadas em `game_state.falas` (p/ o HUD). `validar_dungeon`: texto
> não-vazio, gatilho válido, `pos` no grid. Editor (`tools/editor.js`): ferramenta
> "fala NPC" + entidade `S.falas` + painel (emoji/nome/texto/gatilho/raio) + marcador
> 💬 no mapa + seleção/mover/apagar + save/load + validação. Cliente: `game.js` balão
> com fila (auto-dismiss 5s, clique avança) + seção "💬 Falas" no `renderMasterHud`
> (dispara as manuais); `src/gameState.js` `dispararFala(id)` + evento `fala`.
> Spec: `docs/superpowers/specs/2026-07-16-falas-npc-design.md`. Teste:
> `tools/test_modo_mestre.py` (seção [24]).

> **Modo Mestre — Controle manual do monstro (SP1):** na janela Manual, o monstro
> se move como um herói — as casas alcançáveis (BFS footprint-aware sobre o
> `movement` real, autoritativo em `_master_reach_bfs`/`_master_monster_reach`,
> enviado em `game_state.master_manual_reach`) aparecem em azul; clicar numa delas
> anda até lá via `mestre_mover_monstro_para`→`handle_mestre_mover_monstro_para`
> (path-walk por `_master_path_to` + `_commit_monster_step`, gastando
> `master_moves_left`). As setas do HUD saíram. Clicar num herói no alcance ataca
> (reusa `mestre_atacar_monstro`). A ficha (`renderFichaMonstro`, agora à direita
> abaixo do HUD) ganhou seção **Ações**: habilidades ativas resolvíveis por
> `_use_monster_ability` (save+dc — as do editor de criaturas) têm botão **Ativar**
> (`mestre_usar_habilidade`→`handle_mestre_usar_habilidade`, mira um herói, consome
> a ação via `_master_acted`, mostra usos/recarga de `ability_uses`/
> `ability_cooldowns`); as demais aparecem como "IA apenas"
> (`_habilidade_ativavel_manual` é o ponto de plugagem futuro). Sem mestre,
> byte-idêntico. SP2 (pendente): inventário de itens do monstro. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-17-modo-mestre-controle-manual-monstro-sp1*`.
> Teste: `tools/test_modo_mestre.py` (seções [25]/[26]).

> **Modo Mestre — Inventário do monstro (SP2):** o mestre usa os itens de bolsa da
> criatura e ativa TODAS as habilidades especiais dela na janela Manual. Apoia-se no
> sistema de equipamento já existente (`equipment_enabled`/`equipped_items` →
> `_aplicar_equipamentos_monstro`, que equipa arma/armadura afetando ataque/CA e
> coleta `m["equipment_consumables"]`, os itens `item_slot=="bag"`). **Itens:**
> `use_item`-do-mestre via `mestre_usar_item`→`handle_mestre_usar_item` (reusa
> `_monster_throw_item` p/ arremessáveis mirando um herói; heal/regeneration/atk_bonus/
> coat_poison/antidote/veil_shadow p/ alvo-próprio; pergaminho `scroll` só se
> `_monster_e_conjurador` via `_executar_magia_grimorio`; food/ração/vinho/cerveja
> recusados — sem efeito em monstros). Economia **espelha o jogador**: consumível de
> bolsa = ação bônus (`_master_bonus_acted`), arremesso/pergaminho = principal
> (`_master_acted`), ambos resetados na abertura da janela. Itens não usados caem no
> loot na morte (comportamento de `equipped_items` já existente). **Habilidades de
> editor (herói/guilda):** o SP1 só tornava ativáveis as save+dc; agora as derivadas
> de herói/guilda (`source in {heroi,guilda}`, ex.: Mira Certeira) também são, via o
> helper `_ativar_editor_ability` (extraído de `_monster_try_editor_ability` e
> compartilhado IA+mestre — contadores `monster_ability_uses`/`monster_ability_cooldowns`);
> `_habilidade_ativavel_manual` e `handle_mestre_usar_habilidade` ganharam o ramo (b)
> self-buff (sem alvo). Cliente: `renderFichaMonstro` ganhou seções **Itens** (botão
> Usar; arremessável/pergaminho abrem mira num herói via `_mestreUsarItemFicha`;
> food/só-conjurador rotulados) e **Equipado** (arma/armadura em leitura);
> `ativavel`/`usosRest`/`cdRest` cobrem as duas famílias de contador (`ability_*` vs
> `monster_ability_*`); `mestreUsarItem` em `gameState.js`. Monstro exemplo:
> **"soldado"** em `monstros_personalizados.json`. Sem mestre, byte-idêntico. Spec/
> plano em `docs/superpowers/{specs,plans}/2026-07-17-modo-mestre-inventario-monstro-sp2*`.
> Teste: `tools/test_modo_mestre.py` (seções [27]/[28]).

> **Agarrão de criatura (crocodilo/cobra) — efeito NO ACERTO mora no pipeline de
> ataque:** `agarrar` (Crocodilo, Fort CD 12) e `constricao` (Cobra, Fort CD 11)
> disparavam só dentro de `_ai_crocodilo_jovem`/`_ai_cobra_constritora`, depois da
> chamada de ataque — então sob **controle Manual** (Mestre, Comando, Dominar Mente),
> que ataca por `handle_mestre_atacar_monstro` → `_execute_one_monster_attack`, a
> mordida acertava e nada acontecia. O teste passou para `_agarrao_no_acerto`, chamado
> de dentro de `_execute_one_monster_attack` ao lado de `onda_envolvente`/`infeccao`
> (que sempre funcionaram justamente por estarem lá); a tabela `_AGARRAO_ON_HIT`
> (id → emoji/narração) é o ponto de extensão para novas espécies que agarrem, e a
> CD/save vêm da própria ficha. O dano automático em quem já está preso saiu das duas
> IAs para `_esmagar_preso` + `_preso_adjacente` (tabela `_ESMAGAR_PRESO`: dado padrão
> + narração), agora também **ativável pelo mestre** — `atq_mandibula`/`esmagar` passam
> na frente do corte de `action_type:"passiva"` em `_habilidade_ativavel_manual` e têm
> ramo próprio em `handle_mestre_usar_habilidade` (sem mira: o alvo é sempre o preso;
> custa a ação principal). **Arrastar** virou `_arrastar_preso`, chamado no fim de
> `_commit_monster_step` (comum a IA e Manual): quem está agarrado acompanha o monstro
> mantendo-se adjacente (`_casa_livre_ao_lado`, que prefere a casa recém-liberada e é
> footprint-aware); sem casa livre o agarrão se rompe, em vez de travar o preso. Isso
> substituiu o bloco da IA que teleportava o herói para CIMA do crocodilo. Cliente:
> `_MP_ESMAGAR_PRESO` em `game.js` espelha a exceção nas 3 pontas (filtro de
> `special_abilities` da ficha, `_mpAtivavel` e `_mestreAtivarHabilidade`).
> **O agarrão também prende MONSTRO, não só herói** — o gancho fica fora do ramo
> `is_player` (animados seguem de fora: usam `vida_atual`). Isso era obrigatório
> para a **mesa livre do editor** ("🧪 Testar como Mestre"), que nasce com
> `players = {}` e onde o único alvo possível é outra criatura — ali nenhum efeito
> no acerto contra herói (veneno, infecção, Onda Envolvente) é observável. Também
> cobre Comando/Dominar Mente, os outros dois casos em que `_alvo_manual_mestre`
> aceita alvo-monstro. O estado da criatura agarrada espelha o do herói:
> `_agarrados_por`/`_preso_adjacente` varrem heróis **e** monstros;
> `_commit_monster_step` recusa o passo de quem está preso (guarda `_captor_ativo`,
> que também zera as casas azuis em `_master_monster_reach`); a tentativa de escape
> entra no prólogo compartilhado `_upkeep_inicio_turno_monstro` reusando
> `_processar_escape_agarrar` (que já era genérico), e a falha zera o movimento sem
> tirar o ataque; `_monster_dies` solta heróis e criaturas. Teste:
> `tools/test_agarrao.py` (39 checks, cobre IA, Manual e mesa livre).

> **`ai_type` de espécie vale em ficha personalizada:** `_run_monster_ai` mandava
> TODA ficha com `_personalizado` para `_run_profile_ai`, o que tornava o campo
> `ai_type` inerte nelas — embora `_validate_custom_monster` valide esse campo
> justamente contra os `ai_type` existentes em `MONSTER_DEFS`. Consequência: salvar
> um nativo por cima dele mesmo no Editor de criaturas (`overwrite_native`) trocava
> a IA da espécie por "agressivo" em silêncio (o crocodilo perdia Mandíbula
> automática, arrasto e perseguição; o grotão, a Cauda Varredora; o lagarto, o Combo
> Devorador). Agora o desvio para o perfil genérico só acontece quando o `ai_type`
> é um dos **`AI_PROFILES`** (agressivo/tatico/cacador/conjurador/emboscador/
> protetor/covarde/irracional/sentinela); um `ai_type` de espécie cai na IA nativa
> daquela criatura. Inerte para as fichas existentes, que gravam `ai_type:
> "agressivo"`. **Armadilhas conhecidas do mesmo import** (dados, não código): o
> editor zera `resistances`, reescreve `weaknesses`, perde `garra_attack`/
> `loot_table`, zera `spawn_min/max`, normaliza `size` e — por ligar
> `apply_attribute_damage` mantendo o modificador embutido em `damage` — **dobra o
> bônus de atributo no dano** (o `damage` do editor é só o dado: "1d8", e o motor
> soma o modificador). Além disso `_apply_custom_monsters` força `m["movement"] = 6`
> em toda ficha personalizada, ignorando o valor do arquivo.

> **Editor de Itens — Fase 1 (Armas):** nova aba "Editor de itens" no editor de
> masmorras (`tools/editor.html` + `tools/editor_items_editor.js`); sub-aba
> **Armas** funcional, as outras 7 (armaduras/escudos/anéis/botas/poções/
> arremessáveis/venenos) visíveis mas desabilitadas (fases futuras). **Catálogo
> global vivo:** salvo em `itens_personalizados.json` + índice regenerado
> `tools/editor_items_custom.js` (`window.EDITOR_CUSTOM_ITEMS`), mesclado no boot
> por `_apply_custom_items` em `WEAPONS`/`SHOP_WEAPONS`/`_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` (server.py). Handlers WS `upload_custom_item` +
> `upload_item_art` (PNG → `assets/itens/<id>.png`). **Efeitos passivos
> funcionais** no combate (lidos de `p["weapon"]` em `handle_attack`): dado/
> categoria/stat/manejo, **alcance editável** em quadrados (`range`/`throw_range`),
> **acuidade** (`finesse` → dano usa o melhor de FOR/DES), bônus fixo
> **independentes** de ataque (`atk_bonus`) e de dano (`damage_bonus`), dano
> elemental adicional (`extra_damages`, lista de `{die,type}` em
> fire/cold/lightning/acid/holy), **munição** para armas à distância (`ammo`:
> flechas/virotes → registrado em `RANGED_AMMO` no merge), **material**
> (`material`: metal/madeira → registrado em `CORROSAO_ARMA_METAL`/`_MADEIRA`,
> define qual Devorador corrói) e **corrosão em dois eixos** — `corrosao_resistente`
> (N níveis sem penalidade) + `corrosao_niveis_penalidade` (M níveis com penalidade,
> escala −1/nível, quebra em N+M+1; lidos por `_corrosao_arma_pen`/
> `_corroer_equipamento`, byte-idêntico p/ armas base quando M=2). `granted_ability`
> (habilidade de Guilda/herói) é só **metadado** nesta fase. Compra/equipar preservam
> esses campos (whitelists de `handle_shop_buy`/`combat_fields`). **Disponibilidade**
> por item (loja/baús/loot de monstro); armas com `baus=true` aparecem no
> seletor de itens de baú/recompensa do editor (`CAT.items` em `tools/editor.js`).
> **Preço sugerido** e serialização/validação puras em
> `tools/editor_items_logic.js` (reusado pelo teste node). **Copiar-como-modelo:**
> itens base nunca são alterados; todo item salvo é sempre novo (id próprio).
> Testes: `tools/test_editor_itens.py` (servidor) e
> `tools/test_editor_items_logic.js` (node). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-20-editor-itens-fase1-armas*`.
> Fases seguintes: as outras 7 abas + habilidades ativáveis funcionais.

> **Editor de Itens — Fase 2a (Armaduras + Escudos):** habilita as sub-abas
> **Armaduras** e **Escudos** (as outras 5 seguem 🔒). `item_type` `"armor"`/`"shield"`,
> mesmo catálogo global vivo (`itens_personalizados.json`), mesclado por
> `_apply_custom_items` (despacho por `item_type`) em `SHOP_ARMORS`/
> `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL`. Campos: `ac_bonus` (CA base) +
> **motor de multi-efeito** `bonuses:[{effect,value}]` (`def_`/`maxhp`/`spd`, via
> `_apply_single_effect` extraído de `_apply_gear_effect`), `armor_category` (só
> armadura), `granted_ability` (metadado), `allowed_classes`, disponibilidade, preço.
> **Corrosão generalizada** para os slots de defesa (armadura/escudo/elmo/botas), com
> o modelo **N/M** das armas: `_corr` ganhou trilhas por slot; `_corroer_equipamento`
> degrada UMA peça na prioridade **armadura→escudo→arma→elmo→botas** (custom corrói por
> `corrosion_materials`, base por id-set; escudos base `escudo_p`/`escudo_g` agora em
> `CORROSAO_ARMADURA_METAL`); a penalidade (`_corrosao_ca_pen` CA; `_corrosao_spd_pen`
> velocidade em `_moves_base`) lê o N/M **cacheado** em `_corr` no momento da corrosão,
> então **persiste após a destruição**. Peças base sem N/M usam N=0/M=2 → byte-idêntico
> (uma correção só na destruição: CA vira base em vez de base−1; `test_devorador` ajustado).
> Elmo/botas ficam **engine-ready** (UI de material/N/M deles na sub-aba futura; base
> não recebe material). Compra/equipar preservam os campos (ramo `ferreiro_armor` +
> whitelists). Cliente: `serializeArmor`/`validateArmorDraft`/`suggestPriceArmor` em
> `editor_items_logic.js`; formulário armadura/escudo em `editor_items_editor.js`;
> `CAT.items` do editor de masmorras inclui armaduras/escudos custom. Testes:
> `tools/test_editor_itens.py` (seções [A1]-[A6]) + `tools/test_editor_items_logic.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-21-editor-itens-fase2a-armaduras-escudos*`.
> Fases seguintes: **B** bônus de atributo (motor), **C** resistências de dano, **D**
> iniciativa; depois anéis/botas/poções/arremessáveis/venenos + habilidades ativáveis.

> **Editor de Itens — Fase B (motor de bônus de atributo):** os efeitos `str_`/`dex`/
> `con_`/`int_` na lista `bonuses` do motor de multi-efeito passam a ser **funcionais**.
> `_apply_single_effect` despacha esses efeitos para `_apply_attribute_delta(p, attr,
> delta)`, que muda o **atributo bruto** (`p[attr]`) e ajusta os derivados
> **armazenados** por Δ do modificador: **acerto** (`atk_bonus`/`base_atk_bonus`) só para
> a classe cujo atributo de ataque bate (`_CLASS_ATK_ATTR`: warrior/mage/cleric/paladin→
> `str_`, rogue/bard/ranger→`dex`); **CA** (`ac`/`ac_base`) e **Reflexos** (`ref_`) para
> DES; **Fortitude** (`fort`) e **PV máx** (`max_hp += Δ(get_bonus_constituicao)×nível`,
> com top-up de HP travado pelo Último Esforço) para CON; **Vontade** (`will`) para INT.
> **Dano, visão** (`_get_raio_visao` lê int/dex/spd) **e iniciativa** (`initiative_value`
> = dex + mod(int)) se atualizam **sozinhos** (leem o bruto). É **simétrico** e
> **independente de ordem** (o Δmod telescópica), então empilhar/remover itens sempre
> volta ao estado inicial. Validação (`_ITEM_BONUS_EFFECTS`) e editor (`BONUS_EFFECTS` +
> dropdown de bônus adicionais em `editor_items_editor.js`) ganharam as 4 opções.
> **Limitação conhecida** (aceita, igual ao veneno): subir de nível com item de +CON
> equipado pode dessincronizar o `max_hp`. Testes: `tools/test_editor_itens.py` [B1]-[B5].
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-21-editor-itens-fase-b-atributos*`.
> Fases seguintes: **C** resistências de dano do herói, **D** iniciativa como campo próprio.

> **Editor de Itens — Fase C (resistências de dano do herói):** um efeito **`resist`**
> na lista `bonuses` do motor de multi-efeito **adiciona/remove uma entrada em
> `p["resistances"]`** ao equipar/desequipar (via `_apply_resistance` no laço de
> `_apply_gear_effect`; roteado para lá em vez do `_apply_single_effect` escalar). A
> entrada carrega um `type` (um de `_RESIST_TYPES`, os 9 tipos de dano) e um modo pela
> convenção do `value`: **value≤0 → metade** (`{type,mode:"half"}`), **value>0 → redução
> fixa** (`{type,reduction:N}`). Como `_apply_damage_types` já é **genérico pelo alvo**
> (lê `target["resistances"]`) e é chamado com o jogador como alvo nos caminhos de dano
> tipado (ataque de monstro/elementais, armadilhas, gás/ácido, fogo…), a redução vale
> **automaticamente** — zero mudança nos ~24 sites. Empilha (uma entrada por item;
> desequipar remove uma igual). Validação (`_ITEM_BONUS_EFFECTS`+`resist`) **preserva o
> `type`** (descarta tipo desconhecido/ausente); cliente: `serializeArmor` preserva o
> `type` (`RESIST_TYPES`) e o editor tem um **dropdown de tipo** que só aparece quando o
> bônus é "Resistência". Testes: `tools/test_editor_itens.py` [C1]-[C3] + node. Fora de
> escopo: imunidade total e vulnerabilidade do herói. Fase seguinte: **D** iniciativa
> como campo próprio.

> **Editor de Itens — Fase D (bônus de iniciativa):** efeito escalar **`initiative`**
> no motor de multi-efeito (`_apply_single_effect`, ramo igual ao de `spd`) →
> `p["initiative_bonus"]`, somado em `initiative_value` (junto de `dex + mod(int)`).
> Vale a partir do próximo `_rebuild_initiative` (por encontro — igual ao efeito de
> DES/INT da Fase B). Valor pode ser **negativo** (armadura pesada −2). Validação
> (`_ITEM_BONUS_EFFECTS`) + cliente (`BONUS_EFFECTS` + opção "Iniciativa" no dropdown de
> bônus adicionais) ganharam o efeito; por ser escalar, cai no caminho comum do
> `serializeArmor` (sem tratamento especial como o `resist`). Fecha o trio **B/C/D** do
> Editor de Itens. Testes: `tools/test_editor_itens.py` [D1] + node. Fases seguintes: as
> outras sub-abas (anéis/botas/poções/arremessáveis/venenos) + habilidades ativáveis.

> **Editor de Itens — bônus de visão:** efeito escalar **`vision`** no motor de multi-efeito
> (`_apply_single_effect`, mesmo ramo de `spd`/`initiative`) → `p["vision_bonus"]`, somado em
> `_get_raio_visao` **antes** do piso `max(1, …)`, ao lado do bônus de atributos e do Guerreiro
> da Luz — vale para heróis (raio de revelação da névoa em quadrados). Aceita negativo. Está no
> allow-list `_ITEM_BONUS_EFFECTS` (server) / `BONUS_EFFECTS` (`editor_items_logic.js`) e no
> dropdown "bônus adicionais" dos 4 forms de gear (armadura/escudo/anel/bota) como "Visão
> (quadrados)". Junto veio um fix do preview de armadura, que rotulava qualquer efeito fora de
> `def_/maxhp/spd` como "Velocidade" — os dois previews agora compartilham `BONUS_LBL`/
> `bonusLabel` em `editor_items_editor.js`. Testes: `tools/test_editor_itens.py` [M1] + node.

> **Editor de Itens — Fase E (Anéis + Botas):** destrava as sub-abas **Anéis** e
> **Botas** (as outras 3 seguem 🔒). Acessórios reusam o **motor de multi-efeito**
> (`bonuses:[{effect,value}]`) — sem CA-base nem `armor_category`; todo efeito vem da
> lista `bonuses`. `item_type` `"ring"`/`"boots"`, validados por
> `_validate_custom_accessory` (dispatch em `_validate_custom_item`), mesclados por
> `_apply_custom_items` no **mercador** (`SHOP_MERCHANT` — nova linha de cleanup dos
> customs, já que nenhum outro bloco o limpava) + `_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` (baús/loot). `_custom_accessory_inventory_dict` gera um dict
> único p/ loja e bolsa/baú (como os anéis nativos). O **equip já era funcional**:
> `_slot_category_for_item` mapeia `item_slot:"ring"`→`ring1`/`ring2` e
> `item_slot:"boots"`→ slot dedicado `boots`; `_apply_gear_effect` aplica a lista
> `bonuses`. **Novo efeito `atk_bonus`** (bônus fixo de acerto) adicionado a
> `_ITEM_BONUS_EFFECTS` (server) e `BONUS_EFFECTS` (cliente) — vale para anéis, botas
> **e** armaduras/escudos (motor compartilhado); `_apply_single_effect` já o tratava.
> **Botas corroem** só via `corrosion_materials` no dict (`_peca_corroivel` corrói
> peça custom por interseção de material; o slot `boots` já está no laço de
> `_corroer_equipamento`) — **não** são registradas nos sets `CORROSAO_ARMADURA_*`
> (evita poluir a detecção de metal dos monstros). **Anéis não corroem.** Cliente:
> `serializeAccessory`/`validateAccessoryDraft`/`suggestPriceAccessory` em
> `editor_items_logic.js` (filtro de bônus extraído p/ `filterBonuses`, DRY com
> `serializeArmor`); `editor_items_editor.js` destrava as sub-abas + form parametrizado
> (`renderAccessoryForm`, corrosão só em botas, rótulo "Loja (Mercador)"), com o
> template de bônus compartilhado `abonusTemplate` e a indireção `previewFn` (para as
> linhas de bônus reusarem o maquinário da armadura sem quebrar no preview de anel).
> Testes: `tools/test_editor_itens.py` [E1]–[E5] + `tools/test_editor_items_logic.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-22-editor-itens-fase-e-aneis-botas*`.
> Fases seguintes: poções/arremessáveis/venenos (subsistemas próprios) + `granted_ability`
> ativável.

> **Editor de Itens — Fase F (Poções):** destrava a sub-aba **Poções** (as outras 2 —
> arremessáveis/venenos — seguem 🔒). Poções são **consumíveis de bolsa**
> (`item_slot:"bag"`) despachados por `effect` em `handle_use_item`; os 3 efeitos do
> escopo (`heal` com multi-dose, `regeneration`, `atk_bonus`) **já estão implementados**
> para o jogador, então esta fase **não toca no motor de combate** — só validar/mesclar/UI.
> `item_type:"potion"` → `_validate_custom_potion` (dispatch em `_validate_custom_item`;
> efeito validado contra o novo set `_ITEM_POTION_EFFECTS`; `max_uses`/`uses_left` só p/
> `heal`; protege ids nativos da união `SHOP_MERCHANT ∪ SHOP_TEMPLE ∪ SHOP_TAVERN`).
> `_custom_potion_inventory_dict` = dict plano único p/ loja e bolsa/baú. Merge por
> `_apply_custom_items` no **mercador** (`SHOP_MERCHANT`) + `_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` — **cleanup herdado** da Fase E (a linha do `SHOP_MERCHANT` + o
> bloco genérico `prev_custom_ids`; sem código de limpeza novo). O `atk_bonus` de poção
> (buff temporário do turno via `blessed`) é distinto do `atk_bonus` de gear da Fase E
> (lista `bonuses`) — sem colisão, pois a poção é consumível por `effect`. Cliente:
> `serializePotion`/`validatePotionDraft`/`suggestPricePotion` + `POTION_EFFECTS` em
> `editor_items_logic.js`; `editor_items_editor.js` destrava a sub-aba com `renderPotionForm`
> (seletor de efeito com rótulos amigáveis; campo Doses só p/ Cura, re-render no toggle como
> o `ie-manejo` das armas; rótulo "Loja (Mercador)"). Testes: `tools/test_editor_itens.py`
> [F1]–[F4] (inclui uso ponta-a-ponta via `handle_use_item` — cura/regen/buff + multi-dose)
> + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-23-editor-itens-fase-f-pocoes*`. Fases seguintes:
> arremessáveis/venenos (subsistemas próprios) + antídoto/cura de status (ramo novo no
> `handle_use_item`) + `granted_ability` ativável.

> **Editor de Itens — Fase G (Arremessáveis):** destrava a sub-aba **Arremessáveis** (só
> **Venenos** segue 🔒). Cobre os **dois modos de mira** do subsistema: `ataque_alvo` (teste de
> ataque por DES vs CA) e `area` (raio + save de Reflexos, metade no sucesso), com dano+elemento
> e o status **em chamas**. `item_type:"throwable"` → `_validate_custom_throwable` (dispatch em
> `_validate_custom_item`; `alvo` em `_ITEM_THROW_TARGETS`, `elemento` em `_ITEM_THROW_ELEMENTS`,
> alcance clamp 1–12, `area_raio` 1–3 e `save {tipo:"reflexos",cd}` só na área, `chamas_dur`/
> `chamas_agua_apaga` quando `em_chamas`; protege ids nativos da união das 3 lojas **∪
> `ARREMESSAVEIS`**). `_custom_throwable_defn` gera a entrada de `ARREMESSAVEIS` no formato
> nativo (marcada `custom:True` para o **cleanup próprio** em `_apply_custom_items`, espelhando
> o `prev_weapon_ids` de `WEAPONS`); `_custom_throwable_inventory_dict` é o dict de bolsa/loja e
> **carrega os metadados de mira** (`alvo`/`alcance`/`area_raio`). Merge no mercador +
> `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL` (limpeza de loja/baús/loot herdada da Fase E).
> **`handle_throw_item`/`_throw_item_alvo`/`_throw_item_area` ficam intocados** — leem tudo do
> `defn`. **Primeira fase do Editor de Itens a tocar o cliente de jogo:** a mira é decidida por
> `CATALOGO_ITENS[item.id]` (catálogo ESTÁTICO em `src/gameState.js`, que não conhece customs),
> então dois pontos ganharam fallback para os campos do próprio item — `resolveTileClick`
> (`src/gameState.js`, ramo `pendingThrow`: `… || th.alvo || 'ataque_alvo'`) e
> `_iniciarMiraArremesso` (`game.js`: `alvoTipo`/`alcance`/`area_raio` + `alvo` no
> `GS.pendingThrow`). Itens **nativos** mantêm a precedência do `CATALOGO_ITENS` (comportamento
> inalterado). Cliente: `serializeThrowable`/`validateThrowableDraft`/`suggestPriceThrowable` +
> `THROW_TARGETS`/`THROW_ELEMENTS` em `editor_items_logic.js`; `renderThrowableForm` com campos
> condicionais (área/dano/chamas re-renderizam no toggle, padrão do `ie-manejo`). **Fora de
> escopo:** efeitos bespoke do catálogo nativo — ácido residual (`residual`/`corrosao_ac`),
> controle (`controle`, cola/rede), zonas (`zona`, fumaça) e água benta. Testes:
> `tools/test_editor_itens.py` [G1]–[G4] (inclui arremesso mirado e de área ponta-a-ponta via
> `handle_throw_item`) + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-26-editor-itens-fase-g-arremessaveis*`.

> **Editor de Itens — Fase H (Venenos):** destrava a sub-aba **Venenos** e **fecha as 8
> sub-abas** do editor. Cobre as **5 operações** de `VENENOS`: `dano` (com os 2 modelos de
> resistência — `save_aplicacao`, testa 1× ao aplicar, ou `save_neutraliza_por_rodada`, testa a
> cada rodada), `reduzir` (atributo via `_VENENO_ATTR_MAP`; CON recalcula PV/Fortitude sozinho),
> `penalidade` (pares `[chave, valor]` em ataque/movimento/dano/ca/percepcao), `petrificar` e
> `cegar` (ambos com `duracao_falha`/`penalidade_falha` do sucesso parcial; `cegar` ainda com
> `penalidade_ataque` e `bloqueia_distancia`). **Um veneno vive em DUAS estruturas** — a entrada
> de `VENENOS` (definição do efeito) e um item de bolsa `effect:"coat_poison"` com `veneno_id`;
> nos nativos o id do item e a chave do veneno são o MESMO string, convenção mantida aqui.
> `item_type:"poison"` → `_validate_custom_poison` (sets `_ITEM_POISON_OPS`/`_ATTRS`/`_PENS`/
> `_SAVES`; CD clamp 1–40; duração/valores aceitam dado `NdX` ou int; protege ids nativos das 3
> lojas **∪ `VENENOS`**). `_custom_poison_defn` gera a entrada de `VENENOS` no formato nativo
> (`nome`/`icone`), marcada `custom:True` para o **cleanup próprio** (mesmo padrão de
> `ARREMESSAVEIS`); `_custom_poison_inventory_dict` é o frasco de bolsa/loja e carrega
> `veneno_id` + **`descricao`/`efeito {save,dificuldade,anula}`**, exatamente o que o tooltip do
> cliente já lê. **`_aplicar_veneno` fica intocado** — é data-driven nas 5 operações. **Cliente
> sem mudanças:** `coat_poison` é genérico (loja filtra por `effect`, tooltip lê do próprio
> item, uso pelo caminho comum de `use_item`). Único retoque fora da região de itens custom: a
> mensagem de `penalidade` em `_aplicar_veneno` era hardcoded ("−1 ataque e −1 movimento") e
> agora é montada dos pares reais — com valores custom ela mentia. Testes:
> `tools/test_editor_itens.py` [H1]–[H5] (inclui untar a arma → acertar → envenenar, e os ramos
> `reduzir`/`cegar`) + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-26-editor-itens-fase-h-venenos*`. **Com esta fase, as 8
> sub-abas do Editor de Itens estão completas**; o que resta são `granted_ability` ativável
> (habilidades concedidas por item) e antídoto/cura de status.

> **Editor de Itens — estoque por cidade (checkbox "Loja"):** com as lojas por cidade
> (`city_shops.json`), o catálogo global (`SHOP_WEAPONS`/`SHOP_ARMORS`/`SHOP_MERCHANT`) diz o que
> **existe** e a allow-list de ids de cada cidade diz o que a loja **vende** (`_city_shop_items`).
> Por isso o checkbox "Loja" sozinho não fazia o item custom aparecer em jogo. Agora o formulário
> tem um **seletor de cidades** (checkboxes na seção Disponibilidade dos 6 forms, desabilitados
> quando "Loja" está desmarcado): ao salvar, o cliente manda `cidades_loja` em `upload_custom_item`
> e `_save_custom_item(raw, city_ids)` chama `_sync_custom_item_city_stock(item, city_ids, old_id)`,
> que **retira o id de todas as lojas antes de inserir** (cobre renomear, trocar de tipo e desmarcar
> "Loja") e grava o `city_shops.json`. A loja de destino vem de `_custom_item_shop_id`
> (arma→`ferreiro_weapon`; armadura/escudo→`ferreiro_armor`; anel/bota/poção/arremessável/veneno→
> `mercador`), espelhado no cliente por `shopIdForItemType` (`editor_items_logic.js`) — há teste de
> sincronia dos dois mapas. `cidades_loja` ausente (cliente antigo) **não** mexe no estoque.
> **Fix de ordem de boot:** `_load_city_shops()` filtra os ids contra o catálogo vivo e roda antes
> de `_apply_custom_items`, então apagava todo id custom do estoque a cada boot (inclusive os
> adicionados pelo Editor de Cidades) — passou a rodar **de novo** logo após o merge dos customs.
> O `city_shops.json` continua sendo a **fonte única** do estoque: o item não guarda a lista de
> cidades; o editor lê o estoque atual para pré-marcar os checkboxes. Testes:
> `tools/test_editor_itens.py` [L1]–[L4] + `tools/test_editor_items_logic.js`.

> **Editor de Itens — Fase I (habilidades concedidas por item):** `granted_ability` deixa de ser
> metadado e vira poder real nos **5 tipos de item equipável** (arma/armadura/escudo/anel/bota).
> O núcleo é um helper module-level **`_habilidades_concedidas(player)`** (varre TODOS os slots
> de `gear` — assim elmo/acessórios futuros funcionam sem mexer aqui) + a extensão de **dois
> portões de uma linha**: `tem_espec` e `tem_tecnica_equipada` passam a aceitar
> `guild_<id>` vindo de um item. Com isso, **técnicas da Guilda** viram ativáveis (botão no HUD
> com efeito, recarga, custo e mira REAIS — reusa `handle_usar_tecnica`, sem tocar nos efeitos) e
> **especializações** viram passivas sempre-ativas. Como `technique_cooldowns` é indexado pelo id,
> ter a técnica no slot da Guilda **e** num item compartilha a mesma recarga (sem uso duplo); a
> restrição de classe da técnica é respeitada (o cliente só renderiza o que está em
> `guildCatalogFor`). **Fix necessário:** `handle_usar_tecnica` fazia a checagem **inline**
> (`tecnica_id not in (eq.get("tecnica"), eq.get("tecnica_exclusiva"))`) em vez de chamar o
> portão — sem passar a usar `tem_tecnica_equipada`, a concessão por item não chegava ao handler.
> **Amostra de 3 habilidades de herói** (`hero_<classe>_<skill>`): Detectar Armadilhas e Esconder
> nas Sombras (Ladino) e Imposição das Mãos (Paladino) — a trava de classe virou
> `class_id != X and <id> not in _habilidades_concedidas(p)`, e as mensagens que citavam
> "Richard"/"Luccas" como donos exclusivos foram generalizadas. `GRANTED_HERO_SKILLS` (mapa
> id→(classe, skill)) + `_granted_hero_skills(p)` injetado no `push_state` mandam a **definição
> real** da skill ao cliente (sem duplicar nomes/custos lá). **Por que só 3:** `handle_skill` é
> **legado e inerte** (retorna cedo; o guerreiro arma as habilidades no cliente e o efeito ocorre
> em `handle_attack` via `buffs`) — cada habilidade de classe é mensagem+handler+trava+painel
> próprios (há 24 checagens `class_id != …`), várias acopladas ao maquinário da classe. As outras
> ~17 ficam para uma **Fase J** com o padrão já validado. Validação: `_granted_ability_valida`
> rejeita ids não suportados nos 3 validadores (antes qualquer string virava metadado morto).
> Editor: o seletor "Habilidade concedida" — que só existia em armas — agora está nos 5 forms,
> com opções **filtradas e agrupadas** (Técnicas / Especializações / Herói). Cliente: técnicas
> concedidas entram no laço do 4º slot com rótulo **"ITEM"**; habilidades de herói ganham um bloco
> que reusa `_rogueSkillBtn`/`_paladinSkillBtn` (ambos agnósticos de classe). Testes:
> `tools/test_editor_itens.py` [I1]–[I6] + `tools/test_guilda.py`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-27-editor-itens-fase-i-habilidades-concedidas*`.

> **Fase J (habilidades de herói restantes concedidas por item):** completa o padrão da Fase I
> com mais **11 habilidades** — **14 no total**. Núcleo: **portão único**
> `_pode_hab_heroi(player, cls_id, aid)` (classe dona OU item concede) + `_tem_alguma_hab_heroi`
> (classe dona OU **qualquer** id de um conjunto — usado pelos upkeeps, que cobrem várias
> sustentadas de uma vez). As 3 travas da Fase I foram **retrofitadas** para o helper, então há um
> só padrão no código. **15 sites** tocados: clérigo (`handle_cura`, `handle_cura_area`,
> `handle_purificacao`, `handle_ressurreicao`), ladino (`handle_criar_armadilha`,
> `handle_veneno_rapido`), paladino (`handle_golpe_sagrado` + `desativar`, `handle_protetor` +
> `desativar`, `handle_acao_livre_richard`, `_processar_manutencao_richard`) e bardo
> (`handle_provocacao` + `_provocador`, que exigia `class_id=="bard"` e mataria os bônus da
> provocação concedida). Em `handle_acao_livre_richard` a trava passou a ser lida **depois** do
> `habilidade_id`, gateando por `hero_paladin_<habilidade_id>` — conceder Regeneração Divina não
> libera Guerreiro da Luz. **Fix de uma lacuna da Fase I:** os dois upkeeps
> (`_processar_inicio_turno_luccas`, `_processar_manutencao_richard`) eram travados por classe, de
> modo que uma habilidade **concedida** nunca pagava manutenção — agora pagam. Sem mudança em
> `_capacidade_poison_melee` (já retorna o base 1 para não-ladinos). Cliente: o bloco de
> habilidades concedidas ganhou os despachos de `_clericSkillBtn`/`_bardSkillBtn` (os quatro
> helpers de botão são agnósticos de classe). Editor: `GRANTED_HERO_IDS` cresceu para 14, com um
> **teste de sincronia** ([J6]) que lê o JS e compara com `GRANTED_HERO_SKILLS` — necessário
> porque `editor_catalog.js` é gerado e não podia ser regenerado. **Fora de escopo (Tier 3):**
> Canção Heroica, Animar Mortos, metamagias, Usar Instrumento (exige instrumento no `off_hand`),
> Mira/Golpe/Fúria do guerreiro (não têm handler — são armadas no cliente e aplicadas em
> `handle_attack` via `buffs`), Ataque Furtivo (passiva) e as 3 magias de MP legadas. Testes:
> `tools/test_editor_itens.py` [J0]–[J6] + as suítes de classe (`test_guilda`,
> `test_paladino_espec`, `test_bardo_espec`, `test_ladino_espec`, `test_clerigo_espec`). Spec/plano
> em `docs/superpowers/{specs,plans}/2026-07-27-fase-j-habilidades-heroi-concedidas*`.

> **Antídotos e curas de status (consumíveis):** três itens que **curam um status e imunizam
> temporariamente** contra ele — **Antídoto** (veneno), **Óleo Dissolvente** (petrificação) e
> **Elixir Depurativo** (doença), todos no mercador com `imunidade_dado:"1d4"`. A lógica de cura
> vivia **inline** dentro de `handle_purificacao`; foi extraída para `_curar_veneno_status` (reverte
> `efeitos_veneno` + cegueira) e `_curar_petrificacao` (`_curar_doenca` já existia), e a Purificação
> do clérigo passou a chamá-las. **Imunidade temporária genérica:**
> `_conceder_imunidade_status(p, status, rodadas)` grava `p["imunidades_status"][status] =
> round_num + N` (rodada absoluta, como os demais buffs) e `_imune_a_status(p, status)` lê;
> `_STATUS_IMUNIZAVEIS = {veneno, petrificacao, doenca}`. São **4 pontos de bloqueio**, levantados
> das fontes reais: `_aplicar_veneno` (veneno), o ramo `petrificar` do veneno **e** a habilidade de
> monstro `effect == "petrificado"` (fonte independente — por isso a imunidade à petrificação não é
> redundante), e o topo de `_aplicar_doenca`. **Três efeitos de consumível** (`cure_poison`/
> `cure_petrification`/`cure_disease`) em `handle_use_item`, como ação bônus: curam o alvo e
> concedem a imunidade rolando `imunidade_dado`. O item **é consumido mesmo sem o status presente**
> (imunidade preventiva é uso legítimo); a narração distingue os dois casos. **Alvo:** `use_item`
> ganhou **`target_id` opcional** (ausente = quem usou, retrocompatível); com alvo, valida jogador
> vivo e **adjacente** (`_no_raio ≤1`) **antes** do bloco de ação bônus, então alvo inválido não
> gasta item nem ação. Cliente: a decisão de mira mora dentro de `useItem` (game.js) — se o efeito
> é de cura e não veio alvo, abre o `openTargetModal` com o próprio herói + aliados adjacentes (com
> só o próprio por perto, o modal é pulado); `src/ui/inventoryModal.js` **não mudou**. **Mudança de
> gameplay:** o `antidote` nativo era `effect:"heal", value:6` — curava 6 HP e **não removia veneno
> nenhum** apesar do nome; agora cura de verdade. Editor: os 3 efeitos entram em
> `_ITEM_POTION_EFFECTS`/`POTION_EFFECTS` e o form da sub-aba Poções troca "Valor/Doses" pelos
> campos do **dado de imunidade**. Testes: `tools/test_editor_itens.py` [K1]–[K6] +
> `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-antidotos-cura-de-status*`.

> **Cidades editáveis (editor):** a aba "🏘️ Cidades" do editor de cidades cria cidades novas,
> edita as existentes (nome/tipo/imagem) e as exclui. As 4 originais continuam declaradas em
> `WORLD_LOCATIONS`/`WORLD_ROUTES` como base imutável (snapshot em `_BUILTIN_WORLD_LOCATIONS`/
> `_BUILTIN_WORLD_ROUTES`); `cidades_personalizadas.json` é a camada por cima
> (`cities`/`overrides`/`deleted`/`routes`), aplicada no boot e no save do editor pela MESMA
> função `_aplicar_estado_cidades` — arquivo e edição ao vivo não podem divergir. Um arquivo
> **ilegível** (≠ ausente) liga `WORLD_CITIES_OK=False` e **bloqueia salvar**, senão o save
> gravaria a perda. Lojas (`CITY_SHOPS`), pontos (`CITY_MAP_POINTS`) e cenas (`CITY_SCENES`)
> são derivados: toda cidade ganha entrada vazia e as excluídas somem
> (`_sincronizar_cidades_derivadas`; no boot cada subsistema se semeia na própria declaração,
> **antes** do seu loader — ordem load-bearing). Cidade nova nasce **vazia** (sem lojas, sem
> pontos, sem cenas — `{}`), e o editor de cenas mostra o upload de fundo e o "+ Adicionar NPC"
> também com a cena vazia. **Mudança de regra:**
> `WORLD_ROUTES` virou tabela de **preços** — par sem entrada = viagem grátis
> (`handle_world_travel`), e `broadcast_city_state`/`_city_shops_editor_payload` emitem uma rota
> para TODOS os pares via `_tabela_rotas()`, então o cliente (`game.js`) **não mudou** e nunca vê
> destino bloqueado. O handler `_save_world_cities_upload` recusa `routes` vazio (zeraria os
> custos originais). `alva_e_luz` (`CITY_INICIAL`) nunca é excluível e é o fallback das salas cuja
> cidade sumiu. x/y: das **originais** vem do arraste no mapa-múndi (`world_map_points.json`, o
> painel nem mostra os campos); das **criadas** viaja no payload. Upload da ilustração:
> `upload_city_art` → `assets/city/`. Teste: `tools/test_cidades_editor.py` (64 checks). Spec/plano
> em `docs/superpowers/{specs,plans}/2026-07-28-editor-cidades-nova-cidade*`.

> **Pontos da ilustração da cidade — `CITY_MAP_POINTS` é a fonte única:** o cliente **não**
> desenha mais nenhum marcador fixo. Os hotspots nativos de `_CTY_BLDGS` e a Caravana embutida
> (`game.js`) só aparecem quando existe um ponto com o **mesmo id** em
> `game_state/city_state.city_map_points`; sem isso eles duplicavam o ponto equivalente criado no
> editor e ficavam numa posição fixa que o editor não listava nem reposicionava. Marcadores
> criados a partir de pontos do editor levam `dataset.cityExtra` e são **removidos** quando o
> ponto some (antes ficavam presos até rebuildar a cidade). Do lado do servidor,
> `_garantir_pontos_implicitos()` materializa como ponto editável tudo que a cidade mostraria
> sozinha — a **Caravana de Viagem** (sempre) e o **prédio de cada loja existente** (`_PONTO_LOJAS`,
> posições em `_PONTO_PADRAO`) — pulando o tipo que já tenha um ponto autoral (mesmo com outro id),
> para não duplicar. Roda em `_sincronizar_cidades_derivadas` (boot + save de cidades) e em
> `_save_city_shops_upload` (abrir uma loja nova numa cidade cria o ponto do prédio na hora).
> `handle_city_map_points` (ajuste "📍 Ajustar pontos" em jogo) passou a fazer `update` de x/y em
> vez de substituir o dict — antes o ajuste apagava `type`/`name` do ponto autoral. Teste:
> `tools/test_cidades_editor.py` seção [12].

> **Ponto da cidade vinculado a uma masmorra:** um ponto da ilustração pode ser uma **entrada
> de masmorra** — `type:"dungeon"` (que já existia na allow-list, sem nunca ser oferecido pelo
> editor) mais o campo novo **`aventura`**, o id de um destino do mapa-múndi (`WORLD_ADVENTURES`).
> **Nenhuma mensagem nova:** o clique confirma via `world_adventure`, o mesmo handler do
> mapa-múndi, então requisito, custo 🍖/💧, etapa encadeada, revisita, história e a trava de
> anfitrião vêm de graça. **Validação assimétrica de propósito:** `_save_city_shops_upload`
> (save do editor) só preserva `aventura` se o destino **existir** — id órfão perde o campo e o
> ponto continua salvo; `_load_city_map_points` (boot) checa **só o formato**, como já faz com
> `scene`, porque um `world_adventures.json` ausente/corrompido zeraria `WORLD_ADVENTURES` e uma
> checagem de existência ali apagaria todos os vínculos da memória — que o próximo save do
> editor gravaria em disco. **Spoiler:** `city_map_points` viaja inteiro no payload, então
> `GameRoom._city_points_payload()` (cópia rasa, usada em `_city_state_payload`) remove os pontos
> de masmorra cujo destino não passa em `_aventura_visivel` — nem o id do destino oculto chega ao
> cliente; destino visível porém bloqueado permanece e o clique explica o que falta. O payload do
> editor (`_city_shops_editor_payload`) **não** filtra e ganhou `adventures:[{id,nome,dungeons}]`
> para o `<select>`. Cliente: `pointAllowed` ganhou o ramo `dungeon` (só desenha com destino em
> `world.adventures`), `_cityHotspotClick` abre `abrirEntradaMasmorra` (overlay
> `#city-dungeon-entry`) em vez do legado `triggerDungeonEntrance` (que segue no arquivo, servindo
> o botão oculto); as regras de custo/etapa/requisito/anfitrião saíram do painel do mapa-múndi
> para `_adventureInfo`/`_adventureGoButton`, compartilhados pelas duas telas. Editor
> (`tools/editor_city.js`): **dois botões** de criar — "+ Adicionar ponto (loja/local)" e
> "+ Adicionar entrada de masmorra" —, `dungeon` **fora** do dropdown de tipo (o tipo só se obtém
> pelo botão dedicado) e formulário próprio com "Destino vinculado" + aviso quando falta destino
> ou o destino não tem masmorra. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-04-ponto-de-cidade-vinculado-a-masmorra*`. Teste:
> `tools/test_cidades_editor.py` seções [13]-[15].

> **Masmorra sequenciada + saída individual pela escada:** duas mudanças no fluxo de
> expedição. **(1) Etapas encadeadas:** cada etapa de uma aventura do mapa-múndi
> (`WORLD_ADVENTURES[...]["dungeons"]`) aceita **string (legado) ou objeto
> `{file, encadear, intro, outro}`** — normalizado por `_etapa_obj`/`_etapa_file`, mesmo
> padrão de `_fase_obj`/`_fase_file` das campanhas. Com `encadear`, `handle_encerrar_missao`
> chama `_emendar_proxima_etapa`, que carrega a próxima masmorra e entra nela **sem** passar
> por `_voltar_para_cidade` — e como é justamente `_voltar_para_cidade` quem recarrega slots,
> zera `technique_cooldowns` e renova refeições, o "**nada se recupera**" sai de graça (HP,
> fome/sede, slots, recargas e status atravessam a emenda). O flag `self._emendando` abre a
> guarda `phase != "city"` de `enter_dungeon` (único caminho que entra numa masmorra vindo de
> `playing`) e suprime os resets "por masmorra nova" (corrosão/vinho/cerveja/chamas). A
> história da emenda vai em `game_state.story` (`self._story_encadeada`, beat
> `outro da etapa N + intro da N+1`) — o cliente **não mudou**: `_captarStory` já lê
> `msg.story` de qualquer mensagem e deduplica por `key`. **(2) Saída individual:**
> `handle_exit_dungeon` deixou de levar o grupo inteiro — agora exige turno próprio, estar em
> cima de `stairs_pos` e a masmorra permitir (`saida_permitida`, campo novo da masmorra,
> default `True`), cobra **ida e volta** (`_custo_viagem_saida` = 2× o `fome`/`sede` da
> aventura; fora de aventura é grátis) e marca
> `p["fora_masmorra"] = {rodadas_restantes, ignorar_primeiro_fecho}`. O portão é o
> **`_ativo(p)`** — que já significa "está no tabuleiro, na iniciativa e é alvo válido" —
> estendido com `and not p.get("fora_masmorra")`: os 27 sites que o consultam tratam o ausente
> como um desconectado, sem serem tocados (o peão vai para `[-1,-1]`, espelhando
> `handle_disconnect_em_jogo`). Na cidade, `_em_cidade(pid)` (= sala na cidade **ou** este
> jogador fora) substitui `phase != "city"` em `handle_shop_buy`/`handle_shop_sell`/
> `handle_guild_buy`/`handle_guild_equip`/`handle_scene_npc`; ficam **de fora** de propósito
> `world_travel`, `world_adventure`, `enter_dungeon` e `city_map_points` (ações de grupo).
> `broadcast` ganhou `skip` e `push_state` **não** manda `game_state` a quem está fora (o
> cliente prefere `gameState` a `cityState` e mostraria o paperdoll da masmorra);
> `push_state_or_city` manda `city_state` individual (`_city_state_payload`/
> `send_city_state_to`). **Espera:** `_tick_retorno_masmorra` decrementa no fecho de rodada
> (`_advance_initiative`), guardando **rodadas restantes** e não uma rodada-alvo absoluta —
> assim sobrevive à emenda, que reinicia `round_num`; `ignorar_primeiro_fecho` faz o fecho da
> rodada em que o herói saiu não contar (senão a espera valeria N ou N-1 conforme o momento da
> saída). Ao zerar ele ganha 1 rodada de tolerância e volta sozinho na seguinte;
> `voltar_masmorra` (`handle_voltar_masmorra`) antecipa. `_reentrar_masmorra` recoloca na
> escada (casa vizinha só se ocupada) com turno cheio e manda `enter_dungeon` só para ele.
> `_checar_masmorra_vazia` (chamado na saída e em `_player_dies`) devolve a sala à cidade
> quando não sobra herói ativo dentro mas há alguém vivo na cidade — não é derrota. O ausente
> **participa** da divisão de XP/ouro (`_conceder_objetivo_reward` já itera por `alive`) e vai
> junto na etapa encadeada. Editor: checkbox "⛓️ emendar na próxima" + encerramento/abertura
> por etapa e **espera de retorno** (fixa em rodadas ou fórmula `NdX`, `_clean_espera`/
> `_rolar_espera`) em `tools/editor_world.js`; checkbox "🚪 saída pela escada" no painel da
> masmorra (`tools/editor.html`/`editor.js`). Cliente: `game_state` traz
> `saida_permitida`/`custo_saida`/`espera_saida` para a confirmação no clique da escada; card
> esmaecido "🏙️ na cidade — volta em N rodada(s)" em `renderPlayers`; banner com contador e
> botão "⛓️ Voltar à masmorra" em `_renderBannerForaMasmorra`; `GS.voltarMasmorra`/
> `foraMasmorraDe`/`estouForaDaMasmorra`/`rodadasParaVoltar`. **Atenção:** `GS.isMyTurn` é uma
> **propriedade booleana**, não função — chamá-la com `()` lança `TypeError`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-masmorra-sequenciada-saida-individual*`. Teste:
> `tools/test_masmorra_sequenciada.py`.

> **História em slides nas aventuras:** o `intro`/`outro` de cada etapa de aventura aceita
> **string** (1 slide de texto) ou **`{slides:[{text,image,fit}], audio}`** — o mesmo formato
> das campanhas, já normalizado por `_story_norm`. Ao salvar, `_clean_story_field` preserva o
> objeto (antes um `str(...)` o destruía) e **restringe a mídia a `assets/story/`**
> (`_story_media_ok`, sem `..`). **Três beats**, todos no campo `story` que o cliente já
> consome sem mudança (`_captarStory` lê `msg.story` de qualquer mensagem e deduplica por
> `key`): **abertura** da etapa em `handle_world_adventure` (`aventura:<id>:<i>`, vale para
> toda etapa iniciada pelo mapa), **transição** em `_emendar_proxima_etapa`
> (`encadeada:<id>:<i>`) e **encerramento** no ramo não-encadeado de `handle_encerrar_missao`
> (`fim:<id>:<i>`), que sai no `city_state`. `_voltar_para_cidade` ganhou o parâmetro
> `story=None`: ela limpa `_story_encadeada` e faz o broadcast na mesma chamada, então gravar
> o beat antes não sobreviveria. O encerramento cobre tanto a última etapa quanto uma
> intermediária sem `encadear` — nos dois casos o grupo volta à cidade. **Editor:** o painel
> de slides (miniatura, upload de imagem/áudio para `assets/story/` via `STORY_UPLOAD`,
> reordenar, pré-visualizar) saiu de `editor_campaign.js` para **`tools/editor_story.js`**
> (`window.EDITOR_STORY`, 8 funções) e agora serve as duas abas; cada etapa do mapa-múndi tem
> "📖 abertura" e "📖 encerramento" (estado em `_introSt`/`_outroSt`, serializado por
> `storyToSaved` no salvar). Em `editor_campaign.js` os apelidos `const` do módulo precisam
> vir **antes** de `const C`, que chama `emptyStory()` na inicialização. **Cliente:**
> `hideWorldMap()` no handler de `enterDungeon` — o mapa-múndi é um overlay sobre
> `screen-city` que só sumia quando a cidade mudava, então voltar da masmorra caía nele em vez
> da ilustração da cidade (`world_location` nunca muda ao entrar numa aventura). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-historia-em-slides-nas-aventuras*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [15]-[17].

> **Destino oculto no mapa-múndi:** cada destino de aventura aceita
> `oculto_ate_liberar` (bool, default `false`). Com o flag ligado, o destino **não entra**
> em `city_state.world.adventures` enquanto o requisito não é cumprido — o filtro é do
> servidor (`_aventura_visivel`, ao lado de `_avaliar_requisito`), então o cliente não muda
> e não há o que espiar no payload. `handle_world_adventure` responde **"Destino de aventura
> inválido."** (a mesma resposta de um id inexistente) quando o destino é oculto e ainda
> bloqueado; destinos visíveis mantêm a mensagem detalhada com o que falta. O payload do
> **editor** (`_world_adventures_editor_payload`) não filtra — o autor precisa enxergar o que
> criou. **Atenção:** requisito vazio **passa** em `_avaliar_requisito`, então o flag sozinho,
> sem nenhum requisito, não esconde nada; por isso o checkbox "🕵️ ocultar no mapa até liberar"
> (bloco de requisitos em `tools/editor_world.js`) fica desabilitado até haver um requisito
> preenchido, e preencher um re-renderiza o painel para habilitá-lo. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-29-destino-oculto-ate-liberar*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [18]-[18c].

> **Fim da rota:** além do `intro`/`outro` de cada etapa, o **destino** tem um campo de
> história próprio, `outro_rota` (mesmo formato: string ou `{slides, audio}`, salvo por
> `_clean_story_field`). No ramo não-encadeado de `handle_encerrar_missao` o beat `fim:` é
> montado com duas partes — `[etapa.outro]` e, **só quando `completed_index + 1 >=
> len(stages)`** (a etapa concluída era a última), também `adventure.outro_rota`. Como
> `_story_beat` concatena na ordem e descarta as partes vazias, sai de graça: etapa
> intermediária mostra só o encerramento dela; a última mostra encerramento da etapa **e**
> fim da rota no mesmo slideshow; destino sem `outro_rota` fica idêntico ao de antes. A
> `key` do beat não muda. Editor: botão "🏁 fim da rota" no painel do destino (abaixo de
> "Renome por etapa concluída"), estado `_outroRotaSt`, mesmo painel de slides do
> `EDITOR_STORY`. Não há mudança de momento: o beat viaja no `city_state` e o slideshow é
> um overlay de tela cheia, então o jogador lê antes de ver a cidade. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-29-fim-da-rota*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [19]/[19b].

> **Prévia fiel do editor (`index.html?preview=1`):** o botão "◈ Visualizar em 3D" do
> editor deixou de ter renderer próprio — `tools/editor_preview_3d.js` era uma
> reimplementação paralela de 183 linhas que divergia do jogo (decoração `special:floor`/
> `wall` virava caixa lisa em vez do PNG, `DECOR_GLB` incompleto, monstro sempre sprite
> chapado em vez de `MONSTER_GLB`, iluminação fixa em vez dos presets `VC.ambientes`).
> Agora ele só hospeda um `<iframe src="../index.html?preview=1">` — o **cliente real** — e
> injeta nele o `game_state` que o **servidor** monta com o **mesmo `load_authored_dungeon`**
> do jogo. Fidelidade estrutural: objeto, monstro ou material novo aparece na prévia sem
> ninguém tocar no editor. Fluxo: `EDITOR.buildJSON()` (sem gravar) → `preview_dungeon` pelo
> WebSocket (`EDITOR_SAVE.previewDungeon`, no `story_upload.js`) → `_preview_dungeon_state`
> (server.py) → `preview_state` → `postMessage` no iframe → `GS.injectPreviewState`.
> **Servidor:** `push_state` foi dividida em `_game_state_payload()` (dict puro) +
> `push_state` (await + broadcast), espelhando `_city_state_payload`/`broadcast_city_state`;
> `_preview_dungeon_state` monta um `GameRoom("PREVIEW")` descartável, marca todo o mapa
> como `explored` e usa `master_pid = PREVIEW_PID` — a **visão sem névoa sai do mecanismo já
> existente do Modo Mestre** (`isMaster()` = `master_pid == myPid`), sem caminho novo de
> render. É **tolerante**: masmorra em construção rende avisos (entrada suprida pela 1ª casa
> de chão, sala default do tabuleiro inteiro, monstro de tipo desconhecido descartado) em vez
> de recusa; só grid/tiles ausentes viram erro. **Cliente:** `GS.isPreview` (regex em
> `location.search`) faz `send()` virar no-op e expõe `injectPreviewState`, que passa pelo
> mesmo `case 'game_state'`; `game.js` pula login/lobby, vai direto a `screen-game` com
> `mode3D = true` e marca `body.preview-mode` (CSS esconde HUD/log/dados). O iframe avisa
> `preview_ready` antes de receber o estado — sem isso o `init3D` não teria onde desenhar.
> Como nada em `tools/*.js` usa mais `THREE`, o `editor.html` **deixou de carregar Three.js**.
> Prévia = só cenário (`players: []`, `current_turn: null`) e só câmera. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-previa-3d-fiel-editor*`. Teste:
> `tools/test_preview_editor.py`.

> **`Connection: close` nas respostas estáticas (bug de rede do servidor):** a lib
> `websockets` FECHA a conexão TCP depois que `process_request` responde, mas o `_http`
> não declarava isso. Em HTTP/1.1 a ausência do cabeçalho significa conexão persistente:
> o navegador guardava o socket no pool e reusava numa requisição **posterior**, que
> morria na rede (XHR com `status 0`, sem resposta). Batia justamente nos pedidos
> **tardios** — os `.glb` carregados sob demanda (`_loadDecorGLB`, `_loadMonsterGLB`) —
> e não no HTML/JS/PNG do carregamento inicial. Provado com socket cru: 1ª resposta
> `200`, 2ª na mesma conexão não existe. Afeta o **jogo**, não só a prévia do editor.
> Defesa em profundidade no cliente: `GLB_TENTATIVAS`/`_glbVaiRetentar` dão **uma
> tentativa extra** só para falha de conexão (`status 0` ou sem status) — 404/403
> desistem de imediato. Sem isso a 1ª falha marcava `'erro'` no cache, que é definitivo:
> o objeto sumia até a página ser recarregada. `_glbMotivo` traduz o `ProgressEvent`
> (antes virava `"[object ProgressEvent]"`). O servidor **não responde a HEAD** (a lib
> só aceita GET), então sondar status por HEAD não é opção. Teste:
> `tools/test_preview_editor.py` seção [4b].

> **Cenas de conversa por local:** a cena da taverna (ilustração em tela cheia com
> frequentadores clicáveis) deixou de ser exclusiva da taverna e virou um recurso de
> **qualquer ponto da cidade**, com **várias cenas por cidade**. `TAVERN_SCENES[cidade]`
> (uma cena) virou **`CITY_SCENES[cidade][cena]`**, persistido em `city_scenes.json`
> (`_load_city_scenes`/`_save_city_scenes`); `_migrar_tavern_scenes` converte o
> `tavern_scenes.json` antigo uma única vez no boot, deixando o arquivo antigo intocado
> como rede de segurança. Cada cena tem `nome` além de `background`/`mask`/`mode`/`slots`;
> teto de 16 cenas/cidade (`MAX_CENAS_POR_CIDADE`), id em `CENA_ID_RE`. `CITY_SCENES` é o
> 4º derivado por cidade, ao lado de `CITY_SHOPS`/`CITY_MAP_POINTS` (mesmo
> `_sincronizar_cidades_derivadas`), então criar/excluir cidade continua correto de graça.
> **O vínculo mora no ponto**, não na cena: `CITY_MAP_POINTS[cidade][ponto]` ganhou `scene`
> (id da cena), `emoji` (livre, sobrepõe o do tipo) e o tipo novo `cena` (local que só
> existe para conversar). A direção importa — um ponto tem **no máximo uma** cena, então
> "duas cenas disputando o mesmo local" não é estado representável. `_garantir_pontos_implicitos`
> religa um ponto à cena de **mesmo id** quando ele não tem vínculo: é isso que faz a
> taverna migrada abrir sozinha, sem caso especial no runtime. **Efeito colateral aceito:**
> esse par não pode ficar sem cena (o editor mostra a opção desabilitada em vez de prometer
> algo que não gruda), e por isso o botão "+ Criar ponto para esta cena" cria o ponto com id
> **próprio** (`ponto_<cena>`), mantendo o desvincular possível nas cenas novas.
> **Conversa de uso único agora SOME do menu:** `_cenas_payload` (ex-`_tavern_payload`)
> **omite do payload** tanto a conversa bloqueada por requisito quanto a `uma_vez` já
> resolvida — os campos `disponivel`/`oculta`/`bloqueio` deixaram de existir. Isso fechou de
> quebra um vazamento real: antes o texto da conversa bloqueada viajava no `city_state` e só
> o cliente não o desenhava. Com a omissão, o filtro do cliente sumiu e o fallback que
> sintetizava `{id:'inicial'}` de `slot.dialog` foi **removido** — ele ressuscitava justamente
> a opção omitida e gerava um botão que respondia "Conversa não encontrada". `conversations: []`
> hoje significa uma coisa só: não sobrou nada que este jogador possa escolher.
> Protocolo: `city_state.tavern` → **`city_state.scenes`**; `tavern_npc` → **`scene_npc`**
> (`handle_scene_npc`); a chave de conversa concluída passou de 3 para 4 partes
> (`cidade:cena:npc:conversa`) e `_migrar_chaves_conversa` converte as antigas dos savegames
> na carga (`scene_conversations_done`, com fallback de leitura para
> `tavern_conversations_done`). **Cliente:** `openShop(pointId, type)` recebe o **id do ponto**
> (antes o tipo do prédio) e resolve cena e loja de forma independente, montando as abas como
> *[💬 nome da cena] + [abas da loja]* — a taverna perdeu a aba hardcoded e virou a primeira
> cliente da regra geral. Dentro de `_renderShopItems` o índice de aba **relativo à loja**
> (`aba = shopTabIdx - (temCena ? 1 : 0)`) é o que vale em toda comparação, senão a lista de
> itens sai trocada. Ponto do tipo `cena` **sem** cena vinculada (ou apontando para cena
> inexistente) **não** é desenhado — senão viraria um marcador que abre um modal sem abas.
> `GS.scenes/cityPoints/sceneIdOfPoint/sceneOfPoint/activeScene/talkSceneNpc` em
> `src/gameState.js`; CSS e funções renomeados de `tavern-*` para `cena-*`. **Editor:** aba
> "💬 Cenas e NPCs" (ex-"Taverna e NPCs") com lista de cenas, "+ Nova cena", nome, "Vinculada
> a" (o dropdown não oferece `dungeon`/`caravana`/`guilda`, que têm tela própria) e excluir —
> cena ausente do envio = exclusão no servidor, que também limpa o vínculo do ponto.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-30-cenas-de-conversa-por-local*`.
> Testes: `tools/test_cenas_conversa.py` (57 checks) + `tools/test_cidades_editor.py`.

> **Idioma (i18n) — motor PT/EN:** o painel ⚙️ (o "menu geral", canto superior direito, em
> todas as telas, também por Esc) ganhou a linha **🌐 Idioma** (`<select>` Português/English)
> que troca o idioma **por jogador** — dois jogadores na mesma sala podem estar em idiomas
> diferentes. Dicionário ÚNICO em `src/lang/strings.js` (`{chave: {pt, en}}`), lido pelo
> cliente via `<script>` (síncrono: sem piscar português antes do inglês e sem depender de
> `fetch`) e pelo servidor via `json.loads` — mesmo padrão de `tools/editor_catalog.js`. Mora
> em `src/` porque a allow-list de estáticos é `("src","assets")`; na raiz daria 404. O
> recorte do objeto é ancorado por regex no **início da linha** `window.LANG_STRINGS =`, e não
> na primeira `{` do arquivo, para que comentários de seção possam conter chaves à vontade.
> **Cliente:** `src/i18n.js` é motor PURO (`I18N.t/setLang/on/lang`, zero DOM); `game.js` tem
> o atalho `t()`, a persistência (`lfh_lang` no localStorage) e `_i18nApply(root)`, que varre
> `[data-i18n]`/`[data-i18n-ph]`/`[data-i18n-title]`. **Cuidado:** só marque com `data-i18n`
> elemento cujo conteúdo INTEIRO seja o texto — `textContent` apaga filhos (por isso o rótulo
> do checkbox de Mestre em `screen-savegames` tem o texto num `<span>`). A propagação do
> idioma ao servidor é por **um ouvinte só** (`I18N.on(code => GS.setLang(code))`), que cobre
> tanto o clique no seletor quanto a restauração do localStorage no boot — fazer isso só no
> clique é um bug real já cometido: a interface ficava em inglês e a narração em português.
> **Servidor:** `T("chave", **params)` marca "texto ainda não traduzido"; `broadcast`/
> `send_to`/`err` resolvem pelo parâmetro `default` do `json.dumps`, no idioma da conexão,
> agrupando por idioma (um `json.dumps` por idioma presente na sala). Isso cobre de graça o
> `gm_log` dentro do `game_state` (que passa a guardar `T` — seguro, o log nunca vai a disco).
> **Regra de migração:** string crua continua string crua e sai em português para todos;
> migrar uma frase é envolvê-la em `T(...)` e acrescentar a chave. Sem `en` → cai no `pt`; sem
> a chave → devolve a própria chave. Idioma por conexão em `LANG_BY_PID` (dict de módulo,
> chaveado pelo `pid` do contador global `new_id()`), não na sala: vale antes de entrar em sala
> e cobre o Mestre, que sai de `self.players` no `start_game`; limpo no `finally` do `handler`.
> Ao receber `set_lang` o servidor reenvia o estado, e esse reenvio cai no caminho normal de
> render do cliente — não há função de re-render nova. **Amostra traduzida nesta etapa:** painel
> ⚙️, `screen-connect`, `screen-savegames`, a narração de abrir porta e o erro de porta
> distante. O resto (~546 `gm_say` + ~470 erros + a interface) é a etapa 2; o bloco `#hint-host`
> (que mistura `<b>`/`<code>`) e o conteúdo autoral (masmorras, campanhas, falas de NPC,
> itens/monstros custom) estão FORA de escopo. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-i18n*`. Testes: `tools/test_idioma.py` (31)
> e `tools/test_idioma_cliente.js` (16, node) — os dois têm varredura estática que aponta chave
> órfã, e é ela que diz, na etapa 2, o que ainda falta.
