# Mangual do Elo Astral Implementation Plan

> **For agentic workers:** Plan executed inline in this session.

**Goal:** Add the Mangual do Elo Astral to combat, five blacksmith inventories, the localized catalog, and editor catalog.

**Architecture:** Add a weapon-specific four-square chain reach, measured in a straight orthogonal or diagonal line, with line of sight enforced by the server. Preserve the field through purchase/equipment and export it with the item definition.

**Tech Stack:** Python server, JSON shop catalog, JavaScript localization/editor catalog, existing PNG asset.

**Spec:** User-approved item design in conversation.

## Global Constraints

- Price 5,000 coins; +2 hit and damage; ordinary flail profile (1d8 bludgeoning, Strength, natural-20 critical ×2.5); Cleric, Paladin, Warrior.
- Passive reach: up to 4 squares in a straight orthogonal or diagonal line; line of sight required; one chosen target; no cooldown.
- Reuse `assets/itens magicos/mangual_elo_astral.png`.
- Preserve unrelated local work and do not run tests unless requested.

## Review Focus

- Base flails must remain limited to adjacent tiles.
- Astral reach must reject bends, distances over 4, and blocked line of sight.
- Weapon metadata must survive shop purchase and equipment synchronization.

## Files

- `server.py`: weapon/shop definition, reach validation, metadata persistence.
- `city_shops.json`: five blacksmith stocks.
- `src/lang/catalogo.js`: localized display name and description.
- `tools/export_catalog.py` / `tools/editor_catalog.js`: editor catalog field and generated output.
- `CLAUDE.md`: durable item rule summary.
- `assets/itens magicos/mangual_elo_astral.png`: existing item image.

## Task 1: Register and validate the weapon

- [x] Add the weapon and shop entry with the approved stats, price, reach field, icon, and classes.
- [x] Add a helper for 4-square straight-line reach and server line-of-sight validation; retain ordinary flail behavior.
- [x] Preserve the new reach field through purchase/equipment metadata.
- [x] Add the ID to all five blacksmith lists and localize its catalog name/description.
- [x] Export the editor catalog and document the rule in `CLAUDE.md`.
- [x] Run static syntax, JSON, PNG, and diff checks only; do not run game tests.
