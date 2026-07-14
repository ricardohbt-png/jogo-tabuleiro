# Guilda dos Heróis — Fase 2d: Oportunidade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the "Oportunidade" Guild technique — a support technique (not a
reaction) that grants one ally a single "extra action" credit, reserved for that
ally's own next turn: either extra movement, or one extra "main action" (attack,
class ability, or grimoire spell), consumed by whichever happens first.

**Architecture:** Two new player-state fields (`oportunidade_credito`,
`oportunidade_round`) track the credit. A new `GUILD_CATALOG` entry + branch in
`handle_usar_tecnica` grant it (reusing the existing `alvo:"aliado"` targeting
pattern already wired client-side for Ataque Coordenado). The credit is spent via
one of two paths: (1) a small addition to the existing `_acao_bloqueada` helper
(which already grants the Velocidade spell one bonus action) makes attack/magia/
scroll and 9 other class-ability handlers accept the credit automatically once
those 9 are migrated off their raw `action_done` check onto `_acao_bloqueada`; (2)
a brand-new handler `handle_usar_oportunidade_movimento` for the movement path.

**Tech Stack:** Python (server.py, authoritative game server), vanilla JS
(`src/gameState.js` state/network layer, `game.js` rendering/UI) — no new
dependencies. Spec: `docs/superpowers/specs/2026-07-04-guilda-fase2d-oportunidade-design.md`.

---

## Task 1: Player state fields + catalog entry

