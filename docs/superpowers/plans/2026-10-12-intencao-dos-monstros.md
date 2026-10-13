# Intenção dos monstros (previsão) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar ao jogador, na vez dele, quem cada monstro visível atacaria "se agisse agora", com setas no tabuleiro 2D/3D e uma linha no tooltip.

**Architecture:** Um mixin de servidor só de leitura (`monster_intent.py`) reusa os mesmos helpers de alvo/alcance da IA real e responde à mensagem privada `prever_intencoes` com `intencoes_monstros`. No cliente, um módulo puro (`src/intencaoMonstros.js`) decide o que mostrar (modo, filtro, contador, descarte de resposta velha); `game.js` só desenha (2D no fim do `renderMap`, 3D num grupo reutilizável) e guarda a preferência. A estrutura de dados é a mesma que uma futura "intenção gravada" (evolução B) usaria.

**Tech Stack:** Python 3 (`websockets`, mixin de `GameRoom`), JS vanilla (sem bundler), Three.js r128, testes por script (`python tools/test_*.py`, `node tools/test_*.js`).

**Spec:** `docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md`

## Global Constraints

- Servidor autoritativo; `src/gameState.js` sem `document`/`window`/`canvas`/`THREE`; `game.js` só renderiza (CLAUDE.md, "Regras de Arquitetura").
- **Estado primeiro, visual depois:** ordem das tarefas = servidor → protocolo → módulo puro/GS → render → preferência.
- Previsão **só leitura**: depois de `_prever_intencoes`, `_monster_ai_focus_target_id` e `_monster_ai_reserved_tiles` voltam exatamente ao valor anterior (ou ficam ausentes se não existiam) e nenhum dict de monstro/jogador muda.
- Todo atributo novo de `GameRoom` precisa de categoria em `FOTO_SALA_CATEGORIAS` (`"efemero"`).
- Texto de interface: chaves `ui.<área>.<slug>` em `src/lang/interface.js` com `pt` e `en`; `python tools/dividas.py` e `python tools/test_interface.py` continuam limpos.
- `game.js`, `server.py` e `CLAUDE.md` estão em **CRLF**: edite com a ferramenta de edição, nunca com script que casa `\n`.
- Preferência em `localStorage["lfh_intencoes"]`, sempre com `try/catch`; valores `off` | `grupo` (padrão) | `todas`.
- Mensagem do cliente `prever_intencoes {}` (+`heroi` automático no Solo com grupo); resposta `intencoes_monstros {rodada, itens:[…]}` só ao solicitante. Taxa mínima de 150 ms por jogador no servidor.
- Item: `{monstro_id, alvo_id, alvo_tipo ("heroi"|"animado"), alvo_pos, acao ("corpo"|"distancia"|"ameaca"), alcanca (bool), casa_ataque ([x,y]|null), certeza ("firme"|"provavel")}`.
- Execução em **worktree a partir do `master`** (`superpowers:using-git-worktrees`): a árvore principal tem trabalho em andamento do autor em `game.js`, `server.py`, `index.html` etc. que não deve ser tocado nem commitado. Commits só com caminhos explícitos. Sem push sem pedido. Trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

- **Herói morto/desconectado/fora da masmorra pede previsão:** resposta vazia ou nenhuma, nunca erro (Task 2).
- **Monstro escondido (`invisivel_sombras`, `invisivel_magico`, `oculto_vela`) ou dormente:** nunca aparece (Task 1).
- **Mestre humano com monstro em Manual:** sem previsão; em Semi, alvo forçado "firme" (Task 1).
- **Chamadas repetidas/rajada de pedidos:** limite de taxa e cache sem estourar (Task 2).
- **Resposta velha chegando depois do `game_state` novo:** cliente descarta (Task 3).
- **`localStorage` bloqueado ou valor inválido:** cai em `grupo` sem erro (Task 3 e Task 6).
- **Exceção interna na previsão:** devolve lista vazia, não derruba o handler (Task 1).

---

## File Structure

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `monster_intent.py` | criar | Mixin `MonsterIntent`: `_prever_intencoes`, `_intent_*` (só leitura) |
| `server.py` | modificar | herdar o mixin, atributos efêmeros, categoria da foto, `handle_prever_intencoes`, despacho |
| `src/intencaoMonstros.js` | criar | Módulo puro `window.IntencaoMonstros` (modos, seleção, contador, descarte, estilo) |
| `src/gameState.js` | modificar | `pedirIntencoes`, `intencoes`, caso `intencoes_monstros`, invalidação por `game_state` |
| `index.html` | modificar | carregar `src/intencaoMonstros.js` ao lado de `src/guiaTutorial.js` |
| `game.js` | modificar | pedido automático, desenho 2D/3D, tooltip, preferência, atalho T |
| `src/lang/interface.js` | modificar | chaves PT/EN |
| `tools/test_monster_intent.py` | criar | testes do servidor |
| `tools/test_intencoes_cliente.js` | criar | testes do módulo puro e da fiação |
| `CLAUDE.md` | modificar | seção curta documentando a feature |

---

### Task 1: Núcleo da previsão no servidor (`monster_intent.py`)

**Files:**
- Create: `monster_intent.py`
- Modify: `server.py` (import + herança de `GameRoom`, ~linhas 31 e 11317; `FOTO_SALA_CATEGORIAS` ~3493; `__init__` perto de 11438)
- Test: `tools/test_monster_intent.py`

**Interfaces:**
- Produces: `GameRoom._prever_intencoes(pid) -> list[dict]` (item descrito em Global Constraints). Atributos `self._intent_cache: dict` e `self._intent_ultimo: dict` (usados na Task 2).
- Consumes (já existem): `_ativo`, `_alvos_hostis_para_monstros`, `_heroi_enxerga_monstro(hero, m)`, `_monstro_ativo_em_combate`, `_mestre_ativo`, `_get_monster_primary_target(m, targets)`, `_alvos_visiveis_para_monstro(m, targets)`, `_monster_attack_in_range(m, pos, atk_def)`, `_monster_hostility_attacks(m)`, `_monster_melee_goal(m, target_obj)`, `_monster_ranged_goal(m, target_obj, atk_def)`, `_master_reach_bfs(m, budget)`, `_monster_ai_role(m)`, `_requiem_forca_bardo(m)`.

- [ ] **Step 1: Escrever o teste que falha** (`tools/test_monster_intent.py`)

