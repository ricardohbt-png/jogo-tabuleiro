"""Testes do dano contínuo de Onda Envolvente / Afogar."""
import asyncio
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


async def run():
    room = object.__new__(S.GameRoom)
    target = {"id": "hero", "name": "Herói", "alive": True, "hp": 20,
              "pos": [2, 2], "preso": True, "preso_por": "agua"}
    room.players = {"hero": target}
    room._is_water_tile = lambda x, y: (x, y) == (2, 2)
    room._apply_damage_types = lambda damage, _types, _target: damage
    popups = []
    async def ignore(*_args, **_kwargs):
        return None
    async def capture_popup(*args, **kwargs):
        popups.append((args, kwargs))
    room.gm_say = ignore
    room._player_dies = ignore
    room._enviar_trap_result = capture_popup
    elemental = {"id": "agua", "special_abilities": [{"id": "onda_envolvente", "damage": "1d6"}]}
    with patch.object(S, "roll_dice", side_effect=[3, 5]):
        await S.GameRoom._processar_onda_envolvente_turno(room, elemental)
    check("Afogar causa o dano base", target["hp"] <= 17)
    check("Água adiciona 1d6 de dano", target["hp"] == 12)
    check("Afogar envia popup", len(popups) == 1 and popups[0][1].get("tipo_id") == "afogamento")
    check("popup informa o bônus da água", popups[0][1].get("water_bonus") == 5)


asyncio.run(run())
