# Esqueleto Armadurado Implementation Plan

**Goal:** Replace the legacy `skeleton` profile with the armored skeleton requested by the user while keeping old map references valid.

**Architecture:** Keep `type: skeleton`; configure it through the existing humanoid skeleton AI, equipment, material, corrosion, resistance, and loot systems. Register the supplied GLB as the monster's explicit `model3d` while retaining the current 2D image as fallback. Export the editor catalog from the server definitions.

**Tech Stack:** Python (`server.py`), JavaScript (`game.js`, generated `tools/editor_catalog.js`), GLB assets, Markdown (`CLAUDE.md`).

**Spec:** User's approved answers in the conversation: 15% material chance independently for each equipped piece; magical weapon is a +1 variant of the weapon rolled; Intelligence affects Will saves, so INT 4 gives Will -1 from base +2.

## Global Constraints

- Preserve old map references to `type: skeleton`.
- Keep the legacy type out of the random procedural spawn pool (`spawn_max: 0`); existing maps and authored encounters can use it directly.
- Keep `esqueleto_humano` and `esqueleto_animal` unchanged.
- Use the same weapon and shield rolls as `esqueleto_humano`.
- Armor selection uses Bronze 50%, Leather Mail 30%, Plate 20% as the price-weighted implementation default.
- Each equipped weapon, armor, or shield independently has 15% chance for an available material variant.
- The Iron Helm is independently equipped on 30% of armored skeletons, adds +1 AC, and is included in intact equipment loot.
- A separate 0.5% weapon roll upgrades the selected weapon/material variant to magical +1.
- Gold loot: 30% chance, amount 4–14 inclusive; equipped non-destroyed gear drops.

## Review Focus

- Old maps still resolve `skeleton` and use the new AI and miniature.
- Armor CA is 10 plus armor bonus, with shield CA added; no DEX contribution.
- Material probabilities remain independent per item and do not change other monsters' odds.
- Magical variant retains the rolled weapon profile and any material properties.
- Loot includes actual material/magical gear and excludes corroded destroyed pieces.

### Task 1: Server ficha, equipment, materials, and loot

**Files:** `server.py`

- [ ] Replace the legacy profile with the complete ND 1, 14 HP, attribute, saves, undead traits, and explicit model profile while retaining procedural-spawn exclusion.
- [ ] Reuse the existing humanoid weapon and shield roll; add price-weighted armor roll and equip the items through the existing equipment pipeline.
- [ ] Add skeleton-specific independent 15% material rolls and 0.5% same-weapon magical +1 variants.
- [ ] Route skeletons through humanoid AI and custom equipment loot; add the 30% 4–14 gold roll.

### Task 2: Miniature and editor catalog

**Files:** `assets/models3d/monstros/esqueleto_armadurado.glb`, `game.js`, `tools/editor_catalog.js`

- [ ] Copy the provided GLB, register the dedicated `esqueletoArmadurado` 2D sprite, and leave `esqueletoHumano` art untouched.
- [ ] Regenerate the editor catalog using `tools/export_catalog.py`.

### Task 3: Record rules and static checks

**Files:** `CLAUDE.md`

- [ ] Document the new ficha, loadout rolls, CA, material and magic odds, saves, and loot.
- [ ] Check Python/JavaScript syntax, JSON parseability, GLB existence, and diff whitespace. Do not run automated tests unless the user requests them.
