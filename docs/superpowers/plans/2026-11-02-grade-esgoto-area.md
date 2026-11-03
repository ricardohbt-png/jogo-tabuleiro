# Grade de esgoto por área Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let the editor place a rectangular, walkable sewer grate over lower floor cells; opening it removes the full cover and resolves falls for occupants.

**Architecture:** The editor records one `grade_esgoto` decoration with a rectangular `size`, created by click-drag. Serialization derives a special bridge-cover record linked to that decoration, with one shared surface height inferred from the highest adjacent floor. The server indexes this cover as walkable bridge terrain and opens all covered cells atomically; the client hides the full decoration and exposes the lower floor.

**Tech Stack:** JavaScript editor and client state, Python authoritative game server, existing JSON dungeon format and bridge indexing.

**Spec:** User requests that the decoration create its own walkable cover and be resized by selecting an arbitrary rectangular area with the mouse and releasing; examples include 2x2 and 1x2. Opening removes the full cover; each occupant falls according to the height difference at its tile.

## Global Constraints

- Preserve ordinary bridge behavior and saves without sewer grates.
- Keep the lower `FLOOR` and its elevation as the fall destination.
- The cover is one shared elevation; each underlying tile retains its own elevation.
- The cover is rectangular, bounded by the map, and supports 1x1 as well as larger areas.
- Do not add or run tests unless the user asks; perform static and manual code-path verification only.

## Review Focus

- Drag direction and release outside the board produce the intended bounded rectangle.
- Every covered cell is walkable before opening and absent from the bridge index after opening.
- Per-cell lower elevations produce per-occupant fall distances.
- Save/load/copy/move/delete preserve the decoration footprint and its derived cover.
- Opened grates hide the full mesh and show the whole opening in 2D and 3D.

---

### Task 1: Editor area placement and serialization

**Files:** `tools/editor.js`, `tools/editor_catalog.js`

- [x] Add a drag preview for `grade_esgoto` placement, storing `size` from the inclusive rectangular selection on release.
- [x] Validate every cell as an in-grid `FLOOR`, reject overlaps/abysmal material, and require a lower floor beneath a derived perimeter height.
- [x] Derive one linked sewer-cover bridge record per grate in `buildJSON`, leaving normal bridge records unchanged.
- [x] Ensure editor selection, resize footprint, copy/paste, and deletion continue to treat the grate as one rectangular decoration.

### Task 2: Server cover geometry and activation

**Files:** `server.py`

- [x] Extend bridge-cover expansion and validation for linked sewer-grate rectangles with explicit tiles and fixed surface height.
- [x] Derive and index each grate cover at runtime without altering underlying floor elevations.
- [x] On activation, mark all covered cells as holes, hide the grate, rebuild bridge indexes, and apply height-difference fall damage to occupants on each covered cell.
- [x] Preserve serialization and movement through open cells for the full rectangle.

### Task 3: Client rendering and movement

**Files:** `src/gameState.js`, `game.js`

- [x] Mirror area-based open-grate pathfinding and fall-entry behavior in the movement preview.
- [x] Hide the full grate mesh after opening and render an opening for every covered tile in 2D.
- [x] Keep bridge elevation/rendering synchronized with the server's serialized cover tiles.

### Task 4: Documentation and review

**Files:** `CLAUDE.md`

- [x] Update the sewer-grate contract to document drag-selected rectangular covers and per-cell falls.
- [x] Review the changed code paths and run syntax/whitespace checks without running tests.
