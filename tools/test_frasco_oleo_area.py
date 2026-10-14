"""Regressão: Frasco de Óleo atinge somente a casa escolhida."""

import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server as S
from test_editor_itens import _room_com_alvo


def test_frasco_oleo_afeta_somente_casa_de_impacto():
    assert S.ARREMESSAVEIS["frasco_oleo"]["area_raio"] == 0

    room, player = _room_com_alvo()
    room.map_w = room.map_h = 8
    room.tiles = [[S.FLOOR for _ in range(8)] for _ in range(8)]
    room.monsters["m1"]["pos"] = [2, 1]
    room.monsters["m2"] = {
        "id": "m2", "name": "Alvo adjacente", "type": "orc", "hp": 999,
        "ac": 1, "pos": [3, 1], "alive": True, "special_abilities": [],
    }
    player["bag"] = [{"id": "frasco_oleo", "name": "Frasco de Óleo Incendiário"}]
    center_hp = room.monsters["m1"]["hp"]
    adjacent_hp = room.monsters["m2"]["hp"]
    player_hp = player["hp"]
    random.seed(4321)

    asyncio.run(room.handle_throw_item("p1", {
        "item_id": "frasco_oleo", "tx": 2, "ty": 1,
    }))

    assert room.monsters["m1"]["hp"] < center_hp
    assert room.monsters["m1"].get("em_chamas_rodadas", 0) > 0
    assert room.monsters["m2"]["hp"] == adjacent_hp
    assert player["hp"] == player_hp
    assert not player["bag"]
    assert player["action_done"] is True


def test_frasco_oleo_aceita_payload_antigo_com_alvo():
    room, player = _room_com_alvo()
    room.map_w = room.map_h = 8
    room.tiles = [[S.FLOOR for _ in range(8)] for _ in range(8)]
    player["bag"] = [{"id": "frasco_oleo", "name": "Frasco de Óleo Incendiário"}]
    hp = room.monsters["m1"]["hp"]
    random.seed(4322)

    # Clientes abertos antes da atualização ainda enviam target_id/target_pos.
    asyncio.run(room.handle_throw_item("p1", {
        "item_id": "frasco_oleo", "target_id": "m1", "target_pos": [2, 1],
    }))

    assert room.monsters["m1"]["hp"] < hp
    assert not player["bag"]
    assert player["action_done"] is True


if __name__ == "__main__":
    test_frasco_oleo_afeta_somente_casa_de_impacto()
    test_frasco_oleo_aceita_payload_antigo_com_alvo()
    print("2 verificações passaram")
