# Instrumentos do Bardo — Fase 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 3 instrumentos (Trompa/Lira/Flauta) ao sistema da Fase 1 — Chamado do General (cone com medo + penalidade de movimento), Dueto Marcial (ataque reativo do bardo) e Dueto Fantasma (eco de dano) — reusando o framework existente e uma penalidade de movimento de monstro compartilhada.

**Architecture:** Nenhuma mudança de framework. Cada instrumento é uma entrada nova em `INSTRUMENTOS_BASE` + um handler `_instr_*` despachado por `efeito.tipo` em `handle_usar_instrumento`. Lira/Flauta ligam buffs de duração cujos efeitos são disparados por hooks em `handle_attack` (ao lado de `_furtivo_reativo`). A penalidade de movimento reusa o mecanismo da Cola (`mov_reduzido_orig`/`mov_reduzido_rodadas`).

**Tech Stack:** Python (`server.py`), Vanilla JS (`src/gameState.js`, `game.js`), testes `tools/test_instrumentos_bardo.py`.

**Spec:** `docs/superpowers/specs/2026-07-11-instrumentos-bardo-fase2-design.md`

---

## Convenções/pontos reusados (confirmados; verificar por leitura antes de editar)
- `INSTRUMENTOS_BASE` (server.py ~163) + `handle_usar_instrumento` (dispatch por `base["efeito"]["tipo"]`, ~4926) + os `_instr_*` da Fase 1.
- `_cone_tiles(self, ox, oy, dx, dy, comp, base)` (~10604) → `set` de `(x,y)`.
- `_save_mostrado(self, alvo, tipo, dif)` async → `(passou, …)`; `tipo="vontade"`.
- `_instrumento_cd(self, bardo, inst)`; `_distancia_chebyshev(a,b)` (módulo); `_ataque_basico_reativo(self, atacante, alvo)` async (~6223); `_monster_dies` async; `roll_dice`, `mod`, `gm_say`, `send_to`.
- Medo de monstro: `m["com_medo"]=True; m["medo_rodadas"]=N` (reusa `_processar_medo`/`_fugir_monstro`).
- Movimento reduzido (Cola): `m["mov_reduzido_orig"]`/`m["mov_reduzido_rodadas"]`, restaurados 1×/turno em `_processar_*_turno` (~9950). Os ~20 ramos de IA leem `m.get("movement",…)` — por isso reduzir `m["movement"]` diretamente é o caminho.
- Hook de ataque de jogador: `handle_attack` chama `await self._furtivo_reativo(p, target)` na resolução do acerto (site principal ~6577, com `dmg`/`p`/`target` em escopo).
- Cliente: `usarInstrumento` sender (~1260), `acionarInstrumento` (game.js ~7647), tooltip já lê `desc`/stats de `INSTRUMENTOS_BASE`.

---

## Task 1: Penalidade de movimento compartilhada + retro-fix do Tambor Velho

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append ao arquivo de teste):

```python
def test_reduzir_mov_monstro():
    room, p = _room_bardo(); _mute(room)
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room._reduzir_mov_monstro(m, 2, 1)
    assert m["movement"] == 4
    assert m["mov_reduzido_orig"] == 6
    assert m["mov_reduzido_rodadas"] == 1
    # piso 1 e maior redução vence
    room._reduzir_mov_monstro(m, 100, 1)
    assert m["movement"] == 1
    assert m["mov_reduzido_orig"] == 6   # original preservado

def test_tambor_velho_reduz_movimento():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "velho")  # raio1, 1d2, push0
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [5, 5], "alive": True, "movement": 6}
    room.monsters["m1"] = m
    async def _falha(*a, **k): return (False, 1, 0, 1)
    async def _d(n, faces, label): return 1
    room._save_mostrado = _falha; room._rolar_dano_mostrado = _d
    _run(room.handle_usar_instrumento("p1", {}))
    assert m["movement"] == 5   # push=0 → -1 movimento (lacuna da Fase 1 fechada)
```

