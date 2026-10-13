"""Reações elementais (terreno x elemento). Roda da raiz: python -X utf8 tools/test_terrain_reactions.py
Spec: docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
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

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    """Sala 20x12 de chão, fase 'playing', sem rede; captura broadcasts e narração."""
    r = S.GameRoom("REACOES")
    r.msgs = []
    r.narr = []
    async def noop(*a, **k):
        pass
    async def bc(msg, *a, **k):
        r.msgs.append(msg)
    async def say(txt, *a, **k):
        r.narr.append(str(txt))
    r.gm_say = say; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 13):
        for x in range(1, 21):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 20, "h": 12, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


def roda(coro):
    return asyncio.run(coro)


print("[1] materiais novos")
check("piche é piso com terreno piche",
      S.MATERIAIS["piche"]["categoria"] == "piso" and S.MATERIAIS["piche"]["terreno"] == "piche")
check("lava_solidificada é piso transitável",
      S.MATERIAIS["lava_solidificada"]["categoria"] == "piso"
      and not S.MATERIAIS["lava_solidificada"]["solido"])
r = sala()
h = heroi(r, "a", "Ana", "warrior", [2, 2])
pinta(r, "piche", [(5, 5)])
pinta(r, "lava_solidificada", [(6, 5)])
pinta(r, "lava", [(7, 5)])
check("entrar no piche custa 2", r._water_step_cost(h, 5, 5) == 2)
check("entrar na crosta custa 1", r._water_step_cost(h, 6, 5) == 1)
check("entrar na lava custa 2", r._water_step_cost(h, 7, 5) == 2)
check("a crosta não é lava", not r._is_lava_tile(6, 5) and r._is_lava_tile(7, 5))

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
