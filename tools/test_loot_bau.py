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

    print("\n[3] _necromante_loot usa defs de loja (vinho/ração de viagem)")
    from server import make_monster, MONSTER_DEFS
    r = setup()
    ndef = next(d for d in MONSTER_DEFS if d.get("type") == "dark_mage")
    # rola 71..90 -> vinho ; 91..95 -> ração
    for alvo_roll, esperado in ((80, "garrafa_vinho"), (93, "racao_viagem")):
        m = make_monster(ndef, {"id": 1, "cx": 2, "cy": 2})
        m["pos"] = [2, 2]
        m["usou_dominar"] = True   # evita o pergaminho de dominar no fim
        _orig = random.randint
        random.randint = lambda a, b: alvo_roll if (a, b) == (1, 100) else _orig(a, b)
        try:
            await r._necromante_loot(m)
        finally:
            random.randint = _orig
        achou = any(it["id"] == esperado
                    for c in r.chests.values() for it in c["items"])
        check(f"necromante larga '{esperado}'", achou)
        r.chests.clear()

    print("\n[4] CHEST_ITEMS podado + catálogo consistente")
    from server import CHEST_ITEMS
    ids_chest = [i["id"] for i in CHEST_ITEMS]
    # A poda tirou os itens que duplicavam a loja (checado logo abaixo); a lista
    # em si cresce com o conteudo autoral, entao NAO se crava o seu tamanho.
    check("a serrilhada continua em CHEST_ITEMS", "sword" in ids_chest, f"tem: {ids_chest}")
    sword = next(i for i in CHEST_ITEMS if i["id"] == "sword")
    check("serrilhada com price 32", sword.get("price") == 32)
    check("serrilhada mantém corrosao_resistente", sword.get("corrosao_resistente") == 1)
    for iid in ("magic_sword", "bow", "shield", "ring", "racao"):
        check(f"'{iid}' saiu do catálogo", iid not in _DUNGEON_ITEM_CATALOG)
    for iid in ("health_potion", "elixir", "antidote", "garrafa_vinho",
                "staff", "chainmail", "leather", "amulet", "boots", "cloak"):
        check(f"'{iid}' permanece no catálogo (loja)", iid in _DUNGEON_ITEM_CATALOG)
    check("health_potion resolve p/ 'Poção de Cura'",
          _DUNGEON_ITEM_CATALOG["health_potion"]["name"] == "Poção de Cura")
    check("sword permanece no catálogo", "sword" in _DUNGEON_ITEM_CATALOG)

    print(f"\n===== {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
