# Modo Mestre — Controle manual do monstro (SP1): movimento em casas + ficha de ações

**Data:** 2026-07-17
**Escopo:** Subprojeto 1 de 2. SP2 (inventário de itens do monstro) terá spec próprio.

## Contexto

Hoje, no Modo Mestre Jogador, quando chega a iniciativa de um monstro em modo
**Manual**, abre-se a "janela Manual" (`_master_manual_window`) e o mestre:

- **Move** o monstro 1 casa por vez clicando em setas (`↑↓←→`) no HUD, que
  disparam `mestre_mover_monstro {dx,dy}`. O orçamento é `MASTER_MANUAL_MOVE=5`
  passos fixos (`master_moves_left`), independente da ficha do monstro.
- **Ataca** um herói escolhido num `<select>` (`mestre_atacar_monstro`).
- **Encerra** o monstro (`mestre_encerrar_monstro`).

Limitações que este SP resolve:

1. O movimento não parece com o do jogador (que vê as casas alcançáveis em azul e
   clica no destino).
2. A ficha do monstro (`renderFichaMonstro`, `#ficha-monstro`) fica no canto
   inferior-esquerdo, é só-leitura e não deixa o mestre **usar** as habilidades
   ativas da criatura.

Já existe infraestrutura reusável: `_monster_can_occupy` (caminhabilidade
footprint-aware), `_commit_monster_step` (comita 1 passo), e `_use_monster_ability`
(executor genérico de habilidade ativa com `save`/`dc`/`damage`/`effect` +
`uses_per_combat`/`uses_per_day`/`cooldown_turns`, já debitando usos/recarga).

**Invariante geral:** todo o comportamento novo só vale com **mestre ativo**
(`_mestre_ativo()`) e dentro da **janela Manual** de um monstro. Sem mestre, o jogo
permanece byte-idêntico.

## Decisões de design (do brainstorming)

- **Movimento:** o alcance azul usa o **`movement` real do monstro** (não mais o 5
  fixo).
- **Habilidades:** ativar uma habilidade **consome a ação do turno** do monstro
  (igual atacar — pode mover E ativar, mas não ativar E atacar).
- **Itens:** fora do escopo do SP1. A seção "Itens" da ficha chega no SP2
  (inventário de monstro).

## Parte A — Movimento em casas azuis (autoritativo)

### Servidor

- `_master_manual_window(m)` passa a inicializar
  `m["master_moves_left"] = m.get("movement", self.MASTER_MANUAL_MOVE)` (o `movement`
  real da criatura; o `MASTER_MANUAL_MOVE` vira só fallback).
- Novo método `_master_monster_reach(m)`: BFS ortogonal a partir da âncora do
  monstro, usando `_monster_can_occupy(m, x, y)` como teste de caminhabilidade
  (respeita footprint, paredes, portas fechadas e outras entidades vivas), limitado
  por `master_moves_left`. Retorna lista de âncoras `[x,y]` alcançáveis (exclui a
  casa atual). Custo por passo = 1 (mesmo modelo do BFS do jogador).
- `push_state` inclui `master_manual_reach: [[x,y],…]` **somente quando**
  `master_manual_mid` está setado; recalculado a cada push (encolhe conforme anda).
- Nova mensagem `mestre_mover_monstro_para {monster_id, tx, ty}` →
  `handle_mestre_mover_monstro_para(pid, monster_id, tx, ty)`:
  - Guarda: `pid == master_pid` e `monster_id == master_manual_mid`; monstro vivo.
  - Acha o caminho (BFS acima) da âncora até `(tx,ty)`, limitado por
    `master_moves_left`.
  - **Caminha passo a passo** via `_commit_monster_step`, decrementando
    `master_moves_left` a cada passo; para se um passo for bloqueado ou o orçamento
    zerar (semelhante ao "partial path" do jogador).
  - `push_state` no fim.
- O handler de setas `handle_mestre_mover_monstro` (dx/dy) é **removido** junto com
  a UI de setas (decisão confirmada). A mensagem `mestre_mover_monstro` sai do
  dispatcher.

### Cliente

- Render 2D e 3D: quando `GS.isMaster()` e `state.master_manual_reach` existe, pinta
  essas casas no **mesmo azul de movimento** do jogador (reusa o realce `reachable`
  de `drawFloor3D`/pass de chão).
- `handleTileClick` (ramo mestre), nesta ordem:
  1. `_modoImplantarReforco` ativo → implantar reforço (comportamento atual).
  2. Janela Manual aberta **e** a casa clicada está em `master_manual_reach` →
     `GS.mestreMoverMonstroPara(manualMid, tx, ty)`.
  3. **Bônus de consistência:** janela Manual aberta e a casa tem um herói
     adjacente/no alcance do ataque → `GS.mestreAtacarMonstro(manualMid, heroId)`
     (o `<select>` de alvo continua como fallback).
  4. Senão, se há monstro na casa → abre a ficha dele (`renderFichaMonstro`).
- HUD do mestre (`renderMasterHud`): remove o bloco de setas
  (`.mestre-manual-setas`). Mantém "⚔️ Atacar alvo" (via select, fallback) e
  "Encerrar monstro".
