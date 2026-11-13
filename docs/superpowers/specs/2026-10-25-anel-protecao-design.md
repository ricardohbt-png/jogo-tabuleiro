# Anel de Proteção — Design

## Intenção e objetivo

Adicionar ao Legends for Hire um anel comprável que concede +1 de Classe de Armadura enquanto equipado, usando o ícone existente `assets/itens/ring.png`, por 80 moedas, em todos os mercadores das cidades.

## Escopo

- Item nativo `anel_protecao`, slot `ring`, efeito `def_` com valor 1, preço 80 e descrição localizada.
- Incluir o SKU nas cinco listas `mercador` de `city_shops.json`.
- Preservar o sistema existente de equipar até dois anéis e o cálculo incremental/recalculado de CA.
- Não criar arte nova, regra de limite por classe, estoque procedural, loot ou item editável no Editor de Itens.

## Abordagens consideradas

- **Item nativo (escolhida):** acrescentar a definição a `SHOP_MERCHANT`, o SKU às listas de estoque das cidades e as traduções ao catálogo. Reusa diretamente os efeitos e fluxos de compra/equipamento atuais.
- **Acessório personalizado:** gravar no sistema de itens personalizados e sincronizar a disponibilidade por cidade. Isso atende itens configurados pelo Editor, mas é trabalho adicional para um item fixo solicitado para todos os mercados.

## Decisões aprovadas

- Nome: Anel de Proteção.
- Bônus: +1 CA enquanto equipado; pode ocupar qualquer um dos dois espaços de anel.
- Preço: 80 moedas.
- Disponibilidade: os mercadores das cinco cidades atualmente configuradas.
- Imagem: `assets/itens/ring.png`.

## Restrições e verificação

- Seguir `CLAUDE.md` como fonte de arquitetura e protocolo.
- Não tocar nas alterações locais preexistentes não relacionadas.
- Verificar catálogo e preço, presença em todos os mercadores, ícone, compra, equipar/desequipar e alteração simétrica de CA.
