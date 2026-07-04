# Técnicas de Reação (Guilda Fase 2c) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar 4 Técnicas da Guilda de reação (Ataque Coordenado, Sangue Frio, Resistência Absoluta, Contra-Ataque) que disparam automaticamente em eventos, reusando o padrão do Furtivo Supremo.

**Architecture:** Reações auto-disparam via ganchos nos handlers existentes; um helper compartilhado `_ataque_basico_reativo` faz o ataque fora do turno (aplicando dano direto, sem recursão, como `_furtivo_reativo`). Catálogo por `efeito.tipo` no `handle_usar_tecnica` (2 técnicas exigem alvo).

**Tech Stack:** Python 3 (`server.py`), vanilla JS (`game.js`), harness próprio (`tools/test_tecnicas_espec.py`).

**Spec:** `docs/superpowers/specs/2026-07-03-guilda-fase2c-tecnicas-reacao-design.md`

---

## Arquivos tocados

- **Modify** `server.py`: `GUILD_CATALOG` (4 técnicas); `make_player` (campos); `handle_usar_tecnica` (4 ramos); `_ataque_basico_reativo` + helpers (`_resistencia_saves_bonus`, `_arma_contra_ataque_ok`, `_alvo_no_alcance_arma`); `handle_attack` (Sangue Frio reroll + Ataque Coordenado hook); `_testar_save` (Resistência Absoluta); 2 sites de erro de monstro (Contra-Ataque); reset de fim de turno (`coordenado_alvo`).
- **Modify** `game.js`: seleção de alvo aliado (Ataque Coordenado, sem raio).
- **Modify** `tools/test_tecnicas_espec.py`: novas seções.
- **Modify** `CLAUDE.md`: parágrafo 2c.

> **Fatos verificados (anchors por conteúdo — nº aproximados; RE-VERIFICAR):**
> - `_furtivo_reativo` (server.py ~5397): padrão de reação; dano direto, sem recursão.
> - `handle_attack` hit: `target["hp"] -= dmg` seguido de `await self._furtivo_reativo(p, target)` (~5714-5715).
> - `handle_attack` convergência hit/miss (dentro do ramo monstro): custo de sobrevivência `p["fome"] = max(0, p["fome"] - 1)` (~5767), com `target`/`p` em escopo.
> - `handle_attack` erro do jogador: `hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)` (~5710 do 2b — LOCALIZAR) e o gm_say **ERROU!** (~5752).
> - Erro de ataque de monstro: `return False  # errou` em `_execute_one_monster_attack` (~11734, precedido de gm_say **ERROU!**) com `target`/`is_player`/`m` em escopo; caminho legado com outro gm_say **ERROU!** (~13449).
> - Furtivo do rogue no ataque normal: `if p.get("class_id") == "rogue" and self._verificar_ataque_furtivo(p, target): nd4 = self._dados_furtivo(p.get("level", 1))` (~5707-5708) — reusar `_dados_furtivo`/`_verificar_ataque_furtivo`.
> - `roll_dice(die_str)` (módulo, ~55); `d20_attack(atk, ac)` (módulo, retorna `(hit, roll, total, crit)`); `mod(x)` (módulo, modificador de atributo); `_monster_dies` (LOCALIZAR pelo nome).
> - `WEAPONS`/`RANGED_AMMO` (server.py ~161/197): `hand_crossbow` é ranged (usa munição); chicote/alabarda usam `range:2` mas NÃO estão em `RANGED_AMMO`; lança `reach:lanca`; cajado `reach:cajado`.
> - `_lanca_no_alcance_jogador(pos, target)`, `_cajado_no_alcance_jogador(pos, target)`, `_is_adjacent_to_monster(pos, target)`, `_monster_tiles(m)` — checagens de alcance existentes.

---

### Task 1: Catálogo (4 técnicas)

**Files:** Modify `server.py` (`GUILD_CATALOG`); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [12]** (antes do print final):

