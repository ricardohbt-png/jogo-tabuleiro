# Etapa 5 — Lote 1: os catálogos estáticos do cliente — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Traduzir os **131 textos que vivem em estruturas de dados** do `game.js` — o primeiro lote da etapa 5, e o de forma mais uniforme.

**Arquitetura:** Estes textos não estão espalhados em templates de render: moram em objetos de topo chaveados por id. O `I18N.aplicarCatalogo` já percorre estrutura assim; o que falta é (a) dar `id` às entradas que não têm, (b) ensinar o filtro a preferir a chave `ui.*` do cliente à `cat.*` do servidor, e (c) escrever as chaves.

---

## ⚠️ REVISÃO — 2026-08-14, depois da Task 3

As Tasks 2 e 3 fecharam. Ao medir o terreno da Task 4 apareceram **quatro fatos
que a versão original deste plano não conhecia**, e três deles a contradizem. As
Tasks 4, 5 e 6 abaixo foram reescritas; o que segue é o porquê.

**(1) Uma chave `ui.*` sozinha nunca é encontrada.** `_chaveBase` só fixa a base
quando existe `cat.<família>.<id>` no dicionário — `_tentaFamilias` testa
literalmente `tem('cat.' + fam + '.' + id + '.nome')`. Como não há família
`skill`, o `ui.skill.mira_certeira.nome` do teste da Task 4 original jamais seria
achado, e nenhum dos passos seguintes consertava isso. **A prioridade `ui.*` da
Task 2 continua correta e necessária** — ela decide QUAL chave vence quando as
duas existem; ela não cria base onde não há `cat.*`. Foi este mesmo muro que, na
Task 3, empurrou `_ELEMENTAL_HABILIDADES_LEWIS` para o `_rotulo` apesar de ele
ser `{id:{objeto}}`.

**(2) `ui.magia.<id>.desc` seria disputada por dois textos diferentes.**
`_CSD.mage.skills[]` são 10 magias com uma frase curta cada; o `GRIMORIO_CLIENT`
são as MESMAS magias com o card HTML. Se as duas estruturas usassem id de magia,
a Task 5 sobrescreveria a Task 4 — e, como a `ui.` vence a `cat.`, o card de 10
linhas cairia dentro da lista da tela de seleção.

**(3) O `resumo` do `GRIMORIO_CLIENT` não tem leitor nenhum, e o
`aplicarCatalogo` não o alcançaria de todo jeito.** `CAMPOS_DESC` é
`['desc','descricao']`; `resumo` não está lá, e não pode entrar — o laço para no
primeiro campo que casa (`break`), então um objeto com `resumo` E `descricao`
teria só um dos dois trocado. Medido: `resumo` aparece 27× no `game.js`, todas as
27 na própria declaração. São 23 textos mortos no placar.

**(4) O placar conta o `pt` que o `aplicarCatalogo` já traduz.** Este é o fato
que mais muda o plano. O `aplicarCatalogo` traduz **mutando o objeto**, então a
string em português tem de continuar no `game.js` para haver o que trocar — ela é
load-bearing, não é dívida. Só que o tokenizador não sabe disso e a conta como
pendente. São 12 `nome` + 26 `descricao` do `GRIMORIO_CLIENT`, mais o que já
acontece com `ARMADILHAS_LUCCAS` e `CATALOGO_ITENS` desde a etapa 3. Sem
consertar o **instrumento**, a Task 5 é um teto que não se pode furar, e o alvo
de ~576 da Task 6 é inalcançável. Daí a **Task 4.5**, nova.

**O que NÃO muda:** o mecanismo da Task 2; a ordem (barato primeiro, denso por
último); e a regra de que o `pt` de toda chave nova é idêntico ao texto de hoje.

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

### Correções da revisão à tabela acima

| estrutura | o que a tabela dizia | o que a medição mostrou |
|---|---|---|
| `ABILITY_NAME_TO_ID` | 9 entradas | **24** — cobre quase todo `skills[]`, e é a fonte de id da Task 4 |
| `GRIMORIO_CLIENT` (61) | "resumo + descricao" | **12 `nome` + 26 `descricao` + 23 `resumo`**; os 23 `resumo` são mortos, os outros 38 são load-bearing |
| `_CSD` (50) | "nome, desc e skills[]" | confere; mas as skills **não têm `id`** e há `skills` × `selectionSkills` (só o 2º é renderizado para o mago) |
| `HERO_DATA` (5) | "`class:` em maiúsculas" | 3 `class` + 2 campos de `habilidadeClasse` **sem leitor nenhum** |

