# Lobisomem Alfa ND 6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the ND 6 Lobisomem Alfa with fire-limited revival, definitive silver/fire deaths, and a black-furred, red-eyed miniature.

**Architecture:** Keep the existing Lobisomem type and rules unchanged. Add a distinct native monster definition and narrowly scoped Alfa state/turn/death helpers; track only the resolved fire portion of damage for its regeneration ceiling. Give the Alfa its own PNG and GLB identity and regenerate the editor catalog from `server.py`.

**Tech Stack:** Python `server.py`, Python regression scripts under `tools/`, generated `tools/editor_catalog.js`, browser client `game.js`, GLB/PNG assets, Blender or existing GLB/PNG processing tools.

**Spec:** `docs/superpowers/specs/2026-10-12-lobisomem-alfa-design.md`

## Global Constraints

- Use type/image ID `lobisomem_alfa`; keep the regular Lobisomem at ND 3, 31 PV, CA 17, and its current rules.
- Alfa: ND 6, 85 PV, CA 19, attack bonus +8, two Garras `2d6+5` and one Mordida `2d8+5`, and regeneration of 5 PV per turn.
- Nonmagical physical damage without silver is halved; silver doubles physical damage; silver or magic damage that does not kill blocks the next passive heal.
- Only the resolved fire component reduces the regeneration ceiling, by its final applied amount; the ceiling is `max(0, max_hp - lobisomem_alfa_dano_fogo)`.
- At 0 PV, the Alfa returns with 1 PV at its next turn only if the ceiling is positive and no definitive-death condition applies.
- A lethal silver hit is definitive. If fire has reduced the ceiling to 0, the next fall to 0 PV is definitive. Fire does not kill a living Alfa merely by reducing the ceiling.
- Do not change Troll rules or the regular Lobisomem's definition, behavior, or assets.
- Use a dedicated GLB and PNG mini for the Alfa, preserving the base Lobisomem's geometry/pose and source assets; show black fur and clearly red eyes.

## Review Focus

- Mixed damage attacks must add only their fire component to the cap counter — test fire+physical damage and verify the cap falls only by fire.
- Damage reduction/resistance must be applied before fire is accumulated — test zero fire damage and a reduced fire hit.
- Multiple falls to 0 PV must not restart or duplicate the return state — test one return followed by another lethal event.
- Silver fatality must be based on the actual killing hit, while nonlethal silver only pauses healing — test a nonlethal hit followed by a lethal ordinary hit and vice versa.
- A 0-PV regenerating Alfa must remain in both initiative systems but must not act until it returns — test live initiative and “Testar como Mestre”.

---

### Task 1: Add the Alfa ficha and isolated combat damage rules

**Files:**
- Modify: `server.py` (`MONSTER_DEFS`; Alfa-only damage adjustment and fire bookkeeping)
- Create: `tools/test_lobisomem_alfa.py`
- Test: `tools/test_lobisomem_alfa.py`

**Interfaces:**
- Produces `MONSTER_DEFS` entry `type == "lobisomem_alfa"` with the exact stats and attack definitions above.
- Produces per-instance state `lobisomem_alfa_dano_fogo` and an Alfa-specific resolved-fire accumulator invoked by the central damage funnel.

- [x] **Step 1: Write failing tests** for the Alfa catalog values, unchanged base-wolf values, attack routine, physical mitigation, silver doubling, magical/nonlethal-silver regeneration pause, and mixed fire+physical damage where only the resolved fire portion reduces the ceiling.
- [x] **Step 2: Run** `python -X utf8 tools/test_lobisomem_alfa.py`; confirm failures are caused by the missing Alfa definition/behavior.
- [x] **Step 3: Add** the Alfa `MONSTER_DEFS` entry with `image: "lobisomem_alfa"`, inherited aggressive AI, scent and retreat behavior, stats, attacks, abilities, and silver weakness.
- [x] **Step 4: Add** Alfa-specific physical mitigation and track resolved fire damage without changing Troll or regular-wolf branches. Mixed damage must carry/separate its fire component so non-fire damage never reduces the ceiling; verify damage reduced to zero does not reduce the ceiling.
- [x] **Step 5: Run** `python -X utf8 tools/test_lobisomem_alfa.py`; confirm the new definition and damage rules pass.

