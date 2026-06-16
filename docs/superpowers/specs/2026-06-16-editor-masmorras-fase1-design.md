# Editor de Masmorras & Campanha — Fase 1: Fundação (formato + carregador)

**Data:** 2026-06-16
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Spec aprovado — pronto para plano de implementação

---

## Contexto: decomposição em 4 fases

O pedido original (editor visual de masmorras + objetivos + ordenação como fases de
um jogo) é grande demais para um único spec. Foi decomposto em 4 subsistemas
independentes, cada um funcional e testável sozinho, construídos nesta ordem. **Este
documento especifica apenas a Fase 1.**

| Fase | Entrega |
|---|---|
| **1 — Fundação** | Esquema JSON da masmorra + carregador no `server.py` (joga uma masmorra autorada em vez de gerar aleatória) + grid de tamanho variável + seleção no lobby. Testável escrevendo um JSON à mão. |
| 2 — Editor visual | `tools/editor.html` offline: pintar tiles, marcar salas, posicionar entidades, salvar/carregar JSON no formato da Fase 1. |
| 3 — Entidades e objetivos | Casa de saída, prisioneiro com escolta (IA segue herói mais próximo; morte → falha), item/baú-chave, alvo/chefe, eliminar-todos; objetivo principal + secundários; conclusão → cidade/loja → próxima. |
| 4 — Campanha | `campaign.json`, várias campanhas, ordem das fases, progressão contínua (HP/XP/nível/ouro/itens entre fases), aba de campanha no editor, seletor no lobby. |

### Decisões de produto que orientam todas as fases

- **Modo campanha + procedural coexistem** — nada do jogo atual é removido.
- **Editor é offline** em `tools/`, produzindo JSON; zero risco para produção.
- **Modelo de mapa:** salas retangulares + pintura livre de tiles (preserva
  portas trancadas, névoa e despertar de monstros).
- **Monstros:** posicionados individualmente em casa exata; vinculados a uma sala
  (para dormir/despertar).
- **Baús:** conteúdo exato (ouro + itens) definido por baú.
- **Armadilhas:** um dos 8 tipos ricos de `ARMADILHAS`, em casa exata.
- **Objetivos:** 1 objetivo **principal** (cumpri-lo encerra a masmorra → próxima
  fase) + objetivos **secundários** opcionais (se não cumpridos quando o principal
  encerra, ficam pendentes e a fase encerra mesmo assim). Tipos: resgatar
  prisioneiro, derrotar chefe/alvo, eliminar todos, chegar à saída, pegar item/abrir
  baú-chave.
- **Ao concluir:** volta à cidade/loja entre fases e depois avança.
- **Progressão:** contínua (campanha) — heróis carregam HP/XP/nível/ouro/itens.
- **Prisioneiro:** após libertado, segue o herói mais próximo (IA simples); se morrer,
  a fase falha.
- **Morte total do grupo:** comportamento atual (`game_over`), sem lógica especial.

---

## Fase 1 — Escopo

A Fase 1 faz o `server.py` **carregar e jogar uma masmorra autorada** a partir de um
arquivo JSON, com **tamanho de grid variável**, em vez de chamar `generate_dungeon()`.

- O **esquema JSON é definido por completo agora** (incluindo prisioneiro, saída e
  objetivos) para que o editor da Fase 2 tenha onde gravar.
- O **carregador da Fase 1 instancia somente o que o motor atual entende**: `grid`,
  `tiles`, `rooms`/portas, `monsters`, `chests`, `traps`, `entrance`.
- `exit`, `prisoner`, `objectives`, `target`, `key_objective` são **lidos, validados e
  guardados** (`self.dungeon_def`), porém **inertes em jogo** até a Fase 3.
- **Sem editor** (Fase 2). Testa-se escrevendo um JSON à mão em `dungeons/`.
- **Sem regressão:** o modo procedural permanece idêntico.

### Fora de escopo (fases seguintes)

