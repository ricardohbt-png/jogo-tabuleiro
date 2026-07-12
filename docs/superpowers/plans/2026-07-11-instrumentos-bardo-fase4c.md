# Instrumentos do Bardo — Fase 4c (Encantamento Rúnico — efeitos bespoke) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar o Encantamento Rúnico com os 3 efeitos bespoke — Harpa (Nota Cortante em linha), Tambor (Atordoa/−1 Ataque), Alaúde (+1 Fort/Vontade na Canção).

**Architecture:** Lógica de handler/hook (não stat-based). Harpa reusa `_caminho_relampago`; Tambor reusa `perde_turno` + um debuff round-stamped estilo `_pressao_ca_pen`; Alaúde soma um bônus em `_testar_save` (mesmo ponto do `_lenda_resist_bonus`). Sem mudança de framework.

**Tech Stack:** Python (`server.py`), Vanilla JS (`game.js`), testes `tools/test_instrumentos_bardo.py`.

**Spec:** `docs/superpowers/specs/2026-07-11-instrumentos-bardo-fase4c-design.md`

---

## Pontos de integração (confirmados; verificar por leitura)
- `_instr_nota_cortante` (server.py ~5166), `_instr_acorde_trovejante` (~5200).
- `_caminho_relampago(self, origem, dx, dy, alcance)` (~11196) → sequência de casas `(x,y)` na reta.
- `_ndfaces`, `_rolar_dano_mostrado`, `_save_mostrado`, `_instrumento_cd`, `_monster_dies`, `_no_raio`, `_empurrar`, `_reduzir_mov_monstro`.
- `m_atk` do ataque de monstro: `_execute_one_monster_attack` (~13671, expressão multi-linha) **e** o loop legado (~15432, linha única) — hookar OS DOIS (lição da Fase 3: goblin/esqueleto/orc/mago negro/troll/dragão usam o loop legado).
- `_pressao_ca_pen` (~4673) — padrão round-stamped de debuff de monstro.
- `_testar_save` (~11695): `bonus = (... + self._lenda_resist_bonus(alvo, fonte) + self._resistencia_saves_bonus(alvo))`.
- `_eh_jogador(obj)` — True se obj é jogador. Canção: aliados sob a Canção têm `buffs_cancao`; o bardo tem `cancao_ativa`.
- Cliente: `acionarInstrumento(me, inst, b)` (game.js ~7647), ramo `nota_cortante`; `escolherDirecaoInstrumento(b, cb)` (seletor de 8 direções do Chamado).
- Testes: helpers `_room_bardo`/`_run`/`_mute`/`_save_falha`/`_dano10`/`_dano8` em `tools/test_instrumentos_bardo.py`.

---

## Task 1: Harpa Rúnica — Nota Cortante em linha (server + cliente)

**Files:** `server.py`, `game.js`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_harpa_runica_linha():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao", encantamento="runico")  # alcance 5
    a = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    b = {"id": "m2", "name": "B", "hp": 30, "pos": [8, 5], "alive": True}
    fora = {"id": "m3", "name": "C", "hp": 30, "pos": [6, 7], "alive": True}
    room.monsters = {"m1": a, "m2": b, "m3": fora}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"dir": [1, 0]}))
    assert a["hp"] == 20 and b["hp"] == 20   # ambos na linha +x (dano cheio 10)
    assert fora["hp"] == 30                  # fora da linha

def test_harpa_runica_sem_direcao_recusa():
    room, p = _room_bardo(); _mute(room)
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao", encantamento="runico")
    m = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    fome0 = p["fome"]
    _run(room.handle_usar_instrumento("p1", {}))   # sem dir
    assert m["hp"] == 30 and p["fome"] == fome0

def test_harpa_normal_ainda_alvo_unico():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("harpa", "padrao")   # não Rúnica
    a = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    b = {"id": "m2", "name": "B", "hp": 30, "pos": [8, 5], "alive": True}
    room.monsters = {"m1": a, "m2": b}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano10
    _run(room.handle_usar_instrumento("p1", {"target_id": "m1"}))
    assert a["hp"] == 20 and b["hp"] == 30   # só o alvo
```

- [ ] **Step 2** — Run `python tools/test_instrumentos_bardo.py` → FAIL.

- [ ] **Step 3 — implementar (server).** No início de `_instr_nota_cortante`, desviar p/ a linha se Rúnica:
```python
    async def _instr_nota_cortante(self, p, inst, st, data):
        """Alvo único até `alcance` casas; Reflexos → metade. Rúnica: linha reta direcional."""
        if inst.get("encantamento") == "runico":
            return await self._nota_cortante_linha(p, inst, st, data)
        alvo_id = (data or {}).get("target_id")
        # ... (resto do corpo atual, inalterado) ...
