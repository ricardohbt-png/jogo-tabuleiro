# Etapa 3 do idioma — Alcance dos nomes + descrições de catálogo — Design

**Data:** 2026-08-10
**Depende de:** etapas 1 (motor PT/EN) e 2 (vocabulário — 397 nomes). Specs em
`docs/superpowers/specs/2026-08-10-idioma-i18n-design.md` e
`.../2026-08-10-idioma-etapa2-vocabulario-design.md`.

---

## Onde isto se encaixa

Terceiro dos cinco sub-projetos:

1. Motor PT/EN ✅
2. Vocabulário — 397 nomes ✅ *(com alcance menor que o anunciado — ver abaixo)*
3. **Alcance dos nomes + 189 descrições** ← este
4. Erros (470) e narração (544) do servidor
5. Interface do cliente (~1.000)

## O que a verificação revelou

A etapa 2 afirmou que os 397 nomes aparecem traduzidos. **Isso é falso para 53 deles.**
O teste de lá provou o filtro com um payload real, mas não a cobertura: há caminhos em que
o nome nunca passa pelo filtro. Duas causas distintas.

### Causa 1 — o id está na chave do dicionário pai

O filtro resolve a família lendo `o.id` ou `o.type`. Mas dois payloads são dicionários
**chaveados pelo id**, cujos valores não têm campo de id dentro:

| Payload | Forma | Afetados |
|---|---|---:|
| `lobby_state.classes` | `{ "warrior": {name, desc, color, emoji} }` | 6 |
| `game_start.instrumentos_base` | `{ "harpa": {nome, desc, stats, …} }` | 9 |

Verificado ao vivo contra o servidor: nenhum dos dois tem `id` interno.

### Causa 2 — cópias estáticas dentro do cliente

Três catálogos vivem no código do cliente, em português, e não vêm de payload nenhum:

| Catálogo | Onde | Conteúdo |
|---|---|---|
| `GRIMORIO_CLIENT` | `game.js:10487` | 27 magias: `nome`, `resumo`, `descricao` (HTML) |
| `ARMADILHAS_LUCCAS` | `game.js:9850` | 11 armadilhas: `nome`, `desc` |
| `CATALOGO_ITENS` | `src/gameState.js:519` | 72 itens: `nome`, `descricao` |

Os painéis de magia e de armadilha leem daí, então os nomes traduzidos na etapa 2 nunca
chegam a essas telas.

### Causa 3 — precedência invertida num ponto

Dos 72 itens de `CATALOGO_ITENS`, **28 ids coincidem** com os do servidor. Nos dois pontos
que consultam esse catálogo a precedência é oposta:

- `normalizarItemTooltip` (`game.js:4145`) — `nome: bruto.nome || bruto.name || catalogado.nome`.
  O servidor vence; o tooltip sai traduzido. **Correto.**
- `_converterBagParaInventario` (`game.js:4026`) — `inv[i] = cat ? { ...cat } : {…}`.
  O item do servidor é **descartado inteiro** e o nome volta ao português. **Vazamento.**

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Escopo | Fechar o alcance dos nomes **e** acrescentar as descrições |
| Nos catálogos estáticos do cliente | Traduzir **só o nome** |
| Descrições geradas | Todas as 189, mesmo as 40 que o cliente ainda não exibe |
| Itens só-do-cliente (44) | Fora de escopo |

**Por que só o nome nos catálogos estáticos:** as descrições que o cliente guarda são
**conteúdo próprio, já divergente** do servidor. As de armadilha dizem o mesmo com outra
redação ("1d4 dano" × "1d4 de dano"); as de magia são outra coisa inteira — um card HTML
com alcance, área e efeito por rodada, contra uma frase de 69 caracteres no servidor.
Substituir o HTML da magia pela tradução da frase curta destruiria informação. Esse texto
é interface, e vai na etapa 5.

**Por que gerar as 189 mesmo assim:** 40 delas (magia 27, armadilha 13) não são exibidas
pelo cliente hoje, mas são baratas (69 caracteres em média), deixam o placar de "falta
traduzir" chegar a zero, e a etapa 4 provavelmente vai querê-las na narração. Excluí-las
exigiria uma lista de exceções no gerador — complexidade sem ganho.

## Fora de escopo

- Os **44 itens que só existem em `CATALOGO_ITENS`** (sem par no servidor). Quem os
  renderiza é a loja-overlay antiga; etapa 5.
- `resumo` e `descricao` HTML das magias, e o `desc` próprio das armadilhas no cliente.
  Etapa 5.
- Unificar os catálogos duplicados. Eles já divergem em ids e em texto; reconciliá-los é
  projeto próprio, não efeito colateral da tradução.
- Ataques e habilidades aninhados nas fichas de monstro.

---

## Arquitetura

### Chaves de descrição

`cat.<família>.<id>.desc`, ao lado das `.nome`, no mesmo `src/lang/catalogo.js`, geradas
pelo mesmo `tools/gerar_vocabulario.py`. **Só sai chave para quem tem descrição.**

| Família | Descrições |
|---|---:|
| `guilda` | 127 |
| `magia` | 27 |
| `armadilha` | 13 |
| `instrumento` | 9 |
| `classe` | 6 |
| `item` | 7 |
| **Total** | **189** |

