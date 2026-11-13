# Slots de munição nas aljavas

## Objetivo e regras

Substituir o aumento geral de capacidade das pilhas da bolsa por espaços próprios em cada aljava equipada, seguindo o modelo dos bolsos do cinto. A mini aljava ocupa um espaço de item e oferece um slot; a pequena e a grande ocupam a mão secundária, no lugar do escudo, e oferecem respectivamente dois e três slots. Cada slot armazena até 40 projéteis de uma mesma pilha compatível de flechas ou virotes, incluindo variantes especiais. Aljavas equipadas simultaneamente oferecem seus próprios slots.

A munição permanece dentro da aljava ao desequipá-la e fica inacessível até ela ser equipada novamente. Os ataques com armas compatíveis devem poder consumir munição das aljavas equipadas, respeitando as preferências de munição existentes. O limite normal das pilhas na bolsa volta a ser 10. Pilhas antigas acima desse limite são preservadas integralmente, sem aceitar novos projéteis enquanto estiverem no limite ou acima dele.

## Abordagens

Foi escolhida a abordagem de armazenar os slots e seus conteúdos no próprio item da aljava, como no cinto: isso preserva o conteúdo ao mover, desequipar e reequipar o item. Acrescentar posições à bolsa comum foi descartado porque não acompanha naturalmente cada aljava ao desequipá-la.

## Limites e implementação

A mudança não concede munição nem altera os preços. O servidor deve validar capacidade, tipo e movimentação; a ficha deve apresentar os slots e permitir movimentar as pilhas. Atualizar as descrições e os catálogos correspondentes, manter compatibilidade com jogos salvos e verificar movimentação, disparos e preservação do conteúdo.
