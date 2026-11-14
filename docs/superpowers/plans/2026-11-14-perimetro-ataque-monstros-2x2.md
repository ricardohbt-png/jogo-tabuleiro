# Perímetro de ataque dos monstros 2×2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que inimigos 2×2 ataquem corpo a corpo qualquer uma das 12 casas ao redor do footprint, inclusive os cantos diagonais.

**Architecture:** O servidor continua autoritativo e ganha uma geometria de perímetro baseada nas casas realmente ocupadas, válida para 2×2 orientados e não orientados. `game.js` espelha a geometria em validação, mira e prévias. Ataques à distância, altura e entidades não-monstro preservam as regras atuais.

**Tech Stack:** Python, JavaScript.

**Spec:** Escopo aprovado pelo usuário nesta conversa.

## Global Constraints

- Somente atacantes inimigos 2×2 usam o perímetro expandido.
- Alcance corpo a corpo maior que 1 expande o perímetro por anéis de distância Chebyshev.
- Regras verticais e formas de ataques à distância ficam intactas.

## Review Focus

- Molochus orientado deve ameaçar as laterais e retaguarda sem alterar sua orientação de movimento.
- Os quatro cantos diagonais adjacentes devem ser aceitos pelo servidor e pelo cliente.
- Ataques com `reach` maior que 1 devem preservar a distância configurada.
- Heróis transformados e outras entidades 2×2 não-monstro não devem receber a nova regra.
- Prévia do Mestre e ameaça no cliente devem corresponder à validação autoritativa.

---

### Task 1: Geometria autoritativa do servidor

**Files:**
- Modify: `server.py`

- [x] Adicionar uma geometria de perímetro 2×2 baseada em `_monster_tiles` e usá-la para atacantes monstros 2×2 orientados ou não.
- [x] Preservar a geometria existente para entidades 2×2 que não sejam monstros.

### Task 2: Mira e prévias do cliente

**Files:**
- Modify: `game.js`

- [x] Espelhar o perímetro em alcance, preview do Mestre, preview de ameaça e seleção de ataque corpo a corpo.

### Task 3: Documentar e validar

**Files:**
- Modify: `CLAUDE.md`

- [x] Registrar a regra e validar sintaxe, sincronização visual e diff. Testes automatizados não foram executados.
