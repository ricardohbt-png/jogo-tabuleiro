# Etapa 4c do idioma — Nomes de catálogo dentro da frase — Design

**Data:** 2026-08-11
**Depende de:** etapas 1 (motor PT/EN), 2 (vocabulário), 3 (alcance + descrições),
4a (erros) e 4b-i (narração, lote mecânico) — todas implementadas e verificadas.

---

## Onde isto se encaixa

1. Motor PT/EN ✅
2. Vocabulário — 397 nomes ✅
3. Alcance dos nomes + 189 descrições ✅
4. a) Erros — 471 mensagens ✅ · b-i) Narração mecânica — 390 sites ✅ ·
   **c) Nomes dentro da frase ← este** · b-ii) Narração, lote difícil (153 sites)
5. Interface do cliente (~1.000)

**Esta etapa não é a 4b-ii.** A 4b-ii continua pendente e mantém o nome: são os 153
`gm_say` que ainda não foram migrados (109 multilinha, 28 f-strings que atravessam a
linha, 3 concatenações, 7 por variável, 6 do pool `gm(...)`). A 4c ataca um problema
**ortogonal**, dentro dos 390 sites que a 4b-i já migrou.

## O problema

A 4b-i migrou a frase, mas passou o nome **verbatim**. O resultado é frase em inglês com
nome em português:

> *The adventurers leave the city and enter the dungeon. Round 1 — **Elemental Elétrico**'s
> initiative.*

O `nome_de(familia, id)` existe desde a etapa 2 exatamente para isto (devolve o nome como
texto TARDIO, resolvido no idioma de quem lê) e o `t()` resolve parâmetro aninhado desde
então. Faltou usá-lo.

## A superfície, medida

716 parâmetros são passados nos 390 `T("narracao.…")`, em 187 expressões distintas:

| forma | passagens | expressões | nesta etapa? |
|---|---:|---:|---|
| nome de **jogador** (`p['name']`, `caster['name']`) | 158 | 4 | não — está certo cru |
| acesso **direto** a dict (`m['name']`, `item['name']`, `alvo.get('name')`…) | 216 | 37 | **sim** |
| **variável local** (`nome` 28, `alvo_nome` 24, `tgt_name` 15, `dono_nome` 2…) | 79 | 10 | **sim** |
| números, dados, CDs, rolagens | 263 | 136 | não |

**Escopo: as 295** (216 + 79). Todas as 8 famílias de catálogo entram — item, monstro,
magia, armadilha, guilda, decor, instrumento, classe —, porque as 8 já estão traduzidas
desde a etapa 3 e deixar algumas de fora só trocaria uma frase meio-inglesa por outra.

## A armadilha que decide o desenho

`nome_de()` num id **sem** entrada no catálogo devolve a própria chave: o log mostraria
literalmente `cat.monstro.soldado.nome`. E o jogo tem conteúdo **autoral** — editor de
criaturas e editor de itens — que por definição não está no `catalogo.js` gerado.

Pior: alguns nomes são **mutados em tempo de execução**, e aí nem o id salva:

| origem | exemplo | linha |
|---|---|---|
| item saqueado do Devorador | `Alabarda de Prata (corroído)` | 24780 |
| munição restante no loot | `Virotes (×7)` | 22507 |
| servo do Pedro | `Goblin Animado` | 12422 |
| instrumento (composto por 3 eixos) | `Harpa Lendária Élfica` | 1066 |
| elemental fora de controle | `Elemental Descontrolado` | 19697 |

Traduzir "pelo id" cegamente apagaria a informação que o sufixo carrega — o jogador
deixaria de saber que a peça está corroída, quantos virotes sobraram, ou que aquele
goblin é um servo e não um inimigo.

**Fora de perigo:** as 16 armas de prata (`Alabarda de Prata`) são compostas no *boot*, e
por isso já entraram no `catalogo.js` como itens próprios, com tradução (`Silver
Halberd`). Nada a fazer nelas.

## Design

### 1. `nome_cat(familia, ident, cru)` — a guarda de igualdade

```python
def nome_cat(familia, ident, cru):
    """Nome de catálogo tardio, mas SÓ quando o nome cru ainda é o do catálogo.
    Nome autoral, renomeado no editor ou mutado em runtime não tem entrada — ou
    tem uma que não bate — e sai cru, exatamente como hoje."""
    ent = LANG_STRINGS.get(f"cat.{familia}.{ident}.nome")
    return T(f"cat.{familia}.{ident}.nome") if ent and ent.get("pt") == cru else cru
```

