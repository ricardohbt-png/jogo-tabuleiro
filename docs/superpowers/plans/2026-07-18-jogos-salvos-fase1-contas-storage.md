# Jogos Salvos — Fase 1: Contas + Camada de Savegames + CRUD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir a camada de persistência (contas com apelido+PIN e jogos salvos em JSON) e os handlers WebSocket que não dependem de gameplay — sem ainda tocar no fluxo de partida.

**Architecture:** Funções puras de arquivo em `server.py` (espelhando o padrão tolerante do `load_guild_save` e a escrita atômica do `write_guild_save`), mais handlers de mensagem globais no `handler()` da conexão. Tudo testável por script isolado, sem cliente.

**Tech Stack:** Python 3.x, `websockets`, `hashlib.pbkdf2_hmac` para o PIN, JSON em disco, testes no estilo `tools/test_*.py` (script com `check(name, cond)`).

**Spec:** `docs/superpowers/specs/2026-07-18-jogos-salvos-campanhas-persistentes-design.md`

---

## Escopo desta fase

Entra: diretórios `accounts/` e `savegames/`; hash/verify de PIN; CRUD de conta e de savegame (funções puras); handlers `login`, `create_account`, `list_savegames`, `create_savegame`, `delete_savegame`; travas `SAVEGAMES_IN_USE`/`ACCOUNTS_ONLINE`; `.gitignore`.

**Fora desta fase** (vão para as Fases 2 e 3): `snapshot_character`/`restore_character`, checkpoints de gravação, `load_savegame` que abre lobby e faz o vínculo conta↔personagem, `restore` no `start_game`, e toda a UI do cliente. O handler `load_savegame` (retomar a partida) fica para a Fase 2 porque depende do vínculo.

## Estrutura de arquivos

- **Modificar `server.py`:**
  - Topo (linhas ~10-26): adicionar `import hashlib`, `import hmac`, `import shutil`, `import datetime`.
  - Perto de `GUILD_SAVE_DIR` (linha ~470): novo bloco com `BASE_DIR`, helpers `_atomic_write_json`/`_now_iso`, camada de **contas** e camada de **savegames**, e as travas.
  - No `handler()` (bloco global, perto de `if t == "create_room":` linha ~19393): novos `if t == "login"` etc.
- **Criar `tools/test_savegames.py`** — testes desta fase.
- **Modificar `.gitignore`** — adicionar `accounts/` e `savegames/`.

---

## Task 1: Imports e helpers de arquivo

**Files:**
- Modify: `server.py:10-26` (imports) e `server.py:~470` (helpers, logo antes de `GUILD_SAVE_DIR`)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_savegames.py` com o cabeçalho no estilo do projeto e o primeiro bloco:

```python
"""Jogos Salvos — Fase 1. Roda da raiz: python tools/test_savegames.py"""
import asyncio, sys, os, tempfile, shutil, json
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    # [1] helpers de arquivo
    print("\n[1] Helpers de arquivo")
    tmp = tempfile.mkdtemp()
    try:
        p = os.path.join(tmp, "sub", "x.json")
        S._atomic_write_json(p, {"a": 1})
        with open(p, encoding="utf-8") as f:
            check("escreve JSON atômico (cria subpasta)", json.load(f) == {"a": 1})
        check("não deixa .tmp para trás", not os.path.exists(p + ".tmp"))
        iso = S._now_iso()
        check("_now_iso formato UTC Z", isinstance(iso, str) and iso.endswith("Z") and "T" in iso)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL/erro — `AttributeError: module 'server' has no attribute '_atomic_write_json'`.

- [ ] **Step 3: Adicionar os imports**

Em `server.py`, logo após `import base64` (linha 11), acrescentar:

```python
import datetime
import hashlib
import hmac
import shutil
```

- [ ] **Step 4: Implementar os helpers**

Em `server.py`, imediatamente antes da linha `GUILD_SAVE_DIR = os.path.join(...)` (~470), inserir:

```python
# ─── Persistência de contas e jogos salvos ────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _now_iso():
    """Timestamp UTC no formato 2026-07-18T14:00:00Z."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _atomic_write_json(path, data):
    """Grava JSON de forma atômica (.tmp + os.replace), criando a pasta."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nas 3 checagens do bloco [1].

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): helpers _atomic_write_json/_now_iso + imports"
```

---

## Task 2: Hash e verificação de PIN

**Files:**
- Modify: `server.py` (bloco de contas, após os helpers da Task 1)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `tools/test_savegames.py`, dentro de `main()` antes do print final:

