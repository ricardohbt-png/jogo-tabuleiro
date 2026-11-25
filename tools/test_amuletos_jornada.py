"""Amuletos da Jornada: +Constituição e +limite máximo de fome e sede enquanto equipados.
Roda da raiz: python -X utf8 tools/test_amuletos_jornada.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

ITENS = {"amuleto_jornada": (5, 1), "amuleto_jornada_infindavel": (10, 1), "relicario_jornada_eterna": (20, 2)}


def heroi():
    return S.make_player("p0", "H", "warrior", 0)


def item(iid):
    return next(i for i in S.SHOP_MERCHANT if i["id"] == iid)


def sala():
    r = S.GameRoom("AMU")
    return r


class AmuletosTests(unittest.TestCase):
    def test_estao_no_mercador_de_todas_as_cidades(self):
        with open(os.path.join(RAIZ, "city_shops.json"), encoding="utf-8") as f:
            lojas = json.load(f)
        achados = 0
        for cidade, d in lojas.items():
            merc = d.get("mercador") if isinstance(d, dict) else None
            if merc is None:
                continue
            achados += 1
            for iid in ITENS:
                self.assertIn(iid, merc, f"{iid} falta em {cidade}")
        self.assertGreaterEqual(achados, 5)

    def test_equipar_e_desequipar_e_simetrico(self):
        r = sala()
        for iid, (limite, con) in ITENS.items():
            p = heroi()
            con_antes, fome_antes, sede_antes = p["con_"], p["fome_max"], p["sede_max"]
            r._apply_gear_effect(p, item(iid), True)
            self.assertEqual(p["fome_max"], fome_antes + limite, iid)
            self.assertEqual(p["sede_max"], sede_antes + limite, iid)
            self.assertEqual(p["con_"], con_antes + con, iid)
            r._apply_gear_effect(p, item(iid), False)
            self.assertEqual((p["fome_max"], p["sede_max"], p["con_"]), (fome_antes, sede_antes, con_antes), iid)

    def test_dois_amuletos_acumulam_e_saem_um_de_cada_vez(self):
        r = sala(); p = heroi(); base = p["fome_max"]
        r._apply_gear_effect(p, item("amuleto_jornada"), True)
        r._apply_gear_effect(p, item("amuleto_jornada_infindavel"), True)
        self.assertEqual(p["fome_max"], base + 15)
        r._apply_gear_effect(p, item("amuleto_jornada"), False)
        self.assertEqual(p["fome_max"], base + 10)

    def test_desequipar_nao_deixa_fome_acima_do_novo_teto(self):
        r = sala(); p = heroi()
        r._apply_gear_effect(p, item("relicario_jornada_eterna"), True)
        p["fome"] = p["fome_max"]
        r._apply_gear_effect(p, item("relicario_jornada_eterna"), False)
        self.assertLessEqual(p["fome"], p["fome_max"])


if __name__ == "__main__":
    unittest.main()