```python
"""Intenção dos monstros: previsão só de leitura, fiel à IA real.
Roda da raiz: python tools/test_monster_intent.py
Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
"""
import asyncio
import copy
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    """Sala 18×10 vazia, fase 'playing', sem rede."""
    r = S.GameRoom("INTENT")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 11):
        for x in range(1, 19):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 18, "h": 10, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    return r


def heroi(r, pid, nome, classe, pos, hp=None):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    if hp is not None:
        h["hp"] = hp
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def monta(r):
    r._rebuild_initiative()


print("[1] herói à vista é o alvo; sem efeito colateral")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
antes = (copy.deepcopy(r.monsters), copy.deepcopy(r.players),
         r.__dict__.get("_monster_ai_focus_target_id", "AUSENTE"),
         r.__dict__.get("_monster_ai_reserved_tiles", "AUSENTE"))
itens = r._prever_intencoes("a")
check("um item para o orc", len(itens) == 1 and itens[0]["monstro_id"] == m["id"])
check("alvo é a Ana", itens and itens[0]["alvo_id"] == "a" and itens[0]["alvo_tipo"] == "heroi")
check("alvo_pos é a casa da Ana", itens and itens[0]["alvo_pos"] == [5, 5])
check("orc a 3 casas alcança (movimento 4+)", itens and itens[0]["alcanca"] is True)
check("casa_ataque é adjacente ao herói",
      itens and itens[0]["casa_ataque"] is not None
      and max(abs(itens[0]["casa_ataque"][0] - 5), abs(itens[0]["casa_ataque"][1] - 5)) == 1)
check("ação corpo a corpo", itens and itens[0]["acao"] == "corpo")
depois = (r.monsters, r.players,
          r.__dict__.get("_monster_ai_focus_target_id", "AUSENTE"),
          r.__dict__.get("_monster_ai_reserved_tiles", "AUSENTE"))
check("monstros e jogadores idênticos", antes[0] == depois[0] and antes[1] == depois[1])
check("foco e casas reservadas restaurados (inclusive ausentes)",
      antes[2] == depois[2] and antes[3] == depois[3])

print("[2] paridade com a IA real: escolhe o mais ferido")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
b = heroi(r, "b", "Bia", "warrior", [5, 7], hp=3)
m = monstro(r, "orc", [8, 6])
monta(r)
alvo_real = r._get_monster_primary_target(
    m, r._alvos_visiveis_para_monstro(m, r._alvos_hostis_para_monstros()))
r._monster_ai_focus_target_id = None
itens = r._prever_intencoes("a")
check("previsão = alvo que a IA escolheria",
      itens and itens[0]["alvo_id"] == alvo_real["obj"]["id"] == "b")

print("[3] exclusões")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
m["invisivel_sombras"] = True
monta(r)
check("monstro escondido nunca aparece", r._prever_intencoes("a") == [])
m.pop("invisivel_sombras")
m["hp"] = 0
check("monstro morto não aparece", r._prever_intencoes("a") == [])
m["hp"] = m["max_hp"]
r.rooms[0]["locked"] = True
check("sala trancada (dormente) não aparece", r._prever_intencoes("a") == [])
r.rooms[0]["locked"] = False
r.tiles[5][6] = S.WALL; r.tiles[4][6] = S.WALL; r.tiles[6][6] = S.WALL
r.tiles[3][6] = S.WALL; r.tiles[7][6] = S.WALL; r.tiles[2][6] = S.WALL
r.tiles[8][6] = S.WALL; r.tiles[1][6] = S.WALL; r.tiles[9][6] = S.WALL; r.tiles[10][6] = S.WALL
check("monstro atrás de parede (fora da visão do herói) não aparece",
      r._prever_intencoes("a") == [])
check("herói inexistente: lista vazia", r._prever_intencoes("zzz") == [])

print("[4] Mestre: Manual sem previsão, Semi com alvo forçado")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
b = heroi(r, "b", "Bia", "warrior", [5, 7])
m = monstro(r, "orc", [8, 6])
monta(r)
r.master_pid = "mestre"
r.connections = {"mestre": object(), "a": object(), "b": object()}
m["alertado"] = True
m["control_mode"] = "manual"
check("Manual: sem previsão", r._prever_intencoes("a") == [])
m["control_mode"] = "semi"
m["master_target_id"] = "b"
itens = r._prever_intencoes("a")
check("Semi: alvo forçado é a Bia", itens and itens[0]["alvo_id"] == "b")
check("Semi: certeza firme", itens and itens[0]["certeza"] == "firme")

print("[5] exceção interna vira lista vazia e restaura o estado")
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
r._monster_ai_focus_target_id = "marca"
orig = r._get_monster_primary_target
def quebra(*args, **kw):
    raise RuntimeError("boom")
r._get_monster_primary_target = quebra
check("exceção -> []", r._prever_intencoes("a") == [])
r._get_monster_primary_target = orig
check("foco restaurado mesmo após exceção", r._monster_ai_focus_target_id == "marca")

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -X utf8 tools/test_monster_intent.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_prever_intencoes'`.

- [ ] **Step 3: Implementar o mixin** (`monster_intent.py`)

```python
"""Previsão da intenção dos monstros (somente leitura).

Mixin de GameRoom. Reusa os helpers de alvo/alcance da IA real para responder
"quem este monstro atacaria se agisse agora?" sem alterar nenhum estado: o foco
coletivo e as casas reservadas são salvos e restaurados em `finally`.

Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
O item devolvido é a MESMA estrutura que a evolução B (intenção gravada pela IA
no fim do turno do monstro) usaria.
"""

_AUSENTE = object()


class MonsterIntent:
    # ── seleção de quem entra na previsão ────────────────────────────────────
    def _intent_observadores(self, p):
        """Heróis cuja visão vale para este pedido: o próprio e os do mesmo
        controlador (Solo com grupo)."""
        ctrl = p.get("controlador")
        obs = [p]
        if ctrl:
            obs += [q for q in self.players.values()
                    if q is not p and (q.get("controlador") == ctrl
                                       or q.get("id") == ctrl) and self._ativo(q)]
        return obs

    def _intent_monstros_em_ordem(self):
        """Monstros na ordem da iniciativa vigente (reproduz o foco coletivo);
        os que não estão na fila vão ao fim."""
        ordem = [e.get("id") for e in self.initiative_order if e.get("kind") == "monster"]
        vistos = set()
        saida = []
        for mid in ordem:
            m = self.monsters.get(mid)
            if m is not None and mid not in vistos:
                vistos.add(mid)
                saida.append(m)
        for mid, m in self.monsters.items():
            if mid not in vistos:
                saida.append(m)
        return saida

    def _intent_monstro_elegivel(self, m):
        if m.get("hp", 0) <= 0:
            return False
        if m.get("invisivel_sombras") or m.get("invisivel_magico") or m.get("oculto_vela"):
            return False
        if not self._monstro_ativo_em_combate(m):
            return False
        if self._mestre_ativo() and m.get("control_mode") == "manual":
            return False
        return True

    # ── um monstro ────────────────────────────────────────────────────────────
    def _intent_compulsao(self, m):
        if self._requiem_forca_bardo(m):
            return True
        if m.get("provocado") and m.get("provocado_turnos", 0) > 0:
            return True
        return bool(self._mestre_ativo() and m.get("control_mode") == "semi"
                    and m.get("master_target_id"))

    def _intent_de_monstro(self, m, alvos_base):
        alvos = self._alvos_visiveis_para_monstro(m, alvos_base)
        escolhido = self._get_monster_primary_target(m, alvos)
        if not escolhido:
            return None
        obj = escolhido["obj"]
        ataques = self._monster_hostility_attacks(m)
        a_dist = next((a for a in ataques if a.get("range")), None)
        a_corpo = next((a for a in ataques if not a.get("range")), None)
        papel = self._monster_ai_role(m)
        alvo_pos = list(obj["pos"])

        # 1) já em alcance sem se mexer?
        em_alcance = None
        for atk in ([a_dist] if a_dist else []) + ([a_corpo] if a_corpo else []):
            if self._monster_attack_in_range(m, alvo_pos, atk):
                em_alcance = atk
                break
        casa = None
        atk_usado = em_alcance
        alcanca = False
        if em_alcance is not None:
            alcanca, casa = True, list(m["pos"])
        else:
            # 2) alcança movendo? (mesma busca de casa da IA, com o BFS do movimento)
            try:
                orcamento = int(m.get("movement", 4) or 0)
            except (TypeError, ValueError):
                orcamento = 4
            alcancaveis = self._master_reach_bfs(m, orcamento)
            if a_dist is not None:
                goal = self._monster_ranged_goal(m, escolhido, a_dist)
                atk_usado = a_dist
            else:
                goal = self._monster_melee_goal(m, escolhido)
                atk_usado = a_corpo
            if goal is not None and tuple(goal) in alcancaveis:
                alcanca, casa = True, list(goal)

        if papel in {"controlador", "suporte"} or atk_usado is None:
            acao = "ameaca"
        elif atk_usado.get("range"):
            acao = "distancia"
        else:
            acao = "corpo"

        # "firme" só quando nada pode mudar a escolha: compulsão, ou único alvo
        # visível já ao alcance sem mover. Habilidade especial nunca é firme.
        firme = (acao != "ameaca"
                 and (self._intent_compulsao(m)
                      or (len(alvos) == 1 and em_alcance is not None)))
        return {
            "monstro_id": m["id"],
            "alvo_id": obj.get("id"),
            "alvo_tipo": "animado" if escolhido.get("kind") == "animado" else "heroi",
            "alvo_pos": alvo_pos,
            "acao": acao,
            "alcanca": bool(alcanca),
            "casa_ataque": casa if alcanca else None,
            "certeza": "firme" if firme else "provavel",
        }

    # ── API ───────────────────────────────────────────────────────────────────
    def _prever_intencoes(self, pid):
        """Lista de intenções dos monstros que o herói `pid` enxerga agora."""
        p = self.players.get(pid)
        if not p or not self._ativo(p) or not p.get("pos"):
            return []
        foco_antes = self.__dict__.get("_monster_ai_focus_target_id", _AUSENTE)
        reservas_antes = self.__dict__.get("_monster_ai_reserved_tiles", _AUSENTE)
        try:
            self._monster_ai_focus_target_id = None
            self._monster_ai_reserved_tiles = set()
            alvos_base = self._alvos_hostis_para_monstros()
            observadores = self._intent_observadores(p)
            itens = []
            for m in self._intent_monstros_em_ordem():
                if not self._intent_monstro_elegivel(m):
                    continue
                if not any(self._heroi_enxerga_monstro(o, m) for o in observadores):
                    continue
                item = self._intent_de_monstro(m, alvos_base)
                if item:
                    itens.append(item)
            return itens
        except Exception:
            return []
        finally:
            for nome, antes in (("_monster_ai_focus_target_id", foco_antes),
                                ("_monster_ai_reserved_tiles", reservas_antes)):
                if antes is _AUSENTE:
                    self.__dict__.pop(nome, None)
                else:
                    setattr(self, nome, antes)
```

