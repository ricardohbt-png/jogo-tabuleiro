# Modo Mestre Jogador — Fase A (Núcleo de Controle)

**Data:** 2026-07-13
**Escopo:** Camada A do "Modo Mestre Jogador" — o mínimo jogável em que um humano
assume o papel de mestre e controla os monstros já colocados no tabuleiro.

## Contexto e decomposição

O documento de design original ("Modo Mestre Jogador — Design Revisado") descreve
um sistema grande, dividido pelo autor em V1/V2. Mesmo o V1 reúne subsistemas
independentes. Decidimos decompor em camadas, cada uma com seu próprio ciclo
spec → plano → implementação:

- **Camada A (esta spec):** assento de mestre no lobby, controle dos monstros já
  no tabuleiro (Auto/Semi/Manual), visão sem névoa e HUD do mestre.
- **Camada B (futura):** conteúdo que o mestre implanta/dispara — elenco de
  reforços, gatilhos de spawn (baú → Mimic), falas de NPC.
- **Camada C (futura):** auxílios de autoria em tempo de design — campo de ND
  unificado, termômetro no editor, ND/XP de armadilha, marcação de salas
  obrigatórias, validador de 6 regras.
- **Camada D (futura, "V2"):** economia — Pontos de Ação, Influência, métrica de
  Tensão Gerada e progressão/rank do mestre.

A Camada A é o núcleo de risco (assento, laço de turno, controle interativo
assíncrono). B e C são puramente aditivos sobre ela.

### Restrição de escopo (do usuário)

O pedido original foi: **não modificar outras partes do jogo; se necessário,
perguntar antes.** Isso não é 100% alcançável para o núcleo, porque um mestre
humano exige tocar em plumbing compartilhado (cap do lobby, laço de turno,
despacho da IA de monstro, serialização de estado). A forma realista da restrição,
aprovada no brainstorm:

> Toda mudança é **condicionada à presença de um mestre** e é **no-op / caminho
> idêntico quando não há mestre**. Uma partida normal de 6 jogadores contra a IA
> deve se comportar de forma **byte-idêntica** ao comportamento atual.

Nenhuma mecânica de herói (ataque, magia, item, habilidade) é alterada.

## Estado atual relevante do código (verificado)

- **Turnos:** o jogo **sempre** roda em modo de iniciativa individual
  (`self.initiative_active = True` é setado incondicionalmente na entrada da
  masmorra, `server.py`). Cada monstro é um ator próprio em `initiative_order`,
  ativado um a um por `_activate_initiative_actor` → (ramo `kind=="monster"`) →
  `gm_phase(only_monster=m)` → `_advance_initiative()`. O laço legado
  `player_order` + `gm_phase()` em lote é um fallback dormente.
- **IA de monstro:** `gm_phase(monster)` resolve status/venenos, escolhe alvo via
  `_alvos_visiveis_para_monstro` / `_get_monster_primary_target` e age via
  `_run_monster_ai(m, targets)`. Ataque individual: `_execute_one_monster_attack`.
- **Lobby:** `self.players` é um dict plano `pid -> {id, name, class_id, ready,
  connected, slot}`. `add_player` rejeita o 7º (`if len(self.players) >= 6`).
  `select_class` marca `class_id` + `ready=True` e usa a trava global
  `CHARACTERS_IN_USE`. `broadcast_lobby` calcula `can_start = len>=1 and all
  class_id`.
- **Precedente de controle manual:** o necromante (Pedro) já controla seus
  animados manualmente — `mover_animado` (1 passo), `atacar_animado` (ataque),
  numa janela pós-turno — reutilizando os resolvers de movimento/ataque. O
  controle Manual do mestre espelha esse padrão.
- **Precedente de espera assíncrona:** o Último Esforço pausa o fluxo num
  `asyncio.Event` até o jogador agir. O turno Manual do mestre usa o mesmo
  mecanismo.
- **Névoa:** `push_state` envia visões por-jogador filtradas por névoa. O mestre
  precisa de um novo ramo de visão completa.
- **Campos de ND já existentes:** monstros novos têm `cr`; todos têm `tier`.
  (O sistema de ND unificado é da Camada C; a Camada A não depende dele.)

## Componentes da Camada A

### 1. Assento de mestre (lobby)

**Dados no jogador:** um novo booleano `is_master` no dict do player. O mestre é
um player com `is_master=True` e `class_id=None`.

