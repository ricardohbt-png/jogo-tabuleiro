"""Teste focal do Sopro de Dragão do editor.

Rode da raiz: python tools/test_sopro_dragao.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def test_validacao():
    raw = {
        "type": "dragao_teste_sopro", "name": "Dragão Teste", "hp": 20, "ac": 12,
        "attacks": [{"name": "Garra", "damage": "1d6"}],
        "monster_abilities": [{
            "id": "sopro_dragao", "uses_per_day": 2, "cooldown_turns": 3,
            "damage_dice": 4, "damage_faces": 8, "damage_type": "cold",
            "shape": "cone", "target_mode": "todos", "range": 6,
            "save": "fortitude", "dc": 17, "success_effect": "nega",
        }],
    }
    ok, monster = server._validate_custom_monster(raw)
    assert ok, monster
    breath = monster["special_abilities"][0]
    assert breath["damage"] == "4d8"
    assert breath["damage_types"] == [server.DMG_COLD]
    assert {key: breath[key] for key in ("shape", "target_mode", "range", "save", "dc", "success_effect")} == {
        "shape": "cone", "target_mode": "todos", "range": 6,
        "save": "fortitude", "dc": 17, "success_effect": "nega",
    }


def test_geometria():
    room = object.__new__(server.GameRoom)
    room.map_w, room.map_h = 12, 12
    room._blocks_tile = lambda x, y: False
    room._tem_linha_de_visao = lambda a, b: True
    monster = {"pos": [4, 4]}
    linha = room._sopro_dragao_tiles(monster, [8, 4], {"shape": "linha", "range": 4})
    assert linha == {(5, 4), (6, 4), (7, 4), (8, 4)}
    cone = room._sopro_dragao_tiles(monster, [8, 4], {"shape": "cone", "range": 3})
    assert {(5, 4), (6, 3), (6, 4), (6, 5), (7, 2), (7, 6)} <= cone


if __name__ == "__main__":
    test_validacao()
    test_geometria()
    print("Sopro de Dragão: OK")
