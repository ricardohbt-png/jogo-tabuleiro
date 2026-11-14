# Materiais de Armadura em Monstros — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ao gerar monstros que usam armaduras com variantes de material, aplicar 70% armadura comum, 12% Aço Damasco, 12% Obsidiana de Ferro e 6% Liga de Titânio.

**Architecture:** Após configurar o equipamento sorteado/fixo do monstro e antes de equipá-lo, substituir somente IDs-base de armadura que tenham variantes cadastradas. A mesma variante é compartilhada por IDs duplicados no equipamento. Resistências concedidas por uma armadura de monstro são lidas do item ativo para parar quando a peça for destruída. Mantos e couro simples permanecem sem variante.

**Tech Stack:** Python (`server.py`) e documentação de arquitetura (`CLAUDE.md`).

**Spec:** Distribuição aprovada pelo usuário em 2026-11-13.

## Global Constraints

- Manter armas, escudos e armaduras sem variante fora deste sorteio.
- As chances absolutas são 70% comum, 12% Aço Damasco, 12% Obsidiana de Ferro e 6% Liga de Titânio.
- Só sortear variantes para IDs presentes em `_ARMOR_MATERIAL_BASE_IDS` e no catálogo de itens.

## Review Focus

- Armaduras fixas e sorteadas devem receber o mesmo sorteio de material.
- Mantos e Armadura de Couro simples devem permanecer inalterados.
- A armadura escolhida deve continuar preservada em `equipped_items` e no equipamento/loot derivado.

---

### Task 1: Sortear variantes de armadura na criação do monstro

**Files:**
- Modify: `server.py` — adicionar o sorteio de material para IDs-base de armadura e chamá-lo antes de `_aplicar_equipamentos_monstro`.
- Modify: `CLAUDE.md` — registrar escopo, probabilidades e armaduras compatíveis.

**Interfaces:**
- Consumes: `_ARMOR_MATERIAL_BASE_IDS`, `SHOP_ARMORS` material variants e `_DUNGEON_ITEM_CATALOG`.
- Produces: `equipped_items` da instância com o ID comum ou variante correspondente.

- [x] Implementar o sorteio nas probabilidades aprovadas e aplicá-lo às armaduras compatíveis.
- [x] Fazer a redução física da armadura sorteada funcionar para monstros enquanto o item estiver ativo.
- [x] Documentar que a chance é por peça elegível e que mantos/couro simples permanecem comuns.
- [x] Revisar o fluxo de criação e confirmar que os IDs de armadura são mantidos no equipamento e no loot.

### Task 2: Sortear a armadura base do Soldado

**Files:**
- Modify: `server.py` — sortear a peça base do Soldado antes do sorteio de material.
- Modify: `CLAUDE.md` — registrar as probabilidades e o impacto médio estimado.

**Interfaces:**
- Consumes: `equipped_items` da ficha `soldado` e os quatro IDs de armadura aprovados.
- Produces: uma das armaduras selecionadas, seguida pelo sorteio de material existente.

- [x] Sortear Couro e Placas 50%, Cota de Malha 30%, Bronze 15% ou Placas 5%.
- [x] Preservar os demais equipamentos do Soldado e sincronizar `equipped_items`/`equipment`.
- [x] Documentar a chance e revisar o fluxo do spawn.

### Task 3: Sortear a proteção do Bandido

**Files:**
- Modify: `server.py` — sortear a proteção no loadout do Bandido.
- Modify: `CLAUDE.md` — registrar distribuição e impacto esperado.

**Interfaces:**
- Consumes: loadout do Bandido em `_configurar_bandido_spawn` e sorteio de material de armadura.
- Produces: loadout com 40% sem armadura, 30% Manto, 20% Couro e 10% Couro e Placas.

- [x] Inserir somente a armadura sorteada no equipamento, preservando arma e itens existentes.
- [x] Permitir que Couro e Placas passe pelo sorteio de material já definido.
- [x] Documentar valores e revisar o fluxo de spawn/loot.
