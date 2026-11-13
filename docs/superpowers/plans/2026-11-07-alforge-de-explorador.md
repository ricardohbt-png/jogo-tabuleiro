# Alforje de Explorador Implementation Plan

> **For agentic workers:** Execute natively in the current session, one focused change at a time.

**Goal:** Add the Alforje de Explorador for 220 coins, using `assets/itens/alforge2.png`, granting +2 inventory spaces and one utility pocket that stores up to 4 compatible items.

**Architecture:** Reuse existing backpack and utility-belt behaviors. Declare the item in the server/client catalogs, add its one-pocket capacity to server and inventory UI, include it in the same shops as the basic backpack/belt, and regenerate only the editor catalog.

**Tech Stack:** Python server/catalog, JavaScript client/UI, JSON shop data.

**Spec:** `docs/superpowers/specs/2026-11-07-alforge-de-explorador-design.md`

## Global Constraints

- Name: `Alforje de Explorador`; price: 220 coins.
- Inventory capacity: +2 slots.
- Utility capacity: 1 pocket, maximum 4 identical compatible items.
- Occupies one equipped item slot; stored contents persist when unequipped.
- Use existing image `assets/itens/alforge2.png`.
- Do not alter unrelated items or mechanics.
- Do not add or run tests unless requested.

## Review Focus

- Equipping the alforje grants both effects through the same item slot.
- A second utility item remains unaffected and retains its own pocket count.
- Pocket content stays attached to the alforje when unequipped and re-equipped.
- Only one item stack of up to 4 units fits in the alforje pocket.
- The image and 220-coin price agree across server, client, shop, and editor catalogs.
- Unequipping cannot leave bag entries beyond the visible capacity after removing the alforje's +2 slots.

---

### Task 1: Register the hybrid item and pocket behavior

**Files:**
- Modify: `server.py` — item definition, utility capacity, and inventory expansion effect handling.
- Modify: `src/gameState.js` — client item definition.
- Modify: `src/ui/inventoryModal.js` — one-pocket and four-unit UI capacity maps.
- Modify: `city_shops.json` — add alongside the basic backpack and belt entries.
- Modify: `src/lang/catalogo.js` — localized name and description.
- Modify: `tools/editor_catalog.js` — regenerate with `write_catalog_js()` only.
- Modify: `tools/editor.js` — expose the item's pocket in authored loot.
- Modify: `CLAUDE.md` — document the item behavior.
- Use: `assets/itens/alforge2.png`.

**Interfaces:**
- Consumes existing `bagslots` effect and utility-belt storage handling.
- Produces item ID `alforge_explorador` with `effect: "bagslots"`, `value: 2`, and a one-pocket utility capacity with stack limit 4.

- [x] Add the item and capacity metadata to server and client catalogs.
- [x] Wire one pocket / four-unit UI presentation and transfers without changing existing item capacities.
- [x] Expose the pocket in the authored-loot editor and prevent unsafe alforje unequip when remaining bag capacity is insufficient.
- [x] Add the item to shops and localization, then regenerate only `tools/editor_catalog.js`.
- [x] Review the diff and run `git diff --check`; do not run tests.

Ruling: Add an alforje-specific unequip capacity guard — removing its +2 can otherwise hide bag entries beyond `bag_size` — cost if wrong: the player must free enough space before unequipping this item.

Final review: fresh reviewer found the capacity edge case and editor authoring gap; both were fixed. No tests were run per the plan constraint.
