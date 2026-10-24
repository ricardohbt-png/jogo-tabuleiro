# Miniatura 3D de Gilo — proposta

## Intenção

Criar uma miniatura 3D própria de Gilo a partir de `assets/models3d/monstros/bandido.glb`, aproximando-a da arte `assets/pawns/monstros/gilo_dedos_sujos/gilo_dedos_sujos.png`: roupas em marrom mais escuro, duas bestas de mão e chapéu medieval de couro. O capuz existente permanece sob o chapéu.

## Escopo

- Criar `assets/models3d/monstros/gilo_dedos_sujos.glb` como cópia derivada; preservar o GLB do Bandido.
- Recolorir roupa e couro sem alterar rosto, proporções ou detalhes não relacionados.
- Remover as adagas da cópia e substituir por uma besta de mão em cada mão.
- Acrescentar o chapéu de couro inspirado na imagem de Gilo, mantendo o capuz sob ele.
- Renderizar prévias de frente e costas para conferência visual.
- Vincular o modelo à ficha oficial de `gilo_dedos_sujos` e ao catálogo do editor, preservando imagem 2D, atributos, habilidades e equipamento da ficha.
- Reproduzir a calibração visual do Bandido no jogo: multiplicador de escala 1,05, orientação da frente no sentido do movimento e mesma centralização/apoio na base da casa.

## Abordagens consideradas

1. **Edição 3D da cópia (recomendada):** manter o corpo e a silhueta do Bandido, recolorir a textura e editar/adicionar geometria para as duas bestas e o chapéu. É a opção que mostra os objetos corretamente em diferentes ângulos.
2. **Pintura projetada na textura:** pintar as armas e o chapéu na textura existente. É mais simples, mas deixa a geometria das adagas e do capuz visível e distorce os novos detalhes quando a miniatura gira.

## Limites e decisões do autor

- A malha original do Bandido é única; a remoção geométrica das adagas precisa ser inspecionada durante a edição. A cópia não deve alterar a malha original.
- O resultado pode simplificar detalhes da arte 2D para caber na escala de uma miniatura de tabuleiro.
- A escolha de manter o capuz sob o chapéu veio do usuário; a edição 3D da cópia foi aprovada.
- Não alterar ficha (exceto o caminho `model3d`), comportamento, imagem 2D ou outros assets do Bandido.
