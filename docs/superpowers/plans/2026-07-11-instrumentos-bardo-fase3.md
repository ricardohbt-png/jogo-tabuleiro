# Instrumentos do Bardo — Fase 3 (Réquiem Final / Violino) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar o Violino (Réquiem Final) — habilidade sustentada de alvo único com DoT escalonado, concentração, aura de provocação (taunt) e manutenção por rodada — reusando o framework de instrumentos e os padrões existentes de status/upkeep/IA.

**Architecture:** Uma nova base em `INSTRUMENTOS_BASE` + um handler de ativação; o resto são hooks em pontos de turno já existentes: DoT no início do turno do monstro (junto de paralisia/veneno), manutenção no início do turno do bardo (junto da Canção), taunt na seleção de alvo da IA (junto de `provocado`), concentração nos sites de dano ao jogador. Estado no bardo: `requiem_alvo` (id do monstro) + `requiem_contador` (escalada). No monstro-alvo: `requiem_por` (id do bardo).

**Tech Stack:** Python (`server.py`), Vanilla JS (`game.js`, `src/gameState.js`), testes `tools/test_instrumentos_bardo.py`.

**Spec:** `docs/superpowers/specs/2026-07-11-instrumentos-bardo-fase3-design.md`

---

## Pontos de integração (confirmados; verificar por leitura)
- `INSTRUMENTOS_BASE` (~163) + `handle_usar_instrumento` (dispatch por `base["efeito"]["tipo"]`; cobra custo só se o handler retorna `True`; checa economia de ação antes).
- `_no_raio(self, o, a, r)`; `_tem_linha_de_visao(pos1, pos2)`; `_instrumento_cd`; `_distancia_chebyshev(a,b)` (módulo); `_save_mostrado(self, alvo, tipo, dif, extra_mod=0)` async; `roll_dice`; `_monster_dies` async; `gm_say`, `send_to`, `push_state`.
- Turno do monstro (~15062-15073): `_processar_venenos_turno(m)`, `_processar_paralisacao_turno(m)` — inserir `_processar_requiem_turno(m)` + `if m["hp"]<=0: continue`.
- Turno do bardo (~12730): `_cobrar_manutencao_cancao(cur_p)` — inserir `_cobrar_manutencao_requiem(cur_p)`.
- Seleção de alvo da IA: `_get_monster_primary_target(m, targets)` (~13337) + booleanos `forcado = (m.get("provocado") ...) or bool(self.taunted)` (~14134/14212/14476).
- Sites de dano ao bardo p/ concentração: `_execute_one_monster_attack` (o `target["hp"] -= dmg` de player, ~6737), `_processar_venenos_turno`, `_processar_em_chamas_turno`, `_processar_efeitos_armadilha_turno`.
- `_player_dies(pid)` async, `_monster_dies(m, killer)` async — pontos de limpeza do Réquiem.
- Padrão de manutenção: `_cobrar_manutencao_cancao` (~8147). Padrão de save por turno: `_processar_paralisacao_turno` (~11081).
- Testes: helpers `_room_bardo`/`_run`/`_mute` já existem em `tools/test_instrumentos_bardo.py`. `_room_bardo` já seta `map_w`/`map_h`/`tiles` (Fase 2).

---

## Task 1: Violino base + ativação + toggle-off

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):

```python
def test_requiem_ativa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")  # alcance 6
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert p["requiem_alvo"] == "m1"
    assert p["requiem_contador"] == 0
    assert m["requiem_por"] == "p1"
    assert p["action_done"] is True   # 2 mãos: gasta a ação

def test_requiem_toggle_off():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    fome_apos_ativar = p["fome"]
    p["action_done"] = True   # já atacou depois; toggle-off deve funcionar mesmo assim
    _run(room.handle_usar_instrumento("p1", {}))   # 2ª ativação = desliga
    assert p["requiem_alvo"] is None
    assert m.get("requiem_por") is None
    assert p["fome"] == fome_apos_ativar   # desligar não cobra custo

def test_requiem_fora_de_alcance_recusa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "velho")  # alcance 4
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [12, 5], "alive": True}
    room.monsters["m1"] = m
    room._tem_linha_de_visao = lambda a, b: True
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert p.get("requiem_alvo") is None and p["fome"] == fome0
```

