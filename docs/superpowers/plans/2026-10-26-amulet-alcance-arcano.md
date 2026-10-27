# Amuleto do Alcance Arcano Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 400-coin Amuleto do Alcance Arcano and increase spell casting range by one square while equipped.

**Architecture:** Register a reversible equipment bonus in the server catalog and update the player spell definition copy before validation/execution. Mirror the range bonus in player targeting previews, leaving scrolls and monster targeting unchanged. Add localized catalog data and market stock.

**Tech Stack:** Python game server, JavaScript client, JSON city stock, localized catalog.

**Spec:** `docs/superpowers/specs/2026-10-26-amulet-alcance-arcano-design.md`

## Global Constraints

- `CLAUDE.md` is the authoritative source for architecture and protocol.
- Keep the server authoritative for range validation.
- Do not change unrelated local modifications.

## Review Focus

- Only positive spell casting ranges receive the extra square.
- Scaling range remains correct after applying the bonus.
- Self-centered spells, areas, cones, and spell effects do not grow.
- Scroll and monster casting remain unaffected.
- Equipping and removing the amulet applies and removes the bonus symmetrically.

---

### Task 1: Register item and equipment effect

**Files:** `server.py`, `city_shops.json`, `src/lang/catalogo.js`, `CLAUDE.md`

- [x] Add `amulet_alcance_arcano`, price 400, image `assets/itens/amulet.png`, to the five mercaders.
- [x] Add reversible `spell_range` equipment accounting and document the item.

### Task 2: Apply spell range on server and client

**Files:** `server.py`, `game.js`

- [x] Copy spell metadata for a cast and add +1 to its positive range fields when the amulet is equipped.
- [x] Cover custom level-scaled reach calculations and mirror the bonus only in player targeting previews.

### Task 3: Refresh generated catalog and verify

**Files:** `tools/editor_catalog.js`

- [x] Regenerate the editor catalog.
- [x] Run syntax and catalog/stock integrity checks; inspect the focused diff.
