# “Me mostra” Assisted Tutorial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each click on **Me mostra** guide one safe tutorial stage, then wait for the player’s real action and server acceptance.

**Architecture:** Refine the existing local demonstration controller to advance one declared operation per click and preserve its cursor across dismissal. Keep game actions and lesson progress in the existing server-authoritative flow; author and validate three pilot routes before expanding.

**Tech Stack:** Python 3, vanilla JavaScript, existing WebSocket events, DOM/CSS, Node and Python test harnesses.

**Spec:** `docs/superpowers/specs/2026-10-12-tutorial-me-mostra-demonstracao-assistida-design.md`

## Global Constraints

- “Me mostra” never executes movement, attack, spell, item use, resource spending or turn ending.
- The server remains authoritative for completing actions and advancing the lesson.
- Demonstration routes use only a validated allowlist of focus and safe interface operations.
- One click advances one visual operation; while waiting for a real action, a click repeats its guidance.
- A new lesson step waits for a fresh click; it never starts a new route automatically.
- Dismissing the window or pausing guidance preserves the cursor for the next click.
- Display available mouse, keyboard and gamepad controls using actual supported bindings and inputs.
- Board highlights work in 2D/3D and respect fog of war.
- The initial pilot covers inventory/equip, board movement and skill use on the training dummy.
- Keep unrelated local changes and generated content outside the pilot untouched.

## Existing Files and Responsibilities

- `src/guiaDemonstracao.js`: pure, local demonstration cursor and safe operation runner; already exists in the working tree with timer-based advancement.
- `tools/test_guia_demonstracao_cliente.js`: Node harness for the controller and client integration; already exists and must be updated to click-driven behavior.
- `game.js` and `game.css`: lesson window, highlights, controller adapter, dismissal/reopen behavior and input guidance.
- `src/lang/tutorial.js`: localized guidance and input labels.
- `tools/tutorial_guia_comum.py`, `tools/tutorial_guia_guerreiro.py`, `tools/gerar_guia_comum.py`: authored pilot routes and generated tutorial guide data.
- `dungeons/campo_de_treinamento.json`, `src/lang/tutorial_guia.js`: generated data; regenerate through the existing authoring tools.
- `tools/test_tutorial_conteudo.py`, `tools/test_tutorial_guia.py`, `tools/test_guia_tutorial_cliente.js`: content, server contract and pure client validation.

## Review Focus

- Repeated clicks at the action boundary must not skip or confirm an action. **Test:** Task 1, same-session click and replay cases.
- A server-accepted action that changes the lesson must clear the old cursor and leave the next route inactive. **Test:** Task 2, lesson-step transition integration case.
- Dismissing and reopening the lesson must preserve the current operation index. **Test:** Task 2, suspend/resume case.
- An unavailable or fog-hidden target must fall back without revealing it. **Test:** Task 2, target visibility/fallback cases.
- Gamepad activation must advance only once per press and retain the interaction; keyboard and mouse paths must remain usable. **Test:** Task 2, input event cases and Task 4 manual validation.

---

### Task 1: Make the demonstration cursor click-driven

**Files:**
- Modify: `src/guiaDemonstracao.js`
- Test: `tools/test_guia_demonstracao_cliente.js`

**Interfaces:**
- Consumes: `GuiaTutorial.demonstracaoValidada(passo)`, `GuiaTutorial.parseUi(ui)`, and adapter callbacks for focus and safe interface opening.
- Produces: `criar(opcoes)` returns `avancar(passo, chave)`, `suspender(motivo)`, `cancelar(motivo)`, `redesenhar()`, and state/cursor accessors. A new key loads the route and runs its first operation; the same key runs at most one next operation. After suspension, the next click reapplies the currently displayed operation without consuming the next one. Once the route ends, advancing repeats the final action guidance without changing state.

- [x] **Step 1: Add failing controller tests**

