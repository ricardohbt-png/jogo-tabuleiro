# Punhais do Assassino — design

## Objetivo

Adicionar duas armas mágicas baseadas na Adaga para venda nas lojas de ferreiro: Punhal do Assassino e Punhal do Assassino Maior. Ambas usam a arte `assets/itens magicos/punhal_do_assassino.png`.

## Regras aprovadas

- As duas armas mantêm o perfil da Adaga: 1d4 perfurante, finesse, mão secundária e arremesso a 3 casas.
- Punhal do Assassino: +1 no acerto e no dano, custa 1.500 moedas e adiciona +1d4 ao Ataque Furtivo do Ladino.
- Punhal do Assassino Maior: +2 no acerto e no dano, custa 3.500 moedas e adiciona +2d4 ao Ataque Furtivo do Ladino.
- O dado extra só é rolado quando o Ataque Furtivo do Ladino é ativado com o punhal equipado, incluindo ataques furtivos principais e reações. Não altera ataques comuns ou Ataque Furtivo de monstros.
- A prévia de dano mostra os dados furtivos adicionais antes do ataque.
- Os bônus são registrados na definição autoritativa do servidor e levados ao catálogo do editor; as regras e preços ficam documentados em `CLAUDE.md`.

## Abordagem

Armazenar a quantidade de d4 de Ataque Furtivo em metadado da própria arma e somá-la ao número de dados quando o cálculo autoritativo de Ataque Furtivo do Ladino for acionado. Isso reaproveita a ordem existente do dano (antes de resistência/redução). Uma propriedade genérica de dano por acerto foi descartada porque aplicaria dados também em golpes normais.

## Limites

Sem mudanças a outras adagas, à progressão de Ataque Furtivo, à elegibilidade de classes ou aos demais ataques. Usar a arte gerada e compartilhada pelos dois itens.
