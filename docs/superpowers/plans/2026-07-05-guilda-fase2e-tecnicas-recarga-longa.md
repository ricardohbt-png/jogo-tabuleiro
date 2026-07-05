# Guilda dos Heróis — Fase 2e: Técnicas de Recarga Longa — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4 new técnicas da Guilda (tier 10, recarga 10 rodadas) — Instinto de
Sobrevivência, Último Esforço, Golpe Decisivo, Sorte — following the spec at
`docs/superpowers/specs/2026-07-05-guilda-fase2e-tecnicas-recarga-longa-design.md`.

**Architecture:** Instinto de Sobrevivência and Último Esforço auto-trigger from a
new branch in `_player_dies` (same pattern as the existing Paladin Regeneração
branch). Último Esforço additionally opens a special "last stand" sub-phase
(mirrors the existing animados/prisioneiro post-turn window pattern) that pauses
the calling coroutine on an `asyncio.Event` until the hero's 2 bonus turns end.
Golpe Decisivo and Sorte are ordinary `usar_tecnica`-activated técnicas that hook
`handle_attack`'s existing hit/miss resolution. A single `_forca_critico` concept
(Golpe Decisivo armed OR Último Esforço active) generalizes the existing
`if crit: dmg *= 2` into a 2×/3× multiplier, shared by both. Sorte's reroll reuses
a newly extracted `_resolver_dano_ataque_basico` helper instead of duplicating
`handle_attack`'s ~40 lines of weapon-damage math.

**Tech Stack:** Python 3 (asyncio, `websockets`) server; vanilla JS client
(`game.js` + `src/gameState.js`); custom test harness (`python tools/test_X.py`,
not pytest).

---

## Task 1: Catálogo, template do jogador e serialização do game_state

**Files:**
- Modify: `server.py` (GUILD_CATALOG ~line 396, após `tecnica_oportunidade`)
- Modify: `server.py` (template do jogador, ~linha 3452, após `"mov_bonus_ate": 0,`)
- Modify: `server.py` (`GameRoom.__init__`, ~linha 3779, após `self.animados_phase_pid = None`)
- Modify: `server.py` (reset de entrada na masmorra, ~linha 4888, após `self.animados_phase_pid = None`)
- Modify: `server.py` (payload do `game_state`, ~linha 14237, após `"animados_turn": self.animados_phase_pid,`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste de catálogo (vai falhar)**

Adicionar ao final de `tools/test_tecnicas_espec.py`, dentro de `async def main():`
(antes do fechamento da função — a última seção hoje é `# [22] Handlers migrados
para _acao_bloqueada`; **confirme com grep** `grep -n '# \[' tools/test_tecnicas_espec.py`
antes de inserir, caso o arquivo tenha mudado desde a escrita deste plano, e
continue a numeração a partir do próximo número real):

```python
    # [23] Catálogo — Recarga Longa (Fase 2e)
    print("\n[23] Catálogo — Recarga Longa (2e)")
    for tid, cf in [("tecnica_instinto_sobrevivencia", 6), ("tecnica_ultimo_esforco", 6),
                    ("tecnica_golpe_decisivo", 6), ("tecnica_sorte", 2)]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 10", it and it["recarga_rodadas"] == 10)
        check(f"{tid} preco 350", it and it["preco"] == 350)
        check(f"{tid} custo {cf}/{cf}", it and it["custo_fome"] == cf and it["custo_sede"] == cf)
        check(f"{tid} classe None", it and it["classe"] is None)
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: as novas checagens do bloco `[23]` falham com `❌` (os `it` retornam
`None` porque as entradas ainda não existem no catálogo).

- [ ] **Step 3: Adicionar as 4 entradas no `GUILD_CATALOG`**

Em `server.py`, logo depois do bloco `"tecnica_oportunidade": { ... },` (linha
~400), adicionar:

```python
    # ── Técnicas de Recarga Longa (Fase 2e) ─────────────────────────────────
    "tecnica_instinto_sobrevivencia": {
        "id": "tecnica_instinto_sobrevivencia", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
        "nome": "Instinto de Sobrevivência", "icon": "🍀", "automatica": True,
        "desc": "Automática. Se um dano zeraria seu HP, você fica com 1 em vez de "
                "morrer. Depois disso, entra em recarga.",
        "efeito": {"tipo": "passiva_evitar_morte"},
    },
    "tecnica_ultimo_esforco": {
        "id": "tecnica_ultimo_esforco", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
        "nome": "Último Esforço", "icon": "🔥", "automatica": True,
        "desc": "Automática. Se um dano zeraria seu HP, você fica com 1 e ganha 2 "
                "turnos seguidos: todo ataque tem vantagem e todo acerto é crítico "
                "(nat20 → dano TRIPLICADO). Não pode se curar. Ao final, cai como se "
                "tivesse morrido normalmente (pode ser reerguido por Ressurreição).",
        "efeito": {"tipo": "passiva_ultimo_esforco"},
    },
    "tecnica_golpe_decisivo": {
        "id": "tecnica_golpe_decisivo", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 10,
        "nome": "Golpe Decisivo", "icon": "💥",
        "desc": "Arma o próximo ataque básico (corpo a corpo ou à distância): se "
                "acertar, é crítico automático (dano dobrado); num natural 20 "
                "enquanto armado, o dano é TRIPLICADO. Consumida no próximo ataque, "
                "acerte ou erre.",
        "efeito": {"tipo": "golpe_decisivo"},
    },
    "tecnica_sorte": {
        "id": "tecnica_sorte", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 350, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 10,
        "nome": "Sorte", "icon": "🎲",
        "desc": "Depois de errar um ataque, você pode gastar esta técnica para "
                "rolá-lo novamente contra o mesmo alvo. Independente do Sangue Frio.",
        "efeito": {"tipo": "sorte"},
    },
```

- [ ] **Step 4: Rodar o teste de novo e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: todas as checagens do bloco `[23]` com `✅`.

- [ ] **Step 5: Adicionar os campos novos no template do jogador**

Em `server.py`, logo depois de `"mov_bonus_ate": 0,` (linha ~3452):

```python
        "tecnica_golpe_decisivo_armado": False,   # Golpe Decisivo: próximo ataque básico
        "ultimo_ataque_perdido": None,             # Sorte: {target_id, eff_atk, eff_target_ac, vantagem, desvantagem, surv_mod, cancao_dano, gl_dano}
        "ultimo_esforco_ativo": False,              # True durante a sub-fase do Último Esforço
        "ultimo_esforco_turnos_restantes": 0,       # 2 → 1 → 0 (fecha a sub-fase)
```

- [ ] **Step 6: Adicionar o estado de sala no `GameRoom.__init__`**

Em `server.py`, logo depois de `self.animados_phase_pid = None  # pid no "turno dos servos" (logo após o mago)`
(linha ~3779):

```python
        self.last_stand_pid = None      # pid na sub-fase do Último Esforço (ou None)
        self.last_stand_event = None    # asyncio.Event sinalizado ao fechar a janela
        self.last_stand_timer_task = None
```

- [ ] **Step 7: Resetar `last_stand_pid` na entrada da masmorra**

Em `server.py`, logo depois de `self.animados_phase_pid = None   # ponteiro de turno transitório (zera em qualquer entrada)`
(linha ~4888):

```python
        self.last_stand_pid = None   # idem — nunca deve sobreviver a uma nova entrada
```

- [ ] **Step 8: Incluir `last_stand_pid` no payload de `game_state`**

Em `server.py`, logo depois de `"animados_turn": self.animados_phase_pid,   # pid no turno dos servos (ou None)`
(linha ~14237):

```python
            "last_stand_pid": self.last_stand_pid,   # pid na sub-fase do Último Esforço (ou None)
```

- [ ] **Step 9: Rodar a suíte inteira e confirmar que nada quebrou**

Run: `python tools/test_tecnicas_espec.py`
Expected: todas as seções (1 a 23) com `✅`, 0 `❌`.

- [ ] **Step 10: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): catálogo e estado base da Fase 2e (recarga longa)"
```

---

## Task 2: Instinto de Sobrevivência (`_player_dies`)

**Files:**
- Modify: `server.py` (`tem_espec`, ~linha 691 — adicionar `tem_tecnica_equipada` logo depois)
- Modify: `server.py` (`_player_dies`, ~linha 13872)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Adicionar à seção `[24]`:

```python
    # [24] Instinto de Sobrevivência
    print("\n[24] Instinto de Sobrevivência")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 5
    p = hero("warrior", "tecnica_instinto_sobrevivencia"); p["hp"] = 10; p["alive"] = True
    r.players["h"] = p
    await r._player_dies("h")
    check("instinto: sobrevive com 1 HP", p["hp"] == 1 and p["alive"] is True)
    check("instinto: recarga ativada", r.tecnica_restante(p, "tecnica_instinto_sobrevivencia") == 10)
    # Dentro da recarga, um novo "zerou o HP" mata normalmente.
    p["hp"] = 0
    await r._player_dies("h")
    check("instinto: morre normalmente dentro da recarga", p["alive"] is False)

    # Prioridade: Regeneração do Paladino (já existente) vence se ambos disponíveis.
    r2 = setup(); r2.current_pid = lambda: "h2"; r2.round_num = 1
    p2 = hero("paladin", "tecnica_instinto_sobrevivencia")
    p2["hp"] = 10; p2["alive"] = True; p2["regen_ressurge"] = True; p2["regen_pool"] = 5
    r2.players["h2"] = p2
    await r2._player_dies("h2")
    check("instinto: Regeneração do Paladino tem prioridade", p2["hp"] == 1 and p2["alive"] is True
          and r2.tecnica_restante(p2, "tecnica_instinto_sobrevivencia") == 0)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[24]` falha (nenhum ramo trata `tecnica_instinto_sobrevivencia` em
`_player_dies` ainda — o jogador morre em vez de ficar com 1 HP).

- [ ] **Step 3: Adicionar o helper `tem_tecnica_equipada`**

Em `server.py`, logo depois de `tem_espec` (linha ~693):

```python
def tem_tecnica_equipada(player, tecnica_id):
    """True se a técnica está no 4º slot equipado do jogador (normal ou exclusiva)."""
    eq = player.get("guild_equip", {})
    return tecnica_id in (eq.get("tecnica"), eq.get("tecnica_exclusiva"))
