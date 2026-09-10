"""Roda da raiz: python tools/test_magias_teste_livre.py"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup():
    room = GameRoom("TEST")
    room.phase = "playing"
    room.player_order = ["p1"]
    room.turn_index = 0
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room._executar_magia_grimorio = noop
    room._teleporte_alvo_visivel = lambda *args, **kwargs: True
    return room


async def main():
    room = setup()
    player = make_player("p1", "Pedro", "mage", 0)
    player["level"] = 1
    player["magias_conhecidas"] = []
    player["fome"] = 0
    player["sede"] = 0
    player["slots_cooldown"] = {"primeiro": [], "segundo": [], "terceiro": [], "quarto": [11, 11, 11]}
    room.players["p1"] = player

    errors = []

    async def capture_error(pid, message):
        if message.get("type") == "error":
            errors.append(message.get("msg", ""))

    room.send_to = capture_error

    print("\n[1] Metamorfose livre para teste")
    await room.handle_magia("p1", {
        "magia_id": "metamorfose",
        "target_id": "p1",
        "forma_id": "pombo",
    })
    check("aceita sem magia conhecida", not errors)
    check("não consome fome", player["fome"] == 0)
    check("não consome sede", player["sede"] == 0)
    check("não consome slot de 4º", player["slots_cooldown"]["quarto"] == [11, 11, 11])

    print("\n[2] Teleporte livre para teste mesmo sem slots")
    errors.clear()
    player["action_done"] = False
    await room.handle_magia("p1", {"magia_id": "teleporte", "target_id": "p1"})
    check("aceita sem slot disponível", not errors)
    check("continua sem consumir fome/sede", player["fome"] == 0 and player["sede"] == 0)
    check("continua sem consumir slot", player["slots_cooldown"]["quarto"] == [11, 11, 11])

    print(f"\n{'=' * 40}\nPASS: {PASS}  FAIL: {FAIL}\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
