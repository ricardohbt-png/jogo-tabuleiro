# Jogos salvos organizados — capítulos, pontos de salvamento e abas Solo/Multiplayer

Data: 2026-10-05 · Estado: aprovado em brainstorming, aguardando revisão do spec

## Problema

- Cada jogo salvo guarda **um único estado** (checkpoint na cidade + `dungeon_snapshot` a cada
  rodada). Não há como voltar a um ponto anterior nem "salvar e continuar jogando" — só
  "💾 Salvar e sair".
- "Meus Jogos" acumula cartões: a conta `richard` vê 9 jogos, 6 deles chamados "campanha", quase
  todos com o mesmo grupo. Cada sessão nova virava um jogo novo, e "Continuar em sequência" cria
  **outro** cartão (`parent_campaign_id`).
- Solo e Multiplayer têm títulos próprios, mas ficam na mesma lista, um embaixo do outro.

## Decisões (brainstorming com o autor)

1. **Vários pontos por jogo:** automáticos rotativos + manuais nomeados; dá para voltar a um
   ponto anterior. No multiplayer só o anfitrião volta.
2. **Multiplayer:** abas Solo | Multiplayer; dentro de Multiplayer, "Que eu hospedo" e "Que eu
   participo".
3. **Sequência = capítulo** dentro do mesmo jogo, não cartão novo.
4. **Saves antigos:** mantidos (cada um vira jogo com 1 ponto) + botão **Arquivar**.
5. **Armazenamento:** o jogo guarda só o **índice** dos pontos; o conteúdo de cada ponto mora num
   documento próprio (abordagem B — o histórico não pesa na gravação por rodada).

Referências de mercado: Baldur's Gate 3 / Divinity (campanha → lista de saves com autosave
rotativo, quicksave e manuais), Terraria/Valheim (menus separados de solo e multiplayer; o mundo é
do anfitrião), Mass Effect (capítulos na mesma linha do tempo).

## Modelo de dados

### Jogo (documento `savegames/<sid>`, existente)

Campos novos (o resto do documento continua sendo o **estado vivo** de hoje — é dele que
"Continuar" parte):

```json
"capitulos": [
  {"n": 1, "nome": "Capítulo 1", "campaign_file": "…", "criado": "<iso>",
   "pontos": [
     {"id": "pt_ab12cd", "tipo": "auto|manual", "nome": "Minas, rodada 4",
      "onde": "cidade|masmorra|cidade_com_masmorra", "local": "Minas",
      "rodada": 4, "criado": "<iso>", "por": "<conta>"}
   ]}
],
"capitulo_atual": 1,
"arquivado_por": ["<conta>", …]
```

- `pontos` é só o índice (metadados para a lista); ordenado do mais novo ao mais antigo.
- `arquivado_por` é **por conta**: arquivar esconde o jogo só para quem arquivou (o convidado
  pode arquivar sem afetar o anfitrião).

### Ponto (coleção nova `pontos`, chave `<sid>_<pt_id>`)

```json
{"sid": "...", "id": "pt_ab12cd", "estado": { …campos mutáveis do jogo… }}
```

`estado` é a cópia profunda das chaves mutáveis do jogo — a MESMA lista que a continuação já copia
hoje (`campaign_phase`, `world_location`, `world_adventure_progress`, `renome`, `fatos`,
`scene_conversations_done`, `members`, `characters`, `slots`, `shortcut_slots`, `refugio`,
`hero_rooms`) **mais** `dungeon_snapshot` e `campaign_file`. A lista vira uma constante única
(`CAMPOS_DO_PONTO`) usada por ponto e por capítulo, para não divergirem.

`COLECOES` ganha `"pontos"`. Apagar um jogo apaga os pontos dele.

## Quando se salva

### Automático (`tipo: "auto"`)

- **Ao entrar numa masmorra** (depois da 1ª foto da visita), **ao voltar à cidade**
  (`_voltar_para_cidade`, depois do checkpoint) e **a cada 5 rodadas** na masmorra
  (`PONTO_AUTO_RODADAS = 5`, na mesma virada de rodada que já grava a foto).
- Mantém só os **3 mais recentes** por capítulo (`PONTOS_AUTO_MAX = 3`); o mais antigo é apagado
  (índice + documento).
- Mesmas guardas da foto: não grava fora de jogo salvo, na sala de teste, com janela pendente nem
  sem herói conectado.
- O estado vivo continua sendo gravado como hoje (checkpoint + foto por rodada); o ponto é uma
  cópia adicional.

### Manual (`tipo: "manual"`)

- Mensagem nova **`salvar_ponto {nome}`** — botão "💾 Salvar" no ⚙️ (só com jogo salvo), ao lado
  de "Salvar e sair". O cliente pede um nome com sugestão "<local>, rodada N" / "<cidade>".
