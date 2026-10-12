# Tutorial “Me mostra” — demonstração assistida por etapas

Data: 2026-10-12. Estado: aguardando revisão do usuário.

## Objetivo

Transformar **Me mostra** em uma orientação interativa que abre interfaces úteis,
destaca controles e alvos e acompanha cada lição até o jogador realizar a ação
solicitada. O tutorial deve ficar fácil de seguir sem executar ações de jogo pelo
jogador.

## Decisões aprovadas

- Um clique em **Me mostra** avança uma etapa visual segura: pode abrir uma tela
  ou inventário e destacar o próximo item, controle ou alvo.
- Equipar, usar, atacar, mover e outras ações que alteram a partida continuam
  manuais. A demonstração espera a ação real e aceita pelo servidor.
- Enquanto espera, outro clique repete a orientação da ação atual; não a confirma
  nem a pula.
- Depois que a ação real faz a lição avançar, a orientação seguinte aguarda um
  novo clique em **Me mostra**.
- Mostrar o botão da interface e todos os atalhos reais disponíveis: mouse,
  teclado e gamepad, respeitando as configurações do jogador.
- Fechar uma tela ou cancelar a ação preserva a etapa; o próximo clique reaplica
  a orientação. Uma ação recusada também mantém a etapa aguardando.
- O servidor continua como autoridade do progresso. A demonstração não cria
  progresso, recompensas ou estado paralelo.
- Começar por três casos — abrir inventário e equipar um item, mover até um alvo
  no mapa, e usar uma habilidade no boneco de treino — validar esses fluxos e só
  então ampliar para outras lições.

## Abordagens consideradas

1. **Roteiros declarativos por etapa — escolhido.** O passo do guia descreve
   operações visuais e preparações seguras permitidas. Um cursor local percorre
   essas operações a cada clique. O servidor permanece responsável por aceitar
   a ação real. Isso deixa o comportamento explícito e auditável.
2. **Passeio visual temporizado.** Uma sequência automática de destaques exigiria
   menos cliques, mas poderia avançar sem o jogador acompanhar e disputaria foco
   com as interações reais.
3. **Inferir os comandos a partir do tipo de lição.** Evitaria autoria manual,
   mas não descreve com precisão a ordem e os controles específicos ensinados.

## Experiência do jogador

1. O jogador clica em **Me mostra**. A demonstração executa uma operação segura
   do roteiro, como abrir o inventário, e destaca o próximo elemento.
2. Cada novo clique avança uma operação visual. No limite de uma ação de jogo,
   mostra claramente o que fazer e todos os controles disponíveis.
3. O jogador executa a ação pela interface normal. A demonstração aguarda o
   evento existente e só considera a etapa concluída após a aceitação do servidor.
4. Enquanto aguarda, **Me mostra** repete o destaque e as instruções sem avançar.
   Uma tentativa inválida deixa o roteiro no mesmo ponto e reapresenta o alvo.
5. Ao avançar a lição, o cursor anterior é encerrado. A próxima demonstração só
   começa quando o jogador clicar novamente em **Me mostra**.
6. Fechar uma interface preserva a posição do cursor. O clique seguinte reabre
   ou reapresenta a orientação, sem fechar uma tela que já estava aberta.

Os destaques no tabuleiro funcionam em 2D e 3D, sem revelar alvos ocultos pela
névoa. O foco de teclado/gamepad acompanha a mesma instrução visual. O jogador
pode cancelar a demonstração sem alterar seu progresso ou sua ação.

## Dados e arquitetura

O campo opcional `demonstracao` no passo do guia é uma lista pequena de
operações de apresentação validadas. Exemplos incluem focar um elemento e abrir
uma interface segura. Não aceita JavaScript, seletores arbitrários nem chamadas
a handlers de movimento, ataque, magia, item ou fim de turno.

As fontes em `tools/tutorial_guia_*.py` continuam sendo a autoria do conteúdo;
geradores atualizam arquivos derivados. `server.py` valida e envia os dados no
payload do passo existente. `src/guiaTutorial.js` pode normalizar operações sem
acessar DOM ou canvas. `game.js` mantém o cursor local da demonstração, abre
interfaces por funções idempotentes, desenha os destaques e encerra a sessão
quando o passo ou herói muda. O progresso continua no fluxo e nos eventos
autoritativos atuais, sem novo protocolo de ação.

As teclas e comandos vêm dos vínculos reais de cada dispositivo/configuração.
Nenhum clique ou comando sintético confirma ação. A janela existente mantém sua
compatibilidade com mouse, teclado e gamepad.

## Erros, cancelamento e isolamento

- Alvo indisponível ou oculto: não revelar o alvo; manter as dicas normais e
  apresentar uma mensagem de orientação alternativa.
- Ação recusada: permanecer na etapa de espera e restaurar o destaque.
- Fechamento de interface/cancelamento: preservar o cursor e reaplicar no
  próximo clique.
- Mudança de passo, lição, herói ou saída do tutorial: encerrar timers e foco
  temporário da sessão anterior.
- Cada demonstração pertence ao jogador/herói que recebeu a lição e não executa
  comandos em nome de outro jogador.
- Passos antigos sem `demonstracao` continuam usando a orientação visual já
  existente.

## Piloto e critérios de aceitação

Implementar e validar inicialmente:

1. abrir inventário, destacar um item e esperar o jogador equipá-lo;
2. destacar o destino no mapa e esperar o jogador mover o peão;
3. destacar a habilidade e o boneco de treino e esperar o uso real da habilidade.

Para cada caso, verificar que cada clique avança só uma etapa visual; a ação
manual é o único modo de avançar uma lição; o aceite do servidor é necessário;
repetir a orientação, fechar tela ou sofrer recusa não pula a etapa; e o próximo
passo do guia espera novo clique. Verificar destaques no mapa 2D/3D, respeito à
névoa e atalhos reais de mouse, teclado e gamepad. Revisar o piloto antes de
autorizar a expansão às outras lições.

## Fora de escopo

- Executar automaticamente movimento, ataque, magia, item, recurso ou fim de
  turno.
- Alterar requisitos, recompensas, histórico ou condições de conclusão das
  lições.
- Reescrever todo o tutorial antes da validação do piloto.
- Criar uma simulação paralela da partida.
