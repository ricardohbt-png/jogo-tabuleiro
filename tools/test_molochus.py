"""Regressoes das variantes e habilidades do Molochus."""
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
    r = S.GameRoom("MOLOCHUS_TEST")
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 12, "h": 12,
                "cx": 6, "cy": 6, "locked": False}]
    r.monsters = {}
    r.players = {}
    r.zonas_especiais = []
    r._falas = []

    async def noop(*_args, **_kwargs):
        return None

    async def say(msg, *_args, **_kwargs):
        r._falas.append(str(msg))

    r.broadcast = noop
    r.push_state = noop
    r.gm_say = say
    r.send_to = noop
    return r


def creature(r, monster_type, mid):
    definition = next(m for m in S.MONSTER_DEFS if m["type"] == monster_type)
    m = S.make_monster(definition, r.rooms[0])
    m["id"] = mid
    m["pos"] = [5, 5]
    r.monsters[mid] = m
    return m


def hero(r, pid, pos, hp=500, ref=-50):
    p = S.make_player(pid, pid, "warrior", 0)
    p.update({"pos": list(pos), "alive": True, "connected": True,
              "hp": hp, "max_hp": hp, "ac": 1, "ac_base": 1,
              "fort": -50, "ref_": ref, "will": -50, "str_": 20})
    r.players[pid] = p
    return p


async def main():
    print("[1] Fichas, movimento e resistencias")
    expected = {
        "molochus_jovem": (64, 20, "1d4", 1),
        "molochus_adulto": (96, 22, "1d6", 2),
        "molochus_anciao": (170, 26, "2d6", 2),
    }
    for typ, values in expected.items():
        r = room(); m = creature(r, typ, typ)
        aura = next(a for a in m["special_abilities"] if a["id"] == "aura_escaldante")
        check(f"{typ}: PV/CA/movimento", (m["max_hp"], m["ac"], m["movement"]) == values[:2] + (6,))
        check(f"{typ}: aura e imagem", aura["damage"] == values[2] and m["image"] == "molochos")
        check(f"{typ}: imunidade/fraquezas", m["immunities"] == ["fire"] and {w["type"] for w in m["weaknesses"]} == {"cold", "water"})
        check(f"{typ}: habilidades", "aura_escaldante" in [a["id"] for a in m["special_abilities"]])

    print("[2] Imunidade a fogo e dano dobrado de gelo/agua")
    r = room(); m = creature(r, "molochus_adulto", "m")
    check("fogo e zerado", r._apply_damage_types(10, [S.DMG_FIRE], m) == 0)
    check("gelo dobra", r._apply_damage_types(10, [S.DMG_COLD], m) == 20)
    check("agua dobra", r._apply_damage_types(10, [S.DMG_WATER], m) == 20)

    print("[3] Ataque, aura e Sangue em Ebulição")
    old_roll = S.roll_dice
    S.roll_dice = lambda _expr: 1
    try:
        r = room(); m = creature(r, "molochus_adulto", "m"); p = hero(r, "h", [5, 6])
        hp_before = p["hp"]
        await r._execute_one_monster_attack(m, m["attacks"][0], {"kind": "player", "obj": p})
        check("ataque aplica dano", p["hp"] < hp_before)

        hp_before = p["hp"]
        await r._processar_aura_escaldante_inicio(p)
        check("aura adjacente causa dano", p["hp"] < hp_before)

        r2 = room(); m2 = creature(r2, "molochus_adulto", "m2"); p2 = hero(r2, "h2", [5, 6])
        hp_before = p2["hp"]
        await r2._molochus_sangue_em_ebulicao(m2, p2, True, 1)
        check("sangue retalia melee", p2["hp"] < hp_before)
        hp_before = p2["hp"]
        await r2._molochus_sangue_em_ebulicao(m2, p2, False, 1)
        check("sangue nao retalia distancia", p2["hp"] == hp_before)
    finally:
        S.roll_dice = old_roll

    print("[4] Investida e Explosao de Vapor")
    old_roll = S.roll_dice; S.roll_dice = lambda _expr: 1
    try:
        r = room(); m = creature(r, "molochus_adulto", "m"); p = hero(r, "h", [5, 6])
        m["_molochus_move_count"] = 3
        await r._execute_one_monster_attack(m, m["attacks"][2], {"kind": "player", "obj": p})
        check("investida flamejante usa movimento", any("Investida Flamejante" in f for f in r._falas) or p["hp"] < p["max_hp"])

        r2 = room(); m2 = creature(r2, "molochus_adulto", "m2"); p2 = hero(r2, "h2", [5, 8])
        target = {"kind": "player", "obj": p2}
        targets = [target]
        used = await r2._usar_explosao_vapor(m2, next(a for a in m2["special_abilities"] if a["id"] == "explosao_vapor"), target, targets)
        check("vapor usa cone", used and p2["hp"] < p2["max_hp"])
        check("vapor tem recarga 6", m2["ability_cooldowns"].get("explosao_vapor") == 6)
        check("vapor nao repete em recarga", not await r2._monster_try_explosao_vapor(m2, targets))
    finally:
        S.roll_dice = old_roll

    print("[5] Morte Explosiva e chamas persistentes")
    old_roll = S.roll_dice; S.roll_dice = lambda _expr: 1
    try:
        r = room(); m = creature(r, "molochus_adulto", "m"); p = hero(r, "h", [5, 6])
        await r._molochus_morte_explosiva(m, next(a for a in m["special_abilities"] if a["id"] == "morte_explosiva"))
        check("explosao cria zona", any(z.get("tipo") == "molochus_chamas" and z.get("raio") == 2 for z in r.zonas_especiais))
        hp_before = p["hp"]
        await r._processar_zona_molochus_inicio_turno(p)
        check("chamas causam dano no inicio", p["hp"] < hp_before)
    finally:
        S.roll_dice = old_roll

    print("[6] Editor preserva configuracoes")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "molochus_adulto"))
    raw.update({"type": "molochus_editor_teste", "name": "Molochus Editor Teste", "monster_abilities": [
        {"id": "aura_escaldante", "damage_dice": 2, "damage_faces": 8, "radius": 1},
         {"id": "dano_retaliacao", "damage_dice": 3, "damage_faces": 4, "damage_type": "fire"},
        {"id": "investida_flamejante", "damage_dice": 4, "damage_faces": 6, "move_required": 3},
        {"id": "explosao_vapor", "damage_dice": 5, "damage_faces": 6, "dc": 17, "cooldown_turns": 1},
        {"id": "morte_explosiva", "damage_dice": 6, "damage_faces": 6, "radius": 3, "duration": 3},
    ]})
    ok, normalized = S._validate_custom_monster(raw)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("ficha customizada aceita", ok)
    check("configuracoes molochus preservadas", abilities["aura_escaldante"]["damage"] == "2d8" and abilities["dano_retaliacao"]["damage"] == "3d4")
    check("vapor mantém recarga fixa", abilities["explosao_vapor"]["cooldown_turns"] == 6 and abilities["explosao_vapor"]["dc"] == 17)
    check("explosao mantém raio/duracao", abilities["morte_explosiva"]["radius"] == 3 and abilities["morte_explosiva"]["duration"] == 3)

    print("Todos os testes do Molochus passaram.")


if __name__ == "__main__":
    asyncio.run(main())
