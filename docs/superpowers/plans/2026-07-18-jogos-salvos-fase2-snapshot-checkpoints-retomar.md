# Jogos Salvos — Fase 2: Snapshot/Restore + Checkpoints + Retomar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o progresso do personagem realmente persistir por jogo salvo: capturar/restaurar a ficha durável, gravar nos pontos seguros (cidade / fim de fase), vincular conta↔personagem no lobby, retomar um jogo salvo e travar sessão-única.

**Architecture:** Duas funções puras (`snapshot_character`/`restore_character`) sobre a whitelist de campos duráveis do `make_player`, mais integração no `GameRoom` (bind no lobby, overlay no `start_game`, checkpoint em `_voltar_para_cidade`) e um handler `load_savegame` que abre um lobby ligado ao savegame. Reusa a camada de storage da Fase 1.

**Tech Stack:** Python 3.x, `websockets`, testes no estilo `tools/test_savegames.py` (`check(name, cond)`) + o mock de sala do `tools/test_guilda.py` (`setup()` que substitui `broadcast`/`send_to`/`push_state`).

**Spec:** `docs/superpowers/specs/2026-07-18-jogos-salvos-campanhas-persistentes-design.md`
**Depende de:** Fase 1 (contas + camada de savegames), já implementada.

---

## Escopo desta fase

Entra: `snapshot_character`/`restore_character`; `GameRoom` ganha `savegame_id`/`savegame`/`account_by_pid`; threading da conta logada até a sala; bind conta↔personagem no `select_class`; overlay no `start_game`; checkpoint em `_voltar_para_cidade`; handler `load_savegame` (retomar, com trava `SAVEGAMES_IN_USE`); liberação da trava no teardown da sala.

**Fora desta fase** (Fase 3): toda a UI do cliente (login, Novo/Continuar jogo, lobby com auto-vínculo). Nesta fase o servidor fica pronto e testado; o cliente ainda usa o fluxo antigo de `create_room`.

## Campos duráveis (contrato de snapshot)

`snapshot_character` copia SÓ esta whitelist (todos já em estado consistente na cidade, então `restore` é só sobrescrita — sem recalcular efeitos de equipamento):

```
gold, hp, max_hp, mp, max_mp, xp, level, level_bonus,
ac, ac_base, atk_bonus, base_atk_bonus, weapon,
fort, ref_, will, spd,
bag, bag_size, gear,
guild_owned, guild_equip, magias_conhecidas
```

Campos de runtime (cooldowns, buffs de turno, fome/sede, pos, facing, action_done…) NÃO entram — resetam por sessão. `fome`/`sede` já voltam a 100 na cidade.

## Estrutura de arquivos

- **Modificar `server.py`:**
  - Bloco de persistência (~linha 665, após `try_create_savegame`): `_DURABLE_FIELDS`, `snapshot_character`, `restore_character`.
  - `GameRoom.__init__` (~5126): `self.savegame_id=None`, `self.savegame=None`, `self.account_by_pid={}`.
  - `add_player` (~5040): aceitar e guardar o `account`.
  - `select_class` (~5055): bind conta↔personagem no savegame.
  - `start_game` (~5236): overlay via `restore_character` para membros presentes.
  - `_voltar_para_cidade` (~10996): checkpoint `_checkpoint_savegame`.
  - `handler()` (~19489): threading do `account` em `create_room`/`join_room`; novo handler `load_savegame`; liberar `SAVEGAMES_IN_USE` no teardown.
- **Modificar `tools/test_savegames.py`** — blocos `[9]`–`[12]`.

---

## Task 1: `snapshot_character` / `restore_character`

**Files:**
- Modify: `server.py` (bloco de persistência, após `try_create_savegame`)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha.** Adicionar em `main()` (após o bloco `[8]`, antes do summary):