```python
    # [12] Catálogo — Reações (2c)
    print("\n[12] Catálogo — Reações")
    for tid, rec, preco, cf in [("tecnica_ataque_coordenado",5,180,4),("tecnica_sangue_frio",5,180,2),
                                ("tecnica_resistencia_absoluta",5,180,4),("tecnica_contra_ataque",8,280,6)]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga {rec}", it and it["recarga_rodadas"] == rec)
        check(f"{tid} preco {preco}", it and it["preco"] == preco)
        check(f"{tid} custo {cf}/{cf}", it and it["custo_fome"] == cf and it["custo_sede"] == cf)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("coordenado exige alvo aliado", S.guild_item("tecnica_ataque_coordenado").get("alvo") == "aliado")
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Adicionar as 4 técnicas ao `GUILD_CATALOG`** (após a última técnica do 2b — Grep `"tecnica_passo_fantasma"`, inserir após seu `},`):

```python
    # ── Técnicas de Reação (Fase 2c) ────────────────────────────────────────
    "tecnica_ataque_coordenado": {
        "id": "tecnica_ataque_coordenado", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Ataque Coordenado", "icon": "🤝", "alvo": "aliado",
        "desc": "Escolha um aliado; neste turno, quando você atacar um inimigo, o aliado também o ataca.",
        "efeito": {"tipo": "ataque_coordenado"},
    },
    "tecnica_sangue_frio": {
        "id": "tecnica_sangue_frio", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 5,
        "nome": "Sangue Frio", "icon": "🧊",
        "desc": "A primeira vez que errar um ataque, você pode rolá-lo novamente.",
        "efeito": {"tipo": "sangue_frio"},
    },
    "tecnica_resistencia_absoluta": {
        "id": "tecnica_resistencia_absoluta", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 180, "custo_fome": 4, "custo_sede": 4, "recarga_rodadas": 5,
        "nome": "Resistência Absoluta", "icon": "🛡️",
        "desc": "Recebe +2 em todos os testes de resistência por 2 rodadas.",
        "efeito": {"tipo": "buff_saves", "saves": 2, "rodadas": 2},
    },
    "tecnica_contra_ataque": {
        "id": "tecnica_contra_ataque", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 280, "custo_fome": 6, "custo_sede": 6, "recarga_rodadas": 8,
        "nome": "Contra-Ataque", "icon": "🗡️",
        "desc": "Até o próximo turno, quando um inimigo errar você (arma corpo a corpo/alcance ou besta de mão, e ele no alcance), você o ataca de volta.",
        "efeito": {"tipo": "contra_ataque"},
    },
