# Céu e abismo sob pontes e penhascos

## Objetivo

Adicionar ao editor um material de piso que mostre céu distante e nuvens em
casas de terreno inferior, inclusive sob pontes. O material representa um
abismo: criaturas sem voo ativo não podem caminhar até ele; se forem empurradas
para uma casa dessas ou caírem nela, morrem automaticamente. Criaturas que
estejam efetivamente voando não caem enquanto permanecerem no ar.

## Abordagem

O abismo será um material especial de piso, aplicado pelo pincel e pelo
preenchimento de materiais já existentes. Pontes continuam sendo superfícies
independentes e elevadas sobre o piso que está abaixo. A altura real continua
vindo de `elevacoes` e `pontes`; o novo material identifica as casas que exibem
o céu e aplicam a regra de abismo.

O material será declarado em `server.py` como piso e marcado com metadado de
terreno próprio (por exemplo, `terreno: "abismo"`). Não usará `solido`: esse
campo representa bloqueio físico e impediria a resolução de empurrões e quedas.
O servidor será a autoridade da regra, enquanto a previsão de movimento do
cliente seguirá a mesma classificação.

## Edição e apresentação

- O catálogo exportado inclui o material na categoria de piso, com nome
  traduzido como **Céu/Abismo**.
- O autor pinta as casas inferiores com o seletor de piso ou o preenchimento
  já disponível. O material fica salvo no mapa pela estrutura existente
  `materiais["x,y"]`; mapas antigos não precisam de migração.
- No modo 2D, o piso usa azul de céu e nuvens suaves desenhadas de forma
  contínua entre as casas.
- No modo 3D, uma textura procedural correspondente aparece sobre a geometria
  do piso na elevação inferior. A ponte continua acima dela; o céu fica visível
  ao redor e através dos vãos existentes da ponte.
- O material só pode ser aplicado a chão/porta, seguindo a compatibilidade
  atual dos materiais de piso.

## Regras de movimento e morte

- Movimento voluntário a pé não pode terminar nem traçar caminho por uma casa
  de abismo. Cliente, servidor e IA tratam a casa como destino bloqueado para
  criaturas no chão. O jogo não oferece uma caminhada que leve a uma morte
  certa.
- Empurrões e outros deslocamentos forçados que terminem em uma casa de abismo
  causam morte automática para criaturas que não estejam voando.
- Criaturas voadoras podem cruzar e ocupar essas coordenadas enquanto
  permanecem efetivamente no ar, usando a regra de voo existente (`voo` ativo
  e altura acima do piso).
- Se o voo acabar ou a criatura for derrubada e ela cair sobre uma casa de
  abismo, a chegada ao piso causa morte automática. A altura não reduz esse
  resultado.
- A regra vale para heróis, monstros e outras criaturas móveis. A morte é
  processada pelo servidor e preserva o fluxo normal de cadáver/estado morto.
- Colocação inicial não pode deixar heróis ou criaturas não voadoras sobre o
  abismo. Uma ponte que cubra a coordenada é uma superfície superior válida e
  não conta como ocupação do abismo enquanto a criatura estiver no tabuleiro da
  ponte.

## Ressurreição de heróis

Na Ressurreição do clérigo, se o alvo morreu em uma casa de abismo, o servidor
usa a posição registrada do cadáver para procurar a casa segura mais próxima.
A casa de retorno precisa ser uma superfície válida, livre e não fatal:

- piso caminhável, ou uma casa coberta por uma ponte utilizável;
- fora do abismo quando não houver ponte sobre a coordenada;
- sem parede, porta fechada, decoração/material bloqueador ou ocupante vivo.

A busca é determinística e considera a ocupação no momento da magia. A animação
de ressurreição aponta para a casa escolhida. Se não houver destino seguro, o
alvo permanece morto e a magia não consome ação nem recursos. A ressurreição no
templo da cidade e a reanimação de monstros não mudam de regra nesta entrega.

## Compatibilidade e critérios de aceitação

- Catálogo, editor, salvamento/carregamento, render 2D, render 3D, pathfinding e
  movimento autoritativo reconhecem o novo material.
- Herói no chão não consegue caminhar para o abismo; empurrão para lá mata.
- Criatura efetivamente voando atravessa a casa; ao perder o voo e cair nela,
  morre.
- A IA terrestre não escolhe o abismo como rota voluntária.
- Ressuscitar uma vítima do abismo a coloca na casa segura livre mais próxima;
  sem destino, não consome os recursos da magia.
- Pontes continuam caminháveis na superfície superior mesmo quando o piso
  inferior tem o material de abismo.
- Mapas sem o material novo mantêm o comportamento atual.

## Escopo fora desta mudança

- Animação contínua das nuvens.
- Alteração da tabela de dano de queda para outros terrenos.
- Mudança na ressurreição realizada na cidade ou na reanimação de monstros.