```python
    # [9] snapshot/restore da ficha
    print("\n[9] Snapshot/restore de personagem")
    from server import make_player
    p = make_player("p1", "Herói", "warrior", 0)
    p["gold"] = 999; p["hp"] = 3; p["xp"] = 120; p["level"] = 2
    p["bag"].append({"id": "pocao", "name": "Poção"})
    p["guild_owned"]["tecnicas"].append("brutalidade")
    p["guild_equip"]["tecnica"] = "brutalidade"
    p["technique_cooldowns"]["brutalidade"] = 7   # runtime — NÃO deve entrar
    snap = S.snapshot_character(p)
    check("snapshot pega ouro", snap["gold"] == 999)
    check("snapshot pega hp", snap["hp"] == 3)
    check("snapshot pega guild", snap["guild_owned"]["tecnicas"] == ["brutalidade"])
    check("snapshot ignora runtime (cooldowns)", "technique_cooldowns" not in snap)
    # restore num personagem fresco
    p2 = make_player("p2", "Outro", "warrior", 1)
    S.restore_character(p2, snap)
    check("restore aplica ouro", p2["gold"] == 999)
    check("restore aplica hp", p2["hp"] == 3)
    check("restore aplica nível/xp", p2["level"] == 2 and p2["xp"] == 120)
    check("restore aplica bag", any(i.get("id") == "pocao" for i in p2["bag"]))
    check("restore aplica guild equip", p2["guild_equip"]["tecnica"] == "brutalidade")
    check("restore preserva id/nome do shell", p2["id"] == "p2" and p2["name"] == "Outro")
    # isolamento: mutar o snapshot não afeta o personagem e vice-versa (deep copy)
    snap["bag"].append({"id": "x"})
    check("restore fez deep copy (bag isolada)", not any(i.get("id") == "x" for i in p2["bag"]))
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (`no attribute 'snapshot_character'`).

- [ ] **Step 3: Implementar.** No bloco de persistência, após `try_create_savegame`:

```python
# Campos duráveis da ficha (o resto é runtime e reseta por sessão). Na cidade,
# esses valores já estão consistentes, então restore é só sobrescrita.
_DURABLE_FIELDS = (
    "gold", "hp", "max_hp", "mp", "max_mp", "xp", "level", "level_bonus",
    "ac", "ac_base", "atk_bonus", "base_atk_bonus", "weapon",
    "fort", "ref_", "will", "spd",
    "bag", "bag_size", "gear",
    "guild_owned", "guild_equip", "magias_conhecidas",
)

def snapshot_character(player):
    """Extrai a ficha durável do jogador (deep copy). Ver _DURABLE_FIELDS."""
    return {k: deepcopy(player[k]) for k in _DURABLE_FIELDS if k in player}

def restore_character(player, snap):
    """Sobrepõe a ficha durável num make_player fresco (deep copy). Mantém
    id/nome/class_id/slot do shell; ignora chaves fora da whitelist."""
    for k in _DURABLE_FIELDS:
        if k in snap:
            player[k] = deepcopy(snap[k])
```

(`deepcopy` já está importado: `from copy import deepcopy`.)

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → blocos [1]–[9] passam.

- [ ] **Step 5: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): snapshot_character/restore_character (ficha durável)"
```

---

## Task 2: `GameRoom` conhece o savegame e a conta de cada jogador

**Files:**
- Modify: `server.py` — `GameRoom.__init__` (~5126) e `add_player` (~5040)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha.** Adicionar em `main()`:

```python
    # [10] GameRoom ↔ savegame
    print("\n[10] Sala conhece savegame e contas")
    from server import GameRoom
    r = GameRoom("TST0")
    check("savegame_id default None", r.savegame_id is None)
    check("savegame default None", r.savegame is None)
    check("account_by_pid default vazio", r.account_by_pid == {})
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (`AttributeError: ... 'savegame_id'`).

- [ ] **Step 3a: Implementar os atributos.** Em `GameRoom.__init__`, logo após `self.selected_campaign = None` (~5169), acrescentar:

```python
        # ── Jogos salvos (Fase 2) ─────────────────────────────────────────
        self.savegame_id = None      # id do savegame ligado a esta sala (ou None)
        self.savegame = None         # dict do savegame carregado (ou None)
        self.account_by_pid = {}     # pid -> apelido da conta logada
```

- [ ] **Step 3b: Threading da conta no `add_player`.** A assinatura atual é `async def add_player(self, ws, pid, name):`. Trocar para aceitar `account=None` e guardá-lo. Localizar:

```python
    async def add_player(self, ws, pid, name):
```
e o corpo que faz `self.players[pid] = {...}`. Alterar a assinatura para:

```python
    async def add_player(self, ws, pid, name, account=None):
```
e, logo após `self.connections[pid] = ws`, acrescentar:

```python
        if account:
            self.account_by_pid[pid] = account
```

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → [1]–[10] passam.

- [ ] **Step 5: Regressão.** `python tools/test_guilda.py` e `python tools/test_modo_mestre.py` → continuam verdes (não mudamos comportamento default; `add_player` ganhou só um parâmetro opcional).

- [ ] **Step 6: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): GameRoom.savegame_id/savegame/account_by_pid + add_player(account)"
```

