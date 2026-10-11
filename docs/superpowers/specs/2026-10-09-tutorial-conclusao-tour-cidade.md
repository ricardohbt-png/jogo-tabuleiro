# Conclusão do tutorial e tour da cidade

## Objetivo

Encerrar a missão do Campo de Treinamento com uma fala visual do Mestre de Armas e conduzir cada jogador a conhecer as lojas da cidade ao retornar.

## Experiência

- Quando `mission_complete_pending` aparecer na aventura identificada pelo servidor como `tutorial.tour_cidade`, o HUD de objetivos inclui um quadro curto de parabéns com o retrato existente `assets/portraits/mestre_de_armas_conclusao.png`. O botão e a confirmação de encerramento permanecem no mesmo fluxo.
- Ao confirmar o encerramento e voltar à cidade, o mapa abre um cartão do Mestre com a próxima parada destacada. O jogador clica no marcador para ver a explicação e abrir a interface real daquela loja.
- Paradas comerciais: Ferreiro (armas, armaduras, munição, reparo e venda), Mercador (itens, instrumentos, arremessáveis, venenos, pergaminhos e venda), Templo (compras e serviços) e Taverna (alimentos).
- Após explorar uma loja, o botão do tour fecha o modal comercial e avança ao próximo marcador. O jogador pode pular todo o tour a qualquer momento; pular ou concluir impede a abertura automática em retornos futuros.
- O cartão final apresenta Guilda (especializações e técnicas) e Caravana (mapa-múndi e viagens) como próximos destinos.
- O progresso do tour é guardado por conta no `localStorage`, incluindo a parada atual, para retomar após recarregar. O marcador esperado é escolhido dos pontos visíveis da cidade; tipos de loja que não existirem são ignorados.
- Todas as novas falas e rótulos existem em português e inglês. A mesma experiência funciona com mouse, teclado e gamepad, mantendo a ativação dos pontos existente.

## Limites

- O tour só começa depois da conclusão confirmada do Campo de Treinamento (`tutorial.tour_cidade` + `mission_complete_pending`), nunca por sair de outra masmorra.
- Não altera economia, estoque, permissões de compra, recompensas ou mecânica de encerramento.
- Não altera o tamanho/corte da janela de lição do tutorial.

## Arquivos

- `game.js`: capturar a conclusão do tutorial, compor o quadro de parabéns, administrar o tour e integrar os cliques às lojas existentes.
- `server.py`: identificar no payload do tutorial a aventura específica Campo de Treinamento.
- `game.css`: cartão, realce do marcador e ajustes responsivos do tour.
- `src/lang/tutorial.js`: textos do Mestre e controles do tour nos idiomas pt/en.
- `CLAUDE.md`: registrar o fluxo e persistência do tour.
