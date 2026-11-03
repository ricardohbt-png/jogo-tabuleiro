# Grade de esgoto Implementation Plan

> **For agentic workers:** implement inline in this workspace and preserve unrelated local changes.

**Goal:** Add a usable sewer hatch decoration that opens a bridge tile and drops any character standing on it onto the lower floor.

**Architecture:** Reuse authored bridge holes and fall damage. The server owns the open state and resolves falls; the client mirrors the special movement into an open hatch and hides the closed prop; editor/server validation require a bridge over a lower `FLOOR` tile.

**Tech Stack:** Python server and map validation, JavaScript map editor and Three.js renderer, Blender 5.1 procedural GLB plus transparent PNG.

**Spec:** `docs/superpowers/specs/2026-11-02-grade-esgoto-design.md`

## Global Constraints

- The hatch lands on the lower floor at the same coordinate in the same map.
- Ordinary terrain drops remain blocked; only an open sewer hatch permits voluntary descent.
- The hatch remains open after activation and its state is included in dungeon snapshots.
- Preserve all unrelated local work already present in the workspace.
- Do not add or run automated tests in this task.

## Review Focus

- Invalid placement without a bridge, lower `FLOOR`, or positive drop is rejected by both editor and server.
- Opening while a character occupies the grate resolves one fall.
- Reopening is rejected/ignored and the bridge hole remains represented in saved state.
- Entering an already open hatch is allowed, while other voluntary drops remain blocked.
- The closed GLB is visible in 2D/3D; the open state reveals the lower floor.

### Task 1: Model and catalog

**Files:** `tools/create_grade_esgoto.py`, `assets/objetos/grade_esgoto.{blend,glb,png}`, `game.js`, `server.py`, generated `tools/editor_catalog.js`.

- [x] Build a low-profile iron grate with stone rim, closed-state GLB and transparent PNG.
- [x] Register the decoration metadata and PNG-to-GLB mapping; regenerate the editor catalog.
- [x] Import the GLB in Blender/trimesh and inspect the rendered preview.

### Task 2: Authoring and server behavior

**Files:** `server.py`, `tools/editor.js`, `src/lang/editor.js`, `CLAUDE.md`.

- [x] Validate the bridge/lower-floor/height contract in the editor and server.
- [x] Route adjacent interaction through the existing mechanism confirmation.
- [x] Open the bridge hole permanently, snapshot the decoration state, and resolve falls for occupants.
- [x] Permit movement through an open hatch and apply the existing terrain fall rules.

### Task 3: Client rendering and verification

**Files:** `src/gameState.js`, `game.js`, `src/lang/narracao.js` only if the existing narration needs a new key.

- [x] Mirror open-hatch traversal in client pathfinding.
- [x] Hide the closed grate when open and let the bridge renderer reveal the lower floor.
- [x] Run syntax checks, Blender export/import inspection, and `git diff --check`; do not run automated tests.
