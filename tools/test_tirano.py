"""Regressoes dos Tiranos da Mata e Ancestral."""
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
    r = S.GameRoom("TIRANO_TEST")
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


def creature(r, monster_type, mid, pos=(5, 5)):
    definition = next(m for m in S.MONSTER_DEFS if m["type"] == monster_type)
    m = S.make_monster(definition, r.rooms[0])
    m["id"] = mid
    m["pos"] = list(pos)
    r.monsters[mid] = m
    return m


def hero(r, pid, pos=(5, 6), hp=500):
    p = S.make_player(pid, pid, "warrior", 0)
    p.update({"pos": list(pos), "alive": True, "connected": True,
              "hp": hp, "max_hp": hp, "ac": 1, "ac_base": 1,
              "fort": -50, "ref_": 20, "will": -50, "str_": 20})
    r.players[pid] = p
    return p


async def main():
    print("[1] Fichas e RD")
    r = room()
    mata = creature(r, "tirano_da_mata", "mata")
    ancestral = creature(r, "tirano_ancestral", "ancestral", (8, 8))
    check("Mata tem PV/CA/movimento", (mata["max_hp"], mata["ac"], mata["movement"]) == (120, 22, 6))
    check("Ancestral preserva movimento 7", ancestral["movement"] == 7)
    check("assets compartilham tirano_da_mata", mata["image"] == ancestral["image"] == "tirano_da_mata")
    check("Mata ocupa 2x2 como criatura grande",
          mata["size"] == [2, 2] and ancestral["size"] == [2, 3]
          and not mata.get("oriented") and ancestral.get("oriented"))
    mata["facing"] = [-1, 0]
    check("footprint fixo 2x2",
           set(map(tuple, r._monster_tiles(mata))) ==
           {(5, 5), (5, 6), (6, 5), (6, 6)})
    check("ataque comum usa as duas casas de cada face",
          set(map(tuple, r._monster_orthogonal_attack_tiles(mata))) ==
          {(5,4),(6,4),(5,7),(6,7),(4,5),(4,6),(7,5),(7,6)})
    check("RD arma comum", r._apply_damage_types(10, [S.DMG_PHYSICAL], mata, {"id": "espada"}) == 6)
    check("RD nao bloqueia dano especial", r._apply_damage_types(10, [S.DMG_PHYSICAL], mata) == 10)
    check("veneno dobrado", r._apply_damage_types(10, [S.DMG_POISON], mata) == 20)

    print("[2] Mandibulas e Sacudida")
    old_roll = S.roll_dice
    S.roll_dice = lambda _expr: 1
    try:
        r = room(); m = creature(r, "tirano_da_mata", "m"); p = hero(r, "p")
        p.update({"preso": True, "preso_por": m["id"]})
        hp_before = p["hp"]
        await r._tirano_inicio_turno(m)
        check("mordida automatica no inicio", p["hp"] < hp_before)
        await r._tirano_sacudida(m)
        check("sacudida solta o alvo", not p.get("preso") and p.get("preso_por") is None)
        check("sacudida usa recarga 5", m["ability_cooldowns"].get("sacudida_brutal") == 5)
    finally:
        S.roll_dice = old_roll

    print("[3] Engolir, dano interno e escape")
    old_roll = S.roll_dice
    S.roll_dice = lambda _expr: 1
    try:
        r = room(); m = creature(r, "tirano_ancestral", "a"); p = hero(r, "p")
        popup_messages = []
        async def capture_popup(pid, msg):
            popup_messages.append((pid, msg))
        r.send_to = capture_popup
        p.update({"preso": True, "preso_por": m["id"]})
        await r._tirano_engolir(m)
        check("engolir marca o heroi", p.get("engolido") and p.get("engolido_por") == m["id"])
        check("engolir envia popup com imagem e efeitos",
              any(pid == "p" and msg.get("type") == "trap_result"
                  and msg.get("tipo_id") == "engolido"
                  and msg.get("acid_damage") == "3d6"
                  and msg.get("escape_dc") == 22
                  for pid, msg in popup_messages))
        hp_before = p["hp"]
        await r._tirano_inicio_turno(m)
        check("acido tica dentro do estomago", p["hp"] < hp_before)
        m_hp = m["hp"]
        await r._tirano_dano_interno(p, m, 20)
        check("dano interno nao reduz limiar externo", m["hp"] < m_hp and not p.get("engolido"))
    finally:
        S.roll_dice = old_roll

    print("[4] Editor preserva as configuracoes")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "tirano_ancestral"))
    raw.update({"type": "tirano_editor_teste", "monster_abilities": [
        {"id": "mandibulas_colossais", "dc": 24, "automatic_damage": "4d10+12"},
        {"id": "sacudida_brutal", "damage_dice": 7, "damage_faces": 6, "throw_distance": 4},
        {"id": "engolir", "dc": 23, "acid_dice": 4, "acid_faces": 6, "stomach_hp": 25},
        {"id": "abrir_caminho"}, {"id": "passo_devastador", "damage_dice": 4, "damage_faces": 8},
    ]})
    ok, normalized = S._validate_custom_monster(raw)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("ficha customizada aceita", ok)
    check("mandibulas preservam dano e CD", abilities["mandibulas_colossais"]["dc"] == 24 and abilities["mandibulas_colossais"]["automatic_damage"] == "4d10+12")
    check("engolir preserva estomago", abilities["engolir"]["acid_damage"] == "4d6" and abilities["engolir"]["stomach_hp"] == 25)
    check("passo preserva dano", abilities["passo_devastador"]["damage"] == "4d8")
    print("Todos os testes dos Tiranos passaram.")


if __name__ == "__main__":
    asyncio.run(main())
