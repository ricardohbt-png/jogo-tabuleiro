# Bomba de Fumaça — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir consumir uma Bomba de Fumaça fora do turno para interromper um ataque inimigo contra si ou um aliado, animar seu lançamento e resolver aquele ataque com desvantagem.

**Architecture:** Janela autoritativa e efêmera na sala, com `asyncio.Event`, prazo e primeira aceitação válida. O ataque aguarda a decisão e o lançamento, conservando seu atacante/alvo e a ordem de iniciativa. O cliente mantém a oferta em `gameState.js`; `game.js` apresenta a decisão e reutiliza projéteis e fumaça existentes.

**Tech Stack:** Python/asyncio/WebSocket; JavaScript sem framework; Canvas 2D e Three.js 3D; scripts de regressão existentes em `tools/`.

**Spec:** `docs/superpowers/specs/2026-10-19-bomba-fumaca-reacao-design.md` (aprovada pelo usuário em 2026-10-19).

## Global Constraints

- A janela dura até 12 segundos. Recusa de todos encerra imediatamente; expiração equivale a recusar.
- O único custo é uma bomba consumida; não gastar ação principal, bônus, movimento, fome/sede ou carga adicional de reação.
- Nuvem normal de duas rodadas, raio 1 e alcance base 4, com modificadores de arremesso e trajetória existentes.
- Todas as conexões aptas recebem a oferta simultaneamente; a primeira confirmação válida consome uma bomba e fecha as demais ofertas.
- Somente ataques direcionados a heróis com rolagem de acerto d20; efeitos de resistência, dano automático e explosivos de área não abrem oferta.
- O ataque interrompido usa 2d20 e o menor resultado, inclusive contra atacante com visão no escuro; efeitos normais da fumaça regem ataques posteriores.
- Cobrir IA modular, ataque legado, arremessável direcionado, controle do Mestre e heróis de Solo com grupo.
- Estado/comunicação em `src/gameState.js` primeiro; servidor depois; renderer em `game.js` por último. Textos PT/EN e controles por mouse, teclado e gamepad.
- Manter a estrutura atual de `GameRoom`; não substituir o combate por uma fila geral nem refatorar sistemas não relacionados.
- Preservar os arquivos locais de outros trabalhos e limitar commits aos arquivos desta entrega.

## Review Focus

- A mesma conexão dispara o ataque e controla quem pode reagir: o leitor WebSocket deve continuar recebendo a resposta (Task 3).
- Dois aceites chegam juntos e um vem de um herói extra: somente um estoque autorizado diminui (Tasks 1–2).
- A fumaça esconde o atacante ou lhe concede vantagem por visão no escuro: o ataque pendente continua contra o alvo original com desvantagem explícita (Task 3).
- Um prazo do Mestre vence durante a reação ou o projétil: não deve iniciar outro golpe nem avançar a iniciativa (Task 3).
- Uma oferta fecha enquanto outra UI está aberta ou o jogador reconecta: nenhum modal antigo responde por outra janela ou outro herói (Tasks 1, 2 e 4).

## Arquivos e responsabilidades

- `src/gameState.js`: estado da oferta, eventos recebidos, respostas com identidade explícita e limpeza.
- `server.py`: elegibilidade, consumo, concorrência, prazo, integração dos ataques, tarefas e timers, ciclo de vida da sala.
- `game.js`: caixa de reação, acessibilidade, integração de gamepad e apresentação da fumaça existente.
- `src/combatScene.js`: alterar somente se o encadeamento existente de projéteis não fornecer o tempo/ordem necessários para a fumaça preceder o ataque.
- `src/lang/interface.js`: rótulos, descrição e contagem regressiva PT/EN.
- `CLAUDE.md`: contrato do novo protocolo, regras e pontos de integração após a implementação.
- Criar `tools/test_bomba_fumaca_reacao.py` e `tools/test_bomba_fumaca_reacao_cliente.js`: regressões comportamentais da janela e do combate.

### Task 1: Estado da oportunidade e resposta explícita no cliente

**Files:** modificar `src/gameState.js`; criar `tools/test_bomba_fumaca_reacao_cliente.js`.