- [ ] **Step 2** — Run `python tools/test_instrumentos_bardo.py` → FAIL (base `violino` / handler ausentes).

- [ ] **Step 3 — implementar.**

3a. `INSTRUMENTOS_BASE` (após `flauta`):
```python
    "violino": {
        "nome": "Violino", "icon": "🎻", "maos": 2, "modo": "ativada",
        "habilidade_nome": "Réquiem Final",
        "desc": "Inicia uma melodia mortal sobre um alvo. A cada turno dele, faz Vontade ou sofre dano crescente (1d, 2d, 3d…). Enquanto toca, o alvo e inimigos a ≤3 do bardo são forçados a atacá-lo, e o bardo testa concentração ao sofrer dano. Manutenção -2🍖/-2💧 por rodada.",
        "efeito": {"tipo": "requiem_final", "save": "vontade"},
        "custo_fome": 4, "custo_sede": 4,
        "manutencao_fome": 2, "manutencao_sede": 2,
        "afixos_validos": ["fome", "sede", "alcance"],
        "stats": {
            "velho":   {"dado": "d2", "teto": 3, "alcance": 4},
            "rustico": {"dado": "d4", "teto": 4, "alcance": 5},
            "padrao":  {"dado": "d6", "teto": 5, "alcance": 6},
        },
    },
```

3b. Toggle-off EARLY em `handle_usar_instrumento`: logo APÓS resolver `inst`/`base`
(depois do check `if base["modo"] != "ativada"`) e ANTES dos checks de economia de ação e
custo, inserir:
```python
        # Réquiem Final: clicar de novo com o Réquiem ativo DESLIGA (grátis, sempre disponível).
        if base["efeito"]["tipo"] == "requiem_final" and p.get("requiem_alvo"):
            await self._encerrar_requiem(p, "desativado manualmente")
            await self.push_state()
            return
```

3c. Handler de ativação (perto dos outros `_instr_*`):
```python
    async def _instr_requiem_final(self, p, inst, st, data):
        """Inicia o Réquiem sobre um alvo (LOS + alcance). O toggle-off é tratado
        antes, em handle_usar_instrumento."""
        alvo_id = (data or {}).get("target_id")
        m = self.monsters.get(alvo_id)
        if not m or m.get("hp", 0) <= 0:
            await self.send_to(p["id"], {"type": "error", "msg": "Alvo inválido."}); return False
        if not self._no_raio(p, m, st["alcance"]):
            await self.send_to(p["id"], {"type": "error",
                "msg": f"Alvo fora do alcance ({st['alcance']} casas)."}); return False
        if not self._tem_linha_de_visao(p["pos"], m["pos"]):
            await self.send_to(p["id"], {"type": "error",
                "msg": "🧱 Sem linha de visão para o alvo."}); return False
        # (recast: se já havia um Réquiem, o toggle-off acima não disparou porque
        #  chegamos aqui só quando NÃO havia requiem_alvo — mas por segurança encerra.)
        if p.get("requiem_alvo"):
            await self._encerrar_requiem(p, "recomeça em novo alvo")
        p["requiem_alvo"] = m["id"]
        p["requiem_contador"] = 0
        m["requiem_por"] = p["id"]
        await self.gm_say(f"🎻 **{p['name']}** inicia o **Réquiem Final** sobre **{m['name']}**!")
        return True
```

3d. `_encerrar_requiem` helper (perto dos `_instr_*`):
```python
    async def _encerrar_requiem(self, bardo, motivo):
        """Encerra o Réquiem do bardo (idempotente). Limpa o estado do bardo e do alvo."""
        if not bardo.get("requiem_alvo"):
            return
        m = self.monsters.get(bardo.get("requiem_alvo"))
        if m:
            m.pop("requiem_por", None)
        bardo["requiem_alvo"] = None
        bardo["requiem_contador"] = 0
        await self.gm_say(f"🎻 O Réquiem Final de **{bardo['name']}** se encerra — {motivo}.")
```

3e. Dispatch em `handle_usar_instrumento`:
```python
        elif tipo == "requiem_final":
            ok = await self._instr_requiem_final(p, inst, st, data)
```

