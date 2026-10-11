# Diário dos Aventureiros Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an interactive, campaign-shared adventurer diary to the shared refuge room, with mission and important-item history plus the opener's private bestiary knowledge.

**Architecture:** The server owns diary writes and campaign persistence. It sends shared mission/item history with refuge state, and sends the requesting account's bestiary only in a private response when the diary opens. Right-click inspection separately requests the account's allowed knowledge level for the explicitly selected, visible creature; counts and levels never ride in `game_state` broadcasts. The client renders a three-page book; a native book action in the Refuge panel opens it while existing chest and room actions remain intact.

**Tech Stack:** Python WebSocket server, vanilla JavaScript, HTML/CSS, existing account profile bestiary and language dictionaries.

**Spec:** `docs/superpowers/specs/2026-10-11-diario-dos-aventureiros-refugio-design.md`

## Global Constraints

- Mission and important-item history is shared by campaign; bestiary kills/knowledge stays per account.
- Use stable adventure, stage, route-exit and item IDs; resolve user-facing names through localization.
- Record mission completion only after the authoritative `handle_encerrar_missao` validation succeeds.
- Reveal bestiary fields at the same 15/30/50 thresholds in both the diary and right-click monster inspector.
- Preserve the shared chest and private-room interactions and support mouse, keyboard and gamepad.
- Do not invent historical dates or item acquisitions when old saves lack evidence.

## Review Focus

- Legacy campaign save with progress and route discoveries but no diary: migration/reconstruction must avoid fabricated timestamps and duplicate entries.
- Revisited stage or repeated route exit: mission history must remain deduplicated and retain partial route completion.
- Key item later consumed, sold or stored: the diary record must remain and must not award the item again.
- Two accounts with different bestiary counts opening the same shared room: each must receive only their own knowledge.
- Bestiary fields with special handling (resistances, immunities, vulnerabilities, damage reduction) at thresholds 0/15/30/50: no field may reveal early.

---

## File Map

- `server.py`: campaign schema/checkpoints, authoritative mission and key-item event recording, private bestiary response, and canonical bestiary reveal policy.
- `game.js`: diary modal/pages, localized rendering, native Refuge-panel book action, and controls.
- `src/gameState.js`: diary request sender and state/event handling, without DOM or rendering logic.
- `game.css`: responsive book/page presentation.
- `src/lang/interface.js`: diary UI strings in Portuguese and English.
- `tools/test_diario_aventureiros.py`, `tools/test_diario_cliente.js`: focused server and client regression coverage.
- `CLAUDE.md`: record resulting data and protocol contracts after implementation.

## Interfaces Between Tasks

- Server diary storage: `savegame["adventurer_journal"] = {"missions": [], "items": []}`. Mission entry identity is `(adventure_id, stage_index)` with deduplicated `exit_ids` and a `complete` flag; item identity is `item_id`. Entries contain stable IDs and optional confirmed timestamp only.
- Server helper: `GameRoom._diario_registrar_missao(adventure_id: str, stage_index: int, exit_ids: list[str], complete: bool, completed_at: str | None) -> None`; idempotently merges discovered exits and completion.
- Server helper: `GameRoom._diario_registrar_item(item_id: str, acquired_at: str | None) -> None`; idempotently adds an explicitly configured important item.
- Client request: `GS.openAdventurerDiary()` sends `{type: "open_adventurer_diary"}`.
- Client response: private `{type: "adventurer_diary_state", missions: [...], items: [...], bestiary: {...}}`; `bestiary` is account-scoped and never part of a shared room broadcast.
- Client inspector request: `{type: "inspect_monster", monster_id}` after an explicit right-click; server validates visibility and returns only the requesting player's knowledge level in a private `monster_knowledge_state`.
- Existing `refugio_state` gains only shared `adventurer_journal` data. Do not attach bestiary there.

### Task 1: Campaign Journal Schema and Legacy Reconstruction

**Files:**
- Modify: `server.py` (`ensure_campaign_schema`, save/load and `CAMPOS_DO_PONTO`)
- Test: `tools/test_diario_aventureiros.py`

**Interfaces:**
- Produces the normalized storage shape and safe legacy reconstruction defined in “Interfaces Between Tasks.”

- [x] **Step 1: Add failing migration and checkpoint tests**
  - Assert a legacy campaign with no `adventurer_journal` gains empty `missions` and `items` lists.
  - Assert a campaign journal survives savegame round-trip and point/checkpoint save and restore.
  - Assert migration does not alter existing `journal`, route progress or item inventory.
- [x] **Step 2: Run the focused tests and confirm the missing-field failures**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Expected: new migration and checkpoint assertions fail before implementation.
- [x] **Step 3: Add schema normalization and checkpoint persistence**
  - Normalize malformed/missing journal data to the exact shape in “Interfaces Between Tasks.”
  - Add `adventurer_journal` to `CAMPOS_DO_PONTO`; preserve unknown valid entries and sanitize IDs without dropping valid old data.
