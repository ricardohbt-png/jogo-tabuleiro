# Modo Mestre Jogador — Fase A — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que um humano assuma o papel de mestre no lobby e controle os monstros já colocados no tabuleiro em 3 modos (Auto/Semi/Manual), com visão sem névoa — sem alterar nenhuma mecânica de herói e mantendo uma partida sem-mestre byte-idêntica ao comportamento atual.

**Architecture:** Servidor (`server.py`) autoritativo: o mestre é rastreado por `self.master_pid`/`self.master_name` (NÃO fica em `self.players` durante o jogo, então todo laço que itera heróis permanece intocado). Cada monstro ganha `control_mode` lido via `.get(...,"auto")`. Um único ponto de decisão no ramo de monstro de `_activate_initiative_actor` despacha Auto/Semi/Manual. O modo Manual usa um `asyncio.Event` (padrão do Último Esforço) + timer de segurança. A visão sem névoa é quase toda no cliente (o servidor já faz broadcast do estado completo a todos).

**Tech Stack:** Python 3 + `websockets` (servidor headless, testes `tools/test_*.py`), Vanilla JS (`src/gameState.js` lógica/WebSocket, `game.js` render). Sem bundler, sem framework de teste JS.

**Convenção deste plano:** o `server.py` é editado em paralelo pelo usuário — os números de linha DERIVAM. Localize cada ponto de edição pela **assinatura da função** e pela **string âncora única** citada, não por número de linha. Nunca use `git add server.py` cego (varre WIP do usuário): `git add` apenas os arquivos que você tocou, e confira `git status`/`git diff --staged` antes de cada commit.

---

## Estrutura de arquivos

- **Modificar** `server.py`:
  - `__init__` do `GameRoom` — novos campos de estado do mestre.
  - `add_player` — teto 6 heróis + 1 mestre.
  - `select_class` — recusa mestre.
  - novo `claim_role` — assumir/soltar o papel.
  - `broadcast_lobby` — `can_start` ignora mestre + expõe `master_pid`.
  - `start_game` — extrai o mestre antes de reconstruir `full_players`.
  - `broadcast_city_state` + `push_state` — expõem `master_pid`.
  - `_get_monster_primary_target` — override de alvo do modo Semi.
  - `_activate_initiative_actor` (ramo `kind=="monster"`) — despacho Auto/Semi/Manual.
  - novos helpers: `_mestre_ativo`, `_master_manual_window`, timer de segurança do manual.
  - novos handlers: `handle_mestre_set_modo`, `handle_mestre_set_alvo`, `handle_mestre_mover_monstro`, `handle_mestre_atacar_monstro`, `handle_mestre_encerrar_monstro`.
  - `handler(ws)` (roteador) — novas mensagens + `rejoin` do mestre + disconnect.
- **Criar** `tools/test_modo_mestre.py` — testes de servidor.
- **Modificar** `game.js` — toggle de mestre no lobby, detecção de papel, HUD do mestre, render sem névoa.
- **Modificar** `src/gameState.js` — envio das mensagens `claim_role`/`mestre_*`, getter `isMaster`.

Nenhuma mecânica de herói é tocada. Todos os caminhos novos são no-op quando `self.master_pid is None`.

---

## Task 1: Estado do mestre + assumir/soltar papel no lobby