A guarda é o coração da etapa: é ela que torna a mudança **segura por construção** para
todo conteúdo autoral, sem lista de exceções para manter. Um monstro criado no editor não
tem chave → sai cru. Um nativo renomeado por `overwrite_native` tem chave mas nome
diferente → sai cru, preservando o nome do autor.

### 2. `nome_criatura(x)` — despacho pela forma do dict

`alvo` e `target` são ora herói, ora monstro, ora servo animado — o **mesmo parâmetro**,
em ~45 sites. Nenhuma decisão estática acerta os três; a informação só existe em runtime,
no dict:

| forma | como se reconhece | resultado |
|---|---|---|
| jogador | tem `class_id` | `x["name"]` cru — nome escolhido pelo jogador |
| monstro | tem `type` | `nome_cat("monstro", x["type"], x["name"])` |
| servo animado | tem `vida_atual` e `tipo` | composto — ver 3 |

### 3. Nomes compostos: carregar as partes, nunca reparsear a string

Princípio único para os quatro casos: **não** tentar desmontar a string pronta procurando
o sufixo. Onde falta a parte, grava-se a parte.

**Servo animado** — `handle_animar_mortos` passa a gravar `nome_base` (o `corpse["nome"]`)
ao lado do `nome` composto que já grava. O animado já carrega `tipo`.
`nome_criatura` devolve `T("cat.monstro.animado", nome=nome_cat("monstro", a["tipo"],
a["nome_base"]))` — pt `"{nome} Animado"`, en `"Animated {nome}"`.

**Item corroído** — o servidor **para de mutar** `item["name"]`; o item já carrega
`corrosao_inicial`. `nome_item` compõe `T("cat.item.corroido", nome=…)` — pt
`"{nome} (corroído)"`, en `"{nome} (corroded)"`.

Isto conserta de quebra um **bug pré-existente que não é de narração**: o filtro
`traduzirNomes` do cliente troca `name` pelo nome do catálogo sempre que o id tem chave,
então hoje, em inglês, a peça já aparece na bolsa como "Silver Halberd" — o sufixo
"(corroído)" some em silêncio e o jogador não vê que a armadura está corroída. O filtro
passa a recolocar o sufixo quando o item tem `corrosao_inicial`.

**Munição** — `SHOP_AMMO` ficou fora da lista de fontes do `gerar_vocabulario.py` na etapa
2, então nenhum dos 6 nomes tem chave. Duas correções:

- acrescentar `SHOP_AMMO` às fontes do gerador — traduz o SKU de loja
  (`Flechas (×10)` → `Arrows (×10)`), e essas chaves nascem no `catalogo.js`;
- uma chave curta por munição (`cat.item.<id>.nome_curto`: `Flechas` → `Arrows`) para o
  loot compor `T("cat.item.municao_x", nome=…, n=…)`, já que o nome de loja embute a
  contagem do pacote e não serve de base. O loot para de mutar o `name` e passa a se
  apoiar no `ammo_count`, que já existe.

O gerador só emite `.nome` e `.desc`, então `nome_curto` — como `cat.item.corroido`,
`cat.item.municao_x` e `cat.monstro.animado` — é **chave escrita à mão** e mora no
`composto.js`, não no `catalogo.js` gerado.

**Instrumento** — `_instrumento_nome` monta em português com concordância de gênero
(`Harpa` + `Velha` + `Élfica` + `Rúnica`). Em inglês o adjetivo vem **antes** do
substantivo, então a ordem não é a mesma. A composição vira dicionário, não código:

| chave | pt | en |
|---|---|---|
| `cat.instrumento.nome_composto` | `{base}{ql}{orig}{run}` | `{ql}{run}{orig}{base}` |
| `cat.instrumento.adj.velho.f` | `" Velha"` | `"Old "` |
| `cat.instrumento.adj.velho.m` | `" Velho"` | `"Old "` |
| `cat.instrumento.adj.elfica.f` | `" Élfica"` | `"Elven "` |
| `cat.instrumento.adj.lendario.f` | `" Lendária"` | `"Legendary "` |