```

- [ ] **Step 4: Adicionar o ramo em `_player_dies`**

Em `server.py`, dentro de `_player_dies` (linha ~13872), logo depois do bloco
existente da Regeneração do Paladino (que termina em `return` na linha ~13882):

```python
    async def _player_dies(self, pid):
        p = self.players[pid]
        if not p["alive"]: return
        # Regeneração: se ainda há reserva, reergue com 1 HP em vez de cair (-3 fome/sede).
        if p.get("regen_ressurge") and p.get("regen_pool", 0) > 0:
            p["hp"] = 1
            p["fome"] = max(0, p.get("fome", 0) - 3)
            p["sede"] = max(0, p.get("sede", 0) - 3)
            p.pop("regen_pool", None); p.pop("regen_ressurge", None)
            await self.gm_say(f"🌿 **{p['name']}** seria derrotado, mas a **Regeneração** o reergue com 1 HP! (-3 fome/sede)")
            return
        if (tem_tecnica_equipada(p, "tecnica_instinto_sobrevivencia")
                and self.tecnica_restante(p, "tecnica_instinto_sobrevivencia") == 0):
            p["hp"] = 1
            p["technique_cooldowns"]["tecnica_instinto_sobrevivencia"] = self.round_num + 10
            await self.gm_say(f"🍀 **{p['name']}** recorre ao **Instinto de Sobrevivência** e resiste com 1 HP!")
            return
        p["alive"] = False
        p["hp"] = 0
        ...   # resto do corpo já existente — INALTERADO
```

(Só as duas linhas do novo `if` são inseridas; nada abaixo de `p["alive"] = False`
muda.)

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[24]` inteira com `✅`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Instinto de Sobrevivência (Fase 2e)"
```

---

## Task 3: Golpe Decisivo + generalização do multiplicador de crítico

**Files:**
- Modify: `server.py` (`handle_usar_tecnica`, ~linha 4420, novo `elif`)
- Modify: `server.py` (`handle_attack`, ~linhas 5766-5860 — vantagem, `_forca_critico`, e os 2 sites `if crit: dmg *= 2`)
- Modify: `server.py` (`handle_end_turn`, ~linha 11147, expira flag não usada)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[25]`:

```python
    # [25] Golpe Decisivo
    print("\n[25] Golpe Decisivo")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r._is_turn = lambda pid: True
    p = hero("warrior", "tecnica_golpe_decisivo"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_golpe_decisivo")
    check("golpe: flag armada", p.get("tecnica_golpe_decisivo_armado") is True)
    check("golpe: recarga setada", r.tecnica_restante(p, "tecnica_golpe_decisivo") == 10)

    # Integração: acerto SEM nat20 vira crítico (×2); acerto COM nat20 vira ×3.
    def _mk_room_golpe(natural20):
        rr = setup(); rr.current_pid = lambda: "h"; rr._is_turn = lambda pid: True
        hh = hero("warrior"); hh["tecnica_golpe_decisivo_armado"] = True; hh["pos"] = [0, 0]
        hh["atk_bonus"] = 0
        hh["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
        rr.players["h"] = hh
        rr.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                              "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
        roll = 20 if natural20 else 12
        rr._rolar_ataque = lambda atk, ac, v=False, d=False: (True, roll, roll + atk, roll == 20, None)
        rr._golpe_raw = lambda p_, raw: raw   # sem especialização do guerreiro interferindo
        return rr, hh
    rr1, hh1 = _mk_room_golpe(False)
    hp0 = rr1.monsters["m1"]["hp"]
    await rr1.handle_attack("h", "m1")
    dmg1 = hp0 - rr1.monsters["m1"]["hp"]
    check("golpe: acerto sem nat20 vira crítico (dobrado)", dmg1 >= 2)   # 1d6(min1)+0, dobrado >=2
    check("golpe: flag consumida após o ataque", hh1.get("tecnica_golpe_decisivo_armado") is False)

    rr2, hh2 = _mk_room_golpe(True)
    hp0b = rr2.monsters["m1"]["hp"]
    await rr2.handle_attack("h", "m1")
    dmg2 = hp0b - rr2.monsters["m1"]["hp"]
    check("golpe: nat20 enquanto armado triplica", dmg2 >= 3)

    # Consumida mesmo em erro.
    rr3, hh3 = _mk_room_golpe(False)
    rr3._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 2, False, None)
    await rr3.handle_attack("h", "m1")
    check("golpe: consumida mesmo errando", hh3.get("tecnica_golpe_decisivo_armado") is False)

    # Expira no fim do turno sem uso.
    r4 = setup(); r4.current_pid = lambda: "h"
    p4 = hero("warrior"); p4["tecnica_golpe_decisivo_armado"] = True; p4["moves_left"] = p4["spd"]
    r4.players["h"] = p4
    r4.player_order = ["h"]; r4.turn_index = 0
    await r4.handle_end_turn("h")
    check("golpe: expira no fim do turno sem uso", p4.get("tecnica_golpe_decisivo_armado") is False)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[25]` falha (`handle_usar_tecnica` não tem ramo `golpe_decisivo`;
`handle_attack` não força crítico).

