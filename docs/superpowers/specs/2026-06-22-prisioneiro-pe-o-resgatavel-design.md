# Peão de prisioneiro resgatável e editável — Design

**Data:** 2026-06-22
**Branch:** feat/hud-paladino-richard

## Objetivo

No editor de mapa de "resgate do prisioneiro", a casa onde se coloca o
prisioneiro deve conter um **peão** que, após o resgate, **segue o herói que o
resgatou**. O peão pode sofrer ataques dos inimigos; sua morte **falha a missão
de resgate**. Stats: **CA 10**, **movimento de 6 quadrados**, **7 pontos de
vida**. O peão deve ter **imagem/miniatura editável** (upload de imagem própria
por prisioneiro).

## Contexto

O sistema de prisioneiro já existe (Fase 3 do editor de masmorras). Estado atual:

- `server.py`: `PRIS_HP = 12`; instanciação em `server.py:3653`; liberação em
  `handle_libertar_prisioneiro`; movimento+dano em `_processar_prisioneiro_turno`
  (1 passo em direção ao herói **mais próximo** + dano automático 2–5 de monstros
  adjacentes); objetivo `rescue_prisoner` em `_objetivo_cumprido`/`_objetivo_status`
  (morte → `rescue_failed`).
- `tools/editor.js`: ferramenta `prisoner` posiciona o peão (emoji 🧍); painel em
  `editor.js:233`; serialização em `buildJSON` (`editor.js:291`) e load em
  `editor.js:359`.
- `game.js`: renderizado **apenas no 2D** (`game.js:4903`, emoji ⛓️/🧍 + barra de
  HP). **Não é desenhado no 3D.**
- `d20_attack(atk_bonus, target_ac)` (`server.py:80`) já existe; monstros têm
  `atk_bonus`. `tools/story_upload.js` tem um pipeline genérico de upload por
  WebSocket (`request(type, fields)`), hoje exposto só como `STORY_UPLOAD.upload`
  (salva em `assets/story/` via `_save_story_upload`).

## Decisões (confirmadas com o usuário)

1. **Imagem:** upload de arquivo próprio (reaproveita o upload por WebSocket).
   Salvo em `assets/pawns/prisioneiros/`. Caminho gravado no JSON da masmorra.
2. **Falha:** morte do prisioneiro marca `rescue_failed` (semântica atual). Se o
   resgate for objetivo principal, a masmorra fica inconcluível; se secundário,
   o grupo perde só o bônus.
3. **Ameaça:** monstros atacam o prisioneiro **só quando adjacentes** (não o
   caçam). Continuam mirando heróis.
4. **Movimento:** logo **após o turno do resgatador**, até 6 quadrados em direção
   a ele, parando ao ficar adjacente.
5. **3D:** renderizar o prisioneiro em **2D e 3D** (billboard com a imagem),
   corrigindo o fato de ele sumir no 3D hoje.
6. **Fallback:** sem imagem, usa o emoji atual (⛓️ cativo / 🧍 liberto).

## Mudanças

### 1. Stats (server.py)

- Constantes: `PRIS_HP = 12` → `7`; adicionar `PRIS_AC = 10`, `PRIS_MOVE = 6`.
- Instanciação (`server.py:3653`): o dict `prisoner` ganha
  `"ac": PRIS_AC`, `"move": PRIS_MOVE`, `"image": pr.get("image")`,
  `"rescuer_pid": None`.
- `_validate` (`server.py:1760`): aceitar `prisoner.image` opcional (se presente,
  deve ser string).

### 2. Movimento — segue o resgatador, após o turno dele

- `handle_libertar_prisioneiro`: ao libertar, gravar
  `self.prisoner["rescuer_pid"] = pid`.
