"""Regressoes das variantes e das habilidades do Garaloux."""
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
    r = S.GameRoom("GARALOUX_TEST")
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


def hero(r, pid, pos, strength=-50, hp=500):
    p = S.make_player(pid, pid, "warrior", 0)
    p.update({"pos": list(pos), "alive": True, "connected": True,
              "hp": hp, "max_hp": hp, "ac": 1, "ac_base": 1,
              "fort": -50, "ref_": -50, "will": -50, "str_": strength})
    r.players[pid] = p
    return p


async def main():
    print("[1] Fichas e movimento")
    expected = {
        "garaloux_jovem": (50, 18, 7, 14),
        "garaloux_adulto": (82, 21, 7, 16),
        "garaloux_alfa": (145, 25, 7, 18),
    }
    for typ, values in expected.items():
        r = room()
        m = creature(r, typ, typ)
        salto = next(a for a in m["special_abilities"] if a["id"] == "salto_selvagem")
        check(f"{typ}: PV/CA/movimento", (m["max_hp"], m["ac"], m["movement"]) == values[:3])
        check(f"{typ}: CD de Reflexos", salto["reflex_dc"] == values[3])
        check(f"{typ}: imagem Garaloux", m["image"] == "garaloux")

    print("[2] Salto, escape por Forca e colisao")
    old_roll = S.roll_dice
    S.roll_dice = lambda _expr: 1
    try:
        r = room()
        m = creature(r, "garaloux_adulto", "adulto")
        p = hero(r, "h1", [5, 6])
        m["_garaloux_move_count"] = 3
        await r._execute_one_monster_attack(m, m["attacks"][2], {"kind": "player", "obj": p})
        check("Salto imobiliza apos falha em Reflexos", p.get("preso") is True)
        check("escape usa Forca", next(a for a in m["special_abilities"] if a["id"] == "salto_selvagem")["escape_saves"] == ["forca"])
        p["str_"] = 50
        await r._processar_escape_agarrar(p)
        check("Forca liberta o alvo", not p.get("preso"))

        r1 = room()
        m1 = creature(r1, "garaloux_adulto", "g")
        p1 = hero(r1, "h", [5, 6])
        m1["_garaloux_move_count"] = 3
        await r1._execute_one_monster_attack(m1, m1["attacks"][2], {"kind": "player", "obj": p1})
        r2 = room()
        m2 = creature(r2, "garaloux_adulto", "g")
        p2 = hero(r2, "h", [5, 6])
        r2.tiles[7][5] = S.WALL
        m2["_garaloux_move_count"] = 3
        await r2._execute_one_monster_attack(m2, m2["attacks"][2], {"kind": "player", "obj": p2})
        check("parede causa +1d6 de colisao", p2["hp"] < p1["hp"])
    finally:
        S.roll_dice = old_roll

    print("[3] Dilacerar e Frenesi")
    r = room()
    m = creature(r, "garaloux_adulto", "adulto")
    p = hero(r, "h1", [5, 6])
    await r._monster_execute_attacks(m, {"kind": "player", "obj": p})
    check("duas Garras aplicam Dilacerar uma vez", any("Dilacera" in text for text in r._falas))
    m["hp"] = m["max_hp"] // 2
    check("Frenesi da +2 no ataque e dano", r._furia_ataque_bonus(m) == 2 and r._furia_bonus(m) == 2)

    print("[4] Predador Supremo sem cadeia")
    r = room()
    m = creature(r, "garaloux_alfa", "alfa")
    p1 = hero(r, "h1", [5, 6], hp=1)
    p2 = hero(r, "h2", [4, 5])
    await r._execute_one_monster_attack(m, m["attacks"][0], {"kind": "player", "obj": p1})
    check("Mordida adicional apos eliminar", p2["hp"] < p2["max_hp"])

    print("[5] Editor preserva as novas configuracoes")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "garaloux_adulto"))
    raw.update({"type": "garaloux_editor_teste", "name": "Garaloux Editor Teste",
                "monster_abilities": [
                    {"id": "salto_selvagem", "reflex_dc": 17, "escape_dc": 18},
                    {"id": "dilacerar", "damage_dice": 3, "damage_faces": 6},
                    {"id": "investida_brutal", "damage_dice": 4, "damage_faces": 6},
                    {"id": "furia_garaloux", "threshold": 0.5},
                    {"id": "predador_supremo"},
                ]})
    ok, normalized = S._validate_custom_monster(raw)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("ficha customizada aceita", ok)
    check("CDs do Salto preservadas", abilities["salto_selvagem"]["reflex_dc"] == 17 and abilities["salto_selvagem"]["escape_dc"] == 18)
    check("dados das habilidades preservados", abilities["dilacerar"]["damage"] == "3d6" and abilities["investida_brutal"]["damage"] == "4d6")

    print("Todos os testes do Garaloux passaram.")


if __name__ == "__main__":
    asyncio.run(main())
