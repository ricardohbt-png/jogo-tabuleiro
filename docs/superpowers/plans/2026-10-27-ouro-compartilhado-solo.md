# Ouro compartilhado no modo Solo — plano de implementação

> **Execução:** implementação nativa nesta sessão, conforme o pedido de seguir com o desenho aprovado.

**Objetivo:** Permitir ativar por jogo o uso do saldo total do grupo Solo para pagar compras e serviços da cidade, preservando os saldos individuais.

**Arquitetura:** Uma configuração booleana do jogo salvo controla o modo de pagamento e é alternada por uma ação da cidade. O servidor soma os saldos das fichas do grupo, valida e debita em ordem determinística; a cidade exibe o total já calculado e cada herói conserva o seu saldo. Clientes usam o total somente para apresentar disponibilidade; o servidor continua autoritativo.

**Stack:** Python (`server.py`), JavaScript (`game.js`), CSS (`game.css`) e traduções PT/EN (`src/lang/interface.js`).

**Design:** `docs/superpowers/specs/2026-10-27-ouro-compartilhado-solo-design.md`.

## Restrições globais

- Vale apenas para Solo com grupo; default desligado em jogos novos e existentes.
- A chave fica na cidade, é salva por jogo e pode mudar a cada visita.
- Ligado, toda compra/serviço da cidade usa a soma das moedas do grupo, exceto caravana.
- Saques e recompensas seguem creditados ao herói que os recebeu.
- O comprador paga primeiro; o restante sai dos outros heróis por ordem fixa do grupo.
- Desligar não redistribui saldos; ações da masmorra e multiplayer não mudam.
- Não adicionar nem executar testes nesta tarefa, salvo pedido do usuário.

## Arquivos

- `server.py`: persistência da preferência, payload da cidade, ação da chave, cálculo/debito/estorno do saldo, integração dos pagamentos.
- `game.js`: controle na cidade, helpers de total e saldo para compra, validação visual nos painéis de loja/serviço.
- `game.css`: apresentação da chave e do total na barra de heróis da cidade.
- `src/lang/interface.js`: textos do total, estado da chave e ajuda em português/inglês.
- `CLAUDE.md`: registrar o contrato do saldo compartilhado e os limites.

## Foco da revisão

- Save legado sem preferência: compartilhamento começa desligado.
- Solo com grupo: habilitar/desabilitar a chave atualiza a cidade e persiste no save.
- Multiplayer ou Solo de um herói: não expõe nem ativa o compartilhamento.
- Compra acima do total: não debita nenhuma ficha e não concede item/serviço.
- Débito suficiente: comprador é debitado primeiro, depois membros em ordem fixa; total restante e saldos individuais coincidem.
- Reembolso de compra recusada: restaura as mesmas fichas debitadas.
- Loot/venda: permanece creditado ao herói correspondente; caravana e ações de masmorra não usam a carteira compartilhada.

## Tarefas

### 1. Preferência persistente e interface na cidade

Adicionar `ouro_compartilhado: false` ao savegame novo e à migração `ensure_campaign_schema`; preservar o valor ao criar continuação de campanha. Criar uma ação de cidade que só aceite alternar a chave no Solo com grupo, persistir imediatamente no save e publicar o novo `city_state`. Expor no payload se a sessão tem grupo Solo e o valor atual.

Na barra `#city-hero-bar`, reaproveitar o total que `_updateCityHeroBar` já soma para mostrar rótulo explícito de ouro total do grupo no Solo com grupo e incluir a chave ligada/desligada. Manter os cartões e saldos individuais. Adicionar textos PT/EN e estilo.

### 2. Débito combinado autoritativo e integração dos pagamentos

Em `GameRoom`, implementar helpers para obter os heróis da conexão Solo, calcular saldo disponível e debitar em ordem: herói comprador primeiro, depois outros por `slot` e pid. Validar o total inteiro antes de qualquer alteração; devolver um registro de débito para estornar exatamente os mesmos heróis quando um fluxo de compra é recusado após o débito.

Usar os helpers em `handle_shop_buy`, `handle_guild_buy`, `handle_repair_item`, `handle_templo_remover_maldicao` e `handle_templo_ressuscitar`. Deixar inalterados créditos de venda/loot/recompensa e pagamentos de caravana/masmorra.

No cliente, calcular o saldo que pode gastar a partir do `city_state`; aplicar a soma quando a chave estiver ligada e o saldo individual quando desligada. Atualizar as verificações de disponibilidade e o valor no cabeçalho das lojas, reparo, Guilda, remoção de maldição e ressurreição.

### 3. Registro e revisão de escopo

Adicionar em `CLAUDE.md` o contrato final. Revisar os trechos alterados para confirmar escopo e preservar modificações locais já existentes; não executar testes.
