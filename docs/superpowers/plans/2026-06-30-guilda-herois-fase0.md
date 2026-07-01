# Guilda dos Heróis — Fase 0 (Fundação) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir a fundação da Guilda dos Heróis — prédio na cidade, catálogo declarativo, compra, persistência por personagem (save em arquivo + trava de "em uso"), 4º slot de técnica, motor de recarga — validada ponta-a-ponta pela técnica de referência **Brutalidade**.

**Architecture:** Servidor autoritativo (`server.py`): catálogo declarativo `GUILD_CATALOG` (estilo `GRIMORIO`/`DECOR_TYPES`), campos novos no jogador, camada de save em `saves/<class_id>.json`, trava global `CHARACTERS_IN_USE`, handlers `guild_buy`/`guild_equip`/`usar_tecnica`, recarga reusando `self.round_num`. Cliente (`game.js` + `src/gameState.js`): painel da Guilda no hotspot `guilda`, slot de equipar na ficha da cidade, 4º botão de técnica no HUD. Sem MP; custo em fome/sede via caminho existente.

**Tech Stack:** Python 3 + `websockets` (servidor); Vanilla JS + Three.js r128 (cliente). Testes no harness caseiro do projeto (`tools/test_*.py`, função `main()` async + `check()`, rodado da raiz), **não** pytest.

**Spec:** `docs/superpowers/specs/2026-06-30-guilda-herois-fase0-design.md`

---

## Mapa de arquivos

| Arquivo | Papel nesta fase |
|---|---|
| `server.py` | Catálogo, modelo de dados, save/load, trava, handlers, recarga, efeito de Brutalidade, blocos no `city_state`/`game_state`, dispatch de mensagens. |
| `saves/` (nova pasta) | 1 JSON por personagem (`warrior.json`, `mage.json`, …). Criada em runtime na 1ª gravação. |
| `game.js` | Painel da Guilda (hotspot), slot de equipar na ficha, 4º botão de técnica no HUD, leitura do bloco `guild`. |
| `src/gameState.js` | Getters do bloco `guild` (owned/equip/catálogo) e dos cooldowns; senders `guildBuy`/`guildEquip`/`usarTecnica`. |
| `tools/test_guilda.py` (novo) | Testes de servidor: save round-trip, catálogo, trava, compra, equipar, ativação+recarga, reset na cidade, dano +2. |
| `CLAUDE.md` | Documentar protocolo novo, a Guilda e a implicação da trava. |
| `.gitignore` | Ignorar `saves/` (dados de runtime, não versionar). |

**Convenção de teste do projeto** (seguir em `tools/test_guilda.py`):
```python
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

def setup(phase="city"):
    r = GameRoom("TEST")
    errs = []; calls = {"city": 0, "push": 0}
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    async def cap_city(*a, **k): calls["city"] += 1
    async def cap_push(*a, **k): calls["push"] += 1
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = cap_city; r.push_state = cap_push; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r._calls = calls
    return r
```

> **Isolamento dos testes de save:** os testes de persistência devem usar uma pasta temporária, **não** a `saves/` real. Cada teste que grava seta `S.GUILD_SAVE_DIR = <tmp>` antes e restaura depois (ver Task 1). A trava `S.CHARACTERS_IN_USE` deve ser limpa (`S.CHARACTERS_IN_USE.clear()`) no início de cada teste que a exercita.

---

## Task 1: Modelo de dados do jogador + camada de save/load

**Files:**
- Modify: `server.py` — `make_player` (~2891, dentro do dict retornado) e novo bloco de helpers de save (inserir logo antes de `CLASSES = {` em ~205, junto das constantes de topo).
- Test: `tools/test_guilda.py` (novo).

- [ ] **Step 1: Escrever o teste que falha (save round-trip)**

Criar `tools/test_guilda.py` com o cabeçalho da convenção acima e este primeiro bloco em `main()`:

```python
async def main():
    import tempfile, shutil
    S.CHARACTERS_IN_USE.clear()

    # [1] make_player tem os campos da guilda
    print("\n[1] Campos da guilda no make_player")
    p = make_player("p1", "Victor", "warrior", 0)
    check("guild_owned.especializacoes vazio", p["guild_owned"]["especializacoes"] == [])
    check("guild_owned.tecnicas vazio", p["guild_owned"]["tecnicas"] == [])
    check("guild_equip.tecnica None", p["guild_equip"]["tecnica"] is None)
    check("technique_cooldowns vazio", p["technique_cooldowns"] == {})

    # [2] save round-trip em pasta temporária
    print("\n[2] Save round-trip")
    tmp = tempfile.mkdtemp()
    old_dir = S.GUILD_SAVE_DIR
    S.GUILD_SAVE_DIR = tmp
    try:
        p["guild_owned"]["tecnicas"] = ["brutalidade"]
        p["guild_equip"]["tecnica"] = "brutalidade"
        S.write_guild_save(p)
        loaded = S.load_guild_save("warrior")
        check("carregou tecnicas", loaded["tecnicas"] == ["brutalidade"])
        check("carregou equip.tecnica", loaded["equip"]["tecnica"] == "brutalidade")
        # ausente → vazio
        check("classe sem save → vazio", S.load_guild_save("mage")["tecnicas"] == [])
        # corrompido → vazio, sem crash
        with open(os.path.join(tmp, "rogue.json"), "w", encoding="utf-8") as f:
            f.write("{lixo}")
        check("save corrompido → vazio", S.load_guild_save("rogue")["tecnicas"] == [])
        # apply popula um player
        q = make_player("p2", "Victor", "warrior", 0)
        S.apply_guild_save(q)
        check("apply_guild_save popula", q["guild_owned"]["tecnicas"] == ["brutalidade"]
              and q["guild_equip"]["tecnica"] == "brutalidade")
    finally:
        S.GUILD_SAVE_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_guilda.py`
Expected: erro (AttributeError: module 'server' has no attribute 'GUILD_SAVE_DIR' / 'write_guild_save').

- [ ] **Step 3: Adicionar os campos no `make_player`**

Em `server.py`, no dict retornado por `make_player` (logo após a linha `"skills": cls["skills"],`, ~2891), inserir:

```python
        # ── Guilda dos Heróis (Fase 0) ──────────────────────────────────────
        "guild_owned": {"especializacoes": [], "tecnicas": []},   # ids comprados (persistido)
        "guild_equip": {"tecnica": None, "tecnica_exclusiva": None},  # equipado (persistido)
        "technique_cooldowns": {},          # { tecnica_id: pronta_em_round } — runtime
        "tecnica_buff_dano_arma": 0,        # Brutalidade: +N dano de arma até fim do turno
```

- [ ] **Step 4: Adicionar as constantes e helpers de save**

Em `server.py`, logo antes de `CLASSES = {` (~205), inserir. (`os` e `json` já são importados no topo do arquivo — confirmar; se faltar, adicionar `import os, json`.)

```python
# ─── GUILDA DOS HERÓIS — persistência por personagem (Fase 0) ─────────────────
# Save por class_id (6 personagens fixos), global ao processo. Guarda só posse +
# equipar da guilda; ouro/HP/nível continuam por-sessão. Ver spec Fase 0 §5.
GUILD_SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")

# Trava global: personagem em uso não pode ser escolhido em outra sala.
CHARACTERS_IN_USE = {}   # class_id -> room code

def guild_save_path(class_id):
    return os.path.join(GUILD_SAVE_DIR, f"{class_id}.json")

def _guild_empty():
    return {"especializacoes": [], "tecnicas": [],
            "equip": {"tecnica": None, "tecnica_exclusiva": None}}

def load_guild_save(class_id):
    """Lê o save do personagem. Ausente/corrompido → estrutura vazia (sem crash)."""
    try:
        with open(guild_save_path(class_id), "r", encoding="utf-8") as f:
            data = json.load(f)
        eq = data.get("equip", {}) or {}
        return {
            "especializacoes": list(data.get("especializacoes", [])),
            "tecnicas": list(data.get("tecnicas", [])),
            "equip": {"tecnica": eq.get("tecnica"),
                      "tecnica_exclusiva": eq.get("tecnica_exclusiva")},
        }
    except FileNotFoundError:
        return _guild_empty()
    except (json.JSONDecodeError, OSError, ValueError) as e:
        print(f"[guild] save de {class_id} inválido ({e}); começando vazio")
        return _guild_empty()

def write_guild_save(player):
    """Grava guild_owned/guild_equip de forma atômica (.tmp + replace)."""
    class_id = player.get("class_id")
    if not class_id:
        return
    os.makedirs(GUILD_SAVE_DIR, exist_ok=True)
    data = {
        "class_id": class_id,
        "especializacoes": list(player["guild_owned"]["especializacoes"]),
        "tecnicas": list(player["guild_owned"]["tecnicas"]),
        "equip": {"tecnica": player["guild_equip"]["tecnica"],
                  "tecnica_exclusiva": player["guild_equip"]["tecnica_exclusiva"]},
    }
    path = guild_save_path(class_id)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def apply_guild_save(player):
    """Popula guild_owned/guild_equip do jogador a partir do save do personagem."""
    s = load_guild_save(player["class_id"])
    player["guild_owned"]["especializacoes"] = s["especializacoes"]
    player["guild_owned"]["tecnicas"] = s["tecnicas"]
    player["guild_equip"]["tecnica"] = s["equip"]["tecnica"]
    player["guild_equip"]["tecnica_exclusiva"] = s["equip"]["tecnica_exclusiva"]
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: blocos [1] e [2] com ✅; saída "N passaram, 0 falharam".

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): modelo de dados do jogador + camada de save/load"
```

---

## Task 2: Catálogo declarativo `GUILD_CATALOG` + Brutalidade + helpers

**Files:**
- Modify: `server.py` — inserir após os helpers de save da Task 1.
- Test: `tools/test_guilda.py`.

- [ ] **Step 1: Escrever o teste que falha (catálogo)**

Adicionar em `main()` (antes do bloco final de resumo):

```python
    # [3] Catálogo
    print("\n[3] GUILD_CATALOG")
    b = S.guild_item("brutalidade")
    check("brutalidade existe", b is not None)
    check("categoria tecnica", b["categoria"] == "tecnica")
    check("recarga 3", b["recarga_rodadas"] == 3)
    check("custo 2/2", b["custo_fome"] == 2 and b["custo_sede"] == 2)
    itens_w = S.guild_items_for_class("warrior")
    check("brutalidade aplicável a warrior", any(i["id"] == "brutalidade" for i in itens_w))
    check("item None → não existe", S.guild_item("nao_existe") is None)
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_guilda.py`
Expected: bloco [3] falha (`guild_item` inexistente).

- [ ] **Step 3: Implementar o catálogo e helpers**

Em `server.py`, após `apply_guild_save`, inserir:

```python
# ─── GUILDA DOS HERÓIS — catálogo declarativo (Fase 0) ────────────────────────
# Estilo GRIMORIO/DECOR_TYPES. categoria: "tecnica" | "especializacao".
# classe: None = todas; ou class_id. exclusiva: técnica exclusiva Mago/Clérigo.
# efeito: descrito por dados; casos complexos usam {"tipo":"hook","handler":...}.
GUILD_CATALOG = {
    "brutalidade": {
        "id": "brutalidade", "categoria": "tecnica", "classe": None,
        "linha": None, "nivel": None, "requer": None, "exclusiva": False,
        "preco": 120, "custo_fome": 2, "custo_sede": 2, "recarga_rodadas": 3,
        "nome": "Brutalidade", "icon": "🪓",
        "desc": "Até o fim do turno, ataques físicos com arma causam +2 de dano.",
        "efeito": {"tipo": "buff_turno", "bonus_dano_arma": 2},
    },
    # Fases 1-2 acrescentam aqui.
}

def guild_item(item_id):
    return GUILD_CATALOG.get(item_id)

def guild_items_for_class(class_id):
    """Itens do catálogo disponíveis para uma classe (cópias para envio)."""
    return [dict(v) for v in GUILD_CATALOG.values()
            if v["classe"] is None or v["classe"] == class_id]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: bloco [3] ✅; 0 falhas.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): catalogo declarativo GUILD_CATALOG + Brutalidade"
```

---

## Task 3: Trava de "personagem em uso" + carga do save ao construir o jogador

**Files:**
- Modify: `server.py` — `select_class` (~3303), `start_game` (~3431, após `make_player`), `handle_disconnect_em_jogo` (~4108, no fim), e o bloco `finally` do dispatch (~13281, caso lobby pop).
- Test: `tools/test_guilda.py`.

