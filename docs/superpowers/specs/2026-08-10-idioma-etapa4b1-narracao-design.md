# Etapa 4b-i do idioma — Narração do servidor (lote mecânico) — Design

**Data:** 2026-08-10
**Depende de:** etapas 1 (motor PT/EN), 2 (vocabulário), 3 (alcance + descrições) e 4a
(erros do servidor), todas implementadas e verificadas.

---

## Onde isto se encaixa

1. Motor PT/EN ✅
2. Vocabulário — 397 nomes ✅
3. Alcance dos nomes + 189 descrições ✅
4. a) Erros — 471 mensagens ✅ · **b-i) Narração, lote mecânico (416)** ← este ·
   b-ii) Narração, lote difícil (128)
5. Interface do cliente (~1.000)

A narração tem 544 pontos de chamada, e a medição mostrou que eles não são homogêneos —
há três níveis de dificuldade, com mecanismos de migração diferentes. Este sub-projeto
pega só o nível mecânico, que é o mesmo caso já resolvido na etapa 4a.

## A superfície, medida

| Forma | Sites | Neste escopo? |
|---|---:|---|
| `gm_say(f"…")` numa linha | 399 | **sim** |
| `gm_say("…")` literal | 17 | **sim** |
| `gm_say(` com o texto na linha seguinte (multilinha) | 109 | não — 4b-ii |
| `gm_say(prefix + f"…")` | 3 | não — 4b-ii |
| `gm_say(variavel)` | 7 | não — 4b-ii |
| `gm_say(gm("chave"))` — pool de variantes | 6 sites / 30 frases | não — 4b-ii |
| já migrados na etapa 1 | 2 | — |

**Por que os multilinha ficam de fora:** são frases montadas por concatenação implícita de
fragmentos, e são justamente as narrações mais longas e com mais parâmetros — as linhas de
combate. Um script que tentasse remontá-las erraria em silêncio; e um erro numa linha de
combate custa mais que num literal, porque ela aparece dezenas de vezes por partida.

**O pool `gm(...)`** é um subsistema próprio: `GM` é um dicionário de 10 chaves com 3
variantes cada, e `gm(key)` sorteia uma. Traduzir isso não é migrar um site — é migrar um
catálogo, e cabe junto com os outros casos difíceis.

## As interpolações, medidas

764 interpolações nas 399 f-strings, em 207 expressões distintas. **300 delas são um
identificador simples** (`dano`, `dur`, `nome`). As mais frequentes:

| Expressão | Ocorrências |
|---|---:|
| `p['name']` | 144 |
| `m['name']` | 87 |
| `alvo['name']` | 41 |
| `caster['name']` | 17 |
| `item['name']` | 14 |
| `target['name']` | 12 |

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Escopo | Só o lote mecânico: 17 literais + 399 f-strings de uma linha |
| Nome do parâmetro | Regra determinística de três degraus, com tabela mínima de apelidos |
| Nome da chave | Slug do texto **sem** as interpolações |
| Onde mora o dicionário | Arquivo novo `src/lang/narracao.js`, mantido à mão |

---

## Arquitetura

### Batismo determinístico dos parâmetros

Três degraus, aplicados em ordem:

1. **Identificador simples** → ele mesmo. `{dano}` → `dano=dano`. Cobre 300 das 764.
2. **`X['name']` ou `X["name"]`** → `X`. `{alvo['name']}` → `alvo=alvo['name']`.
3. **Qualquer outra coisa** → slug da expressão, truncado. `{alvo.get('name', alvo.get('nome'))}`
   → `alvo_get_name_alvo_get_nome`.

Depois disso, uma **tabela mínima de apelidos**, só para os dois nomes opacos e mais
frequentes: `p` → `heroi`, `m` → `monstro`. Sozinhos são 231 das 764 interpolações (30%), e
`{heroi} ataca {alvo}` é legível para quem traduz, enquanto `{p} ataca {alvo}` não é.

Colisão de nome dentro da mesma frase (duas expressões que mapeiam para o mesmo parâmetro)
ganha sufixo numérico e é **relatada** — nunca resolvida em silêncio.

**Isto difere da etapa 4a de propósito.** Lá as 81 mensagens foram batizadas à mão, pelo
**papel** na frase (`{requisito}`). Aqui são 399 sites automáticos: determinismo vale mais
que elegância, e o resultado continua legível. Os dois dicionários vão conviver com estilos
de nome ligeiramente diferentes, e isso é aceitável — o que não pode variar é o `{nome}`
entre o `pt` e o `en` da mesma chave, e disso o teste de paridade cuida.

### Chaves

`narracao.<slug>`, onde o slug vem do texto em português **com as interpolações removidas**:

```
f"🚪 **{p['name']}** abre uma porta!"   → narracao.abre_uma_porta
"Os aventureiros partem da cidade."     → narracao.os_aventureiros_partem_da_cidade
```

Remover as interpolações antes de gerar o slug é o que torna a chave legível; incluí-las
produziria `narracao.p_name_abre_uma_porta`. A dedup por construção continua valendo: duas
frases idênticas compartilham a chave.

### Onde o dicionário mora

Arquivo novo `src/lang/narracao.js`, declarando `window.LANG_NARRACAO` e fundindo em
`window.LANG_STRINGS`, no mesmo formato dos três que já existem. O carregador do servidor
funde todos os `.js` de `src/lang/`, e o `index.html` ganha uma tag `<script>`.

Como no `erros.js` e ao contrário do `catalogo.js`, **não fica um gerador rodando**: depois
da migração o `server.py` não tem mais o texto, só a chave. O script é de uso único.

## Testes

`tools/test_narracao.py`:

1. **Nenhum `gm_say` de uma linha com literal sobrou** — nem `f"…"` nem `"…"`. É a prova de
   migração completa do escopo.
2. **Os sites fora de escopo são contados e relatados, não cobrados.** O teste imprime
   quantos multilinha, concatenações, variáveis e sites de pool restam. Isso evita a suíte
   ficar vermelha por trabalho que ainda não foi combinado, e deixa o placar da etapa 4b-ii
   visível.
3. **Toda chave `T("narracao.…")` usada no `server.py` existe no dicionário.**
4. **Chave do `narracao.js` sem uso é relatada** (não falha).
5. **A mesma narração chega em dois idiomas** pelo `broadcast` real, com dois jogadores em
   idiomas diferentes — o teste ponta a ponta que as etapas anteriores usaram.

A paridade de `{parâmetros}` entre `pt` e `en` já é global (criada na etapa 4a) e passa a
cobrir também estas chaves, sem mudança.

## Fora de escopo

- Os 128 sites difíceis (multilinha, concatenação, variável, pool) — etapa 4b-ii.
- A interface do cliente — etapa 5.
- Rever o **conteúdo** da narração. Se uma frase é confusa em português, continua confusa.

## Tradução

Até 416 chaves, provavelmente menos porque a narração também se repete. O número exato sai
do script; **não o crave em teste** (a lição da etapa 3).

O registro é diferente do dos erros. Narração é a **voz do mestre** contando o que acontece
— presente, direta, com energia:

- "**{heroi}** strikes **{alvo}** for **{dano}** damage!" — não "A hit has been performed."
- Mantém a pontuação de entusiasmo do original: se o português termina em `!`, o inglês também.

**Emojis e `**negrito**` passam intactos** — abrem quase toda narração e são formatação.
**Números, dados e valores entre `**` são sagrados.** Nomes de habilidade e item seguem o
`"en"` das chaves `cat.*.nome`; o glossário das etapas 2 a 4a continua valendo.