**Files:**
- Modify: `server.py` (`GameRoom.__init__`, `add_player`, `select_class`, novo `claim_role`, `broadcast_lobby`, roteador `handler`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_modo_mestre.py` com o harness padrão do projeto (espelha `tools/test_guilda.py`):

```python
"""Modo Mestre Jogador — Fase A. Roda da raiz: python tools/test_modo_mestre.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

class FakeWS:
    """WebSocket falso: .send é um no-op assíncrono (add_player usa ws.send no reject)."""
    async def send(self, *a, **k): pass

def lobby_room():
    """Sala em fase de lobby com send_to/broadcast capturados."""
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_lobby = noop; r.broadcast_city_state = noop; r.send_to = cap_send
    r._errs = errs
    r.phase = "lobby"
    return r

async def add(r, pid, name):
    """Adiciona um jogador sem depender de websocket real."""
    r.connections[pid] = object()   # sentinela: 'conectado'
    r.players[pid] = {"id": pid, "name": name, "class_id": None,
                      "ready": False, "connected": True, "slot": len(r.players)}
    if not r.host_pid: r.host_pid = pid

async def main():
    S.CHARACTERS_IN_USE.clear()

    print("\n[1] claim_role cria e solta o mestre")
    r = lobby_room()
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    check("m1 é mestre", r.players["m1"].get("is_master") is True)
    check("mestre sem classe", r.players["m1"]["class_id"] is None)
    check("mestre ready", r.players["m1"]["ready"] is True)
    # segundo mestre é recusado
    await add(r, "m2", "Intruso")
    await r.claim_role("m2", "master")
    check("2º mestre recusado", r.players["m2"].get("is_master") is not True)
    check("erro de 2º mestre emitido", any("mestre" in e.lower() for e in r._errs))
    # soltar o papel
    await r.claim_role("m1", "hero")
    check("m1 deixou de ser mestre", not r.players["m1"].get("is_master"))
    check("m1 volta a não-ready", r.players["m1"]["ready"] is False)

    print("\n[2] mestre não escolhe classe")
    r = lobby_room()
    await add(r, "m1", "Mestre"); await r.claim_role("m1", "master")
    r._errs.clear()
    await r.select_class("m1", "warrior")
    check("select_class recusado p/ mestre", r.players["m1"]["class_id"] is None)
    check("erro emitido", len(r._errs) >= 1)

    print("\n[3] can_start ignora o mestre")
    r = lobby_room()
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    await r.select_class("h1", "warrior")
    check("can_start com herói pronto + mestre", r._can_start() is True)

    print("\n[4] teto 6 heróis + 1 mestre")
    r = lobby_room()
    for i in range(6):
        ok = await r.add_player(FakeWS(), f"h{i}", f"Heroi{i}")
        check(f"herói {i} entra", ok is True)
    ok7 = await r.add_player(FakeWS(), "h6", "Setimo")
    check("7º herói barrado", ok7 is False)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute 'claim_role'` (e/ou `_can_start`).

- [ ] **Step 3: Implementar**

**3a.** No `GameRoom.__init__`, junto de `self.players = {}` (âncora: `self.players = {}       # pid -> player dict`), adicione:

```python
        self.master_pid = None     # pid do mestre humano (Modo Mestre) ou None
        self.master_name = None    # nome do mestre (p/ rejoin)
```

**3b.** Em `add_player`, o teto atual é (âncora `if len(self.players) >= 6:`):

```python
    async def add_player(self, ws, pid, name):
        if len(self.players) >= 6:
            await ws.send(json.dumps({"type": "error", "msg": "Sala cheia (máximo 6 jogadores)."}))
            return False
```

Troque a condição para contar apenas heróis (não-mestre):

```python
    async def add_player(self, ws, pid, name):
        heroes = sum(1 for p in self.players.values() if not p.get("is_master"))
        if heroes >= 6:
            await ws.send(json.dumps({"type": "error", "msg": "Sala cheia (máximo 6 heróis)."}))
            return False
```

**3c.** No topo de `select_class` (âncora `async def select_class(self, pid, cls_id):`), antes de `if cls_id not in CLASSES:`, adicione a guarda de mestre:

```python
    async def select_class(self, pid, cls_id):
        if self.players.get(pid, {}).get("is_master"):
            await self.send_to(pid, {"type": "error",
                "msg": "O mestre não escolhe classe. Solte o papel de mestre primeiro."})
            return
        if cls_id not in CLASSES:
            return
```

**3d.** Adicione o método `claim_role` logo após `select_class`:

```python
    async def claim_role(self, pid, role):
        """Lobby: um jogador assume ('master') ou solta ('hero') o papel de mestre."""
        if self.phase != "lobby":
            return
        p = self.players.get(pid)
        if not p:
            return
        if role == "master":
            outro = next((q for q in self.players.values()
                          if q.get("is_master") and q["id"] != pid), None)
            if outro:
                await self.send_to(pid, {"type": "error",
                    "msg": "Já existe um mestre nesta sala."})
                return
            # libera a classe anterior deste jogador, se tinha
            prev = p.get("class_id")
            if prev and CHARACTERS_IN_USE.get(prev) == self.code:
                del CHARACTERS_IN_USE[prev]
            p["is_master"] = True
            p["class_id"] = None
            p["ready"] = True
            self.master_pid = pid
            self.master_name = p["name"]
        else:  # "hero"
            p["is_master"] = False
            p["ready"] = False
            if self.master_pid == pid:
                self.master_pid = None
                self.master_name = None
        await self.broadcast_lobby()
```

**3e.** Extraia a regra de `can_start` para um método (para o teste e para reutilizar) e faça-a ignorar o mestre. Em `broadcast_lobby`, o valor atual é (âncora `"can_start": (`):

```python
            "can_start": (
                len(self.players) >= 1 and
                all(p["class_id"] for p in self.players.values())
            ),
```

Substitua por uma chamada a um método novo:

```python
            "can_start": self._can_start(),
            "master_pid": self.master_pid,
```

E adicione o método (logo acima de `broadcast_lobby`):

```python
    def _can_start(self):
        heroes = [p for p in self.players.values() if not p.get("is_master")]
        return len(heroes) >= 1 and all(p["class_id"] for p in heroes)
```

**3f.** No roteador `handler(ws)`, junto de `elif t == "select_class":` (âncora dessa linha), adicione:

```python
                elif t == "claim_role":
                    if room: await room.claim_role(pid, msg.get("role"))
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS nas seções [1]–[4].

- [ ] **Step 5: Regressão de sanidade dos testes existentes de lobby/guilda**

Run: `python tools/test_guilda.py`
Expected: PASS (mudanças não afetam guilda).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): assento de mestre no lobby (claim_role, cap 6+1, can_start)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: `start_game` extrai o mestre; `master_pid` nos payloads

**Files:**
- Modify: `server.py` (`start_game`, `broadcast_city_state`, `push_state`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()` de `tools/test_modo_mestre.py`, antes do print final:

```python
    print("\n[5] start_game extrai o mestre de self.players")
    r = lobby_room()
    # captura o payload do city_state
    cap = {}
    async def cap_city2():
        cap["master_pid"] = getattr(r, "master_pid", None)
    r.broadcast_city_state = cap_city2
    await add(r, "h1", "Victor"); await add(r, "m1", "Mestre")
    await r.claim_role("m1", "master")
    await r.select_class("h1", "warrior")
    r.host_pid = "h1"
    await r.start_game("h1")
    check("mestre fora de self.players", "m1" not in r.players)
    check("herói continua em self.players", "h1" in r.players)
    check("master_pid preservado", r.master_pid == "m1")
    check("master_name preservado", r.master_name == "Mestre")
    check("player_order sem o mestre", "m1" not in r.player_order)
    check("conexão do mestre preservada", "m1" in r.connections)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em [5] — `start_game` recusa (todos precisam de classe) ou `make_player` quebra com o mestre.

- [ ] **Step 3: Implementar**

Em `start_game`, o começo é (âncora `if not all(p["class_id"] for p in self.players.values()):`):

```python
        if not all(p["class_id"] for p in self.players.values()):
            await self.send_to(pid, {"type": "error", "msg": "Todos devem escolher uma classe."})
            return
        for pp in self.players.values():
            if pp["class_id"] in ("mage", "cleric") and len(pp.get("magias_conhecidas", [])) < 2:
                ...
        # Build full player states
        full_players = {}
        for slot, (pid2, p) in enumerate(self.players.items()):
            novo = make_player(pid2, p["name"], p["class_id"], slot)
            ...
        self.players = full_players
        self.player_order = list(full_players.keys())
```

Substitua o começo por uma versão que separa o mestre. Troque as duas validações e o laço de build:

```python
        heroes = {pid2: p for pid2, p in self.players.items() if not p.get("is_master")}
        master_entry = next((p for p in self.players.values() if p.get("is_master")), None)
        if not all(p["class_id"] for p in heroes.values()):
            await self.send_to(pid, {"type": "error", "msg": "Todos os heróis devem escolher uma classe."})
            return
        for pp in heroes.values():
            if pp["class_id"] in ("mage", "cleric") and len(pp.get("magias_conhecidas", [])) < 2:
                await self.send_to(pid, {"type": "error",
                    "msg": "Magos e clérigos devem escolher 2 magias antes de iniciar."}); return

        # Build full player states — SOMENTE heróis; o mestre não vira peão.
        full_players = {}
        for slot, (pid2, p) in enumerate(heroes.items()):
            novo = make_player(pid2, p["name"], p["class_id"], slot)
            novo["magias_conhecidas"] = list(p.get("magias_conhecidas", []))
            apply_guild_save(novo)
            full_players[pid2] = novo
        self.players = full_players
        self.player_order = list(full_players.keys())
        if master_entry:
            self.master_pid = master_entry["id"]
            self.master_name = master_entry["name"]
```

> `self.connections` não é tocado — a conexão do mestre continua lá, então os broadcasts o alcançam.

**3b.** Exponha `master_pid` nos dois payloads em jogo. Em `broadcast_city_state`, dentro do dict `{"type": "city_state", ...}` (âncora `"type": "city_state",`), adicione a chave:

```python
            "type": "city_state",
            "master_pid": self.master_pid,
```

Em `push_state`, dentro do dict `{"type": "game_state", ...}` (âncora `"type": "game_state",`), adicione:

```python
            "type": "game_state",
            "master_pid": self.master_pid,
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [5].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): start_game separa o mestre dos herois + master_pid nos payloads

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Modo de controle nos monstros + handlers de modo/alvo + `_mestre_ativo`

**Files:**
- Modify: `server.py` (novos `_mestre_ativo`, `handle_mestre_set_modo`, `handle_mestre_set_alvo`, roteador)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()`:

```python
    print("\n[6] modo de controle e alvo dos monstros")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    r.monsters = {"g1": {"id": "g1", "hp": 8, "pos": [2, 2]},
                  "g2": {"id": "g2", "hp": 8, "pos": [3, 3]}}
    check("_mestre_ativo True", r._mestre_ativo() is True)
    await r.handle_mestre_set_modo("m1", ["g1", "g2"], "semi")
    check("g1 semi", r.monsters["g1"]["control_mode"] == "semi")
    check("g2 semi", r.monsters["g2"]["control_mode"] == "semi")
    await r.handle_mestre_set_alvo("m1", ["g1"], "h1")
    check("g1 alvo h1", r.monsters["g1"]["master_target_id"] == "h1")
    # não-mestre é recusado
    r._errs.clear()
    await r.handle_mestre_set_modo("h1", ["g1"], "manual")
    check("não-mestre recusado", r.monsters["g1"]["control_mode"] == "semi")
    # mestre desconectado → _mestre_ativo False
    del r.connections["m1"]
    check("_mestre_ativo False sem conexão", r._mestre_ativo() is False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em [6] — `_mestre_ativo`/`handle_mestre_set_modo` não existem.

- [ ] **Step 3: Implementar**

Adicione estes métodos ao `GameRoom` (coloque-os perto de `handle_mover_animado`, para agrupar o controle manual de entidades):

```python
    def _mestre_ativo(self):
        """True se há um mestre humano CONECTADO. Quando False, todo monstro é
        tratado como 'auto' (partida idêntica à do jogo sem mestre)."""
        return bool(self.master_pid) and self.master_pid in self.connections

    async def handle_mestre_set_modo(self, pid, monster_ids, modo):
        """Mestre troca o modo de controle de 1+ monstros (Seleção em Lote)."""
        if pid != self.master_pid:
            return
        if modo not in ("auto", "semi", "manual"):
            return
        for mid in (monster_ids or []):
            m = self.monsters.get(mid)
            if m and m["hp"] > 0:
                m["control_mode"] = modo
                if modo != "semi":
                    m.pop("master_target_id", None)
        await self.push_state()

    async def handle_mestre_set_alvo(self, pid, monster_ids, target_id):
        """Mestre atribui um alvo (herói) a 1+ monstros em modo Semi."""
        if pid != self.master_pid:
            return
        for mid in (monster_ids or []):
            m = self.monsters.get(mid)
            if m and m["hp"] > 0:
                m["master_target_id"] = target_id
        await self.push_state()
```

No roteador `handler`, junto do bloco `claim_role` da Task 1:

```python
                elif t == "mestre_set_modo":
                    if room: await room.handle_mestre_set_modo(pid, msg.get("monster_ids"), msg.get("modo"))

                elif t == "mestre_set_alvo":
                    if room: await room.handle_mestre_set_alvo(pid, msg.get("monster_ids"), msg.get("target_id"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [6].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): control_mode nos monstros + handlers set_modo/set_alvo + _mestre_ativo

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Override de alvo do modo Semi

**Files:**
- Modify: `server.py` (`_get_monster_primary_target`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()`:

```python
    print("\n[7] modo Semi força o alvo do monstro")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    m = {"id": "g1", "hp": 8, "pos": [5, 5], "control_mode": "semi", "master_target_id": "hB"}
    r.monsters = {"g1": m}
    pA = {"id": "hA", "pos": [5, 6], "alive": True}   # mais próximo
    pB = {"id": "hB", "pos": [9, 9], "alive": True}   # alvo forçado (mais longe)
    targets = [{"kind": "player", "obj": pA}, {"kind": "player", "obj": pB}]
    escolha = r._get_monster_primary_target(m, targets)
    check("Semi escolhe o alvo forçado", escolha["obj"] is pB)
    # alvo forçado ausente da lista → cai no padrão (mais próximo)
    m["master_target_id"] = "hZ"
    escolha2 = r._get_monster_primary_target(m, targets)
    check("alvo inválido cai no mais próximo", escolha2["obj"] is pA)
    # sem mestre conectado → ignora o control_mode
    del r.connections["m1"]
    m["master_target_id"] = "hB"
    escolha3 = r._get_monster_primary_target(m, targets)
    check("sem mestre → padrão", escolha3["obj"] is pA)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em [7] — `_get_monster_primary_target` ainda escolhe o mais próximo.

- [ ] **Step 3: Implementar**

Em `_get_monster_primary_target`, logo após `if not targets: return None` (âncora `presente = lambda obj: any(t["obj"] is obj for t in targets)` — insira ANTES dessa linha):

```python
        if not targets:
            return None
        # Modo Semi (Mestre): força o alvo escolhido, se ele estiver visível.
        if self._mestre_ativo() and m.get("control_mode") == "semi":
            tid = m.get("master_target_id")
            if tid:
                forced = next((t for t in targets if t["obj"].get("id") == tid), None)
                if forced:
                    return forced
        presente = lambda obj: any(t["obj"] is obj for t in targets)
```

> Se o alvo forçado não estiver em `targets` (morto, invisível, fora de visão), a função segue para a seleção normal — exatamente o comportamento "age como auto nesse turno" da spec.

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [7].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): modo Semi forca o alvo do monstro (fallback p/ auto se invisivel)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Janela de controle Manual (fantoche) + timer de segurança + despacho no turno

**Files:**
- Modify: `server.py` (`__init__`, ramo de monstro em `_activate_initiative_actor`, novos `_master_manual_window`, timer, 3 handlers, roteador)
- Test: `tools/test_modo_mestre.py`

**Constante:** o manual usa um orçamento de movimento próprio (monstros não têm campo uniforme). Defina, junto das outras constantes de classe do `GameRoom` (ex.: perto de `TURN_LIMIT_S`):

```python
    MASTER_MANUAL_MOVE = 5      # passos por turno de um monstro em modo Manual
    MASTER_MANUAL_LIMIT_S = 60  # timeout anti-AFK do mestre por monstro manual
```

- [ ] **Step 1: Escrever o teste que falha**

Adicione ao `main()`:

```python
    print("\n[8] janela Manual: mover, atacar e encerrar")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.connections["m1"] = object()
    # stubs dos resolvers reutilizados (evita dependência do combate completo)
    ataques = {"n": 0}
    async def fake_atk(m, atk_def, target_obj):
        ataques["n"] += 1; return True
    r._execute_one_monster_attack = fake_atk
    async def fake_commit(m, nx, ny): m["pos"] = [nx, ny]
    r._commit_monster_step = fake_commit
    r._monster_can_occupy = lambda m, nx, ny, facing=None: True
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "control_mode": "manual",
         "attacks": [{"name": "garra", "damage": "1d4"}]}
    r.monsters = {"g1": m}
    r.master_manual_mid = "g1"
    m["master_moves_left"] = r.MASTER_MANUAL_MOVE
    m["_master_acted"] = False
    hero = {"id": "hA", "pos": [5, 4], "alive": True, "hp": 10}
    r.players = {"hA": hero}
    await r.handle_mestre_mover_monstro("m1", "g1", 1, 0)
    check("monstro moveu 1 casa", m["pos"] == [5, 4])
    check("gastou 1 de movimento", m["master_moves_left"] == r.MASTER_MANUAL_MOVE - 1)
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("ataque resolvido", ataques["n"] == 1)
    check("marcou ataque usado", m["_master_acted"] is True)
    # 2º ataque no mesmo turno é recusado
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("2º ataque recusado", ataques["n"] == 1)
    # encerrar dispara o Event
    r.master_manual_event = asyncio.Event()
    await r.handle_mestre_encerrar_monstro("m1", "g1")
    check("Event setado ao encerrar", r.master_manual_event.is_set())
    check("janela limpa", r.master_manual_mid is None)
    # comandos fora da janela são recusados
    r._errs.clear()
    await r.handle_mestre_mover_monstro("m1", "g1", -1, 0)
    check("mover fora da janela recusado", m["pos"] == [5, 4])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL em [8] — handlers não existem.

- [ ] **Step 3: Implementar**

**3a.** No `__init__`, junto dos campos da Task 1:

```python
        self.master_manual_mid = None       # id do monstro na janela Manual (ou None)
        self.master_manual_event = None     # asyncio.Event que fecha a janela
        self.master_manual_timer = None     # tarefa do timeout anti-AFK
```

**3b.** Os 3 handlers do controle manual (perto de `handle_mestre_set_alvo`):

```python
    async def handle_mestre_mover_monstro(self, pid, monster_id, dx, dy):
        """Manual: move o monstro da janela 1 passo ortogonal."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        if m.get("master_moves_left", 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Monstro sem movimento neste turno."}); return
        dx = max(-1, min(1, int(dx))); dy = max(-1, min(1, int(dy)))
        if (dx == 0 and dy == 0) or (dx != 0 and dy != 0):
            return   # só passos ortogonais de 1 casa
        nx, ny = m["pos"][0] + dx, m["pos"][1] + dy
        if not self._monster_can_occupy(m, nx, ny):
            await self.send_to(pid, {"type": "error", "msg": "Caminho bloqueado."}); return
        await self._commit_monster_step(m, nx, ny)
        m["master_moves_left"] -= 1
        await self.push_state()

    async def handle_mestre_atacar_monstro(self, pid, monster_id, target_id):
        """Manual: o monstro da janela ataca um herói (1 ataque/turno)."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        if m.get("_master_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já atacou neste turno."}); return
        alvo = self.players.get(target_id)
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
        m["_master_acted"] = True
        atk_def = (m.get("attacks") or [{}])[0]
        await self._execute_one_monster_attack(m, atk_def, {"kind": "player", "obj": alvo})
        await self.push_state()

    async def handle_mestre_encerrar_monstro(self, pid, monster_id):
        """Manual: encerra a vez do monstro; libera o laço de iniciativa."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        if self.master_manual_event and not self.master_manual_event.is_set():
            self.master_manual_event.set()
        self.master_manual_mid = None