- [ ] **Step 2** — Run `python tools/test_instrumentos_bardo.py` → FAIL (`_reduzir_mov_monstro` ausente).

- [ ] **Step 3 — implementar.** Adicionar o helper dentro de `GameRoom` (perto de `_instr_acorde_trovejante`):

```python
    def _reduzir_mov_monstro(self, m, val, rodadas):
        """Reduz o movimento do monstro por `rodadas` turnos, reusando o mecanismo
        da Cola (mov_reduzido_orig/rodadas, restaurado em _processar_*_turno).
        Empilha pela MAIOR redução e MAIOR duração; piso 1; nunca aumenta o mov."""
        if val <= 0 or rodadas <= 0:
            return
        if "mov_reduzido_orig" not in m:
            m["mov_reduzido_orig"] = m.get("movement", 5)
        orig = m["mov_reduzido_orig"]
        novo = max(1, orig - val)
        m["movement"] = min(m.get("movement", orig), novo)
        m["mov_reduzido_rodadas"] = max(m.get("mov_reduzido_rodadas", 0), rodadas)
```

Retro-fix: em `_instr_acorde_trovejante`, no ramo `push == 0` (Tambor Velho), TROCAR a
escrita dos campos `mov_pen_*` (não lidos) por uma chamada ao helper. Localizar:

```python
                else:
                    m["mov_pen_val"] = 1
                    m["mov_pen_ate"] = self.round_num + 1
```
por:
```python
                else:
                    self._reduzir_mov_monstro(m, 1, 1)   # Tambor Velho: -1 movimento
```

- [ ] **Step 4** — Run tests → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): penalidade de mov de monstro (reusa Cola) + retro-fix Tambor Velho"
```

---

## Task 2: Trompa de Guerra — Chamado do General

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):

```python
def test_chamado_general_falha_medo_e_pen():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")  # cone5 pen_falha2 pen_suc1
    dentro = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    fora   = {"id": "m2", "name": "Ogro",   "hp": 20, "pos": [5, 1], "alive": True, "movement": 6}
    room.monsters = {"m1": dentro, "m2": fora}
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert dentro.get("com_medo") is True and dentro["medo_rodadas"] == 1
    assert dentro["movement"] == 4          # 6 - pen_falha 2
    assert fora.get("com_medo") is None     # fora do cone, intacto
    assert fora["movement"] == 6

def test_chamado_general_sucesso_so_pen_menor():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room.monsters = {"m1": m}
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert m.get("com_medo") is None
    assert m["movement"] == 5                # 6 - pen_sucesso 1

def test_chamado_general_sem_direcao_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("trompa", "padrao")
    m = {"id": "m1", "name": "Goblin", "hp": 20, "pos": [6, 5], "alive": True, "movement": 6}
    room.monsters = {"m1": m}
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))     # sem dir
    assert p["fome"] == fome0 and m["movement"] == 6
```

- [ ] **Step 2** — Run → FAIL (base `trompa` inexistente / handler ausente).

- [ ] **Step 3 — implementar.**

3a. Nova entrada em `INSTRUMENTOS_BASE` (após `alaude`):
```python
    "trompa": {
        "nome": "Trompa de Guerra", "icon": "📯", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Chamado do General",
        "desc": "Sopra a trompa num cone à frente. Inimigos fazem Vontade: falha = Amedrontados (fogem) + perdem movimento; sucesso = perdem menos movimento.",
        "efeito": {"tipo": "chamado_general", "save": "vontade"},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede", "alcance"],
        "stats": {
            "velho":   {"cone": 3, "medo": 1, "pen_falha": 0, "pen_sucesso": 0},
            "rustico": {"cone": 4, "medo": 1, "pen_falha": 1, "pen_sucesso": 0},
            "padrao":  {"cone": 5, "medo": 1, "pen_falha": 2, "pen_sucesso": 1},
        },
    },
