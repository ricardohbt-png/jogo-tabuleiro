# Etapa 2 do idioma — Vocabulário (nomes de catálogo) — Design

**Data:** 2026-08-10
**Depende de:** `docs/superpowers/specs/2026-08-10-idioma-i18n-design.md` (etapa 1 — motor
PT/EN, já implementado e verificado).

---

## Onde isto se encaixa

A tradução do jogo é grande demais para um projeto só. A medição da superfície:

| Onde | Quanto |
|---|---|
| Narração do mestre (`gm_say`) | 544 |
| Mensagens de erro | 470 |
| Nomes de catálogo | 442 entradas → **397 chaves únicas** após deduplicar por id |
| Descrições de catálogo | 185 |
| Interface do cliente (toasts, painéis, HTML) | ~1.000 |

Foi decomposta em quatro sub-projetos, cada um com seu ciclo spec → plano →
implementação. **Este é o primeiro: o vocabulário — só os nomes.** Os outros três
(descrições, erros + narração do servidor, interface do cliente) vêm depois.

**Por que o vocabulário vem primeiro:** quase toda frase do jogo embute um nome de
monstro, item ou habilidade. Traduzir a narração antes obrigaria a reescrever as 544
chamadas uma segunda vez para tornar o nome tardio. Fazendo o vocabulário primeiro, as
etapas seguintes só envolvem texto em `T(...)` e não voltam atrás.

## O problema que este sub-projeto resolve primeiro

O motor da etapa 1 **não resolve parâmetro que é ele próprio traduzível**. Verificado:

```python
S.t('x.frase', 'en', quem=S.T('x.goblin'))
→ "T('x.goblin', {}) attacked!"
```

`t()` faz `str(params[nome])`, e `str` de um `T` devolve o repr. Sem corrigir isso, uma
frase em inglês só pode receber o nome em português cravado. É a correção que destrava
tudo o que vem depois.

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Escopo | **Só os nomes** (397 chaves). Descrições, fichas de monstro aninhadas, erros, narração e interface ficam fora. |
| Onde os nomes são traduzidos | **No cliente**, por um filtro único aplicado a toda mensagem recebida |
| Origem das chaves | **Geradas** por script a partir dos catálogos, não escritas à mão |
| Conteúdo autoral (itens/monstros do editor) | Continua no idioma em que foi escrito — sai de graça do fallback |

Justificativa da segunda: são **405 pontos no cliente** que leem `.name` e **498 f-strings
no servidor** que embutem nome. Um filtro na entrada da mensagem deixa os 405 intocados. A
alternativa — o servidor trocar o nome no payload — esbarra em os payloads reaproveitarem
os mesmos dicts que vão para o savegame (`bag`, `gear`, `weapon` estão em
`_DURABLE_FIELDS`), exigindo cópia defensiva em vários construtores, com risco de corromper
estado persistido.

## Fora de escopo

- As 185 descrições (`desc`/`descricao`) — lote seguinte.
- Ataques e habilidades especiais aninhados nas fichas de monstro.
- Erros, narração e interface do cliente — os outros três sub-projetos.
- Traduzir conteúdo criado no editor (masmorras, campanhas, itens e monstros custom).

---

## Arquitetura

### Convenção de chave

`cat.<família>.<id>.nome`, com o id estável que cada catálogo já tem (`id`, `type`, ou a
chave do dict):

```
cat.item.espada_longa.nome
cat.monstro.goblin.nome
cat.guilda.brutalidade.nome
```

Oito famílias:

| Família | Origem | Chaves |
|---|---|---:|
| `item` | `WEAPONS` ∪ `SHOP_WEAPONS` ∪ `SHOP_ARMORS` ∪ `SHOP_MERCHANT` ∪ `SHOP_TEMPLE` ∪ `SHOP_TAVERN` ∪ `ARREMESSAVEIS` ∪ `VENENOS` | 140 |
| `guilda` | `GUILD_CATALOG` | 125 |
| `monstro` | `MONSTER_DEFS` | 51 |
| `decor` | `DECOR_TYPES` | 28 |
| `magia` | `GRIMORIO` | 27 |
| `armadilha` | `ARMADILHAS` | 11 |
| `instrumento` | `INSTRUMENTOS_BASE` | 9 |
| `classe` | `CLASSES` | 6 |