```

- [ ] **Step 4: Rodar e ver passar.**
- [ ] **Step 5: Commit** — `git add server.py tools/test_tecnicas_espec.py` / `git commit -m "feat(guilda): catalogo das Tecnicas de Reacao (Fase 2c)"`.

---

### Task 2: Fundação `_ataque_basico_reativo` + campos de estado

**Files:** Modify `server.py` (`make_player`; helper novo); Test `tools/test_tecnicas_espec.py`

- [ ] **Step 1: Test section [13]**

```python
    # [13] _ataque_basico_reativo (fundação)
    print("\n[13] _ataque_basico_reativo")
    r = setup()
    r._monster_dies = lambda *a, **k: None
    async def _mdies(*a, **k): return None
    r._monster_dies = _mdies
    # acerto determinístico via stub de d20_attack (módulo) — melhor stub em _rolar_ataque:
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 18, 20, False, 3)
    atacante = hero("warrior"); atacante["atk_bonus"] = 3
    atacante["weapon"] = {"id":"machado_basico","name":"Machado","die":"1d6","stat":"str_"}
    alvo = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    r.monsters = {"m1": alvo}
    hp0 = alvo["hp"]
    await r._ataque_basico_reativo(atacante, alvo)
    check("reativo: aplica dano no acerto", alvo["hp"] < hp0)
    # erro não aplica dano
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (False, 2, 4, False, 1)
    alvo2 = {"id":"m2","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    hp2 = alvo2["hp"]
    await r._ataque_basico_reativo(atacante, alvo2)
    check("reativo: erro não aplica dano", alvo2["hp"] == hp2)
    # alvo morto é ignorado
    alvo3 = {"id":"m3","name":"Orc","nome":"Orc","pos":[0,1],"hp":0,"max_hp":20,"ac":10,"ca":10}
    r._rolar_ataque = lambda atk, ac, v=False, d=False: (True, 18, 20, False, 3)
    await r._ataque_basico_reativo(atacante, alvo3)
    check("reativo: ignora alvo morto", alvo3["hp"] == 0)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Campos de estado em `make_player`** (junto de `"passo_fantasma_ate": 0,`):
```python
        "coordenado_alvo": None,            # Ataque Coordenado: aliado par (este turno)
        "coordenado_turno": -1,             # turn_index em que o par foi armado
        "sangue_frio_armado": False,        # Sangue Frio: re-rolagem disponível
        "resistencia_saves_ate": 0,         # Resistência Absoluta até esta rodada
        "resistencia_saves_val": 0,
        "contra_ataque_ate": 0,             # Contra-Ataque até esta rodada
```

- [ ] **Step 4: Helper `_ataque_basico_reativo`** (perto de `_furtivo_reativo`):
```python
    async def _ataque_basico_reativo(self, atacante, alvo):
        """Ataque básico disparado por uma reação (fora do turno). Aplica dano
        direto (não chama handle_attack → sem recursão). Furtivo se rogue elegível."""
        if not atacante or not atacante.get("alive") or not alvo or alvo.get("hp", 0) <= 0:
            return
        w = atacante.get("weapon") or {}
        atk = atacante.get("atk_bonus", 0)
        hit, roll, total, crit, _d = self._rolar_ataque(atk, alvo.get("ac", 10), False, False)
        await self.broadcast({"type": "dice_roll", "die": "d20", "value": roll,
                               "label": f"{atacante['name']} — reação", "hit": hit, "crit": crit})
        if not hit:
            await self.gm_say(f"↩️ **{atacante['name']}** reage mas **erra** **{alvo['name']}**.")
            return
        die = w.get("die")
        base = roll_dice(die) if die else 1
        stat = w.get("stat", "str_")
        dmg = max(1, base + mod(atacante.get(stat, 10)))
        if crit: dmg *= 2
        extra = ""
        if atacante.get("class_id") == "rogue" and self._verificar_ataque_furtivo(atacante, alvo):
            nd4 = self._dados_furtivo(atacante.get("level", 1))
            fdano = sum(random.randint(1, 4) for _ in range(nd4))
            dmg += fdano; extra = f" +🗡️{fdano} furtivo [{nd4}d4]"
        alvo["hp"] = max(0, alvo["hp"] - dmg)
        await self.broadcast({"type": "dice_roll", "die": "d" + (die.split("d")[1] if die else "6"),
                               "value": base, "label": "Dano (reação)"})
        await self.gm_say(f"↩️ **{atacante['name']}** reage e atinge **{alvo['name']}**: "
                          f"**{dmg}** de dano{extra}. ({alvo['hp']}/{alvo['max_hp']} HP)")
        if alvo["hp"] <= 0:
            await self._monster_dies(alvo, atacante.get("id"))
```
> **VERIFICADO:** o método de morte é `_monster_dies(monster, killer_pid)` (chamado como `await self._monster_dies(target, pid)` em vários sites). Use `await self._monster_dies(alvo, atacante.get("id"))`.

- [ ] **Step 5: Rodar e ver passar** ([12][13]). Compile OK.
- [ ] **Step 6: Commit** — `git commit -m "feat(guilda): fundacao _ataque_basico_reativo + campos de estado 2c"`.

---

### Task 3: Resistência Absoluta (`buff_saves`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `_testar_save`); Test

- [ ] **Step 1: Test section [14]**
```python
    # [14] Resistência Absoluta
    print("\n[14] Resistência Absoluta")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_resistencia_absoluta"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_resistencia_absoluta")
    check("resist: janela 2 rodadas", p["resistencia_saves_ate"] == r.round_num + 2 and p["resistencia_saves_val"] == 2)
    check("resist: helper = 2 na janela", r._resistencia_saves_bonus(p) == 2)
    _, _d, sb_no, _t = r._testar_save({"pos":[0,0]}, "fortitude", 99)
    _, _d2, sb_yes, _t2 = r._testar_save(p, "fortitude", 99)
    check("resist: _testar_save soma +2", sb_yes - sb_no == 2)
    r.round_num += 3
    check("resist: expira", r._resistencia_saves_bonus(p) == 0)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Helper + ramo + `_testar_save`**
Helper:
```python
    def _resistencia_saves_bonus(self, p):
        return p.get("resistencia_saves_val", 0) if p.get("resistencia_saves_ate", 0) >= self.round_num else 0
```
Ramo no dispatch (após os do 2b):
```python
        elif ef.get("tipo") == "buff_saves":
            p["resistencia_saves_ate"] = self.round_num + ef.get("rodadas", 2)
            p["resistencia_saves_val"] = ef.get("saves", 2)
```
Em `_testar_save`, somar o bônus (é o mesmo método que já recebe `fonte=None` da Fase 1e; adicionar o termo):
```python
        bonus = (self._veneno_save_bonus(alvo, tipo_save) + self._mod_magia(alvo, "resistencia")
                 + extra_mod + self._lenda_resist_bonus(alvo, fonte)
                 + self._resistencia_saves_bonus(alvo))
```
(Localize a linha de `bonus =` em `_testar_save` e adicione só o `+ self._resistencia_saves_bonus(alvo)`.)

- [ ] **Step 4: Rodar e ver passar** ([12]-[14]). Regressão: `python tools/test_bardo_espec.py` (78/0 — `_testar_save`/Lendas intactos), `python tools/test_ogro.py` (24/0).
- [ ] **Step 5: Commit** — `git commit -m "feat(guilda): Tecnica Resistencia Absoluta (+2 saves 2 rodadas)"`.

---

### Task 4: Sangue Frio (`sangue_frio`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `handle_attack` reroll); Test

- [ ] **Step 1: Test section [15]** (verifica a lógica de re-rolagem via um helper puro)
```python
    # [15] Sangue Frio
    print("\n[15] Sangue Frio")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_sangue_frio"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_sangue_frio")
    check("sangue frio: armado", p.get("sangue_frio_armado") is True)
    # o consumo/reroll é exercitado via _sangue_frio_consumir
    check("sangue frio: consome e retorna True quando armado", r._sangue_frio_consumir(p) is True)
    check("sangue frio: desarmado após consumir", p.get("sangue_frio_armado") is False)
    check("sangue frio: sem re-roll se desarmado", r._sangue_frio_consumir(p) is False)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Helper + ramo + hook em handle_attack**
