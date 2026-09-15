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
    rex = creature(r, "tiranossauro_rex", "rex", (2, 2))
    ancestral = creature(r, "tirano_ancestral", "ancestral", (8, 8))
    check("Mata tem PV/CA/movimento", (mata["max_hp"], mata["ac"], mata["movement"]) == (120, 22, 6))
    check("T-Rex tem PV 156 e RD 4 só contra armas comuns", rex["max_hp"] == 156
          and rex["resistances"] == [{"type": "physical", "reduction": 4, "common_weapon_only": True}])
    check("T-Rex: arma comum sofre a RD", r._apply_damage_types(10, [S.DMG_PHYSICAL], rex, {"id": "espada"}) == 6)
    check("T-Rex: arma mágica atravessa a RD", r._apply_damage_types(10, [S.DMG_PHYSICAL], rex, {"id": "espada", "magical": True}) == 10)
    check("T-Rex: dano sem arma (habilidade/monstro) atravessa a RD", r._apply_damage_types(10, [S.DMG_PHYSICAL], rex) == 10)
    rex_ids = [a["id"] for a in rex["special_abilities"]]
    check("T-Rex não tem mais a ação Sacudida Brutal", "sacudida_brutal" not in rex_ids)
    sj = next((a for a in rex["special_abilities"] if a["id"] == "sacudida_jurassica"), None)
    check("T-Rex tem a passiva Sacudida Jurássica", sj is not None and sj["action_type"] == "passiva"
          and sj["bite_damage"] == "4d12+7" and sj["extra_damage"] == "2d6"
          and sj["wall_damage"] == "2d6" and sj["throw_distance"] == 4)
    check("Mata continua com a Sacudida Brutal em ação", any(a["id"] == "sacudida_brutal" for a in mata["special_abilities"]))
    check("Ancestral preserva movimento 7", ancestral["movement"] == 7)
    check("assets compartilham tirano_da_mata", mata["image"] == ancestral["image"] == "tirano_da_mata")
    check("Mata ocupa 2x2 como criatura grande",
          mata["size"] == [2, 2] and ancestral["size"] == [2, 2]
          and not mata.get("oriented") and not ancestral.get("oriented"))
    mata["facing"] = [-1, 0]
    check("footprint fixo 2x2",
           set(map(tuple, r._monster_tiles(mata))) ==
           {(5, 5), (5, 6), (6, 5), (6, 6)})
    check("ataque comum usa as duas casas de cada face",
           set(map(tuple, r._monster_orthogonal_attack_tiles(mata))) ==
           {(5,4),(6,4),(5,7),(6,7),(4,5),(4,6),(7,5),(7,6)})
    ancestral["facing"] = [1, 0]
    check("Ancestral tambem usa as duas casas de cada face",
          set(map(tuple, r._monster_orthogonal_attack_tiles(ancestral))) ==
          {(8,7),(9,7),(8,10),(9,10),(7,8),(7,9),(10,8),(10,9)})
    ancestral_attack_tiles = r._monster_orthogonal_attack_tiles(ancestral)
    check("Ancestral reconhece alcance corpo a corpo nas quatro faces",
          all(r._monster_attack_in_range(ancestral, tile, ancestral["attacks"][0])
              for tile in ancestral_attack_tiles))
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

        # -- Sacudida Jurassica (T-Rex): passiva de inicio de turno ----------
        def rex_cenario(hero_pos=(7, 5), hp=500):
            r = room(); m = creature(r, "tiranossauro_rex", "rex", (5, 5))
            m["facing"] = [1, 0]
            p = hero(r, "p", hero_pos, hp=hp)
            p.update({"preso": True, "preso_por": m["id"]})
            rolls = []
            S.roll_dice = lambda expr: (rolls.append(expr) or 1)
            return r, m, p, rolls

        r, m, p, rolls = rex_cenario()
        hp_before = p["hp"]
        await r._tirano_inicio_turno(m)
        check("[2b] sacudida rola mordida+2d6 uma única vez (sem 4d12+7 avulso das Mandíbulas)",
              rolls == ["4d12+7+2d6"])
        check("[2b] sacudida debita o dano", p["hp"] == hp_before - 1)
        check("[2b] sacudida solta a presa", not p.get("preso") and p.get("preso_por") is None)
        check("[2b] presa arremessada 4 casas para longe do footprint", p["pos"] == [11, 5])
        check("[2b] narra a sacudida", any("sacode" in f for f in r._falas))

        r, m, p, rolls = rex_cenario(hero_pos=(6, 7))
        await r._tirano_inicio_turno(m)
        check("[2b] direção vem da casa mais próxima do 2x2 (reta, não diagonal)", p["pos"] == [6, 11])

        r, m, p, rolls = rex_cenario()
        r.tiles[5][9] = S.WALL
        hp_before = p["hp"]
        await r._tirano_inicio_turno(m)
        check("[2c] parede: para na casa anterior e rola +2d6", p["pos"] == [8, 5] and rolls == ["4d12+7+2d6", "2d6"])
        check("[2c] parede: dano extra debitado", p["hp"] == hp_before - 2)

        r, m, p, rolls = rex_cenario()
        r.tiles[5][9] = S.DOOR
        await r._tirano_inicio_turno(m)
        check("[2c] porta fechada conta como obstáculo sólido", p["pos"] == [8, 5] and rolls == ["4d12+7+2d6", "2d6"])

        r, m, p, rolls = rex_cenario()
        r._decor_block_tiles = {(9, 5)}
        await r._tirano_inicio_turno(m)
        check("[2c] decoração sólida conta como obstáculo sólido", p["pos"] == [8, 5] and rolls == ["4d12+7+2d6", "2d6"])

        r, m, p, rolls = rex_cenario(hero_pos=(7, 5))
        m["pos"] = [8, 5]; p["pos"] = [10, 5]
        await r._tirano_inicio_turno(m)
        check("[2c] borda do mapa conta como obstáculo sólido", p["pos"] == [11, 5] and rolls == ["4d12+7+2d6", "2d6"])

        r, m, p, rolls = rex_cenario()
        outro = hero(r, "q", (9, 5))
        await r._tirano_inicio_turno(m)
        check("[2c] outra criatura interrompe o voo SEM +2d6", p["pos"] == [8, 5] and rolls == ["4d12+7+2d6"]
              and outro["pos"] == [9, 5])

        r, m, p, rolls = rex_cenario()
        p["preso"] = False; p.pop("preso_por", None)
        hp_before = p["hp"]
        await r._tirano_inicio_turno(m)
        check("[2e] presa que já escapou não é sacudida", rolls == [] and p["hp"] == hp_before and p["pos"] == [7, 5])

        r, m, p, rolls = rex_cenario()
        ataques = []
        async def fake_attack(mm, atk, alvo_obj):
            ataques.append((atk["name"], alvo_obj["obj"]["id"]))
        r._execute_one_monster_attack = fake_attack
        hero(r, "v2", (4, 4))
        targets = [{"kind": "player", "obj": pl} for pl in r.players.values()]
        await r._tirano_inicio_turno(m)
        await r._ai_tirano(m, targets)
        check("[2d] depois de sacudir o T-Rex ainda ataca no mesmo turno", len(ataques) >= 1)

        # Prologo compartilhado (IA e Manual do mestre) dispara a sacudida.
        r, m, p, rolls = rex_cenario()
        r.master_pid = "mestre"; m["control_mode"] = "manual"; m["alertado"] = True
        pode_agir = await r._upkeep_inicio_turno_monstro(m, list(r.monsters.values()))
        check("[2g] prólogo do Manual dispara a sacudida", pode_agir and rolls[:1] == ["4d12+7+2d6"]
              and not p.get("preso") and p["pos"] == [11, 5])

        # Tirano da Mata inalterado: dano automatico + Sacudida Brutal com recarga.
        r = room(); m = creature(r, "tirano_da_mata", "m"); p = hero(r, "p", (7, 5))
        p.update({"preso": True, "preso_por": m["id"]})
        rolls = []
        S.roll_dice = lambda expr: (rolls.append(expr) or 1)
        await r._tirano_inicio_turno(m)
        check("[2f] Mata: Mandíbulas continuam com dano automático", rolls == ["2d10+10"] and p.get("preso"))
        await r._tirano_sacudida(m)
        check("[2f] Mata: Sacudida Brutal rola 4d6, solta e arremessa 2", rolls[1] == "4d6"
              and not p.get("preso") and p["pos"] == [9, 5])
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
                  and msg.get("monstro") == "Tirano Ancestral"
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
        {"id": "sacudida_brutal", "damage_dice": 7, "damage_faces": 6, "bite_damage": "5d10+8", "extra_damage": "3d6", "wall_damage": "4d6", "throw_distance": 4},
        {"id": "engolir", "dc": 23, "acid_dice": 4, "acid_faces": 6, "stomach_hp": 25},
        {"id": "abrir_caminho"}, {"id": "passo_devastador", "damage_dice": 4, "damage_faces": 8},
    ]})
    ok, normalized = S._validate_custom_monster(raw)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("ficha customizada aceita", ok)
    check("mandibulas preservam dano e CD", abilities["mandibulas_colossais"]["dc"] == 24 and abilities["mandibulas_colossais"]["automatic_damage"] == "4d10+12")
    check("engolir preserva estomago", abilities["engolir"]["acid_damage"] == "4d6" and abilities["engolir"]["stomach_hp"] == 25)
    check("passo preserva dano", abilities["passo_devastador"]["damage"] == "4d8")
    check("sacudida customizada preserva colisão", abilities["sacudida_brutal"]["bite_damage"] == "5d10+8" and abilities["sacudida_brutal"]["extra_damage"] == "3d6" and abilities["sacudida_brutal"]["wall_damage"] == "4d6")
    raw = copy.deepcopy(next(m for m in S.MONSTER_DEFS if m["type"] == "tiranossauro_rex"))
    raw.update({"type": "rex_editor_teste", "monster_abilities": [
        {"id": "mandibulas_colossais", "dc": 19},
        {"id": "sacudida_jurassica", "bite_damage": "5d12+8", "extra_damage": "3d6", "wall_damage": "4d6", "throw_distance": 5},
    ]})
    ok, normalized = S._validate_custom_monster(raw)
    abilities = {a["id"]: a for a in normalized["special_abilities"]}
    check("ficha custom do T-Rex aceita", ok)
    sj = abilities.get("sacudida_jurassica")
    check("sacudida jurássica custom preserva campos e fica passiva", sj is not None
          and sj["action_type"] == "passiva" and sj["bite_damage"] == "5d12+8"
          and sj["extra_damage"] == "3d6" and sj["wall_damage"] == "4d6" and sj["throw_distance"] == 5)
    check("resistência common_weapon_only sobrevive ao editor",
          any(x.get("type") == "physical" and x.get("reduction") == 4 and x.get("common_weapon_only")
              for x in normalized["resistances"]))
    print("Todos os testes dos Tiranos passaram.")


if __name__ == "__main__":
    asyncio.run(main())
