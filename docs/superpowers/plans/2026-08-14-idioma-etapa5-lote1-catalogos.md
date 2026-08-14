# Etapa 5 — Lote 1: os catálogos estáticos do cliente — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Traduzir os **104 literais que vivem em estruturas de dados** do `game.js` — o primeiro lote da etapa 5, e o de forma mais uniforme.

**Arquitetura:** Estes literais não estão espalhados em templates: moram em objetos de topo (`_CSD`, `GRIMORIO_CLIENT`, `_TIPO_ITEM_LABEL`…), chaveados por id. Três deles já passam por `I18N.aplicarCatalogo` desde a etapa 3 — o que falta ali é a **descrição**, que a etapa 3 deixou de fora de propósito. Os demais ganham chaves novas e entram no mesmo mecanismo. Nenhum template string é tocado neste lote.

**Stack:** JavaScript vanilla (`game.js`, `src/i18n.js`, `src/lang/*.js`), testes `node`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `game.js` e `server.py` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A`. Combine a pausa do `game.js` antes de começar.
- **A etapa 5.0 (fundação) já fechou:** o observador do `document.body` aplica `_i18nApply` em markup inserido depois, e o ícone de habilidade é achado por `data-ability-id`.
- **`I18N.aplicarCatalogo(obj, soNome)`** reescreve `name`/`nome` (e `desc`/`descricao` quando `soNome` é falso) percorrendo o objeto e casando `cat.<família>.<id>`. **Não tem saída antecipada em português**: é isso que faz a volta ao `pt` restaurar o texto original.
- **Hoje o `game.js` chama** `aplicarCatalogo(GRIMORIO_CLIENT, true)`, `aplicarCatalogo(ARMADILHAS_LUCCAS, true)` e `aplicarCatalogo(GS.CATALOGO_ITENS, true)` — os três com `soNome = true`. A etapa 3 documentou o porquê: a **descrição** desses catálogos é conteúdo próprio do cliente, mais rico que a do servidor (a das magias é um card HTML com alcance e efeito por rodada, contra uma frase curta no servidor), e trocá-la apagaria informação.
- **O dicionário é JSON estrito** dentro do objeto: sem comentário DENTRO das chaves.
- Suítes verdes: `test_interface` (6), `test_idioma` (36), `test_vocabulario` (38), `test_erros` (9), `test_narracao` (67), `test_idioma_cliente` (24), `test_vocabulario_cliente` (45).

### Fatos medidos (não precisa re-verificar)

| estrutura | literais | situação |
|---|---:|---|
| `GRIMORIO_CLIENT` | 35 | nome já traduzido (etapa 3); falta a **descrição** |
| `_CSD` | 26 | nada — nomes de herói, `desc` e lista de `skills` |
| `ABILITY_NAME_TO_ID` | 9 | **não traduzir** — é chave de lógica |
| `_TIPO_ITEM_LABEL` | 5 | rótulo de tipo de item |
| `_OBJ_LABELS` | 4 | rótulo de objetivo |
| `ARMADILHAS_LUCCAS` | 4 | nome já traduzido; falta a **descrição** |
| `_ELEMENTAL_HABILIDADES_LEWIS` | 4 | — |
| `_EQUIPADO_SLOTS` | 4 | rótulo de slot |
| `HERO_DATA` | 4 | `class:` em maiúsculas (GUERREIRO ANÃO…) |
| `PURIFICACAO_TIPOS_LEWIS` | 3 | — |
| `_MP_CUSTO_LBL` | 2 | — |
| `_CTY_BLDGS` | 1 | — |

**Total do lote: 104, dos quais 9 não se traduzem** (o `ABILITY_NAME_TO_ID`) → **95 a traduzir**.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/lang/interface.js` | **Criar.** Chaves `ui.*` deste lote, escritas à mão |
| `index.html` | Carrega `src/lang/interface.js` |
| `game.js` | `_CSD` e os rótulos ganham id + entram no `aplicarCatalogo`; a descrição dos 3 catálogos passa a ser traduzida |
| `tools/test_interface.py` | As funções deste lote entram em `FECHADAS` |
| `tools/test_vocabulario_cliente.js` | Testes das estruturas novas |

---

## Task 1: O arquivo de chaves da interface

