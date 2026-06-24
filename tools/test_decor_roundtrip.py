"""Roundtrip: a masmorra de amostra com decorações valida no servidor.
Roda da raiz: python tools/test_decor_roundtrip.py"""
import sys, os, json
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "dungeons", "test_decoracoes.json"), encoding="utf-8") as f:
        d = json.load(f)
    ok, msg = server.validar_dungeon(d)
    check(f"amostra válida ({msg})", ok is True)
    check("tem 5 decorações", len(d["decorations"]) == 5)
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
