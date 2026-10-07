"""Use/throw from exact equipped belt pockets, with legacy bag compatibility."""
import ast
import asyncio
from copy import deepcopy
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from test_projeteis import S, sala

ROOT = Path(__file__).resolve().parents[1]


def item(iid):
    return deepcopy(S._DUNGEON_ITEM_CATALOG[iid])


def use_dispatch():
    tree = ast.parse((ROOT / 'server.py').read_text(encoding='utf8'))
    branch = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
                  and ast.unparse(node.test) == "t == 'use_item'")
    fn = ast.AsyncFunctionDef(name='dispatch', args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=x) for x in ('room', 'pid', 'msg')], kwonlyargs=[], kw_defaults=[], defaults=[]), body=branch.body, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    scope = {}
    exec(compile(module, '<use_item dispatch>', 'exec'), scope)
    return scope['dispatch']


class BeltActionTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.dispatch = staticmethod(use_dispatch())

    def setUp(self):
        self.r, self.p = sala()
        self.p['bag'] = []
        self.p['hp'] = 1
        self.p['bonus_action_used'] = False
        self.errors = []
        async def capture(pid, msg):
            self.errors.append(msg)
        async def noop(*args, **kwargs):
            pass
        self.r.send_to = capture
        self.r._licao_evento = noop

    def belt(self, iid, quantity=2, slot='item1', model='cinto_utilidades'):
        belt = item(model)
        self.r._normalize_utility_belt(belt)
        belt['utility_belt_token'] = 'test-' + str(getattr(self, '_belt_sequence', 0))
        self._belt_sequence = getattr(self, '_belt_sequence', 0) + 1
        belt['utility_belt_slots'][0] = {'item': item(iid), 'quantity': quantity}
        self.p['gear'][slot] = belt
        return belt

    async def use(self, iid, **source):
        options = dict(source='utility_belt', gear_slot='item1', pocket_index=0)
        options.update(source)
        options.setdefault('belt_token', (self.p['gear'].get(options['gear_slot']) or {}).get('utility_belt_token') if isinstance(options['gear_slot'], str) else None)
        await self.r.handle_use_item('p1', iid, **options)

    async def throw(self, iid='frasco_oleo', **source):
        data = dict(item_id=iid, target_id='m1', source='utility_belt', gear_slot='item1', pocket_index=0)
        data.update(source)
        data.setdefault('belt_token', (self.p['gear'].get(data['gear_slot']) or {}).get('utility_belt_token') if isinstance(data['gear_slot'], str) else None)
        await self.r.handle_throw_item('p1', data)

    async def test_use_from_either_model_and_slot_consumes_exact_source(self):
        for model in ('cinto_utilidades', 'cinto_com_bolsos'):
            for slot in ('item1', 'item2'):
                with self.subTest(model=model, slot=slot):
                    self.setUp()
                    belt = self.belt('health_potion', 2, slot, model)
                    bag_item = item('health_potion')
                    self.p['bag'] = [bag_item]
                    other = self.belt('health_potion', 3, 'item2' if slot == 'item1' else 'item1')
                    await self.use('health_potion', gear_slot=slot)
                    self.assertGreater(self.p['hp'], 1)
                    self.assertEqual(belt['utility_belt_slots'][0]['quantity'], 1)
                    self.assertEqual(other['utility_belt_slots'][0]['quantity'], 3)
                    self.assertIs(self.p['bag'][0], bag_item)
                    self.assertTrue(self.p['bonus_action_used'])

    async def test_last_unit_clears_pocket(self):
        belt = self.belt('health_potion', 1)
        await self.use('health_potion')
        self.assertIsNone(belt['utility_belt_slots'][0])

    async def test_multidose_bottle_keeps_doses_until_empty_then_starts_next(self):
        belt = self.belt('health_potion_concentrated', 2)
        entry = belt['utility_belt_slots'][0]
        maximum = entry['item']['max_uses']
        entry['item']['uses_left'] = 2
        await self.use('health_potion_concentrated')
        self.assertEqual((entry['quantity'], entry['item']['uses_left']), (2, 1))
        self.p['bonus_action_used'] = False
        await self.use('health_potion_concentrated')
        self.assertEqual((entry['quantity'], entry['item']['uses_left']), (1, maximum))
        for remaining in range(maximum - 1, -1, -1):
            self.p['bonus_action_used'] = False
            await self.use('health_potion_concentrated')
            if remaining:
                self.assertEqual((entry['quantity'], entry['item']['uses_left']), (1, remaining))
        self.assertIsNone(belt['utility_belt_slots'][0])

    async def test_source_moved_during_bonus_action_never_applies_heal_or_changes_doses(self):
        for iid in ('health_potion', 'health_potion_concentrated'):
            for change in ('transfer', 'unequip', 'replace'):
                with self.subTest(iid=iid, change=change):
                    self.setUp()
                    belt = self.belt(iid, 1)
                    old_item = belt['utility_belt_slots'][0]['item']
                    if iid == 'health_potion_concentrated': old_item['uses_left'] = 2
                    original_bonus = self.r._executar_acao_bonus
                    suspended, resume = asyncio.Event(), asyncio.Event()
                    async def gated_bonus(player):
                        result = await original_bonus(player)
                        suspended.set()
                        await resume.wait()
                        return result
                    self.r._executar_acao_bonus = gated_bonus
                    pending = asyncio.create_task(self.use(iid))
                    try:
                        await asyncio.wait_for(suspended.wait(), 1)
                        if change == 'transfer':
                            self.assertTrue(await self.r.handle_move_utility_belt_item('p1', dict(
                                direction='to_bag', gear_slot='item1', pocket_index=0, bag_index=0)))
                        elif change == 'unequip':
                            self.p['gear']['item1'] = None
                            self.p['bag'].append(belt)
                        else:
                            self.belt(iid, 1)
                        old_before = deepcopy(old_item)
                        source_before = deepcopy(self.p['gear'])
                        bag_before = deepcopy(self.p['bag'])
                    finally:
                        resume.set()
                        await pending
                    self.assertEqual(self.p['hp'], 1, 'stale belt source must not heal')
                    self.assertEqual(old_item, old_before, 'stale source must not mutate old doses')
                    self.assertEqual(self.p['gear'], source_before)
                    self.assertEqual(self.p['bag'], bag_before)
                    self.assertTrue(self.errors)

    async def test_belt_use_commits_consumption_before_effect_narration(self):
        for iid, doses in (('health_potion', None), ('health_potion_concentrated', 2),
                           ('health_potion_concentrated', 1)):
            with self.subTest(iid=iid, doses=doses):
                self.setUp()
                belt = self.belt(iid, 2)
                entry = belt['utility_belt_slots'][0]
                if doses is not None: entry['item']['uses_left'] = doses
                # The real bonus action has its own narration; isolate the effect narration.
                async def bonus(player): return True
                self.r._executar_acao_bonus = bonus
                observations = []
                async def effect_narration(message):
                    observations.append((self.p['hp'], deepcopy(entry)))
                self.r.gm_say = effect_narration
                await self.use(iid)
                hp, snapshot = observations[0]
                self.assertGreater(hp, 1)
                self.assertEqual(snapshot['quantity'], 2 if doses == 2 else 1)
                if doses is not None:
                    self.assertEqual(snapshot['item']['uses_left'],
                                     1 if doses == 2 else snapshot['item']['max_uses'])

    async def test_unknown_poison_refusal_does_not_consume_belt_source(self):
        belt = self.belt('veneno_aranha_sombria', 2)
        belt['utility_belt_slots'][0]['item']['veneno_id'] = 'missing_poison'
        before = deepcopy(belt)
        await self.use('veneno_aranha_sombria')
        self.assertEqual(belt, before)
        self.assertTrue(self.errors)

    async def test_use_existing_rejections_do_not_consume(self):
        for reason in ('bonus', 'last_effort', 'transformed', 'empty_doses', 'throwable', 'invalid_ally', 'far_ally', 'not_turn'):
            with self.subTest(reason=reason):
                self.setUp()
                iid = ('frasco_oleo' if reason == 'throwable' else
                       'health_potion_concentrated' if reason == 'empty_doses' else
                       'antidote' if 'ally' in reason else 'health_potion')
                belt = self.belt(iid)
                options = {}
                if reason == 'bonus': self.p['bonus_action_used'] = True
                if reason == 'last_effort': self.p['ultimo_esforco_ativo'] = True
                if reason == 'transformed': self.p['metamorfose_ativa'] = True
                if reason == 'empty_doses': belt['utility_belt_slots'][0]['item']['uses_left'] = 0
                if reason == 'invalid_ally': options['target_id'] = 'missing'
                if reason == 'far_ally':
                    ally = S.make_player('ally', 'Ally', 'warrior', 0)
                    ally['pos'] = [10, 10]
                    self.r.players['ally'] = ally
                    options['target_id'] = 'ally'
                if reason == 'not_turn': self.r._is_turn = lambda pid: False
                before = deepcopy(self.p)
                await self.use(iid, **options)
                self.assertEqual(self.p, before)

    async def test_throw_targeted_hit_miss_and_area_from_both_slots(self):
        for slot in ('item1', 'item2'):
            for mode in ('hit', 'miss', 'area'):
                with self.subTest(slot=slot, mode=mode):
                    self.setUp()
                    iid = 'bomba_incendiaria' if mode == 'area' else 'frasco_oleo'
                    belt = self.belt(iid, 2, slot)
                    self.p['bag'] = [item(iid)]
                    before_hp = self.r.monsters['m1']['hp']
                    options = dict(gear_slot=slot)
                    if mode == 'area': options.update(tx=4, ty=1)
                    with patch.object(S.random, 'randint', return_value=1 if mode == 'miss' else 20):
                        await self.throw(iid, **options)
                    self.assertEqual(belt['utility_belt_slots'][0]['quantity'], 1)
                    self.assertEqual(len(self.p['bag']), 1)
                    self.assertTrue(self.p['action_done'])
                    if mode == 'miss': self.assertEqual(self.r.monsters['m1']['hp'], before_hp)
                    else: self.assertLess(self.r.monsters['m1']['hp'], before_hp)

    async def test_throw_last_unit_clears_pocket(self):
        belt = self.belt('frasco_oleo', 1)
        await self.throw()
        self.assertIsNone(belt['utility_belt_slots'][0])

    async def test_throw_rejections_preserve_items_and_actions(self):
        for reason in ('action', 'not_turn', 'target', 'dead', 'range', 'wall', 'area_missing', 'area_range', 'area_wall', 'not_throwable'):
            with self.subTest(reason=reason):
                self.setUp()
                iid = ('bomba_incendiaria' if reason.startswith('area_') else
                       'health_potion' if reason == 'not_throwable' else 'frasco_oleo')
                self.belt(iid)
                options = {}
                if reason == 'action': self.p['action_done'] = True
                if reason == 'not_turn': self.r._is_turn = lambda pid: False
                if reason == 'target': options['target_id'] = 'missing'
                if reason == 'dead': self.r.monsters['m1']['hp'] = 0
                if reason == 'range': self.r.monsters['m1']['pos'] = [99, 99]
                if 'wall' in reason: self.r._tem_linha_de_visao = lambda *a, **k: False
                if reason == 'area_range': options.update(tx=99, ty=99)
                if reason == 'area_wall': options.update(tx=4, ty=1)
                before = deepcopy(self.p)
                await self.throw(iid, **options)
                self.assertEqual(self.p, before)

    async def test_invalid_source_never_falls_back_to_matching_bag_item(self):
        cases = [dict(source='unknown'), dict(source=None), dict(gear_slot='arma'),
                 dict(gear_slot=[]), dict(pocket_index=-1), dict(pocket_index=4),
                 dict(pocket_index=True), dict(pocket_index='0'), dict(pocket_index=None),
                 dict(pocket_index=[]), dict(gear_slot='item2')]
        for action in ('use', 'throw'):
            for options in cases + [dict(state=state) for state in ('unequipped', 'replaced', 'mismatch', 'empty', 'malformed')]:
                with self.subTest(action=action, options=options):
                    self.setUp()
                    iid = 'health_potion' if action == 'use' else 'frasco_oleo'
                    belt = self.belt(iid)
                    self.p['bag'] = [item(iid)]
                    options = dict(options)
                    state = options.pop('state', None)
                    if state == 'unequipped':
                        self.p['gear']['item1'] = None
                        self.p['bag'].append(belt)
                    if state == 'replaced': self.p['gear']['item1'] = item('backpack')
                    if state == 'mismatch': belt['utility_belt_slots'][0]['item'] = item('elixir')
                    if state == 'empty': belt['utility_belt_slots'][0] = None
                    if state == 'malformed': belt['utility_belt_slots'][0]['quantity'] = True
                    before = deepcopy(self.p)
                    await (self.use(iid, **options) if action == 'use' else self.throw(iid, **options))
                    self.assertEqual(self.p, before)
                    self.assertTrue(self.errors)

    async def test_default_and_explicit_bag_semantics(self):
        for explicit in (False, True):
            for action in ('use', 'throw', 'area'):
                with self.subTest(explicit=explicit, action=action):
                    self.setUp()
                    iid = {'use': 'health_potion', 'throw': 'frasco_oleo', 'area': 'bomba_incendiaria'}[action]
                    belt = self.belt(iid)
                    before_belt = deepcopy(belt)
                    self.p['bag'] = [item(iid)]
                    extra = {'source': 'bag', 'gear_slot': 'item1', 'pocket_index': 0} if explicit else {}
                    if action == 'use': await self.r.handle_use_item('p1', iid, **extra)
                    else:
                        data = dict(item_id=iid, **extra)
                        data.update(tx=4, ty=1) if action == 'area' else data.update(target_id='m1')
                        await self.r.handle_throw_item('p1', data)
                    self.assertEqual(self.p['bag'], [])
                    self.assertEqual(belt, before_belt)

    async def test_bag_multidose_behavior_unchanged(self):
        potion = item('health_potion_concentrated')
        potion['uses_left'] = 2
        self.p['bag'] = [potion]
        await self.r.handle_use_item('p1', potion['id'])
        self.assertEqual(potion['uses_left'], 1)
        self.assertEqual(self.p['bag'], [potion])
        self.p['bonus_action_used'] = False
        await self.r.handle_use_item('p1', potion['id'])
        self.assertEqual(self.p['bag'], [])
        self.assertEqual(potion['uses_left'], 0)

    async def test_use_message_dispatch_passes_source_and_target(self):
        # Execute the real use_item dispatch branch without opening a network server.
        belt = self.belt('antidote')
        self.p['envenenado'] = True
        await self.dispatch(self.r, 'p1', dict(item_id='antidote', target_id='p1', source='utility_belt', gear_slot='item1', pocket_index=0, belt_token=belt['utility_belt_token']))
        self.assertEqual(belt['utility_belt_slots'][0]['quantity'], 1)


