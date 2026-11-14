# Aba de Escudos do Ferreiro

## Intenção

Separar os muitos escudos da lista de armaduras, facilitando encontrá-los no ferreiro.

## Contrato

- Adicionar **Escudos** logo após **Armaduras**.
- A aba inclui todos os itens da loja com `kind === "shield"` (23 atuais: modelos-base, materiais e especiais); Armaduras mantém os itens restantes.
- Preservar munições, compras, estoque por cidade, venda, reparo e offset das lojas com cena.
- A compra de escudos continua usando `ferreiro_armor`.

## Abordagem

Filtrar as duas abas na interface pelo metadado autoritativo `kind`; não criar outra categoria de estoque, pois o catálogo e a compra do servidor já tratam os escudos no fluxo de armaduras.

## Limites

Não alterar atributos, preços, classes permitidas ou regras dos escudos.