```

> `_execute_one_monster_attack` recebe `target_obj` — confira na Task 3 do combate existente o formato aceito (nos call sites internos ele recebe o objeto do alvo). Se a assinatura interna esperar o dict do jogador diretamente (e não `{"kind","obj"}`), passe `alvo`. **Verifique lendo `_execute_one_monster_attack` no momento da implementação** e ajuste o argumento para casar exatamente com os call sites existentes (ex.: `_ai_agressivo`).

**3c.** A janela bloqueante + timer:

```python
    async def _master_manual_window(self, m):
        """Abre a janela interativa do modo Manual e aguarda o mestre agir.
        Retorna quando o mestre encerra OU o timeout resolve via IA auto."""
        self.master_manual_mid = m["id"]
        m["master_moves_left"] = self.MASTER_MANUAL_MOVE
        m["_master_acted"] = False
        self.master_manual_event = asyncio.Event()
        await self.push_state()
        self.master_manual_timer = asyncio.create_task(self._master_manual_timeout(m["id"]))
        try:
            await self.master_manual_event.wait()
        finally:
            if self.master_manual_timer and not self.master_manual_timer.done():
                self.master_manual_timer.cancel()
            self.master_manual_timer = None
            self.master_manual_mid = None

    async def _master_manual_timeout(self, mid):
        """Anti-AFK: se o mestre não encerrar em MASTER_MANUAL_LIMIT_S, o monstro
        age via IA auto e a janela fecha."""
        try:
            await asyncio.sleep(self.MASTER_MANUAL_LIMIT_S)
        except asyncio.CancelledError:
            return
        if self.master_manual_mid != mid:
            return
        m = self.monsters.get(mid)
        if m and m["hp"] > 0:
            alive_players = [p for p in self.players.values() if self._ativo(p)]
            if alive_players:
                await self.gm_phase(m)   # fallback: IA controla o monstro
        if self.master_manual_event and not self.master_manual_event.is_set():
            self.master_manual_event.set()