Em `server.py` (use a ferramenta de edição, CRLF):

1. Junto ao import de `tutorial_training` (~linha 31): `from monster_intent import MonsterIntent`.
2. `class GameRoom(TutorialTraining):` → `class GameRoom(TutorialTraining, MonsterIntent):`.
3. Em `GameRoom.__init__`, logo depois de `self.initiative_order = []` (~11438), acrescentar:

```python
        self._intent_cache = {}     # pid -> (assinatura, itens); ver MonsterIntent
        self._intent_ultimo = {}    # pid -> time.monotonic() do último pedido
```

4. Em `FOTO_SALA_CATEGORIAS`, ao lado de `"send_to": "efemero"` (~3563), acrescentar `"_intent_cache": "efemero", "_intent_ultimo": "efemero",`.

- [ ] **Step 4: Rodar e ver passar**

Run: `python -X utf8 tools/test_monster_intent.py` → `N ok, 0 falhas`.
Run: `python -X utf8 tools/test_salvar_masmorra.py` → continua verde (a varredura de atributos sem categoria).
Se a seção [3] "atrás de parede" falhar porque o monstro ainda é visto, ajuste as paredes do teste para isolar de fato o monstro (a asserção é sobre visibilidade, não sobre o desenho da parede).

- [ ] **Step 5: Commit**

```bash
git add monster_intent.py server.py tools/test_monster_intent.py
git commit -m "feat: previsão da intenção dos monstros (somente leitura)"
```
(somente os hunks próprios em `server.py`, se o arquivo tiver trabalho alheio; ver Global Constraints.)

---

### Task 2: Mensagem `prever_intencoes` (handler, taxa, cache)

**Files:**
- Modify: `server.py` (novo método ao lado de `handle_prever_ataque` ~14220; despacho ao lado de `prever_ataque` ~50007)
- Test: `tools/test_monster_intent.py` (nova seção)

**Interfaces:**
- Consumes: `_prever_intencoes(pid)` (Task 1), `_intent_cache`, `_intent_ultimo`.
- Produces: mensagem ao solicitante `{"type":"intencoes_monstros","rodada":int,"itens":[…]}`; `GameRoom.handle_prever_intencoes(pid)`.

- [ ] **Step 1: Teste que falha** (acrescentar antes do `print(f"\n{PASS} ok…")`)

```python
print("[6] handler: resposta privada, taxa e cache")
import time as _time
r = sala()
a = heroi(r, "a", "Ana", "warrior", [5, 5])
m = monstro(r, "orc", [8, 5])
monta(r)
enviados = []
async def captura(pid, msg, *a_, **k_):
    enviados.append((pid, msg))
r.send_to = captura
asyncio.run(r.handle_prever_intencoes("a"))
check("uma resposta ao solicitante", len(enviados) == 1 and enviados[0][0] == "a")
msg = enviados[0][1] if enviados else {}
check("tipo e rodada", msg.get("type") == "intencoes_monstros" and msg.get("rodada") == 1)
check("itens com o orc", len(msg.get("itens", [])) == 1)
enviados.clear()
asyncio.run(r.handle_prever_intencoes("a"))
check("segundo pedido imediato: limitado pela taxa", enviados == [])
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("depois do intervalo responde de novo", len(enviados) == 1)
chamadas = []
orig = r._prever_intencoes
def conta(pid):
    chamadas.append(pid)
    return orig(pid)
r._prever_intencoes = conta
enviados.clear()
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("mesma configuração: usa o cache (não recalcula)", chamadas == [] and len(enviados) == 1)
m["pos"] = [9, 5]
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("monstro andou: cache invalidado e recalcula", chamadas == ["a"])
enviados.clear()
a["alive"] = False
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("herói morto: sem resposta", enviados == [])
a["alive"] = True
r.phase = "city"
r._intent_ultimo["a"] = _time.monotonic() - 1.0
asyncio.run(r.handle_prever_intencoes("a"))
check("fora de 'playing': sem resposta", enviados == [])
```

- [ ] **Step 2: Rodar e ver falhar** — `AttributeError: … handle_prever_intencoes`.

- [ ] **Step 3: Implementar** em `server.py`, logo depois de `handle_prever_ataque` (verifique se o módulo já importa `time`; se não, `import time` no topo):

```python
    INTENT_INTERVALO_MIN = 0.15   # s entre respostas ao mesmo jogador

    def _intent_assinatura(self):
        """Muda quando algo que altera a previsão muda (posições, vida, vez)."""
        return (
            self.round_num, self.initiative_index,
            tuple(sorted((pid, tuple(p.get("pos") or ()), bool(p.get("alive")))
                         for pid, p in self.players.items())),
            tuple(sorted((mid, tuple(m.get("pos") or ()), m.get("hp", 0),
                          bool(m.get("provocado")), bool(m.get("alertado")),
                          m.get("control_mode"))
                         for mid, m in self.monsters.items())),
            tuple(sorted((a.get("id"), tuple(a.get("pos") or ()))
                         for a in self._all_animados())),
        )

    async def handle_prever_intencoes(self, pid, data=None):
        """Previsão de intenção dos monstros (só leitura). Responde só a quem
        pediu (`intencoes_monstros`). Ver monster_intent.py."""
        p = self.players.get(pid)
        if self.phase != "playing" or not p or not self._ativo(p):
            return
        agora = time.monotonic()
        if agora - self._intent_ultimo.get(pid, 0.0) < self.INTENT_INTERVALO_MIN:
            return
        self._intent_ultimo[pid] = agora
        assinatura = self._intent_assinatura()
        guardado = self._intent_cache.get(pid)
        if guardado and guardado[0] == assinatura:
            itens = guardado[1]
        else:
            itens = self._prever_intencoes(pid)
            self._intent_cache[pid] = (assinatura, itens)
        await self.send_to(pid, {"type": "intencoes_monstros",
                                 "rodada": self.round_num, "itens": itens})
```

Despacho (ao lado de `prever_ataque`, ~50007):

```python
                elif t == "prever_intencoes":
                    if room: await room.handle_prever_intencoes(pid)
```

