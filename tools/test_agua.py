"""Testes das regras do terreno Água — modelo de CUSTO POR CASA.

A água não reduz mais o orçamento do turno: ela encarece cada casa que a
criatura ENTRA (`_water_step_cost`). O orçamento (`moves_left` no herói,
`_water_moves_left` no monstro) é o normal e é debitado do custo a cada passo.

Execute da raiz: python tools/test_agua.py
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
from server import GameRoom, MATERIAIS, make_player

PASS = 0
FAIL = 0


def check(label, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


# ── Fixtures ────────────────────────────────────────────────────────────────
# Mapa de referência (linha y=1): x=0 seco | x=1,2 água rasa | x=3 água profunda
AGUA_RASA = (1, 1)
AGUA_RASA_2 = (2, 1)
AGUA_FUNDA = (3, 1)
AREIA = (4, 1)


def sala():
    """Sala mínima com o mapa de referência e os broadcasts capturados."""
    r = GameRoom("WATER_TEST")
    errs = []

    async def noop(*a, **k):
        pass

    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))

    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.broadcast_city_state = noop
    r.send_to = cap_send
    r._errs = errs

    r.phase = "playing"
    r.map_w = r.map_h = 10
    r.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    r.rooms = []
    r.monsters = {}
    r.chests = {}
    r.ground_items = {}
    r.decorations = []
    r.materiais = {AGUA_RASA: "agua", AGUA_RASA_2: "agua", AGUA_FUNDA: "agua_profunda", AREIA: "areia_deserto"}
    return r


def heroi(armor_id=None, pos=(0, 1)):
    p = make_player("h", "Teste", "warrior", 0)
    p["pos"] = list(pos)
    p["gear"]["armor"] = ({"id": armor_id} if armor_id else None)
    return p


def main():
    print("\n[1] Materiais de água continuam pisos atravessáveis")
    for mat in ("agua", "agua_profunda"):
        check(f"{mat} é piso não-sólido",
              MATERIAIS[mat]["categoria"] == "piso" and not MATERIAIS[mat]["solido"])

    print("\n[2] _water_step_cost — matriz terreno × armadura")
    r = sala()
    seco = (0, 1)
    # Chão seco custa 1 para qualquer armadura.
    for armor in (None, "leather", "chainmail", "plate"):
        check(f"seco/{armor or 'sem armadura'}: 1",
              r._water_step_cost(heroi(armor), *seco) == 1)
    # Água rasa: base 2; leve não acrescenta, média +1, pesada +2.
    for armor, esperado in ((None, 2), ("leather", 2), ("chainmail", 3), ("plate", 4)):
        check(f"rasa/{armor or 'sem armadura'}: {esperado}",
              r._water_step_cost(heroi(armor), *AGUA_RASA) == esperado)
    # Água profunda: base 3, mesmos acréscimos.
    for armor, esperado in ((None, 3), ("leather", 3), ("chainmail", 4), ("plate", 5)):
        check(f"profunda/{armor or 'sem armadura'}: {esperado}",
              r._water_step_cost(heroi(armor), *AGUA_FUNDA) == esperado)

    print("\n[3] Monstros: armadura natural e prioridade do equipamento")
    natural = {"pos": [3, 1], "natural_armor": 2}
    check("natural na rasa: 2+1=3", r._water_step_cost(natural, *AGUA_RASA) == 3)
    check("natural na profunda: 3+1=4", r._water_step_cost(natural, *AGUA_FUNDA) == 4)
    check("natural em chão seco não paga nada: 1", r._water_step_cost(natural, *seco) == 1)
    check("areia do deserto custa 2 por casa", r._water_step_cost(heroi(), *AREIA) == 2)
    equipado = {"natural_armor": 6,
                "equipment_items": [{"kind": "armor", "armor_category": "pesada"}]}
    check("armadura equipada vence a natural (profunda: 3+2=5)",
          r._water_step_cost(equipado, *AGUA_FUNDA) == 5)

    print("\n[4] Movimento Errático ignora o custo de água")
    erratico = {"pos": [3, 1], "movement": 6, "natural_armor": 6,
                "special_abilities": [{"id": "movimento_erratico"}]}
    check("errático na rasa: 1", r._water_step_cost(erratico, *AGUA_RASA) == 1)
    check("errático na profunda: 1", r._water_step_cost(erratico, *AGUA_FUNDA) == 1)

    print("\n[5] _water_turn_moves — orçamento normal, sem penalidade de terreno")
    check("sem armadura mantém a base", r._water_turn_moves(heroi(), 5) == 5)
    check("pesada mantém a base (a água cobra por casa, não aqui)",
          r._water_turn_moves(heroi("plate"), 5) == 5)
    check("piso mínimo de 1", r._water_turn_moves(heroi(), 0) == 1)
    sujo = heroi()
    sujo["_water_min_step_used"] = True
    sujo["_water_penalty_applied"] = True
    sujo["_water_heavy_step_used"] = True
    sujo["_deep_water_penalty_applied"] = True
    r._water_turn_moves(sujo, 5)
    check("limpa os flags de passo do turno anterior",
          not any(sujo.get(k) for k in ("_water_min_step_used", "_water_penalty_applied",
                                        "_water_heavy_step_used", "_deep_water_penalty_applied")))

    print("\n[6] handle_move (herói) — custo debitado por casa")
    r = sala()
    p = heroi(pos=(0, 1))
    r.players = {"h": p}
    r.current_pid = lambda: "h"
    p["moves_left"] = 6
    asyncio.run(r.handle_move("h", 1, 0))          # entra na água rasa: custa 2
    check("entrou na água rasa", p["pos"] == [1, 1])
    check("debitou 2 (6→4)", p["moves_left"] == 4)
    asyncio.run(r.handle_move("h", 1, 0))          # segue na rasa: cobra de novo
    check("água contínua cobra a cada casa (4→2)", p["moves_left"] == 2)
    asyncio.run(r.handle_move("h", 1, 0))          # profunda custa 3 > 2 restantes
    check("bloqueia passo sem orçamento", p["pos"] == [2, 1])
    check("avisa o custo da casa", any("custa 3" in e for e in r._errs))

    print("\n[7] Passo mínimo: a 1ª casa do turno nunca fica travada")
    r = sala()
    p = heroi("plate", pos=(0, 1))                 # pesada na rasa custa 4
    r.players = {"h": p}
    r.current_pid = lambda: "h"
    p["moves_left"] = 1                            # orçamento menor que o custo
    asyncio.run(r.handle_move("h", 1, 0))
    check("com 1 de movimento ainda entra na água", p["pos"] == [1, 1])
    check("mas zera o orçamento", p["moves_left"] == 0)
    check("marca o passo mínimo como usado", p.get("_water_min_step_used") is True)
    r._errs.clear()
    asyncio.run(r.handle_move("h", 1, 0))
    check("não concede um segundo passo mínimo", p["pos"] == [1, 1])
    # O passo mínimo exige orçamento > 0: com 0 e sem ter andado, continua travado.
    r2 = sala()
    p2 = heroi("plate", pos=(0, 1))
    r2.players = {"h": p2}
    r2.current_pid = lambda: "h"
    p2["moves_left"] = 0
    asyncio.run(r2.handle_move("h", 1, 0))
    check("orçamento zerado não anda nem o passo mínimo", p2["pos"] == [0, 1])

    print("\n[8] _commit_monster_step (monstro) — mesmo custo e mesmo passo mínimo")
    r = sala()
    m = {"id": "g1", "type": "goblin", "name": "G", "pos": [0, 1], "hp": 10, "max_hp": 10,
         "ac": 12, "movement": 6, "size": [1, 1]}
    r.monsters = {"g1": m}
    m["_water_moves_left"] = r._water_turn_moves(m, m["movement"])
    m["_moved_this_turn"] = False
    check("passo para a rasa aceito", asyncio.run(r._commit_monster_step(m, 1, 1)) is True)
    check("debitou 2 (6→4)", m["_water_moves_left"] == 4)
    check("passo para a rasa aceito (2ª casa)", asyncio.run(r._commit_monster_step(m, 2, 1)) is True)
    check("debitou 2 (4→2)", m["_water_moves_left"] == 2)
    check("profunda (custo 3) recusada com 2", asyncio.run(r._commit_monster_step(m, 3, 1)) is False)
    check("posição intacta após a recusa", m["pos"] == [2, 1])

    print("\n[9] Orçamento do monstro é renovado a cada turno")
    # Regressão: o gasto NÃO pode acumular entre turnos. `gm_phase` renova para a
    # IA e `_master_manual_window` para o modo Manual do Mestre (test_modo_mestre [29]).
    r = sala()
    m = {"id": "g1", "type": "goblin", "name": "G", "pos": [0, 5], "hp": 10, "max_hp": 10,
         "ac": 12, "movement": 3, "size": [1, 1]}
    r.monsters = {"g1": m}
    andou = []
    for _ in range(3):                              # 3 turnos, terreno seco
        m["_water_moves_left"] = r._water_turn_moves(m, m["movement"])
        m["_moved_this_turn"] = False
        andou.append(asyncio.run(r._commit_monster_step(m, m["pos"][0] + 1, m["pos"][1])))
    check("anda nos 3 turnos seguidos", andou == [True, True, True])
    check("orçamento renovado sobra 2 (3-1)", m["_water_moves_left"] == 2)

    print("\n[10] _apply_water_entry_penalty — compat dos chamadores legados")
    # Os chamadores antigos descontam 1 por conta própria depois desta chamada,
    # então ela debita SOMENTE o excedente do terreno (custo - 1).
    r = sala()
    leg = heroi(pos=(0, 1)); leg["moves_left"] = 6
    r._apply_water_entry_penalty(leg, *AGUA_RASA)
    check("rasa sem armadura debita o excedente 1 (6→5)", leg["moves_left"] == 5)
    leg_pesado = heroi("plate", pos=(0, 1)); leg_pesado["moves_left"] = 6
    r._apply_water_entry_penalty(leg_pesado, *AGUA_RASA)
    check("rasa/pesada debita o excedente 3 (6→3)", leg_pesado["moves_left"] == 3)
    leg_seco = heroi(pos=(0, 1)); leg_seco["moves_left"] = 6
    r._apply_water_entry_penalty(leg_seco, *(0, 1))
    check("chão seco não debita nada", leg_seco["moves_left"] == 6)
    leg_err = {"pos": [0, 1], "moves_left": 6, "natural_armor": 6,
               "special_abilities": [{"id": "movimento_erratico"}]}
    r._apply_water_entry_penalty(leg_err, *AGUA_FUNDA)
    check("errático não debita nada", leg_err["moves_left"] == 6)

    print(f"\n{'='*50}\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