```python
    # [2] hash de PIN
    print("\n[2] Hash/verify de PIN")
    h = S.hash_pin("1234")
    check("hash tem 4 campos $", h.count("$") == 3 and h.startswith("pbkdf2_sha256$"))
    check("PIN não aparece em texto puro", "1234" not in h)
    check("verify aceita o PIN certo", S.verify_pin("1234", h) is True)
    check("verify recusa PIN errado", S.verify_pin("9999", h) is False)
    check("verify recusa hash malformado", S.verify_pin("1234", "lixo") is False)
    check("dois hashes do mesmo PIN diferem (salt)", S.hash_pin("1234") != S.hash_pin("1234"))
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'hash_pin'`.

- [ ] **Step 3: Implementar hash/verify**

Em `server.py`, no bloco de persistência (após `_atomic_write_json`), inserir:

```python
def hash_pin(pin, salt=None, iterations=100_000):
    """PBKDF2-SHA256 com salt por conta. Retorna 'pbkdf2_sha256$iter$salt$hash'."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(pin).encode("utf-8"), salt, iterations)
    return (f"pbkdf2_sha256${iterations}$"
            f"{base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}")

def verify_pin(pin, stored):
    """True se o PIN bate com o hash armazenado; False em qualquer falha/forma inválida."""
    try:
        algo, iters, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        dk = hashlib.pbkdf2_hmac("sha256", str(pin).encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(base64.b64encode(dk).decode(), hash_b64)
    except Exception:
        return False
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1] e [2].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): hash_pin/verify_pin (PBKDF2-SHA256)"
```

---

## Task 3: CRUD de contas

**Files:**
- Modify: `server.py` (bloco de contas)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [3] contas
    print("\n[3] CRUD de contas")
    tmp = tempfile.mkdtemp()
    old = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    try:
        acc, err = S.create_account("Ricardo", "1234")
        check("cria conta", acc is not None and err is None)
        check("apelido normalizado (minúsculas)", acc["username"] == "ricardo")
        check("arquivo existe", os.path.exists(S.account_path("ricardo")))
        acc2, err2 = S.create_account("ricardo", "5555")
        check("apelido duplicado recusa", acc2 is None and "existe" in (err2 or "").lower())
        _, e3 = S.create_account("", "1234")
        check("apelido vazio recusa", e3 is not None)
        _, e4 = S.create_account("bob", "12")
        check("PIN não-4-dígitos recusa", e4 is not None)
        loaded = S.load_account("RICARDO")
        check("load_account acha por apelido case-insensitive", loaded is not None)
        check("load_account inexistente → None", S.load_account("ninguem") is None)
        # arquivo corrompido → None
        with open(S.account_path("corrompida"), "w", encoding="utf-8") as f:
            f.write("{lixo}")
        check("conta corrompida → None", S.load_account("corrompida") is None)
    finally:
        S.ACCOUNTS_DIR = old
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'ACCOUNTS_DIR'`.

- [ ] **Step 3: Implementar a camada de contas**

Em `server.py`, no bloco de persistência, inserir:

```python
ACCOUNTS_DIR = os.path.join(BASE_DIR, "accounts")

def _norm_username(name):
    return (name or "").strip().lower()

def account_path(username):
    return os.path.join(ACCOUNTS_DIR, f"{_norm_username(username)}.json")