- [ ] **Step 3: Adicionar o ramo de ativação em `handle_usar_tecnica`**

Em `server.py`, logo depois de `elif ef.get("tipo") == "oportunidade": ...` (o
bloco termina em `alvo["oportunidade_round"] = self.round_num` — linha ~4428):

```python
        elif ef.get("tipo") == "golpe_decisivo":
            p["tecnica_golpe_decisivo_armado"] = True
```

- [ ] **Step 4: Generalizar o multiplicador de crítico em `handle_attack`**

Em `server.py`, no trecho de `handle_attack` (linhas ~5766-5782), o código atual é:

```python
            esc = self._verificar_escuridao(p, target)
            _mira_ranged = bool(w_range is not None and p.get("tecnica_mira_perfeita"))
            _investida = bool(w_range is None and self._investida_tecnica_bonus(p, is_ranged=False))
            vantagem    = (bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela"))
                           or esc == "vantagem"
                           or self._provocacao_atk_vantagem(p, target)
                           or _mira_ranged or _investida)
            desvantagem = esc == "desvantagem"
            hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if not hit and self._sangue_frio_consumir(p):
                await self.gm_say(f"🧊 **{p['name']}** mantém o sangue frio e rola novamente!")
                hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if _mira_ranged:
                p["tecnica_mira_perfeita"] = False   # consumida no ataque à distância (acerto ou erro)
            if p.get("investida_armada") and w_range is None:
                p["investida_armada"] = False   # consome no 1º ataque corpo a corpo
```

Trocar por (adiciona `_forca_critico` à disjunção da vantagem, guarda-o antes de
rolar, força `crit=True` no acerto, consome Golpe Decisivo, e adiciona o
armazenamento do erro para a Sorte — este último implementado na Task 4, aqui só
deixamos o `hit`/`roll` acessíveis):

```python
            esc = self._verificar_escuridao(p, target)
            _mira_ranged = bool(w_range is not None and p.get("tecnica_mira_perfeita"))
            _investida = bool(w_range is None and self._investida_tecnica_bonus(p, is_ranged=False))
            _forca_critico = bool(p.get("tecnica_golpe_decisivo_armado")) or bool(p.get("ultimo_esforco_ativo"))
            vantagem    = (bool(p.get("invisivel_magico")) or bool(p.get("oculto_vela"))
                           or esc == "vantagem"
                           or self._provocacao_atk_vantagem(p, target)
                           or _mira_ranged or _investida or bool(p.get("ultimo_esforco_ativo")))
            desvantagem = esc == "desvantagem"
            hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if not hit and self._sangue_frio_consumir(p):
                await self.gm_say(f"🧊 **{p['name']}** mantém o sangue frio e rola novamente!")
                hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if hit and _forca_critico:
                crit = True
            if p.get("tecnica_golpe_decisivo_armado"):
                p["tecnica_golpe_decisivo_armado"] = False   # consumida no próximo ataque, acerte ou erre
            if _mira_ranged:
                p["tecnica_mira_perfeita"] = False   # consumida no ataque à distância (acerto ou erro)
            if p.get("investida_armada") and w_range is None:
                p["investida_armada"] = False   # consome no 1º ataque corpo a corpo
```

Em seguida, nos DOIS pontos de dano (arma e desarmado, dentro do `if hit:` mais
abaixo), o código atual tem:

```python
                    dmg = raw_dmg + stat_bonus
                    if crit: dmg *= 2
```

e

```python
                    dmg = base + str_bonus
                    if crit: dmg *= 2
```

Trocar as DUAS ocorrências de `if crit: dmg *= 2` por:

```python
                    if crit: dmg *= 3 if (_forca_critico and roll == 20) else 2
```

- [ ] **Step 5: Expirar a flag no fim do turno**

Em `server.py`, em `handle_end_turn` (linha ~11147), logo depois de
`p["tecnica_mira_perfeita"] = False   # Mira Perfeita não usada expira no fim do turno`:

```python
        p["tecnica_golpe_decisivo_armado"] = False   # Golpe Decisivo não usado expira no fim do turno
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[25]` inteira com `✅`; nenhuma seção anterior (1-24) quebrou.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Golpe Decisivo + multiplicador de crítico generalizado (Fase 2e)"
```

---

## Task 4: Sorte (reroll reativo)

**Files:**
- Modify: `server.py` (novo helper `_resolver_dano_ataque_basico`, perto de `_sangue_frio_consumir`, ~linha 4330)
- Modify: `server.py` (`handle_attack` — refatorar os 2 sites de dano para chamar o helper, e armazenar `ultimo_ataque_perdido` no erro)
- Modify: `server.py` (`handle_usar_tecnica`, novo `elif` para `sorte`)
- Modify: `server.py` (`handle_end_turn`, limpar `ultimo_ataque_perdido`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[26]`:

```python
    # [26] Sorte
    print("\n[26] Sorte")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r._is_turn = lambda pid: True
    p = hero("warrior", "tecnica_sorte"); p["pos"] = [0, 0]
    p["atk_bonus"] = 0
    p["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
    r.players["h"] = p
    r.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                         "hp": 30, "max_hp": 30, "ac": 10, "ca": 10}}
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 2, False, None)   # erra
    await r.handle_attack("h", "m1")
    check("sorte: erro guarda ultimo_ataque_perdido", p.get("ultimo_ataque_perdido") is not None)
    check("sorte: alvo guardado é o m1", p["ultimo_ataque_perdido"]["target_id"] == "m1")

    async def _mdies(*a, **k): return None
    r._monster_dies = _mdies
    r._golpe_raw = lambda p_, raw: raw
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 15, 15, False, None)   # reroll acerta
    hp0 = r.monsters["m1"]["hp"]
    await r.handle_usar_tecnica("h", "tecnica_sorte")
    check("sorte: reroll acerta e aplica dano", r.monsters["m1"]["hp"] < hp0)
    check("sorte: limpa ultimo_ataque_perdido após usar", p.get("ultimo_ataque_perdido") is None)
    check("sorte: recarga setada", r.tecnica_restante(p, "tecnica_sorte") == 10)

    # Sem erro recente: recusa educadamente.
    r2 = setup(); r2.current_pid = lambda: "h"; r2._is_turn = lambda pid: True
    p2 = hero("warrior", "tecnica_sorte"); r2.players["h"] = p2
    await r2.handle_usar_tecnica("h", "tecnica_sorte")
    check("sorte: recusa sem ataque recente", "Nenhum ataque recente" in (r2._errs[-1] if r2._errs else ""))

    # Limpo no fim do turno.
    r3 = setup(); r3.current_pid = lambda: "h"
    p3 = hero("warrior"); p3["ultimo_ataque_perdido"] = {"target_id": "m1"}; p3["moves_left"] = p3["spd"]
    r3.players["h"] = p3; r3.player_order = ["h"]; r3.turn_index = 0
    await r3.handle_end_turn("h")
    check("sorte: ultimo_ataque_perdido limpo no fim do turno", p3.get("ultimo_ataque_perdido") is None)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[26]` falha (nada guarda `ultimo_ataque_perdido`; `handle_usar_tecnica`
não tem ramo `sorte`).

