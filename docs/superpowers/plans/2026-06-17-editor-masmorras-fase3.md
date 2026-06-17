# Editor de Masmorras — Fase 3 (Objetivos/Prisioneiro/Saída) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar vida em jogo (só em masmorras autoradas) à saída, ao prisioneiro e aos objetivos que a Fase 1 guarda inertes — concluir a masmorra pelo objetivo principal, com bônus dos secundários.

**Architecture:** Toda a lógica de objetivo fica num `_check_objectives()` chamado uma vez no início de `push_state` (catch-all: roda após qualquer ação). O prisioneiro é um dict leve `self.prisoner` instanciado no carregador autorado, com follow-AI e dano de monstros adjacentes processados em `gm_phase`. Cliente ganha HUD de objetivos, casa de saída, peão do prisioneiro e botão "Libertar". Procedural fica intacto (tudo protegido por `self.objectives`).

**Tech Stack:** Python (`server.py`, autoritativo) + Vanilla JS (`src/gameState.js` lógica, `game.js` render). Testes = scripts `tools/test_*.py` com `check()` (NÃO pytest), stub de rede.

**Spec:** `docs/superpowers/specs/2026-06-17-editor-masmorras-fase3-design.md`

---

## Notas de design (ler antes de começar)

- **Convenção de teste:** ver `tools/test_persistencia_masmorra.py`. `sys.path.insert` da raiz, `import server`, `GameRoom("TEST")`, stub de `gm_say/broadcast/push_state/send_to/broadcast_city_state` com `noop`, helper `check()`, `sys.exit(1 if FAIL else 0)`, `sys.stdout.reconfigure(encoding="utf-8")` no topo. Rodar com `PYTHONIOENCODING=utf-8` no Windows.
- **Aplica-se só ao autorado:** toda a lógica nova roda só quando `self.objectives` (setado só no carregador autorado). Procedural: `self.objectives=None` → `_check_objectives` retorna cedo.
- **Hook único:** `push_state` chama `await self._check_objectives()` no início. `_check_objectives` recomputa `self.objective_status` (p/ o HUD) e, se o principal está `done` e ainda não concluído, concede bônus dos secundários e chama `end_game(victory=True)`. Guardas: `self.objectives`, `self.phase=="playing"`, flag `self._objetivo_concluido` (evita repetir).
- **Campos do jogador:** XP em `p["xp"]`, ouro em `p["gold"]`; subir de nível via `await self._check_level_up(p)` (já existe).
- **Marcadores da Fase 1:** monstros autorados têm `m["authored_target"]`/`m["authored_boss"]` (Fase 1). `kill_target` usa `authored_target`. `m["boss"]` é forçado `False` no autorado (não dispara o end_game procedural).
- **Coordenadas:** `(x,y)` → `tiles[y][x]`. WALL=0/FLOOR=1/DOOR=2. Adjacência = Chebyshev ≤1.
- **Commits:** cada task termina com `git add <arquivos exatos>` (nunca `git add -A`).

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | `__init__` (defaults), `load_authored_dungeon` (instanciar exit/prisoner/objectives + key chest), `_objetivo_cumprido`/`_check_objectives`/`_conceder_bonus_secundario`, `handle_open_chest` (flag key chest), `gm_phase` (prisioneiro: follow + dano), `handle_libertar_prisioneiro` + dispatch, `push_state` (hook + campos) |
| `dungeons/test_fase3.json` | Criar | Fixture: saída + prisioneiro + baú-chave + monstro alvo |
| `tools/test_objetivos.py` | Criar | Testes headless dos objetivos + prisioneiro |
| `src/gameState.js` | Modificar | getters `objectives`/`exitPos`/`prisoner`; sender `libertarPrisioneiro`; decisor `prisioneiroLibertavel` |
| `game.js` | Modificar | HUD de objetivos, casa de saída, peão do prisioneiro, botão "Libertar" |

---

## Task 1: Fixture + instanciar exit/prisoner/objectives no carregador

**Files:**
- Create: `dungeons/test_fase3.json`
- Modify: `server.py` (`GameRoom.__init__`; `load_authored_dungeon`)
- Create: `tools/test_objetivos.py`

- [ ] **Step 1: Criar a fixture `dungeons/test_fase3.json`**

Grid 16×12, duas salas (entrada à esquerda; sala trancada à direita) + corredor com porta. Saída no canto direito; prisioneiro na sala trancada; baú-chave; um monstro `target`.