---

## Task 3: Bind conta↔personagem no `select_class`

**Files:**
- Modify: `server.py` — `select_class` (~5055)
- Test: `tools/test_savegames.py` (usa o mock de sala do estilo `test_guilda.setup()`)

Regra: numa sala ligada a savegame, ao escolher classe — (a) se a conta já tem classe vinculada no savegame, força ESSA classe; (b) se a classe já é de OUTRA conta no savegame, recusa; (c) 1ª escolha grava `members[conta] = {class_id}` e cria a ficha fresca em `characters[class_id]` (via `snapshot_character(make_player(...))`), e persiste com `write_savegame`. Sem savegame ligado (`self.savegame is None`), comportamento é o ATUAL (byte-idêntico).

- [ ] **Step 1: Escrever o teste que falha.** Adicionar em `main()` um helper de sala e o bloco `[11]`:

```python
    # [11] bind conta↔personagem no lobby
    print("\n[11] Bind de personagem no savegame")
    import asyncio as _aio
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    try:
        r = GameRoom("TST1")
        async def _noop(*a, **k): pass
        r.broadcast_lobby = _noop; r.send_to = _noop
        sg = S.create_savegame("Jogo", "ricardo", "campaign", "elara.json", False)
        r.savegame_id = sg["id"]; r.savegame = sg
        # jogador joao (conta) entra e escolhe warrior
        r.players["j1"] = {"id": "j1", "name": "Joao", "class_id": None, "ready": False, "connected": True, "slot": 0}
        r.account_by_pid["j1"] = "joao"
        _aio.get_event_loop().run_until_complete(r.select_class("j1", "warrior"))
        check("grava vínculo no savegame", sg["members"].get("joao", {}).get("class_id") == "warrior")
        check("cria ficha fresca do personagem", "warrior" in sg["characters"])
        check("persistiu em disco", S.load_savegame(sg["id"])["members"]["joao"]["class_id"] == "warrior")
        # outra conta tenta pegar a MESMA classe → recusa
        r.players["j2"] = {"id": "j2", "name": "Maria", "class_id": None, "ready": False, "connected": True, "slot": 1}
        r.account_by_pid["j2"] = "maria"
        errs = []
        async def _cap(pid, m, *a, **k):
            if isinstance(m, dict) and m.get("type") == "error": errs.append(m.get("msg", ""))
        r.send_to = _cap
        _aio.get_event_loop().run_until_complete(r.select_class("j2", "warrior"))
        check("recusa classe de outra conta", r.players["j2"]["class_id"] is None and errs)
        # joao volta e é forçado ao warrior mesmo pedindo mage
        _aio.get_event_loop().run_until_complete(r.select_class("j1", "mage"))
        check("conta vinculada é forçada à sua classe", r.players["j1"]["class_id"] == "warrior")
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (o bind ainda não existe; `members` fica vazio).

- [ ] **Step 3: Implementar.** Em `select_class`, logo no início (após obter `p = self.players.get(pid)` e as validações de mestre/`cls_id in CLASSES`, e ANTES da checagem de "não tomado na sala"), inserir o bloco de savegame:

```python
        # ── Jogo salvo: vínculo conta↔personagem (Fase 2) ─────────────────
        if self.savegame is not None:
            conta = self.account_by_pid.get(pid)
            if not conta:
                await self.send_to(pid, {"type": "error",
                    "msg": "Faça login para escolher um personagem neste jogo."})
                return
            membros = self.savegame.setdefault("members", {})
            ja = membros.get(conta, {}).get("class_id")
            if ja:
                # Conta já vinculada: força a classe dela (ignora cls_id pedido).
                cls_id = ja
            else:
                # Classe já pertence a OUTRA conta neste savegame?
                dono = next((c for c, m in membros.items()
                             if m.get("class_id") == cls_id and c != conta), None)
                if dono:
                    await self.send_to(pid, {"type": "error",
                        "msg": "Esse personagem é de outro jogador neste jogo."})
                    return
                # 1ª escolha: grava vínculo + ficha fresca e persiste.
                membros[conta] = {"class_id": cls_id}
                chars = self.savegame.setdefault("characters", {})
                if cls_id not in chars:
                    novo = make_player(pid, self.players[pid]["name"], cls_id, self.players[pid].get("slot", 0))
                    chars[cls_id] = snapshot_character(novo)
                write_savegame(self.savegame)
