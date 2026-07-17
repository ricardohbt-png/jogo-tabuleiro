# Controle manual do monstro (SP1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No Modo Mestre, dar ao monstro em modo Manual um movimento em casas azuis (como o jogador) e uma ficha à direita onde o mestre ativa as habilidades especiais da criatura (com usos/recarga).

**Architecture:** Servidor autoritativo — o `movement` real vira o orçamento (`master_moves_left`); um BFS footprint-aware (`_master_reach_bfs`) alimenta tanto o realce azul (`master_manual_reach` no `game_state`) quanto o caminho andado (`handle_mestre_mover_monstro_para`). Ativar habilidade reusa `_use_monster_ability` (já debita usos/recarga) e consome a ação (`_master_acted`). Cliente injeta o reach nos conjuntos `reachable` de 2D/3D e expande `renderFichaMonstro`.

**Tech Stack:** Python (`server.py`, `websockets`), Vanilla JS (`game.js`, `src/gameState.js`), CSS (`game.css`). Testes: harness próprio em `tools/test_modo_mestre.py` (função `check()`), rodado com `python tools/test_modo_mestre.py`.

**Invariante:** tudo só age com `_mestre_ativo()` e dentro da janela Manual. Sem mestre, byte-idêntico.

**⚠️ WIP do usuário:** `server.py` e `tools/test_modo_mestre.py` têm alterações não commitadas do usuário em paralelo. **NUNCA** usar `git add -A`/`git add .`. Sempre `git add <arquivo específico>`. Antes de cada commit, conferir `git status`.

---

### Task 1: Servidor — orçamento = movimento real + BFS de alcance + `master_manual_reach`