- [ ] **Step 3: Extrair o helper `_resolver_dano_ataque_basico`**

Em `server.py`, logo antes de `_sangue_frio_consumir` (linha ~4330), adicionar:

```python
    def _resolver_dano_ataque_basico(self, p, target, crit, roll, forca_critico=False,
                                       surv_mod=0, cancao_dano=0, gl_dano=0, bonus_extra=0):
        """Rola e computa o dano físico de um ataque básico (arma ou desarmado)
        que JÁ acertou — reaproveitado pelo hit normal de handle_attack e pelo
        reroll da Sorte. `forca_critico` é quem decide se um natural 20 triplica
        (Golpe Decisivo/Último Esforço) em vez de dobrar. Retorna
        (dmg, weapon_name, dmg_detail, raw_dmg, die_str) — raw_dmg/die_str são
        None no ataque desarmado (sem dado de arma). Não repete munição/veneno/
        furtivo/projétil incendiário — resolvidos à parte pelo chamador."""
        weapon = p.get("weapon")
        die_str = weapon.get("die") if weapon else None
        if die_str:
            raw_dmg = roll_dice(die_str)
            raw_dmg = self._golpe_raw(p, raw_dmg)
            if weapon.get("finesse"):
                stat_bonus = max(mod(p.get("str_", 12)), mod(p.get("dex", 12)))
            else:
                stat_bonus = mod(p.get(weapon["stat"], 12))
            dmg = raw_dmg + stat_bonus
            weapon_name = weapon.get("name", "arma")
            sb = f"+{stat_bonus}" if stat_bonus >= 0 else str(stat_bonus)
            dmg_detail = f"[{die_str}={raw_dmg}{sb}]"
        else:
            raw_dmg = None
            str_bonus = mod(p.get("str_", 12))
            base = 2 if p.get("skill_dobrar_dano") else 1
            dmg = base + str_bonus
            weapon_name = "soco"
            sb = f"+{str_bonus}" if str_bonus >= 0 else str(str_bonus)
            dmg_detail = f"[{base}{sb}]"
        if crit:
            dmg *= 3 if (forca_critico and roll == 20) else 2
        dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + bonus_extra
                  + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p)
                  + p.get("skill_bonus_dano", 0) - self._corrosao_arma_pen(p))
        dmg = self._apply_damage_types(dmg, [DMG_PHYSICAL], target, weapon)
        return dmg, weapon_name, dmg_detail, raw_dmg, die_str
```

- [ ] **Step 4: Fazer `handle_attack` chamar o helper (substitui os 2 blocos de dano)**

Em `server.py`, o trecho atual de `handle_attack` (dentro de `if hit:`) é:

```python
            if hit:
                weapon = p.get("weapon")
                die_str = weapon.get("die") if weapon else None
                if die_str:
                    # Armed attack — roll weapon die
                    raw_dmg = roll_dice(die_str)
                    raw_dmg = self._golpe_raw(p, raw_dmg)   # Golpe: ×1,5 base / ×2 com Nível III
                    # finesse (atributo 'forcaOuDestreza'): melhor de FOR/DES
                    if weapon.get("finesse"):
                        stat_bonus = max(mod(p.get("str_", 12)), mod(p.get("dex", 12)))
                    else:
                        stat_bonus = mod(p.get(weapon["stat"], 12))
                    dmg = raw_dmg + stat_bonus
                    if crit: dmg *= 3 if (_forca_critico and roll == 20) else 2
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p)
                              + (2 if _mira_ranged else 0)   # Mira Perfeita: +2 no ataque à distância
                              + (2 if _investida else 0)      # Investida Heroica (carga reta ≥2)
                              + p.get("skill_bonus_dano", 0)
                              - self._corrosao_arma_pen(p))
                    # Fraquezas/imunidades ao dano físico da arma
                    dmg = self._apply_damage_types(dmg, [DMG_PHYSICAL], target, weapon)
                    die_type = "d" + die_str.split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
                    weapon_name = weapon.get("name", "arma")
                    sb = f"+{stat_bonus}" if stat_bonus >= 0 else str(stat_bonus)
                    dmg_detail = f"[{die_str}={raw_dmg}{sb}]"
                else:
                    # Unarmed — fixed 1 + STR modifier
                    str_bonus = mod(p.get("str_", 12))
                    base = 2 if p.get("skill_dobrar_dano") else 1   # Golpe Devastador
                    dmg = base + str_bonus
                    if crit: dmg *= 3 if (_forca_critico and roll == 20) else 2
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano + self._mod_magia(p, "dano")
                              + self._tecnica_bonus_dano(p))
                    weapon_name = "soco"
                    sb = f"+{str_bonus}" if str_bonus >= 0 else str(str_bonus)
                    dmg_detail = f"[{base}{sb}]"
```

Substituir o bloco INTEIRO acima (só a parte que computava `dmg`/`weapon_name`/
`dmg_detail` inline — o restante do `if hit:` logo abaixo, como Golpe Sagrado,
Ataque Furtivo, `target["hp"] -= dmg`, munição incendiária, veneno e morte do
monstro, **continua exatamente igual**, sem mudanças) por:

```python
            if hit:
                _bonus_extra = (2 if _mira_ranged else 0) + (2 if _investida else 0)
                dmg, weapon_name, dmg_detail, raw_dmg, die_str = self._resolver_dano_ataque_basico(
                    p, target, crit, roll, forca_critico=_forca_critico,
                    surv_mod=surv_mod, cancao_dano=cancao_dano, gl_dano=gl_dano,
                    bonus_extra=_bonus_extra)
                if die_str:
                    die_type = "d" + die_str.split("d")[1]
                    await self.broadcast({"type": "dice_roll", "die": die_type,
                                           "value": raw_dmg, "label": "Dano"})
```

- [ ] **Step 5: Armazenar o erro para a Sorte**

Em `server.py`, no mesmo trecho de `handle_attack` da Task 3 (logo depois de
`if p.get("investida_armada") and w_range is None: p["investida_armada"] = False`),
adicionar:

```python
            if not hit and tem_tecnica_equipada(p, "tecnica_sorte"):
                p["ultimo_ataque_perdido"] = {
                    "target_id": target_id, "eff_atk": eff_atk, "eff_target_ac": eff_target_ac,
                    "vantagem": vantagem, "desvantagem": desvantagem,
                    "surv_mod": surv_mod, "cancao_dano": cancao_dano, "gl_dano": gl_dano,
                }
```

- [ ] **Step 6: Adicionar o ramo reativo em `handle_usar_tecnica`**

Em `server.py`, logo depois do `elif ef.get("tipo") == "golpe_decisivo":` (Task 3):

