"""Regressão do Teto Esmagador (armadilha de sala).
Roda da raiz: python tools/test_teto_esmagador.py
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
from server import GameRoom, make_player, make_monster, MONSTER_DEFS, ARMADILHAS


def setup():
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room._conceder_xp_armadilha = noop
    room.phase = "playing"
    room.rooms = [{"id": 7, "x": 2, "y": 2, "w": 5, "h": 5}]
    room.players = {}
    room.monsters = {}
    room.armadilhas = []
    room.prisoner = None
    room.sent = []

    async def capture(pid, message):
        room.sent.append((pid, message))

    room.send_to = capture
    return room


def trap_messages(room, pid):
    return [message for target, message in room.sent
            if target == pid and message.get("type") == "trap_result"]


def fixed_rng(values):
    it = iter(values)

    def randint(a, b):
        return next(it) if b == 20 else 3

    return randint


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
    check("armadilha no catálogo", "teto_esmagador" in ARMADILHAS)
    meta = ARMADILHAS["teto_esmagador"]
    check("Reflexos CD 20", meta["save"] == "reflexos" and meta["dificuldade"] == 20)
    check("imagem dedicada no cliente", "teto_esmagador.png" in open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "game.js"),
        encoding="utf-8").read())

    room = setup()
    p1 = make_player("p1", "A", "warrior", 0)
    p1["pos"] = [3, 3]
    p1["ref_"] = 0
    p2 = make_player("p2", "B", "rogue", 1)
    p2["pos"] = [6, 6]
    p2["ref_"] = 0
    outside = make_player("p3", "C", "mage", 2)
    outside["pos"] = [9, 9]
    outside["ref_"] = 0
    room.players = {"p1": p1, "p2": p2, "p3": outside}

    monster_def = next(m for m in MONSTER_DEFS if m["type"] == "urso_negro")
    monster = make_monster(monster_def, {"id": 11, "cx": 4, "cy": 4})
    monster["pos"] = [4, 4]
    monster["hp"] = monster["max_hp"] = 40
    room.monsters[monster["id"]] = monster
    room.prisoner = {"id": "__prisioneiro__", "pos": [5, 5], "alive": True,
                     "hp": 7, "max_hp": 7, "ref_": 0,
                     "rescuer_pid": "p1", "nome": "Prisioneiro"}

    arm = {"id": "ceiling-1", "tipo": "teto_esmagador", "pos": [3, 3], "ativada": False}
    room.armadilhas = [arm]
    old_randint = server.random.randint
    # ordem: p1 falha, p2 passa, monstro falha, prisioneiro passa
    server.random.randint = fixed_rng([1, 20, 1, 20])
    try:
        await room._disparar_armadilha(p1, arm)
    finally:
        server.random.randint = old_randint

    p1_msgs = trap_messages(room, "p1")
    p2_msgs = trap_messages(room, "p2")
    check("remove após uma ativação", room.armadilhas == [])
    check("herói na sala falha e sofre 4d6", p1_msgs and p1_msgs[0]["dano"] == 12
          and p1["hp"] == p1["max_hp"] - 12)
    check("herói na sala que passa evita", p2_msgs and p2_msgs[0]["sucesso"] is True
          and p2_msgs[0]["dano"] == 0 and p2["hp"] == p2["max_hp"])
    check("monstro na sala também sofre o dano", monster["hp"] == 28)
    check("prisioneiro recebe o próprio resultado", len(p1_msgs) == 2)
    check("herói fora da sala não é afetado", outside["hp"] == outside["max_hp"]
          and trap_messages(room, "p3") == [])

    room = setup()
    p = make_player("p4", "D", "warrior", 0)
    p["pos"] = [3, 3]
    p["ref_"] = 0
    room.players[p["id"]] = p
    arm = {"id": "ceiling-2", "tipo": "teto_esmagador", "pos": [3, 3], "ativada": False}
    room.armadilhas = [arm]
    old_randint = server.random.randint
    server.random.randint = fixed_rng([20])
    try:
        await room._disparar_armadilha(p, arm)
    finally:
        server.random.randint = old_randint
    success = trap_messages(room, "p4")
    check("sucesso nega o dano", success and success[0]["sucesso"] is True
          and success[0]["dano"] == 0 and p["hp"] == p["max_hp"])

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
