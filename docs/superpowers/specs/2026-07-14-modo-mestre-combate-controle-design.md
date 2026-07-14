# Modo Mestre Jogador — Combate ao Avistar, Controle Manual e Ficha do Monstro

**Data:** 2026-07-14
**Escopo:** Refinação da Fase A do Modo Mestre, a partir do playtest do usuário
("não consegui controlar os monstros"). Torna o controle dos monstros pelo mestre
realmente jogável e adiciona duas peças de UI (imagem do mestre na seleção; ficha
do monstro ao clicar).

## Contexto

A Fase A entregou o assento de mestre, os 3 modos de controle (Auto/Semi/Manual),
o HUD e a visão sem névoa. No teste real, o mestre **não conseguiu controlar os
monstros**, por dois motivos combinados:

1. Todo monstro começa em **Auto** (a IA joga por ele); o mestre teria que trocar
   cada um para Manual na mão.
2. A janela de controle Manual só abre **no turno daquele monstro**, e os monstros
   estavam **dormentes** (salas trancadas) — nunca chegaram a ter um turno ativo.

O usuário quer a sensação de RPG de mesa: explora-se por turnos (como hoje), e
**quando um herói avista um monstro, o combate começa** e o mestre passa a
controlar os monstros na sequência de turnos.

### Decisões do brainstorm (todas confirmadas pelo usuário)

- **Início do combate = avistar (linha de visão).** Um monstro dormente acorda
  quando um herói vivo tem LOS para ele.
- **Alcance do alerta = a sala/grupo inteiro.** Avistar um monstro acorda todos os
  monstros da mesma `room_id`.
- **Turnos dos heróis inalterados.** A exploração continua por turnos como hoje; só
  muda QUANDO os monstros acordam.
- **Monstro acorda em Manual** (com mestre presente). O mestre dirige; pode rebaixar
  pra Semi/Auto no HUD por monstro.
- **Escopo só-mestre.** Toda a mecânica nova roda apenas quando há um mestre humano
  ativo (`_mestre_ativo()`). **Sem mestre, a ativação de monstro é byte-idêntica ao
  jogo de hoje** (dormência por sala-trancada). O jogo cooperativo clássico não muda.

## Estado atual relevante do código (verificado)

- **LOS:** `_monstro_enxerga_alvo(m, alvo)` decide se o monstro `m` enxerga um alvo
  (usado por `_alvos_visiveis_para_monstro`). A checagem de avistamento herói→monstro
  reusa essa primitiva (invertida): "algum herói vivo enxerga o monstro".
- **Dormência hoje:** puramente "a sala do monstro está trancada" — `gm_phase` faz
  `room_m = self._room_by_id(m.get("room_id")); if room_m and room_m.get("locked"):
  continue`. Não há flag por-monstro de "acordado".
- **Despertar hoje:** `handle_open_door` destranca a sala (`r["locked"] = False`) e
  os monstros passam a agir. É o único gatilho de combate atual.
- **Turnos:** iniciativa individual sempre ativa; `_rebuild_initiative` inclui TODOS
  os monstros vivos. O despacho por-monstro está em `monster_step` (dentro de
  `_activate_initiative_actor`): `manual` → `_master_manual_window`; `auto`/`semi` →
  `gm_phase(monster)`.
- **Hook de movimento do herói:** `handle_move` comita o passo e já roda efeitos
  pós-passo (fogueira etc.) — ponto natural para checar avistamento.
- **Dados do monstro (para a ficha):** monstros detalhados têm `attacks`
  (`name`/`atk_bonus`/`damage`/`num_attacks`/`categoria`), `special_abilities`
  (`id`/`name`/`action_type`/`descricao`/`dc`/`save`), atributos (`str_`/`dex`/`con_`/
  `int_`), saves (`fort`/`ref_`/`will`), `hp`/`max_hp`/`ac`/`movement`, `immunities`,
  `weaknesses`. Os legados (goblin/orc/...) têm só `hp`/`ac`/`atk_bonus`/`damage`.
  **Tudo isso já é enviado ao cliente** (o `push_state` serializa o dict cru do
  monstro para todos), então a ficha é puro cliente.
