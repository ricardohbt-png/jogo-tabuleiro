# Cintos de Consumíveis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two equipable belts whose own pockets stack eligible consumables, preserve contents with the belt, and integrate collection, inventory actions, merchant sales, and authored dungeon loot.

**Architecture:** Keep pocket data on each belt item as `utility_belt_slots`, with the server validating all transfers, acquisition routing, and consumption. The existing inventory modal renders pockets for equipped belts; item loot serialization in the dungeon editor preserves optional preloaded pockets.

**Tech Stack:** Python game server and its `tools/test_*.py` suites; browser JavaScript in `src/gameState.js`, `src/ui/inventoryModal.js`, `game.js`, and `tools/editor.js`; existing localization and catalog export pipeline.

**Spec:** [../specs/2026-10-06-cinto-de-utilidades-design.md](../specs/2026-10-06-cinto-de-utilidades-design.md)

## Global Constraints

- Item IDs: `cinto_utilidades` (80 moedas, 4 bolsos) and `cinto_com_bolsos` (30 moedas, 2 bolsos); both use `assets/itens/cinto_e_bolsos.png`.
- A character can equip up to two belts in `item1` and `item2`; each belt has its own pockets and capacity.
- Each pocket contains one eligible item ID and 1–4 units; supported groups are throwables/bottled effects, poison vials, and potions.
- Ineligible items include weapons, equipment, ammunition, scrolls, and all other item groups.
- Manual movement transfers one unit; server validation must be atomic and authoritative.
- Acquisition routing searches equipped belts in `item1`, then `item2` order, before using the normal bag.
- Contents remain on the belt when unequipped, dropped, looted, saved, and loaded; unequipped contents are inaccessible.
- Pocket data stays in the belt item's serializable `utility_belt_slots` field; old belt instances without it behave as empty.
- Preserve existing bag behavior and use/throw effects except for recognizing a belt pocket as the source and decrementing its quantity on successful consumption.
- The inventory uses its existing modal, with brown pockets, smaller icons, normal-size hit areas, quantity badges, and accessible existing interactions.

## Review Focus

- **Malformed client pocket coordinates, stale gear slot, or invalid quantity:** server rejects the request without changing either source; test in Task 2.
- **Two copies of the same item in one belt, including a swap that would create a duplicate stack:** reject without item loss or duplication; test in Task 2.
- **Full bag after all belt pockets are unavailable:** acquisition fails and the source chest, decor, ground, or merchant purchase remains unchanged; test in Task 2.
- **Belt removed, swapped, or dropped between render and use/throw request:** stale source is rejected and does not consume another item's stack; test in Task 3.
- **Legacy or preloaded belt payload with missing, extra, or invalid pockets:** normalize to the belt's fixed capacity and preserve valid contents through editor round-trip; test in Tasks 2 and 5.

---

### Task 1: Register the belt items and shared presentation

**Files:**
- Modify: `server.py` (`SHOP_MERCHANT`, item catalog and dungeon loot catalog inputs)
- Modify: `src/gameState.js` (`CATALOGO_ITENS`)
- Modify: `game.js` (`itemIconHTML`)
- Modify: `src/lang/*` (item names, descriptions, and UI messages following existing locale conventions)
- Test: `tools/test_cinto_utilidades_catalogo.py` (new)

**Interfaces:**
- Produces item IDs `cinto_utilidades` and `cinto_com_bolsos`, with `item_slot: "item"`, prices 80 and 30, and explicit shared icon path `assets/itens/cinto_e_bolsos.png`.
- Descriptions state pocket count, four units per pocket, item grouping, and that contents require the belt to be equipped.
- Adding both merchant entries must make them available through the existing dungeon item catalog/export pipeline.

- [ ] **Step 1: Write failing catalog tests**
  - Assert both server merchant definitions have exact IDs, prices, item category, and shared icon.
  - Assert generated dungeon loot catalog includes both IDs and client catalog exposes localized name/description and icon metadata.
- [ ] **Step 2: Run `python -X utf8 tools/test_cinto_utilidades_catalogo.py` and confirm the new assertions fail.**
- [ ] **Step 3: Register the two item definitions and extend `itemIconHTML(item, fallbackEmoji)` to resolve their shared image.**
- [ ] **Step 4: Run `python -X utf8 tools/test_cinto_utilidades_catalogo.py` and `python -X utf8 tools/test_export_catalog.py`; confirm both pass and generated catalog contains both IDs.**
- [ ] **Step 5: Commit only the catalog, icon, locale, and test files with `feat: adiciona cintos ao catalogo`.**

### Task 2: Implement authoritative pocket storage, routing, and movement

**Files:**
- Modify: `server.py` (belt helpers, acquisition routing, equip/unequip, drop and loot paths)
- Test: `tools/test_cinto_utilidades.py` (new)
- Reference tests: `tools/test_roteamento_itens.py`, `tools/test_equipar.py`

