# Besta do Duelista Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the all-class Besta do Duelista to the game, using its generated PNG and placing it in every smithy.

**Architecture:** Follow the existing `hand_crossbow` weapon path, keeping authoritative combat and shop data in `server.py`; mirror the item in `src/gameState.js`, bolt compatibility, client range/display helpers, city stock, translations, editor export, and `CLAUDE.md`.

**Tech Stack:** Python, JavaScript, JSON, existing catalog generators.

**Spec:** `docs/superpowers/specs/2026-11-12-besta-do-duelista.md`

## Global Constraints

- Preserve unrelated worktree changes.
- No new power or cooldown; retain existing one-handed crossbow rules.
- Do not add or run tests for this change; use static syntax and catalog checks only.

## Review Focus

- Any class can buy, equip, and attack with the item.
- It uses DEX, 1d6, 4-square orthogonal range, and all current bolt variants.
- Existing dual-crossbow specialization works with matching or mixed hand-crossbow variants.
- All five smithies stock it and the editor catalog points to the PNG.

---

### Task 1: Catalog, combat compatibility, and shop integration

**Files:** `server.py`, `src/gameState.js`, `game.js`, `city_shops.json`, `tools/editor_catalog.js`, `src/lang/catalogo.js`, `CLAUDE.md`.

- [x] Add the server weapon and shop entry, class-unrestricted metadata, 1d6/range 4, icon, and bolt support.
- [x] Mirror the client item, ammo compatibility, straight-line range, projectile classification, and icon path.
- [x] Extend existing hand-crossbow dual-wield rules to the new variant without changing other weapon behavior.
- [x] Add the item to all five `ferreiro_weapon` lists; export catalog and fill English translations.
- [x] Document the weapon and run static syntax/catalog/worktree checks.
