"""Testes das regras do terreno Água. Execute: python tools/test_agua.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, MATERIAIS, make_player


def check(label, condition):
    assert condition, label
    print("OK:", label)


def actor_with_armor(armor_id=None):
    p = make_player("water_test", "Teste", "warrior", 0)
    p["pos"] = [1, 1]
    p["gear"]["armor"] = ({"id": armor_id} if armor_id else None)
    return p


def main():
    room = GameRoom("WATER_TEST")
    room.materiais = {(1, 1): "agua", (2, 1): "agua", (3, 1): "agua_profunda"}

    check("água é piso atravessável", MATERIAIS["agua"]["categoria"] == "piso" and not MATERIAIS["agua"]["solido"])
    check("sem armadura: -1", room._water_turn_moves(actor_with_armor(), 5) == 4)
    check("leve: -2", room._water_turn_moves(actor_with_armor("leather"), 5) == 3)
    check("média: -3", room._water_turn_moves(actor_with_armor("chainmail"), 5) == 2)
    check("pesada: uma casa", room._water_turn_moves(actor_with_armor("plate"), 5) == 1)
    reset_heavy = actor_with_armor("plate")
    reset_heavy["_water_heavy_step_used"] = True
    room._water_turn_moves(reset_heavy, 5)
    check("rodada nova libera a única casa pesada", not reset_heavy.get("_water_heavy_step_used"))

    heavy = actor_with_armor("plate")
    heavy["pos"] = [0, 1]
    heavy["moves_left"] = 5
    room._apply_water_entry_penalty(heavy, 1, 1)
    heavy["moves_left"] -= 1
    check("pesada para após entrar na água", heavy["moves_left"] == 0)

    plain = actor_with_armor()
    plain["pos"] = [0, 1]
    plain["moves_left"] = 5
    room._apply_water_entry_penalty(plain, 1, 1)
    check("entrada na água aplica -1 uma vez", plain["moves_left"] == 4)
    room._apply_water_entry_penalty(plain, 2, 1)
    check("água contínua não cobra duas vezes", plain["moves_left"] == 4)

    # Água profunda limita o movimento inteiro pelo tipo de proteção.
    check("água profunda é piso atravessável", MATERIAIS["agua_profunda"]["categoria"] == "piso" and not MATERIAIS["agua_profunda"]["solido"])
    deep_plain = actor_with_armor(); deep_plain["pos"] = [3, 1]
    check("profunda sem armadura: metade", room._water_turn_moves(deep_plain, 6) == 3)
    deep_light = actor_with_armor("leather"); deep_light["pos"] = [3, 1]
    check("profunda leve: um terço", room._water_turn_moves(deep_light, 6) == 2)
    deep_medium = actor_with_armor("chainmail"); deep_medium["pos"] = [3, 1]
    check("profunda média: um quarto arredondado para baixo", room._water_turn_moves(deep_medium, 6) == 1)
    deep_heavy = actor_with_armor("plate"); deep_heavy["pos"] = [3, 1]
    check("profunda pesada: uma casa", room._water_turn_moves(deep_heavy, 6) == 1)
    natural_armor_monster = {"pos": [3, 1], "natural_armor": 2}
    check("monstro com armadura natural conta como leve", room._water_turn_moves(natural_armor_monster, 6) == 2)
    natural_armor_monster["pos"] = [1, 1]
    check("armadura natural também afeta água rasa", room._water_turn_moves(natural_armor_monster, 6) == 4)
    equipped_armor_monster = {"pos": [3, 1], "natural_armor": 6,
                               "equipment_items": [{"kind": "armor", "armor_category": "pesada"}]}
    check("armadura equipada do monstro tem prioridade", room._water_turn_moves(equipped_armor_monster, 6) == 1)
    print("\nTerreno Água: OK")


if __name__ == "__main__":
    main()