```

(O restante de `select_class` — checagem de classe tomada na sala, trava `CHARACTERS_IN_USE`, `self.players[pid]["class_id"] = cls_id`, `ready`, broadcast — permanece e agora usa o `cls_id` possivelmente forçado.)

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → [1]–[11] passam.

- [ ] **Step 5: Regressão.** `python tools/test_guilda.py`, `python tools/test_modo_mestre.py` → verdes (sem savegame, o bloco é pulado).

- [ ] **Step 6: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): bind conta↔personagem no select_class (só com savegame)"
```

---

## Task 4: Overlay no `start_game` + checkpoint em `_voltar_para_cidade`

**Files:**
- Modify: `server.py` — `start_game` (~5236) e `_voltar_para_cidade` (~10996)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha.** Adicionar bloco `[12]`:

```python
    # [12] overlay no start + checkpoint na cidade
    print("\n[12] Overlay e checkpoint")
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    try:
        r = GameRoom("TST2")
        async def _noop(*a, **k): pass
        r.broadcast = _noop; r.broadcast_city_state = _noop; r.send_to = _noop
        r.gm_say = _noop; r._gerar_loja_pergaminhos = lambda: None
        r._cancelar_timer_turno = lambda: None
        sg = S.create_savegame("Jogo", "ricardo", "campaign", "elara.json", False)
        # ficha salva com ouro alto para o warrior
        base = S.snapshot_character(S.make_player("x", "x", "warrior", 0))
        base["gold"] = 777; base["level"] = 4
        sg["members"]["joao"] = {"class_id": "warrior"}
        sg["characters"]["warrior"] = base
        sg["campaign_phase"] = 2
        S.write_savegame(sg)
        r.savegame_id = sg["id"]; r.savegame = sg
        r.campaign_phase = 2
        # lobby: joao(warrior) presente; maria(mage) AUSENTE
        r.players = {"j1": {"id": "j1", "name": "Joao", "class_id": "warrior", "connected": True, "slot": 0}}
        r.account_by_pid = {"j1": "joao"}
        r.host_pid = "j1"
        import asyncio as _aio
        _aio.get_event_loop().run_until_complete(r.start_game("j1"))
        check("overlay restaurou ouro salvo", r.players["j1"]["gold"] == 777)
        check("overlay restaurou nível salvo", r.players["j1"]["level"] == 4)
        # progride e volta à cidade → checkpoint grava a ficha atual
        r.players["j1"]["gold"] = 1234
        _aio.get_event_loop().run_until_complete(r._voltar_para_cidade())
        disco = S.load_savegame(sg["id"])
        check("checkpoint gravou ouro atual", disco["characters"]["warrior"]["gold"] == 1234)
        check("checkpoint preservou ausente", "mage" not in disco["characters"])
        check("checkpoint gravou fase", disco["campaign_phase"] == 2)
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (overlay/checkpoint ainda não existem; ouro sai o default da classe).

- [ ] **Step 3a: Overlay no `start_game`.** Localizar o laço que constrói os jogadores:

```python
        for slot, (pid2, p) in enumerate(heroes.items()):
            novo = make_player(pid2, p["name"], p["class_id"], slot)
            novo["magias_conhecidas"] = list(p.get("magias_conhecidas", []))
            apply_guild_save(novo)   # carrega compras/equip persistidos do personagem
            full_players[pid2] = novo
```
Substituir por (quando há savegame, restaura a ficha salva; senão mantém o comportamento antigo com `apply_guild_save`):

```python
        for slot, (pid2, p) in enumerate(heroes.items()):
            novo = make_player(pid2, p["name"], p["class_id"], slot)
            novo["magias_conhecidas"] = list(p.get("magias_conhecidas", []))
            if self.savegame is not None:
                snap = (self.savegame.get("characters", {}) or {}).get(p["class_id"])
                if snap:
                    restore_character(novo, snap)   # sobrepõe a ficha salva
                # sem snap (não deveria ocorrer — o bind cria a ficha): fica
                # a ficha FRESCA. NÃO cai no apply_guild_save global, que
                # reintroduziria o vazamento entre jogos que a Fase 1 eliminou.
            else:
                apply_guild_save(novo)   # jogo sem savegame (fluxo antigo)
            full_players[pid2] = novo
```
E logo após `self.campaign_phase` já ter sido definido no lobby: garantir que a fase venha do savegame. Após `self.players = full_players` no `start_game`, acrescentar:

```python
        if self.savegame is not None:
            self.campaign_phase = self.savegame.get("campaign_phase", 0)
