# Portão levadiço Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the native portcullis so the map author can select its width by dragging across a straight run of compatible `DOOR` tiles, while preserving one shared gate state and the existing mechanics.

**Architecture:** Keep `door_styles` keyed by the group's anchor and add `portcullis_groups`, mapping that anchor to every occupied `DOOR` coordinate. An absent group entry means a legacy one-cell portcullis. The server owns one raised/lowered state per anchor and resolves blocking, crush, and escape across the group's span; the editor and client use the same span for authoring, input, movement, visibility, and continuous rendering.

**Tech Stack:** Python `server.py`, Three.js and 2D canvas in `game.js`, `src/gameState.js`, dungeon editor in `tools/editor.js`, Blender Python assets, localization modules.

**Spec:** `docs/superpowers/specs/2026-10-30-portao-levadico-design.md`

## Global Constraints

- A portcullis group covers one or more straight, contiguous native `DOOR` tiles; `door_styles["anchor_x,anchor_y"] = "portao_levadico"` identifies it.
- `portcullis_groups["anchor_x,anchor_y"]` stores the group's ordered list of `[x, y]` tiles; absent entries preserve legacy one-tile portcullises.
- Raising or lowering requires an adjacent hero and costs the principal action.
- Lowering with a creature on the threshold triggers Reflexos CD 13: success takes half of 4d6 physical damage and moves to a side; failure takes 4d6 and becomes trapped.
- Escape uses the next principal action and a Força CD 16 check; success moves the creature to a free side with no extra damage. Failure causes 1d6 physical damage once that round and leaves it trapped for another attempt.
- Door operations affect all creatures on the threshold, regardless of allegiance; no collision damage is added when a forced move is blocked.
- Lowering an already opened gate blocks movement and line of sight without relocking/re-hiding the room or returning its monsters to dormancy.
- Do not add or run automated test suites unless the user asks; preserve the checkout's unrelated local changes.

## Review Focus

- **Room and condition behavior:** the first raise honors locks and `door_conditions`; later toggles do not re-hide the room or reset monsters. Review Task 6 against `handle_open_door` and `_is_closed_door`.
- **Editor span validity:** gaps, non-`DOOR` tiles, mixed orientations, conflicting ownership, malformed lists, or overlapping groups cannot partially save. Review Task 5's editor round trip and Task 6's server validation.
- **Legacy and group state:** missing `portcullis_groups` means one tile; toggling any member changes exactly one group's anchor state. Review Task 6's normalization and photo/snapshot serialization.
- **Footprint and escape:** a large creature touching multiple tiles receives one crush; displacement uses a legal footprint on either side, and blocked exits add no collision damage. Review Task 6's target deduplication and exit validation.
- **Client consistency:** every group tile shares passability, visibility, interaction, and one continuous raised/lowered visual on both axes. Review Task 7's state helpers, input paths, and rendering.

## Files and Responsibilities

- `tools/create_portao_levadico.py`, `assets/objetos/portao_levadico.blend`, and raised/lowered PNG/GLB variants: create and export the visual asset.
- `tools/editor.js`: drag-select a straight run of compatible native door tiles, author `door_styles` and `portcullis_groups`, and preserve the group through save/load.
- `server.py`: validate/hydrate the group span, normalize legacy one-tile gates, store raised/lowered and trapped state per anchor, enforce actions, resolve footprint-aware crush/escape, and serialize state.
- `src/gameState.js`: expose the group tiles and anchor, derive passability/visibility, target actions, and legal exits from one shared span.
- `game.js`: render one continuous raised/lowered gate in 2D/3D and route clicks, keyboard, and gamepad actions from any group tile to its anchor.
- `src/lang/interface.js` and `src/lang/narracao.js`: localize interaction, save, trapped, escape, and damage messages.
- `CLAUDE.md`: document the native gate data/state contract and damage/escape rules.

## Tasks

### Task 1: Create raised/lowered gate assets

**Files:**
- Create: `tools/create_portao_levadico.py`
- Create: `assets/objetos/portao_levadico.blend`
- Create: `assets/objetos/portao_levadico_baixado.png`, `portao_levadico_baixado.glb`
- Create: `assets/objetos/portao_levadico_levantado.png`, `portao_levadico_levantado.glb`

