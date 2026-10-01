# Salvar a aventura (solo e multiplayer) — design para revisão

**Data:** 2026-10-01 · **Status:** decisões tomadas; Etapa 1 (ajustada) implementada,
Etapa 2 adiada.

## 0. Decisões do autor (2026-10-01) e o que foi feito

1. **Só "entrar com conta".** O jogo rápido sem salvamento saiu da tela inicial
   (botão "Criar Nova Sala" e entrada por código sem conta). A tela inicial tem
   apelido, servidor, senha e "🎲 Entrar". Os jogos salvos ficam na conta. O
   handler `create_room` continua no servidor: o editor ("Testar como Mestre")
   e as suítes de teste o usam.
2. **Escolher um jogo salvo pula a escolha de personagem.** Quem já tem
   personagem vinculado entra com ele marcado (`_continuar_jogo_salvo`, chamado
   em `add_player`). No jogo **solo** (1 membro, sem Mestre) a partida começa
   direto na cidade: o servidor manda um `lobby_state` com `auto_start:true`
   (o cliente aprende o pid e o código e não desenha a tela de herói) e chama
   `start_game`. Em **grupo**, o lobby continua como sala de espera do
   anfitrião, com os heróis já marcados. Criar jogos novos segue igual.
3. **Salvar só o progresso da cidade.** Já era o comportamento dos pontos
   seguros, com uma exceção corrigida: alguns salvamentos rodavam no meio da
   masmorra (forma de Metamorfose desbloqueada em combate, opções do ⚙️, cenas
   de campanha) e gravavam a ficha de quem estava lá dentro — o loot de uma
   masmorra inacabada ficava salvo enquanto ela recomeçava, o que deixava
   repetir o saque. Agora `_checkpoint_savegame` pula, com o grupo na masmorra,
   quem está lá dentro; quem subiu pela escada (`fora_masmorra`) está na cidade
   e é gravado. A Etapa 2 (foto da masmorra) fica para depois.
4. **Retomar sem o anfitrião; quem entra primeiro assume.** Qualquer membro de
   jogo sem Mestre já podia abrir o jogo. O que faltava: o segundo membro que
   clicava em Continuar recebia "jogo já em uso". Agora
   `sala_aberta_do_jogo_salvo` + `entrar_em_jogo_salvo_aberto` o levam à sala
   aberta: no lobby entra normalmente; com a partida na cidade entra com a ficha
   salva (`entrar_com_jogo_em_andamento`); com o grupo na masmorra chega como
   quem subiu a escada (`fora_masmorra` com espera 0) e desce na rodada seguinte
   ou pelo botão "Voltar à masmorra"; quem caiu é religado à mesma identidade
   (`religar_heroi`/`religar_mestre`, extraídos do `rejoin`). Sem anfitrião
   conectado, quem chega assume (`_assumir_anfitriao_se_vago`); o Mestre nunca
   perde o posto por uma queda. Jogo com Mestre continua só abrindo pelo Mestre.

**Jogador novo com a partida em andamento (2026-10-01, depois):** quem não
tem personagem no jogo entra pelo código ("Meus Jogos" → código do amigo) mesmo
com o grupo na cidade ou na masmorra. Ele fica numa sala de espera
(`GameRoom.aguardando`, fora de `players`/`connections`, então não recebe o
estado da partida) e recebe um `lobby_state` só dele (`_enviar_escolha_tardia`:
`entrada_tardia:true`, `host:null`, `taken_classes` com as classes dos heróis na
sala e as de membros ausentes). Escolher o herói (e as 2 magias, para mago e
clérigo) chama `_tentar_entrada_tardia`, que o leva para dentro pelo mesmo
caminho do membro que chega atrasado. Com entrada por votação, o pedido abre a
votação e ele espera; aprovado, entra; recusado, volta a escolher. A votação
deixou de mandar `lobby_state` fora do lobby (antes jogaria o grupo na tela de
heróis). Quem desiste no meio sai da sala de espera.

Teste: `tools/test_continuar_jogo.py` (66 checks, pelo `server.handler` real).

## 1. Problema

O jogador relata que "sempre começa do início". O sistema de jogos salvos já
existe e funciona (conta → "Meus Jogos" → Continuar), mas tem duas lacunas:

1. **O caminho mais visível não salva.** "⚔ Criar Nova Sala" (`createRoom` →
   `create_room`) cria uma `GameRoom` sem `savegame`; tudo se perde ao fechar.
   Salvar exige entrar com conta, e isso não fica evidente.
2. **A masmorra em andamento não é salva.** `_checkpoint_savegame` grava só o
   que é durável na cidade. Quem fecha o jogo no meio de uma masmorra volta à
   cidade com a ficha de antes de entrar: mapa, monstros mortos, baús abertos,
   loot e XP ganhos lá dentro se perdem.

Há ainda um detalhe que agrava a lacuna 2: **dentro da mesma sessão**, voltar
da cidade já retoma a mesma masmorra (`dungeon_generated=True`,
`server.py:9695`). Só que isso vive só na memória. Se a sala cai (todos saem
por mais de 15 min, `SALA_VAZIA_TTL_S`) ou o servidor reinicia, a masmorra
meio feita é perdida e uma nova é gerada.

## 2. O que já existe (não muda)

| Peça | Onde |
|---|---|
| Armazenamento em cache + descarga diferida nos pontos seguros | `LOJA`, `_agendar_descarga` (`server.py:1719-1935`) |
| Documento do jogo salvo | `create_savegame` (`server.py:2248`) |
| Ficha durável (lista explícita de campos) | `_DURABLE_FIELDS`, `snapshot_character`, `restore_character` (`server.py:2516-2576`) |
| Abrir jogo salvo numa sala nova | `try_open_savegame_room` (`server.py:2583`) |
| Gravação nos pontos seguros | `_checkpoint_savegame` (`server.py:21940`), chamada em ~25 lugares |
| Um jogo salvo aberto por vez | `SAVEGAMES_IN_USE` |
| Vínculo conta ↔ personagem no multiplayer | `select_class` com `savegame` (`server.py:10082`) |
| Reconexão dentro da mesma sala (F5/queda) | `rejoin` + `lfh_session` no `localStorage` |
| Tela "Meus Jogos" com Continuar | `GS.on('savegamesList')` (`game.js:51573`) |

O plano reaproveita tudo isso. Nada de mecanismo de persistência novo: a foto da
masmorra entra **dentro do mesmo documento do jogo salvo**, pela mesma `LOJA`.

## 3. Visão geral

Duas etapas independentes, entregues e revisadas separadamente.

- **Etapa 1 — salvar à vista** (pequena, só cliente e um pouco de servidor).
  Torna o caminho que salva o caminho padrão e tira atritos ao continuar.
- **Etapa 2 — foto da masmorra** (grande, servidor + um pouco de cliente).
  Ao continuar um jogo salvo, o grupo volta para dentro da masmorra, no ponto em
  que parou (início da rodada mais recente).

---

## 4. Etapa 1 — salvar à vista

### 4.1 Tela inicial

- **Cartão "▶ Continuar"** no topo do `screen-connect`, quando o navegador
  lembra a última conta usada (`localStorage["lfh_ultima_conta"]`: só o
  apelido, **nunca a senha**). Mostra o nome do jogo e "onde parou" (ex.:
  "Alva e Luz — cidade" ou, depois da Etapa 2, "Minas — rodada 7"). O clique
  pede a senha (o campo já existe) e abre direto o jogo salvo: login →
  `load_savegame` com o id guardado em `localStorage["lfh_ultimo_jogo"]`.
- **Reordenar os botões:** "Entrar com minha conta" vira o botão principal,
  com o texto "🎲 Jogar (salva o progresso)". "Criar Nova Sala" fica abaixo,
  menor, com o texto "Jogo rápido — não salva".
- Ao clicar em "Jogo rápido", um aviso curto, uma vez por navegador: "Este modo
  não guarda progresso. Para continuar outro dia, entre com uma conta."
  (Pode ser desligado com "não mostrar de novo".)

### 4.2 Continuar sem repetir a escolha de personagem

Hoje, ao abrir um jogo salvo, cada jogador volta ao lobby e escolhe a classe de
novo, mesmo já tendo um personagem vinculado (`members[conta].class_id`).

- Em `add_player`, quando a sala tem `savegame` e a conta já tem `class_id`
  vinculado, chamar `select_class` automaticamente com essa classe.
- **Solo:** se o jogo salvo tem um único membro e nenhum Mestre, e esse membro
  acabou de entrar com o personagem vinculado, o lobby inicia sozinho
  (`start_game`). O jogador cai direto na cidade (ou, com a Etapa 2, na
  masmorra).
