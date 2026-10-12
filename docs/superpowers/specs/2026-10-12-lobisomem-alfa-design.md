# Lobisomem Alfa ND 6 — especificação de design

## Objetivo

Adicionar uma variante independente e mais poderosa do Lobisomem, com desafio
ND 6, regeneração que permite retornar após cair a 0 PV e duas formas de impedir
definitivamente esse retorno: um golpe letal de prata ou fogo acumulado que
reduza a zero o teto de regeneração. A miniatura deve ser reconhecível como a
mesma criatura, com pelo preto e olhos vermelhos.

## Ficha aprovada

- ID: `lobisomem_alfa`; nome: `Lobisomem Alfa`; ND: 6.
- 85 PV, CA 19, deslocamento 6 e bônus de ataque +8.
- Rotina de ataque: duas Garras (`2d6+5` cada) e uma Mordida (`2d8+5`). O dano
  médio máximo da rotina é 38 antes de considerar a chance de acerto.
- Regeneração: 5 PV no início do turno do Alfa.
- A ficha comum do Lobisomem permanece inalterada.

## Morte, retorno e dano elementar

- Ao cair a 0 PV, o Alfa entra em estado de regeneração e permanece na fila de
  iniciativa. No início do próximo turno, se ainda puder regenerar, retorna com
  1 PV; então a regeneração normal de 5 PV por turno fica sujeita ao teto.
- Um ataque com arma de prata que cause a queda a 0 PV encerra o estado de
  regeneração e causa morte definitiva. A vulnerabilidade atual à prata (dano
  dobrado) é mantida. Dano físico não mágico e sem prata continua reduzido à
  metade; dano de prata ou mágico que não seja letal apenas bloqueia a próxima
  cura passiva, conforme a regra do Lobisomem comum, sem marcar morte
  definitiva.
- Todo dano de fogo efetivamente aplicado ao Alfa soma-se a
  `lobisomem_alfa_dano_fogo`. Seu teto de regeneração é
  `max(0, max_hp - lobisomem_alfa_dano_fogo)`. Dano absorvido ou reduzido a zero
  não reduz o teto. Em um ataque de dano misto, só a parcela final de fogo
  reduz o teto; o valor físico ou de outro elemento não deve ser contado como
  fogo.
- Se o teto atingir 0, o Alfa não consegue retornar após cair a 0 PV. O fogo
  acumulado não mata instantaneamente uma criatura que ainda tenha PV: ele
  remove a capacidade de regenerar; a queda subsequente a 0 PV é definitiva.
- Se fogo levar o Alfa a 0 PV antes de zerar o teto, ele pode retornar enquanto
  o teto for maior que zero. Isto dá efeito à decisão de que o fogo deve
  consumir toda a reserva regenerativa para substituir a prata como meio de
  morte definitiva.
- Retorno, regeneração passiva, dano de fogo, dano de prata e morte definitiva
  devem funcionar no fluxo de iniciativa do jogo e no simulador “Testar como
  Mestre”. Um Alfa em regeneração a 0 PV continua sendo tratado como ator vivo
  para esses fluxos, mas não pode executar ataques enquanto estiver caído.

## Comportamento e miniatura

- O Alfa usa a IA agressiva, percepção por olfato e comportamento de recuo já
  existentes no Lobisomem comum.
- Criar um asset visual próprio a partir de
  `assets/models3d/monstros/lobisomem.glb`, sem sobrescrever o modelo base.
- O pelo do Alfa deve ficar preto, com olhos vermelhos claramente visíveis em
  escala de miniatura. Preservar geometria, pose e demais detalhes do original.
- Publicar o GLB em `assets/models3d/monstros/lobisomem_alfa.glb` e uma imagem
  PNG de miniatura própria em
  `assets/pawns/monstros/lobisomem_alfa/lobisomem_alfa.png`, para que o jogo use
  a mesma identidade visual no tabuleiro 3D, 2D e nos editores.

## Integração

- Cadastrar a nova ficha no bestiário nativo e atualizar o catálogo gerado do
  editor, sem alterar a definição original do Lobisomem.
- Ligar `image` ao identificador `lobisomem_alfa` e registrar seu modelo GLB na
  tabela de modelos do cliente.
- Garantir que o novo tipo seja reconhecido pelo editor de criaturas e possa
  ser adicionado a encontros/masmorras pelo fluxo normal.

## Critérios de aceitação

1. O catálogo expõe `lobisomem_alfa` como ND 6 com os PV, CA e ataques acima;
   a ficha comum continua ND 3 e sem alterações.
2. A sequência de ataques contém duas garras e uma mordida, com os bônus/danos
   definidos.
3. O Alfa regenera 5 PV por turno, respeita o teto após fogo e retorna de 0 PV
   apenas quando as regras de morte definitiva não se aplicam; golpes de prata
   ou mágicos não letais bloqueiam a próxima cura passiva.
4. Uma queda a 0 PV causada por prata é definitiva; uma queda após o teto de
   regeneração chegar a 0 por dano de fogo também é definitiva.
5. Fogo acumulado não causa morte instantânea quando ainda há PV; fogo antes
   do teto chegar a 0 pode levar a 0 PV e permitir retorno, conforme a regra.
6. O Alfa a 0 PV regenerando permanece na fila real e no simulador, sem agir
   enquanto estiver caído.
7. A miniatura do Alfa mostra pelo preto e olhos vermelhos em PNG e GLB; o
   modelo e a miniatura do Lobisomem comum permanecem inalterados.
8. A IA do Alfa mantém detecção de heróis invisíveis/ocultos e o comportamento
   atual de recuo e retorno à perseguição.

## Fora de escopo

- Alterar a ficha ou o visual do Lobisomem comum.
- Alterar o comportamento de regeneração/morte do Troll.
- Adicionar resistências, imunidades, habilidades ou regras de loot não
  especificadas acima.
