import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S
# O sorteio de material (variantes) e coberto em outro teste; aqui o equipamento-base e fixo.
S._sortear_material_arma_monstro = lambda i: i
S._sortear_material_armadura_monstro = lambda i: i


def spawn(bow=.5, ammo=.5, ring=.5, selected='ring_str'):
    definition = next(d for d in S.MONSTER_DEFS if d['type']=='goblin_arqueiro')
    with patch.object(S.random,'random',side_effect=[bow,ammo,ring]), \
         patch.object(S.random,'choice',side_effect=lambda options: next(x for x in options if x['id']==selected)):
        return S.make_monster(definition, {'id':0,'cx':3,'cy':3})

class GoblinArcher(unittest.TestCase):
    def test_bow_probabilities_and_catalog_stats(self):
        for roll, iid, distance, damage in [(.8499,'arco_curto',6,'1d6'),(.85,'longbow',10,'1d8')]:
            m=spawn(bow=roll)
            self.assertEqual(m['equipped_weapon']['id'],iid)
            self.assertEqual((m['attacks'][0]['range'],m['attacks'][0]['damage']), (distance,damage))
            self.assertEqual(m['flechas'],20)

    def test_arrow_chance_boundaries(self):
        for roll, iid in [(0,'flechas_prata'),(.199999,'flechas_prata'),(.2,'flechas_magicas'),(.219999,'flechas_magicas'),(.22,'flecha_incendiaria'),(.229999,'flecha_incendiaria'),(.23,'flechas_explosivas'),(.234999,'flechas_explosivas'),(.235,'flechas')]:
            with self.subTest(roll=roll):
                m=spawn(ammo=roll)
                self.assertEqual(m['municao_arqueiro']['id'],iid)
                self.assertEqual(m['municao_arqueiro']['ammo_count'],20)

    def test_six_rings_have_their_effect(self):
        for iid in ('ring_str','anel_impacto','anel_supremacia','ring_vita','anel_protecao','anel_vigia'):
            with self.subTest(ring=iid):
                m=spawn(ring=0,selected=iid)
                self.assertIn(iid,m['equipped_items'])
                if iid in ('ring_str','anel_supremacia'): self.assertEqual(m.get('equipment_attack_bonus'),1)
                if iid in ('anel_impacto','anel_supremacia'): self.assertEqual(m.get('equipment_damage_bonus'),1)
                if iid=='ring_vita': self.assertEqual(m['max_hp'],14)
                if iid=='anel_protecao': self.assertEqual(m['ac'],14)
                if iid=='anel_vigia': self.assertEqual(m.get('equipment_vision_bonus'),2)

    def test_ring_probability_and_vision(self):
        self.assertIn('anel_vigia',spawn(ring=.009999,selected='anel_vigia')['equipped_items'])
        self.assertEqual(len(spawn(ring=.01)['equipped_items']),1)
        r=S.GameRoom('VISION')
        self.assertEqual(r._get_raio_visao_monstro(spawn(ring=0,selected='anel_vigia')),
                         r._get_raio_visao_monstro(spawn())+2)

