# Tiara da Expansão Arcana Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 800-coin Tiara da Expansão Arcana and apply its +1 radius to area spells.

**Architecture:** Register the item and reversible gear effect in the authoritative server catalog. Extend the existing area-size helpers for staff magic so the tiara stacks with the Cajado Arcano, and mirror the same sizing in the client targeting preview. Add the item to all city markets and localized catalogs.

**Tech Stack:** Python game server, JavaScript client, JSON city stock, localized catalog.

**Spec:** `docs/superpowers/specs/2026-10-26-tiara-expansao-arcana-design.md`

## Global Constraints

- `CLAUDE.md` is the authoritative source for architecture and protocol.
- Keep the server authoritative for affected tiles and targets.
- Do not change unrelated local modifications.

## Review Focus

- Radius-based areas grow by one tile on every edge.
- Level-scaled and player-sized areas include the tiara bonus.
- Spell targeting preview matches server area and excludes scrolls.
- Equipping and removing the tiara adds and removes its bonus symmetrically.
- The Cajado Arcano and tiara bonuses stack.

---

### Task 1: Register and apply the item

**Files:** `server.py`, `city_shops.json`, `src/lang/catalogo.js`, `CLAUDE.md`

- [x] Add the item to `SHOP_MERCHANT` and the five city stock lists.
- [x] Add the reversible `spell_area` equipment effect.
- [x] Add localized name and description, then document the item mechanics.

### Task 2: Integrate authoritative area sizing and preview

**Files:** `server.py`, `game.js`

- [x] Extend the server area sizing helpers to add one radius for the tiara and stack with the staff.
- [x] Mirror the equipment check and sizing in the client's spell-target preview; scroll casts receive no bonus.

### Task 3: Refresh generated editor catalog and inspect changes

**Files:** `tools/editor_catalog.js`

- [x] Regenerate the editor catalog from `server.py`.
- [x] Check the diff and static syntax/data integrity without modifying unrelated files.
