# Bestiário Global Progressivo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir no perfil de cada conta o conhecimento compartilhado de monstros, com marcos de 15, 30 e 50 abates confirmados.

**Architecture:** O servidor atualiza o perfil permanente da conta no ponto de morte real e publica o nível de conhecimento apropriado para cada jogador. O cliente mantém a consulta rápida no hover e oferece uma ficha deliberada de exame; o Bardo vivo continua sendo uma fonte imediata de conhecimento completo, independente da contagem.

**Tech Stack:** Python (`server.py`, estado e persistência autoritativos), JavaScript (`game.js`, UI), traduções existentes em `src/lang/`.

**Spec:** [2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md](../specs/2026-10-11-ameacas-bestiario-e-etapas-de-missao-design.md), seção 2.

## Global Constraints

- Contar mortes pelo ID estável `monster.type`, nunca pelo nome traduzido.
- Os marcos cumulativos são 15, 30 e 50; nível 15 revela defesas, 30 perfil de combate e 50 ficha completa.
- A passiva Conhecimento das Lendas continua revelando a ficha completa com um Bardo vivo.
- O conhecimento não concede bônus mecânicos e não altera especializações de Lendas.
- Excluir editor, modo de teste, alvos de treinamento e mortes que não sejam finais/confirmadas.
- Persistir no perfil individual da conta e creditar todos os participantes heróis da partida, sem cruzar contas.

## Review Focus

- Morte final que passa por regeneração, resistência automática ou último esforço: só contar quando o servidor confirmar a remoção definitiva.
- Morte sem `killer_pid`, morte por armadilha/ambiente e criatura abatida por outro monstro: aplicar a regra de crédito a todos os participantes da partida.
- Reconexão ou caminhos múltiplos de morte: não duplicar a mesma instância.
- Conta antiga, perfil ausente ou bestiário malformado: migrar para mapa vazio sem apagar os demais campos.
- Conta de Mestre, bot, convidado ou partida de teste: não conceder progresso indevido.

---

### Task 1: Persistência do bestiário por conta

**Files:**
- Modify: `server.py` (`ensure_account_profile`, `write_account`, helpers de acesso a conta)

**Interfaces:**
- Produces: `account.profile.bestiary`, um dicionário `{monster_type: {"kills": int}}`, sanitizado durante migração.
- Reuses: `load_account(username)`, `write_account(account)` e `self.account_by_pid[pid]`.

- [ ] Adicionar inicialização/migração do mapa `profile.bestiary`, preservando campos desconhecidos e ignorando contadores inválidos ou negativos.
- [ ] Criar helper servidor para incrementar um tipo estável e retornar `{kills, level, unlocked_milestone}` com níveis 0/1/2/3 nos limites 0/15/30/50.
- [ ] Fazer a persistência reutilizar `load_account` e `write_account`; não escrever em `savegame.characters` nem criar progresso por herói.
- [ ] Conferir por inspeção de fluxo que duas contas recebem documentos distintos e que conta sem usuário válido não causa falha de jogo.

### Task 2: Crédito idempotente de abates definitivos

**Files:**
- Modify: `server.py` (`GameRoom._monster_dies`, `GameRoom.account_by_pid`, preparação dos participantes)

**Interfaces:**
- Consumes: helper de incremento da Task 1.
- Produces: progresso creditado uma única vez por instância morta e notificação de marcos liberados.

- [ ] Marcar a instância como contabilizada apenas no caminho que confirma morte final, depois de regeneração, resistência morta e habilidades de sobrevivência retornarem sem salvar o monstro.
- [ ] Excluir `training_target`, `test_mode`, criaturas de teste e instâncias sem tipo estável.
- [ ] Creditar participantes heróis autenticados da sala; excluir mestre, NPC, aliado de treino e jogadores que só observam. O crédito não depende do `killer_pid`.
- [ ] Incrementar uma vez por conta por instância, registrar novos marcos sem repetir notificações e deixar mortes anteriores a uma reconexão sem reprocessamento.
- [ ] Notificar apenas quando cruzar 15, 30 ou 50; não mostrar notificação para cada abate.

### Task 3: Estado de conhecimento no payload

**Files:**
- Modify: `server.py` (serialização por jogador em `_game_state_payload` e tooltip payload do monstro)
- Modify: `game.js` (leitura do estado no tooltip)

**Interfaces:**
- Consumes: `profile.bestiary` e cálculo de nível da Task 1.
- Produces: metadado de conhecimento por jogador e tipo de monstro; não envia dados de nível superior ao desbloqueado, salvo Bardo vivo.

- [ ] Localizar o escopo per-player do payload e publicar para cada monstro apenas o nível correspondente à conta conectada.
- [ ] Proteger informação ainda bloqueada: atributos, ataques e habilidades especiais de níveis superiores não devem ser serializados para aquele cliente pelo payload do bestiário.
- [ ] Preservar a revelação completa coletiva já existente quando houver Bardo vivo.
- [ ] Atualizar a ficha aberta após notificação ou novo `game_state`, sem alterar tooltip de inimigo para jogadores sem nível suficiente.

### Task 4: Exame detalhado e tradução

**Files:**
- Modify: `game.js` (hover compacto e ação “Examinar”)
- Modify: `src/lang/tutorial.js` ou arquivos de idioma/UI autoritativos localizados na execução (chaves equivalentes PT/EN)
- Modify: `game.css` (estilo do painel, se necessário)

**Interfaces:**
- Consumes: nível de conhecimento per-player da Task 3.
- Produces: ficha por seções que distingue informação observada, estudada, catalogada e revelada pelo Bardo.

- [ ] Manter o hover curto para nome, PV e CA; acrescentar comando acessível por mouse, teclado e controle para abrir/fechar “Examinar”.
- [ ] Mostrar em cada nível só as seções liberadas pela especificação; estado 0 mantém a informação atual.
- [ ] Adicionar chaves localizadas em português e inglês, sem strings de idioma fixas no cliente.
- [ ] Mostrar notificações de marcos nos dois idiomas e atualizar uma ficha de exame já aberta.
- [ ] Fazer revisão estática do fluxo 2D e 3D, autenticação, marcos e compatibilidade de contas antigas; não alterar dados de campanha.
