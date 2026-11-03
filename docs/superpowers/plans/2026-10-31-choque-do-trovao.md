# Choque do Trovão Implementation Plan

**Goal:** Add the approved magical warhammer, its critical push, and its rechargeable lightning pulse.

**Architecture:** Keep the item definition authoritative in `server.py`; preserve its combat and cooldown fields through purchase and equipment synchronization. Resolve the area attack on the server and expose it through the existing granted weapon-skill UI pattern. Add shop stock, localizations, generated editor catalog, and canonical documentation.

**Tech Stack:** Python server, JavaScript client/localization, JSON city shop stock, generated editor catalog, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-31-choque-do-trovao-design.md`

## Global Constraints

- Use the approved 1d8 warhammer profile, +1 attack/damage, and +1d4 lightning per hit.
- Critical push is a Strength DC 13 check and moves the survivor one square; blocked pushes do not cause collision damage.
- Pulse is a main action, affects eight adjacent squares including allies but not the wielder, deals 2d6 lightning, Reflex DC 13 half, and recharges after 10 rounds.
- Price is 2,500 coins; classes are Cleric, Paladin, and Warrior.
- Do not add or run automated tests unless asked.

## Review Focus

- Both attack and equipment copies retain the passive elemental damage and critical push.
- The pulse validates turn, action, class, equipped weapon, and cooldown on the server.
- A creature occupying multiple footprint squares is damaged once.
- All five blacksmith stocks and the generated editor catalog include the item.
- PT and EN descriptions state friendly fire, save outcomes, cooldown, and all passive bonuses.

---

### Task 1: Register item and preserve combat fields

**Files:** `server.py`

- [x] Add the item definition with warhammer damage profile, price, icon, classes, +1 bonuses, 1d4 lightning, and critical push.
- [x] Preserve the new critical-push and pulse cooldown fields through purchase and weapon synchronization.
- [x] Apply Strength DC 13 and one-square push after a surviving target takes a natural-20 critical hit.

### Task 2: Implement the pulse action and UI

**Files:** `server.py`, `src/gameState.js`, `game.js`, `src/lang/interface.js`, `src/lang/catalogo.js`

- [x] Add server action validation, eight-square creature collection with footprint deduplication, Reflex DC 13, 2d6 lightning damage, cooldown, and combat narration.
- [x] Expose the weapon-granted skill, cooldown state, and activation control using existing skill UI conventions.
- [x] Add Portuguese and English skill and item descriptions.

### Task 3: Stock, catalog, and documentation

**Files:** `city_shops.json`, `tools/export_catalog.py`, generated `tools/editor_catalog.js`, `CLAUDE.md`

- [x] Add the item to `ferreiro_weapon` in all five cities.
- [x] Include its unique rule fields in the generated editor catalog and regenerate it.
- [x] Record the canonical item mechanics and price in `CLAUDE.md`.

### Task 4: Static review

- [x] Review the changed paths and inspect the diff for scope and formatting issues.
- [x] Do not claim automated test or live-combat verification.

Static review completed: Python bytecode compilation, JavaScript syntax checks for the modified client/API/localization files, five-city JSON stock and generated-catalog assertions, and `git diff --check` passed. Automated tests and live combat were not run.
