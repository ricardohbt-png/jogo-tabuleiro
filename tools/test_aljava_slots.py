import os
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


class AljavaSlots(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom('QUIVER')
        self.player = S.make_player('p', 'Hero', 'warrior', 0)
        self.room.players['p'] = self.player
        self.room.phase = 'playing'
        self.player['bag'] = []
        async def noop(*args, **kwargs): pass
        self.room.push_state_or_city = noop
        self.room.gm_say = noop
        self.room.send_to = noop

    def item(self, iid, count=None):
        item = deepcopy(S._DUNGEON_ITEM_CATALOG[iid])
        if count is not None:
            item['ammo_count'] = count
        return item

    def test_capacities_and_normal_bag_limit(self):
        for iid, capacity in [('mini_aljava', 1), ('aljava_pequena', 2), ('aljava_grande', 3)]:
            q = self.item(iid)
            self.assertEqual(self.room._quiver_capacity(q), capacity)
            self.player['gear']['item1'] = q
            self.assertEqual(S._max_ammo_stack_for(self.player, self.item('flechas')), 10)

    async def test_move_and_preserve_legacy_stack(self):
        q = self.item('mini_aljava')
        self.player['gear']['item1'] = q
        self.player['bag'] = [self.item('flechas', 45)]
        data = {'direction': 'to_quiver', 'gear_slot': 'item1', 'slot_index': 0, 'bag_index': 0}
        self.assertTrue(await self.room.handle_move_quiver_ammo('p', data))
        self.assertEqual(q['quiver_slots'][0]['ammo_count'], 40)
        self.assertEqual(self.player['bag'][0]['ammo_count'], 5)
        data['direction'] = 'to_bag'
        self.assertTrue(await self.room.handle_move_quiver_ammo('p', data))
        self.assertEqual(self.player['bag'][0]['ammo_count'], 20)
        self.assertEqual(q['quiver_slots'][0]['ammo_count'], 25)

    async def test_reject_non_ammo_and_incompatible_stacks(self):
        q = self.item('mini_aljava')
        self.player['gear']['item1'] = q
        self.player['bag'] = [self.item('health_potion')]
        data = {'direction': 'to_quiver', 'gear_slot': 'item1', 'slot_index': 0, 'bag_index': 0}
        before = deepcopy(self.player)
        self.assertFalse(await self.room.handle_move_quiver_ammo('p', data))
        self.assertEqual(self.player, before)
        q['quiver_slots'] = [self.item('flechas', 10)]
        self.player['bag'] = [self.item('virotes', 10)]
        before = deepcopy(self.player)
        self.assertFalse(await self.room.handle_move_quiver_ammo('p', data))
        self.assertEqual(self.player, before)

    def test_equipped_quiver_ammo_selection_and_depletion(self):
        q = self.item('aljava_pequena')
        q['quiver_slots'] = [self.item('flechas_prata', 1), self.item('flechas', 2)]
        self.player['gear']['off_hand'] = q
        source = self.room._quiver_ammo_sources(self.player, ['flechas', 'flechas_prata'])
        self.assertEqual([s[2]['ammo_type'] for s in source], ['flechas_prata', 'flechas'])
        self.room._consume_quiver_ammo(source[0])
        self.assertIsNone(q['quiver_slots'][0])
        self.assertEqual(q['quiver_slots'][1]['ammo_count'], 2)

    async def test_unequip_and_reequip_retains_contents(self):
        q = self.item('mini_aljava')
        q['quiver_slots'] = [self.item('flechas_prata', 35)]
        self.player['gear']['item1'] = q
        await self.room.handle_unequip('p', 'item1')
        self.assertEqual(self.player['bag'][0]['quiver_slots'][0]['ammo_count'], 35)
        self.assertEqual(self.room._quiver_ammo_sources(self.player, ['flechas_prata']), [])
        await self.room.handle_equip_from_bag('p', 0)
        equipped = self.player['gear']['item1'] or self.player['gear']['item2']
        self.assertEqual(equipped['quiver_slots'][0]['ammo_count'], 35)
        self.assertEqual(len(self.room._quiver_ammo_sources(self.player, ['flechas_prata'])), 1)


if __name__ == '__main__':
    unittest.main()
