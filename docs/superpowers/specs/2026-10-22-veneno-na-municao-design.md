# Veneno aplicado à munição — desenho

Data: 2026-10-22. Este documento registra as regras aprovadas em conversa para
substituir o veneno armazenado na arma por veneno associado às pilhas de flechas
e virotes. Ainda não descreve implementação nem altera o comportamento do jogo.

## Intenção

Fazer o veneno acompanhar cada projétil no inventário. O jogador escolhe a
munição que deseja preparar, vê sua condição pelo nome e tooltip, e perde cada
projétil envenenado quando o dispara. Veneno Rápido III permite combinar dois
venenos diferentes no mesmo conjunto de projéteis.

## Regras aprovadas

- Cada frasco prepara até 10 flechas ou virotes. O jogador escolhe uma pilha e
  uma quantidade de 1 a 10; quantidades abaixo de 10 pedem confirmação. O frasco
  usado é consumido inteiro, e qualquer dose que não couber na quantidade
  escolhida é perdida.
- A munição escolhida é separada automaticamente da pilha normal. O restante
  conserva o tipo e os atributos originais. Pilhas com combinações de veneno
  diferentes permanecem separadas; pilhas com a mesma munição e a mesma
  combinação podem se agrupar.
- O nome visível muda para **Flecha Envenenada** ou **Virote Envenenado**. O
  tooltip lista o nome e um resumo do efeito de cada veneno associado.
- Sem Veneno Rápido III, cada projétil recebe um veneno. Com Veneno Rápido III,
  o jogador pode escolher um frasco para aplicar um veneno ou dois frascos de
  tipos diferentes para aplicar ambos aos mesmos projéteis. A dose dos dois
  frascos cobre o mesmo conjunto de até 10 projéteis, não 10 para cada frasco.
- Uma pilha que já tenha veneno não pode receber outra aplicação: a ação é
  bloqueada. A combinação de dois venenos é feita na mesma aplicação inicial.
  Pilhas em outros slots podem receber outras combinações; não há limite global
  de tipos de veneno guardados no inventário.
- Todo uso de veneno que hoje o aplica a uma arma à distância passa a poder
  preparar munição. Veneno Rápido III é o requisito para combinar dois venenos.
  As regras de envenenamento de armas corpo a corpo permanecem fora desta
  mudança.
- Cada projétil é consumido quando disparado, mesmo se o ataque errar. Os
  venenos só são resolvidos quando o ataque acerta. Cada veneno associado faz
  seu próprio teste de resistência e aplica normalmente seu efeito em caso de
  falha.
- Veneno Rápido continua sendo ação livre e custa 1 ponto de sede por frasco:
  1 para uma aplicação simples, 2 para uma combinação. Os custos e a economia de
  ação dos demais usos de veneno permanecem os atuais.
- Para escolher munição durante o ataque, permanece a prioridade existente:
  uma pilha compatível equipada na mão esquerda é usada primeiro; para bestas,
  se não houver munição equipada, o jogo escolhe automaticamente uma pilha
  compatível da bolsa. Não será acrescentada uma seleção de munição a cada tiro.
- Partidas salvas que já tenham cargas de veneno em uma arma à distância
  conservam essas cargas e as consomem pelo comportamento antigo até acabarem.
  Enquanto houver cargas antigas na arma, uma nova aplicação de veneno à
  munição para essa arma é bloqueada; isso evita combinar a carga legada com os
  efeitos já associados aos projéteis. Após as cargas antigas se esgotarem,
  aplicações novas usam somente o sistema ligado à munição.

## Confirmação e validação

Ao escolher menos de 10 projéteis, a confirmação informa a quantidade, quantos
frascos serão consumidos e que a dose restante será perdida. A aplicação só
acontece após a confirmação. Sem munição compatível suficiente, sem os frascos
necessários, com venenos repetidos na combinação, ou ao tentar reaplicar em uma
pilha envenenada, a ação é recusada sem consumir frascos, sede ou munição.

## Abordagem técnica recomendada

Armazenar os identificadores dos venenos na própria pilha de munição, junto de
`ammo_type` e `ammo_count`. A assinatura da pilha precisa incluir o tipo de
munição e a combinação de venenos para que pilhas diferentes não se misturem.
No disparo, o servidor consome uma unidade da pilha selecionada e usa os
identificadores daquela unidade para resolver os efeitos no alvo.

Essa abordagem mantém o efeito no item ao trocar de arma, mover munição entre
slots ou guardar o item. Manter cargas na arma seria mais simples, mas não
atenderia à exigência de que o veneno acompanhe as flechas e os virotes.

## Fora de escopo

- Alterar os efeitos, duração, CDs ou testes próprios dos venenos.
- Mudar munição corpo a corpo, arremessável ou não classificada como flecha ou
  virote.
- Criar escolha da munição a cada disparo.
- Alterar a ação/custo dos usos de veneno que não sejam Veneno Rápido.
- Converter retroativamente veneno já carregado em armas nas partidas salvas.

## Critério de conclusão

Uma pilha parcialmente preparada fica separada da munição comum, mantém seus
venenos ao ser movida, mostra os efeitos corretos no tooltip e perde exatamente
uma unidade por disparo. Um acerto resolve um ou dois venenos com testes
independentes; um erro consome o projétil sem aplicar efeitos. A aplicação
respeita as confirmações, custos e bloqueios descritos acima.
