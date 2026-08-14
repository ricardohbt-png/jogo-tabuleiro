# Etapa 5 — Lote 1: os catálogos estáticos do cliente — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Traduzir os **131 textos que vivem em estruturas de dados** do `game.js` — o primeiro lote da etapa 5, e o de forma mais uniforme.

**Arquitetura:** Estes textos não estão espalhados em templates de render: moram em objetos de topo chaveados por id. O `I18N.aplicarCatalogo` já percorre estrutura assim; o que falta é (a) dar `id` às entradas que não têm, (b) ensinar o filtro a preferir a chave `ui.*` do cliente à `cat.*` do servidor, e (c) escrever as chaves. Nenhum template de render é tocado neste lote.

**Stack:** JavaScript vanilla (`game.js`, `src/i18n.js`, `src/lang/interface.js`), testes `node` e `python`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `game.js` e `server.py` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A`. Combine a pausa do `game.js` antes de começar.
- **A etapa 5.0 (fundação) fechou:** o observador do `document.body` aplica `_i18nApply` em markup inserido depois, e o ícone de habilidade é achado por `data-ability-id`.
- **A Task 1 deste lote fechou** (`3d0d470`): `src/lang/interface.js` existe, é carregado no `index.html` e fundido pelo `_load_lang()` do servidor.
- **`I18N.aplicarCatalogo(obj, soNome)`** percorre o objeto e casa `cat.<família>.<id>`, trocando `name`/`nome` e — quando `soNome` é falso — `desc`/`descricao`. **Não tem saída antecipada em português**: é isso que faz a volta ao `pt` restaurar o original.
- **`tools/js_strings.py`** é o tokenizador que mede texto em JS. Use-o para contar; **não use regex por linha**, que ignora template multilinha (foi assim que a medição errou três vezes).
- **O dicionário é JSON estrito** dentro do objeto: sem comentário DENTRO das chaves.
- Suítes verdes: `test_interface` (6), `js_strings` (8), `test_idioma` (36), `test_vocabulario` (38), `test_erros` (9), `test_narracao` (67), `test_idioma_cliente` (27), `test_vocabulario_cliente` (45).

### Fatos medidos, com o tokenizador (não precisa re-verificar)

| estrutura | linhas | textos | observação |
|---|---|---:|---|
| `GRIMORIO_CLIENT` | 10707–11024 | **61** | 27 magias; **19 textos com +200 chars** — os cards HTML |
| `_CSD` | 23589–23704 | **50** | nome, `desc` e `skills[]` das 6 classes |
| `ABILITY_NAME_TO_ID` | 110–123 | 9 | **não traduzir** — chave de lógica |
| `HERO_DATA` | 23425–23540 | 5 | `class:` em maiúsculas |
| `_TIPO_ITEM_LABEL` | 13300–13304 | 5 | |
| `_OBJ_LABELS` | 4622–4630 | 4 | |
| `_ELEMENTAL_HABILIDADES_LEWIS` | 11972–11977 | 4 | |
| `_MP_CUSTO_LBL` | 12103 | 2 | |

**Total 140; 131 a traduzir.** O resto do `game.js` (567 textos) são os lotes 2 e 3.

**A ordem das tarefas é deliberada:** os rótulos pequenos vêm primeiro para o mecanismo
`ui.*` ser provado em algo barato; o `GRIMORIO_CLIENT`, que é o mais denso e o único com
risco de perda de conteúdo, vem por último, já com o caminho batido.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/i18n.js` | `aplicarCatalogo` prefere a chave `ui.*` à `cat.*` |
| `src/lang/interface.js` | as 131 chaves |
| `game.js` | `id` nas entradas que não têm; chamadas de `aplicarCatalogo` |
| `tools/test_vocabulario_cliente.js` | testes do mecanismo e de cada estrutura |
| `tools/test_interface.py` | `FECHADAS` ao fim do lote |

---

## Task 2: A prioridade `ui.*` sobre `cat.*`