- [ ] **Step 4** — Run → PASS (`_encerrar_requiem` já existe p/ o toggle/recast).
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Violino/Requiem Final — ativacao, alcance/LOS, toggle-off, _encerrar_requiem"
```

---

## Task 2: DoT escalonado + tick no turno do monstro + limpeza na morte

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):

```python
def test_requiem_escalada_e_teto():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "velho")  # dado d2, teto 3
    m = {"id": "m1", "name": "Lich", "hp": 100, "max_hp": 100, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    seq = []
    orig_roll = server.roll_dice
    server.roll_dice = lambda s: (seq.append(s) or 1)
    for _ in range(5):
        _run(room._processar_requiem_turno(m))
    server.roll_dice = orig_roll
    assert seq == ["1d2", "2d2", "3d2", "3d2", "3d2"]   # sobe até o teto 3 e trava

def test_requiem_sucesso_sem_dano():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room._processar_requiem_turno(m))
    assert m["hp"] == 30                 # passou: sem dano
    assert p["requiem_contador"] == 1    # escalada avança mesmo assim

def test_requiem_mata_encerra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 3, "max_hp": 30, "pos": [8, 5], "alive": True}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 0; m["requiem_por"] = "p1"
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    mortes = []
    async def _dies(mon, killer): mortes.append(mon["id"]); mon["hp"] = 0
    room._monster_dies = _dies
    orig_roll = server.roll_dice
    server.roll_dice = lambda s: 10
    _run(room._processar_requiem_turno(m))
    server.roll_dice = orig_roll
    assert mortes == ["m1"]
    assert p["requiem_alvo"] is None     # a morte do alvo encerrou o Réquiem
```

- [ ] **Step 2** — Run → FAIL (`_processar_requiem_turno` ausente).

- [ ] **Step 3 — implementar.**

3a. Processor (perto de `_processar_paralisacao_turno`):
```python
    async def _processar_requiem_turno(self, m):
        """Início do turno do alvo do Réquiem: escala o contador (até o teto), testa
        Vontade; falha = contador×dado; sucesso = sem dano. Encerra se o bardo/violino
        não for mais válido."""
        bid = m.get("requiem_por")
        if not bid:
            return
        bardo = self.players.get(bid)
        off = bardo.get("gear", {}).get("off_hand") if bardo else None
        valido = (bardo and bardo.get("alive") and bardo.get("requiem_alvo") == m["id"]
                  and off and off.get("tipo_item") == "instrumento" and off.get("base") == "violino")
        if not valido:
            m.pop("requiem_por", None)
            if bardo:
                await self._encerrar_requiem(bardo, "instrumento guardado")
            return
        st = self._instrumento_stats(off)
        bardo["requiem_contador"] = min(bardo.get("requiem_contador", 0) + 1, st["teto"])
        n = bardo["requiem_contador"]
        save_ok, *_ = await self._save_mostrado(m, "vontade", self._instrumento_cd(bardo, off))
        if save_ok:
            await self.gm_say(f"🎻 **{m['name']}** resiste ao Réquiem nesta rodada.")
            return
        dano = roll_dice(f"{n}{st['dado']}")
        m["hp"] = max(0, m["hp"] - dano)
        await self.gm_say(f"🎻 O Réquiem Final dilacera **{m['name']}**: {n}{st['dado']} = **{dano}**!")
        if m["hp"] <= 0:
            await self._monster_dies(m, bid)
```

3b. Hook no turno do monstro (~15064, depois do bloco de venenos/mods e do `if m["hp"]<=0: continue`, antes de petrificado/paralisado ou logo após): inserir:
```python
            await self._processar_requiem_turno(m)
            if m["hp"] <= 0:
                continue
```
(colocar após a checagem de hp do bloco de venenos/mods; garantir que roda antes de o monstro agir.)

3c. Limpeza na morte do alvo — em `_monster_dies(self, m, killer_pid)`, logo no início (após confirmar a morte), encerrar o Réquiem se este monstro era um alvo:
```python
        bid_req = m.get("requiem_por")
        if bid_req and self.players.get(bid_req):
            await self._encerrar_requiem(self.players[bid_req], f"{m.get('name','o alvo')} pereceu")
```
(inserir perto do topo de `_monster_dies`; `_encerrar_requiem` é idempotente e limpa `requiem_por` do próprio m.)

- [ ] **Step 4** — Run → PASS. Rodar `python tools/test_tecnicas_espec.py` (exercita `_monster_dies`) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Requiem DoT escalonado (teto por qualidade) + tick no turno do alvo + limpeza na morte"
```

