"""Herói salvo morto (0 PV) não pode voltar "vivo" com 0 PV numa aventura nova.
`hp` é durável e `alive` não: a ficha restaurada ficava com alive=True e hp=0.
Roda da raiz: python -X utf8 tools/test_heroi_morto_restaurado.py"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def heroi_morto():
    p = S.make_player("p0", "Ana", "warrior", 0)
    p["hp"] = 0
    p["alive"] = False
    return p


class RestauracaoTests(unittest.TestCase):
    def test_ficha_salva_com_0_pv_volta_com_1_pv_e_viva(self):
        snap = S.snapshot_character(heroi_morto())
        self.assertEqual(snap["hp"], 0, "a ficha guarda os 0 PV")
        novo = S.make_player("p1", "Ana", "warrior", 0)
        S.restore_character(novo, snap)
        self.assertEqual(novo["hp"], 1)
        self.assertTrue(novo["alive"])

    def test_pv_negativo_tambem_volta_com_1(self):
        snap = S.snapshot_character(heroi_morto())
        snap["hp"] = -4
        novo = S.make_player("p1", "Ana", "warrior", 0)
        S.restore_character(novo, snap)
        self.assertEqual(novo["hp"], 1)
        self.assertTrue(novo["alive"])

    def test_heroi_ferido_mas_vivo_nao_muda(self):
        p = S.make_player("p0", "Ana", "warrior", 0)
        p["hp"] = 3
        snap = S.snapshot_character(p)
        novo = S.make_player("p1", "Ana", "warrior", 0)
        S.restore_character(novo, snap)
        self.assertEqual(novo["hp"], 3)
        self.assertTrue(novo["alive"])

    def test_ficha_sem_hp_nao_e_tratada_como_morta(self):
        novo = S.make_player("p1", "Ana", "warrior", 0)
        hp_inicial = novo["hp"]
        S.restore_character(novo, {})
        self.assertEqual(novo["hp"], hp_inicial)
        self.assertTrue(novo["alive"])


if __name__ == "__main__":
    unittest.main()