Editor visual (F2); lógica em jogo de saída/prisioneiro/objetivos (F3); ordem de fases,
várias campanhas e progressão entre fases (F4).

---

## Arquitetura atual relevante (verificada no código)

- Mapa atual fixo `MAP_W = MAP_H = 30`; tiles `WALL=0 / FLOOR=1 / DOOR=2`
  (`server.py:26-30`).
- `generate_dungeon()` (`server.py:1745`) devolve `tiles` + `room_data` (cada sala com
  `id,x,y,w,h,role,cleared,looted,locked,doors`).
- `enter_dungeon` (`server.py:3115`) gera a masmorra só na 1ª entrada
  (`dungeon_generated`), posiciona heróis na sala `entrance`, faz spawn de monstros/
  traps/baús por `role`, monta `self.door_rooms` (porta → salas).
- Spawn: `spawn_monsters_for_room` (`server.py:2486`), `make_monster`, `make_trap`
  (`server.py:2520`), `_spawn_chest(pos, gold, items, source_id)` (`server.py:5930`).
- Catálogos de item: `CHEST_ITEMS` (server, `server.py:1447` — consumíveis/armas
  simples com `id/name/emoji/item_slot/effect/value`) e `CATALOGO_ITENS` (cliente,
  `src/gameState.js:504` — equipamento da loja, ids em português).
- `ARMADILHAS` (server, ~`server.py:1629`): 8 tipos colocáveis.
- **Cliente já é agnóstico ao tamanho do mapa:** todos os caminhos de render (2D/3D)
  derivam dimensões de `state.tiles` (`tiles.length` / `tiles[0].length`) — ver
  `game.js:4378, 4401, 9738, 10627, 10841, 10967, 11015`. Logo, o grid variável é
  quase 100% trabalho de servidor.
- Lobby: `broadcast_lobby` (`server.py:2755`) emite `lobby_state` com `host`,
  `players`, `classes`, `can_start`. Fluxo: `create_room`/`join_room` → `select_class`
  → `start_game` → cidade → `enter_dungeon`.

---

## 1. Esquema JSON da masmorra (`dungeons/<id>.json`)

```jsonc
{
  "schema_version": 1,
  "id": "fase_01_cripta",                 // único; recomenda-se == nome do arquivo
  "name": "Cripta dos Sussurros",          // exibido no lobby
  "grid": { "w": 24, "h": 18 },            // dimensões do tabuleiro desta masmorra

  // h linhas × w colunas. Cada célula: 0=WALL, 1=FLOOR, 2=DOOR
  "tiles": [ [0,1,2,/* ... w valores ... */], /* ... h linhas ... */ ],

  "rooms": [
    { "id": 0, "x": 2, "y": 2, "w": 6, "h": 5,
      "role": "entrance",        // entrance|monster|chest|trap|boss|empty (informativo)
      "locked": false,            // entrada normalmente destrancada
      "doors": [ [7,4] ] }        // tiles DOOR no anel da sala (entradas)
  ],

  "entrance": { "x": 4, "y": 4 },           // [F1 ATIVO] spawn dos heróis + escada
  "exit":     { "x": 20, "y": 15 },         // [guardado] vira ativo na F3

  "monsters": [
    { "type": "goblin", "pos": [10,6],
      "room_id": 1,               // sala à qual pertence (dormir/despertar)
      "boss": false,              // marca de chefe
      "target": false }           // [guardado] alvo do objetivo kill_target (F3)
  ],

  "chests": [
    { "pos": [12,8], "gold": 30,
      "items": [ {"id":"health_potion"}, {"id":"espada_longa"} ],
      "key_objective": false }    // [guardado] baú-chave (F3)
  ],

  "traps": [ { "tipo": "fosso_estacas", "pos": [9,9] } ],   // tipo ∈ ARMADILHAS

  "prisoner":   { "pos": [22,3], "room_id": 4 },            // [guardado] F3

  "objectives": {                                            // [guardado] F3
    "primary":   { "type": "kill_target" },
    "secondary": [ { "type": "rescue_prisoner" },
                   { "type": "open_key_chest" } ]
  }
}
```

