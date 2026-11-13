"""Poção de cura na cidade: sem turno, ação bônus nem fome/sede.
Rode da raiz: python -X utf8 tools/test_pocao_cura_cidade.py"""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402


def sala():
    r = S.GameRoom("CURA_CIDADE")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"
    r.erros = []

    async def noop(*a, **k):
        pass

    async def send_to(pid, msg):
        if msg.get("type") == "error":
            r.erros.append(msg["msg"])

    r.send_to = send_to
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.broadcast_city_state = noop
    r.push_state_or_city = noop
    return r, p


def pocao(item_id="health_potion_small"):
    for lista in (S.SHOP_TEMPLE, S.SHOP_MERCHANT, S.SHOP_TAVERN):
        for i in lista:
            if i["id"] == item_id:
                return deepcopy(i)
    raise AssertionError(item_id)


class PocaoCuraCidadeTests(unittest.IsolatedAsyncioTestCase):
    async def test_cura_na_cidade_e_consome(self):
        r, p = sala()
        p["hp"] = 1
        fome, sede = p["fome"], p["sede"]
        it = pocao()
        p["bag"].append(it)
        await r.handle_use_item("p1", it["id"])
        self.assertGreater(p["hp"], 1)
        self.assertNotIn(it, p["bag"])
        self.assertFalse(p.get("bonus_action_used"))
        self.assertEqual((p["fome"], p["sede"]), (fome, sede))

    async def test_vida_cheia_nao_gasta_a_pocao(self):
        r, p = sala()
        p["hp"] = p["max_hp"]
        it = pocao()
        p["bag"].append(it)
        await r.handle_use_item("p1", it["id"])
        self.assertIn(it, p["bag"])
        self.assertEqual(len(r.erros), 1)

    async def test_outros_consumiveis_continuam_bloqueados_na_cidade(self):
        r, p = sala()
        p["hp"] = 1
        it = {"id": "x_regen", "name": "R", "emoji": "x", "effect": "regeneration",
              "value": 10, "item_slot": "bag"}
        p["bag"].append(it)
        await r.handle_use_item("p1", it["id"])
        self.assertIn(it, p["bag"])
        self.assertEqual(p["hp"], 1)

    async def test_pocao_com_doses_gasta_uma_dose(self):
        r, p = sala()
        p["hp"] = 1
        it = pocao()
        it["max_uses"], it["uses_left"] = 3, 3
        p["bag"].append(it)
        await r.handle_use_item("p1", it["id"])
        self.assertIn(it, p["bag"])
        self.assertEqual(it["uses_left"], 2)


if __name__ == "__main__":
    unittest.main()
