# Chapéu do Aventureiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adicionar o Chapéu do Aventureiro como equipamento funcional e comprável.

**Architecture:** Usar os efeitos nativos de item `vision` e `initiative`, sem lógica especial. O servidor mantém o catálogo autoritativo; os estoques de cidade e os arquivos de catálogo/localização são derivados e atualizados pelos geradores existentes.

**Tech Stack:** Python, JSON, catálogo de tradução em JavaScript.

**Spec:** `docs/superpowers/specs/2026-10-30-chapeu-aventureiro-design.md`

## Arquivos e responsabilidades

- `server.py`: definição autoritativa, preço, slot, classes e bônus.
- `city_shops.json`: disponibilidade nos cinco mercadores.
- `src/lang/catalogo.js`: nomes e descrição localizados, via gerador.
- `tools/editor_catalog.js`: catálogo exportado para o editor.
- `CLAUDE.md`: registro durável das regras do item.
- `assets/itens/chapeu_aventureiro.png`: ícone já existente, referenciado pelo item.

## Tarefas

1. [x] Adicionar a definição em `server.py`: preço 120, `item_slot: head`, efeito `vision: +1`, bônus adicional `initiative: +1`, sem restrição de classe.
2. [x] Incluir o ID nos cinco estoques de mercador em `city_shops.json`.
3. [x] Executar os geradores existentes de vocabulário e catálogo do editor; conferir nome, descrição, ícone e ID exportados.
4. [x] Documentar o item em `CLAUDE.md` e revisar os diffs relacionados.

## Restrições globais

- Preservar alterações locais preexistentes não relacionadas.
- Reutilizar os efeitos de equipamento existentes, sem mudar suas fórmulas.
- Não alterar ou criar testes automatizados neste pedido.

## Verificação

- [x] Validar sintaxe Python de `server.py`, JSON de `city_shops.json` e sintaxe dos catálogos JavaScript.
- [x] Conferir estaticamente a definição autoritativa, cinco estoques e as entradas geradas de tradução/editor.
- Testes automatizados não foram adicionados nem executados.