- [ ] **Step 4: Rodar e ver passar** — `python -X utf8 tools/test_monster_intent.py` → tudo verde; `python -X utf8 tools/test_protocolo_robustez.py` não regride (leva ~6,5 min; rode em segundo plano).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_monster_intent.py
git commit -m "feat: mensagem prever_intencoes com taxa e cache"
```

---

### Task 3: Módulo puro do cliente e camada `GS`

**Files:**
- Create: `src/intencaoMonstros.js`
- Modify: `src/gameState.js` (perto de `previsaoAtaque` ~1380-1402; `case 'previsao_ataque'` ~1918; `case 'game_state'` ~1808; export ~3981); `index.html` (tag `<script>` ao lado de `src/guiaTutorial.js`)
- Test: `tools/test_intencoes_cliente.js`

**Interfaces:**
- Produces `window.IntencaoMonstros`:
  - `MODOS = ['off','grupo','todas']`; `lerModo(raw) -> modo` (inválido → `'grupo'`); `proximoModo(modo) -> modo` (ordem off→grupo→todas→off).
  - `descartar(msg, state) -> bool` (true = velha: `msg.rodada !== state.round`).
  - `selecionar(itens, {modo, destaqueId}) -> [{...item, forte:bool}]`: `off` → só o destaque; `grupo` → itens com `alcanca === true` (+ destaque); `todas` → tudo; o item do `destaqueId` sempre entra com `forte:true`.
  - `contar(selecionados) -> {alvo_id: n}`.
  - `estilo(item) -> {cor, tracejado, opacidade}`: corpo `#e5484d`, distância `#f08a24`, ameaça `#9b5de5`; `firme` → contínuo, opacidade 0.95; `provavel` → tracejado, 0.6.
- Produces em `GS`: `pedirIntencoes()`, `intencoes()` (lista já filtrada por rodada ou `[]`), evento `intencoesMonstros`.

- [ ] **Step 1: Teste que falha** (`tools/test_intencoes_cliente.js`)

```javascript
// Intenção dos monstros (cliente) — roda da raiz: node tools/test_intencoes_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");
let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };
global.window = {};
const IM = eval(fs.readFileSync(path.join(raiz, "src", "intencaoMonstros.js"), "utf8") + "; window.IntencaoMonstros");

const item = (over) => Object.assign({
  monstro_id: "m1", alvo_id: "a", alvo_tipo: "heroi", alvo_pos: [5, 5],
  acao: "corpo", alcanca: true, casa_ataque: [6, 5], certeza: "firme" }, over || {});

console.log("[1] modos");
check("MODOS", JSON.stringify(IM.MODOS) === '["off","grupo","todas"]');
check("lerModo válido", IM.lerModo("todas") === "todas" && IM.lerModo("off") === "off");
check("lerModo inválido/ausente cai em grupo", IM.lerModo("x") === "grupo" && IM.lerModo(null) === "grupo" && IM.lerModo(undefined) === "grupo");
check("proximoModo cicla", IM.proximoModo("off") === "grupo" && IM.proximoModo("grupo") === "todas" && IM.proximoModo("todas") === "off");

console.log("[2] descartar resposta velha");
check("rodada igual: mantém", IM.descartar({ rodada: 3 }, { round: 3 }) === false);
check("rodada diferente: descarta", IM.descartar({ rodada: 2 }, { round: 3 }) === true);
check("sem estado: descarta", IM.descartar({ rodada: 2 }, null) === true);
check("mensagem lixo: descarta", IM.descartar(null, { round: 1 }) === true);

console.log("[3] selecionar");
const itens = [item(), item({ monstro_id: "m2", alcanca: false, casa_ataque: null }),
               item({ monstro_id: "m3", acao: "distancia" })];
check("off: nada", IM.selecionar(itens, { modo: "off" }).length === 0);
check("grupo: só quem alcança", IM.selecionar(itens, { modo: "grupo" }).map(i => i.monstro_id).join() === "m1,m3");
check("todas: todos", IM.selecionar(itens, { modo: "todas" }).length === 3);
let s = IM.selecionar(itens, { modo: "grupo", destaqueId: "m2" });
check("destaque entra mesmo sem alcançar, e é forte",
      s.length === 3 && s.find(i => i.monstro_id === "m2").forte === true);
check("os demais não são fortes", s.filter(i => i.forte).length === 1);
s = IM.selecionar(itens, { modo: "off", destaqueId: "m1" });
check("off ainda mostra o destaque", s.length === 1 && s[0].monstro_id === "m1" && s[0].forte);
check("lixo não quebra", IM.selecionar(null, { modo: "todas" }).length === 0 && IM.selecionar([null, item()], { modo: "todas" }).length === 1);

console.log("[4] contar");
const c = IM.contar(IM.selecionar([item(), item({ monstro_id: "m9" }), item({ monstro_id: "m8", alvo_id: "b" })], { modo: "todas" }));
check("contador por alvo", c.a === 2 && c.b === 1);

console.log("[5] estilo");
check("firme: contínuo e forte", IM.estilo(item()).tracejado === false && IM.estilo(item()).opacidade > 0.9);
check("provável: tracejado e fraco", IM.estilo(item({ certeza: "provavel" })).tracejado === true && IM.estilo(item({ certeza: "provavel" })).opacidade < 0.7);
check("cores por ação", IM.estilo(item()).cor === "#e5484d" && IM.estilo(item({ acao: "distancia" })).cor === "#f08a24" && IM.estilo(item({ acao: "ameaca" })).cor === "#9b5de5");

console.log("[6] fiação do GS");
const gs = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
check("GS: pedirIntencoes envia prever_intencoes", /type:\s*'prever_intencoes'/.test(gs));
check("GS: trata intencoes_monstros", gs.includes("case 'intencoes_monstros'"));
check("GS: exporta pedirIntencoes e intencoes", /pedirIntencoes,/.test(gs) && /\bintencoes,/.test(gs));
const html = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
check("index.html carrega o módulo", html.includes("src/intencaoMonstros.js"));

console.log(`\n${PASS} ok, ${FAIL} falhas`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar e ver falhar** — `node tools/test_intencoes_cliente.js` → `ENOENT … src/intencaoMonstros.js`.

- [ ] **Step 3: Implementar** `src/intencaoMonstros.js`:

```javascript
// Intenção dos monstros — lógica PURA do cliente (sem DOM, canvas ou THREE).
// O servidor prevê (prever_intencoes → intencoes_monstros); aqui só se decide
// o que mostrar. Spec: docs/superpowers/specs/2026-10-12-intencao-dos-monstros-design.md
(function () {
  const MODOS = ['off', 'grupo', 'todas'];
  const CORES = { corpo: '#e5484d', distancia: '#f08a24', ameaca: '#9b5de5' };

  function lerModo(raw) { return MODOS.includes(raw) ? raw : 'grupo'; }
  function proximoModo(modo) { return MODOS[(MODOS.indexOf(modo) + 1) % MODOS.length]; }

  // Resposta velha: a rodada da mensagem não bate com a do estado atual.
  function descartar(msg, state) {
    if (!msg || !state) return true;
    return msg.rodada !== state.round;
  }

  // modo: off | grupo (só quem alcança alguém) | todas. O monstro em destaque
  // (mouse/tooltip) entra sempre e é "forte".
  function selecionar(itens, opts) {
    const { modo, destaqueId } = opts || {};
    if (!Array.isArray(itens)) return [];
    const saida = [];
    for (const it of itens) {
      if (!it || typeof it !== 'object') continue;
      const forte = destaqueId != null && String(it.monstro_id) === String(destaqueId);
      const entra = forte || modo === 'todas' || (modo === 'grupo' && it.alcanca === true);
      if (entra) saida.push(Object.assign({}, it, { forte }));
    }
    return saida;
  }

  function contar(selecionados) {
    const n = {};
    for (const it of selecionados || []) n[it.alvo_id] = (n[it.alvo_id] || 0) + 1;
    return n;
  }

  function estilo(item) {
    const firme = item && item.certeza === 'firme';
    return {
      cor: CORES[item && item.acao] || CORES.corpo,
      tracejado: !firme,
      opacidade: firme ? 0.95 : 0.6,
    };
  }

  window.IntencaoMonstros = { MODOS, lerModo, proximoModo, descartar, selecionar, contar, estilo };
})();
```

Em `index.html`, ache a tag de `src/guiaTutorial.js` e acrescente, imediatamente depois, uma tag irmã igual (mesmo formato de `?v=`) para `src/intencaoMonstros.js`.

Em `src/gameState.js`:

(a) Depois de `_limparPrevisoes` (~linha 1402):

```javascript
  // Intenção dos monstros: o servidor responde a prever_intencoes só a quem
  // pediu. A resposta vale para a rodada em que foi pedida; chegando velha, é
  // descartada (ver IntencaoMonstros.descartar, aplicado no game.js).
  let _intencoes = { rodada: null, itens: [] };
  function intencoes() {
    return (gameState && _intencoes.rodada === gameState.round) ? _intencoes.itens : [];
  }
  function pedirIntencoes() { return send({ type: 'prever_intencoes' }); }