O arquivo passa de 397 para **586 chaves**. Idempotência, relato de órfãs e falha alta em
colisão continuam valendo sem mudança — são propriedades de `mesclar()` e `fundir_item()`,
que não sabem qual sufixo estão tratando.

### Três mudanças no filtro do cliente

**(a) `_chaveDeNome` vira `_chaveBase`.** Resolve família e id **uma vez** e devolve o
prefixo `cat.<família>.<id>`; o mesmo percurso então troca `name`/`nome` quando existe
`<prefixo>.nome`, e `desc`/`descricao` quando existe `<prefixo>.desc`. Aceita o objeto se
**qualquer uma** das duas chaves existir — senão uma entrada com descrição traduzida mas
sem nome ficaria de fora.

**(b) A chave do dicionário pai também vale como id.** Ao percorrer um dicionário, cada
par `[k, v]` em que `v` é objeto tenta `k` como id, além dos campos internos. É isso que
alcança `classes` e `instrumentos_base`.

**(c) Uma porta sem a saída antecipada.** `traduzirNomes` continua retornando na primeira
linha quando o idioma é o padrão — é o caminho das mensagens, e em português não há o que
trocar. Mas os catálogos estáticos precisam ser reescritos **também ao voltar para o
português**, para restaurar o texto original. Então o percurso é extraído para
`aplicarCatalogo(obj, soNome)`, sem a saída antecipada. `traduzirNomes(msg)` passa a ser
a saída antecipada mais `aplicarCatalogo(msg, false)` — mensagem troca nome E descrição.
O segundo parâmetro existe por causa dos catálogos estáticos, que pedem `true`.

A troca por id (e não por texto) torna a operação idempotente: aplicar de novo com outro
idioma reescreve a partir da chave, não do texto já trocado. É isso que faz a volta ao
português funcionar.

### Aplicar nos catálogos estáticos

No `game.js`, no ouvinte de troca de idioma que já existe, e uma vez no boot:

```js
I18N.aplicarCatalogo(GRIMORIO_CLIENT,   true);   // true = só o nome
I18N.aplicarCatalogo(ARMADILHAS_LUCCAS, true);
I18N.aplicarCatalogo(GS.CATALOGO_ITENS, true);
```

As três estruturas têm `id` interno em cada entrada, então a extensão (b) não é necessária
para elas — o filtro atual já as alcança. O `soNome=true` é o que implementa a decisão
acima, e é a única diferença entre esta chamada e a do caminho das mensagens.

### O vazamento de precedência

`_converterBagParaInventario` passa a ser `{ ...cat, nome: it.name || cat.nome }`.
Deliberadamente cirúrgico: só o nome exibido passa a vir do servidor, alinhando com o que
o tooltip já faz. Espalhar `...it` por cima do catálogo mudaria `tipo`, `preco` e outros
campos de que aquele caminho depende.

Essa correção e a tradução de `CATALOGO_ITENS` são complementares, não redundantes: a
tradução cobre os 28 ids coincidentes em qualquer ponto de render; a precedência garante
que o dado do servidor mande, inclusive para item que o catálogo do cliente não conhece.

## Testes

`tools/test_vocabulario.py` (estende a suíte):

1. O gerador emite `.desc` para as 189 entradas com descrição.
2. Entrada sem descrição **não** gera chave `.desc`.
3. O arquivo fica com 586 chaves.
4. Idempotência com as duas famílias de chave: descrição traduzida à mão sobrevive.

`tools/test_vocabulario_cliente.js` (estende a suíte):

1. O filtro troca `desc` e `descricao` junto com o nome.
2. Objeto com nome traduzível e sem descrição no dicionário mantém a descrição original.
3. Objeto alcançável só por `.desc` (sem `.nome`) ainda é tratado.
4. **Dicionário chaveado por id** — `{classes: {warrior: {name, desc}}}` é traduzido.
5. `aplicarCatalogo(obj, true)` troca o nome mesmo com o idioma em português (é o que
   restaura o original) e **não** toca em `desc`/`descricao`; com `false`, troca os dois.
6. Aplicar `aplicarCatalogo` duas vezes, em idiomas diferentes, devolve o texto certo nas
   duas — prova a idempotência de que a volta ao português depende.
7. Checagem estática de que `_converterBagParaInventario` prefere o nome do servidor, e de
   que o `game.js` chama `aplicarCatalogo` nos três catálogos estáticos — declaradas como
   estáticas, porque o `game.js` monta o DOM no load e não é carregável em teste.

## Tradução

As 189 descrições são frases de regra ("+2 de dano de arma até o fim do turno; recarga 3
rodadas"), média de 69 caracteres. Duas exigências acima do normal:

- **Precisão numérica e mecânica.** Números, dados (`2d6`), durações e condições têm de
  sobreviver intactos: um "+2" que vira "+3" muda a regra que o jogador lê.
- **Consistência com os nomes da etapa 2.** Uma descrição que cita "Canção Heroica" usa o
  mesmo "Heroic Song" que a chave de nome recebeu.

Glossário da etapa 2 mais os termos de regra: 🍖 fome = hunger, 💧 sede = thirst, recarga =
cooldown, rodada = round, turno = turn, alcance = range, save = saving throw, CD = DC,
vantagem/desvantagem = advantage/disadvantage.
