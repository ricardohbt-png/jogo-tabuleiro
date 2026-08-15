# Etapa 5 — Lote 3: a cauda do cliente — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Fechar a etapa 5 — os **426 literais restantes**: 350 no `game.js`, 67 no `src/gameState.js` e 9 no `src/ui/inventoryModal.js`. Placar 350 → 0.

**Arquitetura:** Mecanismo idêntico ao do Lote 2 (`t()` no template, `t('chave',{param})` com interpolação, `_rotulo` para mapas `{id:'texto'}`). O que muda é a **forma do trabalho**: não há mais função grande — a cauda é plana, e o recorte por função deixa de funcionar. Ver "O recorte" abaixo.

**Stack:** JavaScript vanilla, testes `python` e `node`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** tem os blocos dos Lotes 1 e 2. **Leia-os antes de começar** — em especial o item sobre lookup por texto em português.
- **O usuário edita `game.js` e `server.py` em paralelo.** `git status` antes de cada commit; **nunca** `git add -A`; ele costuma ter `.glb` modificados.
- Estado na abertura: placar **350**, `FECHADAS` com 10 funções, 494 chaves em `src/lang/interface.js`, 11 suítes verdes.

### O recorte, e por que ele muda

O Lote 2 recortou "as N maiores funções" e isso funcionou porque havia 11 com ≥10
literais. **Não há mais nenhuma:** a maior tem 9, e a distribuição é

| faixa | funções | textos |
|---|---:|---:|
| 5–9 | 16 | 100 |
| 3–4 | 32 | 108 |
| 2 | 36 | 72 |
| 1 | 70 | 70 |

Recortar por tamanho aqui daria tasks de 2 literais cada. **O recorte deste lote é por
ARQUIVO e por FAIXA**, em 5 tasks — cada uma grande o bastante para valer um commit e
pequena o bastante para caber numa revisão.

### Os dois arquivos novos, e a regra que vale neles

`src/gameState.js` (67) e `src/ui/inventoryModal.js` (9) **nunca foram tocados pela etapa
5**. Atenção à regra do `CLAUDE.md`: **`gameState.js` não pode referenciar `window`,
`document` nem `THREE`**. O `t()` global vem de `window.I18N` — usá-lo cru ali viola a
regra e quebra o teste que a guarda.

**A saída é a mesma que o módulo já usa para o filtro de mensagens:** `gameState.js` não
conhece o I18N; quem o conhece é o `game.js`, que registra a função via
`GS.setMessageFilter(fn)`. Faça igual — um `GS.setTranslator(fn)` que o `game.js`
preenche com `t`, e um `_t()` interno que cai no texto em português se ninguém registrou.
**Confirme antes de escrever** se os 67 literais são de interface ou de log/erro interno;
os de log ficam fora do escopo, como o conteúdo autoral.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `game.js` | os 350 restantes |
| `src/gameState.js` | o injetor de tradutor + os literais de interface |
| `src/ui/inventoryModal.js` | os 9 literais |
| `src/lang/interface.js` | as ~426 chaves |
| `tools/test_interface.py` | `FECHADAS` ao fim de cada task; cobrar o placar em 0 na Task 5 |

---

## Task 1: A faixa 5–9 do `game.js` (100 textos, 16 funções)

**Arquivos:** Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

As 16 maiores que restam: `renderFichaCidadeBody` (9), `ativarHabilidadeDoMenu` (8),
`_renderCenaConversas` (7), `_tooltipPergaminhoHTML` (7), `_mageSkillBtn` (7),
`_renderChestWindow` (7), `renderDescricaoItem` (6), `_iniciarModoMagia` (6),
`abrirPainelLoot` (6), `iniciarModoArremessoAdagaPrincipal` (6),
`iniciarModoArremessoLanca` (6), `showWorldLocationPreview` (5) e as 4 seguintes.

- [ ] **Passo 1: Listar os literais da faixa**

```bash
python - <<'EOF'
import os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "tools")
sys.stdout.reconfigure(encoding="utf-8")
import test_interface as T
cont = T._por_funcao()
ALVO = {fn for fn, n in cont.items() if 5 <= n <= 9}
linhas = T.GAME.split("\n"); dono, atual = {}, None
for i, l in enumerate(linhas):
    m = T.RE_FN.match(l)
    if m: atual = m.group(1) or m.group(2)
    dono[i + 1] = atual
for ln, txt in T._literais_pendentes():
    if dono.get(ln) in ALVO:
        print(f"{dono[ln][:28]:29} {ln:6} {txt[:90]!r}")
EOF
```

- [ ] **Passo 2: PROCURAR LOOKUP POR TEXTO antes de traduzir**

Este é o defeito recorrente da etapa — quatro ocorrências até aqui, todas falhando em
silêncio. Nas funções desta task, procure mapas e condicionais chaveados por português:

```bash
grep -n "includes('[A-ZÀ-Ú]\|\[msg\.nome\]\|\[item\.nome\]\|=== '[A-ZÀ-Ú]" game.js
```

