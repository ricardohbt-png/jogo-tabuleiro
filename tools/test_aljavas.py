"""Aljavas: ampliam o limite de pilha de flechas/virotes enquanto equipadas na mão secundária.
Rode da raiz: python -X utf8 tools/test_aljavas.py"""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def aljava(item_id):
    return deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == item_id))


def jogador(off_hand=None):
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gear"]["off_hand"] = off_hand
    return p


class AljavasTests(unittest.TestCase):
    def test_catalogo_precos_e_estoque_dos_ferreiros(self):
        pequena, grande = aljava("aljava_pequena"), aljava("aljava_grande")
        self.assertEqual((pequena["price"], grande["price"]), (30, 60))
        for item in (pequena, grande):
            self.assertEqual((item["item_slot"], item["effect"]), ("off_hand", "quiver"))
            self.assertEqual(item["icon"], "assets/itens/aljava.png")
            self.assertTrue((RAIZ / item["icon"]).is_file())
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        ferreiros = [c for c, l in lojas.items() if "ferreiro_ammo" in l]
        self.assertEqual(len(ferreiros), 5)
        for cidade in ferreiros:
            ids = [i["id"] if isinstance(i, dict) else i for i in lojas[cidade]["ferreiro_ammo"]]
            for item_id in ("aljava_pequena", "aljava_grande"):
                self.assertEqual(ids.count(item_id), 1, f"{cidade}:{item_id}")

    def test_sem_aljava_o_limite_continua_10(self):
        p = jogador()
        for tipo in ("flechas", "flechas_prata", "virotes", "virotes_incendiarios"):
            self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": tipo}), 10, tipo)

    def test_aljava_pequena_amplia_20_flechas_ou_25_virotes(self):
        p = jogador(aljava("aljava_pequena"))
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "flechas"}), 20)
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "flechas_prata"}), 20)
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "virotes"}), 25)
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "virotes_incendiarios"}), 25)

    def test_aljava_grande_amplia_40_flechas_ou_50_virotes(self):
        p = jogador(aljava("aljava_grande"))
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "flechas_incendiarias"}), 40)
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "virotes_prata"}), 50)

    def test_outro_item_na_mao_secundaria_nao_amplia(self):
        p = jogador({"id": "escudo_p", "name": "Escudo", "effect": "def_"})
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "flechas"}), 10)
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "item_qualquer"}), 10)

    def test_aljava_nao_amplia_o_que_nao_e_municao_de_arco_ou_besta(self):
        p = jogador(aljava("aljava_grande"))
        self.assertEqual(S._max_ammo_stack_for(p, {"ammo_type": "pedras"}), 10)


if __name__ == "__main__":
    unittest.main()
