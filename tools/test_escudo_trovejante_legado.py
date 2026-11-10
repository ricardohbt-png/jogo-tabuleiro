"""Manto de Raios retalia também monstros do laço de ataque legado.

Esqueleto, orc e dragão ainda atacam pelo laço antigo do `gm_phase`, e a
retaliação do escudo trovejante só existia no caminho novo
(`_execute_one_monster_attack`): eles acertavam o portador sem levar o choque.
Roda da raiz: python -X utf8 tools/test_escudo_trovejante_legado.py
"""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


async def rodada(tipo, ativo=True):
    r = S.GameRoom("TROVAO")

    async def nada(*a, **k):
        return None
    r.gm_say = nada
    r.push_state = nada
    r.broadcast = nada
    r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 6
    r.tiles = [[S.FLOOR] * 6 for _ in range(6)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 6, "h": 6, "cx": 2, "cy": 2,
                "locked": False, "doors": []}]
    p = S.make_player("p", "Richard", "paladin", 0)
    p["pos"] = [2, 2]
    p["hp"] = p["max_hp"] = 500
    p["ac"] = -50                      # todo ataque acerta
    escudo = copy.deepcopy(next(i for i in S.SHOP_ARMORS
                                if i["id"] == "escudo_p_retalhacao_trovejante"))
    escudo["thunder_reaction_active_until"] = 99 if ativo else 0
    p["gear"]["off_hand"] = escudo
    r.players["p"] = p
    mdef = next(m for m in S.MONSTER_DEFS if m["type"] == tipo)
    m = S.make_monster(mdef, r.rooms[0])
    m["id"] = "m"
    m["pos"] = [3, 2]
    m["hp"] = m["max_hp"] = 500
    m["alertado"] = True
    r.monsters = {"m": m}
    r.round_num = 1
    await r.gm_phase(only_monster=m)
    return p, m


async def main():
    for tipo in ("skeleton", "orc"):
        p, m = await rodada(tipo)
        check(p["hp"] < 500, f"{tipo}: acertou o portador")
        check(m["hp"] < 500, f"{tipo}: levou o choque do Manto de Raios ({500 - m['hp']} de dano)")
        p, m = await rodada(tipo, ativo=False)
        check(m["hp"] == 500, f"{tipo}: com o manto desligado, nada de choque")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