- **Multiplayer:** o lobby continua existindo (o anfitrião espera os amigos),
  mas cada um já entra com o personagem marcado. O anfitrião pode iniciar sem
  esperar todos: quem chegar depois entra como hoje.

### 4.3 Dentro do jogo

- **Aviso "💾 Progresso salvo"**: o servidor manda `{type:"saved", where}` ao
  final de `_checkpoint_savegame`; o cliente mostra um toast discreto
  (no máximo 1 a cada 30 s, para não poluir a tela durante as compras).
- **"💾 Salvar e sair"** no painel ⚙️, só quando a sala tem jogo salvo:
  - Na cidade: força `_checkpoint_savegame`, confirma e volta para "Meus Jogos".
  - Na masmorra, **antes da Etapa 2**: avisa "Na masmorra, o progresso desde a
    entrada será perdido. O último salvamento é da cidade." e pede confirmação.
  - Na masmorra, **depois da Etapa 2**: grava a foto (ver 5.4) e sai.
- Em "Jogo rápido", o item do ⚙️ aparece desabilitado com a dica "Jogo rápido
  não salva".

### 4.4 Arquivos tocados (Etapa 1)

- `game.js`: tela inicial, cartão Continuar, toast, item do ⚙️.
- `src/gameState.js`: `GS.salvarESair()`, evento `saved`, guardar
  `lfh_ultima_conta`/`lfh_ultimo_jogo`.
- `server.py`: auto-seleção em `add_player`, início automático solo, mensagem
  `saved`, handler `salvar_e_sair`.
- `src/lang/interface.js` + `src/lang/erros.js`: chaves pt/en.
- Teste: `tools/test_salvar_etapa1.py` (auto-seleção, início solo, `saved`
  emitido, `salvar_e_sair` só com jogo salvo).

---

## 5. Etapa 2 — foto da masmorra

### 5.1 Ideia

Guardar no jogo salvo um campo novo `dungeon_snapshot` com tudo o que é preciso
para reconstruir a `GameRoom` dentro da masmorra. Ao abrir o jogo salvo, se a
foto existir, o grupo é recolocado na masmorra em vez de ir para a cidade.

O formato segue o princípio de `_DURABLE_FIELDS`: **lista explícita do que se
grava**, nunca "salvar o objeto inteiro". Campo novo de sala que não estiver na
lista simplesmente não é salvo, e um teste aponta isso (ver 5.8).

### 5.2 O que entra na foto

**Sala** (atributos de `GameRoom`; ~147 definidos no `__init__`, mais 13 criados
depois):

| Grupo | Campos | Observação |
|---|---|---|
| Identidade | `mode`, `selected_dungeon`, `dungeon_def` (só o nome do arquivo), `world_adventure_id`/`_index`/`_revisit`, `campaign_phase` | A masmorra autorada é **recarregada do arquivo** e o resto sobreposto. Se o arquivo mudou de tamanho (`map_w/h` ou `tiles` diferentes), a foto é descartada com aviso. |
| Mapa | `tiles`, `map_w`, `map_h`, `rooms`, `door_rooms`, `opened_doors`, `stairs_pos`, `exit_pos`, `materiais`, `elevacoes`, `pontes`, `secret_passages`, `door_conditions`, `door_condition_activated`, `decorations`, `ambiente` | `tiles` sempre salvo (o procedural não tem arquivo; e paredes podem mudar em jogo). |
| Exploração | `explored`, `magic_reveal`, `salas_visitadas` | Conjuntos de tuplas → listas de `[x,y]`. |
| Criaturas | `monsters`, `corpses`, `hero_corpses`, `prisoner`, `rescue_failed` | Dicts de monstro já são simples; checar referências cruzadas (ver 5.6). |
| Mundo | `chests`, `ground_items`, `traps`, `armadilhas`, `_armadilha_seq`, `zonas_especiais`, `falas`, `licoes`, `licoes_feitas`, `master_reserve`, `key_chest_opened` | |
| Objetivos | `objectives`, `objective_status`, `_objetivo_concluido`, `mission_complete_pending` | |
| Turno | `round_num`, `initiative_order`, `initiative_index`, `turn_index`, `player_order`, `temp_def`, `blessed` | `initiative_order` é recalculada no início da rodada; ver 5.4. |
| Contadores | `_elemental_seq`, `_attack_feedback_seq` e afins | Evitam ids repetidos depois de retomar. |

