# Sub-projeto A — Framework de Arremessáveis + Itens de Fogo

**Data:** 2026-07-09
**Status:** aprovado (brainstorming)

## Contexto

O jogador quer adicionar ~13 itens novos ao mercado, divididos em 5 famílias de
mecânica. Este spec cobre **apenas o Sub-projeto A**: o framework de itens
arremessáveis/consumíveis de bolsa e os dois itens de fogo single-target.

Decomposição do conjunto completo (para referência; cada sub-projeto tem seu
próprio spec → plano → implementação):

| Sub-projeto | Itens | Mecânica nova |
|---|---|---|
| **A (este)** | Frasco de Óleo Incendiário, Fogo Grego | Framework de bolsa→mira→arremesso, teste de ataque por DES, status "em chamas", apagar com Água/ação |
| B | Bomba Incendiária, Granada Explosiva, Granada Superior, Bomba de Fumaça | Mira de área (tiles verdes), save de Reflexos, fumaça = escuridão |
| C | Frasco de Ácido, Vidro de Ácido Grande | Dano residual + corrosão de equipamento |
| D | Cola Alquímica, Rede | Controle (mov reduzido / preso, save p/ escapar) |
| E | Agonia Sufocante | Novo veneno no catálogo (`coat_poison`), trivial |

O Sub-projeto A cria o **framework** que B, C e D reaproveitam. O framework já
nasce ciente dos dois modos de mira (`ataque_alvo` e `area`), mas A só exercita o
modo single-target (tiles vermelhos).

## Infraestrutura existente reaproveitada

- **`handle_throw`** (arremesso de adaga): molde de teste de ataque por DES vs CA,
  checagem de alcance + linha de visão (`_tem_linha_de_visao`). Os novos itens são
  **consumíveis de bolsa**, não armas equipadas — então NÃO reusam `handle_throw`
  direto, mas seguem o mesmo padrão de rolagem.
- **Mira de magia** (`bola_fogo`/`relampago`): já pinta tiles-alvo e resolve save.
  A UI de mira do cliente (`pendingSkill`/`pendingMagia`, `get3DTilePlane`) é o
  molde do novo `pendingThrow`.
- **`_processar_efeitos_armadilha_turno`**: tick 1×/rodada do dano progressivo da
  incendiária. Vai ser generalizado para também varrer o status "em chamas" dos
  entes (heróis e monstros) e mandar o mesmo popup de tick (`trap_result`).
- **`garrafa_agua`** / **`cantil_agua`**: itens de água existentes — servem como o
  "Frasco de Água" que apaga as chamas.
- **`ARMADILHAS` / `GRIMORIO`**: estilo de catálogo declarativo a seguir no novo
  `ARREMESSAVEIS`.

## Decisões de design

1. **Interação:** clique **direito** num consumível da bolsa = "usar/ativar".
   Regra ÚNICA — poção e pergaminho migram do clique esquerdo para o direito
   também. O clique esquerdo continua só selecionando/movendo/equipando.
2. **Custo de ação do arremesso:** **ação principal** (igual a atacar/lançar magia).
3. **Empilhar "em chamas":** pegar fogo de novo enquanto já queima faz a duração
   virar o **maior** valor entre o atual e o novo (refresh, NÃO soma dano).
4. **Apagar com água:** **ação livre** (só consome 1 água) — é a via conveniente.
5. **Apagar batendo:** gasta a **ação principal** do turno.
6. **Qualquer classe** usa os arremessáveis (item de bolsa, sem restrição de classe).

## Componentes

### 1. Modelo de interação (cliente — `game.js` / `inventoryModal.js`)

- Clique direito (`contextmenu`, com `preventDefault`) num slot de bolsa com item
  usável dispara "usar". Migra o "usar" atual de poção/pergaminho (hoje no
  `slot.onclick`) para o handler de clique direito. O clique esquerdo passa a só
  selecionar/arrastar.
- Para item arremessável de mira: usar → **fecha o modal** + entra em **modo-alvo**
  (`pendingThrow`, análogo a `pendingSkill`), pintando o **alcance em tiles
  vermelhos** (mira de ataque single-target). O alcance é Chebyshev ≤ `alcance` do
  item a partir da casa do jogador, respeitando linha de visão.
- Clicar num monstro dentro do alcance → envia `throw_item`. Clicar fora / Esc /
  botão de cancelar → sai do modo-alvo sem gastar nada.
- Funciona em 2D (canvas) e 3D (`get3DTilePlane`), reusando o hook de clique de
  tile já unificado (`handleTileClick`).
- Tiles **verdes de área** ficam pro Sub-projeto B; o framework já reconhece
  `alvo: "area"`, mas nenhum item de A usa.

### 2. Camada de estado do cliente (`src/gameState.js`)

- Estado de UI `pendingThrow` (item selecionado para mira) + getters/setters.
- Action sender `throwItem(itemId, targetId)` → `send({type:'throw_item', item_id, target_id})`.
- Getters de leitura para o render: alcance/alvo do item (lidos do próprio item da
  bolsa, que carrega os campos do catálogo), e helpers de "casa mirável".
- ZERO DOM/THREE aqui (regra de arquitetura).

### 3. Framework no servidor (`server.py`)

- Novo catálogo declarativo **`ARREMESSAVEIS`** (dict id→def), cada def com:
  - `id`, `name`, `emoji`, `price`, `item_slot: "bag"`, `effect: "throwable"`
  - `alcance` (int, quadrados)
  - `alvo` (`"ataque_alvo"` | `"area"` — A só usa `ataque_alvo`)
  - `dano` (string de dado, ex. `"1d6"` / `"2d6"`)
  - `elemento` (ex. `"fogo"`)
  - `em_chamas` (bool) + `chamas_agua_apaga` (bool)
