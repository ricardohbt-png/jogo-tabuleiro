"""Heróis temporários na mesa de teste do editor.
Roda da raiz: python tools/test_herois_teste_editor.py"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom

PASS = FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def room():
    r = GameRoom("TEST_HEROES")
    r.phase = "playing"
    r.test_mode = True
    r.master_pid = "mestre"
    r.map_w = r.map_h = 8
    r.tiles = [[S.FLOOR for _ in range(8)] for _ in range(8)]
    r.chests = {}
    r.ground_items = {}
    r.monsters = {}

    async def noop(*args, **kwargs):
        pass

    r.push_state = noop
    r.send_to = noop
    return r


async def main():
    r = room()
    await r.handle_mestre_adicionar_heroi_teste("mestre", "warrior", 2, 3)
    p = r.players.get("test_hero_warrior")
    check("adiciona guerreiro temporário", p is not None and p.get("test_hero"))
    check("posiciona na casa pedida", p and p["pos"] == [2, 3])
    check("usa ficha real da classe", p and p["class_id"] == "warrior" and p["alive"])

    await r.handle_mestre_adicionar_heroi_teste("mestre", "warrior", 4, 4)
    check("não duplica a mesma classe", len(r.players) == 1)

    r.monsters["grande"] = {"id": "grande", "hp": 10, "pos": [4, 4], "size": [2, 2]}
    await r.handle_mestre_adicionar_heroi_teste("mestre", "mage", 5, 5)
    check("recusa casa dentro de monstro grande", "test_hero_mage" not in r.players)

    await r.handle_mestre_adicionar_heroi_teste("intruso", "mage", 1, 1)
    check("somente o mestre pode adicionar", "test_hero_mage" not in r.players)

    print(f"\nPASS={PASS} FAIL={FAIL}")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
