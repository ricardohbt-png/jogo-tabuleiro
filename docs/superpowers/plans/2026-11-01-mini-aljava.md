# Mini Aljava Implementation Plan

> **For agentic workers:** Implement this plan task-by-task in the current session. Steps use checkbox syntax for tracking.

**Goal:** Add a 30-coin Mini Quiver in item slots that raises arrow and bolt stack capacity to 20.

**Architecture:** Reuse `effect: "quiver"` and centralize equipped-quiver discovery across `off_hand`, `item1`, and `item2`. Use the same discovery for stack capacity and ranged attacks that draw ammo from the bag. Mirror the capacity rule in the client where it decides whether chest loot can be taken, while preserving server authority for transfers.

**Tech Stack:** Python server catalogs and handlers, JavaScript client state/UI, JSON shop lists, localized catalog JSON.

**Spec:** `docs/superpowers/specs/2026-11-01-mini-aljava-design.md`

## Global Constraints

- The item occupies either `item1` or `item2`, uses `assets/itens/aljava.png`, costs 30 coins, and is sold in `ferreiro_ammo`.
- Capacity is 20 for each arrow and bolt type, including existing special variants.
- Multiple equipped Mini Quivers do not add capacity.
- Existing Small and Large Quiver capacities and behavior stay unchanged.
- Server capacity checks remain authoritative; generated editor catalog output must match `server.py`.
- Do not add or run tests in this task.

## Review Focus

- Ammo types are classified correctly as arrows or bolts, including magical, silver, incendiary, and explosive variants.
- Equipping in either item slot grants capacity; equipping two copies does not add capacity.
- Existing off-hand quivers retain their current limits.
- Ranged attacks draw matching ammo from the bag when a Mini Quiver occupies an item slot.
- A full bag can still take chest ammo when an existing stack has room up to 20.
- Shop availability is consistent across all five city entries and the editor catalog.

---

### Task 1: Register the Mini Quiver and apply the capacity rule

**Files:**
- Modify: `server.py` — add the `mini_aljava` `SHOP_AMMO` definition and generalize `_max_ammo_stack_for` to inspect `off_hand`, `item1`, and `item2`, using the largest declared per-family capacity.
- Modify: `server.py` — replace exact small/large quiver ID checks in ranged-attack ammo selection with detection of any equipped `effect: "quiver"` item.
- Modify: `city_shops.json` — add `mini_aljava` to each of the five `ferreiro_ammo` lists.
- Modify: `src/lang/catalogo.js` — add English and Portuguese name and description strings for the item.
- Modify: `src/gameState.js` — expose a pure capacity helper mirroring the server for UI decisions.
- Modify: `game.js` — use the client helper in chest ammo-space detection instead of the hardcoded limit of 10.
- Regenerate: `tools/editor_catalog.js` from `server.py` using `tools/export_catalog.py`.
- Modify: `CLAUDE.md` — record the Mini Quiver contract and the server/client mirroring requirement.

**Interfaces:**
- Client helper: `GS.maxAmmoStackFor(player, item) -> number`, defaulting to 10 and returning the greatest equipped quiver capacity applicable to the ammo family.
- Server helper remains `_max_ammo_stack_for(p, item) -> int` and recognizes all existing quiver types and slots.

- [x] Add the Mini Quiver catalog entry with `id: "mini_aljava"`, `item_slot: "item"`, `effect: "quiver"`, capacities 20/20, price 30, icon path, and localized description keys.
- [x] Add the item ID once to each `ferreiro_ammo` list in `city_shops.json`.
- [x] Update server quiver discovery to inspect `off_hand`, `item1`, and `item2`; use the greatest applicable capacity and recognize any equipped quiver when ranged attacks draw ammo from the bag.
- [x] Add `GS.maxAmmoStackFor(player, item)` and use it when checking available chest ammo space.
- [x] Regenerate `tools/editor_catalog.js` and confirm the item exports with the approved fields.
- [x] Record the implemented contract in `CLAUDE.md` and review the diff for unrelated changes.