```

(b) No `case 'game_state'`, não limpar (a resposta vale pela rodada; a invalidação por posição é do servidor via novo pedido).

(c) Depois de `case 'previsao_ataque'` (~1924):

```javascript
      case 'intencoes_monstros':
        if (gameState && msg.rodada === gameState.round) {
          _intencoes = { rodada: msg.rodada, itens: Array.isArray(msg.itens) ? msg.itens : [] };
        }
        _emit('intencoesMonstros', _intencoes);
        break;
```

(d) No `case 'enter_dungeon'` (~1796-1799) acrescente `_intencoes = { rodada: null, itens: [] };` antes do `_emit('enterDungeon')`.

(e) No objeto exportado (~3981) acrescente `pedirIntencoes,` e `intencoes,` junto de `pedirPrevisaoAtaque,`.

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_intencoes_cliente.js` → `N ok, 0 falhas`; `node tools/test_guia_tutorial_cliente.js` não regride.

- [ ] **Step 5: Commit**

```bash
git add src/intencaoMonstros.js src/gameState.js index.html tools/test_intencoes_cliente.js
git commit -m "feat: módulo puro e GS para a intenção dos monstros"
```

---

### Task 4: Desenho 2D, pedido automático e tooltip

**Files:**
- Modify: `game.js` (`renderMap` fim ~12425; ao lado de `_linhaPrevisaoAtaque` ~18085; preferência ao lado de `_VISAO_COMP_KEY` ~8180)
- Test: `tools/test_intencoes_cliente.js` (seção de fiação)

**Interfaces:**
- Consumes: `IntencaoMonstros` (Task 3), `GS.pedirIntencoes`, `GS.intencoes`, evento `intencoesMonstros`, `CELL`, `_agendarChamas2D`.
- Produces: `_intencaoModo` (var), `_intencoesPedirAgora()`, `_intencoesDestaqueId()`, `_intencoesVisiveis(state, visionSet)`, `_intencoesDesenhar2D(ctx, state, visionSet)`, `_intencaoLinhaTooltip(monster)`.

- [ ] **Step 1: Teste de fiação que falha** (acrescente em `tools/test_intencoes_cliente.js`, antes do resumo)

```javascript
console.log("[7] fiação do game.js (2D)");
const jogo = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("lê o modo salvo com try/catch", /lfh_intencoes/.test(jogo) && /IntencaoMonstros\.lerModo\(/.test(jogo));
check("desenho 2D chamado no fim do renderMap", /_intencoesDesenhar2D\(ctx, state, visionSet\);/.test(jogo));
check("usa o módulo puro para selecionar", jogo.includes("IntencaoMonstros.selecionar("));
check("descarta resposta velha", jogo.includes("IntencaoMonstros.descartar("));
check("pede no início da vez e depois de mover (com intervalo)", jogo.includes("_intencoesPedirAgora") && /250/.test(jogo));
check("tooltip do monstro ganha a linha de intenção", jogo.includes("_intencaoLinhaTooltip("));
check("Mestre e mesa de teste não pedem", /GS\.isMaster\(\)\s*\|\|[^;]*test_mode/.test(jogo.slice(jogo.indexOf("function _intencoesPedirAgora"))));
```

- [ ] **Step 2: Rodar e ver falhar** — as checagens `[7]` falham.

- [ ] **Step 3: Implementar em `game.js`** (edições com a ferramenta de edição; o código abaixo é o conteúdo a inserir).

(a) Logo depois do bloco da visão compartilhada (após `_setVisaoCompPref`, ~linha 8198):