**Item é uma família só, e não uma por loja.** Verificado: os 8 catálogos de item somam 175
entradas com id, que deduplicam em **140 ids únicos**, e **nenhum id repetido carrega nome
diferente** — o mesmo item aparece em `WEAPONS` e em `SHOP_WEAPONS`, sempre com o mesmo
nome. O gerador deduplica; um conflito futuro é erro e o gerador falha alto.

### O dicionário gerado

`tools/gerar_vocabulario.py` varre os catálogos e escreve `src/lang/catalogo.js`, com o
`pt` preenchido a partir do próprio catálogo e o `en` a traduzir.

**Idempotente:** rodar de novo preserva todo `en` já traduzido, acrescenta as chaves novas
e **relata** — sem apagar — as que ficaram órfãs porque o item saiu do catálogo. É isso que
torna a manutenção viável: ao criar uma arma nova no editor de itens, o gerador diz o que
falta traduzir.

**Arquivo separado do `strings.js` escrito à mão**, exatamente como a etapa 1 previu. Para
isso, duas mudanças pequenas:

- `_load_lang()` passa a ler e fundir **todos** os `.js` de `src/lang/`, ancorando em
  `^\s*window\.LANG_\w+\s*=` em vez de só `window.LANG_STRINGS`.
- `index.html` ganha uma tag `<script>` para `src/lang/catalogo.js`, que termina com
  `Object.assign(window.LANG_STRINGS, window.LANG_CATALOGO);`.

Misturar gerado e manuscrito no mesmo arquivo seria pedir para o gerador sobrescrever
tradução feita à mão.

### Cliente — o filtro de entrada

`src/gameState.js` tem um ponto único onde toda mensagem passa
(`ws.onmessage → _handle(JSON.parse(e.data))`, linha 1106). Ele ganha um gancho:

```js
GS.setMessageFilter(fn)   // game.js registra; gameState.js só chama
```

`gameState.js` aplica o filtro antes de despachar, **sem saber o que ele faz** — continua
sem nenhuma referência a `window`, `I18N` ou `document`, como o CLAUDE.md exige. Quem
conhece o dicionário é o `game.js`, que registra a função de tradução.

O filtro percorre só as coleções conhecidas, por família:

| Coleção no payload | Família | Campo do id |
|---|---|---|
| `monsters[]`, `corpses[]`, `master_reserve[]` | `monstro` | `type` |
| `players[].bag[]`, `players[].gear{}`, `players[].weapon` | `item` | `id` |
| `chests[].items[]`, `ground_items[].item`, itens de loja e de `decor_loot` | `item` | `id` |

Para cada objeto, se existir tradução para a chave derivada, o campo `name` é substituído;
**se não existir, o nome fica como está** — que é o comportamento certo para itens e
monstros criados no editor, e a razão de o conteúdo autoral sair de graça.

### Servidor

Duas coisas, e nada mais:

1. **`t()` resolve parâmetro aninhado.** Se o valor de um parâmetro for um `T`, ele é
   resolvido recursivamente no mesmo idioma antes da substituição.
2. **`nome_de(familia, id)`** devolve `T("cat.<familia>.<id>.nome")`, para a etapa da
   narração usar como parâmetro tardio.

Nenhum payload muda. Eles seguem mandando o nome em português, que é justamente o fallback
de que o filtro do cliente depende.

## Testes

`tools/test_vocabulario.py`:

1. O gerador produz uma chave para cada nome de cada uma das 8 famílias, e a chave bate com
   o id real do catálogo.
2. Rodar o gerador duas vezes é idempotente, e a segunda execução **preserva** um `en`
   traduzido à mão.
3. Uma chave órfã (item removido do catálogo) é **relatada e não apagada**.
4. Id repetido com nomes diferentes faz o gerador **falhar**, em vez de escolher um em
   silêncio.
5. `t()` resolve `T` aninhado, nos dois idiomas.
6. `nome_de` devolve um `T` com a chave certa.
7. `_load_lang()` funde vários arquivos de `src/lang/`.

`tools/test_vocabulario_cliente.js` (node):

1. O filtro traduz nome de monstro (por `type`) e de item (por `id`).
2. Nome sem tradução no dicionário **sobrevive intacto** (caso do conteúdo autoral).
3. O filtro alcança as coleções aninhadas (bolsa e equipamento dentro de `players[]`).
4. Nenhuma chave de `catalogo.js` aponta para item que não existe mais no catálogo.

## Sequência dos próximos sub-projetos

1. **Vocabulário — nomes** (este)
2. Descrições de catálogo (185)
3. Erros (470) e narração (544) do servidor — já podem usar nome tardio
4. Interface do cliente (~1.000)