```python
        elif ef.get("tipo") == "sorte":
            perdido = p.get("ultimo_ataque_perdido")
            if not perdido:
                await self.send_to(pid, {"type": "error", "msg": "Nenhum ataque recente para rerolar."})
                return
            alvo = self.monsters.get(perdido["target_id"])
            if not alvo or alvo.get("hp", 0) <= 0:
                await self.send_to(pid, {"type": "error", "msg": "O alvo não está mais disponível."})
                return
            hit, roll, total, crit, _desc = self._rolar_ataque(
                perdido["eff_atk"], perdido["eff_target_ac"], perdido["vantagem"], perdido["desvantagem"])
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                                   "label": "🎲 Sorte (nova rolagem)", "hit": hit, "crit": crit})
            if hit:
                dmg, weapon_name, dmg_detail, raw_dmg, die_str = self._resolver_dano_ataque_basico(
                    p, alvo, crit, roll, surv_mod=perdido.get("surv_mod", 0),
                    cancao_dano=perdido.get("cancao_dano", 0), gl_dano=perdido.get("gl_dano", 0))
                alvo["hp"] -= dmg
                await self.gm_say(f"🎲 **{p['name']}** força a Sorte e acerta **{alvo['name']}** com {weapon_name} {dmg_detail} = **{dmg}**!")
                if alvo["hp"] <= 0:
                    await self._monster_dies(alvo, pid)
            else:
                await self.gm_say(f"🎲 **{p['name']}** tenta a Sorte de novo, mas erra outra vez!")
            p["ultimo_ataque_perdido"] = None
```

(Este `elif` faz o próprio débito de fome/sede/recarga via o rodapé comum de
`handle_usar_tecnica` — não precisa duplicar isso aqui.)

- [ ] **Step 7: Limpar `ultimo_ataque_perdido` no fim do turno**

Em `server.py`, em `handle_end_turn` (linha ~11147), logo depois da linha do Golpe
Decisivo (Task 3, Step 5):

```python
        p["ultimo_ataque_perdido"] = None   # Sorte: janela de reroll fecha no fim do turno
```

- [ ] **Step 8: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[26]` inteira com `✅`; seções 1-25 continuam `✅` (o refactor do
Step 4 não deve mudar nenhum resultado numérico das seções que já testam dano de
`handle_attack`).

- [ ] **Step 9: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Sorte + extração de _resolver_dano_ataque_basico (Fase 2e)"
```

---

## Task 5: Último Esforço — abertura da sub-fase

**Files:**
- Modify: `server.py` (`_is_turn`, ~linha 14169)
- Modify: `server.py` (`_player_dies`, novo ramo sem `return` antecipado)
- Modify: `server.py` (novo `_abrir_ultimo_esforco` + `_iniciar_timer_ultimo_esforco`/`_cancelar_timer_ultimo_esforco`, perto de `_iniciar_timer_turno`)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[27]` (parte 1 — abertura):

```python
    # [27] Último Esforço — abertura da sub-fase
    print("\n[27] Último Esforço — abertura")
    r = setup(); r.current_pid = lambda: "outro"; r.round_num = 3
    p = hero("warrior", "tecnica_ultimo_esforco"); p["hp"] = 10; p["alive"] = True; p["spd"] = 6
    r.players["h"] = p
    r.players["outro"] = hero("cleric"); r.players["outro"]["id"] = "outro"
    r.player_order = ["h", "outro"]

    # Não sobrescrevemos _abrir_ultimo_esforco — deixamos rodar de verdade, mas
    # fechamos a janela "de fora" via uma task concorrente logo após ela abrir.
    # IMPORTANTE: hp=1/ativo=True só valem ENQUANTO a janela está aberta — uma
    # vez que ela fecha (aqui, via este stub; na Task 6, via handle_end_turn de
    # verdade), _player_dies cai no fluxo normal de morte (hp=0/alive=False).
    # Por isso o check de "HP=1" precisa rodar DENTRO da task concorrente, no
    # momento em que a janela está detectada aberta — não depois que
    # _player_dies() já retornou (nesse ponto a morte já foi finalizada).
    async def _fechar_logo():
        while r.last_stand_pid != "h":
            await asyncio.sleep(0)
        check("último esforço: HP=1 enquanto a janela está aberta", p["hp"] == 1)
        check("último esforço: ainda vivo durante a janela", p["alive"] is True)
        check("último esforço: flag ativa durante a janela", p.get("ultimo_esforco_ativo") is True)
        r.players["h"]["ultimo_esforco_turnos_restantes"] = 0
        r.last_stand_pid = None
        r.last_stand_event.set()
    asyncio.create_task(_fechar_logo())
    await r._player_dies("h")
    check("último esforço: morte finalizada após a janela fechar", p["alive"] is False)
    check("último esforço: flag ativa desligada ao fechar", p.get("ultimo_esforco_ativo") is False)
    check("último esforço: recarga setada", r.tecnica_restante(p, "tecnica_ultimo_esforco") == 10)

    # _is_turn aceita o pid em último esforço mesmo sem ser current_pid()
    r2 = setup(); r2.current_pid = lambda: "outro"
    r2.last_stand_pid = "h"
    check("último esforço: _is_turn aceita last_stand_pid", r2._is_turn("h") is True)
    check("último esforço: _is_turn normal p/ outros", r2._is_turn("ninguem") is False)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[27]` falha (`_is_turn` não conhece `last_stand_pid`;
`_player_dies` não abre sub-fase; `r.last_stand_event` é `None`, o teste trava ou
lança `AttributeError`).

- [ ] **Step 3: Estender `_is_turn`**

Em `server.py` (linha ~14169), o código atual:

```python
    def _is_turn(self, pid):
        return self.phase == "playing" and self.current_pid() == pid
```

Trocar por:

```python
    def _is_turn(self, pid):
        if self.phase != "playing":
            return False
        return self.current_pid() == pid or self.last_stand_pid == pid
```

- [ ] **Step 4: Adicionar o timer dedicado do Último Esforço**

Em `server.py`, logo depois de `_turn_timer_expira` (linha ~5028-5036), adicionar:

```python
    def _cancelar_timer_ultimo_esforco(self):
        t = self.last_stand_timer_task
        if t and not t.done():
            t.cancel()
        self.last_stand_timer_task = None

    def _iniciar_timer_ultimo_esforco(self, pid):
        self._cancelar_timer_ultimo_esforco()
        self.last_stand_timer_task = asyncio.create_task(self._ultimo_esforco_timer_expira(pid))

    async def _ultimo_esforco_timer_expira(self, pid):
        try:
            await asyncio.sleep(self.TURN_LIMIT_S)
        except asyncio.CancelledError:
            return
        if self.last_stand_pid != pid:
            return
        await self._fechar_mini_turno_ultimo_esforco(pid, forcar_fim=True)
```

(`_fechar_mini_turno_ultimo_esforco` é implementado na Task 6 — por ora este
código só compila; o teste desta task não exercita o timer.)

- [ ] **Step 5: Adicionar `_abrir_ultimo_esforco`**

Em `server.py`, logo depois de `_cancelar_timer_ultimo_esforco`/`_iniciar_timer_ultimo_esforco`:

```python
    async def _abrir_ultimo_esforco(self, p):
        pid = p["id"]
        p["ultimo_esforco_ativo"] = True
        p["ultimo_esforco_turnos_restantes"] = 2
        p["moves_left"] = p.get("spd", 0)
        p["action_done"] = False
        self.last_stand_pid = pid
        self.last_stand_event = asyncio.Event()
        await self.gm_say(f"🔥 **{p['name']}** recusa a morte — **ÚLTIMO ESFORÇO**! Dois turnos de fúria antes de cair.")
        await self.push_state()
        self._iniciar_timer_ultimo_esforco(pid)
        await self.last_stand_event.wait()
        p["ultimo_esforco_ativo"] = False
        p.pop("ultimo_esforco_turnos_restantes", None)