def load_account(username):
    """Lê a conta; ausente/corrompida/forma inesperada → None (sem crash)."""
    u = _norm_username(username)
    if not u:
        return None
    try:
        with open(account_path(u), "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("pin_hash"), str):
            return None
        return data
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[accounts] conta {u} inválida ({e})")
        return None

def create_account(username, pin):
    """Cria a conta. Retorna (data, None) ou (None, mensagem_de_erro)."""
    u = _norm_username(username)
    if not u or len(u) > 20:
        return None, "Apelido inválido (1–20 caracteres)."
    if not re.fullmatch(r"\d{4}", str(pin or "")):
        return None, "O PIN deve ter 4 dígitos."
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    if os.path.exists(account_path(u)):
        return None, "Apelido já existe."
    data = {"username": u, "pin_hash": hash_pin(pin), "created": _now_iso()}
    _atomic_write_json(account_path(u), data)
    return data, None
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1]–[3].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): CRUD de contas (create/load, PIN 4 dígitos)"
```

---

## Task 4: Camada de savegames (create/load/write/list/delete)

**Files:**
- Modify: `server.py` (bloco de savegames)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [4] savegames
    print("\n[4] CRUD de savegames")
    tmp = tempfile.mkdtemp()
    old = S.SAVEGAMES_DIR
    S.SAVEGAMES_DIR = tmp
    try:
        sg = S.create_savegame("Campanha Teste", "ricardo", "campaign", "elara.json", True)
        sid = sg["id"]
        check("id começa com sg_", sid.startswith("sg_"))
        check("campos iniciais", sg["campaign_phase"] == 0 and sg["members"] == {}
              and sg["characters"] == {} and sg["owner"] == "ricardo")
        check("master_account = dono quando has_master", sg["master_account"] == "ricardo")
        check("arquivo gravado", os.path.exists(S.savegame_path(sid)))
        # procedural zera campaign_file
        sgp = S.create_savegame("Avulso", "ricardo", "procedural", "x.json", False)
        check("procedural sem campaign_file", sgp["campaign_file"] is None and sgp["mode"] == "procedural")
        check("procedural sem master", sgp["master_account"] is None)
        # write + reload
        sg["campaign_phase"] = 3
        S.write_savegame(sg)
        check("reload mantém fase", S.load_savegame(sid)["campaign_phase"] == 3)
        check("write criou .bak da versão anterior", os.path.exists(S.savegame_path(sid) + ".bak"))
        # list filtra por participação
        lst_ric = [s["id"] for s in S.list_savegames("ricardo")]
        check("lista inclui jogos do dono", sid in lst_ric and sgp["id"] in lst_ric)
        check("lista de estranho é vazia", S.list_savegames("estranho") == [])
        # membro também vê
        sg["members"]["maria"] = {"class_id": "mage"}
        S.write_savegame(sg)
        check("membro vê o jogo", sid in [s["id"] for s in S.list_savegames("maria")])
        # corrupção → cai no .bak
        with open(S.savegame_path(sid), "w", encoding="utf-8") as f:
            f.write("{corrompido")
        rec = S.load_savegame(sid)
        check("corrompido cai no .bak", rec is not None and rec["id"] == sid)
        # delete só pelo dono
        ok, e = S.delete_savegame(sgp["id"], "maria")
        check("delete por não-dono recusa", ok is False)
        ok2, _ = S.delete_savegame(sgp["id"], "ricardo")
        check("delete pelo dono ok", ok2 is True and not os.path.exists(S.savegame_path(sgp["id"])))
    finally:
        S.SAVEGAMES_DIR = old
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'SAVEGAMES_DIR'`.

- [ ] **Step 3: Implementar a camada de savegames**

Em `server.py`, no bloco de persistência (após a camada de contas), inserir:

```python
SAVEGAMES_DIR = os.path.join(BASE_DIR, "savegames")

def savegame_path(sid):
    return os.path.join(SAVEGAMES_DIR, f"{sid}.json")

def _new_savegame_id():
    while True:
        sid = "sg_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        if not os.path.exists(savegame_path(sid)):
            return sid

def _savegame_valid_shape(d):
    return (isinstance(d, dict) and isinstance(d.get("id"), str)
            and isinstance(d.get("members"), dict)
            and isinstance(d.get("characters"), dict))

def load_savegame(sid):
    """Carrega o savegame; se o principal estiver corrompido, tenta o .bak; senão None."""
    for p in (savegame_path(sid), savegame_path(sid) + ".bak"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            if _savegame_valid_shape(d):
                return d
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return None

def write_savegame(sg):
    """Grava atômico; antes, rotaciona a versão atual para .bak (backup de 1 nível)."""
    sid = sg.get("id")
    if not sid:
        return
    os.makedirs(SAVEGAMES_DIR, exist_ok=True)
    path = savegame_path(sid)
    if os.path.exists(path):
        try:
            shutil.copy2(path, path + ".bak")
        except OSError:
            pass
    sg["updated"] = _now_iso()
    _atomic_write_json(path, sg)

def create_savegame(name, owner, mode, campaign_file, has_master):
    sid = _new_savegame_id()
    is_campaign = (mode == "campaign")
    sg = {
        "id": sid, "name": (name or "Jogo")[:40], "owner": _norm_username(owner),
        "created": _now_iso(), "updated": _now_iso(),
        "mode": "campaign" if is_campaign else "procedural",
        "campaign_file": campaign_file if is_campaign else None,
        "campaign_phase": 0,
        "has_master": bool(has_master),
        "master_account": _norm_username(owner) if has_master else None,
        "members": {}, "characters": {},
    }
    write_savegame(sg)
    return sg

def list_savegames(username):
    """Resumo dos jogos onde a conta é dona, membro ou mestre (mais recentes primeiro)."""
    u = _norm_username(username)
    out = []
    if not u or not os.path.isdir(SAVEGAMES_DIR):
        return out
    for fn in os.listdir(SAVEGAMES_DIR):
        if not fn.endswith(".json"):
            continue
        sg = load_savegame(fn[:-5])
        if not sg:
            continue
        if (sg.get("owner") == u or u in (sg.get("members") or {})
                or sg.get("master_account") == u):
            out.append({
                "id": sg["id"], "name": sg.get("name"), "mode": sg.get("mode"),
                "campaign_file": sg.get("campaign_file"),
                "campaign_phase": sg.get("campaign_phase", 0),
                "updated": sg.get("updated"), "owner": sg.get("owner"),
                "has_master": sg.get("has_master", False),
                "members": sg.get("members", {}),
            })
    out.sort(key=lambda s: s.get("updated") or "", reverse=True)
    return out

def delete_savegame(sid, requester):
    sg = load_savegame(sid)
    if not sg:
        return False, "Jogo não encontrado."
    if sg.get("owner") != _norm_username(requester):
        return False, "Apenas o dono pode apagar este jogo."
    for p in (savegame_path(sid), savegame_path(sid) + ".bak"):
        try:
            os.remove(p)
        except OSError:
            pass
    return True, None
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1]–[4].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): camada de savegames (create/load/write/list/delete + .bak)"
```

