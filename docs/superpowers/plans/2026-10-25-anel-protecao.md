# Anel de Proteção Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shop ring that grants +1 AC while equipped, costs 80 gold, and is available at every configured city merchant.

**Architecture:** Register the item in the native `SHOP_MERCHANT` catalog with `effect: "def_"`, `value: 1`, and the existing ring icon. Add its ID to each city's merchant allow-list and add localized catalog name and description; the existing buy/equip/AC systems remain authoritative.

**Tech Stack:** Python server and unittest, JSON city shop data, JavaScript localization catalog.

**Spec:** `docs/superpowers/specs/2026-10-25-anel-protecao-design.md`

## Global Constraints

- Use `CLAUDE.md` as the single architecture and protocol source.
- Preserve all pre-existing unrelated local changes.
- Keep the ring compatible with the two existing ring slots and normal AC recalculation.
- Do not generate or replace the existing ring image.

## Review Focus

- Merchant coverage: every city with a merchant stock list must expose the item (test catalog/stock coverage).
- Icon path: the configured PNG must exist (test asset path).
- Price and bonus: the native catalog must define 80 gold and +1 `def_` (test exact values).
- Equipment behavior: buying then equipping adds one AC, and unequipping removes it (integration test).
- Stock uniqueness: the item must occur once per merchant (test counts, not only membership).

---

### Task 1: Native item catalog, city stock, localization, and behavior test

**Files:**
- Modify: `server.py` — add native `anel_protecao` to `SHOP_MERCHANT`.
- Modify: `city_shops.json` — list `anel_protecao` in each of the five `mercador` inventories.
- Modify: `src/lang/catalogo.js` — localized name and description.
- Create: `tools/test_anel_protecao.py` — catalog, asset, city-stock, purchase, equipment, and AC regression checks.

**Interfaces:**
- Consumes: native merchant item catalog, `city_shops.json`, `GameRoom.handle_shop_buy`, and `handle_equip_from_bag`.
- Produces: purchasable `anel_protecao` with `item_slot: "ring"`, `effect: "def_"`, `value: 1`, `price: 80`, and `icon: "assets/itens/ring.png"`.

- [x] Write tests for exact catalog metadata, existing image, unique availability at every merchant, and buy/equip/unequip AC changes.
- [x] Run `python -X utf8 tools/test_anel_protecao.py` and confirm the new assertions fail because the item is absent.
- [x] Add the native item definition, all-city merchant stock entries, and Portuguese/English catalog strings.
- [x] Run `python -X utf8 tools/test_anel_protecao.py` and confirm all assertions pass.
- [x] Run `python -X utf8 -m py_compile server.py`, `node --check src/lang/catalogo.js`, JSON parsing for `city_shops.json`, and `git diff --check`.
- [x] Review the final diff and confirm it contains only the spec, plan, item test, architecture note, and requested item/catalog/stock changes.
