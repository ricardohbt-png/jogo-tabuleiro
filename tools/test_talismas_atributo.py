"""Talismãs de atributo.
Rode da raiz: python -X utf8 tools/test_talismas_atributo.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=1000):
    r = S.GameRoom("TALISMA_TESTE")
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


ATRIBUTOS = {"forca": "str_", "destreza": "dex", "inteligencia": "int_", "constituicao": "con_"}
TIERS = {"despertar": (250, 1, "medalhao3.png"), "ascensao": (500, 2, "medalhao4.png")}


class TalismasTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_precos_icones_e_estoque(self):
        por_id = {i["id"]: i for i in S.SHOP_MERCHANT}
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        mercadores = [c for c, l in lojas.items() if "mercador" in l]
        self.assertEqual(len(mercadores), 5)
        for tier, (preco, valor, icone) in TIERS.items():
            for nome, efeito in ATRIBUTOS.items():
                item = por_id[f"talisma_{tier}_{nome}"]
                self.assertEqual(item["price"], preco)
                self.assertEqual((item["item_slot"], item["effect"], item["value"]),
                                 ("item", efeito, valor))
                self.assertEqual(item["icon"], f"assets/itens/{icone}")
                self.assertTrue((RAIZ / item["icon"]).is_file())
                for cidade in mercadores:
                    ids = [i["id"] if isinstance(i, dict) else i
                           for i in lojas[cidade]["mercador"]]
                    self.assertEqual(ids.count(item["id"]), 1, f"{cidade}:{item['id']}")

    async def _equipa(self, r, p, item_id):
        await r.handle_shop_buy("p1", "mercador", item_id)
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == item_id)
        await r.handle_equip_from_bag("p1", indice)

    async def test_forca_acompanha_ataque_e_remove_ao_desequipar(self):
        r, p = sala()
        forca, atk = p["str_"], p["atk_bonus"]
        await self._equipa(r, p, "talisma_ascensao_forca")
        self.assertEqual(p["str_"], forca + 2)
        self.assertEqual(p["atk_bonus"], atk + (S.mod(forca + 2) - S.mod(forca)))
        await r.handle_unequip("p1", next(k for k, v in p["gear"].items()
                                          if v and v.get("id") == "talisma_ascensao_forca"))
        self.assertEqual((p["str_"], p["atk_bonus"]), (forca, atk))

    async def test_destreza_acompanha_ca(self):
        r, p = sala()
        des, ca = p["dex"], p["ac"]
        await self._equipa(r, p, "talisma_ascensao_destreza")
        self.assertEqual(p["dex"], des + 2)
        self.assertEqual(p["ac"], ca + (S.mod(des + 2) - S.mod(des)))

    async def test_constituicao_acompanha_pv_maximos(self):
        r, p = sala()
        con, pv = p["con_"], p["max_hp"]
        await self._equipa(r, p, "talisma_ascensao_constituicao")
        self.assertEqual(p["con_"], con + 2)
        self.assertGreaterEqual(p["max_hp"], pv)
        await r.handle_unequip("p1", next(k for k, v in p["gear"].items()
                                          if v and v.get("id") == "talisma_ascensao_constituicao"))
        self.assertEqual((p["con_"], p["max_hp"]), (con, pv))


if __name__ == "__main__":
    unittest.main()
