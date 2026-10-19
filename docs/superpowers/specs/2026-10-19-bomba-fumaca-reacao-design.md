# Bomba de Fumaça como reação a ataques inimigos

Data: 2026-10-19
Estado: desenho aprovado pelo usuário em 2026-10-19; implementação ainda não iniciada.
Classificação: arquitetural, pois introduz uma interrupção compartilhada do combate e mensagens novas no protocolo.

## Objetivo e decisões aprovadas

Reduzir a espera entre turnos permitindo que o jogador use uma Bomba de Fumaça quando um inimigo atacar seu personagem ou um aliado. O ataque pausa antes da rolagem. A confirmação consome uma bomba, mostra seu arremesso até o inimigo, forma a nuvem e só então permite a resolução do ataque com desvantagem.

Decisões expressamente aprovadas na conversa:

- O gatilho é o ataque inimigo, com o atacante dentro do alcance de lançamento de quem possui a bomba.
- O jogador pode proteger a si mesmo ou outro herói.
- A oportunidade aparece antes do ataque acontecer.
- A nuvem permanece por duas rodadas, com os efeitos normais da bomba.
- Todas as pessoas aptas recebem a oferta simultaneamente; a primeira confirmação válida vence. As demais caixas fecham e não consomem itens.

## Regras propostas para completar o desenho

Estas escolhas completam detalhes inicialmente não especificados e foram aprovadas com a revisão deste documento:

- A janela dura até 12 segundos, espelhando a duração da reação de Sorte já existente. Mostra contagem regressiva. Todos recusarem encerra a espera imediatamente; o prazo equivale a recusar.
- O único custo é uma bomba consumida. Não há custo adicional de fome/sede, ação principal, ação bônus, movimento ou carga de reação por rodada nesta primeira implementação.
- Uma oportunidade por ataque individual. Ataques múltiplos podem abrir novas oportunidades, desde que ainda haja personagens aptos e bombas.
- A reação atende ataques direcionados a heróis com rolagem de acerto d20, corpo a corpo ou à distância, incluindo arremessáveis de alvo. Efeitos resolvidos apenas por resistência, dano automático e explosivos de área não abrem uma oferta que seria incapaz de alterar sua resolução.
- O ataque que disparou uma reação bem-sucedida recebe desvantagem explícita: 2d20 e o menor resultado, mesmo se o atacante enxergar no escuro. Esse efeito vale apenas para aquele ataque. A visão e os demais efeitos normais da nuvem controlam as ações seguintes.
- A rolagem do ataque pendente usa desvantagem como solicitado; exceções existentes de acerto automático continuam sendo resolvidas pelos mesmos mecanismos posteriores à rolagem.
- O arremesso reage ao atacante escolhido, sem etapa adicional de mira. A nuvem fica centrada na posição do inimigo capturada para aquele ataque e usa raio 1.
- Alcance base 4 casas, modificadores normais de alcance de arremesso e linha de visão/trajetória existentes. Não permite atravessar paredes.
- Apenas heróis vivos, conectados, presentes na mesma masmorra e capazes de agir fisicamente podem reagir. Condições que apenas bloqueiam movimento não impedem o arremesso; condições que incapacitam ações, petrificação, inconsciência, paralisia ou engolimento o impedem. A implementação deverá usar as condições reais existentes sem consumir recursos na consulta de elegibilidade.
- Pode usar bomba válida da bolsa ou do cinto, respeitando os contratos existentes de origem e consumo de item.
- A oferta não depende de ainda haver ação principal/bônus no turno pessoal; essa é a utilidade da reação fora do turno.

## Fluxo visível

1. O servidor confirma atacante e herói-alvo, alcance do ataque e demais precondições já existentes. Nenhum d20, dano ou animação do ataque foi enviado ainda.
2. O servidor calcula os heróis aptos, gera um identificador único e envia a oportunidade somente às conexões correspondentes.
3. A caixa diz: **[Inimigo] vai atacar [Herói]. Lançar uma Bomba de Fumaça?** Mostra o herói que reagirá, a quantidade de bombas, o prazo e os botões **Lançar bomba** e **Não reagir**.
4. Uma conexão que controla vários heróis vê uma única caixa com as opções de seus heróis aptos. A identidade de quem lançará é explícita; nenhuma troca automática de foco escolhe por ele.
5. A primeira aceitação válida reserva a decisão de forma atômica, consome exatamente uma bomba e fecha as ofertas restantes. Respostas atrasadas são ignoradas.
6. O arremesso e a nuvem reutilizam o feedback de projétil, som e visual existentes. A cena termina o lançamento antes do ataque inimigo.
7. O servidor retoma o mesmo ataque, com o mesmo atacante e alvo, aplicando a desvantagem da reação. Não escolhe outro alvo nem cancela o ataque só porque a fumaça alterou a visibilidade.
8. A nuvem continua como zona normal de escuridão por duas rodadas, usando a mesma contagem e expiração do uso normal da bomba. A validade do ataque pendente não altera regras de visão para ataques futuros.

Mouse, teclado e gamepad devem permitir escolher o herói, confirmar e recusar. Escape/B equivale à recusa das opções daquela conexão. Os textos novos terão PT/EN.

## Abordagens consideradas

1. **Janela autoritativa com evento assíncrono (escolhida).** Aproveita os padrões de Sorte, Último Esforço e controle manual. O servidor preserva o ataque na própria execução e aguarda uma decisão ou timeout; o cliente apenas apresenta a oferta e envia a resposta.
2. **Converter todo combate em fila de comandos.** Facilitaria interrupções gerais futuras, mas exige substituir a execução existente e amplia muito o escopo desta bomba.
3. **Pausar apenas no cliente.** Não garante que a rolagem ainda não ocorreu, nem resolve duas confirmações concorrentes. Não atende à regra aprovada.

