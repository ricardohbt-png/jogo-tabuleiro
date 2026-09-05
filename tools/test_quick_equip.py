"""Regressões do equipamento rápido.

Roda da raiz: python tools/test_quick_equip.py
"""
import asyncio
import os
import sys
from copy import deepcopy

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, SHOP_ARMORS, SHOP_WEAPONS, make_player


def setup():
    room = GameRoom("TEST")
    errors = []

    async def noop(*_args, **_kwargs):
        pass

    async def capture(_pid, msg, *_args, **_kwargs):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errors.append(str(msg.get("msg", "")))

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.broadcast_city_state = noop
    room.send_to = capture
    room.phase = "city"
    room.errors = errors
    return room


def item(source, item_id):
    return deepcopy(next(entry for entry in source if entry["id"] == item_id))


def check(label, condition):
    print(("✅" if condition else "❌") + " " + label)
    return bool(condition)


async def main():
    ok = True

    # Troca normal: o item antigo volta exatamente ao índice de onde saiu o novo.
    room = setup()
    hero = make_player("p1", "Victor", "warrior", 0)
    room.players["p1"] = hero
    old_weapon = deepcopy(hero["gear"]["weapon"])
    hero["bag"] = [item(SHOP_WEAPONS, "dagger"), item(SHOP_WEAPONS, "longsword")]
    await room.handle_quick_equip_from_bag("p1", 1)
    ok &= check("equipa a arma escolhida", hero["gear"]["weapon"]["id"] == "longsword")
    ok &= check("arma anterior ocupa o índice original", hero["bag"][1]["id"] == old_weapon["id"])

    # Uma arma de duas mãos precisa acomodar arma principal + escudo removidos.
    room = setup()
    hero = make_player("p1", "Victor", "warrior", 0)
    room.players["p1"] = hero
    hero["gear"]["off_hand"] = item(SHOP_ARMORS, "escudo_p")
    two_handed = item(SHOP_WEAPONS, "espada2m")
    hero["bag"] = [two_handed] + [item(SHOP_WEAPONS, "dagger") for _ in range(hero["bag_size"] - 1)]
    original_weapon = deepcopy(hero["gear"]["weapon"])
    await room.handle_quick_equip_from_bag("p1", 0)
    ok &= check("recusa duas mãos com bolsa cheia", hero["gear"]["weapon"]["id"] == original_weapon["id"])
    ok &= check("avisa falta de espaço", any("Inventário cheio" in error for error in room.errors))

    # Com uma vaga real extra, guarda as duas peças removidas e equipa a arma.
    room = setup()
    hero = make_player("p1", "Victor", "warrior", 0)
    room.players["p1"] = hero
    hero["gear"]["off_hand"] = item(SHOP_ARMORS, "escudo_p")
    old_weapon = deepcopy(hero["gear"]["weapon"])
    hero["bag"] = [item(SHOP_WEAPONS, "espada2m")] + [item(SHOP_WEAPONS, "dagger") for _ in range(hero["bag_size"] - 2)]
    await room.handle_quick_equip_from_bag("p1", 0)
    ok &= check("equipa arma de duas mãos com vaga", hero["gear"]["weapon"]["id"] == "espada2m")
    ok &= check("libera a mão secundária", hero["gear"]["off_hand"] is None)
    ok &= check("arma anterior ocupa o índice zero", hero["bag"][0]["id"] == old_weapon["id"])
    ok &= check("escudo volta para a bolsa", any(entry["id"] == "escudo_p" for entry in hero["bag"]))

    raise SystemExit(0 if ok else 1)


asyncio.run(main())
