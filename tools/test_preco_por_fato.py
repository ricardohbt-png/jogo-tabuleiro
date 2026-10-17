"""Preço das lojas da cidade por marcador (fato): o que aparece é o que se cobra; a venda não sobe.
Roda da raiz: python -X utf8 tools/test_preco_por_fato.py"""
import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

CID = "vila_dos_charcos"
FATO = "charcos_criancas_mortas"


def sala(cidade=CID, ouro=5000, fatos=()):
    r = S.GameRoom("PRECO")
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gold"] = ouro
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"
    r.world_location = cidade
    r.fatos = set(fatos)
    r.msgs = []

    async def send(pid, m, *a, **k): r.msgs.append(m)

    async def noop(*a, **k): pass
    r.send_to = send; r.gm_say = noop; r.broadcast = noop
    r.push_state = noop; r.broadcast_city_state = noop; r.push_state_or_city = noop
    return r, p


def preco_no_payload(r, loja, item_id):
    sh = r._city_state_payload()["shops"]
    if loja == "taverna": itens = sh["taverna"]
    elif loja == "mercador": itens = sh["mercador"]
    elif loja == "weapon": itens = sh["ferreiro"]["weapons"]
    else: itens = sh["ferreiro"]["armors"]
    return next(i["price"] for i in itens if i["id"] == item_id)


class PrecoTests(unittest.TestCase):
    def setUp(self):
        self._orig = {k: list(v) for k, v in S.CITY_PRICE_MODS.items()}
        S.CITY_PRICE_MODS[CID] = [{"fato": FATO, "preco_mult": 1.5}]

    def tearDown(self):
        S.CITY_PRICE_MODS.clear(); S.CITY_PRICE_MODS.update(self._orig)

    def test_sem_marcador_preco_normal(self):
        r, _ = sala()
        base = next(i["price"] for i in S.CITY_SHOP_SOURCES["taverna"] if i["id"] == "banquete_viagem")
        self.assertEqual(preco_no_payload(r, "taverna", "banquete_viagem"), base)

    def test_com_marcador_o_payload_ja_traz_o_preco_novo(self):
        r, _ = sala(fatos={FATO})
        base = next(i["price"] for i in S.CITY_SHOP_SOURCES["taverna"] if i["id"] == "banquete_viagem")
        self.assertEqual(preco_no_payload(r, "taverna", "banquete_viagem"), round(base * 1.5))
        wid = S.CITY_SHOPS[CID]["ferreiro_weapon"][0]
        wbase = next(i["price"] for i in S.CITY_SHOP_SOURCES["ferreiro_weapon"] if i["id"] == wid)
        self.assertEqual(preco_no_payload(r, "weapon", wid), round(wbase * 1.5))

    def test_compra_cobra_o_preco_mostrado(self):
        r, p = sala(fatos={FATO})
        mostrado = preco_no_payload(r, "taverna", "banquete_viagem")
        asyncio.run(r.handle_shop_buy("p1", "taverna", "banquete_viagem"))
        self.assertEqual(5000 - p["gold"], mostrado)

    def test_venda_nao_sobe(self):
        r, p = sala(fatos={FATO})
        base = next(i["price"] for i in S.CITY_SHOP_SOURCES["taverna"] if i["id"] == "banquete_viagem")
        asyncio.run(r.handle_shop_buy("p1", "taverna", "banquete_viagem"))
        item = next(i for i in p["bag"] if i["id"] == "banquete_viagem")
        self.assertEqual(item["buy_price"], base, "a revenda parte do preço base")
        ouro = p["gold"]
        asyncio.run(r.handle_shop_sell("p1", "bag_0"))
        self.assertEqual(p["gold"] - ouro, max(1, base // 3))

    def test_outra_cidade_nao_muda(self):
        r, _ = sala(cidade="alva_e_luz", fatos={FATO})
        base = next(i["price"] for i in S.CITY_SHOP_SOURCES["taverna"] if i["id"] == "banquete_viagem")
        self.assertEqual(preco_no_payload(r, "taverna", "banquete_viagem"), base)

    def test_tirar_o_marcador_volta(self):
        r, _ = sala(fatos={FATO})
        r.fatos.discard(FATO)
        base = next(i["price"] for i in S.CITY_SHOP_SOURCES["taverna"] if i["id"] == "banquete_viagem")
        self.assertEqual(preco_no_payload(r, "taverna", "banquete_viagem"), base)

    def test_arquivo_invalido_nao_derruba_o_boot(self):
        with tempfile.TemporaryDirectory() as d:
            for conteudo in ("{ quebrado", json.dumps({"naoexiste": [{"fato": "x", "preco_mult": 2}]}),
                             json.dumps({CID: [{"fato": "x", "preco_mult": 99}]}),
                             json.dumps({CID: "oi"}), json.dumps([1])):
                f = Path(d) / "m.json"; f.write_text(conteudo, encoding="utf-8")
                mods = S._carregar_modificadores_cidade(str(f))
                self.assertEqual(mods, {}, conteudo)
            f.write_text(json.dumps({CID: [{"fato": "x", "preco_mult": 2}]}), encoding="utf-8")
            self.assertEqual(S._carregar_modificadores_cidade(str(f)), {CID: [{"fato": "x", "preco_mult": 2.0}]})

    def test_produto_dos_modificadores(self):
        S.CITY_PRICE_MODS[CID].append({"fato": "b", "preco_mult": 2})
        self.assertEqual(S._city_price_mult(CID, {FATO, "b"}), 3.0)
        self.assertEqual(S._city_price_mult(CID, set()), 1.0)

    def test_mercador_e_pergaminhos_tambem_seguem_a_regra(self):
        S.CITY_SHOPS["vila_dos_charcos"].setdefault("mercador", [])
        ids = S.CITY_SHOPS[CID]["mercador"]
        ids_backup = list(ids)
        try:
            if "boots" not in ids: ids.append("boots")
            r, _ = sala(fatos={FATO})
            base = next(i["price"] for i in S.CITY_SHOP_SOURCES["mercador"] if i["id"] == "boots")
            self.assertEqual(preco_no_payload(r, "mercador", "boots"), round(base * 1.5))
            r.shop_scrolls = [{"id": "pergaminho_x", "name": "P", "price": 100}]
            sh = r._city_state_payload()["shops"]["mercador"]
            self.assertEqual(next(i["price"] for i in sh if i["id"] == "pergaminho_x"), 150)
        finally:
            ids[:] = ids_backup


if __name__ == "__main__":
    unittest.main()
