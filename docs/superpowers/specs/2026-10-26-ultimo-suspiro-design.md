# Último Suspiro — Design

## Intenção

Adicionar um acessório de uso único que evite uma morte e elevar o preço da técnica Último Esforço, refletindo seu poder.

## Comportamento aprovado

- **Último Suspiro** custa 500 moedas, ocupa um dos dois espaços `item` e usa o ícone dedicado `assets/itens/ultimo_suspiro.png`.
- Cada cópia equipada concede uma proteção. Ao chegar a 0 PV, o herói permanece com 1 PV e uma cópia equipada é consumida/removida. A próxima proteção só dispara quando outro dano levar os PV a zero.
- Duas cópias podem ser equipadas e acumuladas, uma proteção por cópia. Itens guardados na bolsa não protegem.
- Proteções equipadas são verificadas antes das técnicas que evitam morte. Último Esforço permanece como a última camada; sua mecânica atual de dois mini-turnos permanece inalterada.
- Último Esforço passa de 350 para 700 moedas.

## Abordagens

- Consumir automaticamente cópias na bolsa: descartada porque ignoraria os espaços de equipamento e permitiria carregar proteções sem equipá-las.
- Uma carga por acessório equipado nos espaços `item1`/`item2`: escolhida por permitir acumular até duas proteções e tornar o custo de oportunidade visível.
- Um efeito temporário ativado manualmente que não ocupa equipamento: descartada após a decisão de equipar o item e permitir duas cópias cumulativas.

## Escopo e limites

Adicionar o item ao catálogo e ao estoque dos mercadores, integrar o consumo no fluxo autoritativo de morte, atualizar a ficha da técnica e documentar a regra em `CLAUDE.md`. Não alterar a duração ou os efeitos de Último Esforço, Instinto de Sobrevivência ou regeneração.