Achou algum? **Conserte antes de traduzir**, mandando/casando por id — o padrão do
`data-ability-id` e do `tipo_id`. Traduzir primeiro entrega a função já defeituosa.

- [ ] **Passo 3: Traduzir**

Chaves `ui.<área>.<slug>`. Mapas `{id:'texto'}` viram `_rotulo(id, 'ui.<área>', padrao)`
e o mapa sai do arquivo (decisão do commit `733207b`).

**Rode `node --check game.js` depois de CADA replace em massa, não só no fim** — no Lote 2
um replace injetou `${...}` dentro de string de aspas simples em 5 sítios de uma vez.

**Cuidado com `t` sombreado:** `renderPurchasedItems` declara `const t =
document.createElement('div')`. Se a função que você está tocando tiver um `t` local, use
`_rotulo`. Confira com `grep -n "const t = " game.js`.

- [ ] **Passo 4: Medir**

```bash
python tools/test_interface.py
```

Queda esperada: **~100** (350 → ~250). Se cair mais, houve string idêntica noutra função
(aconteceu na Task 3 do Lote 2) — **meça o diff por função** contra o commit anterior
antes de seguir:

```bash
git stash && python tools/test_interface.py > /tmp/antes.txt; git stash pop
```

- [ ] **Passo 5: Fechar as funções e commitar**

Acrescente os 16 nomes ao `FECHADAS`, rode de novo (a seção `[2]` tem de passar) e:

```bash
git status --short
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): faixa 5-9 do game.js (Lote 3, Task 1)"
```

- [ ] **Passo 6: Verificar na tela**

Servidor de pé, **cache-buster** (`?v=algo`) e — obrigatório — **confirme no console que a
versão nova carregou** antes de olhar qualquer coisa. No Lote 2 uma sonda mostrou inglês
idêntico ao português e teria virado "a tradução não funciona"; era o cache.

---

## Task 2: A faixa 3–4 do `game.js` (108 textos, 32 funções)

**Arquivos:** Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

- [ ] **Passo 1: Listar** — mesmo script da Task 1, com `3 <= n <= 4`.
- [ ] **Passo 2: Procurar lookup por texto** — mesmo `grep` da Task 1, Passo 2.
- [ ] **Passo 3: Traduzir** — mesmas regras (chave `ui.<área>.<slug>`, `node --check` a
      cada replace, `_rotulo` onde `t` estiver sombreado).
- [ ] **Passo 4: Medir** — queda esperada **~108** (~250 → ~142).
- [ ] **Passo 5: Fechar as 32 funções e commitar**

```bash
git add game.js src/lang/interface.js tools/test_interface.py
git commit -m "feat(i18n): faixa 3-4 do game.js (Lote 3, Task 2)"
```

- [ ] **Passo 6: Verificar na tela** (cache-buster + prova de versão).

---

## Task 3: A cauda de 1–2 do `game.js` (142 textos, 106 funções)

**Arquivos:** Modificar: `game.js`, `src/lang/interface.js`, `tools/test_interface.py`

106 funções com 1 ou 2 literais cada. Aqui o custo é de navegação, não de tradução.

- [ ] **Passo 1: Listar tudo de uma vez, ordenado por linha**

```bash
python - <<'EOF'
import os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "tools")
sys.stdout.reconfigure(encoding="utf-8")
import test_interface as T
cont = T._por_funcao()
ALVO = {fn for fn, n in cont.items() if n <= 2}
linhas = T.GAME.split("\n"); dono, atual = {}, None
for i, l in enumerate(linhas):
    m = T.RE_FN.match(l)
    if m: atual = m.group(1) or m.group(2)
    dono[i + 1] = atual
for ln, txt in sorted(T._literais_pendentes()):
    if dono.get(ln) in ALVO:
        print(f"{ln:6} {dono[ln][:24]:25} {txt[:80]!r}")
EOF
```

- [ ] **Passo 2: Procurar lookup por texto** — mesmo `grep`.
- [ ] **Passo 3: Traduzir em blocos de ~300 linhas do arquivo**, de cima para baixo,
      rodando `node --check game.js` ao fim de cada bloco. Trabalhar por posição no
      arquivo (e não por função) reduz o vaivém.
- [ ] **Passo 4: Medir** — o placar do `game.js` tem de chegar a **0**.
- [ ] **Passo 5: Commitar** (em 2 commits, metade cada — 142 numa revisão só é onde
      escapa erro).

---

## Task 4: `gameState.js` (67) e `inventoryModal.js` (9)

**Arquivos:** Modificar: `src/gameState.js`, `src/ui/inventoryModal.js`,
`src/lang/interface.js`, `game.js`, `tools/test_idioma_cliente.js`

- [ ] **Passo 1: Separar interface de log interno**

```bash
python -c "
import io, sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
from js_strings import texto_de_interface
for arq in ('src/gameState.js','src/ui/inventoryModal.js'):
    s = io.open(arq, encoding='utf-8').read()
    print('===', arq)
    for ln, txt in texto_de_interface(s): print(f'  {ln:6} {txt[:80]!r}')
"
```