**Interfaces:**
- Produz getter `GS.smokeReaction`, objeto da oferta ativa ou `null`.
- Produz `GS.responderReacaoFumaca(requestId: string, heroId: string | null, usar: boolean): boolean`.
- Eventos `smokeReactionPrompt` e `smokeReactionClosed`; mensagens `smoke_reaction_prompt`, `smoke_reaction_choice`, `smoke_reaction_closed`.
- Oferta: `{request_id, attacker:{id,name,pos}, target:{id,name,pos}, candidates:[{hero_id,name,quantity}], expires_at}`. `expires_at` é epoch em milissegundos.
- Resposta: `{type:'smoke_reaction_choice', request_id, usar, heroi}`; para recusar a conexão inteira, usar `heroi:null`, sem herdar o foco atual de `send()`.

- [ ] **Step 1:** Escrever testes de estado com WebSocket simulado, conforme os testes existentes do módulo: `testPromptStoresCandidates` verifica 2 candidatos; `testExplicitHeroOverridesFocus` verifica `sent.heroi === 'extra2'`; `testDeclineDoesNotInheritFocus` verifica `sent.heroi === null`; `testStaleCloseKeepsNewPrompt` fecha `r1` e conserva `r2`; `testResetClearsPrompt` verifica `GS.smokeReaction === null` após desconexão/saída.
- [ ] **Step 2:** Rodar `node tools/test_bomba_fumaca_reacao_cliente.js`; confirmar falha por interface ausente.
- [ ] **Step 3:** Implementar getter, sender e cases de mensagens. Não adicionar a oferta ao conjunto que troca foco automaticamente: ela já contém todos os heróis da conexão. Identificar e limpar a oferta nos caminhos reais de saída/reconexão/reset; rejeitar resposta cujo identificador não esteja ativo.
- [ ] **Step 4:** Rodar o novo teste, `node tools/test_solo_grupo_cliente.js` e `node --check src/gameState.js`; exigir zero falhas.
- [ ] **Step 5:** Commit limitado ao estado e seu teste: `feat: add smoke reaction client state`.

### Task 2: Janela autoritativa e disputa por uma bomba

**Files:** modificar `server.py`; criar `tools/test_bomba_fumaca_reacao.py`.

**Interfaces:**
- `GameRoom._smoke_reaction_candidates(self, attacker: dict, target_obj: dict) -> list[dict]`: consulta sem consumir ações; cada entrada contém herói, conexão proprietária e quantidade disponível.
- `GameRoom._smoke_reaction_item(self, hero: dict) -> tuple`: retorna `(item, source_location)` com a origem válida da bolsa/cinto, ou `(None, None)`.
- `GameRoom._await_smoke_reaction(self, attacker: dict, target_obj: dict) -> dict | None`: aguarda a decisão e devolve a reserva vencedora com `hero_id`, `item`, `source_location`, `pos`, `request_id`; o consumo já ocorreu.
- `GameRoom.handle_smoke_reaction_choice(self, connection_pid: str, data: dict) -> None` (async): valida propriedade diretamente pela conexão real, inclusive quando `heroi:null` indica recusa de todos os seus candidatos.
- `GameRoom._close_smoke_reaction(self, reason: str) -> None` (async): fecha ofertas e acorda o evento com segurança em cancelamento.
- Campo efêmero `_smoke_reaction` inicialmente `None`; timeout configurável `SMOKE_REACTION_TIMEOUT = 12` para reduzir a duração somente no fixture dos testes.

- [ ] **Step 1:** Criar fixture `setup_reaction_room()` com piso, dois heróis conectados e monstro real, seguindo `tools/test_previsao_ataque.py`; capturar mensagens e usar um Event de teste para saber quando a oferta abriu. Acrescentar testes com `assert` para raio base 4, bônus de alcance, parede, bolsa, cinto, imobilização sem incapacidade, herói incapacitado, ausência de alvo herói, recusa de todos e timeout sem consumo.
- [ ] **Step 2:** Incluir teste concorrente usando `asyncio.gather` com dois aceites: soma das quantidades cai exatamente 1, uma reserva vence, duas conexões recebem fechamento. Acrescentar identidade forjada, item removido antes do aceite e repetição de resposta; exigir nenhum consumo indevido.
- [ ] **Step 3:** Rodar `python -X utf8 tools/test_bomba_fumaca_reacao.py`; confirmar falhas pela ausência da janela.
- [ ] **Step 4:** Implementar as interfaces e o despacho da resposta antes da tradução de personagem do handler WebSocket, preservando o `connection_pid` real. Usar `time.monotonic()` para o prazo interno e epoch em ms para o cliente. Consultar estoque e condições sem efeitos colaterais; revalidar no aceite e reservar/consumir sem `await` entre validação e decisão. Gerar identificador único por ataque.
- [ ] **Step 5:** Integrar desconexão, religar_heroi, reinício/saída e exclusões de save. Se a janela continuar aberta para outra conexão, reconectar reoferece somente os candidatos originalmente autorizados e ainda aptos, sem renovar prazo ou reabrir uma recusa. Testar `testDisconnectLastCandidateResumes`, `testReconnectKeepsDeadline`, `testCancellationClosesAll` com asserts sobre evento, prazo e `_smoke_reaction is None` ao fim.
- [ ] **Step 6:** Rodar o novo teste e `python -X utf8 tools/test_cinto_utilidades_uso.py`; exigir zero falhas. Commit: `feat: add authoritative smoke bomb reaction window`.

