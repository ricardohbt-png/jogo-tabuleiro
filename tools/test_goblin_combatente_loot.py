"""Real death loot and potion/attack lifecycle; run from repository root."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from test_goblin_combatente_equipamento import WEAPONS, spawn


def room():
    r = S.GameRoom("GOBLIN_LOOT_TEST")
    async def noop(*args, **kwargs):
        pass
    # Only transport/narration is disconnected; combat and death are real.
    r.gm_say = r.broadcast = r.push_state = r.send_to = noop
    r.phase = "playing"
    r.map_w = r.map_h = 10
    r.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    return r


def target(r):
    p = S.make_player("p1", "Target", "warrior", 0)
    p.update(pos=[3, 4], hp=100, max_hp=100)
    r.players[p["id"]] = p
    return p


async def kill(r, m, loot_roll=1):
    r.monsters[m["id"]] = m
    m["hp"] = 0
    with patch.object(S.random, "randint", return_value=loot_roll):
        await r._monster_dies(m, None)
    return next(iter(r.chests.values()))


class CombatantLootTests(unittest.IsolatedAsyncioTestCase):
    async def test_each_weapon_optional_shield_and_unused_potion_drop_without_dagger(self):
        for index, (weapon_id, *_rest) in enumerate(WEAPONS):
            for shield in (False, True):
                for potion in (False, True):
                    with self.subTest(weapon=weapon_id, shield=shield, potion=potion):
                        r = room()
                        m = spawn(index, 0 if shield else 0.99, 0 if potion else 0.99)
                        chest = await kill(r, m)
                        expected = [weapon_id] + (["escudo_p"] if shield else [])
                        expected += ["health_potion_small"] if potion else []
                        self.assertCountEqual([it["id"] for it in chest["items"]], expected)
                        self.assertEqual(chest["gold"], 0)
                        self.assertNotIn("dagger", [it["id"] for it in chest["items"]])

    async def test_potion_instance_metadata_and_independent_gold_drops_survive_death(self):
        r = room()
        m = spawn(potion_roll=0)
        m["equipment_consumables"][0]["uses_left"] = 1
        m["equipment_consumables"][0]["instance_note"] = "carried"
        m["loot_drops"] = [{"kind": "gold", "chance": 100, "amount": 3}]
        chest = await kill(r, m, 50)
        self.assertEqual(chest["gold"], 5)  # Native roll 50: 2 gold; editor: 3 gold.
        potions = [it for it in chest["items"] if it["id"] == "health_potion_small"]
        self.assertEqual(len(potions), 1)
        self.assertEqual(potions[0]["uses_left"], 1)
        self.assertEqual(potions[0]["instance_note"], "carried")
        potions[0]["uses_left"] = 0
        self.assertEqual(m["equipment_consumables"][0]["uses_left"], 1)

    async def test_threshold_heal_consumes_potion_and_real_attack_continues(self):
        for hp, expected_hp, remaining in ((11, 11, True), (10, 15, False), (9, 14, False)):
            with self.subTest(hp=hp):
                r = room()
                m = spawn(potion_roll=0)
                m.update(pos=[3, 3], hp=hp, max_hp=20)
                r.monsters[m["id"]] = m
                p = target(r)
                with patch.object(S.random, "randint", side_effect=lambda a, b: 19 if b == 20 else 1):
                    await r._monster_execute_attacks(m, {"kind": "player", "obj": p})
                self.assertEqual(m["hp"], expected_hp)
                self.assertEqual(p["hp"], 99)  # Noncritical hit, 1d6=1.
                self.assertEqual(bool(m["equipment_consumables"]), remaining)
                chest = await kill(r, m)
                expected = ["lanca_curta"] + (["health_potion_small"] if remaining else [])
                self.assertCountEqual([it["id"] for it in chest["items"]], expected)

    async def test_dual_dagger_loot_and_successful_throw_are_preserved(self):
        definition = next(d for d in S.MONSTER_DEFS if d["type"] == "goblin_dual")
        r = room()
        m = S.make_monster(definition, {"id": 0, "cx": 3, "cy": 3})
        m["pos"] = [3, 3]
        r.monsters[m["id"]] = m
        p = target(r)
        self.assertIn("arremesso", [ability["id"] for ability in m["special_abilities"]])
        with patch.object(S.random, "randint", side_effect=lambda a, b: 20 if b == 20 else 1):
            await r._goblin_arremesso(m, [{"kind": "player", "obj": p}])
        self.assertEqual(p["hp"], 97)
        self.assertTrue(m["pode_arremessar"])
        chest = await kill(r, m)
        self.assertCountEqual([it["id"] for it in chest["items"]], ["shortsword", "dagger"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
