# Marcadores cooperativos nas masmorras Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add temporary, party-visible tactical markers to dungeon boards without spending actions or revealing information hidden by fog of war.

**Architecture:** `GameRoom` owns marker state, validates creation, expires markers at round boundaries, and supplies each connected dungeon player only the markers permitted by that player's visibility. Because shared vision is a per-client preference in `localStorage`, the client reports that preference to the server for recipient filtering; this report never grants gameplay visibility or authority. `GS` sends marker actions and receives them in the normal game-state payload. `game.js` owns the category selector, board targeting and shared 2D/3D drawing; `game.css` and `src/lang/interface.js` provide presentation and localization.

**Tech Stack:** Python 3 server (`server.py`), browser JavaScript (`src/gameState.js`, `game.js`), CSS (`game.css`), interface catalog (`src/lang/interface.js`), Python and Node regression scripts under `tools/`.

**Spec:** `docs/superpowers/specs/2026-10-11-marcadores-cooperativos-masmorra-design.md`

## Global Constraints

- MVP is dungeon-only.
- Categories are **Atacar**, **Perigo**, **Investigar** and **Mover**.
- A player has at most one active marker; their next marker replaces it.
- Markers do not consume action, movement or turn and are not saved.
- A marker on an enemy may only target a living, currently visible enemy; a house marker may only target a valid, currently visible house.
- Recipients must not receive marker data that reveals a hidden enemy, position or area.
- Right-click remains monster inspection.
- Mouse, keyboard and gamepad must be supported.
- Marker creation is rate-limited by the server.

## Review Focus

- **Recipient fog of war:** a teammate without current vision must not receive a marker that reveals its target; test recipient-specific filtering for tiles and enemies.
- **Visibility rules:** direct and shared vision, blindness, line-of-sight blockers and remote reveals must match the game's existing visibility rules; test each relevant input.
- **Round boundary:** a marker must survive one full round after creation and expire at the following round transition; test creation immediately before and after `_virada_de_rodada`.
- **Target lifecycle:** killing a marked enemy or removing its owner must clear the marker without leaving a stale icon; test both.
- **Input coexistence:** marking must not trigger a move, attack, skill aim or right-click inspection; test mouse, keyboard and gamepad paths.

---

### Task 1: Add authoritative marker state and validation

**Files:**
- Modify: `server.py` (`GameRoom.__init__`, `GameRoom.handle_*`, `_game_state_payload`, `_virada_de_rodada`, and connection cleanup)
- Test: `tools/test_marcadores_cooperativos.py`

**Interfaces:**
- Produces: `GameRoom.handle_cooperative_marker(connection_pid, category, target_type, target_id=None, pos=None, hero_id=None)`; resolves ownership using `heroi_da_acao`, accepts one of the four categories and exactly one target form (`enemy` with a stable ID, or `tile` with `[x, y]`).
- Produces: `GameRoom.handle_cooperative_vision_preference(connection_pid, enabled)`; stores an ephemeral per-connection preference used only to filter marker delivery.
- Produces: marker records keyed by owner hero ID with `{owner_id, category, target_type, target_id, pos, expires_round}`. Enemy markers store the enemy ID and resolve its current position from authoritative room state.
- Produces: `GameRoom._cooperative_markers_for_pid(pid)` returning a fresh list of only currently eligible markers for that recipient.