---

## Task 3: Aura de provocação (taunt)

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):

```python
def test_requiem_taunt():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["requiem_alvo"] = "m1"
    alvo   = {"id": "m1", "name": "Lich", "hp": 30, "pos": [12, 12], "alive": True, "requiem_por": "p1"}  # longe, mas é o alvo
    perto  = {"id": "m2", "name": "Goblin", "hp": 10, "pos": [6, 5], "alive": True}   # ≤3 do bardo
    longe  = {"id": "m3", "name": "Ogro", "hp": 10, "pos": [15, 15], "alive": True}   # >3, não é alvo
    room.monsters = {"m1": alvo, "m2": perto, "m3": longe}
    assert room._requiem_forca_bardo(alvo) is p     # o alvo (qualquer distância)
    assert room._requiem_forca_bardo(perto) is p    # dentro do raio 3
    assert room._requiem_forca_bardo(longe) is None # fora e não-alvo
```

- [ ] **Step 2** — Run → FAIL (`_requiem_forca_bardo` ausente).

- [ ] **Step 3 — implementar.**

3a. Helper (perto dos `_instr_*`):
```python
    def _requiem_forca_bardo(self, m):
        """Bardo que este monstro é forçado a atacar por um Réquiem ativo (ou None):
        se `m` é o alvo do Réquiem, ou está a ≤3 de um bardo com Réquiem ativo."""
        bid = m.get("requiem_por")
        if bid and bid in self.players and self.players[bid].get("alive") \
           and self.players[bid].get("requiem_alvo") == m["id"]:
            return self.players[bid]
        for q in self.players.values():
            if q.get("alive") and q.get("requiem_alvo") \
               and _distancia_chebyshev(m["pos"], q["pos"]) <= 3:
                return q
        return None
```

3b. Integrar em `_get_monster_primary_target(m, targets)` (~13337): no INÍCIO, antes do check de `provocado`:
```python
        rb = self._requiem_forca_bardo(m)
        if rb:
            return {"kind": "player", "obj": rb}
```

3c. Integrar nos booleanos `forcado` (localizar as ~3 ocorrências de
`forcado = (m.get("provocado") and m.get("provocado_turnos", 0) > 0) or bool(self.taunted)`
— ~14134/14212/14476) — acrescentar o Réquiem:
```python
            forcado = (m.get("provocado") and m.get("provocado_turnos", 0) > 0) or bool(self.taunted) or bool(self._requiem_forca_bardo(m))
```

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Requiem taunt — alvo + inimigos a <=3 do bardo forcados a ataca-lo"
```

---

## Task 4: Concentração (quebra ao sofrer dano)

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):

```python
def test_concentracao_quebra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["requiem_contador"] = 2
    async def _falha(*a, **k): return (False, 1, 0, 1)
    room._save_mostrado = _falha
    _run(room._concentracao_requiem(p, 12))
    assert p["requiem_alvo"] is None       # concentração quebrou
    assert m.get("requiem_por") is None

def test_concentracao_resiste():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"
    async def _passa(*a, **k): return (True, 20, 0, 20)
    room._save_mostrado = _passa
    _run(room._concentracao_requiem(p, 12))
    assert p["requiem_alvo"] == "m1"       # resistiu, segue tocando

def test_concentracao_cd_8_mais_dano():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"
    cds = []
    async def _cap(alvo, tipo, dif, **k): cds.append(dif); return (True, 20, 0, 20)
    room._save_mostrado = _cap
    _run(room._concentracao_requiem(p, 7))
    assert cds == [15]                     # 8 + 7
```

- [ ] **Step 2** — Run → FAIL (`_concentracao_requiem` ausente).

- [ ] **Step 3 — implementar.**

3a. Helper (perto dos `_instr_*`):
```python
    async def _concentracao_requiem(self, bardo, dano):
        """Bardo sob Réquiem testa Vontade (CD 8+dano) ao sofrer dano; falha encerra.
        Origem Anã (+2) plumbada p/ Fase 4."""
        if not bardo.get("requiem_alvo") or dano <= 0:
            return
        extra = 0
        off = bardo.get("gear", {}).get("off_hand")
        if off and off.get("origem_bonus") == "concentracao":
            extra = 2
        save_ok, *_ = await self._save_mostrado(bardo, "vontade", 8 + dano, extra_mod=extra)
        if not save_ok:
            await self._encerrar_requiem(bardo, "concentração quebrada")