```javascript
// ── Intenção dos monstros ────────────────────────────────────────────────────
// O servidor prevê (prever_intencoes); aqui só se desenha. Modos: off | grupo
// (padrão: só quem alcança alguém) | todas. Preferência por navegador.
const _INTENCAO_KEY = 'lfh_intencoes';
let _intencaoModo = (() => {
  try { return IntencaoMonstros.lerModo(localStorage.getItem(_INTENCAO_KEY)); }
  catch(e){ return 'grupo'; }
})();
function _setIntencaoModo(modo){
  _intencaoModo = IntencaoMonstros.lerModo(modo);
  try { localStorage.setItem(_INTENCAO_KEY, _intencaoModo); } catch(e){}
  _intencoesPedirAgora(true);
  if(GS.gameState) { if(mode3D && g3) renderMap3D(GS.gameState); else renderMap(GS.gameState); }
}
let _intencaoUltimoPedido = 0;
function _intencoesPodePedir(){
  const st = GS.gameState;
  if(!st || st.phase !== 'playing' || GS.isMaster() || st.test_mode) return false;
  if(_intencaoModo === 'off') return false;
  return !!GS.isMyTurn;
}
function _intencoesPedirAgora(forcar){
  if(!_intencoesPodePedir() && !(forcar && GS.gameState && !GS.isMaster() && !GS.gameState.test_mode && GS.isMyTurn)) return;
  const agora = performance.now();
  if(!forcar && agora - _intencaoUltimoPedido < 250) return;
  _intencaoUltimoPedido = agora;
  GS.pedirIntencoes();
}
// Monstro cujo tooltip está aberto (o #tip-previsao existe enquanto ele estiver).
function _intencoesDestaqueId(){
  const el = document.getElementById('tip-previsao');
  return (el && el.isConnected && _tipPrevisaoAlvo) ? _tipPrevisaoAlvo.id : null;
}
function _intencoesVisiveis(state, visionSet){
  if(!state || _intencaoModo === 'off' && _intencoesDestaqueId() == null) return [];
  const bruto = GS.intencoes ? GS.intencoes() : [];
  const sel = IntencaoMonstros.selecionar(bruto, { modo: _intencaoModo, destaqueId: _intencoesDestaqueId() });
  const pode = (x, y) => !visionSet || visionSet.has(`${x},${y}`);
  const mons = new Map((state.monsters || []).map(m => [String(m.id), m]));
  return sel.filter(it => {
    const m = mons.get(String(it.monstro_id));
    return m && m.hp > 0 && pode(m.pos[0], m.pos[1]);
  });
}
function _intencoesDesenhar2D(ctx, state, visionSet){
  const itens = _intencoesVisiveis(state, visionSet);
  if(!itens.length) return;
  const mons = new Map((state.monsters || []).map(m => [String(m.id), m]));
  const contagem = IntencaoMonstros.contar(itens);
  const vistoAlvo = {};
  ctx.save();
  for(const it of itens){
    const m = mons.get(String(it.monstro_id));
    if(!m) continue;
    const est = IntencaoMonstros.estilo(it);
    const x0 = m.pos[0] * CELL + CELL / 2, y0 = m.pos[1] * CELL + CELL / 2;
    const x1 = it.alvo_pos[0] * CELL + CELL / 2, y1 = it.alvo_pos[1] * CELL + CELL / 2;
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2 - Math.min(CELL * 0.6, Math.hypot(x1 - x0, y1 - y0) * 0.18);
    ctx.globalAlpha = it.forte ? 1 : est.opacidade;
    ctx.strokeStyle = est.cor; ctx.fillStyle = est.cor;
    ctx.lineWidth = it.forte ? 4 : 2;
    ctx.setLineDash(est.tracejado ? [CELL * 0.14, CELL * 0.12] : []);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(mx, my, x1, y1); ctx.stroke();
    ctx.setLineDash([]);
    const ang = Math.atan2(y1 - my, x1 - mx), ponta = CELL * (it.forte ? 0.3 : 0.22);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x1 - ponta * Math.cos(ang - 0.45), y1 - ponta * Math.sin(ang - 0.45));
    ctx.lineTo(x1 - ponta * Math.cos(ang + 0.45), y1 - ponta * Math.sin(ang + 0.45));
    ctx.closePath(); ctx.fill();
    if(it.alcanca && it.casa_ataque){
      const cx = it.casa_ataque[0] * CELL + CELL / 2, cy = it.casa_ataque[1] * CELL + CELL / 2;
      ctx.globalAlpha = 0.55 * (it.forte ? 1 : est.opacidade);
      ctx.strokeRect(cx - CELL * 0.3, cy - CELL * 0.3, CELL * 0.6, CELL * 0.6);
    }
    vistoAlvo[it.alvo_id] = true;
  }
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.round(CELL * 0.34)}px sans-serif`; ctx.textAlign = 'center';
  for(const id of Object.keys(vistoAlvo)){
    if(contagem[id] < 2) continue;
    const it = itens.find(i => String(i.alvo_id) === id);
    ctx.fillText('×' + contagem[id], it.alvo_pos[0] * CELL + CELL * 0.85, it.alvo_pos[1] * CELL + CELL * 0.25);
  }
  ctx.restore();
  _agendarChamas2D();   // mantém o redesenho leve (~12 quadros/s) enquanto houver setas
}
function _intencaoLinhaTooltip(monster){
  const it = (GS.intencoes ? GS.intencoes() : []).find(i => String(i.monstro_id) === String(monster?.id));
  if(!it) return '';
  const alvo = (GS.gameState?.players || []).find(p => p.id === it.alvo_id);
  const nome = alvo ? alvo.name : t('ui.intencao.um_aliado');
  const chave = it.acao === 'distancia' ? 'ui.intencao.tooltip.distancia'
              : it.acao === 'ameaca' ? 'ui.intencao.tooltip.ameaca' : 'ui.intencao.tooltip.corpo';
  const cert = it.certeza === 'firme' ? '' : ` <span style="color:#c8b89a">(${t('ui.intencao.provavel')})</span>`;
  return `<div style="margin-top:4px;font-size:11px;color:${IntencaoMonstros.estilo(it).cor}">${t(chave, {alvo: nome})}${cert}</div>`;
}
GS.on('intencoesMonstros', () => {
  const st = GS.gameState;
  if(st) { if(mode3D && g3) renderMap3D(st); else renderMap(st); }
});
// Pede no início da vez e depois de cada mudança de estado na minha vez
// (movimento, ataque), agrupando em 250 ms.
GS.on('gameState', st => { if(st && st.phase === 'playing') _intencoesPedirAgora(); });
```

(Com o modo `off` o cliente não pede previsão, então `GS.intencoes()` fica vazio e a linha do tooltip some sozinha. É o comportamento desejado: "Desligada" desliga tudo.)

Observação: `_intencoesVisiveis` mantém o destaque do tooltip mesmo em `off` caso ainda haja dados de antes; isso é inofensivo, porque sem novos pedidos a lista fica velha e é descartada pela rodada.

(b) No fim de `renderMap`, depois de `_guiaDesenhar2D(ctx, state, visionSet);` (~12425), acrescente a linha: `  _intencoesDesenhar2D(ctx, state, visionSet);`.

(c) Em `_linhaPrevisaoAtaque` (~18085), troque o `return` final por:

```javascript
  return `<div id="tip-previsao" style="margin-top:5px;padding-top:4px;border-top:1px solid #c8a95155;font-size:11px;">${_htmlPrevisaoAtaque(prev)}</div>` + _intencaoLinhaTooltip(monster);
```

(d) Em qualquer ponto de `game.js` que já descarte resposta velha, use: ao receber `intencoesMonstros` o `GS` já compara a rodada (Task 3). Para a checagem textual do teste `[7]`, acrescente no handler `GS.on('intencoesMonstros', …)` uma primeira linha: `if(IntencaoMonstros.descartar({rodada: GS.gameState?.round}, GS.gameState)) return;` — evita redesenhar quando não há estado.

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_intencoes_cliente.js`; `node --check game.js`; abra uma partida local (ver Task 7) para a primeira conferência visual.

- [ ] **Step 5: Commit**

```bash
git add game.js tools/test_intencoes_cliente.js
git commit -m "feat: setas de intenção dos monstros no 2D e linha no tooltip"
```
(só os hunks próprios em `game.js`; ver Global Constraints.)

---

### Task 5: Desenho 3D

**Files:**
- Modify: `game.js` (nova seção ao lado de `_guiaMarca3D` ~56205; chamada no laço 3D ~46416; limpeza no `dispose3D`)
- Test: `tools/test_intencoes_cliente.js` (fiação) + conferência visual

**Interfaces:**
- Consumes: `_intencoesVisiveis` (Task 4), `g3`, `getMonsterMesh(id)`, `topoSuperficie3D(st,x,y)`, `g3.T` (THREE).
- Produces: `_intencoesAtualizar3D()`, `g3.intencoesPool`.

- [ ] **Step 1: Teste de fiação que falha** (acrescente)

```javascript
console.log("[8] fiação do game.js (3D)");
check("3D: função de atualização chamada junto do guia", /_guiaAtualizar3D\(\);[\s\S]{0,200}_intencoesAtualizar3D\(\)|_intencoesAtualizar3D\(\);[\s\S]{0,200}_guiaAtualizar3D\(\)/.test(jogo));
check("3D: pool reutilizável (sem criar malha por quadro)", jogo.includes("g3.intencoesPool"));
check("3D: dispose limpa o pool", /intencoesPool[\s\S]{0,400}dispose/.test(jogo));
```

- [ ] **Step 2: Rodar e ver falhar** — `[8]` falha.

- [ ] **Step 3: Implementar.** Junto de `_guiaMarca3D` (~56205) insira:

