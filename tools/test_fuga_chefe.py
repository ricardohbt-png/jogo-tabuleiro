"""Fuga do chefe: o golpe que mataria o monstro com `fuga_chefe` o faz fugir.
Roda da raiz: python -X utf8 tools/test_fuga_chefe.py

REGRA
  • vence o combate (XP, objetivo cumprido) mas sem cadáver, sem loot e sem ouro;
  • grava o fato, narra o texto, foge uma vez só; sem o campo, morre como sempre.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

FUGA = {"fato": "gilo_fugiu", "texto": "O Gilo some numa nuvem de fumaça."}


def sala(fuga=None):
    d = copy.deepcopy(S.carregar_dungeon("amostra.json"))
    d["monsters"][0]["target"] = True
    if fuga is not None:
        d["monsters"][0]["fuga_chefe"] = fuga
    d["objectives"] = {"primary": {"type": "kill_target"}, "secondary": []}
    r = S.GameRoom("FUGA")
    r.msgs, r.falou = [], []

    async def noop(*a, **k): pass

    async def say(msg, *a, **k): r.falou.append(str(msg))

    async def bc(m, *a, **k): r.msgs.append(m)
    r.gm_say = say; r.broadcast = bc; r.send_to = noop; r.push_state = noop
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.load_authored_dungeon(d)
    r.phase = "playing"
    return r, next(iter(r.monsters.values()))


class FugaTests(unittest.IsolatedAsyncioTestCase):
    async def test_foge_sem_cadaver_nem_loot_e_cumpre_o_objetivo(self):
        r, m = sala(FUGA)
        xp0 = r.players["p1"]["xp"]
        baus0 = set(r.chests)
        m["hp"] = 0
        await r._monster_dies(m, "p1")
        self.assertNotIn(m["id"], r.corpses)
        self.assertEqual(set(r.chests), baus0, "sem baú de loot novo")
        self.assertIn("gilo_fugiu", r.fatos)
        self.assertIn(FUGA["texto"], r.falou)
        self.assertTrue(m.get("fugiu"))
        self.assertGreater(r.players["p1"]["xp"], xp0, "ganha o XP da vitória")
        self.assertTrue(r._objetivo_cumprido({"type": "kill_target"}))

    async def test_so_foge_uma_vez(self):
        r, m = sala(FUGA)
        m["hp"] = 0
        await r._monster_dies(m, "p1")
        n = len(r.falou)
        await r._monster_dies(m, "p1")
        self.assertEqual(len(r.falou), n)

    async def test_funil_de_dano_geral_tambem_foge(self):
        r, m = sala(FUGA)
        await r._aplicar_dano_alvo(m, m["hp"] + 5, "fire", killer_pid="p1")
        self.assertTrue(m.get("fugiu"))
        self.assertIn("gilo_fugiu", r.fatos)
        r2, m2 = sala(FUGA)
        await r2._dano_em_alvo(m2, m2["hp"] + 5, "poison", killer_pid="p1")
        self.assertTrue(m2.get("fugiu"))

    async def test_sem_o_campo_morre_normal(self):
        r, m = sala(None)
        m["hp"] = 0
        await r._monster_dies(m, "p1")
        self.assertFalse(m.get("fugiu"))
        self.assertNotIn("gilo_fugiu", r.fatos)

    def test_validador(self):
        d = copy.deepcopy(S.carregar_dungeon("amostra.json"))
        d["monsters"][0]["fuga_chefe"] = FUGA
        self.assertTrue(S.validar_dungeon(d)[0])
        for ruim in ({"fato": "", "texto": "x"}, {"fato": "a", "texto": ""}, {"fato": "a"}, "lixo",
                     {"fato": "a" * 101, "texto": "x"}, {"fato": "a", "texto": "x" * 301}):
            d["monsters"][0]["fuga_chefe"] = ruim
            self.assertFalse(S.validar_dungeon(d)[0], ruim)


if __name__ == "__main__":
    unittest.main()
