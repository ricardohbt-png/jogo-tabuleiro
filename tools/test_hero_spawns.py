"""Verifica o modo de início com posições separadas por herói.
Roda da raiz: python tools/test_hero_spawns.py
"""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, FLOOR, validar_dungeon, make_player


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


def hero_dungeon():
    width, height = 10, 8
    tiles = [[0] * width for _ in range(height)]
    for y in range(1, 7):
        for x in range(1, 9):
            tiles[y][x] = FLOOR
    rooms = [
        {"id": 1, "x": 1, "y": 1, "w": 3, "h": 3, "role": "empty", "locked": False, "doors": []},
        {"id": 2, "x": 6, "y": 1, "w": 3, "h": 3, "role": "empty", "locked": False, "doors": []},
        {"id": 3, "x": 1, "y": 4, "w": 3, "h": 3, "role": "empty", "locked": False, "doors": []},
        {"id": 4, "x": 6, "y": 4, "w": 3, "h": 3, "role": "empty", "locked": False, "doors": []},
    ]
    return {
        "schema_version": 1,
        "id": "hero_spawns_test",
        "name": "Hero Spawns Test",
        "start_mode": "hero_spawns",
        "grid": {"w": width, "h": height},
        "tiles": tiles,
        "rooms": rooms,
        "entrance": None,
        "hero_spawns": [
            {"class_id": "warrior", "pos": [2, 2], "room_id": 1},
            {"class_id": "bard", "pos": [7, 2], "room_id": 2},
        ],
        "exit": {"x": 5, "y": 4},
        "saida_permitida": False,
        "monsters": [],
        "chests": [],
        "traps": [],
        "decorations": [],
        "secret_passages": [],
        "falas": [],
        "master_reinforcements": [],
        "expected_party": {"heroes": 2, "level": 1},
        "objectives": {"primary": {"type": "all_heroes_at_exit"}, "secondary": []},
    }


def setup_room():
    room = GameRoom("HERO_SPAWNS_TEST")

    async def noop(*args, **kwargs):
        return None

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room.broadcast_city_state = noop
    room.players["p1"] = make_player("p1", "Victor", "warrior", 0)
    room.players["p2"] = make_player("p2", "Henrique", "bard", 1)
    room.player_order = ["p1", "p2"]
    room.host_pid = "p1"
    room.phase = "city"
    room.mode = "authored"
    room.dungeon_def = hero_dungeon()
    return room


def test_validation():
    print("\n[1] validação")
    definition = hero_dungeon()
    ok, message = validar_dungeon(definition)
    check(f"modo hero_spawns válido ({message})", ok)

    duplicate = copy.deepcopy(definition)
    duplicate["hero_spawns"][1]["class_id"] = "warrior"
    ok, _ = validar_dungeon(duplicate)
    check("classe duplicada recusa", not ok)

    no_exit = copy.deepcopy(definition)
    no_exit["exit"] = None
    ok, _ = validar_dungeon(no_exit)
    check("objetivo coletivo sem saída recusa", not ok)


async def test_runtime():
    print("\n[2] carregamento e spawn")
    room = setup_room()
    await room.enter_dungeon("p1")
    check("modo runtime hero_spawns", room.start_mode == "hero_spawns")
    check("não cria stairs_pos", room.stairs_pos is None)
    check("Guerreiro recebe posição autorada", room.players["p1"]["pos"] == [2, 2])
    check("Bardo recebe posição autorada", room.players["p2"]["pos"] == [7, 2])
    check("salas iniciais são reveladas", (2, 2) in room.explored and (7, 2) in room.explored)
    payload = room._game_state_payload()
    check("game_state expõe start_mode", payload["start_mode"] == "hero_spawns")
    check("game_state expõe hero_spawns", len(payload["hero_spawns"]) == 2)

    room.players["p1"]["pos"] = [4, 4]
    room.players["p2"]["pos"] = [6, 4]
    check("objetivo exige todos os heróis", room._objetivo_cumprido(room.objectives["primary"]))


def main():
    test_validation()
    asyncio.run(test_runtime())
    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
