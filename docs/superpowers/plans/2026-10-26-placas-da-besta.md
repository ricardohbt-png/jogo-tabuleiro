# Placas da Besta Implementation Plan

> **For agentic workers:** Execute inline in the current authorized task; do not delegate.

**Goal:** Add Placas da Besta as a +3 CA armor with physical damage reduction 1 for 250 coins.

**Architecture:** Register a native `SHOP_ARMORS` entry and use the established resistance bonus on equipment. The city inventories and editor catalog consume this shared definition.

**Tech Stack:** Python server, JSON city inventory, JavaScript localization/editor catalog, PNG asset.

**Spec:** `docs/superpowers/specs/2026-10-26-placas-da-besta-design.md`

## Global Constraints

- Preserve `leather_plate` and its original stats.
- Apply only `physical` damage reduction, and only while equipped.
- Give the armor 4 corrosion levels without penalty, followed by the standard 2 penalized levels before destruction.
- Retain the base armor's allowed classes and corrosion materials.
- Do not run or add tests; use static validation only.

## Review Focus

- Equip and unequip must add/remove exactly one physical reduction entry.
- Elemental and magic damage must not be reduced by the item.
- All five city blacksmith armor stocks and the editor catalog must contain the item and image path.

### Task 1: Register armor, image, and market listing

**Files:**
- Modify: `server.py` — add `placas_da_besta` to `SHOP_ARMORS` with `bonuses: [{effect: resist, type: physical, value: 1}]`.
- Modify: `city_shops.json` — add it to all five `ferreiro_armor` inventories.
- Modify: `src/lang/catalogo.js` — add the Portuguese and English name and description.
- Modify: `CLAUDE.md` — record item and resistance behavior.
- Generate: `tools/editor_catalog.js` from the native catalog.
- Add: `assets/itens/placas_da_besta.png` from the approved reference-based image.

**Interfaces:** The item ID is `placas_da_besta`; the resistance entry is managed by the existing `_apply_resistance` gear flow.

- [x] Add the image and catalog definition.
- [x] Add the item to all five city stocks and localized names/descriptions.
- [x] Regenerate the editor catalog and run static syntax, JSON, asset, and diff checks only.
