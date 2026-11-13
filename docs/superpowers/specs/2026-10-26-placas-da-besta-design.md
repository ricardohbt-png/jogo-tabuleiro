# Placas da Besta

## Objetivo

Criar uma variante reforçada da Armadura de Couro e Placas, com aparência de ônix, como item comprável.

## Regras aprovadas

- ID `placas_da_besta`; armadura no slot `armor`, CA +3 e preço de 250 moedas.
- Reduz em 1 cada instância de dano do tipo `physical` enquanto equipada; não reduz dano mágico ou elemental.
- Tolera 4 níveis de corrosão sem penalidade; nos 2 níveis seguintes sofre as penalidades normais e é destruída no nível seguinte.
- Herda da armadura-base as classes Guerreiro, Ladino, Bardo e Paladino e os materiais de corrosão.
- É vendida nos ferreiros de armaduras das cinco cidades.
- Usa `assets/itens/placas_da_besta.png`, variante da referência `assets/itens/leather_plate.png`: mais espessa, negra, brilhante como ônix.

## Abordagem

Usar o bônus de resistência nativo `{"effect":"resist","type":"physical","value":1}`; ele já aplica e remove redução física do herói ao equipar/desequipar e é entendido por `_apply_damage_types`. Não criar um caminho de dano especial.

## Limites

Não altera a Armadura de Couro e Placas original, nem resistências de monstros ou outros tipos de dano.
