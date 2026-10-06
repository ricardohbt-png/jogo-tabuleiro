"""Authoritative utility belt storage, routing, movement and transfer tests."""
import asyncio
from copy import deepcopy
import json
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def item(iid):
    return deepcopy(S._DUNGEON_ITEM_CATALOG[iid])


def stack(iid='health_potion', quantity=1):
    return {'item': item(iid), 'quantity': quantity}


class BeltTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.r = S.GameRoom('BELT')
        self.p = S.make_player('p', 'Hero', 'warrior', 0)
        self.r.players['p'] = self.p
        self.p['bag'] = []
        self.p['gear']['item1'] = None
        self.p['gear']['item2'] = None
        self.r.phase = 'playing'
        async def noop(*args, **kwargs): pass
        self.r.send_to = noop
        self.r.broadcast = noop
        self.r.gm_say = noop
        self.r.push_state = noop
        self.r.broadcast_city_state = noop
        self.r._licao_evento = noop

    def require(self, name):
        self.assertTrue(callable(getattr(self.r, name, None)), f'missing belt behavior: {name}')
        return getattr(self.r, name)

    def belt(self, iid='cinto_utilidades', entries=None, slot='item1'):
        b = item(iid)
        if entries is not None: b['utility_belt_slots'] = deepcopy(entries)
        self.p['gear'][slot] = b
        return b

    async def move(self, direction='to_belt', pocket=0, bag=0, **extras):
        handler = self.require('handle_move_utility_belt_item')
        data = dict(direction=direction, gear_slot='item1', pocket_index=pocket, bag_index=bag)
        data.update(extras)
        return await handler('p', data)

    async def rejected(self, **data):
        before = deepcopy(self.p)
        self.assertFalse(await self.move(**data))
        self.assertEqual(self.p, before, 'rejection must be atomic')

    def test_legacy_and_capacity(self):
        normalize = self.require('_normalize_utility_belt')
        for iid, count in [('cinto_utilidades', 4), ('cinto_com_bolsos', 2)]:
            b = item(iid)
            self.assertIs(normalize(b), b)
            self.assertEqual(b['utility_belt_slots'], [None] * count)
        self.assertEqual(self.require('_utility_belt_capacity')({'id': 'backpack'}), 0)
        self.assertFalse(self.require('_is_utility_belt_item')({'effect': 'utility_belt', 'id': 'backpack'}))

    def test_normalization_preserves_metadata_and_clears_invalid(self):
        b = self.belt(entries=[stack(), stack('health_potion'), stack('elixir', True), stack('longsword'), stack('fogo_grego')])
        b['utility_belt_slots'][0]['item']['uses_left'] = 2
        self.require('_normalize_utility_belt')(b)
        self.assertEqual([s and s['quantity'] for s in b['utility_belt_slots']], [1, None, None, None])
        self.assertEqual(b['utility_belt_slots'][0]['item']['uses_left'], 2)
        json.dumps(b)
        for invalid in ['bad', {}, 9, None]:
            b['utility_belt_slots'] = invalid
            self.r._normalize_utility_belt(b)
            self.assertEqual(b['utility_belt_slots'], [None] * 4)

    def test_eligibility_allow_and_deny(self):
        eligible = self.require('_is_utility_belt_eligible')
        for iid in ['health_potion', 'health_potion_concentrated', 'regeneration_potion', 'elixir', 'antidote', 'oleo_dissolvente', 'elixir_depurativo', 'fogo_grego', 'frasco_acido', 'cola_alquimica', 'veneno_aranha_sombria']:
            self.assertTrue(eligible(item(iid)), iid)
        for iid in ['longsword', 'backpack', 'vela_escuridao', 'racao_viagem', 'cinto_utilidades', 'flechas']:
            self.assertFalse(eligible(item(iid)), iid)
        for invalid in [None, [], {}, {'id': 'fake', 'effect': 'heal', 'item_slot': 'bag'}, {'id': 'fake', 'item_type': 'scroll', 'effect': 'throwable'}]:
            self.assertFalse(eligible(invalid))

    def test_custom_potion_eligibility(self):
        custom = S._custom_potion_inventory_dict({'id': 'test_potion', 'name': 'Test', 'emoji': 'x', 'effect': 'heal', 'value': 1, 'price': 1, 'allowed_classes': []})
        self.assertTrue(self.require('_is_utility_belt_eligible')(custom))

    def test_routing_prefers_existing_stack_in_second_belt(self):
        first = self.belt(entries=[None] * 4)
        second = self.belt('cinto_com_bolsos', [stack(quantity=2), None], 'item2')
        self.assertEqual(self.r._route_acquired_item(self.p, item('health_potion')), 'bag')
        self.assertEqual(second['utility_belt_slots'][0]['quantity'], 3)
        self.assertEqual(first['utility_belt_slots'], [None] * 4)
        self.assertEqual(self.p['bag'], [])

    def test_routing_order_and_independent_same_id_stacks(self):
        first = self.belt(entries=[stack(quantity=4), None, None, None])
        second = self.belt('cinto_com_bolsos', [None, None], 'item2')
        self.r._route_acquired_item(self.p, item('health_potion'))
        self.assertEqual(second['utility_belt_slots'][0], stack())
        self.r._route_acquired_item(self.p, item('elixir'))
        self.assertEqual(first['utility_belt_slots'][1], stack('elixir'))
        for _ in range(3): self.r._route_acquired_item(self.p, item('health_potion'))
        self.r._route_acquired_item(self.p, item('health_potion'))
        self.assertEqual([x['id'] for x in self.p['bag']], ['health_potion'])

    def test_no_equipped_belt_and_noneligible_fallback(self):
        self.p['bag'] = [item('cinto_utilidades')]
        self.assertEqual(self.r._route_acquired_item(self.p, item('health_potion')), 'bag')
        self.belt(entries=[None] * 4)
        self.r._route_acquired_item(self.p, item('vela_escuridao'))
        self.assertEqual(self.p['bag'][-1]['id'], 'vela_escuridao')

    async def test_full_bag_pickup_preserves_source(self):
        self.belt(entries=[stack(quantity=4), stack('elixir', 4), stack('fogo_grego', 4), stack('frasco_acido', 4)])
        self.p['bag'] = [item('health_potion')] * 6
        self.r.ground_items['g'] = {'id': 'g', 'pos': list(self.p['pos']), 'item': item('health_potion')}
        before = deepcopy(self.p)
        await self.r.handle_pickup_item('p', 'g')
        self.assertEqual(self.p, before)
        self.assertIn('g', self.r.ground_items)

    async def test_one_unit_each_way_and_stack_limit(self):
        b = self.belt(entries=[None] * 4)
        self.p['bag'] = [item('health_potion') for _ in range(4)]
        for qty in range(1, 5):
            self.assertTrue(await self.move())
            self.assertEqual(b['utility_belt_slots'][0]['quantity'], qty)
            self.assertEqual(len(self.p['bag']), 4 - qty)
        self.p['bag'].append(item('health_potion'))
        await self.rejected()
        self.assertTrue(await self.move(direction='to_bag', bag=1))
        self.assertEqual(b['utility_belt_slots'][0]['quantity'], 3)
        for _ in range(3): self.assertTrue(await self.move(direction='to_bag'))
        self.assertIsNone(b['utility_belt_slots'][0])
        self.assertEqual(len(self.p['bag']), 5)

    async def test_single_swap_preserves_full_item(self):
        b = self.belt(entries=[stack('health_potion_concentrated'), None, None, None])
        b['utility_belt_slots'][0]['item']['uses_left'] = 2
        self.p['bag'] = [item('elixir')]
        self.assertTrue(await self.move())
        self.assertEqual(b['utility_belt_slots'][0], stack('elixir'))
        self.assertEqual(self.p['bag'][0]['uses_left'], 2)

    async def test_reject_multi_swap_and_duplicate(self):
        self.belt(entries=[stack(quantity=2), stack('elixir'), None, None])
        self.p['bag'] = [item('fogo_grego')]
        await self.rejected()
        self.p['bag'] = [item('elixir')]
        await self.rejected(pocket=2)
        self.p['gear']['item1']['utility_belt_slots'][0]['quantity'] = 1
        await self.rejected()

    async def test_full_bag_and_invalid_indices_are_atomic(self):
        self.belt(entries=[stack(), None, None, None])
        self.p['bag'] = [item('health_potion')] * 6
        await self.rejected(direction='to_bag')
        for data in [{'pocket': -1}, {'pocket': 4}, {'pocket': True}, {'pocket': '0'}, {'bag': -1}, {'bag': 6}, {'bag': False}, {'bag': '0'}, {'direction': 'other'}, {'gear_slot': 'weapon'}, {'quantity': 2}, {'quantity': True}]:
            await self.rejected(**data)
        self.p['gear']['item1']['utility_belt_slots'][0]['quantity'] = '1'
        await self.rejected(direction='to_bag')
        self.p['gear']['item1']['utility_belt_slots'][0]['quantity'] = 5
        await self.rejected(direction='to_bag')
        self.p['gear']['item1']['utility_belt_slots'] = 'bad'
        await self.rejected()

    def test_malformed_poison_identifiers_normalize_to_empty(self):
        for poison_id in ([], {}):
            with self.subTest(poison_id=poison_id):
                invalid = {'id': 'invalid_poison_vial', 'item_slot': 'bag',
                           'effect': 'coat_poison', 'veneno_id': poison_id}
                b = self.belt(entries=[{'item': invalid, 'quantity': 1}, stack(), None, None])
                self.r._normalize_utility_belt(b)
                self.assertEqual(b['utility_belt_slots'], [None, stack(), None, None])
                self.assertFalse(self.r._is_utility_belt_eligible(invalid))

    async def test_malformed_poison_identifiers_reject_movement_atomically(self):
        for poison_id in ([], {}):
            with self.subTest(poison_id=poison_id):
                invalid = {'id': 'invalid_poison_vial', 'item_slot': 'bag',
                           'effect': 'coat_poison', 'veneno_id': poison_id}
                self.belt(entries=[None] * 4)
                self.p['bag'] = [invalid]
                await self.rejected()
                self.belt(entries=[{'item': invalid, 'quantity': 1}, None, None, None])
                self.p['bag'] = []
                await self.rejected(direction='to_bag')

    async def test_malformed_belt_identifier_is_rejected(self):
        self.p['gear']['item1'] = {'id': [], 'utility_belt_slots': [None] * 4}
        self.p['bag'] = [item('health_potion')]
        await self.rejected()

    async def test_legacy_manual_fill_and_unequipped_rejection(self):
        b = self.belt()
        self.p['bag'] = [item('health_potion')]
        self.assertTrue(await self.move())
        self.assertEqual(b['utility_belt_slots'], [stack(), None, None, None])
        self.p['gear']['item1'] = None
        await self.rejected(direction='to_bag')

    async def test_equipping_and_unequipping_preserve_contents(self):
        b = item('cinto_com_bolsos')
        self.p['bag'] = [b]
        await self.r.handle_equip_from_bag('p', 0)
        self.assertEqual(b.get('utility_belt_slots'), [None, None])
        b['utility_belt_slots'][0] = stack(quantity=3)
        await self.r.handle_unequip('p', 'item1')
        self.assertEqual(self.p['bag'][0]['utility_belt_slots'], [stack(quantity=3), None])
        await self.r.handle_quick_equip_from_bag('p', 0)
        self.assertEqual(self.p['gear']['item1']['utility_belt_slots'][0]['quantity'], 3)

    async def test_drop_and_pickup_whole_belt(self):
        b = self.belt(entries=[stack(quantity=3), None, None, None])
        self.r._free_drop_tile_near = lambda pos: list(pos)
        await self.r.handle_drop_item('p', 'gear', slot_key='item1')
        gid = next(iter(self.r.ground_items))
        self.assertEqual(self.r.ground_items[gid]['item'], b)
        await self.r.handle_pickup_item('p', gid)
        self.assertEqual(self.p['bag'][0], b)

    async def test_chest_and_decor_transfer_whole_belt(self):
        b = item('cinto_com_bolsos')
        b['utility_belt_slots'] = [stack(quantity=3), None]
        b['instance_tag'] = 'whole-object'
        self.r.chests['c'] = {'id': 'c', 'pos': list(self.p['pos']), 'gold': 0, 'items': [deepcopy(b)]}
        await self.r.handle_take_from_chest('p', 'c', 'item', 0)
        self.assertEqual(self.p['bag'][0], b)
        self.assertNotIn('c', self.r.chests)
        decor = {'id': 'd', 'loot': {'gold': 0, 'items': [deepcopy(b)]}}
        self.r._decor_by_id = lambda iid: decor if iid == 'd' else None
        self.r._adjacente_a_decor = lambda pos, d: True
        await self.r.handle_take_from_decor('p', 'd', 'item', 0)
        self.assertEqual(self.p['bag'][1], b)
        self.assertEqual(decor['loot']['items'], [])

    async def test_preloaded_monster_loot_preserves_belt_slots(self):
        source = {'tipo': 'item', 'id': 'cinto_com_bolsos', 'utility_belt_slots': [stack(quantity=3), None]}
        monster = {'id': 'm', 'name': 'Test', 'hp': 0, 'pos': list(self.p['pos']), 'type': 'skeleton', 'undead': True, 'xp': 0, 'loot_table': {'1-100': source}}
        self.r.monsters['m'] = monster
        await self.r._monster_dies(monster, 'p')
        chest = next(iter(self.r.chests.values()))
        self.assertEqual(chest['items'][0].get('utility_belt_slots'), source['utility_belt_slots'])

    def test_authored_chest_hydration_preserves_belt_slots(self):
        source = {'id': 'cinto_com_bolsos', 'instance_tag': 'preloaded', 'utility_belt_slots': [stack(quantity=3), None]}
        hydrated = S.hidratar_itens_bau([source])[0]
        self.assertEqual(hydrated.get('instance_tag'), 'preloaded')
        self.assertEqual(hydrated.get('utility_belt_slots'), source['utility_belt_slots'])
        source['utility_belt_slots'][0]['quantity'] = 1
        self.assertEqual(hydrated['utility_belt_slots'][0]['quantity'], 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
