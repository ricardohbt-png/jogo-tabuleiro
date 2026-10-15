# Encontros aleatórios e caravana segura — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Interromper viagens arriscadas com no máximo um combate aleatório e oferecer caravana paga, sem encontros, entre cidades.

**Architecture:** O servidor continua autoritativo para viagem, custos, pagamento, rolagem, encontro e retomada. `GameRoom` mantém uma continuação de viagem persistente enquanto executa um combate temporário no mapa autorado de estrada; no cliente, `gameState.js` envia intenções e `game.js` apresenta prévias, opções e prompts sem calcular resultados autoritativos.

**Tech Stack:** Python 3 + `websockets`, JavaScript vanilla, estado e envio em `src/gameState.js`, renderização em `game.js`, textos em `src/lang/*.js`, mapa autorado em JSON.

**Spec:** `docs/superpowers/specs/2026-10-14-viagens-emboscadas-caravanas-design.md`

## Global Constraints

- `server.py` é a fonte autoritativa para estado, combate, ouro e recursos; validar todas as mensagens de rede e não confiar em custos/chances enviados pelo cliente.
- `src/gameState.js` contém lógica de estado pura e ações WebSocket, nunca DOM, canvas, Three.js ou `window`.
- `game.js` é o renderer; usa estado por `GS.*` e envia ações por métodos de `GS`, sem escrever em estado interno.
- Mensagens novas de UI devem ter textos pt/en e paridade de parâmetros em `src/lang/interface.js`, `src/lang/erros.js` ou `src/lang/narracao.js`, conforme o uso.
- Manter Three.js r128, sem framework ou bundler novo.
- Não modificar `dungeons/floresta.json`; o teste usa `dungeons/estrada_floresta_emboscada.json`.
- A lógica de viagem pendente deve integrar os mecanismos existentes de checkpoint/foto e retomada; não duplicar cobrança nem rolagem em reconnect.
- Não acrescentar prêmio exclusivo para encontro; vitória usa o fluxo normal de XP/saque.

## Review Focus

- Duas mensagens repetidas de iniciar/retomar viagem não cobram ou rolam duas vezes — Task 2.
- Personagem sem ouro, patrocinador que recusa/fecha a janela e duas solicitações concorrentes não deixam pagamento parcial nem iniciam caravana — Task 3.
- Solo com grupo não trata heróis controlados pela mesma conexão como patrocinadores multiplayer — Task 3.
- Personagem morto, grupo com níveis diferentes, composição maior que o mapa ou spawn bloqueado não causa composição desproporcional nem sobreposição — Task 1.
- Vitória, derrota total, retorno de masmorra, continuar, reconnect e retomada do save preservam uma única continuação e o custo já debitado — Task 4.

---

### Task 1: Regras puras, composições e mapa autorado

**Files:**
- Modify: `server.py` (helpers de faixa, preço, risco e seleção de composição)
- Create: `dungeons/estrada_floresta_emboscada.json`
- Create: `tools/test_encontros_viagem.py`

**Interfaces:**
- Produces: helpers puros de viagem para `tier_viagem(fome: int, sede: int)`, `chance_encontro(fome: int, sede: int) -> int`, `tarifa_caravana(fome: int, sede: int) -> int` e `selecionar_composicao_viagem(grupo, categoria, rng) -> composição`.
- Consumes: `WORLD_ROUTES`, os custos `fome`/`sede` de aventuras, catálogo `MONSTER_DEFS`/`monster_cr`, gerador aleatório injetável nos testes e o schema de masmorra autorada.

- [ ] **Step 1: Escrever testes de regra que falham** — cubra soma de custos 0, 12, 14, 15, 16, 20, 21 e 28; chances 10/15/20; tarifas para cada faixa; `ceil` de 15%; seleção determinística com RNG controlado; e grupo com personagens vivos/mortos e níveis diferentes.
- [ ] **Step 2: Rodar o teste focado** — `python -X utf8 tools/test_encontros_viagem.py`; confirmar que falha nos helpers ainda ausentes.
- [ ] **Step 3: Implementar os helpers puros em `server.py`** — proposta de faixas: total até 14 curta, 15–20 média, acima de 20 longa; total 0 usa chance curta. Tarifas-base 10/20/30 + `ceil(total × 0.15)`.
- [ ] **Step 4: Preparar composições** — cadastrar conjuntos pré-aprovados de animais e bandoleiros com peso de ND total, grupo esperado e zonas de spawn; escolher uma composição compatível com a força e o número dos heróis viajantes, sem alterar atributos individuais de monstros.
- [ ] **Step 5: Criar o mapa 26×16** — curva suave de estrada, bordas florestadas, clareiras laterais, entrada em uma extremidade e faixas de spawn distintas; manter o mapa sem monstros fixos, baús ou objetivo autorado. O fluxo temporário detecta a derrota do último inimigo e retoma a viagem sem botão de encerrar missão.
- [ ] **Step 6: Validar o mapa e os spawns** — teste deve validar schema, `ambiente: ar_livre`, objetivo, tiles de entrada, limites do mapa, distância segura e footprints sem colisão para o maior grupo/composição.
- [ ] **Step 7: Rodar verificação focada** — `python -X utf8 tools/test_encontros_viagem.py`; esperado: todas as regras, composições e validações do mapa aprovadas.

