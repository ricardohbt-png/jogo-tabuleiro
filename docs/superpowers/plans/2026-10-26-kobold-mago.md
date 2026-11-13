# Kobold Mago Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adicionar o Kobold Mago ND 0,75 ao bestiário com magias, item aleatório, saque e miniatura 3D.

**Architecture:** Declarar a ficha no catálogo autoritativo `server.py`; reaproveitar conjuração e loot de kobold, generalizando o consumo de slots para qualquer conjurador com limite explícito. Registrar o modelo na tabela central do cliente e regenerar o catálogo do editor pelo exportador oficial.

**Tech Stack:** Python, JavaScript, GLB.

**Spec:** `docs/superpowers/specs/2026-10-26-kobold-mago-design.md`

## Global Constraints

- Preservar alterações locais já existentes.
- As três chances de equipamento de cabeça são mutuamente exclusivas.
- O kobold mantém a chance de alimento já usada pelas variantes `kobold_`.
- Não adicionar spawn automático nem alterar outros monstros.
- Não executar testes nesta alteração.

## Review Focus

- Limite total de três magias mesmo conhecendo duas.
- Efeito mágico e saque correspondem ao item de cabeça sorteado.
- Moedas ficam no intervalo inclusivo de 5 a 20.
- Miniatura 3D aponta ao GLB empacotado, preservando as versões externas.
- O catálogo de monstros do editor continua gerado pela fonte oficial.

## Tasks

1. Adicionar a ficha ND 0,75, 3 slots, sorteio de duas entre cinco magias existentes e sorteio exclusivo de item de cabeça em `server.py`.
2. Generalizar o débito e o limite de slots; aplicar bônus de magia dos itens de cabeça ao conjurador monstro.
3. Integrar moedas e item equipado ao saque do novo kobold, mantendo o drop de comida.
4. Copiar o GLB colorido para `assets/models3d/monstros/kobold_mago.glb`, criar a miniatura PNG 2D em `assets/pawns/monstros/kobold_mago/kobold_mago.png` e vinculá-los ao tipo em `game.js`/`server.py`.
5. Regenerar `tools/editor_catalog.js` com `tools/export_catalog.py` e registrar contratos relevantes em `CLAUDE.md`.
