# Punhais do Assassino Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adicionar duas adagas mágicas com bônus progressivos e dados adicionais somente no Ataque Furtivo do Ladino.

**Architecture:** `server.py` continua sendo a fonte autoritativa para as armas e o cálculo de dano. O catálogo gerado pelo servidor inclui o metadado novo, enquanto `CLAUDE.md` registra os preços e regras.

**Tech Stack:** Python, catálogo JavaScript gerado.

**Spec:** `docs/superpowers/specs/2026-11-07-punhal-do-assassino-design.md`

## Global Constraints

- Preservar os atributos atuais da Adaga.
- Aplicar dados extras apenas a Ataque Furtivo acertado do Ladino.
- Usar a imagem `assets/itens magicos/punhal_do_assassino.png`.
- Preservar todas as mudanças preexistentes na árvore de trabalho.

## Review Focus

- Ataque comum com o punhal não rola dados furtivos adicionais.
- Ataque Furtivo com cada versão soma exatamente 1d4 ou 2d4 à progressão existente.
- O dano furtivo total continua entrando antes das resistências e reduções.
- O item e sua descrição aparecem no catálogo gerado do editor.

### Task 1: Definição e resolução de combate

**Files:** `server.py`

- [x] Adicionar ambos os IDs a `WEAPONS` e `SHOP_WEAPONS`, copiando os atributos da Adaga, incluindo preço, ícone, raridade/descrição, bônus mágico e metadado `sneak_attack_extra_d4`.
- [x] Somar esse metadado ao total de d4 somente nos fluxos autoritativos de Ataque Furtivo do Ladino: ataque principal acertado e reações furtivas; incluir a mesma quantidade na prévia de dano.
- [x] Conferir compilação Python e que os campos de loja e combate coincidem para os dois IDs.

### Task 2: Catálogo e documentação

**Files:** `tools/export_catalog.py`, `tools/editor_catalog.js` (gerado), `CLAUDE.md`

- [x] Exportar o novo metadado de arma no catálogo do editor e regenerar o arquivo usando `python tools/export_catalog.py`.
- [x] Documentar nome, propriedades, gatilho, ícone e preço das duas versões em `CLAUDE.md`.
- [x] Conferir o catálogo exportado e o diff final, sem alterar dados não relacionados.
