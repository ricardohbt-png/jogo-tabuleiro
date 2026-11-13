# Boinas do Batedor e do Alerta — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cadastrar e implementar as duas boinas aprovadas, com bônus passivos e venda nas cinco cidades.

**Architecture:** Definir os itens em `SHOP_MERCHANT`, reutilizar o efeito de visão já suportado e adicionar um modificador reversível de salvaguarda ao caminho comum de equipamento/testes de resistência. Atualizar as allowlists explícitas e regenerar os catálogos derivados.

**Tech Stack:** Python, JSON, catálogos JavaScript gerados.

**Spec:** `docs/superpowers/specs/2026-10-26-boinas-do-batedor-e-do-alerta-design.md`

## Global Constraints

- Boina do Batedor: 60 moedas, +1 visão.
- Boina do Alerta: 150 moedas, +1 visão e +1 em todos os testes de resistência.
- Ambas usam `assets/itens/chapeu1.png`, ocupam o slot `head`, sem restrições de classe.
- Adicionar às listas `mercador` nas cinco cidades; preservar demais alterações locais.
- Não adicionar nem executar testes nesta tarefa.

## Review Focus

- O bônus de salvaguarda soma com modificadores temporários e é revertido ao desequipar: inspecionar `_apply_single_effect`, `_apply_gear_effect` e `_testar_save`.
- O item aparece em cada allowlist de mercador: conferir os cinco arrays `mercador` em `city_shops.json`.
- Nomes, descrições, ícone e preços aparecem nos catálogos: conferir os arquivos gerados e seu diff.
- Nenhuma alteração preexistente fora do escopo é removida: revisar `git diff` dos arquivos tocados.

### Task 1: Efeitos passivos e catálogo dos itens

**Files:**
- Modify: `server.py`
- Modify: `CLAUDE.md`

**Interfaces:**
- `vision` permanece sendo o efeito principal de cada item.
- O novo efeito de bônus de salvaguarda deve ser aplicado/removido por `_apply_single_effect` e considerado em `_testar_save`.

- [x] Adicionar as duas entradas ao catálogo com IDs, preço, ícone, `item_slot: head`, descrição e bônus aprovados.
- [x] Adicionar suporte reversível ao efeito `save_bonus` e somá-lo nos testes de resistência.
- [x] Atualizar a entrada de arquitetura correspondente em `CLAUDE.md` após finalizar os arquivos de catálogo.

### Task 2: Estoque e catálogos derivados

**Files:**
- Modify: `city_shops.json`
- Regenerate: `src/lang/catalogo.js`
- Regenerate: `tools/editor_catalog.js`

- [x] Acrescentar os dois IDs à allowlist `mercador` de cada cidade.
- [x] Rodar `python -X utf8 tools/gerar_vocabulario.py` e preencher as traduções em inglês dos dois itens.
- [x] Rodar `python -X utf8 tools/export_catalog.py`.

### Task 3: Revisão estática

- [x] Validar a sintaxe Python alterada sem executar testes.
- [x] Validar o JSON e conferir os dois IDs e preços em cada mercador.
- [x] Revisar o diff final dos arquivos deste plano, preservando as alterações que já estavam no workspace.
