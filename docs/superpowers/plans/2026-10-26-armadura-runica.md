# Armadura Rúnica Implementation Plan

> **For agentic workers:** Execute this plan inline in the current authorized task; do not delegate.

**Goal:** Implement the approved Armadura Rúnica as a +7 AC armor costing 2,500 coins with two selectable defensive spells.

**Architecture:** Keep `armadura_runica` as the stable item ID and make the `SHOP_ARMORS` definition authoritative for loot and shops. Grant two temporary skills while it is equipped; one server handler validates the chosen protection and shares a 30-round item cooldown.

**Tech Stack:** Python server, JavaScript HUD, JSON city inventories, PT/EN item catalog.

**Spec:** `docs/superpowers/specs/2026-10-26-armadura-runica-design.md`

## Global Constraints

- The armor grants +7 CA total, costs 2,500 coins, and is restricted to `warrior` and `paladin`.
- Each activation chooses one of the two spells, lasts exactly 5 rounds, and starts the shared 30-round cooldown.
- No normal spell slot is consumed.
- Preserve existing loot references to `armadura_runica`.
- Do not run or add tests in this task; perform static syntax, JSON, catalog, and diff checks only.

## Review Focus

- Both buttons must share one item cooldown and the server must reject direct forged requests during cooldown.
- Only the equipped armor grants the skills; unequipping it removes both skills.
- Existing Giant Rúnico loot must resolve to the full armor definition.
- Fixed durations must be exactly 5 rounds for both spell effects.
- Only Paladin and Warrior may buy, equip, or activate the armor.

---

### Task 1: Register and wire the Armadura Rúnica

**Files:**
- Modify: `server.py` — replace the CHEST_ITEMS placeholder with an authoritative `SHOP_ARMORS` item; implement the equipped-item skill payload, cooldown validation, spell execution, and WebSocket route.
- Modify: `game.js` — render the two granted spell buttons and send the selected spell ID.
- Modify: `city_shops.json` — add `armadura_runica` to all five `ferreiro_armor` inventories.
- Modify: `src/lang/catalogo.js` — update the PT/EN item description.
- Modify: `CLAUDE.md` — document the final item contract.
- Generate: `tools/editor_catalog.js` from the authoritative catalog.
- Use: `assets/itens/armadura_runica.png`.

**Interfaces:**
- Server skill IDs: `usar_armadura_runica_barreira` and `usar_armadura_runica_elemental`.
- Client request: `{type: "use_runic_armor", spell_id: "barreira_arcana"|"protecao_energia"}`.
- Cooldown field stored on the equipped item: `armadura_runica_pronta_em`.

- [x] Implement the armor definition, shop stock, and localized description.
- [x] Implement the temporary ability payload, single authoritative activation handler, and route.
- [x] Add the two skill buttons with the shared cooldown and server request.
- [x] Regenerate the editor catalog and run the required static validations only.
