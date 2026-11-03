# Refeições para o grupo na taverna

## Intenção e objetivo

Adicionar duas refeições de balcão para alimentar e hidratar todos os heróis do grupo numa única compra. **Banquete de Comemoração** restaura +40 de fome e +40 de sede para cada herói e custa 5 moedas por herói. **Grande Celebração** restaura +75 de fome e +75 de sede para cada herói e custa 12 moedas por herói.

## Abordagens

- **Serviços de balcão em grupo (escolhida):** cada refeição aparece no catálogo da taverna; o servidor calcula o preço total pelo número de heróis, cobra quem iniciou a compra e aplica a restauração ao grupo. Cada uma pode ser comprada uma vez por visita para o grupo inteiro. Mantém o fluxo atual de refeição imediata.
- **Consumíveis individuais:** colocar um item na mochila de cada herói e exigir uso separado. Isso adiciona passos e não corresponde a uma refeição única para o grupo.
- **Pedido de refeição por herói:** cada compra restaura apenas o comprador e cobra preço individual. Não satisfaz o efeito de grupo solicitado.

## Regras e limites

- O grupo é a lista de fichas com `class_id`, excluindo Mestre e heróis de teste; heróis controlados por procuração no modo Solo com grupo contam individualmente.
- O custo total é `preço_por_herói × número_de_heróis`; a compra é recusada sem debitar se o comprador não tiver ouro suficiente.
- Os preços por herói são fixos e não recebem os modificadores de preço da cidade.
- Cada herói recebe o bônus individual, limitado pelos máximos normais de fome e sede.
- Cada uma das duas opções fica marcada como usada para o grupo até a próxima visita à cidade, seguindo o limite atual das refeições de balcão.
- As refeições existentes e os consumíveis na mochila mantêm seu comportamento.

## Implementação

Adicionar entradas ao catálogo de refeições da taverna, identificação/tradução de nomes e descrição localizada do preço por integrante; expor o total calculado na loja e validar cobrança, limite de visita e restauração no servidor. O servidor continua autoritativo para todas as regras.

## Fora de escopo

Não alterar preços ou efeitos das refeições atuais, nem permitir compras repetidas das novas opções durante a mesma visita.