**Protocolo (client → server):** nova mensagem `claim_role` com campo
`role: "master" | "hero"`.
- `role:"master"`: só na fase de lobby; se já houver outro mestre na sala,
  rejeita com `error`. Libera a classe anterior do jogador (se tinha) via
  `CHARACTERS_IN_USE`, seta `is_master=True`, `class_id=None`, `ready=True`.
- `role:"hero"`: limpa `is_master=False`, `ready=False` (volta a precisar
  escolher classe). Não escolhe classe por si — o jogador então usa
  `select_class` normalmente.

**Cap e início:**
- `add_player`: o teto passa a ser **≤6 heróis + ≤1 mestre** (7 conexões).
  Implementação: contar heróis (`class_id` ou não-master) separadamente do
  mestre. Um novo entrante só é barrado se já houver 6 não-mestres **e** ele não
  for assumir o papel de mestre livre. (Regra simples: aceitar até 7 conexões;
  `claim_role` faz a validação de "só 1 mestre".)
- `select_class`: recusa se `is_master=True` (o mestre não escolhe classe até
  soltar o papel).
- `can_start` (em `broadcast_lobby`): `≥1 herói` presente **e** todo player
  **não-mestre** tem `class_id`. O mestre é opcional e nunca bloqueia o start.

**Lobby UI (cliente):** um toggle "🎭 Assumir como Mestre" ao lado dos cards de
classe. Ao ativar, oculta a seleção de classe daquele jogador e mostra "Mestre".
Um segundo jogador vê o papel como indisponível (já tomado).

### 2. Modos de controle e hook de turno

**Dados no monstro:** novo campo `control_mode: "auto" | "semi" | "manual"`
(default `"auto"` em todo monstro, inclusive com mestre presente) e
`master_target_id` (opcional, usado no modo Semi).

**Protocolo:** `mestre_set_modo {monster_id | monster_ids[], modo}` — troca o modo
de 1 ou vários monstros de uma vez (a base da "Seleção em Lote"). Permitido a
qualquer momento (sem custo, sem restrição de turno), só se o remetente for o
mestre. `mestre_set_alvo {monster_ids[], target_id}` — atribui `master_target_id`
a 1+ monstros Semi de uma vez.

**Hook (server, `_activate_initiative_actor`, ramo `kind=="monster"`):** decide
pelo `control_mode` do monstro. **Se não houver mestre na sala, todo monstro é
tratado como `auto` independentemente do campo** (garante caminho idêntico ao
atual):
- **auto** → `gm_phase(monster)` + `_advance_initiative()` (comportamento atual).
- **semi** → resolve com a IA normal, mas força o alvo para `master_target_id`.
  Se `master_target_id` estiver vazio, morto, ou fora de visão, age como **auto**
  nesse turno. (A forma exata de "forçar o alvo" será detalhada no plano —
  provável: passar o alvo escolhido para o caminho de `_run_monster_ai` em vez de
  deixar `_get_monster_primary_target` decidir.)
- **manual** → abre a janela bloqueante (ver §3).

**Seleção em Lote:** é apenas o uso de `mestre_set_modo`/`mestre_set_alvo` com
lista de ids. Cada monstro consome seu modo/alvo quando sua própria iniciativa
chega. Não há fase agrupada.

### 3. Janela de controle Manual (fantoche)

Espelha o padrão dos animados do necromante + a espera do Último Esforço.

**Fluxo (server):** quando um monstro `manual` é ativado:
1. `_cancelar_timer_turno`, marca `self.master_manual_mid = monster.id`, prepara
   o orçamento do monstro (`moves_left`, flag de ataque usado), `push_state`
   (o HUD do mestre habilita os controles desse monstro), e aguarda um
   `asyncio.Event` dedicado (`self.master_manual_event`).
2. **Timer de segurança** (ver §5) roda em paralelo: se estourar, resolve o
   monstro via IA `auto` e dispara o Event.
3. O mestre envia:
   - `mestre_mover_monstro {monster_id, dx, dy}` — 1 passo ortogonal, reusa o
     commit de movimento de monstro existente (o mesmo usado pela IA / animados),
     respeitando bloqueios, armadilhas ao pisar, fogueira etc.
   - `mestre_atacar_monstro {monster_id, target_id}` — reusa
     `_execute_one_monster_attack`.
   - `mestre_encerrar_monstro {monster_id}` — encerra a vez desse monstro.
4. Ao encerrar (ou timeout), limpa `master_manual_mid`, dispara o Event, o laço
   retoma e chama `_advance_initiative()`.