---

## Task 5: Travas de concorrência

**Files:**
- Modify: `server.py` (declarar as travas junto do bloco de persistência, perto de `CHARACTERS_IN_USE`)
- Test: `tools/test_savegames.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [5] travas
    print("\n[5] Travas de concorrência")
    check("SAVEGAMES_IN_USE existe e é dict", isinstance(S.SAVEGAMES_IN_USE, dict))
    check("ACCOUNTS_ONLINE existe e é dict", isinstance(S.ACCOUNTS_ONLINE, dict))
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'SAVEGAMES_IN_USE'`.

- [ ] **Step 3: Implementar as travas**

Em `server.py`, no bloco de persistência, inserir:

```python
# Um savegame só roda em uma sessão ao vivo por vez; uma conta só loga em uma.
SAVEGAMES_IN_USE = {}   # savegame_id -> room code
ACCOUNTS_ONLINE = {}    # username -> pid da conexão autenticada
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1]–[5].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): travas SAVEGAMES_IN_USE/ACCOUNTS_ONLINE"
```

---

## Task 6: Handler `login` / `create_account`

**Files:**
- Modify: `server.py` (no `handler()`, no bloco global, logo antes de `if t == "create_room":` ~19393)
- Test: `tools/test_savegames.py` (teste de unidade da lógica, chamando um helper puro)

Para manter o handler testável sem WebSocket, a lógica fica num helper puro `try_login(pid, username, pin)` que retorna `(ok, payload_or_error)`; o handler só faz I/O de socket e mexe em `ACCOUNTS_ONLINE`.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [6] try_login (helper puro)
    print("\n[6] Login")
    tmp = tempfile.mkdtemp()
    olda = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    S.ACCOUNTS_ONLINE.clear()
    try:
        S.create_account("ana", "4321")
        ok, pay = S.try_login("pid1", "Ana", "4321")
        check("login com PIN certo ok", ok is True and pay["username"] == "ana")
        ok2, err2 = S.try_login("pid2", "ana", "0000")
        check("login com PIN errado recusa", ok2 is False and "pin" in (err2 or "").lower())
        ok3, err3 = S.try_login("pid3", "fantasma", "1111")
        check("login de conta inexistente recusa", ok3 is False)
        # já online noutra conexão
        S.ACCOUNTS_ONLINE["ana"] = "pid1"
        ok4, err4 = S.try_login("pid9", "ana", "4321")
        check("conta já online recusa 2º login", ok4 is False and "uso" in (err4 or "").lower())
        # mesma conexão relogando é permitido (idempotente)
        ok5, _ = S.try_login("pid1", "ana", "4321")
        check("mesma conexão pode relogar", ok5 is True)
    finally:
        S.ACCOUNTS_DIR = olda
        S.ACCOUNTS_ONLINE.clear()
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'try_login'`.

- [ ] **Step 3: Implementar `try_login` e o handler**

Em `server.py`, no bloco de persistência, inserir o helper puro:

```python
def try_login(pid, username, pin):
    """Valida credenciais e reserva a conta em ACCOUNTS_ONLINE.
    Retorna (True, dados_da_conta) ou (False, mensagem_de_erro)."""
    u = _norm_username(username)
    acc = load_account(u)
    if not acc:
        return False, "Conta não encontrada. Crie uma conta primeiro."
    if not verify_pin(pin, acc.get("pin_hash", "")):
        return False, "PIN incorreto."
    dono = ACCOUNTS_ONLINE.get(u)
    if dono and dono != pid:
        return False, "Esta conta já está em uso em outra conexão."
    ACCOUNTS_ONLINE[u] = pid
    return True, {"username": u}
