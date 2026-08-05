# Ficha do Monstro para o Mestre — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar a ficha do monstro do Modo Mestre numa ficha de comando completa — ataques granulares, todas as habilidades ativáveis, economia de ação real e relógio visível — numa caixa única com três abas.

**Architecture:** O servidor continua autoritativo. Adicionam-se cargas de ataque por índice, um mapa de custo derivado do `action_type` da ficha, três extrações de código hoje embutido na IA (compartilhadas entre IA e mestre) e um relógio de inatividade. O cliente funde `#hud-mestre` e `#ficha-monstro` numa caixa com abas alimentada por um bloco novo `master_manual` do `game_state`.

**Tech Stack:** Python 3 + `websockets` (server.py, arquivo único). Cliente vanilla JS sem bundler (game.js, game.css, src/gameState.js). Testes: `python tools/test_modo_mestre.py` (harness próprio, sem pytest).

**Spec:** `docs/superpowers/specs/2026-08-04-ficha-monstro-mestre-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta mudança |
|---|---|
| `server.py` | Cargas de ataque, custo por `action_type`, gate de habilidades, 3 extrações, relógio, payload |
| `src/gameState.js` | Novos action senders e getters do painel do mestre |
| `game.js` | `renderMasterPanel` (funde `renderMasterHud` + `renderFichaMonstro`), mira de golpe |
| `game.css` | Estilos da caixa com abas |
| `tools/test_modo_mestre.py` | Seções `[30]`–`[34]` |

Não há arquivo novo: `server.py` e `game.js` são grandes por convenção do projeto, e o código desta mudança pertence às regiões já existentes do Modo Mestre.

---

## Invariante que todas as tasks preservam

**Sem mestre conectado, ou com o monstro em `control_mode == "auto"`, o comportamento tem de ser byte-idêntico ao de hoje.** As três extrações existem para que IA e mestre compartilhem o mesmo código, e não para que a IA passe a se comportar diferente. A Task 8 testa isso explicitamente.

---

## Task 1: Custo de ação por `action_type`

**Files:**
- Modify: `server.py` (adicionar perto de `_habilidade_ativavel_manual`, linha ~20778)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `tools/test_modo_mestre.py`, imediatamente antes da linha `print(f"\n=== {PASS} passaram, {FAIL} falharam ===")`:

```python
    print("\n[30] _custo_acao_ability — traduz action_type em custo")
    r = playing_room_com_mestre()
    check("acao → principal",      r._custo_acao_ability({"action_type": "acao"}) == "principal")
    check("magia → principal",     r._custo_acao_ability({"action_type": "magia"}) == "principal")
    check("ataque → principal",    r._custo_acao_ability({"action_type": "ataque"}) == "principal")
    check("acao_bonus → bonus",    r._custo_acao_ability({"action_type": "acao_bonus"}) == "bonus")
    check("acao_livre → livre",    r._custo_acao_ability({"action_type": "acao_livre"}) == "livre")
    check("desconhecido → principal", r._custo_acao_ability({"action_type": "xyz"}) == "principal")
    check("sem action_type → principal", r._custo_acao_ability({}) == "principal")
    check("None → principal",      r._custo_acao_ability(None) == "principal")
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA com `AttributeError: 'GameRoom' object has no attribute '_custo_acao_ability'`

- [ ] **Step 3: Implementar**

Em `server.py`, logo **antes** de `def _habilidade_ativavel_manual(self, ability):`:

```python
    # Custo de ação de uma habilidade, derivado do action_type da própria ficha.
    # "principal" é o default seguro: uma habilidade sem classificação nunca sai
    # de graça.
    _CUSTO_POR_ACTION_TYPE = {
        "acao":       "principal",
        "magia":      "principal",
        "ataque":     "principal",
        "acao_bonus": "bonus",
        "acao_livre": "livre",
    }

    def _custo_acao_ability(self, ability):
        """'principal' | 'bonus' | 'livre' — o que esta habilidade consome."""
        at = (ability or {}).get("action_type")
        return self._CUSTO_POR_ACTION_TYPE.get(at, "principal")
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: as 8 checagens da seção `[30]` em verde; nenhuma falha nova nas anteriores.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): custo de acao derivado do action_type da ficha"
```

---

## Task 2: Cargas de ataque na abertura da janela Manual

**Files:**
- Modify: `server.py:12129-12151` (`_master_manual_window`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `tools/test_modo_mestre.py`, antes da linha do total:

```python
    print("\n[31] cargas de ataque montadas na abertura da janela")
    r = playing_room_com_mestre()
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [1, 1],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Garras", "atk_bonus": 5, "damage": "1d4", "num_attacks": 2},
                     {"name": "Mordida", "atk_bonus": 4, "damage": "1d6", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("cargas por índice", m["master_attack_charges"] == {0: 2, 1: 1})
    check("tipo de ação zerado", m.get("_master_acao_tipo") is None)
    r.master_manual_event.set()
    await task

    print("\n[31b] monstro legado (sem attacks[]) ganha 1 carga")
    r = playing_room_com_mestre()
    m2 = {"id": "g2", "name": "Goblin", "hp": 6, "max_hp": 6, "pos": [1, 1],
          "size": [1, 1], "movement": 4, "control_mode": "manual",
          "atk_bonus": 2, "damage": "1d6"}
    r.monsters = {"g2": m2}
    task = asyncio.create_task(r._master_manual_window(m2))
    await asyncio.sleep(0)
    check("legado tem 1 carga no índice 0", m2["master_attack_charges"] == {0: 1})
    r.master_manual_event.set()
    await task
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA em "cargas por índice" — `master_attack_charges` não existe.

- [ ] **Step 3: Implementar**

Em `server.py`, dentro de `_master_manual_window`, **após** a linha `m["_master_bonus_acted"] = False` (linha ~12141), inserir:

```python
        m["_master_acao_tipo"] = None
        m["master_attack_charges"] = self._montar_cargas_ataque(m)
        m.pop("_master_touched", None)
```

E adicionar o helper logo **antes** de `async def _master_manual_window(self, m):`:

```python
    def _montar_cargas_ataque(self, m):
        """{índice de attacks[]: num_attacks} — as rolagens disponíveis no turno.
        Espelha o que _monster_execute_attacks faz de uma vez na IA. Monstro de
        ficha legada (sem attacks[]) recebe uma única carga no índice 0."""
        ataques = m.get("attacks") or []
        if not ataques:
            return {0: 1}
        return {i: max(1, int(a.get("num_attacks", 1) or 1))
                for i, a in enumerate(ataques)}
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: seções `[31]` e `[31b]` em verde.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): cargas de ataque por num_attacks na janela Manual"
```

---

## Task 3: `attack_index` e gasto de cargas no ataque

**Files:**
- Modify: `server.py:12044-12071` (`handle_mestre_atacar_monstro`)
- Modify: `server.py:24388` (dispatch de `mestre_atacar_monstro`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao fim de `tools/test_modo_mestre.py`:

```python
    print("\n[32] ataques granulares — cargas, alvos distintos, recusa da 4ª")
    r = playing_room_com_mestre()
    golpes = []
    async def fake_atk(mm, atk_def, target_obj):
        golpes.append((atk_def.get("name"), target_obj["obj"]["id"])); return True
    r._execute_one_monster_attack = fake_atk
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [2, 2],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "_master_acted": False, "_master_bonus_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 2, 1: 1},
         "attacks": [{"name": "Garras", "num_attacks": 2},
                     {"name": "Mordida", "num_attacks": 1}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True},
                 "hB": {"id": "hB", "name": "Bea", "pos": [3, 2], "alive": True}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("1ª garra saiu", golpes == [("Garras", "hA")])
    check("carga 0 debitada", m["master_attack_charges"][0] == 1)
    check("ação comprometida com ataque", m["_master_acao_tipo"] == "ataque")
    check("ação principal marcada", m["_master_acted"] is True)
    await r.handle_mestre_atacar_monstro("m1", "g1", "hB", 0)
    check("2ª garra em outro herói", golpes[-1] == ("Garras", "hB"))
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 1)
    check("mordida saiu", golpes[-1] == ("Mordida", "hA"))
    check("todas as cargas gastas", m["master_attack_charges"] == {0: 0, 1: 0})
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("4ª tentativa recusada", len(golpes) == 3)
    check("erro explica as cargas", any("golpe" in e.lower() for e in r._errs))

    print("\n[32b] attack_index ausente = índice 0 (cliente antigo)")
    r = playing_room_com_mestre()
    golpes2 = []
    async def fake_atk2(mm, atk_def, target_obj):
        golpes2.append(atk_def.get("name")); return True
    r._execute_one_monster_attack = fake_atk2
    m = {"id": "g1", "name": "Orc", "hp": 12, "max_hp": 12, "pos": [2, 2],
         "size": [1, 1], "control_mode": "manual",
         "_master_acted": False, "_master_acao_tipo": None,
         "master_attack_charges": {0: 1},
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA")
    check("sem attack_index usa o 0", golpes2 == ["Machado"])
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA — `handle_mestre_atacar_monstro() takes 4 positional arguments but 5 were given`.

- [ ] **Step 3: Implementar**

Substituir `handle_mestre_atacar_monstro` inteiro (server.py:12044-12071) por:

```python
    async def handle_mestre_atacar_monstro(self, pid, monster_id, target_id, attack_index=None):
        """Manual: o monstro da janela desfere UM golpe do índice pedido.
        As cargas vêm de num_attacks (master_attack_charges) e podem ser
        distribuídas entre alvos diferentes — mesmo total que a IA rola em
        _monster_execute_attacks. Todos os golpes pertencem à mesma ação
        principal: comprometê-la com ataques bloqueia habilidades de ação, e
        vice-versa."""
        if pid != self.master_pid or monster_id != self.master_manual_mid:
            return
        m = self.monsters.get(monster_id)
        if not m or m["hp"] <= 0:
            return
        if m.get("_master_acted") and m.get("_master_acao_tipo") != "ataque":
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação principal."}); return
        try:
            idx = 0 if attack_index is None else int(attack_index)
        except (TypeError, ValueError):
            idx = 0
        cargas = m.setdefault("master_attack_charges", self._montar_cargas_ataque(m))
        if cargas.get(idx, 0) <= 0:
            await self.send_to(pid, {"type": "error", "msg": "Este golpe não tem mais cargas neste turno."}); return
        ataques = m.get("attacks") or []
        base = ataques[idx] if 0 <= idx < len(ataques) else {}
        atk_def = dict(base)
        if m.get("veneno_arma_ativo"):
            atk_def["on_hit"] = m.get("veneno_arma_id")
        alvo = self.players.get(target_id)
        if not alvo or not alvo.get("alive"):
            await self.send_to(pid, {"type": "error", "msg": "Alvo inválido."}); return
        rng = atk_def.get("range")
        if rng:
            if max(abs(m["pos"][0] - alvo["pos"][0]), abs(m["pos"][1] - alvo["pos"][1])) > rng:
                await self.send_to(pid, {"type": "error", "msg": "Alvo fora de alcance."}); return
        elif not self._is_adjacent_to_monster(alvo["pos"], m):
            await self.send_to(pid, {"type": "error", "msg": "Alvo não está adjacente."}); return
        cargas[idx] = cargas.get(idx, 0) - 1
        m["_master_acted"] = True
        m["_master_acao_tipo"] = "ataque"
        m["_ja_executou_acao"] = True
        m["_master_touched"] = True
        hit = await self._execute_one_monster_attack(m, atk_def, {"kind": "player", "obj": alvo})
        m.pop("_golpe_brutal_ativo", None)   # Golpe Brutal vale para um golpe só
        if hit and m.get("veneno_arma_ativo"):
            m["veneno_arma_ativo"] = False
            m.pop("equipment_poison", None)
        self._reiniciar_timer_manual()
        await self.push_state()
```

> `_reiniciar_timer_manual` só existe a partir da Task 9. Até lá, ele **não**
> deve ser chamado. Adicione um stub agora, junto ao helper da Task 2, para o
> código rodar; a Task 9 substitui o corpo:
>
> ```python
>     def _reiniciar_timer_manual(self):
>         """Stub — implementado na Task 9 (relógio de inatividade)."""
>         return
> ```

E no dispatch (server.py:24388), trocar:

```python
                    if room: await room.handle_mestre_atacar_monstro(pid, msg.get("monster_id"), msg.get("target_id"))
```

por:

```python
                    if room: await room.handle_mestre_atacar_monstro(pid, msg.get("monster_id"), msg.get("target_id"), msg.get("attack_index"))
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: seções `[32]` e `[32b]` em verde. As seções `[26]`–`[29]` continuam verdes: `_master_acted` manteve o nome e o significado.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): ataque granular por attack_index com cargas de num_attacks"
```

---

## Task 4: Economia de ação nas habilidades e itens

**Files:**
- Modify: `server.py:20840-20901` (`handle_mestre_usar_habilidade`)
- Modify: `server.py:20524-20622` (`handle_mestre_usar_item`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[33] economia por action_type — bônus e livre não gastam a principal")
    r = playing_room_com_mestre()
    async def fake_use(mm, ability, target_obj): return True
    r._use_monster_ability = fake_use
    ab_bonus = {"id": "grito", "name": "Grito", "action_type": "acao_bonus", "save": "vontade", "dc": 10}
    ab_livre = {"id": "farejar", "name": "Farejar", "action_type": "acao_livre", "save": "fort", "dc": 10}
    ab_acao  = {"id": "petrificar", "name": "Petrificar", "action_type": "acao", "save": "fort", "dc": 13}
    m = {"id": "g1", "name": "Coisa", "hp": 20, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "garra", "num_attacks": 1}],
         "master_attack_charges": {0: 1},
         "special_abilities": [ab_bonus, ab_livre, ab_acao]}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    await r.handle_mestre_usar_habilidade("m1", "g1", "farejar", "hA")
    check("acao_livre não gasta nada", m["_master_acted"] is False and m["_master_bonus_acted"] is False)
    await r.handle_mestre_usar_habilidade("m1", "g1", "grito", "hA")
    check("acao_bonus gasta só a bônus", m["_master_bonus_acted"] is True and m["_master_acted"] is False)
    r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "grito", "hA")
    check("2ª bônus recusada", any("bônus" in e.lower() or "bonus" in e.lower() for e in r._errs))
    await r.handle_mestre_usar_habilidade("m1", "g1", "petrificar", "hA")
    check("acao gasta a principal", m["_master_acted"] is True)
    check("tipo registrado", m["_master_acao_tipo"] == "habilidade")

    print("\n[33b] atacar depois de habilidade de ação é recusado")
    r._errs.clear()
    golpes = []
    async def fake_atk(mm, atk_def, target_obj): golpes.append(1); return True
    r._execute_one_monster_attack = fake_atk
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("ataque após magia recusado", golpes == [])
    check("carga preservada", m["master_attack_charges"][0] == 1)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA em "acao_livre não gasta nada" — hoje qualquer habilidade marca `_master_acted`.

