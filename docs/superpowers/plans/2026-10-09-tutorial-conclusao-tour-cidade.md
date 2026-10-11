# Tutorial Conclusion and City Tour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Congratulate the party when the training mission can be concluded, then guide each player through the city shops after the return.

**Architecture:** Keep mission completion authoritative on the server. The server marks only the `treinamento` adventure in the tutorial payload; the client captures its completion-pending signal before the dungeon state is cleared, then starts a per-account persisted city tour on return. The tour reuses city markers, shop modals, and Master-at-Arms art already in the project.

**Tech Stack:** Python WebSocket game server, browser JavaScript, CSS, existing language dictionaries.

**Spec:** `docs/superpowers/specs/2026-10-09-tutorial-conclusao-tour-cidade.md`

## Global Constraints

- Only `tutorial.tour_cidade` completion starts the feature.
- Preserve current mission confirmation, shop behavior, stock, and purchase rules.
- Persist tour state per account in browser `localStorage`; do not auto-replay after completion or skip.
- Keep city tour text localized for Portuguese and English.
- Do not change the pending tutorial dialogue-box sizing/cropping request.
- Do not add or run automated tests unless requested; perform syntax and diff checks only.

## Review Focus

- A normal dungeon return must not trigger this tour.
- A return from the tutorial must remain detectable after `gameState` is cleared.
- City updates and shop purchases must not restart or advance the active tour unexpectedly.
- Missing or hidden shop markers must not leave the tour stuck.
- Closing/reloading a shop must preserve the current step and allow resuming.

### Task 1: Completion message and transition signal

**Files:**
- Modify: `server.py`
- Modify: `game.js`

- [x] Add a localized congratulations panel with the existing Master-at-Arms portrait to the objectives HUD only when the tutorial mission is ready to finish.
- [x] Add `tutorial.tour_cidade` to the server payload only for the `treinamento` adventure, and capture that + mission-complete-pending in client memory before the client clears the dungeon state.
- [x] Consume that signal only on the transition from the game screen to the city screen.

### Task 2: Persisted guided city tour

**Files:**
- Modify: `game.js`
- Modify: `game.css`
- Modify: `src/lang/tutorial.js`

- [x] Add account-scoped tour state with intro, current shop, visit, next, finish, skip, and resume behavior.
- [x] Find each stop from the visible `city_map_points` markers and spotlight the current marker.
- [x] Intercept the current marker click to show its localized explanation and open its existing shop.
- [x] Keep the tour card above the shop, and on “continue” call `closeShop()` and advance.
- [x] Include the Guilda and Caravana in the final guidance; skip unavailable shop types.
- [x] Defer tour startup until any city story beat finishes; do not repeat while a tour card is already active.
- [x] Add responsive styling and Portuguese/English text for all steps and controls.

### Task 3: Project documentation and static verification

**Files:**
- Modify: `CLAUDE.md`

- [x] Document the completion signal, tour persistence, stops, and localization source.
- [x] Run `node --check game.js` and confirm syntax success.
- [x] Run `git diff --check` and confirm no whitespace errors.
- [x] Review the final diff to ensure no tutorial dialogue-box sizing rules changed.
