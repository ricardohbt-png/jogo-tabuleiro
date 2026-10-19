import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S


class ArremessoRapidoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("ARREMESSO_RAPIDO_TEST")
        self.room.phase = "playing"
        self.room.round_num = 1
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.errors = []

        async def noop(*args, **kwargs):
            pass

        async def capture(pid, message, *args, **kwargs):
            if isinstance(message, dict) and message.get("type") == "error":
                self.errors.append(message.get("msg"))

        self.room.push_state = self.room.broadcast_city_state = noop
        self.room.broadcast = self.room.gm_say = noop
        self.room.send_to = capture
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *args: True
        self.room._apply_damage_types = lambda damage, *args, **kwargs: damage
        self.room._save_mostrado = self._save
        self.player = S.make_player("h", "Aventureiro", "warrior", 0)
        self.player.update(pos=[3, 3], dex=16, atk_bonus=10, action_done=False,
                           bonus_action_used=False, gold=500, fome=60, sede=60)
        self.player["bag"] = []
        self.room.players["h"] = self.player
        for mid, pos in (("m1", [5, 3]), ("m2", [6, 6])):
            self.room.monsters[mid] = {
                "id": mid, "type": "urso_negro", "name": mid,
                "pos": pos, "hp": 40, "max_hp": 40, "ac": 10,
                "alive": True,
            }

    async def _save(self, *args, **kwargs):
        return False, 1, 0, 1

    def add_item(self, item_id):
        item = deepcopy(next(x for x in S.SHOP_MERCHANT if x["id"] == item_id))
        self.player["bag"].append(item)
        return item

    async def throw(self, item_id, target="m1"):
        with patch.object(S.random, "randint", return_value=10), \
                patch.object(S, "roll_dice", return_value=1):
            if target == "area":
                await self.room.handle_throw_item("h", {"item_id": item_id, "tx": 6, "ty": 6})
            else:
                await self.room.handle_throw_item("h", {"item_id": item_id, "target_id": target})

    async def test_catalog_is_universal_passive_and_costs_250(self):
        entry = S.GUILD_CATALOG.get("arremesso_rapido")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["categoria"], "especializacao")
        self.assertIsNone(entry["classe"])
        self.assertEqual(entry["preco"], 250)
        self.assertIn("passivo", entry["desc"].lower())
        self.assertIn("ação bônus", entry["desc"].lower())
        old_dir = S.GUILD_SAVE_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp:
                S.GUILD_SAVE_DIR = tmp
                async def noop(*args, **kwargs):
                    pass
                for index, cls in enumerate(("warrior", "mage", "cleric", "rogue", "bard", "paladin")):
                    room = S.GameRoom(f"BUY_ARREMESSO_RAPIDO_{cls}")
                    room.phase = "city"
                    room.push_state_or_city = room.broadcast_city_state = room.push_state = room.gm_say = noop
                    p = S.make_player(f"buy{index}", cls, cls, 0)
                    p["gold"] = 250
                    room.players[p["id"]] = p
                    await room.handle_guild_buy(p["id"], "arremesso_rapido")
                    self.assertIn("arremesso_rapido", p["guild_owned"]["especializacoes"], cls)
                    self.assertEqual(p["gold"], 0, cls)
        finally:
            S.GUILD_SAVE_DIR = old_dir

    async def test_second_throw_uses_bonus_action_and_keeps_normal_area_resolution(self):
        self.player["guild_owned"]["especializacoes"].append("arremesso_rapido")
        acid = self.add_item("frasco_acido")
        grenade = self.add_item("granada")

        await self.throw("frasco_acido", target="m1")
        self.assertTrue(self.player["action_done"])
        self.assertFalse(self.player["bonus_action_used"])
        self.assertNotIn(acid, self.player["bag"])
        self.assertEqual(self.player["fome"], 59)

        await self.room.handle_throw_item("h", {"item_id": "granada", "tx": 99, "ty": 99})
        self.assertIn(grenade, self.player["bag"])
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player.get("arremesso_rapido_usados"), 1)

        await self.throw("granada", target="area")
        self.assertTrue(self.player["bonus_action_used"])
        self.assertNotIn(grenade, self.player["bag"])
        self.assertEqual(self.player["fome"], 58)
        self.assertEqual(self.player["sede"], 59)
        self.assertEqual(self.player.get("arremesso_rapido_usados"), 2)
        self.assertEqual(self.player.get("arremesso_rapido_rodada"), 1)
        player_state = next(x for x in self.room._game_state_payload()["players"] if x["id"] == "h")
        self.assertEqual(player_state["arremesso_rapido_usados"], 2)
        self.assertEqual(player_state["arremesso_rapido_rodada"], 1)

    async def test_cannot_throw_more_than_two_with_talent(self):
        self.player["guild_owned"]["especializacoes"].append("arremesso_rapido")
        self.add_item("frasco_acido")
        self.add_item("frasco_acido")
        self.add_item("frasco_acido")
        await self.throw("frasco_acido", target="m1")
        await self.throw("frasco_acido", target="m2")
        await self.throw("frasco_acido", target="m1")
        self.assertEqual(len(self.player["bag"]), 1)
        self.assertEqual(self.player.get("arremesso_rapido_usados"), 2)

    async def test_without_talent_second_throw_stays_blocked_and_keeps_item(self):
        self.add_item("frasco_acido")
        self.add_item("frasco_acido")
        await self.throw("frasco_acido", target="m1")
        await self.throw("frasco_acido", target="m2")
        self.assertEqual(len(self.player["bag"]), 1)
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player.get("arremesso_rapido_usados", 0), 0)

    async def test_preused_bonus_action_blocks_second_throw_without_consuming_item(self):
        self.player["guild_owned"]["especializacoes"].append("arremesso_rapido")
        self.add_item("frasco_acido")
        self.add_item("frasco_acido")
        await self.throw("frasco_acido", target="m1")
        self.player["bonus_action_used"] = True
        await self.throw("frasco_acido", target="m2")
        self.assertEqual(len(self.player["bag"]), 1)
        self.assertEqual(self.player.get("arremesso_rapido_usados"), 1)


if __name__ == "__main__":
    unittest.main()
