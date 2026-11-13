# Hidromel — design

## Objetivo

Adicionar Hidromel como bebida portátil multiuso, vendida nas cinco tavernas e elegível ao sorteio adicional de comida deixada por certos monstros. Usa `assets/itens/hidromel.png`.

## Regras

- Preço: 18 moedas; garrafa com 2 doses.
- Cada uso restaura 18 de fome e 18 de sede.
- Cada dose aplica −1 em Reflexos e −1 na CA por 10 rodadas. As cargas acumulam e cada uma expira 10 rodadas após o próprio uso.
- A garrafa é removida após a segunda dose.

## Abordagem

Adicionar efeito próprio `hidromel`, reutilizar o fluxo de dose por instância do Rum e manter temporizadores de penalidade separados. A redução de CA entra em `_player_effective_ac` pela quantidade de temporizadores ativos; assim não altera `p["ac"]` base nem o cálculo de equipamentos.

## Limites

Não altera Rum, Vinho ou cervejas. Não altera equipamentos nem penalidades de monstros.
