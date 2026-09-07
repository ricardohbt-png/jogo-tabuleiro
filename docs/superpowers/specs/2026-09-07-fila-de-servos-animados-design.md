# Fila de servos animados: seleção automática por iniciativa e controle pelo joystick

Data: 2026-09-07

## Problema

O mago (Pedro) anima cadáveres com **Reviver os Mortos**. Ao encerrar o turno
dele abre-se a *janela dos servos* (`animados_phase_pid`), em que ele controla
manualmente cada criatura animada — e, se resgatou o prisioneiro, também ele.

Hoje essa janela é uma sala com várias peças e nenhuma ordem:

- O servidor monta `animados_order` (já ordenado por iniciativa) e o envia no
  `game_state`, mas **esquece dele em seguida** — não existe "o servo da vez".
- O cliente auto-seleciona apenas o **primeiro** servo quando a janela abre
  (`game.js`, gancho de `GS.on('gameState')`). Depois disso nada avança: o
  jogador precisa **clicar manualmente** em cada servo seguinte.
- Não existe a noção de "encerrar o turno de UM servo". A mensagem `end_turn`
  fecha a janela inteira de uma vez.
- No joystick o cursor fica ancorado no **herói** (`_gamepadEnsureCursor`) e a
  prévia de rota passa por `GS.resolveTileClick`, que é a lógica do herói. Ou
  seja: durante a janela dos servos o controle trabalha contra o jogador.

## Objetivo

Ao encerrar o turno do mago, o primeiro servo (por iniciativa) é selecionado
sozinho. Ao encerrar o turno **desse servo**, o próximo é selecionado sozinho, e
assim por diante até a fila acabar — quando a janela fecha e a rodada avança.
Com o joystick conectado, a peça selecionada é a peça que o joystick controla.

## Decisões de design

| Questão | Decisão |
|---|---|
| Como termina o turno de um servo | O botão/tecla de **encerrar turno** que já existe passa a encerrar só o servo atual e selecionar o próximo. O último encerra a janela inteira. Mesmo padrão do `mestre_encerrar_monstro` do Modo Mestre. |
| Onde entra o prisioneiro | **Último da fila**: servo 1 → … → servo N → prisioneiro → fecha. Ele não tem ficha de combate, então não disputa iniciativa. |
| Alcance do joystick | **Tudo**: cursor, prévia de rota, confirmação e modo de ataque passam a valer para a peça da vez — o mesmo contrato que o joystick já dá ao herói, só trocando de peça. |
| Servo que não pode agir | **Pulado sozinho**, com o motivo narrado (morto, dormindo, preso pelo rodamoinho com o turno bloqueado). |
| Seleção manual | **Continua funcionando.** A fila é o padrão, não uma jaula: clicar num servo ainda troca o controle, e encerrar encerra o selecionado. |

## Parte 1 — O servidor dirige a fila

### Estado novo em `GameRoom`

Ao lado do `animados_order` que já existe:

- `self.animados_done: set` — ids já encerrados nesta janela.
- `self.prisioneiro_done: bool` — o mesmo para o prisioneiro.

Ambos são limpos nos **três** pontos que já zeram `animados_order` (abertura da
janela em `handle_end_turn`, fechamento da janela, e o reset por entrada de
masmorra).

### Campo novo no `game_state`

`animados_atual` — o id do servo da vez, a string `"prisoner"`, ou `null`.

É derivado, nunca armazenado: o **primeiro de `animados_order` que não está em
`animados_done` e consegue agir**; esgotados os servos, o prisioneiro se ele for
controlado por este jogador e não estiver `prisioneiro_done`; esgotado tudo,
`null`.

"Consegue agir" exclui: `vida_atual <= 0`, `dormindo`,
`_rodamoinho_bloqueado_turno` e `_rodamoinho_profundo_bloqueado_turno`.

### Mensagem nova `encerrar_animado`

`{ "type": "encerrar_animado", "animado_id": <int | "prisoner"> }`
→ `handle_encerrar_animado(pid, animado_id)`

1. Recusa se `animados_phase_pid != pid`, se o id não pertence à fila deste
   jogador, ou se o id já está em `animados_done` / `prisioneiro_done` (encerrar
   duas vezes o mesmo servo não pode consumir a vez do seguinte).
2. Marca o id em `animados_done` (ou liga `prisioneiro_done`).
3. Recalcula o próximo, **narrando cada salto** de servo travado.
4. Se não sobrou ninguém, **delega a `handle_end_turn(pid)`**.

A delegação é segura e não exige refatorar a cauda de `handle_end_turn`: como
`animados_phase_pid == pid` nesse momento, o bloco de abertura da janela é
pulado pela própria condição que já está lá, e a execução cai direto no
fechamento (`animados_phase_pid = None`, reset de `moves_left`/`action_done`,
avanço da iniciativa). Consequência aceita e idêntica ao comportamento atual: a
Dor Constante e o `_licao_evento("encerrar_turno")` são cobrados no fechamento,
como já acontece hoje na segunda pressão de "encerrar turno".

### O que NÃO muda

`handle_end_turn` continua fechando a janela inteira de uma vez. É a rede de
segurança que o timer anti-AFK usa (`_turn_timer_expira` → `_forcar_fim_turno`,
que keya em `current_pid()` — ainda o mago durante a janela). Nada nesse caminho
é tocado.

## Parte 2 — O cliente segue a fila

