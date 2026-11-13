# Portão levadiço — desenho

## Intenção

Adicionar ao tabuleiro uma decoração de castelo que também funcione como porta nativa. O portão pode ser levantado e abaixado em combate; abaixá-lo sobre uma criatura na passagem cria um perigo de esmagamento e aprisionamento.

## Abordagens consideradas

1. Decoração estática nas versões levantada e abaixada: simples, mas sem operação durante a partida.
2. Porta nativa que só pode abrir: reutiliza as regras atuais, mas não permite fechar a passagem novamente.
3. **Porta nativa operável nos dois sentidos (escolhida):** mantém as regras das salas e condições de porta, acrescentando estado levantado/abaixado e a ação de operar o portão.

## Regras acordadas

- O portão ocupa o vão de uma porta nativa (`DOOR`); levantado deixa passar, abaixado bloqueia movimento e linha de visão.
- Um herói adjacente, de qualquer lado, pode operar o portão. Levantar ou abaixar consome uma ação principal.
- Levantar não causa dano. Se o portão for abaixado com uma criatura no vão, ela faz Reflexos CD 13.
- Sucesso: sofre metade do dano rolado de 4d6 e é movida um quadrado para um dos lados do portão, antes ou depois.
- Falha: sofre 4d6 de dano físico e fica presa no vão. A próxima ação principal fica comprometida com uma tentativa de escapar com Força CD 16.
- Sucesso no teste de Força: a criatura sai para um quadrado adjacente livre, antes ou depois do portão, sem dano adicional.
- Falha no teste de Força: continua presa, sofre 1d6 de dano físico naquela rodada e tenta escapar novamente usando a próxima ação principal.
- O efeito se aplica a qualquer criatura atingida, inclusive aliados. Não há dano extra se a casa de saída estiver bloqueada.
- Fechar um portão já aberto bloqueia novamente a passagem e a linha de visão, mas não volta a trancar ou ocultar a sala, nem coloca monstros de volta em dormência. As condições existentes de abertura da porta continuam valendo.

## Objetivos e limites

- Criar miniaturas PNG e GLB do portão levantado e abaixado, com fonte Blender reutilizável.
- Integrar o estado visual e a interação à porta nativa, mantendo a autoridade de movimento, dano, salvamento e aprisionamento no servidor.
- Usar uma casa ou um grupo de casas contíguas de porta conforme a largura escolhida, permitindo operar de ambos os lados.
- Não adicionar dano ao levantar, dano recorrente sem falha no teste de Força, ou dano de colisão quando a saída adjacente estiver bloqueada.
- Não fazer o fechamento reverter o destrancamento, exploração ou alerta de sala já ocorrido.

## Pontos para a implementação

- A CD do teste de Força, os dois estados e o vínculo com a sala/condição da porta devem persistir no salvamento e sincronizar para todos os clientes.
- O teste de Força usa a ação principal da rodada seguinte. Cada tentativa malsucedida aplica 1d6 uma vez naquela rodada; nova tentativa apenas na ação principal seguinte.
- O deslocamento escolhe uma das casas imediatamente antes ou depois do portão. Se ambas estiverem bloqueadas, a criatura não se desloca e continua presa, sem dano adicional por colisão.
- Os valores e regras deste desenho refletem as escolhas feitas pelo usuário; a implementação visual, a entrada de interação e os casos de saída bloqueada ainda precisam ser confirmados no plano.

## Aditivo: portão levadiço com largura ajustável

### Intenção

Permitir que o Mestre escolha a largura do portão no editor, cobrindo uma ou mais casas contíguas de `DOOR`, e conservar uma única interação e um único estado para a grade inteira.

### Abordagens consideradas

1. **Ampliar apenas o modelo:** visualmente maior, mas bloqueio e esmagamento continuariam limitados à casa original; não atende ao pedido.
2. **Várias portas independentes adjacentes:** reutiliza a configuração atual, mas permite estados e ações separados e pode aplicar o dano por trecho; não funciona como uma grade única.
3. **Um portão nativo agrupado com largura selecionável (escolhida):** o Mestre arrasta pelo vão para selecionar uma ou mais casas `DOOR` contíguas; uma ação controla todas as casas selecionadas. Exige ampliar editor, estado de partida, bloqueio, dano e renderização.

### Regras e limites

- O Mestre define o vão arrastando do primeiro ao último tile `DOOR` contíguo. O comprimento é a quantidade selecionada, sem um tamanho fixo; largura mínima de uma casa mantém portões antigos e permite trechos estreitos.
- Todas as casas selecionadas devem estar alinhadas, ser `DOOR`, ter orientação compatível e representar o mesmo vão nativo. O editor rejeita seleção com lacunas, paredes, portas incompatíveis ou condições/salas conflitantes.
- O grupo tem uma única âncora estável para identidade, interação e estado salvo: o primeiro tile na ordem `(y,x)`, independentemente do sentido do arraste. Interagir com qualquer trecho a até uma casa opera a grade inteira e consome uma ação principal. Levantado, o vão todo permite passagem; abaixado, o vão todo bloqueia movimento e linha de visão.
- Ao abaixar, cada criatura viva que ocupe qualquer parte do vão resolve Reflexos CD 13 contra 4d6 físico uma única vez, ainda que seu footprint cubra várias casas selecionadas. Sucesso causa metade e tenta movê-la para uma casa legal antes ou depois do portão; falha causa dano integral e a prende. As regras de escape Força CD 16 e 1d6 na falha permanecem as mesmas.
- O deslocamento move a criatura inteira usando as regras atuais de footprint e colisão. Se não houver saída legal, ela permanece presa; não recebe dano adicional de colisão.
- Portões nativos já existentes, que ocupam uma casa, continuam compatíveis e mantêm seu tamanho e comportamento.
- A representação visual deve cobrir todas as casas selecionadas como uma grade contínua nos modos 2D e 3D, sem renderizar grades sobrepostas nem dividir a interação.

### Pontos técnicos a resolver na implementação

- O editor precisa criar, validar, girar, salvar e carregar o grupo como uma unidade; o arraste seleciona um segmento reto e contíguo de portas compatíveis.
- Servidor e cliente precisam compartilhar a mesma lista de casas do grupo para bloqueio, linha de visão, alvos, movimentação, interação e estado persistido.
- O estado levantado/abaixado deve ser serializado por grupo; mapas antigos com `door_styles` por casa continuam sendo interpretados como portões unitários.
- A grade 3D/PNG precisa ser dimensionada ao vão selecionado, respeitando orientação e escala de tabuleiro.
