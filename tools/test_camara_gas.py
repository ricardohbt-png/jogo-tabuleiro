"""Testes da armadilha Câmara de Gás.

Roda da raiz: python tools/test_camara_gas.py
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
    room.rooms = [{"id": "r1", "x": 0, "y": 0, "w": 5, "h": 5,
                   "cx": 2, "cy": 2, "role": "trap", "cleared": False,
                   "looted": False, "locked": False, "doors": []}]
    room.players = {}
    room.monsters = {}
    room.armadilhas = []
    room.zonas_especiais = []
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
    meta = ARMADILHAS.get("camara_gas")
    check("armadilha no catálogo", bool(meta))
    check("Fortitude CD 13 e duração 1d6+1", meta and meta["special"] == "camara_gas"
          and meta["save"] == "fortitude" and meta["dificuldade"] == 13)
    root = os.path.dirname(os.path.dirname(__file__))
    game_js = open(os.path.join(root, "game.js"), encoding="utf-8").read()
    check("imagem dedicada no cliente", "camara_gas: 'fosso_envenenado.png'" in game_js)
    check("realce verde escuro da sala", "camarasGas" in game_js and "rgba(8,90,25,0.62)" in game_js)

    room = setup()
    p1 = make_player("p1", "A", "warrior", 0)
    p2 = make_player("p2", "B", "mage", 1)
    p1["pos"] = [2, 2]
    p2["pos"] = [3, 3]
    p1["hp"] = p1["max_hp"] = 40
    p2["hp"] = p2["max_hp"] = 40
    room.players = {"p1": p1, "p2": p2}
    arm = {"id": "gas-1", "tipo": "camara_gas", "pos": [2, 2], "ativada": False}
    room.armadilhas = [arm]

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        await room._disparar_armadilha(p1, arm)
    finally:
        server.random.randint = old_randint
    check("disparo cria zona na sala", len(room.zonas_especiais) == 1
          and room.zonas_especiais[0]["tipo"] == "camara_gas"
          and room.zonas_especiais[0]["room_id"] == "r1"
          and room.zonas_especiais[0]["duracao"] == 4)
    check("todos na sala sofrem o teste inicial", p1["hp"] == 37 and p2["hp"] == 37)
    check("armadilha física é consumida", room.armadilhas == [])
    check("popup usa o id da Câmara de Gás", trap_messages(room, "p1")
          and all(m["tipo_id"] == "camara_gas" for m in trap_messages(room, "p1")))

    p2["pos"] = [8, 8]
    hp_before = p2["hp"]
    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        await room._processar_camara_gas_inicio_turno(p2)
    finally:
        server.random.randint = old_randint
    check("quem saiu da sala não sofre o tick", p2["hp"] == hp_before)

    p1["pos"] = [2, 2]
    hp_before = p1["hp"]
    old_randint = server.random.randint
    server.random.randint = fixed_rng(20)
    try:
        await room._processar_camara_gas_inicio_turno(p1)
    finally:
        server.random.randint = old_randint
    check("sucesso em Fortitude evita o dano do turno", p1["hp"] == hp_before)

    room.zonas_especiais[0]["duracao"] = 1
    await room._processar_zonas_turno()
    check("zona desaparece ao fim da duração", room.zonas_especiais == [])

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