**Heróis:** a ficha **inteira** de cada herói (posição, `moves_left`, buffs,
recargas, slots de magia, status, `facing`, `fora_masmorra`…), não só
`_DURABLE_FIELDS`. Chaveada por `class_id`, como `characters`, porque o `pid`
muda a cada conexão.

**Não entra (recriado ou descartado ao retomar):**

- Conexões e identificadores de conexão: `connections`, `account_by_pid`,
  `master_pid`, `host_pid`, `_ws`, `ip`.
- Tudo que é `asyncio` e janela aberta: `*_event`, `*_timer`, `*_task`,
  `*_deadline`, `master_manual_mid`, `command_control_*`, `mind_control_*`
  (o controle volta como estado do monstro, não como janela aberta),
  `last_stand_*`, `sorte_reacao`, `_fire_prompt`, `_pending_teleporte`,
  `_pending_metamorfose`.
- Filas efêmeras de feedback visual: `_combat_damage_events`,
  `_positive_effect_events`, `_resistance_events`, `_damage_visual_context`,
  `_condition_alerts`, `_survival_alerts`.
- Índices derivados, reconstruídos por `_rebuild_decor_index` e afins:
  `_decor_*_tiles`, `_campfire_tiles`, `_fire_damage_tiles`, `_mat_*_tiles`,
  `_ponte_*`.
- `gm_log`: contém objetos `T` (texto tardio). Salvar as últimas ~20 entradas
  já renderizadas em pt **não** serve (o log é traduzido por jogador). Decisão
  proposta: não salvar o log; ao retomar, uma única linha "📜 A aventura
  continua…". *(Ponto para o autor decidir — ver §7.)*
- Sala de teste do editor (`test_mode`, `test_combat`): nunca grava.

### 5.3 Formato e conversões

```text
savegame.dungeon_snapshot = {
  "versao": 1,
  "gravado_em": "2026-10-01T20:15:00Z",
  "onde": "masmorra" | "cidade_com_masmorra",
  "sala":   { …campos da tabela 5.2… },
  "herois": { "<class_id>": { …ficha inteira… } },
}
```

- Conversões em funções puras e testáveis, `_foto_codificar(valor)` e
  `_foto_decodificar(valor, esquema)`:
  - `set` de tuplas → lista de pares, ordenada (assim duas gravações iguais dão
    o mesmo JSON e é fácil comparar);
  - `dict` com chave tupla (`materiais`, `elevacoes`, `magic_reveal`,
    `door_rooms`) → lista de `[[x,y], valor]`;
  - `T` → recusado (falha alta no teste, não silenciosa).
- `versao` permite migrar fotos antigas quando o formato mudar. Versão
  desconhecida → foto descartada com aviso, jogo continua da cidade.
- Tamanho estimado: um `game_state` sem o catálogo de metamorfose fica em torno
  de 20–30 KB; a foto deve ficar na mesma ordem. Os jogos salvos inteiros hoje
  somam ~1,3 MB, então cabe no cache em memória com folga.

### 5.4 Quando gravar

Gravar a cada ação seria caro e arriscado (estado no meio de uma resolução).
Proposta, do mais frequente ao mais raro:

1. **Início de cada rodada**, dentro de `_virada_de_rodada`, **só se não houver
   janela pendente** (manual do mestre, Comando, Dominar Mente, Último
   Esforço, Sorte, prompt de fogo, Improviso). Se houver, pula esta rodada e
   tenta na próxima. É o "ponto seguro" da masmorra: ninguém está no meio de um
   turno.
2. **"💾 Salvar e sair"** (Etapa 1): grava a foto da **última virada de rodada**
   (guardada em memória), não do instante atual. Assim o jogador nunca salva no
   meio de um ataque. O efeito para ele é perder no máximo a rodada em curso;
   a confirmação diz isso.
3. **Ao voltar para a cidade com a masmorra ainda em aberto**
   (`dungeon_generated=True`): `onde="cidade_com_masmorra"`. Resolve o caso em
   que a masmorra meio feita sumia quando a sala caía.