**Files:**
- Modify: `server.py` (`_master_manual_window` ~9350; novo bloco de métodos perto de `_monster_can_occupy` ~15772; `push_state` ~19007)
- Test: `tools/test_modo_mestre.py` (nova seção `[25]`, antes da linha `print(f"\n=== {PASS}...")`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir esta seção nova em `tools/test_modo_mestre.py`, imediatamente antes da linha `print(f"\n=== {PASS} passaram, {FAIL} falharam ===")`:

```python
    print("\n[25] _master_reach_bfs / _master_monster_reach respeitam orçamento e paredes")
    r = playing_room_com_mestre()
    # parede vertical em x=3 (coluna toda), abre um vão em y=2
    for y in range(10):
        r.tiles[y][3] = S.WALL
    r.tiles[2][3] = S.FLOOR
    m = {"id": "g1", "hp": 8, "pos": [1, 2], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 2}
    r.monsters = {"g1": m}
    reach = r._master_monster_reach(m)
    reach_set = {tuple(c) for c in reach}
    check("alcança a 2 passos ortogonais", (1, 0) in reach_set and (1, 4) in reach_set)
    check("não inclui a casa atual", (1, 2) not in reach_set)
    check("não atravessa parede (x=4 fora de 2 passos)", (4, 2) not in reach_set)
    check("respeita orçamento (3 passos fora)", (1, 5) not in reach_set)
    # com orçamento maior, cruza o vão em (3,2) e chega em (4,2)
    m["master_moves_left"] = 3
    reach2 = {tuple(c) for c in r._master_monster_reach(m)}
    check("com 3 passos cruza o vão", (3, 2) in reach2 and (4, 2) in reach2)
    check("orçamento 0 → vazio", r._master_monster_reach({"id":"g2","pos":[1,2],"master_moves_left":0}) == [])
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `AttributeError: 'GameRoom' object has no attribute '_master_monster_reach'`.

- [ ] **Step 3: Implementar os métodos de BFS**

Em `server.py`, logo após o método `_monster_can_occupy` (termina em `return True`, ~linha 15782), inserir:

```python
    def _master_reach_bfs(self, m, budget):
        """BFS ortogonal footprint-aware a partir da âncora de m, ≤ budget passos.
        Retorna prev {(x,y): (px,py)|None} de todas as casas alcançáveis (inclui a
        inicial). Caminhabilidade = _monster_can_occupy (paredes/portas/footprint/
        entidades vivas, ignorando a própria m)."""
        sx, sy = m["pos"]
        prev = {(sx, sy): None}
        dist = {(sx, sy): 0}
        q = [(sx, sy)]; head = 0
        while head < len(q):
            x, y = q[head]; head += 1
            if dist[(x, y)] >= budget:
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in prev or not self._monster_can_occupy(m, nx, ny):
                    continue
                prev[(nx, ny)] = (x, y)
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
        return prev

    def _master_monster_reach(self, m):
        """Lista [x,y] alcançável pela âncora de m dentro de master_moves_left
        (exclui a casa atual). Alimenta o realce azul do cliente."""
        budget = int(m.get("master_moves_left", 0) or 0)
        if budget <= 0:
            return []
        prev = self._master_reach_bfs(m, budget)
        sx, sy = m["pos"]
        return [[x, y] for (x, y) in prev if (x, y) != (sx, sy)]

    def _master_path_to(self, m, tx, ty, budget):
        """Menor caminho (lista de âncoras, exclui a casa inicial, inclui o destino)
        de m até (tx,ty) em ≤ budget passos. [] se inalcançável."""
        if budget <= 0:
            return []
        sx, sy = m["pos"]
        if (sx, sy) == (tx, ty):
            return []
        prev = self._master_reach_bfs(m, budget)
        if (tx, ty) not in prev:
            return []
        path = []; cur = (tx, ty)
        while cur != (sx, sy):
            path.append([cur[0], cur[1]]); cur = prev[cur]
        path.reverse()
        return path
```

- [ ] **Step 4: Orçamento = movimento real na abertura da janela**

Em `server.py`, `_master_manual_window` (~9350), trocar a linha:

```python
        m["master_moves_left"] = self.MASTER_MANUAL_MOVE
```

por:

```python
        m["master_moves_left"] = int(m.get("movement", self.MASTER_MANUAL_MOVE) or self.MASTER_MANUAL_MOVE)
```

- [ ] **Step 5: Publicar `master_manual_reach` no `game_state`**

Em `server.py`, `push_state` (~19007), logo após a linha `"master_manual_mid": self.master_manual_mid,` inserir:

```python
            "master_manual_reach": (
                self._master_monster_reach(self.monsters[self.master_manual_mid])
                if self.master_manual_mid and self.master_manual_mid in self.monsters
                and self.monsters[self.master_manual_mid]["hp"] > 0 else []
            ),
```

- [ ] **Step 6: Rodar e confirmar sucesso**

Run: `python tools/test_modo_mestre.py`
Expected: PASS na seção `[25]` (e nenhuma regressão nas anteriores; as `[8]/[8b]` ainda usam o handler antigo — migradas na Task 2).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): BFS de alcance do monstro manual + orçamento = movimento real"
```

---

### Task 2: Servidor — `handle_mestre_mover_monstro_para` + remoção do handler de setas

**Files:**
- Modify: `server.py` (substituir `handle_mestre_mover_monstro` ~9247; dispatcher ~19208)
- Test: `tools/test_modo_mestre.py` (migrar seções `[8]`, `[8b]`; nova `[8d]`)

- [ ] **Step 1: Reescrever os testes [8]/[8b] e adicionar [8d] para o novo handler**

Em `tools/test_modo_mestre.py`, localizar a seção `[8]` (começa em `print("\n[8] ...`) e a `[8b]`. Substituir **os dois blocos** (de `print("\n[8]` até o fim do bloco `[8b]`, imediatamente antes de `print("\n[8c]`) por:

```python
    print("\n[8] mover_para caminha até a casa alcançável e gasta o orçamento")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 5}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    passos = {"n": 0}
    async def fake_commit_ok(mm, nx, ny):
        mm["pos"] = [nx, ny]; passos["n"] += 1; return True
    r._commit_monster_step = fake_commit_ok
    await r.handle_mestre_mover_monstro_para("m1", "g1", 4, 1)   # 3 casas para cima
    check("chegou ao destino", m["pos"] == [4, 1])
    check("gastou 3 de movimento", m["master_moves_left"] == 2)
    check("comitou 3 passos", passos["n"] == 3)

    print("\n[8b] mover_para recusa fora da janela e destino inalcançável")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [4, 4], "size": [1, 1], "master_moves_left": 5}
    r.monsters = {"g1": m}; r.master_manual_mid = "g9"   # outra janela
    r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 4, 1)
    check("mover fora da janela recusado", m["pos"] == [4, 4])
    r.master_manual_mid = "g1"; r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 9, 9)   # longe demais p/ 5 passos
    check("destino inalcançável recusado", m["pos"] == [4, 4])
    check("erro de inalcançável emitido", any("alcanç" in e.lower() for e in r._errs))

    print("\n[8d] mover_para para no orçamento (destino além do alcance não anda)")
    r = playing_room_com_mestre()
    m = {"id": "g1", "hp": 8, "pos": [0, 0], "size": [1, 1],
         "control_mode": "manual", "master_moves_left": 2}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    async def commit_track(mm, nx, ny): mm["pos"] = [nx, ny]; return True
    r._commit_monster_step = commit_track
    r._errs.clear()
    await r.handle_mestre_mover_monstro_para("m1", "g1", 5, 0)   # 5 casas, só 2 de orçamento
    check("não moveu além do alcance", m["pos"] == [0, 0])
```

Manter as seções `[8c]` (ataque melee) e `[9]` como estão.

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `AttributeError: ... has no attribute 'handle_mestre_mover_monstro_para'`.

- [ ] **Step 3: Substituir o handler de setas pelo handler de destino**

Em `server.py`, **substituir todo** o método `handle_mestre_mover_monstro` (~9247–9265, de `async def handle_mestre_mover_monstro` até o `await self.push_state()` que o encerra) por:

```python
    async def handle_mestre_mover_monstro_para(self, pid, monster_id, tx, ty):
        """Manual: caminha o monstro da janela até (tx,ty), passo a passo,
        gastando master_moves_left. O servidor acha o caminho (footprint-aware) e
        comita cada passo; para no bloqueio ou ao esgotar o orçamento."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        try:
            tx = int(tx); ty = int(ty)
        except (TypeError, ValueError):
            return
        budget = int(m.get("master_moves_left", 0) or 0)
        if budget <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Monstro sem movimento neste turno."}); return
        path = self._master_path_to(m, tx, ty, budget)
        if not path:
            await self.send_to(pid, {"type": "error", "msg": "Destino inalcançável."}); return
        for nx, ny in path:
            if m.get("master_moves_left", 0) <= 0:
                break
            if not self._monster_can_occupy(m, nx, ny):
                break
            if not await self._commit_monster_step(m, nx, ny):
                break
            m["master_moves_left"] -= 1
        await self.push_state()
```

- [ ] **Step 4: Trocar a entrada do dispatcher**

Em `server.py` (~19208), substituir estas duas linhas:

```python
                elif t == "mestre_mover_monstro":
                    if room: await room.handle_mestre_mover_monstro(pid, msg.get("monster_id"), msg.get("dx"), msg.get("dy"))
```

por:

```python
                elif t == "mestre_mover_monstro_para":
                    if room: await room.handle_mestre_mover_monstro_para(pid, msg.get("monster_id"), msg.get("tx"), msg.get("ty"))
```

- [ ] **Step 5: Rodar e confirmar sucesso**

Run: `python tools/test_modo_mestre.py`
Expected: PASS em `[8]`, `[8b]`, `[8d]` (e todo o resto verde).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): mover monstro por clique no destino (path-walk); remove setas"
```

---

### Task 3: Servidor — ativar habilidade especial do monstro (`handle_mestre_usar_habilidade`)

**Files:**
- Modify: `server.py` (novos métodos perto de `_use_monster_ability` ~16231; dispatcher ~19208)
- Test: `tools/test_modo_mestre.py` (nova seção `[26]`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_modo_mestre.py`, antes da linha final `print(f"\n=== {PASS}...`):