- [x] **Step 4: Reconstruct safe mission history from existing campaign progress**
  - Read `world_adventure_progress` and `world_adventure_route_progress` using their current stage/exit IDs.
  - Reconstruct completed stages and known exits without timestamps; do not infer unrecorded item history.
  - Test partial alternate-route stages and idempotent repeated migration.
- [x] **Step 5: Run the focused persistence tests**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Expected: migration, legacy reconstruction, deduplication and checkpoint round-trip assertions pass.
- [x] **Step 6: Commit the isolated server schema change**


### Task 2: Authoritative Mission and Important-Item Recording

**Files:**
- Modify: `server.py` (`handle_encerrar_missao`, `_trigger_campaign_scene`, and campaign journal helpers)
- Test: `tools/test_diario_aventureiros.py`

**Interfaces:**
- Consumes: `adventurer_journal` and helpers from Task 1.
- Produces: campaign-shared mission/item history exposed by the refuge payload in Task 4.

- [x] **Step 1: Add failing mission-history tests**
  - Successful confirmed mission completion records adventure ID, stage index, discovered exit IDs and a server timestamp.
  - Failed `handle_encerrar_missao` preconditions (objective incomplete, pending completion false, or required exits missing) add no record.
  - Revisit does not create another completed-stage entry; new required exit is merged and repeated exit is deduplicated.
- [x] **Step 2: Add failing important-item tests**
  - An item ID with an authored `key_item_obtained` campaign-scene trigger is recorded once when the authoritative acquisition event runs.
  - Ordinary item acquisition is not recorded without explicit campaign authoring.
  - Consuming, selling, or storing the item does not remove its diary record or grant another item.
- [x] **Step 3: Run focused tests and confirm event-hook failures**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Expected: mission and key-item recording assertions fail before implementation.
- [x] **Step 4: Implement idempotent registration at authoritative event points**
  - Record a mission only after the existing guards in `handle_encerrar_missao` pass. Preserve route-exit completion semantics; record partial exit discovery from persisted route progress when available.
  - Record an important item when `_trigger_campaign_scene("key_item_obtained", item_id)` receives a valid, explicitly authored event. Store IDs, not localized strings.
- [x] **Step 5: Run mission/item tests, including revisit and multi-exit cases**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Expected: all event, deduplication, no-spoiler and no-reward-duplication assertions pass.
- [x] **Step 6: Commit the authoritative event change**

### Task 3: One Canonical Bestiary Reveal Policy

**Files:**
- Modify: `server.py` (bestiary payload and canonical field-level reveal helper)
- Modify: `game.js` (right-click inspector consumes canonical reveal levels if it currently duplicates rules)
- Test: `tools/test_diario_aventureiros.py`
- Test: `tools/test_monster_inspector.js`
- Test: `tools/test_bestiario_global.py`

**Interfaces:**
- Produces: a canonical reveal representation for a monster and kill count, consumed by both diary and right-click inspection.

- [x] **Step 1: Add failing reveal-policy tests for 0, 15, 30 and 50 kills**
  - At 0 kills, assert only current basic observation (name, HP and AC) is shown.
  - At 15 kills, assert immunities, resistances and vulnerabilities are shown.
  - At 30 kills, assert attacks, damage types, ranges, attributes and saves are added.
  - At 50 kills, assert special abilities and known DCs complete the sheet.
  - Assert a living Bard's `Conhecimento das Lendas` reveals the full sheet independently of count, matching the existing approved rule.
  - Explicitly assert damage reduction is hidden at 0 and shown with the defensive information at 15.
- [x] **Step 2: Run focused tests and inspect current leaks**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Expected: tests identify fields that bypass the current level checks, including the known resistance block if still present.
- [x] **Step 3: Implement a single canonical field-level reveal helper**
  - Keep the established 15/30/50 field grouping above and encode it once in the server policy.
  - Treat Bard full reveal as an alternate knowledge source in the same policy, not a separate UI bypass.
  - Return known fields separately from hidden fields; never send hidden raw values to the client diary payload.
- [x] **Step 4: Make the right-click inspector follow the same policy**
  - Remove client-side shortcuts that reveal fields outside the canonical response.
  - Keep red/green threat visualization consistent with fields the account is allowed to know.
- [x] **Step 5: Run server and inspector tests**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Run: `node tools/test_monster_inspector.js`

Expected: all thresholds, Bard policy, hidden-field privacy and existing inspector behavior pass.
- [x] **Step 6: Commit the canonical bestiary policy**

  - Final privacy correction: remove personalized bestiary counters/levels from every `game_state` broadcast and fetch inspector knowledge only after a private explicit inspection request.

