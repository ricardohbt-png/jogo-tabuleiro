# Etapa 5 do idioma — Interface do cliente — Design

**Data:** 2026-08-14
**Depende de:** etapas 1 (motor PT/EN), 2 (vocabulário), 3 (descrições), 4a (erros),
4b-i e 4b-ii (narração) e 4c (nomes na frase) — todas implementadas e verificadas.

---

## Onde isto se encaixa

O **servidor está 100% traduzido**: não há mais narração nem mensagem de erro em
português nele, e a varredura por `ast` do `test_narracao.py` cobra isso. Esta é a
**última etapa** do roadmap de idioma.

## O problema, medido

**636 literais** em português no `game.js` (26.302 linhas), mais 52 no
`src/gameState.js` e 7 nos demais. O que o jogador vê hoje ao ligar o inglês:

```
screen-class-select:  "SALA · ▶ Iniciar Jogo · ⚔ Partir para a Aventura · Escolha seu herói"
screen-game:          "Turno 1 · Reset · Meu Personagem · Ações · Encerrar Turno"
screen-city:          "Carregando… · ⚔ Entrar na Masmorra"
```

Só `screen-connect` e `screen-savegames` estão traduzidos — o que a etapa 1 cobriu.

### Por forma do literal

| forma | qtd | tratamento |
|---|---:|---|
| rótulo/tooltip/mensagem solta | ~450 | chave |
| HTML inline (`<small>texto</small>`) | 73 | chave dentro do template |
| texto com **interpolação** | 63 | `t('chave', {param})` — `data-i18n` não carrega parâmetro |
| atribuição a `innerHTML`/`textContent` | 30 | chave |
| atributo (`title=`, `placeholder=`) | 20 | `data-i18n-title` / `data-i18n-ph` |
| **português como chave de LÓGICA** | ~10 | **não traduzir** — migrar a busca para id |

### Por função — a medição que vale

**CORREÇÃO.** A primeira medição desta etapa classificava por **faixa de linhas** entre
marcos de render, assumindo que o `game.js` fosse organizado por tela. Não é: são 26 mil
linhas e **172 funções** com literal, e as de telas diferentes se intercalam. A medição
por faixa dizia *"seleção de herói: 58"* quando o número real é **5** — os outros 53 eram
código de arremesso, baú, conexão e diagnóstico 3D que só por acaso moravam naquele
intervalo.

Pior que a imprecisão: **os literais não particionam por tela.** As funções maiores são
compartilhadas — `_itemDesc` (17) descreve item na ficha, na loja *e* no baú;
`gerarConteudoTooltip` (28) serve tooltip de qualquer tela; `setBtn` (18) monta botão do
HUD e da ficha. Uma sub-etapa "seleção de herói" traduziria 5 strings e deixaria a tela
ainda meio em português.

Distribuição real, por função:

| função | literais |
|---|---:|
| `_mageSkillBtn` | 43 |
| `gerarConteudoTooltip` | 28 |
| `renderConteudoAtributosFichaJogo` | 27 |
| `calcularVidaMaxima` | 27 |
| `_showTrapResult` | 26 |
| `handleTileClick` | 21 |
| `setBtn` | 18 |
| `_itemDesc` | 17 |
| … cauda de 164 funções | ~429 |

O editor (`tools/*.js`) fica **fora**: é ferramenta do autor, não do jogador.

## O número que decide o desenho

**163 atribuições a `innerHTML` contra 4 chamadas de `_i18nApply`.**

O mecanismo de tradução ao vivo já existe e funciona: `_i18nApply(root)` preenche
`[data-i18n]`, `[data-i18n-ph]` e `[data-i18n-title]`, e o `_setLang` chama
`_i18nApply(document.body)` na troca. O problema é que markup inserido **depois** só é
traduzido se alguém lembrar de chamar `_i18nApply` no container.

Já há um sintoma no código: o `_setLang` carrega um `_refreshTurnTimerOption()` com o
comentário *"rótulos montados em JS, não por data-i18n"*, e existem 9 chamadas
`_refreshX()`. Essa lista cresce sozinha a cada tela traduzida.

## Design

### A. Fundação (sub-etapa 5.0)

**`MutationObserver`.** Um observador no `document.body`, ligado no boot, aplica
`_i18nApply` a qualquer nó inserido que contenha `[data-i18n]`. As 163 atribuições a
`innerHTML` continuam como estão, e **é impossível esquecer de aplicar**.

Isso elimina a classe inteira de bug "traduzi mas não aparece na tela" — que é
exatamente o que a etapa 3 registrou como lição (*"testes passam ≠ o usuário vê"*) e o
que o usuário reportou hoje. Também apaga a dívida dos `_refreshX()` manuais.

**Medição antes de fixar, com teto explícito:** o observador só age quando o nó traz
`data-i18n`. Antes de adotá-lo em definitivo, medir com o jogo em combate (o momento de
maior taxa de re-render) por 30 segundos e registrar o **tempo total gasto dentro do
callback**. Teto: **1% do tempo de frame** — com 60fps isso é 0,16 ms por frame, ou
~300 ms nos 30 s. Acima disso, cair para chamada manual de `_i18nApply` nos pontos de
inserção e **registrar o motivo no `CLAUDE.md`**; a decisão não pode ficar implícita.

