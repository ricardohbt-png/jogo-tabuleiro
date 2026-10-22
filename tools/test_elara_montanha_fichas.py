"""Fichas da rota do Olho. Roda da raiz: python -X utf8 tools/test_elara_montanha_fichas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_montanha_fichas as F


class FichasTests(unittest.TestCase):
    def test_validam_e_tem_o_cr(self):
        for fn, cr in ((F.ficha_assassino, 3), (F.ficha_bardo_agente, 2)):
            ok, norm = S._validate_custom_monster(fn())
            self.assertTrue(ok, norm)
            self.assertEqual(S.monster_cr(norm), cr, norm["type"])

    def test_assassino_e_chefe(self):
        ok, n = S._validate_custom_monster(F.ficha_assassino())
        self.assertTrue(n["boss"])

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([F.ficha_assassino(), F.ficha_bardo_agente()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
