# Salas Obrigatórias (design)

**Data:** 2026-07-16
**Escopo:** sub-feature da Camada C do Modo Mestre — o autor marca salas que o grupo
precisa **visitar** ou **limpar**, expostas como um novo **tipo de objetivo** da fase.

## Contexto

A Camada C são auxílios de autoria. Hoje os objetivos são tipos (`kill_all`,
`kill_target`, `reach_exit`, `open_key_chest`, `rescue_prisoner`) avaliados em
`_objetivo_cumprido`/`_objetivo_status`, com recompensa via `_conceder_objetivo_reward`
e encerramento manual quando o principal cumpre (`mission_complete_pending`). **Não há
flag de sala obrigatória** — esta feature adiciona uma.

### Decisões do brainstorm (confirmadas pelo usuário)

1. **Exigência por sala:** o autor escolhe, por sala, entre **visitar** (um herói
   entra) ou **limpar** (sem monstros vivos nela).
2. **Integração:** um **novo tipo de objetivo** `salas_obrigatorias` (principal ou
   secundário), cumprido quando TODAS as salas marcadas atendem sua condição.
3. **Limpar sala vazia:** conta como cumprida de imediato (`clear` = "sem monstros
   vivos"; sem monstros → já satisfeita).
4. **Status com progresso:** o objetivo reporta **N/M salas** cumpridas.

## Estado atual relevante do código (verificado)

- `self.rooms`: cada sala tem `{id, x, y, w, h, role, locked, doors}`. Sem flag de
  obrigatória.
- `_objetivo_cumprido(obj)` (server.py ~18212): switch por `obj["type"]`; retorna
  bool. `_objetivo_status` → `"done"|"pending"|"failed"`.
- `_check_objectives` (~18241): monta o payload de status (`{"primary": {"type",
  "status"}, "secondary":[…]}`), concede recompensa do principal e liga
  `mission_complete_pending`.
- `player_room(self.rooms, x, y)` já mapeia uma posição à sala que a contém (usado em
  `_disparar_bau_armadilha`).
- Monstros têm `room_id`; "limpar" = nenhum monstro vivo com aquele `room_id`.
- Editor: objetivos editados no painel de nível de masmorra (`!S.sel` de
  `renderPanel`, dropdown `OBJ`); salas editadas no painel da sala selecionada.
  `validar_dungeon` valida os campos autorados.

## Componentes

### 1. Marcação no editor (dado)

- Cada sala ganha campos opcionais: `required` (bool) e `required_mode`
  (`"visit"` | `"clear"`, default `"clear"`).
- **Editor:** no painel da sala selecionada, checkbox "sala obrigatória" + (quando
  marcada) um seletor visitar/limpar. Gravado em `rooms[i]` no `save()`/load.
- **Dropdown de objetivo:** acrescentar `salas_obrigatorias` à lista `OBJ`.

### 2. Novo tipo de objetivo (servidor)

- `_objetivo_cumprido`: ramo `salas_obrigatorias` → `True` se, para toda sala com
  `required`, a condição do seu `required_mode` é satisfeita:
  - `clear`: `not any(m["hp"] > 0 and m.get("room_id") == sala["id"] for m in self.monsters.values())`.
  - `visit`: `sala["id"] in self.salas_visitadas`.
  - Sem salas marcadas → cumprido (vazio) — mas ver validação.
- Helper `_salas_obrigatorias_progresso()` → `(feitas, total)` sobre as salas
  `required`.
- `_check_objectives`: no payload de status, quando o objetivo é
  `salas_obrigatorias`, incluir `"progresso": {"feitas": f, "total": t}` (além de
  `status`). O cliente renderiza "f/t salas".
- **Rastreio de visita:** `self.salas_visitadas` (set de room_id). Inicializado no
  `__init__` (`set()`) e resetado ao entrar numa masmorra nova. Em `handle_move`,
  após confirmar o passo do herói, `sala = player_room(self.rooms, *p["pos"])` e, se
  achou, `self.salas_visitadas.add(sala["id"])`.
- Recompensa: reusa `_conceder_objetivo_reward` (o objetivo já tem `xp`/`reward` como
  os outros).

### 3. Cliente

- O objetivo `salas_obrigatorias` aparece na lista de objetivos como os demais (o
  cliente já renderiza `type` + `status`). Onde o rótulo do objetivo é montado,
  acrescentar um texto amigável ("Salas obrigatórias") e, se `progresso` presente,
  "f/t salas".
- (Opcional/futuro, fora de escopo) destacar as salas obrigatórias pendentes no
  minimapa do mestre.

### 4. Validação (`validar_dungeon`)

- `required_mode`, se presente numa sala, deve ser `"visit"` ou `"clear"`.
- Se algum objetivo (principal ou secundário) é `salas_obrigatorias`, deve existir
  ≥1 sala com `required=True`; senão erro claro ("objetivo salas_obrigatorias sem
  salas marcadas").

## Fronteiras de módulo

- `server.py`: campos na carga da sala (já vêm do defn via `self.rooms`), `salas_visitadas`,
  ramo em `_objetivo_cumprido`, progresso no status, rastreio em `handle_move`,
  validação. Nenhuma mudança nas mecânicas de combate.
- `tools/editor.js`: checkbox+seletor no painel da sala; `salas_obrigatorias` no dropdown;
  serialização `required`/`required_mode` no `rooms[]`.
- `game.js`: rótulo/progresso do novo objetivo na lista de objetivos.

## Testes

- **Servidor** (`tools/test_modo_mestre.py` ou dedicado):
  - `_objetivo_cumprido` `salas_obrigatorias`: cumprido quando todas required rooms
    atendem; pendente se falta uma; `clear` de sala sem monstros = cumprida; `visit`
    exige `salas_visitadas`.
  - `_salas_obrigatorias_progresso` → (feitas, total) correto.
  - `handle_move` marca a sala visitada.
  - `validar_dungeon`: rejeita `salas_obrigatorias` sem salas marcadas e
    `required_mode` inválido.
- **Editor/jogo:** `node --check`; verificação manual — marcar salas, escolher o
  objetivo, e conferir o progresso/cumprimento em jogo.

## Fora de escopo

- Destaque das salas pendentes no minimapa do mestre (futuro).
- Ordem obrigatória de visita (basta cumprir todas, em qualquer ordem).
- Salas obrigatórias como "gate" de encerramento além do objetivo (decisão foi:
  é um tipo de objetivo, não uma trava extra).
- Validador de 6 regras (spec futura da Camada C).
