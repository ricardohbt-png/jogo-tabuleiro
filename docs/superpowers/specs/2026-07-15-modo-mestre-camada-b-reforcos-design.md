# Modo Mestre Jogador — Camada B: Reforços do Mestre (design)

**Data:** 2026-07-15
**Escopo:** primeira spec da Camada B do Modo Mestre Jogador — o mestre implanta
monstros de reforço no tabuleiro durante a partida, de uma reserva definida pelo
autor da fase no editor.

## Contexto

A Camada A (núcleo de controle: assento de mestre, Auto/Semi/Manual, visão sem
névoa, HUD) e a fase de combate (avistar por LOS, Manual por padrão, ficha do
monstro) já estão implementadas e mergeadas em `feat/instrumentos-bardo-fase5`. A
Camada A deu ao mestre **controle** sobre os monstros já colocados; esta spec dá a
ele **conteúdo para implantar** — a primeira das três frentes da Camada B do design
original (reforços; gatilhos de spawn; falas de NPC). Gatilhos de spawn e falas de
NPC ficam para specs B2/B3 futuras.

### Restrição de escopo (invariante do Modo Mestre)

Como em toda a Camada A: **toda mudança é condicionada à presença de um mestre e é
no-op / caminho idêntico quando não há mestre.** Uma partida sem mestre deve
permanecer **byte-idêntica**. O campo `master_reinforcements` numa masmorra sem
mestre ativo nunca é lido em jogo (só é carregado como estado inerte).

### Decisões do brainstorm (confirmadas pelo usuário)

1. **Escopo:** só reforços nesta spec (gatilhos de spawn e falas de NPC depois).
2. **Origem do elenco:** o **autor** define a reserva no editor (tipos + contagem).
3. **Posição:** o mestre implanta em **qualquer casa livre** (liberdade total — o
   balanço vem do tamanho da reserva, não de restrição de posição).
4. **Ritmo:** **reserva finita, sem freio** — implanta livremente até esgotar.
5. **Primeira ação:** o reforço **espera o slot de iniciativa** dele (não age na
   hora).
6. **Momento:** o mestre pode implantar **a qualquer momento** (ação livre pelo HUD).
7. **Nível:** a reserva é definida **por masmorra** (no arquivo da dungeon).

## Estado atual relevante do código (verificado)

- **Iniciativa reconstruída por rodada:** `_rebuild_initiative()` (server.py) é
  chamado no fim de cada rodada (dentro de `_advance_initiative`, quando
  `initiative_index >= len(initiative_order)`) e itera `self.monsters.values()`
  fresco. **Consequência-chave:** um monstro adicionado a `self.monsters` no meio da
  rodada entra automaticamente na iniciativa da rodada seguinte e age no seu slot —
  exatamente o comportamento "espera o slot de iniciativa" desejado, sem inserção
  manual na fila.
- **Precedente de spawn em jogo:** `_pergaminho_invocar_hostil` já cria um monstro
  em jogo via `make_monster(mdef, sala)` + `self.monsters[m["id"]] = m`, sem tocar
  na iniciativa (confia no rebuild por rodada). Os reforços seguem o mesmo padrão.
- **Casa livre:** `_free_drop_tile_near` já encapsula a noção de casa livre para
  largar itens (chão livre de parede/porta/decoração sólida via `_blocks_tile`; sem
  monstro/jogador vivo; sem baú; sem item no chão). A validação de posição do
  reforço reusa os mesmos predicados, mas para uma casa **escolhida** (tx,ty) em vez
  de buscar a mais próxima.
- **Dormência (fase de combate):** `_monstro_ativo_em_combate(m)` decide se um
  monstro age/é controlável. COM mestre, só se `alertado`. Um reforço implantado
  nasce **`alertado=True`** (o mestre o trouxe deliberadamente) + `control_mode=
  "manual"` (o mestre o dirige), então já é ativo e controlável.
- **HUD do mestre:** `renderMasterHud(state)` (game.js) desenha o painel do mestre a
  partir de `state.monsters` + `master_manual_mid`. É o ponto de extensão para a
  seção "Reforços".
- **Clique em tile:** `handleTileClick(tx, ty)` já tem o ramo do mestre (abre a
  ficha) e o padrão de "modo de mira" (`window._modoMagia`/`_modoThrowItem` que
  interceptam o próximo clique). O modo implantar reusa esse padrão.
- **Serialização:** `push_state` faz `dict(m, …)` por monstro e já envia
  `master_pid`/`master_manual_mid`. A reserva entra como mais um campo do payload.

## Componentes

### 1. Autoria — formato da masmorra + editor

- **Formato:** novo campo opcional no arquivo da dungeon:
  `master_reinforcements: [{ "type": <monster_type>, "count": <int ≥ 1> }, …]`.
  Ausente/vazio = sem reforços (masmorras existentes seguem válidas).
- **Editor:** painel **"Reforços do Mestre"** — lista de linhas (tipo do monstro
  via seletor do catálogo já exportado ao editor + campo de contagem), com
  adicionar/remover. Grava no campo acima ao salvar.
