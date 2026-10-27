"""Botas do Passo Felino.
Rode da raiz: python -X utf8 tools/test_botas_passo_felino.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=1000):
    r = S.GameRoom("BOTAS_TESTE")
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


class BotasPassoFelinoTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_estoque_dos_cinco_mercadores(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "botas_passo_felino")
        self.assertEqual(item["price"], 500)
        self.assertEqual((item["item_slot"], item["effect"], item["value"]),
                         ("boots", "dex", 2))
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        mercadores = [c for c, l in lojas.items() if "mercador" in l]
        self.assertEqual(len(mercadores), 5)
        for cidade in mercadores:
            self.assertEqual(lojas[cidade]["mercador"].count("botas_passo_felino"), 1, cidade)

    async def _equipa(self, r, p, item_id):
        await r.handle_shop_buy("p1", "mercador", item_id)
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == item_id)
        await r.handle_equip_from_bag("p1", indice)

    async def test_equipa_no_slot_de_botas_e_soma_2_de_destreza(self):
        r, p = sala()
        des, ca, ref = p["dex"], p["ac"], p.get("ref_", 0)
        await self._equipa(r, p, "botas_passo_felino")
        self.assertEqual(p["gear"]["boots"]["id"], "botas_passo_felino")
        self.assertEqual(p["dex"], des + 2)
        delta = S.mod(des + 2) - S.mod(des)
        self.assertEqual(p["ac"], ca + delta)
        self.assertEqual(p.get("ref_", 0), ref + delta)

    async def test_desequipar_restaura_e_nao_mexe_na_velocidade(self):
        r, p = sala()
        des, ca, spd = p["dex"], p["ac"], p.get("spd")
        await self._equipa(r, p, "botas_passo_felino")
        self.assertEqual(p.get("spd"), spd)
        await r.handle_unequip("p1", "boots")
        self.assertEqual((p["dex"], p["ac"]), (des, ca))


if __name__ == "__main__":
    unittest.main()