**Placar depois da Task 3: 687.** A conta do lote passou a ser
`687 − 50 (Task 4) − 61 (Task 5, sendo 23 por remoção e 38 pelo instrumento) = 576`.
O alvo original se mantém, por um caminho diferente.

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
| `tools/test_interface.py` | a regra do `pt` já dicionarizado (Task 4.5) + `FECHADAS` ao fim do lote |

---

## Task 2: A prioridade `ui.*` sobre `cat.*` — ✅ CONCLUÍDA (`3e29142`)

> Passos abaixo mantidos como registro. Resultado: `test_vocabulario_cliente`
> 49/0. **Leia o ponto (1) da revisão**: este mecanismo escolhe entre `ui.` e
> `cat.` quando as duas existem — ele não faz uma `ui.` sozinha ser encontrada.

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

## Task 3: Os rótulos pequenos (20 textos) — ✅ CONCLUÍDA (`733207b`, `ebe2e11`, `4d0f138`)

> Placar 707 → 687. As cinco estruturas caíram no helper novo
> `_rotulo(id, prefixo, padrao)` — **inclusive as duas que são `{id:{objeto}}`**,
> pelo motivo do ponto (1) da revisão. Duas descobertas que valem para as tasks
> seguintes: **(a)** `HERO_DATA[*].class` tinha um leitor só e
> `HERO_DATA.pedro.habilidadeClasse.{nome,alcance,descricao}` não tinha nenhum —
> português sem leitor não tem onde chamar `t()`, e foi removido (a cópia gêmea
> em `gameState.js` saiu junto, senão o comentário "sincronizado" viraria
> mentira); **(b)** por isso, **grepe os leitores antes de traduzir** qualquer
> estrutura.

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

## Task 4 (REESCRITA): O `_CSD` — a tela de seleção de herói (50 textos)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

**Mudança de abordagem.** A versão original mandava dar `id` às entradas e chamar
`aplicarCatalogo(_CSD, false)`. Isso não funciona, pelos pontos (1) e (2) da revisão: as
skills não têm família `cat.*` que estabeleça a base, e usar id de magia nas skills do
mago colidiria com a Task 5. O `_CSD` vai pelo **`_rotulo` no ponto de render**, sob o
namespace próprio **`ui.selecao.*`** — o mesmo caminho já provado três vezes na Task 3.

Isso é barato porque **toda a leitura de texto do `_CSD` está em dois lugares**:
`_csfShowPanel` (`d.name` → `#cs-hero-name`, `d.cls` → `#cs-hero-cls`, `d.desc` →
`#cs-desc`) e o `skillsForSelect.map` (`sk.name ?? sk.nome`, `sk.desc`). Há um terceiro
uso de `d.cls`, no `toast` de confirmação da escolha.

- [ ] **Passo 1: Medir os leitores antes de mexer** (lição da Task 3)

```bash
grep -n "_CSD\b" game.js
grep -n "\.cls\b\|sk\.name\|sk\.nome\|sk\.desc\|d\.desc\|d\.name" game.js | head -20
```

Confirme que os únicos consumidores de TEXTO são os três acima. Se aparecer outro,
**inclua-o na migração** — um leitor esquecido mostra a chave crua na tela.

Resolva também o caso do **mago**: `skillsForSelect` é
`classId === 'mage' ? (d.selectionSkills || d.skills.slice(0,4)) : d.skills`, e como
`selectionSkills` sempre existe, o `_CSD.mage.skills[]` (as 10 magias com frase curta)
**nunca é renderizado**. Cheque se algo mais o lê; se não, ele é texto morto como os da
Task 3 e sai inteiro — o que também elimina de vez o risco de colisão do ponto (2).
Se preferir preservá-lo, ele precisa de ids sob `ui.selecao.*`, **nunca** de ids de magia.

- [ ] **Passo 2: Dar `id` a cada skill**

Cada entrada de `skills[]`/`selectionSkills[]` ganha o `id` que já existe em
`ABILITY_NAME_TO_ID` (são **24** entradas, não 9 — ver a correção da tabela). As classes
não precisam de campo novo: a **chave do `_CSD`** (`warrior`, `mage`, …) já é o id.

- [ ] **Passo 3: Emitir o `data-ability-id`**

No `skillsForSelect.map`, o `.cs-skill-name` **ainda não emite** o atributo:

