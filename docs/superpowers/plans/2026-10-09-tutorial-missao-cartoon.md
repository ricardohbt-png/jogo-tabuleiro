# Tutorial como primeira missão Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Execute in the current session after the user approves this plan.

**Goal:** Reorganize the Campo de Treinamento as a short first mission that teaches essential menus and keeps the existing class training as optional follow-up.

**Architecture:** Keep the current map objective and tutorial lesson engine. Author the shared mission in the Portuguese/English tutorial sources and apply map changes through an idempotent script. Reuse the existing `falante` object to carry portrait and scene asset paths to the client; extend the dungeon editor to preserve and edit those fields.

**Tech Stack:** Python tutorial/map authoring, JSON dungeon data, JavaScript client and dungeon editor, CSS, existing image-generation workflow.

**Spec:** `docs/superpowers/specs/2026-10-09-tutorial-missao-cartoon-design.md`

## Global Constraints

- Preserve the Campo de Treinamento map, rules, rewards, saved progress, multiplayer isolation, and `objectives.primary.type == "all_heroes_at_exit"`.
- Keep current lesson IDs when changing existing lessons; give new H/M lessons new IDs so old `tutorial_history` cannot mark them complete prematurely.
- Keep the class-exclusive exercises available and repeatable; do not make them prerequisites for mission extraction.
- Store authored guide text in `tools/tutorial_guia_comum.py`; regenerate `src/lang/tutorial_guia.js` and the dungeon JSON through existing authoring scripts.
- Show M only when the hero has a usable spell; adapt the text for the active input device.
- All new Master-at-Arms images preserve the approved cartoon identity and capelo; scene art contains no embedded text.
- Do not revert the pre-existing local changes in `server.py`; make any required edits there with narrow, contextual patches.
- Do not add or run automated tests unless the user asks for testing; use source review, generated-content inspection, and visual review of the images for this task.

## Review Focus

- A character with no usable spells never receives an impossible M exercise.
- Existing heroes with old `tutorial_history` still receive the newly introduced H/M menu lessons.
- Opening H or M advances only its matching lesson step; unrelated menu actions do not advance it.
- Keyboard, mouse, gamepad, 2D, and 3D layouts keep the board and objective readable while the dialogue is open.
- Saving the map in the dungeon editor preserves `falante.retrato` and `falante.cena` paths.

## Files and Responsibilities

- `tools/tutorial_guia_comum.py` — authoritative localized guide content for the shared mission.
- `tools/aplicar_tutorial_missao.py` — new idempotent patch for mission speech IDs, positions, orders, tasks, requirements, and speaker art metadata.
- `tools/configurar_tutorial_salas.py` — include the new patch in the normal map-authoring pipeline.
- `dungeons/campo_de_treinamento.json` — generated/authored result for the active training dungeon.
- `src/lang/tutorial_guia.js` — generated Portuguese/English step text; never edit by hand.
- `src/guiaTutorial.js` and `game.js` — stable targets for H/M, menu-open step advancement, and image rendering.
- `game.css` — dialogue portrait and scene layout at desktop and narrow widths.
- `tools/editor.js` and `src/lang/editor.js` — edit and round-trip speaker portrait/scene paths.
- `server.py` — only if the dungeon validator needs to constrain new asset paths; `_disparar_fala` already forwards the whole `falante` object.
- `assets/portraits/` — instructor portrait variants.
- `assets/tela de transição/tutorial/` — illustrated mission scenes.
- `CLAUDE.md` — final source-of-truth documentation for the updated tutorial flow and asset fields.

---

### Task 1: Author the shared mission flow

**Files:**
- Create: `tools/aplicar_tutorial_missao.py`
- Modify: `tools/tutorial_guia_comum.py`
- Modify: `tools/configurar_tutorial_salas.py`
- Regenerate: `dungeons/campo_de_treinamento.json`
- Regenerate: `src/lang/tutorial_guia.js`