```python
    print("\n[26] mestre_usar_habilidade — ativa via _use_monster_ability e consome a ação")
    r = playing_room_com_mestre()
    usada = {"ab": None, "alvo": None}
    async def fake_use(mm, ability, target_obj):
        usada["ab"] = ability["id"]; usada["alvo"] = target_obj["obj"]["id"]; return True
    r._use_monster_ability = fake_use
    ab_ok = {"id": "petrificar", "name": "Petrificar", "action_type": "acao",
             "save": "fort", "dc": 13}
    ab_passiva = {"id": "sem_dor", "name": "Sem Dor", "action_type": "passiva"}
    ab_ia = {"id": "turbilhao", "name": "Turbilhão", "action_type": "acao"}   # sem save/dc
    m = {"id": "g1", "hp": 20, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "attacks": [{"name": "garra"}], "_master_acted": False,
         "special_abilities": [ab_ok, ab_passiva, ab_ia]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("habilidade ativada", usada["ab"] == "petrificar" and usada["alvo"] == "hA")
    check("consumiu a ação", m["_master_acted"] is True)

    print("\n[26b] recusa passiva / IA-apenas / já-agiu / alvo fora de alcance")
    r = playing_room_com_mestre()
    r._use_monster_ability = fake_use
    m = {"id": "g1", "hp": 20, "pos": [2, 2], "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "special_abilities": [ab_ok, ab_passiva, ab_ia]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True},
                 "hB": {"id": "hB", "name": "Bea", "pos": [9, 9], "alive": True}}
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "sem_dor", "hA")
    check("passiva recusada", m["_master_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "turbilhao", "hA")
    check("IA-apenas (sem save/dc) recusada", m["_master_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hB")
    check("alvo fora de alcance (melee) recusado", m["_master_acted"] is False)
    m["_master_acted"] = True; r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("já-agiu recusado", any("agiu" in e.lower() for e in r._errs))
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_modo_mestre.py`
Expected: FAIL — `AttributeError: ... has no attribute 'handle_mestre_usar_habilidade'`.