```json
{
  "schema_version": 1,
  "id": "test_fase3",
  "name": "Teste Fase 3 — Objetivos",
  "grid": { "w": 16, "h": 12 },
  "tiles": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,1,1,1,1,1,2,1,1,2,1,1,1,1,1,0],
    [0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
  ],
  "rooms": [
    { "id": 0, "x": 1, "y": 1, "w": 5, "h": 4, "role": "entrance", "locked": false, "doors": [[6,3]] },
    { "id": 1, "x": 10, "y": 1, "w": 5, "h": 4, "role": "monster", "locked": true, "doors": [[9,3]] }
  ],
  "entrance": { "x": 3, "y": 2 },
  "exit": { "x": 14, "y": 4 },
  "monsters": [
    { "type": "goblin", "pos": [12,2], "room_id": 1, "boss": false, "target": true },
    { "type": "skeleton", "pos": [13,3], "room_id": 1, "boss": false, "target": false }
  ],
  "chests": [
    { "pos": [11,4], "gold": 20, "items": [ {"id":"health_potion"} ], "key_objective": true }
  ],
  "traps": [],
  "prisoner": { "pos": [14,1], "room_id": 1 },
  "objectives": {
    "primary": { "type": "rescue_prisoner" },
    "secondary": [ { "type": "kill_all" }, { "type": "open_key_chest" } ]
  }
}
```

Conferir que valida: `python -c "import server,json; print(server.validar_dungeon(json.load(open('dungeons/test_fase3.json',encoding='utf-8'))))"` → `(True, 'ok')`. Se acusar erro, ajuste a casa indicada mantendo a intenção.

- [ ] **Step 2: Escrever o teste que falha**

Criar `tools/test_objetivos.py`:

```python
"""Testes da Fase 3: objetivos, prisioneiro e saída (só masmorra autorada).
Roda da raiz: python tools/test_objetivos.py"""
import asyncio, sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def fixture():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_fase3.json"), encoding="utf-8") as f:
        return json.load(f)

def setup_authored(defn=None):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    for pid, nome, cls in (("p1", "Victor", "warrior"), ("p2", "Pedro", "mage")):
        r.players[pid] = make_player(pid, nome, cls, 0)
    r.player_order = list(r.players.keys())
    r.host_pid = "p1"
    r.mode = "authored"; r.dungeon_def = defn or fixture()
    r.phase = "city"
    return r

async def test_instanciar():
    print("\n[1] carregador instancia exit/prisoner/objectives")
    r = setup_authored()
    await r.enter_dungeon("p1")
    check("exit_pos do arquivo", r.exit_pos == [14, 4])
    check("objectives carregados", r.objectives and r.objectives["primary"]["type"] == "rescue_prisoner")
    check("prisioneiro instanciado (cativo, vivo)",
          r.prisoner and r.prisoner["pos"] == [14, 1]
          and r.prisoner["freed"] is False and r.prisoner["alive"] is True)
    check("baú-chave marcado",
          any(c.get("key_objective") for c in r.chests.values()))
    check("rescue_failed começa False", r.rescue_failed is False)

async def main():
    await test_instanciar()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL no `[1]` — `AttributeError: 'GameRoom' object has no attribute 'exit_pos'`.

- [ ] **Step 4: Adicionar defaults no `__init__`**

Em `server.py`, no `GameRoom.__init__`, logo após a linha `self.dungeon_def = None` (a que já existe, ~`server.py:2874`), inserir:

```python
        # Fase 3 — objetivos/prisioneiro/saída (só em masmorra autorada).
        self.exit_pos = None
        self.objectives = None
        self.objective_status = None
        self.prisoner = None
        self.rescue_failed = False
        self._objetivo_concluido = False
```

- [ ] **Step 5: Instanciar no `load_authored_dungeon`**

Em `server.py`, no fim de `load_authored_dungeon` (após `self.stairs_pos = [ent["x"], ent["y"]]`, ~`server.py:3408`), inserir:

```python
        # Fase 3: instancia o que estava inerte.
        ex = defn.get("exit")
        self.exit_pos = [ex["x"], ex["y"]] if ex else None
        self.objectives = deepcopy(defn.get("objectives") or {"primary": {"type": "kill_all"}, "secondary": []})
        self.objective_status = None
        self.rescue_failed = False
        self._objetivo_concluido = False
        pr = defn.get("prisoner")
        self.prisoner = ({"pos": [pr["pos"][0], pr["pos"][1]], "room_id": pr.get("room_id"),
                          "hp": PRIS_HP, "max_hp": PRIS_HP, "freed": False, "alive": True}
                         if pr else None)
        # Marca o baú-chave por posição (o dict de baú vivo não carrega a flag).
        keyposes = {tuple(c["pos"]) for c in defn.get("chests", []) if c.get("key_objective")}
        for ch in self.chests.values():
            ch["key_objective"] = tuple(ch["pos"]) in keyposes