**Arquivos:**
- Modificar: `src/i18n.js`, `tools/test_vocabulario_cliente.js`

Este é o mecanismo de que todas as tarefas seguintes dependem. Sem ele, traduzir a
descrição de um catálogo do cliente pegaria a frase curta do **servidor** e apagaria o
card rico — que é exatamente por que a etapa 3 chamou `aplicarCatalogo(X, true)`.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar em `tools/test_vocabulario_cliente.js`, antes do bloco de resultado:

```js
console.log("");
console.log("[U] A chave ui.* tem prioridade sobre a cat.* do servidor");
DICT["cat.magia.bola_fogo.nome"] = { pt: "Bola de Fogo", en: "Fireball" };
DICT["cat.magia.bola_fogo.desc"] = { pt: "Frase curta do servidor",
                                     en: "Server short line" };
DICT["ui.magia.bola_fogo.desc"]  = { pt: "<b>Card rico do cliente</b>",
                                     en: "<b>Rich client card</b>" };
const cliente = { bola_fogo: { id: "bola_fogo", nome: "Bola de Fogo",
                               descricao: "<b>Card rico do cliente</b>" } };
I18N.setLang("en");
I18N.aplicarCatalogo(cliente, false);
check("a descricao usa a chave ui.*, nao a cat.*",
      cliente.bola_fogo.descricao === "<b>Rich client card</b>");
check("o nome continua vindo da cat.* quando nao ha ui.*",
      cliente.bola_fogo.nome === "Fireball");
I18N.setLang("pt");
I18N.aplicarCatalogo(cliente, false);
check("voltar ao portugues restaura o card do cliente",
      cliente.bola_fogo.descricao === "<b>Card rico do cliente</b>");

// Sem chave ui.*, a cat.* ainda vale — e é isso que torna seguro trocar as
// chamadas para soNome=false ANTES de escrever todas as chaves.
const semUi = { relampago: { id: "relampago", nome: "Relâmpago",
                             descricao: "<b>Card sem chave ui</b>" } };
DICT["cat.magia.relampago.desc"] = { pt: "Curta", en: "Short" };
I18N.setLang("en");
I18N.aplicarCatalogo(semUi, false);
check("sem ui.*, cai na cat.* (comportamento antigo)",
      semUi.relampago.descricao === "Short");
I18N.setLang("pt");
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: `45 passaram, 2 falharam` — as duas de `ui.*`; as outras duas já passam, porque
descrevem o comportamento atual.

- [ ] **Passo 3: Implementar**

Em `src/i18n.js`, dentro de `aplicarCatalogo`, substituir os dois blocos que hoje usam
`base + '.nome'` e `base + '.desc'` por uma resolução que prefere `ui.`:

```js
      // A chave ui.* (do CLIENTE) vence a cat.* (do servidor) quando as duas
      // existem: os catálogos do cliente guardam um card HTML com alcance e
      // efeito por rodada, contra uma frase curta no servidor. A etapa 3 evitou
      // o choque passando soNome=true; a chave própria resolve sem perder
      // informação. Sem ui.*, o comportamento é o de antes.
      const baseUi = base && base.replace(/^cat\./, 'ui.');
      const kNome = (baseUi && tem(baseUi + '.nome')) ? baseUi + '.nome'
                  : (base && tem(base + '.nome'))     ? base + '.nome' : null;
      const kDesc = (baseUi && tem(baseUi + '.desc')) ? baseUi + '.desc'
                  : (base && tem(base + '.desc'))     ? base + '.desc' : null;
```

e usar `kNome` / `kDesc` no lugar das expressões `tem(base + '…')` dos dois blocos,
mantendo o `!soNome` na condição da descrição.

- [ ] **Passo 4: Rodar**

```bash
node --check src/i18n.js && node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js
```

Esperado: `49 passaram, 0 falharam` e `27 passaram, 0 falharam`.

- [ ] **Passo 5: Commit**

```bash
git status --short
git add src/i18n.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): a chave ui.* do cliente vence a cat.* do servidor"
```

---

## Task 3: Os rótulos pequenos (20 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`