Todas as três mensagens validam: remetente é o mestre, `monster_id ==
self.master_manual_mid`, monstro vivo. Fora dessa janela, são recusadas.

### 4. Visão e HUD do mestre

**Serialização (server, `push_state`):** novo ramo para players `is_master`:
mapa completo sem névoa, todos os monstros com HP/posição, sem filtro de
visibilidade. As visões de herói ficam **inalteradas**.

**HUD (cliente):**
- Câmera livre, sem névoa de guerra.
- Roster de monstros: lista com nome, HP e um seletor de modo (auto/semi/manual)
  por monstro; seleção múltipla para troca em lote.
- Atribuição de alvo Semi: clicar num monstro (ou seleção) e depois num herói.
- Botões de ação da janela Manual (mover nas 4 direções + atacar + encerrar),
  habilitados só quando `master_manual_mid` é um monstro do mestre.
- **Sem rótulo de ND** nesta fase (o sistema de ND é da Camada C).

O cliente reconhece o próprio papel de mestre pelo `is_master` no estado e
renderiza a HUD de mestre em vez da HUD de herói.

### 5. Robustez

- **Timer anti-AFK:** a janela Manual (e, por simetria, qualquer espera do
  mestre) reusa um timer de turno (ex.: 60s). No estouro, o monstro age via IA
  `auto` e a rodada avança. O jogo **nunca** trava esperando o mestre. Espelha o
  timer de turno existente, incluindo a guarda de auto-cancelamento
  (`t is not asyncio.current_task()`).
- **Desconexão do mestre:** enquanto o mestre está desconectado, **todos os
  monstros são tratados como `auto`** (o hook do §2 já cai nesse caminho quando
  não há mestre ativo). O mestre pode religar pela sessão/`rejoin` existente,
  estendido para um player class-less (`is_master`), sem escolher classe.
- **Armadilhas, portas e gatilhos de spawn** continuam 100% automáticos nesta
  fase (o mestre controla **apenas** monstros).

### 6. Vitória/derrota do mestre

Sai de graça do que já existe, **sem código novo** e **sem métrica de Tensão**
(que é da Camada D):
- Derrota do mestre = os heróis cumprem o objetivo principal (fluxo de
  `mission_complete`/`encerrar_missao` atual).
- Vitória do mestre = TPK (fluxo de `game_over` atual).

## Fronteiras de módulo

- **Lobby/assento:** isolado em `add_player`, `select_class`, `claim_role` (novo),
  `broadcast_lobby`. Interface: o booleano `is_master` no player.
- **Hook de modo de turno:** um único ponto de decisão em
  `_activate_initiative_actor`. Interface: `control_mode`/`master_target_id` no
  monstro + "existe mestre ativo?".
- **Janela Manual:** `master_manual_mid` + `master_manual_event` + os 3 handlers
  `mestre_*`. Interface: o Event.
- **Visão do mestre:** um ramo em `push_state`. Interface: `is_master`.
- **HUD do mestre (cliente):** módulo de render separado da HUD de herói,
  selecionado por `is_master`. Comunica-se via as novas mensagens `mestre_*` /
  `claim_role`.

## Testes

Seguindo o padrão do projeto (`tools/test_*.py`, testes de servidor headless):
- `test_modo_mestre.py` cobrindo:
  1. **Regressão de não-modificação:** sala sem mestre → hook de turno cai em
     `auto`; comportamento idêntico (monstros agem via `gm_phase`).
  2. Assento: `claim_role` cria mestre; segundo mestre é rejeitado; `can_start`
     ignora o mestre; `select_class` recusado para o mestre.
  3. Cap 6 heróis + 1 mestre.
  4. Modo Semi: alvo forçado é respeitado; alvo inválido cai em `auto`.
  5. Modo Manual: janela abre, `mestre_mover_monstro`/`mestre_atacar_monstro`
     aplicam efeito, `mestre_encerrar_monstro` avança a iniciativa.
  6. Timeout da janela Manual → resolução `auto` + avanço.
  7. Desconexão do mestre → monstros tratados como `auto`.
  8. Seleção em lote: `mestre_set_modo`/`mestre_set_alvo` com lista.

## Fora de escopo (explicitamente)

Elenco de reforços, gatilhos de spawn, falas de NPC (Camada B); ND unificado,
termômetro, ND/XP de armadilha, marcação de salas, validador (Camada C);
PA/Influência/Tensão/rank do mestre (Camada D). Nenhuma alteração em mecânicas
de herói. Nenhum bônus mecânico diferenciando os 3 modos (isso é da Camada D).