```

E no TOPO do arquivo, junto às outras constantes de jogo (perto de `MAP_W`/`MAP_H`, ~`server.py:30`), adicionar:

```python
PRIS_HP = 12   # vida do prisioneiro (Fase 3)
```

- [ ] **Step 6: Resetar no bloco `nova` de `enter_dungeon`**

Em `server.py`, no `enter_dungeon`, dentro do `if nova:` onde já se zera `self.corpses={}` etc. (~`server.py:3132`), os atributos da Fase 3 são reescritos por `load_authored_dungeon` no autorado; no procedural eles devem voltar a neutro. Logo após a linha `self.magic_reveal = {}` nesse bloco, inserir:

```python
            self.exit_pos = None; self.objectives = None; self.objective_status = None
            self.prisoner = None; self.rescue_failed = False; self._objetivo_concluido = False
```

(No autorado, `load_authored_dungeon` roda depois e sobrescreve; no procedural, ficam neutros.)

- [ ] **Step 7: Rodar e ver passar**

Run: `python tools/test_objetivos.py`
Expected: PASS — `=== 5 passou, 0 falhou ===`.

- [ ] **Step 8: Regressão**

Run: `python tools/test_persistencia_masmorra.py` → `0 falhou`. `python tools/test_dungeon_loader.py` → `0 falhou`. `python -c "import server"`.

- [ ] **Step 9: Commit**

```bash
git add server.py dungeons/test_fase3.json tools/test_objetivos.py
git commit -m "feat: instancia exit/prisoner/objectives no carregador autorado (Fase 3)"
```

---

## Task 2: Avaliação de objetivos + conclusão (kill/reach/chest)

**Files:**
- Modify: `server.py` (`_objetivo_cumprido`, `_check_objectives`; hook em `push_state`; flag em `handle_open_chest`)
- Test: `tools/test_objetivos.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tools/test_objetivos.py` (e chamar em `main()`):

```python
async def test_conclusao_simples():
    print("\n[2] conclusão por objetivo dispara end_game(victory)")

    async def cenario(primary_type, prep):
        r = setup_authored()
        d = r.dungeon_def
        d["objectives"] = {"primary": {"type": primary_type}, "secondary": []}
        await r.enter_dungeon("p1")
        vit = {"chamado": False, "victory": None}
        async def fake_end(victory): vit["chamado"] = True; vit["victory"] = victory
        r.end_game = fake_end
        await prep(r)
        await r._check_objectives()
        return r, vit

    # kill_all: mata todos
    async def mata_todos(r):
        for m in r.monsters.values(): m["hp"] = 0
    r, vit = await cenario("kill_all", mata_todos)
    check("kill_all → vitória", vit["chamado"] and vit["victory"] is True)

    # kill_all não conclui com monstro vivo
    r2 = setup_authored(); r2.dungeon_def["objectives"] = {"primary": {"type": "kill_all"}, "secondary": []}
    await r2.enter_dungeon("p1")
    vit2 = {"c": False}
    async def fe2(victory): vit2["c"] = True
    r2.end_game = fe2
    await r2._check_objectives()
    check("kill_all não conclui com monstros vivos", vit2["c"] is False)

    # kill_target: mata só o alvo
    async def mata_alvo(r):
        for m in r.monsters.values():
            if m.get("authored_target"): m["hp"] = 0
    r, vit = await cenario("kill_target", mata_alvo)
    check("kill_target (só o alvo morto) → vitória", vit["chamado"] is True)

    # reach_exit: herói na saída
    async def poe_na_saida(r):
        list(r.players.values())[0]["pos"] = list(r.exit_pos)
    r, vit = await cenario("reach_exit", poe_na_saida)
    check("reach_exit (herói na saída) → vitória", vit["chamado"] is True)

    # open_key_chest
    async def abre_chave(r):
        r.key_chest_opened = True
    r, vit = await cenario("open_key_chest", abre_chave)
    check("open_key_chest → vitória", vit["chamado"] is True)
