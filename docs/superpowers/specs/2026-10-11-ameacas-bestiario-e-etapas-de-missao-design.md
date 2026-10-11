# Clareza tática — zonas de perigo, bestiário progressivo e etapas de missão

**Data:** 2026-10-11
**Projeto:** Legends for Hire
**Status:** Especificação para revisão do usuário
**Escopo aprovado no brainstorming:** somente as três melhorias abaixo; progressão de níveis/equipamentos entre campanhas fica fora.

## Objetivo

Reduzir a incerteza durante a partida sem revelar decisões futuras dos monstros:

1. alertar sobre áreas que um inimigo pode ameaçar;
2. permitir que o grupo aprenda as defesas e capacidades dos monstros com a experiência;
3. orientar a missão por uma sequência explícita de etapas criada no editor.

O servidor continua sendo a fonte autoritativa de regras e progresso. O cliente apresenta os dados em 2D e 3D, sem simular regras próprias.

## Estado atual relevante

- O hover de inimigo mostra nome, vida e CA; a prévia de ataque do herói já calcula chance de acerto e dano no servidor.
- A passiva **Conhecimento das Lendas** do Bardo revela a ficha completa do inimigo ao grupo enquanto houver um Bardo vivo. As especializações **Lendas por espécie** e **Lendas Supremas** são mecânicas de bônus de combate distintas e não devem ser alteradas por este trabalho.
- O HUD de objetivos, aberto/fechado com **O**, já apresenta objetivo principal, secundários e progresso das saídas alternativas. O servidor mantém os estados e avalia as condições de objetivo.
- O editor de masmorras já serializa objetivos principais e secundários. A lógica atual reconhece `kill_target`, `kill_all`, `reach_exit`, `all_heroes_at_exit`, `open_key_chest`, `rescue_prisoner` e `salas_obrigatorias`.

## 1. Zona de perigo ao focar um inimigo

### Comportamento

- Ao passar o mouse sobre um inimigo visível, o tabuleiro destaca as casas que ele poderia ameaçar, considerando movimento, alcance, obstáculos, linha de visão e footprint da criatura.
- A indicação é deliberadamente ampla: não mostra o alvo escolhido, o ataque preparado, nem garante que o monstro agirá naquela área. Uma legenda curta explica que se trata de perigo possível.
- A zona desaparece ao retirar o mouse do inimigo ou focar outro alvo. Teclado e controle recebem o mesmo comportamento ao focar/selecionar um inimigo.
- Só se calculam e exibem ameaças de inimigos que o jogador pode perceber. A zona nunca revela casas ou criaturas ocultas pela névoa.
- O desenho precisa acompanhar a grade nos modos 2D e 3D, sem alterar regras de movimento ou combate.

### Fonte e limites

- O cálculo usa as regras do servidor para movimentos e ataques possíveis. O cliente não deve prever a escolha futura da IA.
- A interface mostra uma área agregada para o inimigo em foco, sem marcadores por herói e sem dizer qual criatura poderia atingir cada casa.
- Ataques e habilidades cuja área não possa ser projetada fielmente não devem ser representados como uma área exata. A implementação deve incluir apenas geometrias verificáveis e indicar claramente qualquer cobertura parcial.

### Critérios de aceitação

- O mesmo inimigo em foco produz zonas equivalentes em 2D, 3D, mouse, teclado e controle.
- Mudar posição, bloquear linha de visão ou incapacitar o inimigo atualiza ou remove as casas ameaçadas.
- A indicação não expõe alvos, ações planejadas, inimigos ocultos nem informação fora da visão do jogador.

## 2. Conhecimento progressivo e bestiário global

### Regra de conhecimento

O bestiário pertence ao perfil do jogador, é compartilhado por seus heróis e persiste entre campanhas. Em partidas cooperativas, os abates obtidos pelo grupo contribuem para o bestiário dos participantes da partida. Os contadores são acumulados por ID estável de tipo de monstro, nunca pelo nome localizado.

| Abates confirmados do mesmo tipo | Nível conhecido | Informação liberada |
|---:|---|---|
| 15 | Observado | Imunidades, resistências e vulnerabilidades. |
| 30 | Estudado | Perfil de combate: ataques, tipos de dano, alcances, atributos e testes de resistência conhecidos. |
| 50 | Catalogado | Ficha de combate completa, incluindo habilidades especiais e CDs conhecidas. |

Os limites são cumulativos. Alcançar 30 inclui o conhecimento do marco de 15; alcançar 50 inclui os dois marcos anteriores.

### Relação com o Bardo

- Um Bardo vivo continua revelando imediatamente a ficha completa, sem exigir contagem de abates.
- O bestiário oferece uma alternativa permanente para os demais heróis à medida que o grupo derrota criaturas.
- As especializações de Lendas por espécie continuam concedendo seus bônus atuais; este sistema não os substitui nem os altera.
- Níveis de conhecimento devem ser distintos de bônus mecânicos: aprender a ficha não concede ataque, resistência, dano ou outro benefício numérico.

