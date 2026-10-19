import asyncio
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S


class SolucaoMecanismoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("SOLUCAO_MECANISMO_TEST")
        self.room.phase = "playing"
        self.room.round_num = 1
        self.room.tiles = [[S.FLOOR] * 12 for _ in range(12)]
        self.room.map_w = self.room.map_h = 12
        self.room.decorations = []
        self.player = S.make_player("h1", "Explorador", "warrior", 0)
        self.player.update(pos=[3, 3], action_done=False, bonus_action_used=False,
                           gold=500, fome=60, sede=60)
        item = next((i for i in S.SHOP_MERCHANT
                     if i["id"] == "solucao_mecanismo"), {
                         "id": "solucao_mecanismo", "name": "Solução do Mecanismo",
                         "emoji": "📦", "effect": "disarm_traps_area",
                         "icon": "assets/itens/solucao_mecanismo.png",
                         "item_slot": "bag", "price": 250,
                     })
        self.player["bag"] = [deepcopy(item)]
        self.room.players["h1"] = self.player
        self.ally = S.make_player("h2", "Aliada", "mage", 0)
        self.ally.update(pos=[8, 8], xp=0)
        self.ally["bag"] = []
        self.room.players["h2"] = self.ally

        async def noop(*args, **kwargs):
            pass
        self.room.gm_say = noop
        self.room.broadcast = noop
        self.room.push_state = noop
        self.room._is_turn = lambda pid: True
        self.room._check_level_up = noop

    def trap(self, trap_id, pos, *, permanent=False):
        kind = next(iter(S.ARMADILHAS))
        return {"id": trap_id, "tipo": kind, "pos": list(pos),
                "permanente": permanent, "visivel": False, "esgotada": False,
                "desativada": False, "criador": "monster"}

    async def test_shop_catalog_and_item_image(self):
        item = next((i for i in S.SHOP_MERCHANT
                     if i["id"] == "solucao_mecanismo"), None)
        self.assertIsNotNone(item)
        self.assertEqual((item["name"], item["price"], item["item_slot"],
                          item["effect"], item["icon"]),
                         ("Solução do Mecanismo", 250, "bag",
                          "disarm_traps_area", "assets/itens/solucao_mecanismo.png"))
        self.assertTrue((ROOT / item["icon"]).is_file())
        client_catalog = (ROOT / "src/gameState.js").read_text(encoding="utf-8")
        self.assertRegex(client_catalog, r"solucao_mecanismo:\s*\{[^\n]*loja:'mercado'[^\n]*preco:250")
        self.assertIn("item_slot:'bag'", client_catalog[client_catalog.index("solucao_mecanismo:"):])
        translations = (ROOT / "src/lang/catalogo.js").read_text(encoding="utf-8")
        self.assertIn('"cat.item.solucao_mecanismo.nome"', translations)
        self.assertIn('"cat.item.solucao_mecanismo.desc"', translations)
        shops = json.loads((ROOT / "city_shops.json").read_text(encoding="utf-8"))
        merchants = [v.get("mercador") for v in shops.values()
                     if isinstance(v.get("mercador"), list)]
        self.assertEqual(len(merchants), 4)
        self.assertTrue(all("solucao_mecanismo" in stock for stock in merchants))

    async def test_disarms_hidden_traps_in_all_sources_within_chebyshev_radius(self):
        kind = next(iter(S.ARMADILHAS))
        self.room.traps = [
            {"id": "pit-inside", "pos": [6, 6], "damage": 4, "triggered": False},
            {"id": "pit-outside", "pos": [7, 3], "damage": 4, "triggered": False},
            {"id": "pit-already-triggered", "pos": [4, 3], "damage": 4, "triggered": True},
        ]
        self.room.armadilhas = [
            self.trap("placed-inside", [4, 3]),
            self.trap("placed-permanent", [3, 6], permanent=True),
            self.trap("placed-outside", [7, 3]),
        ]
        self.room.decorations = [
            {"id": "decor-inside", "type": "cama", "pos": [5, 3],
             "facing": [0, 1], "trap": {"tipo": kind, "permanente": True},
             "trap_triggered": True, "trap_disarmed": False,
             "trap_revealed": False},
            {"id": "chest-inside", "type": "cama", "pos": [2, 3],
             "facing": [0, 1], "chest_trap_monster_type": "goblin",
             "chest_trap_permanente": True, "chest_trap_triggered": True,
             "chest_trap_disarmed": False, "trap_revealed": False},
            {"id": "decor-outside", "type": "placa", "pos": [9, 3],
             "facing": [0, 1], "trap": {"tipo": kind},
             "trap_triggered": False, "trap_disarmed": False},
        ]

        await self.room.handle_use_item("h1", "solucao_mecanismo")

        self.assertTrue(self.player["bonus_action_used"])
        self.assertFalse(self.player["action_done"])
        self.assertFalse(self.player["bag"])
        self.assertEqual({t["id"] for t in self.room.traps},
                         {"pit-outside", "pit-already-triggered"})
        self.assertEqual({t["id"] for t in self.room.armadilhas}, {"placed-outside"})
        self.assertTrue(self.room.decorations[0]["trap_disarmed"])
        self.assertTrue(self.room.decorations[1]["chest_trap_disarmed"])
        self.assertFalse(self.room.decorations[2]["trap_disarmed"])
        self.assertTrue(self.room.decorations[0]["trap_revealed"])
        self.assertTrue(self.room.decorations[1]["trap_revealed"])
        trap_meta = S.ARMADILHAS[kind]
        normal_share = max(1, S.trap_xp(S.trap_cr(trap_meta)) // 2)
        chest_share = max(1, S.trap_xp(1.0) // 2)
        expected_xp = (2 * normal_share + 2 * normal_share * 2
                       + chest_share * 2)
        self.assertEqual(self.player["xp"], expected_xp)
        self.assertEqual(self.ally["xp"], expected_xp)

    async def test_bonus_action_already_used_keeps_item_and_traps(self):
        trap = self.trap("still-here", [4, 3])
        self.room.armadilhas = [trap]
        self.player["bonus_action_used"] = True

        await self.room.handle_use_item("h1", "solucao_mecanismo")

        self.assertEqual(len(self.player["bag"]), 1)
        self.assertFalse(self.room.armadilhas[0].get("desativada"))
        self.assertFalse(trap.get("desativada"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
