"""Roda da raiz: python -X utf8 tools/test_teleporte_animation.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")


def setup():
    room = GameRoom("TEST")
    room.phase = "playing"
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    room.players = {}
    room.monsters = {}
    room._teleporte_alvo_visivel = lambda *args, **kwargs: True
    room._teleporte_destinos_validos = lambda *args, **kwargs: ([[2, 2]], 15)
    events = []
    direct = []

    async def broadcast(msg):
        events.append(dict(msg))

    async def send_to(pid, msg):
        direct.append((pid, dict(msg)))

    async def noop(*args, **kwargs):
        pass

    room.broadcast = broadcast
    room.send_to = send_to
    room.gm_say = noop
    room.push_state = noop
    return room, events, direct


async def run_case(target_kind):
    room, events, direct = setup()
    caster = make_player("caster", "Pedro", "mage", 0)
    caster["pos"] = [1, 1]
    room.players[caster["id"]] = caster

    if target_kind == "self":
        target = caster
    elif target_kind == "player":
        target = make_player("target", "Ally", "warrior", 1)
        target["pos"] = [3, 1]
        room.players[target["id"]] = target
    else:
        target = {"id": "monster", "name": "Monstro", "pos": [3, 1], "hp": 10}
        room.monsters[target["id"]] = target
        room._testar_save = lambda *args, **kwargs: (False, 2, 0, 2)

    await room._executar_teleporte(caster, server.GRIMORIO["teleporte"],
                                    {"target_id": target["id"]})
    start = next((m for m in events if m.get("type") == "spell_animation"
                  and m.get("phase") == "start"), None)
    check(f"{target_kind}: evento inicial contém animation_id", bool(start and start.get("animation_id")))

    if target_kind == "player":
        prompt = next((m for pid, m in direct if pid == target["id"]
                       and m.get("type") == "teleporte_save_prompt"), None)
        check("jogador: pedido de resistência emitido", prompt is not None)
        await room.handle_teleporte_consent(target["id"], prompt["request_id"],
                                             falha_voluntaria=True)

    pending = room._pending_teleporte
    check(f"{target_kind}: animation_id sobrevive à escolha de destino",
          bool(pending and pending.get("animation_id") == start["animation_id"]))
    destination_prompt = next((m for pid, m in direct if pid == caster["id"]
                               and m.get("type") == "teleporte_destino_prompt"), None)
    check(f"{target_kind}: escolha de destino emitida", destination_prompt is not None)
    await room.handle_teleporte_destino(caster["id"], destination_prompt["request_id"], 2, 2)
    resolved = next((m for m in events if m.get("type") == "spell_animation"
                     and m.get("phase") == "resolve"), None)
    check(f"{target_kind}: resolve fecha a mesma animação",
          bool(resolved and resolved.get("animation_id") == start["animation_id"]
               and resolved.get("success") is True))


async def main():
    for kind in ("self", "player", "monster"):
        await run_case(kind)

    room, events, _direct = setup()
    caster = make_player("caster", "Pedro", "mage", 0)
    caster["pos"] = [1, 1]
    room.players[caster["id"]] = caster
    room._teleporte_destinos_validos = lambda *args, **kwargs: ([], 15)
    await room._executar_teleporte(caster, server.GRIMORIO["teleporte"],
                                    {"target_id": caster["id"]})
    start = next(m for m in events if m.get("phase") == "start")
    resolved = next((m for m in events if m.get("phase") == "resolve"), None)
    check("sem destino livre: animação termina como falha",
          bool(resolved and resolved.get("animation_id") == start.get("animation_id")
               and resolved.get("success") is False))
    print(f"\nTELEPORTE ANIMATION: {PASS} OK, {FAIL} FAIL")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