```

E em `main()`: `await test_conclusao_simples()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL no `[2]` — `AttributeError: ... has no attribute '_check_objectives'`.

- [ ] **Step 3: Implementar a avaliação + conclusão**

Em `server.py`, inserir como métodos de `GameRoom`, logo ANTES de `async def end_game` (~`server.py:11823`):

```python
    def _objetivo_cumprido(self, obj):
        """True se o objetivo `obj` está cumprido no estado atual (só autorado)."""
        t = (obj or {}).get("type")
        vivos = [m for m in self.monsters.values() if m["hp"] > 0]
        if t == "kill_all":
            return len(vivos) == 0
        if t == "kill_target":
            alvos = [m for m in self.monsters.values() if m.get("authored_target")]
            return bool(alvos) and all(m["hp"] <= 0 for m in alvos)
        if t == "reach_exit":
            return self.exit_pos is not None and any(
                p["pos"] == self.exit_pos for p in self.players.values() if p.get("alive"))
        if t == "open_key_chest":
            return bool(getattr(self, "key_chest_opened", False))
        if t == "rescue_prisoner":
            if not self.prisoner or not self.prisoner.get("freed") or not self.prisoner.get("alive"):
                return False
            destino = self.exit_pos or self.stairs_pos
            if not destino:
                return False
            px, py = self.prisoner["pos"]
            return max(abs(px - destino[0]), abs(py - destino[1])) <= 1
        return False

    def _objetivo_status(self, obj):
        if obj and obj.get("type") == "rescue_prisoner" and self.rescue_failed:
            return "failed"
        return "done" if self._objetivo_cumprido(obj) else "pending"

    async def _check_objectives(self):
        """Catch-all chamado por push_state. Recalcula o status p/ o HUD e, se o
        principal está cumprido, concede bônus dos secundários e encerra em vitória."""
        if not self.objectives:
            return
        prim = self.objectives.get("primary")
        secs = self.objectives.get("secondary") or []
        self.objective_status = {
            "primary": {"type": (prim or {}).get("type"), "status": self._objetivo_status(prim)},
            "secondary": [{"type": s.get("type"), "status": self._objetivo_status(s)} for s in secs],
        }
        if (self.phase == "playing" and not self._objetivo_concluido
                and prim and self._objetivo_cumprido(prim)):
            self._objetivo_concluido = True
            for s in secs:
                if self._objetivo_cumprido(s):
                    await self._conceder_bonus_secundario(s)
            await self.end_game(victory=True)
```

`_conceder_bonus_secundario` será implementado na Task 4; por ora adicione um stub temporário logo acima de `_objetivo_cumprido` para o arquivo não quebrar:

```python
    async def _conceder_bonus_secundario(self, obj):
        pass
```

- [ ] **Step 4: Ligar o hook no `push_state`**

Em `server.py`, no INÍCIO de `push_state` (logo após `async def push_state(self):`, ~`server.py:11863`), inserir:

```python
        await self._check_objectives()
```

- [ ] **Step 5: Marcar o baú-chave aberto em `handle_open_chest`**

Em `server.py`, em `handle_open_chest`, logo após a checagem de distância (após o `if max(abs(px - cx), abs(py - cy)) > 2:` retornar — antes do `if kind == "gold":`, ~`server.py:6297`), inserir:

```python
        if chest.get("key_objective"):
            self.key_chest_opened = True
```

> `self.key_chest_opened` nasce ausente; `getattr(self, "key_chest_opened", False)` (em `_objetivo_cumprido`) trata isso. Resete-o no bloco `nova` de `enter_dungeon` adicionando `self.key_chest_opened = False` junto dos outros resets da Task 1 Step 6.

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_objetivos.py`
Expected: PASS — bloco `[2]` verde, `0 falhou`.

- [ ] **Step 7: Regressão**

Run: `python tools/test_persistencia_masmorra.py` → `0 falhou` (procedural: `self.objectives` é None → `_check_objectives` retorna cedo; nada muda).

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat: avaliacao de objetivos + conclusao (kill/reach/chest) (Fase 3)"
```

---

## Task 3: Prisioneiro — libertar, seguir, dano e escolta

