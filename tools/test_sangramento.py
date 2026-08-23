"""Testes unitários das condições SANGRAMENTO e FERIDA ABERTA."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom


async def main():
    room = GameRoom("BLEED_TEST")
    room._rolar_dado = lambda _: 6
    room.gm_say = lambda *args, **kwargs: asyncio.sleep(0)
    alvo = {"id": "p1", "name": "Teste", "hp": 50, "max_hp": 50, "alive": True}
    room.players = {"p1": alvo}

    assert room._aplicar_sangramento(alvo) == {"nivel": 1, "rodadas": 6, "ferida_aberta": False}
    assert room._aplicar_sangramento(alvo) == {"nivel": 2, "rodadas": 8, "ferida_aberta": False}
    assert room._aplicar_sangramento(alvo) == {"nivel": 3, "rodadas": 10, "ferida_aberta": False}
    assert room._aplicar_sangramento(alvo) == {"nivel": 3, "rodadas": 12, "ferida_aberta": True}
    assert room._aplicar_sangramento(alvo) == {"nivel": 3, "rodadas": 14, "ferida_aberta": True}
    assert room._aplicar_hemorragia(alvo) is True
    assert room._aplicar_hemorragia(alvo) is False

    await room._processar_sangramento_turno(alvo)
    assert alvo["hp"] == 43 and alvo["sangramento_rodadas"] == 13

    alvo["ferida_aberta"] = True
    room._curar_hp(alvo, 1, "teste")
    assert not alvo.get("ferida_aberta")
    assert alvo.get("hemorragia") is True

    alvo["ferida_aberta"] = True
    alvo["action_done"] = False
    room._is_turn = lambda pid: True
    room.push_state = lambda: asyncio.sleep(0)
    await room.handle_estancar_sangramento("p1")
    assert alvo.get("sangramento_nivel", 0) == 0
    assert alvo.get("ferida_aberta") is True

    # -- Animados (servos) sao MORTOS-VIVOS: nao sangram -----------------------
    animado = {"id": "a1", "tipo": "esqueleto", "nome_base": "Esqueleto",
               "vida_atual": 10, "vida_max": 10, "pos": [4, 5]}
    assert room._aplicar_sangramento(animado) is None, "servo animado nao deve sangrar"
    assert not animado.get("sangramento_nivel")
    assert room._aplicar_hemorragia(animado) is False

    # -- Prisioneiro e VIVO: sangra, tica no turno dele e morre pelo caminho ----
    # certo (_prisioneiro_morre, nao _monster_dies).
    pr = {"id": "pr1", "name": "Prisioneiro", "hp": 9, "max_hp": 9,
          "pos": [6, 6], "alive": True, "freed": True}
    room.prisoner = pr
    assert room._aplicar_sangramento(pr) is not None, "prisioneiro deve poder sangrar"
    hp_antes = pr["hp"]
    await room._processar_sangramento_turno(pr)
    assert pr["hp"] < hp_antes, "o tick precisa ferir o prisioneiro"
    mortes = []
    async def _morte_pr():
        mortes.append("prisioneiro")
    async def _morte_monstro(m, k=None):
        mortes.append("monstro")
    room._prisioneiro_morre = _morte_pr
    room._monster_dies = _morte_monstro
    pr["hp"] = 1; pr["sangramento_nivel"] = 3; pr["sangramento_rodadas"] = 3
    await room._processar_sangramento_turno(pr)
    assert mortes == ["prisioneiro"], f"morte pelo caminho errado: {mortes}"

    print("SANGRAMENTO_TEST_PASS")


if __name__ == "__main__":
    asyncio.run(main())