```

- [ ] **Step 6: Adicionar o ramo em `_player_dies` (sem `return`)**

Em `server.py`, em `_player_dies`, logo depois do ramo do Instinto de Sobrevivência
(Task 2) e ANTES de `p["alive"] = False`:

```python
        if (tem_tecnica_equipada(p, "tecnica_ultimo_esforco")
                and self.tecnica_restante(p, "tecnica_ultimo_esforco") == 0):
            p["hp"] = 1
            p["technique_cooldowns"]["tecnica_ultimo_esforco"] = self.round_num + 10
            await self._abrir_ultimo_esforco(p)
        p["alive"] = False
        p["hp"] = 0
        ...   # resto inalterado
```

- [ ] **Step 7: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[27]` (abertura) inteira com `✅`.

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Último Esforço — abertura da sub-fase (Fase 2e)"
```

---

## Task 6: Último Esforço — fechamento dos mini-turnos e desconexão

**Files:**
- Modify: `server.py` (`handle_end_turn`, novo branch no topo, ~linha 11073)
- Modify: `server.py` (novo `_fechar_mini_turno_ultimo_esforco`)
- Modify: `server.py` (`handle_disconnect_em_jogo`, ~linha 5063)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[27]` (parte 2 — fechamento), adicionar após a parte 1:

```python
    # [27b] Último Esforço — fechamento via end_turn (2 mini-turnos)
    print("\n[27b] Último Esforço — fechamento")
    r3 = setup(); r3.current_pid = lambda: "outro"; r3.round_num = 1
    p3 = hero("warrior", "tecnica_ultimo_esforco"); p3["hp"] = 1; p3["alive"] = True; p3["spd"] = 6
    r3.players["h"] = p3
    r3.last_stand_pid = "h"
    r3.last_stand_event = asyncio.Event()
    p3["ultimo_esforco_ativo"] = True
    p3["ultimo_esforco_turnos_restantes"] = 2
    check("fechamento: is_turn aceita antes de fechar", r3._is_turn("h") is True)
    await r3.handle_end_turn("h")   # fecha o 1º mini-turno
    check("fechamento: 1 mini-turno restante", p3["ultimo_esforco_turnos_restantes"] == 1)
    check("fechamento: janela ainda aberta", r3.last_stand_pid == "h")
    check("fechamento: moves_left resetado p/ o 2º mini-turno", p3["moves_left"] == p3["spd"])
    await r3.handle_end_turn("h")   # fecha o 2º mini-turno
    check("fechamento: janela fecha de vez", r3.last_stand_pid is None)
    check("fechamento: event sinalizado", r3.last_stand_event.is_set())

    # Desconexão durante a janela fecha imediatamente (não trava o jogo).
    r4 = setup(); r4.current_pid = lambda: "outro"
    p4 = hero("warrior"); p4["hp"] = 1; p4["alive"] = True; p4["connected"] = True
    r4.players["h"] = p4
    r4.host_pid = "outro"
    r4.players["outro"] = hero("cleric"); r4.players["outro"]["id"] = "outro"; r4.players["outro"]["connected"] = True
    r4.last_stand_pid = "h"
    r4.last_stand_event = asyncio.Event()
    p4["ultimo_esforco_ativo"] = True
    p4["ultimo_esforco_turnos_restantes"] = 2
    await r4.handle_disconnect_em_jogo("h")
    check("desconexão: fecha a janela do Último Esforço", r4.last_stand_pid is None)
    check("desconexão: event sinalizado", r4.last_stand_event.is_set())
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[27b]` falha (`handle_end_turn` não trata `last_stand_pid`;
`_fechar_mini_turno_ultimo_esforco` não existe; desconexão não fecha a janela).

- [ ] **Step 3: Adicionar `_fechar_mini_turno_ultimo_esforco`**

Em `server.py`, logo depois de `_abrir_ultimo_esforco` (Task 5):

```python
    async def _fechar_mini_turno_ultimo_esforco(self, pid, forcar_fim=False):
        p = self.players[pid]
        if forcar_fim:
            p["ultimo_esforco_turnos_restantes"] = 0
        else:
            p["ultimo_esforco_turnos_restantes"] -= 1
        if p["ultimo_esforco_turnos_restantes"] > 0:
            p["moves_left"] = p.get("spd", 0)
            p["action_done"] = False
            await self.gm_say(f"⚔️ **{p['name']}** continua o Último Esforço — mais um turno!")
            await self.push_state()
            self._iniciar_timer_ultimo_esforco(pid)
        else:
            self._cancelar_timer_ultimo_esforco()
            self.last_stand_pid = None
            self.last_stand_event.set()
```

- [ ] **Step 4: Interceptar em `handle_end_turn`**

Em `server.py`, `handle_end_turn` (linha ~11073), o topo atual é:

```python
    async def handle_end_turn(self, pid):
        if not self._is_turn(pid): return
        p = self.players[pid]
```

Trocar por:

```python
    async def handle_end_turn(self, pid):
        if not self._is_turn(pid): return
        if self.last_stand_pid == pid:
            await self._fechar_mini_turno_ultimo_esforco(pid)
            return
        p = self.players[pid]
```

- [ ] **Step 5: Fechar a janela na desconexão**

Em `server.py`, `handle_disconnect_em_jogo` (linha ~5063), logo depois de
`p["connected"] = False`:

```python
        if self.last_stand_pid == pid:
            await self._fechar_mini_turno_ultimo_esforco(pid, forcar_fim=True)
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seções `[27]` e `[27b]` inteiras com `✅`.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Último Esforço — fechamento dos mini-turnos e desconexão (Fase 2e)"
```

---

## Task 7: Último Esforço — proibição de auto-cura

**Files:**
- Modify: `server.py` (`handle_use_item`, efeito `"heal"`, ~linha 10841)
- Modify: `server.py` (`handle_cura`, ~linha 7224)
- Modify: `server.py` (`handle_cura_area`, loop de aliados, ~linha 7280)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[28]`:

```python
    # [28] Último Esforço — proibição de auto-cura
    print("\n[28] Último Esforço — sem auto-cura")
    r = setup(); r.current_pid = lambda: "h"; r._is_turn = lambda pid: True
    p = hero("warrior"); p["ultimo_esforco_ativo"] = True; p["hp"] = 1; p["max_hp"] = 20
    p["bag"] = [{"id": "pocao1", "effect": "heal", "value": 10, "emoji": "🧪", "name": "Poção"}]
    r.players["h"] = p
    await r.handle_use_item("h", "pocao1")
    check("último esforço: recusa poção de cura", p["hp"] == 1
          and "curar" in (r._errs[-1] if r._errs else "").lower())

    r2 = setup(); r2.current_pid = lambda: "h"; r2._is_turn = lambda pid: True
    lewis = hero("cleric"); lewis["ultimo_esforco_ativo"] = True; lewis["hp"] = 1; lewis["max_hp"] = 20
    lewis["fome"] = 20; lewis["sede"] = 20
    r2.players["h"] = lewis
    await r2.handle_cura("h", {"target_id": "h", "num_dados": 1})
    check("último esforço: recusa Cura em si mesmo", lewis["hp"] == 1)

    r3 = setup(); r3.current_pid = lambda: "h"; r3._is_turn = lambda pid: True
    lewis3 = hero("cleric"); lewis3["ultimo_esforco_ativo"] = True; lewis3["hp"] = 1; lewis3["max_hp"] = 20
    lewis3["fome"] = 20; lewis3["sede"] = 20; lewis3["pos"] = [0, 0]
    ally3 = make_player("a", "Ana", "warrior", 1); ally3["alive"] = True; ally3["hp"] = 1; ally3["max_hp"] = 20; ally3["pos"] = [1, 0]
    r3.players["h"] = lewis3; r3.players["a"] = ally3
    r3._tem_linha_de_visao = lambda a, b: True
    await r3.handle_cura_area("h", {"num_dados": 1})
    check("último esforço: Cura em Área não cura a si mesmo", lewis3["hp"] == 1)
    check("último esforço: Cura em Área cura os aliados normalmente", ally3["hp"] > 1)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[28]` falha (poção cura normalmente; `handle_cura` aceita
self-target; `handle_cura_area` cura o próprio Lewis também).

- [ ] **Step 3: Bloquear em `handle_use_item`**

Em `server.py` (linha ~10841), o código atual:

```python
        if effect == "heal":
            p["hp"] = min(p["max_hp"], p["hp"] + val)
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}** e recupera **{val}** HP!")
```

Trocar por:

```python
        if effect == "heal":
            if p.get("ultimo_esforco_ativo"):
                await self.send_to(pid, {"type": "error",
                    "msg": "🔥 Em Último Esforço você não pode se curar!"}); return
            p["hp"] = min(p["max_hp"], p["hp"] + val)
            await self.gm_say(f"{item['emoji']} **{p['name']}** usa **{item['name']}** e recupera **{val}** HP!")