```js
  <div class="cs-skill-name" data-ability-id="${_esc(sk.id)}">…</div>
```

Sem ele o ícone some quando o nome vira inglês — o scan por texto da 5.0 é retaguarda e
está chaveado em português. Isto foi **provado no navegador** na 5.0; não pule.

- [ ] **Passo 4: Trocar o texto pelo `_rotulo` e ESVAZIAR o `_CSD`**

Nos três sites, no padrão da Task 3:

```js
  _rotulo(classId, 'ui.selecao.classe',      '')   // name
  _rotulo(classId, 'ui.selecao.classe.cls',  '')   // cls
  _rotulo(classId, 'ui.selecao.classe.desc', '')   // desc
  _rotulo(sk.id,   'ui.selecao.skill',       '')   // name/nome
  _rotulo(sk.id,   'ui.selecao.skill.desc',  '')   // desc
```

E **remova** `name`/`cls`/`desc` das classes e `name`/`nome`/`desc` das skills do `_CSD`.
O que fica são os campos não-textuais (`skyHex`, `lightHex`, `spd`, `portrait`, `hp`,
`stats`, `icon`/`icone`, `fome_cost`, `sede_cost`, `id`). Manter o português como fallback
faria o placar não cair — é a decisão já registrada no commit `733207b`.

- [ ] **Passo 5: Escrever as chaves**

`ui.selecao.classe.<id>` / `.cls.<id>` / `.desc.<id>` e `ui.selecao.skill.<id>` /
`.desc.<id>` no `src/lang/interface.js`, com o `pt` **idêntico** ao texto de hoje.
Extraia do arquivo em vez de transcrever (o script do Passo 1 da Task 5 serve de modelo).

- [ ] **Passo 6: Teste de cobertura no node**

O `_rotulo` mora no `game.js` e não carrega no node, então o teste do motor não o alcança.
Teste o que dá para testar sem navegador: que **toda chave `ui.selecao.*` citada no
`game.js` existe no dicionário** com `pt` e `en`. Acrescente em
`tools/test_vocabulario_cliente.js`; é a mesma varredura estática que já pega chave órfã
nas outras suítes de idioma.

- [ ] **Passo 7: Rodar**

```bash
node --check game.js && node tools/test_vocabulario_cliente.js && python tools/test_interface.py
```

O placar tem de cair **exatamente 50** (687 → 637). Se cair menos, sobrou texto no `_CSD`;
se cair mais, você removeu algo que não era desta task — **pare e meça**.

- [ ] **Passo 8: Verificar na tela**

No navegador, com **cache-buster** (`?v=algo`): abra a seleção de herói nos DOIS idiomas e
confira, por classe, nome/cls/descrição e as quatro habilidades — **e que os ícones
continuam lá**. Antes de concluir, cheque no console que a versão nova carregou (por um
símbolo que só existe depois da sua mudança); o navegador serve o `game.js` do cache e
isso já falseou uma prova na 5.0.

- [ ] **Passo 9: Commit**

```bash
git status --short
git add game.js src/lang/interface.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): tela de selecao de heroi traduzida (Lote 1, Task 4)"
```

---

## Task 4.5 (NOVA): O placar precisa parar de contar o `pt` load-bearing

**Arquivos:**
- Modificar: `tools/test_interface.py`

**Por que existe.** O `aplicarCatalogo` traduz **mutando o objeto**: para haver o que
trocar, a string em português tem de continuar no `game.js`. Ela não é dívida — é a
fonte. Mas o tokenizador não distingue isso de trabalho pendente, e conta 38 textos do
`GRIMORIO_CLIENT` (12 `nome` + 26 `descricao`) que já estão traduzidos desde a etapa 3 ou
estarão ao fim da Task 5. Sem esta task, a Task 5 tem um teto que nada fura e o alvo da
Task 6 é inalcançável.

Isto **não é o mesmo** que o "fallback em português é texto morto" da Task 3. Lá o
português não tinha leitor nenhum e nada o traduzia; aqui ele é lido, é mutado e é a
única cópia que existe no código.

- [ ] **Passo 1: Escrever o teste que falha**

Em `tools/test_interface.py`, uma verificação nova: um literal do `game.js` cujo texto
seja **exatamente** o `pt` de alguma chave `cat.*` ou `ui.*` do dicionário **não conta**
no placar. Prove com um caso conhecido — `'Bola de Fogo'` está em
`cat.magia.bola_fogo.nome` e hoje é contado.

