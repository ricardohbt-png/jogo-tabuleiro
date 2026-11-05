# Caminho de pedras largo — plano

**Objetivo:** Implementar o desenho aprovado em `docs/superpowers/specs/2026-11-04-caminho-pedras-largo-design.md`.

**Arquitetura:** O editor escolhe largura e calcula as casas da prévia e do trecho com a mesma função. A aparência deve conectar regiões largas sem alterar a representação caminhável de cada casa, e deve sobreviver ao salvamento e funcionar nas visualizações 2D e 3D.

**Tecnologia:** JavaScript, canvas, Three.js e dados de decoração existentes.

1. Testar o cálculo de casas para larguras de 1 a 5, movimentos nos dois eixos, arrastos reversos e limites do mapa; implementar a escolha de largura e preservar cancelamento e prévia.
2. Implementar a composição visual contínua e sua persistência, preservando o desenho anterior para caminhos existentes de uma casa; testar curvas, encontros e preenchimento.
3. Verificar renderização no editor e no jogo 2D/3D, salvamento e reabertura, sintaxe e regressões existentes; atualizar `CLAUDE.md`.
