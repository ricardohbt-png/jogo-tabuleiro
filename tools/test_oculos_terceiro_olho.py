"""Óculos do Terceiro Olho: +5 de Percepção enquanto equipado (cabeça).
Roda da raiz: python -X utf8 tools/test_oculos_terceiro_olho.py"""
import asyncio
import json
import os
import sys
import unittest
from copy import deepcopy

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

ID = "oculos_terceiro_olho"


def item():
    return deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == ID))


class CatalogoTests(unittest.TestCase):
    def test_perfil(self):
        it = item()
        self.assertEqual((it["price"], it["item_slot"], it["effect"], it["value"]),
                         (650, "head", "perception_bonus", 5))
        self.assertTrue(os.path.exists(os.path.join(RAIZ, it["icon"])), "ícone inexistente")

    def test_nos_cinco_mercadores(self):
        with open(os.path.join(RAIZ, "city_shops.json"), encoding="utf-8") as f:
            cidades = json.load(f)
        n = 0
        for cidade, lojas in cidades.items():
            lista = (lojas or {}).get("mercador")
            if lista is None:
                continue
            n += 1
            self.assertIn(ID, lista, cidade)
        self.assertEqual(n, 5)


class PercepcaoTests(unittest.TestCase):
    def sala(self):
        r = S.GameRoom("OCU")
        p = S.make_player("p0", "H", "warrior", 0)
        r.players["p0"] = p
        return r, p

    def test_bonus_so_enquanto_equipado(self):
        r, p = self.sala()
        base = r._get_percepcao_heroi(p)
        p["gear"]["head"] = item()
        self.assertEqual(r._get_percepcao_heroi(p), base + 5)
        p["gear"]["head"] = None
        self.assertEqual(r._get_percepcao_heroi(p), base)

    def test_bonus_dentro_da_lista_de_bonus_tambem_conta(self):
        r, p = self.sala()
        base = r._get_percepcao_heroi(p)
        p["gear"]["head"] = {"id": "x", "effect": "vision", "value": 0,
                             "bonuses": [{"effect": "perception_bonus", "value": 2}]}
        self.assertEqual(r._get_percepcao_heroi(p), base + 2)

    def test_equipar_pelo_fluxo_real_nao_quebra(self):
        r, p = self.sala()
        async def nada(*a, **k): pass
        r.gm_say = nada; r.send_to = nada; r.broadcast = nada; r.push_state = nada
        r.broadcast_city_state = nada; r.phase = "city"; r.host_pid = "p0"
        r.connections["p0"] = object()
        base = r._get_percepcao_heroi(p)
        p["bag"] = [item()]
        asyncio.run(r.handle_equip_from_bag("p0", 0))
        self.assertEqual((p["gear"].get("head") or {}).get("id"), ID)
        self.assertEqual(r._get_percepcao_heroi(p), base + 5)


if __name__ == "__main__":
    unittest.main()
