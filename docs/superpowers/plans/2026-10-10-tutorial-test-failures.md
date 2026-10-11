# Tutorial Test Failures Repair Plan

> **For agentic workers:** Execute this plan task by task and verify each affected suite.

**Goal:** Resolve the five reproduced tutorial test failures while preserving the intended class-room onboarding and replay flow.

**Architecture:** Keep tutorial copy in `tools/tutorial_guia_*.py` and regenerate `src/lang/tutorial_guia.js`. Keep progression authoritative in `server.py` and `tutorial_training.py`; update tests only where their setup or expected replay order no longer matches authored lessons.

**Tech Stack:** Python unittest, authored dungeon JSON, generated JavaScript localization.

**Spec:** Existing Campo de Treinamento flow and class H-menu lessons.

## Global Constraints

- Do not hand-edit generated localization output; regenerate it from the guide source.
- Preserve the H-menu lesson before class exercises and preserve room replay reset behavior.
- Do not modify unrelated dirty worktree changes.

## Review Focus

- H-menu assignment copy remains concise and actionable in Portuguese and English.
- UI tutorial steps begin with a clear action verb.
- Replaying a class room restarts its first H-menu lesson and resets the room's exercise state.
- The bridge test models all preceding common lessons before testing a class-specific bridge.

### Task 1: Tutorial guide copy

**Files:** `tools/tutorial_guia_comum.py`, `tools/test_tutorial_conteudo.py`, generated `src/lang/tutorial_guia.js`.

- [ ] Shorten the H-menu assignment copy to the 15-word limit.
- [ ] Rephrase the 11 UI steps so each starts with a recognized action verb.
- [ ] Regenerate the localization file and run `tools/test_tutorial_conteudo.py`.

### Task 2: Room replay expectations

**Files:** `tools/test_tutorial_salas.py`, `tools/test_tutorial_refem.py`, `tools/test_tutorial_bardo_instrumento.py`, `tools/test_tutorial_clerigo_magias.py`, `tutorial_training.py` only if an updated test exposes a real behavior bug.

- [ ] Assert that replay restarts at the H-menu lesson before the class exercises.
- [ ] Verify the prisoner/trap state still resets and class-independent history remains.
- [ ] Align Bard, Cleric, and hostage expectations with the H-menu/M-menu stages now authored before class abilities.
- [ ] Run `tools/test_tutorial_salas.py`.

### Task 3: Bridge flow setup

**Files:** `tools/test_tutorial_portas.py`.

- [ ] Mark the full preceding common intro/combat sequence complete in the simulated setup.
- [ ] Run `tools/test_tutorial_portas.py` and the affected tutorial suites together.

### Task 4: Resistance tutorial expectations

**Files:** `tools/test_tutorial_cores.py`, `tools/test_tutorial_hostilidade.py`.

- [ ] Verify damage colors against the stationary dummy now used by the lesson.
- [ ] Align the optional hostility wing expectations with the authored map, which has no skeleton tutorial encounters.
- [ ] Run every `tools/test_tutorial_*.py` suite.
