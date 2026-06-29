"""Testes da camada de materiais de chão/parede.
Roda da raiz: python tools/test_materiais.py"""
import sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, WALL, FLOOR, DOOR

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def test_catalog():
    print("\n[M1] catálogo MATERIAIS")
    m = server.MATERIAIS
    for k in ("pedra_cinza", "terra", "grama", "pedra_negra", "entulho",
              "pedra_normal", "enegrecida", "pedra_caverna", "desmoronada"):
        check(f"{k} presente", k in m)
    check("pisos são categoria piso", all(m[k]["categoria"] == "piso"
          for k in ("pedra_cinza", "terra", "grama", "pedra_negra", "entulho")))
    check("paredes são categoria parede", all(m[k]["categoria"] == "parede"
          for k in ("pedra_normal", "enegrecida", "pedra_caverna", "desmoronada")))
    check("entulho é sólido e oclui", m["entulho"]["solido"] and m["entulho"]["oclui"])
    check("grama é cosmética (não sólida/oclui)",
          not m["grama"]["solido"] and not m["grama"]["oclui"])
    check("todo material tem nome/categoria/cor/solido/oclui", all(
          set(("nome", "categoria", "cor", "solido", "oclui")) <= set(v) for v in m.values()))
    check("defaults expostos",
          server.MATERIAIS_PISO_DEFAULT == "pedra_cinza"
          and server.MATERIAIS_PAREDE_DEFAULT == "pedra_normal")

if __name__ == "__main__":
    test_catalog()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)
