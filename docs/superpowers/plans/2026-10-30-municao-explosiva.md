# Munição Explosiva Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrar flechas e virotes explosivos ao combate, às lojas de ferreiro e aos efeitos visuais/sonoros.

**Architecture:** O servidor mantém os tipos, dano e lojas autoritativos. O cliente espelha os tipos aceitos e a preferência de autoequipar flechas; a cena de combate recebe os metadados da munição para detonar no impacto, sincronizando o som e a animação.

**Tech Stack:** Python, JavaScript, JSON, Three.js.

**Spec:** `docs/superpowers/specs/2026-10-30-municao-explosiva-design.md`

## Arquivos e responsabilidades

- `server.py`: itens, tipos aceitos, aljavas/ordem de autoequipar, dano principal e área.
- `src/gameState.js`: espelho cliente de itens/tipos de munição e compatibilidade com venenos.
- `src/ui/inventoryModal.js`: preferência visual de autoequipar flechas explosivas.
- `city_shops.json`: estoques de munição dos cinco ferreiros.
- `src/combatScene.js` e `game.js`: transporte do metadado até o impacto, animação e áudio.
- `src/lang/catalogo.js`, `src/lang/composto.js`, `src/lang/interface.js`: nomes, descrição e rótulos PT/EN.
- `tools/editor_catalog.js`: catálogo derivado, atualizado pelo gerador.
- `CLAUDE.md`: regra durável e vínculo do ícone.

## Tarefas

1. [x] Cadastrar as duas munições por pacote de 5/60 moedas, habilitar cada uma nas armas correspondentes, capacidades de aljava e ordem visual de autoequipar flechas; incluir ambas nos cinco estoques `ferreiro_ammo`.
2. [x] Aplicar +1d6 ao alvo acertado e 1d6 às outras criaturas em raio 1 com Reflexos CD 12 para metade; preservar fogo amigo e exclusão de dano em dobro no alvo principal.
3. [x] Propagar o marcador de munição explosiva pelo `attack_feedback` e disparar animação/som somente no impacto de um acerto em 2D e 3D.
4. [x] Gerar catálogos, completar traduções curtas/PT/EN, documentar a regra e revisar os diffs pertinentes.

## Restrições globais

- Usar o ícone `assets/itens magicos/municao_explosiva.png` para os dois tipos.
- Não alterar as regras de granadas, flechas incendiárias, munição de prata ou sorteio de munição dos monstros.
- Preservar mudanças locais não relacionadas.
- Não adicionar nem executar testes automatizados neste pedido.

## Verificação

- Verificar sintaxe de Python/JavaScript, JSON dos estoques e catálogo exportado.
- Conferir que ambos os IDs estão em todas as cinco lojas e nas listas de compatibilidade/aljava; revisar o caminho visual do impacto.
