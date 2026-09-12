# Projéteis no 3D (frente B) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** flecha/virote/lança em malha procedural e itens arremessados (PNG girando) voam do atacante ao alvo quando o d20 assenta; o impacto (reação, número, cue, morte) acontece na chegada; erro passa reto e crava 1 casa além; natural 1 cai a meio caminho.

**Architecture:** o servidor acrescenta um campo opcional `projectile` ao `attack_feedback start` (helper `_projetil_de`) e faz `handle_throw_item` emitir `attack_feedback`; a `CombatScene` (módulo puro) transforma o `GOLPE` em lançamento — emite o comando `launch` e atrasa o `IMPACTO` por `travelMs`; o `game.js` anima o voo numa lista `_projeteis` (família `_bolaFogo*`) e atrasa os números de área por um portão irmão do `_bolaFogoFeedbackStartAt`.

**Tech Stack:** Python (`server.py`, testes com `GameRoom` mockado), Vanilla JS (`src/combatScene.js` puro + `game.js` com Three.js r128), node para `tools/test_combat_scene.js`.

**Spec:** `docs/superpowers/specs/2026-09-12-projeteis-3d-design.md`. **Pré-requisito:** a frente A já mesclada (`src/combatScene.js` existe, 204 checks).

---

## Avisos ao executor

1. **`game.js`/`server.py` têm WIP não commitado do autor.** Execute num **worktree** a partir de `HEAD`. Referências a funções são **por nome** (grep), nunca por linha. Nunca `git add game.js`/`server.py` fora do worktree.
2. `server.py` é UTF-8 com emoji: edite com o Edit tool (nunca por script que fatie por índice). O servidor rodando trava a escrita de `server.py`/`game.js` — pare o preview antes de gravar.
3. Rode `python -X utf8 tools/test_projeteis.py`, `node tools/test_combat_scene.js`, `node --check game.js` conforme cada task pede. Contagens de checks: reporte a real; toda check deve ser ✅.
4. Prova em navegador (Task 7): servidor **reiniciado** numa porta própria (`LFH_PORT=8766`), Ctrl+F5, e gravar a linha do tempo por `setInterval` — screenshot sozinho não prova sincronia.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | `_projetil_de` (module-level), `_emitir_feedback_ataque` descarta `projectile=None`, 3 sites de `start`, fichas do kobold, `handle_throw_item` emite feedback |
| `tools/test_projeteis.py` (novo) | testes do servidor |
| `src/combatScene.js` | `projectile` na cena, comando `launch`, `GOLPE` = voo, `sem_dado`, área, miss/fumble |
| `tools/test_combat_scene.js` | seções novas `[35]`+ e checagens estáticas |
| `src/visualConfig.js` | bloco `scene.projectile` |
| `game.js` | `_receiveAttackFeedback` repassa `projectile`; `_projeteis` + `_projetilLancar/_projetilUpdate3D/_projetilDispose3D`; `launch` em `_executarComandoCena`; tick; `dispose3D`/`init3D`; `_projetilFeedbackStartAt` no diff de HP |

---

### Task 1: Servidor — `_projetil_de` e o campo `projectile` nos 3 sites de ataque

**Files:**
- Create: `tools/test_projeteis.py`
- Modify: `server.py` — novo helper module-level `_projetil_de` (perto de `RANGED_AMMO`), `_emitir_feedback_ataque`, os 3 sites `"start"` (herói/animado/monstro), a ficha `kobold_besteiro` e `_kobold_throw_lance`

- [ ] **Step 1: Escrever o teste falhando**

```python
"""Projéteis (frente B): campo `projectile` no attack_feedback e emissão no arremesso.
Roda da raiz: python -X utf8 tools/test_projeteis.py"""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala():
    """Sala mínima que CAPTURA os broadcasts (a frente A só os silenciava)."""
    r = S.GameRoom("TEST")
    r._msgs = []
    async def cap(msg, *a, **k):
        if isinstance(msg, dict): r._msgs.append(msg)
    async def noop(*a, **k): pass
    r.broadcast = cap; r.gm_say = noop; r.push_state = noop
    r.broadcast_city_state = noop; r.send_to = noop
    r._is_turn = lambda pid: True
    r._tem_linha_de_visao = lambda *a, **k: True
    r.phase = "playing"
    r.map_w = 14; r.map_h = 14
    r.tiles = [[S.FLOOR]*14 for _ in range(14)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    p = S.make_player("p1", "Victor", "warrior", 0); r.players["p1"] = p
    p["pos"] = [1, 1]; p["atk_bonus"] = 50; p["alive"] = True; p["connected"] = True
    r.connections["p1"] = object()
    r.monsters["m1"] = {"id": "m1", "name": "Alvo", "type": "orc", "hp": 999, "ac": 1,
                        "pos": [4, 1], "alive": True, "special_abilities": [],
                        "alertado": True, "room_id": "r0"}
    return r, p

def feedbacks(r, fase="start"):
    return [m for m in r._msgs if m.get("type") == "attack_feedback" and m.get("phase") == fase]

def test_helper():
    print("\n[1] _projetil_de")
    check("arco_curto → arrow", S._projetil_de({"id": "arco_curto", "range": 6, "categoria": "perfurante"}) == {"kind": "arrow"})
    check("longbow → arrow",    S._projetil_de({"id": "longbow"}) == {"kind": "arrow"})
    check("besta → bolt",       S._projetil_de({"id": "besta"}) == {"kind": "bolt"})
    check("hand_crossbow → bolt", S._projetil_de({"id": "hand_crossbow"}) == {"kind": "bolt"})
    check("chicote (range 2, sem projétil) → None", S._projetil_de({"id": "chicote", "range": 2, "categoria": "cortante"}) is None)
    check("alabarda (range 2 perfurante, HERÓI) → None", S._projetil_de({"id": "alabarda", "range": 2, "categoria": "perfurante"}) is None)
    check("arma do editor com ammo virotes → bolt", S._projetil_de({"id": "besta_custom_x", "ammo": "virotes", "range": 5}) == {"kind": "bolt"})
    check("arma do editor com ammo flechas → arrow", S._projetil_de({"id": "arco_custom_x", "ammo": "flechas", "range": 5}) == {"kind": "arrow"})
    check("monstro: range≥2 perfurante → arrow", S._projetil_de({"name": "Arco", "range": 8, "categoria": "perfurante"}, monstro=True) == {"kind": "arrow"})
    check("monstro: range≥2 não-perfurante (cuspe) → None", S._projetil_de({"name": "Cuspe", "range": 4, "categoria": "acido"}, monstro=True) is None)
    check("monstro: range 1 → None", S._projetil_de({"name": "Garras", "range": 1, "categoria": "perfurante"}, monstro=True) is None)
    check("monstro: campo projectile sobrepõe", S._projetil_de({"name": "Besta", "range": 4, "projectile": "bolt"}, monstro=True) == {"kind": "bolt"})
    check("projectile inválido é ignorado", S._projetil_de({"name": "X", "range": 4, "projectile": "laser"}, monstro=True) is None)
    check("None/vazio → None", S._projetil_de(None) is None and S._projetil_de({}) is None)
    kb = next(d for d in S.MONSTER_DEFS if d.get("type") == "kobold_besteiro")
    check("ficha kobold_besteiro declara projectile bolt", kb["attacks"][0].get("projectile") == "bolt")

def test_sites():
    print("\n[2] Campo projectile nos sites de start")
    r, p = sala()
    p["weapon"] = {"id": "arco_curto", "name": "Arco Curto", "die": "1d6", "stat": "dex", "range": 6, "categoria": "perfurante"}
    p["gear"]["off_hand"] = {"id": "flechas", "name": "Flechas", "effect": "ammo", "ammo_type": "flechas", "ammo_count": 10}   # arco exige munição
    random.seed(7)
    asyncio.run(r.handle_attack("p1", "m1"))
    st = feedbacks(r)
    check("herói com arco: start emitido", len(st) == 1)
    check("herói com arco: projectile arrow", st and st[0].get("projectile") == {"kind": "arrow"})
    check("result não carrega projectile", all("projectile" not in m for m in feedbacks(r, "result")))

    r, p = sala(); r._msgs.clear()
    p["weapon"] = {"id": "espada", "name": "Espada", "die": "1d8", "stat": "str_", "categoria": "cortante"}
    r.monsters["m1"]["pos"] = [2, 1]
    asyncio.run(r.handle_attack("p1", "m1"))
    st = feedbacks(r)
    check("herói corpo a corpo: start sem a chave projectile", st and "projectile" not in st[0])

    r, p = sala(); r._msgs.clear()
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "goblin_arqueiro")
    m = S.make_monster(mdef, r.rooms[0]); m["id"] = "g1"; m["pos"] = [6, 1]; m["room_id"] = "r0"; m["alertado"] = True
    r.monsters["g1"] = m
    atk = dict(m["attacks"][0])
    asyncio.run(r._execute_one_monster_attack(m, atk, p))
    st = feedbacks(r)
    check("goblin arqueiro: start com arrow", st and st[-1].get("projectile") == {"kind": "arrow"})

    r, p = sala(); r._msgs.clear()
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "kobold_besteiro")
    m = S.make_monster(mdef, r.rooms[0]); m["id"] = "k1"; m["pos"] = [4, 1]; m["room_id"] = "r0"; m["alertado"] = True
    r.monsters["k1"] = m
    asyncio.run(r._execute_one_monster_attack(m, dict(m["attacks"][0]), p))
    st = feedbacks(r)
    check("kobold besteiro: start com bolt", st and st[-1].get("projectile") == {"kind": "bolt"})

if __name__ == "__main__":
    print("=" * 60); print("  TESTE — Projéteis (frente B)"); print("=" * 60)
    test_helper()
    test_sites()
    print("\n" + "=" * 60)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 60)
    sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python -X utf8 tools/test_projeteis.py`
