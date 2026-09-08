# Senhor das Águas — popup dos redemoinhos no início do turno (e joystick)

Data: 2026-09-08
Estado: reproduzido em jogo; causa raiz confirmada por medição.

## Problema relatado

A segunda etapa do Senhor das Águas (marcar casas da área como redemoinho, ação
livre a partir da 2ª rodada, cota acumulada) só aparece como uma mensagem dentro
do menu de Magias. O jogador quer uma janela abrindo sozinha na tela principal no
início do turno dele, e o fluxo inteiro utilizável no controle.

O código do popup automático **já existe** (`_considerarPopupSenhorDasAguas`,
commit `5b7ab80`, 2026-09-07) e nunca foi verificado em jogo.

## Reprodução

Servidor real + cliente real no navegador; clérigo em masmorra; uma zona
`senhor_das_aguas` sintética injetada nas mensagens `game_state` por
`GS.setMessageFilter` (com `redemoinho_max: 2`, `disponivel_em` já satisfeito).
Assim o cenário é alcançável sem precisar de um clérigo de nível 5 — a magia é de
3º círculo, e `redemoinho_max = nível // 2`.

Armadilha do instrumento, registrada porque custou tempo: no painel de navegação
do agente o `requestAnimationFrame` só corre quando a página compõe um frame.
Como o popup é agendado dentro de um `requestAnimationFrame`, ele parecia "nunca
abrir" — falso negativo do harness, não do jogo. Forçar uma captura de tela faz
os frames correrem e o popup abre. **Ao medir cliente aqui, force composição
antes de concluir qualquer coisa.**

## Causa raiz (D1) — o popup abre atrás dos menus

`#senhor-aguas-overlay` tem `z-index: 121`, na faixa dos avisos de tabuleiro
(baú 110, lição 118, armadilha 120, fala 120). Os menus do personagem estão
muito acima: `#menu-magias-overlay` e `#menu-habilidades-overlay` em **510**,
`#inv-modal-overlay` em **500**.

Medido: com o Grimório aberto, o popup abre (`display: flex`), mas
`document.elementFromPoint` no centro da tela devolve um nó do menu — o popup
fica invisível. A tela mostra apenas a mensagem "🌪️ REDEMOINHOS — AÇÃO LIVRE"
dentro do Grimório: exatamente o sintoma relatado.

O Grimório **persiste entre turnos** — `handleGameState` o re-renderiza a cada
`game_state` enquanto tiver a classe `.open`. Um clérigo que joga a partir do
Grimório nunca vê o popup.

Agravante: `_senhorAguasUltimoPopupTurno` é gravada **antes** de a janela abrir.
Qualquer caminho em que a abertura não aconteça queima a chave e o popup não
tenta de novo naquela rodada.

### Desenho

- Subir o `z-index` do `#senhor-aguas-overlay` para acima dos menus de
  personagem. É uma decisão de camada, não um número solto: o popup é uma
  **decisão do turno**, e decisões vêm à frente de menus de consulta.
- Gravar a chave de deduplicação **somente quando a janela realmente abriu**,
  para que uma falha de abertura não custe a rodada inteira.

Sem alterar a frequência combinada: abre todo turno enquanto sobrar cota; fechar
dispensa apenas aquele turno; o botão do painel de ações continua reabrindo.

## D2 — o popup é invisível para o controle

`_gamepadUiScope()` só reconhece overlay que tenha a classe `.open`
(`[id$="-overlay"].open`); o popup abre só com `style.display`.

Medido com o popup aberto: `_gamepadUiScope()` devolve `screen-game` e
`senhor-aguas-create` não está entre os controles alcançáveis. O direcional
continua movendo o cursor no tabuleiro.

### Desenho

- Adicionar/remover a classe `open` junto do `display`.
- `data-gamepad-cancel` no botão Fechar (B fecha).
- Ao abrir, focar "Criar redemoinhos" via `_gamepadFocusMapPoint`.

## D3 — o cursor da mira não alcança a área

`_aimSeedGamepadCursor()` semeia no monstro mais próximo dentro do conjunto
permitido; sem monstro, na casa do herói; **se nenhum dos dois estiver no
conjunto, desiste**. A área do Senhor das Águas é um quadrado remoto (alcance
5 + nível) que normalmente não contém o herói. `_aimStepTile` só encontra casa
válida seguindo em linha reta a partir do cursor.

Medido: herói em [7,25], área 2x2 em [2,3]-[3,4] (fora da linha, da coluna e das
diagonais do herói) → as **8 direções** falham; a mira fica travada. Numa área
que por acaso divide linha ou diagonal com o herói, algumas direções funcionam —
o que torna a falha intermitente e enganosa.

### Desenho

Quando nenhum candidato atual servir, semear na **casa permitida mais próxima do
herói** (Chebyshev; empate pela ordem do conjunto). Vale para toda a camada de
mira, não só para esta magia.

## D4 — o botão CONFIRMAR é inalcançável no controle

`_aimRenderLegend()` anexa `#aim-session-hud` ao `<body>`, fora de
`#screen-game`, e `_gamepadUiPointerControls()` lista apenas
`#objectives-hud button, #btn-libertar` quando o escopo é a tela de jogo.

Medido com a mira ativa: `_gamepadUiPointerControls()` devolve `[]`. Ou seja,
mesmo com o cursor andando e A marcando casas, **não há como concluir a ação no
controle**.

### Desenho

Incluir `#aim-session-hud button` nessa lista. O fluxo fica: direcional move o
cursor → **A** marca/desmarca → **Y** liga o cursor de interface → analógico
direito escolhe CONFIRMAR/CANCELAR → **A** pressiona. Nada específico desta
magia: qualquer mira de seleção múltipla futura herda o comportamento.

## Fora de escopo

- Regras do servidor (cota, rodada de liberação, tipo de redemoinho).
  `handle_senhor_das_aguas_rodamoinhos` continua autoritativo e intocado.
- O botão do painel de ações e a mensagem da aba de Magias no controle.
- Botão dedicado de confirmação no controle.

## Testes

Node (`tools/test_senhor_aguas_cliente.js`), sobre funções puras e varredura
estática do fonte:

1. Semeadura do cursor: herói fora da área, sem monstro dentro → devolve a casa
   permitida mais próxima, não `null`. Caso de regressão: área desalinhada da
   linha/coluna/diagonal do herói.
2. `#aim-session-hud button` está em `_gamepadUiPointerControls`.
3. `_abrirJanelaSenhorDasAguas` adiciona `open` e `_fecharJanelaSenhorDasAguas`
   remove.
4. O `z-index` do `#senhor-aguas-overlay` é maior que o de
   `#menu-magias-overlay` / `#inv-modal-overlay` (lidos do CSS e do markup).
5. A chave de deduplicação só é gravada quando a janela abre.

Verificação viva (com composição forçada): com o Grimório aberto, o popup abre
por cima; `_gamepadUiScope()` passa a devolver o overlay; a mira semeia dentro da
área e o botão de confirmar entra na lista do cursor de interface.