### Task 4: Private Diary Protocol and Refuge Entry Point

**Files:**
- Modify: `server.py` (`_refugio_payload`, `handle_open_refugio`, WebSocket message dispatch)
- Modify: `src/gameState.js`
- No city-scene data change: the Refuge panel is the existing native interaction surface.

- Test: `tools/test_diario_aventureiros.py`
- Test: `tools/test_diario_cliente.js`

**Interfaces:**
- Consumes: shared journal entries and canonical bestiary helper from Tasks 1–3.
- Produces: `GS.openAdventurerDiary()` and private `adventurer_diary_state` response.

- [x] **Step 1: Add failing protocol privacy tests**
  - `refugio_state` includes campaign-shared missions/items but has no bestiary field.
  - Opening the diary sends shared history plus only the requesting account's bestiary to that PID.
  - Non-members, players outside the unlocked refuge, and malformed requests receive no diary payload.
- [x] **Step 2: Add failing Refuge payload and private-response tests**
  - `refugio_state` contains shared journal history and no bestiary.
  - The private diary response goes only to an authorized member and uses that account's knowledge.
- [x] **Step 3: Implement request/response handling and client state**
  - Add the `open_adventurer_diary` handler and private response shape from “Interfaces Between Tasks.”
  - Add client action sender and state update in `src/gameState.js`; keep this module free of DOM/rendering references.
- [x] **Step 4: Add an accessible native book action to the Refuge panel**
  - Add a localized, keyboard/gamepad-accessible book action while preserving existing chest, room and gold actions.
- [x] **Step 5: Run protocol privacy and Refuge regression tests**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Run: `node tools/test_diario_cliente.js`

Run: `python -X utf8 tools/test_refugio.py`

Expected: private payload assertions pass and Refuge chest/room behavior remains intact.
- [x] **Step 6: Commit protocol and Refuge entry-point support**

### Task 5: Three-Page Diary UI and Accessible Controls

**Files:**
- Modify: `game.js`
- Modify: `game.css`
- Modify: `src/lang/interface.js`
- Test: `tools/test_diario_cliente.js`

**Interfaces:**
- Consumes: `GS.openAdventurerDiary()` and `adventurer_diary_state` from Task 4.
- Produces: Refuge book action opens a localized modal with Missions, Important Items and Bestiary pages.

- [x] **Step 1: Add failing client rendering tests**
  - Opening the Refuge book action requests diary state; response renders three navigable pages.
  - Mission page labels route exits and incomplete stages without calling incomplete stages completed.
  - Important item page shows retained records and never triggers item grants.
  - Bestiary page hides unknown monsters and fields not present in the allowed payload.
- [x] **Step 2: Add localized labels and empty/loading/error states**
  - Add Portuguese and English strings for page names, close/back controls, unknown/empty states and Refuge book label.
- [x] **Step 3: Render responsive book pages in `game.js` and `game.css`**
  - Use semantic buttons for page changes and close; trap focus while open and restore focus to the Refuge book action on close.
  - Support mouse, keyboard and gamepad through the existing menu/focus conventions.
  - Keep the UI presentational; no persistence or bestiary threshold logic belongs in `game.js`.
- [x] **Step 4: Connect the Refuge book action and preserve room controls**
  - Activating the book action invokes `GS.openAdventurerDiary()`.
  - Verify shared chest and private room buttons still open their current destinations.
- [x] **Step 5: Run client and localization checks**

Run: `node tools/test_diario_cliente.js`

Run: `python -X utf8 tools/test_refugio.py`

Expected: three pages, empty states, control access and existing room actions pass.
- [x] **Step 6: Commit the diary UI**

### Task 6: Full Regression, Architecture Notes and Review

**Files:**
- Modify: `CLAUDE.md`
- Test: `tools/test_diario_aventureiros.py`
- Test: `tools/test_diario_cliente.js`
- Test: existing city/editor and bestiary focused suites listed below

- [x] **Step 1: Document the final persistence and protocol contract**
  - Record the shared/private boundary, write events, stable identifiers and reveal thresholds in `CLAUDE.md` after implementation matches this plan.
- [x] **Step 2: Run all focused diary and neighboring regressions**

Run: `python -X utf8 tools/test_diario_aventureiros.py`

Run: `node tools/test_diario_cliente.js`

Run: `python -X utf8 tools/test_roundtrip_editor.py`

Run: `node tools/test_monster_inspector.js`

Expected: all commands exit successfully; no changed fixtures outside diary and Refuge-panel behavior.
- [x] **Step 3: Inspect the whole diff and verify scope**
  - Confirm no bestiary content enters shared broadcasts, no ordinary item is recorded, and no existing refuge interaction was replaced.
- [x] **Step 4: Commit architecture notes and final regression adjustments**