```

3b. Handler (perto dos outros `_instr_*`):
```python
    async def _instr_chamado_general(self, p, inst, st, data):
        """Cone direcional; Vontade → falha: medo + penalidade de mov.; sucesso:
        penalidade menor."""
        dirv = (data or {}).get("dir") or [0, 0]
        dx = 1 if dirv[0] > 0 else -1 if dirv[0] < 0 else 0
        dy = 1 if dirv[1] > 0 else -1 if dirv[1] < 0 else 0
        if dx == 0 and dy == 0:
            await self.send_to(p["id"], {"type": "error", "msg": "Escolha uma direção para o Chamado."}); return False
        comp = st["cone"]
        tiles = self._cone_tiles(p["pos"][0], p["pos"][1], dx, dy, comp, comp)
        alvos = [m for m in self.monsters.values()
                 if m.get("hp", 0) > 0 and tuple(m["pos"]) in tiles]
        if not alvos:
            await self.send_to(p["id"], {"type": "error", "msg": "Nenhum inimigo no cone."}); return False
        await self.gm_say(f"📯 **{p['name']}** sopra o **Chamado do General** (cone {comp})!")
        cd = self._instrumento_cd(p, inst)
        for m in alvos:
            save_ok, *_ = await self._save_mostrado(m, "vontade", cd)
            if not save_ok:
                m["com_medo"] = True
                m["medo_rodadas"] = st["medo"]
                if st.get("pen_falha", 0) > 0:
                    self._reduzir_mov_monstro(m, st["pen_falha"], 1)
                await self.gm_say(f"📯 **{m['name']}** entra em pânico (Amedrontado {st['medo']}r)!")
            else:
                if st.get("pen_sucesso", 0) > 0:
                    self._reduzir_mov_monstro(m, st["pen_sucesso"], 1)
                await self.gm_say(f"📯 **{m['name']}** resiste, mas hesita.")
        return True
```

3c. Dispatch em `handle_usar_instrumento` (ao lado dos `elif tipo == ...`):
```python
        elif tipo == "chamado_general":
            ok = await self._instr_chamado_general(p, inst, st, data)
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Chamado do General (Trompa) — cone Vontade + medo + pen mov"
```

---

## Task 3: Lira — Dueto Marcial (ativação + hook reativo + cota)

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):

```python
def test_dueto_marcial_ativa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")  # dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["dueto_marcial_ate"] == room.round_num + 3
    assert p["instrumento_usado"] is True
    assert p["action_done"] is False   # 1 mão

def test_dueto_marcial_reage_cap_1():
    room, p = _room_bardo(); _mute(room)   # p = bardo em [5,5]
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}  # adjacente ao bardo
    room.players["a1"] = ally
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m   # adjacente ao bardo
    reacoes = []
    async def _react(bardo, alvo): reacoes.append((bardo["id"], alvo["id"]))
    room._ataque_basico_reativo = _react
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))   # 2ª na mesma rodada
    assert reacoes == [("p1", "m1")]   # cap 1/rodada

def test_dueto_marcial_runico_cap_2():
    room, p = _room_bardo(); _mute(room)
    inst = server.criar_instrumento("lira", "padrao"); inst["encantamento"] = "runico"
    p["gear"]["off_hand"] = inst
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}
    room.players["a1"] = ally
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    reacoes = []
    async def _react(bardo, alvo): reacoes.append(1)
    room._ataque_basico_reativo = _react
    for _ in range(3):
        _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    assert len(reacoes) == 2   # Rúnico: 2/rodada

def test_dueto_marcial_guardas():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("lira", "padrao")
    p["dueto_marcial_ate"] = room.round_num + 3
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "pos": [5, 6]}
    room.players["a1"] = ally
    longe = {"id": "m2", "name": "Longe", "hp": 9, "max_hp": 9, "ac": 5, "pos": [9, 9], "alive": True}
    room.monsters["m2"] = longe   # NÃO adjacente ao bardo
    reacoes = []
    async def _react(b, a): reacoes.append(1)
    room._ataque_basico_reativo = _react
    _run(room._reacoes_instrumento_apos_ataque(ally, longe, 5))
    assert reacoes == []          # alvo fora de adjacência do bardo
    # sem Lira equipada → não reage
    p["gear"]["off_hand"] = None
    m = {"id": "m1", "name": "Goblin", "hp": 9, "max_hp": 9, "ac": 5, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(ally, m, 5))
    assert reacoes == []
