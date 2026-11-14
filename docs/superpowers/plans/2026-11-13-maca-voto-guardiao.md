# Maça do Voto Guardião Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Requirements

- Cleric-only magical mace, 1d8 bludgeoning + Strength, with no fixed attack or damage bonus.
- On a successful hit, the Cleric may use Súplica Vital once per 10 rounds to restore 1d6 HP to self or an ally within 2 squares.
- Material variants inherit class restriction and healing power: Damascus Steel +1 attack, Obsidian Iron +1 damage, Titanium Alloy N=2/M=3, and Silver with the standard silver rule.
- Base price 1,600; use established material premiums and silver pricing. Add all variants and images to the item catalog and five blacksmith inventories.

## Implementation tasks

- [ ] Create and inspect the base transparent PNG plus one transparent PNG for each material variant.
- [ ] Register base mace and material variants in `server.py`, including the post-hit healing choice and its 10-round cooldown.
- [ ] Add client prompt/choice handling, localization, shop stock, and exported editor catalog fields.
- [ ] Document mechanics, material profiles, prices, and assets in `CLAUDE.md`.
- [ ] Run static syntax, JSON, asset-presence, price, class-restriction, and five-shop checks; do not run test suites unless requested.
