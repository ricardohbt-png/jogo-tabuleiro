# Espada Mágica Implementation Plan

**Goal:** Add +1, +2, and +3 versions of the magical short sword using the supplied icon.

**Architecture:** Register it as a distinct `SHOP_WEAPONS` item with the existing shortsword profile, add it to each city's blacksmith stock, localize it, regenerate the editor catalog, and document the price.

**Tech Stack:** Python server catalog, JSON city stock, JavaScript localization, generated editor catalog, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-31-espada-magica-design.md`

## Constraints

- Damage: 1d6 slashing with Strength; natural critical on 19–20.
- Bonuses and prices: +1/+1 for 500 coins, +2/+2 for 1,500 coins, and +3/+3 for 3,500 coins; no extra effects.
- Classes: Bard, Rogue, Paladin, Warrior.
- Price: 500 coins; icon: `assets/itens magicos/espada_magica.png`.
- Do not add or run automated tests unless asked.

## Tasks

- [x] Register each weapon profile and shop item; existing purchase and equipment code preserves their magical and bonus fields.
- [x] Add all three items to all five blacksmith stock lists and localize their names and descriptions.
- [x] Regenerate the editor catalog, record the canonical rules in `CLAUDE.md`, and perform static syntax and stock checks.

Static checks passed: Python compilation, JavaScript localization syntax, all three stock entries in each of five cities, generated catalog entries, and `git diff --check`. Combat tests were not run.