- [ ] **Passo 2: Implementar**

Reúna os `pt` do dicionário (reuse o carregador que o `tools/test_vocabulario.py` já tem
para os `src/lang/*.js`) e filtre-os no `_por_funcao`.

**Restrinja a `cat.*` e `ui.*`** — as duas famílias que o `aplicarCatalogo` e o `_rotulo`
usam. Incluir `erro.*`/`narracao.*` faria uma frase do cliente que por acaso coincida com
uma do servidor sumir do placar, mascarando trabalho real dos lotes 2 e 3.

Documente no cabeçalho do arquivo, junto da nota que já explica por que a contagem é por
função: **o casamento é por texto exato e é uma aproximação** — é possível, em tese, um
literal coincidir com um `pt` sem estar ligado a nada. O placar é termômetro, não prova;
a prova é o navegador.

- [ ] **Passo 3: Rodar e registrar o degrau**

```bash
python tools/test_interface.py
```

O total cai de uma vez pelos textos que já estavam traduzidos (esperado: os 12 `nome` do
`GRIMORIO_CLIENT` e o que `ARMADILHAS_LUCCAS`/`CATALOGO_ITENS` trouxerem da etapa 3).
**Anote o número** — é a nova linha de base, e a Task 5 é medida a partir dela.

- [ ] **Passo 4: Commit**

```bash
git status --short
git add tools/test_interface.py
git commit -m "test(i18n): o placar nao conta o pt que o aplicarCatalogo ja traduz"
```

---

## Task 5 (REVISADA): O `GRIMORIO_CLIENT` (61 textos: 26 `descricao`, 23 `resumo`, 12 `nome`)

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

A parte mais densa do lote. São 27 magias, cada uma com `resumo` (frase curta),
`descricao` (card HTML de ~10 linhas com alcance, área e efeito por rodada) e `nome`.

**O que a revisão mudou aqui:**

- Os **`nome`** já são traduzidos desde a etapa 3 e **ficam como estão** — são a fonte que
  o `aplicarCatalogo` muta. Saem do placar pela Task 4.5, não por edição.
- Os **`resumo` são 23 textos mortos**: `grep` mostra as 27 ocorrências todas na própria
  declaração, sem um leitor sequer. Além disso o `aplicarCatalogo` **nunca os alcançaria**,
  porque `CAMPOS_DESC` é `['desc','descricao']` e o laço para no primeiro campo que casa —
  um objeto com `resumo` E `descricao` teria só um dos dois trocado. **Passo 0 novo.**
- Só os **26 `descricao`** são trabalho de tradução de verdade.

- [ ] **Passo 0: Confirmar que o `resumo` continua morto e removê-lo**

```bash
grep -rn "resumo" game.js src/ --include=*.js | grep -v "^src/lang"
```

Se só aparecerem as declarações, remova o campo das 27 magias. Se **algum leitor tiver
surgido** (o usuário edita o `game.js` em paralelo), pare: ele passa a ser tradução por
`_rotulo` no ponto de uso, como na Task 3.

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
    for campo, chave in (("descricao", "desc"),):   # o resumo saiu no Passo 0
        mm = re.search(campo + r"\s*:\s*([\"'`])", corpo)
        if not mm: continue
        txt = literais(corpo[mm.start():])
        if txt: out[f"ui.magia.{m.group(1)}.{chave}"] = txt[0][2]
