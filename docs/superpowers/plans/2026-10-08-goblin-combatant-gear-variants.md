# Goblin Combatant Gear Variants Implementation Plan

## Goal

Implement the approved randomized gear for Goblin Combatant, including combat, potion use, death loot, and matching complete 2D/3D appearances for each weapon and shield combination.

## Architecture

The server remains authoritative for random rolls and stores stable item IDs on each monster instance. `make_monster` must choose gear before equipment application, so the existing catalog equipment applier builds the attack and AC from the chosen items. The existing monster consumable AI handles the healing potion. Death loot reads the instance's current equipment and remaining consumables. The server publishes per-instance image/model keys; `game.js` resolves those keys through the existing 2D image and 3D GLB loaders. The Goblin Dual definition and behavior remain unchanged.

## Tech Stack

Python WebSocket server, JavaScript canvas/Three.js renderer, PNG pawn assets, GLB monster assets, and the repository's Python/Node validation scripts.

## Spec

Approved design: [`2026-10-08-variedade-goblin-combatente-design.md`](../specs/2026-10-08-variedade-goblin-combatente-design.md)

## Global Constraints

- Change only `goblin_combatente` behavior; preserve `goblin_dual`'s dagger and Arremesso.
- Keep six weapons equally likely, with independent 10% shield and 5% potion rolls.
- Preserve the Combatant's +2 attack bonus and standard monster critical behavior.
- Keep the loot consistent with the gear and consumables remaining on that instance at death.
- Preserve current goblin proportions, pose, palette, and framing in all visual variants.
- Update `CLAUDE.md` because it is the authoritative architecture and system-history document.

## Review Focus

1. Equipment must be selected before `_aplicar_equipamentos_monstro`, so the catalog item creates the right attack without losing the +2 bonus. Add deterministic per-weapon construction coverage in Task 1.
2. Item rolls must be independent, and the shield must add exactly +1 AC. Add injected-roll coverage for every outcome in Task 1.
3. The Goblin Dual must retain its current dagger, thrown attack, and loot while Combatant loses them. Add paired regression coverage in Task 1.
4. Potion loot must depend on whether the potion remains in the bag when the monster dies. Cover both unused and consumed potion paths in Task 2.
5. A visual key must resolve to the same weapon/shield combination in both renderers, including both Goblin Dual's legacy appearance and Combatant's selected GLB. Verify the full asset matrix in Task 3.

## Implementation Tasks

### Task 1: Randomized combat equipment and behavior

**Files / interfaces**

- Modify `server.py`: native `MONSTER_DEFS` for `goblin_combatente`, `_aplicar_equipamentos_monstro`, and `make_monster`.
- Add `tools/test_goblin_combatente_equipamento.py` using deterministic random injection or patching consistent with existing server tests.
- Keep Goblin Dual definitions and `_goblin_arremesso` routing unchanged.

**Steps**

1. Write failing tests for all six selected weapons, their catalog damage/category/reach, and the retained +2 attack bonus.
2. Write failing tests for independent shield and potion rolls, including the 10%/5% boundaries and all four presence combinations; assert the shield adds +1 AC.
3. Implement gear selection before equipment application. Populate `equipped_items` with the selected weapon and optional shield, add the potion to `equipment_consumables`, and save stable gear IDs on the instance for presentation and loot.
4. Remove the Combatant's `Arremesso` setup and dagger drop; preserve the Goblin Dual's current dagger and throwing behavior.
5. Run the focused tests and confirm they pass.
6. Commit as `feat(monsters): randomize goblin combatant gear`.

### Task 2: Loot and potion lifecycle

**Files / interfaces**

- Modify `server.py`: `_monster_try_equipment_item` only if the existing behavior needs a targeted restriction, and the monster death-loot code near `_spawn_monster_loot`.
- Extend `tools/test_goblin_combatente_equipamento.py` or add `tools/test_goblin_combatente_loot.py` if separation improves clarity.

**Steps**

1. Add failing tests that kill a Combatant with each selected weapon, optional shield, and an unused potion; assert the resulting loot matches the carried items and contains no dagger.
2. Add failing tests for a potion consumed at or below 50% HP: the monster heals and still attacks, and death loot no longer includes the consumed potion.
3. Implement only the Combatant-specific consumable loot inclusion needed for the existing bag lifecycle; retain gold and unrelated loot sources.
4. Verify paired Goblin Dual loot and Arremesso regression cases.
5. Run focused loot and equipment tests.
6. Commit as `feat(monsters): drop goblin combatant carried gear`.

### Task 3: 2D/3D appearance variants

**Files / interfaces**

- Modify `server.py` to publish per-instance visual keys derived from the selected weapon and shield.
- Modify `game.js`: `_monsterImageName`, `_MONSTER_GLB_MODELS`, and `_monsterGlbPath` (or the current equivalent resolution points).
- Add 12 PNG variants at `assets/pawns/monstros/<image-key>/<image-key>.png` and 12 GLB variants at `assets/models3d/monstros/<image-key>.glb`, using a consistent weapon/shield suffix convention.
- Add a focused asset-contract check, e.g. `tools/test_goblin_combatente_variants.py`, for all expected files and server/client key mappings.

**Steps**

1. Add a failing contract test for all 12 `(weapon, shield)` keys and their PNG/GLB paths.
2. Produce and inspect one 2D and one 3D sample at actual pawn scale. Adjust the asset workflow until both preserve the base goblin silhouette, pose, palette, and framing while clearly showing the selected weapon and wooden shield.
3. Produce the other eleven 2D appearances and the remaining 3D combinations from the approved sample, then inspect the full 2D contact sheet and representative 3D models.
4. Implement server visual-key selection and client resolution for those keys, while retaining legacy resolution for Goblin Dual and all other monsters.
5. Run the asset-contract check and client syntax validation; inspect one combatant appearance in both 2D and 3D.
6. Commit as `feat(assets): add goblin combatant gear variants`.

### Task 4: Documentation and final verification

**Files / interfaces**

- Modify `CLAUDE.md` with the authoritative behavior, gear selection, loot, visual-key contract, and test commands.
- No generated snapshots should be edited unless Task 3 identifies one as authoritative.

**Steps**

1. Add a failing documentation/contract assertion only if the repository already has a suitable architecture-doc test; otherwise keep documentation review manual.
2. Document the finalized item IDs, probabilities, Combatant-only behavior, asset naming contract, and focused validation commands.
3. Run the focused equipment, loot, asset-contract, Python syntax, and JavaScript syntax checks.
4. Review the final diff for accidental changes to Goblin Dual or other monsters.
5. Commit as `docs(monsters): document goblin combatant gear variants`.

## Completion Criteria

- All six weapon variants are selected with equal odds and drive the actual monster attack.
- Shield and potion probabilities are independent; shield grants +1 AC.
- The Combatant has no dagger/Arremesso; the Goblin Dual keeps both.
- Death loot reflects the selected weapon, equipped shield, and only an unconsumed potion.
- All 12 combinations have matching visible 2D and 3D assets and resolve through runtime mappings.
- Focused checks pass and `CLAUDE.md` documents the authoritative contract.
