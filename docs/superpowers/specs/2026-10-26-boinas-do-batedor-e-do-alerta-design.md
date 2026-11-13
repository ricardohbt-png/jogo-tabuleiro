# Boinas do Batedor e do Alerta — especificação

## Objetivo

Adicionar duas boinas equipáveis no slot de cabeça, com a arte existente da boina e venda nos mercadores das cinco cidades.

## Itens aprovados

- **Boina do Batedor** (`boina_batedor`): 60 moedas, +1 de visão enquanto equipada.
- **Boina do Alerta** (`boina_alerta`): 150 moedas, +1 de visão e +1 em todos os testes de resistência enquanto equipada.
- Ambas usam `assets/itens/chapeu1.png`, ocupam `head` e não têm restrições de classe.

## Comportamento

- A visão usa o efeito de equipamento existente (`vision`).
- O bônus de resistência é passivo, soma-se aos outros modificadores de salvaguarda, e é removido ao desequipar a boina.
- As duas boinas aparecem na lista `mercador` das cinco cidades.
- Nome e descrição ficam disponíveis em português e inglês; o catálogo do editor é regenerado a partir do servidor.

## Limites

- Não alterar a arte, a malha 3D, outros preços ou estoques.
- Não adicionar restrições de classe nem efeitos temporários.
