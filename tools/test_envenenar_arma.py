"""Testes de Envenenar Arma. Execute: python tools/test_envenenar_arma.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


async def main():
    room = S.GameRoom("POISON_TEST")
    room.map_w = room.map_h = 9
    room.tiles = [[S.FLOOR] * 9 for _ in range(9)]
    room.rooms = [{"id": "r1", "cx": 4, "cy": 4}]
    room.monsters = {}; room.chests = {}; room.ground_items = {}
    async def noop(*args, **kwargs): pass
    room.gm_say = noop

    definition = next(d for d in S.MONSTER_DEFS if d["type"] == "kobold_lanceiro")
    kobold = S.make_monster(definition, room.rooms[0])
    check("habilidade é passiva", next(a for a in kobold["special_abilities"]
                                        if a["id"] == "envenenar_arma")["action_type"] == "passiva")
    doses = [i for i in kobold["equipment_consumables"] if i.get("effect") == "coat_poison"]
    check("kobold recebe venenos na bolsa", len(doses) >= 1)
    antes = len(kobold["equipment_consumables"])
    check("envenena arma com uma dose", await room._envenenar_arma_do_inventario(kobold))
    check("dose foi consumida", len(kobold["equipment_consumables"]) == antes - 1)
    check("próximo ataque fica envenenado", kobold["veneno_arma_ativo"] is True
          and kobold["veneno_arma_id"] in S.VENENOS)
    check("não gasta segunda dose enquanto arma já está envenenada",
          not await room._envenenar_arma_do_inventario(kobold))


if __name__ == "__main__":
    asyncio.run(main())
