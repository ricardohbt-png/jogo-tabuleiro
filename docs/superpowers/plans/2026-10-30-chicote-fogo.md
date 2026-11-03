# Chicote de Fogo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the approved magical fire whip to combat, inventories, stores, and the editor catalog.

**Architecture:** Add one authoritative weapon entry after silver-weapon generation. Preserve its magic, +1 bonuses, fire-on-hit marker, and critical fire die when purchased and equipped. Use the existing non-stacking burning status and apply one additional 1d6 fire die on critical hits with this whip.

**Tech Stack:** Python `server.py`, JSON `city_shops.json`, localization `src/lang/catalogo.js`, generated `tools/editor_catalog.js`, `CLAUDE.md`.

**Spec:** `docs/superpowers/specs/2026-10-30-chicote-fogo-design.md`

## Global Constraints

- Keep the current whip profile and class restrictions.
- Use the existing `em_chamas_rodadas` system; refresh duration by maximum and do not stack tick damage.
- A critical hit adds one 1d6 fire die; do not widen the critical range or double this extra die.
- Reuse `assets/itens magicos/chicote_flamejante.png`; do not create or rename an image.
- Do not add or run tests unless the user asks.

## Review Focus

- Purchased and looted weapons retain their icon, +1 bonuses, magic flag, and fire trigger.
- Main-hand, off-hand, and spinning-attack hits apply the same existing burning state; misses and defeated targets do not receive it.
- Critical hits with the whip roll and apply an extra 1d6 fire damage; preserve the property through purchase and re-equipping.
- Repeated hits refresh the duration without adding burning damage, and base whips remain unchanged.
- All five blacksmiths and the generated editor catalog expose the new item.

---

### Task 1: Register and integrate the weapon

**Files:**
- Modify: `server.py`
- Modify: `city_shops.json`
- Modify: `src/lang/catalogo.js`
- Modify: `tools/export_catalog.py` and generated `tools/editor_catalog.js`
- Modify: `CLAUDE.md`

**Interface:**
- Weapon ID: `chicote_fogo`.
- Fire property: `fire_on_hit: true`; duration roll `1d4`, extinguishable by water or an action.
- Critical fire damage: `fire_crit_damage: "1d6"`.
- Existing classes: `bard`, `rogue`, `paladin`, `warrior`.
- Cost and rarity: 1.200 coins, Rare.

- [x] Add the weapon after silver-weapon generation and preserve `fire_on_hit` and `fire_crit_damage` in purchase and equipment conversion.
- [x] Integrate fire application on successful main-hand, off-hand, and spinning-attack hits, apply +1d6 fire on critical hits, and ensure off-hand uses this weapon's own +1 attack and +1 damage bonuses.
- [x] Add it to every city's `ferreiro_weapon` stock, add Portuguese/English name and rules, and regenerate the editor catalog.
- [x] Document its full mechanics, cost, classes, and supplied icon in `CLAUDE.md`.
- [x] Review the focused diffs and all data paths statically; do not run tests or syntax checks.