```javascript
// ── Intenção dos monstros no 3D ──────────────────────────────────────────────
// Pool fixo de setas (linha curva + cone). Nunca cria nem destrói malhas por
// quadro: só reposiciona e mostra/esconde. Mesmo orçamento do halo do tutorial.
const INTENCOES_POOL_MAX = 16;
function _intencoesPool3D(){
  if(g3.intencoesPool) return g3.intencoesPool;
  const T = g3.T;
  const slots = [];
  const grupo = new T.Group();
  for(let i = 0; i < INTENCOES_POOL_MAX; i++){
    const mat = new T.LineBasicMaterial({ color: 0xe5484d, transparent: true, opacity: .9, depthTest: false, depthWrite: false, toneMapped: false });
    const geo = new T.BufferGeometry().setFromPoints(Array.from({length: 14}, () => new T.Vector3()));
    const linha = new T.Line(geo, mat); linha.renderOrder = 82; linha.raycast = () => {}; linha.frustumCulled = false;
    const cone = new T.Mesh(new T.ConeGeometry(0.14, 0.34, 10),
      new T.MeshBasicMaterial({ color: 0xe5484d, transparent: true, opacity: .95, depthTest: false, depthWrite: false, toneMapped: false }));
    cone.renderOrder = 83; cone.raycast = () => {};
    const casa = new T.Mesh(new T.RingGeometry(0.2, 0.28, 4),
      new T.MeshBasicMaterial({ color: 0xe5484d, transparent: true, opacity: .6, side: T.DoubleSide, depthTest: false, depthWrite: false, toneMapped: false }));
    casa.rotation.x = -Math.PI / 2; casa.renderOrder = 81; casa.raycast = () => {};
    linha.visible = cone.visible = casa.visible = false;
    grupo.add(linha); grupo.add(cone); grupo.add(casa);
    slots.push({ linha, cone, casa });
  }
  g3.scene.add(grupo);
  g3.intencoesPool = { grupo, slots };
  return g3.intencoesPool;
}
function _intencoesEsconder3D(){
  if(!g3 || !g3.intencoesPool) return;
  for(const s of g3.intencoesPool.slots) s.linha.visible = s.cone.visible = s.casa.visible = false;
}
function _intencoesDispose3D(){
  if(!g3 || !g3.intencoesPool) return;
  const { grupo, slots } = g3.intencoesPool;
  for(const s of slots){
    s.linha.geometry.dispose(); s.linha.material.dispose();
    s.cone.geometry.dispose(); s.cone.material.dispose();
    s.casa.geometry.dispose(); s.casa.material.dispose();
  }
  g3.scene.remove(grupo);
  g3.intencoesPool = null;
}
function _intencoesAtualizar3D(){
  if(!g3) return;
  const st = GS.gameState;
  const vis = st && _guiaVisao3D(st);
  const itens = st ? _intencoesVisiveis(st, vis).slice(0, INTENCOES_POOL_MAX) : [];
  if(!itens.length){ _intencoesEsconder3D(); return; }
  const pool = _intencoesPool3D();
  const T = g3.T;
  const mons = new Map((st.monsters || []).map(m => [String(m.id), m]));
  itens.forEach((it, i) => {
    const s = pool.slots[i];
    const m = mons.get(String(it.monstro_id));
    if(!m) { s.linha.visible = s.cone.visible = s.casa.visible = false; return; }
    const est = IntencaoMonstros.estilo(it);
    const cor = new T.Color(est.cor);
    const mesh = getMonsterMesh(m.id);
    const x0 = mesh ? mesh.position.x : m.pos[0], z0 = mesh ? mesh.position.z : m.pos[1];
    const y0 = topoSuperficie3D(st, m.pos[0], m.pos[1]) + 0.9;
    const x1 = it.alvo_pos[0], z1 = it.alvo_pos[1];
    const y1 = topoSuperficie3D(st, x1, z1) + 0.9;
    const alt = 0.5 + Math.hypot(x1 - x0, z1 - z0) * 0.12;
    const pos = s.linha.geometry.attributes.position;
    for(let k = 0; k < 14; k++){
      const u = k / 13;
      pos.setXYZ(k, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + Math.sin(Math.PI * u) * alt, z0 + (z1 - z0) * u);
    }
    pos.needsUpdate = true;
    s.linha.material.color.copy(cor);
    s.linha.material.opacity = it.forte ? 1 : est.opacidade;
    s.linha.visible = true;
    const fim = new T.Vector3(pos.getX(13), pos.getY(13), pos.getZ(13));
    const ant = new T.Vector3(pos.getX(12), pos.getY(12), pos.getZ(12));
    s.cone.position.copy(fim);
    s.cone.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), fim.clone().sub(ant).normalize());
    s.cone.scale.setScalar(it.forte ? 1.35 : 1);
    s.cone.material.color.copy(cor);
    s.cone.visible = true;
    if(it.alcanca && it.casa_ataque){
      s.casa.position.set(it.casa_ataque[0], topoSuperficie3D(st, it.casa_ataque[0], it.casa_ataque[1]) + 0.06, it.casa_ataque[1]);
      s.casa.material.color.copy(cor);
      s.casa.visible = true;
    } else s.casa.visible = false;
  });
  for(let i = itens.length; i < pool.slots.length; i++){
    const s = pool.slots[i]; s.linha.visible = s.cone.visible = s.casa.visible = false;
  }
}
```

Na linha ~46416 (`_guiaAtualizar3D();` dentro do laço do `startLoop3D`) acrescente `_intencoesAtualizar3D();` logo em seguida. No `dispose3D` (procure `function dispose3D`), acrescente `_intencoesDispose3D();` antes de zerar `g3`.

- [ ] **Step 4: Rodar e ver passar** — `node tools/test_intencoes_cliente.js`; `node --check game.js`.

- [ ] **Step 5: Commit**

```bash
git add game.js tools/test_intencoes_cliente.js
git commit -m "feat: setas de intenção dos monstros no 3D (pool reutilizável)"
```

---

### Task 6: Preferência (⚙️), atalho T e textos PT/EN

**Files:**
- Modify: `game.js` (HTML do painel ~34128; `onchange` ~34216; teclado ~29759), `src/lang/interface.js`
- Test: `tools/test_intencoes_cliente.js`, `tools/test_interface.py`, `tools/dividas.py`

**Interfaces:**
- Consumes: `_intencaoModo`, `_setIntencaoModo` (Task 4), `IntencaoMonstros.proximoModo`.
- Produces: seletor `#cfg-intencao-sel` no painel; tecla **T** alterna o modo; chaves `ui.intencao.*` e `ui.menu.intencao*`.

- [ ] **Step 1: Verificar colisão da tecla T** e testes que falham

Run: `grep -n "'t'\|'T'\|\"t\"\|\"T\"\|KeyT" game.js` e confira que nenhum handler de `keydown` global usa `T` fora de campos de texto. Se houver colisão, escolha outra tecla e ajuste esta tarefa e o spec.

Acrescente em `tools/test_intencoes_cliente.js`:

```javascript
console.log("[9] preferência e atalho");
check("seletor no painel ⚙️", jogo.includes('id="cfg-intencao-sel"'));
check("seletor grava via _setIntencaoModo", /cfg-intencao-sel['"]\)\.onchange[\s\S]{0,120}_setIntencaoModo\(/.test(jogo));
check("atalho T alterna e ignora campos de texto",
      /e\.key === 't' \|\| e\.key === 'T'[\s\S]{0,260}proximoModo/.test(jogo)
      && /INPUT|TEXTAREA|isContentEditable/.test(jogo.slice(jogo.indexOf("e.key === 't' || e.key === 'T'") - 400, jogo.indexOf("e.key === 't' || e.key === 'T'") + 400)));
const lang = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8");
for (const k of ["ui.menu.intencao", "ui.menu.intencao.off", "ui.menu.intencao.grupo", "ui.menu.intencao.todas",
                 "ui.intencao.tooltip.corpo", "ui.intencao.tooltip.distancia", "ui.intencao.tooltip.ameaca",
                 "ui.intencao.provavel", "ui.intencao.um_aliado", "ui.intencao.modo_toast"]) {
  check("chave " + k + " com pt e en", new RegExp('"' + k.replace(/\./g, "\\.") + '":\\s*\\{[^}]*"pt"[^}]*"en"').test(lang.replace(/\n/g, " ")));
}
```

- [ ] **Step 2: Rodar e ver falhar** — `[9]` falha.

- [ ] **Step 3: Implementar.**

(a) Em `src/lang/interface.js`, acrescente (mesmo formato das chaves vizinhas, ex. `ui.menu.visao_compartilhada`):

```javascript
  "ui.menu.intencao": { pt: "Intenção dos monstros", en: "Monster intent" },
  "ui.menu.intencao.off": { pt: "Desligada", en: "Off" },
  "ui.menu.intencao.grupo": { pt: "Ameaças ao meu grupo", en: "Threats to my party" },
  "ui.menu.intencao.todas": { pt: "Todas", en: "All" },
  "ui.menu.intencao_dica": { pt: "Mostra setas de quem cada monstro atacaria agora. Tecla T alterna.", en: "Shows arrows for who each monster would attack right now. Press T to cycle." },
  "ui.intencao.tooltip.corpo": { pt: "⚔️ Vai atacar {alvo}", en: "⚔️ Will attack {alvo}" },
  "ui.intencao.tooltip.distancia": { pt: "🏹 Vai atirar em {alvo}", en: "🏹 Will shoot {alvo}" },
  "ui.intencao.tooltip.ameaca": { pt: "✨ Ameaça {alvo}", en: "✨ Threatens {alvo}" },
  "ui.intencao.provavel": { pt: "provável", en: "likely" },
  "ui.intencao.um_aliado": { pt: "um aliado", en: "an ally" },
  "ui.intencao.modo_toast": { pt: "Intenção dos monstros: {modo}", en: "Monster intent: {modo}" },
```

