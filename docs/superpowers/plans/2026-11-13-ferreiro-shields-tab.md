# Aba de Escudos do Ferreiro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Exibir os 23 escudos atuais do ferreiro em uma aba própria.

**Architecture:** Filtrar `shops.ferreiro.armors` por `kind === "shield"` no cliente; conservar `ferreiro_armor` como identificador usado para comprar. Reindexar munição, reparo e venda pela posição nova das abas.

**Tech Stack:** JavaScript e catálogo de interface PT/EN.

**Spec:** `docs/superpowers/specs/2026-11-13-ferreiro-shields-tab-design.md`

## Global Constraints

- A nova aba **Escudos** vem depois de **Armaduras**.
- Todos os itens com `kind === "shield"` entram nela; armas e outros equipamentos ficam fora.
- Não modificar preços, restrições, nem estoques das cidades.

## Review Focus

- Os escudos básicos, variantes de materiais e especiais passam para a nova aba.
- Itens de armadura sem `kind === "shield"` continuam na aba **Armaduras**.
- Munição, reparo, venda, compra e índice deslocado por conversas continuam corretos.

## Implementation

- [x] Adicionar rótulo PT/EN e aba do ferreiro em `game.js` e `src/lang/interface.js`.
- [x] Filtrar armaduras/escudos por `kind`, manter `ferreiro_armor` na compra e ajustar os índices seguintes em `game.js`.
- [x] Atualizar `CLAUDE.md`; conferir sintaxe e diff sem executar suítes de testes.