```

- [ ] **Step 2** — Run → FAIL (`lira` / `_reacoes_instrumento_apos_ataque` ausentes).

- [ ] **Step 3 — implementar.**

3a. Entrada `INSTRUMENTOS_BASE`:
```python
    "lira": {
        "nome": "Lira", "icon": "🎼", "maos": 1, "modo": "ativada",
        "habilidade_nome": "Dueto Marcial",
        "desc": "Por algumas rodadas, quando um aliado adjacente a você ataca um inimigo também adjacente a você, você desfere um ataque corpo a corpo grátis nele.",
        "efeito": {"tipo": "dueto_marcial"},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede", "duracao"],
        "stats": {
            "velho":   {"duracao": 1},
            "rustico": {"duracao": 2},
            "padrao":  {"duracao": 3},
        },
    },
```

3b. Handler de ativação + helpers + o hook central (perto dos `_instr_*`):
```python
    async def _instr_dueto_marcial(self, p, inst, st, data):
        p["dueto_marcial_ate"] = self.round_num + st["duracao"]
        await self.gm_say(f"🎼 **{p['name']}** entoa o **Dueto Marcial** por {st['duracao']} rodada(s)!")
        return True

    @staticmethod
    def _instr_base_off(p):
        """Base do instrumento no off_hand, ou None (off_hand pode ter escudo/arma)."""
        off = p.get("gear", {}).get("off_hand")
        return off.get("base") if off and off.get("tipo_item") == "instrumento" else None

    def _dueto_marcial_cap(self, inst):
        return 2 if inst.get("encantamento") == "runico" else 1

    def _bardo_dueto_marcial(self, atacante, alvo):
        """Bardo elegível para revidar via Dueto Marcial (ou None). Reseta a cota da
        rodada se virou a rodada."""
        if not alvo or alvo.get("hp", 0) <= 0:
            return None
        for q in self.players.values():
            if q.get("class_id") != "bard" or not q.get("alive") or q["id"] == atacante["id"]:
                continue
            if q.get("dueto_marcial_ate", 0) < self.round_num:
                continue
            off = q.get("gear", {}).get("off_hand")
            if not off or off.get("tipo_item") != "instrumento" or off.get("base") != "lira":
                continue
            if self._distancia_chebyshev(q["pos"], atacante["pos"]) > 1:
                continue
            if self._distancia_chebyshev(q["pos"], alvo["pos"]) > 1:
                continue
            if q.get("dueto_marcial_round") != self.round_num:
                q["dueto_marcial_round"] = self.round_num
                q["dueto_marcial_usos"] = 0
            if q.get("dueto_marcial_usos", 0) >= self._dueto_marcial_cap(off):
                continue
            return q
        return None

    async def _reacoes_instrumento_apos_ataque(self, atacante, alvo, dmg):
        """Hooks de instrumento disparados por um ataque básico de arma (site
        principal de handle_attack). Dueto Fantasma (Task 4) e Dueto Marcial."""
        # Dueto Marcial — reação do bardo ao ataque de um ALIADO
        if atacante.get("class_id") != "bard":
            bardo = self._bardo_dueto_marcial(atacante, alvo)
            if bardo:
                bardo["dueto_marcial_usos"] = bardo.get("dueto_marcial_usos", 0) + 1
                await self._ataque_basico_reativo(bardo, alvo)
```

> Nota: a rama Dueto Fantasma é adicionada a este mesmo método na Task 4.

3c. Dispatch:
```python
        elif tipo == "dueto_marcial":
            ok = await self._instr_dueto_marcial(p, inst, st, data)
