"""Fluxos reais das seis salas; dados isolados, sem escrever saves do usuário."""
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

D = S.carregar_dungeon('campo_de_treinamento.json')

def room(cls):
    r = S.GameRoom('TRAIN_TEST')
    p = S.make_player('hero', 'Aluno', cls, 0)
    r.players[p['id']] = p
    r.load_authored_dungeon(deepcopy(D))
    r.phase = 'playing'; r._is_turn = lambda pid: True
    r.messages = []
    async def send(pid, msg): r.messages.append(msg)
    async def broadcast(msg): r.messages.append(msg)
    async def noop(*args, **kw): pass
    r.send_to = send; r.broadcast = broadcast; r.gm_say = noop; r.push_state = noop
    return r, p

async def lesson(r, p, ident, pos=None):
    target = next(f for f in r.licoes if f['id'] == ident)
    done = [f['id'] for f in r.licoes if f.get('classe') == p['class_id']
            and f.get('ordem', 0) < target['ordem']]
    p['licoes_feitas'] = done
    p['licao_progresso'] = {ident: 1 for ident in done}
    p['licao_atual'] = None
    p['pos'] = list(pos or target['pos'])
    p['action_done'] = False; p['bonus_action_used'] = False
    await r._verificar_falas(p, r._room_containing_point(p['pos']))
    if p['licao_atual'] != ident:
        raise AssertionError((ident, p['licao_atual']))

