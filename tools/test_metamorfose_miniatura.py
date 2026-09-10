"""Roda da raiz: python tools/test_metamorfose_miniatura.py"""
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


async def main():
    room = GameRoom("TEST")

    async def noop(*args, **kwargs):
        pass

    room.broadcast = noop
    room.gm_say = noop
    caster = make_player("p1", "Pedro", "mage", 0)
    room.players["p1"] = caster
    monster = {
        "id": "m1", "type": "goblin", "name": "Goblin", "image": "goblinCombatente",
        "pos": [3, 3], "hp": 8, "max_hp": 8, "cr": 0.25,
    }
    room.monsters["m1"] = monster
    form = room._metamorfose_forma("rato")

    print("\n[1] Metamorfose troca a miniatura do monstro")
    await room._aplicar_metamorfose(caster, monster, form)
    check("marca a forma como ativa", monster.get("metamorfose_ativa") is True)
    check("registra a forma rato", monster.get("metamorfose_forma_type") == "rato")
    check("troca image para rato", monster.get("image") == "rato")
    check("define pawn_override rato", monster.get("pawn_override") == "rato")

    print("\n[2] Reversão restaura a miniatura original")
    await room._reverter_metamorfose(monster)
    check("desativa a metamorfose", monster.get("metamorfose_ativa") is False)
    check("restaura image original", monster.get("image") == "goblinCombatente")

    print("\n[3] Metamorfose troca a miniatura do jogador")
    target = make_player("p2", "Aliado", "warrior", 1)
    room.players["p2"] = target
    await room._aplicar_metamorfose(caster, target, form)
    check("ativa a forma no jogador", target.get("metamorfose_ativa") is True)
    check("define pawn_override rato no jogador", target.get("pawn_override") == "rato")
    check("registra a forma no jogador", target.get("metamorfose_forma_type") == "rato")
    await room._reverter_metamorfose(target)
    check("restaura o jogador sem pawn_override", not target.get("pawn_override"))

    print(f"\n{'=' * 40}\nPASS: {PASS}  FAIL: {FAIL}\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