```

3b. Hook no ataque de monstro — em `_execute_one_monster_attack`, no ramo em que o dano é
aplicado ao jogador (`target["hp"] -= dmg`, o mesmo ramo do Ecos), adicionar após o dano:
```python
                if target.get("requiem_alvo") and target.get("hp", 0) > 0:
                    await self._concentracao_requiem(target, dmg)
```
(usar os nomes reais: `target` = jogador atingido, `dmg` = dano.)

3c. Hooks nos ticks de DoT — em cada um dos 3 processadores abaixo, DEPOIS de o dano de tick
ser aplicado a um JOGADOR, chamar o helper com o dano aplicado. Localizar por leitura o ponto
onde o hp do jogador é reduzido em cada:
- `_processar_venenos_turno(alvo)` — se `alvo` é jogador com `requiem_alvo`: `await self._concentracao_requiem(alvo, dano_tick)`.
- `_processar_em_chamas_turno` — no laço, para cada jogador que sofre o tick: `await self._concentracao_requiem(pl, dano_tick)`.
- `_processar_efeitos_armadilha_turno` — para o jogador que sofre o tick de armadilha: `await self._concentracao_requiem(pl, dano_tick)`.
Se algum desses processadores não distinguir jogador de monstro trivialmente, guardar com
`getattr`/`.get("requiem_alvo")` (monstros nunca têm `requiem_alvo`, então o helper é no-op
para eles) — pode-se chamar o helper incondicionalmente após o dano, já que ele retorna cedo
quando o alvo não tem `requiem_alvo`.

- [ ] **Step 4** — Run → PASS. Rodar `python tools/test_arremessaveis_tatico.py` (veneno/armadilha) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Requiem concentracao (Vontade CD 8+dano) nos sites de dano ao bardo"
```

---

## Task 5: Manutenção por rodada + limpeza na morte do bardo

**Files:** Modify `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):

```python
def test_requiem_manutencao_debita():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    p["requiem_alvo"] = "m1"; p["fome"] = 50; p["sede"] = 50
    _run(room._cobrar_manutencao_requiem(p))
    assert p["fome"] == 48 and p["sede"] == 48   # -2/-2
    assert p["requiem_alvo"] == "m1"

def test_requiem_manutencao_sem_recursos_encerra():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("violino", "padrao")
    m = {"id": "m1", "name": "Lich", "hp": 30, "pos": [8, 5], "alive": True, "requiem_por": "p1"}
    room.monsters["m1"] = m
    p["requiem_alvo"] = "m1"; p["fome"] = 1; p["sede"] = 50
    _run(room._cobrar_manutencao_requiem(p))
    assert p["requiem_alvo"] is None       # sem 🍖 suficiente → encerra
    assert m.get("requiem_por") is None
```

- [ ] **Step 2** — Run → FAIL (`_cobrar_manutencao_requiem` ausente).

- [ ] **Step 3 — implementar.**

3a. Helper (perto de `_cobrar_manutencao_cancao`):
```python
    async def _cobrar_manutencao_requiem(self, p):
        """Upkeep do Réquiem, cobrado no início do turno do bardo. Sem recursos, encerra."""
        if not p.get("requiem_alvo"):
            return
        off = p.get("gear", {}).get("off_hand")
        base = INSTRUMENTOS_BASE.get(off.get("base")) if off and off.get("tipo_item") == "instrumento" else None
        if not base or off.get("base") != "violino":
            await self._encerrar_requiem(p, "instrumento guardado")
            return
        mf = base.get("manutencao_fome", 2)
        ms = base.get("manutencao_sede", 2)
        if p["fome"] < mf or p["sede"] < ms:
            await self._encerrar_requiem(p, "recursos insuficientes")
            return
        p["fome"] = max(0, p["fome"] - mf)
        p["sede"] = max(0, p["sede"] - ms)
        await self.gm_say(f"🎻 Réquiem Final de **{p['name']}** — manutenção 🍖-{mf} 💧-{ms}.")
