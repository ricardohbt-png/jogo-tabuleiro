"""Regressões do Anel de Proteção. Rode da raiz: python -X utf8 tools/test_anel_protecao.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=500):
    r = S.GameRoom("ANEL_TESTE")
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gold"] = ouro
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"
    r.msgs = []

    async def send(pid, m, *a, **k):
        r.msgs.append(m)

    async def noop(*a, **k):
        pass

    r.send_to = send
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.broadcast_city_state = noop
    r.push_state_or_city = noop
    return r, p


class AnelProtecaoTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_estoque_de_todos_os_mercadores(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "anel_protecao")
        self.assertEqual(item["price"], 80)
        self.assertEqual((item["item_slot"], item["effect"], item["value"]),
                         ("ring", "def_", 1))
        self.assertEqual(item["icon"], "assets/itens/ring.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())

        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        mercadores = [cidade for cidade, lojas_cidade in lojas.items()
                      if "mercador" in lojas_cidade]
        self.assertEqual(len(mercadores), 5)
        for cidade in mercadores:
            ids = [i["id"] if isinstance(i, dict) else i
                   for i in lojas[cidade]["mercador"]]
            self.assertEqual(ids.count("anel_protecao"), 1, cidade)

    async def test_compra_equipamento_e_desequipamento_alteram_ca(self):
        r, p = sala()
        ca_inicial = p["ac"]

        await r.handle_shop_buy("p1", "mercador", "anel_protecao")
        self.assertEqual(p["gold"], 420)
        self.assertEqual([i["id"] for i in p["bag"]].count("anel_protecao"), 1)
        indice = next(i for i, item in enumerate(p["bag"])
                      if item["id"] == "anel_protecao")

        await r.handle_equip_from_bag("p1", indice)
        self.assertEqual(p["gear"]["ring1"]["id"], "anel_protecao")
        self.assertEqual(p["ac"], ca_inicial + 1)

        await r.handle_unequip("p1", "ring1")
        self.assertEqual(p["ac"], ca_inicial)


if __name__ == "__main__":
    unittest.main()
