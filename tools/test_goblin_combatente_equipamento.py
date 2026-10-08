"""Run from repository root: python -X utf8 tools/test_goblin_combatente_equipamento.py."""
import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


WEAPONS = (
    ("lanca_curta", "Lança Curta", "perfurante", None),
    ("bordao", "Bordão", "contundente", None),
    ("cajado_madeira", "Cajado de Madeira", "contundente", "cajado"),
    ("shortsword", "Espada Curta", "cortante", None),
    ("maca", "Maça", "contundente", None),
    ("machado_basico", "Machado de Ferro", "cortante", None),
)


def spawn(index=0, shield_roll=0.9, potion_roll=0.9):
    definition = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin_combatente")
    # Select each position of the real equally weighted choice population.
    with patch.object(S.random, "choice", side_effect=lambda population: population[index]), \
            patch.object(S.random, "random", side_effect=[shield_roll, potion_roll]):
        return S.make_monster(definition, {"id": 0, "cx": 3, "cy": 3})


class CombatantEquipmentTests(unittest.TestCase):
    def test_all_six_uniform_choices_build_catalog_melee_attacks_with_plus_two(self):
        for index, (item_id, name, category, reach) in enumerate(WEAPONS):
            with self.subTest(weapon=item_id):
                m = spawn(index)
                self.assertEqual(m.get("combatant_weapon_id"), item_id)
                self.assertEqual(m.get("equipped_items"), [item_id])
                self.assertEqual(len(m["attacks"]), 1)
                attack = m["attacks"][0]
                self.assertEqual((attack["name"], attack["damage"], attack["atk_bonus"]),
                                 (name, "1d6", 2))
                self.assertEqual(attack.get("categoria"), category)
                self.assertEqual(attack.get("reach"), reach)
                self.assertIsNone(attack.get("range"))
                self.assertEqual(attack["damage_types"], ["physical"])
                self.assertEqual(attack["num_attacks"], 1)

    def test_independent_shield_and_potion_rolls_for_every_weapon(self):
        for index, (item_id, *_rest) in enumerate(WEAPONS):
            for shield, potion in ((False, False), (True, False), (False, True), (True, True)):
                with self.subTest(weapon=item_id, shield=shield, potion=potion):
                    m = spawn(index, 0.0 if shield else 0.99, 0.0 if potion else 0.99)
                    self.assertEqual(m.get("equipped_items"), [item_id] + (["escudo_p"] if shield else []))
                    self.assertEqual(m.get("combatant_shield_id"), "escudo_p" if shield else None)
                    self.assertEqual(m["ac"], 14 if shield else 13)
                    self.assertEqual([i["id"] for i in m.get("equipment_consumables", [])],
                                     ["health_potion_small"] if potion else [])

    def test_shield_probability_boundary(self):
        for roll, expected in ((0.099999, True), (0.10, False)):
            with self.subTest(roll=roll):
                m = spawn(shield_roll=roll)
                self.assertEqual(m["ac"], 14 if expected else 13)

    def test_potion_probability_boundary(self):
        for roll, expected in ((0.049999, True), (0.05, False)):
            with self.subTest(roll=roll):
                m = spawn(potion_roll=roll)
                self.assertEqual([i["id"] for i in m.get("equipment_consumables", [])],
                                 ["health_potion_small"] if expected else [])

    def test_combatant_has_no_dagger_or_throwing_ability(self):
        m = spawn()
        self.assertFalse(m.get("pode_arremessar"))
        self.assertNotIn("arremesso", [a["id"] for a in m["special_abilities"]])
        self.assertNotIn("dagger", m.get("guaranteed_loot", []))

    def test_weapon_hero_critical_properties_do_not_enter_monster_attack(self):
        for index in (1, 3, 4):
            with self.subTest(index=index):
                attack = spawn(index)["attacks"][0]
                for key in ("crit_min_nat_roll", "crit_nat20_multiplier", "crit_nat20_stuns", "granted_ability"):
                    self.assertNotIn(key, attack)

    def test_inventory_instances_do_not_share_mutable_catalog_items(self):
        first, second = spawn(potion_roll=0), spawn(potion_roll=0)
        self.assertTrue(first.get("equipment_consumables"))
        before = deepcopy(S._DUNGEON_ITEM_CATALOG["health_potion_small"])
        first["equipment_consumables"][0]["value"] = -1
        self.assertEqual(second["equipment_consumables"][0], before)
        self.assertEqual(S._DUNGEON_ITEM_CATALOG["health_potion_small"], before)

    def test_dual_preserves_dagger_throw_and_both_original_attacks(self):
        definition = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin_dual")
        m = S.make_monster(definition, {"id": 0, "cx": 3, "cy": 3})
        self.assertTrue(m["pode_arremessar"])
        self.assertIn("arremesso", [a["id"] for a in m["special_abilities"]])
        self.assertIn("dagger", m["guaranteed_loot"])
        self.assertEqual([(a["name"], a["damage"], a["atk_bonus"]) for a in m["attacks"]],
                         [("Espada Curta", "1d6", 2), ("Adaga", "1d4+2", 4)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