**Arquivos:**
- Criar: `src/lang/interface.js`
- Modificar: `index.html`, `tools/test_idioma_cliente.js`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar em `tools/test_idioma_cliente.js`, antes do bloco de resultado:

```js
console.log("");
console.log("[I] O dicionario da interface existe e foi carregado");
check("src/lang/interface.js existe",
      fs.existsSync(path.join(raiz, "src", "lang", "interface.js")));
const idx = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
check("o index.html carrega o interface.js",
      /src\/lang\/interface\.js/.test(idx));
check("as chaves da interface entraram no dicionario",
      Object.keys(DICT).some(k => k.startsWith("ui.")));
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_idioma_cliente.js
```

Esperado: `25 passaram, 2 falharam` — a terceira já passa (as 38 chaves `ui.*` da etapa 1
vivem no `strings.js`).

- [ ] **Passo 3: Criar o arquivo**

Criar `src/lang/interface.js`:

```js
// INTERFACE do cliente (etapa 5) — rótulos, tooltips e mensagens de tela.
//
// Separado do strings.js porque este cresce muito (a etapa 5 traz ~636 chaves) e
// misturá-lo com as chaves de motor e das telas de conexão tornaria os dois
// difíceis de revisar. Mantido À MÃO, como o erros.js e o narracao.js.
//
// REGRAS (as mesmas do strings.js): é JSON estrito dentro das chaves — aspas
// duplas, sem vírgula sobrando, SEM COMENTÁRIO dentro do objeto. Fora dele,
// comentários são livres: o servidor ancora o recorte na LINHA
// "window.LANG_INTERFACE =".
//
// Convenção: ui.<área>.<slug>, onde <área> é a TELA em que o texto aparece.
window.LANG_INTERFACE = {};
Object.assign(window.LANG_STRINGS, window.LANG_INTERFACE);
```

- [ ] **Passo 4: Carregar no `index.html`**

Na linha do `document.write` dos scripts síncronos, acrescentar **depois** do `strings.js`
(o arquivo termina com `Object.assign(window.LANG_STRINGS, …)` e precisa que esse objeto
já exista):

```js
document.write('<script src="src/lang/interface.js?v='+v+'"><\/script>');
```

- [ ] **Passo 5: Rodar**

```bash
node --check src/lang/interface.js && node tools/test_idioma_cliente.js && python -c "import server; print('IMPORT OK — o _load_lang funde o arquivo novo sozinho')"
```

Esperado: `27 passaram, 0 falharam` e `IMPORT OK`. O `_load_lang()` do servidor funde
**todos** os `.js` de `src/lang/`, então o arquivo novo entra sem registro em lugar nenhum.

- [ ] **Passo 6: Commit**

```bash
git status --short
git add src/lang/interface.js index.html tools/test_idioma_cliente.js
git commit -m "feat(i18n): dicionario da interface do cliente"
```

---

## Task 2: A descrição dos três catálogos que a etapa 3 deixou

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

A etapa 3 chama `aplicarCatalogo(X, true)` nos três — `soNome = true`, ou seja, **só o
nome**. A descrição ficou de fora porque é conteúdo do cliente, mais rico que a do
servidor. Agora ela ganha chave própria em vez de herdar a do servidor.

- [ ] **Passo 1: Listar o que falta**

```bash
python -c "
import io, re, sys; sys.stdout.reconfigure(encoding='utf-8')
s = io.open('game.js', encoding='utf-8').read()
for nome in ('GRIMORIO_CLIENT', 'ARMADILHAS_LUCCAS'):
    i = s.index('const ' + nome)
    prof, k = 0, i
    while k < len(s):
        prof += (s[k] == '{') - (s[k] == '}')
        if k > i and prof <= 0: break
        k += 1
    bloco = s[i:k+1]
    ids = re.findall(r'^\s*(\w+)\s*:\s*\{', bloco, re.M)
    print(nome, '->', len(ids), 'entradas:', ids[:8])
"
```

- [ ] **Passo 2: Escrever o teste que falha**

Acrescentar em `tools/test_vocabulario_cliente.js`, antes do bloco de resultado:

```js
console.log("");
console.log("[D] A descricao dos catalogos do cliente tambem traduz");
DICT["ui.magia.bola_fogo.desc"] = { pt: "<b>Card em portugues</b>", en: "<b>English card</b>" };
const cat = { bola_fogo: { id: "bola_fogo", nome: "Bola de Fogo",
                           descricao: "<b>Card em portugues</b>" } };
I18N.setLang("en");
I18N.aplicarCatalogo(cat, false);
check("a descricao do catalogo do cliente vira a chave ui.*",
      cat.bola_fogo.descricao === "<b>English card</b>");
I18N.setLang("pt");
I18N.aplicarCatalogo(cat, false);
check("voltar ao portugues restaura a descricao",
      cat.bola_fogo.descricao === "<b>Card em portugues</b>");
```

- [ ] **Passo 3: Rodar e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: as duas novas falham — o `aplicarCatalogo` procura `cat.magia.bola_fogo.desc`
(a do servidor), não `ui.magia.bola_fogo.desc`.

- [ ] **Passo 4: Ensinar o `aplicarCatalogo` a preferir a chave da interface**

Em `src/i18n.js`, dentro de `aplicarCatalogo`, no bloco que troca a descrição:

```js
      // A descrição do CLIENTE tem prioridade sobre a do servidor: os catálogos
      // do cliente guardam um card HTML com alcance e efeito por rodada, contra
      // uma frase curta no servidor. A etapa 3 evitou o problema passando
      // soNome=true; agora a chave própria (ui.*) resolve sem perder informação.
      const baseUi = base && base.replace(/^cat\./, 'ui.');
      const chaveDesc = (baseUi && tem(baseUi + '.desc')) ? baseUi + '.desc'
                      : (base && tem(base + '.desc')) ? base + '.desc' : null;
      if (chaveDesc && !soNome) {
        for (const campo of CAMPOS_DESC) {
          if (typeof o[campo] === 'string') { o[campo] = t(chaveDesc); break; }
        }
      }
```

substituindo o `if (base && !soNome && tem(base + '.desc')) { … }` que existe hoje.

- [ ] **Passo 5: Trocar as três chamadas para `soNome = false`**

Em `game.js`, onde hoje se lê:

```js
  if (typeof GRIMORIO_CLIENT   !== 'undefined') I18N.aplicarCatalogo(GRIMORIO_CLIENT, true);
  if (typeof ARMADILHAS_LUCCAS !== 'undefined') I18N.aplicarCatalogo(ARMADILHAS_LUCCAS, true);
  if (GS.CATALOGO_ITENS)                        I18N.aplicarCatalogo(GS.CATALOGO_ITENS, true);
```

passa a:

```js
  // soNome=false agora que a descrição tem chave PRÓPRIA (ui.*), com prioridade
  // sobre a do servidor — ver aplicarCatalogo. Sem a chave ui.*, o texto do
  // cliente fica intacto, então a troca é segura mesmo antes de traduzir tudo.
  if (typeof GRIMORIO_CLIENT   !== 'undefined') I18N.aplicarCatalogo(GRIMORIO_CLIENT, false);
  if (typeof ARMADILHAS_LUCCAS !== 'undefined') I18N.aplicarCatalogo(ARMADILHAS_LUCCAS, false);
  if (GS.CATALOGO_ITENS)                        I18N.aplicarCatalogo(GS.CATALOGO_ITENS, false);
```

**Atenção — isto é o ponto de risco do lote.** Com `soNome = false` e SEM a chave `ui.*`,
o `aplicarCatalogo` cairia na descrição do SERVIDOR e apagaria o card rico do cliente. A
mudança do Passo 4 impede isso: sem `ui.*`, `chaveDesc` só aponta para `cat.*` se ela
existir — e é justamente por existir que a etapa 3 usou `soNome=true`. **Portanto a ordem
importa: traduza as descrições (Passo 6) ANTES de rodar o jogo**, ou verifique no navegador
que o card não encolheu.

- [ ] **Passo 6: Traduzir as descrições**

Extraia os textos com o script do Passo 1 e escreva as chaves `ui.magia.<id>.desc` e
`ui.armadilha.<id>.desc` no `src/lang/interface.js`, com o `pt` **idêntico** ao texto que
está hoje no `game.js` (é o fallback) e o `en` traduzido. Mantenha as tags HTML intactas.

- [ ] **Passo 7: Rodar**

```bash
node --check src/i18n.js && node --check game.js && node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js
```

Esperado: `47 passaram, 0 falharam` e `27 passaram, 0 falharam`.