- [ ] **Step 3: Implementar**

Em `handle_mestre_usar_habilidade`, substituir a guarda de entrada (linhas 20849-20850):

```python
        if m.get("_master_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já agiu neste turno."}); return
        ability = next((a for a in m.get("special_abilities", []) if a.get("id") == ability_id), None)
        if not self._habilidade_ativavel_manual(ability):
            await self.send_to(pid, {"type": "error", "msg": "Habilidade não ativável manualmente (IA apenas)."}); return
```

por:

```python
        ability = next((a for a in m.get("special_abilities", []) if a.get("id") == ability_id), None)
        if not self._habilidade_ativavel_manual(ability):
            await self.send_to(pid, {"type": "error", "msg": "Habilidade não ativável manualmente (IA apenas)."}); return
        custo = self._custo_acao_ability(ability)
        if custo == "principal" and m.get("_master_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação principal."}); return
        if custo == "bonus" and m.get("_master_bonus_acted"):
            await self.send_to(pid, {"type": "error", "msg": "Este monstro já usou a ação bônus."}); return
```

Em seguida, trocar **todas** as cinco ocorrências de `m["_master_acted"] = True` dentro deste handler (linhas 20859, 20869, 20877, 20882 e 20899) por uma chamada ao helper novo:

```python
        self._debitar_acao_mestre(m, custo, "habilidade")
```

Ou seja, onde hoje se lê `m["_master_acted"] = True` (sozinho ou seguido de `m["_ja_executou_acao"] = True`), passa a ler:

```python
            self._debitar_acao_mestre(m, custo, "habilidade")
            m["_ja_executou_acao"] = True
```

(mantendo `_ja_executou_acao` exatamente onde ele já era setado — não adicione onde não havia).

Adicionar o helper logo após `_custo_acao_ability`:

```python
    def _debitar_acao_mestre(self, m, custo, tipo):
        """Debita o custo de uma ação do mestre e registra em que ela foi gasta.
        'livre' não debita nada. Marca _master_touched, que o relógio e o
        timeout usam para saber que o mestre realmente agiu neste turno."""
        m["_master_touched"] = True
        if custo == "principal":
            m["_master_acted"] = True
            m["_master_acao_tipo"] = tipo
        elif custo == "bonus":
            m["_master_bonus_acted"] = True
        self._reiniciar_timer_manual()
```

Em `handle_mestre_usar_item`, trocar as três atribuições diretas por chamadas ao helper:

- linha 20556-20557 (`throwable`): `m["_master_acted"] = True` / `m["_ja_executou_acao"] = True` → `self._debitar_acao_mestre(m, "principal", "item")` seguido de `m["_ja_executou_acao"] = True`
- linha 20573-20574 (`scroll`): idem
- linha 20618-20619 (`if not veneno_livre: m["_master_bonus_acted"] = True`) → `if not veneno_livre: self._debitar_acao_mestre(m, "bonus", "item")`

E as duas guardas de `throwable`/`scroll` (linhas 20543 e 20564) passam a mensagem já correta — nenhuma mudança necessária nelas.

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[33]` e `[33b]` em verde; `[26]`, `[26b]`, `[27]`, `[28]` continuam verdes (as habilidades daqueles testes são `action_type: "acao"`, que custa a principal — comportamento idêntico).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): economia de acao respeita o action_type da ficha"
```

---

## Task 5: Extrair `_lancar_magia_monstro` e liberar magias ao mestre

**Files:**
- Modify: `server.py:22088-22139` (`_monster_try_spell`)
- Modify: `server.py:20778-20790` (`_habilidade_ativavel_manual`)
- Modify: `server.py:20840+` (`handle_mestre_usar_habilidade` — ramo novo)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[34] magias do mestre — lança, debita usos, respeita recarga")
    r = playing_room_com_mestre()
    lancadas = []
    async def fake_grim(mm, magia, data, *a, **k):
        lancadas.append((magia["id"], data.get("target_id")))
    r._executar_magia_grimorio = fake_grim
    ab_magia = {"id": "silencio", "name": "Silêncio", "action_type": "magia"}
    m = {"id": "g1", "name": "Xamã", "hp": 14, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "cajado", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_magia],
         "monster_spells": [{"id": "silencio", "limit_mode": "encounter", "uses_per_combat": 1}],
         "spell_uses": {"silencio": 1}, "spell_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("predicado aceita magia implementada", r._habilidade_ativavel_manual(ab_magia) is True)
    await r.handle_mestre_usar_habilidade("m1", "g1", "silencio", "hA")
    check("magia lançada no alvo do mestre", lancadas == [("silencio", "hA")])
    check("uso debitado", m["spell_uses"]["silencio"] == 0)
    check("gastou a ação principal", m["_master_acted"] is True)
    m["_master_acted"] = False; m["_master_acao_tipo"] = None; r._errs.clear()
    await r.handle_mestre_usar_habilidade("m1", "g1", "silencio", "hA")
    check("sem usos não lança de novo", len(lancadas) == 1)
    check("ação preservada na recusa", m["_master_acted"] is False)

    print("\n[34b] encantar_* segue não-ativável (não implementada)")
    check("encantar_vampirico barrado",
          r._habilidade_ativavel_manual({"id": "encantar_vampirico", "action_type": "acao",
                                         "dc": 12}) is False)
