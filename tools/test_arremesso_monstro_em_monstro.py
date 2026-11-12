"""Arremesso de alvo único de um monstro em outro monstro (hostilidade entre monstros).

`_monster_throw_item` tratava todo alvo que não é herói como servo animado:
lia `target["vida_atual"]` e a CA em `ca`. Monstro usa `hp` e `ac`, então o
Soldado (ou o Xamã do editor) hostil a outro monstro estourava KeyError ao
acertar o frasco e o turno era engolido. O ramo de área já tratava monstros.
Roda da raiz: python -X utf8 tools/test_arremesso_monstro_em_monstro.py
"""
import asyncio
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


def sala():
    r = S.GameRoom("ARR")

    async def nada(*a, **k):
        return None
    r.gm_say = nada
    r.push_state = nada
    r.broadcast = nada
    r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 10
    r.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 10, "h": 10, "cx": 2, "cy": 2,
                "locked": False, "doors": []}]
    soldado = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == "soldado"), r.rooms[0])
    soldado["id"] = "s"
    soldado["pos"] = [2, 2]
    alvo = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == "goblin"), r.rooms[0])
    alvo["id"] = "g"
    alvo["pos"] = [5, 2]
    alvo["hp"] = alvo["max_hp"] = 999
    alvo["ac"] = -50                   # o frasco sempre acerta
    r.monsters = {"s": soldado, "g": alvo}
    r.round_num = 1
    return r, soldado, alvo


async def main():
    alvo_unico = [i for i, d in S.ARREMESSAVEIS.items()
                  if d.get("alvo") == "ataque_alvo" and d.get("dano")]
    check(bool(alvo_unico), f"há arremessáveis de alvo único com dano ({len(alvo_unico)})")
    for item_id in alvo_unico:
        random.seed(3)
        r, soldado, alvo = sala()
        try:
            await r._monster_throw_item(soldado, {"kind": "monster", "obj": alvo}, {"id": item_id})
        except Exception as e:
            check(False, f"{item_id}: sem erro ({type(e).__name__}: {e})")
            continue
        check(alvo["hp"] < 999 or not S.roll_dice(S.ARREMESSAVEIS[item_id]["dano"]),
              f"{item_id}: o monstro alvo levou dano (PV {alvo['hp']}/999)")

    print("[2] o alvo morre e sai do jogo como monstro")
    r, soldado, alvo = sala()
    alvo["hp"] = 1
    await r._monster_throw_item(soldado, {"kind": "monster", "obj": alvo}, {"id": alvo_unico[0]})
    check(alvo["hp"] <= 0, "o goblin morreu")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
