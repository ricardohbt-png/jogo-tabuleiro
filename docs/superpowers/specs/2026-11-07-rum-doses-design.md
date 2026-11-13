# Rum — design

## Objetivo

Adicionar Rum como consumível de três doses, vendido nas cinco tavernas e elegível para o sorteio adicional de comida deixada por certos monstros. A arte fica em `assets/itens/rum.png`.

## Regras aprovadas

- Cada uso restaura 15 de fome e 15 de sede.
- Cada dose usada aplica −1 em ataque e −1 em Reflexos por 10 rodadas; as penalidades se acumulam até −3 ao usar as três doses da mesma garrafa.
- Cada dose tem seu próprio temporizador de 10 rodadas; ao expirar, só remove a penalidade daquela dose.
- Uma garrafa tem 3 doses (`max_uses`/`uses_left`) e sai da bolsa após a terceira utilização.
- Preço de implementação: 30 moedas, uma unidade equivalente por dose ao Vinho (10 moedas).
- Itens de Rum em saques de comida são sorteados com o peso inverso ao preço, como as demais comidas transportáveis.

## Abordagens

Reusar diretamente o efeito `wine` foi descartado porque o estado existente do Vinho não acumula penalidades nem mantém tempos por dose. A abordagem escolhida é um efeito próprio `rum`, com os mesmos recursos recuperados, contagem de doses por instância e uma lista de expirações independentes. Isso mantém a regra atual do Vinho intacta.

## Limites

Não altera o Vinho ou as cervejas. Não cria penalidades em monstros; a lista de comidas de saque continua selecionando itens de jogador.
