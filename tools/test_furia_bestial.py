"""Fúria Bestial (Grotão) contra herói, monstro e servo animado — IA e Manual.

Regressão: na IA (`_monster_execute_attacks`) o ramo de alvo não-herói usava
`is_monster`, nunca definido -> NameError com alvo monstro/animado (Comando,
Dominar Mente, mesa livre do editor). No Manual (`_furia_bestial_mestre`) o
teste `alvo.get("alive")` barrava monstros, que não têm esse campo.
"""
import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import server as S
from server import GameRoom, make_player, make_monster

PASS = FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala():
    r = GameRoom("TEST")
    r._falas = []
    async def noop(*a, **k): pass
    async def say(msg, *a, **k): r._falas.append(msg)
    r.gm_say = say; r.broadcast = noop; r.push_state = noop
    r.broadcast_lobby = noop; r.broadcast_city_state = noop; r.send_to = noop
    r.phase = "playing"
    r.map_w = 14; r.map_h = 14
    r.tiles = [[S.FLOOR]*14 for _ in range(14)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    return r

def bicho(r, tipo, pos, mid):
    mdef = next(d for d in S.MONSTER_DEFS if d.get("type") == tipo)
    m = make_monster(mdef, r.rooms[0])
    m["id"] = mid; m["pos"] = list(pos); m["room_id"] = "r0"; m["alertado"] = True
    r.monsters[mid] = m
    return m

def grotao_que_sempre_acerta(r):
    g = bicho(r, "grotao", (2, 2), "g1")
    async def acerta(*a, **k): return True     # todos os grupos acertam
    r._execute_one_monster_attack = acerta
    return g

async def ia(r, g, alvo_obj):
    try:
        await r._monster_execute_attacks(g, alvo_obj)
        return None
    except Exception as e:
        return e

async def main():
    print("\n[1] IA — alvo monstro")
    r = sala(); g = grotao_que_sempre_acerta(r)
    alvo = bicho(r, "goblin", (4, 2), "alvo"); alvo["hp"] = alvo["max_hp"] = 999
    e = await ia(r, g, {"kind": "monster", "obj": alvo})
    check("sem exceção", e is None)
    check("alvo monstro sofreu o 1d6 extra", 993 <= alvo["hp"] <= 998)
    check("narrou a Fúria", len(r._falas) == 1)

    print("\n[2] IA — alvo monstro morre pelo extra")
    r = sala(); g = grotao_que_sempre_acerta(r)
    alvo = bicho(r, "goblin", (4, 2), "alvo"); alvo["hp"] = 1
    mortes = []
    async def espiao_morte(mm, killer): mortes.append((mm["id"], killer))
    r._monster_dies = espiao_morte
    e = await ia(r, g, {"kind": "monster", "obj": alvo})
    check("sem exceção", e is None)
    check("fluxo de morte do monstro chamado, creditado ao Grotão",
          mortes == [("alvo", "g1")])

    print("\n[3] IA — alvo servo animado")
    r = sala(); g = grotao_que_sempre_acerta(r)
    anim = {"id": "a1", "nome": "Servo", "tipo": "goblin", "pos": [4, 2],
            "vida_atual": 999, "vida_max": 999, "ca": 10}
    e = await ia(r, g, {"kind": "animado", "obj": anim})
    check("sem exceção", e is None)
    check("servo sofreu o 1d6 extra", 993 <= anim["vida_atual"] <= 998)

    print("\n[4] IA — alvo herói (comportamento antigo preservado)")
    r = sala(); g = grotao_que_sempre_acerta(r)
    p = make_player("h1", "Victor", "warrior", 0)
    p["pos"] = [4, 2]; p["alive"] = True; p["connected"] = True
    p["hp"] = p["max_hp"] = 999
    r.players = {"h1": p}
    e = await ia(r, g, {"kind": "player", "obj": p})
    check("sem exceção", e is None)
    check("herói sofreu o 1d6 extra", 993 <= p["hp"] <= 998)

    print("\n[5] Manual — alvo monstro")
    r = sala(); g = bicho(r, "grotao", (2, 2), "g1")
    alvo = bicho(r, "goblin", (4, 2), "alvo"); alvo["hp"] = alvo["max_hp"] = 999
    await r._furia_bestial_mestre(g, alvo, 0, True)
    await r._furia_bestial_mestre(g, alvo, 1, True)
    check("Fúria dispara contra monstro no Manual", 993 <= alvo["hp"] <= 998)

    print("\n[6] Manual — alvo já morto não recebe o extra")
    r = sala(); g = bicho(r, "grotao", (2, 2), "g1")
    alvo = bicho(r, "goblin", (4, 2), "alvo"); alvo["hp"] = 0
    await r._furia_bestial_mestre(g, alvo, 0, True)
    await r._furia_bestial_mestre(g, alvo, 1, True)
    check("sem narração para alvo morto", not r._falas)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
