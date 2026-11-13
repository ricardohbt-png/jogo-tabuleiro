# Armadura Rúnica

## Objetivo

Transformar o saque-placeholder `armadura_runica` em uma armadura equipável e vendável, aproveitando a arte derivada da Armadura de Placas.

## Regras aprovadas

- Armadura de Placas aprimorada em +1: bônus de armadura +7 no total.
- Preço: 2.500 moedas.
- Exclusiva de Guerreiro e Paladino, como a Armadura de Placas.
- Ação principal: escolher Barreira Arcana ou Proteção contra Energia, sem consumir espaço de magia.
- O efeito escolhido dura exatamente 5 rodadas; a recarga compartilhada entre as duas opções é de 30 rodadas.
- Usa `assets/itens/armadura_runica.png` e fica disponível nos ferreiros de armadura das cinco cidades.
- O item mantém o ID `armadura_runica`, preservando o loot do Gigante Rúnico.

## Abordagens

- Duas habilidades concedidas pela armadura, com um cooldown e validação autoritativos no servidor. Escolhida: mantém cada proteção explícita no painel e reutiliza os executores de magia existentes.
- Um único botão com um modal de seleção. Não escolhido: acrescenta uma etapa de interface sem necessidade, pois as duas habilidades podem aparecer diretamente como opções.

## Limites

Não altera as regras gerais das duas magias, a Armadura de Placas comum nem a tabela de loot do Gigante Rúnico.