- [x] Model a castle portcullis that fits within one `DOOR` tile, with iron bars, crossbars, and side rails; preserve the same origin and axis for both states.
- [x] Create lowered and raised state variants and transparent orthographic PNG previews; save an editable Blender source and export both GLBs.
- [x] Inspect previews for orientation, tile fit, transparency, and readability at board scale; confirm each GLB imports in Blender.

### Task 2: Author the native door style

**Files:**
- Modify: `server.py` dungeon validation/loading and door serialization
- Modify: `tools/editor.js` door selection, save, and load

- [x] Add optional `door_styles` map keyed by `"x,y"`; accept only `portao_levadico` and reject coordinates that are not `DOOR` tiles.
- [x] Load, snapshot, and serialize the style without changing legacy maps where `door_styles` is absent.
- [x] Add an editor control on a selected `DOOR` to choose ordinary door or portcullis; retain existing rotation and room/condition settings.
- [x] Ensure editor save/load round-trips the style and does not add the gate decoration as a separate floor object.

### Task 3: Implement authoritative operation, damage, and escape

**Files:**
- Modify: `server.py` door helpers, action handler, turn/escape processing, and photo fields
- Modify: `src/gameState.js` door-state derivation and targeting

**Interfaces:**
- Consumes: `door_styles` and rotation from Task 2; gate asset state names from Task 1.
- Produces: gate state keyed by `"x,y"`; a `toggle_portcullis(tx, ty)` action; a trapped status containing the gate coordinate; automatic Força attempt at the trapped creature's next turn, consuming its principal action.

- [x] Track which authored portcullises are raised; initialize them from native closed/open status, persist the state in dungeon photos, and include it in `game_state`.
- [x] Require the active hero to be adjacent and have their principal action available when raising/lowering. On first opening, preserve native room unlock, condition, reveal, and monster-awakening rules; reopening after a later closure must not reset those effects.
- [x] When lowering onto each living creature on the threshold, roll Reflexos CD 13. Success applies half of the rolled 4d6 physical damage and moves the target to a free tile on either side. Failure applies full 4d6 and stores a trapped state linked to this gate.
- [x] Make the trapped creature spend its next principal action on Força CD 16. Success clears the trapped state and moves it one square to a free side; failure leaves it trapped and deals 1d6 physical damage once in that round. Permit another escape attempt only on the next principal action.
- [x] Keep a closed gate blocking passage and line of sight even after its room was opened. Use the existing forced-movement collision rules; do not add collision damage or apply the initial crush twice.

### Task 4: Integrate board controls, visuals, and documentation

**Files:**
- Modify: `game.js` 2D/3D door rendering, input dispatch, and gamepad prompt
- Modify: `src/lang/editor.js`, `src/lang/interface.js`, `src/lang/narracao.js`
- Modify: `CLAUDE.md`

- [x] Render ordinary doors unchanged; render each gate in its lowered or raised variant from authoritative state in 2D and 3D.
- [x] Make an adjacent click/keyboard/gamepad action operate an open or closed portcullis; keep standard-door `open_door` behavior unchanged.
- [x] Localize the editor style name, interaction prompts, trapped condition, Reflexos result, Força escape result, and 1d6 failed-attempt damage.
- [x] Document the map field, saved runtime state, action cost, CDs, damage, escape timing, and room-reveal behavior.
- [x] Run Python/JavaScript syntax checks and inspect the asset and focused diffs. Do not run automated test suites unless requested.

### Task 5: Author variable-width portcullis groups in the editor

**Files:**
- Modify: `tools/editor.js` door authoring, pointer drag selection, validation, save, and load
- Modify: `server.py` dungeon definition validation and authored map hydration
- Test: none unless the user asks for tests or verification; perform focused code review only in this task

