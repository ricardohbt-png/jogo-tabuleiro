# Bardo Inimigo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Bard as a native enemy with the approved level 1 stat block, random equipment and instrument, combat abilities, loot, and bestiary entry.

**Architecture:** Define the native monster and spawn-time randomization in `server.py`, reusing the player Bard's attribute values and instrument data. Add a dedicated enemy AI path for Heroic Song, Provocation, and useful active instrument abilities. Integrate forced movement and attack into the player's initiative turn so each of the three Provocation turns still returns control for remaining movement and bonus actions.

**Tech Stack:** Python game server, existing monster definitions/AI, WebSocket game state, Bestiary/catalog editors, localization catalogs.

**Spec:** `docs/superpowers/specs/2026-10-21-bardo-inimigo-design.md`

## Global Constraints

- Keep the enemy at ND 1, with the Bard attributes, saves, HP, movement, and attack values in the spec.
- Use one-handed weapon choices so any listed weapon can be paired with the off-hand instrument.
- Preserve the approved random chances, cooldowns, effect priorities, and 5–15 gold drop.
- Provocation lasts three turns, checks Will DC 11 on each turn, and returns control after the forced attack when the effect continues.
- Preserve existing uncommitted workspace changes; stage only files belonging to this feature.
- Do not add or run tests unless the user asks for verification.

## Review Focus

- A Provocation save succeeds on any of the three turns: the effect ends immediately and must not force another attack.
- The forced approach can be blocked or the Bard can die/disappear: move along the valid path as far as possible, attack only when in range, then leave remaining turn control usable and keep initiative moving.
- Bard's song can overlap existing monster buffs: apply only the chosen +1 attributes and remove only this song's bonuses at expiry.
- Instruments with passive effects or target-specific abilities must not be invoked through an incompatible active-ability path.
- Spawn randomization must preserve exact chance totals, including 0.5% elf and 0.5% dwarf origin.

---

### Task 1: Add the native Bard definition and spawn equipment

**Files:**
- Modify: `server.py` monster definitions near `MONSTER_DEFS` and Bard-equivalent spawn configuration near `_configure_*_spawn`.

**Interfaces:**
- Consume existing `CLASSES["bard"]`, `INSTRUMENTOS_BASE`, `criar_instrumento`, armor/weapon equipment helpers, and monster loot conventions.
- Produce a native `type`/`ai_type` entry for `bardo`, with spawn fields for its weapon, armor, instrument, ammunition, and gold.

- [ ] Add the `bardo` definition with STR 10, DEX 16, CON 12, INT 12, HP 9, movement 6, attack +3, saves Fort 0 / Ref +2 / Will +2, ND 1, and the approved ability declarations.
- [ ] Add uniform armor and weapon selection; create 20 bolts for crossbows and roll once to make the full stack incendiary at the specified weapon-specific rate.
- [ ] Select one of the nine instruments uniformly; apply quality weights 40/30/25/5 and origins 99/0.5/0.5; equip it in the free hand.
- [ ] Set death gold to a uniformly selected integer from 5 through 15 and use the existing Bard enemy image key `bardo`.
- [ ] Review generated weapon/armor combinations to ensure no two-handed weapon can prevent instrument use.

### Task 2: Implement enemy Bard actions and effects

**Files:**
- Modify: `server.py` near `_run_monster_ai`, monster ability execution, and existing Bard song/instrument effect helpers.

**Interfaces:**
- Consume the `bardo` state and its equipped instrument from Task 1, plus existing instrument effect definitions and monster attack/movement helpers.
- Produce a dedicated Bard AI branch that performs at most one special action per turn and falls back to ordinary combat.

- [ ] Add Heroic Song once per combat: choose 1d4+1 bonuses in the fixed order Acerto, Dano, CA, Movimento, Resistência; apply +1 to every allied monster within five cells for 1d4+2 rounds.
- [ ] Add Provocation with three-turn duration, three-cell range, cooldown of four rounds, and a Will DC 11 check on each affected turn.
- [ ] Add instrument use with a four-round cooldown, reusing the existing instrument's effects where the monster AI can resolve that effect safely; keep passive effects passive.
- [ ] Implement the approved AI priority: Heroic Song for allies in range, valid Provocation, useful active instrument ability, then normal attack.
- [ ] Ensure song expiry removes only the Bard song's own bonuses and does not overwrite other active buffs.

### Task 3: Integrate forced Provocation into player turns

**Files:**
- Modify: `server.py` in `_start_initiative_player_turn` / `_activate_initiative_actor`, player attack dispatch, and the state payload only where needed.
- Modify: `game.js` only if an existing client action/control signal is required to represent the forced approach/attack.

**Interfaces:**
- Consume the active player turn after normal upkeep and the Bard's active Provocation state.
- Produce one forced approach-and-attack sequence per failed Will save, then leave the player's remaining movement and bonus actions available.

- [ ] On each of the three affected turns, roll Will DC 11; on success, clear Provocation and proceed with an ordinary player turn.
- [ ] On failure, move the hero along the valid path toward the living Bard; attack when in range, or continue the compelled approach as far as possible before returning control for the remaining turn.
- [ ] Return normal control after the forced attack, preserving remaining movement and bonus actions; clear the state if the Bard dies or leaves play.
- [ ] Keep initiative advancement and turn timers correct for both success and forced-attack outcomes.

### Task 4: Expose the Bard in the Bestiary and catalogs

**Files:**
- Modify: `tools/editor_bestiary.js`, `tools/editor_catalog.js`, `tools/export_catalog.py`, and the relevant `src/lang/` catalog files only if the native definition is not sufficient for display.

**Interfaces:**
- Consume the `bardo` monster definition and its image key from Task 1.
- Produce a Bestiary entry displaying the monster name, ND, attributes, gear, abilities, and loot consistently with existing native monsters.

- [ ] Ensure the catalog export and Bestiary editor retain the Bard's native definition and all fields needed for display.
- [ ] Verify the entry uses the existing Bard monster PNG and presents ND 1.
- [ ] Review the final diff to confirm only Bard-related files are included.
