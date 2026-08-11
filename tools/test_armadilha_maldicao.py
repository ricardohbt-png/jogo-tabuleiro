"""Verifica a configuração de maldições em armadilhas autoradas.
Roda da raiz: python tools/test_armadilha_maldicao.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from tools.export_catalog import build_catalog


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


def dungeon_with_traps():
    width, height = 6, 5
    tiles = [[server.FLOOR] * width for _ in range(height)]
    rooms = [{"id": 1, "x": 0, "y": 0, "w": width, "h": height,
              "role": "entrance", "locked": False, "doors": []}]
    return {
        "schema_version": 1,
        "id": "curse_trap_test",
        "name": "Curse Trap Test",
        "grid": {"w": width, "h": height},
        "tiles": tiles,
        "entrance": {"x": 0, "y": 0},
        "rooms": rooms,
        "traps": [{"tipo": "armadilha_maldicao", "pos": [2, 2],
                   "curse_mode": "especifica", "curse_id": "voz_quebrada"}],
        "decorations": [{"id": "decor_1", "type": "barril", "pos": [3, 2],
                         "facing": [0, 1],
                         "trap": {"tipo": "armadilha_maldicao",
                                  "curse_mode": "especifica",
                                  "curse_id": "olhos_escuridao"}}],
        "monsters": [], "chests": [], "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }


def main():
    print("\n[1] catálogo do editor")
    catalog = build_catalog()
    ids = {c["id"] for c in catalog["curses"]}
    check("editor recebe todas as maldições", ids == set(server.MALDICOES))
    check("catálogo inclui descrição", bool(next(c for c in catalog["curses"] if c["id"] == "voz_quebrada")["description"]))

    print("\n[2] validação e hidratação")
    definition = dungeon_with_traps()
    ok, message = server.validar_dungeon(definition)
    check(f"maldição específica válida ({message})", ok)
    arm = server.make_authored_trap(definition["traps"][0])
    check("armadilha standalone preserva curse_id", arm.get("curse_id") == "voz_quebrada")

    room = server.GameRoom("CURSE_TRAP_TEST")
    room.load_authored_dungeon(definition)
    decor_arm = room._armadilha_da_decoracao(room.decorations[0])
    check("armadilha de decoração preserva curse_id", decor_arm.get("curse_id") == "olhos_escuridao")

    invalid = dungeon_with_traps()
    invalid["traps"][0]["curse_id"] = "nao_existe"
    ok, _ = server.validar_dungeon(invalid)
    check("maldição desconhecida é recusada", not ok)

    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
