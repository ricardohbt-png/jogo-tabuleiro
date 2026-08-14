"""Regressoes do Gigante Runico."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def room():
    r = S.GameRoom("RUNICO_TEST")
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 12, "h": 12,
                "cx": 6, "cy": 6, "locked": False}]
    r.monsters = {}
    r.players = {}

    async def noop(*_args, **_kwargs):
        return None

    r.broadcast = noop
    r.push_state = noop
    r.send_to = noop
    r.gm_say = noop
    return r


def make_creature(r):
    definition = next(m for m in S.MONSTER_DEFS if m["type"] == "gigante_runico")
    monster = S.make_monster(definition, r.rooms[0])
    monster["id"] = "runico"
    monster["pos"] = [5, 5]
    r.monsters[monster["id"]] = monster
    return monster


async def main():
    r = room()
    m = make_creature(r)
    p = S.make_player("p", "P", "warrior", 0)
    p.update({"pos": [5, 7], "alive": True, "connected": True,
              "hp": 100, "max_hp": 100, "ac": 10, "fort": 0,
              "ref_": 0, "will": 0})
    r.players[p["id"]] = p

    assert (m["max_hp"], m["ac"], m["movement"], m["size"], m["percepcao"]) == (70, 19, 6, [2, 2], 13)
    assert r._ciclope_attack_in_range(m, p, m["attacks"][0])

    old_roll = S.roll_dice
    S.roll_dice = lambda _expr: 3
    try:
        m["hp"] = 50
        assert await r._runico_ativar_regeneracao(m)
        await r._processar_regeneracao_runica_inicio(m)
        assert m["hp"] == 52
        m["_runico_bonus_used"] = False
        assert await r._runico_ativar_passo_fantasma(m)
        assert m["_water_moves_left"] >= 2
        m["_runico_bonus_used"] = False
        assert await r._runico_ativar_provocacao(m, {"kind": "player", "obj": p})
        assert p["runico_provocado_por"] == m["id"]
    finally:
        S.roll_dice = old_roll

    print("Todos os testes do Gigante Runico passaram.")


if __name__ == "__main__":
    asyncio.run(main())