```

No `handler()`, imediatamente antes de `if t == "create_room":` (~19393), acrescentar (mantendo o padrão `continue` dos handlers globais):

```python
                if t == "create_account":
                    acc, e = create_account(msg.get("username"), msg.get("pin"))
                    if acc:
                        ok, pay = try_login(pid, acc["username"], msg.get("pin"))
                        await ws.send(json.dumps({"type": "login_result", "ok": ok,
                                                  "username": acc["username"] if ok else None,
                                                  "error": None if ok else pay}))
                    else:
                        await ws.send(json.dumps({"type": "login_result", "ok": False, "error": e}))
                    continue

                if t == "login":
                    ok, pay = try_login(pid, msg.get("username"), msg.get("pin"))
                    await ws.send(json.dumps({"type": "login_result", "ok": ok,
                                              "username": pay["username"] if ok else None,
                                              "error": None if ok else pay}))
                    continue
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1]–[6].

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): handlers login/create_account (+ try_login puro)"
```

---

## Task 7: Handlers `list_savegames` / `create_savegame` / `delete_savegame`

**Files:**
- Modify: `server.py` (`handler()`, bloco global, junto dos handlers da Task 6)
- Test: `tools/test_savegames.py` (helper puro `try_create_savegame`)

Estes handlers exigem que a conexão esteja logada. A conexão guarda a conta autenticada num dict `account_by_pid` local do `handler()`. Para testar sem socket, extrair `try_create_savegame(account, name, mode, campaign_file, has_master)` que valida e chama `create_savegame`.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `main()`:

```python
    # [7] try_create_savegame (helper puro)
    print("\n[7] Criar savegame (validação)")
    tmp = tempfile.mkdtemp()
    olds = S.SAVEGAMES_DIR
    S.SAVEGAMES_DIR = tmp
    try:
        sg, e = S.try_create_savegame("ricardo", "Nova", "campaign", "elara.json", False)
        check("cria com conta logada", sg is not None and e is None)
        sg2, e2 = S.try_create_savegame(None, "Nova", "campaign", "elara.json", False)
        check("recusa sem conta logada", sg2 is None and e2 is not None)
        sg3, e3 = S.try_create_savegame("ricardo", "", "campaign", "elara.json", False)
        check("recusa nome vazio", sg3 is None and e3 is not None)
    finally:
        S.SAVEGAMES_DIR = olds
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_savegames.py`
Expected: FAIL — `AttributeError: module 'server' has no attribute 'try_create_savegame'`.

- [ ] **Step 3: Implementar o helper e os handlers**

Em `server.py`, no bloco de persistência, inserir:

```python
def try_create_savegame(account, name, mode, campaign_file, has_master):
    """Valida a criação de um savegame por uma conta logada.
    Retorna (savegame, None) ou (None, mensagem_de_erro)."""
    if not account:
        return None, "Você precisa estar logado para criar um jogo."
    if not (name or "").strip():
        return None, "Dê um nome ao jogo."
    if mode == "campaign" and not campaign_file:
        return None, "Escolha uma campanha."
    sg = create_savegame(name, account, mode, campaign_file, has_master)
    return sg, None
```

No `handler()`, primeiro criar o dicionário de conta logada por conexão. Localizar, dentro de `async def handler(ws):`, a linha `room = None` (~19294) e logo abaixo dela acrescentar:

```python
    account = {"name": None}   # conta autenticada nesta conexão (via login)