- [ ] **Step 3: Implementar o predicado e o handler**

Em `server.py`, logo após o método `_use_monster_ability` (termina em `return True`, ~linha 16299), inserir:

```python
    def _habilidade_ativavel_manual(self, ability):
        """SP1: o mestre só ativa habilidades ATIVAS resolvíveis por
        _use_monster_ability (têm save e dc — as do editor de criaturas). As demais
        (bespoke hardcoded, action_type 'magia') aparecem na ficha como 'IA apenas'.
        Ponto único de plugagem para lotes futuros (dispatch por id/action_type)."""
        if not ability or ability.get("action_type") == "passiva":
            return False
        return ability.get("save") is not None and ability.get("dc") is not None

    async def handle_mestre_usar_habilidade(self, pid, monster_id, ability_id, target_id):
        """Manual: o mestre ativa uma habilidade ativa do monstro num herói.
        Consome a ação do turno (como atacar). Só habilidades ativáveis (save+dc)."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        if m.get("_master_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já agiu neste turno."}); return
        ability = next((a for a in m.get("special_abilities", []) if a.get("id") == ability_id), None)
        if not self._habilidade_ativavel_manual(ability):
            await self.send_to(pid, {"type": "error", "msg": "Habilidade não ativável manualmente (IA apenas)."}); return
        alvo = self.players.get(target_id)
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
        rng = ability.get("range")
        dist = max(abs(m["pos"][0] - alvo["pos"][0]), abs(m["pos"][1] - alvo["pos"][1]))
        if rng:
            if dist > rng:
                await self.send_to(pid, {"type": "error", "msg": "Alvo fora de alcance."}); return
        elif not self._is_adjacent_to_monster(alvo["pos"], m):
            await self.send_to(pid, {"type": "error", "msg": "Alvo não está adjacente."}); return
        used = await self._use_monster_ability(m, ability, {"kind": "player", "obj": alvo})
        if not used:
            await self.send_to(pid, {"type": "error", "msg": "Habilidade sem usos ou em recarga."}); return
        m["_master_acted"] = True
        await self.push_state()
```

- [ ] **Step 4: Adicionar a entrada do dispatcher**

Em `server.py` (~19212), logo após a linha do `mestre_atacar_monstro`:

```python
                elif t == "mestre_atacar_monstro":
                    if room: await room.handle_mestre_atacar_monstro(pid, msg.get("monster_id"), msg.get("target_id"))
```

inserir:

```python
                elif t == "mestre_usar_habilidade":
                    if room: await room.handle_mestre_usar_habilidade(pid, msg.get("monster_id"), msg.get("ability_id"), msg.get("target_id"))
```

- [ ] **Step 5: Rodar e confirmar sucesso**

Run: `python tools/test_modo_mestre.py`
Expected: PASS em `[26]`/`[26b]`, todo o resto verde. Confirmar a contagem final `=== N passaram, 0 falharam ===`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): ativar habilidade especial do monstro na ficha (consome ação)"
```

---

### Task 4: Cliente (gameState.js) — senders novos, remover o de setas

**Files:**
- Modify: `src/gameState.js` (~1285 defs; ~2115 export)

- [ ] **Step 1: Trocar o sender de movimento e adicionar o de habilidade**

Em `src/gameState.js`, substituir a linha (~1285):

```javascript
  function mestreMoverMonstro(monsterId, dx, dy) { send({ type: 'mestre_mover_monstro', monster_id: monsterId, dx, dy }); }
```

por:

```javascript
  function mestreMoverMonstroPara(monsterId, tx, ty) { send({ type: 'mestre_mover_monstro_para', monster_id: monsterId, tx, ty }); }
  function mestreUsarHabilidade(monsterId, abilityId, targetId) { send({ type: 'mestre_usar_habilidade', monster_id: monsterId, ability_id: abilityId, target_id: targetId }); }
```

- [ ] **Step 2: Atualizar o objeto exportado**

Em `src/gameState.js` (~2115), substituir a linha:

```javascript
    mestreMoverMonstro,
```

por:

```javascript
    mestreMoverMonstroPara,
    mestreUsarHabilidade,
```

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(mestre): senders mestreMoverMonstroPara + mestreUsarHabilidade"
```

---

### Task 5: Cliente (game.js) — realce azul do monstro + clique-para-mover/atacar + tirar setas do HUD

**Files:**
- Modify: `game.js` (helper novo perto de `_monstroEmCasa` ~10356; render 2D ~5146; render 3D ~14673; `handleTileClick` ~10 ramo mestre ~21183; `renderMasterHud` ~10272/10305)

- [ ] **Step 1: Adicionar o helper de reach do mestre**

