"""Testes do Baú Engolidor.

Roda da raiz: python tools/test_bau_engolidor.py
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
    room.player_order = ["p1"]
    room.turn_index = 0
    room.players = {}
    room.monsters = {}
    room.armadilhas = []
    room.traps = []
    room.sent = []
    room.map_w = room.map_h = 10
    room.tiles = [[server.FLOOR for _ in range(room.map_w)] for _ in range(room.map_h)]

    async def noop(*args, **kwargs):
        pass

    async def capture(pid, message):
        room.sent.append((pid, message))

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = capture
    room._blocks_tile = lambda x, y: (x, y) == (5, 5)
    room._entity_blocks = lambda *args, **kwargs: False
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
    meta = ARMADILHAS.get("bau_engolidor")
    check("armadilha no catálogo", bool(meta))
    check("Reflexos CD 20 e escape por Força CD 20",
          meta and meta["save"] == "reflexos" and meta["dificuldade"] == 20
          and meta["escape_save"] == "forca" and meta["escape_dificuldade"] == 20)
    root = os.path.dirname(os.path.dirname(__file__))
    game_js = open(os.path.join(root, "game.js"), encoding="utf-8").read()
    check("imagem dedicada no cliente", "bau_engolidor: 'bau_engolidor.png'" in game_js)
    check("estado visual de peão oculto", "p.bau_engolido" in game_js)

    room = setup()
    player = make_player("p1", "Victor", "rogue", 0)
    player["pos"] = [5, 4]
    player["gold"] = 100
    player["fome"] = player["sede"] = 100
    player["guild_owned"] = {"especializacoes": ["ladino_bau_engolidor"]}
    room.players[player["id"]] = player
    decor = {"id": "obj1", "type": "barril", "pos": [5, 5], "facing": [0, 1],
             "trap": None, "trap_triggered": False, "trap_disarmed": False,
             "trap_revealed": False, "chest_trap_monster_type": None}
    room.decorations = [decor]

    await room.handle_criar_armadilha("p1", {
        "tipo": "bau_engolidor", "decor_id": "obj1", "tx": 5, "ty": 5,
    })
    check("colocação fica vinculada ao objeto", decor["trap"] == {"tipo": "bau_engolidor"}
          and not room.armadilhas)

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        player["action_done"] = False
        await room.handle_interagir_decor("p1", "obj1")
    finally:
        server.random.randint = old_randint
    first = trap_messages(room, "p1")
    check("falha no Reflexos prende o herói", player.get("bau_engolido")
          and player.get("bau_engolido_por") == "decor_trap_obj1")
    check("peão é deslocado para o interior do objeto", player["pos"] == [5, 5])
    check("popup informa a prisão", first and first[-1]["sucesso"] is False
          and any("preso" in text for text in first[-1]["efeitos_extra"]))

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        player["action_done"] = False
        await room.handle_escapar_bau("p1")
    finally:
        server.random.randint = old_randint
    check("falha no escape mantém o estado", player.get("bau_engolido") and player["action_done"])

    old_randint = server.random.randint
    server.random.randint = fixed_rng(20)
    try:
        player["action_done"] = False
        await room.handle_escapar_bau("p1")
    finally:
        server.random.randint = old_randint
    check("sucesso em Força liberta o herói", not player.get("bau_engolido")
          and player["pos"] != [5, 5])
    check("armadilha do objeto fica consumida", decor["trap_triggered"] and not decor["trap_disarmed"])

    room2 = setup()
    p2 = make_player("p1", "Victor", "rogue", 0)
    p2["pos"] = [5, 4]
    p2["gold"] = 100
    p2["fome"] = p2["sede"] = 100
    p2["guild_owned"] = {"especializacoes": ["ladino_bau_engolidor"]}
    room2.players[p2["id"]] = p2
    await room2.handle_criar_armadilha("p1", {"tipo": "bau_engolidor", "tx": 5, "ty": 5})
    check("servidor rejeita colocação sem objeto", any("objeto" in m.get("msg", "") for _, m in room2.sent))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
