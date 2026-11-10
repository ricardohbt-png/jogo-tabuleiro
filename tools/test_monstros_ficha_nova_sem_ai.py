"""Monstro de ficha nova (lista `attacks`) sem `ai_type` não pode cair no laço legado.

Desde 22/10 o Mago das Trevas e as formas animais ND 0 (rato, gato, ovelha,
pombo) usam a ficha nova: os ataques ficam em `attacks`, sem `atk_bonus` no
topo. O `gm_phase` só mandava para a IA modular quem tinha `ai_type`; o resto
caía no laço legado, que lê `m["atk_bonus"]` e estourava `KeyError` ao chegar
perto do herói. O turno era engolido: o mago nunca atacava nem lançava magia,
e os animais nunca fugiam.
Roda da raiz: python -X utf8 tools/test_monstros_ficha_nova_sem_ai.py
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


def sala(tipo, pos_monstro=(3, 2)):
    r = S.GameRoom("FICHA")

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
    p = S.make_player("p", "Ana", "warrior", 0)
    p["pos"] = [2, 2]
    p["hp"] = p["max_hp"] = 500
    r.players["p"] = p
    mdef = next(m for m in S.MONSTER_DEFS if m["type"] == tipo)
    m = S.make_monster(mdef, r.rooms[0])
    m["id"] = "m"
    m["pos"] = list(pos_monstro)
    m["alertado"] = True
    r.monsters = {"m": m}
    r.round_num = 1
    return r, p, m


async def turnos(r, m, n):
    for _ in range(n):
        await r.gm_phase(only_monster=m)
        r.round_num += 1


async def main():
    print("[1] o Mago das Trevas ataca ou lança magia, sem erro")
    r, p, m = sala("dark_mage")
    erro = None
    try:
        await turnos(r, m, 6)
    except Exception as e:
        erro = f"{type(e).__name__}: {e}"
    check(erro is None, f"turno do mago sem erro ({erro})")
    check(p["hp"] < 500 or p.get("dormindo") or p.get("efeitos_magia"),
          f"o mago causou dano ou efeito no herói (PV {p['hp']}/500)")

    print("[2] formas animais ND 0 fogem do herói")
    for tipo in ("rato", "gato", "ovelha", "pombo"):
        r, p, m = sala(tipo, (3, 2))
        erro = None
        try:
            await turnos(r, m, 2)
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
        dist = max(abs(m["pos"][0] - 2), abs(m["pos"][1] - 2))
        check(erro is None, f"{tipo}: turno sem erro ({erro})")
        check(dist > 1, f"{tipo}: afastou-se do herói (distância {dist})")

    print("[3] fichas legadas (atk_bonus no topo) continuam no laço antigo")
    for tipo in ("skeleton", "orc"):
        r, p, m = sala(tipo)
        await turnos(r, m, 6)
        check(p["hp"] < 500, f"{tipo}: continua atacando (PV {p['hp']}/500)")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
