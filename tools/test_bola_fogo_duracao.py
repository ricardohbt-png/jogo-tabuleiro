"""Garante que o fogo residual da Bola de Fogo expira por rodada, não por alvo."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


async def verificar():
    room = server.GameRoom("FIREBALL_DURATION_TEST")
    room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)
    room._aplicar_dano_area_fogo = lambda *args, **kwargs: asyncio.sleep(0)
    zona = {
        "tipo": "bola_fogo", "ativa": True, "cx": 3, "cy": 3,
        "raio": 1, "area_lado": 3, "dano_r2": 5, "dano_r3": 2,
        "rodada_atual": 2, "rodadas_max": 3,
        "criado_em": 1, "expira_em": 4,
    }

    room.round_num = 2
    await room._processar_zona_bola_fogo(zona)
    assert zona["ativa"] and zona["rodada_atual"] == 3

    room.round_num = 3
    await room._processar_zona_bola_fogo(zona)
    assert zona["ativa"] and zona["rodada_atual"] == 4

    # Na quarta rodada extingue mesmo sem haver qualquer alvo na área.
    room.round_num = 4
    await room._processar_zona_bola_fogo(zona)
    assert not zona["ativa"]


if __name__ == "__main__":
    asyncio.run(verificar())
    print("Bola de Fogo: duração temporal aprovada")
