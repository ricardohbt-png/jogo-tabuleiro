# Etapa 5 — Lote 2: as funções grandes do `game.js` — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Traduzir os **203 literais das 11 maiores funções** do `game.js` — 36% do que resta da etapa 5. Placar 562 → ~359.

**Arquitetura:** Ao contrário do Lote 1 (que foi escopado por ESTRUTURA DE DADOS e resolveu tudo por `_rotulo`/`aplicarCatalogo`), este lote mexe em **templates de render**. O mecanismo é o da tabela C da spec: `data-i18n` quando o elemento inteiro é o texto, `t('chave')` dentro do template quando não é, e `t('chave', {param})` quando há interpolação. Nenhuma estrutura de dados é tocada.

**Stack:** JavaScript vanilla (`game.js`, `src/lang/interface.js`), testes `python` e `node`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto. O bloco do Lote 1 explica os dois caminhos de tradução do cliente.
- **O usuário edita `game.js` e `server.py` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A`. Ele costuma ter `.glb` modificados na árvore; não os inclua.
- **O Lote 1 fechou** (`d1c0e1f`): 707 → 562. Toda estrutura de dados do `game.js` já está traduzida.
- **Convenção de chave:** `ui.<área>.<slug>`, onde `<área>` é a TELA. Dicionário em `src/lang/interface.js`, **JSON estrito dentro das chaves** (sem comentário lá dentro).
- **Falta `en`? Cai no `pt`.** É isso que permite commitar metade de um lote.
- **`tools/js_strings.py`** é o tokenizador. Use-o para contar; **não use regex por linha**, que ignora template multilinha.
- Suítes verdes hoje: `test_interface` (22), `js_strings` (8), `test_idioma` (36), `test_vocabulario` (38), `test_erros` (9), `test_narracao` (67), `test_idioma_cliente` (27), `test_vocabulario_cliente` (55).

### O fato que motivou a Task 1

A spec manda recortar os lotes "por tamanho de função". Só que o placar atribui cada
literal à **declaração anterior mais próxima** — e isso inclui *arrow functions internas*.
Medido no `game.js`: `L` (`game.js:4317`), `add` (`14129`), `mkSelect` (`14078`) e
`_wToggle` (`13044`) são helpers de uma linha DENTRO de outra função, e o placar lhes
atribuía 18, 18, 6 e 9 literais que são da função que os contém. A lista das "maiores
funções" era em parte um artefato.

Restringir a atribuição a declarações de **topo** (coluna 0) troca esses nomes por nomes
reais e faz o conjunto `FECHADAS` voltar a significar alguma coisa. É a Task 1, e todo o
recorte abaixo depende dela.

### As 11 funções, medidas com a atribuição corrigida

| função | textos | tela |
|---|---:|---|
| `gerarConteudoTooltip` | 29 | tooltip de item (compartilhado) |
| `renderConteudoAtributosFichaJogo` | 27 | ficha do herói |
| `_showTrapResult` | 25 | popup de armadilha |
| `handleTileClick` | 21 | tabuleiro (toasts) |
| `gerarHabilidadesEspeciais` | 18 | ficha / tooltip de monstro |
| `_modificadoresTemporariosStatus` | 18 | ficha do herói |
| `_itemDesc` | 17 | descrição de item (compartilhado) |
| `renderMyPanel` | 15 | HUD |
| `_renderShopItems` | 12 | loja |
| `_paladinSkillBtn` | 11 | HUD do paladino |
| `_rogueSkillBtn` | 10 | HUD do ladino |

**Total 203.** O resto (359) é o Lote 3: 17 funções de 5–9, 67 de 2–4 e 73 de 1.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `tools/test_interface.py` | atribuição só por declaração de topo; `FECHADAS` ao fim de cada task |
| `game.js` | os templates das 11 funções |
| `src/lang/interface.js` | as ~203 chaves |

---

## Task 1: A atribuição por função de TOPO

**Arquivos:**
- Modificar: `tools/test_interface.py`

Sem isto, `FECHADAS` não serve para nada neste lote: marcar `L` como fechada não impede
regressão nenhuma, porque `L` não é uma função de verdade.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar na seção `[1]` de `tools/test_interface.py`, logo depois do `check("placar
emitido", True)`:

```python
    # Helper interno (arrow de uma linha DENTRO de outra função) não pode virar
    # dono de literal: a atribuição é pela declaração anterior mais próxima, e
    # `L`/`add`/`mkSelect`/`_wToggle` roubavam 51 literais das funções que os
    # contêm. Sem isto o conjunto FECHADAS não significa nada.
    internos = [fn for fn in ("L", "add", "mkSelect", "_wToggle") if fn in cont]
    check(f"nenhum helper interno é dono de literal ({internos or 'ok'})",
          not internos)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_interface.py
```

Esperado: falha, listando `['L', 'add', 'mkSelect', '_wToggle']`.

- [ ] **Passo 3: Implementar**

Em `tools/test_interface.py`, a `RE_FN` hoje aceita indentação (`^\s*`). Troque por
âncora de coluna 0 e explique:

```python
# SÓ declarações de TOPO (coluna 0). A atribuição é pela declaração anterior mais
# próxima, então um helper indentado — `const L = (txt) => …` dentro de um render —
# virava dono dos literais da função que o contém. Com a âncora, o dono é sempre a
# função de topo, que é o que o conjunto FECHADAS precisa para significar algo.
RE_FN = re.compile(
    r"^(?:async\s+)?function\s+(\w+)"
    r"|^(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\(?[\w,\s]*\)?\s*=>")
```

- [ ] **Passo 4: Rodar**

```bash
python tools/test_interface.py
```

Esperado: 23 passaram, 0 falharam. O **total continua 562** (só o dono muda), e as maiores
passam a ser `gerarConteudoTooltip` 29, `renderConteudoAtributosFichaJogo` 27,
`_showTrapResult` 25. Se o total mudar, algo além da atribuição foi afetado — **pare**.

- [ ] **Passo 5: Commit**

```bash
git status --short
git add tools/test_interface.py
git commit -m "test(i18n): o placar atribui literal a funcao de TOPO, nao a helper interno"
```

---

## Task 2: Tooltip e descrição de item (58 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

`gerarConteudoTooltip` (29), `_itemDesc` (17), `_renderShopItems` (12). São as três funções
**compartilhadas** entre ficha, loja e baú — traduzi-las cobre três telas de uma vez.

- [ ] **Passo 1: Listar os literais de cada função**

```bash
python - <<'EOF'
import io, os, re, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "tools")
sys.stdout.reconfigure(encoding="utf-8")
import test_interface as T
ALVO = ("gerarConteudoTooltip", "_itemDesc", "_renderShopItems")
linhas = T.GAME.split("\n")
dono, atual = {}, None
for i, l in enumerate(linhas):
    m = T.RE_FN.match(l)
    if m: atual = m.group(1) or m.group(2)
    dono[i + 1] = atual
for ln, txt in T._literais_pendentes():
    if dono.get(ln) in ALVO:
        print(f"{dono[ln]:32} {ln:6} {txt!r}")
EOF
```

- [ ] **Passo 2: Escrever as chaves**

Em `src/lang/interface.js`, sob `ui.item.*` (a área é o tooltip/descrição de item, não a
tela). O `pt` tem de ser **idêntico** ao literal de hoje. Exemplo da forma:

```json
  "ui.item.tooltip.dano": {
    "en": "Damage",
    "pt": "Dano"
  },
```

Para texto com número no meio, use parâmetro em vez de quebrar a frase:

```json
  "ui.item.tooltip.alcance_quadrados": {
    "en": "{n} squares",
    "pt": "{n} quadrados"
  },
```

- [ ] **Passo 3: Trocar no template**

Dentro de template string, chame o `t()` direto:

```js
  linhas.push(renderLinhaTooltip('📏', t('ui.item.tooltip.alcance'),
                                 t('ui.item.tooltip.alcance_quadrados', {n: item.alcance})));
```

Quando o elemento inteiro for um rótulo FIXO, prefira o marcador, que troca ao vivo sem
re-render:

```js
  `<div class="secao-titulo" data-i18n="ui.item.tooltip.efeitos"></div>`
```

**Duas condições, as duas obrigatórias:** (a) o conteúdo INTEIRO do elemento é aquele texto
— o `_i18nApply` usa `textContent`, que apaga filhos; e (b) o texto é FIXO. Um elemento
cujo conteúdo já vem de `_rotulo(...)` ou de qualquer expressão **não** leva `data-i18n`:
o marcador sobrescreveria o valor calculado com uma chave estática. Na dúvida, use `t()`
dentro do template — sempre correto, só não troca sem re-render.

- [ ] **Passo 4: Medir**

```bash
node --check game.js && node --check src/lang/interface.js && python tools/test_interface.py
```

O placar tem de cair **exatamente 58** (562 → 504). Se cair menos, sobrou literal; se cair
mais, você mexeu fora do escopo — **pare e meça**.

- [ ] **Passo 5: Fechar as três funções**

Acrescente ao conjunto `FECHADAS` no topo de `tools/test_interface.py`:

```python
FECHADAS = {"gerarConteudoTooltip", "_itemDesc", "_renderShopItems"}
```

Rode de novo: a seção `[2]` tem de passar. Se acusar regressão, sobrou literal na função.

- [ ] **Passo 6: Verificar na tela**

Suba o servidor e abra com **cache-buster**:

```bash
python server.py
```

No navegador (`http://localhost:8765/index.html?v=lote2t2`), nos DOIS idiomas: passe o mouse
num item da bolsa, abra a loja e abra um baú. **Antes de concluir, cheque no console que a
versão nova carregou** — por um símbolo que só existe depois da sua mudança. O navegador
serve o `game.js` do cache, e isso já falseou prova duas vezes nesta etapa.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): tooltip, descricao e loja de item (Lote 2, Task 2)"
```

---

## Task 3: A ficha do herói (60 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

`renderConteudoAtributosFichaJogo` (27), `_modificadoresTemporariosStatus` (18),
`renderMyPanel` (15).

- [ ] **Passo 1: Listar os literais**

Mesmo script do Passo 1 da Task 2, trocando a tupla:

```python
ALVO = ("renderConteudoAtributosFichaJogo", "_modificadoresTemporariosStatus",
        "renderMyPanel")
