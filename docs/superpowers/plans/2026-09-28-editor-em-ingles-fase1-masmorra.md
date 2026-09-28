# Editor em inglês — Fase 1 (aba Masmorra) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Traduzir para PT/EN tudo o que a aba **Masmorra** do editor mostra — `tools/editor.js` inteiro (304 textos medidos) — e fazer a troca de idioma redesenhar também a barra de ferramentas.

**Architecture:** Mesma infraestrutura da Fase 0: `t('ui.editor.masmorra.<slug>', params)` no ponto de render; dicionário em `src/lang/editor.js`; nomes de catálogo por `nomeCat`. Estruturas de dados de módulo (`TOOLS`, `LICAO_VERBOS`, `HERO_SPAWN_META`, …) guardam **ids/chaves**, nunca texto — o texto é resolvido na hora de desenhar, senão ficaria preso no idioma do carregamento. Ao fim, `editor.js` entra em `FECHADAS` no placar.

**Tech Stack:** JavaScript vanilla, Python (placar), Node (testes de fiação).

**Spec:** `docs/superpowers/specs/2026-09-28-editor-em-ingles-design.md` · **Fase 0:** `docs/superpowers/plans/2026-09-28-editor-em-ingles-fase0.md`

---

## Por que as tarefas de texto não listam cada frase

São ~300 frases, muitas com interpolação. O plano fixa **método, convenção, recorte por função e critério de aceite medível** (o placar zera naquelas funções), e deixa a escrita de cada chave para quem executa — que precisa ler o contexto de cada frase para traduzir bem. Isso é deliberado, não lacuna.

## Fatos do código (conferidos em 2026-09-28)

- `tools/editor.js` é uma IIFE, **CRLF**, ~3.860 linhas. Use a ferramenta Edit; não use `replace` com `\n` em script.
- O placar: `python -X utf8 tools/test_editor_idioma.py` — seção [4] conta por função (`_pendentes_por_funcao("editor.js")`), [5] lista `t` locais. Medição de partida de `editor.js` (304):
  `validarEditor` 89 · `_renderPanelCorpo` 76 · `buildToolbar` 17 · `lootItemCategory` 15 · `LICAO_VERBOS` 14 · `trapCharacteristicsHTML` 14 · `TOOLS` 11 · `LOOT_ITEM_GROUPS` 10 · `_validarDesign` 9 · `save` 9 · `trapEffectLabel` 8 · `HERO_SPAWN_META` 6 · `CAT` 4 · `VISAO_ROTULO` 3 · `CURSE_CATEGORIES` 3 · `_termometroHTML` 3 · `drawDecorFrontMarker` 2 · `curseFieldsHTML` 2 · e 1 em `S`, `copyMenu`, `lootItemRowHTML`, `rewardFieldsHTML`, `_avisosDesignHTML`, `_salaDe`, `drawMaterialAreaPreview`, `updateStatus`, `loadJSON`.
  Para ver só uma função: `python -X utf8 -c "import sys;sys.path.insert(0,'tools');import test_editor_idioma as T;print(T._pendentes_por_funcao('editor.js'))"`.
  Para ver as LINHAS pendentes: `python -X utf8 -c "import sys,io;sys.path.insert(0,'tools');from js_strings import texto_de_interface as f;[print(l,t[:90]) for l,t in f(io.open('tools/editor.js',encoding='utf-8').read())]"`.
