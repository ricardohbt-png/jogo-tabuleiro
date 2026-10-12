# Tutorial “Me mostra” — prévia visual com peão fantasma

Data: 2026-10-12. Estado: aguardando revisão do usuário.

## Objetivo

Fazer **Me mostra** encenar visualmente os passos principais do tutorial dentro
do mapa e das interfaces. A prévia deve mostrar o movimento, o equipamento e a
habilidade com uma representação fantasma, para o jogador compreender a ação e
depois executá-la por conta própria.

## Contexto atual

O cliente já tem um cursor local por clique e roteiros declarativos validados.
As rotas piloto abrem o inventário ou focam uma casa, uma habilidade e um
boneco, mas não animam a sequência. O halo do mapa já funciona em 2D e 3D e
respeita a névoa. O servidor segue como autoridade para aceitar ações e avançar
lições.

## Decisões aprovadas

- Usar uma prévia com peão fantasma no contexto do tabuleiro.
- O fantasma é visual e privado ao cliente que iniciou a demonstração.
- Nenhuma prévia move o herói real, altera inventário, gasta recursos, consome
  turno, ataca, rola dados, causa dano, conclui tarefas ou envia comandos de
  jogo ao servidor.
- A ação real continua manual. A lição só avança após o evento aceito pelo
  servidor.
- Um clique inicia uma animação curta da operação visual atual. Ao terminar,
  a demonstração espera a ação real; outro clique repete a prévia atual.
- Fechar ou pausar interrompe e remove o fantasma, preservando a operação para
  que o próximo clique a reapresente.
- O piloto conserva os três casos aprovados: equipar um item, mover no mapa e
  usar habilidade em boneco de treino. A cobertura de outras lições fica para
  depois da validação visual destes casos.

## Experiência

### Movimento

O painel identifica o passo da prévia. Um caminho visível liga a posição atual
do herói ao destino. Uma cópia translúcida da miniatura percorre esse caminho,
orientando-se conforme o sentido de cada trecho. Ao final, o destino pulsa e a
mensagem pede ao jogador que faça o movimento real. A prévia não seleciona a
casa nem emite a ação de movimento.

### Equipamento

Com o inventário aberto, um cursor ilustrativo parte de uma arma compatível na
bolsa e percorre até o slot correto. Um brilho no slot marca o destino. A
animação não arrasta item, dispara clique sintético nem altera o equipamento.
Se não houver item compatível visível, a prévia destaca o slot e informa que o
jogador deve selecionar o item manualmente.

### Habilidade

A demonstração destaca o botão da habilidade, indica o boneco permitido e
encena um breve movimento de aproximação/golpe com o fantasma e um efeito
visual sem resultado de combate. Não exibe acerto, crítico, dano ou consumo de
ação. Depois, deixa o alvo destacado e aguarda que o jogador arme e use a
habilidade de verdade.

O painel mantém o número da etapa e os controles reais disponíveis. O jogador
pode repetir a prévia, pausar ou fechar a lição. Uma recusa do jogo mantém a
etapa e permite reapresentar a animação.

## Arquitetura

### Roteiro e controlador

As fontes de tutorial continuam em `tools/tutorial_guia_*.py`; os arquivos
gerados continuam sendo atualizados pelos geradores existentes. Os roteiros
recebem apenas operações de prévia permitidas, como movimento, transferência
ilustrativa de item para slot e encenação de habilidade. Cada operação tem um
esquema de dados limitado, sem JavaScript, seletores arbitrários ou nome de
handler executável.

O servidor valida e encaminha esses dados junto ao passo existente, sem novo
protocolo de ação ou estado de progresso. `src/guiaDemonstracao.js` controla o
cursor e a sessão por clique. Uma camada cliente de animação calcula a pose e o
progresso temporal; `game.js` conecta essa camada aos renderizadores 2D/3D,
interfaces e ciclo de vida do tutorial.

### Renderização isolada

- **2D:** desenhar a miniatura fantasma como camada visual do mapa, sem gravá-la
  no estado recebido nem na lista de peões.
