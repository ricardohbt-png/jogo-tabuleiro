# Solo com grupo (1 a 6 heróis) — design

Data: 2026-10-01

## Objetivo

No modo **Solo**, o jogador escolhe com quantos heróis joga (1 a 6) e controla todos.
Menos heróis = mais difícil; mais heróis = XP dividido por mais gente.

**Já existe e não muda:** o XP de monstro/armadilha/objetivo é um total fixo dividido
entre os heróis vivos (`_calc_monster_xp`, `_conceder_xp_armadilha`,
`_conceder_objetivo_reward`), e os monstros não escalam pelo tamanho do grupo
(`expected_party` é só referência do editor). A dificuldade e a divisão de XP saem de graça.

## Decisões

| # | Decisão |
|---|---|
| 1 | O jogador controla **todos** os heróis (sem IA de companheiro). |
| 2 | Grupo **fixo** por jogo salvo. Recrutar/dispensar fica para etapa futura. |
| 3 | O número é definido na **tela de seleção**: no Solo, marcam-se de 1 a 6 classes. |
| 4 | Foco segue a iniciativa **e** pode ser trocado à mão para ações livres/consulta. |
| 5 | Arquitetura: **heróis por procuração** (pid virtual + `controlador`). |
| 6 | Saída pela escada segue individual; o herói que sai **só espera** (sem lojas) enquanto o grupo está dentro. |
| — | Cada herói é de uma **classe diferente** (fichas e travas são por `class_id`). |

## 1. Seleção de heróis e jogo salvo

**Tela de seleção (Solo).** O carrossel continua; em vez de escolher, o jogador
**marca/desmarca** classes. Faixa "Seu grupo" com os marcados; Iniciar acende com ≥1.
Mago/clérigo marcados abrem cada um o seu seletor de 2 magias; o Iniciar exige as magias
de todos os conjuradores marcados. Multiplayer: inalterado.

**Mensagem nova `select_party {classes:[…], magias:{class_id:[…]}}`.** Aceita só em jogo
salvo Solo, no lobby, do anfitrião; **substitui** a seleção anterior inteira. O 1º herói
ocupa a casca existente (pid da conexão); os demais nascem como cascas com pid virtual
(`new_id()`) e `controlador = pid da conexão`. O `start_game` monta todos por
`_montar_heroi`.

**Jogo salvo.** `members[conta]` mantém `class_id` (herói principal, compatibilidade) e
ganha `class_ids: [...]` (o grupo). `characters[class_id]` já guarda uma ficha por classe;
`slots[cls]` de cada classe aponta para a conta. Save sem `class_ids` = grupo de 1.

**Continuar.** `_continuar_jogo_salvo` recria o grupo inteiro a partir de `class_ids`
(magias de cada ficha copiadas para a casca, como hoje) e inicia direto.

**Solo é fechado.** Num Solo com grupo, outra conta não entra pelo código da sala.

## 2. Servidor: quem age e para onde vai a resposta

**Resolvedor único** `room.heroi_da_acao(pid_conexao, msg)`, chamado no `handler` antes do
despacho:
1. `msg.heroi` presente e controlado por esta conexão → esse herói;
2. senão, herói desta conexão que está na vez (`current_pid`, `animados_phase_pid`,
   `last_stand_pid`) → esse;
3. senão → o principal (pid da conexão) — comportamento atual.

`msg.heroi` de outro controlador é recusado. **Mensagens da conexão** (lista explícita, sem
tradução): `set_lang`, `salvar_e_sair`, `select_party`, votação, conta/login, mensagens de
Mestre.

**`send_to(pid_do_herói)`**: sem conexão própria e com `controlador` → entrega na conexão
do controlador, no idioma dela. `broadcast` não muda (itera conexões).

**Turno:** `_is_turn` inalterado. Limite de tempo vale por herói.

**Queda/volta:** conexão cai → `handle_disconnect_em_jogo` para cada herói dela; `rejoin`/
Continuar religa todos ao controlador novo.

**Foto da masmorra:** `pids` já mapeia pid → classe de todos os heróis; na retomada, o
principal vira o pid da conexão nova, os extras ganham pids novos e o `controlador` é
religado.

**Pontos a varrer:** usos de `account_by_pid`, `ACCOUNTS_ONLINE`, `connected` e do `skip` de
`push_state`. O checkpoint de fichas percorre os `class_ids` da conta. A conexão segue
recebendo `game_state` enquanto **algum** herói dela estiver na masmorra.

**Saída pela escada no Solo com grupo:** individual como hoje; o herói fora fica com o card
"🏙️ na cidade — volta em N rodadas", sem acesso às lojas (`_em_cidade` falso para ele
enquanto houver herói do mesmo controlador dentro). Se todos saírem, o grupo volta à cidade
pelo caminho normal (`_checar_masmorra_vazia`).

## 3. Cliente: herói em foco

`src/gameState.js`:
- `connPid` — identidade da conexão (sessão `lfh_session`, idioma, mensagens da conexão);
- `myPid` — passa a ser **o herói em foco** (os ~316 usos atuais já significam isso);
- `meusHerois` — pids com `controlador == connPid` (mais o próprio `connPid`).

Com 1 herói, `myPid == connPid` e nada muda.

**Foco:** na vez de um herói meu, o foco pula para ele e a câmera centraliza.
`GS.focarHeroi(pid)` aceita só pids de `meusHerois`. `isMyTurn` = herói em foco está na
vez. Toda mensagem de ação sai com `heroi: myPid`.

**Faixa de retratos:** os cartões de `renderPlayers` dos meus heróis ficam clicáveis, com
moldura de foco e marca "⚔️ na vez". Na cidade, `_updateCityHeroBar` abre a ficha
**editável** de qualquer herói meu.

**Visão:** no Solo com grupo, a visão compartilhada entre os meus heróis fica sempre ligada
(`heroisVisaoCompartilhada`). Ataque/mira seguem exigindo a linha de visão de quem age.

## Testes

- `tools/test_solo_grupo.py`, pelo `server.handler` real (FakeWS de
  `test_handler_smoke`): `select_party` com 3 classes (inclui mago com magias); turno passa
  entre os heróis; `heroi` errado recusado; ação livre fora da vez aceita; herói alheio
  recusado; XP dividido por 3; queda/volta religa os 3; Salvar e sair → Continuar devolve
  os 3 (cidade e foto da masmorra); escada: herói fora sem lojas; save antigo de 1 herói
  idêntico.
- Teste node do foco: pula na vez, `focarHeroi` recusa pid alheio, `isMyTurn` do foco,
  mensagens levam `heroi`.
- Prova no navegador: 1 aba, grupo de 3, uma rodada de masmorra, troca de foco fora da
  vez, Salvar e sair → Continuar.
- Placar de idioma (`tools/dividas.py`) limpo para os textos novos.

## Fora de escopo

Recrutar/dispensar heróis; vários heróis por jogador no Multiplayer; classes repetidas;
Mestre com Solo.
