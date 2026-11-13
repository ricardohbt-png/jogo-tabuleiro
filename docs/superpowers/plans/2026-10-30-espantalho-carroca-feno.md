# Espantalho e carroça carregada de feno Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an in-game scarecrow and a hay-loaded wagon decoration whose fire appearance advances over five rounds before leaving ash.

**Architecture:** Build the props additively in Blender, reusing the existing wagon model as the geometry and material reference. Keep the wagon fire stage and timer authoritative in the server; publish stage state through decoration snapshots and let the client select the matching visual in 2D and 3D. Register both decorations in the server catalog and regenerate the editor catalog from the project exporter.

**Tech Stack:** Python game server, `terrain_reactions.py`, Three.js client, editor catalog exporter, Blender Python, PNG and GLB assets.

**Spec:** `docs/superpowers/specs/2026-10-30-espantalho-carroca-feno-design.md`

## Global Constraints

- `espantalho` is a 1×1, tall, solid, rotatable decoration without interaction or combat effects.
- `carroca_feno` is a 2×2, tall, solid, rotatable decoration based on `assets/objetos/carroca.glb` with hay added as its load.
- The ignition round counts as round 1; hay burns in rounds 1–2, the whole wagon burns in rounds 3–4, and round 5 leaves only ash.
- The wagon remains solid while burning; its fire contact uses 1d4 damage and remains inside the 2×2 footprint.
- Do not change the existing `monte_feno` rules, burn neighboring cells, or add combat behavior to the scarecrow.
- Preserve existing local modifications in touched files; the checkout contains unrelated uncommitted work.

## Review Focus

- Fire starts from any source on any wagon footprint cell; verify a single ignition, with no duplicate zone or repeated reset of the timer.
- Round transitions use the ignition round as round 1; manually inspect stage values at rounds 1, 2, 3, 4, and 5.
- A burning wagon remains a 2×2 blocker through round 4 and is removed exactly at the start of round 5.
- Fire contact remains limited to the wagon's 2×2 footprint and uses the current 1d4 behavior; no adjacent tile is added.
- Decoration state snapshots and save/load preserve the current fire stage and expiration point; inspect by following the existing room serialization path.

## Files and Responsibilities

- Create `tools/create_espantalho_carroca_feno.py` and Blender sources/renders under `assets/objetos/`; model the scarecrow, the wagon with hay, its two burning looks, and transparent board thumbnails.
- Modify `server.py` to register `espantalho` and `carroca_feno`, expose models, preserve burn fields in hydration/snapshots, and remove the wagon at round 5.
- Modify `terrain_reactions.py` to detect hay-loaded wagons, begin the stage timer on fire contact, advance stages, and reuse the existing 1d4 footprint contact rule.
- Modify `game.js` for GLB/PNG mapping and stage-dependent visuals; avoid changing the existing `carroca` and `monte_feno` render paths.
- Regenerate `tools/editor_catalog.js` using `tools/export_catalog.py`; update the decoration names in `src/lang/catalogo.js`.
- Update `CLAUDE.md` with the new decoration and burn timing contract.

## Tasks

### Task 1: Create prop geometry and visual stages

**Files:**
- Create: `tools/create_espantalho_carroca_feno.py`
- Create: `assets/objetos/espantalho.blend`, `espantalho.glb`, `espantalho.png`
- Create: `assets/objetos/carroca_feno.blend`, `carroca_feno.glb`, `carroca_feno.png` and the two burning stage GLBs/PNGs

- [x] Import `carroca.glb` into a Blender scene, preserve its 2×2 proportions/materials, add tied golden hay bales inside the bed, and save a reusable `.blend` source.
- [x] Create matching stage visuals: stage 1 flames restricted to the load; stage 2 flames engulfing load and wagon; keep geometry, origin, rotation axis, and footprint consistent across the three variants.
- [x] Create a readable, grounded 1×1 scarecrow with crossed wooden supports, patched clothing, straw protrusions, and a weathered hat; export its `.blend`, GLB, and transparent PNG.
- [x] Render orthographic board thumbnails with transparent backgrounds. Inspect the current and new models from isometric and top-down views for footprint fit and legibility.

### Task 2: Add authoritative fire stages

**Files:**
- Modify: `terrain_reactions.py`
- Modify: `server.py`

- [x] Extend fire-on-hay detection to include intact `carroca_feno` without changing `_rx_feno_em` behavior for `monte_feno`.
- [x] On first fire contact, save an ignition round and burn stage on the decoration and create one fire zone over its 2×2 footprint with 1d4 contact damage.
- [x] At the beginning of elapsed round 3, set the whole-wagon stage; keep that stage through elapsed round 4.
- [x] At the beginning of elapsed round 5, remove only the `carroca_feno` decoration, deactivate its zone, rebuild the decoration index, and emit the existing ash/fuligem ground reaction over the footprint.
- [x] Include fire stage, ignition round, and zone linkage in existing decoration/session serialization so a reconnect does not restart the burn.

### Task 3: Integrate catalog and runtime visuals

**Files:**
- Modify: `server.py`
- Modify: `game.js`
- Regenerate: `tools/editor_catalog.js`
- Modify: `src/lang/catalogo.js`
- Modify: `CLAUDE.md`

- [x] Register both decorations with authoritative metadata: `espantalho` 1×1 tall/solid/rotatable and `carroca_feno` 2×2 tall/solid/rotatable.
- [x] Map PNG and GLB files in client renderer and use the burn-stage field to select hay-only fire and full-wagon fire variants in both 2D and 3D.
- [x] Ensure the stage-5 ash reaction is shown by the existing `reacao_elemental` renderer and the prop is no longer rendered or collidable.
- [x] Regenerate the editor catalog from the authoritative server catalog and add localized names for both entries.
- [x] Document asset paths, footprint, collision, fire schedule, and ash lifetime in `CLAUDE.md`.

### Task 4: Validate the delivered asset and integration

**Files:**
- Inspect the new Blender files, PNG/GLB assets, and diffs to `server.py`, `terrain_reactions.py`, `game.js`, editor catalog, localization, and `CLAUDE.md`.

- [x] Run Blender headless export/render for the new assets and inspect the resulting transparent PNGs and the GLB stage variants.
- [x] Run syntax checks for the touched Python and JavaScript files; do not run or add automated tests in this task.
- [x] Review a focused diff to confirm existing local changes and existing `carroca`/`monte_feno` behavior are preserved.
- [x] Report any behavior that could not be confirmed in a live board session.
