# Design — Deletar salas + XP e recompensas por objetivo

Data: 2026-06-23
Branch: feat/hud-paladino-richard (a confirmar; provável nova branch de feature)

## Problema

No editor de masmorras (`tools/editor.js`):

1. É possível criar salas (arrastar com a ferramenta "sala"), mas **não há como
   deletar** uma sala já criada — a ferramenta "apagar" só limpa tiles/entidades,
   nunca o retângulo da sala em `S.rooms`.
2. Os objetivos de missão são apenas `{type}`. Não dá para definir **XP** por
   objetivo nem **recompensa** (ouro / itens / armas / itens mágicos).

No servidor, os objetivos secundários concedem um bônus fixo
(`OBJ_BONUS_XP=50` / `OBJ_BONUS_OURO=25`) **a cada herói vivo** (valor cheio, não
dividido), e isso só acontece quando o objetivo **principal** é cumprido — momento
em que a fase encerra automaticamente (cidade/vitória).

## Objetivo

- Permitir deletar salas no editor.
- Permitir, no editor, definir por objetivo (principal e secundários): XP total e
  recompensa (ouro + itens do catálogo).
- No jogo: dividir o XP entre os heróis vivos, dividir o ouro, e largar os itens no
  chão como um baú de recompensa.
- Trocar o encerramento automático da fase por um **encerramento manual** com
  confirmação, para que o grupo possa pegar os itens antes de terminar.

## Decisões (confirmadas com o usuário)

- **Deletar sala:** perguntar a cada vez se também limpa o chão (volta a parede) ou
  mantém o chão.
- **XP:** o valor no editor é o **total** do objetivo, **dividido igualmente entre
  os heróis vivos** no momento da conclusão.
- **Escopo:** **principal e secundários** têm XP + recompensa configuráveis.
- **Recompensa:** ouro dividido entre os vivos; itens largados no chão (baú de
  recompensa). **Um único baú** agrega os itens de todos os objetivos cumpridos.
- **Encerramento:** cumprir o principal **não** encerra a fase; larga a recompensa,
  habilita um botão "Encerrar missão" com aviso/confirmação, e só então encerra.

## Componentes e mudanças

### 1. Deletar salas — `tools/editor.js` (somente editor, sem servidor)

- No `renderPanel()`, no ramo `k === "room"`, adicionar botão **🗑 Deletar sala**.
- Ao clicar, mostrar confirmação inline com 2 ações (cancelar = não clicar):
  - **Deletar (manter chão):** remove a sala de `S.rooms`; desvincula apenas as
    portas que pertenciam a ela (suas entradas em `r.doors`).
  - **Deletar (limpar chão):** idem, mas converte todas as casas do retângulo da
    sala para `WALL` e remove os tiles `DOOR` internos (e suas referências em
    `doors` de qualquer sala).
- Entidades com `room_id` apontando para a sala deletada passam a `room_id = null`
  (não são apagadas): monstros, prisioneiro.
- Após deletar: `S.sel = null; renderPanel(); render()`.

Salas são dado de autoria — nenhuma mudança no servidor para esta parte.

### 2. Modelo de dados dos objetivos

Cada objetivo (primary e cada item de secondary) passa de `{type}` para:

```json
{
  "type": "kill_all",
  "xp": 150,
  "reward": { "gold": 100, "items": [{ "id": "magic_sword" }] }
}
```

- `xp` (int ≥ 0), `reward.gold` (int ≥ 0), `reward.items` (lista de `{id}`) — todos
  **opcionais**.
- **Compatibilidade retroativa** (dungeons salvas antes desta feature):
  - Secundário sem `xp` → usa `OBJ_BONUS_XP` (50). Sem `reward.gold` → `OBJ_BONUS_OURO` (25).
  - Principal sem `xp`/`reward` → sem recompensa extra.
  - Itens de recompensa usam o mesmo catálogo dos baús (`CAT.items` /
    `CHEST_ITEMS`/`SHOP_*` no servidor para resolver a definição por `id`).

### 3. Editor de objetivos — `tools/editor.js` (`renderPanel`, ramo sem seleção)

Para o **principal** e para **cada secundário**:

- Campo numérico **XP (total)**.
- Campo numérico **ouro**.
- Lista de **itens de recompensa** com adicionar/remover, reutilizando o seletor de
  `CAT.items` (mesmo padrão visual do editor de baú em `editor.js`). O catálogo já
  inclui armas (`sword`, `magic_sword`, `bow`, `staff`) e itens mágicos
  (`amulet`, `ring`, `cloak`, `boots`...), então não há novas categorias.

Persistência:

- `buildJSON()` grava `xp` e `reward` em `objectives.primary` e em cada
  `objectives.secondary[i]` quando definidos.