```

Depois, no handler `login` e `create_account` da Task 6, gravar a conta ao autenticar — alterar as duas chamadas de `try_login` para registrar em `account["name"]` no sucesso. Ou seja, logo após `ok, pay = try_login(...)` e quando `ok`, adicionar `account["name"] = pay["username"]` (em ambos os handlers, antes do `await ws.send`).

Agora, junto dos handlers globais, acrescentar:

```python
                if t == "list_savegames":
                    await ws.send(json.dumps({"type": "savegames_list",
                                              "savegames": list_savegames(account["name"])}))
                    continue

                if t == "create_savegame":
                    sg, e = try_create_savegame(account["name"], msg.get("name"),
                                                msg.get("mode"), msg.get("campaign_file"),
                                                bool(msg.get("has_master")))
                    if sg:
                        await ws.send(json.dumps({"type": "savegame_created", "savegame": sg}))
                    else:
                        await err(e)
                    continue

                if t == "delete_savegame":
                    ok, e = delete_savegame(msg.get("id"), account["name"])
                    if ok:
                        await ws.send(json.dumps({"type": "savegames_list",
                                                  "savegames": list_savegames(account["name"])}))
                    else:
                        await err(e)
                    continue
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_savegames.py`
Expected: PASS nos blocos [1]–[7].

- [ ] **Step 5: Liberar a conta no disconnect**

Localizar o fim de `async def handler(ws):` — o bloco `finally:`/limpeza de desconexão (perto de onde `handle_disconnect` é chamado). Acrescentar a liberação da conta:

```python
        if account["name"] and ACCOUNTS_ONLINE.get(account["name"]) == pid:
            del ACCOUNTS_ONLINE[account["name"]]
```

(Se o `handler` não tiver `finally`, adicionar a limpeza no ponto onde a conexão é encerrada, ao lado da limpeza de sala existente.)

- [ ] **Step 6: Rodar o teste completo e a suíte de regressão**

Run: `python tools/test_savegames.py`
Expected: PASS em todos os blocos [1]–[7].

Run: `python tools/test_guilda.py`
Expected: continua PASS (não quebramos o save da Guilda atual).

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_savegames.py
git commit -m "feat(saves): handlers list/create/delete savegame + libera conta no disconnect"
```

---

## Task 8: `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Verificar o estado atual**

Run: `grep -nE "saves|accounts|savegames" .gitignore`
Expected: aparece `saves/` (ou similar); `accounts/`/`savegames/` ainda não.

- [ ] **Step 2: Adicionar as pastas**

Acrescentar ao `.gitignore`:

```
accounts/
savegames/
```

- [ ] **Step 3: Confirmar que o git ignora**

Run: `git status --porcelain accounts savegames`
Expected: sem saída (as pastas, se existirem por testes, não aparecem como não-rastreadas).

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore(saves): ignora accounts/ e savegames/"
```

---

## Self-Review (Fase 1)

- **Cobertura do escopo:** contas (Task 2/3), savegames (Task 4), travas (Task 5), handlers login/create_account (Task 6), list/create/delete (Task 7), gitignore (Task 8). ✔
- **Sem placeholders:** todo passo tem código real e comando com resultado esperado. ✔
- **Consistência de tipos:** `_norm_username`, `account_path`, `load_account`, `create_account`, `create_savegame`, `load_savegame`, `write_savegame`, `list_savegames`, `delete_savegame`, `try_login`, `try_create_savegame`, `SAVEGAMES_IN_USE`, `ACCOUNTS_ONLINE`, `account["name"]` usados com o mesmo nome/forma em todas as tasks. ✔

---

## Roadmap — Fases 2 e 3 (planos próprios, escritos após a Fase 1)

**Fase 2 — Snapshot/restore + checkpoints + retomar:**
- `snapshot_character(player)` / `restore_character(player, snap)` (campos duráveis do §Ficha durável do spec).
- Handler `load_savegame` que abre um lobby ligado ao savegame (respeita `SAVEGAMES_IN_USE`).
- Vínculo conta↔personagem no lobby: 1ª escolha grava `members`+`characters`; retomar auto-atribui e carrega; recusa classe de outra conta.
- `restore_character` no `start_game` para membros presentes; ausentes pulados; `campaign_phase` restaurada.
- Gravação nos pontos seguros (cidade / fim de fase) via `write_savegame`.
- Testes em `tools/test_savegames.py`: snapshot/restore ida-e-volta, checkpoint na cidade preserva ausentes, retomar carrega a fase certa, travas.

**Fase 3 — UI do cliente (`game.js` / `src/gameState.js`):**
- Tela de login (apelido+PIN) antes do menu.
- Home "Novo jogo" × "Continuar jogo" (lista `savegames_list`).
- Formulário de novo jogo (nome + campanha + toggle Mestre).
- Lobby com auto-vínculo ao retomar; senders `login`/`createAccount`/`createSavegame`/`listSavegames`/`loadSavegame`/`deleteSavegame`.
