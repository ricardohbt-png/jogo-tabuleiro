"""Ida-e-volta: o formato que o editor produz é aceito pelo servidor.
Usa dungeons/test_fase1.json como referência do formato do editor.
Roda da raiz: python tools/test_roundtrip_editor.py"""
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
    with open(os.path.join(base, "dungeons", "test_fase1.json"), encoding="utf-8") as f:
        d = json.load(f)
    ok, msg = server.validar_dungeon(d)
    check(f"masmorra de referência valida ({msg})", ok is True)
    # campos que o editor sempre emite estão presentes
    for k in ("schema_version", "grid", "tiles", "rooms", "entrance",
              "monsters", "chests", "traps", "objectives"):
        check(f"campo '{k}' presente", k in d)
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