- `window.t` (global, da cola `tools/editor_i18n.js`) existe **antes** de `editor.js` carregar — `t(...)` num `const` de módulo não quebra por TDZ, mas o resultado ficaria **congelado no idioma do carregamento**. Por isso estrutura de dados guarda id/chave.
- `t` LOCAL sombreia o global: `(t) =>`, `t =>`, `for (const t of …)`, `const t = …`. Dentro desse escopo, `t('…')` vira TypeError em runtime sem nenhum teste pegar. Tarefa 1 renomeia todos em `editor.js`.
- **Decisão por texto em português** (quebra em silêncio ao traduzir): `lootItemCategory` devolve o NOME do grupo ("Armas", "Poções e consumíveis") e esse nome é a chave do agrupamento em `lootItemSelectHTML`. Tarefa 2 troca por id.
- **Suítes que leem `editor.js` como texto** e não podem quebrar:
  - `tools/test_tutorial.py` [20]: o bloco `const LICAO_VERBOS = [` … `]` precisa continuar tendo `v: "<verbo>"` por entrada (o primeiro `]` fecha o bloco — não pôr `]` dentro das entradas);
  - `tools/test_sombra_objetos.py`: `const VISAO_NIVEIS = [...]` intacto; `o.visao = d.visao` e `visao: d.visao` presentes;
  - `tools/test_elevacao_rampa.js`: `function bridgeAltura(`, `placeBridge … altura: bridgeAltura(`, `pontes: S.pontes.map … altura: bridgeAltura(`;
  - `tools/test_arte3d.py` lê `editor.js`.
  Rode as quatro ao fim de CADA tarefa (comando na Tarefa 1, Step 5).
- `nomeCat(familia, id, padrao)`: famílias com chave no dicionário — `classe` (os 6 heróis), `monstro` (por `type`), `decor` (por `type`), `armadilha` (por `tipo`), `item` (por `id`). Item/monstro criado pelo autor não tem chave → volta o `padrao` (nome do autor).
- O servidor rodando na 8765 pode travar escrita; se um Write/Edit falhar com Errno 22, pare-o.
- O worktree NÃO tem os arquivos não commitados do autor (imagens novas etc.) — 404 de retrato no editor é esperado e não é desta fase.

## Convenção de chave

`ui.editor.masmorra.<área>.<slug>` — áreas: `ferramenta`, `grupo`, `painel`, `valid` (validação), `design` (avisos do validador de design), `status`, `salvar`, `loot`, `armadilha`, `licao`, `visao`, `maldicao`, `termometro`, `canvas`. O slug é o texto em português em minúsculas, sem acento, com `_`, curto (ex.: `ui.editor.masmorra.valid.falta_a_entrada`). Parâmetros `{nome}` com nome descritivo, iguais em pt e en. Rótulos por id: `ui.editor.masmorra.ferramenta.<id>`, `ui.editor.masmorra.loot.<grupo_id>`, `ui.editor.masmorra.licao.<verbo>`, `ui.editor.masmorra.visao.<nivel>`, `ui.editor.masmorra.maldicao.<v>`.

Toda chave nova vai para `src/lang/editor.js` com `en` e `pt` (o `pt` é o texto original, **idêntico**, inclusive emoji e pontuação). JSON estrito dentro do objeto.

## Arquivos

| Arquivo | Ação |
|---|---|
| `tools/editor.js` | modificar (todas as tarefas) |
| `src/lang/editor.js` | acrescentar chaves (Tarefas 2–7) |
| `tools/test_editor_idioma.py` | `FECHADAS` e seção [6] (Tarefas 3 e 8) |
| `tools/test_editor_settab.js` | stub `buildToolbar` + caso da Masmorra (Tarefa 3) |
| `CLAUDE.md` | registro (Tarefa 8) |

---

### Task 1: Renomear os `t` locais de `editor.js`

**Files:** Modify `tools/editor.js`

- [ ] **Step 1: Listar**

Run: `python -X utf8 tools/test_editor_idioma.py` — a seção [5] lista as linhas de `editor.js` com `t` local.

- [ ] **Step 2: Renomear cada um pelo papel**, escopo a escopo, trocando a declaração E todos os usos dentro do escopo: tile/célula → `tile`; armadilha → `trap`; item de catálogo → `it`; ferramenta (`TOOLS`) → `tool`; tipo → `tipo`; parâmetro genérico de `.map/.find/.filter` → um nome curto que não seja `t` (`x`, `r`, `o`…). Não renomeie propriedades (`obj.t`) nem strings.

- [ ] **Step 3: Conferir** que [5] não lista mais `editor.js` e que não há `t(` quebrado:

Run: `python -X utf8 tools/test_editor_idioma.py` → a linha de `editor.js` some de [5].
Run: `node --check tools/editor.js` → sem saída.

- [ ] **Step 4: Nenhum texto mudou** — o placar de `editor.js` em [4] continua **304**.