4. **Apagar a foto** quando a masmorra termina (`dungeon_generated=False` nos 5
   pontos que já fazem isso: `server.py:43829-44025`), na derrota total e ao
   emendar a próxima etapa (`_emendar_proxima_etapa` grava a foto da nova).

Todas usam `write_savegame` + `_agendar_descarga()`, como os checkpoints atuais.
A trava da descarga já junta rajadas: uma virada de rodada a cada ~30 s não
muda o padrão de acesso ao armazenamento.

### 5.5 Como retomar

1. `try_open_savegame_room` monta a sala como hoje e, se houver foto, guarda-a
   em `room._foto_pendente` (ainda não aplica: falta saber quem está jogando).
2. Lobby → `start_game` como hoje (com a auto-seleção da Etapa 1). No fim de
   `start_game`, em vez de `phase="city"` + `broadcast_city_state`:
   - `onde="masmorra"`: chama `_retomar_masmorra(foto)`.
   - `onde="cidade_com_masmorra"`: vai à cidade normalmente, mas aplica a parte
     de masmorra da foto e marca `dungeon_generated=True`; a próxima entrada
     retoma em vez de gerar.
3. `_retomar_masmorra(foto)`:
   - recarrega a masmorra autorada do arquivo (ou nada, se procedural) e
     sobrepõe os campos da foto;
   - para cada herói presente, sobrepõe a ficha da foto pelo `class_id` no
     player recém-criado, mantendo `id`/`name`/`slot` da conexão nova (mesmo
     cuidado de `restore_character`);
   - **herói da foto sem jogador presente** (multiplayer, amigo que ainda não
     entrou): é criado como jogador desconectado, exatamente como
     `handle_disconnect_em_jogo` o deixa hoje — fora do tabuleiro, fora da
     iniciativa, fora dos alvos (`_ativo` é falso). Quando o amigo entrar com a
     conta, o caminho de entrada tardia o recoloca na sua posição salva (ou numa
     casa livre ao lado, se ocupada), como `_reentrar_masmorra` já faz;
   - reconstrói índices (`_rebuild_decor_index` e afins);
   - `phase="playing"`, `initiative_active=True`, monta a iniciativa da rodada
     salva e ativa o primeiro ator com `_start_initiative_player_turn` /
     prólogo de monstro, **como o início de qualquer rodada**;
   - manda `enter_dungeon` + `game_state` a todos e narra "📜 A aventura
     continua — rodada N".
4. Mestre humano: volta a ser o Mestre (o jogo salvo já sabe a conta). Monstros
   em modo Manual continuam Manual; a janela é aberta normalmente quando chegar
   a vez deles.

### 5.6 Riscos e como tratá-los

| Risco | Tratamento |
|---|---|
| Campo de sala/herói que não é JSON (tupla, `set`, `T`, objeto `asyncio`) | Codificador recusa tipos desconhecidos; teste de ida e volta em todas as masmorras de exemplo e da campanha. |
| Campo novo adicionado no futuro e esquecido | Teste que lista os atributos de `GameRoom` e exige que cada um esteja em "salva" ou em "não salva", com motivo. Mesmo modelo do `test_modo_publico.py` com `HANDLERS_ESCRITA`. |
| Referência cruzada por objeto (ex.: monstro guardando o dict do herói em vez do id) | Varredura no teste: depois de decodificar, nenhum objeto pode aparecer em dois lugares (`id()` repetido). Onde houver, trocar por id. |
| Estado que só existe numa janela aberta | Gravar só na virada de rodada sem janela pendente (5.4). |
| Masmorra autorada editada entre o salvamento e a retomada | Comparar tamanho do mapa; se mudou, descartar a foto e voltar à cidade com aviso. Monstro de tipo que não existe mais é descartado (mesma tolerância da prévia do editor). |
| Duas pessoas abrindo o mesmo jogo | Já coberto por `SAVEGAMES_IN_USE`. |
| Foto corrompida | `load_savegame` já tem o `.bak`; além disso, foto que falha ao decodificar é descartada e o jogo continua da cidade (nunca trava a entrada). |
| Jogo rápido | Continua sem salvar (por definição). |

### 5.7 Cliente

Mudanças pequenas, porque a retomada usa as mesmas mensagens de uma entrada
normal (`enter_dungeon` + `game_state`):

- `savegamesList`: o servidor manda `onde`/`rodada`/nome da masmorra no resumo
  (`list_savegames`); o cartão mostra "Minas — rodada 7".