**Files:**
- Modify: `server.py` (`handle_libertar_prisioneiro` + dispatch; passo de seguir + dano em `gm_phase`)
- Test: `tools/test_objetivos.py`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar a `tools/test_objetivos.py` (e chamar em `main()`):

```python
async def test_prisioneiro():
    print("\n[3] prisioneiro: libertar, seguir, escolta, morte")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    p1 = r.players["p1"]
    # herói adjacente ao prisioneiro cativo
    p1["pos"] = [r.prisoner["pos"][0] - 1, r.prisoner["pos"][1]]
    p1["action_done"] = False
    r.turn_index = r.player_order.index("p1")
    await r.handle_libertar_prisioneiro("p1")
    check("prisioneiro libertado por herói adjacente", r.prisoner["freed"] is True)
    check("libertar gastou a ação", p1["action_done"] is True)

    # escolta: prisioneiro junto da saída → rescue cumprido
    r.prisoner["pos"] = [r.exit_pos[0], r.exit_pos[1]]
    check("rescue cumprido perto da saída",
          r._objetivo_cumprido(r.objectives["primary"]) is True)

    # morte do prisioneiro → falha, sem encerrar.
    # Chama _processar_prisioneiro_turno direto (gm_phase moveria o monstro antes),
    # e neutraliza o passo de seguir p/ o prisioneiro não sair de perto do monstro.
    r2 = setup_authored()
    r2.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r2.enter_dungeon("p1")
    r2.prisoner["freed"] = True; r2.prisoner["hp"] = 1
    vit = {"c": False}
    async def fe(victory): vit["c"] = True
    r2.end_game = fe
    r2._step_towards = lambda ent, dest: None       # isola: sem mover o prisioneiro
    m = next(iter(r2.monsters.values()))
    m["hp"] = 10; m["pos"] = [r2.prisoner["pos"][0] + 1, r2.prisoner["pos"][1]]   # adjacente
    await r2._processar_prisioneiro_turno()
    check("prisioneiro morto marca rescue_failed", r2.rescue_failed is True)
    check("morte do prisioneiro NÃO encerra a partida", vit["c"] is False)
    check("status do resgate = failed",
          r2._objetivo_status(r2.objectives["primary"]) == "failed")
```

E em `main()`: `await test_prisioneiro()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL no `[3]` — `AttributeError: ... 'handle_libertar_prisioneiro'`.

- [ ] **Step 3: Implementar o handler de libertar**

Em `server.py`, inserir como método de `GameRoom`, perto dos outros handlers de ação (por exemplo logo após `_check_objectives` que você criou na Task 2):

```python
    async def handle_libertar_prisioneiro(self, pid):
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p.get("alive") or p.get("action_done"):
            return
        if not self.prisoner or not self.prisoner.get("alive") or self.prisoner.get("freed"):
            await self.send_to(pid, {"type": "error", "msg": "Não há prisioneiro para libertar."}); return
        px, py = p["pos"]; bx, by = self.prisoner["pos"]
        if max(abs(px - bx), abs(py - by)) > 1:
            await self.send_to(pid, {"type": "error", "msg": "Aproxime-se do prisioneiro."}); return
        self.prisoner["freed"] = True
        p["action_done"] = True
        await self.gm_say(f"🔓 **{p['name']}** libertou o prisioneiro!")
        await self.push_state()
```

- [ ] **Step 4: Passo de seguir + dano no `gm_phase`**

Em `server.py`, no fim de `gm_phase` (após o laço `for m in alive_monsters:` que move/ataca os monstros — perto do fim do método, ~`server.py:11430`), inserir uma chamada ao processamento do prisioneiro:

```python
        await self._processar_prisioneiro_turno()