### Task 3: Interromper e retomar os caminhos reais de ataque

**Files:** modificar `server.py`; ampliar `tools/test_bomba_fumaca_reacao.py`.

**Interfaces:**
- Consome `_await_smoke_reaction(...)` da Task 2.
- `GameRoom._play_smoke_reaction(self, result: dict) -> None` (async): emite o projétil, aguarda seu tempo de gesto/voo, chama `_aplicar_escuridao` com raio 1, duração 2 e visual_id único `fumaca_*`, publica estado e permite prosseguir. Não consome o item novamente.
- `GameRoom._run_smoke_capable_command(self, coroutine, label: str) -> asyncio.Task`: inicia tarefa rastreada e isolada para comandos originados no WebSocket que possam alcançar um ataque inimigo bloqueante; mantém o leitor livre e impede comando de combate concorrente na sala durante a pausa.
- Resultado de reação é variável local do ataque; não criar bônus durável no monstro.

- [ ] **Step 1:** Testar o fluxo real modular com aceitação pelo fixture: antes da resposta, zero d20/dano; após aceitar, sequência `prompt → closed → projétil → nuvem → rolagem`. Controlar os d20 como 18 e 3 e verificar uso do 3; estoque diminui 1 e flags de ação/fome/sede não mudam. Verificar nuvem raio 1/duração 2 e expiração pelo processador normal de zonas.
- [ ] **Step 2:** Testar as variantes reais: ataque legado em `gm_phase`, arremessável direcionado e `handle_mestre_atacar_monstro`. Incluir monstro com visão no escuro/vantagem, personagem protegido diferente do lançador, múltiplos golpes e fumaça ocultando o atacante; o primeiro alvo e a desvantagem explícita devem persistir. Área sem d20 não abre janela.
- [ ] **Step 3:** Implementar o hook depois da validação inicial do golpe e antes de qualquer rolagem/feedback. Retomar com o alvo capturado; ligar a desvantagem explícita em cada ramo de rolagem e sua narração/dados. Chamar `_play_smoke_reaction` apenas para resultado vencedor; nuvem usa `_aplicar_escuridao`, sem duplicar sua regra de duração.
- [ ] **Step 4:** Auditar os chamadores de `_execute_one_monster_attack` e `_monster_throw_item_impl` para identificar comandos WebSocket que podem aguardar a própria conexão. Aplicar `_run_smoke_capable_command` aos comandos de Mestre/controle, ação de teste e interação com decoração que dispare ataque. As tarefas existentes de iniciativa permanecem no fluxo próprio. Usar o isolamento de falhas existente e limpar a referência da tarefa em `finally`.
- [ ] **Step 5:** Suspender os timers ativos de turno e controle manual durante decisão/voo, conservando o prazo restante; retomar apenas o timer que ainda pertença ao mesmo ator/fase. Impedir avanço da iniciativa ou novas mutações de combate concorrentes; permitir respostas, reconexão e consultas. Acrescentar `testSameConnectionCanAnswer`, `testMasterTimeoutDuringReactionDoesNotAdvance`, `testCancelledCommandDoesNotRestoreOldTimer` e `testOriginalTargetSurvivesSmokeVisibilityChange`.
- [ ] **Step 6:** Rodar o novo teste, `python -X utf8 tools/test_modo_mestre.py`, `python -X utf8 tools/test_solo_grupo.py` e `python -X utf8 tools/test_arremessaveis_tatico.py`. Exigir zero falhas. Commit: `feat: pause enemy attacks for smoke bomb reactions`.