`HERO_DATA` (5), `_TIPO_ITEM_LABEL` (5), `_OBJ_LABELS` (4),
`_ELEMENTAL_HABILIDADES_LEWIS` (4), `_MP_CUSTO_LBL` (2).

- [ ] **Passo 1: Ver a forma de cada uma**

```bash
python -c "
import io, sys; sys.stdout.reconfigure(encoding='utf-8')
s = io.open('game.js', encoding='utf-8').read()
for nome in ('HERO_DATA','_TIPO_ITEM_LABEL','_OBJ_LABELS',
             '_ELEMENTAL_HABILIDADES_LEWIS','_MP_CUSTO_LBL'):
    i = s.find('const ' + nome)
    print('---', nome); print(s[i:i+400] if i >= 0 else 'NAO ACHADO'); print()
"
```

Distinga as duas formas, porque o tratamento difere:

- **`{id: {nome: 'x'}}`** — objeto com campo: passa pelo `aplicarCatalogo`.
- **`{id: 'x'}`** — valor string direto: o filtro **não** o alcança (ele troca campos de
  objeto, não valores de um mapa). Estes viram `t('ui.<área>.<id>')` no **ponto de uso**.

- [ ] **Passo 2: Migrar uma estrutura, medindo antes e depois**

Para cada uma, na ordem acima:

```bash
python tools/test_interface.py 2>&1 | head -6
```

Anote o total. Migre a estrutura (chaves no `interface.js` com o `pt` **idêntico** ao texto
de hoje; `aplicarCatalogo` ou `t()` conforme a forma). Rode de novo: **o total tem de cair
exatamente pelo número daquela estrutura**. Se não cair, ela não estava sendo contada onde
você pensou — **pare e meça antes de seguir**.

- [ ] **Passo 3: Rodar**

```bash
node --check game.js && node --check src/lang/interface.js && node tools/test_vocabulario_cliente.js && python tools/test_interface.py
```

- [ ] **Passo 4: Commit**

```bash
git status --short
git add game.js src/lang/interface.js
git commit -m "feat(i18n): rotulos de tipo de item, objetivo, elemental e custo"
```

---

## Task 4: O `_CSD` — a tela de seleção de herói (50 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

Por classe: `name` (VICTOR COICE BRAVO), `desc` (a frase dramática) e `skills[]` com
`name`/`nome` e `desc`. É a primeira tela que o jogador vê.

- [ ] **Passo 1: Escrever o teste que falha**

