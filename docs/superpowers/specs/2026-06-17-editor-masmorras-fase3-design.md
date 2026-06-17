# Editor de Masmorras — Fase 3: Objetivos, Prisioneiro e Saída (em jogo)

**Data:** 2026-06-17
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Aprovado — pronto para plano de implementação

---

## Contexto: onde a Fase 3 entra

Terceira das 4 fases do editor de masmorras (ver [[editor-masmorras-fases]] e os specs das
Fases 1 e 2). A Fase 1 já **lê, valida e guarda** (inertes em `self.dungeon_def`) os campos
`exit`, `prisoner` e `objectives` das masmorras autoradas; a Fase 2 dá ao editor a UI para
autorá-los. A **Fase 3 dá vida a eles em jogo**.

- **Aplica-se só às masmorras autoradas** (`mode == "authored"`). O modo **procedural fica
  inalterado** (vitória ao matar o boss, como hoje).
- Lógica quase toda no `server.py` (autoritativo) + acréscimos de exibição no cliente
  (`gameState.js`/`game.js`): HUD de objetivos, casa de saída, peão do prisioneiro, botão
  "libertar".
- Fase 4 (campanha/ordem de fases/progressão) vem depois e reaproveita a conclusão de
  objetivo desta fase.

### Decisões de produto (aprovadas no brainstorm)

- **rescue_prisoner** = libertar **e** escoltar o prisioneiro vivo até a **saída** (ou à
  escada de entrada, se não houver saída).
- **Morte do prisioneiro** → só o **objetivo de resgate falha** (marcado); os heróis seguem
  vivos. Se o resgate era o principal, a masmorra não tem mais como ser concluída (saem pela
  escada e tentam de novo). **Não** é derrota do grupo.
- **Libertar** = ação de um **herói adjacente** (nova mensagem `libertar_prisioneiro`).
- **Secundários cumpridos** → **bônus de XP/ouro** ao grupo na conclusão.
- **Principal cumprido** → `end_game(victory)` (vitória → cidade), como o boss-kill faz hoje.

---

## Arquitetura atual relevante (verificada)

- `enter_dungeon` (`server.py:3442`) ramifica `autorada = self.mode == "authored" and
  self.dungeon_def is not None` e chama `load_authored_dungeon(self.dungeon_def)`
  (`server.py:3354`), que hoje só **stasha** `self.dungeon_def` e instancia tiles/salas/
  monstros/baús/armadilhas/entrada — **não** instancia exit/prisoner/objectives, e o baú
  não carrega `key_objective`.
- `end_game(victory)` (`server.py:11823`): `phase="ended"`, `dungeon_generated=False` em
  vitória, broadcast `game_over`. (Procedural: matar monstro com `m.get("boss")` chama
  `end_game(victory=True)` — Fase 1 forçou `m["boss"]=False` em masmorras autoradas, então
  esse caminho **não dispara** nelas; a conclusão autorada será dirigida por objetivo.)
- `m["authored_target"]` / `m["authored_boss"]` já são gravados por `load_authored_dungeon`
  (Fase 1) a partir de `mo.get("target")` / `mo.get("boss")`.
- `push_state` (`server.py:11863`) serializa o estado para o cliente (inclui `stairs_pos`).
  Acrescentaremos `objectives`, `exit_pos`, `prisoner` aqui.
- Turnos: heróis agem; depois o processamento do turno dos monstros (onde os monstros se
  movem/atacam). O prisioneiro libertado terá seu passo de "seguir" nesse mesmo momento.

---

## 1. Instanciar o que estava inerte (no carregador autorado)

`load_authored_dungeon` (ou `enter_dungeon`, no bloco autorado) passa a instanciar, a
partir de `self.dungeon_def`:

