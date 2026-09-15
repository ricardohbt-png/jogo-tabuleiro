"""Testes da armadilha Fosso.

Roda da raiz: python tools/test_fosso.py
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
    meta = ARMADILHAS.get("fosso")
    check("armadilha no catálogo", bool(meta))
    check("Reflexos CD 15 e dano 1d6",
          meta and meta["save"] == "reflexos" and meta["dificuldade"] == 15
          and meta["special"] == "fosso")
    root = os.path.dirname(os.path.dirname(__file__))
    game_js = open(os.path.join(root, "game.js"), encoding="utf-8").read()
    check("imagem dedicada no cliente", "fosso: 'armadilha_fosso.png'" in game_js)

    room = setup()
    player = make_player("p1", "Victor", "warrior", 0)
    player["hp"] = player["max_hp"] = 40
    room.players[player["id"]] = player
    arm = {"id": "pit-1", "tipo": "fosso", "pos": [5, 5], "ativada": False}
    room.armadilhas = [arm]

    old_randint = server.random.randint
    server.random.randint = fixed_rng(1)
    try:
        await room._disparar_armadilha(player, arm)
    finally:
        server.random.randint = old_randint
    failed = trap_messages(room, "p1")
    check("falha envia popup", failed and failed[0]["sucesso"] is False)
    check("falha causa 1d6", failed and failed[0]["dano"] == 3 and player["hp"] == 37)
    check("perde movimento e fica oculto", player.get("moves_left") == 0
          and player.get("movimento_perdido") and player.get("fosso_oculto")
          and player.get("fosso_pular_proximo_turno"))
    check("armadilha é consumida", room.armadilhas == [])
    hp_before = player["hp"]
    await room._dano_em_alvo(player, 20, "fisico")
    check("oculto não recebe dano", player["hp"] == hp_before)
    check("oculto não é alvo vivo", not room._alvo_vivo({"kind": "player", "obj": player}))

    room = setup()
    passed_player = make_player("p-save", "Rita", "warrior", 0)
    passed_player["hp"] = passed_player["max_hp"] = 40
    room.players[passed_player["id"]] = passed_player
    safe_arm = {"id": "pit-safe", "tipo": "fosso", "pos": [5, 5], "ativada": False}
    room.armadilhas = [safe_arm]
    old_randint = server.random.randint
    server.random.randint = fixed_rng(15)
    try:
        await room._disparar_armadilha(passed_player, safe_arm)
    finally:
        server.random.randint = old_randint
    safe = trap_messages(room, "p-save")
    check("sucesso no Reflexos nega todos os efeitos", safe and safe[0]["sucesso"]
          and passed_player["hp"] == 40 and not passed_player.get("fosso_oculto"))

    room = setup()
    p1 = make_player("p1", "A", "warrior", 0)
    p2 = make_player("p2", "B", "mage", 1)
    room.players = {"p1": p1, "p2": p2}
    room.player_order = ["p1", "p2"]
    # Caminho REAL do jogo: fila de iniciativa (o fallback sem iniciativa
    # de handle_end_turn foi removido). Ordem fixa p1 → p2.
    room.initiative_active = True
    room.initiative_order = [{"kind": "player", "id": "p1", "seq": 0, "initiative": 10},
                             {"kind": "player", "id": "p2", "seq": 1, "initiative": 9}]
    room.initiative_index = 0
    p2["fosso_oculto"] = True
    p2["fosso_pular_proximo_turno"] = True
    await room.handle_end_turn("p1")
    check("próximo turno inteiro fica perdido", room.current_pid() == "p2"
          and p2.get("fosso_turno_perdido") and p2.get("fosso_oculto")
          and p2.get("moves_left") == 0 and p2.get("action_done"))
    await room.handle_end_turn("p2")
    check("reaparece após encerrar a rodada perdida", not p2.get("fosso_oculto")
          and not p2.get("fosso_turno_perdido"))

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
