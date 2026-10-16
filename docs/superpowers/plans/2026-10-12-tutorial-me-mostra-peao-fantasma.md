# Tutorial “Me mostra” — prévia com peão fantasma Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax.

**Goal:** Animar prévias visuais de movimento, equipamento e habilidade em “Me mostra”, mantendo as ações reais manuais e autoritativas no servidor.

**Architecture:** Ampliar a lista declarativa de operações permitidas no servidor e cliente. Um módulo cliente independente calcula o progresso temporal; `game.js` desenha a miniatura/cursor fantasma nos renderizadores existentes e integra o ciclo de vida. Os roteiros dos três casos piloto permanecem autorados nos módulos existentes.

**Tech Stack:** Python 3, JavaScript sem framework, canvas 2D, Three.js 0.128, WebSocket existente, testes Node.js e `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-12-tutorial-me-mostra-previsualizacao-fantasma-design.md`

## Global Constraints

- Nenhuma prévia move o herói real, altera inventário, gasta recursos, consome turno, ataca, rola dados, causa dano, conclui tarefas ou envia comandos de jogo ao servidor.
- A ação real continua manual. A lição só avança após o evento aceito pelo servidor.
- Um clique inicia uma animação curta da operação visual atual; ao terminar, a demonstração espera a ação real; outro clique repete a prévia atual.
- O fantasma é visual e privado ao cliente que iniciou a demonstração.
- Caminhos e alvos devem continuar sujeitos à visão/névoa; nenhuma prévia revela informação oculta.
- O piloto cobre equipar um item, mover no mapa e usar habilidade em boneco de treino; não ampliar antes da validação visual destes casos.
- Preservar arquivos locais não relacionados e só gerar saídas do tutorial a partir das fontes autoradas existentes.

## Review Focus

- Payload declarativo malformado ou com campo extra: rejeitar a operação sem executar parcialmente o roteiro. **Teste:** Task 1, testes de esquema espelhados no servidor e cliente.
- Jogador interage durante a animação: pará-la sem bloquear o evento normal do jogo. **Teste:** Task 3, entrada real encerra apenas a prévia.
- Casa ou alvo sai da visão ou muda durante a animação: ocultar o trecho e interromper sem revelar coordenadas. **Teste:** Task 3, contexto inválido cancela a amostra visível.
- Alternância 2D/3D ou reconstrução da cena durante a prévia: liberar a cópia e não deixar callback ativo. **Teste:** Task 3, limpeza de ciclo de vida.
- Miniatura ou item de origem não existe no estado atual: usar fallback sem interromper a lição. **Teste:** Tasks 2–3, contexto ausente produz fallback visual.

---

### Task 1: Validar operações de prévia declarativas

**Files:**
- Modify: `server.py:_guia_demonstracao_valida`
- Modify: `src/guiaTutorial.js:demonstracaoValidada`
- Test: `tools/test_tutorial_guia.py`
- Test: `tools/test_guia_tutorial_cliente.js`

**Interfaces:**
- Consumes: operações existentes `focar` e `abrir_interface`, com limite `GUIA_DEMO_MAX_OPERACOES = 4`.
- Produces: validação espelhada para `prever_movimento`, `prever_equipamento` e `prever_habilidade`, sem mudar o payload de ações WebSocket.

- [x] **Step 1: Add failing server schema tests**

In `ValidacaoTests`, add `test_demonstracao_visual_valida_por_operacao` for:

```python
{"acao": "prever_movimento", "alvo": "casa:[5,15]"}
{"acao": "prever_equipamento", "alvo": "slot:weapon"}
{"acao": "prever_habilidade", "habilidade": "golpe_devastador", "alvo": "monstro:boneco_treino"}
```

Add rejection cases for wrong `alvo` kinds, malformed ability ID syntax, missing fields, and extra fields such as `handler` or `comando`.

- [x] **Step 2: Run the server test and verify the new schema cases fail**

Run: `python -X utf8 tools/test_tutorial_guia.py`
Expected: only new preview operation cases fail; legacy `focar` and `abrir_interface` remain accepted.

- [x] **Step 3: Add the closed schemas to the server validator**

Update `_guia_demonstracao_valida` to accept exact key sets for the three operations, with these constraints: movement target matches `casa:[x,y]`; equipment target matches `slot:<id>`; `habilidade` is a bare lowercase ID matching `[a-z0-9_]+`; skill target matches `monstro:<id>` syntax. Reject unknown keys and preserve the 4-operation cap.

- [x] **Step 4: Mirror validation in the client**

