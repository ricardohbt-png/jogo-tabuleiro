"""Testes da armadilha Guilhotina.

Roda da raiz: python tools/test_guilhotina.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import ARMADILHAS, GameRoom, make_player


def setup():
    room = GameRoom("TEST")
    room.phase = "playing"
    room.players = {}
    room.monsters = {}
    room.armadilhas = []
    room.sent = []

    async def noop(*args, **kwargs):
        pass

    async def capture(pid, message):
        room.sent.append((pid, message))

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = capture
    return room


def fixed_rng(d20):
    def randint(a, b):
        return d20 if b == 20 else 3
    return randint


def trap_messages(room, pid):
    return [m for target, m in room.sent if target == pid and m.get("type") == "trap_result"]


PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


async def main():
    meta = ARMADILHAS.get("guilhotina")
    check("armadilha no catálogo", bool(meta))
    check("Reflexos CD 14 e dano 3d6",
          meta and meta["save"] == "reflexos" and meta["dificuldade"] == 14
          and meta["efeitos"][0]["valor"] == "3d6")
    root = os.path.dirname(os.path.dirname(__file__))
    game_js = open(os.path.join(root, "game.js"), encoding="utf-8").read()
    check("imagem dedicada no cliente", "guilhotina: 'guilhotina.png'" in game_js)

    room = setup()
    player = make_player("p1", "Victor", "warrior", 0)
    player["hp"] = player["max_hp"] = 40
    room.players[player["id"]] = player
    arm = {"id": "guillotine-1", "tipo": "guilhotina", "pos": [5, 5], "ativada": False}
    room.armadilhas = [arm]

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        await room._disparar_armadilha(player, arm)
    finally:
        server.random.randint = old_randint
    failed = trap_messages(room, "p1")
    check("falha envia popup", failed and failed[0]["sucesso"] is False)
    check("falha causa 3d6", failed and failed[0]["dano"] == 9 and player["hp"] == 31)
    check("armadilha é consumida", room.armadilhas == [])

    room = setup()
    player = make_player("p2", "Victor", "warrior", 0)
    player["hp"] = player["max_hp"] = 40
    room.players[player["id"]] = player
    arm = {"id": "guillotine-2", "tipo": "guilhotina", "pos": [5, 5], "ativada": False}
    room.armadilhas = [arm]
    old_randint = server.random.randint
    server.random.randint = fixed_rng(14)
    try:
        await room._disparar_armadilha(player, arm)
    finally:
        server.random.randint = old_randint
    passed = trap_messages(room, "p2")
    check("sucesso no Reflexos evita", passed and passed[0]["sucesso"] is True
          and passed[0]["dano"] == 0 and player["hp"] == 40)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