Em `game.js`, logo após a função `_monstroEmCasa` (~10359), inserir:

```javascript
// Casas alcançáveis pelo monstro Manual (autoritativo — vem do servidor).
function _masterReachSet(state){
  const s = new Set();
  if(GS.isMaster() && state && Array.isArray(state.master_manual_reach))
    state.master_manual_reach.forEach(([x,y]) => s.add(`${x},${y}`));
  return s;
}
// Heróis no alcance de ataque do monstro Manual (realce vermelho + clique-atacar).
function _masterAttackSet(state){
  const s = new Set();
  if(!(GS.isMaster() && state && state.master_manual_mid)) return s;
  const mm = (state.monsters||[]).find(x=>x.id===state.master_manual_mid);
  if(!mm || mm._master_acted) return s;
  const atk = (mm.attacks||[{}])[0]; const rng = atk.range || null;
  for(const p of (state.players||[])){
    if(!p.alive) continue;
    const dx=Math.abs(mm.pos[0]-p.pos[0]), dy=Math.abs(mm.pos[1]-p.pos[1]);
    const inR = rng!=null ? Math.max(dx,dy)<=rng : ((dx===1&&dy===0)||(dx===0&&dy===1));
    if(inR) s.add(`${p.pos[0]},${p.pos[1]}`);
  }
  return s;
}
```

- [ ] **Step 2: Injetar no render 2D**

Em `game.js` (~5146), logo após o bloco `if/else if` que popula `reachable` (a linha que termina `...me.moves_left,reachable);`) e antes de `const attackable=new Set();`, inserir:

```javascript
  if(GS.isMaster()){
    _masterReachSet(state).forEach(k => reachable.add(k));
  }
```

E logo após o bloco que popula `attackable` do animado (a linha `attackable.add(\`${ax+ddx*r},${ay+ddy*r}\`);` e seu fechamento), antes de `const weaponRangeTiles`, inserir:

```javascript
  if(GS.isMaster()){
    _masterAttackSet(state).forEach(k => attackable.add(k));
  }
```

- [ ] **Step 3: Injetar no render 3D**

Em `game.js` (~14673), logo após o bloco `if/else if` que popula `reachable` (linha `...me.moves_left, reachable);`) e antes de `// Attackable tiles`, inserir:

```javascript
  if(GS.isMaster()){
    _masterReachSet(state).forEach(k => reachable.add(k));
  }
```

E logo após o bloco do `attackable3d` do animado (~14698), antes de `// Durante a mira de magia`, inserir:

```javascript
  if(GS.isMaster()){
    _masterAttackSet(state).forEach(k => attackable3d.add(k));
  }
```

- [ ] **Step 4: Reescrever o ramo mestre do `handleTileClick`**

Em `game.js` (~21183), substituir o bloco:

```javascript
  if(GS.isMaster()){
    if(window._modoImplantarReforco){
      GS.mestreImplantarReforco(window._modoImplantarReforco, tx, ty);
      window._modoImplantarReforco = null;
      return;
    }
    const mon = _monstroEmCasa(tx, ty);
    if(mon) renderFichaMonstro(mon);
    return;
  }
```

por:

```javascript
  if(GS.isMaster()){
    if(window._modoImplantarReforco){
      GS.mestreImplantarReforco(window._modoImplantarReforco, tx, ty);
      window._modoImplantarReforco = null;
      return;
    }
    const st = GS.gameState;
    const manualMid = st && st.master_manual_mid;
    if(manualMid){
      const mm = (st.monsters||[]).find(x=>x.id===manualMid);
      // 1) herói no alcance → ataca
      const alvo = (st.players||[]).find(p=>p.alive && p.pos[0]===tx && p.pos[1]===ty);
      if(mm && alvo && !mm._master_acted){
        const atk=(mm.attacks||[{}])[0]; const rng=atk.range||null;
        const dx=Math.abs(mm.pos[0]-tx), dy=Math.abs(mm.pos[1]-ty);
        const inR = rng!=null ? Math.max(dx,dy)<=rng : ((dx===1&&dy===0)||(dx===0&&dy===1));
        if(inR){ GS.mestreAtacarMonstro(manualMid, alvo.id); return; }
      }
      // 2) casa azul → move
      if((st.master_manual_reach||[]).some(([x,y])=>x===tx&&y===ty)){
        GS.mestreMoverMonstroPara(manualMid, tx, ty); return;
      }
    }
    const mon = _monstroEmCasa(tx, ty);
    if(mon) renderFichaMonstro(mon);
    return;
  }
```

- [ ] **Step 5: Tirar as setas do `renderMasterHud` e abrir a ficha do monstro Manual**