Helper:
```python
    def _sangue_frio_consumir(self, p):
        """Consome a re-rolagem do Sangue Frio se armada. Retorna True se deve re-rolar."""
        if p.get("sangue_frio_armado"):
            p["sangue_frio_armado"] = False
            return True
        return False
```
Ramo no dispatch:
```python
        elif ef.get("tipo") == "sangue_frio":
            p["sangue_frio_armado"] = True
```
Hook em `handle_attack`: logo após o `hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)` (o do ramo de alvo-monstro), adicionar a re-rolagem no erro:
```python
            hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
            if not hit and self._sangue_frio_consumir(p):
                await self.gm_say(f"🧊 **{p['name']}** mantém o sangue frio e rola novamente!")
                hit, roll, total, crit, _desc = self._rolar_ataque(eff_atk, eff_target_ac, vantagem, desvantagem)
```
(Se já houver as linhas do 2b — `_mira_ranged`/`_investida` limpando flags logo abaixo — insira a re-rolagem ANTES dessas limpezas, para que o novo `hit` seja o usado. Localize a linha do `_rolar_ataque` por conteúdo.)

- [ ] **Step 4: Rodar e ver passar** ([12]-[15]). `python tools/test_guilda.py`, `python tools/test_bardo_espec.py`, `python tools/test_ladino_espec.py` verdes.
- [ ] **Step 5: Commit** — `git commit -m "feat(guilda): Tecnica Sangue Frio (re-rola o 1o erro)"`.

---

### Task 5: Ataque Coordenado (`ataque_coordenado`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; `handle_attack` hook; reset fim de turno); Test

