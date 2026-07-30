"""Testes de Mestre dos Mortos. Execute: python tools/test_mestre_dos_mortos.py"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def check(label, condition):
    assert condition, label
    print("OK:", label)


async def main():
    room = S.GameRoom("NECRO_TEST")
    room.map_w = room.map_h = 11
    room.tiles = [[S.FLOOR] * 11 for _ in range(11)]
    room.rooms = [{"id": "r1", "cx": 5, "cy": 5}]
    room.monsters = {}
    room.decorations = []
    room._rebuild_decor_index()
    room.chests = {}; room.ground_items = {}
    async def noop(*args, **kwargs): pass
    room.gm_say = noop

    necro_def = next(d for d in S.MONSTER_DEFS if d["type"] == "necromante")
    necro = S.make_monster(necro_def, room.rooms[0])
    necro["pos"] = [5, 5]
    room.monsters[necro["id"]] = necro
    check("necromante não começa com acompanhantes", len(room.monsters) == 1)

    invocados = await room._conjurar_mestre_dos_mortos(necro, "esqueleto_animal")
    check("invoca dois esqueletos", len(invocados) == 2)
    check("tipo escolhido é preservado", all(m["type"] == "esqueleto_animal" for m in invocados))
    check("servos nascem junto ao necromante", all(max(abs(m["pos"][0] - 5), abs(m["pos"][1] - 5)) <= 3 for m in invocados))
    check("uso posterior é bloqueado", not await room._conjurar_mestre_dos_mortos(necro, "esqueleto_humano"))


if __name__ == "__main__":
    asyncio.run(main())