- Os itens de loja apontam para o catálogo (ficam vendáveis no mercado). Entram na
  lista de itens da loja com `effect: "throwable"`.
- Nova mensagem **`throw_item`** (`item_id`, `target_id`) → **`handle_throw_item`**:
  1. Valida turno (`_is_turn`), jogador vivo, ação principal disponível
     (`_acao_bloqueada` — mesmo helper de ataque/magia, cobre Velocidade/Oportunidade).
  2. Acha o item na bolsa; recusa se não for arremessável.
  3. Valida alvo (monstro existente), alcance (Chebyshev ≤ `alcance`) e
     **linha de visão** (`_tem_linha_de_visao`).
  4. Rola **ataque por DES** vs CA do alvo (`d20 + atk_bonus`; nat1 falha, nat20
     crítico) — broadcast `dice_roll`.
  5. **Acerto:** rola `dano`, aplica dano do elemento (`_dano_em_alvo`), aplica o
     status `em_chamas` se `em_chamas`. Crítico dobra o dano inicial (o tick de
     fogo permanece 1/rodada fixo). Mata via `_monster_dies` se HP ≤ 0.
  6. **Erro/nat1:** sem dano/status.
  7. **Consome o item da bolsa em acerto E erro** (o frasco se espatifa).
  8. Marca `action_done` + consome recursos de sobrevivência; `push_state`.
- Sem restrição de classe.

### 4. Status "em chamas" (`server.py`)

- Campos no ente (herói ou monstro): `em_chamas_rodadas` (int) + `chamas_agua_apaga`
  (bool).
- Aplicação (`_aplicar_em_chamas(alvo, rodadas, agua_apaga)`): define
  `em_chamas_rodadas = max(atual, rodadas)` (refresh), grava `chamas_agua_apaga`.
- **Tick:** generalizar `_processar_efeitos_armadilha_turno` (ou um novo passo
  irmão chamado no mesmo ponto do loop de rodada, linha ~11837) para varrer os
  entes em chamas: 1 de dano de fogo, decrementa `em_chamas_rodadas`, manda popup
  de tick (`trap_result` com `tick:true`, ícone 🔥) ao jogador afetado (ou ao
  `rescuer_pid` se for o prisioneiro; monstros não recebem cliente). Ao chegar a 0,
  limpa o status.
- Serializa `em_chamas_rodadas` no `game_state` (jogadores e monstros) para o render.

### 5. Apagar o fogo (`server.py` + cliente)

- **Beber Água:** em `handle_use_item`, quando o item for `garrafa_agua`/
  `cantil_agua` E o jogador estiver `em_chamas_rodadas > 0` E `chamas_agua_apaga`:
  apaga o status, consome 1 água, **NÃO gasta ação** (ação livre). (Fora de chamas,
  a água mantém o comportamento normal de matar sede.)
- **Bater pra apagar:** nova mensagem `apagar_chamas` → `handle_apagar_chamas`:
  gasta a **ação principal**, zera `em_chamas_rodadas`. Botão "🔥 Apagar chamas" no
  HUD (`renderMyPanel`) quando `em_chamas_rodadas > 0`.
- **Fogo Grego** (`chamas_agua_apaga=False`): a via da água recusa (mensagem
  explicativa); só `apagar_chamas` (ação) funciona.
- Monstros não apagam (sem IA) — queimam até a duração acabar.

### 6. Itens (loja/mercado)

| Item | id | Emoji | Alcance | Ataque | Dano | Em chamas | Água apaga? | Preço |
|---|---|---|---|---|---|---|---|---|
| Frasco de Óleo Incendiário | `frasco_oleo` | 🔥 | 4 | DES vs CA | 1d6 fogo | 1/rod., 1d4 rod. | Sim | 15 🪙 |
| Fogo Grego | `fogo_grego` | 🟢 | 4 | DES vs CA | 2d6 fogo | 1/rod., 1d4 rod. | **Não** | 40 🪙 |

### 7. Render (`game.js`)

- Modo-alvo: alcance em tiles **vermelhos** (2D e 3D), reusando a maquinaria de
  destaque de mira das magias.
- Ente em chamas: indicador visual 🔥 sobre o peão (2D e 3D) enquanto
  `em_chamas_rodadas > 0`.
- Frasco arremessado: emoji voando (2D) / sprite (3D) — pode reusar o feedback já
  usado por arremesso/magia; animação elaborada é opcional (YAGNI).

### 8. Testes (`tools/test_arremessaveis.py`)

- Acerto: dano correto, item consumido, status aplicado.
- Erro / nat1: sem dano/status, item consumido.
- Fora de alcance / sem LOS: recusa, item NÃO consumido, ação não gasta.
- Tick de fogo: dano 1/rodada em herói e em monstro; duração decrementa; expira em 0.
- Refresh de duração (empilhar = max, não soma).
- Apagar com água: ação livre, consome água, some o status (só Óleo).
- Fogo Grego ignora água; só a ação (`apagar_chamas`) apaga.
- Crítico dobra o dano inicial; tick permanece 1/rodada.

## Fora de escopo (deste sub-projeto)

- Mira de área / tiles verdes / save de Reflexos (Sub-projeto B).
- Corrosão de equipamento (Sub-projeto C).
- Efeitos de controle: cola/rede (Sub-projeto D).
- Veneno Agonia Sufocante (Sub-projeto E).
- Animação 3D elaborada do projétil.
