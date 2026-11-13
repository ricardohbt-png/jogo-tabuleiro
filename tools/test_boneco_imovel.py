"""Bonecos de treino (movimento 0) nunca saem do lugar.

`_water_turn_moves` garantia "mínimo 1" de movimento a toda criatura, então um
boneco de movimento 0 ganhava 1 casa por turno assim que a busca da última
posição conhecida (`_monster_search_last_seen`) o fazia perseguir o herói. No
Campo de Treinamento os alvos de Mira Certeira, Golpe Devastador e Fúria
Berserker (que não morrem) andavam até bloquear a passagem.
Roda da raiz: python -X utf8 tools/test_boneco_imovel.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


async def nada(*a, **k):
    return None


def sala():
    r = S.GameRoom("IMOVEL")
    r.gm_say = nada
    r.push_state = nada
    r.broadcast = nada
    r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 20
    r.tiles = [[S.FLOOR] * 20 for _ in range(20)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 20, "h": 20, "cx": 5, "cy": 5,
                "locked": False, "doors": []}]
    return r


def main():
    tipos = ["boneco_mira", "boneco_golpe", "boneco_furia",
             "boneco_treino", "boneco_treino_veneno", "boneco_palha"]
    print("[1] nenhum boneco de movimento 0 anda, de nenhuma distância")
    for tipo in tipos:
        for dist in (2, 3, 6):
            r = sala()
            d = next(x for x in S.MONSTER_DEFS if x["type"] == tipo)
            m = S.make_monster(d, r.rooms[0])
            m["id"] = "m"
            m["pos"] = [10, 10]
            m["alertado"] = True
            p = S.make_player("p1", "Teste", "warrior", 0)
            p["pos"] = [10 + dist, 10]
            p["hp"] = p["max_hp"] = 50
            p["connected"] = True
            r.players = {"p1": p}
            r.monsters = {"m": m}
            r.round_num = 1
            r._monster_remember_visible_targets(m, [{"kind": "player", "obj": p}])
            for _ in range(3):                      # vários turnos seguidos
                asyncio.run(r.gm_phase(m))
            check(m["pos"] == [10, 10], f"{tipo} a {dist} casas ficou parado ({m['pos']})")

    print("[2] o piso de 1 movimento continua valendo para quem anda")
    r = sala()
    heroi = S.make_player("p1", "Teste", "warrior", 0)
    check(r._water_turn_moves(heroi, 0) == 1, "herói com base 0 segue com piso 1")
    goblin = S.make_monster(next(x for x in S.MONSTER_DEFS if x["type"] == "goblin"), r.rooms[0])
    goblin["pos"] = [3, 3]
    check(r._water_turn_moves(goblin, goblin["movement"]) >= 1, "monstro que anda segue com orçamento")


main()
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