### Task 4: Caixa de reação e sequência visual em 2D/3D

**Files:** modificar `game.js`, `src/lang/interface.js`; modificar `src/combatScene.js` somente se a temporização exigir; ampliar `tools/test_bomba_fumaca_reacao_cliente.js`.

**Interfaces:**
- Consome `GS.smokeReaction`, `GS.responderReacaoFumaca(...)`, `smokeReactionPrompt`, `smokeReactionClosed` da Task 1.
- `_showSmokeReaction(msg: object): void` e `_closeSmokeReaction(requestId: string): void` no renderer; um overlay `#smoke-reaction-overlay` por conexão.
- Rótulos `ui.reacao_fumaca.*` PT/EN para título, ataque anunciado, herói/quantidade, lançar, não reagir e segundos restantes.

- [ ] **Step 1:** Ampliar testes com DOM mínimo segundo o padrão dos testes de UI do projeto: fechamento antigo não remove oferta nova; dois candidatos resultam em respostas com identidades distintas; Escape e recusa enviam uma única negativa; fechamento remoto/desconexão remove listeners e contador. Dados de nomes são tratados como texto, sem executar HTML.
- [ ] **Step 2:** Implementar caixa com o texto aprovado, botão de lançamento por candidato e recusa única por conexão. Mostrar prazo remanescente a partir de `expires_at`, sem usar o contador cliente como autoridade para consumir item. Desabilitar respostas duplicadas enquanto aguarda fechamento.
- [ ] **Step 3:** Registrar o overlay na seleção de contexto/modal do gamepad existente em `game.js`, priorizando sua navegação sem acionar o mapa atrás. A confirma; B/Escape recusa; teclado navega entre candidatos/botões. Preservar e restaurar foco anterior somente se o elemento continuar válido.
- [ ] **Step 4:** Reutilizar o arremesso de item e `_fumacaSync`. Conferir no `src/combatScene.js` os tempos reais e garantir que dados/animação do ataque seguinte não ultrapassem gesto, voo e surgimento da nuvem. Acrescentar teste da ordem das mensagens/feedback sem substituir a verificação visual real.
- [ ] **Step 5:** Rodar o teste cliente novo e `node tools/test_combat_feedback_colors.js`; executar `node --check game.js`, `node --check src/gameState.js`, `node --check src/combatScene.js`. Exigir zero falhas. Commit: `feat: show multiplayer smoke reaction prompt`.

### Task 5: Validação integrada e registro do contrato

**Files:** modificar `CLAUDE.md`; ajustar somente arquivos desta feature se a validação revelar falhas.

**Interfaces:** sistema completo das Tasks 1–4; atualizar documentação dos três tipos de mensagem, elegibilidade, custos, duração e pontos de pausa.

- [ ] **Step 1:** Executar uma vez as suítes focadas novas após a integração; rodar `python -X utf8 -m py_compile server.py` e `git diff --check`. Repetir apenas testes afetados por correções posteriores.
- [ ] **Step 2:** Iniciar ou reutilizar o servidor local conforme `CLAUDE.md` e exercitar a reação em sessão real com duas conexões. Aceitar quase simultaneamente e confirmar uma única bomba consumida; recusar em outra rodada e confirmar continuidade imediata quando todos recusam.
- [ ] **Step 3:** Repetir o fluxo visual em 2D e 3D: caixa antes dos dados, voo até o atacante, fumaça antes do golpe, dois d20 com o menor usado, nuvem persistindo/expirando normalmente. Exercitar teclado e gamepad se dispositivo estiver disponível; registrar qualquer limitação de dispositivo/sessão sem afirmar validação que não ocorreu.
- [ ] **Step 4:** Exercitar Solo com grupo escolhendo herói diferente do foco e ataque controlado pelo Mestre. Confirmar que a mesma conexão pode responder durante a pausa e que a iniciativa avança uma única vez ao terminar o turno do monstro.
- [ ] **Step 5:** Documentar em `CLAUDE.md` o comportamento final e os comandos de teste realmente usados. Fazer a revisão final da alteração procurando consumo duplo, tarefa/evento pendurado e mudanças fora de escopo. Commit limitado: `docs: document smoke bomb reaction protocol`.
- [ ] **Step 6:** Informar ao usuário o comportamento entregue, resultado das verificações e caminhos não exercitados; apresentar opções de integração da branch sem fazer merge/push sem a decisão correspondente.
