# Espada do Juramento Inquebrantável Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Paladin-only longsword with a once-per-10-rounds ally-protection reaction and four metal material variants.

**Architecture:** Keep `server.py` authoritative for reaction eligibility, damage reduction, cooldown, and material generation. Add a localized client prompt through the existing gameState event pattern; export item fields to the editor and stock all five blacksmiths. Generate five transparent PNG item icons that share the sword silhouette.

**Tech Stack:** Python game server/catalog, JavaScript client and localization, JSON shop inventories, PNG art.

**Spec:** `docs/superpowers/specs/2026-11-13-espada-juramento-inquebrantavel-design.md`

## Global Constraints

- Base profile is 1d8 slashing + Strength, natural 19–20 critical ×2, with no fixed attack or damage bonus.
- Only Paladin can use any version.
- The optional reaction reduces one positive instance of damage from an enemy attack against a living ally within 3 squares by 1d6 after the target's other reductions and before HP loss; use starts a 10-round cooldown, declining does not.
- Material rules and prices must match the approved spec.
- Preserve unrelated workspace edits and do not run test suites unless requested.

## Review Focus

- Reaction only offered for valid Paladin, living ally, range, positive post-resistance damage, and a ready cooldown.
- Item fields/cooldown survive purchase, equipment synchronization, and editor export.
- Each variant preserves the Paladin class gate and protection ability while using its material bonus/corrosion profile and correct icon/price.
- All five blacksmith inventories and localized item labels/descriptions contain the variants.

## Implementation Tasks

- [x] Generate the base sword PNG and four material-specific transparent PNGs; inspect alpha and preserve a coherent silhouette.
- [x] Add the base weapon and material variants in `server.py`; add the reaction flow and copy its fields through purchase/equipment synchronization/editor export.
- [x] Reuse the existing client `sorte_reacao` choice and protocol; add PT/EN prompt and narration strings; add all five IDs to all five blacksmith inventories.
- [x] Regenerate `tools/editor_catalog.js`, update `CLAUDE.md`, and preserve unrelated generator/worktree changes.
- [x] Run static syntax, JSON, asset, class/price/material, shop inventory, and diff checks; no test suite or playthrough unless requested.