```

- [ ] **Passo 2: Escrever as chaves**

Sob `ui.ficha.*` (ficha e modificadores) e `ui.hud.*` (`renderMyPanel`). O `pt` idêntico ao
de hoje.

**Atenção ao `renderMyPanel`:** ele monta os banners de status (regeneração, saciado,
exaustão, Último Esforço, Réquiem). Vários têm contador — use parâmetro:

```json
  "ui.hud.ultimo_esforco": {
    "en": "🔥 LAST STAND — {n} turn(s) left",
    "pt": "🔥 ÚLTIMO ESFORÇO — {n} turno(s) restante(s)"
  },
```

- [ ] **Passo 3: Trocar no template**

Como na Task 2: `t()` dentro do template, `data-i18n` só onde o elemento inteiro é o texto.

- [ ] **Passo 4: Medir**

```bash
node --check game.js && python tools/test_interface.py
```

Queda **exatamente 60** (504 → 444).

- [ ] **Passo 5: Fechar as três funções**

```python
FECHADAS = {"gerarConteudoTooltip", "_itemDesc", "_renderShopItems",
            "renderConteudoAtributosFichaJogo", "_modificadoresTemporariosStatus",
            "renderMyPanel"}
```

- [ ] **Passo 6: Verificar na tela**

Nos dois idiomas, com cache-buster: abra a ficha do herói (atributos + modificadores) e
olhe o HUD com um status ativo.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): ficha do heroi e banners do HUD (Lote 2, Task 3)"
```