```

- [ ] **Step 3b: Checkpoint em `_voltar_para_cidade`.** Adicionar um helper e chamá-lo. No fim de `_voltar_para_cidade`, imediatamente após `await self.broadcast_city_state()`, acrescentar:

```python
        self._checkpoint_savegame()
```
E definir o helper (logo após `_voltar_para_cidade`):

```python
    def _checkpoint_savegame(self):
        """Grava a ficha durável dos heróis PRESENTES + a fase atual no savegame.
        Ausentes ficam intocados. No-op se a sala não tem savegame."""
        if self.savegame is None:
            return
        chars = self.savegame.setdefault("characters", {})
        for p in self.players.values():
            if p.get("is_master") or not p.get("class_id"):
                continue
            chars[p["class_id"]] = snapshot_character(p)
        self.savegame["campaign_phase"] = self.campaign_phase
        write_savegame(self.savegame)
```

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → [1]–[12] passam.

- [ ] **Step 5: Regressão.** `python tools/test_guilda.py`, `python tools/test_modo_mestre.py` → verdes.

- [ ] **Step 6: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): overlay no start_game + checkpoint na cidade"
```

---

## Task 5: Handler `load_savegame` (retomar) + trava de sessão-única

**Files:**
- Modify: `server.py` — `handler()`: threading do `account` em `create_room`/`join_room`, novo `load_savegame`, liberação de `SAVEGAMES_IN_USE` no `finally`.
- Test: `tools/test_savegames.py` (helper puro `try_open_savegame_room`)

Para testar sem WebSocket, a lógica de abrir a sala fica num helper `try_open_savegame_room(account, sid, rooms)` que valida (logado, savegame existe, membro/dono/mestre, não em uso), cria a `GameRoom`, seta `mode`/`campaign`/`campaign_phase` do savegame e marca `SAVEGAMES_IN_USE`. O handler só faz I/O de socket + `add_player`.

- [ ] **Step 1: Escrever o teste que falha.** Adicionar bloco `[13]`:

```python
    # [13] retomar savegame (helper puro)
    print("\n[13] Retomar savegame")
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    S.SAVEGAMES_IN_USE.clear()
    try:
        sg = S.create_savegame("Jogo", "ricardo", "campaign", "elara.json", True)
        sg["members"]["joao"] = {"class_id": "warrior"}; S.write_savegame(sg)
        rooms = {}
        room, e = S.try_open_savegame_room("ricardo", sg["id"], rooms)
        check("abre sala para o dono", room is not None and e is None)
        check("sala ligada ao savegame", room.savegame_id == sg["id"] and room.savegame is not None)
        check("herda modo/campanha/fase", room.mode == "campaign" and room.selected_campaign == "elara.json")
        check("marca SAVEGAMES_IN_USE", S.SAVEGAMES_IN_USE.get(sg["id"]) == room.code)
        # já em uso → recusa 2ª abertura
        room2, e2 = S.try_open_savegame_room("joao", sg["id"], rooms)
        check("recusa 2ª sessão do mesmo savegame", room2 is None and "uso" in (e2 or "").lower())
        # estranho (não-membro) → recusa
        room3, e3 = S.try_open_savegame_room("estranho", sg["id"], rooms)
        check("recusa não-membro", room3 is None)
        # sem login → recusa
        room4, e4 = S.try_open_savegame_room(None, sg["id"], rooms)
        check("recusa sem login", room4 is None)
    finally:
        S.SAVEGAMES_DIR = olds; S.SAVEGAMES_IN_USE.clear()
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha.** `python tools/test_savegames.py` → FAIL (`no attribute 'try_open_savegame_room'`).

- [ ] **Step 3a: Implementar o helper.** No bloco de persistência (após `restore_character`), inserir. Note que `make_code`/`GameRoom` estão definidos MAIS ABAIXO no arquivo; como Python resolve nomes em tempo de chamada, referenciá-los dentro da função é seguro:

```python
def _conta_participa(sg, conta):
    return bool(sg) and (sg.get("owner") == conta
                         or conta in (sg.get("members") or {})
                         or sg.get("master_account") == conta)

