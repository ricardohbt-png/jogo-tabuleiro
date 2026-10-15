# Encontros aleatórios e viagens seguras — especificação de design

**Data:** 2026-10-14

**Estado:** proposta consolidada para revisão; ainda não implementada.

## Objetivo

Adicionar encontros aleatórios durante viagens do mapa-múndi e uma opção paga de
caravana segura entre cidades. A decisão deve colocar economia contra segurança,
manter os custos atuais de fome/sede e funcionar em partidas multiplayer e Solo
com grupo.

## Contexto atual verificado

- `GameRoom.handle_world_travel` (`server.py`) valida o anfitrião, cobra fome/sede
  de cada personagem e muda a localização imediatamente.
- `GameRoom.handle_world_adventure` valida e cobra os custos da aventura antes de
  preparar a entrada na masmorra. A cena narrativa e `_pending_dungeon_entry`
  pertencem a esse fluxo.
- O cliente já mostra uma transição de viagem de três segundos, mas o servidor não
  mantém uma viagem em andamento (`game.js::_showCityTravelTransition`).
- `WORLD_ROUTES` é uma tabela de custos, não um grafo de rotas: pares de cidades
  sem custo explícito continuam conectados e custam 0/0.
- As rotas nativas têm custos combinados de fome+sede 12, 14, 16, 18, 24 e 28.
- A lista de monstros já tem animais como lobo, urso e cobra; não foi encontrado
  um tipo de monstro “bandido” no catálogo atual.
- Há retratos de mercador em `assets/tavern/mercador.png` e
  `assets/tavern/mercador2.png`.

## Decisões aprovadas no brainstorm

1. A chance de encontro é rolada uma vez por viagem arriscada e há no máximo um
   encontro nessa viagem.
2. As chances são 10% para viagem curta, 15% para média e 20% para longa. Uma
   viagem sem custo de provisões fica no mínimo de 10%.
3. A duração da viagem é classificada pelo custo combinado de fome+sede. Proposta
   para revisar: curta até 14; média de 15 a 20; longa acima de 20. Isso separa as
   seis rotas nativas em dois exemplos de cada faixa. A mesma classificação vale
   para aventuras; custos 0/0 ficam na faixa curta.
4. A caravana está disponível somente em viagem cidade-a-cidade e garante que não
   haverá encontro aleatório. A viagem arriscada continua disponível sem tarifa.
5. Tarifa por personagem: base de 10 moedas (curta), 20 (média) ou 30 (longa),
   mais `ceil(0,15 × (fome + sede))`. A tarifa é adicional ao consumo normal de
   fome/sede, que continua sendo cobrado por personagem.
6. No multiplayer, se alguém não puder pagar a própria passagem, um mercador
   solicita a outro jogador que cubra a passagem completa daquele personagem.
   Cobrir é voluntário, não cria dívida, e a viagem de caravana só começa se todas
   as passagens estiverem pagas. Se não houver cobertura, o grupo pode escolher a
   viagem arriscada ou cancelar.
7. No Solo com grupo, cada personagem paga a própria passagem. Não há empréstimo
   automático entre personagens.
8. Em destino cidade, vencer o encontro retoma a viagem até a cidade escolhida.
   Em destino masmorra, vencer abre a escolha “continuar até a masmorra” ou
   “retornar à cidade de origem”. Provisões já consumidas não são reembolsadas e
   retornar não cobra outra viagem.
9. Derrota usa as regras normais do jogo. Não se cria uma regra exclusiva para
   emboscadas.
10. Os encontros usam grupos de inimigos preparados por faixas de força do grupo,
    com variação aleatória entre composições aprovadas. A força considera somente
    personagens viajantes vivos; não se altera o nível/atributos de um inimigo
    individual para escalá-lo.
11. O primeiro mapa é reutilizável, ao ar livre, 26×16, estrada larga de terra com
    curva suave, floresta nas bordas e clareiras laterais. O grupo entra por uma
    extremidade; inimigos surgem à frente na estrada ou nas clareiras, a distância
    segura. Não há baús, objetivos de aventura ou monstros fixos no mapa-base.

## Fluxo pretendido

### Viagem entre cidades

1. O anfitrião abre o destino conectado. A prévia mostra custo atual de fome/sede,
   chance da estrada e duas ações: **Viajar pela estrada** ou **Pagar caravana**.
2. Para a estrada, o servidor revalida destino, recursos e fase; cobra os recursos
   uma vez; registra origem/destino; e faz uma única rolagem de encontro.
3. Sem encontro, conclui a viagem e publica `city_state` na cidade de destino.
4. Com encontro, entra no mapa de estrada em combate. Ao concluir o combate com
   vitória, limpa o estado de encontro e conclui a viagem pendente para o destino.
5. Para caravana, o servidor verifica as moedas personagem a personagem. Se faltar
   cobertura, envia uma solicitação ao grupo. Após todas as passagens estarem
   cobertas e a confirmação do anfitrião, cobra tarifa e provisões de forma
   atômica, muda a cidade e não rola encontro.

### Viagem a destino de masmorra

1. A aventura mantém validações, requisitos, custo de provisões, história e etapa
   atual já existentes.
2. Após validar e cobrar provisões uma vez, rola a chance usando o custo da etapa.
   Não há opção de caravana para masmorra.
