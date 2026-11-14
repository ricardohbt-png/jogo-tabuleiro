# Aba de Arcos e Bestas do Ferreiro

## Intenção

Diminuir a lista da aba **Armas** e facilitar encontrar armas de combate à distância sem alterar os estoques nem a compra autoritativa do ferreiro.

## Contrato aprovado

- Adicionar a aba **Arcos e Bestas** imediatamente após **Armas**.
- Mover para ela os 11 modelos-base de arco/besta atualmente vendidos e as 33 variantes de materiais, totalizando 44 itens.
- Manter munições na aba **Munição**, separada.
- Preservar venda, reparo, tradução, foco de gamepad e compras usando `ferreiro_weapon`.

## Abordagens

1. Filtrar o catálogo existente no cliente usando os IDs-base de arco/besta. **Escolhida:** mantém `city_shops.json` e o contrato de compra intactos.
2. Criar uma categoria/estoque novo no servidor. Rejeitada porque duplicaria a classificação de armas e exigiria mudar estoques em todas as cidades sem benefício para esta divisão visual.

## Limites

Não alterar preços, permissões, itens, munições ou estoque das cidades.