**Files:**
- Modify: `server.py:3438` (player template, right after `contra_ataque_ate`)
- Modify: `server.py:394` (GUILD_CATALOG, right after `tecnica_contra_ataque`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Add the two new player-state fields**

In `server.py`, find this exact block (line 3438):

```python
        "contra_ataque_ate": 0,             # Contra-Ataque até esta rodada
        "imune_silencio_ate": 0,            # Espírito Indomável: imunidade a Silêncio até esta rodada
```

Replace with:

```python
        "contra_ataque_ate": 0,             # Contra-Ataque até esta rodada
        "oportunidade_credito": False,       # Oportunidade: crédito de ação extra concedido, ainda não gasto
        "oportunidade_round": 0,             # round_num em que foi concedido — expira se round_num avançar
        "imune_silencio_ate": 0,            # Espírito Indomável: imunidade a Silêncio até esta rodada
```

- [ ] **Step 2: Add the GUILD_CATALOG entry**

In `server.py`, find this exact block (line 387-394):

```python
    "tecnica_contra_ataque": {
        "id": "tecnica_contra_ataque", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 280, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 8,
        "nome": "Contra-Ataque", "icon": "🗡️",
        "desc": "Até o próximo turno, quando um inimigo errar você (arma corpo a corpo/alcance ou besta de mão, e ele no alcance), você o ataca de volta.",
        "efeito": {"tipo": "contra_ataque"},
    },
```

Add right after it (still inside the reaction-techniques block):

```python
    "tecnica_oportunidade": {
        "id": "tecnica_oportunidade", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
        "nome": "Oportunidade", "icon": "⏳", "alvo": "aliado",
        "desc": "Escolha um aliado (não pode ser você); no PRÓPRIO turno dele, ganha uma "
                "ação extra — mover mais, atacar de novo, usar a habilidade de classe de "
                "novo, ou lançar mais uma magia. Expira no fim desta rodada se não for usada.",
        "efeito": {"tipo": "oportunidade"},
    },
```

- [ ] **Step 3: Write the failing test**

Append to `tools/test_tecnicas_espec.py`, right before the final `print(f"\n{'='*40}...` block (currently line 335):

```python
    # [18] Catálogo — Oportunidade (2d)
    print("\n[18] Catálogo — Oportunidade")
    it = S.guild_item("tecnica_oportunidade")
    check("existe tecnica_oportunidade", it is not None)
    check("oportunidade recarga 10", it and it["recarga_rodadas"] == 10)
    check("oportunidade preco 350", it and it["preco"] == 350)
    check("oportunidade custo 6/6", it and it["custo_fome"] == 6 and it["custo_sede"] == 6)
    check("oportunidade classe None", it and it["classe"] is None)
    check("oportunidade exige alvo aliado", it and it.get("alvo") == "aliado")
    p_tmpl = hero("warrior")
    check("template: oportunidade_credito default False", p_tmpl["oportunidade_credito"] is False)
    check("template: oportunidade_round default 0", p_tmpl["oportunidade_round"] == 0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tools/test_tecnicas_espec.py`
Expected: all `[18]` checks show `✅`, `FAIL=0` in the summary.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): catálogo + estado da técnica Oportunidade (Fase 2d)"
```

---

## Task 2: `_acao_bloqueada` — crédito de Oportunidade

**Files:**
- Modify: `server.py:9127-9138` (`_acao_bloqueada`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Write the failing test**

Append after the `[18]` section:

```python
    # [19] _acao_bloqueada — crédito de Oportunidade
    print("\n[19] _acao_bloqueada — crédito de Oportunidade")
    r = setup(); r.round_num = 5
    p = hero("warrior"); p["action_done"] = True
    check("sem crédito: continua bloqueado", r._acao_bloqueada(p) is True)
    p["oportunidade_credito"] = True; p["oportunidade_round"] = 5
    check("com crédito válido (round bate): libera", r._acao_bloqueada(p) is False)
    check("libera: action_done volta a False", p["action_done"] is False)
    check("libera: crédito consumido", p["oportunidade_credito"] is False)
    # Crédito de rodada anterior (expirado) não libera
    p2 = hero("warrior"); p2["action_done"] = True
    p2["oportunidade_credito"] = True; p2["oportunidade_round"] = 3   # round atual é 5
    check("crédito de rodada anterior: expirado, continua bloqueado", r._acao_bloqueada(p2) is True)
    # Coexistência com Velocidade: os dois créditos não interferem entre si
    p3 = hero("warrior"); p3["action_done"] = True
    p3["velocidade_rodadas"] = 2; p3["velocidade_extra_usada"] = False
    p3["oportunidade_credito"] = True; p3["oportunidade_round"] = 5
    check("velocidade consumida primeiro", r._acao_bloqueada(p3) is False)
    check("velocidade: extra usada marcada", p3["velocidade_extra_usada"] is True)
    check("velocidade consumida NÃO gasta o crédito de Oportunidade", p3["oportunidade_credito"] is True)
    p3["action_done"] = True   # agiu de novo
    check("2ª ação extra: agora usa o crédito de Oportunidade", r._acao_bloqueada(p3) is False)
    check("crédito de Oportunidade agora consumido", p3["oportunidade_credito"] is False)
    p3["action_done"] = True   # agiu uma 3ª vez, sem mais créditos disponíveis
    check("3ª tentativa: sem mais créditos, bloqueado", r._acao_bloqueada(p3) is True)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tools/test_tecnicas_espec.py`
Expected: FAIL on every `[19]` check that depends on the Oportunidade branch (e.g.
"com crédito válido (round bate): libera" fails because `_acao_bloqueada` doesn't
know about `oportunidade_credito` yet).

- [ ] **Step 3: Write minimal implementation**

In `server.py`, find this exact block (line 9127-9138):

```python
    def _acao_bloqueada(self, p):
        """True se p não pode fazer outra ação principal. Velocidade concede 1 ação
        extra por turno: ao tentar agir já tendo agido, consome a extra e libera."""
        if p.get("perde_turno"):
            return True  # Imobilizado (teia, etc.) — perde o turno inteiro
        if not p.get("action_done"):
            return False
        if p.get("velocidade_rodadas", 0) > 0 and not p.get("velocidade_extra_usada"):
            p["velocidade_extra_usada"] = True
            p["action_done"] = False
            return False
        return True
