"""Verifica alcances autoritativos do machado e da lança curta."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def main():
    room = server.GameRoom("WEAPON_RANGE_TEST")
    monster = {"id": "m1", "pos": [3, 3], "size": [1, 1]}
    player = {"pos": [2, 2], "weapon": server.WEAPONS["lanca_curta"]}

    assert server.WEAPONS["machado_basico"]["throw_range"] == 2
    assert server.WEAPONS["lanca_curta"]["throw_range"] == 4
    assert next(w for w in server.SHOP_WEAPONS if w["id"] == "machado_basico")["throw_range"] == 2
    assert next(w for w in server.SHOP_WEAPONS if w["id"] == "lanca_curta")["throw_range"] == 4
    assert room._alvo_no_alcance_arma(player, monster)

    player["weapon"] = server.WEAPONS["machado_basico"]
    assert not room._alvo_no_alcance_arma(player, monster)
    print("5 passed, 0 failed")


if __name__ == "__main__":
    main()
