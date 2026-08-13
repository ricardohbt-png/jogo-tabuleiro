# Etapa 4b-ii do idioma — Narração do servidor, o que sobrou — Design

**Data:** 2026-08-13
**Depende de:** etapas 1 (motor PT/EN), 2 (vocabulário), 3 (descrições), 4a (erros),
4b-i (narração mecânica) e 4c (nomes dentro da frase) — todas implementadas e verificadas.

---

## Onde isto se encaixa

1. Motor PT/EN ✅
2. Vocabulário — 397 nomes ✅
3. Alcance dos nomes + 189 descrições ✅
4. a) Erros — 471 ✅ · b-i) Narração mecânica — 390 ✅ · c) Nomes dentro da frase — 288 ✅ ·
   **b-ii) Narração, o que sobrou ← este**
5. Interface do cliente (~1.000)

Com esta etapa **não sobra narração em português no servidor**. O que restar do idioma é
só a interface do cliente.

## A superfície, medida

| forma | sites | por que sobrou da 4b-i |
|---|---:|---|
| multilinha (texto na linha seguinte) | 110 | f-string montada por concatenação implícita entre linhas |
| f-string que atravessa a linha | 1 | idem |
| concatenação `prefix + f"…"` | 3 | o texto não começa na chamada |
| `gm_say(gm(key))` — pool | 6 chamadas / **30 frases** | subsistema próprio: `random.choice` |
| `gm_say(variavel)` | 6 | a string vem montada de outro lugar |

Os 6 por variável não são um grupo homogêneo — são **cinco formas distintas**:

| site | forma |
|---|---|
| `gm_say(text)` (fim de jogo) | é o pool (`gm("victory")`) — resolvido pela seção B |
| `gm_say(log)` (equipar) | produtor `_equip_into_slot`/`_equip_into_pair` devolve a frase |
| `gm_say(msg)` (canção) | produtor `_interromper_cancao` devolve a frase **e recebe o motivo em português** |
| `gm_say(motivo)` (fim de turno forçado) | parâmetro repassado pelos chamadores |
| `gm_say(msg)` e `gm_say(partes_txt)` | frase **montada por pedaços** com `join` |

## Design

### A. Migrador por `ast`, não por regex

O módulo `ast` parseia o `server.py` e localiza cada `gm_say(<arg>)`. Para f-string
(`JoinedStr`) e concatenação (`BinOp`), ele entrega a estrutura pronta: alternância de
`Constant` (texto) e `FormattedValue` (interpolação), com **posição exata no fonte**. O
texto lógico é a concatenação dos `Constant`; a expressão de cada parâmetro vem de
`ast.get_source_segment`, verbatim.

Isso cobre **110 multilinha + 1 que atravessa + 3 concatenações** com a mesma máquina,
porque para o `ast` os três são a mesma árvore.

**Por que não regex:** o spec da 4b-i já havia rejeitado regex para multilinha, e a Task 5
da 4c confirmou na prática — um `[^)]*` para o default de um `.get` aninhado deixou o
arquivo sem parsear. Fragmento de f-string quebrado entre linhas, com prefixos misturados
e aspas aninhadas, é exatamente onde regex bate no teto.

**Batismo dos parâmetros:** o mesmo de três degraus do `migrar_narracao.py` (identificador
simples vira ele mesmo, `X['name']` vira `X`, o resto vira slug da expressão), com a mesma
tabela de apelidos. Isso mantém os nomes coerentes com as 380 chaves já existentes.

**A reescrita é por posição, de trás para frente** no arquivo, para os offsets não
invalidarem, e toca só o span da chamada — todo o resto fica byte-idêntico.

**Três travas**, as mesmas que salvaram a Task 5 da 4c:
1. expressão que o `ast` não classifique como f-string/concatenação simples é **pulada e
   relatada**, nunca adivinhada;
2. o resultado passa por `ast.parse` **antes** de ir ao disco;
3. conferidor de diff estrutural, linha a linha.

**Fora do escopo deste migrador:** trocar nome de catálogo cru pelos helpers da 4c. Os
sites multilinha passam `m['name']` cru hoje, e depois de migrados entram na mesma
superfície que o `migrar_nomes_narracao.py` da 4c já sabe varrer — então é **um passo
próprio, rodando aquele script de novo**, e não uma responsabilidade deste.

### B. O pool `gm(key)`

`gm(key)` é `random.choice(GM[key])`. O sorteio tem de acontecer **uma vez** e o idioma
ser resolvido depois — senão dois jogadores na mesma sala leriam variantes diferentes do
mesmo evento:

```python
def gm(key):
    return T(f"narracao.gm.{key}.{random.randrange(len(GM[key]))}")
```

Uma chave por variante (`narracao.gm.intro.0/1/2`). O dicionário `GM` **continua existindo**
no `server.py` e vira a fonte do português.

