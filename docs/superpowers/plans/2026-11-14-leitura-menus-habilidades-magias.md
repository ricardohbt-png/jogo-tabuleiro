# Leitura dos Menus de Habilidades e Magias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve readability of the in-game Habilidades and Magias menus on desktop and narrow screens.

**Architecture:** Keep existing menu markup and interaction models. Adjust responsive CSS in `game.css`; update spell and ability tooltip sizing and focus bindings in `game.js`.

**Tech Stack:** Existing HTML templates, CSS, and vanilla JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-14-leitura-menus-habilidades-magias-design.md`

## Global Constraints

- Preserve game mechanics, spell/skill text, shortcuts, spell slots, and gamepad navigation.
- Do not edit unrelated local changes.
- Do not add or run tests for this task; perform syntax and diff checks only.

## Review Focus

- Long descriptions must remain readable and scroll inside the tooltip without pushing it beyond the viewport.
- Narrow layouts must keep spell slots and shortcut controls reachable.
- Keyboard focus and mouse hover must share tooltip behavior without triggering activation.

### Task 1: Responsive menu typography and layout

**Files:**
- Modify: `game.css`

- [x] Widen both dialogs within viewport limits, increase card description/metadata sizes and contrast, switch card grids to one column at appropriate narrow-screen breakpoints, and replace skill-card hover scaling with border/focus emphasis.

### Task 2: Readable and keyboard-reachable detail tooltips

**Files:**
- Modify: `game.js`
- Modify: `game.css`

- [x] Give skill/spell detail tooltips a shared readable width, font size, maximum height, and internal scrolling.
- [x] Bind tooltip display to focus and blur as well as mouse enter and leave; keep non-actionable cards readable without making them activate.

### Task 3: Static verification

**Files:**
- Verify: `game.js`, `game.css`

- [x] Run JavaScript syntax and diff whitespace checks; inspect the final diff for unrelated changes.
