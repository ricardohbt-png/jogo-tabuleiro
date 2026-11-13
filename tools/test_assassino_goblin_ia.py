"""Assassino Goblin: a IA tenta se esconder sem levantar erro e ataca quando falha.
Roda da raiz: python -X utf8 tools/test_assassino_goblin_ia.py
Regressão: `cooldowns` não definido em _ai_goblin_assassin (NameError engolido: o monstro não agia).
"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


class Dado:
    """Fixa os d20: `valor` no 1º (furtividade) e `depois` nos seguintes (ataque)."""
    def __init__(self, valor, depois=None):
        self.valor = valor
        self.depois = valor if depois is None else depois
        self.n = 0
    def _d20(self):
        self.n += 1
        return self.valor if self.n == 1 else self.depois
    def __enter__(self):
        self.orig = S.random.randint
        S.random.randint = lambda a, b: self._d20() if (a, b) == (1, 20) else self.orig(a, b)
    def __exit__(self, *exc):
        S.random.randint = self.orig


def cena():
    r = S.GameRoom("ASSASS")
    async def noop(*a, **k):
        pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 11):
        for x in range(1, 19):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 18, "h": 10, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    h = S.make_player("h", "Herói", "warrior", 0)
    h["pos"] = [5, 5]
    r.players = {"h": h}
    d = next(d for d in S.MONSTER_DEFS if d["type"] == "goblin_assassino")
    m = S.make_monster(d, {"id": 0, "cx": 6, "cy": 5})
    m["pos"] = [6, 5]
    r.monsters = {m["id"]: m}
    return r, h, m


class AssassinoIATests(unittest.TestCase):
    def test_esconder_falho_nao_levanta_erro_e_ataca(self):
        r, h, m = cena()
        hp = h["hp"]
        with Dado(1, 20):
            asyncio.run(r._ai_goblin_assassin(m, [{"kind": "player", "obj": h, "id": "h"}]))
        self.assertFalse(m.get("invisivel_sombras"))
        self.assertLess(h["hp"], hp)
        self.assertGreater(m["monster_ability_cooldowns"].get("bandido_esconder_se", 0), 0)

    def test_esconder_com_sucesso_fica_invisivel(self):
        r, h, m = cena()
        with Dado(20):
            asyncio.run(r._ai_goblin_assassin(m, [{"kind": "player", "obj": h, "id": "h"}]))
        self.assertTrue(m.get("invisivel_sombras"))


if __name__ == "__main__":
    unittest.main()