- [x] **Step 1: Define the mission beats in the shared guide source**

Rewrite the shared opening and the relevant common lessons as six mission beats: briefing, preparation, learn the hero's menus, first combat, confirm the skeleton threat, and extract the party. Preserve the existing objective sentence's mechanics and keep each action in its own guide step.

- [x] **Step 2: Add an idempotent mission-map patch**

Create `aplicar_tutorial_missao(definicao)` in `tools/aplicar_tutorial_missao.py`. It must update existing stable lesson IDs in place, add new `fala_menu_habilidades` and conditional `fala_menu_magias` IDs, retain all class lesson records, and leave the primary objective as `all_heroes_at_exit`. Running the function twice must produce the same authored map.

- [x] **Step 3: Wire the patch into the existing authoring pipeline**

Call the new patch from `tools/configurar_tutorial_salas.py` before serialization. Let the existing guide generator emit `src/lang/tutorial_guia.js`; do not hand-edit generated strings.

- [x] **Step 4: Generate the active map and guide content**

Run `python -X utf8 tools/configurar_tutorial_salas.py` from the repository root. Inspect the resulting `fala` IDs, positions, orders, prerequisites, and localized keys; confirm the class rooms and current rewards remain present.

### Task 2: Teach H and M through the real menus

**Files:**
- Modify: `src/guiaTutorial.js`
- Modify: `game.js`
- Modify: `tools/tutorial_guia_comum.py`
- Regenerate: `src/lang/tutorial_guia.js`

**Interface:**
- `botao:habilidades` resolves to the visible skills-menu entry for the current layout.
- `botao:magias` continues to resolve to the visible spell-menu entry.
- The existing client API `GS.avancarPasso()` reports the menu-open action through the existing informative-step path; no new WebSocket message is introduced.

- [x] **Step 1: Add visible tutorial targets for the skills menu**

Mark the visible H/skills entry points with `data-guia="botao:habilidades"` and teach `GuiaTutorial` to select the visible entry, following the existing visible-element behavior for `botao:magias`.

- [x] **Step 2: Add menu-open completion hooks**

After `abrirMenuHabilidades` or `abrirMenuMagias` opens successfully, advance only when the current tutorial step expects that menu. Do not advance on a key press that was ignored, a closed menu, or a different menu. Keep the current server check that rejects advancement of the final or non-informative step.

- [x] **Step 3: Place H/M before the first combat exercise**

Use the authored H lesson for every hero. Use the M lesson only when the same requirements used by the current usable-spell training identify a spell the hero can cast. Include the equivalent visible control for gamepad and keep R/Esc as optional reference hints.

### Task 3: Create the approved instructor and scene art

**Files:**
- Create: `assets/portraits/mestre_de_armas_briefing.png`
- Create: `assets/portraits/mestre_de_armas_alerta.png`
- Create: `assets/portraits/mestre_de_armas_conclusao.png`
- Create: `assets/tela de transição/tutorial/briefing_guilda.png`
- Create: `assets/tela de transição/tutorial/ameaca_esqueletos.png`
- Create: `assets/tela de transição/tutorial/retorno_guilda.png`

- [x] **Step 1: Generate instructor expression variants**

Use `assets/portraits/mestre_de_armas.png` and `assets/tela de transição/guilda_dos_herois.png` as references. Keep the same recognizable face, dark hair and beard, blue cloak, gold details, and capelo. Generate briefing, alert, and conclusion expressions with transparent backgrounds; do not overwrite the approved base image.

- [x] **Step 2: Generate three tutorial story illustrations**

Create a guild briefing, the party discovering the skeleton threat, and the party returning together. Match the reference's hand-painted cartoon linework and warm palette. Keep all text, signs, objectives, and dialogue out of the images so they remain localized in the UI.

- [x] **Step 3: Review the generated assets visually**

Check that the variants read as the same instructor, retain the capelo, have clean transparency where required, and leave clear composition space for the tutorial panel. Keep the source illustration unchanged.

