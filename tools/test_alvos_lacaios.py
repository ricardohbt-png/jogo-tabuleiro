"""Regressão: a IA inimiga percebe e ataca lacaios dos jogadores."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import server as S
from server import GameRoom, make_monster, make_player


def room():
    r = GameRoom("TEST")
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * r.map_w for _ in range(r.map_h)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 12, "h": 12,
                "cx": 6, "cy": 6, "locked": False}]
    r.monsters = {}
    r.chests = {}
    r.ground_items = {}
    r._falas = []
    async def noop(*_args, **_kwargs):
        pass
    r.broadcast = noop
    r.push_state = noop
    r.gm_say = noop
    r.send_to = noop
    return r


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print("  ✅", label)


async def main():
    r = room()
    p = make_player("p1", "Pedro", "mage", 0)
    p.update({"alive": True, "connected": True, "pos": [10, 10]})
    r.players["p1"] = p
    r.connections["p1"] = object()

    servo = {
        "id": "servo1", "tipo": "elemental", "tipo_elemental": "pedra",
        "nome": "Elemental de Pedra", "owner": "p1", "pos": [4, 3],
        "vida_atual": 20, "vida_max": 20, "ac": 1,
    }
    p["animados"] = [servo]

    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == "goblin_combatente")
    monstro = make_monster(mdef, r.rooms[0])
    monstro.update({"id": "g1", "pos": [4, 2], "room_id": "r0", "alertado": True})
    r.monsters["g1"] = monstro

    alvos = r._alvos_hostis_para_monstros()
    escolha = r._get_monster_primary_target(monstro, alvos)
    check("servo entra nos alvos hostis", any(t["obj"] is servo for t in alvos))
    check("servo pode ser escolhido como alvo", escolha["obj"] is servo)

    vida_antes = servo["vida_atual"]
    await r.gm_phase(monstro)
    check("inimigo ataca o servo sem ataque prévio do jogador",
          servo["vida_atual"] < vida_antes)

    print("\n=== alvos de lacaios: passou ===")


if __name__ == "__main__":
    asyncio.run(main())
