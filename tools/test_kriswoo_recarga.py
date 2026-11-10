"""Lâmina de Kriswoo: a recarga de 10 rodadas só vale quando a técnica vem da arma.

Quem já tem o Ataque Giratório equipado pela Guilda (recarga 6) e empunha a
Lâmina passava a pagar 10 rodadas: a arma piorava a técnica que o herói comprou.
Roda da raiz: python -X utf8 tools/test_kriswoo_recarga.py
"""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []
TEC = "tecnica_ataque_giratorio"


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


async def recarga(com_guilda, com_lamina):
    r = S.GameRoom("KRIS")

    async def nada(*a, **k):
        return None
    r.gm_say = nada
    r.push_state = nada
    r.broadcast = nada
    r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 6
    r.tiles = [[S.FLOOR] * 6 for _ in range(6)]
    p = S.make_player("p", "Victor", "warrior", 0)
    p["pos"] = [2, 2]
    p["fome"] = p["sede"] = 100
    r.players["p"] = p
    r._is_turn = lambda pid: True
    if com_lamina:
        p["gear"]["weapon"] = copy.deepcopy(S.WEAPONS["lamina_de_kriswoo"])
        p["weapon"] = copy.deepcopy(S.WEAPONS["lamina_de_kriswoo"])
    if com_guilda:
        p.setdefault("guild_owned", {}).setdefault("tecnicas", []).append(TEC)
        if com_guilda == "lista":
            p["guild_equip"]["tecnicas"] = [TEC]
        else:
            p["guild_equip"]["tecnica"] = TEC
    await r.handle_usar_tecnica("p", TEC)
    return r.tecnica_restante(p, TEC)


async def main():
    base = S.guild_item(TEC)["recarga_rodadas"]
    check(await recarga(True, False) == base, f"só pela Guilda: recarga {base}")
    check(await recarga(False, True) == 10, "só pela Lâmina: recarga 10")
    check(await recarga(True, True) == base,
          f"Guilda + Lâmina: vale a recarga da Guilda ({base}), não a da arma")
    check(await recarga("lista", True) == base,
          f"Guilda (lista de técnicas) + Lâmina: recarga {base}")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