**Onde as chaves moram:** em `src/lang/narracao.js`, junto das outras 410 de narração, e
**mantidas à mão** como todas de lá. O `gerar_vocabulario.py` **não** entra nisto: ele só
emite o prefixo `cat.*` a partir dos catálogos de item/monstro/magia, e ensiná-lo a emitir
`narracao.*` misturaria dois arquivos com regras opostas (um gerado, outro escrito à mão).
O script de migração semeia as 30 chaves uma vez, com o `pt` vindo do `GM`.

`gm()` passa a devolver `T` em vez de `str`. É chamado em 6 lugares, todos `gm_say(...)`,
que já sabem serializar `T`.

### C. O motor aprende a juntar listas

Um parâmetro pode ser uma **lista**, e o `t()` a junta com separadores do próprio idioma.
No servidor, dentro do `_param_texto` (que já resolve `T` aninhado desde a etapa 2):

```python
if isinstance(valor, (list, tuple)):
    itens = [_param_texto(v, lang) for v in valor]      # elemento pode ser T
    if not itens:        return ""
    if len(itens) == 1:  return itens[0]
    return (t("lista.separador", lang).join(itens[:-1])
            + t("lista.ultimo", lang) + itens[-1])
```

Duas chaves novas: `lista.separador` (`", "` nos dois idiomas) e `lista.ultimo`
(`" e "` / `" and "`). Resultado: `"A"`, `"A e B"`, `"A, B e C"` — natural nos dois. O
`t()` do cliente ganha o mesmo tratamento, onde hoje faz `String(params[k])`.

**Onde moram:** em `src/lang/strings.js`, o arquivo escrito à mão da etapa 1. São chaves do
**motor**, não de conteúdo — não pertencem ao `narracao.js` (frases do mestre) nem ao
`composto.js` (peças de nome), e o prefixo `lista.` deixa isso explícito.

**Ganho fora do escopo declarado, deliberado:** isto fecha a limitação do
`nomes = " e ".join(...)` que a 4c registrou no `CLAUDE.md`. Aplicar lá é uma linha, e a
limitação existia só por falta deste mecanismo.

### D. Os produtores e o parâmetro

| site | vira |
|---|---|
| `_equip_into_slot` / `_equip_into_pair` | devolvem `T` |
| `_interromper_cancao(p, motivo)` | devolve `T`; o motivo vira `T` passado pelo chamador |
| `_forcar_fim_de_turno(pid, motivo)` | os **chamadores** passam `T` |

O `if log:` dos chamadores continua funcionando sem mudança: o `T` tem `__len__`, então
frase não-vazia é *truthy*, e `None`/`""` seguem falsos. É a mesma propriedade que mantém
24 mocks de teste de pé desde a etapa 4a.

### E. As 30 frases do pool

Não são mecânicas — são a voz autoral do mestre, prosa de ambientação. Vão traduzidas
mantendo tom e ritmo do português, **num commit próprio** para o autor revisar de uma vez.
Se alguma não soar certa, é uma linha no dicionário.

## O que continua em português depois desta etapa

- Conteúdo autoral: masmorras, campanhas, falas de NPC, itens e monstros do editor.
- As 7 passagens de nome que a 4c registrou (nome de ataque em tupla literal, rótulo de
  status, nome de habilidade por parâmetro, `weapon_name`, nome de cidade) — exceto o
  `nomes`, que a seção C resolve.
- A interface do cliente (etapa 5).

## Modos de falha

| situação | comportamento |
|---|---|
| `ast` não reconhece a forma do argumento | site pulado e relatado; segue em português |
| resultado não parseia | nada é escrito |
| chave sem `en` | cai no `pt` — regra do motor desde a etapa 1 |
| lista vazia como parâmetro | string vazia, sem separador solto |
| `gm(key)` com chave inexistente | `KeyError`, como hoje — não é regressão |

## Como se prova

`tools/test_narracao.py` ganha:

- uma frase **multilinha migrada** chegando nos dois idiomas pelo broadcast real;
- o pool: `gm(key)` devolve `T`, e **dois jogadores em idiomas diferentes leem a mesma
  variante** — a regressão que mais importa, porque um sorteio por idioma seria invisível
  num teste de uma conexão só;
- **junção de listas** com 1, 2 e 3 itens, nos dois idiomas;
- os **produtores** devolvendo `T`, e o `if log:` continuando *truthy*.

A varredura estática da seção `[2]` passa a **cobrar** o que hoje só relata: zero
`gm_say(` com texto na linha seguinte, zero `gm_say(gm(`, zero concatenação. O relatório
vira teste.

O teste de paridade de `{parâmetros}` entre `pt` e `en` (`test_erros.py`) pega as chaves
novas de graça. No cliente, `test_vocabulario_cliente.js` ganha a junção de listas.

Regressão obrigatória: as 11 suítes de sempre, mais `test_idioma` e `test_vocabulario` —
o `gm()` mudou de tipo de retorno.

Prova ponta a ponta com dois clientes em idiomas diferentes na mesma sala, **com o
servidor reiniciado** (armadilha registrada na 4b-i: um servidor de antes da migração
mostra tudo em português e parece que nada funcionou).