```

**3d.** Despacho no ramo de monstro de `_activate_initiative_actor`. O código atual é (âncora `async def monster_step(mid):`):

```python
        async def monster_step(mid):
            monster = self.monsters.get(mid)
            if monster and monster.get("hp", 0) > 0:
                await self.gm_phase(monster)
            await self._advance_initiative()
        self.initiative_task = asyncio.create_task(monster_step(actor["id"]))
```

Substitua o corpo por:

```python
        async def monster_step(mid):
            monster = self.monsters.get(mid)
            if monster and monster.get("hp", 0) > 0:
                mode = monster.get("control_mode", "auto") if self._mestre_ativo() else "auto"
                if mode == "manual":
                    await self._master_manual_window(monster)
                else:
                    await self.gm_phase(monster)   # auto e semi (semi força o alvo em _get_monster_primary_target)
            await self._advance_initiative()
        self.initiative_task = asyncio.create_task(monster_step(actor["id"]))
```

> Quando não há mestre ativo, `mode` é sempre `"auto"` → caminho byte-idêntico ao atual.

**3e.** Roteador — as 3 mensagens manuais:

```python
                elif t == "mestre_mover_monstro":
                    if room: await room.handle_mestre_mover_monstro(pid, msg.get("monster_id"), msg.get("dx"), msg.get("dy"))

                elif t == "mestre_atacar_monstro":
                    if room: await room.handle_mestre_atacar_monstro(pid, msg.get("monster_id"), msg.get("target_id"))

                elif t == "mestre_encerrar_monstro":
                    if room: await room.handle_mestre_encerrar_monstro(pid, msg.get("monster_id"))
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [8].