- Novo `_mover_prisioneiro_seguindo(ended_pid)`, chamado no fim de **cada** turno
  de herói (hook no fluxo de `end_turn`/avanço de turno), com o pid que encerrou:
  - Sai se não houver prisioneiro liberto/vivo.
  - Se `rescuer_pid` aponta para herói morto/ausente, reatribui ao herói vivo
    mais próximo (segue um único alvo; sem caminho duplicado). Fazer essa
    verificação **antes** de comparar com `ended_pid`, para que a morte do
    resgatador não trave o prisioneiro.
  - Só **move** se `ended_pid == rescuer_pid`. Aí dá até `PRIS_MOVE` (6) passos
    via `_step_towards` em direção à posição do resgatador, **parando ao ficar
    adjacente** (Chebyshev ≤ 1) ou quando não há progresso.
- Remover a parte de **movimento** de `_processar_prisioneiro_turno`.

### 3. Ameaça — CA 10 (fase inimiga)

- `_processar_prisioneiro_turno` mantém **só o dano**:
  - Para cada monstro vivo **adjacente** ao prisioneiro, rolar
    `d20_attack(m["atk_bonus"], PRIS_AC)`.
  - Em acerto, aplicar o dano da arma do monstro (mesmo cálculo já usado contra
    heróis — reutilizar a rolagem de dano existente do monstro).
  - HP ≤ 0 → `alive = False`, `rescue_failed = True`, narração de morte (mantida).

### 4. Imagem editável (upload)

- **server.py:**
  - Helper de gravação de imagem em `assets/pawns/prisioneiros/` (só extensões de
    imagem; mesma proteção contra path-traversal e limite de tamanho do
    `_save_story_upload`). Pode ser uma generalização de `_save_story_upload`
    parametrizada por diretório + extensões permitidas.
  - Novo handler de mensagem `upload_prisoner` (perto de `server.py:12377`),
    respondendo `upload_result` com o nome salvo.
  - Confirmar que a rota estática (`process_request`) serve
    `assets/pawns/prisioneiros/` (subpasta de `assets/`, já permitida).
- **tools/story_upload.js:** expor `window.PRISONER_UPLOAD.upload(file)`
  reaproveitando `request()` (mensagem `upload_prisoner`, retorna o nome salvo).
- **tools/editor.js:**
  - Painel do prisioneiro (`editor.js:233`): preview da imagem atual, `<input
    type=file accept="image/*">` e linha de status.
  - Ao escolher arquivo: `PRISONER_UPLOAD.upload(file)` → em sucesso,
    `S.prisoner.image = nome`; re-render. Em erro (servidor offline), mostrar
    status de falha.
  - `buildJSON` (`editor.js:291`): incluir `image: S.prisoner.image` quando houver.
  - Load (`editor.js:359`): preservar `image` (já vem em `obj.prisoner`).

### 5. Renderização (game.js)

- **2D (`game.js:4903`):** se `_pris.image`, desenhar a imagem (loader de imagem
  por URL no padrão das miniaturas de herói em `game.js:4295`); senão, fallback
  para o emoji atual. Barra de HP e label mantidos.
- **3D:** adicionar o prisioneiro à cena como billboard (`_makeBillboardSprite`,
  igual a heróis/monstros) usando `_pris.image`; sem imagem, billboard de
  fallback. Inserir no ponto de sync 3D onde heróis/monstros são construídos.

### Serialização

`self.prisoner` já é serializado inteiro em `push_state` (`server.py:12327`); os
novos campos (`ac`, `move`, `image`, `rescuer_pid`) acompanham automaticamente.

## Fora de escopo

- Mudar a IA de alvo dos monstros (não caçam o prisioneiro).
- Presets de imagem (só upload).
- Alterar o protocolo de objetivos.

## Critérios de sucesso

- Prisioneiro nasce com 7 HP, CA 10, movimento 6 e (opcional) imagem.
- Após libertado, segue o resgatador (até 6/turno, parando adjacente); se o
  resgatador morre, segue o herói vivo mais próximo.
- Monstros adjacentes rolam d20+atk vs CA 10; podem matá-lo → falha o resgate.
- Imagem escolhida no editor aparece no peão em 2D e 3D; sem imagem, usa emoji.
- Masmorras antigas (sem `image`) continuam funcionando.