## Servidor e protocolo

Criar uma janela efêmera por sala contendo identificador, atacante, alvo, candidatos, recusas, prazo, evento e resultado. A janela não integra os saves. O servidor valida novamente elegibilidade, propriedade do herói, estoque, alcance, trajetória e identificador ao aceitar uma resposta.

Protocolo proposto:

- `smoke_reaction_prompt`: identificador, atacante/alvo com nomes e posições, candidatos autorizados da conexão e prazo. Quantidades/origens disponíveis vêm do servidor.
- `smoke_reaction_choice`: identificador, `usar` e `heroi` quando houver escolha de personagem. O cliente não determina o atacante, alvo, alcance, consumo ou bônus.
- `smoke_reaction_closed`: identificador e motivo (`used`, `declined`, `timeout`, `cancelled`), enviado a todas as conexões que receberam a oferta.

A primeira confirmação válida deve marcar a janela como resolvida e consumir a bomba sem liberar a execução com um `await` entre validar e reservar. Só depois publica o fechamento e os efeitos. Uma falha de validação não consome item nem impede os demais candidatos de responder.

Reutilizar o consumo de origem do item e extrair apenas o mínimo necessário do arremesso de área para que a reação não gaste ação principal. Não chamar diretamente o handler de uso normal, que valida turno e registra ação.

Pontos de cobertura identificados:

- `_execute_one_monster_attack` / `_execute_one_monster_attack_impl`: fluxo modular e golpes controlados pelo Mestre.
- Trecho de ataque legado dentro de `gm_phase`: precisa chamar a mesma janela antes da rolagem.
- `_monster_throw_item_impl`, somente no ramo `ataque_alvo` com d20.
- Despacho WebSocket e autorização `heroi_da_acao`: receber respostas fora do turno, mantendo a autorização por conexão.
- Ataques disparados por handlers na mesma conexão que controla os heróis: não bloquear o leitor WebSocket esperando uma resposta daquela própria conexão. A espera precisa ocorrer em uma tarefa controlada, com bloqueio de mutações de combate concorrentes e limpeza apropriada.
- Não permitir que timers de turno/Mestre ou um segundo comando avancem a iniciativa enquanto o ataque está aguardando a decisão e o lançamento. Preservar o tempo restante e retomar o fluxo original.

Não reutilizar uma marca durável de desvantagem no monstro: o resultado pertence à chamada do ataque que foi interrompida, para não vazar para outros golpes ou outra rodada.

## Cliente e animações

Seguir a arquitetura obrigatória de `CLAUDE.md`: estado e comunicação primeiro em `src/gameState.js`, servidor e protocolo depois, e apresentação por último em `game.js`.

`gameState.js` mantém a oportunidade ativa e oferece os métodos de resposta. A identidade de resposta deve permanecer explícita em grupo Solo; fechamento remoto, mudança de sala ou desconexão limpa o estado. Não duplicar callbacks de `GS.on` já registrados, pois há apenas um callback por evento.

`game.js` cria a caixa de reação, navegação acessível e contagem regressiva. A caixa não revela posições ou entidades além do necessário para o ataque anunciado. A animação reutiliza `attack_feedback`, `src/combatScene.js`, `_fumacaSync` e os renderizadores de fumaça existentes. O cálculo de alcance permanece no servidor/estado, nunca no renderer.

O encadeamento usa a duração real do gesto e voo existentes, com proteção de timeout; clientes sem renderização continuam sem poder bloquear indefinidamente a partida. A fumaça deve surgir na chegada da bomba e anteceder a animação e os dados do golpe inimigo em 2D e 3D.

## Encerramento e falhas

- Recusa remove somente os candidatos da conexão que recusou. Se nenhum restar, prossegue imediatamente sem gastar itens.
- Desconexão remove os candidatos correspondentes. Se todos saírem, encerra a janela. Não aguardar resposta de conexão inexistente.
- Fim da partida, saída/reinício da masmorra, invalidação do atacante/alvo ou cancelamento da tarefa encerra a janela em `finally`, fecha a UI e não deixa um evento pendurado.
- Reconexão recupera uma oferta ainda válida com seu prazo original; nunca renova o prazo nem ressuscita uma decisão fechada.
- Uma resposta repetida ou de outro jogador não consome item e não altera a decisão.

## Validação prevista após aprovação

Verificações focadas no servidor: elegibilidade por alcance/parede/condição; autoproteção e proteção de aliado; bolsa/cinto; dois aceites simultâneos consumindo uma bomba; recusa/timeout/desconexão; continuidade do mesmo ataque; menor dos dois dados; duas rodadas de nuvem; IA modular, legado, arremessável direcionado e Mestre.

Verificações focadas no cliente: oferta/fechamento por identificador; escolha correta de herói em grupo Solo; mensagens atrasadas; teclado/gamepad; sem alteração de turno pessoal.

Validar o fluxo em sessão real 2D e 3D: caixa antes dos dados, lançamento até o atacante, nuvem no impacto, ataque com desvantagem e desaparecimento normal da nuvem. A conclusão deve declarar explicitamente qualquer caminho que não tiver sido exercitado.

## Limite desta entrega

Esta especificação trata da Bomba de Fumaça como primeira reação de item. Habilidades coordenadas, outros itens de apoio e novos custos de fome/sede ou recarga ficam para desenhos próprios.