- [ ] **Step 5: Suítes que leem editor.js**

```bash
python -X utf8 tools/test_tutorial.py | tail -2
python -X utf8 tools/test_sombra_objetos.py | tail -1
node tools/test_elevacao_rampa.js | tail -2
python -X utf8 tools/test_arte3d.py | tail -2
node tools/test_editor_settab.js 2>/dev/null | tail -1
```
Expected: todas sem falha.

- [ ] **Step 6: Commit** — `refactor(editor-idioma): renomeia os t locais de editor.js (não sombreiam o t() global)`

---

### Task 2: Estruturas de dados com id/chave

**Files:** Modify `tools/editor.js`, `src/lang/editor.js`

Alvos (e o que cada um vira):

1. **`TOOLS`**: tirar `label`; `group` passa a ser id sem acento (`"tiles"`, `"entidades"`, `"acoes"`). Em `buildToolbar`: `g.textContent = t("ui.editor.masmorra.grupo." + tool.group)` e `b.textContent = t("ui.editor.masmorra.ferramenta." + tool.id)`. Qualquer outro leitor de `.label` de TOOLS (grep `\.label` no arquivo) passa a usar a chave.
2. **`LOOT_ITEM_GROUPS`** vira lista de ids: `["armas","armaduras","escudos","venenos","arremessaveis","instrumentos","municoes","pocoes","aneis","outros"]`; `lootItemCategory` devolve esses ids; em `lootItemSelectHTML` o `label` do `<optgroup>` é `t("ui.editor.masmorra.loot." + group)`. Grep outros usos de `lootItemCategory(` e do nome dos grupos.
3. **`HERO_SPAWN_META`**: tirar `name`; onde se mostra, usar `nomeCat("classe", h.id, h.id)`. `heroSpawnMeta` passa a devolver `{ … }` sem `name` e o fallback `name: id` vira o id cru quando mostrado.
4. **`LICAO_VERBOS`**: tirar `nome`, manter `{ v: "…" }` (exigência do `test_tutorial.py`); onde se mostra, `t("ui.editor.masmorra.licao." + x.v)`.
5. **`VISAO_ROTULO`**: vira função `visaoRotulo(nivel)` que devolve `t("ui.editor.masmorra.visao." + nivel)`; troque os leitores. `VISAO_NIVEIS` fica intocado.
6. **`CURSE_CATEGORIES`**: tirar `name`; mostrar `t("ui.editor.masmorra.maldicao." + c.v)`.
7. **`CAT`** (4 textos) e **`S`** (1: nome padrão "Nova Masmorra"): ver as linhas pendentes; o nome padrão de masmorra nova vira `t("ui.editor.masmorra.nome_padrao")` no ponto em que a masmorra nova é criada (se `S` é criado no carregamento, pode ficar ali — o nome é conteúdo e fica no idioma de quando foi criada, o que é correto).

- [ ] **Step 1:** Fazer as 7 mudanças, acrescentando as chaves em `src/lang/editor.js` (pt = texto original idêntico).
- [ ] **Step 2:** Placar: as funções/estruturas `TOOLS`, `LOOT_ITEM_GROUPS`, `lootItemCategory`, `HERO_SPAWN_META`, `LICAO_VERBOS`, `VISAO_ROTULO`, `CURSE_CATEGORIES`, `CAT`, `S` com **0**. Total de `editor.js` cai de 304 para ~238.
- [ ] **Step 3:** `python -X utf8 tools/test_editor_idioma.py` (verde, [1] com paridade) · `node --check tools/editor.js` · as 5 suítes da Tarefa 1 Step 5.
- [ ] **Step 4: Commit** — `feat(editor-idioma): estruturas de dados da Masmorra guardam id/chave (TOOLS, loot, lições, visão…)`

---

### Task 3: Barra de ferramentas e troca de idioma

**Files:** Modify `tools/editor.js`, `tools/test_editor_settab.js`, `src/lang/editor.js`

