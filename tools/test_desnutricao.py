"""Testes da magia Desnutrição.
Roda da raiz: python tools/test_desnutricao.py
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


def add_players(room):
    caster = make_player("c1", "Lewis", "cleric", 0)
    target = make_player("p2", "Alvo", "warrior", 1)
    caster["pos"] = [1, 1]
    target["pos"] = [3, 1]
    room.players[caster["id"]] = caster
    room.players[target["id"]] = target
    return caster, target


def save_result(passed):
    async def _save(*_args, **_kwargs):
        return passed, 12, 3, 15
    return _save


async def main():
    print("\n[1] Catálogo e drenagem de Fome do jogador")
    room = setup_room()
    caster, target = add_players(room)
    room._save_mostrado = save_result(False)
    magia = server.GRIMORIO["desnutricao"]
    check("círculo = segundo", magia["circulo"] == "segundo")
    await room._executar_desnutricao(caster, magia, {"target_id": target["id"]})
    check("falha drena 20 de Fome", target["fome"] == 80)
    check("penalidade dura 2 turnos", target["desnutricao_mov_rodadas"] == 2)

    room._preparar_desnutricao_jogador_turno(target)
    check("1º turno recebe -1 Movimento", target["_desnutricao_mov_ativa"]
          and room._moves_base(target) == target["spd"] - 1)
    room._preparar_desnutricao_jogador_turno(target)
    check("2º turno recebe -1 Movimento", target["_desnutricao_mov_ativa"])
    room._preparar_desnutricao_jogador_turno(target)
    check("penalidade expira no 3º turno", not target["_desnutricao_mov_ativa"])

    print("\n[2] Sucesso no teste reduz o efeito")
    target["fome"] = 100
    target.pop("desnutricao_mov_rodadas", None)
    room._save_mostrado = save_result(True)
    await room._executar_desnutricao(caster, magia, {"target_id": target["id"]})
    check("sucesso drena 10 de Fome", target["fome"] == 90)
    check("sucesso não reduz Movimento", "desnutricao_mov_rodadas" not in target)

    print("\n[3] Imunidade de morto-vivo e construto")
    for label, flags in (("morto-vivo", {"undead": True}), ("construto", {"construct": True})):
        monster = {"id": f"m_{label}", "name": label, "type": label,
                   "hp": 10, "max_hp": 10, "pos": [3, 1], **flags}
        room.monsters[monster["id"]] = monster
        await room._executar_desnutricao(caster, magia, {"target_id": monster["id"]})
        check(f"{label} permanece sem efeitos", not any(
            key.startswith("desnutricao") for key in monster))

    print("\n[4] Monstro vivo recebe controle de duas rodadas")
    monster = copy.deepcopy(next(m for m in server.MONSTER_DEFS
                                if not m.get("undead") and not m.get("construct")
                                and m.get("attacks")))
    monster.update({"id": "m1", "pos": [3, 1], "hp": 20, "max_hp": 20,
                    "name": monster.get("name", "Monstro"), "ai_type": "agressivo"})
    room.monsters[monster["id"]] = monster
    room._save_mostrado = save_result(False)
    await room._executar_desnutricao(caster, magia, {"target_id": monster["id"]})
    check("monstro recebe 2 rodadas de restrição", monster["desnutricao_rodadas"] == 2)
    check("monstro recebe -1 Ataque", monster["desnutricao_ataque_penalidade"] == -1)
    check("monstro recebe -2 Dano", monster["desnutricao_dano_penalidade"] == -2)

    await room._status_monstro_turno(monster, [monster])
    check("1º turno fica restrito", monster["_desnutricao_restrito_turno"]
          and monster["desnutricao_rodadas"] == 1)
    await room._status_monstro_turno(monster, [monster])
    check("2º turno fica restrito", monster["_desnutricao_restrito_turno"]
          and monster["desnutricao_rodadas"] == 0)
    await room._status_monstro_turno(monster, [monster])
    check("efeito expira depois dos 2 turnos", not monster["_desnutricao_restrito_turno"]
          and "desnutricao_ataque_penalidade" not in monster)

    print(f"\n{'=' * 40}\nPASS: {PASS}  FAIL: {FAIL}\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
