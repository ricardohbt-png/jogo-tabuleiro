# Chicote de Fogo — design

## Objetivo

Adicionar ao jogo uma arma mágica rara chamada **Chicote de Fogo**, usando o ícone já existente em `assets/itens magicos/chicote_flamejante.png`.

## Regras aprovadas

- Usa o perfil do Chicote atual: 1d4 cortante, Destreza, alcance 2, mão secundária e classes Bardo, Ladino, Paladino e Guerreiro.
- É mágico e concede +1 no acerto e +1 no dano.
- Um acerto crítico causa +1d6 de dano de fogo, além do dano normal do crítico. A faixa de crítico permanece normal; o d6 adicional é rolado uma vez.
- Cada acerto bem-sucedido aplica `Em Chamas` por `1d4` rodadas, incluindo ataques de mão principal, mão secundária e técnicas que acertem com a arma. O efeito causa 1 dano de fogo por rodada, não acumula dano, e um novo acerto renova a duração usando o maior valor, conforme `_aplicar_em_chamas`.
- Água ou uma ação pode apagar o fogo, respeitando as regras existentes para `em_chamas_rodadas`.
- Preço: 1.200 moedas. Raridade: Rara.
- Aparece no ferreiro de armas das cinco cidades e no catálogo do editor.

## Abordagem

Declarar a arma em `SHOP_WEAPONS` após gerar variantes de prata, para não criar uma variante prateada automática. Preservar `fire_on_hit`, `fire_crit_damage`, `magical`, `atk_bonus` e `damage_bonus` na compra e ao reequipar. Aplicar o estado de fogo em acertos e o d6 adicional em acertos críticos de mão principal, secundária e técnicas.

## Fora de escopo

Não criar dano de fogo instantâneo em acertos comuns, dano acumulável, efeito de fogo grego, faixa de crítico ampliada, animação dedicada ou alteração global do estado Em Chamas.

## Verificação

Revisão estática dos caminhos de catálogo, compra, ataque principal/secundário, estoque e documentação. Não adicionar nem executar testes sem pedido explícito.
