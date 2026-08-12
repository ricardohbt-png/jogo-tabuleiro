"""Regressões do Ferrão dos Charcos e das configurações do editor."""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    if not condition:
        raise AssertionError(label)
    print("OK:", label)


def room():
    r = S.GameRoom("FERRAO_CHARCOS_TEST")
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 12, "h": 12,
                "cx": 6, "cy": 6, "locked": False}]
    r.monsters = {}
    r.players = {}
    r._falas = []

    async def noop(*_args, **_kwargs):
        return None

    r.broadcast = noop
    r.push_state = noop
    r.gm_say = lambda msg, *_args, **_kwargs: r._falas.append(str(msg)) or noop()
    r.send_to = noop
    return r


def creature(r, monster_type, mid):
    definition = next(m for m in S.MONSTER_DEFS if m["type"] == monster_type)
    m = S.make_monster(definition, r.rooms[0])
    m["id"] = mid
    m["pos"] = [5, 5]
    r.monsters[mid] = m
    return m


def hero(r, pid, pos):
    p = S.make_player(pid, pid, "warrior", 0)
    p.update({"pos": list(pos), "alive": True, "connected": True,
              "hp": 500, "max_hp": 500, "ac": 1, "ac_base": 1,
              "fort": -50, "ref_": -50, "will": -50})
    r.players[pid] = p
    return p


async def main():
    print("[1] Fichas e movimento aquático")
    expected = {
        "ferrao_charcos_jovem": (46, 18, 6),
        "ferrao_charcos_adulto": (74, 20, 6),
        "ferrao_charcos_anciao": (130, 24, 6),
    }
    for typ, values in expected.items():
        r = room(); m = creature(r, typ, typ)
        check(f"{typ}: PV/CA/movimento", (m["max_hp"], m["ac"], m["movement"]) == values)
        check(f"{typ}: ignora custo de água", r._water_step_cost(m, 5, 5) == 1)
        check(f"{typ}: usa a imagem do Ferrão", m["image"] == "ferrao_do_lamacal")

    print("[2] Veneno e ferrão paralítico perdem só o movimento")
    r = room(); m = creature(r, "ferrao_charcos_jovem", "jovem"); p = hero(r, "h1", [5, 6])
    await r._execute_one_monster_attack(m, m["attacks"][3], {"kind": "player", "obj": p})
    check("veneno marca perda de movimento", p.get("turbilhao_perde_movimento") is True)
    check("veneno não marca perda de ação", not p.get("turbilhao_perde_acao"))

    print("[3] Dois Tentáculos imobilizam e Constrição causa dano")
    r = room(); m = creature(r, "ferrao_charcos_adulto", "adulto"); p = hero(r, "h1", [5, 6])
    tent = m["attacks"][1]
    await r._execute_one_monster_attack(m, tent, {"kind": "player", "obj": p})
    await r._execute_one_monster_attack(m, tent, {"kind": "player", "obj": p})
    check("dois tentáculos deixam o alvo preso", p.get("preso") and p.get("preso_por") == m["id"])
    hp = p["hp"]
    await r._upkeep_inicio_turno_monstro(m, [m])
    check("constrição causa dano no início do turno", p["hp"] < hp)
    check("alvo continua preso e sem poder se afastar", p.get("preso") and p.get("preso_por") == m["id"])

    print("[4] Ancião mantém dois alvos")
    r = room(); m = creature(r, "ferrao_charcos_anciao", "anciao")
    p1 = hero(r, "h1", [5, 6]); p2 = hero(r, "h2", [4, 5]); p3 = hero(r, "h3", [6, 5])
    for p in (p1, p2, p3):
        await r._execute_one_monster_attack(m, m["attacks"][1], {"kind": "player", "obj": p})
        await r._execute_one_monster_attack(m, m["attacks"][1], {"kind": "player", "obj": p})
    check("anciÃ£o prende dois", p1.get("preso") and p2.get("preso"))
    check("anciÃ£o não prende um terceiro", not p3.get("preso"))

    print("[5] Nuvem Ácida")
    r = room(); m = creature(r, "ferrao_charcos_adulto", "adulto"); p = hero(r, "h1", [6, 5]); outro = creature(r, "ferrao_charcos_jovem", "outro"); outro["pos"] = [5, 6]
    await r._criar_nuvem_acida(m, p["pos"], next(a for a in m["special_abilities"] if a["id"] == "nuvem_acida"))
    check("nuvem tem raio 1 e duração 2", r.zonas_especiais[-1]["raio"] == 1 and r.zonas_especiais[-1]["duracao"] == 2)
    r.round_num += 1
    hp = p["hp"]
    await r._processar_nuvem_acida_inicio_turno(p)
    check("tick da nuvem ocorre no turno", p["hp"] < hp)
    hp = p["hp"]
    await r._processar_nuvem_acida_inicio_turno(p)
    check("tick não duplica no mesmo turno/rodada", p["hp"] == hp)
    check("outro monstro também foi afetado", outro["hp"] < outro["max_hp"])

    print("[6] Editor preserva configurações")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "ferrao_charcos_adulto"))
    raw.update({"type": "ferrao_charcos_editor_teste", "name": "Ferrão Editor Teste", "monster_abilities": [
        {"id": "veneno_charcos", "attack_index": 2, "poison_dc": 18},
        {"id": "tentaculos_imobilizar", "attack_index": 1, "hits_needed": 3, "dc": 19, "max_targets": 2},
        {"id": "constricao_charcos", "damage_dice": 2, "damage_faces": 8, "damage_bonus": 6},
        {"id": "ferrao_paralitico", "attack_index": 3, "dc": 20},
        {"id": "nuvem_acida", "initial_dice": 3, "initial_faces": 6, "tick_dice": 1, "tick_faces": 8, "range": 5, "radius": 1, "duration": 2},
    ]})
    ok, normalized = S._validate_custom_monster(raw)
    check("ficha customizada aceita", ok)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("tentáculos preservam hits/CD/alvos", abilities["tentaculos_imobilizar"]["hits_needed"] == 3 and abilities["tentaculos_imobilizar"]["max_targets"] == 2)
    check("nuvem preserva dano e alcance", abilities["nuvem_acida"]["initial_damage"] == "3d6" and abilities["nuvem_acida"]["range"] == 5 and abilities["nuvem_acida"]["cooldown_turns"] == 4)
    print("Todos os testes do Ferrão dos Charcos passaram.")


if __name__ == "__main__":
    asyncio.run(main())