```

- [ ] **Step 4: Bloquear em `handle_cura`**

Em `server.py` (linha ~7224), logo depois de
`alvo = self.players.get((data or {}).get("target_id"))`:

```python
        alvo = self.players.get((data or {}).get("target_id"))
        if p.get("ultimo_esforco_ativo") and (data or {}).get("target_id") == pid:
            await self.send_to(pid, {"type": "error",
                "msg": "🔥 Em Último Esforço você não pode se curar!"}); return
        if not alvo or not alvo.get("alive"):
```

- [ ] **Step 5: Pular o próprio caster em `handle_cura_area`**

Em `server.py` (linha ~7280), o loop atual:

```python
        curados = []
        for aliado in self.players.values():
            if not aliado.get("alive"): continue
            if not self._no_raio(p, aliado, raio): continue
```

Trocar por:

```python
        curados = []
        for aliado in self.players.values():
            if not aliado.get("alive"): continue
            if aliado["id"] == pid and p.get("ultimo_esforco_ativo"): continue
            if not self._no_raio(p, aliado, raio): continue
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[28]` inteira com `✅`.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "feat(guilda): Último Esforço — bloqueia auto-cura (Fase 2e)"
```

---

## Task 8: Recusar ativação manual de técnicas automáticas

**Files:**
- Modify: `server.py` (`handle_usar_tecnica`, checagem antes do `if/elif` de efeitos, ~linha 4359)
- Test: `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Escrever o teste (vai falhar)**

Seção `[29]`:

```python
    # [29] Recusa ativação manual de técnicas automáticas
    print("\n[29] Recusa ativação manual (automáticas)")
    for tid in ("tecnica_instinto_sobrevivencia", "tecnica_ultimo_esforco"):
        r = setup(); r.current_pid = lambda: "h"
        p = hero("warrior", tid); r.players["h"] = p
        f0 = p["fome"]
        await r.handle_usar_tecnica("h", tid)
        check(f"{tid}: recusa uso manual", "automática" in (r._errs[-1] if r._errs else "").lower())
        check(f"{tid}: não gasta fome/sede", p["fome"] == f0)
        check(f"{tid}: não ativa recarga", r.tecnica_restante(p, tid) == 0)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[29]` falha (hoje, `handle_usar_tecnica` cai no `if/elif` sem
nenhum ramo casar, e AINDA ASSIM debita fome/sede e ativa a recarga no rodapé
comum — bug real que este passo corrige).

- [ ] **Step 3: Adicionar a checagem**

Em `server.py`, `handle_usar_tecnica` (linha ~4359), logo depois de
`item = guild_item(tecnica_id)` / `if not item: return`:

```python
        item = guild_item(tecnica_id)
        if not item:
            return
        if item.get("automatica"):
            await self.send_to(pid, {"type": "error",
                "msg": f"{item['nome']} é automática — não pode ser ativada manualmente."})
            return
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_tecnicas_espec.py`
Expected: seção `[29]` inteira com `✅`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_tecnicas_espec.py
git commit -m "fix(guilda): recusa ativação manual de técnicas automáticas (Fase 2e)"
```

---

## Task 9: Cliente — libera ações durante a janela e some o banner

**Files:**
- Modify: `src/gameState.js` (linha ~1016, `isMyTurn`)
- Modify: `game.js` (loop de técnicas do HUD, ~linha 9985-9997 — não renderizar botão clicável p/ técnicas `automatica`)
- Modify: `game.js` (banner de "Último Esforço" — novo bloco perto do indicador de `animados_turn`)

- [ ] **Step 1: Estender `isMyTurn` para aceitar `last_stand_pid`**

Em `src/gameState.js` (linha ~1016), o código atual:

```javascript
        isMyTurn = msg.current_turn === myPid;
```

Trocar por:

```javascript
        isMyTurn = msg.current_turn === myPid || msg.last_stand_pid === myPid;
```

- [ ] **Step 2: Não renderizar botão de uso para técnicas automáticas**

Em `game.js` (linha ~9985-9997), o código atual:

```javascript
  for(const tid of _tecIds){
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if(!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    const podeUsar = GS.isMyTurn && me.alive && state.phase === 'playing'
                     && restante === 0
                     && (me.fome||0) >= (cat.custo_fome||0) && (me.sede||0) >= (cat.custo_sede||0);
```

Trocar por (adiciona `automatica` à condição de habilitar e ajusta a mensagem):

```javascript
  for(const tid of _tecIds){
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if(!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    const podeUsar = !cat.automatica && GS.isMyTurn && me.alive && state.phase === 'playing'
                     && restante === 0
                     && (me.fome||0) >= (cat.custo_fome||0) && (me.sede||0) >= (cat.custo_sede||0);
```

E, no `btn.innerHTML` logo abaixo (mesma seção, linha ~10000-10005), adicionar a
tag "AUTOMÁTICA" quando aplicável — trocar:

```javascript
        <div class="skill-name">${cat.icon||'⚔️'} ${cat.nome} <small style="color:var(--gold);font-size:.58rem;">GUILDA</small>${estado}</div>
```

por:

```javascript
        <div class="skill-name">${cat.icon||'⚔️'} ${cat.nome} <small style="color:var(--gold);font-size:.58rem;">${cat.automatica ? 'AUTOMÁTICA' : 'GUILDA'}</small>${estado}</div>
```

- [ ] **Step 3: Banner de "Último Esforço" no HUD**

Em `game.js`, achar o bloco que já mostra o indicador de turno dos servos (busca
por `animados_turn === GS.myPid`, linha ~1927 ou ~9479 — usar o primeiro que
estiver dentro do template do HUD principal, não do canvas 2D/3D). Adicionar
logo antes (mesmo padrão condicional, só leitura de `state.last_stand_pid`):

```javascript
      ${state.last_stand_pid === GS.myPid ? `
        <div class="banner-ultimo-esforco" style="background:#7a1f1f;color:#fff;padding:.4rem .8rem;border-radius:6px;margin-bottom:.5rem;text-align:center;font-weight:bold;">
          🔥 ÚLTIMO ESFORÇO — ${me.ultimo_esforco_turnos_restantes || 0} turno(s) restante(s)
        </div>
      ` : ''}
```

