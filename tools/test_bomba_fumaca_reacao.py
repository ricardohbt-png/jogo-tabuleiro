"""Authoritative smoke reaction regression tests; run from repository root."""
import asyncio
from copy import deepcopy
import unittest
import time
import json
from unittest.mock import patch

from test_projeteis import S, sala


class SmokeReactionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.r, self.p = sala()
        self.r.SMOKE_REACTION_TIMEOUT = .08
        self.p['bag'] = [{'id': 'bomba_fumaca', 'name': 'Bomba de Fumaça'}]
        self.p['pos'] = [2, 2]
        self.m = self.r.monsters['m1']
        self.m['pos'] = [3, 2]
        self.m.update(max_hp=999, atk_bonus=2, damage='1d4', str_=10, dex=10)
        self.target = {'kind': 'player', 'obj': self.p}
        self.sent = []
        self.opened = asyncio.Event()
        async def capture(pid, msg):
            self.sent.append((pid, msg))
            if msg.get('type') == 'smoke_reaction_prompt':
                self.opened.set()
        self.r.send_to = capture

    def add_hero(self, pid='p2', controller=None):
        p = S.make_player(pid, pid, 'mage', 1)
        p.update(pos=[2, 3], alive=True, connected=True)
        p['bag'] = [deepcopy(self.p['bag'][0])]
        if controller:
            p['controlador'] = controller
        else:
            self.r.connections[pid] = object()
        self.r.players[pid] = p
        return p

    async def start(self):
        task = asyncio.create_task(self.r._await_smoke_reaction(self.m, self.target))
        await asyncio.wait_for(self.opened.wait(), 1)
        return task, self.r._smoke_reaction['request_id']

    async def choose(self, request, pid='p1', hero='p1', use=True):
        await self.r.handle_smoke_reaction_choice(pid, {
            'request_id': request, 'heroi': hero, 'usar': use})

    async def test_api_exists(self):
        self.assertTrue(callable(getattr(self.r, '_await_smoke_reaction', None)))

    async def test_flash_is_a_five_tile_single_target_market_throwable(self):
        definition = S.ARREMESSAVEIS['bomba_flash']
        market = next(i for i in S.SHOP_MERCHANT if i['id'] == 'bomba_flash')
        self.assertEqual(definition['alcance'], 5)
        self.assertEqual(definition['alvo'], 'ataque_alvo')
        self.assertEqual(market['price'], 50)
        self.assertEqual(market['effect'], 'throwable')
        stocks = [city['mercador'] for cid, city in S.CITY_SHOPS.items()
                  if 'mercador' in city and cid != 'vila_dos_charcos']   # loja especial da Zumbra
        self.assertTrue(stocks)
        self.assertTrue(all('bomba_flash' in stock for stock in stocks))

    async def test_flash_reaction_candidate_uses_its_five_tile_range(self):
        self.p['bag'] = [{'id': 'bomba_flash', 'name': 'Bomba de Flash'}]
        self.m['pos'] = [7, 2]
        candidates = self.r._smoke_reaction_candidates(self.m, self.target)
        self.assertEqual([c['hero_id'] for c in candidates], ['p1'])
        self.assertEqual(candidates[0]['item_id'], 'bomba_flash')

    async def test_flash_hit_debuffs_the_announced_attack(self):
        self.p['bag'] = [{'id': 'bomba_flash', 'name': 'Bomba de Flash'}]
        self.p['ac'] = 100
        self.m['pos'] = [3, 2]
        task = asyncio.create_task(self.r._execute_one_monster_attack(
            self.m, {'name': 'Adaga', 'atk_bonus': 4, 'damage': '1d4',
                     'damage_types': ['physical']}, self.target))
        await asyncio.wait_for(self.opened.wait(), 1)
        reaction = self.r._smoke_reaction
        await self.r.handle_smoke_reaction_choice('p1', {
            'request_id': reaction['request_id'], 'heroi': 'p1', 'usar': True,
            'item_id': 'bomba_flash'})
        with patch.object(S.random, 'randint', side_effect=[20, 18, 3]):
            await task
        attack_roll = next(x for x in self.r._msgs
                           if x.get('type') == 'dice_roll' and x.get('kept'))
        self.assertEqual(attack_roll['value'], 3)
        self.assertEqual(attack_roll['modifier'], 2)
        self.assertTrue(any(x.get('type') == 'dice_roll' and x.get('discarded')
                            and x.get('value') == 18 for x in self.r._msgs))
        self.assertTrue(any(x.get('type') == 'attack_feedback'
                            and x.get('projectile', {}).get('item_id') == 'bomba_flash'
                            for x in self.r._msgs))
        self.assertEqual(self.p['bag'], [])

    async def test_normal_flash_throw_debuffs_monsters_next_attack_once(self):
        self.p['bag'] = [{'id': 'bomba_flash', 'name': 'Bomba de Flash'}]
        self.p['atk_bonus'] = 20
        self.m['ac'] = 1
        with patch.object(S.random, 'randint', return_value=20):
            await self.r._throw_item_alvo_impl(
                self.p, S.ARREMESSAVEIS['bomba_flash'], self.p['bag'][0], 'm1')
        self.assertEqual(self.m.get('_bomba_flash_ataque_pendente'), 1)
        self.p['ac'] = 100
        with patch.object(S.random, 'randint', side_effect=[18, 3]):
            await self.r._execute_one_monster_attack(
                self.m, {'name': 'Adaga', 'atk_bonus': 4, 'damage': '1d4',
                         'damage_types': ['physical']}, self.target)
        attack_roll = next(x for x in self.r._msgs
                           if x.get('type') == 'dice_roll' and x.get('kept'))
        self.assertEqual((attack_roll['value'], attack_roll['modifier']), (3, 2))
        self.assertNotIn('_bomba_flash_ataque_pendente', self.m)

    async def test_flash_miss_consumes_item_without_debuffing_attack(self):
        self.p['bag'] = [{'id': 'bomba_flash', 'name': 'Bomba de Flash'}]
        self.p['atk_bonus'] = 20
        self.m['ac'] = 1
        with patch.object(S.random, 'randint', return_value=1):
            await self.r._throw_item_alvo_impl(
                self.p, S.ARREMESSAVEIS['bomba_flash'], self.p['bag'][0], 'm1')
        self.assertEqual(self.p['bag'], [])
        self.assertNotIn('_bomba_flash_ataque_pendente', self.m)
        self.p['ac'] = 100
        with patch.object(S.random, 'randint', return_value=4):
            await self.r._execute_one_monster_attack(
                self.m, {'name': 'Adaga', 'atk_bonus': 4, 'damage': '1d4',
                         'damage_types': ['physical']}, self.target)
        attack_roll = next(x for x in self.r._msgs
                           if x.get('type') == 'dice_roll' and x.get('die') == 'd20'
                           and x.get('value') == 4)
        self.assertEqual((attack_roll['value'], attack_roll['modifier']), (4, 4))

    async def test_accept_consumes_once_without_actions_or_survival(self):
        before = [self.p.get(k) for k in ('action_done', 'bonus_action_used', 'fome', 'sede')]
        task, rid = await self.start()
        await self.choose(rid)
        result = await task
        self.assertEqual(result['hero_id'], 'p1')
        self.assertEqual(len(self.p['bag']), 0)
        self.assertEqual(before, [self.p.get(k) for k in ('action_done', 'bonus_action_used', 'fome', 'sede')])
        self.assertIsNone(self.r._smoke_reaction)
        await self.choose(rid)
        self.assertEqual(len(self.p['bag']), 0)

    async def test_simultaneous_accepts_only_consume_one(self):
        other = self.add_hero()
        task, rid = await self.start()
        await asyncio.gather(self.choose(rid), self.choose(rid, 'p2', 'p2'))
        self.assertIsNotNone(await task)
        self.assertEqual(len(self.p['bag']) + len(other['bag']), 1)
        self.assertEqual(len([m for _, m in self.sent if m['type'] == 'smoke_reaction_closed']), 2)

    async def test_group_offer_and_explicit_extra(self):
        other = self.add_hero(controller='p1')
        task, rid = await self.start()
        offers = [m for _, m in self.sent if m['type'] == 'smoke_reaction_prompt']
        self.assertEqual(len(offers), 1)
        self.assertEqual(len(offers[0]['candidates']), 2)
        await self.choose(rid, hero='p2')
        self.assertEqual((await task)['hero_id'], 'p2')
        self.assertEqual(len(other['bag']), 0)
        self.assertEqual(len(self.p['bag']), 1)

    async def test_forged_identity_and_stale_request_do_not_consume(self):
        task, rid = await self.start()
        await self.choose(rid, pid='intruder')
        await self.choose('stale')
        self.assertFalse(task.done())
        await self.choose(rid, use=False)
        self.assertIsNone(await task)
        self.assertEqual(len(self.p['bag']), 1)

    async def test_timeout_and_decline(self):
        task, _ = await self.start()
        self.assertIsNone(await task)
        self.assertEqual(len(self.p['bag']), 1)
        self.opened.clear()
        task, rid = await self.start()
        await self.choose(rid, hero=None, use=False)
        self.assertIsNone(await task)

    async def test_range_wall_and_incapacitation(self):
        self.m['pos'] = [6, 2]
        self.assertEqual(len(self.r._smoke_reaction_candidates(self.m, self.target)), 1)
        self.m['pos'] = [7, 2]
        self.assertEqual(self.r._smoke_reaction_candidates(self.m, self.target), [])
        with patch.object(self.r, '_bonus_alcance_arremesso', return_value=1):
            self.assertEqual(len(self.r._smoke_reaction_candidates(self.m, self.target)), 1)
        self.m['pos'] = [3, 2]
        with patch.object(self.r, '_tem_linha_de_visao', return_value=False):
            self.assertEqual(self.r._smoke_reaction_candidates(self.m, self.target), [])
        for status in ('petrificado', 'paralisado', 'dormindo', 'engolido', 'perde_turno'):
            self.p[status] = True
            self.assertEqual(self.r._smoke_reaction_candidates(self.m, self.target), [], status)
            self.p.pop(status)
        self.p['cola_sem_movimento'] = True
        self.assertEqual(len(self.r._smoke_reaction_candidates(self.m, self.target)), 1)

    async def test_belt_stock_is_consumed_from_exact_pocket(self):
        belt = deepcopy(S._DUNGEON_ITEM_CATALOG['cinto_utilidades'])
        self.r._normalize_utility_belt(belt)
        belt['utility_belt_token'] = 'smoke-belt'
        belt['utility_belt_slots'][0] = {'item': self.p['bag'].pop(), 'quantity': 2}
        self.p['gear']['item1'] = belt
        task, rid = await self.start()
        await self.choose(rid)
        self.assertIsNotNone(await task)
        self.assertEqual(belt['utility_belt_slots'][0]['quantity'], 1)

    async def test_invalidated_item_allows_other_candidate(self):
        other = self.add_hero()
        task, rid = await self.start()
        self.p['bag'].clear()
        await self.choose(rid)
        self.assertFalse(task.done())
        await self.choose(rid, 'p2', 'p2')
        self.assertEqual((await task)['hero_id'], 'p2')
        self.assertEqual(other['bag'], [])

    async def test_cancel_cleans_up_and_closes_every_offer(self):
        task, _ = await self.start()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertIsNone(self.r._smoke_reaction)
        self.assertEqual(self.sent[-1][1]['type'], 'smoke_reaction_closed')
        self.assertEqual(len(self.p['bag']), 1)

    async def test_modular_attack_pauses_then_uses_lower_die_and_normal_cloud(self):
        m = S.make_monster(next(d for d in S.MONSTER_DEFS if d['type'] == 'goblin'), self.r.rooms[0])
        m.update(id='m1', pos=[3, 2], hp=999, max_hp=999, visao_escuro=True)
        self.r.monsters['m1'] = m
        self.p['ac'] = 100
        atk = {'name': 'Adaga', 'atk_bonus': 2, 'damage': '1d4', 'damage_types': ['physical']}
        task = asyncio.create_task(self.r._execute_one_monster_attack(m, atk, self.target))
        await asyncio.wait_for(self.opened.wait(), 1)
        self.assertFalse(any(x['type'] == 'dice_roll' for x in self.r._msgs))
        rid = self.r._smoke_reaction['request_id']
        await self.choose(rid)
        with patch.object(S.random, 'randint', side_effect=[18, 3]):
            await task
        kept = [x for x in self.r._msgs if x['type'] == 'dice_roll' and x.get('kept')]
        self.assertEqual(kept[0]['value'], 3)
        self.assertTrue(any(x['type'] == 'attack_feedback' and x.get('projectile', {}).get('item_id') == 'bomba_fumaca'
                            for x in self.r._msgs))
        cloud = next(z for z in self.r.zonas_especiais if z.get('visual_id', '').startswith('fumaca_'))
        self.assertEqual(cloud['duracao'], 2)
        self.assertEqual(cloud['raio'], 1)
        self.assertEqual([cloud['cx'], cloud['cy']], [3, 2])
        self.assertIsNone(self.r._smoke_hold)

    async def test_detached_command_allows_same_connection_to_answer(self):
        task = await self.r._run_smoke_capable_command(
            self.r._prepare_smoke_reaction(self.m, self.target), 'test reaction')
        await asyncio.wait_for(self.opened.wait(), 1)
        await self.choose(self.r._smoke_reaction['request_id'])
        await task
        self.assertEqual(self.p['bag'], [])
        self.assertIsNone(self.r._smoke_command_task)

    async def test_enemy_targeted_throw_uses_disadvantage(self):
        task = asyncio.create_task(self.r._monster_throw_item_impl(
            self.m, self.target, {'id': 'fogo_grego'}))
        await asyncio.wait_for(self.opened.wait(), 1)
        await self.choose(self.r._smoke_reaction['request_id'])
        self.p['ac'] = 100
        with patch.object(S.random, 'randint', side_effect=[19, 2]):
            await task
        self.assertEqual([x['value'] for x in self.r._msgs if x.get('kept')], [2])

    async def test_legacy_attack_pauses(self):
        self.m['ai_type'] = None
        self.m['ca'] = 10
        self.p['ac'] = 100
        task = asyncio.create_task(self.r.gm_phase(self.m))
        await asyncio.wait_for(self.opened.wait(), 1)
        await self.choose(self.r._smoke_reaction['request_id'], use=False)
        await task
        self.assertEqual(len(self.p['bag']), 1)

    async def test_master_timer_waits_and_preserves_remaining_time(self):
        self.r.master_manual_mid = 'm1'
        self.r.master_manual_event = asyncio.Event()
        self.m['_master_touched'] = True
        self.r.master_manual_deadline = time.monotonic() + .025
        task = asyncio.create_task(self.r._prepare_smoke_reaction(self.m, self.target))
        await asyncio.wait_for(self.opened.wait(), 1)
        timer = asyncio.create_task(self.r._master_manual_timeout('m1'))
        await asyncio.sleep(.035)
        self.assertFalse(self.r.master_manual_event.is_set())
        await self.choose(self.r._smoke_reaction['request_id'], use=False)
        await task
        self.assertEqual(self.r.master_manual_mid, 'm1')
        await asyncio.wait_for(timer, 1)
        self.assertTrue(self.r.master_manual_event.is_set())

    async def test_disconnect_last_candidate_releases_attack(self):
        task, _ = await self.start()
        await self.r.handle_disconnect_em_jogo('p1')
        self.assertIsNone(await task)
        self.assertIsNone(self.r._smoke_reaction)

    async def test_cloud_expires_after_two_normal_round_ticks(self):
        task = asyncio.create_task(self.r._prepare_smoke_reaction(self.m, self.target))
        await asyncio.wait_for(self.opened.wait(), 1)
        await self.choose(self.r._smoke_reaction['request_id'])
        self.assertTrue(await task)
        await self.r._processar_zonas_turno()
        self.assertEqual(self.r.zonas_especiais[0]['duracao'], 1)
        await self.r._processar_zonas_turno()
        self.assertFalse(any(z.get('ativa') for z in self.r.zonas_especiais))

    async def test_websocket_reader_accepts_reaction_to_own_controlled_attack(self):
        class Socket:
            remote_address = ('127.0.0.1', 1234)
            def __init__(self): self.incoming = asyncio.Queue(); self.outgoing = []
            def __aiter__(self): return self
            async def __anext__(self):
                item = await self.incoming.get()
                if item is None: raise StopAsyncIteration
                return json.dumps(item)
            async def send(self, raw): self.outgoing.append(json.loads(raw))
        ws = Socket()
        self.r.code = 'WSMK'
        S.rooms['WSMK'] = self.r
        self.r.connections.clear()
        joined = asyncio.Event()
        async def rejoin(hero, socket, *args):
            self.r.connections['p1'] = socket
            joined.set()
            return 'p1'
        self.r.religar_heroi = rejoin
        self.r.command_control_pid = 'p1'
        self.r.command_control_mid = 'm1'
        self.r.command_control_deadline = time.monotonic() + 60
        self.p['ac'] = 100
        reader = asyncio.create_task(S.handler(ws))
        try:
            await ws.incoming.put({'type':'rejoin','code':'WSMK','name':self.p['name']})
            await asyncio.wait_for(joined.wait(), 1)
            await ws.incoming.put({'type':'mestre_atacar_monstro','monster_id':'m1','target_id':'p1'})
            await asyncio.wait_for(self.opened.wait(), 1)
            await ws.incoming.put({'type':'smoke_reaction_choice','request_id':self.r._smoke_reaction['request_id'],
                                   'usar':True,'heroi':'p1'})
            await asyncio.wait_for(self.r._smoke_command_task, 2)
            self.assertEqual(self.p['bag'], [])
            self.assertTrue(any(x.get('kept') for x in self.r._msgs))
        finally:
            await ws.incoming.put(None)
            await asyncio.wait_for(reader, 1)
            S.rooms.pop('WSMK', None)


if __name__ == '__main__':
    unittest.main()