```

3b. Hook no turno do bardo (~12730, junto de `_cobrar_manutencao_cancao(cur_p)`): inserir na
linha seguinte:
```python
            await self._cobrar_manutencao_requiem(cur_p)
```

3c. Limpeza na morte do bardo — em `_player_dies(self, pid)`, encerrar o Réquiem do morto:
```python
        _mp = self.players.get(pid)
        if _mp and _mp.get("requiem_alvo"):
            await self._encerrar_requiem(_mp, f"{_mp.get('name','o bardo')} tombou")
```
(inserir onde o jogador já foi confirmado morto; idempotente.)

- [ ] **Step 4** — Run → PASS.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Requiem manutencao -2/-2 por rodada + limpeza na morte do bardo"
```

---

## Task 6: Cliente — mira/toggle + banner de status

**Files:** Modify `src/gameState.js`, `game.js`. **Editar game.js só com Edit/Write.**

- [ ] **Step 1 — `acionarInstrumento` (game.js).** Adicionar o ramo `requiem_final`: se o
bardo já tem Réquiem ativo (`me.requiem_alvo`), desligar via `GS.usarInstrumento(null)`
(toggle-off); senão abrir `openTargetModal` (1 monstro no alcance, como `nota_cortante`) →
`GS.usarInstrumento(alvo)`. Padrão:
```javascript
  if (tipo === 'requiem_final') {
    if (me.requiem_alvo) { GS.usarInstrumento(null); return; }   // toggle-off
    const st = GS.instrumentoStatsClient(inst) || {};
    const alcance = st.alcance || 0;
    const gs = GS.gameState;
    const pp = me.pos || [0,0];
    const alvos = (gs && gs.monsters || []).filter(mo => mo && mo.hp > 0 &&
      Math.max(Math.abs(pp[0]-mo.pos[0]), Math.abs(pp[1]-mo.pos[1])) <= alcance);
    if (!alvos.length) { toast(`Nenhum inimigo a até ${alcance} quadrados.`, 'var(--orange)'); return; }
    if (alvos.length === 1) { GS.usarInstrumento(alvos[0]); return; }
    openTargetModal(`${b.icon} ${b.habilidade_nome} — Escolha o alvo (alcance ${alcance}q)`, alvos, 'monster',
      id => GS.usarInstrumento({ id }));
    return;
  }
```
(Confirmar que `me` está acessível em `acionarInstrumento`; se a assinatura for
`acionarInstrumento(me, inst, b)` — como na Fase 1 — usar `me` direto.)

- [ ] **Step 2 — banner de status** em `renderMyPanel` (game.js), na família dos banners de
status já existente (ex.: o do Último Esforço / saciado). Quando `me.requiem_alvo`:
```javascript
  if (me.requiem_alvo) {
    const inst = me.gear && me.gear.off_hand;
    const st = inst ? (GS.instrumentoStatsClient(inst) || {}) : {};
    const alvo = (GS.gameState && GS.gameState.monsters || []).find(mo => mo.id === me.requiem_alvo);
    const n = me.requiem_contador || 0;
    const banner = document.createElement('div');
    banner.className = 'status-banner';   // usar a classe real dos outros banners
    banner.textContent = `🎻 Réquiem — alvo ${alvo ? alvo.name : '?'} — ${n}${st.dado||''} (manut. 🍖-2 💧-2)`;
    // inserir no mesmo ponto dos outros banners
  }
```
(Localizar a classe/estrutura real dos banners de status existentes e espelhá-la.)

- [ ] **Step 3 — sintaxe:** `node --check game.js && node --check src/gameState.js`.

- [ ] **Step 4** — NÃO abrir navegador (o controlador verifica). Reportar os pontos p/ verificar.

- [ ] **Step 5 — Commit:**
```bash
git add src/gameState.js game.js
git commit -m "feat(instrumentos): cliente — mira/toggle do Requiem + banner de status"
```

> `usarInstrumento(target, dir)` já existe (Fase 2) e serve; o Réquiem usa só `target`.

---

## Task 7: SKU de loja + docs + regressão final