```

3d. Ligar o hook em `handle_attack`: localizar `await self._furtivo_reativo(p, target)`
(site principal ~6577, DEPOIS de `target["hp"] -= dmg`) e adicionar na linha seguinte:
```python
                await self._reacoes_instrumento_apos_ataque(p, target, dmg)
```
(usar os nomes reais do site: `p` = atacante, `target` = monstro, `dmg` = dano do golpe.)

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Dueto Marcial (Lira) — ataque reativo do bardo, cota 1/rodada (2 Runico)"
```

---

## Task 4: Flauta — Dueto Fantasma (eco de dano)

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):

```python
def test_dueto_fantasma_ativa_e_ecoa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("flauta", "padrao")  # fracao 50, dur 3
    _run(room.handle_usar_instrumento("p1", {}))
    assert p["dueto_fantasma_ate"] == room.round_num + 3
    assert p["dueto_fantasma_fracao"] == 50
    assert p["action_done"] is False   # 1 mão
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 15   # eco = 10*50//100 = 5

def test_dueto_fantasma_sem_flauta_nao_ecoa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = None
    p["dueto_fantasma_ate"] = room.round_num + 3
    p["dueto_fantasma_fracao"] = 50
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 20

def test_dueto_fantasma_expira():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("flauta", "padrao")
    p["dueto_fantasma_ate"] = room.round_num - 1   # expirado
    p["dueto_fantasma_fracao"] = 50
    m = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "pos": [6, 5], "alive": True}
    room.monsters["m1"] = m
    _run(room._reacoes_instrumento_apos_ataque(p, m, 10))
    assert m["hp"] == 20
```

- [ ] **Step 2** — Run → FAIL (`flauta` / rama do eco ausentes).

- [ ] **Step 3 — implementar.**

3a. Entrada `INSTRUMENTOS_BASE`:
```python
    "flauta": {
        "nome": "Flauta", "icon": "🎶", "maos": 1, "modo": "ativada",
        "habilidade_nome": "Dueto Fantasma",
        "desc": "Invoca uma ilusão por algumas rodadas. Cada ataque básico seu que acerta é repetido pela ilusão no mesmo alvo, causando uma fração do dano.",
        "efeito": {"tipo": "dueto_fantasma"},
        "custo_fome": 3, "custo_sede": 3,
        "afixos_validos": ["fome", "sede", "duracao"],
        "stats": {
            "velho":   {"duracao": 1, "fracao": 25},
            "rustico": {"duracao": 2, "fracao": 40},
            "padrao":  {"duracao": 3, "fracao": 50},
        },
    },
```

3b. Handler de ativação:
```python
    async def _instr_dueto_fantasma(self, p, inst, st, data):
        p["dueto_fantasma_ate"] = self.round_num + st["duracao"]
        p["dueto_fantasma_fracao"] = st["fracao"]
        await self.gm_say(f"🎶 **{p['name']}** conjura o **Dueto Fantasma** por {st['duracao']} rodada(s)!")
        return True
```

3c. Adicionar a rama do eco NO INÍCIO de `_reacoes_instrumento_apos_ataque` (antes da
rama Dueto Marcial da Task 3):
```python
        # Dueto Fantasma — eco do próprio ataque do bardo (metade/fração do dano)
        if atacante.get("class_id") == "bard" and atacante.get("alive") \
           and atacante.get("dueto_fantasma_ate", 0) >= self.round_num \
           and self._instr_base_off(atacante) == "flauta" \
           and alvo and alvo.get("hp", 0) > 0:
            eco = (dmg * atacante.get("dueto_fantasma_fracao", 0)) // 100
            if eco > 0:
                alvo["hp"] = max(0, alvo["hp"] - eco)
                await self.gm_say(f"🎶 A ilusão do **Dueto Fantasma** repete o golpe em **{alvo['name']}**: **{eco}** de dano!")
                if alvo["hp"] <= 0:
                    await self._monster_dies(alvo, atacante.get("id"))
                    return   # alvo morto — encerra
```