O que for `console.log`/comentário de depuração **fica fora do escopo** — registre quantos
e por quê no commit.

- [ ] **Passo 2: Escrever o teste que falha**

Em `tools/test_idioma_cliente.js`, acrescentar: `gameState.js` não referencia `window`,
`document` nem `THREE` (a regra do `CLAUDE.md`), **e** o tradutor injetado é usado.

```js
console.log("");
console.log("[G] gameState.js traduz sem conhecer o I18N");
const gsSrc = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
check("gameState.js nao referencia window/document/THREE",
      !/\b(window|document|THREE)\b/.test(gsSrc.replace(/\/\/[^\n]*/g, "")));
check("existe o injetor setTranslator", /setTranslator/.test(gsSrc));
check("o game.js registra o tradutor",
      /GS\.setTranslator\(/.test(fs.readFileSync(path.join(raiz, "game.js"), "utf8")));
```

- [ ] **Passo 3: Rodar e confirmar que falha**

```bash
node tools/test_idioma_cliente.js
```

- [ ] **Passo 4: Implementar o injetor**

Em `src/gameState.js`, espelhando o `setMessageFilter` que já existe:

```js
  // O módulo não conhece o I18N (regra do CLAUDE.md: zero window/document aqui).
  // Quem conhece é o game.js, que injeta o `t` no boot. Sem injeção, cai no
  // português — o mesmo contrato de fallback do resto da etapa 5.
  let _traduz = null;
  function setTranslator(fn) { if (typeof fn === 'function') _traduz = fn; }
  function _t(chave, pt, params) {
    try { return _traduz ? _traduz(chave, params) : pt; }
    catch (e) { return pt; }
  }
```

E em `game.js`, junto do `GS.setMessageFilter(...)` já existente:

```js
  GS.setTranslator((chave, params) => t(chave, params));
```

- [ ] **Passo 5: Traduzir os literais de interface dos dois arquivos**
- [ ] **Passo 6: Rodar**

```bash
node --check src/gameState.js && node --check src/ui/inventoryModal.js \
  && node tools/test_idioma_cliente.js && python tools/test_interface.py
```

- [ ] **Passo 7: Commit**

```bash
git add src/gameState.js src/ui/inventoryModal.js src/lang/interface.js game.js tools/test_idioma_cliente.js
git commit -m "feat(i18n): gameState.js e inventoryModal.js (Lote 3, Task 4)"
```

---

## Task 5: Fechamento da ETAPA 5

**Arquivos:** Modificar: `tools/test_interface.py`, `CLAUDE.md`

- [ ] **Passo 1: O placar passa a COBRAR o zero**

Com o `game.js` em 0, o relatório vira cobrança. Em `tools/test_interface.py`:

```python
    check(f"nenhum literal em português restou no game.js ({total})", total == 0)
```

O conjunto `FECHADAS` deixa de ser necessário para o `game.js` (o total zerado cobre tudo),
mas **mantenha-o**: ele documenta a ordem em que os lotes fecharam e não custa nada.

- [ ] **Passo 2: Rodar tudo**

```bash
python tools/test_interface.py && python tools/js_strings.py && python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

- [ ] **Passo 3: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

Esperado: 336/0, 54/0, 462/0.

- [ ] **Passo 4: A varredura final, no navegador**

Percorra as 7 telas em **inglês**, com cache-buster: conexão, jogos salvos, seleção de
herói, cidade, loja, masmorra (HUD + ficha + tooltip de item) e o painel do mestre.
**Procure sobra de português e chave crua na tela** (`ui.algo.assim` aparecendo como
texto). O `t()` loga `console.warn` para chave ausente — deixe o console aberto.

- [ ] **Passo 5: Documentar o FIM da etapa 5 no `CLAUDE.md`**

Um bloco `>` que feche a etapa: o número final, os dois mecanismos do cliente
(`aplicarCatalogo` × `_rotulo`/`t`), o injetor de tradutor do `gameState.js`, e — o item
que mais se repetiu — **lookup por texto em português**, com as 4 ocorrências e o padrão
de conserto por id. Registre também o que ficou **deliberadamente de fora**: conteúdo
autoral, editor (`tools/*.js`), o `#hint-host` do `index.html` e o `includes('não
encontrada')` de `server.py:1856`.

- [ ] **Passo 6: Commit**

```bash
git add tools/test_interface.py CLAUDE.md
git commit -m "docs(i18n): etapa 5 concluida -- interface do cliente traduzida"
```

---

## Fora deste lote (e da etapa 5 inteira)

- **Editor** (`tools/*.js`) — ferramenta do autor.
- **Conteúdo autoral** — masmorras, campanhas, falas de NPC, itens e monstros do editor.
- **`#hint-host`** do `index.html`, que mistura `<b>`/`<code>` — fora desde a etapa 1.
- **`server.py:1856`** (`"Conta não encontrada…"`) segue como string crua **de propósito**:
  migrá-la para `T()` quebra, em silêncio, o `includes('não encontrada')` do cliente. O
  conserto é um código de erro no payload — trabalho próprio, não desta etapa.
