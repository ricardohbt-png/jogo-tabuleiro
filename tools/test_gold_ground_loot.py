"""Valida pilha de ouro no chão e baú para loot misto.

Roda da raiz: python tools/test_gold_ground_loot.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server as S
from server import FLOOR, WALL, GameRoom, make_player


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  XX  {name}")


def setup():
    room = GameRoom("GOLD_TEST")
    room.tiles = [[FLOOR] * 7 for _ in range(7)]
    room.map_w = room.map_h = 7
    room.players = {}
    room.monsters = {}
    room.chests = {}
    room.ground_items = {}
    room._decor_block_tiles = set()
    room._mat_solid_tiles = set()
    room._mat_occludes_tiles = set()
    room._ponte_tiles = set()
    room._is_closed_door = lambda x, y: False
    room._blocks_tile = lambda x, y: (
        not (0 <= x < room.map_w and 0 <= y < room.map_h)
        or room.tiles[y][x] == WALL
    )

    async def noop(*args, **kwargs):
        return None

    errors = []

    async def send_to(pid, msg, *args, **kwargs):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errors.append(msg.get("msg", ""))

    room.gm_say = noop
    room.push_state = noop
    room.send_to = send_to
    room._test_errors = errors
    player = make_player("p1", "Heroi", "warrior", 0)
    player["pos"] = [3, 3]
    room.players["p1"] = player
    room.phase = "playing"
    return room, player


async def main():
    print("\n[1] Só ouro: pilha no chão")
    room, player = setup()
    outcome = room._spawn_monster_loot([3, 2], 7, [])
    check("ouro cai no chão", outcome == "ground_gold" and len(room.ground_items) == 1)
    check("quantidade e ID visual preservados", next(iter(room.ground_items.values()))["amount"] == 7
          and next(iter(room.ground_items.values()))["item"]["id"] == "gold_coins")
    check("não cria baú para ouro sozinho", not room.chests)

    print("\n[2] Ouro acompanhado de item: baú")
    room, _ = setup()
    item = {"id": "dagger", "name": "Adaga", "emoji": "🗡️"}
    outcome = room._spawn_monster_loot([3, 2], 5, [item])
    chest = next(iter(room.chests.values())) if room.chests else {}
    check("loot misto usa baú", outcome == "chest" and len(room.chests) == 1)
    check("baú mantém ouro e item", chest.get("gold") == 5
          and [it.get("id") for it in chest.get("items", [])] == ["dagger"])
    check("loot misto não duplica ouro no chão", not room.ground_items)

    print("\n[3] Coleta do ouro pelo chão")
    room, player = setup()
    room._spawn_monster_loot([3, 2], 9, [])
    gid = next(iter(room.ground_items))
    gx, gy = room.ground_items[gid]["pos"]
    player["pos"] = [gx - 1, gy]
    gold_before = player["gold"]
    await room.handle_pickup_item("p1", gid)
    check("ouro creditado sem usar inventário", player["gold"] == gold_before + 9
          and len(player["bag"]) == 0)
    check("pilha removida após a coleta", gid not in room.ground_items)

    print("\n[4] Sem espaço livre: fallback seguro")
    room, _ = setup()
    for y in range(room.map_h):
        for x in range(room.map_w):
            if (x, y) != (2, 2):
                room.tiles[y][x] = WALL
    outcome = room._spawn_monster_loot([2, 2], 4, [])
    check("sem casa livre conserva o ouro em baú", outcome == "chest"
          and len(room.chests) == 1 and next(iter(room.chests.values()))["gold"] == 4)

    print(f"\n===== GOLD GROUND LOOT: {PASS} OK, {FAIL} falhas =====")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
