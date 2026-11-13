# Alforje de Explorador — design

## Intent
Criar um item único que combine espaço de inventário e um bolso de utilidades, economizando um espaço equipado.

## Escopo aprovado até aqui
- Nome: Alforje de Explorador; preço: 220 moedas.
- Imagem: `assets/itens/alforge2.png`.
- Efeito: +2 espaços de inventário e 1 bolso de utilidades com capacidade para até 4 unidades iguais de um item compatível.
- Ocupa um único slot de item equipado e conserva os itens guardados ao desequipar, seguindo o comportamento existente dos cintos.
- Só pode ser desequipado quando os itens atuais da mochila e o próprio alforje couberem após a remoção dos 2 espaços extras.

## Abordagens consideradas
- Somar preços dos itens básicos (100 + 120 = 220): recomendada; simples de comparar e reflete a economia de um slot.
- Cobrar 200 moedas: desconto por oferecer capacidade reduzida.
- Cobrar 250 moedas: prêmio pela conveniência de combinar os efeitos.

## Limites
Adicionar o item aos catálogos e lojas e integrar a capacidade de um bolso aos sistemas atuais de armazenamento. Não alterar os itens existentes nem outras mecânicas.
