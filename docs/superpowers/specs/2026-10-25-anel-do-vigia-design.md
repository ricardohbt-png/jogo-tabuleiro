# Anel do Vigia — Design

## Intenção

Adicionar um anel de exploração que amplia em duas casas o raio de visão do herói enquanto estiver equipado.

## Decisões aprovadas

- Nome: Anel do Vigia (`anel_vigia`).
- Efeito permanente: `vision +2`, aplicado pelo bônus de equipamento existente.
- Preço: 80 moedas.
- Ícone existente: `assets/itens/ring.png`.
- Venda nos cinco mercadores definidos em `city_shops.json`.
- Sem restrição de classe; pode usar os dois espaços de anel atuais.

## Abordagens

- Item nativo em `SHOP_MERCHANT`, usando o efeito escalar `vision`: escolhida porque reaproveita compra, equipamento, persistência de CA/atributos e bônus de visão já existentes.
- Acessório personalizado no Editor de Itens: não escolhida porque o anel tem valores fixos, nome e disponibilidade global aprovados.

## Limites e validação

- Não altera percepção, detecção de armadilhas ou visão de monstros; só aumenta o raio de visão dos heróis pelo mecanismo `vision_bonus`.
- Preservar alterações locais não relacionadas.
- Validar sintaxe do servidor e dos catálogos, asset, estoque único em cada mercador e diff.
