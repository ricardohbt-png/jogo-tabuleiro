# Caminho de pedras com largura ajustável

## Objetivo

Na ferramenta Chão, permitir escolher de 1 a 5 quadrados de largura antes de arrastar o Caminho de pedra na terra. O padrão é 1 quadrado, mantendo o comportamento atual. A prévia mostra todas as casas que serão pintadas; soltar confirma o trecho, enquanto Escape ou botão direito cancelam. Recuar o cursor encurta a prévia e o eixo dominante determina o sentido, como hoje.

## Aparência e mecânica

As casas selecionadas formam visualmente um único caminho de pedras contínuo, sem aparecer como várias faixas ou cruzamentos separados. Retas, pontas, curvas e cruzamentos devem se conectar, inclusive ao encontrar caminhos já existentes e caminhos de larguras diferentes. As pedras devem manter escala visual coerente. O resultado deve funcionar no editor e nos modos 2D e 3D do jogo.

Cada casa continua sendo chão de terra caminhável com a decoração existente; pintar outro piso ou parede remove a camada correspondente. Caminhos existentes e trechos de largura 1 preservam sua aparência e funcionamento. O mapa salva e recarrega sem perder o formato.

## Abordagens

Foi escolhida a composição de uma superfície contínua ao longo das casas selecionadas, adaptando bordas e conexões. Esticar a imagem de um único quadrado foi descartado porque ampliaria as pedras e prejudicaria o encaixe das curvas. A implementação deve reaproveitar os recursos visuais e a representação de terreno existentes quando possível.
