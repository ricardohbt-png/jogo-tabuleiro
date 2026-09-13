"""Testes do Vínculo Maldito da Dor. Rode da raiz: python tools/test_vinculo_maldito_da_dor.py"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
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


def setup_room(link_count):
    room = GameRoom("TEST")
    room.round_num = 1
    room.gm_say = _noop
    room.broadcast = _noop
    caster = make_player("caster", "Conjurador", "mage", 0)
    caster["pos"] = [0, 0]
    room.players[caster["id"]] = caster
    for index in range(link_count):
        monster = {
            "id": f"monster-{index}", "name": f"Inimigo {index}",
            "pos": [index + 1, 0], "hp": 100, "max_hp": 100,
            "alive": True, "ac": 10,
        }
        room.monsters[monster["id"]] = monster
        caster["vinculos_malditos_dor"].append({
            "target_id": monster["id"], "expira_em": 10, "duracao": 9,
        })
    return room, caster


async def _noop(*_args, **_kwargs):
    return None


async def main():
    print("\n[1] Catálogo")
    magia = S.GRIMORIO["vinculo_maldito_da_dor"]
    check("está implementada", "vinculo_maldito_da_dor" in S.GRIMORIO_IMPLEMENTADAS)
    check("é de 2º círculo", magia["circulo"] == "segundo")
    check("aceita mago e clérigo", set(magia["classe"]) == {"mage", "cleric"})
    check("save de Vontade", magia["save"] == "vontade")
    check("duração 1d4 + nível", magia["duracao"] == "1d4" and magia["duracao_por_nivel"] == 1)
    check("máximo de 4 alvos", magia["max_alvos"] == 4)
    check("alcance por linha de visão", magia["alcance_los"] is True)

    print("\n[2] Distribuição do dano")
    for links, expected_caster, expected_enemy in (
        (1, 75, 25), (2, 50, 25), (3, 25, 25), (4, 0, 25),
    ):
        room, caster = setup_room(links)
        caster["hp"] = 100
        await room._aplicar_dano_alvo(caster, 100, S.DMG_PHYSICAL, "monster-0")
        enemies = [room.monsters[f"monster-{i}"]["hp"] for i in range(links)]
        check(f"{links} vínculo(s): conjurador recebe {expected_caster}", caster["hp"] == 100 - expected_caster)
        check(f"{links} vínculo(s): cada inimigo recebe {expected_enemy}", enemies == [100 - expected_enemy] * links)

    print("\n[3] Arredondamento e penalidade")
    room, caster = setup_room(1)
    caster["hp"] = 100
    await room._aplicar_dano_alvo(caster, 3, S.DMG_PHYSICAL, "monster-0")
    check("parcela mínima de 1", room.monsters["monster-0"]["hp"] == 99)
    check("dano do conjurador arredonda para baixo", caster["hp"] == 98)
    monstro = room.monsters["monster-0"]
    check("marca o próximo ataque com -1", room._consumir_penalidade_vinculo_dor(monstro) == -1)
    check("penalidade não acumula após consumir", room._consumir_penalidade_vinculo_dor(monstro) == 0)

    print(f"\nResultado: {PASS} passaram, {FAIL} falharam")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