3d. Dispatch:
```python
        elif tipo == "dueto_fantasma":
            ok = await self._instr_dueto_fantasma(p, inst, st, data)
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Dueto Fantasma (Flauta) — eco de fracao do dano no ataque do bardo"
```

---

## Task 5: SKUs de loja (Trompa/Lira/Flauta)

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste que falha** (append):
```python
def test_skus_fase2_existem():
    for base in ("trompa", "lira", "flauta"):
        sku = server.instrumento_sku(base, "padrao", preco=200)
        assert sku["tipo_item"] == "instrumento" and sku["base"] == base
        assert sku["allowed_classes"] == ["bard"]
    # e estão listadas no mercador
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_trompa_padrao" in ids
    assert "instrumento_lira_padrao" in ids
    assert "instrumento_flauta_padrao" in ids
```

- [ ] **Step 2** — Run → FAIL (SKUs não listadas).

- [ ] **Step 3 — implementar.** Localizar o bloco de instrumentos em `SHOP_MERCHANT`
(adicionado na Fase 1 via `instrumento_sku(...)`) e acrescentar:
```python
    instrumento_sku("trompa", "rustico", 150),
    instrumento_sku("trompa", "padrao",  250),
    instrumento_sku("lira",   "rustico", 110),
    instrumento_sku("lira",   "padrao",  200),
    instrumento_sku("flauta", "rustico", 120),
    instrumento_sku("flauta", "padrao",  210),
```

- [ ] **Step 4** — Run → PASS. Também `python tools/test_roteamento_itens.py` (regressão) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): SKUs de loja para Trompa/Lira/Flauta"
```

---

## Task 6: Cliente — direção do Chamado + ativação de Lira/Flauta

**Files:** Modify `src/gameState.js`, `game.js`. **Editar game.js só com Edit/Write (nunca PowerShell).**

- [ ] **Step 1 — sender aceita `dir`.** Em `src/gameState.js`, o `usarInstrumento`
(atualmente `usarInstrumento(target)`) passa a repassar direção:
```javascript
  function usarInstrumento(target, dir) {
    send({ type: 'usar_instrumento',
           target_id: (target && target.id != null) ? target.id : null,
           dir: dir || null });
  }
```
(A assinatura muda de 1 para 2 args; a chamada existente `GS.usarInstrumento(alvo)` /
`GS.usarInstrumento(null)` continua válida — `dir` fica `null`.)

- [ ] **Step 2 — `acionarInstrumento` (game.js).** Localizar a função (~7647). Ela hoje
trata `nota_cortante` (target modal) e o resto (`GS.usarInstrumento(null)`). Adicionar:
- `dueto_marcial` e `dueto_fantasma` → auto (cai no `else` → `GS.usarInstrumento(null)`),
  então NENHUMA mudança é necessária para eles (confirmar que o `else` cobre).
- `chamado_general` → **seletor de direção**. Investigar como uma magia de cone/linha
  (Relâmpago, `alvoTipo='cone'`, ver game.js ~9285 e o retorno `{dir:[dx,dy]}` ~9374)
  coleta a direção no cliente e REUSAR esse fluxo; ao obter `[dx,dy]`, chamar
  `GS.usarInstrumento(null, [dx, dy])`. Se o fluxo de magia for muito acoplado ao
  cast de magia, criar um mini-modal de 8 direções (setas N/NE/L/SE/S/SO/O/NO) que
  chama `GS.usarInstrumento(null, [dx, dy])`. Padrão de código:
```javascript
  if (tipo === 'chamado_general') {
    escolherDirecaoInstrumento(b, (dx, dy) => GS.usarInstrumento(null, [dx, dy]));
    return;
  }