### Task 4: Render and author portraits/scenes in the dialogue

**Files:**
- Modify: `game.js`
- Modify: `game.css`
- Modify: `tools/editor.js`
- Modify: `src/lang/editor.js`
- Modify: `server.py` only if needed for asset-path validation
- Modify: `dungeons/campo_de_treinamento.json`

**Data shape:**
- `falante.retrato`: optional path under `assets/portraits/`.
- `falante.cena`: optional path under `assets/tela de transição/tutorial/`.

- [x] **Step 1: Preserve and edit the two speaker art fields in the dungeon editor**

Extend the fala panel with localized `retrato` and `cena` path fields. Carry both fields through `loadJSON` and `buildJSON`, while retaining compatibility with old falas that contain only `nome` and `emoji`.

- [x] **Step 2: Render the portrait and scene in the current dialogue window**

Read the optional fields from `msg.falante` in `_mostrarJanelaLicao` and `_mostrarProximaFala`. Use `_assetURL` for local asset resolution. Show the scene and larger portrait in the prologue and mission milestone dialogue; use a compact portrait during action steps; retain the emoji fallback for speakers without art.

- [x] **Step 3: Add responsive styling**

Update `game.css` so images fit the existing prologue and lesson panel, keep the tutorial text and buttons readable, preserve transparency, and do not cover the objective HUD or the highlighted board target on narrow screens.

- [x] **Step 4: Validate authored asset paths**

If `validar_dungeon` does not already constrain the nested fields, accept only local image paths beneath the two approved asset directories and reject traversal or remote URLs. Apply a narrow patch around the `falas` validation in `server.py`, preserving the pre-existing local poison changes.

- [x] **Step 5: Attach the approved art to mission dialogue**

Set the appropriate `falante.retrato` and `falante.cena` on the briefing, skeleton discovery, and conclusion speeches. Use the base portrait for action instructions and existing non-tutorial speakers keep their current emoji-only display.

### Task 5: Document the new authoring contract and review the result

**Files:**
- Modify: `CLAUDE.md`
- Review: all files listed in Tasks 1–4

- [x] **Step 1: Document the shared mission and art metadata**

Record the final mission beats, the conditional M lesson, the optional-class behavior, the `falante.retrato`/`falante.cena` fields, asset locations, and the authoritative generation scripts in `CLAUDE.md`.

- [x] **Step 2: Review source and generated outputs**

Review `git diff --check`, confirm the JSON remains loadable by inspection, verify the generated locale keys match the authored guide, inspect the editor's serialized speaker fields, and visually inspect the final portrait and scene files. Keep unrelated `server.py` changes out of any focused change summary.

## Review Focus Checks

- Mixed party: the M lesson appears only for heroes who meet the current usable-spell requirement; other heroes can finish the common mission.
- Returning hero: newly added H/M IDs are not suppressed by histories for older tutorial lessons; old completed IDs remain honored.
- Menu step: H/M opening advances only the expected informative step, while other menus and ignored shortcuts leave it in place.
- Display modes: the portrait/cena layout remains readable in 2D, 3D, mouse/keyboard, gamepad, and narrow viewports.
- Editor round-trip: old emoji-only speakers and new speakers with both image fields survive load/save without losing `guia` or other dialogue fields.


## Registro de execução

- Implementação feita no checkout atual após autorização do usuário para continuar inline.
- Revisão independente somente leitura: sem achados concretos nos critérios focados.
- Validação estática: `node --check` nos JS alterados; `py_compile` nos scripts Python; JSON carregado e inspecionado; assets conferidos; `git diff --check` sem erros.
- Não foram adicionados nem executados testes automatizados, conforme a instrução de execução vigente.
- Sem inspeção interativa em partida: a legibilidade final em 2D/3D, gamepad e viewport estreita não está confirmada.
- Alterações locais preexistentes de melhorias de veneno em `server.py` foram preservadas.