- [ ] **Step 1: Write failing server tests** for valid category/target pairs, invalid category, malformed/out-of-bounds/wall tiles, absent/dead/invisible enemies, non-owner attempts, per-owner replacement, one-active-marker limit and the shared-vision preference default/update path.
- [ ] **Step 2: Run the focused test** with `python -X utf8 tools/test_marcadores_cooperativos.py`; confirm the new behavior fails before implementation.
- [ ] **Step 3: Implement the marker store and handler** in `GameRoom`. Resolve the effective hero through the existing action/ownership path; reject malformed or unauthorized requests without changing turn/action state. Set `expires_round = self.round_num + 1`.
- [ ] **Step 4: Add server visibility checks** for the marker creator and each recipient. Mirror the existing client rules in `computeVisionSet`: current hero sight, shared vision when enabled for that recipient, blindness, line of sight, and live remote reveals. Do not use explored history by itself as proof of current visibility. For a multi-tile enemy, require at least one visible occupied tile.
- [ ] **Step 5: Add rate limiting and cleanup**. Accept at most one marker per owner every 250 ms; reject bursts without a noisy gameplay error. Clear a marker when its owner disconnects, its enemy target dies/disappears, or its dungeon instance ends.
- [ ] **Step 6: Run the focused server tests** and confirm each invalid request leaves the marker store and turn state unchanged.
- [ ] **Step 7: Commit Task 1** with `git add server.py tools/test_marcadores_cooperativos.py docs/superpowers/plans/2026-10-11-marcadores-cooperativos-masmorra.md; git commit -m "feat: valida marcadores cooperativos no servidor"`.

### Task 2: Filter markers in the authoritative game-state broadcast

**Files:**
- Modify: `server.py` (`GameRoom.push_state`, `_game_state_payload`, `_virada_de_rodada`)
- Test: `tools/test_marcadores_cooperativos.py`

**Interfaces:**
- Consumes: `GameRoom._cooperative_markers_for_pid(pid)` from Task 1.
- Produces: a `cooperative_markers` array in each recipient's `game_state` payload, filtered for that recipient. Each payload item includes owner, category, target type and either target ID/current target position or tile position.

- [ ] **Step 1: Add failing broadcast tests** with two recipients who have different sight; assert the eligible recipient gets the marker and the ineligible recipient's serialized payload contains no target ID or position.
- [ ] **Step 2: Implement recipient-specific marker payloads** using `broadcast(..., personalize=...)`; preserve all existing shared fields and existing skips for players outside the dungeon. Re-evaluate eligibility on every state broadcast so markers appear/disappear as vision changes.
- [ ] **Step 3: Expire markers at round transitions** in `_virada_de_rodada`, after `round_num` increments. Remove records whose `expires_round < self.round_num`; this keeps a marker through one complete following round and removes it at the next boundary.
- [ ] **Step 4: Run the focused tests** for current sight, shared sight, blindness, remote reveal, owner disconnect, enemy death and round timing.
- [ ] **Step 5: Commit Task 2** with `git add server.py tools/test_marcadores_cooperativos.py; git commit -m "feat: filtra marcadores pela visao do grupo"`.

### Task 3: Add the client command and targeting state

**Files:**
- Modify: `src/gameState.js` (outgoing action method)
- Modify: `game.js` (selector state, HUD actions, board targeting, keyboard/gamepad focus and reporting the local shared-vision preference)
- Modify: `src/lang/interface.js` (Portuguese and English labels/hints)
- Modify: `game.css` (selector and marker visual states)
- Test: `tools/test_marcadores_cooperativos_cliente.js`

**Interfaces:**
- Produces: `GS.createCooperativeMarker(category, targetType, target)` sending `{type: "cooperative_marker", category, target_type, target_id?, pos?}`.
- Produces: `GS.setCooperativeVisionPreference(enabled)` sending `{type: "cooperative_vision_preference", enabled}` when the local preference changes and once when a dungeon game state is first received.
- Produces: a local targeting state in `game.js`, active only while the category selector is open; a valid board selection sends one action and exits targeting mode.

