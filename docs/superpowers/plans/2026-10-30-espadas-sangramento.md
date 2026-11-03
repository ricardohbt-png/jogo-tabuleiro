# Espadas do Sangramento Implementation Plan

**Goal:** Add magical long and bastard swords that apply the game's existing bleed effect on every successful hit.

**Architecture:** Add complete weapon definitions to the authoritative blacksmith catalog and preserve magical/bleed fields when a purchase becomes an inventory item. Add both IDs to all five blacksmith stock lists, localize names/descriptions, reuse the supplied transparent icon, and document the rules.

**Tech Stack:** Python `server.py`, `city_shops.json`, generated `tools/editor_catalog.js`, JavaScript localization, Markdown documentation.

**Spec:** `docs/superpowers/specs/2026-10-30-espadas-sangramento-design.md`

## Global Constraints

- Preserve the current global Sangramento and Hemorragia rules.
- Keep both swords usable only by Warrior and Paladin.
- Do not create silver variants of these magical swords.
- No automated tests unless explicitly requested.

## Review Focus

- Bought weapons must retain `magical`, `causa_sangramento`, bonuses, class restrictions, and icon.
- The long and bastard swords must have distinct dice and prices.
- Both items must exist in each city's `ferreiro_weapon` stock and the generated editor catalog.
- Localization must explain per-hit bleed and critical Hemorrhage in Portuguese and English.

---

### Task 1: Register weapon definitions and purchase fields

**Files:** `server.py`

- [x] Add `espada_sangramento_longa` (1d8, 1.500) and `espada_sangramento_bastarda` (1d10, 2.000) after silver weapon generation, with +1 attack/damage, `magical`, `causa_sangramento`, shared icon, natural critical on 19–20, and Warrior/Paladin restrictions.
- [x] Preserve `magical` and `causa_sangramento` in the ferreiro purchase-to-inventory conversion.

### Task 2: Add availability, presentation, and documentation

**Files:** `city_shops.json`, `src/lang/catalogo.js`, generated `tools/editor_catalog.js`, `CLAUDE.md`

- [x] Add both item IDs to `ferreiro_weapon` in each of five cities.
- [x] Add PT/EN names and descriptions including rarity, bonuses, bleed-per-hit, and critical Hemorrhage.
- [x] Regenerate the editor catalog with `python tools/export_catalog.py`.
- [x] Document IDs, costs, classes, icon, and the existing bleed interaction in `CLAUDE.md`.

### Task 3: Static verification

- [x] Parse Python and JSON; run `node --check` on changed JavaScript; confirm both IDs in all five blacksmith lists and the generated editor catalog; run `git diff --check`.
- [x] Do not claim runtime verification; no automated tests or live session are in scope.

Static verification passed: `server.py` AST, `city_shops.json` parse and five-city stock assertion, `node --check src/lang/catalogo.js`, `node --check tools/editor_catalog.js`, generated catalog IDs, and `git diff --check` (line-ending warnings only). Automated tests and live purchase/combat were not run.