```

E inserir o método (perto de `gm_phase`):

```python
    async def _processar_prisioneiro_turno(self):
        """Prisioneiro libertado: 1 passo em direção ao herói vivo mais próximo;
        depois, cada monstro adjacente o fere. Morte → rescue_failed (não encerra)."""
        pr = self.prisoner
        if not pr or not pr.get("freed") or not pr.get("alive"):
            return
        herois = [p for p in self.players.values() if self._ativo(p)]
        if herois:
            alvo = min(herois, key=lambda p: max(abs(p["pos"][0] - pr["pos"][0]),
                                                 abs(p["pos"][1] - pr["pos"][1])))
            self._step_towards(pr, alvo["pos"])
        # Dano de monstros adjacentes (caminho dedicado, simples e isolado).
        for m in self.monsters.values():
            if m["hp"] <= 0:
                continue
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                dano = random.randint(2, 5)
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break

    def _step_towards(self, ent, dest):
        """Move `ent` (dict com 'pos') 1 casa em direção a `dest` por casa livre
        (FLOOR/DOOR, não ocupada por monstro/herói). Sem diagonal."""
        ex, ey = ent["pos"]; dx, dy = dest
        opcoes = sorted([(ex + sx, ey + sy) for sx, sy in ((1,0),(-1,0),(0,1),(0,-1))],
                        key=lambda c: max(abs(c[0] - dx), abs(c[1] - dy)))
        ocup = {tuple(m["pos"]) for m in self.monsters.values() if m["hp"] > 0}
        ocup |= {tuple(p["pos"]) for p in self.players.values() if p.get("alive")}
        for nx, ny in opcoes:
            if (0 <= nx < self.map_w and 0 <= ny < self.map_h
                    and self.tiles[ny][nx] != WALL and (nx, ny) not in ocup):
                ent["pos"] = [nx, ny]; return
```

> `random` já está importado no topo de `server.py`.

- [ ] **Step 5: Rotear a mensagem**

Em `server.py`, no switch de mensagens, junto aos outros `elif t == "...":`, inserir:

```python
                elif t == "libertar_prisioneiro":
                    if room: await room.handle_libertar_prisioneiro(pid)
```

(Use como âncora o ramo `elif t == "open_door":` ou outro handler de ação e adicione logo após.)

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_objetivos.py`
Expected: PASS — bloco `[3]` verde, `0 falhou`.

- [ ] **Step 7: Regressão**

Run: `python tools/test_persistencia_masmorra.py` → `0 falhou` (procedural: `self.prisoner` None → `_processar_prisioneiro_turno` retorna cedo).

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat: prisioneiro (libertar/seguir/dano/escolta) (Fase 3)"
```

---

## Task 4: Bônus dos objetivos secundários

**Files:**
- Modify: `server.py` (`_conceder_bonus_secundario` + constantes)
- Test: `tools/test_objetivos.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tools/test_objetivos.py` (e chamar em `main()`):

```python
async def test_bonus_secundario():
    print("\n[4] secundário cumprido concede bônus de XP/ouro")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "kill_all"},
                                   "secondary": [{"type": "open_key_chest"}]}
    await r.enter_dungeon("p1")
    r.end_game = lambda victory=True: asyncio.sleep(0)  # não encerra de verdade
    p1 = r.players["p1"]
    xp0, ouro0 = p1["xp"], p1["gold"]
    # cumpre principal (kill_all) e secundário (open_key_chest)
    for m in r.monsters.values(): m["hp"] = 0
    r.key_chest_opened = True
    await r._check_objectives()
    check("XP do grupo subiu pelo secundário", p1["xp"] > xp0)
    check("ouro do grupo subiu pelo secundário", p1["gold"] > ouro0)
```

E em `main()`: `await test_bonus_secundario()`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_objetivos.py`
Expected: FAIL no `[4]` — o stub de `_conceder_bonus_secundario` não dá bônus (XP/ouro não sobem).

- [ ] **Step 3: Implementar o bônus (substituir o stub)**

Em `server.py`, SUBSTITUIR o stub `async def _conceder_bonus_secundario(self, obj): pass` por:

```python
    async def _conceder_bonus_secundario(self, obj):
        """Concede XP+ouro ao grupo por um objetivo secundário cumprido."""
        for p in self.players.values():
            if p.get("alive"):
                p["xp"] += OBJ_BONUS_XP
                p["gold"] += OBJ_BONUS_OURO
                await self._check_level_up(p)
        nome = (obj or {}).get("type", "objetivo")
        await self.gm_say(f"⭐ Objetivo secundário **{nome}** cumprido! +{OBJ_BONUS_XP} XP, +{OBJ_BONUS_OURO} ouro ao grupo.")
```

E junto às constantes do topo (perto de `PRIS_HP`), adicionar:

