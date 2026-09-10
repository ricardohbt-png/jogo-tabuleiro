"""Regressão do custo extra de fome/sede por terreno no primeiro passo."""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print(f"  OK {label}")


def sala():
    room = GameRoom("SURVIVAL_TERRAIN_TEST")

    async def noop(*args, **kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.broadcast_city_state = noop
    room.send_to = noop
    room.phase = "playing"
    room.map_w = room.map_h = 10
    room.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    room.rooms = []
    room.monsters = {}
    room.chests = {}
    room.ground_items = {}
    room.decorations = []
    room.materiais = {}
    room._ponte_tiles = set()
    return room


def main():
    room = sala()
    terrenos = {
        "agua": (1, 0),
        "agua_profunda": (2, 0),
        "areia_deserto": (0, 2),
        "lava": (0, 2),
        "pantano": (1, 1),
        "planicie_nevada": (1, 0),
        "rodamoinho": (1, 0),
        "rodamoinho_profundo": (3, 0),
    }
    for x, material in enumerate(terrenos):
        room.materiais[(x, 1)] = material
        check(material, room._custo_terreno_fome_sede({}, x, 1) == terrenos[material])

    flying = {"voo": True, "altura": 1}
    room.materiais[(0, 1)] = "lava"
    check("voo ignora o terreno", room._custo_terreno_fome_sede(flying, 0, 1) == (0, 0))
    room._ponte_tiles.add((0, 1))
    check("ponte substitui o terreno inferior", room._custo_terreno_fome_sede({}, 0, 1) == (0, 0))

    room = sala()
    room.materiais.update({(1, 1): "agua", (2, 1): "agua", (3, 1): "areia_deserto"})
    player = make_player("h", "Teste", "warrior", 0)
    player.update({"pos": [0, 1], "moves_left": 6, "fome": 50, "sede": 50})
    room.players = {"h": player}
    room.current_pid = lambda: "h"

    asyncio.run(room.handle_move("h", 1, 0))
    check("primeiro passo na água rasa: fome -1", player["fome"] == 49)
    check("custo normal de movimento: sede -1", player["sede"] == 49)

    asyncio.run(room.handle_move("h", 1, 0))
    check("segundo passo no mesmo turno não cobra novamente", (player["fome"], player["sede"]) == (49, 49))

    player["moved_this_turn"] = False
    asyncio.run(room.handle_move("h", 1, 0))
    check("areia no primeiro passo do novo turno: sede -3", player["sede"] == 46)
    check("areia não acrescenta fome", player["fome"] == 49)

    room = sala()
    player = make_player("h", "Teste", "warrior", 0)
    room.players = {"h": player}
    player["fome"] = 19
    room._verificar_estado_sobrevivencia(player)
    check("entrada na fome crítica gera um aviso", len(room._survival_alerts) == 1)
    check("aviso informa penalidade de fome", room._survival_alerts[0]["penalidade_fome"] == -1)
    room._verificar_estado_sobrevivencia(player)
    check("fome crítica não repete o aviso", len(room._survival_alerts) == 1)
    player["sede"] = 19
    room._verificar_estado_sobrevivencia(player)
    check("entrada na sede crítica gera aviso separado", len(room._survival_alerts) == 2)
    check("fome e sede críticas somam -2", room._survival_alerts[-1]["penalidade_total"] == -2)

    room = sala()
    player = make_player("h", "Teste", "warrior", 0)
    room.players = {"h": player}
    player.update({"fome": 0, "sede": 12, "hp": 5})
    asyncio.run(room._aplicar_exaustao_rodada())
    check("fome zerada aplica 1 PV de dano", player["hp"] == 4)
    check("fome zerada gera popup de dano", room._survival_alerts[-1]["tipo_id"] == "desnutrido_desidratado")
    asyncio.run(room._aplicar_exaustao_rodada())
    check("dano continua nas rodadas seguintes", player["hp"] == 3)
    check("popup de dano não repete a cada rodada", len(room._survival_alerts) == 1)

    print("\nOK custo de sobrevivência por terreno")


if __name__ == "__main__":
    main()