- [ ] **Step 1: Test section [16]**
```python
    # [16] Ataque Coordenado
    print("\n[16] Ataque Coordenado")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1; r.turn_index = 0
    r._alvo_no_alcance_arma = lambda p_, t_: True
    p = hero("warrior", "tecnica_ataque_coordenado"); p["pos"] = [0,0]; r.players["h"] = p
    ally = make_player("a","Ana","warrior",1); ally["alive"]=True; ally["pos"]=[1,0]
    ally["atk_bonus"]=3; ally["weapon"]={"id":"machado_basico","die":"1d6","stat":"str_"}; r.players["a"]=ally
    await r.handle_usar_tecnica("h", "tecnica_ataque_coordenado", "a")
    check("coord: par gravado", p["coordenado_alvo"] == "a" and p["coordenado_turno"] == r.turn_index)
    # dispara o ataque do par no alvo do usuário
    alvo = {"id":"m1","name":"Orc","nome":"Orc","pos":[0,1],"hp":20,"max_hp":20,"ac":10,"ca":10}
    r.monsters = {"m1": alvo}; r._rolar_ataque = lambda a,b,v=False,d=False:(True,18,20,False,3)
    async def _mdies(*a,**k): return None
    r._monster_dies = _mdies
    hp0 = alvo["hp"]
    await r._reacao_ataque_coordenado(p, alvo)
    check("coord: par atacou o alvo", alvo["hp"] < hp0)
    check("coord: consumiu no turno", p["coordenado_alvo"] is None)
    # aliado fora do raio não vira par
    r2 = setup(); r2.current_pid = lambda: "h"; r2.round_num = 1
    p2 = hero("warrior","tecnica_ataque_coordenado"); r2.players["h"]=p2
    await r2.handle_usar_tecnica("h","tecnica_ataque_coordenado", None)
    check("coord: recusa sem aliado", p2.get("coordenado_alvo") is None)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Ramo (valida aliado) + helper de reação**
Ramo no dispatch:
```python
        elif ef.get("tipo") == "ataque_coordenado":
            alvo = self.players.get(target_id) if target_id else None
            if not alvo or not alvo.get("alive") or alvo["id"] == pid:
                await self.send_to(pid, {"type": "error", "msg": "Escolha um aliado vivo."}); return
            p["coordenado_alvo"] = alvo["id"]
            p["coordenado_turno"] = self.turn_index
```
Helper de reação (perto de `_furtivo_reativo`):
```python
    async def _reacao_ataque_coordenado(self, atacante, alvo_monstro):
        """Ataque Coordenado: o aliado par faz um ataque básico reativo no mesmo
        inimigo (1x no turno), se estiver no alcance da própria arma."""
        if atacante.get("coordenado_turno") != self.turn_index:
            return
        par_id = atacante.get("coordenado_alvo")
        atacante["coordenado_alvo"] = None   # consome (1x/turno), mesmo se não alcançar
        par = self.players.get(par_id) if par_id else None
        if not par or not par.get("alive") or not alvo_monstro or alvo_monstro.get("hp", 0) <= 0:
            return
        if not self._alvo_no_alcance_arma(par, alvo_monstro):
            return
        await self._ataque_basico_reativo(par, alvo_monstro)
```

- [ ] **Step 4: Hook em `handle_attack`** — após o custo de sobrevivência do ataque (`p["fome"] = max(0, p["fome"] - 1)`, ~5767), com `target` (monstro) ainda em escopo, adicionar:
```python
        p["fome"] = max(0, p["fome"] - 1)
        await self._reacao_ataque_coordenado(p, target)
```
(`_ataque_basico_reativo` já ignora alvo morto; dispara em acerto/erro do ataque principal, "ao atacar".)

- [ ] **Step 5: Limpar no fim de turno** — junto de `p["investida_armada"] = False` no reset, adicionar `p["coordenado_alvo"] = None`.

- [ ] **Step 6: Rodar e ver passar** ([12]-[16]). Regressões verdes.
- [ ] **Step 7: Commit** — `git commit -m "feat(guilda): Tecnica Ataque Coordenado (ataque reativo do par)"`.

---

### Task 6: Contra-Ataque (`contra_ataque`)

**Files:** Modify `server.py` (`handle_usar_tecnica`; helpers de arma/alcance; 2 sites de erro de monstro); Test

- [ ] **Step 1: Test section [17]**
```python
    # [17] Contra-Ataque
    print("\n[17] Contra-Ataque")
    r = setup(); r.current_pid = lambda: "h"; r.round_num = 1
    p = hero("warrior", "tecnica_contra_ataque"); r.players["h"] = p
    await r.handle_usar_tecnica("h", "tecnica_contra_ataque")
    check("contra: janela até próximo turno", p["contra_ataque_ate"] == r.round_num + 1)
    # elegibilidade de arma
    def _w(wid, extra=None):
        pp = hero("warrior"); pp["weapon"] = {"id": wid, **(extra or {})}; return pp
    check("contra: machado (melee) elegível", r._arma_contra_ataque_ok(_w("machado_basico")) is True)
    check("contra: lança elegível", r._arma_contra_ataque_ok(_w("lanca", {"reach":"lanca"})) is True)
    check("contra: chicote elegível", r._arma_contra_ataque_ok(_w("chicote", {"range":2})) is True)
    check("contra: besta de mão elegível", r._arma_contra_ataque_ok(_w("hand_crossbow", {"range":4})) is True)
    check("contra: arco NÃO elegível", r._arma_contra_ataque_ok(_w("arco_curto", {"range":8})) is False)
    check("contra: besta pesada NÃO elegível", r._arma_contra_ataque_ok(_w("besta", {"range":10})) is False)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Ramo + helpers de arma/alcance**
