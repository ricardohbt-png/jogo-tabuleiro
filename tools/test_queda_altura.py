"""Testa as faixas autoritativas e a resolução do dano de queda do Voo."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import inspect
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


async def test_petrificado_triplica():
    """Corpo de pedra: QUALQUER queda enquanto petrificado sofre x3."""
    room = server.GameRoom("FALL_PETRIFIED_TEST")
    rolls, damages, broadcasts = [], [], []
    bruto = [None]          # valor que o dado devolve, controlado por caso

    async def fake_roll(n, faces, label):
        rolls.append((n, faces))
        return n * faces if bruto[0] is None else bruto[0]

    async def fake_damage(target, damage, element, killer_pid=None):
        damages.append(damage)

    async def fake_broadcast(msg):
        broadcasts.append(msg)

    room._rolar_dano_mostrado = fake_roll
    room._apply_damage_types = lambda raw, types, target: raw
    room._dano_em_alvo = fake_damage
    room.broadcast = fake_broadcast

    # --- o multiplicador puro
    assert server.multiplicador_queda({}) == 1
    assert server.multiplicador_queda({"petrificado": False}) == 1
    assert server.multiplicador_queda({"petrificado": True}) == server.MULT_QUEDA_PETRIFICADO
    assert server.multiplicador_queda(None) == 1

    # --- queda do VOO, petrificado
    alvo = {"id": "m1", "name": "Estatua", "hp": 500, "alive": True,
            "pos": [4, 4], "altura": 8, "petrificado": True}
    r = await room._aplicar_queda(alvo, "petrificacao", None)
    assert rolls[0] == (6, 6), rolls
    assert r["multiplicador"] == 3 and r["dano_bruto"] == 108, r
    assert r["expressao"] == "6d6 ×3", r["expressao"]
    assert damages == [108], damages
    assert broadcasts[-1]["multiplicador"] == 3

    # --- mesma altura, sem petrificacao: continua 36
    alvo2 = {"id": "m2", "name": "Voador", "hp": 500, "alive": True,
             "pos": [5, 5], "altura": 8}
    r2 = await room._aplicar_queda(alvo2, "atordoamento", None)
    assert r2["multiplicador"] == 1 and r2["dano_bruto"] == 36, r2
    assert r2["expressao"] == "6d6"

    # --- ORDEM: x3 no dado BRUTO, antes da resistencia.
    # Com bruto IMPAR as duas ordens divergem: (3*7)//2 = 10, mas (7//2)*3 = 9.
    # Com valor par elas coincidem, e o teste nao provaria nada.
    room._apply_damage_types = lambda raw, types, target: raw // 2
    bruto[0] = 7
    damages.clear()
    alvo3 = {"id": "m3", "name": "Estatua", "hp": 500, "alive": True,
             "pos": [6, 6], "altura": 1, "petrificado": True}
    await room._aplicar_queda(alvo3, "petrificacao", None)
    assert damages == [10], damages
    bruto[0] = None
    room._apply_damage_types = lambda raw, types, target: raw

    # --- queda de TERRENO (desnivel) tambem triplica
    room2 = server.GameRoom("FALL_TERRAIN_PETRIFIED")
    quedas = []

    async def dano_terreno(target, damage, element, killer_pid=None):
        quedas.append(damage)

    room2._rolar_dano_mostrado = fake_roll
    room2._apply_damage_types = lambda raw, types, target: raw
    room2._dano_em_alvo = dano_terreno
    room2.broadcast = fake_broadcast
    room2._queda_no_passo = lambda c, o, d: True
    room2._elevacao_terreno = lambda x, y: 8 if (x, y) == (1, 1) else 0
    pedra = {"id": "m4", "name": "Estatua", "hp": 500, "alive": True,
             "pos": [2, 1], "petrificado": True}
    rt = await room2._aplicar_queda_terreno(pedra, [1, 1], [2, 1])
    assert rt["multiplicador"] == 3 and rt["dano_bruto"] == 108, rt
    assert quedas == [108], quedas


def test_olhar_petrificante_derruba():
    """O Olhar Petrificante era a UNICA fonte que nao derrubava quem voava.

    Guarda ESTRUTURAL: exercitar o olhar exige meia sala montada, e o que pode
    regredir aqui e' a ORDEM -- marcar `petrificado` antes de chamar a queda,
    senao o x3 nao pega.
    """
    fonte = inspect.getsource(server.GameRoom._teste_olhar_petrificante)
    assert "_aplicar_queda" in fonte, "o olhar petrificante voltou a nao derrubar"
    assert fonte.index('alvo["petrificado"] = True') < fonte.index("_aplicar_queda"),         "a queda precisa vir DEPOIS de marcar petrificado, senao perde o x3"


def main():
    test_faixas()
    asyncio.run(test_resolucao())
    asyncio.run(test_petrificado_triplica())
    test_olhar_petrificante_derruba()
    print("4 blocos OK: faixas, resolucao, x3 do petrificado, ordem do olhar")


if __name__ == "__main__":
    main()