- [ ] **Step 1: Escrever o teste que falha (trava + carga)**

Adicionar em `main()`:

```python
    # [4] Trava de personagem em uso
    print("\n[4] Trava de em-uso")
    S.CHARACTERS_IN_USE.clear()
    r1 = setup("lobby")
    r1.players["a"] = {"id": "a", "class_id": None}
    await r1.select_class("a", "mage")
    check("sala1 escolheu mage", r1.players["a"]["class_id"] == "mage")
    check("mage travado p/ TEST", S.CHARACTERS_IN_USE.get("mage") == "TEST")
    r2 = GameRoom("OUTRA")
    r2._errs = []
    async def cap2(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r2._errs.append(msg["msg"])
    r2.send_to = cap2
    async def noop(*a, **k): pass
    r2.broadcast_lobby = noop
    r2.players["b"] = {"id": "b", "class_id": None}
    await r2.select_class("b", "mage")
    check("sala2 recusada (mage em uso)", r2.players["b"]["class_id"] is None and r2._errs)
    # release: helper libera as travas da sala
    r1.release_character("a")
    check("release liberou mage", "mage" not in S.CHARACTERS_IN_USE)

    # [5] Carga do save ao iniciar (apply_guild_save chamado no start)
    print("\n[5] start_game carrega save")
    import tempfile, shutil
    tmp = tempfile.mkdtemp(); old = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp
    S.CHARACTERS_IN_USE.clear()
    try:
        seed = make_player("x", "Victor", "warrior", 0)
        seed["guild_owned"]["tecnicas"] = ["brutalidade"]
        S.write_guild_save(seed)
        r = setup("lobby")
        r.broadcast = noop
        r.players["a"] = {"id": "a", "name": "Victor", "class_id": "warrior", "ready": True}
        r.host_pid = "a"
        await r.start_game("a")
        check("save carregado no start (owned)",
              r.players["a"]["guild_owned"]["tecnicas"] == ["brutalidade"])
    finally:
        S.GUILD_SAVE_DIR = old; shutil.rmtree(tmp, ignore_errors=True); S.CHARACTERS_IN_USE.clear()
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_guilda.py`
Expected: bloco [4]/[5] falha (`release_character` inexistente; save não carregado).

- [ ] **Step 3: Implementar a trava no `select_class`**

Substituir o corpo de `select_class` (server.py:3303) por:

```python
    async def select_class(self, pid, cls_id):
        if cls_id not in CLASSES:
            return
        # Não tomado na sala
        taken = [p["class_id"] for p in self.players.values() if p["id"] != pid]
        if cls_id in taken:
            await self.send_to(pid, {"type": "error", "msg": "Classe já escolhida por outro jogador."})
            return
        # Trava global: personagem em uso em OUTRA sala
        dono = CHARACTERS_IN_USE.get(cls_id)
        if dono and dono != self.code:
            await self.send_to(pid, {"type": "error",
                "msg": f"{CLASSES[cls_id]['name']} já está em uso em outra sala."})
            return
        # Libera o personagem anterior deste jogador (se trocou de classe)
        prev = self.players[pid].get("class_id")
        if prev and prev != cls_id and CHARACTERS_IN_USE.get(prev) == self.code:
            del CHARACTERS_IN_USE[prev]
        CHARACTERS_IN_USE[cls_id] = self.code
        self.players[pid]["class_id"] = cls_id
        self.players[pid]["ready"] = True
        await self.broadcast_lobby()
```

- [ ] **Step 4: Adicionar o helper de liberação e chamá-lo na desconexão**

Adicionar como método de `GameRoom` (perto de `handle_disconnect_em_jogo`):

```python
    def release_character(self, pid):
        """Libera a trava do personagem deste jogador, se pertencer a esta sala."""
        p = self.players.get(pid)
        cls = p.get("class_id") if p else None
        if cls and CHARACTERS_IN_USE.get(cls) == self.code:
            del CHARACTERS_IN_USE[cls]

    def _release_all_locks(self):
        """Libera todas as travas desta sala (sala esvaziou)."""
        for cid in [c for c, code in CHARACTERS_IN_USE.items() if code == self.code]:
            del CHARACTERS_IN_USE[cid]
```

No fim de `handle_disconnect_em_jogo` (após o bloco `if self.phase == "city": ...`, ~4108), inserir — se ninguém mais está conectado, libera as travas:

```python
        if not any(q.get("connected") for q in self.players.values()):
            self._release_all_locks()
```

No bloco `finally` do dispatch (server.py:13281-13282), no ramo do lobby, liberar antes de remover:

```python
            if pid in room.players and room.phase == "lobby":
                room.release_character(pid)   # libera a trava do personagem
                room.players.pop(pid, None)
```

- [ ] **Step 5: Carregar o save no `start_game`**

Em `start_game` (server.py:3431), logo após `novo = make_player(...)` e a cópia de `magias_conhecidas`, inserir:

```python
            apply_guild_save(novo)   # carrega compras/equip persistidos do personagem
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: blocos [4] e [5] ✅; 0 falhas.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): trava de personagem em uso + carga do save no start_game"
```

---

## Task 4: `handle_guild_buy` + bloco `guild` no `city_state` + dispatch

**Files:**
- Modify: `server.py` — novo handler perto de `handle_shop_buy` (~3484); bloco no `broadcast_city_state` (~3451); dispatch (~3092, junto de `select_class`).
- Test: `tools/test_guilda.py`.

- [ ] **Step 1: Escrever o teste que falha (compra)**

Adicionar em `main()`:

```python
    # [6] Compra
    print("\n[6] handle_guild_buy")
    import tempfile, shutil
    tmp = tempfile.mkdtemp(); old = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp
    try:
        r = setup("city")
        w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
        w["gold"] = 200
        await r.handle_guild_buy("p1", "brutalidade")
        check("comprou brutalidade", "brutalidade" in w["guild_owned"]["tecnicas"])
        check("debitou ouro (200-120)", w["gold"] == 80)
        check("persistiu", "brutalidade" in S.load_guild_save("warrior")["tecnicas"])
        # comprar de novo → recusa (já possui)
        n0 = len(w["guild_owned"]["tecnicas"])
        await r.handle_guild_buy("p1", "brutalidade")
        check("não duplica compra", len(w["guild_owned"]["tecnicas"]) == n0)
        # ouro insuficiente
        r2 = setup("city"); w2 = make_player("p2","Victor","warrior",0); r2.players["p2"]=w2
        w2["gold"] = 10
        await r2.handle_guild_buy("p2", "brutalidade")
        check("recusa sem ouro", "brutalidade" not in w2["guild_owned"]["tecnicas"] and r2._errs)
        # item inexistente
        await r2.handle_guild_buy("p2", "nao_existe")
        check("recusa item inexistente", len(r2._errs) >= 2)
    finally:
        S.GUILD_SAVE_DIR = old; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_guilda.py`
