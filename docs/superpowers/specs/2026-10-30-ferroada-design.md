# Ferroada — ficha da arma mágica

## Intenção

Adicionar ao jogo o chicote farpado Ferroada, usando `assets/itens magicos/ferroada.png` e aproveitando a mecânica de Sangramento já usada pelas espadas do Sangramento.

## Regras aprovadas

- Arma mágica chamada Ferroada, à venda por 1.500 moedas.
- Usa o perfil do chicote: 1d4 cortante, Destreza, alcance 2, compatível com mão secundária.
- Concede +1 no acerto e +1 no dano.
- Cada acerto aplica a mecânica existente de Sangramento, sem limite por rodada; um crítico que aplique Sangramento também aplica Hemorragia.
- Crítico natural somente no 20, sem ampliar a faixa.
- Classes permitidas iguais às do Chicote de Fogo: Bardo, Ladino, Paladino e Guerreiro.

## Escopo

Cadastrar a arma no servidor, nas cinco lojas de armas, na localização do catálogo e na documentação; regenerar o catálogo do editor. Não criar uma mecânica de Sangramento nova nem alterar as regras compartilhadas.

## Abordagens consideradas

- Reutilizar `causa_sangramento` e o cálculo normal da arma do chicote, seguindo as espadas já existentes. Escolhida por já aplicar o efeito também em ataques da mão secundária e evitar duplicação de regras.
- Criar um efeito exclusivo da Ferroada com duração ou limite próprio. Rejeitada porque o pedido foi reutilizar a mesma mecânica das espadas.

## Verificação

Verificações estáticas de Python, JavaScript, JSON, presença nos cinco ferreiros, geração do catálogo e `git diff --check`. Não executar testes sem pedido explícito.
