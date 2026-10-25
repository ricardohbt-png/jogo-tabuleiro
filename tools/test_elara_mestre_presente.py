"""Elara: depois da fazenda, o Mestre de Armas aparece em Alva e Luz e dá a fazenda de presente.
Roda da raiz: python -X utf8 tools/test_elara_mestre_presente.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def sala(fatos=()):
    r = S.GameRoom("MESTRE")
    r.world_location = "alva_e_luz"
    r.phase = "city"
    r.fatos = set(fatos)
    return r


class MestrePresenteTests(unittest.TestCase):
    def test_ponto_do_mestre_so_aparece_depois_da_fazenda(self):
        antes = sala()._city_points_payload()["alva_e_luz"]
        depois = sala({"elara_fazenda_vencida"})._city_points_payload()["alva_e_luz"]
        self.assertNotIn("mestre_armas_alva", antes)
        self.assertIn("mestre_armas_alva", depois)

    def test_refugio_continua_oculto_antes_da_fazenda(self):
        self.assertNotIn("ponto_1", sala()._city_points_payload()["alva_e_luz"])

    def test_cena_tem_o_mestre_com_a_fala_do_presente(self):
        cena = S.CITY_SCENES["alva_e_luz"]["mestre_armas_alva"]
        slot = cena["slots"][0]
        self.assertEqual(slot["image"], "assets/portraits/mestre_de_armas.png")
        conv = slot["conversations"][0]
        self.assertEqual(conv["requisito"].get("fato"), "elara_fazenda_vencida")
        self.assertIn("presente", conv["texto"])
        for palavra in ("itens", "dinheiro", "troféus"):
            self.assertIn(palavra, conv["texto"])
        self.assertFalse(conv["uma_vez"])

    def test_ponto_liga_na_cena(self):
        ponto = S.CITY_MAP_POINTS["alva_e_luz"]["mestre_armas_alva"]
        self.assertEqual((ponto["type"], ponto["scene"]), ("cena", "mestre_armas_alva"))


if __name__ == "__main__":
    unittest.main()
