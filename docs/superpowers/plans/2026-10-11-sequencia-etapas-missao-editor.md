# Sequência de Etapas de Missão no Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que autores organizem uma missão em etapas ordenadas e condicionais no editor de masmorras, com avanço autoritativo no servidor e acompanhamento no HUD.

**Architecture:** Um campo opcional `objectives.steps` viaja com a definição da masmorra. O editor-fonte valida e preserva as etapas; o servidor deriva status e avanço usando condições de objetivo existentes, e o HUD apenas renderiza o estado recebido.

**Tech Stack:** JavaScript (`tools/editor.js`, `game.js`), Python (`server.py`), JSON de masmorras.

**Spec:** [2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md](../specs/2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md), seção 3.

## Global Constraints

- Preservar `objectives.primary` e `objectives.secondary`; a lista opcional de etapas é campo adicional.
- Uma masmorra sem etapas deve manter o comportamento atual.
- Usar somente condições já avaliadas por `_objetivo_cumprido`.
- Não criar avanço manual por botão nem recompensas por etapa.
- A última condição deve corresponder ao objetivo principal, mantendo recompensas e conclusão atuais.
- Texto das instruções tem versão portuguesa e inglesa.

## Review Focus

- Arquivos antigos sem `steps` e round-trip carregar/salvar sem perda.
- Condição de etapa satisfeita antes de ela ficar ativa: avanço imediato sem perder o evento.
- Objetivo de saída e saídas alternativas: não concluir missão antes do fluxo existente.
- Reordenação, exclusão e IDs duplicados: estado não pode apontar para uma etapa errada.
- Reconexão no meio da missão: todos os jogadores recebem o mesmo índice e estado.

---

### Task 1: Campo opcional e validação autoritativa

**Files:**
- Modify: `server.py` (carregamento/validação de masmorra, payload e checkpoint de missão)

**Interfaces:**
- Produces: `objectives.steps: [{id, text:{pt,en}, condition:{type,...}}]` quando lista autorada não vazia.
- Reuses: `_objetivo_cumprido(obj)`, `_objetivo_status(obj)`, `_check_objectives()`.

- [ ] Definir validação de sequência opcional: IDs únicos, textos PT/EN não vazios, tipo conhecido e última condição com mesma definição do objetivo principal.
- [ ] Manter arquivos sem `steps` em forma legada, sem inserir sequência implícita.
- [ ] Derivar `mission_step_status` no servidor (`active`, `done`, `locked`) e estado atual persistido na foto/checkpoint da partida.
- [ ] Quando uma etapa se torna ativa, avaliar imediatamente sua condição; avançar em cadeia se etapas seguintes também estiverem satisfeitas.
- [ ] Integrar o avanço após os pontos de atualização já usados por `_check_objectives`, sem conceder recompensa adicional nem alterar `mission_complete_pending`.

### Task 2: Edição, round-trip e validação visual

**Files:**
- Modify: `tools/editor.js` (painel de objetivos, carregar, serializar, validar)
- Do not edit: `tools/editor_dungeons.js` (snapshot gerado)

**Interfaces:**
- Consumes: formato `objectives.steps` da Task 1.
- Produces: UI de adicionar, remover e mover etapas, com condição e texto bilíngue.

- [ ] Adicionar lista reordenável no painel atual de objetivos, oferecendo as sete condições já suportadas pelo servidor.
- [ ] Persistir IDs estáveis por etapa, texto PT/EN e parâmetros da condição no JSON da masmorra.
- [ ] Carregar e salvar preservando propriedades desconhecidas e os objetivos primário/secundários existentes.
- [ ] Impedir salvar quando houver etapa incompleta, ID repetido ou última condição diferente do objetivo principal; apresentar explicação junto ao campo inválido.
- [ ] Confirmar por revisão do ciclo de código do editor que abrir → reordenar → salvar → reabrir mantém ordem, conteúdo e condições.

### Task 3: HUD de etapas

**Files:**
- Modify: `game.js` (`renderObjectivesHUD` e tradução do objetivo)
- Modify: `game.css` (estado visual das etapas, se necessário)
- Modify: arquivos autoritativos de idioma da UI (PT/EN)

**Interfaces:**
- Consumes: `mission_step_status` enviado pelo servidor.
- Produces: lista de etapas no painel de objetivos existente, mantendo tecla O e botão compacto.

- [ ] Renderizar etapa ativa em destaque, concluídas como concluídas e futuras como secundárias; não inferir progresso a partir do texto.
- [ ] Manter objetivos principal/secundários, progresso de saídas, recompensas e botão de encerrar missão.
- [ ] Resolver texto PT/EN a partir do idioma atual do cliente e escapar texto autorado antes de inserir no HTML.
- [ ] Conferir estado legada sem sequência e missão salva retomada no meio da sequência sem regressão de layout ou de encerramento.