- `self.exit_pos = [x, y]` (ou `None` se não houver `exit`).
- `self.objectives = {"primary": {...}, "secondary": [...]}` (cópia do def).
- `self.prisoner` = `None` se não houver, senão um dict vivo:
  ```python
  {"pos": [x,y], "room_id": rid, "hp": PRIS_HP, "max_hp": PRIS_HP,
   "freed": False, "alive": True}
  ```
  (`PRIS_HP` = constante, ex. 12.)
- `self.objective_status` = estado vivo derivado a cada checagem (ver §4); `self.rescue_failed = False`.
- O baú marcado `key_objective` passa a carregar essa flag: `_spawn_chest` (ou o laço do
  carregador) grava `chest["key_objective"] = True` no baú correspondente.

No procedural, todos esses ficam em valores neutros (`self.exit_pos=None`,
`self.prisoner=None`, `self.objectives=None`) — e nada da lógica de objetivo roda.

Reset por expedição (no bloco `nova` de `enter_dungeon`): zera `self.prisoner`,
`self.exit_pos`, `self.objectives`, `self.objective_status`, `self.rescue_failed`.

---

## 2. Tipos de objetivo e condições de conclusão

`_objetivo_cumprido(obj) -> bool`, por tipo:

| Tipo | Cumprido quando |
|---|---|
| `kill_all` | nenhum monstro vivo (`all(m["hp"]<=0 …)`) |
| `kill_target` | todo monstro com `authored_target` está morto (se não houver nenhum `authored_target`, é inalcançável — erro de autoria; servidor não trava) |
| `reach_exit` | algum herói vivo está sobre `self.exit_pos` |
| `open_key_chest` | o baú com `key_objective` foi aberto (`chest["aberto"]`/looted) |
| `rescue_prisoner` | `self.prisoner.freed and self.prisoner.alive` e o prisioneiro está a Chebyshev ≤1 da saída (ou da `stairs_pos`, se não houver saída) |

Secundários usam a mesma função. Um objetivo de resgate cujo prisioneiro morreu
(`self.rescue_failed`) reporta status `failed` e nunca "cumprido".

---

## 3. Prisioneiro (mecânica)

- **Cativo:** começa em `prisoner.pos` (normalmente sala trancada), peão no tabuleiro com
  HP próprio. Enquanto não libertado, fica imóvel e não é alvo automático dos monstros
  (está "preso").
- **Libertar:** mensagem `libertar_prisioneiro` (sem campos) de um herói **adjacente**
  (Chebyshev ≤1) ao prisioneiro, no turno dele — **ação principal** (gasta a ação). Marca
  `freed=True`. A partir daí ele segue.
- **Seguir (IA):** 1 passo por rodada, no processamento do turno dos monstros, em direção
  ao **herói vivo mais próximo**, pelo mesmo pathing dos monstros (casas livres; não entra
  em parede/porta fechada). Não ataca.
- **Alvo de monstros:** uma vez libertado, é um **alvo válido** para os ataques dos
  monstros (entra na lista de alvos da IA, com HP); reusa a aplicação de dano existente.
- **Morte:** HP ≤ 0 → `alive=False`, `self.rescue_failed=True`, vira cadáver/sai do
  tabuleiro. **Não** encerra a partida.
- **Escolta:** §2 (`rescue_prisoner`).

---

## 4. Avaliação de objetivos e conclusão

- `_check_objectives()` (async) roda **após eventos relevantes**: morte de monstro
  (kill_all/kill_target), baú aberto (open_key_chest), movimento de herói (reach_exit),
  passo do prisioneiro (rescue/escolta). Só roda quando `autorada` e `self.objectives`.
- Recalcula `self.objective_status` (cada objetivo → `done`/`pending`/`failed`) para o HUD.
- Se o **principal** está `done`:
  1. concede o **bônus de cada secundário cumprido** (XP+ouro por `_conceder_bonus_secundario`;
     constantes `OBJ_BONUS_XP`, `OBJ_BONUS_OURO`), narrando no GM log;
  2. chama `end_game(victory=True)`.
