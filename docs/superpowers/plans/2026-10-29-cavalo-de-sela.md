# Cavalo de Sela Implementation Plan

> **For agentic workers:** Execute inline with `superpowers:executing-plans`, one task at a time. Keep each checkbox current.

**Goal:** Add the approved native Cavalo de Sela stat block and its four-round Disparada cooldown.

**Architecture:** Register a separate native monster entry and dispatch it to a dedicated passive AI. The horse reuses shared movement, provocation, and cooldown helpers where safe; the cow remains unchanged. Record the durable gameplay contract in `CLAUDE.md`.

**Tech Stack:** Python game server and Markdown project documentation.

**Spec:** `docs/superpowers/specs/2026-10-29-cavalo-de-sela-design.md`

## Global Constraints

- Preserve the approved ficha values exactly: ND 1/4, 16 PV, CA 11, movement 8, FOR 16, DES 12, CON 14, INT 2, saves +4/+3/+1, Coice +4 (`1d6+2`).
- Disparada doubles movement for that fleeing turn; its cooldown is 4 rounds and it adds no attack or damage bonus.
- Keep existing cow behavior and unrelated local changes intact.
- Create the requested transparent PNG pawn; do not create a GLB or mount controls in this task.
- Do not add or run automated tests.

## Review Focus

- Horse attacks only after it has been provoked; other passive-animal behavior remains unchanged.
- A ready Disparada moves the horse twice as far when fleeing, then remains unavailable until its four-round cooldown expires.
- The native ficha stays out of random spawns and existing maps.

---

### Task 1: Register the horse, passive AI, and architecture note

**Files:**
- Modify: `server.py` (`MONSTER_DEFS`, passive-animal provocation, flee steps, `_run_monster_ai`, horse AI)
- Modify: `src/lang/narracao.js` (Disparada message)
- Regenerate: `tools/editor_catalog.js` with `tools/export_catalog.py`
- Create: `assets/pawns/monstros/cavalo_sela/cavalo_sela.png`
- Modify: `CLAUDE.md`

**Interfaces:**
- Produces: native type `cavalo_sela`, `ai_type: "cavalo_passivo"`, special ability `disparada_cavalo_sela`, and runtime cooldown state in `ability_cooldowns`.

- [x] Add the native stat block exactly as stated in the spec, with no random spawns or map placements.
- [x] Generalize provocation marking narrowly to recognize both `vaca_passiva` and `cavalo_passivo`, while preserving the existing cow state keys and flow.
- [x] Allow the shared flee helper an optional step count defaulting to one; process terrain hazards on every step. Add a dedicated horse AI: 50% chance to flee per turn; when fleeing and the four-round cooldown is ready, announce Disparada, move twice, and start cooldown 4; otherwise flee one step. If not fleeing, only pursue and coice after provocation.
- [x] Register the horse AI before generic monster behaviors and write the horse contract in `CLAUDE.md`.
- [x] Regenerate the editor catalog from `server.py` so the editor receives the native ficha.
- [x] Generate and install the transparent horse PNG at the standard pawn path, and set `image: "cavalo_sela"` on the native definition.
- [x] Review only the horse/cow-adjacent diff, run `git diff --check`, and parse `server.py` with Python AST without importing the server or running tests.

**Review result:** Ready with one minor deferred edge case: if every player is protected in a pit, the horse can spend Disparada's cooldown even though `_fugir_monstro` has no eligible target.