Expected: `AttributeError: module 'server' has no attribute '_projetil_de'`.

- [ ] **Step 3: Helper module-level** — inserir logo após o bloco `RANGED_AMMO = { ... }` em `server.py`:

```python
# ── Projétil visual de um ataque (frente B — só afeta a animação do cliente) ──
# Devolve {"kind": ...} ou None. Herói: pela arma (id nativo ou `ammo` do
# editor); arma de haste com `range` (chicote, alabarda) NÃO tem projétil.
# Monstro/servo: `projectile` explícito no ataque, senão range≥2 + perfurante.
_PROJETIL_POR_ARMA    = {"arco_curto": "arrow", "longbow": "arrow", "besta": "bolt", "hand_crossbow": "bolt"}
_PROJETIL_POR_MUNICAO = {"flechas": "arrow", "virotes": "bolt"}
_PROJETIL_KINDS       = ("arrow", "bolt", "spear")

def _projetil_de(defn, monstro=False):
    if not defn or not isinstance(defn, dict):
        return None
    explicito = defn.get("projectile")
    if explicito in _PROJETIL_KINDS:
        return {"kind": explicito}
    kind = _PROJETIL_POR_ARMA.get(defn.get("id")) or _PROJETIL_POR_MUNICAO.get(defn.get("ammo"))
    if kind:
        return {"kind": kind}
    if monstro:
        rng = defn.get("range")
        if isinstance(rng, (int, float)) and rng >= 2 and defn.get("categoria") == "perfurante":
            return {"kind": "arrow"}
    return None
```

- [ ] **Step 4: `_emitir_feedback_ataque` descarta `projectile=None`** — dentro da função, logo antes do `await self.broadcast({`:

```python
        if resultado.get("projectile") is None:
            resultado.pop("projectile", None)      # só o start com projétil leva a chave
```

- [ ] **Step 5: Os 3 sites `"start"`** (grep `_emitir_feedback_ataque(` seguido de `"start"`):

Herói (em `handle_attack`; a variável da arma é `weapon_here`):
```python
            attack_feedback_id = await self._emitir_feedback_ataque(
                "start", p, target, attack_name, attack_mode,
                projectile=_projetil_de(weapon_here))
```
Servo animado (site com `"start", a, m, ...`; o dict do ataque é `ataque`):
```python
        attack_feedback_id = await self._emitir_feedback_ataque(
            "start", a, m, attack_name, attack_mode,
            projectile=_projetil_de(ataque, monstro=True))
```
Monstro (site com `"start", m, target, ...`; o dict é `atk_def`):
```python
        attack_feedback_id = await self._emitir_feedback_ataque(
            "start", m, target, attack_name, attack_mode,
            projectile=_projetil_de(atk_def, monstro=True))
```

- [ ] **Step 6: Fichas** — em `MONSTER_DEFS`, no ataque `{"name": "Besta de Mão", "atk_bonus": 4, "damage": "1d4+2", ... "range": 4}` do `kobold_besteiro`, acrescentar `"projectile": "bolt"` (após `"range": 4`). Em `_kobold_throw_lance`, logo após `atk["range"] = 4`, acrescentar `atk["projectile"] = "spear"`.

- [ ] **Step 7: Rodar**

Run: `python -X utf8 tools/test_projeteis.py`
Expected: `21 passaram, 0 falharam` (reporte a contagem real; zero ❌). Rode também `python -X utf8 tools/test_agarrao.py` (não deve regredir).

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_projeteis.py
git commit -m "feat(projeteis): campo projectile no attack_feedback (arco/besta/lanca; kobold)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Servidor — `handle_throw_item` emite `attack_feedback`

**Files:**
- Modify: `server.py` — `_throw_item_alvo`, `_throw_item_area`
- Modify: `tools/test_projeteis.py`

- [ ] **Step 1: Acrescentar os testes** (antes do `if __name__`), e chamar `test_throw()` no main:

```python
def test_throw():
    print("\n[3] Arremesso mirado emite attack_feedback")
    r, p = sala(); r._msgs.clear()
    defn = S.ARREMESSAVEIS["frasco_oleo"]
    p["bag"] = [{"id": "frasco_oleo", "name": defn["name"], "emoji": defn["emoji"], "item_slot": "bag"}]
    random.seed(4321)
    asyncio.run(r.handle_throw_item("p1", {"item_id": "frasco_oleo", "target_id": "m1"}))
    st = feedbacks(r); rs = feedbacks(r, "result")
    check("start emitido", len(st) == 1)
    check("start: kind item + item_id + emoji", st and st[0].get("projectile") == {"kind": "item", "item_id": "frasco_oleo", "item_emoji": defn["emoji"]})
    check("start: alvo e posições", st and st[0]["target_id"] == "m1" and st[0]["attacker_pos"] == [1, 1] and st[0]["target_pos"] == [4, 1])
    check("result emitido com o mesmo attack_id", rs and rs[0]["attack_id"] == st[0]["attack_id"])
    check("result carrega hit/crit/natural", rs and all(k in rs[0] for k in ("hit", "crit", "natural", "natural_critical", "natural_fumble")))
    i_start = next(i for i, m in enumerate(r._msgs) if m.get("type") == "attack_feedback")
    i_dado = next(i for i, m in enumerate(r._msgs) if m.get("type") == "dice_roll")
    check("start sai ANTES do d20", i_start < i_dado)

    print("\n[4] Arremesso de área emite attack_feedback sem alvo")
    r, p = sala(); r._msgs.clear()
    defn = S.ARREMESSAVEIS["bomba_incendiaria"]
    p["bag"] = [{"id": "bomba_incendiaria", "name": defn["name"], "emoji": defn["emoji"], "item_slot": "bag"}]
    random.seed(11)
    asyncio.run(r.handle_throw_item("p1", {"item_id": "bomba_incendiaria", "tx": 4, "ty": 1}))
    st = feedbacks(r); rs = feedbacks(r, "result")
    check("start emitido", len(st) == 1)
    check("start: target_id None e target_pos = casa", st and st[0]["target_id"] is None and st[0]["target_pos"] == [4, 1])
    pj = st[0].get("projectile") if st else None
    check("start: projectile area + sem_dado + area_raio", pj and pj.get("kind") == "item" and pj.get("area") is True
          and pj.get("sem_dado") is True and pj.get("area_raio") == defn.get("area_raio", 1) and pj.get("item_id") == "bomba_incendiaria")
    check("result imediato com hit True", rs and rs[0].get("hit") is True and rs[0]["attack_id"] == st[0]["attack_id"])
    i_start = next(i for i, m in enumerate(r._msgs) if m.get("type") == "attack_feedback")
    i_res = next(i for i, m in enumerate(r._msgs) if m.get("type") == "attack_feedback" and m.get("phase") == "result")
    dados = [i for i, m in enumerate(r._msgs) if m.get("type") == "dice_roll"]
    check("start e result saem antes de qualquer dado da área", not dados or i_res < dados[0])
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python -X utf8 tools/test_projeteis.py`
Expected: `[3]`/`[4]` com ❌ "start emitido".

- [ ] **Step 3: `_throw_item_alvo`** — logo ANTES da linha `roll = random.randint(1, 20)` (após os checks de alcance/LOS), inserir:

```python
        attack_feedback_id = await self._emitir_feedback_ataque(
            "start", p, target, defn.get("name") or item.get("name") or "Arremesso", "normal",
            projectile={"kind": "item", "item_id": defn.get("id") or item.get("id"), "item_emoji": defn.get("emoji") or item.get("emoji")})
```

e logo APÓS o `await self.broadcast({"type": "dice_roll", "die": "d20", ... "hit": hit, "crit": crit})` (o d20 do arremesso), inserir:

```python
        await self._emitir_feedback_ataque(
            "result", p, target, defn.get("name") or item.get("name") or "Arremesso", "normal",
            attack_id=attack_feedback_id, roll=roll, total=total,
            hit=bool(hit), crit=bool(crit), natural=int(roll),
            natural_critical=bool(roll == 20), natural_fumble=bool(nat1))
```

- [ ] **Step 4: `_throw_item_area`** — logo APÓS `raio = defn.get("area_raio", 1)` (antes do `gm_say` "arremessa em"), inserir:

```python
        # Feedback visual: o frasco voa até a casa; sem alvo único e sem d20
        # de ataque (os saves rolam durante o voo). Alvo sintético só com pos.
        alvo_area = {"id": None, "name": "", "pos": [cx, cy]}
        nome_arr = defn.get("name") or item.get("name") or "Arremesso"
        attack_feedback_id = await self._emitir_feedback_ataque(
            "start", p, alvo_area, nome_arr, "normal",
            projectile={"kind": "item", "item_id": defn.get("id") or item.get("id"),
                        "item_emoji": defn.get("emoji") or item.get("emoji"),
                        "area": True, "area_raio": int(raio), "sem_dado": True})
        await self._emitir_feedback_ataque(
            "result", p, alvo_area, nome_arr, "normal",
            attack_id=attack_feedback_id, hit=True, crit=False,
            natural_critical=False, natural_fumble=False)
```

- [ ] **Step 5: Rodar**

Run: `python -X utf8 tools/test_projeteis.py && python -X utf8 tools/test_editor_itens.py`
Expected: projéteis `32 passaram, 0 falharam` (contagem real); `test_editor_itens` continua verde (as seções [G3]/[G4] usam `handle_throw_item` com `broadcast=noop` — nada muda para elas).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_projeteis.py
git commit -m "feat(projeteis): arremesso de item emite attack_feedback (alvo e area)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Módulo — `projectile` na cena, comando `launch`, voo, `sem_dado`, área, erro/fumble

**Files:**
- Modify: `src/combatScene.js`
- Modify: `tools/test_combat_scene.js` (seções `[35]`–`[39]`, inseridas ANTES da seção `[33]`)

- [ ] **Step 1: Testes** — inserir antes de `console.log("\n[33] Fiação estática ...")`:

```js
console.log("\n[35] Projétil: launch na entrada do GOLPE e impacto na chegada");
CS.reset(); CS.configure({});
const ARCO = { attack_id: "arc_1", attacker_key: "p:id_1", target_key: "m:id_9",
               attacker_pos: [0, 0], target_pos: [4, 0], projectile: { kind: "arrow" } };
CS.start(ARCO, 0); CS.tick(0);
check("cena com projétil não é melee", CS._scenes[0].melee === false);
check("travelMs = 4 casas × 55 = 220 (clamp min 220)", CS._scenes[0].travelMs === 220);
CS.result({ ...ARCO, hit: true }, 1); CS.tick(180);
check("espera o dado como qualquer ataque", CS.phaseOf("arc_1") === "ESPERANDO_DADO");
CS.dieSettled({ die: "d20" }, 500);
const cmdsL = CS.tick(500);
const launch = cmdsL.find(c => c.cmd === "launch");
check("GOLPE emite launch", !!launch);
check("launch carrega kind/from/to/hit/travelMs", launch && launch.kind === "arrow" && launch.hit === true
  && launch.from[0] === 0 && launch.to[0] === 4 && launch.to[1] === 0 && launch.travelMs === 220 && launch.flightMs === 220);
check("impact NÃO sai no lançamento", !cmdsL.some(c => c.cmd === "impact"));
check("alvo ainda sem pose durante o voo", CS.poseFor("m:id_9", 600) === null);
check("atacante faz o coice durante o voo", CS.poseFor("p:id_1", 545).dx < 0);
const cmdsI = CS.tick(720);
check("impact sai só na chegada (500 + 220)", cmdsI.some(c => c.cmd === "impact") && CS._scenes[0].impactAt === 720);
check("impact carrega projectile kind", cmdsI.find(c => c.cmd === "impact").projectile === "arrow");
check("alvo reage após a chegada", CS.poseFor("m:id_9", 720 + 130).dx > 0);

console.log("\n[36] Projétil: distância longa satura no travelMaxMs e instant colapsa");
CS.reset(); CS.configure({});
CS.start({ ...ARCO, attack_id: "arc_2", target_pos: [30, 0] }, 0); CS.tick(0);
check("30 casas × 55 = 1650 → clamp 900", CS._scenes[0].travelMs === 900);
CS.reset(); CS.configure({ duration: ms => ms * 0.5 });
CS.start({ ...ARCO, attack_id: "arc_3" }, 0); CS.tick(0);
check("travelMs passa pela duration (fast 0,5× → 110)", CS._scenes[0].travelMs === 110);
CS.reset(); CS.configure({ instant: () => true, duration: () => 0.001 });
CS.start({ ...ARCO, attack_id: "arc_4" }, 0); CS.tick(0); CS.result({ ...ARCO, attack_id: "arc_4", hit: true }, 1);
const cmdsInst = CS.tick(1);
check("instant: impact imediato e SEM launch", cmdsInst.some(c => c.cmd === "impact") && !cmdsInst.some(c => c.cmd === "launch"));
CS.configure({});

console.log("\n[37] Projétil: erro passa reto, fumble cai a meio caminho");
CS.reset();
CS.start({ ...ARCO, attack_id: "arc_5" }, 0); CS.tick(0);
CS.result({ ...ARCO, attack_id: "arc_5", hit: false }, 1); CS.tick(180); CS.dieSettled({ die: "d20" }, 500);
let l5 = CS.tick(500).find(c => c.cmd === "launch");
check("erro: to estendido 1 casa além do alvo", l5 && l5.hit === false && Math.abs(l5.to[0] - 5) < 1e-9);
check("erro: travelMs até o alvo, flightMs inclui a casa a mais", l5 && l5.travelMs === 220 && l5.flightMs === 275);
CS.tick(720);
check("erro: impact na chegada ao alvo (não no fim do voo)", CS._scenes[0].impactAt === 720);
check("erro: alvo esquiva", CS.poseFor("m:id_9", 720 + 100).tilt > 0);
CS.reset();
CS.start({ ...ARCO, attack_id: "arc_6" }, 0); CS.tick(0);
CS.result({ ...ARCO, attack_id: "arc_6", hit: false, natural_fumble: true }, 1); CS.tick(180); CS.dieSettled({ die: "d20" }, 500);
const l6 = CS.tick(500).find(c => c.cmd === "launch");
check("fumble: to a meio caminho", l6 && l6.fumble === true && Math.abs(l6.to[0] - 2) < 1e-9);
check("fumble: travelMs = flightMs = metade", l6 && l6.travelMs === 110 && l6.flightMs === 110);
CS.tick(610);
check("fumble: impact no fim do voo curto", CS._scenes[0].impactAt === 610);
check("fumble: alvo NÃO esquiva (nem foi alcançado)", CS.poseFor("m:id_9", 660) === null);

console.log("\n[38] Projétil sem_dado (área): sem espera de dado, sem alvo, fecha sozinho");
CS.reset();
const BOMBA = { attack_id: "bmb_1", attacker_key: "p:id_1", target_key: null,
                attacker_pos: [0, 0], target_pos: [3, 0],
                projectile: { kind: "item", item_id: "bomba_incendiaria", item_emoji: "💣", area: true, area_raio: 1, sem_dado: true } };
CS.start(BOMBA, 0); CS.tick(0); CS.result({ ...BOMBA, hit: true }, 1);
CS.tick(180);
check("sem_dado: entra em GOLPE assim que o windup acaba, sem ESPERANDO_DADO", CS.phaseOf("bmb_1") === "GOLPE");
check("dieSettled ignora cena sem_dado", CS.dieSettled({ die: "d20" }, 200) === null);
check("launch de área com item_id/emoji/area_raio", (() => {
  const l = CS._ultimoLaunch; return l && l.kind === "item" && l.item_id === "bomba_incendiaria" && l.item_emoji === "💣" && l.area === true && l.area_raio === 1; })());
check("pendingFor nunca devolve cena de área", CS.pendingFor("m:id_9", 200) === null && CS.pendingFor(null, 200) === null);
const cmdsB = CS.tick(180 + 270);
const ib = cmdsB.find(c => c.cmd === "impact");
check("impact de área na chegada (3 casas × 90 = 270)", ib && ib.area === true && ib.area_raio === 1 && ib.targetPos[0] === 3);
CS.tick(180 + 270 + 260);
check("cena de área fecha após recuperar (não fica esperando hand-off)", CS.phaseOf("bmb_1") === null);

console.log("\n[39] Sem projectile no start → byte-idêntico (ranged de haste continua coice + impacto imediato)");
CS.reset();
CS.start({ ...ARCO, attack_id: "arc_7", projectile: undefined }, 0); CS.tick(0);
CS.result({ ...ARCO, attack_id: "arc_7", hit: true }, 1); CS.tick(180); CS.dieSettled({ die: "d20" }, 500);
const c7 = CS.tick(500);
check("sem projectile: nenhum launch", !c7.some(c => c.cmd === "launch"));
CS.tick(590);
check("sem projectile: impact no msOut do coice (90 ms)", CS._scenes[0].impactAt === 590);
CS.reset(); CS.configure({ cfg: { projectile: { enabled: false } } });
CS.start(ARCO, 0); CS.tick(0);
check("projectile.enabled=false: a cena ignora o campo", CS._scenes[0].projectile === null);
CS.configure({});
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_combat_scene.js`
Expected: `[35]` falha em "travelMs = ..." (`undefined`).

- [ ] **Step 3: Implementar no módulo**

(a) `DEFAULT_CFG` — acrescentar após `expireMs:  6000,`:

```js
    projectile: {
      enabled: true,
      msPerTile: { arrow: 55, bolt: 45, spear: 75, item: 90 },
      travelMinMs: 220, travelMaxMs: 900,
      missOvershootTiles: 1,
      fumbleFraction: 0.5,
    },
```

(b) `novaCena` — após o cálculo de `dir`/`melee` e antes de `const s = {`:

```js
    const pj = normalizarProjetil(msg.projectile);
    if (pj) melee = false;                         // projétil nunca é corpo a corpo
    const distCasas = (aPos && tPos) ? Math.max(Math.abs(tPos[0] - aPos[0]), Math.abs(tPos[1] - aPos[1])) : 1;
```
e dentro do objeto `s`, após `melee,`:
```js
      projectile: pj, distCasas,
      travelMs: pj ? travelMsDe(pj.kind, distCasas) : 0,
      launchAt: null,
```
e a função (antes de `novaCena`):
```js
  // Campo `projectile` do attack_feedback → dict normalizado ou null.
  // `enabled:false` no cfg ignora o campo (o servidor continua mandando).
  function normalizarProjetil(p) {
    if (!p || typeof p !== 'object' || !cfg.projectile || cfg.projectile.enabled === false) return null;
    const kind = ['arrow', 'bolt', 'spear', 'item'].includes(p.kind) ? p.kind : null;
    if (!kind) return null;
    return {
      kind, item_id: p.item_id || null, item_emoji: p.item_emoji || null,
      area: !!p.area, area_raio: Math.max(0, Number(p.area_raio) || 0), sem_dado: !!p.sem_dado,
    };
  }
  function travelMsDe(kind, distCasas) {
    const pc = cfg.projectile;
    const ms = Math.max(1, distCasas) * (pc.msPerTile[kind] || pc.msPerTile.arrow);
    return D(Math.max(pc.travelMinMs, Math.min(pc.travelMaxMs, ms)));
  }
```

(c) Entrada no `GOLPE` com lançamento — inserir após `function entrar(...)`:

```js
  // GOLPE = lançamento quando há projétil: emite `launch` com o destino já
  // resolvido (erro passa reto 1 casa além; natural 1 cai a meio caminho) e o
  // impacto fica para a CHEGADA (travelMs). Sem projétil, o GOLPE é o de sempre.
  function entrarGolpe(s, now, cmds) {
    entrar(s, 'GOLPE', now);
    if (!s.projectile) return;
    const pc = cfg.projectile, hit = !!(s.result && s.result.hit), fumble = !!(s.result && s.result.fumble);
    const from = s.aPos ? s.aPos.slice() : [0, 0];
    let to = s.tPos ? s.tPos.slice() : from.slice();
    let travelMs = s.travelMs, flightMs = s.travelMs;
    if (fumble) {
      to = [from[0] + (to[0] - from[0]) * pc.fumbleFraction, from[1] + (to[1] - from[1]) * pc.fumbleFraction];
      travelMs = flightMs = Math.round(s.travelMs * pc.fumbleFraction);
      s.travelMs = travelMs;                          // o impacto (sem esquiva) fecha no fim do voo curto
    } else if (!hit) {
      to = [to[0] + s.dir[0] * pc.missOvershootTiles, to[1] + s.dir[1] * pc.missOvershootTiles];
      flightMs = travelMs + Math.round(pc.missOvershootTiles * D(pc.msPerTile[s.projectile.kind] || pc.msPerTile.arrow));
    }
    s.launchAt = now;
    const c = {
      cmd: 'launch', id: s.id, attackerKey: s.attackerKey, targetKey: s.targetKey,
      kind: s.projectile.kind, item_id: s.projectile.item_id, item_emoji: s.projectile.item_emoji,
      from, to, dir: s.dir.slice(), travelMs, flightMs, hit, fumble,
      crit: !!(s.result && s.result.crit), area: s.projectile.area, area_raio: s.projectile.area_raio,
    };
    root.CombatScene && (root.CombatScene._ultimoLaunch = c);   // só para testes
    cmds.push(c);
  }
```

(d) `emitirImpacto` — acrescentar ao objeto `c`:
```js
      projectile: s.projectile ? s.projectile.kind : null,
      area: !!(s.projectile && s.projectile.area),
      area_raio: s.projectile ? s.projectile.area_raio : 0,
```

(e) `tick` — trocar os dois `entrar(s, 'GOLPE', now)` e adaptar a espera:
```js
        case 'ARMANDO':
          if (s.result && instantFn()) { irParaImpacto(s, now, cmds); break; }
          if (s.result && now - s.phaseAt >= D(cfg.windup.ms)) {
            if (s.dieAt != null || (s.projectile && s.projectile.sem_dado)) entrarGolpe(s, now, cmds);
            else entrar(s, 'ESPERANDO_DADO', now);
          }
          break;
        case 'ESPERANDO_DADO':
          if (!s.result) break;
          if (instantFn()) { irParaImpacto(s, now, cmds); break; }
          if (s.dieAt != null || (s.projectile && s.projectile.sem_dado) || now - s.resultAt >= cfg.waitDieMs)   // timeout: NÃO passa por D()
            entrarGolpe(s, now, cmds);
          break;
        case 'GOLPE': {
          const dur = s.projectile ? s.travelMs : (s.melee ? D(cfg.strike.ms) : D(cfg.ranged.msOut));
          if (now - s.phaseAt >= dur) irParaImpacto(s, now, cmds);
          break;
        }
```
e em `RECUPERANDO`, a linha do `finalizar`:
```js
            else if (s.handoffs > 0 || !(s.result && s.result.hit) || (s.projectile && s.projectile.area)) finalizar(s, cmds, now);
```

(f) `dieSettled` — acrescentar ao filtro: `&& !(x.projectile && x.projectile.sem_dado)`.

(g) `cenaParaHandoff` — primeira linha do laço: `if (s.done || s.targetKey == null || s.targetKey !== targetKey) continue;`.

(h) `poseAlvo` — na linha do erro: `if (!s.result.hit) { if (s.projectile && s.result.fumble) return null; return { dx: 0, dz: 0, tilt: cfg.dodge.angle * wave, tiltDir: d, base: s.tPos }; }`.

(i) O coice do atacante (`poseAtacante`, ramo `!s.melee`) já funciona: o `GOLPE` usa `ranged.msOut` para o recuo e `RECUPERANDO` o retorno — não muda.

- [ ] **Step 4: Rodar**

Run: `node tools/test_combat_scene.js`
Expected: `0 falharam` (≈235 checks; reporte a contagem). Os 204 anteriores intocados.

- [ ] **Step 5: Commit**

