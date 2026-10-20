# Ignus Fatus e Fata Morgana Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sell both illusion items and implement their authoritative creation, movement, monster lure, expiration, and visual presentation.

**Architecture:** Keep illusions in a room-local temporary collection, separate from players and monsters. The server validates item use and movement, exposes active illusions in `game_state`, and integrates them into monster perception and target selection; `game.js` handles tile targeting, rendering, and movement input.

**Tech Stack:** Python `server.py`, WebSocket game protocol, `city_shops.json`, browser JavaScript in `game.js`, generated item localization, Python and Node regression scripts.

**Spec:** `docs/superpowers/specs/2026-10-18-ignus-fatus-fata-morgana-design.md`

## Global Constraints

- Ignus Fatus costs 45 coins, uses a bonus action, lasts 2 rounds, and stays stationary.
- Fata Morgana costs 120 coins, uses a bonus action, lasts 4 rounds, and receives at most one movement order of up to 6 tiles at the start of its owner's turn before hero actions.
- Both illusions spawn on a free visible tile within 6 tiles of the owner; invalid uses consume neither item nor bonus action.
- A hero may have only one active illusion; a second use is rejected before consumption.
- Illusions are temporary, separate entities with no HP, attacks, interactions, or movement blocking, and are excluded from campaign saves.
- Perceiving automatic monsters prioritize and pursue an illusion; manually controlled monsters remain under Master control.
- The first monster attack attempt dissipates the illusion without damage and ends that monster's turn.
- Expiration or dissipation removes the illusion and lets monsters resume normal target search.
- Use `assets/itens/ignus_fatus.png` and `assets/itens/fata_morgana.png`; do not generate replacement artwork.
- Keep item catalog names and descriptions localized in Portuguese and English and keep `city_shops.json` stock aligned with the merchant catalog.

## Review Focus

- An invalid, occupied, or out-of-range creation tile must not consume the item or bonus action; test each rejection.
- A second active illusion must not consume the second item or bonus action; test both item variants.
- An illusion outside a monster's perception or behind blocking line of sight must not attract it; test both range and occlusion.
- An illusion that expires or is attacked must leave no target or last-seen memory that diverts the next monster turn; test cleanup and normal retargeting.
- Fata Morgana movement must obey the 6-tile/path rules and not debit hero movement; test rejected paths, a valid move, and unchanged hero movement.

---

### Task 1: Add merchant catalog entries and authoritatively create illusions

**Files:**
- Modify: `server.py` — `SHOP_MERCHANT`, bonus-action effect allowlist, `GameRoom.handle_use_item`, room state, and item-use message dispatch.
- Modify: `city_shops.json` — add both IDs to merchant stock.
- Modify: `src/lang/catalogo.js` — generated item names/descriptions with English translations.
- Modify: `src/lang/narracao.js` — bilingual activation narration for the two effects.
- Modify: `src/lang/erros.js` — bilingual message when the owner already has an active illusion.
- Modify: `tools/editor_catalog.js` — regenerate the editor catalog from `server.py`.
- Create: `tools/test_ignus_fatus.py` — catalog, stock, purchase/use validation, active limit, duration, and cleanup tests.

**Interfaces:**
- `handle_use_item(pid, item_id, ..., target_pos=None)` accepts an optional target tile for these effects; the WebSocket dispatcher forwards `target_pos`.
- The room owns an ephemeral `illusions` mapping keyed by stable illusion ID. Each value contains `id`, `owner_pid`, `room_id`, `kind`, `pos`, `created_round`, and `expires_round`.
- `game_state` exposes active illusions as an `illusions` array; this task may initially test the payload without rendering it.

- [x] **Step 1: Write failing tests** for the 45/120 catalog prices, icons and effects; stock in merchant allowlists; valid creation and bonus-action consumption; rejection before consumption for wrong turn, missing item, occupied/out-of-range/occluded tile, one-active-per-owner, and expiring after 2/4 rounds.
- [x] **Step 2: Run `python -X utf8 tools/test_ignus_fatus.py`** and verify the new cases fail for the missing catalog and behavior.
- [x] **Step 3: Implement catalog, stock and authoritative use** in the listed files. Validate all failure conditions before consuming a bag item or bonus action; create an ephemeral entity with the spec's exact duration and expose it in `game_state`.
- [x] **Step 4: Run `python -X utf8 tools/test_ignus_fatus.py`** and verify every catalog, stock, validation, and lifecycle assertion passes.
- [x] **Step 5: Run `python -X utf8 tools/gerar_vocabulario.py`**, fill the generated English names and descriptions in `src/lang/catalogo.js`, run `python -X utf8 tools/export_catalog.py`, and run `python -X utf8 tools/test_vocabulario.py` plus `python -X utf8 tools/test_export_catalog.py`.

### Task 2: Integrate monster perception, lure behavior, and Fata Morgana movement

**Files:**
- Modify: `server.py` — `_alvos_hostis_para_monstros`, `_alvos_visiveis_para_monstro`, `_monster_target_score`, monster turn resolution, AI last-seen cleanup, round expiry, and WebSocket dispatch for illusion movement.
- Modify: `tools/test_ignus_fatus.py` — AI targeting, occlusion/range, movement, attack, and cleanup regressions.