```

Replace with:

```python
    def _acao_bloqueada(self, p):
        """True se p não pode fazer outra ação principal. Velocidade e a técnica
        Oportunidade concedem 1 ação extra: ao tentar agir já tendo agido, consomem
        o crédito disponível e liberam a ação."""
        if p.get("perde_turno"):
            return True  # Imobilizado (teia, etc.) — perde o turno inteiro
        if not p.get("action_done"):
            return False
        if p.get("velocidade_rodadas", 0) > 0 and not p.get("velocidade_extra_usada"):
            p["velocidade_extra_usada"] = True
            p["action_done"] = False
            return False
        if p.get("oportunidade_credito") and p.get("oportunidade_round") == self.round_num:
            p["oportunidade_credito"] = False
            p["action_done"] = False
            return False
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tools/test_tecnicas_espec.py`
Expected: all `[19]` checks `✅`, `FAIL=0`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): _acao_bloqueada aceita o crédito de Oportunidade"
```

---

## Task 3: Concessão — branch em `handle_usar_tecnica`

**Files:**
- Modify: `server.py:4408-4410`
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Write the failing test**

Append after `[19]`:

```python
    # [20] Oportunidade — concessão (handle_usar_tecnica)
    print("\n[20] Oportunidade — concessão")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 7
    p = hero("warrior", "tecnica_oportunidade"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1, 1]
    r.players["a"] = ally
    await r.handle_usar_tecnica("h", "tecnica_oportunidade", "a")
    check("concessão: crédito no aliado", ally["oportunidade_credito"] is True)
    check("concessão: round gravado", ally["oportunidade_round"] == 7)
    check("concessão: recarga setada no ativador", r.tecnica_restante(p, "tecnica_oportunidade") > 0)
    check("concessão: custo 6/6 debitado", p["fome"] == 20 - 6 and p["sede"] == 20 - 6)
    # Recusa: não pode escolher a si mesmo
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 7
    p2 = hero("warrior", "tecnica_oportunidade"); r2.players["h"] = p2
    await r2.handle_usar_tecnica("h", "tecnica_oportunidade", "h")
    check("concessão: recusa auto-alvo", p2.get("oportunidade_credito") is False
          and any("não pode ser você" in e.lower() for e in r2._errs))
    # Recusa: aliado morto
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 7
    p3 = hero("warrior", "tecnica_oportunidade"); r3.players["h"] = p3
    morto = make_player("m", "Morto", "cleric", 1); morto["alive"] = False; r3.players["m"] = morto
    await r3.handle_usar_tecnica("h", "tecnica_oportunidade", "m")
    check("concessão: recusa aliado morto", morto.get("oportunidade_credito") is False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tools/test_tecnicas_espec.py`
Expected: FAIL on all `[20]` checks (`ef.get("tipo") == "oportunidade"` has no branch
yet, so nothing is granted and no error is sent — the technique still goes through
the generic cost/recharge tail with no effect).

- [ ] **Step 3: Write minimal implementation**

In `server.py`, find this exact block (line 4408-4410):

```python
        elif ef.get("tipo") == "contra_ataque":
            p["contra_ataque_ate"] = self.round_num + 1
        # (outros tipos/handlers chegam nas Fases 1-2)
```

Replace with:

```python
        elif ef.get("tipo") == "contra_ataque":
            p["contra_ataque_ate"] = self.round_num + 1
        elif ef.get("tipo") == "oportunidade":
            alvo = self.players.get(target_id) if target_id else None
            if not alvo or not alvo.get("alive") or alvo["id"] == pid:
                await self.send_to(pid, {"type": "error",
                    "msg": "Escolha um aliado vivo (não pode ser você)."}); return
            alvo["oportunidade_credito"] = True
            alvo["oportunidade_round"] = self.round_num
        # (outros tipos/handlers chegam nas Fases 1-2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tools/test_tecnicas_espec.py`
