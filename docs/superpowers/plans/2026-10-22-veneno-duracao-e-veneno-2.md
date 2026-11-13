# Plano: duração do veneno e Veneno Rápido II

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer cada aplicação corpo a corpo durar 3 acertos, ou 6 com Veneno Rápido II, e permitir que um frasco prepare até 20 projéteis com Veneno II.

**Architecture:** O servidor deriva a duração das cargas e o teto de preparo das especializações, mantendo Veneno III como combinação de dois efeitos. Para preparar até 20 projéteis sem mudar o limite de 10 por slot, uma transação reúne pilhas compatíveis, calcula todas as separações e valida o espaço final antes de consumir recursos.

**Tech Stack:** Python em `server.py`; JavaScript em `game.js` e `src/gameState.js`; textos em `src/lang/catalogo.js`, `src/lang/interface.js` e `src/lang/narracao.js`; contrato em `CLAUDE.md`.

**Spec:** `docs/superpowers/specs/2026-10-22-veneno-duracao-e-veneno-2-design.md`

## Restrições globais

- Uma aplicação em arma corpo a corpo dura 3 acertos para qualquer personagem.
- `ladino_veneno_2` eleva a duração corpo a corpo para 6 acertos por veneno.
- Sem Veneno II, um frasco envenena até 10 projéteis; com Veneno II, até 20.
- As pilhas de munição continuam limitadas a 10 projéteis.
- Com `ladino_veneno_3`, dois frascos diferentes aplicam ambos os efeitos ao mesmo conjunto; cada frasco cobre o conjunto inteiro.
- Abaixo da capacidade por frasco (10 ou 20), confirmar e informar quantidade, frascos e dose perdida.
- O frasco é consumido inteiro; Veneno Rápido custa 1 de sede por frasco e continua ação livre; o frasco genérico mantém a economia atual.
- A munição é consumida no acerto ou erro; venenos só resolvem no acerto, cada um com teste próprio.
- A aplicação recusada não consome veneno, sede, ação ou munição.
- Não aumentar globalmente o limite de munição por pilha nem conceder cargas novas retroativamente a venenos já aplicados.
- Não adicionar nem executar testes automatizados sem solicitação do usuário; fazer revisão manual de código e diff.

## Foco da revisão

- A coleta de várias pilhas precisa exigir tipo e atributos idênticos, ignorar pilhas já envenenadas e preservar a combinação em cada unidade preparada.
- Uma seleção parcial que crie pilhas extras precisa validar espaço da bolsa antes de qualquer consumo; bolsa cheia deve recusar sem mudanças.
- Veneno III em 20 projéteis deve consumir exatamente dois frascos diferentes e anexar os dois IDs a cada projétil preparado.
- O projétil continua sendo gasto no erro; em ataque corpo a corpo, apenas acertos gastam uma carga de veneno.
- Cargas corpo a corpo antigas mantêm seu saldo salvo; somente novas aplicações usam 3/6 cargas.

---

### Task 1: Duração das cargas corpo a corpo

**Arquivos:**
- Modificar `server.py`: `_capacidade_poison_melee`, `_aplicar_veneno_na_arma`, `_weapon_poison_slots` e textos enviados ao aplicar.
- Modificar `src/gameState.js`: `ladinoVenenoMaxHits`.
- Modificar `game.js`: exibição da duração e dos usos restantes da habilidade.
- Modificar `src/lang/catalogo.js`, `src/lang/interface.js` e `src/lang/narracao.js`: descrições para 3/6 acertos.

**Interfaces:**
- Produz: capacidade corpo a corpo de 3 cargas por veneno, dobrada para 6 com `ladino_veneno_2`; `ladino_veneno_3` mantém até dois venenos distintos em sequência FIFO.
- Consome: `poison_slots` existentes e especializações do jogador.

- [x] Atualizar a capacidade por veneno para `3 * (2 se ladino_veneno_2, senão 1)` e o limite total para até dois venenos distintos no nível III.
- [x] Fazer novas aplicações gravarem 3/6 cargas por veneno sem preencher cargas adicionais em saves existentes.
- [x] Alinhar HUD, painel e narração ao saldo e à capacidade de 3/6 acertos.
- [x] Revisar manualmente o fluxo de acerto, erro, troca de veneno e esgotamento FIFO para armas corpo a corpo.

### Task 2: Planejamento transacional de até 20 projéteis

**Arquivos:**
- Modificar `server.py`: criar o plano puro de seleção e separação de pilhas e integrar `handle_envenenar_municao`.

**Interfaces:**
- Produz: `_planejar_preparo_municao(p, ammo_source, ammo_index, quantity, poison_ids)` que retorna a futura lista da bolsa e o futuro item da mão esquerda, ou `None` se não houver munição compatível.
- Consome: `_ammo_stack_key`, `_ammo_stack_poison_ids`, fontes `bag`/`off_hand` e limite `MAX_AMMO_STACK == 10` por pilha.

- [x] Planejar candidatos na ordem: pilha escolhida primeiro; depois pilhas ainda não envenenadas com a mesma assinatura de munição, priorizando mão esquerda e depois bolsa em ordem de índice.
- [x] Limitar o total preparado a 10 sem Veneno II e a 20 com Veneno II; distribuir o resultado em pilhas de até `MAX_AMMO_STACK` sem misturar assinaturas.
- [x] Calcular cópias preparadas, sobras sem veneno e ocupação final da bolsa antes de mudar qualquer item ou recurso.
- [x] Aplicar o plano inteiro de forma síncrona somente após validar munição, frascos, habilidade, sede, ação e espaço; não suspender com `await` entre a última validação e o commit de recursos/itens, deixando a narração para depois.
- [x] Preservar a origem de frasco do cinto de utilidades e a combinação de até dois venenos distintos em toda pilha preparada.
- [x] Revisar manualmente limites de 10/20, estoque repartido, estoque insuficiente, seleção parcial com bolsa cheia, mão esquerda, frasco no cinto e Veneno III.

### Task 3: Interface, mensagens e contrato

**Arquivos:**
- Modificar `game.js`: painel de envenenamento, quantidade máxima e total compatível disponível.
- Modificar `src/gameState.js`: valor de exibição do benefício de Veneno II.
- Modificar `src/lang/catalogo.js`, `src/lang/interface.js` e `src/lang/narracao.js`: limites, custos, confirmação e descrições.
- Modificar `CLAUDE.md`: contrato atualizado de veneno corpo a corpo e munição.

**Interfaces:**
- Consome: limite efetivo calculado pelo servidor (10/20), pilhas compatíveis visíveis e número de frascos escolhidos.
- Produz: painel que permite pedir até 20 projéteis sem ultrapassar 10 por pilha e confirmação para qualquer quantidade inferior à capacidade do frasco.

- [x] Derivar o máximo selecionável da posse de `ladino_veneno_2` e somar apenas munição compatível ainda sem veneno.
- [x] Exibir a quantidade global escolhida e manter o slot-base como seletor de tipo/atributos; não pedir seleção de munição a cada disparo.
- [x] Ajustar confirmação para capacidade 10/20 e informar quantidade, número de frascos e dose perdida.
- [x] Atualizar textos de Veneno II/III sem alterar custos, ação, nomes de venenos ou efeitos sobre o alvo.
- [x] Atualizar `CLAUDE.md` e revisar manualmente o contrato final e o diff.

## Validação

Não executar testes automatizados sem pedido explícito do usuário. A revisão final deve inspecionar estaticamente as transações e seus chamadores, conferir que nenhuma mutação ocorre antes das validações e usar `git diff --check` para o diff deste trabalho.