- [ ] **Step 1: Teste que falha** — em `tools/test_editor_settab.js`, acrescentar um stub `buildToolbar` que registra chamadas (declarado junto de `render`/`renderPanel`, que o `setTab` extraído enxerga) e os casos:
  - `setTab('masmorra', true)` chama `buildToolbar` **antes** de `render` e `renderPanel`;
  - `setTab('masmorra')` (troca de aba comum) **não** chama `buildToolbar` (comportamento de hoje).
  Run `node tools/test_editor_settab.js` → os 2 novos falham.
- [ ] **Step 2:** Em `setTab`, no ramo `if (dung)`: `if (soRedesenhar) buildToolbar();` antes de `render(); renderPanel();`. Run → verde.
- [ ] **Step 3:** Traduzir o resto de `buildToolbar` (17): o `hint` do herói, rótulos e opções dos seletores da barra (armadilha, material, decoração, "balde", etc.). Nomes de catálogo nos `<option>` via `nomeCat`: heróis `nomeCat("classe", h.id, h.id)`, armadilhas `nomeCat("armadilha", tr.tipo, tr.nome)`, decorações `nomeCat("decor", d.type, d.name)`, monstros `nomeCat("monstro", m.type, m.name)`.
- [ ] **Step 4:** Placar `buildToolbar` = 0; testes da Tarefa 1 Step 5 + `node tools/test_editor_settab.js`.
- [ ] **Step 5: Commit** — `feat(editor-idioma): barra de ferramentas da Masmorra traduzida e remontada na troca de idioma`

---

### Task 4: Painel lateral (`_renderPanelCorpo`)

**Files:** Modify `tools/editor.js`, `src/lang/editor.js`

- [ ] **Step 1:** Traduzir os 76 textos de `_renderPanelCorpo`: rótulos, `<option>` de texto (o `value` NUNCA muda), dicas `<small>`, botões, `title`/`placeholder`. Nas listas de objetivo, o texto mostrado de cada `OBJ` passa por `t("ui.editor.masmorra.objetivo." + id)` — hoje só `all_heroes_at_exit` tem rótulo e os outros mostram o id cru; mostre rótulo para todos.
- [ ] **Step 2:** Nomes de catálogo nos `<select>` do painel (linhas com `CAT.monsters.map`, `CAT.traps…map`, `CAT.items.map`, `trapOptions`): `name: nomeCat(família, id, nomeOriginal)`. O `value` continua o id.
- [ ] **Step 3:** Placar `_renderPanelCorpo` = 0. Testes da Tarefa 1 Step 5.
- [ ] **Step 4: Commit** — `feat(editor-idioma): painel lateral da Masmorra traduzido`

---

### Task 5: Auxiliares do painel e do canvas

**Files:** Modify `tools/editor.js`, `src/lang/editor.js`

Funções: `trapCharacteristicsHTML` (14), `trapEffectLabel` (8), `_termometroHTML` (3), `drawDecorFrontMarker` (2), `curseFieldsHTML` (2), `copyMenu`, `lootItemRowHTML`, `rewardFieldsHTML`, `_avisosDesignHTML`, `_salaDe`, `drawMaterialAreaPreview` (1 cada).

- [ ] **Step 1:** Traduzir. Texto desenhado no canvas (`ctx.fillText`) também usa `t()`. Rótulo de faixa de dificuldade vindo de `src/difficulty.js` (`label` em português): traduzir por `t("ui.dificuldade." + faixa.key)` — a chave já existe no dicionário do jogo (conferir com grep em `src/lang/interface.js`).
- [ ] **Step 2:** Placar dessas funções = 0. Testes da Tarefa 1 Step 5.
- [ ] **Step 3: Commit** — `feat(editor-idioma): auxiliares do painel e do canvas da Masmorra traduzidos`

---

### Task 6: Validação, status, salvar e carregar

**Files:** Modify `tools/editor.js`, `src/lang/editor.js`

Funções: `validarEditor` (89), `_validarDesign` (9), `save` (9), `updateStatus` (1), `loadJSON` (1).

