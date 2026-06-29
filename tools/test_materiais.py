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

def _room():
    async def _noop(*a, **k): pass
    r = GameRoom("TEST")
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop; r.push_state = _noop
    return r

def _defn_full():
    """6x3, chão todo, com entulho em (2,1) e grama em (3,1)."""
    d = _defn_base()
    d["materiais"] = {"2,1": "entulho", "3,1": "grama"}
    return d

def test_carga():
    print("\n[M3] carga/índices/payload de materiais")
    r = _room()
    r.load_authored_dungeon(_defn_full())
    check("materiais carregado com chave-tupla", r.materiais.get((2, 1)) == "entulho")
    check("índice sólido tem entulho", (2, 1) in r._mat_solid_tiles)
    check("índice opaco tem entulho", (2, 1) in r._mat_oclui_tiles)
    check("grama não é sólida nem opaca",
          (3, 1) not in r._mat_solid_tiles and (3, 1) not in r._mat_oclui_tiles)
    ser = r._serializar_materiais()
    check("serializa como 'x,y'->id", ser.get("2,1") == "entulho" and ser.get("3,1") == "grama")

    r2 = _room()
    r2.load_authored_dungeon(_defn_base())
    check("sem campo materiais → dict vazio", r2.materiais == {})
    check("sem materiais → índices vazios",
          r2._mat_solid_tiles == set() and r2._mat_oclui_tiles == set())

def test_entulho_servidor():
    print("\n[M4] entulho bloqueia no servidor")
    r = _room()
    r.load_authored_dungeon(_defn_full())   # entulho em (2,1)
    check("_blocks_tile bloqueia entulho", r._blocks_tile(2, 1) is True)
    check("_blocks_tile não bloqueia grama", r._blocks_tile(3, 1) is False)
    check("entulho barra LOS", r._tem_linha_de_visao([0, 1], [4, 1]) is False)
    check("LOS livre na linha de cima", r._tem_linha_de_visao([0, 0], [4, 0]) is True)
    r.explored = set()
    r._reveal_around(0, 1, radius=5)
    check("entulho oclui revelação atrás dele", (4, 1) not in r.explored)
    check("casa antes do entulho é revelada", (1, 1) in r.explored)

def test_roundtrip():
    print("\n[M5] round-trip materiais")
    import json
    d = _defn_full()
    ok, msg = server.validar_dungeon(json.loads(json.dumps(d)))
    check("defn com materiais valida", ok)
    d2 = json.loads(json.dumps(d))
    r = _room(); r.load_authored_dungeon(d2)
    ser = r._serializar_materiais()
    check("round-trip preserva entulho", ser.get("2,1") == "entulho")
    check("round-trip preserva grama", ser.get("3,1") == "grama")

if __name__ == "__main__":
    test_catalog()
    test_validacao()
    test_carga()
    test_entulho_servidor()
    test_roundtrip()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)
