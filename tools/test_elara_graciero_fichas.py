"""Fichas e item de Graciero. Roda da raiz: python -X utf8 tools/test_elara_graciero_fichas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_graciero_fichas as F


class FichasTests(unittest.TestCase):
    def test_fichas_validam_e_tem_o_cr(self):
        for fn, cr in ((F.ficha_escorpiao_gigante, 1.5), (F.ficha_leonel, 3)):
            ok, norm = S._validate_custom_monster(fn())
            self.assertTrue(ok, norm)
            self.assertEqual(S.monster_cr(norm), cr, norm["type"])

    def test_leonel_e_chefe_com_dois_ataques(self):
        ok, n = S._validate_custom_monster(F.ficha_leonel())
        self.assertTrue(n["boss"])
        self.assertEqual(n["attacks"][0]["num_attacks"], 2)

    def test_escorpiao_gigante_golpeia_forte(self):
        ok, n = S._validate_custom_monster(F.ficha_escorpiao_gigante())
        self.assertEqual(n["attacks"][0]["damage"], "2d4")

    def test_olho_valida_e_nao_vai_a_loja_nem_ao_loot(self):
        ok, item = S._validate_custom_item(F.item_olho())
        self.assertTrue(ok, item)
        self.assertEqual(item["disponibilidade"], {"loja": False, "baus": True, "loot_monstro": False})
        self.assertEqual(item.get("bonuses"), [])

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([F.ficha_escorpiao_gigante(), F.ficha_leonel(), F.item_olho()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