io.open("scratchpad/grimorio_pt.json", "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=2))
print(len(out), "chaves extraidas -> scratchpad/grimorio_pt.json")
EOF
```

Confira o arquivo: **27 chaves `ui.magia.<id>.desc`** (uma por magia). Se vier menos, o
recorte falhou — **pare e ajuste antes de traduzir**.

- [ ] **Passo 2: Escrever as chaves com o `en` vazio**

Um script que lê o JSON acima e escreve no `src/lang/interface.js` cada chave como
`{"pt": <extraído>, "en": ""}`. Com o `en` vazio o motor cai no `pt`, então **nada quebra**
enquanto a tradução não vem — e o jogo pode ser rodado a qualquer momento.

- [ ] **Passo 3: Trocar a chamada para `soNome = false`**

Em `game.js`:

```js
  if (typeof GRIMORIO_CLIENT !== 'undefined') I18N.aplicarCatalogo(GRIMORIO_CLIENT, false);
```

A chamada mora em `_aplicarCatalogosEstaticos()` (`game.js`), junto das de
`ARMADILHAS_LUCCAS` e `CATALOGO_ITENS` — **troque só a do `GRIMORIO_CLIENT`**; as outras
duas seguem em `true` até os lotes 2 e 3.

Seguro **só nesta ordem**, e a ordem é o ponto crítico da task: as **27** magias têm
`cat.magia.<id>.desc` no servidor (medido: 27/27). Virar `soNome=false` antes do Passo 2
substituiria os 27 cards HTML pela frase curta do servidor. Com as chaves `ui.magia.*.desc`
já escritas e o `pt` correto, a Task 2 garante que a `ui.` vence a `cat.` e o card
sobrevive.

- [ ] **Passo 4: Provar que o card não encolheu — ANTES de traduzir**

Este é o passo que protege o conteúdo. No navegador (com cache-buster), em **português**,
abra o tooltip de 3 magias e confirme que o card está completo (alcance, área, efeito por
rodada) — não a frase curta do servidor. Se encolheu, a chave `ui.*` não foi encontrada:
**pare e conserte antes de seguir**.

- [ ] **Passo 5: Traduzir os 27**

Preencha o `en` de cada chave. Regras: as **tags HTML passam intactas**; `<b>Alcance:</b>`
vira `<b>Range:</b>`; números, dados (`1d6`) e nomes de mecânica seguem o glossário
(CA = AC, CD = DC, Reflexos = Reflex, rodada = round).

Faça em **dois commits**, metade cada — 27 cards densos numa revisão só é onde escapa erro.

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

Esperado: todas verdes, e o placar em **~576** — mas por três caminhos diferentes, e vale
conferir cada degrau em vez de só o total:

| origem | textos | como saiu |
|---|---:|---|
| Task 3 | 20 | migrados para `_rotulo`; o português **removido** do `game.js` |
| Task 4 | 50 | idem, sob `ui.selecao.*` |
| Task 5 | 23 | `resumo` **morto**, removido |
| Task 4.5 | 38 | `nome`/`descricao` **continuam no arquivo** — são a fonte que o `aplicarCatalogo` muta; o instrumento é que parou de contá-los |

Se o total bater mas um degrau não, alguma coisa saiu por engano — **meça o degrau**.

- [ ] **Passo 3: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

- [ ] **Passo 4: Documentar no `CLAUDE.md`**

Um bloco `>` cobrindo:

- o `src/lang/interface.js` e a convenção `ui.<área>.<slug>`;
- a **prioridade `ui.*` sobre `cat.*`** e por que a etapa 3 tinha usado `soNome=true`;
- **os dois caminhos, e como escolher entre eles** — `aplicarCatalogo` quando existe
  `cat.<família>.<id>` no servidor (`GRIMORIO_CLIENT`), `_rotulo` no ponto de render
  quando não existe (`_CSD`, elementais, rótulos). Este é o fato que mais custou a
  descobrir: uma chave `ui.*` sozinha **não é encontrada**, porque `_chaveBase` exige uma
  `cat.*` para fixar a base;
- o `_CSD` sob `ui.selecao.*` com `id` por skill ligado ao `data-ability-id`;
- que **`nome`/`descricao` do `GRIMORIO_CLIENT` continuam em português no `game.js` de
  propósito** — são a fonte que o `aplicarCatalogo` muta —, e que o placar sabe disso;
- o número novo do placar.

- [ ] **Passo 5: Commit**

```bash
git add tools/test_interface.py CLAUDE.md
git commit -m "docs(i18n): catalogos estaticos do cliente traduzidos"
```

---

## Fora deste lote (registrado, não esquecido)

- **567 textos** no resto do `game.js`, mais 69 no `gameState.js` e 9 no
  `inventoryModal.js` — os lotes 2 e 3.
- **`ABILITY_NAME_TO_ID` (24 entradas, 9 delas contadas pelo tokenizador)** não se traduz:
  é chave de lógica, e a 5.0 já a tornou dispensável para o ícone. Na Task 4 ela é usada
  ao contrário — como **fonte dos ids** das skills do `_CSD`.
- **O placar atribui cada texto à declaração anterior mais próxima**, então dado declarado
  logo abaixo de uma função conta para ela (`_CSD` aparece sob `calcularVidaMaxima`). Serve
  como termômetro relativo — o total cai —, não como recorte fino. Por isso este lote foi
  escopado pelas estruturas, medidas com o tokenizador.