- [ ] **Step 1:** Cada `e.push("…")`/`` e.push(`…${x}…`) `` vira `e.push(t("ui.editor.masmorra.valid.<slug>", {…}))`. Os prefixos compostos (`${label}: …`) viram parâmetro `{rotulo}`. Mensagens idênticas repetidas usam a MESMA chave. `alert`/`confirm` de `save` idem (`ui.editor.masmorra.salvar.*`). Em `updateStatus`, a frase de contagem vira `t("ui.editor.masmorra.status.problemas", {n, lista, mais})` — cuidado com o sufixo " …" quando há mais de 4.
- [ ] **Step 2:** Ninguém compara o TEXTO dessas mensagens (conferido: só `ok`/`erros.length`); mantenha assim.
- [ ] **Step 3:** Placar dessas funções = 0. Testes da Tarefa 1 Step 5.
- [ ] **Step 4: Commit** — `feat(editor-idioma): validação, status e salvar da Masmorra traduzidos`

---

### Task 7: Varredura final do arquivo

- [ ] **Step 1:** `python -X utf8 tools/test_editor_idioma.py` → `editor.js` com **0** em [4]. Se sobrar algo, traduzir (ou, se for conteúdo autoral/id, registrar por quê).
- [ ] **Step 2:** Grep por texto em português que o placar não enxerga: `grep -nE "[À-ú]" tools/editor.js | grep -v "^\s*//"` — revisar o que for string visível e não comentário.
- [ ] **Step 3: Commit** (se houver mudança) — `feat(editor-idioma): sobras de editor.js traduzidas`

---

### Task 8: Fechar a aba no placar, conferir no navegador e registrar

**Files:** Modify `tools/test_editor_idioma.py`, `CLAUDE.md`

- [ ] **Step 1:** Em `tools/test_editor_idioma.py`, `FECHADAS = {"editor.js"}`. Rodar: verde (placar 0 e nenhum `t` sombreado em `editor.js`).
- [ ] **Step 2: Navegador.** Servir o worktree numa porta à parte (o servidor do autor na 8765 serve a pasta principal): configuração temporária em `.claude/launch.json` da pasta principal, `python -m http.server 8790 --directory <worktree>`, e remover ao fim. Abrir `http://localhost:8790/tools/editor.html?v=f1`, trocar para English e:
  - clicar em cada ferramenta da barra, selecionando uma entidade de cada tipo no mapa (sala, porta, monstro, baú, armadilha, decoração, prisioneiro, fala, passagem, parede ilusória) para abrir cada variação do painel;
  - em cada estado, varrer o DOM de `#toolbar`, `#panel` e `#statusbar` atrás de português:
    ```js
    [...document.querySelectorAll('#toolbar,#panel,#statusbar')].map(e=>e.innerText).join('\n')
      .split('\n').filter(l=>/[ãõçáéíóúâêôà]|\b(de|da|do|para|com|sem|não)\b/i.test(l))
    ```
    O que aparecer e não for nome autoral (masmorra, sala, monstro/item criado pelo autor) é dívida: traduzir e voltar.
  - trocar EN→PT→EN com uma sala selecionada e um nome de masmorra digitado: seleção, nome e mapa continuam; a barra muda de idioma.
  - console sem erro novo (404 de retrato faltando é esperado).
- [ ] **Step 3:** Suítes: `test_editor_idioma.py`, `test_editor_i18n.js`, `test_editor_settab.js`, as 4 da Tarefa 1 Step 5, `test_idioma.py`, `dividas.py`.
- [ ] **Step 4:** `CLAUDE.md` — acrescentar ao bloco da Fase 0 (fim do arquivo) um parágrafo "**Fase 1 (Masmorra)**": `editor.js` fechado no placar; estruturas de módulo guardam id/chave (`TOOLS`, `LOOT_ITEM_GROUPS` por id — era decisão por texto), `nomeCat` nos seletores, `setTab('masmorra', true)` remonta a barra, convenção `ui.editor.masmorra.<área>.<slug>`.
- [ ] **Step 5: Commit** — `feat(editor-idioma): aba Masmorra fechada no placar + registro`

## Notas para a Fase 2 (Criaturas)

- `editor_monster_editor.js` agrupa seções em abas comparando `<h2>` com nomes em português (~linha 801): trocar por `data-*` antes de traduzir os títulos.
- `read()` força `ai_type`/`movement` no rascunho (ver plano da Fase 0).