---

## Task 4: Botões de habilidade (39 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

`gerarHabilidadesEspeciais` (18), `_paladinSkillBtn` (11), `_rogueSkillBtn` (10).

- [ ] **Passo 1: Listar os literais**

```python
ALVO = ("gerarHabilidadesEspeciais", "_paladinSkillBtn", "_rogueSkillBtn")
```

- [ ] **Passo 2: Emitir `data-ability-id` onde faltar**

**Este passo é obrigatório e não é opcional.** Os dois `*SkillBtn` desenham nome de
habilidade; o `replaceAbilityEmoji` acha o ícone por `data-ability-id` e só cai no scan por
texto em PORTUGUÊS como retaguarda. Traduzir o nome sem emitir o id faz o ícone sumir **em
silêncio** — provado no navegador na 5.0, e a Task 4 do Lote 1 corrigiu o mesmo problema na
tela de seleção.

Confira antes de traduzir:

```bash
grep -n "skill-name" game.js | head -20
```

Todo `.skill-name` das funções desta task tem de sair com
`data-ability-id="${sk.id}"` (ou o id equivalente daquela habilidade).

- [ ] **Passo 3: Escrever as chaves e trocar no template**

Sob `ui.hud.skill.*`. **Não reuse as chaves `ui.selecao.skill.*` do Lote 1**: aquelas são a
descrição longa da tela de seleção; estas são o rótulo curto do botão, com estado
("● ativo", "● armada", "ação já gasta"). Textos diferentes, chaves diferentes.

