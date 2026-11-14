# Espadas do Veredito Radiante — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adicionar as versões mágicas +1 e +3 da espada bastarda exclusiva do Paladino, com o poder sagrado aprovado, e vendê-las nos cinco ferreiros.

**Architecture:** `server.py` é a fonte autoritativa para armas, dano, cooldown e protocolo de escolha; `city_shops.json` define o estoque de cada ferreiro. O exportador publica os metadados no catálogo do editor e as traduções PT/EN mostram nome e descrição.

**Tech Stack:** Python, JavaScript, JSON, PNG.

**Spec:** contrato aprovado nesta conversa.

## Global Constraints

- Perfil: 1d10 cortante + Força; crítico natural 19–20, multiplicador ×2.
- Exclusivas do Paladino; +1 custa 3.000 moedas e +3 custa 8.000.
- Poder escolhido após acerto: +2d8 sagrado, recarga de 10 rodadas.
- Versão +3 também causa +2d8 sagrado em crítico natural; não multiplica o dado e não acumula com o poder manual no mesmo golpe.
- Preservar as alterações locais não relacionadas; sem executar suítes de teste.

## Implementation Tasks

- [x] Adicionar armas e resolução autoritativa do dano/cooldown/escolha em `server.py`, preservando os campos da arma no fluxo de compra/equipamento.
- [x] Adicionar apresentação da escolha e traduções PT/EN em `game.js`, `src/gameState.js` e `src/lang/*` conforme o protocolo do projeto.
- [x] Adicionar os IDs aos cinco ferreiros em `city_shops.json`; exportar para `tools/editor_catalog.js`.
- [x] Vincular os dois PNGs existentes, atualizar `CLAUDE.md` e conferir diferenças, sintaxe/JSON e presença dos itens/estoques/ícones.
