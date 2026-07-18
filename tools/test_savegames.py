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

    # [2] hash de PIN
    print("\n[2] Hash/verify de PIN")
    h = S.hash_pin("1234")
    check("hash tem 4 campos $", h.count("$") == 3 and h.startswith("pbkdf2_sha256$"))
    check("PIN não aparece em texto puro", "1234" not in h)
    check("verify aceita o PIN certo", S.verify_pin("1234", h) is True)
    check("verify recusa PIN errado", S.verify_pin("9999", h) is False)
    check("verify recusa hash malformado", S.verify_pin("1234", "lixo") is False)
    check("dois hashes do mesmo PIN diferem (salt)", S.hash_pin("1234") != S.hash_pin("1234"))

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

    # [5] travas
    print("\n[5] Travas de concorrência")
    check("SAVEGAMES_IN_USE existe e é dict", isinstance(S.SAVEGAMES_IN_USE, dict))
    check("ACCOUNTS_ONLINE existe e é dict", isinstance(S.ACCOUNTS_ONLINE, dict))

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

    # [8] validação de segurança (path traversal)
    print("\n[8] Segurança de caminhos")
    tmp = tempfile.mkdtemp()
    olda = S.ACCOUNTS_DIR
    S.ACCOUNTS_DIR = tmp
    S.ACCOUNTS_ONLINE.clear()
    try:
        _, e1 = S.create_account("../evil", "1234")
        check("recusa apelido com ../", e1 is not None)
        _, e2 = S.create_account("c:/temp/evil", "1234")
        check("recusa apelido com caminho absoluto", e2 is not None)
        _, e3 = S.create_account("bob smith", "1234")
        check("recusa apelido com espaço", e3 is not None)
        check("load_savegame recusa id inválido", S.load_savegame("../foo") is None)
        check("load_savegame recusa id None", S.load_savegame(None) is None)
        # re-login pela mesma conexão libera a conta anterior
        S.create_account("aaa", "1111")
        S.create_account("bbb", "2222")
        S.try_login("pidX", "aaa", "1111")
        S.try_login("pidX", "bbb", "2222")
        check("re-login libera conta anterior",
              "aaa" not in S.ACCOUNTS_ONLINE and S.ACCOUNTS_ONLINE.get("bbb") == "pidX")
    finally:
        S.ACCOUNTS_DIR = olda
        S.ACCOUNTS_ONLINE.clear()
        shutil.rmtree(tmp, ignore_errors=True)

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
    p2 = make_player("p2", "Outro", "warrior", 1)
    S.restore_character(p2, snap)
    check("restore aplica ouro", p2["gold"] == 999)
    check("restore aplica hp", p2["hp"] == 3)
    check("restore aplica nível/xp", p2["level"] == 2 and p2["xp"] == 120)
    check("restore aplica bag", any(i.get("id") == "pocao" for i in p2["bag"]))
    check("restore aplica guild equip", p2["guild_equip"]["tecnica"] == "brutalidade")
    check("restore preserva id/nome do shell", p2["id"] == "p2" and p2["name"] == "Outro")
    snap["bag"].append({"id": "x"})
    check("restore fez deep copy (bag isolada)", not any(i.get("id") == "x" for i in p2["bag"]))

    # [10] GameRoom ↔ savegame
    print("\n[10] Sala conhece savegame e contas")
    from server import GameRoom
    r = GameRoom("TST0")
    check("savegame_id default None", r.savegame_id is None)
    check("savegame default None", r.savegame is None)
    check("account_by_pid default vazio", r.account_by_pid == {})

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
        r.players["j1"] = {"id": "j1", "name": "Joao", "class_id": None, "ready": False, "connected": True, "slot": 0}
        r.account_by_pid["j1"] = "joao"
        _aio.run(r.select_class("j1", "warrior"))
        check("grava vínculo no savegame", sg["members"].get("joao", {}).get("class_id") == "warrior")
        check("cria ficha fresca do personagem", "warrior" in sg["characters"])
        check("persistiu em disco", S.load_savegame(sg["id"])["members"]["joao"]["class_id"] == "warrior")
        r.players["j2"] = {"id": "j2", "name": "Maria", "class_id": None, "ready": False, "connected": True, "slot": 1}
        r.account_by_pid["j2"] = "maria"
        errs = []
        async def _cap(pid, m, *a, **k):
            if isinstance(m, dict) and m.get("type") == "error": errs.append(m.get("msg", ""))
        r.send_to = _cap
        _aio.run(r.select_class("j2", "warrior"))
        check("recusa classe de outra conta", r.players["j2"]["class_id"] is None and errs)
        _aio.run(r.select_class("j1", "mage"))
        check("conta vinculada é forçada à sua classe", r.players["j1"]["class_id"] == "warrior")
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)

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
        base = S.snapshot_character(S.make_player("x", "x", "warrior", 0))
        base["gold"] = 777; base["level"] = 4
        sg["members"]["joao"] = {"class_id": "warrior"}
        sg["characters"]["warrior"] = base
        sg["campaign_phase"] = 2
        S.write_savegame(sg)
        r.savegame_id = sg["id"]; r.savegame = sg
        r.campaign_phase = 2
        r.players = {"j1": {"id": "j1", "name": "Joao", "class_id": "warrior", "connected": True, "slot": 0}}
        r.account_by_pid = {"j1": "joao"}
        r.host_pid = "j1"
        _aio.run(r.start_game("j1"))
        check("overlay restaurou ouro salvo", r.players["j1"]["gold"] == 777)
        check("overlay restaurou nível salvo", r.players["j1"]["level"] == 4)
        r.players["j1"]["gold"] = 1234
        _aio.run(r._voltar_para_cidade())
        disco = S.load_savegame(sg["id"])
        check("checkpoint gravou ouro atual", disco["characters"]["warrior"]["gold"] == 1234)
        check("checkpoint preservou ausente", "mage" not in disco["characters"])
        check("checkpoint gravou fase", disco["campaign_phase"] == 2)
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)

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
        room2, e2 = S.try_open_savegame_room("joao", sg["id"], rooms)
        check("recusa 2ª sessão do mesmo savegame", room2 is None and "uso" in (e2 or "").lower())
        room3, e3 = S.try_open_savegame_room("estranho", sg["id"], rooms)
        check("recusa não-membro", room3 is None)
        room4, e4 = S.try_open_savegame_room(None, sg["id"], rooms)
        check("recusa sem login", room4 is None)
    finally:
        S.SAVEGAMES_DIR = olds; S.SAVEGAMES_IN_USE.clear()
        shutil.rmtree(tmp, ignore_errors=True)

    # [14] a mesma classe pode existir em savegames diferentes (trava global não vale c/ savegame)
    print("\n[14] Classe repetida entre savegames")
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    S.CHARACTERS_IN_USE.clear()
    try:
        async def _noop(*a, **k): pass
        # sala A (savegame 1) — joao pega warrior
        rA = GameRoom("AAAA"); rA.broadcast_lobby = _noop; rA.send_to = _noop
        sgA = S.create_savegame("A", "ricardo", "campaign", "elara.json", False)
        rA.savegame_id = sgA["id"]; rA.savegame = sgA
        rA.players["a1"] = {"id": "a1", "name": "Joao", "class_id": None, "ready": False, "connected": True, "slot": 0}
        rA.account_by_pid["a1"] = "joao"
        _aio.run(rA.select_class("a1", "warrior"))
        check("sala A vinculou warrior", rA.players["a1"]["class_id"] == "warrior")
        check("savegame NÃO usa trava global CHARACTERS_IN_USE", "warrior" not in S.CHARACTERS_IN_USE)
        # sala B (savegame 2, OUTRA conta) — também pega warrior, sem bloqueio
        rB = GameRoom("BBBB"); rB.broadcast_lobby = _noop; rB.send_to = _noop
        sgB = S.create_savegame("B", "maria", "campaign", "elara.json", False)
        rB.savegame_id = sgB["id"]; rB.savegame = sgB
        rB.players["b1"] = {"id": "b1", "name": "Maria", "class_id": None, "ready": False, "connected": True, "slot": 0}
        rB.account_by_pid["b1"] = "maria"
        _aio.run(rB.select_class("b1", "warrior"))
        check("sala B também vincula warrior (savegames independentes)", rB.players["b1"]["class_id"] == "warrior")
    finally:
        S.SAVEGAMES_DIR = olds; S.CHARACTERS_IN_USE.clear()
        shutil.rmtree(tmp, ignore_errors=True)

    # [15] lobby_state carrega savegame + conta por jogador
    print("\n[15] Lobby com contexto de savegame")
    tmp = tempfile.mkdtemp(); olds = S.SAVEGAMES_DIR; S.SAVEGAMES_DIR = tmp
    try:
        r = GameRoom("LOBS")
        cap = {}
        async def _capb(msg, *a, **k): cap.update(msg)
        r.broadcast = _capb
        sg = S.create_savegame("Jogo", "ricardo", "campaign", "elara.json", False)
        sg["members"]["joao"] = {"class_id": "warrior"}; S.write_savegame(sg)
        r.savegame_id = sg["id"]; r.savegame = sg
        r.players["j1"] = {"id": "j1", "name": "Joao", "class_id": "warrior", "ready": True, "connected": True, "slot": 0}
        r.account_by_pid["j1"] = "joao"
        r.players["j2"] = {"id": "j2", "name": "Maria", "class_id": None, "ready": False, "connected": True, "slot": 1}
        r.account_by_pid["j2"] = "maria"
        _aio.run(r.broadcast_lobby())
        check("payload traz savegame {id,name}", cap.get("savegame", {}).get("id") == sg["id"] and cap["savegame"]["name"] == "Jogo")
        pj = {p["id"]: p for p in cap["players"]}
        check("jogador vinculado marcado bound", pj["j1"].get("account") == "joao" and pj["j1"].get("bound") is True)
        check("jogador não-vinculado bound=False", pj["j2"].get("account") == "maria" and pj["j2"].get("bound") is False)
        r2 = GameRoom("LOB2"); cap2 = {}
        async def _capb2(msg, *a, **k): cap2.update(msg)
        r2.broadcast = _capb2
        r2.players["a"] = {"id": "a", "name": "X", "class_id": None, "ready": False, "connected": True, "slot": 0}
        _aio.run(r2.broadcast_lobby())
        check("sem savegame → savegame None", cap2.get("savegame") is None)
    finally:
        S.SAVEGAMES_DIR = olds; shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