Expected: bloco [6] falha (`handle_guild_buy` inexistente).

- [ ] **Step 3: Implementar `handle_guild_buy`**

Adicionar em `GameRoom` perto de `handle_shop_buy`:

```python
    async def handle_guild_buy(self, pid, item_id):
        if self.phase != "city":
            return
        p = self.players.get(pid)
        if not p:
            return
        item = guild_item(item_id)
        if not item:
            await self.send_to(pid, {"type": "error", "msg": "Item da guilda desconhecido."})
            return
        # Classe compatível
        if item["classe"] is not None and item["classe"] != p.get("class_id"):
            await self.send_to(pid, {"type": "error", "msg": "Este aprimoramento não é da sua classe."})
            return
        cat = item["categoria"]   # "tecnica" | "especializacao"
        owned = p["guild_owned"]["tecnicas"] if cat == "tecnica" else p["guild_owned"]["especializacoes"]
        if item_id in owned:
            await self.send_to(pid, {"type": "error", "msg": "Você já possui isto."})
            return
        # Pré-requisito
        req = item.get("requer")
        if req and req not in owned:
            nome_req = (guild_item(req) or {}).get("nome", req)
            await self.send_to(pid, {"type": "error", "msg": f"Requer antes: {nome_req}."})
            return
        # Ouro
        if p.get("gold", 0) < item["preco"]:
            await self.send_to(pid, {"type": "error", "msg": "Ouro insuficiente."})
            return
        p["gold"] -= item["preco"]
        owned.append(item_id)
        write_guild_save(p)
        await self.broadcast_city_state()
```

- [ ] **Step 4: Adicionar o bloco `guild` no `broadcast_city_state`**

Em `broadcast_city_state` (server.py:3445), adicionar a chave `"guild"` ao dict enviado (após `"shops": {...}`):

```python
            "guild": {
                "catalog": list(GUILD_CATALOG.values()),
                "players": {
                    pid: {"owned": pp["guild_owned"], "equip": pp["guild_equip"]}
                    for pid, pp in self.players.items()
                },
            },
```

- [ ] **Step 5: Registrar o dispatch**

No roteador de mensagens (server.py, junto de `elif t == "select_class":`), adicionar:

```python
                elif t == "guild_buy":
                    if room: await room.handle_guild_buy(pid, msg.get("item_id"))
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: bloco [6] ✅; 0 falhas.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): handle_guild_buy + bloco guild no city_state"
```

---

## Task 5: `handle_guild_equip` (regras de slot) + dispatch

**Files:**
- Modify: `server.py` — novo handler perto de `handle_guild_buy`; dispatch.
- Test: `tools/test_guilda.py`.

- [ ] **Step 1: Escrever o teste que falha (equipar)**

Adicionar em `main()`:

```python
    # [7] Equipar
    print("\n[7] handle_guild_equip")
    tmp = tempfile.mkdtemp(); old = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp
    try:
        r = setup("city")
        w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
        w["guild_owned"]["tecnicas"] = ["brutalidade"]
        await r.handle_guild_equip("p1", "tecnica", "brutalidade")
        check("equipou brutalidade", w["guild_equip"]["tecnica"] == "brutalidade")
        check("persistiu equip", S.load_guild_save("warrior")["equip"]["tecnica"] == "brutalidade")
        await r.handle_guild_equip("p1", "tecnica", None)
        check("desequipou", w["guild_equip"]["tecnica"] is None)
        # não possui → recusa
        await r.handle_guild_equip("p1", "tecnica", "brutalidade_fantasma")
        check("recusa técnica não possuída", w["guild_equip"]["tecnica"] is None and r._errs)
        # warrior não tem slot exclusivo
        r._errs = []
        await r.handle_guild_equip("p1", "tecnica_exclusiva", "brutalidade")
        check("warrior recusa slot exclusivo", w["guild_equip"]["tecnica_exclusiva"] is None and r._errs)
        # mago pode ter os 2 slots (usando brutalidade como genérica; exclusiva exige exclusiva:true)
        rm = setup("city"); m = make_player("m","Pedro","mage",0); rm.players["m"] = m
        m["guild_owned"]["tecnicas"] = ["brutalidade"]
        await rm.handle_guild_equip("m", "tecnica", "brutalidade")
        check("mago equipa genérica", m["guild_equip"]["tecnica"] == "brutalidade")
        await rm.handle_guild_equip("m", "tecnica_exclusiva", "brutalidade")
        check("exclusiva recusa técnica não-exclusiva", m["guild_equip"]["tecnica_exclusiva"] is None and rm._errs)
    finally:
        S.GUILD_SAVE_DIR = old; shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_guilda.py`
Expected: bloco [7] falha (`handle_guild_equip` inexistente).

- [ ] **Step 3: Implementar `handle_guild_equip`**

```python
    async def handle_guild_equip(self, pid, slot, item_id):
        if self.phase != "city":
            await self.send_to(pid, {"type": "error", "msg": "Só é possível equipar técnicas na cidade."})
            return
        p = self.players.get(pid)
        if not p:
            return
        if slot not in ("tecnica", "tecnica_exclusiva"):
            await self.send_to(pid, {"type": "error", "msg": "Slot de técnica inválido."})
            return
        # Slot exclusivo só para mago/clérigo
        if slot == "tecnica_exclusiva" and p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não tem slot de técnica exclusiva."})
            return
        if item_id is None:   # desequipar
            p["guild_equip"][slot] = None
            write_guild_save(p)
            await self.broadcast_city_state()
            return
        item = guild_item(item_id)
        if not item or item["categoria"] != "tecnica":
            await self.send_to(pid, {"type": "error", "msg": "Técnica desconhecida."})
            return
        if item_id not in p["guild_owned"]["tecnicas"]:
            await self.send_to(pid, {"type": "error", "msg": "Você não possui esta técnica."})
            return
        # Coerência exclusiva ↔ slot
        if slot == "tecnica_exclusiva" and not item.get("exclusiva"):
            await self.send_to(pid, {"type": "error", "msg": "Esta técnica não é exclusiva."})
            return
        if slot == "tecnica" and item.get("exclusiva"):
            await self.send_to(pid, {"type": "error", "msg": "Técnica exclusiva vai no slot exclusivo."})
            return
        p["guild_equip"][slot] = item_id
        write_guild_save(p)
        await self.broadcast_city_state()
```