- Qualquer herói do jogo pode salvar (o anfitrião e os convidados); o Mestre também.
- Na masmorra grava o estado do **início da rodada atual** (a foto vigente, como o "Salvar e
  sair"); se ainda não há foto da visita, grava uma antes. Nunca o meio de uma ação.
- Teto de **10 manuais por capítulo** (`PONTOS_MANUAIS_MAX`); acima disso recusa com
  `erro.limite_de_pontos_manuais` pedindo para apagar um.
- Responde `ponto_salvo {ponto}` a quem pediu e faz broadcast do aviso "💾 Progresso salvo" já
  existente (`_avisar_salvo`).
- "Salvar e sair" passa a criar também um ponto automático.

## Carregar um ponto anterior

- **Só pela tela "Meus Jogos"**, com o jogo **fechado** (nenhuma sala aberta dele em
  `SAVEGAMES_IN_USE`). Não há volta no tempo dentro da partida.
- Mensagem nova **`carregar_ponto {savegame_id, ponto_id}`**; permissão: Solo → o dono; Multiplayer
  → só o anfitrião (`owner`; com Mestre, o `master_account`). Senão `erro.so_o_anfitriao_carrega`.
- Antes de sobrescrever, o estado vivo vira um ponto automático **"Antes de carregar <nome>"**
  (desfazível; conta na rotação dos automáticos).
- Copia `estado` do ponto para o documento do jogo, regrava e devolve a lista atualizada. O próximo
  "Continuar" retoma dali pelo caminho de hoje (`dungeon_snapshot` → `_retomar_masmorra`).
- Ponto de capítulo anterior pode ser carregado: o jogo volta a esse capítulo (`capitulo_atual`).
- Apagar ponto: **`apagar_ponto {savegame_id, ponto_id}`**, mesma permissão de carregar.

## Capítulos ("Continuar em sequência")

- O botão do cartão passa a mandar **`novo_capitulo {savegame_id, nome, campaign_file}`**
  (anfitrião/dono). Fecha o capítulo atual com um ponto automático "Fim do capítulo N", cria o
  capítulo N+1 com a campanha escolhida, zera `campaign_phase` e limpa `dungeon_snapshot`, mantendo
  heróis, ouro, Refúgio e progresso de mundo — o mesmo que a continuação copia hoje.
- `create_savegame(... continue_from=...)` deixa de ser chamado pelo cliente; o caminho continua
  no servidor só para compatibilidade e testes antigos.

## Tela "Meus Jogos"

- **Abas** Solo | Multiplayer com contagem; a aba escolhida fica em `localStorage`
  (`lfh_aba_jogos`). Só a aba ativa é desenhada.
- Multiplayer: grupos **"Que eu hospedo"** (`owner == conta` ou `master_account == conta`) e
  **"Que eu participo"** (demais).
- **Um cartão por jogo:** iniciais/retratos dos heróis, nome, "Capítulo N · <onde parou> · <quem
  joga> · há X tempo", botão principal "Continuar" (convidado: "Entrar") e seta que expande os
  pontos.
- Expandido: pontos do capítulo atual (ícone relógio = auto, marcador = manual), com "Carregar" e
  🗑 só para quem pode; capítulos anteriores recolhidos ("Capítulo 1 — 4 pontos guardados").
- Menu do cartão: Arquivar/Desarquivar, Novo capítulo (anfitrião), Apagar jogo (dono), Encerrar
  (Mestre — já existe).
- **Arquivados (N)** no fim da aba, recolhido.
- `list_savegames` acrescenta `capitulos` (só índices), `capitulo_atual`, `arquivado` (para a conta
  que pediu) e `anfitriao`. Mensagem nova **`arquivar_jogo {savegame_id, arquivado}`**.

## Migração dos saves existentes

Em `ensure_campaign_schema` (já roda na carga e na listagem):

- Sem `capitulos`: cria o capítulo 1 com **um ponto automático "Estado salvo"** copiando o estado
  vivo (`onde`/`rodada` do resumo da foto, se houver).
- Jogo com `parent_campaign_id` cujo pai existe e é do mesmo dono: vira o capítulo seguinte do pai
  (pontos movidos para o pai; o filho é apagado só depois de o pai ser gravado com sucesso). Pai
  inexistente → fica como jogo próprio (é o caso de `sg_toref8`).
- `play_mode` ausente: mantém a inferência de `_savegame_play_mode`.
- Idempotente: rodar duas vezes não duplica pontos nem capítulos.

## Fora de escopo

- Progresso da Guilda (`saves/<class_id>.json`) continua por classe, fora do jogo — carregar um
  ponto não desfaz compras na Guilda.
- Voltar no tempo com a partida aberta.
- Sair de um jogo multiplayer como convidado (remover-se dos membros).
- Juntar automaticamente jogos diferentes de mesmo nome.

## Idioma

Todos os textos novos com chave `ui.savegames.*` / `ui.save.*` (cliente) e `erro.*` (servidor), pt
e en; `tools/dividas.py` sem pendências ao fechar.

## Testes

- `tools/test_pontos_salvamento.py` (servidor): rotação dos 3 automáticos; teto de 10 manuais;
  salvar ponto no meio da masmorra grava a foto da rodada; carregar copia o estado e cria "Antes de
  carregar"; convidado não carrega nem apaga; carregar com sala aberta é recusado; novo capítulo
  mantém heróis e zera a fase; migração (save simples → 1 ponto; continuação com pai → capítulo;
  idempotência); arquivar por conta; apagar jogo apaga os pontos; `test_salvar_masmorra` [2] cobre
  os campos novos de `GameRoom`, se houver.
- Ponta a ponta pelo `server.handler` real: salvar ponto, sair, carregar ponto anterior, continuar e
  conferir rodada/casa/PV do ponto.
- Cliente (node): agrupamento por aba e por anfitrião/convidado; a aba escolhida persiste.
- Navegador: tela com as duas abas, cartão expandido, salvar pelo ⚙️ em jogo, carregar e continuar.
