"""Regressões do Anel do Vigia. Rode da raiz: python -X utf8 tools/test_anel_vigia.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=500):
    r = S.GameRoom("VIGIA_TESTE")
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


class AnelVigiaTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_estoque_de_todos_os_mercadores(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "anel_vigia")
        self.assertEqual(item["price"], 80)
        self.assertEqual((item["item_slot"], item["effect"], item["value"]),
                         ("ring", "vision", 2))
        self.assertEqual(item["icon"], "assets/itens/ring.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())

        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        mercadores = [cidade for cidade, lojas_cidade in lojas.items()
                      if "mercador" in lojas_cidade]
        self.assertEqual(len(mercadores), 5)
        for cidade in mercadores:
            ids = [i["id"] if isinstance(i, dict) else i
                   for i in lojas[cidade]["mercador"]]
            self.assertEqual(ids.count("anel_vigia"), 1, cidade)

    async def test_compra_equipamento_e_desequipamento_alteram_a_visao(self):
        r, p = sala()
        visao_inicial = r._get_raio_visao(p)

        await r.handle_shop_buy("p1", "mercador", "anel_vigia")
        self.assertEqual(p["gold"], 420)
        indice = next(i for i, item in enumerate(p["bag"])
                      if item["id"] == "anel_vigia")

        await r.handle_equip_from_bag("p1", indice)
        self.assertEqual(p["gear"]["ring1"]["id"], "anel_vigia")
        self.assertEqual(r._get_raio_visao(p), visao_inicial + 2)

        await r.handle_unequip("p1", "ring1")
        self.assertEqual(r._get_raio_visao(p), visao_inicial)


if __name__ == "__main__":
    unittest.main()