```bash
git add src/combatScene.js tools/test_combat_scene.js
git commit -m "feat(projeteis): CombatScene — GOLPE vira lancamento, impacto na chegada, area e sem_dado

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Config + `_receiveAttackFeedback` repassa `projectile`

**Files:**
- Modify: `src/visualConfig.js` (bloco `scene`, após `expireMs:  6000,`)
- Modify: `game.js` — `_receiveAttackFeedback`
- Modify: `tools/test_combat_scene.js` — seção `[33]`

- [ ] **Step 1: Checagens estáticas** — acrescentar ao final da seção `[33]`:

```js
check("visualConfig tem scene.projectile", /projectile:\s*\{/.test(vcSrc) && /msPerTile/.test(vcSrc));
check("_receiveAttackFeedback repassa msg.projectile", /projectile:\s*msg\.projectile/.test(gameSrc));
```

- [ ] **Step 2: `visualConfig.js`** — dentro de `scene: { ... }`, após `expireMs:  6000,`:

```js
        // Projéteis (frente B): tempos de voo por tipo, arcos e o que a
        // flecha faz ao errar/errar feio. Lido pela CombatScene e pelo render.
        projectile: {
          enabled: true,
          msPerTile: { arrow: 55, bolt: 45, spear: 75, item: 90 },
          travelMinMs: 220, travelMaxMs: 900,
          arc: { arrow: 0.25, arrowPerTile: 0.04, bolt: 0.08, spear: 0.35, item: 0.55 },
          launchY: 0.45, landY: 0.35,
          missOvershootTiles: 1,
          fumbleFraction: 0.5,
          stickMs: 900, hitLingerMs: 300,
          itemSpinPerSec: 2.5,
          areaBurst: { base: 18, perRadius: 8 },
        },
```

- [ ] **Step 3: `game.js`** — em `_receiveAttackFeedback`, o objeto `base`:

```js
    const base = {attack_id:id, attacker_key:_entityKeyById(msg.attacker_id), target_key:_entityKeyById(msg.target_id),
      attacker_pos:msg.attacker_pos, target_pos:msg.target_pos, projectile: msg.projectile || null};
```

- [ ] **Step 4: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: 0 falharam.

- [ ] **Step 5: Commit**

```bash
git add src/visualConfig.js game.js tools/test_combat_scene.js
git commit -m "feat(projeteis): config scene.projectile + attack_feedback repassa o campo a cena

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: `game.js` — render dos projéteis

**Files:**
- Modify: `game.js` — novo bloco antes de `function _executarComandoCena(c){`; ramo `launch` em `_executarComandoCena`; `_tickCombatScene`; `dispose3D`; `init3D`
- Modify: `tools/test_combat_scene.js` — seção `[33]`

- [ ] **Step 1: Checagens estáticas** — acrescentar à seção `[33]`:

```js
check("game.js tem o render de projéteis", ["function _projetilLancar(", "function _projetilUpdate3D(", "function _projetilDispose3D(", "function _projetilTickTodos("].every(s => gameSrc.includes(s)));
check("comando launch é consumido", gameSrc.includes("c.cmd === 'launch'"));
check("tick anima os projéteis", gameSrc.includes("_projetilTickTodos(now)"));
check("dispose3D limpa os projéteis", (() => { const i = gameSrc.indexOf("\nfunction dispose3D("); return i > 0 && gameSrc.slice(i, i + 1500).includes("_projetilLimparTodos()"); })());
```

- [ ] **Step 2: O módulo de render** — inserir antes de `function _executarComandoCena(c){`:

```js
// ── Projéteis (frente B) ───────────────────────────────────────────────────────
// Um voo por comando `launch` da CombatScene. Objeto de cena independente (não
// é filho do peão), materiais PRÓPRIOS (nunca os clones _sceneMats do peão),
// posições vindas do próprio comando (nunca de userData.gridX). Família dos
// efeitos _bolaFogo*: build/update/dispose + lista + tick no laço 3D.
const _projeteis = [];
let _projetilGeo = null;   // geometrias/materiais base por tipo, criados uma vez

function _projetilCfg(){ return VC.feedback?.combat?.scene?.projectile || {}; }

function _projetilBases(T){
  if(_projetilGeo) return _projetilGeo;
  const madeira = new T.MeshStandardMaterial({ color: 0x5a3a1e, roughness: .8 });
  const aco     = new T.MeshStandardMaterial({ color: 0x9aa3ad, roughness: .35, metalness: .7 });
  const pena    = new T.MeshStandardMaterial({ color: 0xe8e2d0, roughness: .9, side: T.DoubleSide });
  const mk = (comp, raio, ponta, empenas) => {
    const g = new T.Group();
    const haste = new T.Mesh(new T.CylinderGeometry(raio, raio, comp, 6), madeira);
    haste.rotation.x = Math.PI / 2;                       // eixo Z = direção do voo
    g.add(haste);
    const tip = new T.Mesh(new T.ConeGeometry(raio * 2.4, ponta, 6), aco);
    tip.rotation.x = Math.PI / 2; tip.position.z = comp / 2 + ponta / 2; g.add(tip);
    for(let i = 0; i < empenas; i++){
      const e = new T.Mesh(new T.PlaneGeometry(0.08, 0.05), pena);
      e.position.z = -comp / 2 + 0.05; e.rotation.z = i * Math.PI / 2; g.add(e);
    }
    g.userData.comp = comp;
    return g;
  };
  _projetilGeo = {
    arrow: mk(0.55, 0.012, 0.06, 2),
    bolt:  mk(0.35, 0.018, 0.06, 1),
    spear: mk(0.95, 0.016, 0.10, 0),
    mats: [madeira, aco, pena],
  };
  return _projetilGeo;
}

function _projetilSpriteItem(T, itemId, emoji){
  const cv = document.createElement('canvas'); cv.width = cv.height = 64;
  const c2 = cv.getContext('2d');
  c2.font = '48px serif'; c2.textAlign = 'center'; c2.textBaseline = 'middle';
  c2.fillText(emoji || '🧪', 32, 36);
  const tex = new T.CanvasTexture(cv); tex._owned = true;
  const mat = new T.SpriteMaterial({ map: tex, transparent: true, depthWrite: false });
  const spr = new T.Sprite(mat); spr.scale.set(0.35, 0.35, 0.35);
  if(itemId){
    // PNG real do item quando existe; falha (404/rede) mantém o emoji.
    new T.TextureLoader().load(_assetURL(`assets/itens/${itemId}.png`), png => {
      if(!spr.parent) { png.dispose(); return; }        // voo já acabou
      png._owned = true; mat.map = png; mat.needsUpdate = true; tex.dispose();
    }, undefined, () => {});
  }
  return spr;
}

function _projetilLancar(c){
  if(!g3 || !g3.scene || !window.THREE) return;
  const pc = _projetilCfg();
  if(pc.enabled === false) return;
  if(!(c.flightMs >= 20)) return;                       // instant/fast extremo: sem voo
  const T = g3.T;
  const kind = c.kind;
  let obj;
  if(kind === 'item') obj = _projetilSpriteItem(T, c.item_id, c.item_emoji);
  else obj = _projetilBases(T)[kind === 'bolt' ? 'bolt' : kind === 'spear' ? 'spear' : 'arrow'].clone();
  const dist = Math.max(1, Math.hypot(c.to[0] - c.from[0], c.to[1] - c.from[1]));
  const arcCfg = pc.arc || {};
  const arco = kind === 'arrow' ? (arcCfg.arrow ?? .25) + (arcCfg.arrowPerTile ?? .04) * dist
             : kind === 'bolt' ? (arcCfg.bolt ?? .08) : kind === 'spear' ? (arcCfg.spear ?? .35) : (arcCfg.item ?? .55);
  const anim = {
    id: c.id, kind, obj, hit: !!c.hit, fumble: !!c.fumble, area: !!c.area, area_raio: c.area_raio || 0,
    from: [c.from[0], c.from[1]], to: [c.to[0], c.to[1]],
    y0: pc.launchY ?? .45, y1: (!c.hit || c.fumble) ? 0.02 : (pc.landY ?? .35), arco,
    start: performance.now(), flightMs: c.flightMs, travelMs: c.travelMs,
    impactAt: performance.now() + c.travelMs,
    lingerMs: (!c.hit || c.fumble) ? (pc.stickMs ?? 900) : (pc.hitLingerMs ?? 300),
    spin: (pc.itemSpinPerSec ?? 2.5) * Math.PI * 2,
    pousado: false, quebrado: false, ring: null,
  };
  obj.position.set(anim.from[0], anim.y0, anim.from[1]);
  g3.scene.add(obj);
  _projeteis.push(anim);
}

function _projetilPos(anim, u){
  const x = anim.from[0] + (anim.to[0] - anim.from[0]) * u;
  const z = anim.from[1] + (anim.to[1] - anim.from[1]) * u;
  const y = anim.y0 + (anim.y1 - anim.y0) * u + 4 * anim.arco * u * (1 - u);
  return [x, y, z];
}

function _projetilQuebrar(anim, now){
  if(anim.quebrado || !g3) return;
  anim.quebrado = true;
  const T = g3.T, pc = _projetilCfg();
  const [x, y, z] = _projetilPos(anim, 1);
  let cor = 0xbfbfbf, n = 14;
  if(anim.area){
    cor = 0xff8a32;
    n = (pc.areaBurst?.base ?? 18) + (pc.areaBurst?.perRadius ?? 8) * anim.area_raio;
    // Anel no chão que expande e desvanece (como o anel de derrota).
    const mat = new T.MeshBasicMaterial({ color: 0xffb060, transparent: true, opacity: .8, depthWrite: false, blending: T.AdditiveBlending, side: T.DoubleSide });
    const ring = new T.Mesh(new T.TorusGeometry(.35, .03, 8, 32), mat);
    ring.rotation.x = Math.PI / 2; ring.position.set(x, .03, z); ring.renderOrder = 135;
    g3.scene.add(ring); anim.ring = { mesh: ring, start: now, raio: Math.max(1, anim.area_raio) };
  } else if(anim.kind === 'item'){
    cor = 0xff8a32;
  }
  _spawnBurstParticles(T, g3.scene, { x, y: Math.max(.1, y), z }, cor, n);
}

function _projetilUpdate3D(anim, now){
  const el = now - anim.start;
  const u = Math.min(1, el / Math.max(1, anim.flightMs));
  const [x, y, z] = _projetilPos(anim, u);
  const obj = anim.obj;
  if(u < 1){
    obj.position.set(x, y, z);
    if(anim.kind === 'item'){
      obj.material.rotation = (el / 1000) * anim.spin;
    } else {
      const [x2, y2, z2] = _projetilPos(anim, Math.min(1, u + 0.02));
      obj.lookAt(x2, y2, z2);                             // eixo Z do grupo = ponta
    }
    return;
  }
  if(!anim.pousado){
    anim.pousado = true; anim.pousoAt = now;
    obj.position.set(x, y, z);
    if(anim.kind === 'item') _projetilQuebrar(anim, now);
    else if(!anim.hit || anim.fumble){ obj.rotation.set(0, obj.rotation.y, 0); obj.rotateX(-Math.PI * .19); }   // cravada ~35°
  }
  if(anim.kind === 'item') obj.visible = false;
  // Cravada/caída: some no fim do linger (seta acertada some junto com a reação).
  const p = Math.min(1, (now - anim.pousoAt) / Math.max(1, anim.lingerMs));
  obj.traverse(o => { if(o.material && o.material.opacity !== undefined && !o.material.userData._projOwned){ o.material = o.material.clone(); o.material.transparent = true; o.material.userData._projOwned = true; } });
  obj.traverse(o => { if(o.material && o.material.userData._projOwned) o.material.opacity = 1 - p; });
  if(anim.ring){
    const q = Math.min(1, (now - anim.ring.start) / 400);
    anim.ring.mesh.scale.setScalar(1 + q * anim.ring.raio * 2.2);
    anim.ring.mesh.material.opacity = .8 * (1 - q);
  }
  anim.fim = (p >= 1) && (!anim.ring || now - anim.ring.start >= 400);
}

function _projetilDispose3D(anim){
  if(anim.obj){
    if(anim.obj.parent) anim.obj.parent.remove(anim.obj);
    anim.obj.traverse(o => {
      if(o.material && o.material.userData && o.material.userData._projOwned) o.material.dispose();
      if(o.isSprite && o.material){ if(o.material.map && o.material.map._owned) o.material.map.dispose(); o.material.dispose(); }
    });
  }
  if(anim.ring && anim.ring.mesh){
    if(anim.ring.mesh.parent) anim.ring.mesh.parent.remove(anim.ring.mesh);
    anim.ring.mesh.geometry.dispose(); anim.ring.mesh.material.dispose();
  }
}

function _projetilTickTodos(now){
  for(let i = _projeteis.length - 1; i >= 0; i--){
    const anim = _projeteis[i];
    _projetilUpdate3D(anim, now);
    if(anim.fim){ _projetilDispose3D(anim); _projeteis.splice(i, 1); }
  }
}

function _projetilLimparTodos(){
  for(const anim of _projeteis) _projetilDispose3D(anim);
  _projeteis.length = 0;
  if(_projetilGeo){
    for(const k of ['arrow', 'bolt', 'spear']) _projetilGeo[k].traverse(o => { if(o.geometry) o.geometry.dispose(); });
    for(const m of _projetilGeo.mats) m.dispose();
    _projetilGeo = null;
  }
}
```

- [ ] **Step 3: Consumir `launch`** — em `_executarComandoCena`, logo após `if(!c) return;`:

```js
  if(c.cmd === 'launch'){ _projetilLancar(c); return; }
```

- [ ] **Step 4: Tick** — em `_tickCombatScene`:

```js
function _tickCombatScene(now){
  if(!window.CombatScene) return;
  for(const c of CombatScene.tick(now)) _executarComandoCena(c);
  if(_projeteis.length) _projetilTickTodos(now);
}
```

- [ ] **Step 5: Limpeza** — em `dispose3D`, logo após `if(window.CombatScene) CombatScene.reset();`, inserir `_projetilLimparTodos();`. Em `init3D`, logo após `if(window.CombatScene) CombatScene.reset();` (o da `init3D`), inserir `_projetilLimparTodos();`.

- [ ] **Step 6: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: 0 falharam.

- [ ] **Step 7: Commit**

```bash
git add game.js tools/test_combat_scene.js
git commit -m "feat(projeteis): render 3D — seta/virote/lanca procedurais e item em PNG voando em arco

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: `game.js` — portão dos números de área

**Files:**
- Modify: `game.js` — nova função ao lado de `_bolaFogoFeedbackStartAt`; `_detectHpChanges`
- Modify: `tools/test_combat_scene.js` — seção `[33]`

- [ ] **Step 1: Checagem estática** — acrescentar à seção `[33]`:

```js
check("diff de HP consulta _projetilFeedbackStartAt", corpoDaFuncao("_detectHpChanges").includes("_projetilFeedbackStartAt(entry)"));
```

- [ ] **Step 2: A função** — inserir logo após `function _bolaFogoFeedbackStartAt(entry){ ... }`:

```js
// Irmã do portão da bola de fogo: quem está no raio de um arremesso de ÁREA em
// voo só mostra o número quando o frasco chega (os saves rolam durante o voo).
function _projetilFeedbackStartAt(entry){
  if(!entry || !Array.isArray(entry.pos)) return null;
  const px = Number(entry.pos[0]), py = Number(entry.pos[1]);
  if(!Number.isFinite(px) || !Number.isFinite(py)) return null;
  let liberarEm = null;
  for(const anim of _projeteis){
    if(!anim.area) continue;
    const d = Math.max(Math.abs(anim.to[0] - px), Math.abs(anim.to[1] - py));
    if(d > anim.area_raio) continue;
    liberarEm = liberarEm == null ? anim.impactAt : Math.max(liberarEm, anim.impactAt);
  }
  return liberarEm;
}
```

- [ ] **Step 3: O portão** — em `_detectHpChanges`, trocar

```js
        const fireStart = _bolaFogoFeedbackStartAt(entry);
```
por
```js
        const fireStartBola = _bolaFogoFeedbackStartAt(entry);
        const fireStartProj = _projetilFeedbackStartAt(entry);
        const fireStart = fireStartBola == null ? fireStartProj
          : fireStartProj == null ? fireStartBola : Math.max(fireStartBola, fireStartProj);
```

- [ ] **Step 4: Verificar**

Run: `node --check game.js && node tools/test_combat_scene.js`
Expected: 0 falharam.

- [ ] **Step 5: Commit**

```bash
git add game.js tools/test_combat_scene.js
git commit -m "feat(projeteis): numeros de dano de area esperam a chegada do frasco

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Prova no navegador

**Files:** nenhum (verificação; correções em commit próprio).

- [ ] **Step 1:** subir o servidor do worktree em porta própria (`LFH_PORT=8766 python server.py` em background), abrir `http://localhost:8766/index.html`, Ctrl+F5; `typeof CombatScene.cfg().projectile` → `"object"`.
- [ ] **Step 2:** criar sala, escolher **Ladino** (Luccas) — ou qualquer classe — e, na cidade, comprar `arco_curto` no ferreiro e equipar (`GS.send({type:'buy_item', shop_id:'ferreiro_weapon', item_id:'arco_curto'})` + equipar pela ficha), e um `frasco_oleo` + `bomba_incendiaria` no mercador; masmorra `amostra.json` (goblin a 1 casa). Afastar-se 3 casas do goblin (`GS.move`), `GS.setTurnTimer(false)`.
- [ ] **Step 3: Acerto com flecha** — recorder: `setInterval` 50 ms gravando `CombatScene._scenes.map(s=>s.phase)`, `_projeteis.length`, `_projeteis[0]?.obj.position` e o `__fbLog` de `_spawnCombatFeedback` (wrapper como na frente A). `GS.send({type:'attack', target_id})`. Esperado: `launch` no assentamento do dado; a posição do projétil percorre `from→to` em `travelMs`; o número sai em `impactAt` (= chegada), não antes. Screenshot no meio do voo.
- [ ] **Step 4: Erro** — repetir até errar: o projétil continua 1 casa além, fica cravado e some; esquiva na passagem.
- [ ] **Step 5: Frasco no alvo** — `GS.send({type:'throw_item', item_id:'frasco_oleo', target_id})`: PNG girando, quebra com partículas laranja, número na chegada.
- [ ] **Step 6: Bomba de área** — `GS.send({type:'throw_item', item_id:'bomba_incendiaria', tx, ty})` numa casa com o goblin no raio: anel + burst; o número do goblin só aparece na chegada (checar `__fbLog` vs `impactAt`).
- [ ] **Step 7: Ataque do goblin arqueiro** — se possível (masmorra com `goblin_arqueiro`, ex. `Arena`): a flecha do monstro voa até o herói.
- [ ] **Step 8: `instant`** — painel ⚙️ velocidade instantânea: sem voo, impacto imediato, sem erro no console.
- [ ] **Step 9:** console sem erros; FPS igual fora do voo. Parar o servidor (`taskkill`).
- [ ] **Step 10: Commit de ajustes (se houver)** — `fix(projeteis): ajustes da prova em navegador`.

---

### Task 8: Documentação

**Files:**
- Modify: `CLAUDE.md` — bloco `>` novo após o bloco "Animação de combate híbrida (3D)".

- [ ] **Step 1: Bloco**

```markdown
> **Projéteis no 3D (frente B):** flecha/virote/lança (malha procedural orientada pela
> trajetória) e itens arremessados (PNG do item girando; emoji em canvas como fallback)
> **voam do atacante ao alvo quando o d20 assenta** e o impacto acontece **na chegada**.
> **Servidor:** `_projetil_de(defn, monstro=False)` (module-level, ao lado de `RANGED_AMMO`)
> deriva `{"kind": arrow|bolt|spear}` — herói pela arma (`_PROJETIL_POR_ARMA` / `ammo` do
> editor; arma de haste com `range` como chicote/alabarda NÃO tem projétil), monstro/servo
> por `projectile` explícito no ataque ou `range≥2` + `perfurante` (kobold besteiro declara
> `bolt`; a lança do kobold, `spear`). Vai como campo opcional `projectile` no
> `attack_feedback start` (`_emitir_feedback_ataque` descarta `None`). **`handle_throw_item`
> passou a emitir `attack_feedback`**: `ataque_alvo` = start antes do d20 + result; `area` =
> alvo sintético `{id:None, pos:[cx,cy]}` com `area`/`area_raio`/`sem_dado` e result
> imediato. `handle_arremesso_lanca` do herói é **código morto** (sem despacho) — fora.
> **Cena (`src/combatScene.js`):** `projectile` normalizado na cena (`enabled:false` no cfg
> ignora o campo), `melee=false`, `travelMs = clamp(dist×msPerTile[kind])` (passa pela
> `duration` — é animação, não timeout); `entrarGolpe` emite o comando **`launch`**
> `{kind,item_id,item_emoji,from,to,dir,travelMs,flightMs,hit,fumble,crit,area,area_raio}` e
> o `GOLPE` dura `travelMs` → impacto na chegada; erro estende `to` 1 casa além (`flightMs` >
> `travelMs`, impacto na passagem pelo alvo); fumble encurta `to` a meio caminho e o alvo
> **não** esquiva; `sem_dado` pula `ESPERANDO_DADO` e `dieSettled` ignora a cena (senão
> roubaria o d20 de um save); cena de área não tem `targetKey` (`cenaParaHandoff` a ignora) e
> fecha sozinha após recuperar. `impact` carrega `projectile`/`area`/`area_raio`. Sem
> `projectile` → byte-idêntico. **Render (`game.js`):** `_projeteis` +
> `_projetilLancar/_projetilUpdate3D/_projetilDispose3D/_projetilTickTodos/_projetilLimparTodos`
> (família `_bolaFogo*`; parábola `from→to`, `lookAt` na tangente; PNG via `TextureLoader`
> trocando o mapa do sprite de emoji quando chega; cravada 35° no erro; burst + anel na área);
> tick em `_tickCombatScene`; limpeza em `dispose3D`/`init3D`. Números de área esperam a
> chegada por `_projetilFeedbackStartAt` (irmã de `_bolaFogoFeedbackStartAt`; o diff de HP usa
> o mais tardio dos dois). Config em `VC.feedback.combat.scene.projectile`. Testes:
> `tools/test_projeteis.py` (servidor), `tools/test_combat_scene.js` (`[35]`–`[39]` + `[33]`).
> Spec/plano em `docs/superpowers/{specs,plans}/2026-09-12-projeteis-3d*`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: projeteis no 3D (frente B) no CLAUDE.md

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
