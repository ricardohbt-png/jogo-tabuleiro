"""Verificação do catálogo de categorias e materiais das armaduras.

Execute da raiz: python tools/test_armaduras.py
"""
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    SHOP_ARMORS, CORROSAO_ARMADURA_ORGANICA, CORROSAO_ARMADURA_METAL,
    GameRoom, _DUNGEON_ITEM_CATALOG, make_player, mod,
)


def armor(item_id):
    return next(item for item in SHOP_ARMORS if item["id"] == item_id)


def check(label, condition):
    assert condition, label
    print("OK:", label)


def main():
    expected = {
        "cloak": ("leve", {"organic"}),
        "leather": ("leve", {"organic"}),
        "leather_plate": ("leve", {"organic", "metal"}),
        "chainmail": ("media", {"metal"}),
        "bronze_armor": ("media", {"metal"}),
        "leather_mail": ("media", {"organic", "metal"}),
        "plate": ("pesada", {"metal"}),
        "monster_leather_plate": ("pesada", {"organic", "metal"}),
        "fullplate": ("pesada", {"metal"}),
    }
    for item_id, (category, materials) in expected.items():
        item = armor(item_id)
        check(f"{item_id}: categoria", item["armor_category"] == category)
        check(f"{item_id}: materiais", set(item["corrosion_materials"]) == materials)

    for item_id in ("leather_plate", "leather_mail", "monster_leather_plate"):
        check(f"{item_id}: corrosão orgânica", item_id in CORROSAO_ARMADURA_ORGANICA)
        check(f"{item_id}: corrosão metálica", item_id in CORROSAO_ARMADURA_METAL)

    check("couro e placas: preço", armor("leather_plate")["price"] == 60)
    check("couro e placas: classes", set(armor("leather_plate")["allowed_classes"]) == {"warrior", "rogue", "bard", "paladin"})
    check("couro com malha: preço", armor("leather_mail")["price"] == 300)
    check("couro com malha: classes", set(armor("leather_mail")["allowed_classes"]) == {"cleric", "bard", "paladin", "warrior"})
    check("couro de monstro e placas: preço", armor("monster_leather_plate")["price"] == 600)
    check("couro de monstro e placas: classes", set(armor("monster_leather_plate")["allowed_classes"]) == {"paladin", "warrior"})

    warrior = make_player("test_w", "Guerreiro", "warrior", 0)
    paladin = make_player("test_p", "Paladino", "paladin", 1)
    check("inicial do guerreiro preserva categoria", warrior["gear"]["armor"]["armor_category"] == "leve")
    check("inicial do paladino preserva categoria", paladin["gear"]["armor"]["armor_category"] == "media")

    # Saques nativos chegam do catálogo com kind/ac_bonus, sem o formato de
    # efeito usado pelo gear dos heróis. Cada armadura deve aplicar sua CA ao
    # ser equipada, sem alterar o catálogo usado pelos monstros.
    room = GameRoom("test_armaduras")
    for item_id, (expected_category, _materials) in expected.items():
        p = make_player(f"p_{item_id}", "Teste", "warrior", 0)
        room._equip_into_slot(p, deepcopy(_DUNGEON_ITEM_CATALOG[item_id]), "armor")
        expected_ac = 10 + mod(p["dex"]) + armor(item_id)["ac_bonus"]
        check(f"{item_id}: saque aplica bônus de CA", p["ac"] == expected_ac)
        check(f"{item_id}: saque vira item de armadura", p["gear"]["armor"]["item_slot"] == "armor")
    print("\nCategorias e materiais de armaduras: OK")


if __name__ == "__main__":
    main()
