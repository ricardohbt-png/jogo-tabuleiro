"""Banquete de Viagem à venda nas tavernas: vai para a mochila (não é comido no balcão),
custa 100, restaura 40/40 ao ser usado e não tem o limite de 1×/visita do Banquete de balcão.
Roda da raiz: python -X utf8 tools/test_banquete_viagem_na_taverna.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=500):
    r = S.GameRoom("TAVERNA")
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gold"] = ouro
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"
    r.msgs = []

    async def send(pid, m, *a, **k): r.msgs.append(m)

    async def noop(*a, **k): pass
    r.send_to = send; r.gm_say = noop; r.broadcast = noop
    r.push_state = noop; r.broadcast_city_state = noop; r.push_state_or_city = noop
    return r, p


class TavernaTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_estoque_das_cidades(self):
        item = next(i for i in S.SHOP_TAVERN if i["id"] == "banquete_viagem")
        self.assertEqual((item["price"], item["fome"], item["sede"]), (100, 40, 40))
        self.assertEqual(item["item_slot"], "bag")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        for cidade, v in lojas.items():
            self.assertIn("banquete_viagem", v["taverna"], cidade)
            ids = [(i["id"] if isinstance(i, dict) else i) for i in S._city_shop_items(cidade, "taverna")]
            self.assertIn("banquete_viagem", ids, cidade)

    async def test_compra_vai_para_a_mochila_sem_comer(self):
        r, p = sala()
        p["fome"] = p["sede"] = 10
        antes = {k: p[k] for k in ("fome", "sede")}
        await r.handle_shop_buy("p1", "taverna", "banquete_viagem")
        self.assertEqual([m for m in r.msgs if m.get("type") == "error"], [])
        self.assertEqual(p["gold"], 400, "custa 100 moedas")
        self.assertEqual([i["id"] for i in p["bag"]].count("banquete_viagem"), 1)
        self.assertEqual({k: p[k] for k in antes}, antes, "não é consumido no balcão")
        self.assertNotIn("banquete_viagem", p.get("taverna_refeicoes", []))

    async def test_usar_da_mochila_restaura_40_e_40(self):
        r, p = sala()
        await r.handle_shop_buy("p1", "taverna", "banquete_viagem")
        p["fome"] = p["sede"] = 10
        r.phase = "playing"
        r._is_turn = lambda pid: True
        await r.handle_use_item("p1", "banquete_viagem")
        self.assertEqual((p["fome"], p["sede"]), (50, 50))
        self.assertFalse([i for i in p["bag"] if i["id"] == "banquete_viagem"], "o banquete é consumido")

    async def test_sem_limite_de_uma_por_visita(self):
        r, p = sala()
        await r.handle_shop_buy("p1", "taverna", "banquete_viagem")
        await r.handle_shop_buy("p1", "taverna", "banquete_viagem")
        self.assertEqual([m for m in r.msgs if m.get("type") == "error"], [])
        self.assertEqual([i["id"] for i in p["bag"]].count("banquete_viagem"), 2)
        self.assertEqual(p["gold"], 300)

    async def test_sem_ouro_recusa(self):
        r, p = sala(ouro=99)
        await r.handle_shop_buy("p1", "taverna", "banquete_viagem")
        self.assertEqual(p["gold"], 99)
        self.assertFalse([i for i in p["bag"] if i["id"] == "banquete_viagem"])

    async def test_o_banquete_de_balcao_continua_consumido_na_hora(self):
        r, p = sala()
        await r.handle_shop_buy("p1", "taverna", "banquete")
        self.assertFalse([i for i in p["bag"] if i["id"] == "banquete"])
        self.assertIn("banquete", p.get("taverna_refeicoes", []))
        await r.handle_shop_buy("p1", "taverna", "banquete")
        self.assertTrue([m for m in r.msgs if m.get("type") == "error"], "1×/visita")

    def test_cliente_nao_trata_como_refeicao_de_balcao(self):
        js = (RAIZ / "game.js").read_text(encoding="utf-8")
        self.assertIn("item.effect==='meal_survival' && item.item_slot!=='bag'", js)


if __name__ == "__main__":
    unittest.main()
