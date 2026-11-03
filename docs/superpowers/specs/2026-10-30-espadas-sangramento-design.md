# Espadas do Sangramento — design

## Objetivo

Adicionar duas armas mágicas ao jogo usando `assets/itens magicos/espada_vorpal.png`: uma Espada Longa do Sangramento e uma Espada Bastarda do Sangramento.

## Regras aprovadas

- Espada longa: 1d8 cortante, +1 no acerto e dano, 1.500 moedas, raridade Rara.
- Espada bastarda: 1d10 cortante, +1 no acerto e dano, 2.000 moedas, raridade Muito rara.
- Ambas mantêm crítico natural em 19–20 e são restritas a Guerreiro e Paladino, como suas armas-base.
- Cada acerto bem-sucedido aplica o Sangramento atual do jogo. Acertos críticos também aproveitam a Hemorragia aplicada pelo fluxo atual. Não se altera a progressão global, duração, dano ou imunidades do Sangramento.
- Ambas aparecem no estoque `ferreiro_weapon` das cinco cidades, no catálogo do editor e nas traduções PT/EN.

## Abordagem

Registrar armas completas em `SHOP_WEAPONS` depois da geração automática de variantes de prata, para não criar cópias de prata acidentais. Reutilizar a imagem fornecida como ícone. Preservar `magical` e `causa_sangramento` ao comprar a arma e guardá-la na bolsa.

## Fora de escopo

Não criar efeitos novos de Sangramento, cooldown, teste de resistência ou animação dedicada; não mudar outras armas ou o preço global do Sangramento.

## Verificação

Validar sintaxe Python/JavaScript, integridade JSON do estoque, presença dos IDs em todas as lojas, catálogo exportado e `git diff --check`. Não rodar testes automatizados sem pedido explícito.
