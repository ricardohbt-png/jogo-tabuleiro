# Desfazer movimento e Esperar — design

Controle do turno para o jogador, agora que a posição vale bônus (direção, costas, flanco).

## Desfazer movimento
- Cada comando de andar guarda um ponto de retorno (ficha do herói + impressão digital do mundo).
- Desfazer volta ao ponto anterior (posição, direção, movimento, fome/sede da 1ª casa) e vale para vários comandos em ordem inversa.
- Só se NADA além do movimento mudou: a ficha só pode diferir nas chaves do próprio passo e o mundo
  (névoa, salas, monstros alertas, baús, itens, armadilhas reveladas) tem de ser o mesmo. Genérico e conservador.
- Só na vez do herói, fora da janela dos servos e do Último Esforço; nunca Mestre/mesa de teste.

## Esperar
- Move o herói para o fim da fila da rodada. Só no começo da vez (sem andar/agir), 1×/rodada, e se alguém ainda age depois.
- O preparo do início do turno (veneno, recargas, movimento) roda uma só vez: a reativação o pula.

## Fora
Monstros esperarem/desfazerem, desfazer ataques/ações, ataque de oportunidade, atalho de controle.
