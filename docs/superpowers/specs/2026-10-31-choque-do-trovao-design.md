# Choque do Trovão — design

## Objetivo

Adicionar a arma mágica **Choque do Trovão**, usando `assets/itens magicos/choque_do_trovao.png`.

## Regras aprovadas

- Martelo de guerra contundente: 1d8 + Força, crítico natural 20 triplica o dano.
- Arma mágica Muito Rara, +1 no acerto e no dano, mais 1d4 elétrico por acerto.
- Em um acerto crítico, se o alvo sobreviver ao dano, faz teste de Força CD 13; falha empurra uma casa na direção oposta ao portador. Obstáculos ou criaturas bloqueiam o movimento, sem dano de colisão.
- **Pulso do Trovão** usa ação principal e atinge todas as criaturas vivas nas oito casas adjacentes ao portador, incluindo aliados e excluindo o portador. Cada alvo faz Reflexos CD 13; falha sofre 2d6 elétrico e sucesso sofre metade.
- Recarga do pulso: 10 rodadas, guardada na instância equipada da arma.
- Preço: 2.500 moedas. Classes: Clérigo, Paladino e Guerreiro, iguais ao Martelo de Guerra.
- Disponível nos ferreiros de armas das cinco cidades e no catálogo do editor.

## Abordagem

Registrar a arma no catálogo `SHOP_WEAPONS`, preservando seus campos especiais ao comprar e reequipar. Acrescentar o empurrão no fluxo autoritativo de acerto crítico e uma ação concedida pela arma para executar o pulso; apresentar habilidade, recarga e descrições em PT/EN. Documentar o contrato em `CLAUDE.md`.

## Verificação

Revisão estática dos caminhos de compra/equipamento, combate, ação concedida, cinco estoques e catálogo do editor. Não adicionar nem executar testes sem pedido explícito.