- [ ] **Step 5: Regressão — jogo sem mestre é idêntico**

Adicione ao `main()` uma prova de não-regressão do despacho:

```python
    print("\n[9] sem mestre: monstro manual ainda roda auto")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = None   # nenhum mestre
    chamou = {"gm": 0}
    async def fake_gm(m=None): chamou["gm"] += 1
    r.gm_phase = fake_gm
    async def fake_adv(): pass
    r._advance_initiative = fake_adv
    m = {"id": "g1", "hp": 8, "pos": [1, 1], "control_mode": "manual"}
    r.monsters = {"g1": m}
    # simula o corpo de monster_step com o despacho novo
    mode = m.get("control_mode", "auto") if r._mestre_ativo() else "auto"
    check("sem mestre → auto", mode == "auto")
```

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [9].

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): janela Manual (fantoche) com Event + timer anti-AFK + despacho no turno

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Reconexão do mestre + desconexão → monstros em auto

**Files:**
- Modify: `server.py` (roteador `rejoin`; `handle_disconnect_em_jogo` se necessário)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Verificar o disconnect atual**

Leia `handle_disconnect_em_jogo` e o ponto do roteador onde a conexão cai (âncora do `finally`/`handle_disconnect`). O mestre NÃO está em `self.players`, então o loop de desconexão de heróis o ignora naturalmente. O único efeito necessário: remover a conexão do mestre de `self.connections` (o que já acontece no cleanup genérico do `handler`), fazendo `_mestre_ativo()` virar False → monstros caem em auto. **Confirme** que o cleanup do `handler` faz `room.connections.pop(pid, None)` para qualquer pid. Se fizer, nenhuma mudança de disconnect é necessária.