class ArcherAttack(unittest.IsolatedAsyncioTestCase):
    async def test_actual_magic_arrow_adds_attack_and_damage(self):
        m=spawn(ammo=.21); m['pos']=[3,3]
        p=S.make_player('p','Hero','warrior',0); p.update(pos=[3,6],hp=100,max_hp=100)
        r=S.GameRoom('ARCHER_ATTACK'); r.phase='playing'; r.map_w=r.map_h=10
        r.tiles=[[S.FLOOR]*10 for _ in range(10)]; r.players['p']=p; r.monsters[m['id']]=m
        async def noop(*args,**kwargs): pass
        r.gm_say=r.broadcast=r.push_state=r.send_to=noop
        r._tem_linha_de_visao=lambda *_: True
        with patch.object(S,'d20_attack',return_value=(True,10,15,False)) as attack, \
                patch.object(S,'roll_dice',return_value=2):
            await r._ai_goblin_arqueiro(m,[{'kind':'player','obj':p}])
        self.assertEqual(attack.call_args.args[0],5)
        self.assertEqual(p['hp'],95)
        self.assertEqual(m['flechas'],19)

    async def test_actual_fire_and_explosion_apply_damage(self):
        for ammo_roll, expected in [(.225,94),(.232,94)]:
            with self.subTest(ammo=ammo_roll):
                m=spawn(ammo=ammo_roll); m['pos']=[3,3]
                p=S.make_player('p','Hero','warrior',0); p.update(pos=[3,6],hp=100,max_hp=100)
                r=S.GameRoom('ARCHER_ATTACK'); r.phase='playing'; r.map_w=r.map_h=10
                r.tiles=[[S.FLOOR]*10 for _ in range(10)]; r.players['p']=p; r.monsters[m['id']]=m
                async def noop(*args,**kwargs): pass
                r.gm_say=r.broadcast=r.push_state=r.send_to=noop
                r._tem_linha_de_visao=lambda *_: True
                with patch.object(S,'d20_attack',return_value=(True,10,15,False)), \
                        patch.object(S,'roll_dice',return_value=2):
                    await r._ai_goblin_arqueiro(m,[{'kind':'player','obj':p}])
                self.assertEqual(p['hp'],expected)
                self.assertEqual(m['flechas'],19)

    async def test_explosive_arrow_hits_nearby_ally(self):
        m=spawn(ammo=.232); m['pos']=[3,3]
        ally=spawn(); ally['pos']=[4,6]; ally['hp']=ally['max_hp']=20
        p=S.make_player('p','Hero','warrior',0); p.update(pos=[3,6],hp=100,max_hp=100)
        r=S.GameRoom('ARCHER_AREA'); r.phase='playing'; r.map_w=r.map_h=10
        r.tiles=[[S.FLOOR]*10 for _ in range(10)]; r.players['p']=p
        r.monsters={m['id']:m,ally['id']:ally}
        async def noop(*args,**kwargs): pass
        async def fail_save(*args,**kwargs): return (False,1,0,1)
        r.gm_say=r.broadcast=r.push_state=r.send_to=noop
        r._save_mostrado=fail_save; r._tem_linha_de_visao=lambda *_: True
        with patch.object(S,'d20_attack',return_value=(True,10,15,False)), \
                patch.object(S,'roll_dice',return_value=2):
            await r._ai_goblin_arqueiro(m,[{'kind':'player','obj':p}])
        self.assertEqual(p['hp'],94)
        self.assertEqual(ally['hp'],18)

    async def test_attack_uses_special_ammo_and_consumes_on_miss(self):
        for roll, iid in [(.1,'flechas_prata'),(.21,'flechas_magicas'),(.225,'flecha_incendiaria'),(.232,'flechas_explosivas')]:
            with self.subTest(ammo=iid):
                m=spawn(ammo=roll); m['pos']=[3,3]
                p=S.make_player('p','Hero','warrior',0); p['pos']=[3,6]
                r=S.GameRoom('ARCHER'); r.phase='playing'; r.players['p']=p; r.monsters[m['id']]=m
                r._tem_linha_de_visao=lambda *_: True
                seen=[]
                async def attack(monster, data, target): seen.append(data); return False
                r._execute_one_monster_attack=attack
                await r._ai_goblin_arqueiro(m,[{'kind':'player','obj':p}])
                self.assertEqual(m['flechas'],19)
                self.assertEqual(m['municao_arqueiro']['ammo_count'],19)
                self.assertEqual(len(seen),1)
                if iid=='flechas_prata': self.assertTrue(seen[0]['silver'])
                if iid=='flechas_magicas': self.assertEqual(seen[0]['ammo_atk_bonus'],1)
                if iid=='flecha_incendiaria': self.assertEqual(seen[0]['fire_damage'],'1d4')
                if iid=='flechas_explosivas': self.assertEqual(seen[0]['special_effect'],'explosive_ammo')

    async def test_loot_contains_bow_ring_remaining_arrows_and_gold(self):
        m=spawn(bow=.9,ammo=.21,ring=0,selected='anel_impacto')
        m['flechas']=13; m['municao_arqueiro']['ammo_count']=13; m['hp']=0
        r=S.GameRoom('ARCHER_LOOT'); r.phase='playing'; r.map_w=r.map_h=10
        r.tiles=[[S.FLOOR]*10 for _ in range(10)]; r.monsters[m['id']]=m
        async def noop(*args,**kwargs): pass
        r.gm_say=r.broadcast=r.push_state=r.send_to=noop
        with patch.object(S.random,'randint',side_effect=lambda a,b: 5 if (a,b)==(5,10) else 1), \
                patch.object(S,'CHANCE_COMIDA_MONSTRO',0):
            await r._monster_dies(m,None)
        chest=next(iter(r.chests.values()))
        self.assertEqual(chest['gold'],5)
        ids=[i['id'] for i in chest['items']]
        self.assertIn('longbow',ids); self.assertIn('anel_impacto',ids)
        self.assertNotIn('arco_curto',ids)
        arrows=[i for i in chest['items'] if i['id']=='flechas_magicas']
        self.assertEqual(sum(i['ammo_count'] for i in arrows),13)
        self.assertTrue(all(i['ammo_count']<=10 for i in arrows))

if __name__=='__main__': unittest.main()
