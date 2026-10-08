# Céu/Abismo Implementation Plan

**Goal:** Add an editor floor material that renders a distant sky and makes uncovered abyss tiles fatal to grounded creatures while preserving safe bridge decks and safe cleric resurrection.

**Architecture:** `server.py` remains authoritative for terrain classification, voluntary movement, forced displacement, falls, and resurrection. `src/gameState.js` mirrors only the walkability rule for client previews; `game.js` renders the material in 2D and 3D; the dungeon editor consumes the generated material catalog and validates authored placements.

**Tech Stack:** Python WebSocket game server, JavaScript client state and rendering, Three.js, procedural Canvas textures, existing editor catalog exporter and localization.

**Spec:** `docs/superpowers/specs/2026-10-07-ceu-abismo-design.md`

## Global Constraints

- The server is authoritative for game rules; client logic only predicts movement.
- `voo` active and altitude above the floor is the existing effective-flight rule; obstacle-ignoring flight remains a separate capability.
- The bridge deck is a separate usable surface over the underlying material; a bridge hole exposes the underlying material.
- Keep the existing sparse `materiais["x,y"]` map format; old maps need no migration.
- Do not use `solido` to mark the abyss, because forced movement and falls must reach the tile before resolving death.
- The city temple resurrection and monster resurrection stay outside this feature.

## File Map

- `server.py`: material metadata; safe floor classification; movement, push/fall death, authored starting-position validation, and resurrection destination.
- `src/gameState.js`: mirror the grounded abyss walkability restriction for reachability and route previews.
- `game.js`: 2D sky palette/pattern and 3D procedural sky texture on the lower terrain surface.
- `tools/editor.js`: material brush/fill compatibility and authored spawn validation, following existing catalog-driven material UI.
- `tools/export_catalog.py`: export the new server material to `tools/editor_catalog.js`.
- `src/lang/editor.js`: localized material name for the editor.

## Review Focus

- A bridge deck over an abyss remains safe, while a hole in that bridge exposes the abyss: keep bridge tile coverage and hole filtering consistent between server and client.
- A flying actor can cross the abyss only while `voo` is active and altitude is above the floor; obstacle-ignoring flight must not become a requirement for abyss immunity.
- A grounded voluntary route cannot enter, end on, or use an abyss tile as a shortcut, including partial paths and monster AI routes.
- A forced displacement or a landing after flight ends resolves death once through the normal death/corpse flow, including large-monster footprints.
- Resurrection chooses a deterministic free safe surface from the corpse position; failure leaves the target dead and spends no action or resources.

---

### Task 1: Add the material and render the sky floor

**Files:**
- Modify: `server.py` (`MATERIAIS`)
- Modify: `tools/export_catalog.py` and regenerate `tools/editor_catalog.js`
- Modify: `src/lang/editor.js`
- Modify: `game.js` (`MAT_PALETTE_2D`, material painters, `makeMaterialTex`, floor rendering)
- Modify: `tools/editor.js` only if the existing generic floor catalog/validation needs an abyss-specific exception

**Interfaces:**
- Produces material ID `ceu_abismo`, category `piso`, with terrain metadata `terreno: "abismo"`, `solido=False`, and `custo_mov=None`.
- The generated editor catalog exposes `ceu_abismo` as a regular floor material.
- Both renderers resolve the same ID; the 3D geometry remains at the elevation from `elevacoes`, beneath any bridge deck.

- [ ] Add `ceu_abismo` to `MATERIAIS` with the specified terrain marker and no solid movement blocking.
- [ ] Add the translated editor name and regenerate the catalog with `python tools/export_catalog.py`.
- [ ] Add a continuous-looking blue sky/cloud procedural painter to the 2D material palette and the corresponding 3D canvas texture painter; keep the texture static.
- [ ] Inspect the editor brush and fill options to confirm the floor material is selectable and saved under the existing `materiais` map.
- [ ] Inspect a lower floor with a bridge above it in 3D; confirm the bridge deck stays at its existing height and the sky shows around/through bridge holes.