- `src/gameState.js`: novo sender `mestreMoverMonstroPara(mid, tx, ty)` →
  `send({type:'mestre_mover_monstro_para', monster_id, tx, ty})`; remove
  `mestreMoverMonstro` (setas).

## Parte B — Ativação de habilidades pela ficha

### Servidor

- Nova mensagem `mestre_usar_habilidade {monster_id, ability_id, target_id}` →
  `handle_mestre_usar_habilidade(pid, monster_id, ability_id, target_id)`:
  - Guarda: `pid == master_pid`, `monster_id == master_manual_mid`, monstro vivo,
    `not m.get("_master_acted")` (senão erro "já agiu").
  - Localiza a habilidade em `m["special_abilities"]` por `id`; recusa se
    `action_type == "passiva"` ou se não for **ativável no SP1** (ver escopo abaixo).
  - Valida alvo (herói vivo) e alcance: se a habilidade tem `range`, distância
    Chebyshev ≤ range; senão exige adjacência (`_is_adjacent_to_monster`).
  - Chama `_use_monster_ability(m, ability, {"kind":"player","obj":alvo})` — que já
    faz o save (`_testar_save`), dano, efeito e **debita usos/recarga**. Se retornar
    `False` (sem usos / em recarga), envia `error` e **não** seta `_master_acted`.
  - Em sucesso, seta `m["_master_acted"] = True` (consome a ação) e `push_state`.
- **Escopo do SP1 — o que é ativável:** habilidades resolvíveis por
  `_use_monster_ability`, i.e. que carregam `save` **e** `dc` (as geradas pelo
  **editor de criaturas**, opcionalmente com `damage`/`effect`/`uses`/`cooldown`).
  Um predicado `_habilidade_ativavel_manual(ability)` centraliza esse teste. As
  demais (bespoke hardcoded e `action_type:"magia"`) **aparecem na ficha** mas
  ficam marcadas "IA apenas" e são recusadas pelo handler. Um `dispatch table`
  (mapa `id/action_type → executor`) fica preparado para plugar as bespoke depois.

### Cliente (ficha)

- `renderFichaMonstro(m)` ganha:
  - Seção **"Ações"**: itera `special_abilities` com `action_type != "passiva"`.
    Para cada uma, uma linha com: nome, efeito/descrição, **usos restantes**
    (`ability_uses[id]` vs `uses_per_combat`/`uses_per_day`), **recarga restante**
    (`ability_cooldowns[id]`), e botão **Ativar** — desabilitado se sem usos, em
    recarga, `_master_acted`, ou não-ativável (rótulo "IA apenas").
  - Seção **"Passivas"**: as `action_type == "passiva"` (só-leitura, como hoje).
  - Os campos de usos/recarga runtime (`ability_uses`, `ability_cooldowns`) vão no
    dict serializado do monstro em `game_state.monsters` (o `push_state` já faz
    `dict(m, …)`; garantir que essas chaves entram).
- Ativar (botão): se a habilidade exige alvo, entra em modo de mira reusando
  `openTargetModal` (lista de heróis vivos no alcance) → `GS.mestreUsarHabilidade`.
- `src/gameState.js`: novo sender `mestreUsarHabilidade(mid, abilityId, targetId)`.

## Parte C — Ficha reposicionada à direita, abaixo das opções do mestre

- `#ficha-monstro` deixa o canto inferior-esquerdo e passa a ser ancorada **logo
  abaixo do `#hud-mestre`** na coluna direita (empilhada). CSS reposicionado
  (mesmo eixo direito do HUD do mestre). Mantém o ✕ de fechar.
- Abre **automaticamente** quando a janela Manual de um monstro começa (o mestre já
  vê as ações do monstro ativo). O gatilho: quando `master_manual_mid` muda para um
  monstro, chamar `renderFichaMonstro` desse monstro. Clicar noutro monstro (linha
  do HUD ou tabuleiro) abre a ficha dele em leitura.
- Modelo espelha o painel do jogador (`renderMyPanel`): vitais (❤️ HP / 🛡️ CA /
  👣 mov) + atributos + **Ações** + **Passivas** (+ **Itens** no SP2).

## Testes (`tools/test_modo_mestre.py`)

- **Reach BFS:** casas retornadas respeitam footprint (monstro 2×1/orientado),
  paredes/portas e o orçamento `master_moves_left`; exclui a casa atual.
- **`mestre_mover_monstro_para`:** caminha até o destino alcançável; decrementa
  `master_moves_left` pelo nº de passos; para no bloqueio e no orçamento; recusa
  fora da janela Manual / de outro monstro.
- **`mestre_usar_habilidade`:** debita usos e liga recarga; aplica dano/efeito via
  `_use_monster_ability`; seta `_master_acted`; recusa se já agiu, sem usos, em
  recarga, alvo fora de alcance, ou habilidade não-ativável ("IA apenas").
- **Paridade sem-mestre:** com mestre inativo, nada dos itens acima altera o fluxo
  (byte-idêntico).

## Fora de escopo (SP2)

- Inventário de itens do monstro (origem dos itens: editor/loot; uso pelo mestre;
  interação com o drop de morte). Seção "Itens" na ficha.
- Ativação manual das habilidades bespoke hardcoded e das magias de monstro
  (`action_type:"magia"`) — plugáveis no dispatch table deixado pronto no SP1.