**Interfaces:**
- Add `async def handle_move_illusion(self, pid, illusion_id, target_pos=None)`; it validates that the current player owns an active Fata Morgana, that the hero has not begun movement/actions this turn, and that no order was already made this round. A null destination skips the order; otherwise the server computes a legal path of at most 6 tiles.
- Store the last movement-order round on the illusion so repeated requests cannot exceed one order per owner turn.
- Automatic monster turns consider visible illusions, prioritize them over heroes, move toward them using existing monster pathing, and dissipate them before normal attack resolution when in attack range.
- Removing an illusion clears AI references to its ID so it cannot remain a last-seen target.

- [x] **Step 1: Write failing tests** for no attraction outside perception/line of sight, priority over visible heroes, no override for manual monsters, a single movement order per round, rejection after hero movement/action, skip, movement capped at 6 legal tiles, no change to hero `moves_left`, an attack attempt dissipating without damage and ending the monster turn, and normal retargeting after removal.
- [x] **Step 2: Run `python -X utf8 tools/test_ignus_fatus.py`** and verify these AI and movement cases fail before implementation.
- [x] **Step 3: Implement AI integration and `handle_move_illusion`** using existing perception, path, room, and attack-range helpers. Remove expired/dissipated illusion references from monster target memory.
- [x] **Step 4: Run `python -X utf8 tools/test_ignus_fatus.py`** and verify all AI, movement, attack, and cleanup assertions pass (44/44).

### Task 3: Add tile targeting, 2D/3D rendering, and movement controls

**Files:**
- Modify: `game.js` — item placement preview, illusion selection and destination input, 2D drawing, 3D mesh lifecycle, and state cleanup.
- Create: `tools/test_ignus_fatus_cliente.js` — client selection/render lifecycle tests using the repository's existing Node test style.

**Interfaces:**
- `useItem` enters an illusion-placement mode before sending `use_item` with `{target_pos: [x, y]}`; the UI highlights free tiles within range and line of sight and cancels without sending a use request.
- At the start of the owner's turn, the UI offers to move or leave the Fata Morgana still. A valid destination sends `{type: "move_illusion", illusion_id, target_pos}`; skipping sends a null `target_pos`. The server recomputes and validates the path and closes the order window when the hero begins to move or act.
- `game_state.illusions` drives both 2D and 3D visuals; the Ignus Fatus uses reduced opacity, and Fata Morgana uses the more solid item art.

- [x] **Step 1: Write failing client tests** for placement activation/cancel, valid-tile filtering, use payload, Fata Morgana selection/movement destination payload, rendering from `game_state.illusions`, and removing visuals/selections on dissipation or expiry.
- [x] **Step 2: Run `node tools/test_ignus_fatus_cliente.js`** and verify the new interaction tests fail before implementation.
- [x] **Step 3: Implement placement and movement modes** in `game.js`, including a move-or-skip prompt at the owner's turn start, pointer, keyboard, and gamepad paths, while keeping the hero's own move budget independent.
- [x] **Step 4: Implement and clean up the illusion visuals** in 2D and 3D using the existing PNG assets and the style of existing board actors.
- [x] **Step 5: Run `node tools/test_ignus_fatus_cliente.js`** and verify selection, payload, rendering, and cleanup assertions pass (9/9).

### Task 4: Verify the complete feature in the game flow

**Files:**
- No new source files; update `CLAUDE.md` only if final behavior or regression commands changed during integration.
- Modify: `CLAUDE.md` — record the authoritative behavior and final regression commands after the complete feature passes.

**Interfaces:**
- The feature must work through the real merchant, inventory, turn, monster AI, and board rendering flows, not only direct Python method calls.

- [x] **Step 1: Run `python -X utf8 tools/test_ignus_fatus.py` and `node tools/test_ignus_fatus_cliente.js`.** Result: 45/45 server checks and 10/10 client checks passed.
- [x] **Step 2: Run `python -X utf8 tools/test_vocabulario.py` and `python -X utf8 tools/test_export_catalog.py`.** Result: 38/38 and 23/23 passed; the lamp and Ether Chalice regression suites also passed (11/11 and 10/10).
- [ ] **Step 3: Start a local game and verify** both items can be bought; the player can place each on a valid tile; Ignus Fatus stays still; Fata Morgana moves before its owner's actions; an automatic monster pursues the illusion; an attack dissipates it without hurting a hero; and after expiration/dissipation the monster resumes normal targeting. The local browser reached the login screen; completing this flow would require creating or using a test account, so it was not run.
- [ ] **Step 4: Verify keyboard and gamepad can select/cancel placement and issue or skip Fata Morgana movement.** The shared input paths are covered by client checks, but live keyboard/gamepad control was not exercised because the local game stopped at login.
- [x] **Step 5: Review `git diff` for unrelated changes and confirm the tracked state contains only this feature, its tests, and its spec/plan documentation.** Removed an incidental generated dungeon-editor comment change; the remaining diff is scoped to the feature.