```
Implementar `escolherDirecaoInstrumento(b, cb)` reusando o seletor de direção existente
das magias, OU como um pequeno overlay de 8 botões (reportar qual caminho foi usado).

- [ ] **Step 3 — verificação de sintaxe:** `node --check game.js && node --check src/gameState.js`.

- [ ] **Step 4 — verificação no preview (controlador fará; o subagente NÃO abre o navegador):**
apenas garantir que o código está correto e reportar os pontos para o controlador testar
(equipar Trompa e mirar direção; equipar Lira/Flauta e ativar; tooltips com `desc`).

- [ ] **Step 5 — Commit:**
```bash
git add src/gameState.js game.js
git commit -m "feat(instrumentos): cliente — direcao do Chamado + ativacao de Lira/Flauta"
```

---

## Task 7: Documentação + regressão final

**Files:** Modify `CLAUDE.md`.

- [ ] **Step 1 — CLAUDE.md.** Atualizar o bloco "Instrumentos do Bardo" para citar as
3 novas bases e a penalidade de movimento compartilhada. Acrescentar ao final do bloco
existente uma frase:
```markdown
> **Fase 2 (Trompa/Lira/Flauta):** Chamado do General (Trompa, cone direcional `dir`,
> Vontade → medo `com_medo`/`medo_rodadas` + penalidade de movimento via
> `_reduzir_mov_monstro`, que reusa o mecanismo da Cola `mov_reduzido_*` e fecha a
> lacuna do Tambor Velho da Fase 1); Dueto Marcial (Lira, buff `dueto_marcial_ate`;
> hook `_reacoes_instrumento_apos_ataque` em `handle_attack` faz o bardo revidar
> `_ataque_basico_reativo` quando um aliado adjacente acerta um inimigo adjacente ao
> bardo; cota `_dueto_marcial_cap` = 1/rodada, 2 se Rúnico [Fase 4]); Dueto Fantasma
> (Flauta, buff `dueto_fantasma_ate`/`_fracao`; o mesmo hook ecoa uma fração do dano do
> ataque básico do bardo no mesmo alvo, sem novo teste, sem recursão). Guardas do Ecos
> (bardo vivo + instrumento equipado) aplicadas. Cliente: `acionarInstrumento` usa
> seletor de direção para o Chamado. Fases 3–5 pendentes.
```

- [ ] **Step 2 — regressão completa:**
```bash
python tools/test_instrumentos_bardo.py
python tools/test_bardo_espec.py
python tools/test_tecnicas_espec.py
python tools/test_guilda.py
python tools/test_roteamento_itens.py
python -c "import server"
```
Todos verdes (senão parar e reportar DONE_WITH_CONCERNS).

- [ ] **Step 3 — Commit:**
```bash
git add CLAUDE.md
git commit -m "docs(instrumentos): documenta Fase 2 (Trompa/Lira/Flauta) no CLAUDE.md"
```

---

## Self-Review (cobertura do spec)

- §2 penalidade de movimento (reusa Cola) + retro-fix Tambor Velho → Task 1. ✅
- §3 Chamado do General (cone, Vontade, medo, pen falha/sucesso, stats) → Task 2. ✅
- §4 Dueto Marcial (ativação, hook, adjacência, cota 1/rodada, Rúnico 2, guardas) → Task 3. ✅
- §5 Dueto Fantasma (ativação, eco por fração, hit-only, sem recursão, guardas) → Task 4. ✅
- §6 dispatch + SKUs de loja → Tasks 2–5. ✅
- §6 cliente (sender `dir`, direção do Chamado, auto Lira/Flauta, tooltip) → Task 6. ✅
- §7 testes → Tasks 1–5 (TDD) + Task 7 (regressão). ✅

**Lacunas conhecidas (aceitas):**
- Hook só no site principal de `handle_attack` (~6577); ataques de mão secundária
  (off-hand) de aliados/bardo não disparam Dueto Marcial/Fantasma — consistente com o
  furtivo do Ladino ("1x na mão principal"). Documentar na Task 7 se desejar.
- O seletor de direção do Chamado pode reusar o fluxo de magia OU um mini-modal; o
  caminho exato é decidido na Task 6 (reportado pelo implementador).
