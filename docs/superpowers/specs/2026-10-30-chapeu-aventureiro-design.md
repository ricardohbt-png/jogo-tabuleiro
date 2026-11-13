# Chapéu do Aventureiro

## Intenção

Adicionar ao jogo um equipamento de cabeça não restrito por classe, com foco em exploração e prontidão para o combate, usando o ícone já criado.

## Regras aprovadas

- ID: `chapeu_aventureiro`; espaço: `head`; preço: 120 moedas.
- Enquanto equipado, concede `vision: +1` e `initiative: +1`.
- Qualquer classe pode equipá-lo.
- Ícone: `assets/itens/chapeu_aventureiro.png`.
- Disponível nos cinco estoques de mercadores.

## Integração

O servidor é a fonte autoritativa do item. Os efeitos existentes de visão e iniciativa são aplicados pelo fluxo normal de equipamento; não é necessário criar regras especiais. Regenerar as traduções do catálogo e o catálogo do editor, e registrar o item em `CLAUDE.md`.

## Fora de escopo

Não alterar bônus de outros chapéus, equilíbrio de classes, animação/visual de equipamento no peão, nem adicionar efeitos novos.