### Persistência e contagem

- A persistência é por perfil/conta, não por masmorra ou campanha, e não compartilha descobertas entre contas diferentes.
- O registro e a concessão de progresso são autoritativos no servidor; dados do catálogo/editor não são fonte de progresso de jogador.
- Só uma morte real confirmada pelo servidor conta. A implementação deve excluir modo de teste/editor e evitar duplicar a mesma morte em reconexões ou reprocessamento de estado.
- IDs de tipos existentes são a unidade inicial. Variantes só compartilham contagem se houver uma relação explícita de família; não inferir famílias pelo nome ou substring.

### Interface

- O hover continua conciso para consulta rápida.
- A ficha detalhada pode ser aberta deliberadamente por “Examinar”. Ela separa informações básicas, conhecidas pelo bestiário e reveladas pela passiva do Bardo.
- Ao atingir um marco, mostrar uma notificação curta e atualizar a ficha aberta, se houver.

### Critérios de aceitação

- Contagens e níveis sobrevivem a novas campanhas e são iguais entre os heróis do mesmo perfil.
- Uma criatura nova começa no nível 0; os marcos são liberados somente nos limites 15, 30 e 50.
- O Bardo vivo continua revelando tudo imediatamente, sem alterar o contador nem os bônus de Lendas.
- Nomes traduzidos, variantes sem vínculo explícito e mortes duplicadas não corrompem ou fundem contadores.

## 3. Sequência de próximos passos no editor de masmorras

### Edição

- Adicionar ao painel de objetivos uma lista de etapas que o autor pode adicionar, remover e reordenar.
- Cada etapa contém texto de instrução e uma condição selecionada entre os tipos de objetivo que o servidor já avalia.
- O texto da etapa deve ter conteúdo em português e inglês para não introduzir texto sem tradução no HUD.
- O editor valida condições incompletas, IDs duplicados e a correspondência da última etapa com o objetivo principal.
- A sequência é opcional. Masmorras existentes sem etapas mantêm exatamente o comportamento atual.

### Execução e HUD

- O servidor calcula os estados `done`, `active` e `locked` e envia a sequência com o estado da missão. O cliente apenas renderiza.
- Só a etapa ativa é destacada; anteriores aparecem concluídas e as futuras ficam visualmente secundárias. O HUD continua acessível com **O**.
- Etapas avançam por condições reais do jogo; não há botão manual de avanço.
- Se a condição de uma etapa já estiver satisfeita quando ela se tornar ativa, o servidor a conclui e avança automaticamente, evitando bloqueios por ações realizadas antes da etapa ser destacada.
- A última condição deve corresponder ao objetivo principal existente. A conclusão da missão, recompensas, objetivos secundários e progresso de saídas continuam usando as regras atuais.
- As etapas não concedem recompensas próprias. Somente os objetivos principal e secundários atuais continuam concedendo recompensas.

### Compatibilidade e validação

- O formato atual `objectives.primary` e `objectives.secondary` é preservado. A sequência é um campo opcional adicional no JSON da masmorra.
- O editor e o servidor validam a sequência. Uma sequência inválida não pode ser salva nem iniciar uma missão.
- O cliente não calcula avanço por texto ou por leitura de narrativa; o estado do servidor é a fonte única de conclusão.
- O snapshot gerado do catálogo/editor não é fonte: mudanças futuras devem partir do editor e dos dados-fonte autoritativos.

### Critérios de aceitação

- Uma masmorra sem sequência carrega e conclui como antes.
- Uma masmorra com sequência apresenta a mesma etapa ativa para todos os jogadores e avança após a condição ser cumprida.
- Reordenar etapas no editor persiste após salvar e reabrir o arquivo.
- A última etapa nunca contradiz o objetivo principal, e a missão não concede recompensas duplicadas.
- Condições já satisfeitas antes da ativação não causam travamento.

## Fora de escopo

- Persistir níveis, equipamentos ou inventário dos personagens entre campanhas.
- Alterar bônus da linha de especializações Lendas do Bardo.
- Exibir a ação, alvo ou plano futuro exato de um monstro.
- Criar novos tipos de objetivo, novas regras de combate ou novas habilidades de monstro.
- Refazer o HUD inteiro ou remover os objetivos secundários e o progresso de saídas.

## Riscos a revisar no plano de implementação

1. A zona de perigo pode ficar grande demais em criaturas com movimento/alcance amplo; verificar legibilidade e custo de cálculo antes de ampliar para toda habilidade especial.
2. Dados globais do bestiário precisam de persistência server-side, migração segura e deduplicação de mortes; o cliente não pode conceder abates.
3. O editor serializa objetivos campo a campo; a sequência precisa sobreviver ao ciclo carregar → editar → salvar, além de manter os mapas antigos válidos.
4. Condições de etapa precisam ser avaliadas em transições reais de estado e não apenas em eventos de UI, para evitar progresso perdido por reconexão.
