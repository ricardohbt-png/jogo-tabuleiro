"""Regressão do teste de Reflexos do piso congelado."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


async def main():
    room = server.GameRoom("TEST")
    room.materiais = {(1, 1): "piso_congelado", (2, 1): "pedra_cinza"}
    async def noop(*args, **kwargs):
        return None
    room.gm_say = noop

    resultado = {"passou": False}
    chamadas = []
    async def fake_save(alvo, tipo, dificuldade, **kwargs):
        chamadas.append((alvo, tipo, dificuldade))
        return resultado["passou"], 10, 0, 10
    room._save_mostrado = fake_save

    heroi = {"id": "h1", "name": "Heroi", "pos": [1, 1], "moves_left": 4}
    await room._aplicar_piso_congelado_se_pisar(heroi)
    assert heroi["moves_left"] == 0, "falha deve zerar movimento do heroi"
    assert chamadas[-1][1:] == ("reflexos", 10), "deve testar Reflexos CD 10"

    resultado["passou"] = True
    heroi["pos"] = [1, 1]
    heroi["moves_left"] = 4
    await room._aplicar_piso_congelado_se_pisar(heroi)
    assert heroi["moves_left"] == 4, "sucesso nao deve retirar movimento"

    monstro = {"id": "m1", "name": "Monstro", "pos": [1, 1], "moves_left": 3,
               "_water_moves_left": 3}
    resultado["passou"] = False
    await room._aplicar_piso_congelado_se_pisar(monstro)
    assert monstro["moves_left"] == 0 and monstro["_water_moves_left"] == 0, \
        "falha deve zerar o movimento do monstro"

    voador = {"id": "m2", "name": "Voador", "pos": [1, 1], "moves_left": 3,
              "voo": True, "altura": 2}
    antes = len(chamadas)
    await room._aplicar_piso_congelado_se_pisar(voador)
    assert voador["moves_left"] == 3 and len(chamadas) == antes, \
        "voador em altura deve ignorar o piso"

    room.materiais[(2, 1)] = "planicie_nevada"
    neve = {"id": "h2", "name": "Neve", "pos": [2, 1], "moves_left": 5}
    room._apply_snow_entry_penalty(neve, [3, 1], neve["pos"])
    assert neve["moves_left"] == 2, "entrar na planicie deve reduzir o restante pela metade"
    inicio_neve = {"id": "h3", "name": "Inicio", "pos": [2, 1]}
    assert room._water_turn_moves(inicio_neve, 6) == 3, \
        "comecar o turno na planicie deve dar metade do movimento"

    print("OK piso congelado e planicie nevada: movimento, voo e afundamento")


if __name__ == "__main__":
    asyncio.run(main())
