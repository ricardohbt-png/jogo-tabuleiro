# Senhor das Águas — popup dos redemoinhos no início do turno (e joystick)

Data: 2026-09-08

## Problema

A segunda etapa do Senhor das Águas (marcar casas da área como redemoinho, ação
livre a partir da 2ª rodada, cota acumulada) só é alcançável hoje por uma
mensagem dentro do menu de Magias da ficha. O jogador quer que, no início do
turno dele, uma janela abra sozinha na tela principal oferecendo a escolha — e
que todo o fluxo funcione no controle.

O código para isso **já existe** e nunca funcionou: entrou no commit `5b7ab80`
("wip: ... estacionado"), sem verificação em jogo.

- `_considerarPopupSenhorDasAguas()` (game.js) deveria abrir
  `#senhor-aguas-overlay` a cada `game_state`. Não abre nunca.
- Quando o popup é aberto na mão (clicando na mensagem da aba de Magias), o
  controle não navega nele.
- Depois de "Criar redemoinhos", o controle também não conclui a seleção das
  casas no mapa.

## O que fica combinado

- Janela **explicativa + botões**, como a de hoje (`🌪️ Criar redemoinhos` /
  `Fechar`). Sem opção de "não perguntar mais".
- Abre **todo turno do clérigo** enquanto a magia durar e sobrar cota. Fechar
  dispensa apenas aquele turno; o botão do painel de ações continua reabrindo.
- Joystick precisa funcionar **no popup** e **na seleção das casas no mapa**.
  O botão do painel de ações e a mensagem da aba de Magias ficam fora do escopo
  (continuam como estão, para o mouse).
- Confirmar a seleção no controle: pelo **cursor de interface (Y)** já
  existente, não por botão dedicado.

## Falha 1 — o popup nunca dispara

`_considerarPopupSenhorDasAguas()` reprova em silêncio: sete guardas numa
condição única, sem dizer qual barrou. A leitura estática não acusa nada — todos
os campos lidos (`phase`, `current_turn`, `animados_turn`, `round`,
`zonas_especiais`) existem no payload de `push_state`.

Hipótese principal, a confirmar: `GS.on()` guarda **um** handler por evento
(`_handlers[ev]`, src/gameState.js), e a chamada do popup é a sétima linha de um
handler que executa `handleGameState(msg)` antes. Uma exceção em qualquer linha
anterior mata o popup sem erro visível no jogo.

### Desenho

Extrair a guarda para uma função **pura**:

```
_senhorAguasDecisaoPopup(state, myPid, ultimaChave) -> { abrir, zona, chave, motivo }
```

`motivo` é um dos: `sem_estado`, `sem_heroi`, `fora_de_jogo`, `nao_clerigo`,
`morto`, `fora_do_turno`, `janela_servos`, `sem_zona`, `cota_zerada`,
`rodada_cedo`, `ja_abriu`, `ok`.

`_considerarPopupSenhorDasAguas()` passa a ser uma casca fina: chama a decisão,
registra o motivo em `console.debug` e abre a janela quando `abrir` é verdadeiro.
O conserto definitivo só é escrito **depois** de observar o motivo real em jogo —
o diagnóstico faz parte do trabalho, não é presumido aqui.

## Falha 2 — o controle não enxerga o popup

`_gamepadUiScope()` só reconhece overlays com a classe `.open`
(`[id$="-overlay"].open`). `#senhor-aguas-overlay` é exibido com
`style.display='flex'`, sem a classe. Com o popup aberto, o escopo do controle
continua sendo `#screen-game`: o direcional segue movendo o cursor no tabuleiro
e os botões da janela ficam inalcançáveis.

### Desenho

- `_abrirJanelaSenhorDasAguas()` adiciona `open` ao `classList` (além do
  `display`); `_fecharJanelaSenhorDasAguas()` remove.
- `Fechar` recebe `data-gamepad-cancel`, para B fechar a janela.
- Ao abrir, `_gamepadFocusMapPoint('#senhor-aguas-create', '#senhor-aguas-close')`
  para o foco nascer em "Criar redemoinhos".

## Falha 3 — o controle não conclui a seleção das casas

Dois furos independentes:

**(a) O cursor não nasce dentro da área.** `_aimSeedGamepadCursor()` semeia no
monstro mais próximo dentro do conjunto permitido; sem monstro, na casa do
herói; se nenhum dos dois estiver no conjunto, **não semeia**. A área do Senhor
das Águas é um quadrado remoto que costuma não conter monstro e não contém o
herói. Como `_aimStepTile()` só encontra casa válida seguindo em linha reta a
partir do cursor, o direcional trava.

Conserto: quando nenhum candidato atual serve, semear na **casa permitida mais
próxima do herói** (distância de Chebyshev, empate pela ordem do conjunto).
Vale para toda a camada de mira, não só para esta magia.

**(b) O botão CONFIRMAR é inalcançável.** `_aimRenderLegend()` anexa
`#aim-session-hud` ao `<body>`, fora de `#screen-game`, e
`_gamepadUiPointerControls()` lista apenas `#objectives-hud button, #btn-libertar`
quando o escopo é a tela de jogo.

Conserto: incluir `#aim-session-hud button` nessa lista. O fluxo completo passa a
ser: direcional move o cursor sobre as casas permitidas → **A** marca/desmarca →
**Y** liga o cursor de interface → analógico direito escolhe
CONFIRMAR/CANCELAR → **A** pressiona. Nada disso é específico do Senhor das
Águas: qualquer mira de seleção múltipla futura herda o comportamento.

## Fora de escopo

- Mudar as regras do servidor (cota, rodada de liberação, tipo de redemoinho).
  `handle_senhor_das_aguas_rodamoinhos` continua autoritativo e intocado.
- O botão do painel de ações e a mensagem da aba de Magias no controle.
- Botão dedicado de confirmação no controle.

## Testes

`tools/test_senhor_aguas_cliente.js` (node, no padrão dos demais testes de
cliente), sobre as funções puras:

1. `_senhorAguasDecisaoPopup` devolve `ok` no caso feliz e o motivo certo em
   cada guarda reprovada (uma asserção por motivo).
2. Repetir a mesma chave devolve `ja_abriu` (não reabre no mesmo turno).
3. Semeadura do cursor: herói fora da área e sem monstro dentro dela devolve a
   casa permitida mais próxima, e não `null`.
4. Varredura estática: `#aim-session-hud button` está em
   `_gamepadUiPointerControls`, e `_abrirJanelaSenhorDasAguas` adiciona/remove a
   classe `open`.

Verificação viva: injetar um `game_state` sintético no cliente (com uma zona
`senhor_das_aguas` ativa e cota restante) e observar a janela abrir, mais uma
passada com o controle no popup e na seleção das casas.