O espaço vem embutido **no lado certo de cada idioma**, então parte ausente não deixa
espaço solto e cada idioma escolhe a sua ordem no template. O gênero existe só no `pt` (as
duas variantes têm o mesmo `en`) e continua decidido por `_INSTRUMENTO_GENERO_FEM`, onde
já mora. `Harpa Lendária Élfica` → `Legendary Elven Harp`.

`_instrumento_nome` **continua existindo e devolvendo português** — é ela que grava
`inst["name"]` no estado, que vai a disco no savegame. Ganha uma irmã
`_instrumento_nome_T(inst)`, usada só na narração.

O cliente precisa da sua própria versão: um instrumento tem id único por combinação
(`instrumento_harpa_velho_elfica`), que **não** tem entrada no catálogo, então o
`traduzirNomes` de hoje não o troca e ele fica em português na bolsa. O `src/i18n.js`
ganha um compositor pequeno que reconhece `tipo_item === "instrumento"` e monta o nome a
partir de `base`/`qualidade`/`origem`/`encantamento` — que o item já carrega — lendo **as
mesmas chaves** do `composto.js`. Uma composição, duas implementações: o teste as compara
nos 5 arranjos para que não divirjam.

**`Elemental Descontrolado`** não é composto, é um literal: uma chave e pronto.

### 4. Onde cada peça vive

| arquivo | o que muda |
|---|---|
| `server.py` | `nome_cat`/`nome_criatura`/`nome_item`/`_instrumento_nome_T`; 295 parâmetros; parar de mutar 2 nomes; gravar `nome_base` no animado |
| `src/lang/catalogo.js` | chaves de munição (gerador) |
| `src/lang/composto.js` (novo) | template e adjetivos do nome composto, mantido à mão |
| `tools/gerar_vocabulario.py` | `SHOP_AMMO` nas fontes |
| `src/i18n.js` | sufixo `(corroded)` por `corrosao_inicial`; nome composto de instrumento |
| `tools/test_narracao.py` | seção nova |

O arquivo novo é separado do `catalogo.js` pelo mesmo motivo da etapa 2: o `catalogo.js` é
**gerado** e o gerador sobrescreveria tradução escrita à mão.

## O que continua em português, de propósito

- Monstro e item **autorais** (editor) — sem chave, e é o comportamento correto: é o nome
  que o autor escolheu.
- Nome de **jogador**.
- Os 153 sites da 4b-ii, que ainda nem foram migrados.

## Modos de falha

| situação | comportamento |
|---|---|
| id sem chave no catálogo | nome cru (guarda de igualdade) |
| chave existe, nome foi renomeado | nome cru — nunca descarta o nome do autor |
| `x` não é jogador nem monstro nem animado | `x.get("name")` cru; nunca levanta |
| tradução `en` vazia | cai no `pt` — regra do motor desde a etapa 1 |

Nenhum caminho novo pode levantar exceção: a narração roda dentro do laço de turno, e uma
exceção ali derruba a partida, não só a frase.

## Como se prova

`tools/test_narracao.py` ganha uma seção:

- monstro **nativo** traduz; monstro **autoral** sai cru; nativo **renomeado** sai cru;
- item **corroído** sai `(corroded)` em inglês e `(corroído)` em português;
- servo animado sai `Animated Goblin`;
- instrumento composto sai certo nos 5 arranjos: simples, com qualidade, com origem, com
  rúnico e lendário — nos dois idiomas e nos dois gêneros;
- nome de **jogador** nunca é traduzido;
- varredura estática: nenhum `T("narracao.…")` passa mais `X['name']` cru — mesma técnica
  de conferidor que a 4a e a 4b-i usaram.

Regressão obrigatória, porque a mudança encosta em subsistemas alheios:
`test_instrumentos_bardo.py` (dono do `_instrumento_nome`), `test_devorador.py`
(corrosão), `test_vocabulario.py` + `test_vocabulario_cliente.js` (o gerador muda),
`test_reviver_mortos.py` (o animado ganha campo), e as 4 suítes grandes
(`test_modo_mestre`, `test_guilda`, `test_cenas_conversa`, `test_masmorra_sequenciada`).

Prova ponta a ponta com dois clientes em idiomas diferentes na mesma sala — **com o
servidor reiniciado**, a armadilha que a 4b-i registrou: um servidor de antes da migração
mostra tudo em português e parece que nada funcionou.
