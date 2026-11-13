# Plano: Montaria do Cavalo de Sela

## Resultado

Implementar o desenho aprovado em `docs/superpowers/specs/2026-10-29-montaria-cavalo-sela-design.md`, preservando o estado local existente.

## Tarefas

1. Mapear ciclo de turno, movimento, ataques/áreas, serialização e renderização do cavalo; definir campos de vínculo que sincronizem sem atravessar salas.
2. Implementar no servidor montar/desmontar/Disparada com validações de turno, adjacência, ação bônus, cooldown de quatro rodadas e vínculo autoritativo.
3. Integrar montaria ao movimento normal: orçamento do cavalo com bônus do cavaleiro, co-ocupação exclusiva do par, hazards e bloqueios preservados; suspender IA do cavalo montado e desmontar em morte/saída.
4. Preservar identidade de alvo único e atingir o par em dano de área; atualizar resolução e serialização conforme necessário.
5. Integrar controles e prévia no cliente, renderizar o PNG sob o cavaleiro e sincronizar o estado em Solo/Multiplayer/reconexão.
6. Atualizar documentação de arquitetura; revisar diff e executar apenas verificações estáticas, sem testes automatizados.

## Critérios de conclusão

- Servidor valida e controla todos os estados e custos da montaria.
- Movimento normal, caminhos, terreno, armadilhas e bloqueios mantêm os validadores existentes.
- Montar, desmontar e Disparada consomem uma única ação bônus; Disparada duplica o orçamento base sem acumular multiplicativamente e mantém recarga no cavalo.
- Ataques de alvo único atingem o ID selecionado e áreas atingem cavalo e herói.
- Alterações locais não relacionadas permanecem intactas.