```

> Nota: `encantar_vampirico` tem `dc` mas **não** tem `save`, então o ramo
> save+dc do gate não o alcança. A checagem `[34b]` trava esse fato.

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA em "predicado aceita magia implementada" — retorna `False` hoje.

- [ ] **Step 3: Implementar**

**(a)** Extrair de `_monster_try_spell` o trecho que debita e lança. Substituir as linhas 22133-22139 (do `if cfg.get("limit_mode"...` até `return True`) por:

```python
        await self._lancar_magia_monstro(m, sid, data, cfg)
        return True
```

E adicionar, logo **antes** de `async def _monster_try_spell(self, m, targets):`:

```python
    def _spell_cfg(self, m, sid):
        """Config de magia do monstro pelo id, ou None."""
        return next((c for c in m.get("monster_spells", []) if c.get("id") == sid), None)

    def _magia_monstro_disponivel(self, m, sid):
        """True se o monstro pode lançar sid agora (implementada, com usos e
        fora de recarga). Mesmos limites que _monster_try_spell aplica."""
        cfg = self._spell_cfg(m, sid)
        if not cfg or sid not in GRIMORIO or sid not in GRIMORIO_IMPLEMENTADAS:
            return False
        if cfg.get("limit_mode", "encounter") == "cooldown":
            return self.round_num >= m.get("spell_cooldowns", {}).get(sid, 0)
        return m.get("spell_uses", {}).get(sid, max(1, int(cfg.get("uses_per_combat", 1)))) > 0

    async def _lancar_magia_monstro(self, m, sid, data, cfg=None):
        """Debita uso/recarga e executa a magia. Ponto único usado pela IA
        (_monster_try_spell, que escolhe o alvo) e pelo mestre no Manual (que
        escolhe o alvo)."""
        cfg = cfg or self._spell_cfg(m, sid) or {}
        magia = GRIMORIO.get(sid)
        if not magia:
            return False
        if cfg.get("limit_mode", "encounter") == "cooldown":
            m.setdefault("spell_cooldowns", {})[sid] = self.round_num + max(1, int(cfg.get("cooldown_turns", 1)))
        else:
            uses = m.setdefault("spell_uses", {}).get(sid, max(1, int(cfg.get("uses_per_combat", 1))))
            m["spell_uses"][sid] = max(0, uses - 1)
        await self._executar_magia_grimorio(m, magia, data)
        return True
```

**(b)** No gate, substituir `_habilidade_ativavel_manual` inteiro por:

```python
    def _habilidade_ativavel_manual(self, ability):
        """O mestre ativa: (a) habilidades save+dc (via _use_monster_ability),
        (b) habilidades de editor herói/guilda (via _ativar_editor_ability),
        (c) magias implementadas do grimório (via _lancar_magia_monstro) e
        (d) as extraídas da IA (Golpe Brutal, Desaparecer nas Sombras).
        O resto aparece na ficha como 'IA apenas' ou 'não implementada'."""
        if not ability or ability.get("action_type") == "passiva":
            return False
        aid = ability.get("id")
        if aid in {"mestre_dos_mortos", "sopro_dragao", "amaldicoar_monstro",
                   "golpe_brutal", "desaparecer_nas_sombras"}:
            return True
        if ability.get("action_type") == "magia":
            return aid in GRIMORIO and aid in GRIMORIO_IMPLEMENTADAS
        if ability.get("save") is not None and ability.get("dc") is not None:
            return True
        return ability.get("source") in {"heroi", "guilda"}
```

**(c)** Em `handle_mestre_usar_habilidade`, inserir o ramo de magia logo **após** a validação de custo (antes do ramo `mestre_dos_mortos`):

```python
        if ability.get("action_type") == "magia":
            sid = ability_id
            if not self._magia_monstro_disponivel(m, sid):
                await self.send_to(pid, {"type": "error", "msg": "Magia sem usos ou em recarga."}); return
            alvo = self.players.get(target_id)
            magia = GRIMORIO.get(sid, {})
            data = {"target_id": target_id}
            if alvo:
                dx = alvo["pos"][0] - m["pos"][0]; dy = alvo["pos"][1] - m["pos"][1]
                data["tx"] = alvo["pos"][0]; data["ty"] = alvo["pos"][1]
                data["dir"] = [0 if dx == 0 else (1 if dx > 0 else -1),
                               0 if dy == 0 else (1 if dy > 0 else -1)]
            alc = magia.get("alcance")
            if alc is not None and alvo:
                if max(abs(m["pos"][0] - alvo["pos"][0]), abs(m["pos"][1] - alvo["pos"][1])) > alc:
                    await self.send_to(pid, {"type": "error", "msg": "Alvo fora de alcance."}); return
            await self._lancar_magia_monstro(m, sid, data)
            self._debitar_acao_mestre(m, custo, "habilidade")
            m["_ja_executou_acao"] = True
            await self.push_state(); return
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[34]` e `[34b]` em verde; nenhuma regressão nas anteriores.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): magias do monstro ativaveis pelo mestre (extrai _lancar_magia_monstro)"
```

---

## Task 6: Extrair `_ativar_golpe_brutal`

**Files:**
- Modify: `server.py:22429-22441` (bloco do Ogro)
- Modify: `server.py:20840+` (`handle_mestre_usar_habilidade` — ramo novo)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[35] Golpe Brutal — mesma extração para IA e mestre")
    r = playing_room_com_mestre()
    ab_gb = {"id": "golpe_brutal", "name": "Golpe Brutal", "action_type": "ataque"}
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "Clava", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_gb],
         "ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    ok = await r._ativar_golpe_brutal(m)
    check("ativou", ok is True)
    check("armou o bônus", m.get("_golpe_brutal_ativo") is True)
    check("entrou em recarga 3", m["ability_cooldowns"]["golpe_brutal"] == 3)
    check("bônus de dano é +2", r._golpe_brutal_bonus(m) == 2)
    check("2ª ativação recusada (recarga)", await r._ativar_golpe_brutal(m) is False)
    m2 = {"id": "g2", "name": "Ogro2", "hp": 25, "pos": [5, 5], "size": [1, 1],
          "special_abilities": [], "ability_cooldowns": {}}
    check("sem a habilidade não ativa", await r._ativar_golpe_brutal(m2) is False)

    print("\n[35b] o golpe seguinte consome o bônus armado")
    golpes = []
    async def fake_atk(mm, atk_def, target_obj):
        golpes.append(mm.get("_golpe_brutal_ativo")); return True
    r._execute_one_monster_attack = fake_atk
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    check("golpe saiu com o bônus ativo", golpes == [True])
    check("bônus limpo após o golpe", m.get("_golpe_brutal_ativo") is None)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA com `AttributeError: ... '_ativar_golpe_brutal'`.

- [ ] **Step 3: Implementar**

Adicionar o helper em `server.py`, logo **antes** de `def _golpe_brutal_bonus(self, m):` (linha ~16954):

```python
    async def _ativar_golpe_brutal(self, m):
        """Arma o Golpe Brutal (+2 de dano no próximo golpe) e entra em recarga.
        Compartilhado: a IA do Ogro chama e ataca em seguida; o mestre chama e
        o próximo handle_mestre_atacar_monstro consome o bônus."""
        if not self._tem_habilidade(m, "golpe_brutal"):
            return False
        cds = m.setdefault("ability_cooldowns", {})
        if cds.get("golpe_brutal", 0) > 0:
            return False
        cds["golpe_brutal"] = 3
        m["_golpe_brutal_ativo"] = True
        await self.gm_say(f"💥 **{m['name']}** desfere um **Golpe Brutal** (+2 dano)!")
        return True
```

No bloco do Ogro (server.py:22436-22441), substituir:

```python
        if usar_gb:                                                 # Golpe Brutal (finalizar)
            cds["golpe_brutal"] = 3
            m["_golpe_brutal_ativo"] = True
            await self.gm_say(f"💥 **{m['name']}** desfere um **Golpe Brutal** para finalizar (+2 dano)!")
            hit = await self._execute_one_monster_attack(m, atk, target_obj)
            m.pop("_golpe_brutal_ativo", None)
```

por:

```python
        if usar_gb:                                                 # Golpe Brutal (finalizar)
            await self._ativar_golpe_brutal(m)
            hit = await self._execute_one_monster_attack(m, atk, target_obj)
            m.pop("_golpe_brutal_ativo", None)
```

> A narração perde o "para finalizar" — é a única diferença observável na IA, e
> é texto. Se quiser preservação literal, mantenha o `gm_say` do Ogro fora do
> helper e faça o helper não narrar; o teste `[35]` então checa só o flag e a
> recarga.

Em `handle_mestre_usar_habilidade`, adicionar o ramo logo após o ramo de magia:

```python
        if ability_id == "golpe_brutal":
            if not await self._ativar_golpe_brutal(m):
                await self.send_to(pid, {"type": "error", "msg": "Golpe Brutal em recarga."}); return
            self._debitar_acao_mestre(m, "livre", "habilidade")
            await self.push_state(); return
```

> Golpe Brutal custa `livre` de propósito: ele não é uma ação, é um modificador
> do golpe que vem a seguir — o custo real é a carga de ataque consumida.

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[35]` e `[35b]` em verde.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): extrai _ativar_golpe_brutal compartilhado IA/mestre"
```

---

## Task 7: Extrair `_ativar_desaparecer_sombras`

**Files:**
- Modify: `server.py:22330-22349` (`_tentar_desaparecer_sombras`)
- Modify: `server.py:20840+` (`handle_mestre_usar_habilidade` — ramo novo)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[36] Desaparecer nas Sombras — extração compartilhada")
    r = playing_room_com_mestre()
    r._em_escuridao = lambda mm: True
    ab_ds = {"id": "desaparecer_nas_sombras", "name": "Desaparecer nas Sombras",
             "action_type": "acao_livre"}
    m = {"id": "g1", "name": "Bugbear", "hp": 20, "pos": [2, 2], "size": [1, 1],
         "control_mode": "manual", "_master_acted": False, "_master_bonus_acted": False,
         "_master_acao_tipo": None, "attacks": [{"name": "maça", "num_attacks": 1}],
         "master_attack_charges": {0: 1}, "special_abilities": [ab_ds],
         "ability_cooldowns": {}}
    r.monsters = {"g1": m}; r.master_manual_mid = "g1"
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [2, 3], "alive": True}}
    check("ativou", await r._ativar_desaparecer_sombras(m) is True)
    check("ficou oculto", m.get("oculto_sombras") is True)
    check("recarga 5", m["ability_cooldowns"]["desaparecer_nas_sombras"] == 5)
    check("2ª ativação recusada", await r._ativar_desaparecer_sombras(m) is False)
    r._em_escuridao = lambda mm: False
    m3 = {"id": "g3", "name": "Bug2", "hp": 20, "pos": [7, 7], "size": [1, 1],
          "special_abilities": [ab_ds], "ability_cooldowns": {}}
    check("fora da escuridão não ativa", await r._ativar_desaparecer_sombras(m3) is False)

    print("\n[36b] pelo mestre é ação livre — a principal segue disponível")
    r._em_escuridao = lambda mm: True
    m["ability_cooldowns"]["desaparecer_nas_sombras"] = 0
    m.pop("oculto_sombras", None)
    await r.handle_mestre_usar_habilidade("m1", "g1", "desaparecer_nas_sombras", None)
    check("oculto de novo", m.get("oculto_sombras") is True)
    check("ação principal intacta", m["_master_acted"] is False)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA com `AttributeError: ... '_ativar_desaparecer_sombras'`.

- [ ] **Step 3: Implementar**

Substituir `_tentar_desaparecer_sombras` (server.py:22330-22349) por:

```python
    async def _ativar_desaparecer_sombras(self, m):
        """Fica oculto nas sombras (imune a ataques à distância; corpo a corpo -4)
        até o início do próximo turno, com recarga de 5 turnos. Não move — quem
        move é quem chamou: a IA no loop de _tentar_desaparecer_sombras, o mestre
        com o próprio orçamento de passos."""
        if not self._tem_habilidade(m, "desaparecer_nas_sombras"):
            return False
        if m.get("ability_cooldowns", {}).get("desaparecer_nas_sombras", 0) > 0:
            return False
        if not self._em_escuridao(m):
            return False
        m.setdefault("ability_cooldowns", {})["desaparecer_nas_sombras"] = 5
        m["oculto_sombras"] = True
        await self.gm_say(
            f"🌫️ **{m['name']}** **desaparece nas sombras** — imune a ataques à "
            f"distância e difícil de acertar (corpo a corpo: -4) até seu próximo turno!")
        return True

    async def _tentar_desaparecer_sombras(self, m, target):
        """Ação livre da IA após o Manto: ativa e avança até 3 quadrados no alvo."""
        if not await self._ativar_desaparecer_sombras(m):
            return
        for _ in range(3):
            antes = list(m["pos"])
            await self._monster_move_step(m, target["pos"])
            if m["pos"] == antes:
                break
```

Em `handle_mestre_usar_habilidade`, adicionar o ramo após o do Golpe Brutal:

```python
        if ability_id == "desaparecer_nas_sombras":
            if not await self._ativar_desaparecer_sombras(m):
                await self.send_to(pid, {"type": "error", "msg": "Só nas sombras e fora de recarga."}); return
            self._debitar_acao_mestre(m, custo, "habilidade")
            await self.push_state(); return
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[36]` e `[36b]` em verde.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): extrai _ativar_desaparecer_sombras compartilhado IA/mestre"
```

---

## Task 8: Byte-identidade da IA sem mestre

**Files:**
- Test: `tools/test_modo_mestre.py`

Esta task não muda produção — ela trava a invariante depois das três extrações.

- [ ] **Step 1: Escrever o teste**

```python
    print("\n[37] invariante — sem mestre, monstro auto não vê nada do Manual")
    r = playing_room_com_mestre()
    r.connections.pop("m1", None)          # mestre desconectado
    check("_mestre_ativo() falso", r._mestre_ativo() is False)
    m = {"id": "g1", "name": "Ogro", "hp": 25, "pos": [2, 2], "size": [1, 1],
         "control_mode": "auto", "special_abilities": [], "ability_cooldowns": {}}
    r.monsters = {"g1": m}
    r.master_manual_mid = None
    r._errs.clear()
    await r.handle_mestre_atacar_monstro("m1", "g1", "hA", 0)
    await r.handle_mestre_usar_habilidade("m1", "g1", "golpe_brutal", None)
    await r.handle_mestre_mover_monstro_para("m1", "g1", 3, 2)
    check("nenhum handler do mestre age fora da janela",
          m["pos"] == [2, 2] and "master_attack_charges" not in m
          and m.get("_master_acted") is None)
```

- [ ] **Step 2: Rodar e ver passar direto**

Run: `python tools/test_modo_mestre.py`
Expected: PASS. Se falhar, algum handler das Tasks 3-7 perdeu a guarda `monster_id != self.master_manual_mid` — conserte o handler, não o teste.

- [ ] **Step 3: Commit**

```bash
git add tools/test_modo_mestre.py
git commit -m "test(mestre): trava a invariante de byte-identidade sem mestre"
```

---

## Task 9: Relógio de inatividade e fim do turno duplo

**Files:**
- Modify: `server.py:12129-12169` (`_master_manual_window`, `_master_manual_timeout`)
- Modify: `server.py:12112-12127` (`_on_master_disconnect`)
- Modify: `server.py:12015-12042` (`handle_mestre_mover_monstro_para` — reiniciar o relógio)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[38] relógio de inatividade e ausência de turno duplo")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 0.05
    ia_calls = {"n": 0}
    async def fake_gm_phase(mm): ia_calls["n"] += 1
    r.gm_phase = fake_gm_phase
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [9, 9], "alive": True,
                        "connected": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "hp": 12, "max_hp": 12, "pos": [1, 1],
         "size": [1, 1], "movement": 3, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    # (a) mestre não faz nada → IA resolve
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0.15)
    await task
    check("(a) timeout sem ação chama a IA", ia_calls["n"] == 1)
    # (b) mestre agiu → timeout apenas fecha, sem turno duplo
    ia_calls["n"] = 0
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    r.master_manual_mid = "g1"
    await r.handle_mestre_mover_monstro_para("m1", "g1", 2, 1)
    await asyncio.sleep(0.15)
    await task
    check("(b) timeout após ação do mestre NÃO chama a IA", ia_calls["n"] == 0)
    check("(b) o monstro andou", m["pos"] == [2, 1])

    print("\n[38b] deadline no payload é reiniciado a cada ação")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 60
    m = {"id": "g1", "name": "Orc", "hp": 12, "max_hp": 12, "pos": [1, 1],
         "size": [1, 1], "movement": 3, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    d1 = r.master_manual_deadline
    await asyncio.sleep(0.02)
    r.master_manual_mid = "g1"
    await r.handle_mestre_mover_monstro_para("m1", "g1", 2, 1)
    check("deadline empurrado para frente", r.master_manual_deadline > d1)
    r.master_manual_event.set()
    await task
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA em "(b) timeout após ação do mestre NÃO chama a IA" — hoje chama.

- [ ] **Step 3: Implementar**

No topo de `server.py`, garantir `import time` (se ainda não houver, adicionar ao bloco de imports).

Substituir o corpo do stub `_reiniciar_timer_manual` (criado na Task 3) por:

```python
    def _reiniciar_timer_manual(self):
        """Empurra o fim do relógio anti-AFK. Chamado ao fim de cada ação do
        mestre: o corte só acontece após MASTER_MANUAL_LIMIT_S de imobilidade
        real, não a partir da abertura da janela."""
        if self.master_manual_mid:
            self.master_manual_deadline = time.monotonic() + self.MASTER_MANUAL_LIMIT_S
```

Em `__init__` (perto de `self.master_manual_timer = None`, linha ~12517), adicionar:

```python
        self.master_manual_deadline = 0.0   # time.monotonic() do corte anti-AFK
```

Em `_master_manual_window`, após `self.master_manual_event = asyncio.Event()`, adicionar:

```python
        self.master_manual_deadline = time.monotonic() + self.MASTER_MANUAL_LIMIT_S