- [ ] **Step 4: Registrar o dispatch**

```python
                elif t == "guild_equip":
                    if room: await room.handle_guild_equip(pid, msg.get("slot"), msg.get("item_id"))
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: bloco [7] ✅; 0 falhas.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): handle_guild_equip com regras de slot (mago/clerigo 2 slots)"
```

---

## Task 6: `handle_usar_tecnica` + motor de recarga + efeito Brutalidade + resets + `game_state`

**Files:**
- Modify: `server.py` — novo handler; leitura do buff no dano de `handle_attack` (~4708 e ~4724); reset do buff no fim do turno (~9856); reset de cooldowns em `_voltar_para_cidade` (~6521); bloco no `push_state`/`game_state`; dispatch.
- Test: `tools/test_guilda.py`.

> **Nota:** localizar o dict do `game_state`/`push_state`. Buscar onde `push_state` monta o payload por jogador (grep `"type": "game_state"`). Adicionar por jogador os campos `guild_equip` e `technique_cooldowns` (restante em rodadas). Se o `game_state` já serializa o player inteiro (`list(self.players.values())`), então `guild_equip`/`technique_cooldowns` já vão junto — nesse caso, converter cooldowns para "restante" no cliente. **Verificar** e escolher o caminho no Step 5.

- [ ] **Step 1: Escrever o teste que falha (ativação/recarga/dano)**

Adicionar em `main()`:

```python
    # [8] Usar técnica + recarga + reset
    print("\n[8] usar_tecnica + recarga")
    r = setup("playing")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    r.player_order = ["p1"]; r.turn_index = 0; r.round_num = 1
    w["guild_owned"]["tecnicas"] = ["brutalidade"]
    w["guild_equip"]["tecnica"] = "brutalidade"
    w["fome"] = 50; w["sede"] = 50
    await r.handle_usar_tecnica("p1", "brutalidade")
    check("buff de dano aplicado (+2)", w["tecnica_buff_dano_arma"] == 2)
    check("debitou fome/sede (2/2)", w["fome"] == 48 and w["sede"] == 48)
    check("entrou em recarga (round_num+3)", w["technique_cooldowns"]["brutalidade"] == 1 + 3)
    # reuso bloqueado na mesma rodada
    r._errs = []
    await r.handle_usar_tecnica("p1", "brutalidade")
    check("reuso bloqueado em recarga", r._errs)
    # avança rodadas → libera
    r.round_num = 4
    check("pronta em round 4 (>= pronta_em 4)", w["technique_cooldowns"]["brutalidade"] <= r.round_num)
    # volta à cidade zera cooldowns
    await r._voltar_para_cidade()
    check("cidade zera cooldowns", w["technique_cooldowns"] == {})

    # [9] Prontidão via helper
    print("\n[9] tecnica_restante")
    r.round_num = 1
    w["technique_cooldowns"] = {"brutalidade": 4}
    check("restante = 3", r.tecnica_restante(w, "brutalidade") == 3)
    w["technique_cooldowns"] = {}
    check("restante = 0 quando ausente", r.tecnica_restante(w, "brutalidade") == 0)
```

Adicionar também, no bloco [8] de ataque para provar o +2 de dano, um mini-teste do somatório — **como o cálculo está embutido em `handle_attack`, validamos o helper de bônus**:

```python
    # [10] Bônus de dano da técnica no cálculo
    print("\n[10] bônus de dano da técnica")
    w["tecnica_buff_dano_arma"] = 2
    check("helper soma +2", r._tecnica_bonus_dano(w) == 2)
    w["tecnica_buff_dano_arma"] = 0
    check("helper soma 0 sem buff", r._tecnica_bonus_dano(w) == 0)
```

- [ ] **Step 2: Rodar e confirmar falha**

Run: `python tools/test_guilda.py`
Expected: blocos [8]/[9]/[10] falham (handlers/helpers inexistentes).

- [ ] **Step 3: Implementar o motor de recarga + `handle_usar_tecnica` + helpers**

Adicionar em `GameRoom`:

```python
    def tecnica_restante(self, p, tid):
        pronta = p.get("technique_cooldowns", {}).get(tid)
        return max(0, pronta - self.round_num) if pronta else 0

    def _tecnica_bonus_dano(self, p):
        """+N de dano de arma concedido por técnica de turno (Brutalidade)."""
        return p.get("tecnica_buff_dano_arma", 0)

    async def handle_usar_tecnica(self, pid, tecnica_id, target_id=None):
        if self.phase != "playing":
            return
        p = self.players.get(pid)
        if not p or self.current_pid() != pid:
            await self.send_to(pid, {"type": "error", "msg": "Não é o seu turno."})
            return
        # Deve estar equipada em algum slot
        eq = p["guild_equip"]
        if tecnica_id not in (eq.get("tecnica"), eq.get("tecnica_exclusiva")):
            await self.send_to(pid, {"type": "error", "msg": "Técnica não equipada."})
            return
        item = guild_item(tecnica_id)
        if not item:
            return
        # Recarga
        if self.tecnica_restante(p, tecnica_id) > 0:
            await self.send_to(pid, {"type": "error",
                "msg": f"{item['nome']} em recarga ({self.tecnica_restante(p, tecnica_id)} rodadas)."})
            return
        # Fome/sede suficientes
        if p.get("fome", 0) < item["custo_fome"] or p.get("sede", 0) < item["custo_sede"]:
            await self.send_to(pid, {"type": "error", "msg": "Fome/sede insuficientes."})
            return
        # Aplica efeito
        ef = item.get("efeito", {})
        if ef.get("tipo") == "buff_turno":
            p["tecnica_buff_dano_arma"] = p.get("tecnica_buff_dano_arma", 0) + ef.get("bonus_dano_arma", 0)
        # (outros tipos/handlers chegam nas Fases 1-2)
        # Custo + recarga
        p["fome"] -= item["custo_fome"]
        p["sede"] -= item["custo_sede"]
        p["technique_cooldowns"][tecnica_id] = self.round_num + item["recarga_rodadas"]
        await self.gm_say(f"⚔️ **{p['name']}** ativa **{item['nome']}**!")
        await self.push_state()
```

