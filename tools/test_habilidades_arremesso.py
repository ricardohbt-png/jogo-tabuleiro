"""Regressões da habilidade de arremesso fornecida por armas equipadas."""
import asyncio
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def _room():
    room = S.GameRoom("THROW_SKILL_TEST")
    room.phase = "playing"
    room.push_state = _async_noop
    room.broadcast_city_state = _async_noop
    room.gm_say = _async_noop
    room.broadcast = _async_noop
    return room


async def _async_noop(*_args, **_kwargs):
    pass


def test_habilidades_derivadas_das_armas():
    room = _room()
    player = S.make_player("p1", "Victor", "warrior", 0)
    room.players["p1"] = player

    # A arma inicial tem os dados completos em player["weapon"], mas o
    # espelho visual de gear["weapon"] é enxuto. A habilidade ainda precisa
    # aparecer no payload/menu desde o início da partida.
    iniciais = room._weapon_throw_skills(player)
    assert any(skill["weapon_id"] == "machado_basico" for skill in iniciais)

    player["gear"]["weapon"] = deepcopy(S.WEAPONS["machado_basico"])
    player["weapon"] = deepcopy(player["gear"]["weapon"])
    player["gear"]["off_hand"] = deepcopy(S.WEAPONS["dagger"])
    skills = room._weapon_throw_skills(player)
    by_id = {skill["id"]: skill for skill in skills}

    assert by_id["arremesso_arma_weapon"]["weapon_id"] == "machado_basico"
    assert by_id["arremesso_arma_weapon"]["throw_slot"] == "weapon"
    assert "Força" in by_id["arremesso_arma_weapon"]["description"]
    assert by_id["arremesso_arma_off_hand"]["weapon_id"] == "dagger"
    assert by_id["arremesso_arma_off_hand"]["throw_slot"] == "off_hand"

    player["gear"]["weapon"] = deepcopy(S.WEAPONS["lanca"])
    player["weapon"] = deepcopy(player["gear"]["weapon"])
    skills = room._weapon_throw_skills(player)
    lance = next(skill for skill in skills if skill["id"] == "arremesso_arma_weapon")
    assert lance["weapon_id"] == "lanca"
    assert S.WEAPONS["lanca"]["throw_range"] == 4


def test_atalho_accepta_habilidade_de_arma():
    room = _room()
    player = S.make_player("p1", "Victor", "warrior", 0)
    room.players["p1"] = player
    player["gear"]["weapon"] = deepcopy(S.WEAPONS["machado_basico"])
    player["weapon"] = deepcopy(player["gear"]["weapon"])

    asyncio.run(room.handle_shortcut_set(
        "p1", 0, {"kind": "skill", "id": "arremesso_arma_weapon"}))
    assert player["shortcut_slots"][0] == {
        "kind": "skill", "id": "arremesso_arma_weapon"
    }


def test_atalho_accepta_habilidade_do_instrumento():
    room = _room()
    player = S.make_player("p1", "Henrique", "bard", 0)
    room.players["p1"] = player
    player["gear"]["off_hand"] = S.criar_instrumento("harpa", "padrao")

    asyncio.run(room.handle_shortcut_set(
        "p1", 0, {"kind": "skill", "id": "instrumento_harpa"}))
    assert player["shortcut_slots"][0] == {
        "kind": "skill", "id": "instrumento_harpa"
    }


def test_adaga_e_lanca_valem_para_qualquer_classe():
    room = _room()
    for class_id in ("warrior", "mage", "rogue", "cleric", "bard", "paladin"):
        player = S.make_player("p1", "Teste", class_id, 0)
        room.players["p1"] = player
        for weapon_id in ("dagger", "lanca"):
            player["gear"]["weapon"] = deepcopy(S.WEAPONS[weapon_id])
            player["weapon"] = deepcopy(player["gear"]["weapon"])
            skills = room._weapon_throw_skills(player)
            assert any(skill["weapon_id"] == weapon_id for skill in skills)


if __name__ == "__main__":
    test_habilidades_derivadas_das_armas()
    test_atalho_accepta_habilidade_de_arma()
    test_atalho_accepta_habilidade_do_instrumento()
    test_adaga_e_lanca_valem_para_qualquer_classe()
    print("4 passed, 0 failed")