- `_animadoSel` passa a **espelhar `animados_atual`** sempre que ele mudar. O
  gancho que hoje dispara só na transição da janela
  (`msg.animados_turn === GS.myPid && _lastAnimadosTurn !== GS.myPid`) é
  generalizado para disparar a cada mudança de `animados_atual`. Quando o valor
  é `"prisoner"`, liga `_prisSel` e zera `_animadoSel`.
- **Clicar num servo continua trocando o controle.** Encerrar encerra o
  **selecionado**; o servidor então recalcula o próximo.
- O botão `#btn-end-turn` mostra **"⏭ Encerrar servo (1/3)"** durante a janela.
  Como `_i18nApply` sobrescreve `textContent` de todo `[data-i18n]`, o atributo
  sai do `<span>` enquanto o rótulo é dinâmico e volta ao normal depois. O
  rótulo é repintado em `_atualizarBotaoEncerrarTurno`, que já roda a cada
  `game_state` — e a troca de idioma reenvia o estado, então acompanha sozinha.
- A decisão "encerrar servo vs. encerrar turno" mora em `gameState.js` como
  predicado `GS.animadoPendenteParaEncerrar(selId)`; `game.js` só o consulta.
- A tecla **Enter** (`game.js`) hoje chama `GS.endTurn()` direto e pularia o
  despacho — passa a chamar `endTurn()`, como o botão e o joystick já fazem.

## Parte 3 — O joystick assume a peça da vez

### Uma regra de alcance só (correção de divergência)

O alcance de ataque de um servo está escrito **quatro vezes** hoje, e elas já
divergem: o ramo de servo do `handleTileClick` honra o `attacks[0].range` e o
`range_shape` reais da ficha, enquanto os renders 2D e 3D cravam "cardinal,
alcance 1 (ou 3 se `especial === 'linha_3q'`)". O realce já mente para servos
elementais de alcance maior. O joystick seria a quinta cópia.

Nasce `GS.animadoAttackTargetTiles(animado)` em `gameState.js` — pura, irmã da
`attackTargetTiles()` do herói, honrando `range`, `range_shape` e linha
bloqueada, espelhando o que o servidor valida em `_animado_attack_in_range`. Os
quatro consumidores passam a ler dela.

### A peça controlada

`GS.pecaControlada()` devolve o servo/prisioneiro da vez quando a janela é
minha, e o herói fora dela. A partir dele:

- **`_gamepadEnsureCursor`** ancora nessa peça. A `cursorPlayerKey` — que hoje
  reancora o cursor a cada passo do herói — passa a incluir o id da peça, de
  modo que **trocar de servo joga o cursor sobre o servo novo**. É esse detalhe
  que faz o encadeamento parecer automático no controle.
- **`_selecionarPreviaMovimento`** ganha origem e orçamento como parâmetros
  (hoje lê `me.pos`/`me.moves_left` cravados). `GS.pendingMove` ganha um campo
  opcional `animadoId`.
- **`_gamepadAtualizarPreviaMovimento`** calcula a rota do servo com
  `GS.findPath` sobre o `moves_left` dele — a mesma conta que o clique do mouse
  já faz — em vez de `GS.resolveTileClick`, que é do herói.
- **`_gamepadAttackTargets`** devolve os alvos do servo pela função nova. A →
  modo de ataque → confirmar cai no ramo de servo do `handleTileClick`, que
  envia `atacar_animado`.

### Armadilha a consertar junto

O ramo de servo do `handleTileClick` roda **antes** da leitura de
`GS.pendingMove`. Sem conserto, uma prévia confirmada por A move o servo e deixa
a prévia pendurada. Esse ramo passa a limpar `GS.pendingMove`.

### Ajustes de contexto durante a janela

- `_gamepadRequestEndTurn` **perde a dupla-pressão de confirmação** enquanto há
  servo na fila: encadear 3 servos com confirmação seriam 6 apertos, e o gesto
  não é destrutivo — só passa a vez de uma peça.
- Ficam inertes os atalhos que só fazem sentido para o herói:
  `_gamepadInteractAtCursor` (baú/item, ancorado em `me.pos`) e
  `_gamepadCycleUsefulTarget`.
- `_renderGamepadHud` / `_gamepadContexto` rotulam a peça da vez
  ("Esqueleto · 4 mov"), para o jogador saber quem o direcional move.

## Idioma

Chaves novas em pt e en:

- `src/lang/narracao.js` — os saltos de servo travado (morto / dormindo / preso
  pelo rodamoinho) e o anúncio do servo da vez.
- `src/lang/interface.js` — o rótulo dinâmico do botão de encerrar e o contexto
  do HUD do joystick.

## Testes

`tools/test_reviver_mortos.py` (servidor):

1. Abrir a janela com 3 servos → `animados_atual` é o de maior iniciativa.
2. `encerrar_animado` no atual → `animados_atual` vira o segundo da ordem.
3. Servo dormindo/preso no meio da fila é **pulado**, com narração.
4. Servo que morre no meio da janela sai da fila.
5. Encerrar o último servo com prisioneiro liberto → `animados_atual` vira
   `"prisoner"`.
6. Encerrar o prisioneiro → a janela fecha e a iniciativa avança (equivalente ao
   `end_turn` de hoje).
7. `encerrar_animado` fora da janela, ou com id alheio, é recusado.
8. `end_turn` durante a janela continua fechando tudo de uma vez (rede de
   segurança do timer preservada).

## Fora de escopo

- Navegação pelo joystick no painel de **habilidades ativas** do servo (Senhor
  da Morte / elemental) — continuam só no mouse.
- Qualquer mudança nas regras de movimento, ataque ou custo dos servos.
- O `comandar_animados` automático (todos agem sozinhos) permanece como está.