- **Cliente Fase A:** `csUpdateLobbyBar`/`_csApplyMasterMode` (esconde painel/confirm
  do herói quando mestre), carrossel 3D de peões da seleção (`csf`), `renderMasterHud`
  (HUD do mestre com linhas de monstro), `computeVisionSet` (visão sem névoa do
  mestre), `handleTileClick` (clique em casa 2D/3D). Imagem já colocada em
  `assets/portraits/mestre_do_jogo.jpeg`.

## Componentes

### 1. Despertar por linha de visão (servidor, só-mestre)

**Dado novo:** flag por-monstro `alertado` (bool, default ausente/False).

**Helper de atividade** `_monstro_ativo_em_combate(m)`:
- Se `self._mestre_ativo()`: retorna `bool(m.get("alertado"))`.
- Senão: retorna o comportamento de hoje — `not (room_m and room_m.get("locked"))`
  (a sala do monstro não está trancada).
Este helper substitui a checagem de dormência inline em `gm_phase` e é consultado no
`monster_step`. **Sem mestre, é exatamente a expressão de hoje** → byte-idêntico.

**Helper de avistamento** `_verificar_avistamento()`:
- Só faz algo se `self._mestre_ativo()`.
- Para cada monstro vivo **não-alertado**: se algum herói vivo (`_ativo`) o enxerga
  (LOS via a primitiva `_monstro_enxerga_alvo` invertida — "o monstro enxerga o
  herói" é simétrico o suficiente; a decisão fina fica no plano), então **acorda a
  sala inteira**: para todo monstro com a mesma `room_id` (e o próprio, se sem sala),
  seta `alertado=True` e `control_mode="manual"` (ver §2). Narra "⚔️ **Combate!** …"
  uma vez por grupo.
- Idempotente (monstros já alertados são ignorados).

**Pontos de chamada:** ao fim de `handle_move` (após comitar o passo do herói) e ao
fim de `handle_open_door` (abrir porta revela a sala → herói passa a enxergar).
Opcionalmente após movimento de monstro que entre no campo de visão de um herói —
tratado como refinamento no plano, não obrigatório para o núcleo.

**Despacho:** em `monster_step`, antes de agir, se `not
self._monstro_ativo_em_combate(monster)`: apenas `await self._advance_initiative()`
e retorna (não abre janela Manual, não roda `gm_phase`). Em `gm_phase`, a checagem
de sala-trancada é trocada por `_monstro_ativo_em_combate`.

### 2. Monstro acorda em Manual (servidor, só-mestre)

Quando `_verificar_avistamento` acorda um grupo **e há mestre**, cada monstro do
grupo recebe `control_mode="manual"` (default). Assim, no turno dele, abre a janela
Manual para o mestre. O mestre pode rebaixar para Semi/Auto pelo HUD
(`handle_mestre_set_modo`) a qualquer momento. (Sobrescrever para "manual" no
despertar é aceitável: um monstro dormente não teria motivo de ter modo pré-setado.)

### 3. Garantir o fluxo funcionando (verificação)

O teste in-app da Fase A não chegou a um turno de monstro (estavam dormentes). O
plano **deve incluir um teste in-app com 2 clientes** (herói + mestre) provando o
ciclo completo: herói avista um monstro → a sala acorda (narração de combate) → os
monstros entram Manual → na vez de um monstro a janela abre para o mestre → mover/
atacar/encerrar avança a iniciativa corretamente. É o critério de "não controlo
nada" resolvido.

### 4. Imagem do mestre na seleção de personagem (cliente)

Na tela de seleção, quando `GS.isMaster()` for verdadeiro, **em vez do carrossel 3D
de peões**, mostrar `assets/portraits/mestre_do_jogo.jpeg` na mesma área, com uma
legenda "📖 Mestre do Jogo". Quando o jogador solta o papel (vira herói de novo), o
carrossel volta. Estende `_csApplyMasterMode` (Fase A já esconde painel/confirm do
herói ali); agora também alterna a área do carrossel ↔ imagem.

### 5. Ficha do monstro ao clicar (cliente)

Novo painel `#ficha-monstro` (canto da tela, estilo as fichas de personagem),
renderizado **só para o mestre** ao clicar num monstro. Conteúdo, a partir do dict
do monstro no `game_state`:
- Cabeçalho: emoji + nome; **HP** atual/máx; **CA**; movimento.
- Atributos (FOR/DES/CON/INT) e saves (Fort/Ref/Von), quando presentes.
- **Ataques:** cada um como "Nome +bônus · dano" (ex.: "Mordida +5 · 1d8+3").
- **Habilidades:** cada `special_abilities` como "Nome — descricao".
- Imunidades/fraquezas, quando houver.
- Monstros legados (sem `attacks`/`special_abilities`) mostram o básico
  (`atk_bonus`/`damage`) sem quebrar.

**Interação:** clicar num monstro no tabuleiro (2D/3D, via o hook de clique já
existente `handleTileClick`, ramo do mestre) abre a ficha daquele monstro; clicar
numa linha do HUD do mestre abre a ficha **e** mantém a seleção para lote. Fechar
por botão ✕ / clicar fora / Esc. Puro cliente — nenhuma mudança no servidor.

## Fronteiras de módulo

- **Despertar/atividade (servidor):** `_monstro_ativo_em_combate`,
  `_verificar_avistamento`, flag `alertado`; chamadas em `handle_move`/
  `handle_open_door`; leitura em `gm_phase`/`monster_step`. Interface: `alertado` +
  `_mestre_ativo()`.
- **Modo Manual no despertar:** dentro de `_verificar_avistamento` (seta
  `control_mode`).
- **Imagem do mestre (cliente):** `_csApplyMasterMode` (game.js) — alterna carrossel
  ↔ `<img>`. Interface: `GS.isMaster()`.
- **Ficha do monstro (cliente):** `renderFichaMonstro(monstro)` + `#ficha-monstro`;
  disparada pelo ramo de mestre de `handleTileClick` e pelas linhas de
  `renderMasterHud`. Lê o dict do monstro do `game_state`.

## Testes

- **Servidor** (`tools/test_modo_mestre.py`, estendido):
  1. **Não-regressão sem mestre:** `_monstro_ativo_em_combate` = a lógica de
     sala-trancada de hoje quando `master_pid is None`.
  2. `_verificar_avistamento` com mestre: herói com LOS a um monstro acorda todos da
     mesma `room_id` (`alertado=True`) e seta `control_mode="manual"`; sem LOS, nada
     acontece; sem mestre, nada acontece.
  3. `monster_step`/`gm_phase`: monstro não-alertado (com mestre) é pulado.
  4. Idempotência: chamar `_verificar_avistamento` 2× não re-narra nem sobrescreve
     indevidamente.
  (LOS pode ser stubada no teste — o foco é o gating e o despertar da sala, não a
  geometria de visão, que já é testada pelo caminho existente.)
- **Cliente:** verificação in-app com 2 clientes (§3) — sem harness de teste JS.

## Fora de escopo

- Camadas B/C/D do Modo Mestre (reforços, ND/validador, economia).
- Detecção por som/proximidade (só linha de visão).
- Mudar os turnos dos heróis (exploração continua por turnos).
- Furtividade individual (avistar acorda a sala inteira, não monstro-a-monstro).
- Vazamento de dados: os stats do monstro já são enviados a todos os clientes hoje;
  a ficha só adiciona a UI de inspeção para o mestre (não é uma mudança de servidor).