Update the isolated harness with assertions that a click runs only one operation, the timer queue stays empty, the next click runs the next operation, a click at the action boundary repeats the final focus without calling any game action, suspension followed by the same key reapplies the current operation without consuming the next one, an unavailable target uses fallback, and a different lesson/step key starts a fresh cursor.

- [x] **Step 2: Run the focused harness and verify the new expectations fail**

Run: `node tools/test_guia_demonstracao_cliente.js`
Expected: the new one-operation-per-click and cursor-preservation checks fail against the current timer-based controller.

- [x] **Step 3: Replace timed advancement with the per-click cursor**

In `src/guiaDemonstracao.js`, remove timer scheduling. Store the validated route, current operation index, last focus and session key. Execute at most one safe operation per `avancar` call. Make `suspender` hide the current visual guidance while retaining the cursor and set the next click to reapply that same operation; make `redesenhar` restore it. Keep the action boundary as a waiting state.

- [x] **Step 4: Run the harness and verify the controller contract**

Run: `node tools/test_guia_demonstracao_cliente.js`
Expected: all controller state, route cursor, fallback and no-game-action assertions pass.

### Task 2: Integrate persistent guidance and all available controls

**Files:**
- Modify: `game.js`
- Modify: `game.css`
- Modify: `src/guiaTutorial.js`
- Modify: `src/lang/tutorial.js`
- Modify: `tools/test_guia_demonstracao_cliente.js`
- Modify: `tools/test_guia_tutorial_cliente.js`
- Test: `tools/test_guia_tutorial_cliente.js`

**Interfaces:**
- Consumes: click-driven controller from Task 1; existing `licaoPasso`, `licaoPassoOk`, and `licaoConcluida` messages; existing UI focus, gamepad binding, inventory and menu APIs.
- Produces: `_guiaMostrar()` calls `avancar` for the current session; lesson-step changes reset the prior cursor; window close/cancel suspends it; window reopen and renderer/device refresh preserve and redraw it. `GuiaTutorial.demonstracaoDisponivel(passo)` identifies steps that need the button, and `GuiaTutorial.controlesDemonstracao(ui)` returns only supported input methods. The guidance panel shows their actual shortcuts/bindings.

- [x] **Step 1: Add failing integration checks**

Extend the pure guide tests to verify that demonstration-only steps are eligible for **Me mostra** and that `controlesDemonstracao(ui)` reports mouse/keyboard/gamepad only where that interface supports them. Extend the client harness to verify: a new lesson-step message does not auto-start its demonstration; accepted progression clears the old focus; closing and reopening preserves the cursor; and unavailable map targets respect the existing visibility filter.

- [x] **Step 2: Run focused client tests and verify the new checks fail**

Run: `node tools/test_guia_demonstracao_cliente.js`
Run: `node tools/test_guia_tutorial_cliente.js`
Expected: new lifecycle and control-display checks fail before the integration changes; existing guide parsing checks remain green.

- [x] **Step 3: Wire click, dismiss, reopen and lesson transitions**

In `game.js`, route each **Me mostra** click to `avancar`. Preserve the cursor when `_fecharJanelaLicao()` hides the window and restore it when `_reabrirJanelaLicao()` opens the same lesson/step. Reset it only when the lesson ID, step index or focused hero changes, or the tutorial ends. Keep server events as the only source of accepted progression.

- [x] **Step 4: Render supported mouse, keyboard and gamepad controls**

Use the real inventory button, current keyboard shortcuts, configured gamepad bindings, and the actual mouse/keyboard/gamepad interactions supported by the highlighted control. Add localized Portuguese and English labels in `src/lang/tutorial.js`; do not display a binding that the corresponding interface cannot use.

- [x] **Step 5: Run focused client regressions**

Run: `node tools/test_guia_demonstracao_cliente.js`
Run: `node tools/test_guia_tutorial_cliente.js`
Expected: both processes exit 0; step transitions, dismissal/resume, device refresh, focus redraw and fallback remain correct.