- [ ] **Step 4: Ler o buff no cálculo de dano de `handle_attack`**

Em `handle_attack`, na linha do somatório do dano com arma (server.py:4708), incluir `+ self._tecnica_bonus_dano(p)`:

```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") - self._corrosao_arma_pen(p)
                              + self._tecnica_bonus_dano(p))
```

E no ramo desarmado (server.py:4724), idem:

```python
                    dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                              + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p))
```

- [ ] **Step 5: Resetar o buff no fim do turno e os cooldowns na cidade; incluir no `game_state`**

No reset de flags de fim de turno (server.py:~9856, junto de `p["skill_dobrar_dano"] = False`), adicionar:

```python
        p["tecnica_buff_dano_arma"] = 0
```

Em `_voltar_para_cidade` (server.py:~6521, dentro do `for pp in self.players.values():`), adicionar:

```python
            pp["technique_cooldowns"] = {}   # descanso na cidade → recarga total das técnicas
```

Para o `game_state`: **verificar** como `push_state` monta o payload (grep `"type": "game_state"`). Se ele envia o player inteiro (`self.players.values()`), então `guild_equip` e `technique_cooldowns` já viajam — o cliente calcula o restante com `pronta_em - round_num` usando `round` do estado. Confirmar que o `game_state` inclui `round_num` (grep `"round"`; server.py:12922 já envia `"round": self.round_num`). Nenhuma mudança extra necessária nesse caso. Se `push_state` fizer whitelist de campos, adicionar `guild_equip` e `technique_cooldowns` à whitelist.

- [ ] **Step 6: Registrar o dispatch**

```python
                elif t == "usar_tecnica":
                    if room: await room.handle_usar_tecnica(pid, msg.get("tecnica_id"), msg.get("target_id"))
```

- [ ] **Step 7: Rodar e confirmar que passa**

Run: `python tools/test_guilda.py`
Expected: blocos [8]/[9]/[10] ✅; 0 falhas.

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_guilda.py
git commit -m "feat(guilda): usar_tecnica + motor de recarga + efeito Brutalidade + resets"
```

---

## Task 7: Cliente — senders e getters do bloco `guild` (`gameState.js`)

**Files:**
- Modify: `src/gameState.js` — adicionar senders e getters; expor no objeto `GS`.

> Módulo de estado: **sem** DOM/THREE. Só estado + WebSocket + getters (regra de arquitetura do projeto).

- [ ] **Step 1: Adicionar senders**

Perto dos outros action senders (que usam `send({...})`), adicionar:

```javascript
  function guildBuy(itemId)          { send({ type: 'guild_buy',   item_id: itemId }); }
  function guildEquip(slot, itemId)  { send({ type: 'guild_equip', slot: slot, item_id: itemId }); }
  function usarTecnica(tid, targetId){ send({ type: 'usar_tecnica', tecnica_id: tid, target_id: targetId ?? null }); }
```

- [ ] **Step 2: Adicionar getters do bloco guild**

```javascript
  // ── Guilda dos Heróis (Fase 0) ──────────────────────────────────────────
  function guildCatalogFor(classId) {
    const g = (cityState && cityState.guild) || null;
    if (!g) return [];
    return (g.catalog || []).filter(i => i.classe == null || i.classe === classId);
  }
  function guildOwnedOf(pid) {
    const g = (cityState && cityState.guild) || null;
    return (g && g.players && g.players[pid] && g.players[pid].owned)
           || { especializacoes: [], tecnicas: [] };
  }
  function guildEquipOf(pid) {
    const g = (cityState && cityState.guild) || null;
    return (g && g.players && g.players[pid] && g.players[pid].equip)
           || { tecnica: null, tecnica_exclusiva: null };
  }
  // Recarga restante (em rodadas) de uma técnica, lido do game_state.
  function tecnicaRestante(player, tid) {
    const cds = (player && player.technique_cooldowns) || {};
    const pronta = cds[tid];
    const round = (gameState && gameState.round) || 1;
    return pronta ? Math.max(0, pronta - round) : 0;
  }
```

- [ ] **Step 3: Expor no objeto `GS`**

No `return { ... }` do módulo, adicionar: `guildBuy, guildEquip, usarTecnica, guildCatalogFor, guildOwnedOf, guildEquipOf, tecnicaRestante`.

- [ ] **Step 4: Verificação manual (fumaça de sintaxe)**

Run: `python -c "print('js ok')"` *(placeholder — não há linter JS no projeto)*. Abrir o console do navegador após subir o servidor (Task 10) e conferir `window.GS.guildCatalogFor` como função.

- [ ] **Step 5: Commit**

```bash
git add src/gameState.js
git commit -m "feat(guilda): senders e getters do bloco guild no gameState"
```

---

## Task 8: Cliente — painel da Guilda no hotspot (`game.js`)

**Files:**
- Modify: `game.js` — `_cityHotspotClick` (~1084); nova função `openGuild()`; ajustar rótulo do prédio em `_CTY_BLDGS` (~440, `action`).

- [ ] **Step 1: Trocar o toast pelo painel**

Em `_cityHotspotClick` (game.js:1086), trocar:

```javascript
  if(id === 'guilda'){ toast('⚔ Guilda dos Heróis — Missões em breve!','var(--gold)'); return; }
```
por:
```javascript
  if(id === 'guilda'){ openGuild(); return; }
