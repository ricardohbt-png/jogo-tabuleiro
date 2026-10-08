# Variedade de equipamento do Goblin Combatente

## Objetivo

Fazer cada Goblin Combatente surgir com equipamento variado, usar a arma sorteada no combate, mostrar esse equipamento na miniatura 2D e 3D e deixar no loot o que ainda estiver carregando. A mudança é exclusiva do `goblin_combatente`; o Goblin Dual conserva a adaga auxiliar e o Arremesso.

## Regras aprovadas

- Sortear uma arma principal com probabilidade igual entre seis opções: `lanca_curta`, `bordao`, `cajado_madeira`, `shortsword`, `maca` e `machado_basico`.
- Usar `cajado_madeira`, não o Cajado Arcano. Manter o bônus de ataque atual do combatente (+2) e aplicar o dado, categoria e alcance corpo a corpo suportados pelo catálogo. A lança curta causa `1d6`; o golpe mantém a regra de crítico padrão dos monstros.
- Sortear o escudo independentemente da arma: 10% de chance de equipar o Escudo Pequeno (`escudo_p`), apresentado visualmente como de madeira. O equipamento dá +1 de CA ao goblin pelo aplicador de equipamento existente.
- Sortear uma Poção de Cura Pequena (`health_potion_small`) independentemente dos outros itens: 5% de chance. A IA existente tenta usá-la ao chegar a 50% dos PV ou menos; o uso consome a poção e mantém o ataque do turno.
- Remover a adaga e a habilidade `Arremesso` do Goblin Combatente. O código atual também as aplica a esse tipo; corrigir essa divergência. Não alterar o Goblin Dual.
- Ao morrer, o Combatente deixa sua arma principal e o escudo se o tiver equipado, além da poção somente se ainda estiver na bolsa. Não incluir drop de adaga para este tipo. Preservar a tabela de ouro e os outros drops existentes.

## Apresentação 2D e 3D

Criar doze variantes completas de aparência: cada uma das seis armas com e sem escudo. O servidor seleciona as chaves de imagem 2D e modelo 3D correspondentes às mesmas escolhas que alimentam os ataques e o loot. As variantes mantêm o porte, a pose, as cores e o enquadramento atuais do Goblin Combatente; a arma e a presença do escudo são as diferenças visuais.

Antes de produzir as doze variantes, validar uma amostra 2D e uma 3D em tamanho de peão. Se a amostra não preservar o estilo e a escala, ajustar o método de produção antes de completar os demais arquivos. A Poção não altera a miniatura.

## Fluxo técnico

1. Sortear equipamento no início da criação da instância em `make_monster`, antes de aplicar equipamento e construir os ataques.
2. Usar IDs estáveis do catálogo para nome, dado, categoria e item entregue ao loot; guardar as escolhas na instância do monstro para manter estado consistente durante o encontro.
3. Construir o ataque do Combatente a partir da arma sorteada, preservando seu bônus atual e sem modificar as IAs de outros tipos.
4. Inserir os itens equipados e a poção na instância de inventário existente para aproveitar o aplicador de equipamento, a IA de cura e o transporte de loot do servidor.
5. Selecionar as variantes 2D/3D por chaves derivadas da arma e do escudo, usando os caminhos de renderização atuais.
6. Atualizar a documentação de arquitetura `CLAUDE.md` com o comportamento novo e as fontes autoritativas.

## Verificação

- Cobrir de forma determinística as seis armas e as combinações com/sem escudo; confirmar que os ataques usam o item sorteado e o bônus +2.
- Confirmar as rolagens independentes de 10% e 5%, o bônus de CA do escudo e que a poção é usada apenas no limite da IA.
- Confirmar o loot da arma, do escudo e da poção não consumida; confirmar que o Combatente não deixa adaga e que o Goblin Dual mantém adaga e Arremesso.
- Confirmar que as doze chaves de aparência resolvem a um PNG e a um GLB existentes e revisar uma amostra em 2D e 3D.

## Fora de escopo

- Alterar probabilidade, equipamento, ataque ou IA de outros goblins.
- Adicionar novas habilidades de arremesso ao Combatente.
- Dar ao Combatente as propriedades especiais de crítico das armas dos heróis; ele continua usando o crítico padrão dos monstros.
- Fazer a poção aparecer na aparência da miniatura.
