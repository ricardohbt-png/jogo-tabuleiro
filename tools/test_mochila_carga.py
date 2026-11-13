"""Mochila de Carga.
Rode da raiz: python -X utf8 tools/test_mochila_carga.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=1000):
    r = S.GameRoom("MOCHILA_TESTE")
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gold"] = ouro
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"

    async def noop(*a, **k):
        pass

    r.send_to = noop
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.broadcast_city_state = noop
    r.push_state_or_city = noop
    return r, p


class MochilaCargaTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_mesmos_mercadores_da_mochila_de_couro(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "mochila_carga")
        self.assertEqual(item["price"], 250)
        self.assertEqual((item["item_slot"], item["effect"], item["value"]),
                         ("item", "bagslots", 6))
        self.assertEqual(item["icon"], "assets/itens/backpack.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        com_couro = [c for c, l in lojas.items() if "backpack" in l.get("mercador", [])]
        com_carga = [c for c, l in lojas.items() if "mochila_carga" in l.get("mercador", [])]
        self.assertEqual(len(com_couro), 4)
        self.assertEqual(sorted(com_carga), sorted(com_couro))
        for cidade in com_carga:
            self.assertEqual(lojas[cidade]["mercador"].count("mochila_carga"), 1, cidade)

    async def _equipa(self, r, p, item_id):
        await r.handle_shop_buy("p1", "mercador", item_id)
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == item_id)
        await r.handle_equip_from_bag("p1", indice)

    async def test_equipar_soma_6_espacos_e_desequipar_devolve(self):
        r, p = sala()
        base = p["bag_size"]
        await self._equipa(r, p, "mochila_carga")
        self.assertEqual(p["bag_size"], base + 6)
        slot = next(k for k, v in p["gear"].items() if v and v.get("id") == "mochila_carga")
        await r.handle_unequip("p1", slot)
        self.assertEqual(p["bag_size"], base)

    async def test_acumula_com_a_mochila_de_couro(self):
        r, p = sala()
        base = p["bag_size"]
        await self._equipa(r, p, "mochila_carga")
        await self._equipa(r, p, "backpack")
        self.assertEqual(p["bag_size"], base + 6 + 3)


if __name__ == "__main__":
    unittest.main()
