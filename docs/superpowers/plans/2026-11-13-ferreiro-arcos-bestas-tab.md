# Aba de Arcos e Bestas do Ferreiro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Separar os 44 arcos/bestas e variantes de materiais em uma nova aba do ferreiro.

**Architecture:** Filtrar no cliente a lista existente de `ferreiro_weapon`, mantendo o mesmo `shopKey` para compra. Atualizar os índices relativos de abas do ferreiro; a aba conversas, quando presente, permanece deslocada pelo offset existente.

**Tech Stack:** JavaScript, catálogo de interface PT/EN.

**Spec:** `docs/superpowers/specs/2026-11-13-ferreiro-arcos-bestas-tab-design.md`

## Global Constraints

- Nova aba logo após **Armas**; munição permanece separada.
- As 11 armas-base e suas 33 variantes de materiais entram na nova aba.
- Estoques e fluxo de compra existentes não mudam.

## Review Focus

- A classificação deve capturar todas as 44 armas e não as munições ou armas corpo a corpo.
- Reparar e vender continuam ligados aos índices corretos com e sem aba de conversas.
- Compras na nova aba continuam usando `ferreiro_weapon`.

## Implementation

- [x] Adicionar a chave de aba PT/EN e a aba após **Armas** em `src/lang/interface.js` e `game.js`.
- [x] Filtrar arcos/bestas pelo ID-base, incluindo variantes, e corrigir índices de armaduras, munição, reparo e venda em `game.js`.
- [x] Atualizar `CLAUDE.md`; conferir sintaxe e diff. Não executar suítes de teste.
