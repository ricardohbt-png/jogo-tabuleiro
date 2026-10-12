# Marcadores cooperativos nas masmorras

## Objetivo

Dar ao grupo uma forma rápida de coordenar alvos e posições no tabuleiro. O recurso deve ser temporário, fácil de entender e não pode interferir nas ações de combate, no clique direito de inspeção de monstros ou na névoa de guerra.

## Escopo aprovado

- O MVP funciona somente dentro de masmorras.
- O jogador pode marcar um inimigo ou uma casa com uma destas intenções: **Atacar**, **Perigo**, **Investigar** e **Mover**.
- Os outros heróis da mesma partida recebem as marcações em tempo real.
- A marcação não consome ação, movimento nem turno.
- A marcação é temporária e não é salva na campanha.
- A interação deve ser acessível por mouse, teclado e gamepad, conforme os controles já oferecidos pelo jogo.
- O botão direito permanece dedicado à inspeção detalhada de monstros.

## Experiência do jogador

1. O jogador abre o seletor de marcações por um controle visível no HUD ou por um atalho acessível.
2. Escolhe uma das quatro intenções.
3. Escolhe um inimigo ou uma casa válida no tabuleiro.
4. O jogo mostra um ícone legível sobre o alvo ou a casa e o mantém visível aos companheiros elegíveis.
5. O jogador pode substituir sua própria marca ao criar outra. A marca também desaparece ao expirar, quando seu alvo deixa de existir ou quando a partida encerra.

As categorias devem ter ícone e rótulo, para que a distinção não dependa apenas de cor. A paleta inicial pode usar vermelho para Atacar, âmbar para Perigo, ciano para Investigar e verde para Mover, desde que o contraste seja validado contra as cores de combate já presentes.

## Regras de validade e visibilidade

- Uma marca de casa só pode apontar para uma posição válida e visível ao jogador que a criou.
- Uma marca de inimigo só pode apontar para uma criatura existente e atualmente visível ao jogador que a criou.
- A marca não revela inimigos, posições nem áreas que o destinatário não poderia ver pelas regras normais de visão. A elegibilidade de cada destinatário deve ser avaliada pelo servidor, em vez de depender apenas de ocultação visual no cliente.
- Se um inimigo marcado morrer ou desaparecer da partida, a marca é removida.
- Cada jogador mantém no máximo uma marca ativa; uma nova substitui a anterior.
- As marcas expiram ao final da próxima rodada completa após sua criação. A implementação deve usar o contador de rodada autoritativo do servidor.
- Desconectar o dono remove sua marca. Sair da masmorra limpa as marcas daquela instância.
- O servidor limita a frequência de criação para impedir spam; a recusa não deve consumir turno nem gerar erro ruidoso.

## Integração técnica esperada

- O estado das marcações é efêmero e autoritativo no servidor da sala (`GameRoom`); não faz parte de saves ou do progresso da campanha.
- Mensagens específicas de criar, atualizar e remover marcação transportam categoria, autor e alvo estável (ID da criatura) ou posição do tabuleiro. O servidor valida remetente, partida, alvo, posição, visibilidade e limite de frequência antes de aceitar.
- A entrega é restrita aos jogadores conectados à mesma instância de masmorra e ainda elegíveis pela regra de visão.
- O cliente mantém um renderizador compartilhado para as vistas 2D e 3D, sem alterar a seleção de alvo, a mira de habilidades ou o clique direito.
- A origem da ação é representada visualmente, mas o protocolo não depende de nomes de herói para validar permissões.

## Abordagens consideradas

1. **Seletor de categoria seguido de alvo (recomendado):** funciona nas duas vistas e pode ser percorrido pelo teclado e gamepad; requer um controle pequeno no HUD.
2. **Menu de contexto sobre cada alvo:** reduz passos com mouse, mas conflita com inspeção, tem suporte ruim a gamepad e não oferece uma forma uniforme de marcar casas.
3. **Atalhos separados para cada categoria:** é rápido para teclado, mas ocupa combinações de teclas e exige remapeamento/suporte específico em cada controle.

O MVP usa a primeira abordagem. O clique direito não será reaproveitado. A implementação pode acrescentar acesso contextual secundário no futuro, sem mudar o fluxo principal.

## Fora de escopo

- Marcações na cidade ou no mapa-múndi.
- Chat, mensagens livres, planejamento de rota ou histórico de marcações.
- Custos de ação, efeitos de combate ou alterações de IA.
- Marcadores persistentes entre sessões ou campanhas.
- Marcadores para objetos escondidos, armadilhas não reveladas ou inimigos fora da visão.

## Critérios de aceitação

- Os quatro tipos podem ser criados em casas; Atacar também pode marcar uma criatura visível.
- Todos os destinatários elegíveis na masmorra recebem, substituem e removem marcações em tempo real.
- Destinatários que não têm visão da posição ou criatura não recebem informação que revele o conteúdo oculto.
- O marcador expira no limite definido, some em remoção do alvo/desconexão/saída da masmorra e nunca persiste em save.
- A criação não altera ações, turnos, movimento, seleção de alvo, inspeção do monstro ou mira de habilidades.
- O fluxo funciona em 2D, 3D, teclado e gamepad.
- A frequência de criação é limitada no servidor e mensagens inválidas não alteram o estado da partida.

## Decisões pendentes para revisão

- Aprovar o documento antes de elaborar o plano de implementação.
- No plano técnico, confirmar o ponto exato do ciclo de rodada usado para expiração e quais controles de teclado/gamepad encaixam sem conflito com os atalhos atuais.
