"""Ordem dos servos: a mesma no game_state (fichas na vez do herói) e ao abrir a vez deles.

Roda da raiz: python -X utf8 tools/test_servos_ordem.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

FALHAS = []


def check(nome, cond):
    print(("  ✅ " if cond else "  ❌ ") + nome)
    if not cond:
        FALHAS.append(nome)


async def nada(*a, **k):
    return None


def sala():
    r = S.GameRoom("SRV")
    r.gm_say = r.push_state = r.broadcast = r.send_to = nada
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "cx": 6, "cy": 6, "locked": False, "doors": []}]
    p = S.make_player("p", "Pedro", "mage", 0)
    p["pos"] = [5, 5]
    servo = lambda i, dex, int_, **k: dict({"id": i, "owner": "p", "nome": i, "tipo": "skeleton", "dex": dex, "int_": int_,
                                            "vida_atual": 5, "vida_max": 5, "ca": 12, "pos": [6, 5], "movimento": 3,
                                            "moves_left": 3, "acted": False, "attacks": []}, **k)
    p["animados"] = [servo("lento", 8, 10), servo("rapido", 16, 10), servo("medio", 12, 14),
                     servo("morto", 20, 10, vida_atual=0), servo("roubado", 18, 10, dominado_por_monstro=True)]
    r.players = {"p": p}
    r.player_order = ["p"]
    return r, p


def main():
    print("\n[1] Ordem calculada pelo servidor")
    r, p = sala()
    ordem = [a["id"] for a in r._ordem_servos(p)]
    check("por iniciativa (DES + mod INT), vivos e leais", ordem == ["rapido", "medio", "lento"])

    print("\n[2] O game_state manda a mesma ordem para as fichas")
    estado = r._game_state_payload()
    check("servos_ordem por herói", estado.get("servos_ordem", {}).get("p") == ["rapido", "medio", "lento"])
    check("herói sem servos fica fora", "p" in estado["servos_ordem"] and len(estado["servos_ordem"]) == 1)

    print("\n[3] Ao abrir a vez dos servos, a fila é a mesma")
    r, p = sala()
    r.initiative_active = True
    r._rebuild_initiative()
    r.initiative_index = 0
    r._is_turn = lambda pid: True
    asyncio.run(r.handle_end_turn("p"))
    check("animados_order igual à ordem das fichas", r.animados_order == ["rapido", "medio", "lento"])

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