**Interfaces:**
- `GameRoom._utility_belt_capacity(item: dict) -> int`: returns 4 for `cinto_utilidades`, 2 for `cinto_com_bolsos`, otherwise 0.
- `GameRoom._normalize_utility_belt(item: dict) -> dict`: returns the same belt item with exactly its model's pocket count; retain valid eligible stacks and treat missing/invalid entries as empty.
- `GameRoom._is_utility_belt_item(item: dict) -> bool`: true only for the two registered belt IDs.
- `GameRoom._is_utility_belt_eligible(item: dict) -> bool`: true only for approved throwable/bottled, poison-vial, and potion items.
- `GameRoom.handle_move_utility_belt_item(pid, data) -> bool`: accepts `{direction: "to_belt"|"to_bag", gear_slot: "item1"|"item2", pocket_index: int, bag_index: int}`; returns false and leaves state unchanged on invalid operation.
- WebSocket dispatch for `move_utility_belt_item` calls `handle_move_utility_belt_item(pid, msg)`.
- The movement handler transfers one unit, applies the approved stack/swap rules, and emits the normal inventory state update on success.
- `GameRoom._route_acquired_item(p, item)` checks eligible equipped belt stacks and free pockets in the specified order before the existing bag/rescue-equip routing; retain its existing return contract.

- [ ] **Step 1: Add failing tests** for normalization and legacy empty belts; capacities 4/2; eligibility allow/deny; two mixed equipped belts; first incomplete stack then first empty eligible pocket; same ID independent stacks across belts; bag fallback; and rejection when bag is full without consuming the source.
- [ ] **Step 2: Add failing movement tests** for one-unit transfer each way, equal stack to four, full-stack rejection, single-unit swap, multi-unit swap rejection, duplicate-ID rejection, full bag rejection, malformed pocket/index/quantity, and unchanged state after every rejected request.
- [ ] **Step 3: Run `python -X utf8 tools/test_cinto_utilidades.py` and confirm the new behavior fails.**
- [ ] **Step 4: Implement the specified helpers and `handle_move_utility_belt_item`; initialize/normalize belts on equip and preserve the complete item dictionary through unequip, drop, pickup, chest, and decor paths.**
- [ ] **Step 5: Run `python -X utf8 tools/test_cinto_utilidades.py`, `python -X utf8 tools/test_roteamento_itens.py`, and `python -X utf8 tools/test_equipar.py`; confirm no normal acquisition or equipment regression.**
- [ ] **Step 6: Commit the server changes and tests with `feat: adiciona armazenamento autoritativo aos cintos`.**

### Task 3: Use and throw items from equipped belt pockets

**Files:**
- Modify: `server.py` (`handle_use_item`, `handle_throw_item`, message dispatch, exact source consumption)
- Modify: `src/gameState.js` (use/throw message builders)
- Test: `tools/test_cinto_utilidades_uso.py` (new)
- Reference tests: `tools/test_projeteis.py` and existing use-item tests

**Interfaces:**
- Extend `handle_use_item(pid, item_id, target_id=None, source="bag", gear_slot=None, pocket_index=None)`; existing callers retain bag behavior.
- `handle_throw_item(pid, data)` accepts optional `source`, `gear_slot`, and `pocket_index` fields while preserving the current bag request format.
- `GS.useItem(id, sourceInfo)` and `GS.throwItem(id, targetId, targetPos, sourceInfo)` serialize belt coordinates only when `sourceInfo` specifies `{source: "utility_belt", gearSlot, pocketIndex}`.
- Belt consumption verifies the named equipped slot still contains a belt and the named pocket still contains the requested item ID; decrement exactly one only at the existing successful-consumption point.

- [ ] **Step 1: Write failing tests** for use and throw from either equipped belt; one-unit decrement on success; zero consumption on existing rejection paths; empty pocket cleanup; rejection of unequipped/stale belt, invalid pocket, and mismatched item ID; and unchanged bag source semantics.
- [ ] **Step 2: Run `python -X utf8 tools/test_cinto_utilidades_uso.py` and confirm the new belt-source cases fail.**
- [ ] **Step 3: Extend the authoritative handlers and dispatchers with optional source coordinates, keeping consumption adjacent to existing bag-removal points.**
- [ ] **Step 4: Run `python -X utf8 tools/test_cinto_utilidades_uso.py` and `python -X utf8 tools/test_projeteis.py`; confirm throwing from bags still works.**
- [ ] **Step 5: Commit server and client action changes with `feat: permite usar consumiveis dos cintos`.**

### Task 4: Render and operate equipped pockets in the inventory modal

**Files:**
- Modify: `src/ui/inventoryModal.js` (styles, belt sections, actions, drag/drop, focus and tooltips)
- Modify: `src/gameState.js` (expose `moveUtilityBeltItem` action)
- Modify: `game.js` (route belt use/throw actions through existing controls)
- Test: `tools/test_cinto_utilidades_cliente.js` (new; follow existing source-level client test conventions)

