"""Testes da Maldição do Corpo Pesado.
Roda da raiz: python tools/test_maldicao_corpo_pesado.py
"""
import asyncio
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
    caster["pos"] = [0, 0]
    target["pos"] = [3, 3]
    room.players[caster["id"]] = caster
    room.players[target["id"]] = target
    return caster, target


def save_result(passed):
    async def _save(*_args, **_kwargs):
        return passed, 12, 3, 15
    return _save


async def main():
    magia = server.GRIMORIO["maldicao_corpo_pesado"]
    print("\n[1] Catálogo e aplicação")
    room = setup_room()
    caster, target = add_players(room)
    caster["level"] = 2
    room._rolar_dado = lambda *_args, **_kwargs: 4
    room._save_mostrado = save_result(False)
    check("círculo = primeiro", magia["circulo"] == "primeiro")
    await room._executar_maldicao_corpo_pesado(caster, magia, {"target_id": target["id"]})
    check("falha aplica a maldição", target["maldicao_corpo_pesado_rodadas"] == 6)
    check("custos 1/2 viram 2/4", room._custo_fome_sede_efetivo(target, 1, 2) == (2, 4))
    fome_antes, sede_antes = target["fome"], target["sede"]
    room._pagar_fome_sede(target, 1, 2)
    check("débito efetivo reduz o dobro", target["fome"] == fome_antes - 2
          and target["sede"] == sede_antes - 4)

    print("\n[2] Duração exata")
    for _ in range(5):
        await room._processar_mods_magia_turno(target)
    check("continua ativa até a última rodada", target["maldicao_corpo_pesado_rodadas"] == 1
          and room._custo_fome_sede_efetivo(target, 1, 1) == (2, 2))
    await room._processar_mods_magia_turno(target)
    check("expira depois de 6 rodadas", "maldicao_corpo_pesado_rodadas" not in target
          and room._custo_fome_sede_efetivo(target, 1, 1) == (1, 1))

    print("\n[3] Vontade nega o efeito")
    room2 = setup_room()
    caster2, target2 = add_players(room2)
    room2._save_mostrado = save_result(True)
    await room2._executar_maldicao_corpo_pesado(caster2, magia, {"target_id": target2["id"]})
    check("sucesso não aplica a maldição", "maldicao_corpo_pesado_rodadas" not in target2)
    check("sucesso mantém custo normal", room2._custo_fome_sede_efetivo(target2, 1, 1) == (1, 1))

    print(f"\n{'=' * 40}\nPASS: {PASS}  FAIL: {FAIL}\n{'=' * 40}")
    raise SystemExit(1 if FAIL else 0)


asyncio.run(main())