**Files:** Modify `server.py`, `CLAUDE.md`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — teste + SKU.** Append:
```python
def test_sku_violino_existe():
    sku = server.instrumento_sku("violino", "padrao", preco=320)
    assert sku["tipo_item"] == "instrumento" and sku["base"] == "violino"
    ids = {i.get("id") for i in server.SHOP_MERCHANT}
    assert "instrumento_violino_padrao" in ids
```
Run → FAIL. Adicionar ao bloco de instrumentos de `SHOP_MERCHANT`:
```python
    instrumento_sku("violino", "rustico", 240),
    instrumento_sku("violino", "padrao",  360),
```
Run → PASS.

- [ ] **Step 2 — CLAUDE.md.** Após o bloco da Fase 2 dos instrumentos, adicionar um `>`:
```markdown
> **Fase 3 (Réquiem Final / Violino):** habilidade sustentada de alvo único (2 mãos,
> `requiem_final`). Ativação `_instr_requiem_final` (alvo com LOS + `alcance` por qualidade;
> grava `requiem_alvo`/`requiem_contador` no bardo e `requiem_por` no monstro); toggle-off
> tratado cedo em `handle_usar_instrumento` (grátis, sempre disponível). DoT
> `_processar_requiem_turno` (no turno do alvo, junto de paralisia/veneno): contador sobe até
> o teto por qualidade (velho 3 / rústico 4 / padrão 5), Vontade → falha `contador×dado`
> (d2/d4/d6), sucesso sem dano. Taunt `_requiem_forca_bardo` (o alvo + monstros a ≤3 do bardo
> são forçados a atacá-lo — integrado em `_get_monster_primary_target` e nos booleanos
> `forcado`). Concentração `_concentracao_requiem` (Vontade CD 8+dano ao sofrer dano; falha
> encerra) hookada no ataque de monstro + ticks de veneno/chamas/armadilha; Origem Anã +2
> plumbada p/ Fase 4. Manutenção `_cobrar_manutencao_requiem` (-2🍖/-2💧 no turno do bardo;
> sem recursos encerra). `_encerrar_requiem` (idempotente) chamado em morte do alvo/bardo,
> quebra de concentração, sem recursos, desequipar, recast, toggle. Cliente: mira como Nota
> Cortante (ou toggle-off se já ativo) + banner de status em `renderMyPanel`. Fase 4 Rúnico:
> Violino Rúnico dá -1 Vontade ao alvo. Testes: `tools/test_instrumentos_bardo.py`.
```

- [ ] **Step 3 — regressão completa** (registrar PASS/FAIL):
```bash
python tools/test_instrumentos_bardo.py
python tools/test_bardo_espec.py
python tools/test_tecnicas_espec.py
python tools/test_guilda.py
python tools/test_roteamento_itens.py
python tools/test_arremessaveis_tatico.py
python -c "import server"
node --check game.js && node --check src/gameState.js
```
Se algo falhar, STOP e reportar DONE_WITH_CONCERNS.

- [ ] **Step 4 — Commit:**
```bash
git add server.py CLAUDE.md tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): SKU do Violino + docs Fase 3 (Requiem Final)"
```

---

## Self-Review (cobertura do spec)

- §2 base violino (stats/custo/manutenção) → Task 1/7. ✅
- §3 ativação/toggle/recast/LOS/alcance → Task 1. ✅
- §4 DoT escalonado + teto + save + morte → Task 2. ✅
- §5 taunt (`_requiem_forca_bardo` + integrações) → Task 3. ✅
- §6 concentração (helper + 4 sites) → Task 4. ✅
- §7 manutenção → Task 5. ✅
- §8 `_encerrar_requiem` + limpezas (alvo/bardo/desequipar/recast/concentração/recursos/toggle) → Tasks 1/2/4/5. ✅
- §9 cliente (mira/toggle/banner) → Task 6. ✅
- §10 testes → Tasks 1–5 (TDD) + Task 7 (regressão). ✅

**Lacunas conhecidas (aceitas):**
- Os hooks de concentração nos ticks de veneno/chamas/armadilha dependem de o implementador
  localizar o ponto exato de dano ao jogador em cada processador; o helper é no-op para
  monstros, então uma chamada incondicional após o dano é segura. O site de ataque é testado
  ponta-a-ponta; os ticks via chamada direta do helper.
- Taunt "≤3 do bardo" é avaliado dinamicamente na escolha de alvo do monstro (cobre quem
  entra no raio), mas não força um monstro que JÁ escolheu alvo e depois entra no raio na
  mesma rodada — aceito (reavalia na rodada seguinte).