- `loadJSON()` lê esses campos (com defaults para ausentes).
- Default ao adicionar um secundário novo: `{ type, xp: 50, reward: { gold: 25, items: [] } }`.

### 4. Concessão de recompensa — `server.py`

Generalizar `_conceder_bonus_secundario(obj)` para uma função que lê os campos do
objetivo, ex. `_conceder_objetivo_reward(obj, is_primary)`:

- **XP:** `total = obj.get("xp", default)`; cada herói vivo recebe
  `max(1, total // n_vivos)`; chama `_check_level_up`.
- **Ouro:** `total_ouro = obj["reward"]["gold"]` (com default); cada vivo recebe
  `total_ouro // n_vivos` (resto descartado, mínimo 0).
- **Itens:** coletados num acumulador para spawn de um único baú (ver §5).
- `gm_say` com o resumo (XP por herói, ouro por herói, itens largados).

Resolução de item por `id`: reaproveitar o padrão de
`CHEST_ITEMS`/`SHOP_WEAPONS`/`SHOP_MERCHANT` já usado em `_roll_monster_loot`.

### 5. Encerramento manual da missão — `server.py` + `game.js`

Estado novo na sala/jogo: `self.mission_complete_pending = False`.

`_check_objectives()` (server.py ~12201): quando o principal é cumprido pela 1ª vez
(`not self._objetivo_concluido`):

1. Marca `self._objetivo_concluido = True`.
2. Concede recompensa do principal e de cada secundário cumprido (§4), acumulando
   todos os itens.
3. Se houver itens, spawna **um** baú de recompensa via `_spawn_chest(pos, 0,
   itens)` numa casa livre perto do herói que concluiu (fallback: entrada / primeira
   casa de chão livre).
4. Define `self.mission_complete_pending = True` e `gm_say` avisando que a missão
   pode ser encerrada (botão).
5. **Não** chama `_voltar_para_cidade`/`end_game` aqui (remover a transição
   automática deste ponto).

Novo handler `handle_encerrar_missao(pid)`:

- Só age se `self.mission_complete_pending` e a fase ainda está `playing`.
- Executa a transição que antes ficava em `_check_objectives`:
  - Campanha com mais fases → outro/`_campaign_outro`, `campaign_phase += 1`,
    `dungeon_generated = False`, `_voltar_para_cidade()`.
  - Caso contrário → `end_game(victory=True, story=...)`.

`push_state`/`game_state`: incluir `mission_complete_pending` no payload.

Protocolo (CLAUDE.md):

- Client→Server: **`encerrar_missao`** — `—` (herói encerra a missão após o objetivo
  principal cumprido; só habilitado quando `mission_complete_pending`).
- Nota de objetivos: cada objetivo aceita `xp` e `reward { gold, items:[{id}] }`;
  recompensa concedida ao cumprir o principal; XP/ouro divididos entre vivos; itens
  largados num baú; encerramento manual via `encerrar_missao`.

Cliente (`game.js`):

- `renderObjectivesHUD` (≈2953): quando `GS.gameState.mission_complete_pending`
  (expor via getter no `gameState.js`) e for jogo autorado, mostrar botão
  **🏁 Encerrar missão**.
- `onclick`: `confirm("Pegue os itens de recompensa antes de encerrar. Tem certeza
  que quer terminar a missão?")`; se OK, `GS.send({type:"encerrar_missao"})`
  (action sender em `gameState.js`).

### 6. `src/gameState.js`

- Expor `mission_complete_pending` (getter) a partir de `game_state`.
- Action sender `encerrarMissao()` → `send({type:"encerrar_missao"})`.

## Fora de escopo (YAGNI)

- Múltiplos baús de recompensa (um por objetivo) — usar um único baú agregado.
- Distribuição automática "quem fica com qual item" — itens vão para o chão.
- Categorização nova de itens (arma vs mágico) — usar o catálogo existente.
- Pagamento de secundário no instante em que é cumprido (mantém-se "tudo no fim",
  porém agora gated pelo botão de encerrar).

## Testes / verificação

- Editor: criar sala, deletar (manter chão / limpar chão), confirmar `S.rooms`,
  `S.tiles`, `doors` e `room_id` das entidades via `window.EDITOR`.
- Editor: definir XP/ouro/itens em principal e secundário; `buildJSON()` →
  `loadJSON()` round-trip preserva os campos.
- Servidor: dungeon autorada com objetivo principal + secundário com recompensas;
  ao cumprir o principal, verificar XP dividido, ouro dividido, baú de recompensa
  com os itens, `mission_complete_pending=True` e que a fase **não** encerrou.
- `encerrar_missao` faz a transição correta (cidade em campanha / vitória).
- Dungeon antiga (sem `xp`/`reward`) mantém comportamento (50/25 nos secundários).