class TrainingTests(unittest.IsolatedAsyncioTestCase):
    def test_authored_map(self):
        self.assertEqual(S.validar_dungeon(D), (True, 'ok'))
        for cls in S.LICAO_CLASSES:
            rooms = [r for r in D['rooms'] if r.get('allowed_class') == cls]
            self.assertEqual(len(rooms), 1)
            for m in D['monsters']:
                x,y=m['pos']; r=rooms[0]
                if r['x']<=x<r['x']+r['w'] and r['y']<=y<r['y']+r['h']:
                    self.assertEqual(m['room_id'], r['id'])
        for f in D['falas']:
            if (f.get('tarefa') or {}).get('tipo') == 'mover_ate':
                x,y=f['tarefa']['alvo']; self.assertNotEqual(D['tiles'][y][x], S.WALL)

    async def test_all_class_access_pairs(self):
        for cls in S.LICAO_CLASSES:
            r,p=room(cls)
            for own in [x for x in r.rooms if x.get('allowed_class')]:
                for locked in [True,False]:
                    own['locked']=locked
                    for pos in [[own['x']+1,own['y']+1],own['doors'][0]]:
                        self.assertEqual(await r._training_check_entry(p['id'],p,*pos), cls==own['allowed_class'])
            self.assertIsNone(r._training_room(p,5,15))

    async def test_move_door_flight_and_teleport_are_blocked(self):
        r,p=room('mage'); p['pos']=[22,8]; p['moves_left']=5
        p['voo']=True; p['ignora_obstaculos_voo']=True
        await r.handle_move(p['id'],0,-1)
        self.assertEqual(p['pos'],[22,8]);self.assertEqual(p['moves_left'],5)
        await r.handle_open_door(p['id'],22,7)
        self.assertTrue(r._room_by_id(40)['locked'])
        r._room_by_id(40)['locked']=False
        self.assertFalse(r._teleporte_destino_livre(20,4,p))
        self.assertNotIn(r._saida_teletransporte_livre(p,[20,4]), [[x,y] for x in range(19,25) for y in range(1,7)])
        a={'id':'servant','owner':p['id'],'pos':[22,8],'vida_atual':8,'moves_left':5}
        p['animados']=[a];r.animados_phase_pid=p['id']
        await r.handle_mover_animado(p['id'],a['id'],0,-1)
        self.assertEqual(a['pos'],[22,8])
        self.assertFalse(r._tile_livre_para_animado(22,7,a['id'],a['pos']))

    async def test_richard_rescue_protect_and_heal(self):
        r,p=room('paladin')
        await lesson(r,p,'treino_refem',[34,25])
        await r.handle_libertar_prisioneiro(p['id'])
        self.assertTrue(r.prisoner['freed'])
        self.assertEqual(p['licao_atual'],'treino_protetor')
        await r._training_end_turn(p)
        self.assertEqual(r.prisoner['hp'],7)
        await r.handle_protetor(p['id'],{'target_id':'__prisioneiro__'})
        hp=p['hp'];await r._training_end_turn(p)
        self.assertEqual(r.prisoner['hp'],3)
        self.assertEqual(p['hp'],hp-1)
        self.assertTrue(r.prisoner['alive']);self.assertTrue(p['alive'])
        self.assertEqual(p['licao_atual'],'treino_maos')
        p['action_done']=False
        await r.handle_imposicao_maos(p['id'],{'target_id':p['id']})
        self.assertEqual(p['licao_atual'],'treino_maos')
        await r.handle_imposicao_maos(p['id'],{'target_id':'__prisioneiro__'})
        self.assertGreater(r.prisoner['hp'],3)
        self.assertEqual(p['licao_atual'],'treino_guiar_refem')
        self.assertFalse(r.mission_complete_pending)

    async def test_heal_before_protection_does_not_complete(self):
        r,p=room('paladin');await lesson(r,p,'treino_maos',[34,25])
        r.prisoner.update(freed=True,hp=3)
        await r.handle_imposicao_maos(p['id'],{'target_id':'__prisioneiro__'})
        self.assertEqual(p['licao_atual'],'treino_maos')

    async def test_lewis_four_real_skills_in_solo(self):
        r,p=room('cleric')
        await lesson(r,p,'treino_cura',[34,6])
        await r.handle_cura(p['id'],{'target_id':'__treino_cleric_1','num_dados':1})
        self.assertEqual(p['licao_atual'],'treino_cura_area')
        self.assertEqual(len(r.players),1)
        p['action_done']=False
        await r.handle_cura_area(p['id'],{'num_dados':1})
        self.assertEqual(p['licao_atual'],'treino_purificar')
        self.assertTrue(r.training_allies['__treino_cleric_1']['cego'])
        p['action_done']=False
        await r.handle_purificacao(p['id'],{'target_id':'__treino_cleric_1','tipo':'veneno'})
        self.assertEqual(p['licao_atual'],'treino_ressuscitar')
        self.assertFalse(r.training_allies['__treino_cleric_1']['alive'])
        p['action_done']=False
        await r.handle_ressurreicao(p['id'],{'target_id':'__treino_cleric_1'})
        self.assertTrue(r.training_allies['__treino_cleric_1']['alive'])
        self.assertIn('treino_ressuscitar',p['licoes_feitas'])
        self.assertFalse(r.training_allies['__treino_cleric_1']['cego'])

    async def test_training_npcs_are_private(self):
        r,p=room('paladin');p['pos']=[34,6]
        self.assertIsNone(r._training_ally(p,'__treino_cleric_1'))
        self.assertEqual(len(r.players),1)
        self.assertNotIn('__treino_cleric_1',r._montar_foto()['herois'])

    async def test_mage_skips_incompatible_metamagic(self):
        r,p=room('mage');p['magias_conhecidas']=['raio_congelante']
        spells=[l for l in r.licoes if l['id']=='treino_estender_magia']
        self.assertFalse(r._training_requirements(p,spells[0]))
        await lesson(r,p,'treino_reviver')
        self.assertEqual(p['licao_atual'],'treino_reviver')
        self.assertIn('treino_cadaver_mago',r.corpses)

    async def test_new_unlocks_and_saved_history(self):
        r,p=room('warrior');p['tutorial_history']=['treino_mira']
        p['guild_owned']['especializacoes']=['guerreiro_mira_3']
        r.load_authored_dungeon(deepcopy(D))
        self.assertIn('treino_mira',p['licoes_feitas'])
        self.assertIn('treino_guild_guerreiro_mira_3',[l['id'] for l in r.licoes])
        self.assertNotIn('treino_guild_guerreiro_mira_2',[l['id'] for l in r.licoes])
        saved=S.snapshot_character(p)
        self.assertEqual(saved['tutorial_history'],['treino_mira'])

    async def test_snapshot_roundtrip_retains_the_exercise(self):
        r,p=room('paladin');await lesson(r,p,'treino_refem',[34,25])
        await r.handle_libertar_prisioneiro(p['id'])
        await r.handle_protetor(p['id'],{'target_id':'__prisioneiro__'})
        await r._training_end_turn(p)
        packed=S.foto_empacotar(r._montar_foto(),onde='masmorra')
        body=S.foto_desempacotar(packed)
        self.assertTrue(body['sala']['training_mode'])
        self.assertEqual(body['sala']['prisoner']['hp'],3)
        self.assertEqual(body['herois']['paladin']['licao_atual'],'treino_maos')
        fresh,q=room('paladin')
        restored=fresh._foto_aplicar_sala(body,{'paladin':'new_connection'},D)
        fresh.players={'new_connection':restored['herois']['paladin']}
        q=fresh.players['new_connection'];q['id']='new_connection'
        q['action_done']=False
        await fresh.handle_imposicao_maos(q['id'],{'target_id':'__prisioneiro__'})
        self.assertEqual(q['licao_atual'],'treino_guiar_refem')
        self.assertEqual(set(fresh.training_allies),{'__treino_cleric_1','__treino_cleric_2','__treino_bard_1'})

    async def test_repeat_room_keeps_history_and_other_classes(self):
        r,p=room('paladin');await lesson(r,p,'treino_refem',[34,25])
        await r.handle_libertar_prisioneiro(p['id'])
        self.assertIn('treino_refem',p['tutorial_history'])
        r.licoes_feitas.add('treino_cura')
        await r.handle_repetir_tutorial(p['id'])
        self.assertEqual(p['licao_atual'],'treino_refem')
        self.assertFalse(r.prisoner['freed'])
        self.assertIn('treino_cura',r.licoes_feitas)
        self.assertIn('treino_refem',p['tutorial_history'])

    async def test_warrior_real_attacks_and_extra(self):
        r,p=room('warrior');await lesson(r,p,'treino_mira',[23,3])
        m=next(m for m in r.monsters.values() if m['pos']==[24,3])
        with patch.object(S.random,'randint',return_value=20):
            await r.handle_attack(p['id'],m['id'],buffs=['mira_certeira'])
            self.assertEqual(p['licao_atual'],'treino_golpe')
            p['action_done']=False
            await r.handle_attack(p['id'],m['id'],buffs=['golpe_devastador'])
            self.assertEqual(p['licao_atual'],'treino_furia')
            p['action_done']=False
            await r.handle_attack(p['id'],m['id'],buffs=['furia_berserker'])
            self.assertEqual(p['licao_atual'],'treino_furia_extra')
            self.assertFalse(p['action_done'])
            await r.handle_attack(p['id'],m['id'])
            self.assertIn('treino_furia_extra',p['licoes_feitas'])

    async def test_rogue_detection_disarm_and_repeat(self):
        r,p=room('rogue');await lesson(r,p,'treino_detectar',[9,8])
        await r.handle_detectar_armadilhas(p['id'],{})
        self.assertEqual(p['licao_atual'],'treino_desarmar')
        xp=p['xp'];gold=p['gold']
        with patch.object(S.random,'randint',return_value=20):
            await r.handle_desarmar_armadilha(p['id'],{'tx':10,'ty':8})
        self.assertEqual(p['licao_atual'],'treino_esconder')
        self.assertEqual((p['xp'],p['gold']),(xp+S.TUTORIAL_RECOMPENSA_XP,gold+S.TUTORIAL_RECOMPENSA_OURO))  # so a recompensa da licao, sem XP/ouro de armadilha
        await r.handle_repetir_tutorial(p['id'])
        self.assertEqual(p['licao_atual'],'treino_detectar')
        self.assertFalse(p['detectar_ativo'])
        self.assertTrue(any(a['id']=='trap_treino_luccas' for a in r.armadilhas))

    async def test_rogue_last_poison_charge_counts(self):
        r,p=room('rogue');await lesson(r,p,'treino_veneno',[10,7])
        p['gear']['weapon']=deepcopy(S._DUNGEON_ITEM_CATALOG['dagger'])
        flask=next(i for i in p['bag'] if i.get('tutorial_loan'))
        await r.handle_veneno_rapido(p['id'],{'veneno_id':flask['veneno_id']})
        self.assertEqual(p['licao_atual'],'treino_veneno_golpe')
        m=next(m for m in r.monsters.values() if m['pos']==[11,7])
        with patch.object(S.random,'randint',return_value=20):
            await r.handle_attack(p['id'],m['id'])
        self.assertEqual(p['licao_atual'],'treino_criar')
        self.assertFalse(r._weapon_poison_slots(p))

    async def test_bard_maintenance_requires_upkeep(self):
        r,p=room('bard');await lesson(r,p,'treino_cancao',[11,23])
        await r.handle_ativar_cancao(p['id'],{'atributos':[S.CANCAO_ATRIBUTOS[0]['id']]})
        self.assertEqual(p['licao_atual'],'treino_cancao_manter')
        await r._licao_evento(p,'encerrar_turno')
        self.assertEqual(p['licao_atual'],'treino_cancao_manter')
        await r._cobrar_manutencao_cancao(p)
        self.assertEqual(p['licao_atual'],'treino_cancao_parar')
        await r.handle_desativar_cancao(p['id'])
        self.assertEqual(p['licao_atual'],'treino_provocar')

    async def test_mage_revives_real_corpse(self):
        r,p=room('mage');await lesson(r,p,'treino_reviver')
        with patch.object(S.random,'randint',return_value=1):
            await r.handle_animar_mortos(p['id'],{'cadaver_id':'treino_cadaver_mago'})
        self.assertEqual(p['licao_atual'],'treino_comando')
        self.assertEqual(len(p['animados']),1)
        self.assertTrue(p['animados'][0]['training_target'])
        r._training_cleanup()
        self.assertFalse(p['animados'])

    async def test_private_dummies_survive_and_award_nothing(self):
        r,p=room('mage')
        m=next(m for m in r.monsters.values() if m.get('training_class')=='mage')
        xp=p['xp'];gold=p['gold'];m['hp']=0
        await r._monster_dies(m,p['id'])
        self.assertGreater(m['hp'],0)
        self.assertEqual(p['xp'],xp);self.assertEqual(p['gold'],gold)

    async def test_multiplayer_spell_lessons_keep_class_room_and_history(self):
        r,p=room('mage');p['magias_conhecidas']=['raio_congelante']
        p['tutorial_history']=['treino_magia_mage_raio_congelante']
        q=S.make_player('friend','Lewis','cleric',1);q['magias_conhecidas']=['abencoar']
        r.players[q['id']]=q;r.load_authored_dungeon(deepcopy(D))
        magic=next(l for l in r.licoes if l['id']=='treino_magia_mage_raio_congelante')
        cleric=next(l for l in r.licoes if l['id']=='treino_magia_cleric_abencoar')
        self.assertEqual(r._room_containing_point(magic['pos'])['allowed_class'],'mage')
        self.assertEqual(r._room_containing_point(cleric['pos'])['allowed_class'],'cleric')
        self.assertIn(magic['id'],p['licoes_feitas'])
        self.assertNotIn(magic['id'],q['licoes_feitas'])

    async def test_rogue_hide_furtive_and_create(self):
        r,p=room('rogue');await lesson(r,p,'treino_esconder',[10,7])
        m=next(m for m in r.monsters.values() if m['pos']==[11,7])
        with patch.object(S.random,'randint',return_value=20):
            await r.handle_esconder_sombras(p['id'],{})
            self.assertEqual(p['licao_atual'],'treino_furtivo')
            await r.handle_attack(p['id'],m['id'])
            self.assertEqual(p['licao_atual'],'treino_veneno')
        await lesson(r,p,'treino_criar',[9,7])
        await r.handle_criar_armadilha(p['id'],{'tipo':'buraco','tx':9,'ty':8})
        self.assertIn('treino_criar',p['licoes_feitas'])

    async def test_mage_real_compatible_metamagic(self):
        r,p=room('mage');p['magias_conhecidas']=['raio_congelante','barreira_arcana']
        for ident,flag,magic in [('treino_aprimorar_magia','aprimorar_ativo','raio_congelante'),
                                 ('treino_estender_magia','estender_ativo','barreira_arcana'),
                                 ('treino_fortalecer_magia','fortalecer_ativo','raio_congelante')]:
            await lesson(r,p,ident,[23,24]);p[flag]=True
            r.round_num += 10
            r._processar_recarga_slots_rodada()
            m=next(m for m in r.monsters.values() if m['pos']==[24,24])
            await r.handle_magia(p['id'],{'magia_id':magic,'target_id':p['id'] if magic=='barreira_arcana' else m['id'],'tx':24,'ty':24})
            self.assertIn(ident,p['licoes_feitas'],r.messages[-3:])

    async def test_poison_loan_removed_on_exit(self):
        r,p=room('rogue');await lesson(r,p,'treino_veneno')
        flask=next(i for i in p['bag'] if i.get('tutorial_loan'))
        await r.handle_veneno_rapido(p['id'],{'veneno_id':flask['veneno_id']})
        self.assertTrue(r._weapon_poison_slots(p))
        r._training_cleanup()
        self.assertFalse(r._weapon_poison_slots(p))

if __name__=='__main__':unittest.main(verbosity=2)
