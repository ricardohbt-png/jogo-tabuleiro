# Plano de Implementação: Veneno aplicado à munição

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Fazer o veneno acompanhar pilhas de flechas e virotes, com combinação de até dois efeitos por projétil no Veneno Rápido III.

**Architecture:** Guardar uma lista de um ou dois IDs de veneno em cada pilha de munição e incluir essa lista na identidade usada para empilhar itens. Uma única operação autoritativa valida frascos, habilidade, sede, pilha e quantidade; o combate consome o projétil selecionado e resolve cada veneno em um teste independente no acerto. Cargas já salvas na arma continuam pelo fluxo legado até acabarem.

**Tech Stack:** Python em `server.py`; JavaScript em `game.js`; traduções em `src/lang/interface.js` e `src/lang/catalogo.js`; regras do projeto em `CLAUDE.md`.

**Spec:** `docs/superpowers/specs/2026-10-22-veneno-na-municao-design.md`

## Global Constraints

- Cada frasco prepara até 10 projéteis; a quantidade selecionada é de 1 a 10.
- Abaixo de 10 projéteis, confirmar a quantidade, os frascos consumidos e a perda da dose restante.
- Consumir o frasco inteiro, mesmo quando a pilha preparada tiver menos de 10 projéteis.
- Sem Veneno Rápido III, permitir um veneno por projétil; com III, permitir um veneno ou dois venenos distintos nos mesmos projéteis.
- O desbloqueio de Veneno Rápido III é `ladino_veneno_3`.
- Em uma combinação, os dois frascos cobrem a mesma quantidade de projéteis, até 10 no total.
- Uma pilha envenenada não pode receber outra aplicação.
- Pilhas com combinações diferentes permanecem separadas; pilhas de mesma munição e combinação podem se agrupar.
- Consumir o projétil no disparo, mesmo no erro; resolver os testes de veneno somente no acerto e fazer um teste independente por efeito.
- Veneno Rápido é ação livre e custa 1 ponto de sede por frasco; os outros custos e a economia de ação permanecem os atuais.
- Manter a prioridade atual de seleção da munição equipada e da bolsa; não acrescentar escolha de pilha a cada disparo.
- Manter cargas de veneno à distância já salvas na arma até serem consumidas; bloquear novas aplicações de munição nessa arma enquanto existirem cargas legadas.
- Não adicionar nem executar testes automatizados sem solicitação específica do usuário; revisar manualmente os fluxos e os diffs.

## Review Focus

- Uma combinação de dois venenos nunca pode ganhar terceiro efeito ou ser mesclada com uma pilha de combinação diferente; revisão no Task 1 e Task 2.
- A separação de uma pilha parcial não pode perder `ammo_type`, atributos especiais ou IDs de veneno ao mover entre bolsa, mão esquerda, baú e equipamento; revisão no Task 1.
- Validação rejeitada não pode consumir frasco, sede nem munição; revisão no Task 2.
- Disparo normal e Disparo Duplo precisam ler o veneno da pilha efetivamente consumida; erro consome a flecha/virote, acerto resolve cada veneno uma vez; revisão no Task 3.
- Cargas de arma existentes em saves permanecem com o fluxo legado, sem combinar acidentalmente com efeitos da munição; revisão no Task 3.

---

### Task 1: Identidade e preservação das pilhas de munição

**Files:**
- Modify: `server.py` — adicionar normalização e assinatura de pilha; atualizar os caminhos de empilhamento de munição em bolsa, mão esquerda, baú e resgate.
- Modify: `game.js` — ajustar a disponibilidade de empilhamento no inventário/baú para considerar a assinatura da munição.

**Interfaces:**
- Produces: campo persistente `poison_ids: list[str]` em itens `effect == "ammo"`; lista vazia para munição normal e até dois IDs distintos para munição envenenada.
- Produces: helper de servidor `_ammo_stack_key(item) -> tuple`, baseado no identificador/tipo da munição, atributos que alteram seu disparo e conjunto ordenado de `poison_ids`; `ammo_count` não faz parte da chave.
- Consumes: `ammo_type`, `ammo_count`, atributos atuais de munição e `poison_ids` dos itens existentes.

- [x] **Step 1: Definir a chave única de empilhamento**
  Implementar `_ammo_stack_key(item)` e validar/canonicalizar `poison_ids` sem aceitar mais de dois IDs repetidos ou inválidos.
- [x] **Step 2: Aplicar a chave nos caminhos autoritativos de inventário**
  Atualizar merges em `_equip_into_slot`, armazenamento/retirada de baú, resgate e qualquer outro caminho que hoje agrupe munição somente por `ammo_type`.
- [x] **Step 3: Alinhar a interface de armazenamento**
  Atualizar `game.js` onde a UI decide se munição cabe em um stack da mão esquerda ou da bolsa; só indicar merge quando `_ammo_stack_key` lógico for igual.
- [x] **Step 4: Revisão manual dos fluxos cobertos**
  Conferir munição comum, especial, com um veneno e com dois venenos durante equipar, guardar, retirar e mover entre slots. Confirmar que pilhas de combinações diferentes não se fundem.

### Task 2: Preparar munição e confirmar consumo dos frascos

**Files:**
- Modify: `server.py` — criar operação autoritativa comum para aplicar veneno à munição e encaminhar o uso de Veneno Rápido e do frasco genérico.
- Modify: `game.js` — atualizar `abrirPainelVenenoRapido` e o fluxo de uso do frasco para escolher pilha, quantidade e um ou dois venenos.
- Modify: `src/lang/interface.js` — mensagens de seleção, confirmação, bloqueio e custo.