Expected: all `[20]` checks `✅`, `FAIL=0`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Oportunidade concede o crédito de ação extra ao aliado"
```

---

## Task 4: Via "movimento extra" — novo handler + protocolo

**Files:**
- Modify: `server.py` — new method near `_acao_bloqueada`/other `handle_usar_*` methods (add right after `handle_usar_tecnica`, i.e. after line 4415 `await self.push_state()` that closes that method)
- Modify: `server.py:14377-14378` (WebSocket dispatch table)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Write the failing test**

Append after `[20]`:

```python
    # [21] Oportunidade — via movimento
    print("\n[21] Oportunidade — via movimento")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 7
    p = hero("warrior"); p["moves_left"] = p["spd"]
    p["oportunidade_credito"] = True; p["oportunidade_round"] = 7
    r.players["h"] = p
    await r.handle_usar_oportunidade_movimento("h")
    check("movimento: +spd em moves_left", p["moves_left"] == p["spd"] + p["spd"])
    check("movimento: crédito consumido", p["oportunidade_credito"] is False)
    # Sem crédito válido: recusa e não mexe no movimento
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 7
    p2 = hero("warrior"); p2["moves_left"] = p2["spd"]; r2.players["h"] = p2
    await r2.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa sem crédito", p2["moves_left"] == p2["spd"]
          and any("oportunidade" in e.lower() for e in r2._errs))
    # Crédito de rodada anterior (expirado): recusa
    r3 = setup(); r3.current_pid = lambda: "h"; r3.round_num = 8
    p3 = hero("warrior"); p3["moves_left"] = p3["spd"]
    p3["oportunidade_credito"] = True; p3["oportunidade_round"] = 7   # round atual é 8
    r3.players["h"] = p3
    await r3.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa crédito expirado", p3["moves_left"] == p3["spd"])
    # Fora do próprio turno: recusa
    r4 = setup(); r4.current_pid = lambda: "outro"; r4.round_num = 7
    p4 = hero("warrior"); p4["moves_left"] = p4["spd"]
    p4["oportunidade_credito"] = True; p4["oportunidade_round"] = 7
    r4.players["h"] = p4
    await r4.handle_usar_oportunidade_movimento("h")
    check("movimento: recusa fora do próprio turno", p4["moves_left"] == p4["spd"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tools/test_tecnicas_espec.py`
Expected: `AttributeError: 'GameRoom' object has no attribute 'handle_usar_oportunidade_movimento'`.

- [ ] **Step 3: Write minimal implementation**

In `server.py`, right after `handle_usar_tecnica` ends (find the exact block at
lines 4413-4417):

```python
        p["technique_cooldowns"][tecnica_id] = self.round_num + item["recarga_rodadas"]
        await self.gm_say(f"⚔️ **{p['name']}** ativa **{item['nome']}**!")
        await self.push_state()

    async def handle_shop_buy(self, pid, shop, item_id):
```

Insert the new method between `push_state()` and `handle_shop_buy`:

```python
        p["technique_cooldowns"][tecnica_id] = self.round_num + item["recarga_rodadas"]
        await self.gm_say(f"⚔️ **{p['name']}** ativa **{item['nome']}**!")
        await self.push_state()

    async def handle_usar_oportunidade_movimento(self, pid):
        """Gasta o crédito de Oportunidade na via 'movimento extra' (soma spd a
        moves_left). A via 'ação principal extra' não precisa de handler dedicado —
        é consumida automaticamente por _acao_bloqueada na primeira ação principal."""
        if not self._is_turn(pid):
            return
        p = self.players.get(pid)
        if not p or not p.get("alive"):
            return
        if not (p.get("oportunidade_credito") and p.get("oportunidade_round") == self.round_num):
            await self.send_to(pid, {"type": "error",
                "msg": "Sem crédito de Oportunidade disponível."})
            return
        p["oportunidade_credito"] = False
        p["moves_left"] = p.get("moves_left", 0) + p.get("spd", 0)
        await self.gm_say(f"⏳ **{p['name']}** aproveita a Oportunidade para se mover mais!")
        await self.push_state()

    async def handle_shop_buy(self, pid, shop, item_id):
```

- [ ] **Step 4: Register the new message in the WebSocket dispatch table**

In `server.py`, find this exact block (line 14377-14378):

```python
                elif t == "usar_tecnica":
                    if room: await room.handle_usar_tecnica(pid, msg.get("tecnica_id"), msg.get("target_id"))
```

Add right after it:

```python
                elif t == "usar_tecnica":
                    if room: await room.handle_usar_tecnica(pid, msg.get("tecnica_id"), msg.get("target_id"))

                elif t == "usar_oportunidade_movimento":
                    if room: await room.handle_usar_oportunidade_movimento(pid)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python tools/test_tecnicas_espec.py`
Expected: all `[21]` checks `✅`, `FAIL=0`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): via de movimento da Oportunidade + registro no protocolo"
```

---

## Task 5: Migrar os 9 handlers de `action_done` cru para `_acao_bloqueada`

**Files:**
- Modify: `server.py` — 9 sites (`handle_animar_mortos`, `handle_cura`,
  `handle_cura_area`, `handle_purificacao`, `handle_ressurreicao`,
  `handle_imposicao_maos`, `handle_criar_armadilha`, `handle_desarmar_armadilha`,
  `handle_libertar_prisioneiro`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Write the failing test**

Append after `[21]`:

```python
    # [22] Handlers migrados para _acao_bloqueada (Oportunidade cobre todas as ações principais)
    print("\n[22] Handlers migrados para _acao_bloqueada")
    # Regressão: sem crédito, action_done=True continua bloqueando cada handler
    # exatamente como antes (mesma mensagem de erro, nenhuma mudança de estado).

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("mage"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_animar_mortos("h", {})
    check("animar_mortos: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_cura("h", {})
    check("cura: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_cura_area("h", {})
    check("cura_area: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_purificacao("h", {})
    check("purificacao: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("cleric"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_ressurreicao("h", {})
    check("ressurreicao: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("paladin"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_imposicao_maos("h", {})
    check("imposicao_maos: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("rogue"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_criar_armadilha("h", {})
    check("criar_armadilha: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("rogue"); p["pos"] = [0, 0]; p["action_done"] = True; r.players["h"] = p
    await r.handle_desarmar_armadilha("h", {})
    check("desarmar_armadilha: bloqueado sem crédito (regressão)",
          any("já usada" in e.lower() for e in r._errs))

    # libertar_prisioneiro: assinatura diferente (sem `data`), retorno silencioso
    # (sem mensagem de erro) — a checagem é `p.get("action_done")` embutida no `if`.
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior"); p["pos"] = [0, 0]; p["action_done"] = True
    r.players["h"] = p
    r.prisoner = {"pos": [0, 1], "alive": True, "freed": False}
    await r.handle_libertar_prisioneiro("h")
    check("libertar_prisioneiro: bloqueado sem crédito (regressão)", r.prisoner["freed"] is False)

    # Integração: COM crédito válido, libertar_prisioneiro (o mais simples dos 9) passa
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 3
    p2 = hero("warrior"); p2["pos"] = [0, 0]; p2["action_done"] = True
    p2["oportunidade_credito"] = True; p2["oportunidade_round"] = 3
    r2.players["h"] = p2
    r2.prisoner = {"pos": [0, 1], "alive": True, "freed": False}
    await r2.handle_libertar_prisioneiro("h")
    check("libertar_prisioneiro: crédito de Oportunidade libera a ação", r2.prisoner["freed"] is True)
    check("libertar_prisioneiro: crédito consumido", p2["oportunidade_credito"] is False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tools/test_tecnicas_espec.py`
Expected: the two `libertar_prisioneiro` checks in `[22]` fail — the "regressão"
checks for the other 8 handlers already pass today (raw `action_done` check already
blocks), but "libera a ação"/"crédito consumido" fail because
`handle_libertar_prisioneiro` doesn't know about the credit yet.

- [ ] **Step 3: Migrate each of the 9 raw checks to `_acao_bloqueada`**

In `server.py`, apply these 9 exact replacements (find each block, replace only the
`action_done` line as shown — nothing else in each handler changes):

**`handle_animar_mortos`** (~line 6336):
```python
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."})
            return
```
→
```python
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."})
            return
```

**`handle_cura`** (~line 7173):
```python
        if p.get("action_done"):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return
```
→
```python
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return
```

**`handle_cura_area`** (~line 7224) — same substitution as `handle_cura` (identical
line text, different function). Apply the same `p.get("action_done")` →
`self._acao_bloqueada(p)` replacement.

**`handle_purificacao`** (~line 7295) — same substitution, identical line text.

**`handle_ressurreicao`** (~line 7378) — same substitution, identical line text.

**`handle_imposicao_maos`** (~line 7428) — same substitution, identical line text.

**`handle_criar_armadilha`** (~line 10279) — same substitution, identical line text.

**`handle_desarmar_armadilha`** (~line 10492) — same substitution, identical line text.

> The six lines above are byte-for-byte identical
> (`if p.get("action_done"):\n            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return`)
> but appear in different functions — edit each occurrence in place (don't use a
> blind find-and-replace-all across the file, since `handle_animar_mortos`'s version
> has the `send_to`/`return` split across two lines instead of one).

**`handle_libertar_prisioneiro`** (line 14042) — different shape (silent return,
no error message):
```python
        p = self.players.get(pid)
        if not p or not p.get("alive") or p.get("action_done"):
            return
```
→
```python
        p = self.players.get(pid)
        if not p or not p.get("alive") or self._acao_bloqueada(p):
            return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tools/test_tecnicas_espec.py`
Expected: all `[22]` checks `✅`, `FAIL=0`.

- [ ] **Step 5: Run the FULL existing test suite to check for regressions**

Run: `python tools/test_tecnicas_espec.py`
Also run the other Guild-related suites touched indirectly by this refactor (cura/
imposição de mãos/criar armadilha/etc. are exercised by class-specific suites):

```bash
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_ladino_espec.py
python tools/test_reviver_mortos.py
```

Expected: `FAIL=0` on every suite (the migration only changes behavior when a
Velocidade/Oportunidade credit is present — none of those pre-existing tests set
those fields, so `_acao_bloqueada(p)` returns exactly what `p.get("action_done")`
returned before).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "refactor(guilda): unifica 9 handlers em _acao_bloqueada (Oportunidade cobre todas as ações principais)"
```

---

## Task 6: Cliente — `gameState.js` sender

**Files:**
- Modify: `src/gameState.js:1115` (add sender right after `usarTecnica`)
- Modify: `src/gameState.js:1696` (export it)

- [ ] **Step 1: Add the sender**

In `src/gameState.js`, find this exact line (1115):

```javascript
  function usarTecnica(tid, targetId) { send({ type: 'usar_tecnica', tecnica_id: tid, target_id: targetId != null ? targetId : null }); }
```

Add right after it:

```javascript
  function usarTecnica(tid, targetId) { send({ type: 'usar_tecnica', tecnica_id: tid, target_id: targetId != null ? targetId : null }); }
  function usarOportunidadeMovimento() { send({ type: 'usar_oportunidade_movimento' }); }
```

- [ ] **Step 2: Export it in the public API**

In `src/gameState.js`, find this exact line (1696):

```javascript
    usarTecnica,
```

Add right after it:

```javascript
    usarTecnica,
    usarOportunidadeMovimento,
```

- [ ] **Step 3: Verify no syntax errors**

Run: `node --check src/gameState.js`
Expected: no output (exit code 0).

- [ ] **Step 4: Commit**

```bash
git add src/gameState.js
git commit -m "feat(guilda): GS.usarOportunidadeMovimento — envia a via de movimento da Oportunidade"
```

---

## Task 7: Cliente — botão no HUD para quem tem o crédito

**Files:**
- Modify: `game.js` — right after the Guild-technique button loop (after line 10019,
  the closing `};` of the `btn.onclick` handler inside the `for(const tid of
  _tecIds)` loop shown below)

- [ ] **Step 1: Locate the insertion point and add the button block**

In `game.js`, find this exact block (lines 9971-9991 show the loop header; the
insertion point is right after the loop's closing brace, which is a few lines below
what's shown in Step 2 of Task 4's context — the loop iterates `_tecIds` and ends
before the next unrelated UI section). Find this exact anchor line (the loop
variable declaration, unique in the file):

```javascript
  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = [_tecEq.tecnica, _tecEq.tecnica_exclusiva].filter(Boolean);
  for(const tid of _tecIds){
```

Immediately **before** that block, add the Oportunidade credit indicator (it must
render independently of whether the player has any technique equipped — the
credit was granted by an *ally's* Oportunidade, not by this player's own 4th slot):

```javascript
  // ── Crédito de Oportunidade (Fase 2d) — concedido por um aliado, gasto no próprio turno ──
  if (me.oportunidade_credito && me.oportunidade_round === state.round && GS.isMyTurn && me.alive && state.phase === 'playing') {
    const btnOp = document.createElement('button');
    btnOp.className = 'skill-btn guild-tec';
    btnOp.innerHTML = `
      <div class="skill-info">
        <div class="skill-name">⏳ Oportunidade <small style="color:var(--gold);font-size:.58rem;">GUILDA</small></div>
        <div class="skill-desc">Gaste o crédito extra em movimento agora, ou apenas aja normalmente (atacar/curar/lançar magia/etc.) para gastá-lo automaticamente.</div>
      </div>
      <div class="skill-cost">mover +${me.spd||0}</div>`;
    btnOp.onclick = () => GS.usarOportunidadeMovimento();
    sl.appendChild(btnOp);
  }

  const _tecEq  = GS.guildEquipOf(me.id);
  const _tecIds = [_tecEq.tecnica, _tecEq.tecnica_exclusiva].filter(Boolean);
  for(const tid of _tecIds){
```

- [ ] **Step 2: Verify no syntax errors**

Run: `node --check game.js`
Expected: no output (exit code 0).

- [ ] **Step 3: Manual smoke check (dev server)**

Start the game (`iniciar.bat` or `python server.py` + open
`http://localhost:8765/index.html`), join with 2 players, one buys+equips
Oportunidade in the Guild, uses it on the other ally mid-dungeon, ends turn until
it's the ally's turn: confirm the "⏳ Oportunidade" button appears in the ally's
HUD, clicking it adds `spd` to their movement and the button disappears; separately
verify that instead of clicking it, just performing a normal action (e.g. attack)
after already acting also consumes the credit silently (no "Ação principal já
usada" error).

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(guilda): botão de crédito de Oportunidade no HUD do aliado"
```

---

## Task 8: Verificação final

- [ ] **Step 1: Run the full technique test suite one more time**

Run: `python tools/test_tecnicas_espec.py`
Expected: `FAIL=0`, all sections `[1]`–`[22]` pass.

- [ ] **Step 2: Run the class-specific suites touched by the `_acao_bloqueada` migration**

```bash
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_ladino_espec.py
python tools/test_reviver_mortos.py
python tools/test_guilda.py
```

Expected: `FAIL=0` on every suite.

- [ ] **Step 3: Update the roadmap memory**

This is a documentation-only step (not a code change) — after all tests pass,
update `guilda-especializacoes-roadmap.md` in the memory directory to record that
Fase 2d (Oportunidade) is implemented, mirroring how 2a/2b/2c were recorded.
