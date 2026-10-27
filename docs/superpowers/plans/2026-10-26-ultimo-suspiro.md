# Último Suspiro Implementation Plan

> **For agentic workers:** executar as etapas neste turno no workspace atual, preservando alterações preexistentes. Não adicionar nem executar testes automatizados.

**Goal:** Adicionar o acessório Último Suspiro com uma proteção por cópia equipada e elevar Último Esforço para 700 moedas.

**Architecture:** O servidor continua autoritativo para equipamento, preço e prevenção de morte. Cada cópia equipada em `item1` ou `item2` é uma carga consumível; o catálogo do editor é regenerado pelo exportador existente.

**Tech Stack:** Python, JSON, JavaScript de catálogo gerado.

**Spec:** `docs/superpowers/specs/2026-10-26-ultimo-suspiro-design.md`

## Global Constraints

- Cada cópia equipada custa 500 moedas e evita uma morte, deixando o herói com 1 PV.
- No máximo duas cópias podem estar equipadas pelos espaços de item existentes.
- Último Esforço custa 700 moedas; seus efeitos e recarga atuais não mudam.
- Nenhum teste será criado ou executado neste pedido.

## Review Focus

- Consumir apenas uma cópia por evento letal; manter a segunda equipada para o próximo evento.
- Uma cópia na bolsa não pode prevenir morte.
- Último Esforço continua funcionando quando não restarem cópias equipadas.
- O efeito não se aplica quando a morte é forçada.
- O JSON de lojas permanece válido e o item aparece no catálogo regenerado.

### Task 1: Item, loja e catálogo

**Files:**
- Modify: `server.py` (catálogo de mercador e preço de técnica)
- Modify: `city_shops.json` (estoques de mercador)
- Modify: `tools/editor_catalog.js` (regenerado pelo exportador)

- [x] Adicionar `ultimo_suspiro` como item de slot `item`, efeito de proteção, preço 500 e ícone PNG dedicado `assets/itens/ultimo_suspiro.png`.
- [x] Adicionar o ID aos estoques de mercador das cidades.
- [x] Atualizar `tecnica_ultimo_esforco` para preço 700.
- [x] Regenerar `tools/editor_catalog.js` pelo exportador oficial.

### Task 2: Prevenção de morte e documentação

**Files:**
- Modify: `server.py` (fluxo `_player_dies_impl`)
- Modify: `src/lang/narracao.js`
- Modify: `CLAUDE.md`

- [x] Antes das técnicas existentes de prevenção, procurar cópia equipada em `item1`/`item2`, consumir uma e deixar o herói com 1 PV.
- [x] Narrar o salvamento, mantendo a cópia restante equipada.
- [x] Documentar a ordem de gatilho e os novos preços em `CLAUDE.md`.

### Task 3: Revisão estática

- [x] Confirmar por leitura que as proteções são lidas do equipamento (não da bolsa) e consumidas uma de cada vez.
- [x] Confirmar que `city_shops.json` continua parseável e que o catálogo exportado inclui o item e preços atualizados.
- [x] Não executar testes automatizados.
