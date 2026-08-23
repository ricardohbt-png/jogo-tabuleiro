"""Regressão do Jato de Ácido (armadilha colocável).
Roda da raiz: python tools/test_jato_acido.py
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
from server import GameRoom, make_player, ARMADILHAS


def setup():
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room.phase = "playing"
    room.players = {}
    room.monsters = {}
    room.armadilhas = []
    room.sent = []

    async def capture(pid, message):
        room.sent.append((pid, message))

    room.send_to = capture
    return room


def trap_messages(room, pid):
    return [message for target, message in room.sent
            if target == pid and message.get("type") == "trap_result"]


def fixed_rng(d20):
    def randint(a, b):
        return d20 if b == 20 else 3
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
    check("armadilha no catálogo", "jato_acido" in ARMADILHAS)
    meta = ARMADILHAS["jato_acido"]
    check("Reflexos CD 18", meta["save"] == "reflexos" and meta["dificuldade"] == 18)
    check("imagem dedicada no cliente", "armadilha_acido.png" in open(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "game.js"),
        encoding="utf-8").read())

    room = setup()
    player = make_player("p1", "Victor", "warrior", 0)
    room.players[player["id"]] = player
    player["ref_"] = 0
    player["hp"] = player["max_hp"] = 40
    player["gear"]["head"] = {"id": "elmo_teste", "name": "Elmo de Teste", "item_slot": "head", "effect": "def_", "value": 1}
    player["gear"]["boots"] = {"id": "botas_teste", "name": "Botas de Teste", "item_slot": "boots", "effect": "spd", "value": 1}
    arm = {"id": "acid-1", "tipo": "jato_acido", "pos": [5, 5], "ativada": False}
    room.armadilhas = [arm]

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)  # falha o save; dados de dano = 3 + 3
    try:
        await room._disparar_armadilha(player, arm)
    finally:
        server.random.randint = old_randint

    first = trap_messages(room, "p1")
    check("falha envia trap_result", len(first) == 1 and first[0]["sucesso"] is False)
    check("falha causa 2d6", first and first[0]["dano"] == 6)
    check("residual é metade do dano aplicado", arm["efeitos_ativos"][0]["valor"] == 3)
    check("corrosão escolhe equipamento permitido", player.get("corrosao", {}).get("elmo_lvl", 0)
          + player.get("corrosao", {}).get("botas_lvl", 0)
          + player.get("corrosao", {}).get("armadura_lvl", 0)
          + player.get("corrosao", {}).get("arma_lvl", 0)
          + player.get("corrosao", {}).get("escudo_lvl", 0) == 1)
    check("popup descreve corrosão", any("corrosão" in text for text in first[0]["efeitos_extra"]))

    room.round_num += 1
    await room._processar_efeitos_armadilha_turno()
    ticks = [message for message in trap_messages(room, "p1") if message.get("tick")]
    check("rodada seguinte aplica metade", ticks and ticks[0]["dano"] == 3)
    check("armadilha é removida após o residual", room.armadilhas == [])

    room = setup()
    player = make_player("p2", "Victor", "warrior", 0)
    room.players[player["id"]] = player
    player["ref_"] = 0
    arm = {"id": "acid-2", "tipo": "jato_acido", "pos": [5, 5], "ativada": False}
    room.armadilhas = [arm]
    old_randint = server.random.randint
    server.random.randint = fixed_rng(18)  # 18 + 0 >= CD 18
    try:
        await room._disparar_armadilha(player, arm)
    finally:
        server.random.randint = old_randint
    success = trap_messages(room, "p2")
    check("sucesso nega o efeito", success and success[0]["sucesso"] is True
          and success[0]["dano"] == 0 and not player.get("corrosao"))
    check("sucesso não agenda residual", not arm.get("efeitos_ativos"))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