```python
OBJ_BONUS_XP = 50
OBJ_BONUS_OURO = 25
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_objetivos.py`
Expected: PASS — bloco `[4]` verde, `0 falhou`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat: bonus de XP/ouro por objetivo secundario (Fase 3)"
```

---

## Task 5: Serialização + cliente (HUD, saída, prisioneiro, botão)

**Files:**
- Modify: `server.py` (`push_state` — campos)
- Modify: `src/gameState.js`
- Modify: `game.js`

> Servidor testável; cliente verificado no navegador (controlador faz o e2e na Task 6).

- [ ] **Step 1: Acrescentar campos ao `push_state`**

Em `server.py`, no dict do `push_state` (o `await self.broadcast({...})`), acrescentar três chaves (após `"stairs_pos": self.stairs_pos,`, ~`server.py:11876`):

```python
            "objectives": self.objective_status,
            "exit_pos": self.exit_pos,
            "prisoner": self.prisoner,
```

- [ ] **Step 2: Teste rápido de serialização**

Adicionar a `tools/test_objetivos.py` (e chamar em `main()`):

```python
async def test_serializacao():
    print("\n[5] push_state expõe objectives/exit_pos/prisoner")
    r = setup_authored()
    capturado = {}
    async def cap(msg):
        if msg.get("type") == "game_state": capturado.update(msg)
    r.broadcast = cap
    await r.enter_dungeon("p1")
    await GameRoom.push_state(r)   # usa o push_state real (não o stub do setup)
    check("game_state traz exit_pos", capturado.get("exit_pos") == [14, 4])
    check("game_state traz prisoner", capturado.get("prisoner") is not None)
    check("game_state traz objectives", capturado.get("objectives") is not None)
```

E em `main()`: `await test_serializacao()`. Rodar: `python tools/test_objetivos.py` → `0 falhou`.

- [ ] **Step 3: Commit do servidor**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat: serializa objectives/exit_pos/prisoner no game_state (Fase 3)"
```

- [ ] **Step 4: `gameState.js` — getters/sender/decisor**

Localizar o padrão dos getters/senders:
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('src/gameState.js',encoding='utf-8')) if 'function selectDungeon' in l or 'get lobbyState' in l or 'gameState.' in l][:12]"`

No handler de `game_state` (onde `gameState = msg`), os 3 campos já ficam em `gameState`. Adicionar getters (perto de `get lobbyDungeons` etc.):

```javascript
  function objectives() { return (gameState && gameState.objectives) || null; }
  function exitPos()    { return (gameState && gameState.exit_pos) || null; }
  function prisoner()   { return (gameState && gameState.prisoner) || null; }
  function prisioneiroLibertavel() {
    const pr = prisoner(); const me = (gameState && gameState.players || []).find(p => p.id === myPid);
    if (!pr || pr.freed || !pr.alive || !me) return false;
    return Math.max(Math.abs(me.pos[0] - pr.pos[0]), Math.abs(me.pos[1] - pr.pos[1])) <= 1
           && gameState.current_turn === myPid;
  }
  function libertarPrisioneiro() { send({ type: 'libertar_prisioneiro' }); }
```

> Ajuste `objectives`/`exitPos`/`prisoner` para o estilo do arquivo (se forem getters `get x()` no objeto público, siga esse padrão; se forem `function x()`, idem). Exporte os quatro no objeto público `GS` (onde `selectDungeon` é exposto).

- [ ] **Step 5: `game.js` — render do HUD, saída, prisioneiro, botão**

Editar `game.js` apenas pelo tool de Edit (regra do projeto: nunca via PowerShell). Localizar a render do tabuleiro e da HUD:
`python -c "[print(i+1,l.rstrip()) for i,l in enumerate(open('game.js',encoding='utf-8')) if 'stairs_pos' in l or 'drawDoor2D' in l or 'GS.gameState' in l][:15]"`

Adicionar, seguindo os idiomas existentes:
1. **Casa de saída:** onde a escada (`stairs_pos`) é desenhada no 2D/3D, desenhar também `GS.exitPos()` com um marcador 🏁 (cor distinta).
2. **Peão do prisioneiro:** onde peões/entidades são desenhados, se `GS.prisoner()` existe, desenhar um peão na `prisoner.pos` (aparência "cativo" se `!freed`, "seguindo" se `freed`); barra de HP simples (hp/max_hp).
3. **HUD de objetivos:** um painel (canto da tela) listando `GS.objectives().primary` + `.secondary`, cada um com ícone por `status` (`done`→✅, `pending`→⬜, `failed`→❌) e um rótulo legível por tipo (`kill_all`→"Eliminar todos", `kill_target`→"Derrotar o alvo", `reach_exit`→"Chegar à saída", `open_key_chest`→"Abrir o baú-chave", `rescue_prisoner`→"Resgatar o prisioneiro").
4. **Botão "Libertar":** quando `GS.prisioneiroLibertavel()`, mostrar um botão que chama `GS.libertarPrisioneiro()`; esconder caso contrário. Re-render junto da HUD a cada `game_state`.