Ramo no dispatch:
```python
        elif ef.get("tipo") == "contra_ataque":
            p["contra_ataque_ate"] = self.round_num + 1
```
Helpers:
```python
    def _arma_contra_ataque_ok(self, p):
        """Contra-Ataque só com arma corpo a corpo / alcance (lança, chicote, alabarda)
        ou a Besta de Mão. Exclui arcos e a besta pesada (as demais em RANGED_AMMO)."""
        wid = (p.get("weapon") or {}).get("id")
        if wid == "hand_crossbow":
            return True
        return wid not in RANGED_AMMO

    def _alvo_no_alcance_arma(self, p, target):
        """True se `target` (monstro) está no alcance real da arma de `p`."""
        w = p.get("weapon") or {}
        wr = w.get("range")
        if wr is not None:
            body = self._monster_tiles(target)
            return any(max(abs(p["pos"][0]-t[0]), abs(p["pos"][1]-t[1])) <= wr for t in body)
        if w.get("reach") == "lanca":
            return self._lanca_no_alcance_jogador(p["pos"], target)
        if w.get("reach") == "cajado":
            return self._cajado_no_alcance_jogador(p["pos"], target)
        return self._is_adjacent_to_monster(p["pos"], target)
```

- [ ] **Step 4: Hook nos 2 sites de ERRO de ataque de monstro**
Em `_execute_one_monster_attack`, imediatamente antes de `return False  # errou` (após o gm_say **ERROU!**, ~11733), inserir:
```python
            if is_player and target.get("contra_ataque_ate", 0) >= self.round_num \
               and self._arma_contra_ataque_ok(target) and self._alvo_no_alcance_arma(target, m):
                await self._ataque_basico_reativo(target, m)
            return False  # errou
```
No caminho legado (o outro gm_say **ERROU!**, ~13449), inserir o MESMO bloco antes do seu final de ramo (ajuste a indentação; confirme que `target`/`is_player`/`m` estão em escopo naquele site — se a var do jogador tiver outro nome, use-a).

- [ ] **Step 5: Rodar e ver passar** ([12]-[17]). Regressões: `python tools/test_ogro.py` (24/0), `python tools/test_devorador.py` (165/0 — ataques de monstro intactos; d100 flaky conhecido).
- [ ] **Step 6: Commit** — `git commit -m "feat(guilda): Tecnica Contra-Ataque (ataque reativo ao erro do monstro)"`.

---

### Task 7: Cliente — seleção de aliado (Ataque Coordenado)

**Files:** Modify `game.js` (handler do botão do 4º slot — onde o 2b tratou `alvo`)

- [ ] **Step 1:** No handler do 4º slot (`btn.onclick`, onde o 2b trata `cat.alvo === 'monstro_adjacente'`/`'aliado_raio4'`), adicionar o caso `aliado` (sem raio):
```javascript
      } else if(cat.alvo === 'aliado'){
        const alvos = (state.players||[]).filter(q => q && q.alive && q.id !== me.id);
        if(!alvos.length){ toast('Nenhum aliado vivo.', 'var(--orange)'); return; }
        if(alvos.length === 1){ GS.usarTecnica(tid, alvos[0].id); return; }
        openTargetModal(`${cat.icon||'⚔️'} ${cat.nome} — aliado`, alvos, 'player',
          id => GS.usarTecnica(tid, id));
      } else {
```
(Insira o `else if` ANTES do `else { GS.usarTecnica(tid); }` final; mantenha os casos `monstro_adjacente`/`aliado_raio4` do 2b.)