```

Substituir `_master_manual_timeout` inteiro por:

```python
    async def _master_manual_timeout(self, mid):
        """Anti-AFK por inatividade: dorme até o deadline; se o mestre agiu, o
        deadline foi empurrado e a espera recomeça. Ao estourar de verdade, só
        chama a IA se o monstro NÃO fez nada — se o mestre já moveu ou agiu, a
        janela apenas fecha (senão o monstro ganhava um turno duplo)."""
        try:
            while True:
                restante = self.master_manual_deadline - time.monotonic()
                if restante <= 0:
                    break
                await asyncio.sleep(restante)
        except asyncio.CancelledError:
            return
        if self.master_manual_mid != mid:
            return
        self.master_manual_mid = None   # fecha a janela ANTES de resolver
        m = self.monsters.get(mid)
        if m and m["hp"] > 0 and not m.get("_master_touched"):
            alive_players = [p for p in self.players.values() if self._ativo(p)]
            if alive_players:
                await self.gm_phase(m)
        if self.master_manual_event and not self.master_manual_event.is_set():
            self.master_manual_event.set()
```

Em `_on_master_disconnect`, aplicar a mesma regra — trocar:

```python
            m = self.monsters.get(mid)
            if m and m["hp"] > 0:
                alive_players = [p for p in self.players.values() if self._ativo(p)]
                if alive_players:
                    await self.gm_phase(m)   # o monstro interrompido ainda age via IA
```

por:

```python
            m = self.monsters.get(mid)
            if m and m["hp"] > 0 and not m.get("_master_touched"):
                alive_players = [p for p in self.players.values() if self._ativo(p)]
                if alive_players:
                    await self.gm_phase(m)   # só se o mestre não chegou a agir
```

Em `handle_mestre_mover_monstro_para`, antes do `await self.push_state()` final, adicionar:

```python
        m["_master_touched"] = True
        self._reiniciar_timer_manual()
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[38]` e `[38b]` em verde; a seção `[29]` (renovação do orçamento de passo) continua verde.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "fix(mestre): relogio por inatividade e fim do turno duplo no timeout"
```

---

## Task 10: Bloco `master_manual` no payload