- Idempotência: uma flag (`self._objetivo_concluido`) evita conceder bônus / encerrar duas
  vezes.

---

## 5. Estado serializado + cliente

`push_state` acrescenta (sempre presentes; `null`/vazio no procedural):

- `objectives`: `{primary:{type,status}, secondary:[{type,status}]}` com status ao vivo.
- `exit_pos`: `self.exit_pos` (ou `null`).
- `prisoner`: `{pos, freed, hp, max_hp, alive}` (ou `null`).

Cliente:
- `gameState.js`: getters `objectives()`, `exitPos()`, `prisoner()`; sender
  `libertarPrisioneiro()` (envia `{type:"libertar_prisioneiro"}`); decisor puro
  `prisioneiroLibertavel()` (há prisioneiro cativo adjacente ao herói da vez?) para
  habilitar o botão.
- `game.js`: renderiza a **casa de saída** (🏁) no 2D e 3D; o **peão do prisioneiro**
  (cativo vs. seguindo); um **HUD de objetivos** (principal + secundários, cada um com ícone
  de status ✅/⬜/❌); e o **botão "Libertar"** quando `prisioneiroLibertavel()`.

Segue a regra de arquitetura (CLAUDE.md): lógica/decisores em `gameState.js`, render em
`game.js`, servidor autoritativo.

---

## 6. Protocolo (resumo das mudanças)

**Client → Server**

| Mensagem | Campos | Nota |
|---|---|---|
| `libertar_prisioneiro` | — | Herói adjacente ao prisioneiro cativo; ação principal. |

**Server → Client**

`game_state` ganha `objectives`, `exit_pos`, `prisoner`. (`game_over`/`gm_narration`
reaproveitados para vitória e narração de bônus.)

---

## 7. Teste

Testes headless de `GameRoom` (estilo `tools/test_*.py`, stub de rede), reusando uma
masmorra autorada de fixture (criar `dungeons/test_fase3.json` com saída + prisioneiro +
baú-chave + alvo). Casos:

- **kill_all**: matar todos → principal `done` → `end_game(victory)` chamado.
- **kill_target**: matar só o monstro `target` → conclui; matar um não-alvo → não conclui.
- **reach_exit**: herói pisa na saída → conclui.
- **open_key_chest**: abrir o baú-chave → conclui; abrir outro baú → não.
- **rescue_prisoner**: libertar (adjacente) → `freed`; passo de seguir aproxima do herói;
  escoltar até ≤1 da saída → conclui. Morte do prisioneiro → `rescue_failed`, status
  `failed`, partida **não** encerra.
- **secundários**: ao concluir o principal com um secundário cumprido, o grupo recebe o
  bônus de XP/ouro.
- **Regressão**: procedural inalterado (boss-kill → vitória; sem objetivos/prisioneiro).

---

## 8. Fora de escopo (Fase 4)

Ordem de fases, várias campanhas, progressão contínua (HP/XP/ouro/itens entre fases),
avançar para a próxima fase ao concluir (na Fase 3, conclusão = vitória → cidade, como hoje).

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Disparar `end_game` mais de uma vez | Flag `self._objetivo_concluido`. |
| `kill_target` sem nenhum monstro `target` (erro de autoria) | Inalcançável, mas servidor não trava; o editor (Fase 2) pode alertar futuramente. |
| Prisioneiro como alvo de monstros mexer na seleção de alvos da IA | Incluí-lo como alvo só quando `freed and alive`; reusar a aplicação de dano existente; cobrir com teste. |
| Objetivo de saída/escolta sem `exit` autorado | Escolta cai na `stairs_pos`; `reach_exit` sem saída é erro de autoria (inalcançável, sem crash). |
| Procedural afetado | Toda a lógica protegida por `autorada and self.objectives`; regressão coberta por teste. |
| Campos novos no `game_state` quebrarem clientes antigos | Sempre presentes com `null`/vazio; cliente trata ausência com defaults. |
