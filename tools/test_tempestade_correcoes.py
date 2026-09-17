"""Correções da Tempestade de Ciclones (2026-09-17) — flags de ciclone e
entrada na tempestade pelos caminhos de movimento que ficavam de fora.

Roda da raiz:
    python -X utf8 tools/test_tempestade_correcoes.py
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


def setup(level=5):
    r = S.GameRoom("TEST")
    r.events = []

    async def noop(*a, **k):
        pass

    async def send_to(*a, **k):
        if len(a) >= 2 and isinstance(a[1], dict):
            r.events.append(a[1])

    r.broadcast = noop; r.push_state = noop; r.gm_say = noop
    r._broadcast_dado = noop; r.send_to = send_to
    r._tem_linha_de_visao = lambda *a, **k: True
    r._alcance_com_altura = lambda *a, **k: True
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.explored = {(x, y) for y in range(12) for x in range(12)}
    r.phase = "playing"; r.round_num = 1; r.monsters = {}; r.decorations = []
    r._rebuild_decor_index(); r.materiais = {}; r._rebuild_materiais_index()
    p = S.make_player("c", "Lewis", "cleric", 0)
    p.update(level=level, pos=[5, 5], alive=True, hp=100, max_hp=100,
             fome=50, sede=50, action_done=False, moves_left=6)
    p["magias_conhecidas"] = ["tempestade_ciclones"]
    r.players["c"] = p; r.player_order = ["c"]
    r.initiative_active = True; r._rebuild_initiative()
    return r, p


def add_monster(r, tipo, mid, pos):
    mdef = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(mdef, {"cx": pos[0], "cy": pos[1], "id": 0})
    m.update(id=mid, pos=list(pos), hp=60, max_hp=60, resistances=[],
             alertado=True, control_mode="auto")
    r.monsters[mid] = m
    return m


async def tempestade_com_ciclone_em(r, casa, save_passa):
    """Lança a tempestade centrada em (6,6) e confirma um ciclone em `casa`."""
    await r.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 6, "ty": 6})
    z = next(x for x in r.zonas_especiais if x["tipo"] == "tempestade_ciclones")

    async def save(*a, **k):
        return (save_passa, 20 if save_passa else 1, 0, 0)
    r._save_mostrado = save
    permit = [tuple(t) for t in z["ciclones_permitidos"]]
    escolha = [list(casa)] + [list(t) for t in permit if t != tuple(casa)][:z["ciclones_pendentes"] - 1]
    await r.handle_tempestade_ciclones_posicoes("c", z["id"], escolha)
    return z


async def main():
    print("\n[1] Monstro que FALHA o Reflexos perde movimento e ação em UM turno só")
    # O prólogo lia `turbilhao_perde_movimento` com `get`; o `return False` do
    # `turbilhao_perde_acao` pulava os `pop` tardios da IA, e o flag zerava o
    # movimento de novo no turno seguinte.
    r, p = setup()
    m = add_monster(r, "goblin", "g1", (7, 7))
    await tempestade_com_ciclone_em(r, (7, 7), save_passa=False)
    check("impacto marcou perda de movimento e de ação",
          m.get("turbilhao_perde_movimento") and m.get("turbilhao_perde_acao"))
    m["pos"] = [0, 0]                      # fora da tempestade: isola o flag
    resultados = []
    for _ in range(3):
        r.round_num += 1
        m["_water_moves_left"] = r._water_turn_moves(m, m.get("movement", 4))
        m["master_moves_left"] = m["_water_moves_left"]
        age = await r._upkeep_inicio_turno_monstro(m, [m])
        resultados.append((age, m["_water_moves_left"]))
    check("turno 1: não age e não se move", resultados[0] == (False, 0))
    check("turno 2: age E se move normalmente", resultados[1][0] is True and resultados[1][1] > 0)
    check("turno 3: normal", resultados[2][0] is True and resultados[2][1] > 0)
    check("flag de movimento foi consumido pelo prólogo", "turbilhao_perde_movimento" not in m)

    print("\n[2] Monstro sem ai_type (esqueleto) volta a andar depois do ciclone")
    # O caminho legado de gm_phase nunca fazia `pop` do flag: um esqueleto
    # atingido uma vez ficava imóvel para sempre (só o Mestre em Manual soltava).
    r, p = setup()
    m = add_monster(r, "skeleton", "s1", (7, 7))
    check("o esqueleto realmente não tem ai_type", not m.get("ai_type"))
    await tempestade_com_ciclone_em(r, (7, 7), save_passa=True)   # só perde movimento
    m["pos"] = [0, 0]; p["pos"] = [1, 0]                           # fora da tempestade, herói visível
    movs = []
    for _ in range(3):
        r.round_num += 1
        await r.gm_phase(only_monster=m)
        movs.append(m.get("_water_moves_left"))
    check("turno 1: sem movimento", movs[0] == 0)
    check("turno 2: flag apagado", "turbilhao_perde_movimento" not in m)
    check("turno 2 e 3: já se moveu ou tem orçamento (não está preso)",
          all(v is None or v > 0 or m["pos"] != [0, 0] for v in movs[1:]))

    print("\n[3] Servo comandado automaticamente entra na tempestade e sofre o ciclone")
    # `_tempestade_verificar_entrada` só estava nos caminhos manuais
    # (handle_move/mover_animado/mover_prisioneiro/_commit_monster_step); o
    # comando automático, o servo dominado e o licantropo atravessavam ciclones
    # sem sofrer nada.
    r, p = setup(level=5)                  # área 4x4: casas 5..8
    m = add_monster(r, "goblin", "g1", (3, 7))
    z = await tempestade_com_ciclone_em(r, (8, 7), save_passa=False)
    r.round_num += 1
    r.animados_phase_pid = "c"
    servo = {"id": "a1", "tipo": "goblin", "nome_base": "Goblin", "vida_atual": 30, "vida_max": 30,
             "pos": [9, 7], "moves_left": 3, "movimento": 3, "ataque": 1, "dano": "1d6", "acted": False}
    p["animados"] = [servo]
    await r.handle_comandar_animados("c")
    check("servo andou para dentro da tempestade", tuple(servo["pos"]) in {tuple(t) for t in z["tiles"]})
    check("servo sofreu o dano do ciclone ao entrar", servo["vida_atual"] < 30)
    check("servo recebeu a condição do ciclone", servo.get("turbilhao_perde_movimento"))

    print("\n[4] Servo dominado por monstro e licantropo também entram na tempestade")
    r, p = setup(level=5)
    z = await tempestade_com_ciclone_em(r, (8, 7), save_passa=False)
    r.round_num += 1
    servo = {"id": "a2", "tipo": "goblin", "nome_base": "Goblin", "vida_atual": 30, "vida_max": 30,
             "pos": [9, 7], "moves_left": 3, "movimento": 3, "ataque": 1, "dano": "1d6",
             "dominado_por_monstro": "m9"}
    p["animados"] = [servo]
    p["pos"] = [5, 7]                       # alvo do servo dominado, do outro lado
    await r._animado_ataca_jogador(servo)
    check("servo dominado sofreu o ciclone ao entrar", servo["vida_atual"] < 30)
    r, p = setup(level=5)
    z = await tempestade_com_ciclone_em(r, (8, 7), save_passa=False)
    r.round_num += 1
    lobo = S.make_player("w", "Ana", "warrior", 1)
    lobo.update(level=1, pos=[9, 7], alive=True, hp=40, max_hp=40, moves_left=4, licantropo=True)
    r.players["w"] = lobo
    m = add_monster(r, "goblin", "g2", (5, 7))
    hp = lobo["hp"]
    await r._turno_licantropo(lobo)
    check("licantropo andou para dentro da tempestade", tuple(lobo["pos"]) in {tuple(t) for t in z["tiles"]})
    check("licantropo sofreu o ciclone ao entrar", lobo["hp"] < hp)

    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