Acrescente também uma linha em "Como jogar" (procure as chaves `ui.ajuda.*` vizinhas): `"ui.ajuda.intencao": { pt: "Setas vermelhas mostram quem um monstro atacaria agora (tracejada = provável). Tecla T alterna: desligada, ameaças ao grupo, todas.", en: "Red arrows show who a monster would attack right now (dashed = likely). Press T to cycle: off, threats to my party, all." }` e exiba-a no mesmo ponto onde as demais `ui.ajuda.*` são montadas.

(b) No HTML do painel ⚙️ (~34128), depois da linha da visão compartilhada, acrescente:

```javascript
    +     '<label class="cfg-access-check"><span data-i18n="ui.menu.intencao">Intenção dos monstros</span> <select id="cfg-intencao-sel">'
    +       '<option value="off" data-i18n="ui.menu.intencao.off">Desligada</option>'
    +       '<option value="grupo" data-i18n="ui.menu.intencao.grupo">Ameaças ao meu grupo</option>'
    +       '<option value="todas" data-i18n="ui.menu.intencao.todas">Todas</option></select></label>'
    +     '<small data-i18n="ui.menu.intencao_dica" style="display:block;margin:2px 0 6px;opacity:.7;font-size:.7rem;">Mostra setas de quem cada monstro atacaria agora. Tecla T alterna.</small>'
```

e depois do `onchange` da visão compartilhada (~34219):

```javascript
  wrap.querySelector('#cfg-intencao-sel').value = _intencaoModo;
  wrap.querySelector('#cfg-intencao-sel').onchange = (e) => { _setIntencaoModo(e.target.value); };
```

Como o painel é montado uma vez e o modo pode mudar pela tecla T, em `_setIntencaoModo` acrescente: `const sel = document.getElementById('cfg-intencao-sel'); if(sel) sel.value = _intencaoModo;`.

(c) Atalho: no `keydown` global, logo depois do bloco do `R` (~29759-29762), antes do `if(!GS.isMyTurn …) return`:

```javascript
  if((e.key === 't' || e.key === 'T') && !e.ctrlKey && !e.metaKey && !e.altKey
     && GS.gameState && GS.gameState.phase === 'playing' && !GS.isMaster()){
    const alvo = e.target;
    if(alvo && (alvo.tagName === 'INPUT' || alvo.tagName === 'TEXTAREA' || alvo.isContentEditable)) return;
    _setIntencaoModo(IntencaoMonstros.proximoModo(_intencaoModo));
    toast(t('ui.intencao.modo_toast', {modo: t('ui.menu.intencao.' + _intencaoModo)}), 'var(--text2)');
    e.preventDefault(); return;
  }
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_intencoes_cliente.js`, `python -X utf8 tools/test_interface.py`, `python -X utf8 tools/dividas.py`, `node tools/test_idioma_cliente.js` — todos verdes. Se o placar acusar literal em português no HTML do painel, falta `data-i18n` em algum nó.

- [ ] **Step 5: Commit**

```bash
git add game.js src/lang/interface.js tools/test_intencoes_cliente.js
git commit -m "feat: preferência, atalho T e textos PT/EN da intenção dos monstros"
```

---

### Task 7: Prova no navegador, documentação e verificação final

**Files:**
- Modify: `CLAUDE.md` (nova seção curta)
- Test: sem arquivo novo (prova manual registrada)

- [ ] **Step 1: Subir uma cópia isolada** (não toque `savegames/`, `accounts/` etc. reais)

```bash
set LFH_PORT=8791
python server.py
```
(copie o diretório de dados para `%TEMP%` como nas provas anteriores e aponte as variáveis de dados para a cópia; nunca pare o servidor da 8765.) Abra a mesa de teste do editor ("🧪 Testar como Mestre") ou uma partida solo no Campo de Treinamento com monstros hostis.

- [ ] **Step 2: Conferir no navegador (janela oculta mata o rAF: use o polyfill + `renderer.render()` + `toDataURL`)**

1. Modo `grupo` (padrão): na vez do herói, aparecem setas dos monstros que alcançam alguém; nenhum monstro sem alcance.
2. Passar o mouse num monstro: seta grossa, linha "⚔️ Vai atacar X" no tooltip, mesmo que não alcance.
3. Tecla **T**: alterna off → grupo → todas, com toast; o seletor do ⚙️ acompanha.
4. Mover o herói: setas atualizam em até ~0,5 s (pedido novo); servidor responde só ao dono (conferir em `read_network_requests`/console).
5. 2D e 3D mostram o mesmo; sem erro no console; monstro escondido nunca aparece.
6. Medir: com 8+ monstros o FPS não cai de forma perceptível (medidor de FPS do ⚙️).

Registre os achados; corrija o que o teste automático não pegou (cor, espessura, altura da curva) medindo, não no olho.

- [ ] **Step 3: Documentar** em `CLAUDE.md` (ferramenta de edição, CRLF), no fim da seção de "Server → Client" ou logo depois de "Perseguição dos monstros", um parágrafo curto: o que é, `prever_intencoes`/`intencoes_monstros`, onde mora o código (`monster_intent.py`, `src/intencaoMonstros.js`), a regra "só leitura, restaura o foco da IA em `finally`", os modos e a tecla T, a evolução B, e os testes `tools/test_monster_intent.py` e `tools/test_intencoes_cliente.js`.

- [ ] **Step 4: Bateria final**

```bash
python -X utf8 tools/test_monster_intent.py
node tools/test_intencoes_cliente.js
python -X utf8 tools/test_salvar_masmorra.py
python -X utf8 tools/test_perseguicao.py
python -X utf8 tools/test_modo_mestre.py
python -X utf8 tools/test_interface.py
python -X utf8 tools/dividas.py
node tools/test_idioma_cliente.js
```
Todos verdes (o intermitente `test_monster_hostility` do orc aleatório não conta como regressão).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documenta a intenção dos monstros"
```
(só o hunk próprio; o `CLAUDE.md` pode ter trabalho alheio. Sem push sem pedido.)

---

## Self-Review

- **Cobertura do spec:** §1 → Task 1; §2 → Tasks 2–3; §3 → Tasks 4–6; §4 → Task 1 (exclusões, exceção→`[]`, "ameaça", "firme") e Task 4 (Zero setas = nada); §5 → testes nas Tasks 1–6 e prova na Task 7.
- **Desvios deliberados do spec (a registrar no spec ao final):** `alvo_tipo` só `heroi|animado` (a IA escolhe o prisioneiro em outro caminho, `_processar_prisioneiro_turno`); setas monstro→monstro por hostilidade ficam **fora da v1** (a hostilidade roda antes da IA em `_monster_try_hostility_turn`); `alvo_pos` foi acrescentado ao item para o cliente desenhar sem procurar o alvo.
- **Consistência de nomes:** `_prever_intencoes`, `handle_prever_intencoes`, `_intent_cache`/`_intent_ultimo`, `IntencaoMonstros.{lerModo,proximoModo,descartar,selecionar,contar,estilo}`, `GS.pedirIntencoes/intencoes`, `_intencaoModo`, `_setIntencaoModo`, `_intencoesVisiveis`, `_intencoesDesenhar2D`, `_intencoesAtualizar3D` — iguais em todas as tarefas.
- **Risco aberto:** a seção [3] do teste do servidor depende de o desenho das paredes realmente tirar o monstro da visão; se a regra de visão (`_get_raio_visao`) deixar o orc visível, ajuste a geometria do teste, não a regra.