- [ ] **Passo 4: Medir**

```bash
node --check game.js && python tools/test_interface.py
```

Queda **exatamente 39** (444 → 405).

- [ ] **Passo 5: Fechar as três funções**

Acrescente `"gerarHabilidadesEspeciais"`, `"_paladinSkillBtn"`, `"_rogueSkillBtn"` ao
`FECHADAS`.

- [ ] **Passo 6: Verificar na tela — inclusive os ícones**

Nos dois idiomas, com cache-buster: entre numa masmorra com Richard e com Luccas e olhe o
HUD. **Confirme que os ícones das habilidades continuam lá em inglês** — é o modo de falha
desta task.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): botoes de habilidade do paladino e do ladino (Lote 2, Task 4)"
```

---

## Task 5: Popup de armadilha e toasts do tabuleiro (46 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

`_showTrapResult` (25), `handleTileClick` (21).

- [ ] **Passo 1: Listar os literais**

```python
ALVO = ("_showTrapResult", "handleTileClick")
```

- [ ] **Passo 2: Escrever as chaves**

Sob `ui.armadilha.*` e `ui.tabuleiro.*`.

**Cuidado com o `handleTileClick`:** boa parte dos literais dele são `toast(...)` — texto
**fora do DOM**, que `data-i18n` não alcança. Todos viram `t('chave')`, conforme a tabela C
da spec. E como o toast é montado no momento do clique, ele já sai no idioma corrente.

**Cuidado com o `_showTrapResult`:** o nome e o ícone da armadilha vêm do **payload**
`trap_result` do servidor, que já é traduzido pelo filtro `traduzirNomes` (etapa 2). Não
crie chave para eles — só para os rótulos fixos do popup.

- [ ] **Passo 3: Trocar no template**

- [ ] **Passo 4: Medir**

```bash
node --check game.js && python tools/test_interface.py
```

Queda **exatamente 46** (405 → 359).

- [ ] **Passo 5: Fechar as duas funções**

Acrescente `"_showTrapResult"` e `"handleTileClick"` ao `FECHADAS`.

- [ ] **Passo 6: Verificar na tela**

Nos dois idiomas, com cache-buster: pise numa armadilha (o popup) e clique em casas
inválidas no tabuleiro (os toasts).

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): popup de armadilha e toasts do tabuleiro (Lote 2, Task 5)"
```

---

## Task 6: Fechamento do lote

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar tudo**

```bash
python tools/test_interface.py && python tools/js_strings.py && python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: todas verdes, placar em **~359**, e as **11 funções no `FECHADAS`** sem regressão.

- [ ] **Passo 2: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

Esperado: 336/0, 54/0, 462/0.

- [ ] **Passo 3: Documentar no `CLAUDE.md`**

Um bloco `>` cobrindo: que o Lote 2 traduziu **templates de render** (ao contrário do Lote
1, que era estrutura de dados); que a atribuição do placar passou a ser por função de
**topo**, e por que isso era necessário para o `FECHADAS` significar algo; que os botões de
habilidade precisaram emitir `data-ability-id`; e o número novo do placar.

- [ ] **Passo 4: Commit**

```bash
git status --short
git add CLAUDE.md
git commit -m "docs(i18n): funcoes grandes do game.js traduzidas (Lote 2)"
```

---

## Fora deste lote (registrado, não esquecido)

- **359 textos** no `game.js` (17 funções de 5–9, 67 de 2–4, 73 de 1), mais **69** no
  `gameState.js` e **9** no `inventoryModal.js` — o Lote 3.
- **Conteúdo autoral** (masmorras, campanhas, falas de NPC, itens e monstros do editor) e o
  **editor** (`tools/*.js`) estão fora da etapa 5 inteira.
- O bloco `#hint-host` do `index.html`, que mistura `<b>`/`<code>`, segue fora desde a
  etapa 1.
