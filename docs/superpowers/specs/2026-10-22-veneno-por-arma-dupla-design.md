# Veneno por arma no combate com duas armas

Data: 2026-10-22. Esta especificação registra o desenho aprovado para permitir
que heróis e vilões envenenem armas individuais quando lutam com duas armas.

## Intenção

Permitir que cada mão ou ataque de arma tenha seu próprio veneno e saldo de
cargas, com escolha explícita do alvo da aplicação para evitar que o sistema
altere a arma envenenada sem o jogador ou mestre perceber.

## Regras aprovadas

- Cada aplicação de frasco envenena **uma arma**. Envenenar duas armas exige
  dois frascos e duas aplicações.
- Em cada aplicação, o usuário escolhe explicitamente a arma principal ou a
  mão secundária. Não há alternância automática entre mãos.
- Cada arma mantém sua própria fila FIFO de venenos. Um acerto com uma arma
  consome uma carga somente da arma que realizou aquele ataque; erro não gasta
  carga. A aplicação dura 3 acertos, ou 6 com `ladino_veneno_2`, por veneno.
- Com `ladino_veneno_3`, cada arma pode manter até dois venenos distintos em
  sequência; reaplicar um veneno ativo renova suas cargas. Um terceiro veneno
  distinto é recusado sem consumir o frasco nem descartar cargas existentes.
- O ataque da mão secundária usa as cargas da arma secundária. Custos e
  economia de ação de cada ataque permanecem iguais aos atuais.
- Para um monstro controlado pelo mestre, o painel de uso de item permite
  escolher o ataque da ficha que receberá o frasco. Cada ataque mantém uma fila
  independente e consome carga apenas quando aquele ataque acerta.
- A aplicação manual em monstros conserva a economia de ação atual do item.
  A aplicação automática da IA continua escolhendo o primeiro ataque elegível,
  sem criar uma nova decisão para a IA.
- Efeitos `on_hit` nativos do monstro permanecem intactos; o veneno aplicado
  pelo frasco é estado separado da definição original do ataque.
- Personagens sem arma secundária e monstros sem ataques elegíveis não podem
  aplicar o frasco. A tentativa inválida não consome frasco, carga, sede ou
  ação.
- Cargas salvas na arma principal continuam onde estão; a nova mecânica apenas
  passa a persistir e consumir cargas também na mão secundária e nos ataques de
  monstros.

## Interface

- A aplicação em heróis apresenta escolhas identificadas como **Arma
  principal** e **Mão secundária**, incluindo nome e saldo de cargas da arma.
- O painel do mestre mostra os ataques do monstro pelo nome e permite escolher
  um para cada frasco. Cada escolha consome um frasco e vincula a dose somente
  àquele ataque.
- As confirmações e mensagens indicam a arma ou ataque selecionado, o veneno e
  a duração aplicável (3 ou 6 acertos por veneno).
- Se o alvo selecionado já estiver no limite de venenos, ou não for uma arma
  apta, a interface informa a causa sem fechar o painel antes da correção.

## Fora de escopo

- Uma dose cobrindo mais de uma arma ou compartilhamento de cargas entre mãos.
- Mudança nos efeitos dos venenos, CDs, testes ou duração dos efeitos no alvo.
- Mudança nas regras atuais de ataque secundário, custos ou ações.
- Mudança nos ataques próprios da ficha do monstro ou nas decisões de IA.
- Redistribuir ou aumentar cargas de armas já envenenadas.

## Questões técnicas para o plano

- Heróis já guardam a arma principal em `gear.weapon` e a secundária em
  `gear.off_hand`; a carga precisa permanecer no próprio item equipado e viajar
  com ele ao guardar, trocar ou retirar.
- Monstros usam `attacks[]`, não os slots de equipamento do herói. O estado de
  veneno aplicado deve ficar separado de `on_hit` nativo e ser resolvido no
  fluxo comum de acerto do ataque correspondente.
- O consumo de cargas deve ocorrer no acerto da arma/ataque identificado,
  inclusive nos ataques de mão secundária e nos ataques múltiplos dos monstros.
- A seleção e o consumo do frasco, atualização do item escolhido, custo de
  ação/sede e publicação de estado precisam permanecer consistentes.

## Critério de conclusão

O jogador escolhe explicitamente qual mão envenenar em cada uso; o mestre
escolhe explicitamente qual ataque do monstro envenenar. Cada arma/ataque tem
cargas independentes, cada acerto consome uma carga de sua própria fila e erros
preservam as cargas. Para envenenar duas armas são consumidos dois frascos. A
regra funciona sem substituir venenos nativos dos monstros e sem alterar custos
ou ações atuais.
