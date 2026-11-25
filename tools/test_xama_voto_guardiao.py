"""Sorteio raro e Súplica Vital do Xamã Goblin."""
import sys
from pathlib import Path
from copy import deepcopy
from unittest import IsolatedAsyncioTestCase, main
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S


def shaman(roll=0.001, material=0.5):
    md = next(d for d in S.MONSTER_DEFS if d['type'] == 'goblin_xama')
    with patch.object(S.random, 'random', side_effect=[roll, material]):
        return S.make_monster(md, {'id': 1, 'cx': 4, 'cy': 4})


class ShamanTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom('TEST')
        self.room.round_num = 1
        self.room.broadcast = AsyncMock()
        self.room.gm_say = AsyncMock()
        self.m = shaman()
        self.room.monsters = {self.m['id']: self.m}

    async def test_spawn_boundary_and_material_variants(self):
        normal = shaman(0.01)
        self.assertFalse(any(i.get('voto_guardiao') for i in normal.get('equipment_items', [])))
        self.assertEqual(normal['attacks'][0]['damage'], '1d6')
        for roll, suffix in ((0.5, ''), (0.75, '_aco_damasco'), (0.85, '_obsidiana_ferro'),
                             (0.95, '_liga_titanio'), (0.99, '_prata')):
            m = shaman(0.0099, roll)
            w = m['equipment_items'][0]
            self.assertEqual(w['id'], 'maca_voto_guardiao' + suffix)
            self.assertTrue(w['voto_guardiao'])
            self.assertEqual(m['attacks'][0]['atk_bonus'], 3)
            self.assertEqual(m['attacks'][0]['equipment_weapon_id'], w['id'])
            self.assertEqual(m['equipped_items'][0], w['id'])
            self.assertEqual(m['equipped_items'][1:], normal['equipped_items'][1:])

    async def test_heals_most_injured_and_cooldown(self):
        self.m['hp'] = 7
        ally = {'id': 'ally', 'name': 'Aliado', 'type': 'goblin_combatente',
                'hp': 2, 'max_hp': 12, 'pos': [6, 4]}
        dead = {**ally, 'id': 'dead', 'hp': 0}
        far = {**ally, 'id': 'far', 'hp': 1, 'pos': [7, 4]}
        self.room.monsters.update(ally=ally, dead=dead, far=far)
        with patch.object(S, 'roll_dice', return_value=6):
            self.assertTrue(await self.room._xama_suplica_vital_apos_acerto(self.m, self.m['attacks'][0]))
            self.assertEqual(ally['hp'], 8)
            self.assertEqual(self.m['hp'], 7)
            self.assertFalse(await self.room._xama_suplica_vital_apos_acerto(self.m, self.m['attacks'][0]))
            self.room.round_num = 10
            self.assertFalse(await self.room._xama_suplica_vital_apos_acerto(self.m, self.m['attacks'][0]))
            self.room.round_num = 11
            self.assertTrue(await self.room._xama_suplica_vital_apos_acerto(self.m, self.m['attacks'][0]))
            self.assertEqual(ally['hp'], 12)
            self.assertEqual(dead['hp'], 0)

    async def test_full_health_does_not_spend_cooldown_and_destroyed_weapon_cannot_heal(self):
        attack = self.m['attacks'][0]
        self.assertFalse(await self.room._xama_suplica_vital_apos_acerto(self.m, attack))
        self.assertFalse(self.m['equipment_items'][0].get('voto_guardiao_ready_round'))
        self.m['hp'] = 1
        self.m['equipment_items'][0]['corrosion_destroyed'] = True
        self.assertFalse(await self.room._xama_suplica_vital_apos_acerto(self.m, attack))

    async def test_common_attack_hook_only_heals_on_hit(self):
        self.m['hp'] = 1
        self.room._execute_one_monster_attack_impl = AsyncMock(return_value=False)
        target = {'kind': 'player', 'obj': {'id': 'p', 'hp': 10}}
        await self.room._execute_one_monster_attack(self.m, self.m['attacks'][0], target)
        self.assertEqual(self.m['hp'], 1)
        self.room._execute_one_monster_attack_impl.return_value = True
        with patch.object(S, 'roll_dice', return_value=4):
            await self.room._execute_one_monster_attack(self.m, self.m['attacks'][0], target)
        self.assertEqual(self.m['hp'], 5)

    async def test_death_loot_preserves_material_and_corrosion(self):
        m = shaman(0.001, 0.75)
        m['hp'] = 0
        m['equipment_items'][0]['corrosion_level'] = 1
        self.room.monsters = {m['id']: m}
        self.room.players = {}
        self.room.push_state = AsyncMock()
        dropped = []
        self.room._spawn_monster_loot = lambda pos, gold, items: dropped.extend(items) or 'chest'
        await self.room._monster_dies(m, None, force=True)
        mace = next(i for i in dropped if i['id'] == 'maca_voto_guardiao_aco_damasco')
        self.assertEqual(mace['corrosion_level'], 1)


if __name__ == '__main__':
    main()