(Inserir como irmão do bloco de `animados_turn` já existente, dentro do mesmo
template de HUD — não precisa de novo elemento DOM dedicado nem CSS externo, o
estilo inline já é suficiente e consistente com o resto do arquivo, que usa
bastante estilo inline em templates dinâmicos.)

- [ ] **Step 4: Testar manualmente no navegador**

Não há teste automatizado de cliente neste projeto (sem framework de UI). Validar
manualmente: iniciar o servidor (`python server.py`), abrir 2 abas, equipar
Último Esforço num herói via Guilda (requer edit rápido de save ou fluxo normal
de compra), forçar HP a 0 em combate, e observar: (a) banner aparece, (b) o
jogador consegue mover/atacar mesmo não sendo seu "turno" oficial, (c) 2×
"Encerrar Turno" fecha a janela e o herói cai como morto (revivível por
Ressurreição).

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js game.js
git commit -m "feat(guilda): cliente — libera ações e banner do Último Esforço (Fase 2e)"
```

---

## Task 10: Documentação (CLAUDE.md) e regressão final

**Files:**
- Modify: `CLAUDE.md` (novo parágrafo blockquote no fim, seguindo o padrão das Fases 2a-2d)
- Run: suíte completa de testes do projeto

- [ ] **Step 1: Adicionar o parágrafo da Fase 2e ao `CLAUDE.md`**

No fim do arquivo `CLAUDE.md`, logo depois do último parágrafo (o de "Reviver os
Mortos — Fase 1g"), adicionar:

```markdown
> **Técnicas de Recarga Longa (Fase 2e):** 4º lote das Técnicas da Guilda, tier 10
> (preço 350, +6🍖/+6💧, recarga 10 — salvo indicado), completando a faixa que a
> Oportunidade (2d) abriu. **Instinto de Sobrevivência** (automática — dano que
> zeraria o HP vira HP=1, mesmo mecanismo do `regen_ressurge` do Paladino, agora
> genérico) e **Último Esforço** (automática — mesmo gatilho, mas abre uma
> sub-fase de 2 turnos-bônus: vantagem + crítico automático em todo acerto
> [nat20 enquanto ativo → dano TRIPLICADO em vez de dobrado], proibido curar a si
> mesmo, e ao fim cai como morte normal, revivível por Ressurreição) competem
> pelo mesmo gatilho em `_player_dies` mas nunca coexistem equipadas (4º slot).
> A sub-fase do Último Esforço reusa o padrão de "janela pós-turno" já visto em
> animados/prisioneiro: `self.last_stand_pid` + `_is_turn` estendido (aceita
> `current_pid() OU last_stand_pid`) liberam os handlers normais de
> mover/atacar fora da vez oficial; `_abrir_ultimo_esforco` `await`a um
> `asyncio.Event` até o jogador fechar os 2 mini-turnos via `handle_end_turn`
> (interceptado no topo) ou o timer de segurança dedicado
> (`_iniciar_timer_ultimo_esforco`, mesmos 30s do timer normal, mas mirando
> `last_stand_pid`) expirar — como as 17 chamadas a `_player_dies` já são
> `await`adas, isso pausa naturalmente o loop de monstro/turno que a chamou sem
> tocar nesses 17 pontos. **Golpe Decisivo** (manual, buff-and-act — arma o
> próximo ataque básico para crítico automático no acerto) e Último Esforço
> compartilham um único conceito, `_forca_critico`, que generaliza o antigo
> `if crit: dmg *= 2` de `handle_attack` para `dmg *= 3 if (_forca_critico and
> roll == 20) else 2` — um natural 20 sob qualquer uma das duas técnicas
> triplica em vez de dobrar; sem nenhuma delas ativa, o comportamento de sempre
> (nat20 sempre ×2) é idêntico ao de antes. **Sorte** (reativo — o jogador
> escolhe, DEPOIS de ver um erro, se quer gastar a técnica para rerolar aquele
> ataque específico contra o mesmo alvo) é deliberadamente independente do
> Sangue Frio (2c, que arma ANTES de atacar e reroll automático no 1º erro) —
> as duas convivem no catálogo sem se tocar. O reroll da Sorte reaproveita
> `_resolver_dano_ataque_basico`, um helper extraído do bloco de dano de arma/
> desarmado que antes vivia inline em `handle_attack` (dano de arma, `_golpe_raw`,
> bônus de atributo, multiplicador de crítico, modificadores de sobrevivência/
> canção/Guerreiro da Luz) — evita duplicar essa lógica entre o ataque normal e o
> reroll. Também corrigido de passagem: `handle_usar_tecnica` debitava fome/sede
> e ativava a recarga de QUALQUER técnica equipada mesmo sem nenhum `elif` de
> efeito casar — as duas técnicas automáticas (`item.get("automatica")`) agora
> são recusadas explicitamente se alguém tentar ativá-las manualmente. Cliente:
> `isMyTurn` passa a aceitar `last_stand_pid` além de `current_turn` (libera toda
> a UI de ação existente, sem duplicar lógica), e o HUD mostra um banner "🔥
> ÚLTIMO ESFORÇO — X turno(s) restante(s)" enquanto a janela do próprio jogador
> estiver aberta. Teste: `tools/test_tecnicas_espec.py` (seções [23]-[29]).
```

- [ ] **Step 2: Rodar a suíte de técnicas inteira**

Run: `python tools/test_tecnicas_espec.py`
Expected: todas as seções `[1]` a `[29]` com `✅`, 0 `❌`.

- [ ] **Step 3: Rodar as suítes relacionadas (regressão — `_player_dies`/`handle_attack`/`handle_end_turn` são compartilhados por várias classes)**

Run:
```bash
python tools/test_guerreiro_espec.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_ladino_espec.py
python tools/test_bardo_espec.py
python tools/test_mago_espec.py
python tools/test_reviver_mortos.py
python tools/test_guilda.py
python tools/test_ficha_cidade.py
```
Expected: todas com 0 `❌` (nenhuma dessas suítes deveria ser afetada pelas
mudanças desta Fase — servem de regressão para `_player_dies`, `handle_attack`,
`handle_end_turn`, `handle_use_item`, `handle_cura`, `handle_cura_area`, todos
tocados nesta Fase).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(guilda): documenta a Fase 2e (técnicas de recarga longa) no CLAUDE.md"
```

---

## Self-Review (já aplicado ao escrever este plano)

- **Cobertura da spec:** as 4 técnicas (§3-6 da spec), estado novo (§7), testes
  (§8), fronteiras (§9) e riscos (§10, incluindo a auditoria dos 17 call sites —
  coberta implicitamente pela Task 10 Step 3 de regressão, já que qualquer
  call site que dependesse de `p["alive"]==False` logo após `_player_dies`
  quebraria alguma das suítes de regressão) têm task correspondente.
- **Placeholders:** nenhum "TBD"/"implementar depois" — todo passo tem código
  completo (a Task 4 até documenta explicitamente por que a 1ª tentativa de
  código foi descartada e corrigida, em vez de deixar a versão ruim).
- **Consistência de tipos/nomes:** `tem_tecnica_equipada`, `_forca_critico`,
  `_resolver_dano_ataque_basico`, `last_stand_pid`/`last_stand_event`,
  `ultimo_esforco_ativo`/`ultimo_esforco_turnos_restantes`,
  `tecnica_golpe_decisivo_armado`, `ultimo_ataque_perdido` são usados com o
  mesmo nome e assinatura em todas as tasks que os referenciam.