Update `GuiaTutorial.demonstracaoValidada` with the same exact key sets and target kinds. Add client assertions for each valid operation and the same malformed/extra-field cases.

- [x] **Step 5: Run both schema suites**

Run: `python -X utf8 tools/test_tutorial_guia.py`
Run: `node tools/test_guia_tutorial_cliente.js`
Expected: both exit 0; existing schemas, routes and legacy lessons remain valid.

### Task 2: Add a deterministic preview timeline

**Files:**
- Create: `src/guiaDemonstracaoVisual.js`
- Create: `tools/test_guia_demonstracao_visual.js`
- Modify: `index.html`

**Interfaces:**
- Consumes: one already validated preview operation and a presentation context built from the current visible client state.
- Produces: `window.GuiaDemonstracaoVisual.criar({agendar, cancelarAgendamento, agora, aoQuadro, aoFim})`, returning `iniciar(operacao, contexto)`, `cancelar()`, and `ativo()`. `aoQuadro` receives `{operacao, progresso, contexto}` with `progresso` clamped to `[0,1]`.

- [x] **Step 1: Add failing deterministic timeline tests**

Cover start at progress 0, monotonically increasing progress, completion exactly once, repeat as a new animation, cancellation clearing the scheduled frame, and invalid operation cancellation. Use injected clock and frame scheduler; do not rely on wall-clock delays.

- [x] **Step 2: Run the new test and verify it fails before implementation**

Run: `node tools/test_guia_demonstracao_visual.js`
Expected: failure because the module/API does not exist.

- [x] **Step 3: Implement the isolated timeline module**

Implement the specified API with a 1.2-second default for one preview operation, injected scheduler/clock for deterministic tests, one scheduled frame at a time, and idempotent `cancelar()`. The module computes time only; it must not access `GS`, DOM, WebSocket, inventory, or game handlers.

- [x] **Step 4: Load the module before `game.js` and pass its test**

Add `src/guiaDemonstracaoVisual.js` to the dynamic script loader in `index.html` before `game.js`.
Run: `node tools/test_guia_demonstracao_visual.js`
Expected: all timeline and cancellation cases pass.

### Task 3: Render and integrate ghost previews

**Files:**
- Modify: `game.js:_guiaDemonstracaoGarantir`, `_guiaDesenhar2D`, `_guiaAtualizar3D`, `dispose3D`
- Modify: `game.css`
- Modify: `src/lang/tutorial.js`
- Modify: `tools/test_guia_demonstracao_cliente.js`
- Modify: `tools/test_guia_tutorial_cliente.js`

**Interfaces:**
- Consumes: `GuiaDemonstracaoVisual.criar(...)` from Task 2; validated operation contexts from Task 1.
- Produces: `_guiaDemoVisualIniciar(operacao)`, `_guiaDemoVisualQuadro(amostra)`, and `_guiaDemoVisualLimpar()` in `game.js`; no new server message or game action.

- [x] **Step 1: Add failing client integration assertions**

Assert that the adapter routes only validated `prever_*` operations to the visual timeline; closing, pausing, step change, hero change, map mode switch and `dispose3D` stop and clear it; ordinary pointer/keyboard/gamepad events are not prevented or consumed; no action sender is called.

- [x] **Step 2: Run focused client tests and confirm the preview assertions fail**

Run: `node tools/test_guia_demonstracao_cliente.js`
Run: `node tools/test_guia_tutorial_cliente.js`
Expected: new rendering/lifecycle assertions fail before wiring.

- [x] **Step 3: Integrate preview operations with the click cursor**

Extend the controller adapter with a preview callback. Keep `focar` and `abrir_interface` behavior. Store the most recent preview operation so the action-boundary click replays its animation; if there is no preview operation, retain the current focus replay behavior. A user interaction stops the current animation without calling `preventDefault` or `stopPropagation`.

- [x] **Step 4: Draw the movement ghost in 2D and 3D**

In `_guiaDesenhar2D`, draw a translucent copy using `_getHero2DImg(classId)` at interpolated board coordinates after the path is confirmed visible. In `_guiaAtualizar3D`, maintain one scene copy of the controlled hero peão, clone its materials before changing opacity, disable raycast, and interpolate its position/orientation. Dispose clone-only materials and scene nodes without disposing shared model geometry. Use the generic silhouette fallback if the peão mesh is unavailable.

- [x] **Step 5: Draw equipment and skill previews without synthetic input**

Use a `pointer-events:none` visual cursor anchored to the live inventory item and equipment slot rectangles. For skill preview, animate the ghost toward the visible training target and draw a cosmetic impact cue only; do not invoke combat or ability visuals that roll, damage, or consume actions. If an anchor/target is unavailable, stop at the ordinary halo and text fallback.

