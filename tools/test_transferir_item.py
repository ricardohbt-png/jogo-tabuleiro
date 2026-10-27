"""Passar itens entre heróis do mesmo jogador (Solo com grupo).
Rode da raiz: python -X utf8 tools/test_transferir_item.py"""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402


def sala(fase="city"):
    r = S.GameRoom("TRANSFER")
    a = S.make_player("a", "Ana", "warrior", 0)
    b = S.make_player("b", "Bia", "mage", 1)
    b["controlador"] = "a"
    c = S.make_player("c", "Cai", "rogue", 2)       # herói de OUTRO jogador
    for q in (a, b, c):
        r.players[q["id"]] = q
    r.player_order = ["a", "b", "c"]
    r.phase = fase
    r.erros, r.narracao = [], []

    async def noop(*x, **k):
        pass

    async def send_to(pid, msg):
        if msg.get("type") == "error":
            r.erros.append(str(msg["msg"]))

    async def gm(msg, *x, **k):
        r.narracao.append(msg)

    r.send_to, r.gm_say = send_to, gm
    r.broadcast = r.push_state = r.broadcast_city_state = r.push_state_or_city = noop
    return r, a, b, c


def capacete_de_ferro():
    for lista in (S.SHOP_ARMORS, S.SHOP_MERCHANT):
        for i in lista:
            if i["id"] == "helm_iron":
                return deepcopy(i)
    raise AssertionError("helm_iron")


def item(i="x"):
    return {"id": i, "name": i, "emoji": "x", "item_slot": "bag", "effect": "food", "value": 1}


class TransferirTests(unittest.IsolatedAsyncioTestCase):
    async def test_bolsa_vai_para_a_bolsa_do_outro(self):
        r, a, b, _ = sala()
        it = item(); a["bag"].append(it)
        await r.handle_transfer_item("a", "bag", index=len(a["bag"]) - 1, to_hero="b")
        self.assertNotIn(it, a["bag"])
        self.assertIn(it, b["bag"])
        self.assertEqual(r.erros, [])

    async def test_bolsa_cheia_falha_e_o_item_fica(self):
        r, a, b, _ = sala()
        it = item(); a["bag"].append(it)
        b["bag"] = [item(f"f{i}") for i in range(b.get("bag_size", 6))]
        await r.handle_transfer_item("a", "bag", index=len(a["bag"]) - 1, to_hero="b")
        self.assertIn(it, a["bag"])
        self.assertEqual(len(b["bag"]), b.get("bag_size", 6))
        self.assertEqual(len(r.erros), 1)

    async def test_nao_passa_para_heroi_de_outro_jogador_nem_para_si(self):
        r, a, b, c = sala()
        it = item(); a["bag"].append(it)
        for alvo in ("c", "a", "zzz", None):
            await r.handle_transfer_item("a", "bag", index=len(a["bag"]) - 1, to_hero=alvo)
        self.assertIn(it, a["bag"])
        self.assertEqual(len(r.erros), 4)

    async def test_na_masmorra_so_adjacentes(self):
        r, a, b, _ = sala("playing")
        a["pos"], b["pos"] = [5, 5], [9, 9]
        it = item(); a["bag"].append(it)
        await r.handle_transfer_item("a", "bag", index=len(a["bag"]) - 1, to_hero="b")
        self.assertIn(it, a["bag"]); self.assertEqual(len(r.erros), 1)
        b["pos"] = [6, 6]
        await r.handle_transfer_item("a", "bag", index=len(a["bag"]) - 1, to_hero="b")
        self.assertIn(it, b["bag"]); self.assertNotIn(it, a["bag"])

    async def test_equipado_desequipa_e_vai_mesmo_com_a_propria_bolsa_cheia(self):
        r, a, b, _ = sala()
        capacete = capacete_de_ferro()
        a["gear"]["head"] = capacete
        a["bag"] = [item(f"f{i}") for i in range(a.get("bag_size", 6))]
        tamanho = a["bag_size"]
        await r.handle_transfer_item("a", "gear", slot_key="head", to_hero="b")
        self.assertIsNone(a["gear"]["head"])
        self.assertTrue(any(i is capacete for i in b["bag"]))
        self.assertFalse(any(i is capacete for i in a["bag"]))
        self.assertEqual(a["bag_size"], tamanho)

    async def test_equipado_com_destino_cheio_continua_equipado(self):
        r, a, b, _ = sala()
        capacete = capacete_de_ferro()
        a["gear"]["head"] = capacete
        b["bag"] = [item(f"f{i}") for i in range(b.get("bag_size", 6))]
        await r.handle_transfer_item("a", "gear", slot_key="head", to_hero="b")
        self.assertIs(a["gear"]["head"], capacete)
        self.assertEqual(len(r.erros), 1)


if __name__ == "__main__":
    unittest.main()
