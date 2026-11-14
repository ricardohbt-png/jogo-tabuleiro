"""Ataque de monstro com dano fixo (sem dado, ex.: "1") não pode derrubar o turno.

O Escorpião Pequeno, o rato e o gato têm `damage: "1"`. Ao acertar, o
`_execute_one_monster_attack` montava o dado mostrado com
`damage.split("d")[1]`, que estoura IndexError sem "d": o turno era engolido e o
golpe (com o veneno do escorpião) nunca chegava ao herói.
Roda da raiz: python -X utf8 tools/test_dano_fixo_monstro.py
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


async def golpe(tipo):
    r = S.GameRoom("FIXO")
    dados = []

    async def nada(*a, **k):
        return None

    async def bc(msg, *a, **k):
        if msg.get("type") == "dice_roll":
            dados.append(msg)
    r.gm_say = nada
    r.push_state = nada
    r.broadcast = bc
    r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 6
    r.tiles = [[S.FLOOR] * 6 for _ in range(6)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 6, "h": 6, "cx": 2, "cy": 2,
                "locked": False, "doors": []}]
    p = S.make_player("p", "Ana", "warrior", 0)
    p["pos"] = [2, 2]
    p["hp"] = p["max_hp"] = 500
    p["ac"] = -50                      # todo ataque acerta
    r.players["p"] = p
    m = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == tipo), r.rooms[0])
    m["id"] = "m"
    m["pos"] = [3, 2]
    r.monsters = {"m": m}
    r.round_num = 1
    atk = m["attacks"][0]
    await r._execute_one_monster_attack(m, atk, {"kind": "player", "obj": p})
    return p, dados


def test_tipo_do_dado():
    print("[1] dado mostrado a partir da expressão")
    check(S._tipo_dado("1d8") == "d8", "1d8 -> d8")
    check(S._tipo_dado("2d6+3") == "d6", "2d6+3 -> d6")
    check(S._tipo_dado("1") == "d6", "dano fixo usa o dado padrão")
    check(S._tipo_dado("") == "d6" and S._tipo_dado(None) == "d6", "vazio usa o dado padrão")
    check(S._tipo_dado("5", "d4") == "d4", "padrão escolhido pelo chamador")


async def main():
    test_tipo_do_dado()
    print("[2] golpe com dano fixo chega ao herói")
    for tipo in ("escorpiao_pequeno", "rato", "gato"):
        try:
            p, dados = await golpe(tipo)
        except Exception as e:
            check(False, f"{tipo}: golpe sem erro ({type(e).__name__}: {e})")
            continue
        check(p["hp"] < 500, f"{tipo}: o dano foi aplicado (PV {p['hp']}/500)")
        check(all(str(d.get("die", "")).startswith("d") for d in dados),
              f"{tipo}: dados mostrados têm formato dN")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