- [ ] **Step 1: Write failing client tests** for action serialization, category validation, cancel behavior, and selection-mode isolation from normal movement/attack/skill handlers.
- [ ] **Step 2: Add `GS.createCooperativeMarker`** beside the existing `GS` action senders and expose it through the module's public API.
- [ ] **Step 3: Report shared-vision preference** from the existing local preference initialization/update paths, including once after a connection enters a dungeon. Do not persist this ephemeral mirror on the server.
- [ ] **Step 4: Add a visible marker control and four-option selector** to the in-game HUD. Use existing focus helpers and `data-gamepad-action` conventions so Tab/Enter and gamepad navigation can select a category and cancel with Escape/B.
- [ ] **Step 5: Add target selection** to the unified tile/enemy click path. During marking mode, only send a valid visible tile or enemy target; consume that click so it cannot also move, attack, or advance a skill aim.
- [ ] **Step 6: Add Portuguese and English strings** for title, four categories, target prompts, invalid target feedback, cancel and rate-limit feedback.
- [ ] **Step 7: Run the focused client tests** and confirm regular board input is unchanged outside marking mode.
- [ ] **Step 8: Commit Task 3** with `git add src/gameState.js game.js game.css src/lang/interface.js tools/test_marcadores_cooperativos_cliente.js; git commit -m "feat: adiciona selecao de marcadores taticos"`.

### Task 4: Draw markers consistently in 2D and 3D

**Files:**
- Modify: `game.js` (`renderMap`, `renderMap3D` and focused drawing helpers)
- Modify: `game.css` if the DOM selector needs shared icon styling
- Test: `tools/test_marcadores_cooperativos_cliente.js`

**Interfaces:**
- Consumes: `GS.gameState.cooperative_markers` from the recipient-specific game-state payload.
- Produces: a shared visibility filter and category-icon renderer used by both board modes. Enemy markers follow the current position of their target; tile markers remain anchored to their tile.

- [ ] **Step 1: Add failing renderer-data tests** for category-to-icon mapping, enemy position updates, dead/missing target removal and recipient visibility filtering.
- [ ] **Step 2: Implement a marker view helper** that ignores expired/invalid data and only returns data already authorized in the recipient's state payload.
- [ ] **Step 3: Draw markers in 2D** after terrain visibility is known and before/above pawn drawing, with a small label/icon that does not cover the pawn or inspector threat areas.
- [ ] **Step 4: Draw markers in 3D** as small floor-anchored sprites/badges that remain readable at the current camera zoom and are disposed when removed.
- [ ] **Step 5: Validate colors and icons** against existing red attack and green movement threat zones; use distinct glyphs and a high-contrast outline so category meaning is not color-only.
- [ ] **Step 6: Run client tests** and manually inspect 2D and 3D boards, including marker replacement, expiry, target death and a recipient who cannot see the target.
- [ ] **Step 7: Commit Task 4** with `git add game.js game.css tools/test_marcadores_cooperativos_cliente.js; git commit -m "feat: desenha marcadores em 2d e 3d"`.

### Task 5: End-to-end multiplayer verification

**Files:**
- Modify: `tools/test_marcadores_cooperativos.py` and `tools/test_marcadores_cooperativos_cliente.js` only if coverage gaps are found

**Interfaces:**
- Consumes: server marker protocol and client selector/renderer from Tasks 1–4.
- Produces: regression coverage for the full behavior across two connected players and both render modes.

- [x] **Step 1: Run server regression:** `python -X utf8 tools/test_marcadores_cooperativos.py` (16 passed).
- [x] **Step 2: Run client regression:** `node tools/test_marcadores_cooperativos_cliente.js` (29 passed).
- [x] **Step 3: Run existing regression tests** with `python -X utf8 tools/test_visao_compartilhada.py`, `python -X utf8 tools/test_nevoa_visao.py`, `node tools/test_monster_inspector.js` and `node tools/test_visao_compartilhada_cliente.js`; all passed (14, 5, inspector checks, 15).
- [ ] **Step 4: Perform a two-player manual smoke test**: not completed; the local browser session stopped at the test account's password validation. Server recipient-filtering and client integration regressions passed, but live 2D/3D multiplayer behavior still needs visual confirmation.
- [x] **Step 5: Commit the implementation** in focused commits after all checks pass; do not include unrelated workspace files.

---

## Dependency order

Task 1 → Task 2 → Task 3 → Task 4 → Task 5. The server state/filtering contract must be stable before UI consumes it; the client targeting state must exist before render and multiplayer smoke tests.