A medição vale por si: se o custo for desprezível — e a expectativa é que seja, porque
hoje quase nenhum nó traz `data-i18n` —, o número fica registrado e ninguém precisa
re-discutir isso na etapa seguinte.

**`ABILITY_NAME_TO_ID` deixa de ser chaveado por português.** Hoje:

```js
const ABILITY_NAME_TO_ID = Object.freeze({
  'Fúria Berserker': 'furia_berserker', 'Veneno Rápido': 'veneno_rapido', …
});
```

É tabela de **lógica**, não de interface: o nome exibido é usado para achar o ícone da
habilidade. Traduzir o nome sem mexer nisso faz os ícones sumirem. Passa a resolver pelo
id que o servidor já manda. **É pré-requisito de qualquer lote que traduza nome de
habilidade**, não item opcional. Fechado na 5.0.

**Convenção de chave: `ui.<área>.<slug>`** — `ui.hud.encerrar_turno`,
`ui.ficha.atributos`. Espelha `narracao.<slug>` e `erro.<slug>`. A `<área>` aqui é a
TELA em que o texto aparece — ela nomeia a chave, mas **não** recorta o trabalho (o
recorte é por função, ver seção B). As 38 chaves `ui.*` da etapa 1 já seguem isso.

### B. Os lotes, por tamanho de função

**Um spec (este), N planos.** A fundação (5.0) já fechou. O trabalho restante é recortado
por **função, em lotes de tamanho decrescente** — não por tela, pelo motivo da seção
anterior:

- **Lote 1:** as ~15 maiores (~250 literais, 40% do total).
- **Lote 2:** as de porte médio.
- **Lote 3:** a cauda de funções pequenas.

Cada lote é mensurável (o placar cai visivelmente) e pequeno o bastante para o conferidor
de diff ser útil. **A verificação continua sendo jogar e olhar** — só que cada lote cobre
várias telas de uma vez, porque as funções são compartilhadas. Ao fechar um lote,
acrescente os nomes das funções ao conjunto `FECHADAS` do `tools/test_interface.py`: é
isso que impede a regressão.

### C. Mecanismo por forma

| forma | mecanismo | por quê |
|---|---|---|
| rótulo fixo em markup gerado | `data-i18n="chave"` | troca ao vivo, sem re-render |
| atributo | `data-i18n-title` / `data-i18n-ph` | idem, e já suportado |
| texto com interpolação | `t('chave', {param})` | `data-i18n` não carrega parâmetro |
| texto fora do DOM (alert, log, título) | `t('chave')` | não há nó para marcar |

Os 63 interpolados **não** têm troca ao vivo pelo observador — mas todos dependem do
estado, e o servidor reenvia o estado ao receber `set_lang`, o que dispara o render
normal. O efeito para o jogador é o mesmo; só o mecanismo difere.

## O que NÃO entra

- **Editor** (`tools/*.js`) — ferramenta do autor.
- **Conteúdo autoral** — masmorras, campanhas, falas de NPC, itens e monstros do editor.
- Os ~10 sites onde português é **chave de lógica**: esses são *corrigidos* (migram para
  id), não traduzidos.
- As ~6 passagens de nome que a 4c documentou como fora das 8 famílias de catálogo.

## Modos de falha

| situação | comportamento |
|---|---|
| chave sem `en` | cai no `pt` — regra do motor desde a etapa 1 |
| chave ausente | o `t()` devolve a própria chave e loga `console.warn` — aparece na tela, fica óbvio |
| nó inserido sem `data-i18n` | fica no idioma em que foi montado (é o caso dos interpolados, que re-renderizam) |
| observador custa caro | cair para `_i18nApply` manual e registrar a decisão |

## Como se prova

**`tools/test_interface.py`** — varredura estática **por função**: para cada função do
`game.js`, quantos literais com acento ela ainda tem fora de `t()` / `data-i18n`. Segue o
padrão da seção `[3]` do `test_narracao.py`: **relata** o placar inteiro e **cobra** as
funções já fechadas, listadas no conjunto `FECHADAS` do topo do arquivo. Ao terminar um
lote, acrescente os nomes ali — é isso que impede a regressão.

**No cliente:** teste do `MutationObserver` (nó inserido com `data-i18n` é traduzido
sozinho) e do `ABILITY_NAME_TO_ID` migrado (o ícone continua sendo achado com o nome
traduzido).

**Paridade de `{parâmetros}`** entre `pt` e `en`: o `test_erros.py` já cobre todas as
chaves de todos os arquivos, então pega as novas de graça.

**Verificação humana por sub-etapa**, obrigatória: servidor reiniciado, idioma trocado,
aquela tela lida. Automatizado prova que a chave existe; só o olho prova que ela chega.
