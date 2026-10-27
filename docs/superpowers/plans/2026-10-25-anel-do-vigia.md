# Anel do Vigia Implementation Plan

> **For agentic workers:** Use this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Sell the Anel do Vigia for 80 coins and grant +2 hero vision while equipped.

**Architecture:** Add a native `SHOP_MERCHANT` item with `item_slot: "ring"`, `effect: "vision"`, `value: 2`, and the existing generic ring PNG. Add its SKU to the five city merchant lists and generate the editor catalog from the server catalog only.

**Tech Stack:** Python server/catalog, JSON city stock, JavaScript item translations.

**Spec:** `docs/superpowers/specs/2026-10-25-anel-do-vigia-design.md`

## Global Constraints

- `CLAUDE.md` remains the architecture/history source of truth.
- Keep the effect to hero vision radius only.
- Preserve pre-existing unrelated working-tree changes.
- Do not replace `assets/itens/ring.png`.

## Review Focus

- Item metadata remains `ring`/`vision`/`2` at 80 coins.
- The generic ring image exists and is linked on the item.
- All five existing merchant stocks contain the SKU exactly once.
- The server's already-existing gear effect applies and removes the bonus symmetrically.

---

### Task 1: Add and publish the ring

**Files:**
- Modify: `server.py` — native item definition.
- Modify: `city_shops.json` — merchant stock in every city.
- Modify: `src/lang/catalogo.js` — Portuguese and English name/description.
- Modify: `tools/export_catalog.py` and generated `tools/editor_catalog.js` — include full effect in the dungeon editor catalog.
- Modify: `CLAUDE.md` — record current item behavior.

- [x] Add the item and translations, update city stocks, and regenerate only `editor_catalog.js` to avoid rewriting the independently edited dungeon index.
- [x] Validate Python/JavaScript syntax, JSON, image existence, stock uniqueness, and `git diff --check`.
- [x] Review the scoped diff.