### Task 2: Implement fire-limited regeneration, definitive death, and initiative persistence

**Files:**
- Modify: `server.py` (monster spawn state, upkeep regeneration, `_monster_dies`, alive/initiative checks, combat simulator checks)
- Modify: `tools/test_lobisomem_alfa.py`
- Test: `tools/test_simulador_turno.py`

**Interfaces:**
- Consumes the Alfa type/state and resolved-fire accumulator from Task 1.
- Adds `_processar_regeneracao_lobisomem_alfa_inicio(m)` to return from 0 PV or heal 5 PV, respecting the ceiling and one-turn silver/magic pause.
- Preserves the existing initiative contract: an Alfa marked as regenerating at 0 PV is alive for turn scheduling, but has no actions before revival.

- [x] **Step 1: Add failing cases** for passive 5-PV healing; ceiling clamp; partial fire plus return; fire reaching a zero ceiling; lethal silver; nonlethal silver pause; and definitive death on the next fall after the ceiling reaches zero.
- [x] **Step 2: Add failing initiative/simulator cases** proving a fallen regenerating Alfa gets its upkeep and cannot attack at 0 PV.
- [x] **Step 3: Run** `python -X utf8 tools/test_lobisomem_alfa.py` and `python -X utf8 tools/test_simulador_turno.py`; record the expected missing-variant failures.
- [x] **Step 4: Implement** the Alfa upkeep helper and death-state transitions. Set up the regeneration flag exactly once at 0 PV; at the next upkeep, finalize if ceiling is 0 or the killing blow was silver, otherwise revive at 1 PV. Apply 5-PV healing up to the ceiling on later eligible turns.
- [x] **Step 5: Extend** all existing Troll-only initiative/simulator alive predicates narrowly to recognize the Alfa's own regeneration flag; do not generalize or alter Troll logic.
- [x] **Step 6: Run** both test commands again; all Alfa cases pass. Four existing Goblin Combatant throw checks fail because current rules set `pode_arremessar=False`, as documented in `CLAUDE.md`.

### Task 3: Publish the Alfa mini and editor/client catalog identity

**Files:**
- Create: `assets/models3d/monstros/lobisomem_alfa.glb`
- Create: `assets/pawns/monstros/lobisomem_alfa/lobisomem_alfa.png`
- Modify: `game.js` (monster GLB map)
- Regenerate: `tools/editor_catalog.js` via `python tools/export_catalog.py`
- Test: `tools/test_arte3d.py` and `tools/test_export_catalog.py`

**Interfaces:**
- Uses `image: "lobisomem_alfa"` so editor and 2D pawn resolve `assets/pawns/monstros/lobisomem_alfa/lobisomem_alfa.png`.
- Maps that image key to `assets/models3d/monstros/lobisomem_alfa.glb` in `game.js`.

- [x] **Step 1: Add failing coverage** that the bestiary export includes the new ID and that the Alfa has both matching PNG and GLB assets registered for 3D art.
- [x] **Step 2: Run** the catalog/art checks; the new targeted regression first failed on the missing Alfa PNG.
- [x] **Step 3: Create** the dedicated GLB from the base Lobisomem with black fur and red eyes, preserving pose and geometry. The source GLB has one mesh and an embedded 512×512 base-color atlas, so edit the atlas while preserving its UV islands, then re-embed it without changing geometry. Create a matching transparent PNG mini from the base pawn; inspect both outputs visually at board scale before accepting them.
- [x] **Step 4: Map** the Alfa GLB in `game.js` and regenerate `tools/editor_catalog.js` from `server.py` with `python tools/export_catalog.py`.
- [x] **Step 5: Run** the art and catalog tests again and inspect the final diff to ensure the original Lobisomem PNG/GLB are byte-unchanged.

## Final verification

- Run `python -X utf8 tools/test_lobisomem_alfa.py`.
- Run `python -X utf8 tools/test_simulador_turno.py`.
- Run `python -X utf8 tools/test_export_catalog.py`.
- Run `python -X utf8 tools/test_arte3d.py`.
- Run the complete existing project test suite, report any failures by exact command/output, and review the diff against the spec before claiming completion.
