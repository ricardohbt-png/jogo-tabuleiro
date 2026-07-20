"""Testa o loot de baú procedural: sorteia só do pool de poções/consumíveis das
lojas, e todos os ids do pool resolvem no catálogo autoritativo.
Roda da raiz: python tools/test_loot_bau.py"""
import asyncio, sys, os, random
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import (GameRoom, LOOT_POOL_PROCEDURAL, _DUNGEON_ITEM_CATALOG)

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r.broadcast_city_state = noop
    return r

async def main():
    random.seed(3)
    print("\n[1] ids do pool resolvem no catálogo")
    for iid in LOOT_POOL_PROCEDURAL:
        check(f"'{iid}' está no catálogo", iid in _DUNGEON_ITEM_CATALOG)

    print("\n[2] baú procedural só contém itens do pool")
    r = setup()
    fora = []
    for i in range(200):
        await r._spawn_chest_from_room({"cx": 5, "cy": 5, "looted": False})
    for chest in r.chests.values():
        for it in chest["items"]:
            if it["id"] not in LOOT_POOL_PROCEDURAL:
                fora.append(it["id"])
    check("nenhum item fora do pool em 200 baús", fora == [], f"fora: {set(fora)}")
    check("todo baú tem ao menos 1 item", all(c["items"] for c in r.chests.values()))

    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