```

E em `_CTY_BLDGS` (game.js:440), atualizar o texto de ação:
```javascript
  {id:'guilda',   name:'Guilda dos Heróis',  emoji:'⚔',action:'Comprar especializações e técnicas',
```

- [ ] **Step 2: Implementar `openGuild()`**

Adicionar perto de `openShop` (game.js:1263). Ler `myPid`/classe do estado da cidade; renderizar abas Especializações | Técnicas com itens de `GS.guildCatalogFor(classId)`, marcando possuídos (`GS.guildOwnedOf(myPid)`) e comprável (ouro suficiente e pré-requisito). Reusar o container/estilo de modal de loja existente (buscar como `openShop` monta o overlay e replicar). Botão comprar → `GS.guildBuy(item.id)`.

```javascript
function openGuild(){
  const cs = GS.getCityState ? GS.getCityState() : null;   // ver getter existente p/ cityState
  const me = (cs && cs.players || []).find(p => p.id === GS.myPid());
  if(!me){ toast('Guilda indisponível agora.','var(--danger)'); return; }
  const classId = me.class_id;
  const owned   = GS.guildOwnedOf(GS.myPid());
  const catalog = GS.guildCatalogFor(classId);
  // Monta overlay (reusar padrão de openShop): título "⚔ Guilda dos Heróis",
  // duas abas por item.categoria ('especializacao' | 'tecnica').
  // Para cada item: nome, icon, desc, preço; se técnica, custo fome/sede + recarga.
  // Estado: possuído (badge) | bloqueado (requer X) | comprável (botão).
  const tecnicas = catalog.filter(i => i.categoria === 'tecnica');
  const specs    = catalog.filter(i => i.categoria === 'especializacao');
  const itemRow = (i) => {
    const has = (i.categoria==='tecnica' ? owned.tecnicas : owned.especializacoes).includes(i.id);
    const reqOk = !i.requer || (i.categoria==='tecnica'?owned.tecnicas:owned.especializacoes).includes(i.requer);
    const podeComprar = !has && reqOk && (me.gold||0) >= i.preco;
    const custo = i.categoria==='tecnica'
      ? ` · 🍖${i.custo_fome} 💧${i.custo_sede} · ⏱️${i.recarga_rodadas}r` : '';
    const btn = has ? `<span class="guild-owned">Possuído ✓</span>`
      : (!reqOk ? `<span class="guild-locked">Requer ${i.requer}</span>`
      : `<button class="guild-buy" data-id="${i.id}" ${podeComprar?'':'disabled'}>Comprar 🪙${i.preco}</button>`);
    return `<div class="guild-item"><span class="gi-icon">${i.icon||'✨'}</span>
      <div class="gi-body"><b>${i.nome}</b><br><small>${i.desc}${custo}</small></div>${btn}</div>`;
  };
  // … inserir o overlay no DOM (padrão de openShop), com seções specs/tecnicas,
  // e ligar os cliques dos botões .guild-buy a GS.guildBuy(id).
}
```

> **Nota ao executor:** ler `openShop` (game.js:1263) por inteiro antes de escrever o overlay e **replicar o mesmo padrão** de criação/fechamento de modal para consistência visual. Confirmar o getter de `cityState` exposto (grep em `gameState.js` por `getCityState`/`cityState`); se não existir, adicioná-lo (retorna `cityState`) e expor em `GS`.

- [ ] **Step 3: Estilos**

Em `game.css`, adicionar classes `.guild-item`, `.gi-icon`, `.gi-body`, `.guild-buy`, `.guild-owned`, `.guild-locked` (espelhar o visual dos itens de loja existentes).

- [ ] **Step 4: Verificação manual**

Subir o servidor (Task 10), entrar na cidade, clicar na Guilda: painel abre, mostra Brutalidade como comprável; comprar debita ouro e vira "Possuído ✓" (o `city_state` re-broadcast atualiza o painel).

- [ ] **Step 5: Commit**

```bash
git add game.js game.css
git commit -m "feat(guilda): painel da Guilda no hotspot da cidade (compra)"
```

---

## Task 9: Cliente — slot de equipar na ficha + 4º botão de técnica no HUD

**Files:**
- Modify: `game.js` — `renderFichaCidadeBody` (~10381) para o slot de equipar; render do HUD em jogo (perto do loop de skills, ~9657) para o 4º botão.

- [ ] **Step 1: Slot de equipar na ficha da cidade**

Em `renderFichaCidadeBody` (game.js:10381), quando `editable` (é o próprio herói), adicionar seção "Técnica da Guilda". Listar as técnicas possuídas (`GS.guildOwnedOf(player.id).tecnicas`) como opções + "vazio"; a equipada vem de `GS.guildEquipOf(player.id)`. Mago/Clérigo mostram 2 selects (slot `tecnica` e `tecnica_exclusiva`). Trocar → `GS.guildEquip(slot, itemId|null)`.

```javascript
  // ── Técnica da Guilda (Fase 0) ──
  if (editable) {
    const owned = GS.guildOwnedOf(player.id).tecnicas || [];
    const eq    = GS.guildEquipOf(player.id);
    const nome  = id => { const c = GS.guildCatalogFor(player.class_id).find(x=>x.id===id); return c?c.nome:id; };
    const mkSelect = (slot, cur, filtro) => {
      const opts = ['<option value="">— vazio —</option>'].concat(
        owned.filter(filtro).map(id => `<option value="${id}" ${id===cur?'selected':''}>${nome(id)}</option>`));
      return `<select class="guild-equip-sel" data-slot="${slot}">${opts.join('')}</select>`;
    };
    const isEx = id => { const c = GS.guildCatalogFor(player.class_id).find(x=>x.id===id); return c && c.exclusiva; };
    let html = `<div class="ficha-sec"><h4>⚔️ Técnica da Guilda</h4>` +
               mkSelect('tecnica', eq.tecnica, id => !isEx(id));
    if (['mage','cleric'].includes(player.class_id))
      html += `<h4>✨ Técnica Exclusiva</h4>` + mkSelect('tecnica_exclusiva', eq.tecnica_exclusiva, id => isEx(id));
    html += `</div>`;
    // inserir html no corpo da ficha e ligar os <select>.onchange a
    // GS.guildEquip(slot, value || null).
  }
```

> **Nota ao executor:** ler `renderFichaCidadeBody` inteiro (game.js:10381) para inserir a seção no ponto certo do layout e ligar os handlers no mesmo estilo do resto da ficha.

- [ ] **Step 2: 4º botão de técnica no HUD em jogo**

No render do HUD do jogador (game.js, próximo ao loop `for(const sk of (me.skills || [])){` em ~9657), após os botões de habilidade-base, adicionar o(s) botão(ões) da técnica equipada, lendo de `GS.guildEquipOf(me.id)` e do catálogo. Estado desabilitado + rótulo "Xr" quando `GS.tecnicaRestante(me, tid) > 0`; senão clique → `GS.usarTecnica(tid)`.

```javascript
  // ── Técnica(s) da Guilda equipada(s) ──
  const _eq = GS.guildEquipOf(me.id);
  const _tecs = [_eq.tecnica, _eq.tecnica_exclusiva].filter(Boolean);
  for (const tid of _tecs) {
    const cat = GS.guildCatalogFor(me.class_id).find(x => x.id === tid);
    if (!cat) continue;
    const restante = GS.tecnicaRestante(me, tid);
    const btn = document.createElement('button');
    btn.className = 'skill-btn guild-tec' + (restante > 0 ? ' skill-cooldown' : '');
    btn.disabled = restante > 0 || !isMyTurn();   // usar o guard de turno existente
    btn.innerHTML = `${cat.icon||'⚔️'} ${cat.nome}` +
      (restante > 0 ? `<span class="cd">${restante}r</span>`
                    : `<span class="cost">🍖${cat.custo_fome} 💧${cat.custo_sede}</span>`);
    btn.onclick = () => GS.usarTecnica(tid);
    // anexar ao container das habilidades (mesmo pai dos skill-btn)
  }
```

> **Nota ao executor:** identificar o container/pai onde os `skill-btn` são anexados naquele trecho e usar o mesmo guard de "é meu turno" já empregado ali. Adicionar `.guild-tec`, `.skill-cooldown`, `.cd`, `.cost` no `game.css`.

- [ ] **Step 3: Verificação manual**

Servidor no ar (Task 10): comprar Brutalidade → equipar na ficha → entrar na masmorra → o 4º botão aparece → usar aplica +2 de dano no próximo ataque, debita 2/2 fome/sede e mostra "3r"; após 3 rodadas volta a ficar disponível; ao voltar à cidade a recarga zera.

- [ ] **Step 4: Commit**

```bash
git add game.js game.css
git commit -m "feat(guilda): slot de equipar na ficha + 4o botao de tecnica no HUD"
```

---

## Task 10: Verificação ponta-a-ponta + docs + .gitignore

**Files:**
- Modify: `.gitignore`, `CLAUDE.md`.

- [ ] **Step 1: Ignorar a pasta de saves**

Adicionar ao `.gitignore`:
```
# Saves da Guilda dos Heróis (dados de runtime, por personagem)
saves/
```

- [ ] **Step 2: Rodar a suíte de servidor**

Run: `python tools/test_guilda.py`
Expected: todos os blocos ✅; "0 falharam". Rodar também um smoke das suítes vizinhas para garantir não-regressão: `python tools/test_ficha_cidade.py` (deve continuar passando — `make_player` mudou).

- [ ] **Step 3: Smoke test in-app**

Subir o servidor: `python server.py` e abrir `http://localhost:8765/index.html`. Fluxo completo com 1 herói (Victor): iniciar → cidade → Guilda → comprar Brutalidade → ficha → equipar → entrar na masmorra → usar técnica → confirmar +2 de dano, custo 2/2, recarga "3r", liberação após 3 rodadas, e reset ao voltar à cidade. Reabrir o cliente e confirmar que a compra **persistiu** (Brutalidade continua "Possuído ✓" numa nova partida com Victor).

- [ ] **Step 4: Atualizar `CLAUDE.md`**

No protocolo (Client→Server), acrescentar `guild_buy`, `guild_equip`, `usar_tecnica`. Em Server→Client, notar o bloco `guild` no `city_state`. Adicionar um parágrafo curto sobre a Guilda (compra de especializações/técnicas; save por personagem em `saves/<class_id>.json`; **implicação da trava**: só um grupo joga cada personagem por vez no servidor; recarga zera na cidade).

- [ ] **Step 5: Commit**

```bash
git add .gitignore CLAUDE.md
git commit -m "docs(guilda): protocolo, secao da Guilda e .gitignore de saves"
```

---

## Self-review (cobertura do spec)

- **§1 escopo / §11 fronteiras** → Tasks 1-9 entregam só a fundação + Brutalidade; nenhuma habilidade-base é reformulada; nenhuma outra técnica é implementada. ✔
- **§2 modelo de dados** → Task 1 (campos no `make_player`). ✔
- **§3 catálogo declarativo** → Task 2. ✔
- **§4 persistência (save por personagem, atômico)** → Task 1 (write/load/apply) + carga no start (Task 3). ✔
- **§4 trava de em-uso** → Task 3. ✔
- **§5 motor de recarga (round_num, reset na cidade)** → Task 6. ✔
- **§6 protocolo (guild_buy/guild_equip/usar_tecnica; blocos guild)** → Tasks 4/5/6. ✔
- **§7 UI (prédio, equipar na ficha, 4º botão HUD)** → Tasks 8/9. ✔
- **§8 técnica de referência Brutalidade** → Tasks 2/6/9. ✔
- **§9 testes** → `tools/test_guilda.py` cobre save round-trip, catálogo, trava, compra, equipar (2 slots), ativação+recarga, reset na cidade, bônus de dano. ✔

**Consistência de nomes verificada:** `guild_owned`/`guild_equip`/`technique_cooldowns`/`tecnica_buff_dano_arma` (dados); `guild_item`/`guild_items_for_class`/`load_guild_save`/`write_guild_save`/`apply_guild_save`/`guild_save_path` (server helpers); `handle_guild_buy`/`handle_guild_equip`/`handle_usar_tecnica`/`tecnica_restante`/`_tecnica_bonus_dano`/`release_character`/`_release_all_locks` (métodos); `guildBuy`/`guildEquip`/`usarTecnica`/`guildCatalogFor`/`guildOwnedOf`/`guildEquipOf`/`tecnicaRestante` (cliente). Mensagens: `guild_buy`/`guild_equip`/`usar_tecnica`.

**Ponto a confirmar durante a Task 6 (Step 5):** se o `game_state` serializa o player inteiro (então `guild_equip`/`technique_cooldowns` já viajam) ou usa whitelist (aí adicionar os campos). O teste [8]/[9] não depende disso; o HUD (Task 9) depende — validar no smoke test.
```