### Campos: ativo vs. guardado na Fase 1

| Campo | Fase 1 |
|---|---|
| `schema_version`, `id`, `name`, `grid`, `tiles` | **Ativo** |
| `rooms` (+ `doors`) | **Ativo** (monta `self.rooms` e `self.door_rooms`) |
| `entrance` | **Ativo** (spawn dos heróis + `stairs_pos`) |
| `monsters` (`type`,`pos`,`room_id`,`boss`) | **Ativo** (posição exata) |
| `chests` (`pos`,`gold`,`items`) | **Ativo** (conteúdo exato) |
| `traps` (`tipo`,`pos`) | **Ativo** |
| `exit`, `prisoner`, `objectives`, `target`, `key_objective` | **Guardado/inerte** (parseado, validado, salvo em `self.dungeon_def`; sem efeito em jogo) |

### Tipos de objetivo (definidos no esquema; lógica na Fase 3)

`kill_target`, `kill_all`, `reach_exit`, `open_key_chest`, `rescue_prisoner`.

---

## 2. Servidor — carregador, grid dinâmico e validação

### 2.1 Grid dinâmico

- Introduzir `self.map_w` / `self.map_h` em `GameRoom.__init__` (default `MAP_W` /
  `MAP_H` = 30).
- Auditar e trocar os usos de `MAP_W`/`MAP_H` **dentro de métodos de `GameRoom`** (~29
  ocorrências em `server.py`, sobretudo checagens de limite `0 <= x < MAP_W`) por
  `self.map_w` / `self.map_h`.
- Funções de módulo (`generate_dungeon`, etc.) **permanecem usando as constantes**; o
  procedural continua 30×30. No procedural, `enter_dungeon` define
  `self.map_w = MAP_W` / `self.map_h = MAP_H`.

### 2.2 `load_authored_dungeon(defn)`

Novo método de `GameRoom`. A partir do dict validado:

- `self.map_w = defn["grid"]["w"]`; `self.map_h = defn["grid"]["h"]`.
- `self.tiles = defn["tiles"]` (cópia).
- `self.rooms` = salas no mesmo formato de `generate_dungeon` (preencher
  `cleared`/`looted` por `role` como hoje; `cx`/`cy` calculados).
- `self.door_rooms` montado a partir de `rooms[].doors` (igual ao trecho de
  `enter_dungeon`).
- `self.monsters` = um `make_monster(mdef, room)` por entrada, com `pos`/`room_id`/
  `boss` **sobrescritos** pelos valores autorados (sem `spawn_min/max`, sem
  distribuição automática).
- `self.chests` via `_spawn_chest(pos, gold, items)` com os itens exatos.
- `self.traps` / armadilhas via o construtor de `ARMADILHAS` por `tipo` e `pos`.
- `entrance` → posição de spawn dos heróis e `self.stairs_pos`.
- `self.dungeon_def = defn` (cru) para as Fases 3/4 lerem `exit`/`prisoner`/
  `objectives`.

### 2.3 Integração em `enter_dungeon`

No bloco `nova` (1ª entrada): se a sala está em **modo autorado** e tem masmorra
selecionada, chamar `load_authored_dungeon(defn)` no lugar de `generate_dungeon()` +
spawns por `role`. Reveal da entrada, timer e `push_state` permanecem.

### 2.4 Validação (recusar com erro claro; não inicia)

Função `validar_dungeon(defn) -> (ok, msg)`. Regras:

- `schema_version` suportado; campos obrigatórios presentes.
- `len(tiles) == grid.h` e cada linha com `grid.w` colunas; valores ∈ {0,1,2}.
- Toda `pos`/`entrance`/`exit`/`prisoner.pos` dentro do grid.
- `entrance` em FLOOR; cada `monster.pos`/`prisoner.pos` em FLOOR ou DOOR.
- `monster.type` ∈ `MONSTER_DEFS`; `monster.room_id`/`prisoner.room_id` existe em
  `rooms`.
