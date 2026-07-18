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

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
