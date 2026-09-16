"""Regressão mínima da máquina de combate descartável do editor.

Roda da raiz: ``python tools/test_simulador_mestre.py``
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def _room():
    room = object.__new__(S.GameRoom)
    room.players = {
        "test_hero_warrior": {"id": "test_hero_warrior", "test_hero": True,
                              "alive": True, "init": 12, "dex": 10, "int_": 10},
        "real_player": {"id": "real_player", "test_hero": False,
                        "alive": True, "init": 99, "dex": 99, "int_": 99},
    }
    room.monsters = {
        "m1": {"id": "m1", "hp": 8, "init": 10, "dex": 8, "int_": 2},
    }
    room.initiative_value = lambda obj: obj.get("init", 0)
    room._initiative_attribute = lambda obj, key: obj.get(key, 0)
    room.master_manual_mid = "m1"
    room.test_combat = {"active": True, "round": 1, "queue": [],
                        "index": 0, "ended_reason": None}
    return room


def main():
    room = _room()
    fila = room._teste_combate_fila(1)
    assert [item["id"] for item in fila] == ["test_hero_warrior", "m1"]
    assert all(item["id"] != "real_player" for item in fila)

    room.monsters["m1"]["hp"] = 0
    assert room._teste_combate_verificar_fim()
    assert not room.test_combat["active"]
    assert room.test_combat["ended_reason"] == "monstros_eliminados"
    assert room.master_manual_mid is None

    # A sala normal continua usando exclusivamente a iniciativa normal.
    normal = object.__new__(S.GameRoom)
    normal.phase = "playing"
    normal._intro_masmorra_bloqueada = lambda: False
    normal.test_combat = {"active": False}
    normal.current_pid = lambda: "real_player"
    normal.last_stand_pid = None
    normal.animados_phase_pid = None
    assert normal._is_turn("real_player")
    assert not normal._is_turn("test_hero_warrior")
    print("simulador do mestre: 3 verificações passaram")


if __name__ == "__main__":
    main()
