"""Lista de reféns por mapa, com compatibilidade com o refém único."""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as S
from test_decor_roundtrip import _defn_base
from test_elara_leonel_mansao import sala


def mapa(**extra):
    d = _defn_base()
    d.pop("prisoner", None)
    d.update(extra)
    return d


class VariosRefensTests(unittest.TestCase):
    def test_mapa_antigo_vira_lista_de_um(self):
        r = sala(mapa(prisoner={"pos": [3, 3], "room_id": None}))
        self.assertEqual([p["id"] for p in r.prisoners], ["refem_0"])
        self.assertIs(r.prisoner, r.prisoners[0])
        self.assertEqual(r.prisoner["nome"], "Prisioneiro")
        self.assertEqual(r.prisoner["modo"], "guiar")
        self.assertFalse(r.prisoner["salvo"])

    def test_varios_com_ids_e_nomes(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3], "nome": "Tico"}, {"pos": [4, 3]}]))
        self.assertEqual([p["id"] for p in r.prisoners], ["refem_0", "refem_1"])
        self.assertEqual(r.prisoners[0]["nome"], "Tico")
        self.assertEqual(r.prisoners[1]["nome"], "Prisioneiro")

    def test_setter_de_compatibilidade(self):
        r = sala(mapa())
        r.prisoner = {"pos": [1, 1], "alive": True}
        self.assertEqual(r.prisoners[0]["id"], "refem_0")
        r.prisoner = None
        self.assertEqual(r.prisoners, [])
        self.assertIsNone(r.prisoner)

    def test_ajudantes(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [4, 3]}]))
        a, b = r.prisoners
        self.assertIs(r._refem_por_id("refem_1"), b)
        self.assertIs(r._refem_por_id(None), a)
        self.assertIs(r._refem_por_id("__prisioneiro__"), a)
        self.assertIsNone(r._refem_por_id("refem_9"))
        self.assertTrue(r._eh_refem(b))
        self.assertFalse(r._eh_refem(dict(b)))
        a["salvo"] = True
        self.assertIs(r.prisoner, b)
        self.assertEqual(r._refens_no_mapa(), [b])

    def test_validador(self):
        ok, _ = S.validar_dungeon(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [4, 3]}]))
        self.assertTrue(ok)
        treze = [{"pos": [x % 12, 2 + x // 12]} for x in range(13)]
        self.assertFalse(S.validar_dungeon(mapa(prisoners=treze))[0])
        self.assertFalse(S.validar_dungeon(mapa(prisoners=[{"pos": [3, 3]}, {"pos": [3, 3]}]))[0])
        self.assertFalse(S.validar_dungeon(
            mapa(prisoner={"pos": [3, 3]}, prisoners=[{"pos": [4, 3]}]))[0])
        self.assertFalse(S.validar_dungeon(mapa(prisoners={"pos": [3, 3]}))[0])

    def test_foto_antiga_e_nova(self):
        defn = mapa()
        r = sala(defn)
        antigo = {"pos": [2, 2], "hp": 5, "alive": True, "freed": True, "nome": "Zé"}
        corpo = r._foto_aplicar_sala({"sala": {"prisoner": antigo}, "pids": {}}, {}, defn)
        self.assertEqual(len(r.prisoners), 1)
        p = r.prisoners[0]
        self.assertEqual((p["id"], p["modo"], p["salvo"], p["hp"], p["nome"]),
                         ("refem_0", "guiar", False, 5, "Zé"))
        self.assertIs(r.prisoner, p)
        novo = [{"pos": [2, 2], "id": "refem_0", "modo": "guiar", "salvo": True},
                {"pos": [3, 2], "id": "refem_1", "modo": "ficar", "salvo": False}]
        r._foto_aplicar_sala({"sala": {"prisoners": copy.deepcopy(novo)}, "pids": {}}, {}, defn)
        self.assertEqual([(p["id"], p["modo"], p["salvo"]) for p in r.prisoners],
                         [("refem_0", "guiar", True), ("refem_1", "ficar", False)])

    def test_game_state_manda_as_duas_chaves(self):
        r = sala(mapa(prisoners=[{"pos": [3, 3]}]))
        est = r._game_state_payload()
        self.assertEqual(len(est["prisoners"]), 1)
        self.assertIs(est["prisoner"], est["prisoners"][0])


if __name__ == "__main__":
    unittest.main()
