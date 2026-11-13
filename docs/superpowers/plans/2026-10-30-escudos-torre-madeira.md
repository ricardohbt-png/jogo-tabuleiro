# Escudos Torre e Grande de Madeira Implementation Plan

**Goal:** Add two shield items with project-matched PNG icons and existing class, damage-reduction, store, and corrosion mechanics.

**Architecture:** Add complete shield definitions to `SHOP_ARMORS`, preserve their existing shield behavior and material metadata, list them at each blacksmith, localize their descriptions, and regenerate the editor catalog.

**Tech Stack:** Generated PNG assets, Python `server.py`, JSON `city_shops.json`, JavaScript localization and generated editor catalog, Markdown documentation.

**Spec:** `docs/superpowers/specs/2026-10-30-escudos-torre-madeira-design.md`

## Global Constraints

- Do not change the existing Guarda Máxima or corrosion systems.
- Use only the supplied class permissions and material vulnerabilities.
- No automated tests unless requested.

## Review Focus

- Shield icons are transparent and linked by item IDs.
- Damage reduction, class restrictions, and `corrosion_materials` survive purchase/equip.
- Both IDs exist in five `ferreiro_armor` stocks and the generated editor catalog.

---

### Task 1: Create and register shield assets

**Files:** `assets/itens/escudo_torre.png`, `assets/itens/escudo_madeira_grande.png`, `server.py`

- [x] Save the generated transparent PNGs under those paths.
- [x] Add `escudo_torre` (+3 CA, DR 2, Paladin, metal, 70) and `escudo_madeira_grande` (+2 CA, DR 1, Cleric/Warrior/Paladin, organic, 35).

### Task 2: Integrate store, catalog, localization, and documentation

**Files:** `city_shops.json`, `src/lang/catalogo.js`, `tools/editor_catalog.js`, `CLAUDE.md`

- [x] Add each ID to every city's `ferreiro_armor` stock.
- [x] Add PT/EN descriptions and regenerate the editor catalog.
- [x] Document bonuses, classes, prices, and devourer material vulnerabilities.

### Task 3: Static verification

- [x] Validate transparent PNGs, Python/JavaScript syntax, shop JSON and five-city stock, generated catalog IDs, and `git diff --check`.
- [x] Do not claim runtime purchase/combat verification; no automated tests are in scope.

Static verification passed: both PNGs are 1254×1254 RGBA with transparent corners; `server.py` AST, `city_shops.json` parse and five-city stock assertion, `node --check` for the catalog localization and generated editor catalog, exported item IDs/metadata, and `git diff --check` (line-ending warnings only). Automated tests and live purchase/combat were not run.