- [x] **Step 6: Wire pause, repeat, resize, locale and mode-switch cleanup**

Cancel the scheduled frame on pause, close, lesson/hero change, tutorial end, mode switch or 3D rebuild. On resume, replay the same operation only after a fresh click. Recompute screen anchors after resize or language redraw. Add localized preview progress and fallback labels in Portuguese and English.

- [x] **Step 7: Run focused integration suites and syntax checks**

Run: `node tools/test_guia_demonstracao_cliente.js`
Run: `node tools/test_guia_tutorial_cliente.js`
Run: `node --check game.js`
Run: `node --check src/guiaDemonstracaoVisual.js`
Expected: all focused tests exit 0 and both JavaScript files parse.

### Task 4: Author the three pilot preview routes

**Files:**
- Modify: `tools/tutorial_guia_comum.py`
- Modify: `tools/tutorial_guia_guerreiro.py`
- Modify: `tools/test_tutorial_conteudo.py`
- Regenerate: `dungeons/campo_de_treinamento.json`
- Regenerate: `src/lang/tutorial_guia.js` only if generated text changes

**Interfaces:**
- Consumes: preview operation schemas and renderer from Tasks 1–3.
- Produces: one route for each accepted pilot, ending in a manual action and preserving task/reward definitions.

- [x] **Step 1: Add failing route assertions**

Add `DemonstracaoFantasmaContentTests` to assert these ordered operations: `fala_0.andar` focuses and previews `casa:[5,15]`; `fala_2.equipar` focuses and previews `slot:weapon`; `treino_golpe.golpe` focuses `habilidade:golpe_devastador`, focuses `monstro:boneco_treino`, then previews that skill/target. Assert each route remains at or below four operations and its lesson task/`conclui_com` is unchanged.

- [x] **Step 2: Run the focused content test and verify missing route operations fail**

Run: `python -X utf8 tools/test_tutorial_conteudo.py -k demo_fantasma`
Expected: the route operation assertions fail; unrelated historical content tests are not included in this focused run.

- [x] **Step 3: Add only the three authored preview operations**

Update the two source modules. Keep `abrir_interface` routes, text, task conditions, rewards, step ordering and all non-pilot lessons unchanged.

- [x] **Step 4: Regenerate the authored map data and verify the diff is narrow**

Run: `python -X utf8 tools/gerar_guia_comum.py`
Expected: generated guide fields contain the three preview operations. Inspect the semantic diff of `dungeons/campo_de_treinamento.json`; only the pilot `guia[].demonstracao` fields may change. Preserve all other existing local map changes. The language output should remain byte-identical unless a localized label was added to the guide content.

- [x] **Step 5: Run focused content and server validation**

Run: `python -X utf8 tools/test_tutorial_conteudo.py -k demo_fantasma`
Run: `python -X utf8 tools/test_tutorial_guia.py`
Expected: authored route tests and server validation pass.

### Task 5: Validate the pilot visually in the game

**Files:**
- No planned product changes; fix only regressions from Tasks 1–4.

**Interfaces:**
- Consumes: the three authored routes, preview timeline, and 2D/3D renderer adapters.
- Produces: reviewed pilot behavior ready for the user to approve before tutorial-wide expansion.

- [ ] **Step 1: Verify equipment preview**

Open the inventory lesson, play the item-to-slot preview, and confirm the actual item remains in the bag until manually equipped. Close/reopen and repeat; verify there is no synthetic drag/click.

- [ ] **Step 2: Verify movement preview in 2D and 3D**

Confirm the ghost uses the current hero image/model, follows only visible valid houses, faces each segment and does not change the real peão position or movement points. Perform the manual movement and confirm only server acceptance advances the lesson.

- [ ] **Step 3: Verify skill preview and action safety**

Confirm the ghost indicates the ability and training dummy without a roll, damage, or action cost. Arm and use the real ability; confirm accepted progression clears the preview and the next one waits for a new click.

- [ ] **Step 4: Verify lifecycle and controls**

For all pilots, test pause, close/reopen, repeated preview, rejected/canceled action, resize, language change, 2D/3D switch and mouse/keyboard/gamepad controls. Confirm no animation frame, ghost mesh/material, or UI cursor remains after cleanup and no hidden target is exposed.

## Handoff

This plan implements only the approved spec at `docs/superpowers/specs/2026-10-12-tutorial-me-mostra-previsualizacao-fantasma-design.md`. It does not authorize automatic real actions or expansion beyond the pilot before visual review.
