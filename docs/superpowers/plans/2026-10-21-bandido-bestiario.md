# Bandido no Bestiário Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the approved ND 1 Bandido to the Bestiário with Rogue-derived stats, random equipment, stealth, traps, poison, gold, and the existing Bandido art.

**Architecture:** Register Bandido as a native monster in `server.py`, with per-instance randomization in the spawn path and a dedicated `ai_type`. Reuse the existing equipment, poison, stealth, trap, and Bestiary catalog paths; add only the Bandido-specific trap ownership and attack orchestration needed to keep the mechanic isolated.

**Tech Stack:** Python game server, generated JavaScript editor catalog, JavaScript/JSON language catalog, existing PNG assets.

**Spec:** `docs/superpowers/specs/2026-10-21-bandido-bestiario-design.md`

## Global Constraints

- ND is 1.
- Attributes are FOR 10, DES 18, CON 12, INT 10; PV 9; movement 7; CA base 14 plus the Manto's +1 for final CA 15.
- Rogue saves and +4 attack bonus are preserved.
- Each instance randomly selects one trap formula at spawn from `lamina_escondida`, `armadilha_incendiaria`, and `rede`.
- Hide and trap preparation each have a 3-round cooldown.
- Sneak Attack 1 grants advantage and +2d4 on the first strike from concealment.
- Only 20% of instances receive 1–2 Fungo Acre flasks; each applied dose is consumed by a hit.
- Death grants 2–10 gold inclusive.
- Reuse `assets/retratos/monstros/bandido.png` and `assets/pawns/monstros/bandido/bandido.png`.
- Do not change the behavior of other monsters, the Rogue, global trap formulas, poison rules, or 3D models.
- Do not add or run tests unless the user explicitly asks for testing or verification.

## Review Focus

- Equipment CA application: the Manto bonus must be applied exactly once, yielding CA 15.
- Movement normalization: the monster must retain 7 rather than falling back to 6.
- Secondary dagger attack: it must be one extra attack only when the primary weapon is a dagger and its 50% roll succeeds.
- Trap ownership and attribution: the Bandit must avoid its own trap; trap damage must not treat its monster ID as a player ID.
- Randomized spawn and loot: each new instance rolls independently; gold remains within 2–10 inclusive.

---

### Task 1: Register the native Bandit and spawn loadout

**Files:**
- Modify: `server.py` (`MONSTER_DEFS`, `make_monster`, `_aplicar_equipamentos_monstro`, and `_monster_dies_impl`)

**Interfaces:**
- `MONSTER_DEFS` produces the native `bandido` entry with the approved level, stats, natural armor, equipment flag, image/portrait keys, and `ai_type="bandido"`.
- Add `_configurar_bandido_spawn(m: dict) -> None` and call it once from `make_monster` for `type == "bandido"`, before `_aplicar_equipamentos_monstro(m)`. It assigns the primary weapon, optional second dagger, one trap formula, and optional poison inventory.
- Keep `m["equipped_items"]` in sync with the actual Manto and weapon IDs so the existing equipment and loot paths see the selected loadout.

- [x] Add the native definition with ND 1, HP 9, STR/DEX/CON/INT 10/18/12/10, base AC 14, movement 7 with `movement_exception`, Rogue saves, +4 attack, `image="bandido"`, `portrait="bandido"`, and the approved ability declarations.
- [x] Implement the per-instance randomizer: equal chance for dagger/bordao; 50% second dagger only after the primary dagger roll; equal chance among the three approved trap IDs; 20% chance for one or two Fungo Acre items; assign the Manto and rolled weapon IDs.
- [x] Configure attacks so all approved weapon loadouts use +4, the two-dagger loadout has one additional dagger attack, and cloak equipment raises final CA to 15 exactly once.
- [x] In `_monster_dies_impl`, assign the Bandit's guaranteed death payout with `random.randint(2, 10)` inclusive; leave all other monster payout paths unchanged.

### Task 2: Add Bandit AI for hiding, poison, and traps

**Files:**
- Modify: `server.py` (`_monster_known_hazard_tiles`, monster AI dispatch, `_ai_goblin_assassin` reference behavior, `_monster_move_step`, trap placement/trigger metadata)

**Interfaces:**
- Add `async def _ai_bandido(self, m: dict, targets: list[dict]) -> None` and dispatch only `ai_type == "bandido"` to it.
- Use `m["monster_ability_cooldowns"]` with stable ability IDs for hide and trap preparation; cooldown values are 3 own turns, corresponding to 3 rounds.
- Use existing `_envenenar_arma_do_inventario(m)` for Fungo Acre inventory consumption and existing `ARMADILHAS`/`_disparar_armadilha` for trap resolution.

- [x] Implement hiding with the Rogue-level concealment check used by `_ai_goblin_assassin`, set a 3-round cooldown on use, and defer the attack until the next available turn after a successful hide.
- [x] Implement the level-1 sneak attack bonus on the first attack after hiding: advantage and +2d4, consumed at that attack.
- [x] Implement trap selection from the per-instance `trap_type`; place only on an eligible free walkable tile adjacent to the Bandit, set a 3-round cooldown, and spend the attack action for that turn while allowing normal movement.
- [x] Mark Bandit traps as hostile to heroes and known to Bandits so their movement avoids them. Keep the trap trigger available to heroes, use a non-player creator value, and preserve existing trap effect, visibility, and damage attribution paths.
- [x] Before the next eligible attack, use one remaining Fungo Acre dose when no weapon dose is active; consume the coating on hit through the existing poison attack path.
- [x] Keep initiative advancement, invalid-target handling, and existing movement/terrain processing intact.

### Task 3: Publish the Bandit in the Bestiary and game catalog

**Files:**
- Modify: `src/lang/catalogo.js`
- Modify: `tools/export_catalog.py`
- Generate: `tools/editor_catalog.js` using `tools/export_catalog.py`
- Verify against: `tools/editor_bestiary.js`, `game.js`, and the existing PNG assets

**Interfaces:**
- The generated editor catalog reads native monsters from `server.MONSTER_DEFS` and includes the Bandit's stats, equipment, abilities, ND, image, and portrait fields.
- The Bestiary uses `portrait || type` for the portrait and `image || type` for the 2D mini, so both Bandit keys resolve to the existing assets.

- [x] Add the localized Bestiary name key `cat.monstro.bandido.nome` for the supported languages, following neighboring monster entries.
- [x] Include `portrait` in the native monster fields exported by `tools/export_catalog.py` so the Bestiary can use the declared portrait key.
- [x] Regenerate `tools/editor_catalog.js` from the authoritative server catalog; do not hand-edit the generated entry.
- [x] Confirm the generated catalog references the Bandit portrait and mini image paths and lists the approved equipment and abilities.

### Task 4: Record the shipped contract

**Files:**
- Modify: `CLAUDE.md`

- [x] Add a concise Bandit entry describing native type, ND, spawn rolls, AI cooldowns, trap ownership, poison chance, loot range, and image keys.
- [x] Keep the entry consistent with the approved spec and generated catalog.

## Validation Boundary

No automated or manual tests are included in this plan because testing/verification has not been requested. The data generator in Task 3 is part of producing the catalog, not a test suite.