```
E adicionar o handler da linha (logo após `_instr_nota_cortante`):
```python
    async def _nota_cortante_linha(self, p, inst, st, data):
        """Harpa Rúnica: reta direcional; cada monstro na linha faz seu Reflexos-meia."""
        dirv = (data or {}).get("dir") or [0, 0]
        dx = 1 if dirv[0] > 0 else -1 if dirv[0] < 0 else 0
        dy = 1 if dirv[1] > 0 else -1 if dirv[1] < 0 else 0
        if dx == 0 and dy == 0:
            await self.send_to(p["id"], {"type": "error", "msg": "Escolha uma direção para a Nota Cortante rúnica."}); return False
        tiles = {tuple(t) for t in self._caminho_relampago(p["pos"], dx, dy, st["alcance"])}
        alvos = [m for m in self.monsters.values()
                 if m.get("hp", 0) > 0 and tuple(m["pos"]) in tiles]
        if not alvos:
            await self.send_to(p["id"], {"type": "error", "msg": "Nenhum inimigo na linha."}); return False
        await self.gm_say(f"🎵 **{p['name']}** dispara **Nota Cortante** numa linha reta!")
        cd = self._instrumento_cd(p, inst)
        for m in alvos:
            dano = await self._rolar_dano_mostrado(*_ndfaces(st["dano"]), "🎵 Dano sonoro")
            save_ok, *_ = await self._save_mostrado(m, "reflexos", cd)
            if save_ok:
                dano = dano // 2
            m["hp"] = max(0, m["hp"] - dano)
            await self.gm_say(f"🎵 **{m['name']}** sofre **{dano}**{' (metade)' if save_ok else ''}.")
            if m["hp"] <= 0:
                await self._monster_dies(m, p["id"])
        return True
```

- [ ] **Step 4 — implementar (cliente).** Em `game.js` `acionarInstrumento`, no ramo `nota_cortante`, antes do modal de alvo:
```javascript
  if (tipo === 'nota_cortante') {
    if (inst.encantamento === 'runico') {
      escolherDirecaoInstrumento(b, (dx, dy) => GS.usarInstrumento(null, [dx, dy]));
      return;
    }
    // ... (modal de alvo único existente) ...
  }
```
(Adaptar aos nomes reais; `inst`/`b` já estão em escopo.)

- [ ] **Step 5** — Run → PASS. `node --check game.js` → OK.
- [ ] **Step 6 — Commit:**
```bash
git add server.py game.js tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Harpa Runica — Nota Cortante em linha direcional"
```

---

## Task 2: Tambor Rúnico — Atordoar / −1 Ataque

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_tambor_runico_atordoa_e_penaliza():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao", encantamento="runico")
    falho = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    passou = {"id": "m2", "name": "B", "hp": 30, "pos": [5, 6], "alive": True}
    room.monsters = {"m1": falho, "m2": passou}
    async def _save(alvo, tipo, dif, **k): return (alvo["id"] == "m2", 1, 0, 1)  # m2 passa, m1 falha
    room._save_mostrado = _save
    room._rolar_dano_mostrado = _dano8
    room._empurrar = lambda *a: False
    _run(room.handle_usar_instrumento("p1", {}))
    assert falho.get("perde_turno") is True        # falha → atordoado
    assert room._acorde_atk_pen(passou) == -1      # sucesso → -1 ataque
    assert room._acorde_atk_pen(falho) == 0        # falha não recebe a penalidade de atk

def test_acorde_atk_pen_expira():
    room, p = _room_bardo()
    m = {"acorde_atk_pen_ate": room.round_num + 1}
    assert room._acorde_atk_pen(m) == -1
    room.round_num += 2
    assert room._acorde_atk_pen(m) == 0

def test_tambor_normal_nao_atordoa():
    room, p = _room_bardo(); _mute(room)
    p["pos"] = [5, 5]
    p["gear"]["off_hand"] = server.criar_instrumento("tambor", "padrao")   # não Rúnico
    m = {"id": "m1", "name": "A", "hp": 30, "pos": [6, 5], "alive": True}
    room.monsters = {"m1": m}
    room._save_mostrado = _save_falha
    room._rolar_dano_mostrado = _dano8
    room._empurrar = lambda *a: False
    _run(room.handle_usar_instrumento("p1", {}))
    assert m.get("perde_turno") is None
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.**

3a. Helper (perto de `_pressao_ca_pen`):
```python
    def _acorde_atk_pen(self, m):
        """-1 de Ataque do Tambor Rúnico (sucesso no save), até o próximo turno do monstro."""
        return -1 if m.get("acorde_atk_pen_ate", 0) >= self.round_num else 0