```js
console.log("");
console.log("[C] O _CSD (selecao de heroi) traduz nome, desc e skills");
DICT["ui.classe.warrior.nome"] = { pt: "VICTOR COICE BRAVO", en: "VICTOR THE BOLD" };
DICT["ui.classe.warrior.desc"] = { pt: "Tanque de aco.", en: "A tank of steel." };
DICT["ui.skill.mira_certeira.nome"] = { pt: "Mira Certeira", en: "Sure Aim" };
const csd = { warrior: { id: "warrior", name: "VICTOR COICE BRAVO",
                         desc: "Tanque de aco.",
                         skills: [{ id: "mira_certeira", name: "Mira Certeira" }] } };
I18N.setLang("en");
I18N.aplicarCatalogo(csd, false);
check("nome da classe traduzido", csd.warrior.name === "VICTOR THE BOLD");
check("desc da classe traduzida", csd.warrior.desc === "A tank of steel.");
check("nome da skill traduzido", csd.warrior.skills[0].name === "Sure Aim");
I18N.setLang("pt");
I18N.aplicarCatalogo(csd, false);
check("voltar ao portugues restaura o _CSD",
      csd.warrior.name === "VICTOR COICE BRAVO");
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

- [ ] **Passo 3: Dar `id` a cada entrada**

No `game.js`, cada classe do `_CSD` ganha `id` igual à sua chave, e cada skill ganha o id
que já existe em `ABILITY_NAME_TO_ID`:

```js
  warrior:{ id:'warrior', name:'VICTOR COICE BRAVO', cls:'VICTOR', …
    skills:[
      {id:'mira_certeira', icon:'⚔️', name:'Mira Certeira', …},
```

O id da skill é **o mesmo** que o `data-ability-id` da etapa 5.0 usa — é o que liga o
ícone ao texto. **Emita também o `data-ability-id`** no render que monta o card da skill
na seleção; sem ele, o ícone some quando o nome vira inglês (provado no navegador na 5.0).

- [ ] **Passo 4: Chamar o `aplicarCatalogo`**

Junto das outras chamadas em `game.js`:

```js
  if (typeof _CSD !== 'undefined') I18N.aplicarCatalogo(_CSD, false);
```

- [ ] **Passo 5: Traduzir os 50**

Chaves `ui.classe.<id>.nome` / `.desc` e `ui.skill.<id>.nome` / `.desc` no
`src/lang/interface.js`, com o `pt` idêntico ao texto de hoje.

- [ ] **Passo 6: Verificar na tela**

```bash
node --check game.js && node tools/test_vocabulario_cliente.js && python tools/test_interface.py
```

Depois, no navegador: abra a seleção de herói em inglês e confira nome, descrição e as
habilidades de cada classe — **e que os ícones continuam lá**.

**Recarregue com cache-buster** (`?v=algo`) e confirme no console que a versão nova
carregou antes de concluir: o navegador serve o `game.js` do cache, e isso já falseou uma
prova na 5.0.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): tela de selecao de heroi traduzida"
```

---

## Task 5: O `GRIMORIO_CLIENT` (61 textos, 19 deles cards HTML)

**Arquivos:**
- Modificar: `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

A parte mais densa do lote. São 27 magias, cada uma com `resumo` (frase curta) e
`descricao` (card HTML de ~10 linhas com alcance, área e efeito por rodada). O nome já é
traduzido desde a etapa 3; falta `resumo` e `descricao`.

- [ ] **Passo 1: Gerar o lado `pt` a partir do arquivo, não transcrever**

O `pt` tem de ser **idêntico** ao texto do `game.js` — é o fallback. Transcrever 19 cards
HTML à mão é onde entra erro invisível. Extraia-os:

```bash
python - <<'EOF'
import io, json, re, sys
sys.path.insert(0, "tools"); sys.stdout.reconfigure(encoding="utf-8")
from js_strings import literais
s = io.open("game.js", encoding="utf-8").read()
i = s.index("const GRIMORIO_CLIENT"); a = s.index("{", i)
prof, k = 0, a
while k < len(s):
    if s[k] == "{": prof += 1
    elif s[k] == "}":
        prof -= 1
        if prof == 0: break
    k += 1
bloco = s[a:k+1]
# id de cada magia e os campos resumo/descricao, na ordem em que aparecem
ids = re.findall(r"\n  (\w+)\s*:\s*\{", bloco)
out = {}
for m in re.finditer(r"\n  (\w+)\s*:\s*\{", bloco):
    ini = m.end()
    fim = bloco.find("\n  ", ini)
    corpo = bloco[ini:fim if fim > 0 else len(bloco)]
    for campo, chave in (("resumo", "resumo"), ("descricao", "desc")):
        mm = re.search(campo + r"\s*:\s*([\"'`])", corpo)
        if not mm: continue
        txt = literais(corpo[mm.start():])
        if txt: out[f"ui.magia.{m.group(1)}.{chave}"] = txt[0][2]
io.open("scratchpad/grimorio_pt.json", "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=2))
print(len(out), "chaves extraidas -> scratchpad/grimorio_pt.json")
EOF
```

Confira o arquivo: 27 `resumo` + 27 `desc` = 54 chaves. Se vier menos, o recorte falhou —
**pare e ajuste antes de traduzir**.

- [ ] **Passo 2: Escrever as chaves com o `en` vazio**

Um script que lê o JSON acima e escreve no `src/lang/interface.js` cada chave como
`{"pt": <extraído>, "en": ""}`. Com o `en` vazio o motor cai no `pt`, então **nada quebra**
enquanto a tradução não vem — e o jogo pode ser rodado a qualquer momento.

- [ ] **Passo 3: Trocar a chamada para `soNome = false`**

Em `game.js`:

```js
  if (typeof GRIMORIO_CLIENT !== 'undefined') I18N.aplicarCatalogo(GRIMORIO_CLIENT, false);
```

Seguro agora, porque a Task 2 fez a `ui.*` vencer a `cat.*` e o Passo 2 já criou as chaves
`ui.magia.*.desc` com o `pt` correto.

- [ ] **Passo 4: Provar que o card não encolheu — ANTES de traduzir**

Este é o passo que protege o conteúdo. No navegador (com cache-buster), em **português**,
abra o tooltip de 3 magias e confirme que o card está completo (alcance, área, efeito por
rodada) — não a frase curta do servidor. Se encolheu, a chave `ui.*` não foi encontrada:
**pare e conserte antes de seguir**.

- [ ] **Passo 5: Traduzir os 54**

Preencha o `en` de cada chave. Regras: as **tags HTML passam intactas**; `<b>Alcance:</b>`
vira `<b>Range:</b>`; números, dados (`1d6`) e nomes de mecânica seguem o glossário
(CA = AC, CD = DC, Reflexos = Reflex, rodada = round).

Faça em **dois commits**, metade cada — 54 textos densos numa revisão só é onde escapa erro.

- [ ] **Passo 6: Verificar nos dois idiomas**

No navegador: o mesmo tooltip em `pt` e em `en`, os dois com o card completo.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): grimorio do cliente -- resumo e card de cada magia"
```

---

## Task 6: Fechamento do lote

**Arquivos:**
- Modificar: `tools/test_interface.py`, `CLAUDE.md`

- [ ] **Passo 1: Marcar as funções fechadas**

```bash
python tools/test_interface.py
```

Acrescente ao conjunto `FECHADAS` os nomes que o placar atribui a estas estruturas.
**Use os nomes que o placar mostra**, não os que você espera: a atribuição é pela
declaração anterior mais próxima, então o `_CSD` aparece sob `calcularVidaMaxima`.

- [ ] **Passo 2: Rodar tudo**

```bash
python tools/test_interface.py && python tools/js_strings.py && python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: todas verdes, e o placar em ~576 (707 − 131).

- [ ] **Passo 3: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

- [ ] **Passo 4: Documentar no `CLAUDE.md`**

Um bloco `>` cobrindo: o `src/lang/interface.js`; a **prioridade `ui.*` sobre `cat.*`** e
por que a etapa 3 tinha usado `soNome=true`; o `_CSD` com `id` por entrada ligado ao
`data-ability-id`; e o número novo do placar.

- [ ] **Passo 5: Commit**

```bash
git add tools/test_interface.py CLAUDE.md
git commit -m "docs(i18n): catalogos estaticos do cliente traduzidos"
```

---

## Fora deste lote (registrado, não esquecido)

- **567 textos** no resto do `game.js`, mais 69 no `gameState.js` e 9 no
  `inventoryModal.js` — os lotes 2 e 3.
- **`ABILITY_NAME_TO_ID` (9)** não se traduz: é chave de lógica, e a 5.0 já a tornou
  dispensável para o ícone.
- **O placar atribui cada texto à declaração anterior mais próxima**, então dado declarado
  logo abaixo de uma função conta para ela (`_CSD` aparece sob `calcularVidaMaxima`). Serve
  como termômetro relativo — o total cai —, não como recorte fino. Por isso este lote foi
  escopado pelas estruturas, medidas com o tokenizador.