- [ ] **Step 2: Escrever o teste que falha (rejoin do mestre)**

Adicione ao `main()`:

```python
    print("\n[10] rejoin do mestre religa a conexão")
    r = lobby_room(); r.phase = "playing"
    r.master_pid = "m1"; r.master_name = "Mestre"
    # mestre desconectado: sem entrada em connections
    check("mestre inativo desconectado", r._mestre_ativo() is False)
    # simula o núcleo do rejoin do mestre
    r.connections["m1"] = object()
    check("mestre ativo após religar", r._mestre_ativo() is True)
```

> Este teste prova a invariante (`_mestre_ativo` segue a conexão). A ligação real do WebSocket é feita no roteador `rejoin`, testada manualmente no app (Step 4).

- [ ] **Step 3: Implementar o rejoin do mestre no roteador**

No bloco `elif t == "rejoin":`, o código encontra o alvo por nome em `alvo_room.players` (âncora `alvo = next((p for p in alvo_room.players.values()`). O mestre NÃO está em `players`. Adicione um ramo de mestre logo após obter `alvo_room` e antes da busca em `players`:

```python
                    # Reconexão do MESTRE (não está em players; casado por master_name).
                    if alvo_room.master_pid and name == (alvo_room.master_name or ""):
                        if alvo_room.master_pid in alvo_room.connections:
                            await err("O mestre ainda está conectado.")
                            continue
                        pid = alvo_room.master_pid
                        room = alvo_room
                        room.connections[pid] = ws
                        await ws.send(json.dumps({"type": "game_start", "instrumentos_base": INSTRUMENTOS_BASE}))
                        if room.phase == "city":
                            await room.broadcast_city_state()
                        else:
                            await ws.send(json.dumps({"type": "enter_dungeon"}))
                            await room.push_state()
                        await room.gm_say(f"🔌 O mestre **{name}** reconectou-se.")
                        continue
```

- [ ] **Step 4: Rodar o teste + verificação manual**

Run: `python tools/test_modo_mestre.py`
Expected: PASS até [10].

Verificação manual (depois das tasks de cliente): suba `iniciar.bat`, entre com 2 abas, uma como mestre; feche a aba do mestre no meio da masmorra → confirme no log que os monstros voltam a agir sozinhos; reabra e reconecte pelo botão "Reconectar" → confirme o controle de volta.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): rejoin do mestre + desconexao cai em auto

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Cliente — toggle de mestre no lobby

**Files:**
- Modify: `src/gameState.js` (envio de `claim_role`, getter `isMaster`), `game.js` (botão no lobby)

> **Sem harness de teste JS neste projeto.** Verificação é manual via o app rodando (`iniciar.bat`). NÃO edite `game.js` por PowerShell (regra do projeto) — use a ferramenta Edit.

- [ ] **Step 1: Adicionar o sender e o getter em `src/gameState.js`**

Localize um sender existente simples como âncora (ex.: `function selectClass` ou onde `send({type:"select_class", ...})` é definido). Adicione, no mesmo estilo do módulo:

```javascript
  function claimRole(role) {          // role: "master" | "hero"
    send({ type: "claim_role", role });
  }
```

E um getter de papel (o cliente já guarda `myPid`; o payload agora traz `master_pid`):

```javascript
  function isMaster() {
    const st = lobbyState || cityState || gameState;
    return !!(st && st.master_pid && st.master_pid === myPid);
  }
```

Exporte `claimRole` e `isMaster` no objeto público `GS` (âncora: o `return { ... }` / `window.GS = {...}` do módulo). Acrescente-os à lista exportada.

- [ ] **Step 2: Adicionar o botão no lobby (`game.js`)**

Localize a renderização dos cards de classe no lobby (âncora: onde `lobby_state`/`classes` é renderizado, provavelmente uma função como `renderLobby`). Adicione um botão de toggle acima ou ao lado dos cards:

```javascript
    // Toggle de Modo Mestre (Fase A)
    const jaMestre = GS.isMaster();
    const btnMestre = document.createElement('button');
    btnMestre.className = 'lobby-master-toggle' + (jaMestre ? ' ativo' : '');
    btnMestre.textContent = jaMestre ? '🎭 Mestre (clique p/ virar herói)' : '🎭 Assumir como Mestre';
    btnMestre.onclick = () => GS.claimRole(jaMestre ? 'hero' : 'master');
    // anexe btnMestre ao container do lobby onde ficam as classes
```

Quando `GS.isMaster()` for true, oculte/desabilite a grade de seleção de classe daquele cliente (o mestre não escolhe classe). Ex.: envolva a render dos cards em `if (!GS.isMaster()) { ...render classes... }`.

- [ ] **Step 3: Verificação manual**

Suba `iniciar.bat`, 2 abas no lobby. Na aba B clique "Assumir como Mestre":
- Confirme que a grade de classes some para B e aparece "Mestre".
- Na aba A, tente também virar mestre → deve receber erro "Já existe um mestre".
- Com A escolhendo uma classe, o host consegue iniciar (can_start ignora o mestre).

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js game.js
git commit -m "feat(mestre): toggle de Modo Mestre no lobby (cliente)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Cliente — HUD do mestre (roster, modos, alvo, manual) + render sem névoa

**Files:**
- Modify: `src/gameState.js` (senders `mestre_*`), `game.js` (detecção de papel, HUD, render sem névoa)

- [ ] **Step 1: Senders em `src/gameState.js`**

```javascript
  function mestreSetModo(monsterIds, modo) {
    send({ type: "mestre_set_modo", monster_ids: monsterIds, modo });
  }
  function mestreSetAlvo(monsterIds, targetId) {
    send({ type: "mestre_set_alvo", monster_ids: monsterIds, target_id: targetId });
  }
  function mestreMoverMonstro(monsterId, dx, dy) {
    send({ type: "mestre_mover_monstro", monster_id: monsterId, dx, dy });
  }
  function mestreAtacarMonstro(monsterId, targetId) {
    send({ type: "mestre_atacar_monstro", monster_id: monsterId, target_id: targetId });
  }
  function mestreEncerrarMonstro(monsterId) {
    send({ type: "mestre_encerrar_monstro", monster_id: monsterId });
  }
```

Exporte os cinco no `GS`. Adicione também um getter da janela manual atual:

```javascript
  function masterManualMid() {
    return (gameState && gameState.master_manual_mid) || null;
  }
```

> **Dependência de servidor:** para o cliente saber qual monstro está na janela manual, `push_state` deve incluir `master_manual_mid`. Adicione essa chave ao dict de `push_state` na Task 5/Step 3 (junto de `master_pid`): `"master_manual_mid": self.master_manual_mid,`. Faça esse ajuste agora se ainda não estiver lá e re-commite o server (`git add server.py`).

- [ ] **Step 2: Detecção de papel e branch de HUD em `game.js`**

Onde o HUD do jogador é montado a cada `game_state` (âncora: a função que renderiza o painel do herói, ex.: `renderMyPanel` / `renderHUD`), adicione no topo:

```javascript
    if (GS.isMaster()) { renderMasterHud(state); return; }
```

- [ ] **Step 3: `renderMasterHud(state)` em `game.js`**

Crie a função (mantida focada, todo o HUD do mestre num só lugar):

```javascript
  let _masterSel = new Set();   // ids de monstros selecionados no roster

  function renderMasterHud(state) {
    const host = document.getElementById('hud-mestre') || _ensureMasterHudContainer();
    host.innerHTML = '';
    const manualMid = state.master_manual_mid;

    // Roster de monstros
    (state.monsters || []).forEach(m => {
      const row = document.createElement('div');
      row.className = 'mestre-row' + (_masterSel.has(m.id) ? ' sel' : '');
      row.innerHTML = `<span class="nome">${m.name || m.type}</span>` +
                      `<span class="hp">${m.hp}/${m.max_hp || m.hp}</span>` +
                      `<span class="modo">${m.control_mode || 'auto'}</span>`;
      row.onclick = () => { if (_masterSel.has(m.id)) _masterSel.delete(m.id); else _masterSel.add(m.id); renderMasterHud(state); };
      host.appendChild(row);
    });

    // Botões de modo em lote (aplica à seleção)
    ['auto', 'semi', 'manual'].forEach(modo => {
      const b = document.createElement('button');
      b.textContent = modo;
      b.onclick = () => { GS.mestreSetModo([..._masterSel], modo); };
      host.appendChild(b);
    });

    // Atribuir alvo (Semi): escolhe um herói para a seleção
    const selAlvo = document.createElement('select');
    selAlvo.innerHTML = '<option value="">— alvo —</option>' +
      (state.players || []).filter(p => p.alive)
        .map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    selAlvo.onchange = () => { if (selAlvo.value) GS.mestreSetAlvo([..._masterSel], selAlvo.value); };
    host.appendChild(selAlvo);

    // Controles da janela Manual (só quando um monstro seu está na vez)
    if (manualMid) {
      const box = document.createElement('div');
      box.className = 'mestre-manual';
      const mkMove = (dx, dy, lbl) => {
        const b = document.createElement('button');
        b.textContent = lbl;
        b.onclick = () => GS.mestreMoverMonstro(manualMid, dx, dy);
        return b;
      };
      box.append(mkMove(0, -1, '↑'), mkMove(0, 1, '↓'), mkMove(-1, 0, '←'), mkMove(1, 0, '→'));
      const atk = document.createElement('button');
      atk.textContent = '⚔️ atacar herói selecionado';
      atk.onclick = () => { if (selAlvo.value) GS.mestreAtacarMonstro(manualMid, selAlvo.value); };
      const fim = document.createElement('button');
      fim.textContent = 'Encerrar monstro';
      fim.onclick = () => GS.mestreEncerrarMonstro(manualMid);
      box.append(atk, fim);
      host.appendChild(box);
    }
  }

  function _ensureMasterHudContainer() {
    const d = document.createElement('div');
    d.id = 'hud-mestre';
    document.body.appendChild(d);   // reposicione via CSS conforme o layout do jogo
    return d;
  }
```