Em `game.js` (~10272), substituir o bloco `${manualMid ? ` ... `} : ''}` (o `<div class="mestre-manual">` com `.mestre-manual-setas`) por:

```javascript
    ${manualMid ? `
    <div class="mestre-manual">
      <div class="mestre-manual-dica">Clique numa casa azul para mover · num herói no alcance para atacar.</div>
      <button class="mestre-atacar">⚔️ Atacar (alvo do seletor)</button>
      <button class="mestre-encerrar">Encerrar monstro</button>
    </div>` : ''}
```

Em seguida, no bloco de wiring `if(manualMid){ ... }` (~10305), **remover** o `host.querySelectorAll('.mestre-manual-setas button')...` inteiro, mantendo o wiring de `.mestre-atacar` e `.mestre-encerrar`. O bloco fica:

```javascript
  if(manualMid){
    const atkBtn = host.querySelector('.mestre-atacar');
    if(atkBtn) atkBtn.onclick = () => {
      if(selAlvo && selAlvo.value) GS.mestreAtacarMonstro(manualMid, selAlvo.value);
      else toast('Escolha um alvo (herói) antes de atacar.', 'var(--orange)');
    };
    const fimBtn = host.querySelector('.mestre-encerrar');
    if(fimBtn) fimBtn.onclick = () => GS.mestreEncerrarMonstro(manualMid);
  }
```

Por fim, logo antes do fechamento da função `renderMasterHud` (depois do wiring dos `.mestre-reforco-btn`), inserir a auto-abertura da ficha do monstro Manual quando ele muda:

```javascript
  if(manualMid && window._lastManualFichaMid !== manualMid){
    const mm = (state.monsters||[]).find(x=>x.id===manualMid);
    if(mm) renderFichaMonstro(mm);
    window._lastManualFichaMid = manualMid;
  }
  if(!manualMid) window._lastManualFichaMid = null;
```

- [ ] **Step 6: Verificação (leitura + app)**

Não há teste unitário de JS neste ambiente. Conferir por leitura que:
- `_masterReachSet`/`_masterAttackSet` existem e são chamados nos 2 renders (2D e 3D).
- O ramo mestre do `handleTileClick` referencia `GS.mestreMoverMonstroPara` e `GS.mestreAtacarMonstro` (que existem após a Task 4).
- Não sobrou nenhuma referência a `mestre-manual-setas` nem a `GS.mestreMoverMonstro` em `game.js`:

Run: `grep -n "mestre-manual-setas\|mestreMoverMonstro\b" game.js`
Expected: nenhuma linha (só `mestreMoverMonstroPara`, se aparecer).

- [ ] **Step 7: Commit**

```bash
git add game.js
git commit -m "feat(mestre): realce azul + clique-para-mover/atacar o monstro manual; tira setas"
```

---

### Task 6: Cliente — ficha com Ações/Passivas (usos/recarga) + reposição à direita

**Files:**
- Modify: `game.js` (`renderFichaMonstro` ~10330; helper novo abaixo dela)
- Modify: `game.css` (`#ficha-monstro` ~566; novas regras `.fm-*`)

- [ ] **Step 1: Reescrever `renderFichaMonstro` com seções de ação**

Em `game.js`, substituir **toda** a função `renderFichaMonstro` (~10330–10355) por:

```javascript
function renderFichaMonstro(m){
  if(!m){ return; }
  let host = document.getElementById('ficha-monstro');
  if(!host){ host = document.createElement('div'); host.id = 'ficha-monstro'; document.body.appendChild(host); }
  host.style.display = 'block';
  const st = GS.gameState;
  const isManual = !!(st && st.master_manual_mid === m.id);
  const acted = !!m._master_acted;
  const linhaAtaque = (a) => {
    const dano = a.damage || a.dano || '';
    const b = (a.atk_bonus!=null) ? (a.atk_bonus>=0?'+':'')+a.atk_bonus : '';
    return `<div class="fm-atk">⚔️ ${a.name||a.nome||'Ataque'} ${b} · ${dano}</div>`;
  };
  const ativavel = (a) => a.action_type!=='passiva' && a.save!=null && a.dc!=null;
  const usosRest = (a) => {
    const lim = (a.uses_per_combat!=null) ? a.uses_per_combat
              : (a.uses_per_day!=null ? a.uses_per_day : null);
    if(lim==null) return '∞';
    const u = (m.ability_uses||{})[a.id];
    return (u!=null ? u : lim);
  };
  const cdRest = (a) => (m.ability_cooldowns||{})[a.id] || 0;
  const abis = m.special_abilities||[];
  const ativas   = abis.filter(a => a.action_type && a.action_type!=='passiva');
  const passivas = abis.filter(a => !a.action_type || a.action_type==='passiva');
  const linhaAcao = (a) => {
    const ok = ativavel(a);
    const cd = cdRest(a), usos = usosRest(a);
    const semUso = (usos===0 || usos==='0');
    const podeUsar = isManual && !acted && ok && cd===0 && !semUso;
    const meta = `<span class="fm-ab-meta">usos: ${usos} · recarga: ${cd>0?cd+'r':'—'}</span>`;
    const ctrl = ok
      ? `<button class="fm-usar" data-abid="${a.id}"${podeUsar?'':' disabled'}>Ativar</button>`
      : `<span class="fm-ia">IA apenas</span>`;
    return `<div class="fm-hab fm-acao"><div class="fm-ab-top"><b>${a.name||a.nome||a.id}</b> ${ctrl}</div>`+
           `<div class="fm-ab-desc">${a.descricao||a.desc||''}</div>${meta}</div>`;
  };
  const linhaHab = (h) => `<div class="fm-hab"><b>${h.name||h.nome||h.id}</b> — ${h.descricao||h.desc||''}</div>`;
  const ataques = (m.attacks||[]).map(linhaAtaque).join('') ||
                  (m.atk_bonus!=null ? linhaAtaque({name:'Ataque', atk_bonus:m.atk_bonus, damage:m.damage}) : '');
  const stat = (lbl,v)=> (v!=null? `<span class="fm-stat">${lbl} ${v}</span>` : '');
  host.innerHTML =
    `<div class="fm-head"><span class="fm-emoji">${m.emoji||'👾'}</span>`+
    `<span class="fm-nome">${m.name||m.type||'Monstro'}</span>`+
    `<button class="fm-close" title="Fechar">✕</button></div>`+
    `<div class="fm-vitais">❤️ ${m.hp}/${m.max_hp||m.hp} · 🛡️ CA ${m.ac??'—'} · 👣 ${m.movement??'—'}</div>`+
    `<div class="fm-stats">${stat('FOR',m.str_)}${stat('DES',m.dex)}${stat('CON',m.con_)}${stat('INT',m.int_)}`+
    `${stat('Fort',m.fort)}${stat('Ref',m.ref_)}${stat('Von',m.will)}</div>`+
    (ataques? `<div class="fm-sec">Ataques</div>${ataques}`:'')+
    (ativas.length? `<div class="fm-sec">Ações</div>${ativas.map(linhaAcao).join('')}`:'')+
    (passivas.length? `<div class="fm-sec">Passivas</div>${passivas.map(linhaHab).join('')}`:'');
  host.querySelector('.fm-close').onclick = () => { host.style.display='none'; };
  host.querySelectorAll('.fm-usar').forEach(btn => {
    btn.onclick = () => _mestreAtivarHabilidade(m, btn.dataset.abid);
  });
}

// Ativar (mestre): mira um herói no alcance e envia mestre_usar_habilidade.
function _mestreAtivarHabilidade(m, abid){
  const st = GS.gameState; if(!st) return;
  const ab = (m.special_abilities||[]).find(a=>a.id===abid);
  if(!ab) return;
  const rng = ab.range || null;
  const alvos = (st.players||[]).filter(p => {
    if(!p.alive) return false;
    const dx=Math.abs(m.pos[0]-p.pos[0]), dy=Math.abs(m.pos[1]-p.pos[1]);
    return rng!=null ? Math.max(dx,dy)<=rng : ((dx===1&&dy===0)||(dx===0&&dy===1));
  });
  if(!alvos.length){ toast(`Nenhum herói ${rng?('a até '+rng+'q'):'adjacente'}.`, 'var(--orange)'); return; }
  openTargetModal(`${ab.name||abid} — Escolha o alvo`, alvos, 'player',
    (alvoId)=> GS.mestreUsarHabilidade(m.id, abid, alvoId));
}
```

- [ ] **Step 2: Reposicionar a ficha à direita e estilizar as ações**

Em `game.css` (~566), trocar a primeira linha do bloco `#ficha-monstro{`:

```css
  position:fixed; left:12px; bottom:12px; width:280px; z-index:60;
```

por:

```css
  position:fixed; right:12px; bottom:12px; width:250px; z-index:60;
```

E, logo após a última regra `#ficha-monstro .fm-atk, #ficha-monstro .fm-hab{ ... }` (~580), inserir:

```css
#ficha-monstro .fm-acao{ border-top:1px dotted var(--border,#5a4632); padding-top:4px; margin-top:4px; }
#ficha-monstro .fm-ab-top{ display:flex; align-items:center; justify-content:space-between; gap:6px; }
#ficha-monstro .fm-ab-desc{ font-size:.76rem; opacity:.85; line-height:1.25; margin:2px 0; }
#ficha-monstro .fm-ab-meta{ font-size:.7rem; color:var(--text2,#a89878); }
#ficha-monstro .fm-usar{ background:#7a2a20; color:#fff; border:none; border-radius:6px; font-size:.72rem; padding:3px 8px; cursor:pointer; }
#ficha-monstro .fm-usar:hover:not(:disabled){ background:#9a3428; }
#ficha-monstro .fm-usar:disabled{ opacity:.4; cursor:not-allowed; }
#ficha-monstro .fm-ia{ font-size:.68rem; color:var(--text2,#a89878); font-style:italic; }
```

- [ ] **Step 3: Verificação (leitura)**

Run: `grep -n "_mestreAtivarHabilidade\|mestreUsarHabilidade" game.js`
Expected: `renderFichaMonstro` chama `_mestreAtivarHabilidade`, que chama `GS.mestreUsarHabilidade`.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(mestre): ficha do monstro à direita com Ações (usos/recarga) e Passivas"
```

---

### Task 7: Smoke test in-app + doc no CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (nova nota na seção do Modo Mestre)

- [ ] **Step 1: Rodar a suíte do servidor uma última vez**

Run: `python tools/test_modo_mestre.py`
Expected: `=== N passaram, 0 falharam ===`.

- [ ] **Step 2: Smoke test in-app (2 abas: 1 mestre + 1 herói)**

Subir o jogo (`iniciar.bat` ou `python server.py` → `http://localhost:8765/index.html`). Numa aba assumir Mestre, noutra um herói; iniciar a masmorra; pôr um monstro em Manual e esperar a iniciativa dele. Conferir:
- Ao abrir a janela Manual, as casas alcançáveis aparecem em **azul** (respeitando o `movement` do monstro) e a **ficha** abre à direita (abaixo do HUD do mestre).
- Clicar numa casa azul move o monstro até lá (gasta o orçamento; o azul encolhe).
- Clicar num herói adjacente/no alcance ataca.
- Se o monstro tiver habilidade ativa do editor (save+dc), o botão **Ativar** abre a mira e aplica o efeito; usos/recarga atualizam; habilidades sem save/dc aparecem como **IA apenas**.
- Ativar habilidade impede atacar no mesmo turno (ação consumida); mover ainda é permitido.
- "Encerrar monstro" passa a vez.

- [ ] **Step 3: Documentar no CLAUDE.md**

Em `CLAUDE.md`, na seção do Modo Mestre (após a nota "Camada B — Reforços" ou junto às notas do mestre), inserir:

```markdown
> **Modo Mestre — Controle manual do monstro (SP1):** na janela Manual, o monstro
> se move como um herói — as casas alcançáveis (BFS footprint-aware sobre o
> `movement` real, autoritativo em `_master_reach_bfs`/`_master_monster_reach`,
> enviado em `game_state.master_manual_reach`) aparecem em azul; clicar numa delas
> anda até lá via `mestre_mover_monstro_para`→`handle_mestre_mover_monstro_para`
> (path-walk por `_master_path_to` + `_commit_monster_step`, gastando
> `master_moves_left`). As setas do HUD saíram. Clicar num herói no alcance ataca
> (reusa `mestre_atacar_monstro`). A ficha (`renderFichaMonstro`, agora à direita
> abaixo do HUD) ganhou seção **Ações**: habilidades ativas resolvíveis por
> `_use_monster_ability` (save+dc — as do editor de criaturas) têm botão **Ativar**
> (`mestre_usar_habilidade`→`handle_mestre_usar_habilidade`, mira um herói, consome
> a ação via `_master_acted`, mostra usos/recarga de `ability_uses`/
> `ability_cooldowns`); as demais aparecem como "IA apenas"
> (`_habilidade_ativavel_manual` é o ponto de plugagem futuro). Sem mestre,
> byte-idêntico. SP2 (pendente): inventário de itens do monstro. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-17-modo-mestre-controle-manual-monstro-sp1*`.
> Teste: `tools/test_modo_mestre.py` (seções [25]/[26]).
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(mestre): SP1 controle manual do monstro (movimento + ficha de ações)"
```

---

## Notas de verificação

- **Server:** cada task de servidor é TDD via `tools/test_modo_mestre.py` (harness `check()`), rodado com `python tools/test_modo_mestre.py`. As seções `[8]`/`[8b]` foram migradas do handler de setas para o de destino na Task 2.
- **Client:** sem runner de JS aqui — verificação por leitura (grep) + smoke in-app na Task 7 (padrão das fases anteriores do Modo Mestre).
- **Paridade sem-mestre:** todos os caminhos novos gateiam por `GS.isMaster()` (cliente) e `pid==master_pid`/janela Manual (servidor); sem mestre nada é exercido.
