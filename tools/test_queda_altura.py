"""Testa as faixas autoritativas e a resolução do dano de queda do Voo."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def test_faixas():
    esperados = {
        0: (None, None),
        1: ("baixo", (2, 6)),
        3: ("baixo", (2, 6)),
        4: ("medio", (4, 6)),
        7: ("medio", (4, 6)),
        8: ("alto", (6, 6)),
        10: ("alto", (6, 6)),
    }
    for altura, (faixa, dados) in esperados.items():
        assert server.faixa_altura_queda(altura) == faixa
        assert server.dados_dano_queda(altura) == dados


async def test_resolucao():
    room = server.GameRoom("FALL_DAMAGE_TEST")
    rolls = []
    broadcasts = []
    damages = []

    async def fake_roll(n, faces, label):
        rolls.append((n, faces, label))
        return n * faces

    async def fake_damage(target, damage, element, killer_pid=None):
        damages.append((target, damage, element, killer_pid))

    async def fake_broadcast(message):
        broadcasts.append(message)

    room._rolar_dano_mostrado = fake_roll
    room._apply_damage_types = lambda raw, types, target: raw
    room._dano_em_alvo = fake_damage
    room.broadcast = fake_broadcast

    alvo = {"id": "m1", "name": "Criatura voadora", "hp": 50,
            "alive": True, "pos": [4, 4], "altura": 8}
    resultado = await room._aplicar_queda(alvo, "atordoamento", "p1")

    assert resultado["faixa"] == "alto"
    assert resultado["expressao"] == "6d6"
    assert resultado["dano_bruto"] == 36
    assert alvo["altura"] == 0
    assert rolls[0][0:2] == (6, 6)
    assert damages == [(alvo, 36, server.DMG_PHYSICAL, "p1")]
    assert broadcasts[-1]["type"] == "fall_result"
    assert broadcasts[-1]["altura"] == 8
    assert broadcasts[-1]["dano"] == 36

    # Altura zero é um pouso seguro e não rola dano.
    alvo["altura"] = 0
    assert await room._aplicar_queda(alvo) is None
    assert len(rolls) == 1


def main():
    test_faixas()
    asyncio.run(test_resolucao())
    print("12 passed, 0 failed")


if __name__ == "__main__":
    main()