> Estilos (`.mestre-row`, `#hud-mestre`, etc.) em `game.css` — copie o padrão visual do HUD existente. É trabalho de CSS, sem lógica.

- [ ] **Step 4: Render sem névoa para o mestre**

Localize onde os monstros são ocultados pela névoa no render (âncora: no laço de desenho de monstros 2D/3D, uma checagem contra `explored`/`revealed`, ex.: `if (!explored.has(key)) return;`). Envolva essa checagem para NÃO se aplicar ao mestre:

```javascript
    const semNevoa = GS.isMaster();
    // ... dentro do laço de monstros:
    if (!semNevoa && !tileVisivel(m.pos)) return;   // mestre vê tudo
```

Faça o mesmo para o desenho da própria névoa (o overlay escuro): se `GS.isMaster()`, pule o desenho do overlay de névoa. Localize a função que pinta a névoa (âncora: onde `explored` é usado para escurecer tiles não explorados) e adicione `if (GS.isMaster()) return;` no início dela (ou pule a camada).

- [ ] **Step 5: Verificação manual (fluxo completo)**

Suba `iniciar.bat`. Aba A = herói (guerreiro), Aba B = mestre. Inicie a masmorra.
1. **Sem névoa:** confirme que B vê o mapa inteiro e todos os monstros; A continua com névoa.
2. **Semi:** em B, selecione um monstro, clique "semi", escolha um herói no dropdown. No turno desse monstro, confirme que ele persegue/ataca o herói escolhido (mesmo que não seja o mais próximo).
3. **Manual:** ponha um monstro em "manual". Quando a iniciativa dele chegar, confirme que aparecem as setas + atacar + encerrar; mova-o, ataque, encerre; confirme que o jogo avança.
4. **Timeout:** ponha um monstro em manual e NÃO aja por 60s → confirme (no log) que ele age sozinho e o turno avança.
5. **Auto (regressão):** deixe todos em "auto" → o jogo se comporta como hoje.

- [ ] **Step 6: Commit**

```bash
git add src/gameState.js game.js game.css
git commit -m "feat(mestre): HUD do mestre (roster/modos/alvo/manual) + visao sem nevoa (cliente)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Documentação — CLAUDE.md e memória

**Files:**
- Modify: `CLAUDE.md` (nota de arquitetura do Modo Mestre Fase A + as novas mensagens no protocolo)

- [ ] **Step 1: Protocolo Client→Server**

Adicione à tabela "Client → Server" do `CLAUDE.md` as mensagens: `claim_role`, `mestre_set_modo`, `mestre_set_alvo`, `mestre_mover_monstro`, `mestre_atacar_monstro`, `mestre_encerrar_monstro`, com uma linha de descrição cada (espelhe o estilo das entradas existentes).

- [ ] **Step 2: Bloco de arquitetura**

Adicione um bloco `> **Modo Mestre Jogador (Fase A):** ...` ao final do CLAUDE.md resumindo: mestre rastreado por `self.master_pid` (fora de `self.players`), `control_mode` por monstro, despacho em `_activate_initiative_actor`, janela Manual via `asyncio.Event` + timer, visão sem névoa no cliente, tudo no-op sem mestre. Aponte o teste `tools/test_modo_mestre.py` e a spec.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): documenta a Fase A do Modo Mestre Jogador (protocolo + arquitetura)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Self-Review (do autor do plano)

**Cobertura da spec:**
- §1 Assento de mestre → Task 1 + Task 7. ✓
- §2 Modos + hook de turno → Task 3 (campos/handlers) + Task 4 (semi) + Task 5 (hook/manual). ✓
- §3 Janela Manual → Task 5. ✓
- §4 Visão + HUD → Task 8 (com o achado de que a névoa é cliente-side; `master_pid`/`master_manual_mid` nos payloads em Tasks 2/5/8). ✓
- §5 Robustez (timeout, disconnect) → Task 5 (timer) + Task 6 (disconnect/rejoin). ✓
- §6 Vitória/derrota → sem código novo (fluxos existentes); nada a fazer. ✓
- start_game (não estava explícito na spec, mas necessário) → Task 2. ✓

**Consistência de tipos/nomes:** `control_mode`, `master_target_id`, `master_pid`, `master_name`, `master_manual_mid`, `master_manual_event`, `master_moves_left`, `_master_acted`, `MASTER_MANUAL_MOVE`, `MASTER_MANUAL_LIMIT_S` — usados consistentemente entre tasks. Handlers: `handle_mestre_set_modo/set_alvo/mover_monstro/atacar_monstro/encerrar_monstro`; senders JS `mestreSetModo/mestreSetAlvo/mestreMoverMonstro/mestreAtacarMonstro/mestreEncerrarMonstro`. ✓

**Riscos sinalizados para o implementador:**
1. `_execute_one_monster_attack` — confirmar o formato exato do `target_obj` lendo os call sites antes de usar (Task 5/3b).
2. Números de linha derivam (usuário edita `server.py` em paralelo) — usar âncoras de função/string. ✓ (convenção no topo).
3. `master_manual_mid` precisa entrar no payload de `push_state` (nota cruzada em Task 8/1). ✓