**Interface:**
- Authored data: `door_styles[anchorKey] = "portao_levadico"` and `portcullis_groups[anchorKey] = [[x1,y1], ...]` in one canonical straight span. Sort members by `(y,x)`; the first member is the stable anchor. A missing `portcullis_groups[anchorKey]` means `[anchor]` for legacy maps.
- Consumes: native `DOOR` tiles, `door_orientations`, room door ownership, and `door_conditions`.
- Produces: a validated group with a stable anchor; dragging over a span creates the group only if every tile is `DOOR`, contiguous, aligned, orientation-compatible, and owned by the same doorway/condition. Canonical `(y,x)` ordering makes a reversed drag produce the same anchor.

- [x] Add an editor drag mode for selecting a straight `DOOR` span; dragging off-axis, across a gap, or across incompatible doors leaves the authored map unchanged and shows the existing validation feedback.
- [x] Save/load `portcullis_groups` alongside `door_styles`; selecting a single tile continues to serialize as the legacy one-cell form.
- [x] Validate group membership and anchor uniqueness in the editor and server; reject malformed, overlapping, out-of-grid, or non-door spans.
- [x] Inspect save/load paths to confirm groups survive editor round trips without splitting state or changing legacy maps.

### Task 6: Resolve server mechanics over the whole span

**Files:**
- Modify: `server.py` portcullis helpers, action handler, save/photo serialization, and trapped state

**Interface:**
- Produces: `_portcullis_tiles(anchor: tuple[int, int]) -> tuple[tuple[int, int], ...]`, returning the authored span or the legacy singleton; `_portcullis_anchor(tile: tuple[int, int]) -> tuple[int, int] | None`, resolving any member to its controlling anchor.
- State remains `portcullis_raised` as a list of anchor coordinates; trapped creatures continue to store the anchor in `portao_preso`.

- [x] Normalize old and grouped definitions through the two helpers; validate that each span is straight, contiguous, in-bounds, and consists only of compatible `DOOR` tiles.
- [x] Make a toggle request at any group tile resolve and mutate only the group's anchor state; preserve the current adjacency and principal-action requirements.
- [x] Make lowering inspect every group tile and every living entity footprint, deduplicate targets by entity identity, then apply the agreed Reflexos CD 13 / 4d6 once per creature.
- [x] For success displacement and Força CD 16 escape, derive before/after squares for the creature's lane and validate the complete creature footprint; preserve 1d6 once on a failed escape attempt and no blocked-exit collision damage.
- [x] Persist and snapshot anchors for grouped gates; retain legacy singleton `portcullis_raised` hydration.

### Task 7: Make client navigation and rendering use the shared span

**Files:**
- Modify: `src/gameState.js` door group, click resolution, pathfinding, and occupancy helpers
- Modify: `game.js` door rendering, mouse/key/gamepad dispatch, and visual signatures/cache

**Interface:**
- Consumes: `door_styles`, `portcullis_groups`, and `portcullis_raised` from the server snapshot.
- Produces: group-aware door helpers that return the anchor and tile span; any member tile resolves to one `toggle_portcullis` action addressed to the anchor.

- [x] Make both 2D and 3D passability/line-of-sight treat every member tile as closed or open together; pathfinding cannot cross only part of a lowered span.
- [x] Route mouse, keyboard, and gamepad interaction from any span tile to the same anchor without offering duplicate independent actions.
- [x] Render the raised or lowered model as a single continuous gate centered on the span and scaled along its long axis; rotate consistently for horizontal and vertical spans.
- [x] Review gate visibility/state refresh paths and preserve the ordinary door renderer.

### Task 8: Update localized editor guidance and system documentation

**Files:**
- Modify: `src/lang/editor.js`, `src/lang/interface.js`, `src/lang/narracao.js` only if new user-facing messages are needed
- Modify: `CLAUDE.md`

- [x] Add concise editor guidance for drag-selecting the gate width and explain why invalid spans are rejected.
- [x] Document the `portcullis_groups` anchor/span contract, singleton fallback, shared runtime state, footprint-aware crush, and continuous visual behavior.
- [x] Review the focused implementation paths and preserve the established gate mechanics outside multi-tile handling.

## Handoff Notes

- Implementation is expected to remain in the current checkout to preserve its substantial unrelated local changes.
- This plan extends the already implemented single-tile gate; preserve all unrelated worktree changes.
- A whole-board live combat scenario and automated tests are not part of this plan unless the user separately asks for verification; report that limit clearly after implementation.
