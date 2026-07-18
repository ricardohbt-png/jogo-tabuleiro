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

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
