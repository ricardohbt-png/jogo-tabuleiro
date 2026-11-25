"""Equipamento, bônus por mão e destruição da adaga do Goblin Dual."""
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S


def equip(main, off, armor=None, magic=False):
    m = deepcopy(next(d for d in S.MONSTER_DEFS if d['type'] == 'goblin_dual'))
    m['max_hp'] = m['hp']
    with patch.object(S.random, 'choices', side_effect=[[main], [off], [armor]]):
        S._configurar_goblin_dual_spawn(m)
    with patch.object(S.random, 'random', return_value=0 if magic else 1):
        S._finalizar_goblin_dual_armas(m)
    S._aplicar_equipamentos_monstro(m)
    S._configurar_goblin_dual_ataques(m)
    return m


class EquipmentTests(unittest.TestCase):
    def test_two_hands_have_separate_bonuses(self):
        m = equip('sword', 'dagger_aco_damasco')
        self.assertEqual([a['atk_bonus'] for a in m['attacks']], [2, 5])
        self.assertEqual([a['damage_bonus'] for a in m['attacks']], [2, 0])
        self.assertFalse(m.get('equipment_attack_bonus'))
        self.assertFalse(m.get('equipment_damage_bonus'))

    def test_magic_stacks_with_material(self):
        m = equip('sword_obsidiana_ferro', 'dagger_aco_damasco', magic=True)
        self.assertEqual([a['atk_bonus'] for a in m['attacks']], [3, 6])
        self.assertEqual([a['damage_bonus'] for a in m['attacks']], [4, 1])
        self.assertTrue(all(a['magical'] for a in m['attacks']))

    def test_whip_disables_throw_and_armor_adds_ac(self):
        for armor in ('leather', 'chainmail'):
            m = equip('bordao', 'chicote', armor)
            self.assertFalse(m['pode_arremessar'])
            self.assertEqual(len(m['attacks']), 2)
            self.assertNotIn('arremesso', [a['id'] for a in m['special_abilities']])
            item = S._DUNGEON_ITEM_CATALOG[armor]
            self.assertEqual(m['ac'], 13 + item['ac_bonus'])

    def test_nat_one_removes_actual_magic_dagger_from_loot_and_attacks(self):
        m = equip('sword', 'dagger_obsidiana_ferro', magic=True)
        r = S.GameRoom('TEST')
        r.broadcast = AsyncMock()
        r.gm_say = AsyncMock()
        with patch.object(S.random, 'randint', return_value=1):
            asyncio.run(r._goblin_arremesso_em(m, {'kind': 'player', 'obj': {}}))
        self.assertEqual(m['equipped_items'], ['sword_magica'])
        self.assertEqual(len(m['attacks']), 1)
        self.assertFalse(m['pode_arremessar'])
        self.assertTrue(m['equipment_items'][1]['corrosion_destroyed'])
        self.assertEqual(m['guaranteed_loot'], [])

    def test_full_spawn_keeps_both_attacks_and_equipment(self):
        md = next(d for d in S.MONSTER_DEFS if d['type'] == 'goblin_dual')
        for _ in range(50):
            m = S.make_monster(md, {'id': 1, 'cx': 4, 'cy': 4})
            self.assertEqual(len(m['attacks']), 2)
            self.assertEqual([a['equipment_weapon_id'] for a in m['attacks']],
                             m['equipped_items'][:2])
            self.assertEqual(m['pode_arremessar'], m['goblin_dual_off_base'] == 'dagger')


if __name__ == '__main__':
    unittest.main()
