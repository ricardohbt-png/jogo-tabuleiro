"""Testes das poções de cura do Templo.
Roda da raiz: python tools/test_potions.py
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
from server import GameRoom, SHOP_TEMPLE, make_player

PASS = FAIL = 0

def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  OK  {name}")
    else:
        FAIL += 1
        print(f"  XX  {name}")

def potion(item_id):
    return deepcopy(next(i for i in SHOP_TEMPLE if i["id"] == item_id))

def setup():
    room = GameRoom("POTION")
    async def noop(*args, **kwargs):
        pass
    room.gm_say = noop
    room.push_state = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    player = make_player("p1", "Teste", "warrior", 0)
    room.players["p1"] = player
    return room, player

async def main():
    print("\n[1] Catálogo do Templo")
    small = potion("health_potion_small")
    normal = potion("health_potion")
    concentrated = potion("health_potion_concentrated")
    improved = potion("health_potion_improved")
    regeneration = potion("regeneration_potion")
    check("pequena cura 5 e custa 40% arredondado", small["value"] == 5 and small["price"] == 3)
    check("concentrada custa cinco vezes a normal", concentrated["price"] == normal["price"] * 5)
    check("concentrada começa com três doses", concentrated["max_uses"] == 3 and concentrated["uses_left"] == 3)
    check("aprimorada cura 20 e custa três vezes a normal", improved["value"] == 20 and improved["price"] == normal["price"] * 3)
    check("regeneração tem reserva 10 e custa duas vezes a normal", regeneration["value"] == 10 and regeneration["price"] == normal["price"] * 2)

    print("\n[2] Uso da concentrada")
    room, player = setup()
    player["bag"] = [concentrated]
    for expected_uses in (2, 1):
        player["hp"] = 1
        player["bonus_action_used"] = False
        await room.handle_use_item("p1", "health_potion_concentrated")
        check(f"cura 10 HP e mantém a dose {expected_uses}",
              player["hp"] == 11 and player["bag"] == [concentrated]
              and concentrated["uses_left"] == expected_uses)

    player["hp"] = 1
    player["bonus_action_used"] = False
    await room.handle_use_item("p1", "health_potion_concentrated")
    check("terceira dose cura e remove a poção", player["hp"] == 11 and not player["bag"])

    print("\n[3] Regeneração da poção")
    room, player = setup()
    player["bag"] = [regeneration]
    player["hp"] = player["max_hp"]
    await room.handle_use_item("p1", "regeneration_potion")
    check("ativa a reserva e consome o frasco", player.get("potion_regen_pool") == 10 and not player["bag"])
    await room._processar_regeneracao_pocao_turno(player)
    check("HP cheio preserva toda a reserva", player.get("potion_regen_pool") == 10)
    player["hp"] = player["max_hp"] - 1
    await room._processar_regeneracao_pocao_turno(player)
    check("cura 1 e reduz a reserva só quando necessário", player["hp"] == player["max_hp"] and player.get("potion_regen_pool") == 9)

    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    return FAIL

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
