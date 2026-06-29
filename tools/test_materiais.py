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

def _defn_base():
    """Masmorra mínima válida 6x3 toda de chão com 1 sala de entrada."""
    return {
        "schema_version": 1, "id": "t", "name": "T",
        "grid": {"w": 6, "h": 3},
        "tiles": [[FLOOR] * 6 for _ in range(3)],
        "rooms": [{"id": 0, "x": 0, "y": 0, "w": 6, "h": 3, "role": "entrance",
                   "locked": False, "doors": []}],
        "entrance": {"x": 0, "y": 0},
    }

def test_validacao():
    print("\n[M2] validação de materiais")
    import copy
    base = _defn_base()
    ok, _ = server.validar_dungeon(copy.deepcopy(base))
    check("base válida (sem materiais)", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "grama"}
    ok, _ = server.validar_dungeon(d)
    check("piso em chão é válido", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "inexistente"}
    ok, msg = server.validar_dungeon(d)
    check("material desconhecido recusado", not ok and "material" in msg.lower())

    d = copy.deepcopy(base); d["materiais"] = {"9,9": "grama"}
    ok, _ = server.validar_dungeon(d)
    check("material fora do grid recusado", not ok)

    d = copy.deepcopy(base)
    d["tiles"][1][1] = WALL
    d["materiais"] = {"1,1": "grama"}   # piso em parede
    ok, _ = server.validar_dungeon(d)
    check("piso em casa de parede recusado", not ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "pedra_normal"}  # parede em chão
    ok, _ = server.validar_dungeon(d)
    check("parede em casa de chão recusada", not ok)

    d = copy.deepcopy(base)
    d["tiles"][1][1] = WALL
    d["materiais"] = {"1,1": "enegrecida"}
    ok, _ = server.validar_dungeon(d)
    check("parede em casa de parede é válida", ok)

    d = copy.deepcopy(base); d["materiais"] = {"1,1": "entulho"}  # entulho é piso sólido em chão
    ok, _ = server.validar_dungeon(d)
    check("entulho em chão é válido", ok)

    d = copy.deepcopy(base); d["materiais"] = "naoeobjeto"
    ok, _ = server.validar_dungeon(d)
    check("materiais não-objeto recusado", not ok)

if __name__ == "__main__":
    test_catalog()
    test_validacao()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)
