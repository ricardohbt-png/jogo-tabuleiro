# Ouro compartilhado no modo Solo — design

## Intenção

Permitir que o jogador escolha, por jogo salvo Solo, se os heróis do grupo podem somar seus saldos individuais para pagar compras e serviços na cidade.

## Abordagens

- **Saldo individual somado na hora de pagar (escolhida):** mantém `gold` em cada ficha; com a opção ligada, as compras usam o total e registram o débito nas fichas. Saques e recompensas continuam indo para o herói que os recebeu. Limita a mudança aos pagamentos e à apresentação do saldo.
- **Carteira coletiva:** substitui os saldos dos heróis por um fundo persistente único; saques, recompensas e pagamentos passam a movimentá-lo. É mais abrangente e exigiria alterar o fluxo de ouro e a compatibilidade dos jogos salvos.

## Regras escolhidas

- Aplicar somente ao modo Solo com grupo; nos demais modos e no Solo de um herói, o comportamento atual continua.
- A opção aparece como chave na cidade, é salva por jogo e pode ser ligada/desligada em cada visita. Começa desligada, inclusive em jogos salvos existentes.
- Ligada, considerar a soma do ouro das fichas do grupo em toda compra e serviço da cidade: lojas (Ferreiro, Mercador, Taverna e Templo), reparos, Guilda e serviços do Templo.
- Excluir tarifa de caravana e custos de ações durante a masmorra.
- Débito: usar primeiro o ouro do herói que iniciou a compra; se não cobrir o preço, descontar o restante dos outros heróis em ordem fixa do grupo. Não redistribuir saldos ao ligar ou desligar a opção.
- Saques e recompensas permanecem individuais. A cidade mostra sempre o ouro total do grupo, mesmo com o compartilhamento desligado, e continua exibindo o saldo próprio de cada herói. Ligado, o total também é o saldo disponível para compras; desligado, compras usam apenas o saldo individual do herói que as iniciou.
- Antes de qualquer débito, o servidor valida o total do grupo; saldo insuficiente não muda nenhuma ficha nem concede a compra/serviço.

## Fora de escopo

Não mudar recompensas de ouro, a divisão do loot, tarifas de viagem, custos de ações de masmorra nem a carteira de jogos Multiplayer.
