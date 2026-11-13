"""Ficha do Gilo Dedos Sujos. Roda da raiz: python -X utf8 tools/test_elara_gilo_ficha.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_gilo_ficha as G


class FichaTests(unittest.TestCase):
    def test_valida_e_tem_o_essencial(self):
        f = G.ficha_gilo()
        ok, norm = S._validate_custom_monster(f)
        self.assertTrue(ok, norm)
        self.assertEqual(norm["type"], "gilo_dedos_sujos")
        self.assertEqual(norm["cr"], 2.5)
        self.assertEqual(S.monster_cr(norm), 2.5)
        self.assertEqual([x["num_attacks"] for x in norm["attacks"]], [1, 1])   # duas bestas de mão

    def test_nada_da_rede_por_nome(self):
        t = json.dumps(G.ficha_gilo(), ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos"):
            self.assertNotIn(p, t)

    def test_base_nao_e_alterada(self):
        self.assertEqual(G._soldado()["type"], "soldado")
        self.assertEqual(G._soldado()["cr"], 1.0)


if __name__ == "__main__":
    unittest.main()
