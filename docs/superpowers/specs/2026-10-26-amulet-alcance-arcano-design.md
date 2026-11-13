# Amuleto do Alcance Arcano

## Objetivo

Adicionar ao mercador o Amuleto do Alcance Arcano, por 400 moedas, usando `assets/itens/amulet.png`. Enquanto equipado, aumenta em uma casa o alcance de lançamento das magias com alcance positivo.

## Regras

- ID: `amulet_alcance_arcano`.
- Slot: par de acessórios (`item1`/`item2`), para coexistir com outros itens ativos.
- Efeito reversível: `spell_range: +1` enquanto equipado.
- Aumenta alcance de lançamento; não aumenta raio, lado, comprimento de cone ou área de efeito.
- Não se aplica a pergaminhos.
- O servidor valida o alcance; a prévia da mira do jogador mostra o mesmo alcance. A mira de monstros não recebe bônus.
- Preço: 400 moedas, disponível nos cinco mercadores.

## Fora de escopo

- Alterar o alcance de habilidades de classe, ataques, itens, pergaminhos ou magias de monstros.