def try_open_savegame_room(account, sid, rooms):
    """Abre uma GameRoom retomando um savegame. Retorna (room, None) ou (None, erro)."""
    if not account:
        return None, "Você precisa estar logado."
    sg = load_savegame(sid)
    if not sg:
        return None, "Jogo salvo não encontrado."
    if not _conta_participa(sg, account):
        return None, "Você não faz parte deste jogo."
    if sid in SAVEGAMES_IN_USE:
        return None, "Este jogo já está em uso em outra sessão."
    code = make_code()
    room = GameRoom(code)
    rooms[code] = room
    room.savegame_id = sid
    room.savegame = sg
    room.campaign_phase = sg.get("campaign_phase", 0)
    if sg.get("mode") == "campaign" and sg.get("campaign_file"):
        defn = carregar_campanha(sg["campaign_file"])
        if defn is not None:
            room.mode = "campaign"; room.campaign = defn
            room.selected_campaign = sg["campaign_file"]
    SAVEGAMES_IN_USE[sid] = code
    return room, None
```

- [ ] **Step 3b: Handler `load_savegame` + threading da conta.** No `handler()`, no `create_room`, passar a conta ao `add_player`. Localizar:

```python
                if t == "create_room":
                    name = (msg.get("name") or "Herói")[:20]
                    code = make_code()
                    room = GameRoom(code)
                    rooms[code] = room
                    await room.add_player(ws, pid, name)
```
Trocar a última linha por:

```python
                    await room.add_player(ws, pid, name, account["name"])
```
No `join_room`, localizar `ok = await room.add_player(ws, pid, name)` e trocar por:

```python
                    ok = await room.add_player(ws, pid, name, account["name"])
```
Adicionar o handler `load_savegame` junto dos handlers globais (após `delete_savegame`, antes de `create_room`):

```python
                if t == "load_savegame":
                    novo, e = try_open_savegame_room(account["name"], msg.get("id"), rooms)
                    if novo:
                        room = novo
                        nome = account["name"] or (msg.get("name") or "Herói")[:20]
                        await room.add_player(ws, pid, nome, account["name"])
                    else:
                        await err(e)
                    continue
```

- [ ] **Step 3c: Liberar a trava no teardown.** No `finally` do `handler()`, dentro de `if room:`, após `room.connections.pop(pid, None)`, acrescentar a liberação quando a sala esvazia. Localizar o `if room:` e adicionar, ao final do bloco `if room:` (depois dos ramos de lobby/jogo):

```python
            if room.savegame_id and not room.connections:
                SAVEGAMES_IN_USE.pop(room.savegame_id, None)
```

- [ ] **Step 4: Rodar e confirmar que passa.** `python tools/test_savegames.py` → [1]–[13] passam.

- [ ] **Step 5: `ast.parse` + regressão.**
```bash
python -c "import ast; ast.parse(open('server.py', encoding='utf-8').read()); print('OK')"
python tools/test_savegames.py
python tools/test_guilda.py
python tools/test_modo_mestre.py
```
Todos verdes / OK.

- [ ] **Step 6: Commit.**
```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): handler load_savegame (retomar) + trava SAVEGAMES_IN_USE + conta na sala"
```

---

## Self-Review (Fase 2)

- **Cobertura do spec:** snapshot/restore (Task 1), sala↔savegame+conta (Task 2), bind no lobby (Task 3), overlay+checkpoint (Task 4), retomar+trava (Task 5). Presença parcial: coberta pelo checkpoint que só grava presentes e pelo overlay que só monta presentes. ✔
- **Sem placeholders:** todo passo com código real e comando/resultado esperado. ✔
- **Consistência de tipos/nomes:** `_DURABLE_FIELDS`, `snapshot_character`, `restore_character`, `savegame_id`, `savegame`, `account_by_pid`, `_checkpoint_savegame`, `try_open_savegame_room`, `_conta_participa`, `SAVEGAMES_IN_USE`, `account["name"]` usados consistentes entre as tasks e com a Fase 1. ✔
- **Byte-identidade sem savegame:** `select_class`/`start_game`/`_voltar_para_cidade` só mudam quando `self.savegame is not None`; `add_player` ganhou parâmetro OPCIONAL. Fluxo antigo intacto (garantido pela regressão guilda/mestre em cada task). ✔

## Fora de escopo (Fase 3 — próximo plano)

- Tela de login (apelido+PIN) no cliente.
- Home "Novo jogo" × "Continuar jogo" (consumir `savegames_list`, disparar `create_savegame`/`load_savegame`).
- Lobby: mostrar conta↔personagem e auto-vínculo (desabilitar troca de classe de membros já vinculados).
- Senders em `src/gameState.js`.
