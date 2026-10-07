"""Regressions for the final utility belt review: bottle state and stale actions."""
from copy import deepcopy
import json
from itertools import product
import tempfile
import unittest
from unittest.mock import patch

import test_cinto_utilidades as storage
from test_cinto_utilidades import item, stack
import test_cinto_utilidades_uso as actions


class BottleConservationTests(unittest.IsolatedAsyncioTestCase):
    setUp = storage.BeltTests.setUp
    belt = storage.BeltTests.belt
    move = storage.BeltTests.move
    require = storage.BeltTests.require

    async def test_extract_partial_head_leaves_full_reserve(self):
        belt = self.belt(entries=[stack('health_potion_concentrated', 2), None, None, None])
        belt['utility_belt_slots'][0]['item']['uses_left'] = 1
        await self.move(direction='to_bag')
        await self.move(direction='to_bag')
        self.assertEqual([b['uses_left'] for b in self.p['bag']], [3, 1])
        self.assertEqual(sum(b['uses_left'] for b in self.p['bag']), 4)
        self.assertIsNone(belt['utility_belt_slots'][0])

    async def test_manual_merge_preserves_each_bottle(self):
        for head, incoming in [(3, 3), (3, 1), (1, 3), (1, 2)]:
            with self.subTest(head=head, incoming=incoming):
                self.setUp()
                self.belt(entries=[stack('health_potion_concentrated'), None, None, None])['utility_belt_slots'][0]['item']['uses_left'] = head
                bottle = item('health_potion_concentrated')
                bottle['uses_left'] = incoming
                self.p['bag'] = [bottle]
                self.assertTrue(await self.move())
                self.assertEqual(self.p['bag'], [])
                await self.move(direction='to_bag', bag=0)
                await self.move(direction='to_bag', bag=1)
                self.assertEqual([b['uses_left'] for b in self.p['bag']], [head, incoming])

    async def test_automatic_acquisition_preserves_each_bottle_and_reload(self):
        for head, incoming in [(3, 3), (3, 1), (1, 3), (1, 2)]:
            with self.subTest(head=head, incoming=incoming):
                self.setUp()
                belt = self.belt(entries=[stack('health_potion_concentrated'), None, None, None])
                belt['utility_belt_slots'][0]['item']['uses_left'] = head
                bottle = item('health_potion_concentrated')
                bottle['uses_left'] = incoming
                self.assertEqual(self.r._route_acquired_item(self.p, bottle), 'bag')
                # Normalize a saved copy as equip/load does before extracting it.
                self.p['gear']['item1'] = self.r._normalize_utility_belt(deepcopy(belt))
                await self.move(direction='to_bag', bag=0)
                await self.move(direction='to_bag', bag=1)
                self.assertEqual([b['uses_left'] for b in self.p['bag']], [head, incoming])

    async def test_loaded_replacement_warns_once_normal_and_quick(self):
        models = [('cinto_utilidades', 4, 'Utility Belt', 'Cinto de Utilidades'),
                  ('cinto_com_bolsos', 2, 'Pocket Belt', 'Cinto com Bolsos')]
        for method, (model, capacity, en_name, pt_name), lang, loaded in product(
                ('handle_equip_from_bag', 'handle_quick_equip_from_bag'), models, ('pt', 'en'), (True, False)):
            with self.subTest(method=method, model=model, lang=lang, loaded=loaded):
                self.setUp()
                belt = self.belt(model, [stack() if loaded else None] + [None] * (capacity - 1))
                self.belt('cinto_com_bolsos', [None, None], 'item2')
                self.p['bag'] = [item('cinto_com_bolsos')]
                notices = []
                async def narration(message):
                    notices.append(storage.S._t_render(message, lang))
                self.r.gm_say = narration
                await getattr(self.r, method)('p', 0)
                self.assertIn(belt, self.p['bag'])
                warnings = [m for m in notices if ('inaccessible' if lang == 'en' else 'inacessíveis') in m]
                self.assertEqual(len(warnings), 1 if loaded else 0)
                if loaded: self.assertIn(en_name if lang == 'en' else pt_name, warnings[0])

    async def test_partial_reserves_survive_whole_belt_transfer_and_disk_save(self):
        S = storage.S
        belt = self.belt(entries=[stack('health_potion_concentrated'), None, None, None])
        belt['utility_belt_slots'][0]['item']['uses_left'] = 1
        incoming = item('health_potion_concentrated')
        incoming.update(uses_left=2, instance_tag='second-bottle')
        self.r._route_acquired_item(self.p, incoming)
        expected = deepcopy(belt['utility_belt_slots'])
        await self.r.handle_unequip('p', 'item1')
        self.r.phase = 'city'
        with (tempfile.TemporaryDirectory() as root,
              patch.object(S, 'LOJA', S.LojaDocumentos(S.AdaptadorArquivo(root))),
              patch.object(S, '_agendar_descarga', lambda: None)):
            S.LOJA.carregar()
            self.r.savegame = S.create_savegame('Partial bottles', 'belt_tester', 'procedural', None, False)
            self.r._checkpoint_savegame()
            sid = self.r.savegame['id']
            S.LOJA.descarregar()
            S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(root))
            S.LOJA.carregar()
            restored = S.make_player('p', 'Restored', 'warrior', 0)
            S.restore_character(restored, S.load_savegame(sid)['characters']['warrior'])
            self.r.players['p'] = self.p = restored
        await self.r.handle_equip_from_bag('p', 0)
        self.assertEqual(self.p['gear']['item1']['utility_belt_slots'], expected)
        self.r.phase = 'playing'
        self.r._free_drop_tile_near = lambda pos: list(pos)
        await self.r.handle_drop_item('p', 'gear', slot_key='item1')
        ground_id = next(iter(self.r.ground_items))
        self.assertEqual(self.r.ground_items[ground_id]['item']['utility_belt_slots'], expected)
        await self.r.handle_pickup_item('p', ground_id)
        await self.r.handle_equip_from_bag('p', 0)
        await self.move(direction='to_bag', bag=0)
        await self.move(direction='to_bag', bag=1)
        self.assertEqual([b['uses_left'] for b in self.p['bag']], [1, 2])
        self.assertEqual(self.p['bag'][1]['instance_tag'], 'second-bottle')

    async def test_malformed_reserves_reject_movement_atomically(self):
        for reserves in (None, {}, [], [item('elixir')]):
            with self.subTest(reserves=reserves):
                self.setUp()
                belt = self.belt(entries=[stack('health_potion_concentrated', 2), None, None, None])
                belt['utility_belt_slots'][0]['remaining_items'] = reserves
                before = deepcopy(self.p)
                self.assertFalse(await self.move(direction='to_bag'))
                self.assertEqual(self.p, before)

    def test_legacy_equipped_tokens_are_published_stably_in_both_states(self):
        for method in ('_city_state_payload', '_game_state_payload'):
            with self.subTest(method=method):
                self.setUp()
                first = self.belt()
                second = self.belt('cinto_com_bolsos', slot='item2')
                payload = getattr(self.r, method)()
                published = payload['players'][0]['gear']
                tokens = [published[key]['utility_belt_token'] for key in ('item1', 'item2')]
                self.assertTrue(all(isinstance(token, str) and token for token in tokens))
                self.assertNotEqual(*tokens)
                self.assertEqual(first['utility_belt_slots'], [None] * 4)
                self.assertEqual(second['utility_belt_slots'], [None] * 2)
                again = getattr(self.r, method)()['players'][0]['gear']
                self.assertEqual([again[key]['utility_belt_token'] for key in ('item1', 'item2')], tokens)
                json.dumps(payload, default=lambda value: storage.S._t_render(value, 'en'))


class StaleInstanceTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispatch = staticmethod(actions.use_dispatch())

    setUp = actions.BeltActionTests.setUp
    belt = actions.BeltActionTests.belt
    use = actions.BeltActionTests.use
    throw = actions.BeltActionTests.throw

    async def test_same_consumable_replacement_before_dispatch_rejects_all_actions(self):
        for action, iid in [('use', 'health_potion'), ('target', 'frasco_oleo'), ('area', 'bomba_incendiaria')]:
            with self.subTest(action=action):
                self.setUp()
                old = self.belt(iid)
                old['utility_belt_token'] = 'belt-A'
                replacement = self.belt(iid)
                replacement['utility_belt_token'] = 'belt-B'
                self.p['bag'] = [item(iid)]
                before = deepcopy(self.p)
                if action == 'use':
                    await self.dispatch(self.r, 'p1', dict(item_id=iid, source='utility_belt', gear_slot='item1', pocket_index=0, belt_token='belt-A'))
                else:
                    data = dict(item_id=iid, source='utility_belt', gear_slot='item1', pocket_index=0, belt_token='belt-A')
                    data.update(tx=4, ty=1) if action == 'area' else data.update(target_id='m1')
                    await self.r.handle_throw_item('p1', data)
                self.assertEqual(self.p, before)
                self.assertTrue(self.errors)

    async def test_missing_token_rejects_belt_without_consuming_bag(self):
        belt = self.belt('health_potion')
        belt['utility_belt_token'] = 'current'
        self.p['bag'] = [item('health_potion')]
        before = deepcopy(self.p)
        await self.r.handle_use_item('p1', 'health_potion', source='utility_belt', gear_slot='item1', pocket_index=0)
        self.assertEqual(self.p, before)

    async def test_consuming_partial_head_advances_to_partial_reserve(self):
        belt = self.belt('health_potion_concentrated', 1)
        belt['utility_belt_slots'][0]['item']['uses_left'] = 1
        bottle = item('health_potion_concentrated')
        bottle['uses_left'] = 2
        self.p['bag'] = [bottle]
        self.assertTrue(await self.r.handle_move_utility_belt_item('p1', dict(direction='to_belt',gear_slot='item1',pocket_index=0,bag_index=0)))
        await self.dispatch(self.r, 'p1', dict(item_id='health_potion_concentrated', source='utility_belt', gear_slot='item1', pocket_index=0, belt_token=belt['utility_belt_token']))
        self.assertEqual(belt['utility_belt_slots'][0]['quantity'], 1)
        self.assertEqual(belt['utility_belt_slots'][0]['item']['uses_left'], 2)

    async def test_reequipping_same_belt_invalidates_its_previous_action(self):
        belt = self.belt('health_potion')
        token = belt['utility_belt_token']
        await self.r.handle_unequip('p1', 'item1')
        await self.r.handle_equip_from_bag('p1', 0)
        self.assertNotEqual(self.p['gear']['item1']['utility_belt_token'], token)
        before = deepcopy(self.p)
        await self.use('health_potion', belt_token=token)
        self.assertEqual(self.p, before)
        self.assertTrue(self.errors)

    async def test_four_mixed_bottles_consume_exactly_seven_doses(self):
        belt = self.belt('health_potion_concentrated', 1)
        belt['utility_belt_slots'][0]['item']['uses_left'] = 1
        for doses in (2, 3, 1):
            bottle = item('health_potion_concentrated')
            bottle['uses_left'] = doses
            self.r._route_acquired_item(self.p, bottle)
        for quantity, doses in [(3, 2), (3, 1), (2, 3), (2, 2), (2, 1), (1, 1), (0, None)]:
            self.p['bonus_action_used'] = False
            await self.use('health_potion_concentrated')
            entry = belt['utility_belt_slots'][0]
            self.assertEqual((entry['quantity'], entry['item']['uses_left']) if entry else (0, None), (quantity, doses))

    async def test_consumption_applies_current_bottle_metadata_before_promoting_reserve(self):
        belt = self.belt('antidote', 1)
        self.r.round_num = 10
        belt['utility_belt_slots'][0]['item']['imunidade_dado'] = 1
        incoming = item('antidote')
        incoming['imunidade_dado'] = 4
        self.r._route_acquired_item(self.p, incoming)
        await self.use('antidote')
        self.assertEqual(self.p['imunidades_status']['veneno'], 11)
        self.assertEqual(belt['utility_belt_slots'][0]['item']['imunidade_dado'], 4)
        self.p['bonus_action_used'] = False
        await self.use('antidote')
        self.assertEqual(self.p['imunidades_status']['veneno'], 14)
        self.assertIsNone(belt['utility_belt_slots'][0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