### Task 2: Block voluntary walking while allowing effective flight

**Files:**
- Modify: `server.py` (`handle_move`, mobile actor movement guards, `_monster_can_occupy` and route consumers)
- Modify: `src/gameState.js` (`_walkable`, `bfsReachable`, `findPath`)
- Modify: `tools/editor.js` (map validation for authored non-flying starts, if existing validation does not already catch server-invalid starts)

**Interfaces:**
- Add server helper `GameRoom._casa_abismo(x: int, y: int) -> bool`, true only when the material is `ceu_abismo` and no bridge deck covers that coordinate.
- Client pathfinding treats a tile as abyss by `materiais["x,y"] === "ceu_abismo"` and applies the existing flight predicate `actor.voo && alturaDe(actor) > 0`.

- [ ] Add `_casa_abismo` beside the server's terrain helpers; ensure bridge holes do not count as deck coverage.
- [ ] Reject grounded voluntary entry in hero, animated creature, and freed-prisoner movement handlers; permit entry while effectively flying.
- [ ] Make monster occupancy/pathfinding reject abyss for grounded monsters and allow it to flying monsters, including multi-cell footprints.
- [ ] Mirror the same rule in `_walkable` so reachability, full paths, and partial paths never show a grounded route through abyss; keep flying previews aligned with server behavior.
- [ ] Reject authored hero and non-flying creature starting positions on uncovered abyss in editor validation and server map-definition validation; accept a start covered by a bridge deck.
- [ ] Review that non-abyss paths, flying paths, bridge decks, and bridge holes follow the material rule without changing obstacle-ignoring flight behavior.

### Task 3: Resolve forced pushes and falls on abyss

**Files:**
- Modify: `server.py` (shared forced-displacement/fall resolution and existing death paths)

**Interfaces:**
- Add or extend a single server helper for resolving arrival on an uncovered abyss tile after a forced displacement or landing; it must consult `_casa_abismo` and `_voo_imune_terreno`.
- The helper uses the existing authoritative death path for heroes, monsters, animated creatures, and other mobile entities rather than applying fall damage.

- [ ] Trace `_empurrar`, `_queda_no_passo`, and flight-height landing handlers; call the abyss arrival resolver after the final forced position is established.
- [ ] Kill a grounded creature that is pushed onto uncovered abyss; do not intercept or prevent the push before arrival.
- [ ] Keep an effectively flying creature alive while it occupies/crosses the coordinate; kill it if flight ends and it lands there.
- [ ] Ensure the resolution is single-shot and preserves current hero corpse, monster removal, and entity-step/state synchronization flows.
- [ ] Review forced movement against bridge decks and bridge holes, including oriented multi-cell monsters.

### Task 4: Return revived heroes to safe ground

**Files:**
- Modify: `server.py` (`handle_ressurreicao`, safe tile/occupancy helpers, animation payload)

**Interfaces:**
- Add `GameRoom._casa_segura_ressurreicao(alvo, x, y) -> bool` to require a usable floor/bridge surface that is not abyss, wall, closed door, blocking material/decoration, or occupied by a living creature.
- Add a deterministic nearest-safe-tile search from the stored corpse position, bounded to the map.

- [ ] Detect corpse positions on uncovered abyss before starting the resurrection animation or spending resources.
- [ ] Search safe candidates by increasing grid distance from the corpse, using a fixed tie-break order; account for bridges and bridge holes through existing coverage helpers.
- [ ] Use the selected safe position for the resurrection animation and the revived hero's authoritative position.
- [ ] If no safe tile exists, send the existing appropriate failure response and return before changing life/action/resources.
- [ ] Preserve the current adjacent-target rule, HP scaling, status cleanup, and normal resurrection behavior for corpses outside abyss.

## Completion Review

- Walk the acceptance criteria in the approved spec against the changed server, client, renderer, and editor behavior.
- Inspect both render modes with a lower abyss floor and a bridge that includes a hole.
- Review the final diff by file and ensure generated catalog output comes only from the authoritative material source.