### Task 2: Estado autoritativo e pagamento de caravana

**Files:**
- Modify: `server.py` (inicialização do estado da viagem, handlers WebSocket, cobrança de rota/cidade, serialização e checkpoint/save)
- Modify: `tools/test_encontros_viagem.py`

**Interfaces:**
- Consumes: helpers e composições da Task 1.
- Produces: estado `pending_world_travel` validado pelo servidor; extensão de `world_travel` com `mode: "road" | "caravan"`; mensagem de resposta do jogador à solicitação de cobertura, identificada por request id; transições de viagem pendente que não executam a rolagem novamente.

- [ ] **Step 1: Adicionar testes de servidor que falham** — viagem curta/média/longa, caravana sem evento, custo de provisões por herói, ouro insuficiente, patrocínio voluntário, cancelamento, solicitação velha/duplicada e anfitrião não autorizado.
- [ ] **Step 2: Rodar o teste focado** — confirmar as falhas antes da implementação.
- [ ] **Step 3: Implementar transação de partida** — revalidar fase, anfitrião, destino, recursos e modo; calcular os valores no servidor; cobrar ouro e provisões de forma atômica; criar a continuação com origem, destino, tipo, cobrança feita e rolagem já resolvida.
- [ ] **Step 4: Implementar cobertura explícita** — se uma passagem estiver sem pagador, emitir prompt com personagem e tarifa; aceitar cobertura completa somente de outro jogador multiplayer; em Solo, bloquear patrocínio; rejeitar request id antigo, insuficiência de saldo e duplicatas; permitir estrada ou cancelamento sem dívida.
- [ ] **Step 5: Persistir e retomar com segurança** — salvar a continuação junto à foto/checkpoint do combate; reconnect e load devem retomar a mesma viagem pendente com `charged=true` e o resultado da rolagem já armazenado.
- [ ] **Step 6: Rodar os testes de servidor** — todos os casos da Task 2 devem passar; verificar que o saldo de cada personagem muda uma vez apenas.

### Task 3: Interromper com encontro e retomar destino

**Files:**
- Modify: `server.py` (início de combate temporário, vitória/derrota, retorno/continuação)
- Modify: `tools/test_encontros_viagem.py`

**Interfaces:**
- Consumes: `pending_world_travel`, mapa/composições da Task 1 e cobrança da Task 2.
- Produces: transições explícitas `start_encounter`, `resume_city_destination`, `continue_to_adventure` e `return_to_origin`, cada qual consumindo a continuação no máximo uma vez.

- [ ] **Step 1: Adicionar testes de transição que falham** — sem encontro, encontro e vitória em destino cidade, encontro e vitória em aventura com as duas escolhas, derrota total, evento duplicado e retomada depois de reconnect.
- [ ] **Step 2: Rodar o teste focado** — confirmar as falhas antes da implementação.
- [ ] **Step 3: Extrair início validado de aventura sem nova cobrança** — separar validação/cobrança de provisões da preparação/entrada usada para retomar `handle_world_adventure`; preservar cena, etapa, revisitabilidade e snapshot atuais.
- [ ] **Step 4: Iniciar combate temporário** — carregar mapa ao ar livre e a composição escolhida; manter origem/destino no estado pendente; detectar a derrota do último inimigo e retomar automaticamente sem passar por `end_game(victory=True)`, `mission_complete_pending` ou progresso/recompensa especial de aventura.
- [ ] **Step 5: Retomar a viagem na vitória** — cidade conclui para o destino; aventura envia decisão do anfitrião e continua sem custo extra ou retorna à origem sem reembolso; limpar o estado pendente atomicamente.
- [ ] **Step 6: Respeitar derrota padrão** — se a regra geral encerra o jogo, deixar `end_game(victory=False)` atuar e não avançar o destino.
- [ ] **Step 7: Rodar testes de fluxo** — confirmar custo único, destino correto, limpeza do estado e integração com fluxos normais de entrada/derrota.

