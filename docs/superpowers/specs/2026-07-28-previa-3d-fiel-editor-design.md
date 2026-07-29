# Prévia 3D fiel do editor de masmorras

**Data:** 2026-07-28
**Estado:** aprovado, aguardando plano de implementação

## Problema

O editor de masmorras tem um botão "◈ Visualizar em 3D" que abre uma prévia da
masmorra atual. Objetos e sprites de monstro não aparecem como aparecerão no
jogo, e a aparência geral diverge do produto final.

A causa não é um bug pontual. `tools/editor_preview_3d.js` é um **renderer
paralelo** de 183 linhas, escrito à mão, que reimplementa de forma aproximada o
que `game.js` faz. Divergências verificadas rodando o editor pelo servidor com
`dungeons/gustavo.json` carregado e inspecionando a cena Three.js resultante:

| Divergência | Na prévia | No jogo |
|---|---|---|
| Decoração `special:"floor"` | caixa marrom lisa | PNG do chão (`chaograma1.png`, `chaotapete1.png`…) |
| Decoração `special:"wall"` | placa laranja | PNG de parede (brasões, etc.) |
| `DECOR_GLB` | 16 tipos; `altar` e `gaiola` viram caixa cinza | mapa completo em `game.js` |
| Monstros | sempre sprite PNG chapado | `MONSTER_GLB` (modelo 3D) para vários tipos |
| Iluminação | hemisfério + direcional fixos | presets `VC.ambientes` por masmorra |
| Armadilhas | cilindro vermelho | decal do PNG deitado no chão |
| `decoration.image` | `null` quando o autor não define | resolvido pelo servidor a partir de `DECOR_TYPES` |

A última linha é decisiva: o campo `image` de uma decoração é preenchido por
`load_authored_dungeon` no `server.py`, a partir do `meta` do `DECOR_TYPES`. Esse
dado **não existe no estado do editor**. Nenhuma correção do lado do cliente faria
a prévia atual saber qual PNG cada objeto usa.

Consertar as divergências uma a uma não resolve o problema de fundo: enquanto
houver dois renderers, cada objeto, monstro ou material novo volta a divergir.

## Solução

A prévia deixa de ter renderer próprio e passa a **rodar o cliente real do jogo**
sobre um `game_state` produzido pelo **carregador real do servidor**.

### Fluxo

1. O editor serializa a masmorra atual com o mesmo `buildJSON()` que o botão
   Salvar usa, sem gravar nada em disco.
2. Envia `{type:"preview_dungeon", defn}` pelo WebSocket, reaproveitando o padrão
   de conexão sob demanda que `tools/story_upload.js` já implementa.
3. O servidor cria um `GameRoom` descartável, chama o **mesmo
   `load_authored_dungeon(defn)`** usado pelo jogo, marca todo o mapa como
   explorado e devolve `{type:"preview_state", state, avisos}` só para quem pediu.
4. O editor repassa o payload ao `<iframe src="../index.html?preview=1">` por
   `postMessage`.
5. O iframe injeta o estado no `GS` e renderiza pelo caminho normal (`init3D`).

A fidelidade é estrutural, não imitada: mesmo carregador de masmorra no servidor,
mesmo renderer no cliente. Conteúdo novo aparece na prévia sem tocar no editor.

### Névoa de guerra

Em vez de criar um modo "revelar tudo", o payload vem com `master_pid` igual ao
pid falso da prévia. `GS.isMaster()` já retorna `true` nessa condição e o renderer
já sabe desligar a fog e mostrar o mapa inteiro — é a visão que o Modo Mestre usa.
Reuso de mecanismo existente, sem caminho novo de renderização.

### Heróis

`players: []` e `current_turn: null`. A prévia mostra só o cenário: mapa, objetos,
monstros, baús e armadilhas. Decisão do autor: ao desenhar a masmorra o que se
avalia é a aparência do lugar.

### Interação

Só câmera (orbitar, zoom, pan). Em modo prévia o `send()` do `GS` é um no-op, então
cliques no tabuleiro não produzem ação nem erro.

## Mudanças por arquivo

### `server.py`

- `push_state` é dividida em `_game_state_payload()` (dict puro, sem `await`) e
  `push_state` (await das checagens + broadcast). Espelha o par
  `_city_state_payload` / `broadcast_city_state` que já existe no arquivo.
- Novo `handle_preview_dungeon(defn)` + despacho da mensagem `preview_dungeon`:
  valida com `validar_dungeon`, monta a sala descartável, marca `explored` com
  todas as casas, define `master_pid` do pid falso e responde `preview_state`.
- Nenhum caminho de jogo muda de comportamento.

### `src/gameState.js`

- Detecta `?preview=1`: `send()` vira no-op e o módulo expõe
  `injectPreviewState(msg)`, que passa pelo `case 'game_state'` já existente
  (mesma normalização, mesmo evento `gameState`).

### `game.js`

- Em modo prévia pula login e lobby, vai direto para `screen-game` em 3D e esconde
  o HUD: painéis de turno, log, botões de ação e HUD do mestre.

### `tools/editor_preview_3d.js`

- Reescrito: só o overlay, o iframe, o envio do `preview_dungeon` e o
  `postMessage`. Some todo o código de cena, materiais, GLB e sprites.

## Masmorra incompleta

Enquanto o autor desenha, a masmorra costuma estar inválida (sem entrada, sem
sala). A prévia é **tolerante**: se `validar_dungeon` reprovar, o servidor ainda
monta o que for possível e devolve os avisos, que a barra do overlay exibe. Só um
erro que impeça o carregamento (grid ausente, `tiles` malformado) substitui a cena
por uma mensagem de erro.

## Testes

`tools/test_preview_editor.py`:

- `_game_state_payload` produz, no jogo normal, exatamente o mesmo dict que a
  `push_state` produzia antes da divisão — proteção contra regressão.
- A prévia devolve decorações com `image` resolvido a partir do `DECOR_TYPES`.
- A prévia devolve monstros com `vscale` e `pos` conforme autorados.
- A prévia devolve `players: []`, `current_turn: null` e `master_pid` preenchido.
- Masmorra inválida devolve avisos e um estado utilizável, sem exceção.
- Masmorra irrecuperável (sem `grid`) devolve erro, sem derrubar o servidor.

## Fora de escopo

- Heróis posicionados na prévia (e o seletor de 1–6 heróis).
- Simular turno, movimento ou combate na prévia.
- Prévia de cidade, taverna ou mapa-múndi.
- Extrair o construtor de cena do `game.js` para um módulo compartilhado
  (`src/board3d.js`). Foi considerado e descartado: mesmo resultado que o iframe,
  mas com cirurgia em 24 mil linhas de `game.js` e risco real de regressão no jogo.