**Files:**
- Modify: `server.py:23854-23874` (`_game_state_payload`)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[39] payload master_manual")
    r = playing_room_com_mestre()
    r.MASTER_MANUAL_LIMIT_S = 60
    m = {"id": "g1", "name": "Lobisomem", "hp": 30, "max_hp": 30, "pos": [1, 1],
         "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Garras", "num_attacks": 2},
                     {"name": "Mordida", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    check("sem janela, bloco é None", r._master_manual_payload() is None)
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    bloco = r._master_manual_payload()
    check("mid",           bloco["mid"] == "g1")
    check("moves",         bloco["moves_left"] == 4 and bloco["moves_max"] == 4)
    check("acao livre",    bloco["acao"] is None and bloco["bonus"] is False)
    check("cargas",        bloco["attack_charges"] == {"0": 2, "1": 1})
    check("restante > 0",  bloco["restante"] > 0)
    r.master_manual_event.set()
    await task
```

> As chaves de `attack_charges` viram string: o payload é serializado em JSON,
> que não tem chave inteira. O cliente indexa por string.

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA com `AttributeError: ... '_master_manual_payload'`.

- [ ] **Step 3: Implementar**

Adicionar em `server.py`, logo após `_master_monster_reach` (linha ~19978):

```python
    def _master_manual_payload(self):
        """Bloco de estado da janela Manual para o HUD do mestre, ou None.
        Aditivo: master_manual_mid e master_manual_reach seguem no payload."""
        mid = self.master_manual_mid
        if not mid:
            return None
        m = self.monsters.get(mid)
        if not m or m.get("hp", 0) <= 0:
            return None
        return {
            "mid": mid,
            "moves_left": int(m.get("master_moves_left", 0) or 0),
            "moves_max": int(m.get("movement", self.MASTER_MANUAL_MOVE) or self.MASTER_MANUAL_MOVE),
            "acao": m.get("_master_acao_tipo") if m.get("_master_acted") else None,
            "bonus": bool(m.get("_master_bonus_acted")),
            "restante": max(0, round(self.master_manual_deadline - time.monotonic())),
            "attack_charges": {str(k): v for k, v in (m.get("master_attack_charges") or {}).items()},
        }
```

E em `_game_state_payload`, adicionar ao dict `msg_state`, logo após `"master_manual_reach": (...)`:

```python
            "master_manual": self._master_manual_payload(),
```

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[39]` em verde. Todas as seções `[1]`–`[39]` verdes; **zero falhas**.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "feat(mestre): bloco master_manual no game_state"
```

---

## Task 11: Camada de estado do cliente

**Files:**
- Modify: `src/gameState.js:1479` (`mestreAtacarMonstro`)
- Modify: `src/gameState.js:2438-2451` (exports)

- [ ] **Step 1: Adicionar o `attack_index` e os getters**

Em `src/gameState.js`, substituir:

```javascript
  function mestreAtacarMonstro(monsterId, targetId) { send({ type: 'mestre_atacar_monstro', monster_id: monsterId, target_id: targetId }); }
```

por:

```javascript
  function mestreAtacarMonstro(monsterId, targetId, attackIndex) {
    send({ type: 'mestre_atacar_monstro', monster_id: monsterId, target_id: targetId,
           attack_index: (attackIndex == null ? 0 : attackIndex) });
  }
  // Bloco da janela Manual (null fora dela). Ver _master_manual_payload no servidor.
  function masterManual() { return (gameState && gameState.master_manual) || null; }
  // Cargas restantes de um golpe pelo índice em attacks[].
  function masterAttackCharges(idx) {
    const mm = masterManual();
    if (!mm) return 0;
    return (mm.attack_charges || {})[String(idx)] || 0;
  }
  // true se a ação principal ainda pode virar ataque neste turno.
  function masterPodeAtacar() {
    const mm = masterManual();
    if (!mm) return false;
    return mm.acao == null || mm.acao === 'ataque';
  }
```

E acrescentar ao objeto exportado, junto de `masterManualMid`:

```javascript
    masterManual,
    masterAttackCharges,
    masterPodeAtacar,
```

- [ ] **Step 2: Verificar que o módulo carrega**

Run: `node -e "global.window={};global.WebSocket=function(){};require('./src/gameState.js');console.log('ok')"`
Expected: imprime `ok` sem erro de sintaxe.

> Se o módulo não for require-ável neste projeto (ele é um script de browser),
> substitua por `node --check src/gameState.js`, que valida só a sintaxe.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(mestre): gameState expoe master_manual e attack_index"
```

---

## Task 12: Caixa única com abas (estrutura e CSS)

**Files:**
- Modify: `game.css:1262-1294` (bloco `#hud-mestre`), `game.css:691-718` (bloco `#ficha-monstro`)
- Modify: `game.js:11666` (`renderMasterHud`)

- [ ] **Step 1: Substituir o CSS dos dois painéis**

Em `game.css`, apagar o bloco `#ficha-monstro` (linhas 691-718) e substituir o bloco `#hud-mestre` (linhas 1262-1294) por:

```css
/* ── Painel do Mestre: caixa única com abas (Ativo / Monstros / Mestre) ── */
#hud-mestre {
  position: fixed; top: 12px; right: 12px; bottom: 12px; z-index: 40;
  width: 300px; display: none; flex-direction: column;
  background: var(--dark-panel, rgba(4,2,14,0.94));
  border: 1px solid rgba(var(--gold-rgb),.35); border-radius: var(--radius);
  box-shadow: 0 4px 20px rgba(0,0,0,.5);
  font-size: .8rem; color: var(--text);
}
#hud-mestre.aberto { display: flex; }
#hud-mestre .mp-abas { display: flex; border-bottom: 1px solid var(--border); flex-shrink: 0; }
#hud-mestre .mp-aba {
  flex: 1; text-align: center; padding: 7px 4px; font-size: .68rem;
  color: var(--text2); cursor: pointer; border-bottom: 2px solid transparent;
  background: none; border-top: none; border-left: none; border-right: none;
}
#hud-mestre .mp-aba.on { color: var(--gold); border-bottom-color: var(--gold); background: rgba(var(--gold-rgb),.07); }
#hud-mestre .mp-corpo { flex: 1; overflow-y: auto; padding: 9px 10px; }
#hud-mestre .mp-rodape { flex-shrink: 0; padding: 8px; border-top: 1px solid var(--border); }
#hud-mestre .mp-encerrar {
  width: 100%; background: #7a2a20; color: #fff; border: none; border-radius: 5px;
  padding: 7px; font-size: .78rem; font-weight: bold; cursor: pointer;
}
#hud-mestre .mp-encerrar:hover { background: #9a3428; }

/* cabeçalho da ficha */
.mp-head { display: flex; align-items: center; gap: 7px; margin-bottom: 7px; }
.mp-head .emoji { font-size: 1.4rem; }
.mp-head .nome { flex: 1; color: var(--gold); font-weight: bold; font-size: .85rem; }
.mp-head .sub { font-size: .6rem; color: var(--text2); }
.mp-selo { font-size: .58rem; letter-spacing: .5px; text-transform: uppercase;
           padding: 1px 5px; border-radius: 3px; border: 1px solid var(--border2); color: var(--text2); }
.mp-selo.manual { color: #ff8a5a; border-color: rgba(255,138,90,.45); }
.mp-relogio { font-size: .68rem; color: #8ab88a; }
.mp-relogio.urgente { color: #ff8a5a; }

/* barra de recursos */
.mp-recursos { background: var(--bg2); border: 1px solid #ff8a5a; border-radius: 5px;
               padding: 6px 7px; margin-bottom: 8px; display: flex; text-align: center; }
.mp-recursos > div { flex: 1; font-size: .58rem; color: var(--text2); }
.mp-recursos > div + div { border-left: 1px solid var(--border); }
.mp-recursos b { display: block; font-size: .82rem; margin-top: 2px; }
.mp-recursos .livre { color: #8ab88a; }
.mp-recursos .gasta { color: var(--text2); }
.mp-recursos .mov   { color: #7ab8e0; }

/* vitais e condições */
.mp-hpbar { flex: 1; height: 9px; background: #2a1a1a; border-radius: 5px; overflow: hidden; }
.mp-hpbar > i { display: block; height: 100%; background: linear-gradient(90deg,#8a2020,#c04040); }
.mp-vitais { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
.mp-cond { display: flex; flex-wrap: wrap; gap: 4px; margin: 5px 0 7px; }
.mp-cond span { font-size: .6rem; border-radius: 3px; padding: 1px 5px;
                background: #2a2418; border: 1px solid #7a6a2a; color: #c8b878; }
.mp-attrs { font-size: .6rem; color: var(--text2); border-top: 1px solid var(--border);
            padding-top: 5px; margin-bottom: 6px; }

/* seções e linhas de ação */
.mp-sec { color: var(--gold); font-size: .6rem; letter-spacing: 1.5px; margin: 8px 0 4px; }
.mp-linha { display: flex; align-items: center; gap: 6px; border-radius: 5px;
            padding: 5px 7px; margin-bottom: 4px; cursor: pointer; border: 1px solid; }
.mp-linha .txt { flex: 1; }
.mp-linha .txt b { font-size: .72rem; }
.mp-linha .meta { font-size: .6rem; opacity: .85; }
.mp-linha.atk   { background: #2a1a16; border-color: #7a2a20; }
.mp-linha.hab   { background: #1e1a30; border-color: #5a4a8a; }
.mp-linha.item  { background: #16223a; border-color: #2a5a7a; }
.mp-linha.off   { background: var(--bg2); border-color: var(--border); opacity: .45; cursor: not-allowed; }
.mp-linha.armado { box-shadow: 0 0 0 2px var(--gold) inset; }
.mp-cargas { font-size: .78rem; color: #e88; letter-spacing: 1px; }
.mp-custo  { font-size: .52rem; border: 1px solid currentColor; border-radius: 2px;
             padding: 0 3px; opacity: .8; }

/* lista de monstros (aba Monstros) */
#hud-mestre .mestre-lista { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
#hud-mestre .mestre-vazio { color: var(--text2); font-size: .7rem; text-align: center; padding: 8px 0; }
.mestre-row { display: flex; align-items: center; gap: 6px;
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 4px; padding: 4px 7px; cursor: pointer; transition: border-color .15s, background .15s; }
.mestre-row:hover { border-color: var(--border2); }
.mestre-row.sel { border-color: var(--gold); background: rgba(var(--gold-rgb),.12); }
.mestre-row.manual-ativo { border-color: #ff8a5a; box-shadow: 0 0 0 1px rgba(255,138,90,.4) inset; }
.mestre-row.dormente { opacity: .5; font-style: italic; cursor: default; border-style: dashed; }
.mestre-row .nome { flex: 1; font-size: .72rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mestre-row .modo { font-size: .58rem; letter-spacing: .5px; text-transform: uppercase;
  padding: 1px 5px; border-radius: 3px; border: 1px solid var(--border2); color: var(--text2); }
.mestre-row .modo-auto   { color: #8ab88a; border-color: rgba(50,200,100,.35); }
.mestre-row .modo-semi   { color: #e6c35a; border-color: rgba(230,195,90,.35); }
.mestre-row .modo-manual { color: #ff8a5a; border-color: rgba(255,138,90,.45); }
```

- [ ] **Step 2: Trocar o esqueleto de `renderMasterHud`**

Em `game.js`, substituir a criação e o `host.innerHTML` de `renderMasterHud` (linhas 11666-11674 e 11713-11733) pelo casco com abas. A função passa a se chamar `renderMasterPanel` e delega o corpo a três funções por aba (Tasks 13 e 14):

```javascript
function renderMasterPanel(state){
  if(!state) return;
  let host = document.getElementById('hud-mestre');
  if(!host){
    host = document.createElement('div');
    host.id = 'hud-mestre';
    document.body.appendChild(host);
  }
  host.classList.add('aberto');

  const mm = GS.masterManual();
  // A aba Ativo só é o default enquanto existe monstro na janela Manual.
  if(mm && window._masterTabAuto !== mm.mid){ window._masterTab = 'ativo'; window._masterTabAuto = mm.mid; }
  if(!mm) window._masterTabAuto = null;
  const aba = window._masterTab || 'monstros';

  const nMon = (state.monsters || []).length;
  const corpo = aba === 'ativo'    ? _mpAbaAtivo(state)
              : aba === 'monstros' ? _mpAbaMonstros(state)
              :                      _mpAbaMestre(state);

  host.innerHTML =
    `<div class="mp-abas">
       <button class="mp-aba${aba==='ativo'?' on':''}"    data-aba="ativo">🎯 Ativo</button>
       <button class="mp-aba${aba==='monstros'?' on':''}" data-aba="monstros">📋 Monstros <span style="opacity:.6">${nMon}</span></button>
       <button class="mp-aba${aba==='mestre'?' on':''}"   data-aba="mestre">⚠️ Mestre</button>
     </div>
     <div class="mp-corpo">${corpo}</div>` +
    (mm ? `<div class="mp-rodape"><button class="mp-encerrar">Encerrar monstro</button></div>` : '');

  host.querySelectorAll('.mp-aba').forEach(b => {
    b.onclick = () => { window._masterTab = b.dataset.aba; renderMasterPanel(GS.gameState); };
  });
  const fim = host.querySelector('.mp-encerrar');
  if(fim && mm) fim.onclick = () => GS.mestreEncerrarMonstro(mm.mid);

  if(aba === 'ativo')    _mpWireAtivo(host, state);
  if(aba === 'monstros') _mpWireMonstros(host, state);
  if(aba === 'mestre')   _mpWireMestre(host, state);
  _mpTickRelogio(host);
}
```

Substituir as duas chamadas a `renderMasterHud(...)` em `renderMyPanel` ([game.js:12043](game.js:12043)) e no handler de estado ([game.js:12043](game.js:12043)) por `renderMasterPanel(...)`, e a linha que esconde a ficha ([game.js:12051](game.js:12051)) por:

```javascript
  const hudM = document.getElementById('hud-mestre');
  if(hudM) hudM.classList.remove('aberto');
```

- [ ] **Step 3: Verificar a sintaxe**

Run: `node --check game.js`
Expected: sem saída (sintaxe válida). As funções `_mp*` ainda não existem — o arquivo compila, mas o painel só funciona ao fim da Task 14.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(mestre): caixa unica com abas substitui hud-mestre e ficha-monstro"
```

---

## Task 13: Aba Ativo — ficha completa e mira de golpe

**Files:**
- Modify: `game.js` (substituir `renderFichaMonstro`, linhas 11783-11871)
- Modify: `game.js:23951-23977` (ramo de mestre em `handleTileClick`)

- [ ] **Step 1: Escrever as funções da aba Ativo**

Substituir `renderFichaMonstro` inteira por:

```javascript
// Monstro exibido na aba Ativo: o da janela Manual, ou o que o mestre clicou.
function _mpMonstroAtivo(state){
  const mm = GS.masterManual();
  const id = (mm && mm.mid) || window._mpFocoMid;
  return (state.monsters || []).find(x => x.id === id) || null;
}

const _MP_CUSTO_LBL = { principal: 'AÇÃO', bonus: 'BÔNUS', livre: 'LIVRE' };
function _mpCustoDe(a){
  const at = a && a.action_type;
  if(at === 'acao_bonus') return 'bonus';
  if(at === 'acao_livre') return 'livre';
  return 'principal';
}
// Espelha _habilidade_ativavel_manual no servidor. O servidor é a autoridade;
// isto só decide o que fica clicável.
const _MP_HAB_EXTRAIDAS = ['mestre_dos_mortos','sopro_dragao','amaldicoar_monstro',
                           'golpe_brutal','desaparecer_nas_sombras'];
const _MP_NAO_IMPLEMENTADAS = ['encantar_vampirico','encantar_area_vampirico',
                               'encantar_supremo_vampirico'];
function _mpAtivavel(a){
  if(!a || a.action_type === 'passiva') return false;
  if(_MP_NAO_IMPLEMENTADAS.includes(a.id)) return false;
  if(_MP_HAB_EXTRAIDAS.includes(a.id)) return true;
  if(a.action_type === 'magia') return true;   // servidor recusa as não implementadas
  if(a.save != null && a.dc != null) return true;
  return a.source === 'heroi' || a.source === 'guilda';
}

function _mpCondicoes(m){
  const c = [];
  if(m.com_medo || m.medo_rodadas > 0) c.push('😰 amedrontado');
  if(m.perde_turno)                    c.push('💫 atordoado');
  if(m.envenenado || m.veneno_rodadas > 0) c.push('🧪 envenenado');
  if(m.mov_reduzido_rodadas > 0)       c.push('🐌 movimento reduzido');
  if(m.oculto_sombras)                 c.push('🌫️ oculto');
  if(m.em_chamas_rodadas > 0)          c.push('🔥 em chamas');
  return c;
}

function _mpAbaAtivo(state){
  const m = _mpMonstroAtivo(state);
  if(!m) return '<div class="mestre-vazio">Nenhum monstro em foco.<br>Clique num monstro no tabuleiro ou na aba Monstros.</div>';
  const mm = GS.masterManual();
  const manual = !!(mm && mm.mid === m.id);
  const hpPct = Math.max(0, Math.min(100, Math.round(100 * m.hp / (m.max_hp || m.hp || 1))));

  let h = `<div class="mp-head">
      <span class="emoji">${m.emoji || '👾'}</span>
      <div style="flex:1">
        <div class="nome">${_esc(m.name || m.type || 'Monstro')}</div>
        <div class="sub">${m.room_id != null ? 'sala '+_esc(String(m.room_id))+' · ' : ''}ND ${m.cr != null ? m.cr : '—'}</div>
      </div>
      <div style="text-align:right">
        <div class="mp-selo${manual?' manual':''}">${_esc(m.control_mode || 'auto')}</div>
        ${manual ? '<div class="mp-relogio" data-restante="'+(mm.restante||0)+'">⏱ —</div>' : ''}
      </div>
    </div>`;

  if(manual){
    const acao  = mm.acao ? `<b class="gasta">${_esc(mm.acao)}</b>` : '<b class="livre">livre</b>';
    const bonus = mm.bonus ? '<b class="gasta">usada</b>' : '<b class="livre">livre</b>';
    h += `<div class="mp-recursos">
        <div>👣 MOVIMENTO<b class="mov">${mm.moves_left}<span style="font-size:.6rem;opacity:.6">/${mm.moves_max}</span></b></div>
        <div>⚡ AÇÃO${acao}</div>
        <div>✨ BÔNUS${bonus}</div>
      </div>`;
  }

  h += `<div class="mp-vitais"><div class="mp-hpbar"><i style="width:${hpPct}%"></i></div><span>${m.hp}/${m.max_hp || m.hp}</span></div>
    <div style="font-size:.68rem;color:var(--text2)">🛡️ CA ${m.ac != null ? m.ac : '—'} · 👣 ${m.movement != null ? m.movement : '—'}</div>`;

  const cond = _mpCondicoes(m);
  if(cond.length) h += `<div class="mp-cond">${cond.map(c=>`<span>${c}</span>`).join('')}</div>`;

  h += `<div class="mp-attrs">FOR ${m.str_ ?? '—'} · DES ${m.dex ?? '—'} · CON ${m.con_ ?? '—'} · INT ${m.int_ ?? '—'}
        &nbsp;|&nbsp; Fort ${m.fort ?? '—'} · Ref ${m.ref_ ?? '—'} · Von ${m.will ?? '—'}</div>`;

  // ── Ataques ──
  const ataques = (m.attacks && m.attacks.length) ? m.attacks
                : (m.atk_bonus != null ? [{name:'Ataque', atk_bonus:m.atk_bonus, damage:m.damage, num_attacks:1}] : []);
  if(ataques.length){
    h += `<div class="mp-sec">ATAQUES <span style="color:var(--text2);letter-spacing:0">— gastam a ação</span></div>`;
    ataques.forEach((a, i) => {
      const cargas = manual ? GS.masterAttackCharges(i) : (a.num_attacks || 1);
      const pode = manual && cargas > 0 && GS.masterPodeAtacar();
      const b = (a.atk_bonus != null) ? ((a.atk_bonus >= 0 ? '+' : '') + a.atk_bonus) : '';
      const alc = a.range ? `alcance ${a.range}q` : 'corpo a corpo';
      const armado = window._mpGolpeArmado === i ? ' armado' : '';
      h += `<div class="mp-linha ${pode ? 'atk'+armado : 'off'}" data-atk="${i}">
          <span style="font-size:1rem">${a.range ? '🎯' : '⚔️'}</span>
          <div class="txt"><b>${_esc(a.name || 'Ataque')}</b><div class="meta">${b} · ${_esc(a.damage || '')} · ${alc}</div></div>
          <span class="mp-cargas">${'●'.repeat(cargas) || '—'}</span>
        </div>`;
    });
  }

  // ── Magias e habilidades ──
  const abis = (m.special_abilities || []).filter(a => a.action_type && a.action_type !== 'passiva');
  if(abis.length){
    h += `<div class="mp-sec">MAGIAS E HABILIDADES</div>`;
    abis.forEach(a => {
      const naoImpl = _MP_NAO_IMPLEMENTADAS.includes(a.id);
      const ativavel = _mpAtivavel(a);
      const custo = _mpCustoDe(a);
      const bloqueado = custo === 'principal' ? !!(mm && mm.acao) : custo === 'bonus' ? !!(mm && mm.bonus) : false;
      const pode = manual && ativavel && !bloqueado;
      const motivo = naoImpl ? 'não implementada'
                   : !ativavel ? 'IA apenas'
                   : bloqueado ? 'ação já gasta' : '';
      h += `<div class="mp-linha ${pode ? 'hab' : 'off'}" data-hab="${_esc(a.id)}">
          <span style="font-size:1rem">✦</span>
          <div class="txt"><b>${_esc(a.name || a.id)}</b> <span class="mp-custo">${_MP_CUSTO_LBL[custo]}</span>
            <div class="meta">${_esc(a.descricao || a.desc || '')}${motivo ? ' · '+motivo : ''}</div></div>
        </div>`;
    });
  }

  // ── Itens ──
  const cons = m.equipment_consumables || [];
  if(cons.length){
    h += `<div class="mp-sec">ITENS (bolsa)</div>`;
    cons.forEach(it => {
      const principal = it.effect === 'throwable' || it.effect === 'scroll';
      const inutil = ['food','ration','wine','ale'].includes(it.effect);
      const bloqueado = principal ? !!(mm && mm.acao) : !!(mm && mm.bonus);
      const pode = manual && !inutil && !bloqueado;
      h += `<div class="mp-linha ${pode ? 'item' : 'off'}" data-item="${_esc(it.id)}">
          <span style="font-size:1rem">${it.emoji || '🎒'}</span>
          <div class="txt"><b>${_esc(it.name || it.id)}</b> <span class="mp-custo">${principal?'AÇÃO':'BÔNUS'}</span>
            <div class="meta">${inutil ? 'sem efeito em monstros' : _esc(it.descricao || it.desc || '')}</div></div>
        </div>`;
    });
  }

  // ── Equipado e passivas ──
  const eq = [];
  if(m.equipped_weapon) eq.push('🗡️ ' + _esc(m.equipped_weapon.name));
  (m.equipment_items || []).filter(i => i.ac_bonus || i.effect === 'def_')
    .forEach(i => eq.push('🛡️ ' + _esc(i.name)));
  const passivas = (m.special_abilities || []).filter(a => !a.action_type || a.action_type === 'passiva');
  if(eq.length || passivas.length){
    h += `<details><summary class="mp-sec" style="cursor:pointer">EQUIPADO (${eq.length}) · PASSIVAS (${passivas.length})</summary>
      ${eq.map(e=>`<div class="meta">${e}</div>`).join('')}
      ${passivas.map(p=>`<div class="meta"><b>${_esc(p.name||p.id)}</b> — ${_esc(p.descricao||p.desc||'')}</div>`).join('')}
    </details>`;
  }
  return h;
}

function _mpWireAtivo(host, state){
  const m = _mpMonstroAtivo(state);
  if(!m) return;
  host.querySelectorAll('.mp-linha.atk').forEach(el => {
    el.onclick = () => {
      const i = parseInt(el.dataset.atk, 10);
      window._mpGolpeArmado = (window._mpGolpeArmado === i) ? null : i;
      toast(window._mpGolpeArmado != null ? 'Golpe armado — clique num herói.' : 'Golpe desarmado.',
            'var(--gold)');
      renderMasterPanel(GS.gameState);
    };
  });
  host.querySelectorAll('.mp-linha.hab').forEach(el => {
    el.onclick = () => _mestreAtivarHabilidade(m, el.dataset.hab);
  });
  host.querySelectorAll('.mp-linha.item').forEach(el => {
    el.onclick = () => _mestreUsarItemFicha(m, el.dataset.item);
  });
}

// Contador local: o servidor manda os segundos restantes a cada push_state e o
// cliente decrementa entre um estado e outro.
function _mpTickRelogio(host){
  if(window._mpRelogioTimer) clearInterval(window._mpRelogioTimer);
  const el = host.querySelector('.mp-relogio');
  if(!el) return;
  let n = parseInt(el.dataset.restante, 10) || 0;
  const pinta = () => {
    el.textContent = '⏱ ' + Math.floor(n/60) + ':' + String(n%60).padStart(2,'0');
    el.classList.toggle('urgente', n <= 15);
  };
  pinta();
  window._mpRelogioTimer = setInterval(() => { n = Math.max(0, n-1); pinta(); }, 1000);
}
```

- [ ] **Step 2: Ligar a mira no clique do tabuleiro**

Em `game.js`, substituir o bloco de mira do ramo de mestre em `handleTileClick` (linhas 23959-23976) por:

```javascript
    const st = GS.gameState;
    const mm = GS.masterManual();
    if(mm){
      const monM = (st.monsters||[]).find(x=>x.id===mm.mid);
      const alvo = (st.players||[]).find(p=>p.alive && p.pos[0]===tx && p.pos[1]===ty);
      if(monM && alvo && GS.masterPodeAtacar()){
        // Golpe armado na ficha manda; sem golpe armado, o primeiro com carga.
        let idx = window._mpGolpeArmado;
        if(idx == null){
          const n = ((monM.attacks||[]).length) || 1;
          for(let i=0;i<n;i++){ if(GS.masterAttackCharges(i) > 0){ idx = i; break; } }
        }
        if(idx != null && GS.masterAttackCharges(idx) > 0){
          const atk = (monM.attacks||[{}])[idx] || {};
          const rng = atk.range || null;
          const dx = Math.abs(monM.pos[0]-tx), dy = Math.abs(monM.pos[1]-ty);
          const inR = rng != null ? Math.max(dx,dy) <= rng : ((dx===1&&dy===0)||(dx===0&&dy===1));
          if(inR){ GS.mestreAtacarMonstro(mm.mid, alvo.id, idx); window._mpGolpeArmado = null; return; }
          toast('Alvo fora do alcance deste golpe.', 'var(--orange)'); return;
        }
      }
      if((st.master_manual_reach||[]).some(([x,y])=>x===tx&&y===ty)){
        GS.mestreMoverMonstroPara(mm.mid, tx, ty); return;
      }
    }
    const mon = _monstroEmCasa(tx, ty);
    if(mon){ window._mpFocoMid = mon.id; window._masterTab = 'ativo'; renderMasterPanel(GS.gameState); }
    return;
```

E em `_mestreAtivarHabilidade`, trocar a chamada final para reusar o painel: substituir toda ocorrência de `renderFichaMonstro(` por `renderMasterPanel(GS.gameState)` onde ela existir (linhas 11741, 11776 e 23975 já foram cobertas acima).

- [ ] **Step 3: Verificar a sintaxe**

Run: `node --check game.js`
Expected: sem saída.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(mestre): aba Ativo com recursos, condicoes, cargas de golpe e mira"
```

---

## Task 14: Abas Monstros e Mestre

**Files:**
- Modify: `game.js` (restante de `renderMasterHud`, linhas 11677-11712 e 11736-11779)

- [ ] **Step 1: Escrever as duas abas a partir do HUD atual**

Adicionar em `game.js`, junto das demais `_mp*`:

```javascript
function _mpAbaMonstros(state){
  const mm = GS.masterManual();
  const rows = (state.monsters || []).map(m => {
    const dormente = !m.alertado;
    const sel = _masterSel.has(m.id) ? ' sel' : '';
    const ativo = (mm && m.id === mm.mid) ? ' manual-ativo' : '';
    const modo = m.control_mode || 'auto';
    const pct = Math.max(0, Math.min(100, Math.round(100 * m.hp / (m.max_hp || m.hp || 1))));
    if(dormente){
      return `<div class="mestre-row dormente"><span class="nome">${_esc(m.name || m.type || '?')}</span>
              <span style="font-size:.6rem">dormente</span></div>`;
    }
    return `<div class="mestre-row${sel}${ativo}" data-mid="${_esc(m.id)}">
        <span>${m.emoji || '👾'}</span>
        <span class="nome">${_esc(m.name || m.type || '?')}</span>
        <span class="mp-hpbar" style="max-width:34px"><i style="width:${pct}%"></i></span>
        <span class="modo modo-${modo}">${modo}</span>
      </div>`;
  }).join('');
  const heroOpts = (state.players || []).filter(p => p.alive)
    .map(p => `<option value="${_esc(p.id)}">${_esc(p.name)}</option>`).join('');
  return `<div class="mestre-lista">${rows || '<div class="mestre-vazio">Nenhum monstro na masmorra.</div>'}</div>
    <div style="font-size:.6rem;color:var(--text2);margin-bottom:3px">${_masterSel.size} selecionado(s) — aplicar a todos:</div>
    <div class="mestre-modos" style="display:flex;gap:4px;margin-bottom:6px">
      <button data-modo="auto" style="flex:1">Auto</button>
      <button data-modo="semi" style="flex:1">Semi</button>
      <button data-modo="manual" style="flex:1">Manual</button>
    </div>
    <select class="mestre-alvo" style="width:100%">
      <option value="">— alvo (Semi) —</option>${heroOpts}
    </select>`;
}

function _mpWireMonstros(host, state){
  host.querySelectorAll('.mestre-row[data-mid]').forEach(row => {
    row.onclick = () => {
      const mid = row.dataset.mid;
      if(_masterSel.has(mid)) _masterSel.delete(mid); else _masterSel.add(mid);
      window._mpFocoMid = mid;
      renderMasterPanel(GS.gameState);
    };
  });
  host.querySelectorAll('.mestre-modos button').forEach(b => {
    b.onclick = () => { if(_masterSel.size) GS.mestreSetModo([..._masterSel], b.dataset.modo); };
  });
  const selAlvo = host.querySelector('.mestre-alvo');
  if(selAlvo) selAlvo.onchange = () => {
    if(selAlvo.value && _masterSel.size) GS.mestreSetAlvo([..._masterSel], selAlvo.value);
  };
}

function _mpAbaMestre(state){
  const reserva = state.master_reserve || [];
  const falas = state.falas || [];
  let h = '';
  if(reserva.length){
    h += `<div class="mp-sec">REFORÇOS</div>` + reserva.map(r =>
      `<button class="mestre-reforco-btn mp-linha ${window._modoImplantarReforco === r.type ? 'atk armado' : 'atk'}" data-rtype="${_esc(r.type)}">
         <span class="txt"><b>${r.emoji || '👾'} ${_esc(r.name || r.type)}</b> ×${r.count}</span>
       </button>`).join('');
    if(window._modoImplantarReforco)
      h += `<div style="font-size:.6rem;color:var(--text2)">Clique numa casa livre para implantar (Esc cancela)</div>`;
  }
  if(falas.length){
    h += `<div class="mp-sec">FALAS</div>` + falas.map(f =>
      `<button class="mestre-fala-btn mp-linha hab" data-fid="${_esc(f.id)}">
         <span class="txt">${_esc((f.falante && f.falante.emoji) || '💬')} ${_esc((f.falante && f.falante.nome) || 'NPC')}:
         <i>${_esc((f.texto || '').slice(0, 40))}${(f.texto || '').length > 40 ? '…' : ''}</i></span>
       </button>`).join('');
  }
  return h || '<div class="mestre-vazio">Sem reforços nem falas nesta masmorra.</div>';
}

function _mpWireMestre(host, state){
  host.querySelectorAll('.mestre-reforco-btn').forEach(btn => {
    btn.onclick = () => {
      const t = btn.dataset.rtype;
      window._modoImplantarReforco = (window._modoImplantarReforco === t) ? null : t;
      renderMasterPanel(GS.gameState);
    };
  });
  host.querySelectorAll('.mestre-fala-btn').forEach(btn => {
    btn.onclick = () => GS.dispararFala(btn.dataset.fid);
  });
}
```

Apagar o corpo antigo de `renderMasterHud` que restou (a montagem de `rows`, `heroOpts`, `reforcoHtml`, `falasHtml` e todo o wiring das linhas 11736-11779), já substituído acima.

Trocar as duas referências restantes a `renderMasterHud` — na tecla Esc ([game.js:14068](game.js:14068)) — por `renderMasterPanel`.

- [ ] **Step 2: Verificar a sintaxe e que nada ficou órfão**

Run: `node --check game.js`
Expected: sem saída.

Run: `grep -n "renderMasterHud\|renderFichaMonstro" game.js`
Expected: **nenhuma linha** — as duas funções antigas sumiram por completo.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(mestre): abas Monstros e Mestre no painel unico"
```

---

## Task 15: Verificação in-app

**Files:** nenhum — verificação manual.

O cliente não tem harness automatizado neste projeto; esta é a mesma forma como as camadas anteriores do Modo Mestre foram fechadas.

- [ ] **Step 1: Rodar a suíte inteira do servidor**

```bash
python tools/test_modo_mestre.py
```

Expected: `=== N passaram, 0 falharam ===`

- [ ] **Step 2: Rodar as suítes vizinhas para descartar regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_campanha.py && python tools/test_persistencia_masmorra.py
```

Expected: cada uma termina com `0 falharam`. Falhas pré-existentes conhecidas (bugbear, ogro, devorador) **não** contam — confira contra o HEAD antes de culpar esta mudança.

- [ ] **Step 3: Smoke com dois navegadores**

Subir o servidor e abrir `http://localhost:8765/index.html` em duas janelas: uma assume herói, a outra assume Mestre no lobby.

Roteiro, marcando cada um:
- [ ] O painel do mestre abre com as três abas e nada mais flutua sobre o tabuleiro.
- [ ] Um monstro avistado entra em Manual; a aba **Ativo** abre sozinha com ele.
- [ ] A barra mostra movimento `n/max`; clicar numa casa azul reduz o número.
- [ ] Um monstro de dois ataques mostra as cargas certas; clicar um golpe e depois um herói executa aquele golpe e consome uma bolinha.
- [ ] Dois golpes em heróis diferentes funcionam; o golpe seguinte ao esgotar as cargas é recusado com mensagem.
- [ ] Uma magia (Xamã: Silêncio) aparece clicável, dispara no alvo escolhido e some por usos/recarga.
- [ ] Depois de atacar, as habilidades de AÇÃO ficam esmaecidas com "ação já gasta"; um item de BÔNUS continua clicável.
- [ ] O relógio conta para trás e **reinicia** a cada ação.
- [ ] Ficar parado até o relógio zerar sem ter agido: a IA resolve o monstro.
- [ ] Agir e depois deixar o relógio zerar: o turno apenas passa, **sem** o monstro agir de novo.
- [ ] Clicar num monstro que não é o da vez abre a ficha em leitura, sem barra de recursos e sem rodapé.
- [ ] Um vampiro mostra os Encantar como "não implementada".
- [ ] Sair do Modo Mestre (jogar como herói normal) não mostra nenhum resquício do painel.

- [ ] **Step 4: Commit final**

```bash
git add -A docs/
git commit -m "docs: marca a verificacao in-app da ficha do monstro do Mestre"
```

> Cuidado ao commitar: `server.py` e `game.js` têm alterações em andamento do
> usuário nesta branch. Use `git add <arquivo>` só nos arquivos que você tocou e
> confira `git status` antes.

---

## Ordem e dependências

Tasks 1 → 10 são de servidor e devem ser feitas em ordem: a Task 3 depende do helper da Task 2; a Task 4 do helper da Task 1; a Task 9 substitui o stub criado na Task 3.

Tasks 11 → 14 são de cliente e dependem do payload da Task 10.

A Task 15 fecha.