**Interfaces:**
- `GS.moveUtilityBeltItem(direction, gearSlot, pocketIndex, bagIndex)` sends `move_utility_belt_item` with those exact fields.
- Inventory sections read only equipped `player.gear.item1` and `player.gear.item2`; each section renders model capacity from `utility_belt_slots` normalized to the model's fixed capacity.
- Pockets use brown styling, smaller item art within a standard clickable area, stack quantity badges, and the existing selection, tooltip, drag/drop, keyboard/touch, use, and throw affordances.
- Bag-to-belt and belt-to-bag drops invoke the server movement action; client state is updated only from the synchronized server response.

- [ ] **Step 1: Add failing client assertions** for equipped-only sections, 4/2 pockets, brown classes, compact icon sizing with unchanged hit target, count badge, and exact transfer/use/throw protocol payloads.
- [ ] **Step 2: Run `node tools/test_cinto_utilidades_cliente.js` and confirm the expected missing selectors/actions fail.**
- [ ] **Step 3: Implement pocket rendering and interaction using the existing inventory modal's selection, drag/drop, tooltip, and item action patterns.**
- [ ] **Step 4: Run `node tools/test_cinto_utilidades_cliente.js`; inspect the modal at desktop and narrow supported layout sizes, including selection, tooltip, keyboard/touch operation, use, and throw.**
- [ ] **Step 5: Commit modal, state API, rendering, and tests with `feat: mostra bolsos dos cintos no inventario`.**

### Task 5: Author and round-trip preloaded belts in dungeon loot

**Files:**
- Modify: `tools/editor.js` (`exportLootItem`, loot item edit UI, import/export for chests and decor)
- Modify: `server.py` (sanitize/validate authored belt pockets when loading loot)
- Test: `tools/test_cinto_utilidades_editor.js` (new)
- Reference test: `tools/test_editor_items_logic.js`

**Interfaces:**
- `exportLootItem(item)` retains the belt's `utility_belt_slots` only for recognized belt IDs; other loot export behavior remains unchanged.
- Editor belt loot controls expose the model's fixed number of positions; each position selects an eligible consumable and quantity 1–4, or is empty.
- Server accepts normalized belt loot data and ensures the saved item remains one loot entry carrying all pocket contents.

- [ ] **Step 1: Write failing editor round-trip tests** for empty/preloaded examples of both belt types in chest and decor loot; assert the shared image/item ID, exact pocket count, quantity, and preservation through export then import. Pin malformed item IDs, ineligible pocket contents, duplicate same-belt stack IDs, and out-of-range quantity to safe empty/rejected values.
- [ ] **Step 2: Run `node tools/test_cinto_utilidades_editor.js` and confirm round-trip assertions fail.**
- [ ] **Step 3: Add editor controls and preserve valid pocket payloads through `exportLootItem` and the existing chest/decor import/export pipeline; apply matching server sanitization.**
- [ ] **Step 4: Run the focused editor test and `node tools/test_editor_items_logic.js`; confirm ordinary loot serialization is unchanged.**
- [ ] **Step 5: Commit editor, server validation, and tests with `feat: permite preparar cintos com loot`.**

### Task 6: Verify end-to-end commerce, persistence, and localization

**Files:**
- Modify as needed: `server.py`, `src/lang/*`, `tools/export_catalog.py` output via the exporter (never hand-edit generated `tools/editor_catalog.js`)
- Test: `tools/test_cinto_utilidades_catalogo.py`, `tools/test_cinto_utilidades.py`, `tools/test_cinto_utilidades_uso.py`, and `tools/test_cinto_utilidades_editor.js`

**Interfaces:**
- Mercador transactions use prices 80 and 30; rejected purchase due to full inventory does not charge gold.
- Unequip notice is localized and names the specific belt; all item names and descriptions resolve through the existing localization/catalog pipeline.
- Saving/loading, dropping/picking up, and taking from chest/decor preserve each belt's own pockets and quantities as one item.

- [ ] **Step 1: Add failing integration assertions** for exact purchase prices and gold deltas; full-inventory purchase rollback; localized unequip message for each model with contents; and save/load plus drop/pickup/chest/decor transfer of a preloaded belt.
- [ ] **Step 2: Run the focused integration tests and verify each new assertion fails before completing its missing path.**
- [ ] **Step 3: Implement any missing localization, price handling, durable serialization, or transfer preservation without changing unrelated bag behavior.**
- [ ] **Step 4: Run all five focused belt suites, the existing item routing/equipment/projectile suites, and editor catalog export verification; inspect the generated diff and inventory appearance.**
- [ ] **Step 5: Commit only feature files and generated catalog output with `feat: completa cintos de consumiveis`.**