```

3b. Em `_instr_acorde_trovejante`, no laço por alvo, acrescentar os efeitos Rúnicos. Substituir:
```python
            if not save_ok:
                if st.get("push", 0) > 0:
                    dx = (m["pos"][0] > p["pos"][0]) - (m["pos"][0] < p["pos"][0])
                    dy = (m["pos"][1] > p["pos"][1]) - (m["pos"][1] < p["pos"][1])
                    self._empurrar(m, dx, dy, st["push"])
                else:
                    self._reduzir_mov_monstro(m, 1, 1)   # Tambor Velho: -1 movimento
```
por:
```python
            runico = inst.get("encantamento") == "runico"
            if not save_ok:
                if st.get("push", 0) > 0:
                    dx = (m["pos"][0] > p["pos"][0]) - (m["pos"][0] < p["pos"][0])
                    dy = (m["pos"][1] > p["pos"][1]) - (m["pos"][1] < p["pos"][1])
                    self._empurrar(m, dx, dy, st["push"])
                else:
                    self._reduzir_mov_monstro(m, 1, 1)   # Tambor Velho: -1 movimento
                if runico:
                    m["perde_turno"] = True              # Rúnico: Atordoado 1 rodada
            elif runico:
                m["acorde_atk_pen_ate"] = self.round_num + 1   # Rúnico: -1 Ataque até o próximo turno
```

3c. Ler a penalidade no `m_atk` do ataque de monstro — nos DOIS sites, acrescentar `+ self._acorde_atk_pen(m)`:
- `_execute_one_monster_attack` (~13671): dentro da expressão `m_atk = (atk_def["atk_bonus"] + self._pen(m, "ataque") + self._mod_magia(m, "ataque") ...)`, somar `+ self._acorde_atk_pen(m)`.
- Loop legado (~15432): `m_atk = m["atk_bonus"] + self._pen(m, "ataque") + self._mod_magia(m, "ataque")` → acrescentar `+ self._acorde_atk_pen(m)`.

- [ ] **Step 4** — Run → PASS. `python tools/test_tecnicas_espec.py` (exercita ataque de monstro) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Tambor Runico — Atordoa (falha) / -1 Ataque (sucesso)"
```

---

## Task 3: Alaúde Rúnico — +1 Fortitude & Vontade

**Files:** `server.py`; Test `tools/test_instrumentos_bardo.py`.

- [ ] **Step 1 — testes que falham** (append):
```python
def test_alaude_runico_resist():
    room, p = _room_bardo()
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao", encantamento="runico")
    p["cancao_ativa"] = True
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "buffs_cancao": {"bonus_acerto": 1}}
    room.players["a1"] = ally
    assert room._alaude_runico_resist(ally, "fortitude") == 1
    assert room._alaude_runico_resist(ally, "vontade") == 1
    assert room._alaude_runico_resist(ally, "reflexos") == 0
    # sem buffs_cancao → 0
    sem = {"id": "a2", "class_id": "rogue", "alive": True}
    room.players["a2"] = sem
    assert room._alaude_runico_resist(sem, "fortitude") == 0
    # Alaúde não-Rúnico → 0
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao")
    assert room._alaude_runico_resist(ally, "fortitude") == 0

def test_alaude_runico_no_testar_save():
    room, p = _room_bardo()
    p["gear"]["off_hand"] = server.criar_instrumento("alaude", "padrao", encantamento="runico")
    p["cancao_ativa"] = True
    ally = {"id": "a1", "class_id": "warrior", "alive": True, "buffs_cancao": {},
            "saves_base": {}, "fort": 0, "will": 0}
    room.players["a1"] = ally
    # com d20 fixo, o total de Fortitude sobe 1 por causa do Alaúde Rúnico
    import random as _r
    _r.seed(1)
    _, _, bonus_com, _ = room._testar_save(ally, "fortitude", 99)
    p["gear"]["off_hand"] = None
    _r.seed(1)
    _, _, bonus_sem, _ = room._testar_save(ally, "fortitude", 99)
    assert bonus_com - bonus_sem == 1
```

