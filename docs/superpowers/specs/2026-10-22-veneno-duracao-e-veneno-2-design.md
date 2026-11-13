# Veneno corpo a corpo e duração ampliada de Veneno Rápido

Data: 2026-10-22. Esta especificação registra a mudança aprovada em conversa
para aumentar a relevância do veneno em armas corpo a corpo e ampliar o preparo
de munição com Veneno Rápido II. Ainda não descreve implementação.

## Intenção

Dar mais usos a cada aplicação de veneno: golpes corpo a corpo devem poder
aproveitar o mesmo frasco por vários acertos; Veneno Rápido II deve dobrar a
duração e permitir que um frasco prepare até 20 flechas ou virotes.

## Regras aprovadas

- Uma aplicação em arma corpo a corpo dura **3 acertos** para qualquer
  personagem. Cada golpe que acerta consome uma carga; um ataque que erra não
  consome carga.
- `ladino_veneno_2` eleva a duração corpo a corpo de cada veneno aplicado para
  **6 acertos**. O benefício vale tanto para a aplicação por Veneno Rápido
  quanto para o frasco genérico, sem alterar seus custos ou sua economia de
  ação atuais.
- `ladino_veneno_3` mantém a capacidade aprovada de usar dois venenos distintos
  na mesma arma corpo a corpo. Os efeitos continuam em sequência FIFO: os
  acertos consomem primeiro as cargas do veneno mais antigo. Com Veneno II e
  III, cada veneno distinto conserva suas próprias 6 cargas.
- Para armas à distância, o limite continua sendo **10 projéteis por pilha**.
  Sem `ladino_veneno_2`, um frasco prepara até 10 projéteis; com Veneno II, um
  frasco prepara até 20, aplicando o mesmo veneno em cada projétil selecionado.
- Com `ladino_veneno_3`, dois frascos de venenos diferentes aplicam ambos os
  efeitos ao mesmo conjunto de até 10 projéteis sem Veneno II ou até 20 com
  Veneno II. Cada frasco cobre todo o conjunto escolhido. Dois efeitos em 20
  projéteis consomem dois frascos, não quatro.
- Para preparar até 20 sem aumentar o tamanho máximo de pilha, o servidor
  completa a seleção com munição compatível e ainda não envenenada em outros
  slots. O slot escolhido define o tipo e os atributos da munição; a separação
  conserva esses atributos e a combinação de venenos. As pilhas resultantes
  permanecem com no máximo 10 unidades.
- Se houver menos munição compatível que a quantidade pedida, a operação é
  recusada sem consumir frascos, sede, munição ou ação. Qualquer quantidade
  abaixo da capacidade por frasco (10 sem Veneno II, 20 com Veneno II) pede
  confirmação e informa projéteis, frascos e a dose restante que será perdida,
  mesmo quando não há projéteis suficientes no inventário para preencher a
  capacidade. O frasco é consumido inteiro.
- A munição continua sendo consumida no disparo tanto em acerto quanto em erro;
  os efeitos de veneno são resolvidos somente no acerto, cada um com seu próprio
  teste de resistência.
- Os custos permanecem os atuais: Veneno Rápido custa 1 de sede por frasco e é
  ação livre; o frasco genérico conserva sua economia de ação. Usos corpo a
  corpo não passam a cobrar um custo diferente.
- Cargas já aplicadas e salvas em armas corpo a corpo não ganham cargas novas
  retroativamente. Conservam as cargas restantes; novas aplicações passam a
  usar a duração correspondente à regra atual.

## Interface

- O HUD e os painéis mostram o limite aplicável: 3 ou 6 acertos em arma corpo a
  corpo e até 10 ou 20 projéteis por frasco à distância.
- Ao preparar mais de uma pilha de munição, o jogador escolhe uma pilha base e
  a operação completa a quantidade a partir das pilhas compatíveis disponíveis.
- Nome e tooltip continuam identificando as flechas/virotes envenenados e os
  efeitos anexados. Pilhas envenenadas não aceitam uma segunda aplicação.

## Fora de escopo

- Mudar efeitos, CDs, duração dos venenos no alvo ou testes de resistência.
- Aumentar o máximo global de projéteis por pilha acima de 10.
- Mudar o consumo de munição em caso de erro, o qual já é consumida no disparo.
- Alterar a ação ou os custos atuais de aplicar veneno.
- Converter retroativamente cargas já salvas em armas.

## Questões técnicas para o plano

- A seleção de até 20 projéteis precisa validar e separar várias pilhas como
  uma única operação transacional, mantendo a pilha limite 10 e sem misturar
  tipos ou atributos diferentes.
- O limite e o consumo por arma devem derivar da especialização possuída e
  permanecer coerentes no servidor, HUD, painel, tooltip e mensagens.
- Em uma arma com dois venenos corpo a corpo, o estado deve preservar a
  sequência FIFO e a quantidade de cargas correspondente a cada veneno.
- Manter a compatibilidade com cargas persistidas antes desta mudança.

## Critério de conclusão

Uma aplicação corpo a corpo dura três acertos, ou seis por veneno com Veneno
Rápido II; erros não gastam essas cargas. À distância, um frasco prepara até
10 projéteis, ou 20 com Veneno II, usando várias pilhas compatíveis sem criar
pilhas acima de 10. Veneno III aplica dois efeitos distintos a cada projétil do
conjunto e consome um frasco por efeito. Custos, confirmação, consumo no erro,
tooltips e cargas persistidas permanecem coerentes com as regras acima.