### Task 4: Prévia de preço/risco, mercador e controles

**Files:**
- Modify: `src/gameState.js` (novas ações/eventos WebSocket)
- Modify: `game.js` (prévia do destino, escolha estrada/caravana, prompts)
- Modify: `src/lang/interface.js` (textos pt/en)
- Modify: `src/lang/erros.js` (recusas pt/en)
- Modify: `src/lang/narracao.js` (resultado de viagem/emboscada, se necessário)
- Modify: `tools/test_encontros_viagem.py` ou novo `tools/test_viagem_cliente.js`

**Interfaces:**
- Consumes: os payloads/ações de viagem e patrocínio da Task 2 e os estados de encontro/continuação da Task 3.
- Produces: diálogo acessível com tarifa por personagem, total da caravana, custos de fome/sede, risco da estrada, confirmação/cancelamento; prompt do mercador com retrato existente; painel pós-vitória da aventura; suporte a mouse, teclado e gamepad.

- [ ] **Step 1: Escrever testes cliente que falham** — prévia de valores recebidos, ausência de cálculo autoritativo, botões desabilitados para quem não é anfitrião, patrocínio apenas por jogador multiplayer, foco/controle e encerramento/cancelamento do modal.
- [ ] **Step 2: Implementar ações em `gameState.js`** — enviar somente intenção/modo/destino e resposta de patrocínio; guardar solicitações pendentes recebidas sem usar DOM.
- [ ] **Step 3: Implementar UI de destino em `game.js`** — substituir o clique direto por confirmação com estrada e caravana; apresentar custos e chance já enviados no `city_state`; não mostrar caravana em destino masmorra.
- [ ] **Step 4: Implementar prompt do mercador** — usar `assets/tavern/mercador.png` ou `mercador2.png`; cada outro jogador pode aceitar pagar a passagem identificada; apresentar alternativa estrada e cancelar quando a caravana não puder ser fechada.
- [ ] **Step 5: Implementar resultado de emboscada** — após vitória em destino cidade, mostrar/animar a chegada normal; para aventura, oferecer continuar/retornar. Usar a transição visual existente como fallback, sem simular progresso contínuo enquanto o combate estiver ativo.
- [ ] **Step 6: Adicionar traduções e controles** — chaves novas com paridade pt/en; foco inicial, navegação, confirmação e cancelamento em teclado/gamepad, seguindo os modais existentes.
- [ ] **Step 7: Verificar cliente** — `node --check src/gameState.js`, `node --check game.js` e teste cliente focado; fazer uma verificação manual do fluxo com mouse e controle.

### Task 5: Verificação integrada e atualização da fonte de regras

**Files:**
- Modify: `CLAUDE.md` (seção de mapa-múndi/viagens)
- Modify: `tools/test_encontros_viagem.py` (integração final)

- [ ] **Step 1: Rodar testes direcionados** — `python -X utf8 tools/test_encontros_viagem.py`, testes existentes de `tools/test_cidades_editor.py`, `tools/test_masmorra_sequenciada.py` e `tools/test_aventura_retomada.py`; rodar os testes de cliente focados e `git diff --check`.
- [ ] **Step 2: Fazer ensaio manual no jogo** — rota curta/média/longa, caravana paga, passageiro sem ouro com patrocinador, patrocinador que recusa, Solo com grupo, mapa da estrada, vitória/derrota, destino cidade e destino masmorra continuar/retornar, mouse e gamepad.
- [ ] **Step 3: Atualizar `CLAUDE.md`** — registrar fórmula, faixas, protocolo de solicitação/cobertura, retomada, mapa autorado e testes; seguir a regra de fonte única do projeto.
- [ ] **Step 4: Revisar os arquivos alterados** — confirmar que `floresta.json`, custos nativos de provisões, dívida, recompensa de aventura e regras normais de derrota não foram alterados.

## Questões para aprovação antes da implementação

1. Confirmar a classificação proposta: total fome+sede até 14 = curta; 15–20 = média; acima de 20 = longa.
2. Decidir a representação dos bandoleiros: o catálogo não contém bandido. Para limitar a primeira entrega, a recomendação é usar um visual humanoide já existente como substituto temporário; arte/ficha humana dedicada pode ser uma etapa posterior.

---