- [ ] **Step 2** — Run → FAIL.

- [ ] **Step 3 — implementar.**

3a. Helper (perto de `_lenda_resist_bonus`):
```python
    def _alaude_runico_resist(self, alvo, tipo_save):
        """+1 em Fortitude/Vontade p/ aliados sob a Canção quando um bardo empunha um
        Alaúde Rúnico (medo/doença/veneno — escopo amplo). 0 caso contrário."""
        if tipo_save not in ("fortitude", "vontade"):
            return 0
        if not self._eh_jogador(alvo) or not alvo.get("buffs_cancao"):
            return 0
        for q in self.players.values():
            if q.get("class_id") == "bard" and q.get("cancao_ativa"):
                off = q.get("gear", {}).get("off_hand")
                if off and off.get("tipo_item") == "instrumento" \
                   and off.get("base") == "alaude" and off.get("encantamento") == "runico":
                    return 1
        return 0
```

3b. Somar em `_testar_save` (na expressão do `bonus`):
```python
        bonus = (self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia")
                 + extra_mod + self._lenda_resist_bonus(alvo, fonte)
                 + self._resistencia_saves_bonus(alvo)
                 + self._alaude_runico_resist(alvo, tipo_save))
```

- [ ] **Step 4** — Run → PASS. `python tools/test_bardo_espec.py` (Canção) → verde.
- [ ] **Step 5 — Commit:**
```bash
git add server.py tools/test_instrumentos_bardo.py
git commit -m "feat(instrumentos): Alaude Runico — +1 Fort/Vontade aos aliados sob a Cancao"
```

---

## Task 4: Docs + regressão final

**Files:** `CLAUDE.md`; Test suíte.

- [ ] **Step 1 — CLAUDE.md.** Após o bloco da Fase 4b, adicionar um `>`:
```markdown
> **Fase 4c (Encantamento Rúnico — efeitos bespoke):** fecha os 8 efeitos Rúnicos. **Harpa**
> Rúnica: Nota Cortante vira reta direcional (`_nota_cortante_linha`, reusa `_caminho_relampago`;
> cada alvo Reflexos-meia); cliente usa o seletor de direção do Chamado quando a Harpa é Rúnica.
> **Tambor** Rúnico: no Acorde, falha → `perde_turno` (Atordoado), sucesso → −1 Ataque até o
> próximo turno (`acorde_atk_pen_ate` lido por `_acorde_atk_pen`, somado ao `m_atk` no ataque
> modular E no loop legado). **Alaúde** Rúnico: `_alaude_runico_resist` soma +1 em
> Fortitude/Vontade aos aliados sob a Canção (via `_testar_save`, escopo amplo). Fase 5:
> Improviso/Gaita. Testes: `tools/test_instrumentos_bardo.py`.
```
Verificar cada afirmação contra o código.

- [ ] **Step 2 — regressão** (registrar PASS/FAIL):
```bash
python tools/test_instrumentos_bardo.py
python tools/test_bardo_espec.py
python tools/test_tecnicas_espec.py
python tools/test_roteamento_itens.py
python -c "import server"
node --check game.js
```
Se algo falhar, STOP e reportar DONE_WITH_CONCERNS.

- [ ] **Step 3 — Commit:**
```bash
git add CLAUDE.md
git commit -m "docs(instrumentos): documenta Fase 4c (efeitos Runicos bespoke) no CLAUDE.md"
```

---

## Self-Review (cobertura do spec)

- §2 Harpa Rúnica (linha server + cliente) → Task 1. ✅
- §3 Tambor Rúnico (perde_turno + `_acorde_atk_pen` nos 2 sites de m_atk) → Task 2. ✅
- §4 Alaúde Rúnico (+1 Fort/Vontade em `_testar_save`) → Task 3. ✅
- §5 cliente (só a Harpa) → Task 1. ✅
- §6 testes → Tasks 1–3 (TDD) + Task 4 (regressão). ✅

**Lacunas conhecidas (aceitas):**
- O escopo amplo do Alaúde (+1 em TODO Fort/Vontade sob a Canção) foi a decisão do brainstorm;
  cobre medo/doença/veneno + alguns outros Fort/Vontade — aceito.
- `_acorde_atk_pen` hookado nos 2 sites de `m_atk` conhecidos (modular + legado); se houver um 3º
  caminho de ataque de monstro não coberto, documentar (mas os 2 cobrem o roster real, como na Fase 3).