- **Validação** (`validar_dungeon`): cada `type` existe em `MONSTER_DEFS`; `count`
  inteiro ≥ 1. Entradas inválidas são rejeitadas com mensagem clara.

### 2. Runtime — estado + protocolo (servidor)

- **Carga:** ao entrar na masmorra, o servidor materializa a reserva em
  `self.master_reserve` (dict `type → count restante`), a partir de
  `master_reinforcements` da dungeon. Zerado/ausente → dict vazio. Carregado
  sempre; só é **usável** com `_mestre_ativo()`.
- **Nova mensagem `mestre_implantar_reforco { type, tx, ty }`** (client→server),
  handler `handle_mestre_implantar_reforco`. Guardas, em ordem:
  1. `pid == self.master_pid` e `_mestre_ativo()` (senão, silencioso/erro).
  2. fase `playing`.
  3. `self.master_reserve.get(type, 0) > 0`.
  4. `type` válido em `MONSTER_DEFS`.
  5. (tx,ty) dentro do mapa e **casa livre** (reusa os predicados de
     `_free_drop_tile_near`: não bloqueada por `_blocks_tile`; sem monstro/jogador
     vivo; sem baú; sem item no chão).
  - **Efeito:** `m = make_monster(mdef, sala)` onde `sala` é a sala que contém
    (tx,ty) (ou um dict-fallback `{id:None, cx:tx, cy:ty}` se fora de sala, como o
    pergaminho faz); `m["pos"] = [tx, ty]`; `m["alertado"] = True`;
    `m["control_mode"] = "manual"`; `self.monsters[m["id"]] = m`. Decrementa
    `self.master_reserve[type]` (remove a chave se chegar a 0). Narra
    "⚠️ **Reforços!** …". `await self.push_state()`. **Não** insere na iniciativa
    manualmente — o rebuild por rodada o inclui, e ele age no próximo slot.
- **Serialização:** `push_state` inclui `"master_reserve": self.master_reserve` no
  payload (o cliente já ignora o que não usa; só o HUD do mestre lê).

### 3. HUD do mestre (cliente)

- **Seção "Reforços"** em `renderMasterHud`: uma linha por tipo restante em
  `state.master_reserve` (emoji/nome do monstro + contagem). Escondida quando a
  reserva está vazia. Só o mestre vê (o painel já é exclusivo do mestre).
- **Fluxo de implante:** clicar numa linha entra em **modo implantar**
  (`window._modoImplantarReforco = type`, espelhando `_modoMagia`). O próximo
  clique numa casa (via `handleTileClick`, ramo do mestre) envia
  `mestre_implantar_reforco { type, tx, ty }` e sai do modo. Um indicador visual
  (ex.: destaque no cursor/tile ou rótulo "implantando <tipo>… clique numa casa")
  sinaliza o modo ativo; Esc cancela.
- **Getter/sender** em `src/gameState.js`: `GS.mestreImplantarReforco(type, tx, ty)`
  (envia a mensagem) + `GS.masterReserve` (lê `game_state.master_reserve`),
  seguindo o padrão dos outros senders do mestre (`mestreSetModo` etc.).

## Fronteiras de módulo

- **Lógica autoritativa** (reserva, validação de casa, criação do monstro): só no
  `server.py`. O cliente nunca decide se um implante é válido — só envia a intenção.
- **`gameState.js`** ganha o sender + o getter da reserva (zero DOM).
- **`game.js`** só renderiza a seção e gerencia o modo de clique (sem lógica de
  jogo).
- **Editor** só edita/serializa o campo `master_reinforcements`.

## Testes

- **Servidor** (`tools/test_modo_mestre.py`, novas seções):
  - reserva carrega de `master_reinforcements` ao entrar na masmorra.
  - implante válido: cria o monstro na casa, `alertado`+`manual`, decrementa a
    reserva, e o monstro aparece na próxima `_rebuild_initiative`.
  - recusa: casa ocupada/bloqueada; `type` fora da reserva ou esgotado; `pid` que
    não é o mestre; sem mestre ativo; fora da fase `playing`.
  - `validar_dungeon`: aceita `master_reinforcements` válido; rejeita `type`
    inexistente e `count < 1`.
  - **Sem mestre:** nenhum campo novo altera o fluxo (a reserva fica inerte).
- **Cliente:** `node --check game.js` / `src/gameState.js`. Verificação in-app
  (implantar e ver o reforço agir) fica para uma etapa de verificação manual, como
  nas fases anteriores.

## Fora de escopo

- Gatilhos de spawn autorais (baú → Mímico) e falas de NPC — specs B2/B3.
- Qualquer economia/custo de implante (Pontos de Ação, Influência, Tensão) — é a
  Camada D.
- Restrição de posição por LOS/zonas — decisão foi liberdade total de posição.
- Freio de ritmo (teto por rodada / recarga) — decisão foi reserva sem freio.
- Reserva por campanha (compartilhada entre fases) — a reserva é por masmorra.
- Reforço agindo imediatamente ao ser implantado — ele espera o slot de iniciativa.