**Interfaces:**
- Produces: handler `handle_envenenar_municao(pid, msg)` que recebe `ammo_source` (`bag` ou `off_hand`), `ammo_index`, `quantity` (1–10), `poison_ids` (1 ou 2 IDs distintos) e `method` (`veneno_rapido` ou `frasco`). Dois IDs exigem `tem_espec(p, "ladino_veneno_3")`.
- Produces: helper `_envenenar_pilha_municao(item, quantity, poison_ids) -> (envenenada, restante)`, que divide a pilha, mantém atributos da munição e não modifica itens até que a validação esteja completa.
- Consumes: `_ammo_stack_key`, lista de venenos disponíveis e estado da habilidade/custos do jogador.

- [x] **Step 1: Implementar a transformação pura da pilha**
  Criar helper que devolva a pilha envenenada e a pilha restante, preservando tipo, atributos especiais e contagem total; bloquear munição já envenenada e quantidades inválidas.
- [x] **Step 2: Implementar a validação e operação transacional do servidor**
  Validar turno, método de aplicação, habilidade III para dois IDs, IDs distintos e válidos, frascos, sede e quantidade existente antes de consumir qualquer recurso. Para Veneno Rápido, descontar 1 sede por frasco e manter ação livre; para o frasco genérico, manter a economia atual.
- [x] **Step 3: Expor o fluxo de seleção na interface**
  Permitir escolher pilha compatível da bolsa/mão esquerda, quantidade 1–10 e um frasco ou, com Veneno Rápido III, dois frascos diferentes. Aplicar confirmação quando a quantidade for menor que 10, informando quantidade, número de frascos e perda da dose restante.
- [x] **Step 4: Manter rejeições sem efeitos colaterais**
  Garantir que pilha já envenenada, terceiro efeito, veneno repetido na combinação, falta de munição, frasco ou sede não consuma nenhum recurso.
- [x] **Step 5: Revisão manual de entradas**
  Conferir quantidades 1, 9 e 10; uma e duas doses; escolha repetida/indisponível; pilha já envenenada; munição normal e especial; cancelamento da confirmação.

### Task 3: Consumir efeitos no combate e preservar saves antigos

**Files:**
- Modify: `server.py` — ataque normal em `handle_attack_impl`, `_executar_disparo_duplo`, consumo de munição e resolução do veneno.

**Interfaces:**
- Consumes: `ammo_source` e pilha retornados pela seleção atual de munição, com `poison_ids`.
- Produces: ao iniciar o disparo, cópia dos IDs de veneno da unidade consumida; no acerto, chamada individual da resolução existente para cada ID.

- [x] **Step 1: Capturar e consumir o estado do projétil**
  Antes de decrementar `ammo_count`, copiar seus `poison_ids`; decrementar/remover exatamente uma unidade na mesma pilha que o fluxo atual escolheu.
- [x] **Step 2: Resolver venenos no ataque principal**
  No acerto, processar cada ID separadamente com a resolução existente de `_aplicar_veneno`; em erro, consumir munição sem fazer testes ou aplicar efeitos.
- [x] **Step 3: Cobrir o Disparo Duplo**
  Fazer `_executar_disparo_duplo` capturar venenos da pilha de virotes que ele próprio consome e resolver cada efeito no acerto da besta secundária.
- [x] **Step 4: Preservar o estado legado da arma**
  Manter `poison_slots` carregados em saves no fluxo atual até esgotar; impedir aplicação nova à munição para a mesma arma enquanto houver cargas antigas. Evitar que uma carga legada e venenos do projétil sejam somados no mesmo ataque.
- [x] **Step 5: Revisão manual do combate**
  Conferir acerto e erro com um e dois venenos, alvo que resiste a apenas um dos efeitos, munição especial, mão secundária e save com carga legada.

### Task 4: Nome, tooltip, mensagens e documentação do contrato

**Files:**
- Modify: `server.py` — `nome_item` e os dados de estado enviados ao cliente.
- Modify: `game.js` — `normalizarItemTooltip` e `gerarConteudoTooltip`.
- Modify: `src/lang/catalogo.js` e `src/lang/interface.js` — nomes, resumos dos venenos e mensagens necessárias nos idiomas existentes.
- Modify: `CLAUDE.md` — atualizar a seção de Veneno Rápido para descrever venenos em munição, testes por projétil e compatibilidade legada.

**Interfaces:**
- Consumes: `poison_ids` e catálogo existente de efeitos de veneno.
- Produces: nome de exibição “Flecha Envenenada” ou “Virote Envenenado”; tooltip com nome e resumo de cada efeito associado.

- [x] **Step 1: Exibir o nome correto sem perder a munição-base**
  Alterar a resolução de nome para indicar flecha/virote envenenado, preservando a quantidade e os qualificadores de munição especial.
- [x] **Step 2: Renderizar o tooltip de um ou dois efeitos**
  Mapear `poison_ids` para o catálogo e renderizar cada nome e resumo no tooltip da munição.
- [x] **Step 3: Atualizar o catálogo de interface e o contrato do projeto**
  Adicionar mensagens de seleção/confirmação/bloqueio necessárias e substituir em `CLAUDE.md` a regra de cargas à distância pela nova regra, documentando a transição de saves.
- [x] **Step 4: Revisão manual de apresentação**
  Conferir nome e tooltip de pilhas normais, especiais, com um veneno e com dois venenos, incluindo exibição da quantidade.