### Task 3: Author and generate the three pilot routes

**Files:**
- Modify: `tools/tutorial_guia_comum.py`
- Modify: `tools/tutorial_guia_guerreiro.py`
- Modify: `tools/test_tutorial_conteudo.py`
- Regenerate: `dungeons/campo_de_treinamento.json`
- Regenerate: `src/lang/tutorial_guia.js`
- Test: `tools/test_tutorial_guia.py`

**Interfaces:**
- Consumes: safe operation schema from the existing server/client validator and click-driven route from Tasks 1–2.
- Produces: three authored routes: `fala_2` opens inventory then focuses the weapon slot; `fala_0` focuses the valid movement destination; `treino_golpe` focuses the skill then the training dummy. Every route ends at a manual action that the existing server task/event validates.

- [x] **Step 1: Add content assertions for all three pilot routes**

In `tools/test_tutorial_conteudo.py`, assert the operation order for inventory/equip, movement target and skill/dummy, and assert task definitions and existing `conclui_com` values are unchanged. Task 2 covers whether each such step displays **Me mostra**.

- [x] **Step 2: Run content tests and verify the new assertions fail**

Run: `python -X utf8 tools/test_tutorial_conteudo.py`
Expected: missing movement/equip route assertions fail; existing tutorial content checks remain green.

- [x] **Step 3: Author only the pilot data**

Add a `casa:[5,15]` focus operation to `fala_0.andar`; add a weapon-slot focus route to the equip step in `fala_2` and ensure the step exposes `Me mostra`; retain the safe inventory-opening route; retain the two focus targets in `treino_golpe`. Do not change task requirements, lesson rewards or completion verbs.

- [x] **Step 4: Regenerate the authored outputs and validate their consistency**

Run: `python -X utf8 tools/configurar_tutorial_salas.py`
Run: `python -X utf8 tools/test_tutorial_conteudo.py`
Expected: generated guide data includes exactly the three approved pilot routes and generation is idempotent.

- [x] **Step 5: Run server and client guide contracts**

Run: `python -X utf8 tools/test_tutorial_guia.py`
Run: `node tools/test_guia_tutorial_cliente.js`
Run: `node tools/test_guia_demonstracao_cliente.js`
Expected: valid operations reach the client, invalid routes are rejected, and only existing server-accepted gameplay events advance the lesson.

### Task 4: Validate the pilot in the game

**Files:**
- No planned code changes; fix only regressions found in Tasks 1–3.

**Interfaces:**
- Consumes: the three generated routes and controller lifecycle from Tasks 1–3.
- Produces: verified pilot behavior before any expansion to additional lessons.

- [ ] **Step 1: Verify inventory and equip**

In an isolated tutorial, advance the inventory route one click at a time, close/reopen the lesson, and equip the acquired weapon through the real inventory controls. Confirm only the server-accepted equip completes the task.

- [ ] **Step 2: Verify map movement**

In 2D and 3D, advance the movement route and move to the marked visible house through mouse, keyboard and gamepad paths available in the current build. Confirm an invalid/hidden target is not revealed and only accepted movement progresses.

- [ ] **Step 3: Verify skill targeting and regression behavior**

Advance the skill and dummy focus stages, then activate and target the dummy manually. Confirm a rejected or canceled action leaves the stage available, a successful action advances the server lesson, and the next demonstration waits for a new click. Confirm keyboard, mouse and gamepad guidance matches live bindings.

- [ ] **Step 4: Review coverage before expansion**

Record any failed path and correct it before authoring additional lessons. Do not expand beyond the three pilot cases until all three pass.

## Handoff

The working tree already contains a first-pass, uncommitted implementation of the controller and inventory/skill demonstrations. Preserve those changes and refine them to match the approved spec; do not reset unrelated modified or untracked files. This plan does not authorize automatic gameplay actions.