- **3D:** exibir uma cópia visual na cena existente, com materiais próprios
  translúcidos e raycast desabilitado. Remover e liberar a cópia ao terminar,
  pausar ou invalidar a prévia.
- **Interface:** animar um cursor decorativo entre os elementos reais; não
  sintetizar `pointer`, `click`, teclado ou gamepad.
- **Atualização:** reutilizar o ciclo de renderização existente e manter um
  único ciclo temporário por demonstração; sempre limpar o frame agendado e os
  objetos ao sair da sessão.

A posição e o alvo vêm do estado atual do cliente. A rota de movimento deve
usar casas válidas e visíveis; nenhum trecho escondido pode ser revelado. Se o
estado mudar de modo que origem, alvo ou caminho deixem de ser válidos, a
animação para e a instrução fica disponível para nova tentativa.

### Isolamento e autoridade

A demonstração não altera `GS.gameState`, entidades de jogo, inventário ou
mensagens WebSocket de ação. O servidor não recebe eventos de prévia como
movimento, ataque, magia ou equipamento. Só os eventos reais já existentes
podem avançar a lição. A miniatura fantasma não participa de colisão,
seleção, visibilidade de outros jogadores ou cálculo de combate.

## Falhas e ciclo de vida

- Alvo ausente ou incompatível: parar a animação e reaplicar a orientação
  textual/halo atual.
- Alvo fora da visão: não desenhar caminho nem fantasma que revele sua posição.
- Fechar, pausar, trocar herói, trocar de lição ou sair do tutorial: parar o
  ciclo visual e remover objetos, mantendo o cursor somente nos casos de
  pausa/fechamento já aprovados.
- Redimensionar a janela ou trocar 2D/3D: recomputar a representação visual sem
  reiniciar ou concluir a lição.
- Trocar idioma: preservar a posição da prévia e redesenhar os textos
  localizados.
- Falha ao clonar a miniatura: usar uma silhueta translúcida padrão e manter a
  instrução funcional.

## Validação e critérios de aceite

### Testes automatizados

1. Uma operação visual toca uma vez por clique; repetir no limite da ação toca
   a prévia novamente sem aumentar o cursor nem emitir comando de jogo.
2. Pausar/fechar cancela a animação e remove todos os objetos; retomar reaplica
   a mesma etapa sem adiantar o roteiro.
3. Passo novo aceito pelo servidor termina a sessão antiga; a próxima prévia
   só começa em um novo clique.
4. As operações novas são aceitas somente com payloads válidos e são rejeitadas
   quando incluem chamada ou campo não permitido.
5. Testes verificam explicitamente que a camada de prévia não invoca envio de
   movimento, ataque, magia ou inventário.
6. Caminhos e alvos fora da visão não são desenhados.

### Revisão manual em jogo

Executar os três pilotos em 2D e 3D: inventário/equipar, movimento e habilidade
no boneco. Conferir que a cópia usa a miniatura correta, o jogador entende a
ordem ao assistir uma vez, controles mouse/teclado/gamepad permanecem
utilizáveis e as ações reais só avançam depois da aceitação do servidor.
Repetir, fechar e retomar cada prévia; conferir redimensionamento e troca de
idioma; observar que nenhuma trilha, efeito ou entidade fantasma fica presa.

## Fora de escopo

- Executar comandos reais em nome do jogador, inclusive para “mostrar” uma
  ação.
- Automatizar lições completas ou avançar etapas sem ação aceita.
- Mudar regras, alvos, recompensas ou requisitos do tutorial.
- Ampliar a todos os tutoriais antes da aprovação do piloto.
- Sincronizar o fantasma com outros jogadores ou apresentar replay persistente.

## Relação com a demonstração assistida existente

Esta especificação amplia a demonstração assistida aprovada em
`docs/superpowers/specs/2026-10-12-tutorial-me-mostra-demonstracao-assistida-design.md`.
O cursor por clique, o inventário seguro e o progresso autoritativo permanecem
como base. Os novos roteiros acrescentam uma prévia encenada à operação atual;
eles não substituem nem automatizam as ações manuais.
