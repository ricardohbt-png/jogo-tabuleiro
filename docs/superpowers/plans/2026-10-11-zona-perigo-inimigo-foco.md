# Zona de Perigo de Inimigo em Foco Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar, ao focar um inimigo percebido, a área ampla que ele pode ameaçar sem revelar alvo ou decisão futura da IA.

**Architecture:** O estado selecionado/hover do inimigo é estado de UI separado da regra do jogo. A projeção visual usa a geometria autoritativa de movimento/ataque já serializada e desenha o mesmo conjunto de casas no canvas 2D e no tabuleiro Three.js, filtrado pela percepção do jogador.

**Tech Stack:** JavaScript (`src/gameState.js`, `game.js`, `game.css`), protocolo de estado existente em `server.py` se a percepção não bastar no cliente.

**Spec:** [2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md](../specs/2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md), seção 1.

## Global Constraints

- Hover/foco no inimigo visível ativa a sobreposição; perder foco ou mudar alvo a remove.
- Teclado e controle têm o mesmo resultado visual do mouse.
- A indicação é uma ameaça possível e ampla, nunca o alvo ou plano futuro escolhido pela IA.
- Não revelar inimigos ou casas fora do campo de percepção.
- Não alterar movimento, alcance real, IA ou combate.
- Geometrias de habilidades que não possam ser projetadas fielmente ficam fora da área até haver representação correta.

## Review Focus

- Monstros com footprint 2×2, orientado ou grande: área deve acompanhar todas as casas ocupadas.
- Ataque à distância: respeitar linha de visão, paredes e altura quando a projeção for exata.
- Efeito de névoa/cegueira e clarividência: não vazar casas fora da visão atual.
- Foco via navegação por teclado/controle: não depender exclusivamente de eventos de mouse.
- Campo de teste e modo Mestre: preservar as prévias já existentes e evitar sobreposição conflitante.

---

### Task 1: Definir e obter estado de foco

**Files:**
- Modify: `src/gameState.js` (estado visual/foco, somente se estado selecionado ainda não for exposto)
- Modify: `game.js` (hover, seleção de alvo e foco de teclado/controle)

**Interfaces:**
- Produces: `_monsterThreatFocusId()` ou getter equivalente que retorne ID estável do monstro em foco, ou `null`.
- Reuses: `_masterMonsterAtTileClient`, seleção/foco atual de entidades e `GS.monsterTiles`.

- [ ] Mapear os caminhos existentes de foco para mouse, teclado e gamepad; reutilizar o estado comum em vez de criar seleções paralelas.
- [ ] Garantir que o foco só retorne monstro vivo e percebido pelo jogador local; limpar ao mudar de fase, alvo ou estado de visibilidade.
- [ ] Não alterar comandos do Mestre nem estado de mira de magias/itens.

### Task 2: Calcular conjunto de casas ameaçadas

**Files:**
- Modify: `src/gameState.js` (função pura de projeção, se depender apenas do estado serializado)
- Modify: `server.py` (somente se regras necessárias à projeção não forem expostas com segurança no payload)
- Modify: `game.js` (chamada e cache invalidado por `game_state`/foco)

**Interfaces:**
- Produces: `monsterThreatTiles(state, monster) -> Set<string>` ou lista de `[x,y]`, sem alvo associado.
- Consumes: footprint, ataques, alcance, linha de visão, elevação e obstáculos existentes.

- [ ] Cobrir movimento possível mais ataques básicos verificáveis, limitando a área pelo movimento real e custos/obstáculos existentes.
- [ ] Cobrir footprint e orientação por funções `GS` já usadas pelo cliente.
- [ ] Aplicar paredes/linha de visão e elevação somente onde o contrato existente permite calcular o mesmo resultado do servidor; omitir geometrias não confiáveis.
- [ ] Filtrar resultado pela visão do herói local antes de qualquer desenho; invalidar cache ao mudar posição, estado, percepção, obstáculo ou foco.

### Task 3: Desenhar overlay equivalente em 2D e 3D

**Files:**
- Modify: `game.js` (`renderMap`, `renderMap3D`, helpers de overlay e eventos de foco)
- Modify: `game.css` (legenda discreta, se necessário)
- Modify: arquivos autoritativos de idioma PT/EN

**Interfaces:**
- Consumes: ID focado e conjunto de casas da Task 2.
- Produces: realce visual comum com legenda localizada de “área que pode oferecer perigo”.

- [ ] Desenhar as mesmas casas no canvas 2D e como overlay no chão 3D sem alterar geometria de movimento.
- [ ] Usar cor/legenda distinta de casas de movimento, alcance de ataque do jogador e áreas de magia.
- [ ] Limpar overlay ao perder foco, retirar percepção, incapacitar ou remover o monstro.
- [ ] Revisar alinhamento de grade e conflitos visuais com overlays existentes, incluindo Mestre e modo de teste.
