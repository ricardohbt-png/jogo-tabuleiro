# Munição Mágica — design

## Objetivo

Adicionar flechas e virotes mágicos consumíveis que melhoram acerto e dano dos ataques à distância, com versões +1 e +2.

## Regras

- Cada pacote contém 10 projéteis e cada ataque à distância consome um, mesmo quando erra.
- A versão +1 concede +1 no acerto e +1 no dano; custa 50 moedas por pacote.
- A versão +2 concede +2 no acerto e +2 no dano; custa 120 moedas por pacote.
- Flechas são aceitas por arcos e usam `assets/itens magicos/flechas_magicas.png`; virotes são aceitos por bestas e usam `assets/itens magicos/virotes_magicos.png`.
- A munição mágica torna o dano físico do disparo mágico para superar resistência a armas não mágicas.
- Ambos os tipos são consumidos por ataques normais e Disparo Duplo, respeitando a seleção e a prioridade de munição existentes.
- Os quatro itens aparecem no estoque de munição dos cinco ferreiros e no catálogo do editor, com nomes e descrições em português e inglês.

## Abordagens

- Reutilizar `SHOP_AMMO`, `RANGED_AMMO` e o fluxo de resolução de projéteis, acrescentando bônus próprios à munição.
- Transformar cada munição em arma independente ou criar uma habilidade de encantamento; isso duplicaria os fluxos e não preservaria o consumo por projétil.

Escolhida a primeira abordagem por encaixar no sistema de munição existente.

## Fora de escopo

- Não alterar o preço ou os efeitos da munição explosiva, de prata ou incendiária.
- Não alterar os ataques de monstros nem conceder bônus permanentes à arma.
