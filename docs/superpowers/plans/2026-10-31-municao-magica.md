# Munição Mágica Implementation Plan

**Goal:** Add +1 and +2 magical arrow and bolt packs, each containing 10 projectiles.

**Architecture:** Extend the server ammo catalog and ranged weapon compatibility lists, apply ammo attack and damage bonuses in normal and dual crossbow attacks, and mark damage as magical. Add each item to all five blacksmith stocks, generate editor and vocabulary catalogs, and document the rules.

**Tech Stack:** Python server catalog and combat, JSON city stocks, JavaScript localization, generated editor catalog, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-31-municao-magica-design.md`

## Global Constraints

- Package size is 10; +1/+1 costs 50 coins and +2/+2 costs 120 coins.
- Arrows use `assets/itens magicos/flechas_magicas.png`; bolts use `assets/itens magicos/virotes_magicos.png`.
- The server remains authoritative; consume one projectile per shot, hit or miss.
- Preserve existing ammo selection, stacking, aljave capacity, and nonmagical/silver/explosive effects.
- Do not add or run automated tests unless asked.

## Review Focus

- Normal and dual crossbow shots both receive ammo bonuses and consume one projectile.
- Magical ammo bypasses nonmagical weapon resistance without permanently changing the equipped weapon.
- Arrow and bolt types remain restricted to their matching ranged weapons.
- Existing ammo ordering and counts remain unchanged.
- Each city stock and generated catalog entry refers to the right item and icon.

## Tasks

- [x] Add the four ammo definitions, icons, bonus metadata, compatibility, capacity, and auto-equip support in `server.py` and the client item catalog.
- [x] Apply ammo accuracy to the normal attack and preview; apply accuracy, damage, and magical damage rules to normal, dual-crossbow, and luck-reroll combat.
- [x] Add the four IDs to all five `ferreiro_ammo` stocks and add localized names/descriptions, auto-equip labels, and poisoned-ammo names.
- [x] Regenerate `tools/editor_catalog.js`, document the final item rules in `CLAUDE.md`, and review the focused diff and syntax.

Static checks passed: `python -m py_compile server.py`; `node --check` for the changed JavaScript files; valid `city_shops.json`; four IDs present in all five ammunition stocks; both PNGs exist. `tools/export_catalog.py` regenerated the editor catalog. `tools/gerar_vocabulario.py` stopped on an existing conflicting description for `relampago_de_mao`; the four new locale entries were added directly. No automated tests were run.
