# Gilo 3D Miniature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create and link a dark-brown Gilo miniature derived from the Bandit GLB, with two hand crossbows and a leather hat over the existing hood, matching the Bandit's in-game size, position, and facing.

**Architecture:** Build a separate Blender asset from the Bandit source, reusing its body, adding the hat and two hand-crossbow props, and removing the hand daggers. Export the model and front/back previews, then link the GLB through Gilo's ficha and runtime fallback while copying the Bandit's 1.05 visual scale and movement-facing calibration.

**Tech Stack:** Blender 5.1 headless, Python, existing GLB/PNG assets, Three.js monster pawn renderer.

**Spec:** `docs/superpowers/specs/2026-10-23-gilo-miniatura-3d-design.md`

## Global Constraints

- Preserve the original `assets/models3d/monstros/bandido.glb` and its existing assets.
- Preserve Gilo's 2D image, ficha attributes, abilities, equipment, behavior, and tile footprint.
- Keep the Bandit's runtime size multiplier (1.05), centered placement/base anchor, and movement-facing orientation for Gilo.
- The Gilo hat sits over the existing hood; do not remove the hood.
- Use a separate `assets/models3d/monstros/gilo_dedos_sujos.glb` as Gilo's 3D model.

## Review Focus

- The texture recolor leaves face/skin readable and makes clothing and leather clearly darker brown; inspect front and back renders.
- Both daggers are removed and one crossbow is attached to each hand; inspect front and back renders.
- The leather hat sits on the hood and remains attached to the head; inspect the front render and silhouette.
- Gilo matches the Bandit's scale, base position, and movement-facing direction in the game; verify the matching runtime values and rotation branch.
- Gilo's own model path reaches the ficha, editor catalog, and runtime fallback; compare those values after synchronization.

---

### Task 1: Create the Gilo miniature variant and review renders

**Files:**
- Create: `tools/recolor_gilo.py`
- Create: `assets/models3d/monstros/gilo_dedos_sujos.blend`
- Create: `assets/models3d/monstros/gilo_dedos_sujos.glb`
- Create: `assets/models3d/monstros/gilo_dedos_sujos_albedo.png`
- Create: `assets/models3d/monstros/gilo_dedos_sujos_preview.png`
- Create: `assets/models3d/monstros/gilo_dedos_sujos_preview_back.png`
- Read: `assets/models3d/monstros/bandido.glb`, `assets/itens/besta.glb`, `assets/pawns/monstros/gilo_dedos_sujos/gilo_dedos_sujos.png`

**Interfaces:** The script takes no required positional arguments and resolves project paths relative to itself. Its generated GLB preserves the Bandit's source coordinate frame and base alignment.

- [x] **Step 1: Build the Blender variant script**

Import the Bandit GLB, retain its body and source transform, darken clothing/leather toward the Gilo reference while preserving face and gold details, remove dagger geometry, add a tapered, uneven leather hat over the hood, and fit one hand-crossbow prop to each hand. Save the editable blend and export an embedded-texture GLB.

- [x] **Step 2: Render front and back previews**

Render transparent PNG previews from opposite sides using the existing Blender 5.1 headless workflow. Verify the hat remains over the hood, both hand crossbows replace the daggers, and the rear has no leftover dagger.

- [x] **Step 3: Verify asset integrity and visual result**

Load source and output GLBs with trimesh; confirm geometry/material data exists, original Bandit bytes are unchanged, and the variant previews show the intended changes. Check the rendered Gilo body against `bandido_preview.png` at the same display height.

---

### Task 2: Link Gilo and match Bandit runtime calibration

**Files:**
- Modify: `tools/elara_gilo_ficha.py:ficha_gilo`
- Modify: `monstros_personalizados.json` (Gilo record only)
- Modify: `tools/editor_monsters_custom.js` (generated Gilo record only)
- Modify: `game.js:_MONSTER_GLB_MODELS`, `monsterVisualScale`, `_monsterFacingToRotY`
- Modify: `CLAUDE.md` (Gilo 3D asset entry)

**Interfaces:** `ficha_gilo()` adds `model3d: "assets/models3d/monstros/gilo_dedos_sujos.glb"`; `_MONSTER_GLB_MODELS.gilo_dedos_sujos` resolves to that path. Gilo's scale branch uses 1.05, and the movement-facing set includes both `gilo_dedos_sujos` image and type identifiers.

- [x] **Step 1: Add Gilo's model path to the ficha source and saved catalog**

Write the own GLB path to the Gilo generator and only the Gilo record in `monstros_personalizados.json` and `tools/editor_monsters_custom.js`. Preserve all ficha values and the other catalog records.

- [x] **Step 2: Match Bandit scale, center, and orientation in Three.js**

Change the Gilo image fallback to the own GLB, apply the Bandit's 1.05 visual multiplier to Gilo, and add the Gilo identifiers to the same movement-facing path as Bandit. Preserve the existing footprint and use the renderer's normal base anchoring.

- [x] **Step 3: Verify linked values and render calibration**

Parse the JSON and editor catalog and compare Gilo's path. Inspect the runtime scale/orientation branches and compare rendered Gilo and Bandit at the same viewport and facing; confirm the Gilo base stays centered in the same tile position and the front faces movement.