- [ ] **Passo 8: Verificar no navegador que o card não encolheu**

Confirme com o usuário antes de subir servidor. Com o jogo aberto, abra o tooltip de uma
magia em **português** e em **inglês** e confira que os dois têm o card completo (alcance,
efeito por rodada) — não a frase curta do servidor.

**Recarregue com cache-buster** (`?v=algo`) e cheque no console que a versão nova está
carregada antes de concluir: o navegador serve o `game.js` do cache, e a etapa 5.0
registrou isso como armadilha.

- [ ] **Passo 9: Commit**

```bash
git status --short
git add src/i18n.js game.js src/lang/interface.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): descricao dos catalogos do cliente ganha chave propria"
```

---

## Task 3: O `_CSD` — a tela de seleção de herói

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`, `tools/test_vocabulario_cliente.js`

O `_CSD` guarda, por classe: `name` (VICTOR COICE BRAVO), `desc` (a frase dramática) e
`skills[]` com `name`/`nome`, `desc`. São 26 literais, e é a tela que o jogador vê primeiro.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar em `tools/test_vocabulario_cliente.js`:

```js
console.log("");
console.log("[C] O _CSD (selecao de heroi) traduz nome, desc e skills");
DICT["ui.classe.warrior.nome"] = { pt: "VICTOR COICE BRAVO", en: "VICTOR THE BOLD KICK" };
DICT["ui.classe.warrior.desc"] = { pt: "Tanque de aco.", en: "A tank of steel." };
DICT["ui.skill.mira_certeira.nome"] = { pt: "Mira Certeira", en: "Sure Aim" };
const csd = { warrior: { id: "warrior", name: "VICTOR COICE BRAVO",
                         desc: "Tanque de aco.",
                         skills: [{ id: "mira_certeira", name: "Mira Certeira" }] } };
I18N.setLang("en");
I18N.aplicarCatalogo(csd, false);
check("nome da classe traduzido", csd.warrior.name === "VICTOR THE BOLD KICK");
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

Esperado: as quatro novas falham — falta a família `classe`/`skill` com prefixo `ui.` e
faltam os `id` no `_CSD`.

- [ ] **Passo 3: Dar `id` a cada entrada do `_CSD`**

No `game.js`, cada classe do `_CSD` ganha `id` igual à sua chave, e cada skill ganha o
`id` que já existe em `ABILITY_NAME_TO_ID`:

```js
  warrior:{ id:'warrior', name:'VICTOR COICE BRAVO', cls:'VICTOR', … 
    skills:[
      {id:'mira_certeira', icon:'⚔️', name:'Mira Certeira', …},
```

O `id` da skill é **o mesmo** que o `data-ability-id` da etapa 5.0 usa — é o que liga o
ícone ao texto.

- [ ] **Passo 4: Registrar as famílias `ui.` no filtro**

Em `src/i18n.js`, o `_chaveBase` monta `cat.<família>.<id>`. Para o prefixo `ui.`, a
resolução da descrição já foi ensinada no Passo 4 da Task 2; para o **nome**, acrescente a
mesma preferência:

```js
      const baseUi = base && base.replace(/^cat\./, 'ui.');
      const chaveNome = (baseUi && tem(baseUi + '.nome')) ? baseUi + '.nome'
                      : (base && tem(base + '.nome')) ? base + '.nome' : null;
```

e use `chaveNome` no lugar de `base + '.nome'` no bloco que troca o nome.

- [ ] **Passo 5: Chamar o `aplicarCatalogo` no `_CSD`**

Junto das outras três chamadas em `game.js`:

```js
  if (typeof _CSD !== 'undefined') I18N.aplicarCatalogo(_CSD, false);
```

- [ ] **Passo 6: Traduzir os 26**

Escreva as chaves `ui.classe.<id>.nome`, `ui.classe.<id>.desc` e `ui.skill.<id>.nome` /
`.desc` no `src/lang/interface.js`, com o `pt` idêntico ao texto de hoje.

- [ ] **Passo 7: Rodar e verificar na tela**

```bash
node --check src/i18n.js && node --check game.js && node tools/test_vocabulario_cliente.js && python tools/test_interface.py
```

Depois, no navegador (com cache-buster): abra a seleção de herói em inglês e confira nome,
descrição e as três habilidades de cada classe — **e que os ícones continuam lá**, que é o
que a etapa 5.0 preparou.