3. Sem encontro, prossegue no fluxo de entrada atual.
4. Com encontro, abre o mesmo mapa de estrada. Após vitória, o anfitrião escolhe
   continuar ou retornar. Continuar retoma a entrada pendente sem nova cobrança;
   retornar mantém a cidade de origem e não devolve provisões. A cena narrativa da
   aventura só é apresentada depois que o grupo escolhe continuar.

## Contrato de estado e rede proposto

- O servidor é a fonte autoritativa para custo, chance, escolha de grupo, saldo,
  patrocinadores e destino final. Valores exibidos pelo cliente são prévias.
- `world_travel` passa a aceitar um modo (`road`/`caravan`) sem mudar o
  significado de `destination`. Destinos de aventura continuam usando
  `world_adventure`.
- A solicitação de cobertura de passagem e a resposta voluntária do pagador usam
  mensagens dedicadas, validadas pelo servidor contra um identificador de
  solicitação pendente. O servidor só debita quando todo o pagamento pode ser
  concluído.
- Um estado de viagem pendente contém pelo menos: tipo de destino, origem,
  destino, modo, custos já cobrados, resultado da rolagem e etapa de continuação.
  Ele precisa sobreviver a atualizações de estado e à retomada de jogo salvo para
  não perder o destino nem cobrar novamente durante o combate.
- O combate de estrada é uma instância temporária. Ao vencer, não incrementa
  progresso de aventura nem concede recompensa especial; recompensas normais dos
  inimigos continuam obedecendo às regras gerais. Só pode haver uma emboscada na
  viagem pendente. Ao derrotar o último inimigo, a continuação é automática; não
  abre o botão de encerramento de missão nem exige saída do mapa.
- A solicitação de patrocínio só existe em multiplayer. No Solo, a falta de saldo
  deixa a caravana indisponível e mantém a opção arriscada.

## Conteúdo do primeiro teste

- Novo mapa em `dungeons/estrada_floresta_emboscada.json`, sem alterar
  `dungeons/floresta.json`.
- Duas famílias de composição: animais selvagens e bandoleiros. Cada família tem
  mais de uma composição preparada, escolhida conforme tamanho e força do grupo.
- Spawn dos heróis pela entrada; inimigos em regiões de spawn separadas. Validar
  footprint, distância mínima, casas caminháveis e ausência de sobreposição.
- A conclusão da emboscada ocorre ao derrotar todos os inimigos, sem exigir saída,
  baú ou objetivo autorado de aventura.

## Critérios de aceitação

- O cliente apresenta as chances e o preço por personagem antes da confirmação;
  mostra também o total do grupo.
- A mesma rota sempre mostra a mesma tarifa antes de viajar.
- A tarifa usa arredondamento para cima e não depende do ouro inicial ou do saldo
  atual dos personagens.
- Viagem por estrada consome fome/sede uma vez, no começo, tenha ou não encontro.
- Caravana entre cidades cobra a tarifa e as provisões uma vez e nunca gera
  encontro.
- Multiplayer: personagens sem saldo impedem o fechamento da caravana até que
  outros jogadores cubram a tarifa ou o grupo escolha estrada/cancelar. Pagamentos
  não deixam saldo devedor.
- Solo com grupo: cada herói é cobrado individualmente; um herói não cobre
  automaticamente outro.
- Ao vencer a emboscada de cidade, o grupo chega à cidade selecionada. Ao vencer
  uma emboscada de masmorra, continuar e retornar seguem os resultados aprovados,
  sem duplicar custo.
- Se todos os heróis forem derrotados, o fluxo geral de derrota encerra o jogo e
  não conclui a viagem.
- Desconexão/reconexão, recarga do jogo salvo e mensagens duplicadas não podem
  rolar outro encontro nem cobrar de novo.
- O mapa e a interação nova funcionam em mouse, teclado e controle/gamepad.
- Textos novos existem em português e inglês.

## Riscos e limites

- As probabilidades acumulam em viagens sucessivas: dez viagens curtas dão cerca
  de 65% de chance de pelo menos um encontro; dez longas, cerca de 89%. Manter os
  números aprovados no primeiro teste e avaliar a frequência em partidas reais.
- A caravana é propositalmente uma escolha de custo relevante: uma viagem longa
  nativa custa 34–35 moedas por personagem; um grupo de quatro paga 136–140.
- Não existe inimigo “bandido” no catálogo atual. A aparência e a implementação
  dos bandoleiros precisam de revisão: reutilizar um visual humanoide existente
  para o primeiro teste ou incluir uma ficha/arte dedicada.
- Os limites 14/20 para as faixas de duração e o arredondamento para cima são
  propostas concretas desta especificação, não decisões discutidas linha a linha
  no brainstorm; revisar antes da implementação.

## Fora de escopo

- Caravana para masmorra, rotas seguras configuráveis por autor, montarias,
  escolta como NPC de combate ou novas biomas/ mapas nesta fatia.
- Alterar custos de fome/sede existentes.
- Criar dívida, empréstimo automático ou transferência geral de ouro.
- Bônus de XP/loot exclusivo de emboscada ou encontros repetíveis no mesmo
  trajeto.
- Alterar regras de derrota, ressurreição ou saque existentes.