class ClientRequestTests(unittest.TestCase):
    def test_source_metadata_for_use_targeted_and_area_throw(self):
        script = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
let messages = [];
class Socket { constructor() { this.readyState = 1; } send(raw) { messages.push(JSON.parse(raw)); } close() {} }
const ctx = vm.createContext({ WebSocket: Socket, console, setTimeout, clearTimeout,
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} } });
vm.runInContext(fs.readFileSync('src/gameState.js', 'utf8'), ctx);
const GS = vm.runInContext('GS', ctx); GS.connect('ws://test', 'Hero', 'login');
const source = {source:'utility_belt', gearSlot:'item2', pocketIndex:0, beltToken:'belt-A'};
GS.useItem('health_potion', source);
GS.throwItem('frasco_oleo', 'm1', [4,1], source);
GS.throwItemArea('bomba_incendiaria', 4, 1, source);
const coords = {source:'utility_belt', gear_slot:'item2', pocket_index:0, belt_token:'belt-A'};
assert.deepEqual(messages, [
  {type:'use_item', item_id:'health_potion', ...coords},
  {type:'throw_item', item_id:'frasco_oleo', target_id:'m1', target_pos:[4,1], ...coords},
  {type:'throw_item', item_id:'bomba_incendiaria', tx:4, ty:1, ...coords}]);
messages = [];
for (const info of [undefined, {source:'bag', gearSlot:'item1', pocketIndex:1}]) {
  GS.useItem('health_potion', info); GS.throwItem('frasco_oleo', 'm1', [4,1], info);
  GS.throwItemArea('bomba_incendiaria', 4, 1, info);
}
const bag = [{type:'use_item', item_id:'health_potion'},
  {type:'throw_item', item_id:'frasco_oleo', target_id:'m1', target_pos:[4,1]},
  {type:'throw_item', item_id:'bomba_incendiaria', tx:4, ty:1}];
assert.deepEqual(messages, [...bag, ...bag]);
console.log('Client belt/bag request metadata: PASS');
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main(verbosity=2)