- [ ] **Step 6: Commit do cliente**

```bash
git add src/gameState.js game.js
git commit -m "feat: HUD de objetivos + saida + prisioneiro + botao libertar no cliente (Fase 3)"
```

---

## Task 6: Verificação ponta-a-ponta no navegador

**Files:** nenhum (verificação).

> Usar os preview_* tools. Servir o jogo (`python server.py` na 8765). Dirigir via WebSocket de teste como na verificação da Fase 1.

- [ ] **Step 1: Subir o servidor e copiar a fixture**

`dungeons/test_fase3.json` já existe (Task 1). Subir `python server.py`; abrir `http://localhost:8765/index.html`.

- [ ] **Step 2: Caminho de conclusão**

Dirigir o fluxo (via socket de teste, como na Fase 1): `create_room` → `select_dungeon test_fase3.json` → `select_class` → `start_game` → `enter_dungeon`. Verificar no `game_state`: `objectives` (primary rescue_prisoner pending), `exit_pos`=[14,4], `prisoner` cativo. Abrir a porta, mover um herói até adjacente ao prisioneiro, `libertar_prisioneiro`, confirmar `prisoner.freed=true`; escoltar até a saída (mover heróis; o prisioneiro segue no gm_phase) e confirmar que o `game_over victory` dispara.

- [ ] **Step 3: HUD/visual + console**

Abrir a UI no navegador (preview), confirmar o HUD de objetivos, a casa de saída 🏁 e o peão do prisioneiro renderizam, o botão "Libertar" aparece quando adjacente, e o console fica sem erros. Screenshot de evidência.

- [ ] **Step 4: Regressão procedural**

Em uma sala procedural, jogar normalmente: sem HUD de objetivos (objectives null), boss-kill → vitória como antes.

- [ ] **Step 5: Parar o servidor e relatar evidências.**

---

## Self-Review (cobertura do spec)

- **Instanciar exit/prisoner/objectives + key chest** → Task 1.
- **5 tipos de objetivo + conclusão (principal→end_game)** → Task 2 (`_objetivo_cumprido`/`_check_objectives`), prisioneiro/escolta em Task 3.
- **Hook único em push_state** → Task 2 Step 4.
- **Prisioneiro: libertar (ação adjacente), seguir, dano de monstros, morte→rescue_failed (sem derrota), escolta** → Task 3.
- **Bônus de secundários (XP/ouro)** → Task 4.
- **Serialização + cliente (HUD, saída, prisioneiro, botão)** → Task 5.
- **Procedural intacto** → guardas `self.objectives`/`self.prisoner`; regressão em Tasks 2/3/6.
- **Teste por tipo de objetivo + prisioneiro + bônus** → `tools/test_objetivos.py` (Tasks 1–4) + e2e (Task 6).

**Decisão de implementação (registrada):** o dano ao prisioneiro usa um caminho dedicado simples (monstro adjacente → `random.randint(2,5)`) em vez de threadar o prisioneiro pela seleção de alvos/aplicação de dano dos monstros — isola o risco e mantém a IA dos monstros intacta, fiel à intenção do spec ("monstros podem atacá-lo").

**Sem placeholders de código:** cada Step de servidor traz código completo; os Steps de cliente trazem getters/sender concretos + âncoras de localização (game.js/gameState.js grandes; o ponto exato é achado com o grep indicado).

**Consistência de nomes:** `exit_pos`, `objectives`, `objective_status`, `prisoner`, `rescue_failed`, `_objetivo_concluido`, `key_chest_opened`, `_objetivo_cumprido`, `_objetivo_status`, `_check_objectives`, `_conceder_bonus_secundario`, `_processar_prisioneiro_turno`, `_step_towards`, `handle_libertar_prisioneiro`, `PRIS_HP`, `OBJ_BONUS_XP`, `OBJ_BONUS_OURO` — usados de forma idêntica entre as tasks. Cliente: `objectives`/`exitPos`/`prisoner`/`prisioneiroLibertavel`/`libertarPrisioneiro`.
