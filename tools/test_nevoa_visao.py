"""Regressões da névoa de guerra e da linha de visão.
Roda da raiz: python tools/test_nevoa_visao.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import DOOR, FLOOR, GameRoom, WALL


PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


def room():
    r = GameRoom("FOG-TEST")
    r.map_w = r.map_h = 9
    r.tiles = [[FLOOR] * 9 for _ in range(9)]
    r.rooms = []
    r.door_rooms = {}
    r.opened_doors = set()
    r.explored = set()
    return r


def main():
    r = room()
    for y in range(9):
        r.tiles[y][4] = WALL
    r.tiles[4][4] = DOOR

    r._reveal_around(2, 4, radius=4)
    check("parede/porta no limite da visão é revelada", (4, 4) in r.explored)
    check("tile atrás da porta fechada permanece oculto", (5, 4) not in r.explored)
    check("tile diagonal atrás da parede permanece oculto", (5, 3) not in r.explored)

    r.opened_doors.add((4, 4))
    r.explored = set()
    r._reveal_around(2, 4, radius=4)
    check("porta aberta permite revelar o corredor", (5, 4) in r.explored)

    r.magic_reveal = {}
    r.explored = set()
    r._all_animados = lambda: [{"pos": [2, 4], "vida_atual": 1}]
    check("servo também não revela através da parede", (5, 4) not in r._live_reveal_tiles())

    print(f"{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
