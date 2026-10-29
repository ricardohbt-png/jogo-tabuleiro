"""Fogo residual da Bola de Fogo: quem ANDA pela área sofre o dano da rodada.

Antes, só o herói (handle_move) chamava `_verificar_entrada_zona_fogo`; monstros,
servos animados e o prisioneiro atravessavam a zona sem dano, e só quem estivesse
parado dentro dela na virada da rodada era ferido. Um monstro grande também
só era conferido pela casa-âncora.

Roda da raiz:
    python -X utf8 tools/test_bola_fogo_entrada.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


DANO_R2 = 8      # dano da rodada atual (rodada_atual = 2) usado em todos os cenários


def sala():
    room = S.GameRoom("TEST")

    async def noop(*a, **k):
        return None
    room.broadcast = noop
    room.push_state = noop
    room.gm_say = noop
    room.send_to = noop
    room._is_turn = lambda pid: True
    room.phase = "playing"
    room.map_w = room.map_h = 14
    room.tiles = [[S.FLOOR] * 14 for _ in range(14)]
    room.monsters = {}
    room.players = {}
    room.zonas_especiais = [{
        "id": "z1", "tipo": "bola_fogo", "cx": 5, "cy": 5, "raio": 1, "area_lado": None,
        "dano_r2": DANO_R2, "dano_r3": DANO_R2 // 2, "rodada_atual": 2, "rodadas_max": 3,
        "criado_em": 1, "expira_em": 4, "save_dif": 13, "ativa": True, "caster": "p",
    }]
    room.round_num = 1
    return room


def monstro(room, tipo, pos, hp=40):
    mdef = next(x for x in S.MONSTER_DEFS if x["type"] == tipo)
    m = S.make_monster(mdef, {"cx": pos[0], "cy": pos[1], "id": 0})
    m.update(pos=list(pos), id="m1", hp=hp, max_hp=hp)
    room.monsters["m1"] = m
    return m


async def passo(room, m, x, y):
    m["_water_moves_left"] = 6
    m.pop("_moved_this_turn", None)
    return await room._commit_monster_step(m, x, y)


async def main():
    # [1] Monstro que ANDA pela área é ferido a cada passo dentro dela
    room = sala()
    m = monstro(room, "orc_guerreiro", (8, 5))
    m["resistances"] = []
    hps = [m["hp"]]
    for x in (7, 6, 5, 4, 3):
        await passo(room, m, x, 5)
        hps.append(m["hp"])
    print("   hp por passo:", hps)
    check("fora da área (8→7) não fere", hps[1] == hps[0])
    dentro = [hps[i] - hps[i + 1] for i in (1, 2, 3)]
    check("cada passo dentro da área (6,5)(5,5)(4,5) fere", all(d > 0 for d in dentro))
    check("saiu da área (3,5): sem dano", hps[5] == hps[4])

    # [2] Monstro 2x2: só uma casa do corpo entra na área (a âncora fica fora)
    room = sala()
    g = monstro(room, "ciclope", (2, 4), hp=80)
    g["pos"] = [2, 4]
    antes = g["hp"]
    await passo(room, g, 3, 4)
    corpo = [tuple(t) for t in room._monster_tiles(g)]
    print("   corpo do ciclope:", corpo)
    check("âncora fora da área, corpo dentro", (3, 4) not in {(x, y) for x in range(4, 7) for y in range(4, 7)}
          and any(4 <= x <= 6 and 4 <= y <= 6 for x, y in corpo))
    check("monstro grande com o corpo na área é ferido", g["hp"] < antes)

    # [3] Quem voa acima do chão ignora as chamas presas ao piso
    room = sala()
    v = monstro(room, "orc_guerreiro", (7, 5))
    v["altura"] = S.ALTURA_MIN + 2
    antes = v["hp"]
    await passo(room, v, 6, 5)
    check("monstro voando não sofre", v["hp"] == antes)

    # [4] Zona apagada não fere
    room = sala()
    room.zonas_especiais[0]["ativa"] = False
    m = monstro(room, "orc_guerreiro", (7, 5))
    antes = m["hp"]
    await passo(room, m, 6, 5)
    check("zona inativa não fere", m["hp"] == antes)

    # [5] O herói continua levando UM dano por passo (sem dano em dobro)
    room = sala()
    h = S.make_player("h", "Guerreiro", "warrior", 1)
    h.update(pos=[8, 5], alive=True, hp=60, max_hp=60, fome=40, sede=40, moves_left=6, connected=True)
    room.players["h"] = h
    hps = [h["hp"]]
    for _ in range(3):
        await room.handle_move("h", -1, 0)
        hps.append(h["hp"])
    print("   hp do herói por passo:", hps)
    check("passo fora da área (7,5): sem dano", hps[1] == hps[0])
    check("passos dentro (6,5)(5,5): um dano cada", hps[1] - hps[2] > 0 and hps[2] - hps[3] > 0)
    check("o dano por passo não é dobrado", hps[1] - hps[2] == hps[2] - hps[3])

    # [6] Servo animado que anda pela área
    room = sala()
    mage = S.make_player("p", "Pedro", "mage", 0)
    mage.update(pos=[1, 1], alive=True, hp=40, max_hp=40, fome=40, sede=40)
    a = {"id": "a1", "pos": [7, 5], "vida_atual": 30, "vida_max": 30, "moves_left": 6,
         "tipo": "esqueleto", "nome": "Servo", "acted": False}
    mage["animados"] = [a]
    room.players["p"] = mage
    room.animados_phase_pid = "p"
    antes = a["vida_atual"]
    await room.handle_mover_animado("p", "a1", -1, 0)
    check("servo que entra na área sofre", a["vida_atual"] < antes)

    # [7] Prisioneiro liberto que anda pela área
    room = sala()
    mage = S.make_player("p", "Pedro", "mage", 0)
    mage.update(pos=[1, 1], alive=True, hp=40, max_hp=40, fome=40, sede=40)
    room.players["p"] = mage
    room.animados_phase_pid = "p"
    room.prisoner = {"pos": [7, 5], "hp": 30, "max_hp": 30, "alive": True, "freed": True,
                     "rescuer_pid": "p", "moves_left": 6, "ac": 10}
    antes = room.prisoner["hp"]
    await room.handle_mover_prisioneiro("p", -1, 0)
    check("prisioneiro que entra na área sofre", room.prisoner["hp"] < antes)


asyncio.run(main())
print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
sys.exit(1 if FAIL else 0)