- [ ] **Step 2:** `node --check game.js`.
- [ ] **Step 3: Commit** — `git commit -m "feat(guilda): cliente pede aliado p/ Ataque Coordenado"`.

---

### Task 8: Verificação E2E (smoke) + docs

**Files:** Modify `CLAUDE.md`; Test via preview + suíte

- [ ] **Step 1: Suíte verde** — `python tools/test_tecnicas_espec.py` (PASS FAIL=0); regressões `test_guilda.py`/`test_bardo_espec.py`/`test_ladino_espec.py`/`test_ogro.py`/`test_devorador.py` verdes.
- [ ] **Step 2: Smoke E2E** — Bump `CLASSES["warrior"]["start_gold"]`→2000; `preview_start` "game"; abrir a Guilda e confirmar as 4 reações nas faixas Recarga Média/Longa; console sem erros. Reverter `start_gold`; `rm -rf saves/`; reverter `editor_dungeons.js` se o servidor regenerar.
- [ ] **Step 3: Documentar na CLAUDE.md** — após o parágrafo do 2b, adicionar:
```markdown
> **Técnicas de Reação (Fase 2c):** 4 reações auto-disparadas (padrão do Furtivo
> Supremo). Fundação `_ataque_basico_reativo(atacante, alvo)` — ataque fora do turno,
> dano direto sem recursão; +Furtivo se o atacante for o Ladino
> (`_verificar_ataque_furtivo`). **Ataque Coordenado** (`ataque_coordenado` — alvo
> aliado; hook em `handle_attack` faz o par atacar o mesmo inimigo 1x/turno se no
> alcance; `_reacao_ataque_coordenado`), **Sangue Frio** (`sangue_frio` — re-rola o 1º
> erro via `_sangue_frio_consumir` no `handle_attack`), **Resistência Absoluta**
> (`buff_saves` — +2 em todos os saves 2 rodadas, `_resistencia_saves_bonus` no
> `_testar_save`), **Contra-Ataque** (`contra_ataque` — nos 2 sites de erro de ataque
> de monstro, o jogador ataca de volta se `_arma_contra_ataque_ok` [melee/alcance ou
> besta de mão] e `_alvo_no_alcance_arma`). Oportunidade (ordem de turno) fica p/
> mini-lote. Teste: `tools/test_tecnicas_espec.py`.
```
- [ ] **Step 4: Commit final** — `git add CLAUDE.md server.py` / `git commit -m "docs(guilda): documentar Tecnicas de Reacao (Fase 2c)"`.

---

## Auto-revisão (checklist do autor do plano)

- **Cobertura do spec:** catálogo → T1; fundação → T2; Resistência Absoluta → T3; Sangue Frio → T4; Ataque Coordenado → T5; Contra-Ataque → T6; cliente → T7; E2E+docs → T8. ✔
- **Sem placeholders:** código real em cada passo; pontos guiados por conteúdo (hooks de combate T4/T5/T6, `_monster_dies` T2) sinalizados p/ RE-VERIFICAR anchors — lição das fases anteriores. ✔
- **Consistência de nomes:** `efeito.tipo` ∈ {`ataque_coordenado`,`sangue_frio`,`buff_saves`,`contra_ataque`}; helpers `_ataque_basico_reativo`/`_reacao_ataque_coordenado`/`_sangue_frio_consumir`/`_resistencia_saves_bonus`/`_arma_contra_ataque_ok`/`_alvo_no_alcance_arma`; campos `coordenado_alvo`/`coordenado_turno`/`sangue_frio_armado`/`resistencia_saves_ate`/`resistencia_saves_val`/`contra_ataque_ate` — idênticos entre tasks. ✔
- **Risco (recursão):** `_ataque_basico_reativo` aplica dano direto (não chama `handle_attack`); T2 destaca. ✔
- **Risco (`_monster_dies`):** T2 pede confirmar o nome/assinatura do método de morte por Grep antes de usar. ✔
