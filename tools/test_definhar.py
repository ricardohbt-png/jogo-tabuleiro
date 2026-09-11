"""Testes da magia Definhar.
Roda da raiz: python tools/test_definhar.py
"""
import asyncio
import copy
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup_room():
    room = GameRoom("TEST")

    async def noop(*_args, **_kwargs):
        pass

    room.gm_say = noop
    room.broadcast = noop
    room.push_state = noop
    room.send_to = noop
    room._broadcast_dado = noop
    room.round_num = 1
    room.phase = "playing"
    room.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    room._tem_linha_de_visao = lambda *_args, **_kwargs: True
    room._alcance_com_altura = lambda *_args, **_kwargs: True
    return room


def add_caster_and_player(room):
    caster = make_player("c1", "Lewis", "cleric", 0)
    target = make_player("p2", "Alvo", "warrior", 1)
    caster["pos"] = [0, 0]
    target["pos"] = [3, 3]
    room.players[caster["id"]] = caster
    room.players[target["id"]] = target
    return caster, target


def save_result(passed):
    async def _save(*_args, **_kwargs):
        return passed, 12, 3, 15
    return _save


def living_monster(monster_id, pos):
    monster = copy.deepcopy(next(m for m in server.MONSTER_DEFS
                                 if not m.get("undead") and not m.get("construct")
                                 and m.get("attacks")))
    monster.update({"id": monster_id, "pos": list(pos), "hp": 20,
                    "max_hp": 20, "name": monster.get("name", "Monstro"),
                    "ai_type": "agressivo"})
    return monster


async def main():
    magia = server.GRIMORIO["definhar"]

    print("\n[1] Catálogo e área")
    room = setup_room()
    caster, target = add_caster_and_player(room)
    room._save_mostrado = save_result(False)
    check("círculo = terceiro", magia["circulo"] == "terceiro")
    check("área inicial = 3x3", len(room._inverno_area_tiles(3, 3, 3)) == 9)
    caster["level"] = 3
    check("nível 3 amplia para 4x4", len(room._inverno_area_tiles(3, 3, 4)) == 16)
    caster["level"] = 1

    monster = living_monster("m1", [2, 2])
    room.monsters[monster["id"]] = monster
    await room._executar_definhar(caster, magia, {"tx": 3, "ty": 3})
    check("jogador atingido perde 20 Fome", target["fome"] == 80)
    check("jogador atingido perde 20 Sede", target["sede"] == 80)
    check("monstro vivo recebe 2 rodadas", monster["definhar_rodadas"] == 2)
    check("monstro recebe -2 Ataque", monster["definhar_ataque_penalidade"] == -2)
    check("monstro recebe -4 Dano", monster["definhar_dano_penalidade"] == -4)

    print("\n[2] Resistência reduz o efeito dos jogadores")
    room2 = setup_room()
    caster2, target2 = add_caster_and_player(room2)
    room2._save_mostrado = save_result(True)
    await room2._executar_definhar(caster2, magia, {"tx": 3, "ty": 3})
    check("sucesso perde 10 Fome", target2["fome"] == 90)
    check("sucesso perde 10 Sede", target2["sede"] == 90)
    check("sucesso não aplica restrição ao jogador", "definhar_rodadas" not in target2)

    print("\n[3] Imunidades")
    for label, flags in (("morto-vivo", {"undead": True}),
                         ("construto", {"construct": True})):
        immune = living_monster(f"m_{label}", [3, 4])
        immune.update(flags)
        room2.monsters[immune["id"]] = immune
        await room2._executar_definhar(caster2, magia, {"tx": 3, "ty": 3})
        check(f"{label} permanece sem efeitos", not any(
            key.startswith("definhar") for key in immune))

    print("\n[4] Duração exata do controle do monstro")
    room3 = setup_room()
    monster3 = living_monster("m3", [3, 3])
    room3.monsters[monster3["id"]] = monster3
    monster3["definhar_rodadas"] = 2
    monster3["definhar_ataque_penalidade"] = -2
    monster3["definhar_dano_penalidade"] = -4
    await room3._status_monstro_turno(monster3, [monster3])
    check("primeiro turno fica restrito", monster3["_definhar_restrito_turno"]
          and monster3["definhar_rodadas"] == 1
          and room3._privacao_monstro_penalidade(monster3, "ataque") == -2)
    await room3._status_monstro_turno(monster3, [monster3])
    check("segundo turno fica restrito", monster3["_definhar_restrito_turno"]
          and monster3["definhar_rodadas"] == 0
          and room3._privacao_monstro_penalidade(monster3, "dano") == -4)
    await room3._status_monstro_turno(monster3, [monster3])
    check("efeito expira depois de 2 turnos", not monster3["_definhar_restrito_turno"]
          and "definhar_ataque_penalidade" not in monster3)

    print(f"\n{'=' * 40}\nPASS: {PASS}  FAIL: {FAIL}\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
