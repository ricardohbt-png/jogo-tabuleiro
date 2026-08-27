"""Regressões das três variantes do Lacralion e das habilidades configuráveis."""
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
    r = S.GameRoom("LACRALION_TEST")
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


def hero(r, pid, pos):
    p = S.make_player(pid, pid, "warrior", 0)
    p.update({"pos": list(pos), "alive": True, "connected": True,
              "hp": 500, "max_hp": 500, "ac": 1, "ac_base": 1,
              "fort": -50, "ref_": -50, "will": -50})
    r.players[pid] = p
    return p


async def main():
    print("[1] Fichas independentes")
    expected = {
        "lacralion_filhote": (28, 16, 6),
        "lacralion_adulto": (58, 19, 5),
        "lacralion_anciao": (102, 23, 6),
    }
    for typ, values in expected.items():
        r = room()
        m = creature(r, typ, typ)
        check(f"{typ}: PV/CA/movimento", (m["max_hp"], m["ac"], m["movement"]) == values)
        check(f"{typ}: usa o GLB lacralion", m["image"] == "lacralion")

    print("[2] Veneno do filhote")
    r = room()
    m = creature(r, "lacralion_filhote", "filhote")
    p = hero(r, "h1", [5, 6])
    await r._execute_one_monster_attack(m, m["attacks"][2], {"kind": "player", "obj": p})
    check("falha no veneno causa dano", p["hp"] < 500)
    check("falha no veneno aplica Sangramento", p.get("sangramento_nivel") == 1
          and p.get("sangramento_rodadas", 0) >= 1)
    check("veneno não aplica mais Lentidão", not p.get("lento") and not p.get("lento_rodadas"))

    print("[3] Agarrão, Ferrão e limite do ancião")
    r = room()
    m = creature(r, "lacralion_adulto", "adulto")
    p = hero(r, "h1", [5, 6])
    await r._execute_one_monster_attack(m, m["attacks"][0], {"kind": "player", "obj": p})
    check("Pinça imobiliza automaticamente", p.get("preso") is True and p.get("preso_por") == "adulto")
    check("Ferrão recebe +2 contra o preso", r._bonus_ferrao_lacralion(m, p, m["attacks"][2]) == 2)

    r = room()
    m = creature(r, "lacralion_anciao", "anciao")
    p1 = hero(r, "h1", [5, 6])
    p2 = hero(r, "h2", [4, 5])
    p3 = hero(r, "h3", [6, 5])
    for target in (p1, p2, p3):
        await r._execute_one_monster_attack(m, m["attacks"][0], {"kind": "player", "obj": target})
    check("Ancião mantém dois alvos imobilizados", p1.get("preso") and p2.get("preso"))
    check("terceiro alvo não ultrapassa o limite", not p3.get("preso"))

    print("[4] Carapaça somente após acerto corpo a corpo")
    r = room()
    m = creature(r, "lacralion_adulto", "adulto")
    p = hero(r, "h1", [5, 6])
    hp_before = p["hp"]
    await r._carapaca_espinhosa_retalia(m, p)
    check("Carapaça causa dano ao atacante", p["hp"] < hp_before)

    print("[5] Habilidades aparecem no fluxo do editor")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "lacralion_adulto"))
    raw.update({
        "type": "lacralion_editor_teste",
        "name": "Lacralion Editor Teste",
        "monster_abilities": [
            {"id": "veneno_lacralion", "uses_per_day": 1, "cooldown_turns": 0,
             "attack_index": 2, "damage_dice": 1, "damage_faces": 8,
             "poison_dc": 18},
            {"id": "agarrar_lacralion", "uses_per_day": 1, "cooldown_turns": 0,
             "attack_index": 0, "dc": 17, "max_targets": 2},
            {"id": "dano_retaliacao", "uses_per_day": 1, "cooldown_turns": 0,
             "damage_dice": 2, "damage_faces": 6, "damage_type": "lightning"},
        ],
    })
    ok, normalized = S._validate_custom_monster(raw)
    check("configuração personalizada é aceita", ok)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("veneno preserva 1d8/CD18", abilities["veneno_lacralion"]["extra_damage"] == "1d8"
          and abilities["veneno_lacralion"]["poison_dc"] == 18)
    check("agarrão preserva CD17/2 alvos", abilities["agarrar_lacralion"]["dc"] == 17
          and abilities["agarrar_lacralion"]["max_targets"] == 2)
    check("retaliação preserva 2d6/eletricidade", abilities["dano_retaliacao"]["damage"] == "2d6"
          and abilities["dano_retaliacao"]["damage_types"] == ["lightning"])

    print("Todos os testes do Lacralion passaram.")


if __name__ == "__main__":
    asyncio.run(main())