- Cartão "▶ Continuar" da tela inicial (Etapa 1) passa a mostrar o mesmo.
- O item "Salvar e sair" troca o texto de aviso (perde no máximo a rodada
  atual).
- Herói ausente aparece esmaecido no painel de jogadores ("aguardando
  {nome}…"), reaproveitando o estilo do card de desconectado.

### 5.8 Testes (Etapa 2)

`tools/test_salvar_masmorra.py`:

1. **Ida e volta** em cada masmorra de `dungeons/` e numa procedural: entrar,
   jogar 2 rodadas com ações variadas (mover, atacar, abrir porta, abrir baú,
   largar item, colocar armadilha, lançar magia de zona), gravar, criar uma
   sala nova a partir do jogo salvo, retomar e comparar o `game_state` antes e
   depois (ignorando `pid` e campos efêmeros).
2. **Cobertura de campos:** todo atributo de `GameRoom` classificado em
   "salva"/"não salva".
3. **Só JSON:** a foto passa por `json.dumps` sem `default=`.
4. **Janela pendente:** com a janela manual do mestre aberta, a virada não
   grava; na seguinte, grava.
5. **Multiplayer:** 3 heróis salvos, 1 volta → os outros 2 ficam fora do
   tabuleiro e da iniciativa; o 2º entra e reaparece na posição salva.
6. **Masmorra editada:** mudar o tamanho do arquivo → foto descartada, grupo na
   cidade, aviso enviado.
7. **Fim da masmorra:** encerrar missão apaga a foto; derrota total também.
8. **Cidade com masmorra em aberto:** voltar à cidade, fechar, retomar, entrar
   → mesma masmorra (monstros mortos continuam mortos).
9. Um caso pelo `server.handler` real (`tools/test_handler_smoke.py` como
   modelo): login → abrir jogo salvo → cair direto na masmorra.

Prova no navegador, ao final: jogar solo até a rodada 3, "Salvar e sair",
reiniciar o servidor, Continuar, confirmar que o mapa, os monstros, os baús e a
bolsa estão iguais.

### 5.9 Ordem de implementação (Etapa 2)

1. Codificador/decodificador puros + teste de ida e volta de tipos.
2. Lista "salva / não salva" + teste de cobertura.
3. `_montar_foto()` e gravação na virada de rodada (sem retomar ainda).
4. `_retomar_masmorra()` para solo.
5. Herói ausente / entrada tardia (multiplayer).
6. `cidade_com_masmorra` e limpeza da foto nos fins de masmorra.
7. Cliente (resumo no "Meus Jogos", textos), chaves pt/en, `tools/dividas.py`
   limpo.
8. Prova no navegador + seção no `CLAUDE.md`.

---

## 6. Esforço estimado

| Etapa | Tamanho | Risco |
|---|---|---|
| 1 — salvar à vista | pequeno (1 sessão) | baixo |
| 2 — foto da masmorra | grande (várias sessões) | médio: o risco está em campos esquecidos, e é por isso que o teste de cobertura vem antes da retomada |

## 7. Decisões para o autor

1. **Tela inicial:** tornar "entrar com conta" o caminho principal e rebaixar o
   jogo rápido (4.1)? Ou manter como está e só acrescentar o cartão Continuar?
2. **Início automático solo** (4.2): pular o lobby quando o jogo salvo tem um
   único jogador? Alguém pode querer trocar de personagem nesse momento.
3. **Granularidade:** salvar a cada rodada (proposta) ou só quando o jogador
   clica "Salvar e sair" e ao voltar à cidade? A cada rodada protege contra
   queda de energia/servidor, a um custo pequeno.
4. **Log do mestre** (`gm_log`) na retomada: não salvar e mostrar só "A aventura
   continua…" (proposta), ou salvar as últimas entradas como chaves de tradução
   (mais trabalho, porque parte do log tem `T` aninhado)?
5. **Multiplayer com ausentes:** o anfitrião pode começar a masmorra retomada
   sem todos (proposta: sim, como hoje acontece com quem cai), ou deve esperar
   o grupo inteiro?
6. **Mestre ausente:** jogo salvo com Mestre só abre pelo Mestre (regra atual).
   Manter?
7. **Jogo rápido:** continua sem salvar, ou ganha um "salvar como jogo" que
   pede para criar conta na hora?