- [ ] **Passo 8: Commit**

```bash
git status --short
git add game.js src/i18n.js src/lang/interface.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): tela de selecao de heroi traduzida"
```

---

## Task 4: Os rótulos pequenos

**Arquivos:**
- Modificar: `game.js`, `src/lang/interface.js`

Sobram 8 estruturas pequenas, somando 27 literais: `_TIPO_ITEM_LABEL` (5), `_OBJ_LABELS`
(4), `_ELEMENTAL_HABILIDADES_LEWIS` (4), `_EQUIPADO_SLOTS` (4), `HERO_DATA` (4),
`PURIFICACAO_TIPOS_LEWIS` (3), `_MP_CUSTO_LBL` (2), `_CTY_BLDGS` (1).

- [ ] **Passo 1: Ver a forma de cada uma**

```bash
python -c "
import io, re, sys; sys.stdout.reconfigure(encoding='utf-8')
s = io.open('game.js', encoding='utf-8').read()
for nome in ('_TIPO_ITEM_LABEL','_OBJ_LABELS','_ELEMENTAL_HABILIDADES_LEWIS',
             '_EQUIPADO_SLOTS','PURIFICACAO_TIPOS_LEWIS','_MP_CUSTO_LBL','_CTY_BLDGS'):
    i = s.find(nome + ' =')
    if i < 0: print(nome, 'NAO ACHADO'); continue
    print('---', nome); print(s[i:i+320]); print()
"
```

São mapas `id → rótulo`. Cada um vira `ui.<área>.<id>` e passa por `aplicarCatalogo` **se
tiver a forma de objeto com id**; os que forem `{id: 'string'}` (valor string, não objeto)
não passam pelo filtro e precisam de `t()` no ponto de uso.

- [ ] **Passo 2: Migrar um a um, rodando o placar entre cada**

```bash
python tools/test_interface.py
```

O total tem de cair a cada estrutura migrada. Se não cair, a estrutura não estava sendo
contada onde você pensou — **pare e meça antes de seguir**.

- [ ] **Passo 3: Commit**

```bash
git status --short
git add game.js src/lang/interface.js
git commit -m "feat(i18n): rotulos de tipo, objetivo, slot e purificacao"
```

---

## Task 5: Fechamento do lote

**Arquivos:**
- Modificar: `tools/test_interface.py`, `CLAUDE.md`

- [ ] **Passo 1: Marcar as funções fechadas**

No `tools/test_interface.py`, acrescentar ao conjunto `FECHADAS` os nomes que o placar
atribui a estas estruturas. **Rode o placar antes** para pegar os nomes exatos — a
atribuição é pela declaração anterior mais próxima, então o `_CSD` aparece sob
`calcularVidaMaxima`, e não sob `_CSD`:

```bash
python tools/test_interface.py
```

- [ ] **Passo 2: Rodar tudo**

```bash
python tools/test_interface.py && python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: todas verdes, e o placar com ~104 literais a menos que os 636 iniciais.

- [ ] **Passo 3: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

Esperado: `336`, `54` e `462`, zero falhando.

- [ ] **Passo 4: Documentar no `CLAUDE.md`**

Acrescentar um bloco `>` cobrindo: o `src/lang/interface.js` e por que é separado do
`strings.js`; a **prioridade `ui.*` sobre `cat.*`** na descrição (e por que a etapa 3 tinha
usado `soNome=true`); o `_CSD` com `id` por entrada, ligado ao `data-ability-id` da 5.0; e
o número novo do placar.

- [ ] **Passo 5: Commit**

```bash
git add tools/test_interface.py CLAUDE.md
git commit -m "docs(i18n): catalogos estaticos do cliente traduzidos"
```

---

## Fora deste lote (registrado, não esquecido)

- **532 literais em código de interface**, espalhados por ~170 funções — os lotes 2 e 3.
- **`ABILITY_NAME_TO_ID` (9)** não se traduz: é chave de lógica, e a 5.0 já a tornou
  dispensável para o ícone.
- A **imprecisão do placar**: ele atribui cada literal à declaração anterior mais próxima,
  então dado declarado logo abaixo de uma função conta para ela. Serve como termômetro
  relativo (o total cai), não como recorte fino — por isso este lote foi escopado pelas
  estruturas, que são enumeráveis com exatidão.
