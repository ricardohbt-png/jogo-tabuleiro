"""Objetivo concede renome e marcador (fato); validar_dungeon recusa tipos errados.
Roda da raiz: python -X utf8 tools/test_objetivo_renome.py"""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

BASE = {"schema_version": 1, "grid": {"w": 8, "h": 8}, "tiles": [[1] * 8 for _ in range(8)],
        "entrance": {"x": 1, "y": 1}, "rooms": [{"id": "r1", "role": "entrance"}]}


def sala():
    r = S.GameRoom("RENOME")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]

    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.send_to = noop
    return r


def conceder(r, obj, primario=True):
    asyncio.run(r._conceder_objetivo_reward(obj, primario, []))


def com_obj(**obj):
    d = dict(BASE)
    d["objectives"] = {"primary": dict({"type": "kill_all"}, **obj), "secondary": []}
    return d


class RenomeTests(unittest.TestCase):
    def test_concede_renome_e_fato(self):
        r = sala(); r.renome = 3
        conceder(r, {"type": "kill_all", "renome": 2, "fato": "marcador_x"})
        self.assertEqual(r.renome, 5)
        self.assertIn("marcador_x", r.fatos)

    def test_renome_negativo_tem_piso_zero(self):
        r = sala(); r.renome = 2
        conceder(r, {"type": "kill_all", "renome": -5})
        self.assertEqual(r.renome, 0)

    def test_sem_campos_nao_muda_nada(self):
        r = sala(); r.renome = 4
        conceder(r, {"type": "kill_all"})
        self.assertEqual(r.renome, 4)
        self.assertEqual(set(r.fatos), set())

    def test_validar_dungeon_aceita_e_recusa(self):
        self.assertTrue(S.validar_dungeon(com_obj(renome=3, fato="a"))[0])
        self.assertFalse(S.validar_dungeon(com_obj(renome="muito"))[0])
        self.assertFalse(S.validar_dungeon(com_obj(renome=1.5))[0])
        self.assertFalse(S.validar_dungeon(com_obj(fato=["a"]))[0])
        self.assertFalse(S.validar_dungeon(com_obj(renome=10 ** 6))[0])

    def test_validar_alternativo_e_se_falhar(self):
        d = com_obj(se_falhar={"renome": -5, "fato": "m"})
        d["objectives"]["alternativo"] = {"type": "kill_target", "renome": 1}
        self.assertTrue(S.validar_dungeon(d)[0])
        d["objectives"]["alternativo"]["renome"] = "x"
        self.assertFalse(S.validar_dungeon(d)[0])
        d2 = com_obj(se_falhar={"renome": "x"})
        self.assertFalse(S.validar_dungeon(d2)[0])


if __name__ == "__main__":
    unittest.main()