- `chest.items[].id` ∈ (`CHEST_ITEMS` ∪ `CATALOGO_ITENS`); `gold >= 0`.
- `trap.tipo` ∈ `ARMADILHAS`.
- Cada `[x,y]` em `rooms[].doors` é tile DOOR.
- (Recomendado) mapa conexo a partir da entrada por tiles caminháveis.

Em falha, `enter_dungeon`/seleção envia `{"type":"error","msg": ...}` ao host e **não
inicia**.

---

## 3. Lobby e seleção da masmorra

- Servidor lê `dungeons/*.json` (lista `{id, name, file}`); ler ao montar
  `lobby_state` (ou cachear com refresh).
- `lobby_state` ganha: `dungeons: [...]`, `selected_dungeon` (file ou `null`),
  `mode` (`"procedural"` | `"authored"`).
- Nova mensagem **`select_dungeon`** `{ "file": <nome|null> }` — `null` = procedural;
  **somente host**; reemite `lobby_state`. Roteada no cliente por
  **`GS.selectDungeon(file)`** em `src/gameState.js` (respeita a regra estado-vs-render
  do CLAUDE.md).
- UI mínima em `game.js` (tela de lobby): dropdown com "Procedural (aleatória)" +
  cada masmorra de `dungeons/`. Sem editor.
- A seleção é fixada antes de `enter_dungeon`; ao entrar em modo autorado,
  `load_authored_dungeon` usa o `defn` do arquivo selecionado.

---

## 4. Pasta e arquivos

- Nova pasta `dungeons/` na raiz, lida pelo `server.py` (filesystem; **não** precisa
  ser servida ao cliente — a lista chega via `lobby_state`).
- Para teste da Fase 1, criar à mão `dungeons/test_fase1.json` (grid pequeno, ex.
  16×12).

---

## 5. Protocolo (resumo das mudanças)

**Client → Server**

| Mensagem | Campos | Nota |
|---|---|---|
| `select_dungeon` | `file` (string ou `null`) | Só host. `null` = procedural. |

**Server → Client**

`lobby_state` ganha `dungeons`, `selected_dungeon`, `mode`. (`error` reaproveitado
para falha de validação.)

---

## 6. Plano de teste

1. **Masmorra autorada feliz:** escrever `dungeons/test_fase1.json` (grid 16×12).
   Criar sala, selecionar no dropdown, entrar. Verificar:
   - tabuleiro renderiza com 16×12 (não 30×30);
   - paredes/portas/salas conforme autorado;
   - monstros nas casas exatas e vinculados à sala correta;
   - baús com ouro/itens exatos;
   - armadilhas do tipo certo na casa certa;
   - heróis surgem na `entrance`;
   - névoa, sala trancada e abrir-porta (despertar) funcionam.
2. **JSON inválido:** introduzir erro (monstro fora do grid, `type` inexistente, porta
   que não é DOOR, item inexistente) → host recebe erro claro e a partida não inicia.
3. **Regressão procedural:** selecionar "Procedural" → comportamento idêntico ao atual
   (mapa 30×30, spawns por role).
4. **Inerte:** confirmar que `exit`/`prisoner`/`objectives` no JSON não produzem efeito
   em jogo nesta fase (apenas guardados).

---

## 7. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Algum caminho de render do cliente com `30` fixo | Auditar `game.js`; a maioria já deriva de `tiles`. Corrigir pontuais. |
| Esquecer uma checagem `MAP_W/MAP_H` em método de `GameRoom` (bug fora-de-limite) | Grep dirigido; cobrir com a masmorra de teste de grid ≠ 30. |
| Itens em `CATALOGO_ITENS` (cliente) vs. `CHEST_ITEMS` (servidor) divergirem | Validar contra a união; documentar que baús aceitam ambos. |
| Mudança futura do esquema | `schema_version` permite migração/recusa controlada. |
