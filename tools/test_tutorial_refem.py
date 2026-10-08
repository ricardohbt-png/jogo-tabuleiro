"""Fatia 9: guiar o refém até a casa marcada e dispensá-lo (Paladino, Campo de Treinamento)."""
import asyncio
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as S
from test_tutorial_salas import room, lesson, D

ALVO = [32, 24]
LICAO = 'treino_guiar_refem'
CAMINHO = [[0, -1], [-1, 0], [-1, 0], [-1, 0]]   # 35,25 -> 35,24 -> 34,24 -> 33,24 -> 32,24


def _abrir_janela(r, p):
    r.prisoner.update(freed=True, rescuer_pid=p['id'], moves_left=6)
    r.animados_phase_pid = p['id']
    r.animados_order = []; r.animados_done = set(); r.prisioneiro_done = False


async def _ate_guiar(cls='paladin'):
    r, p = room(cls)
    await lesson(r, p, LICAO, [33, 25])
    _abrir_janela(r, p)
    return r, p


class ConteudoTests(unittest.TestCase):
    def test_licao_no_json(self):
        fala = {f['id']: f for f in D['falas']}
        l = fala[LICAO]
        self.assertEqual(l['tarefa']['tipo'], 'guiar_refem')
        self.assertEqual(l['tarefa']['alvo'], ALVO)
        self.assertEqual(l['classe'], 'paladin')
        self.assertTrue(l.get('sala_exclusiva'))
        self.assertEqual(D['tiles'][ALVO[1]][ALVO[0]], S.FLOOR)
        self.assertNotEqual(ALVO, D['prisoner']['pos'])
        self.assertEqual(S.validar_dungeon(D), (True, 'ok'))

    def test_ordens_estritas_e_sem_buraco(self):
        ls = sorted((f for f in D['falas'] if f.get('classe') == 'paladin'), key=lambda f: f['ordem'])
        self.assertEqual([f['ordem'] for f in ls], list(range(1, len(ls) + 1)))
        ids = [f['id'] for f in ls]
        i = ids.index(LICAO)
        self.assertEqual(ids[i - 1], 'treino_maos')
        self.assertEqual(ids[i + 1], 'treino_sagrado')
        self.assertEqual(ids[-1], 'volta_paladin')

    def test_verbo_no_servidor_e_alvo_de_casa(self):
        self.assertIn('guiar_refem', S.LICAO_VERBOS)
        self.assertIn('guiar_refem', S.LICAO_VERBOS_CASA)


class FluxoTests(unittest.IsolatedAsyncioTestCase):
    async def test_refem_agora_anda_dentro_da_sala(self):
        r, p = await _ate_guiar()
        await r.handle_mover_prisioneiro(p['id'], -1, 0)
        self.assertEqual(r.prisoner['pos'], [34, 25])

    async def test_refem_nao_sai_da_sala(self):
        r, p = await _ate_guiar()
        r.prisoner['pos'] = [32, 25]
        await r.handle_mover_prisioneiro(p['id'], -1, 0)   # 31,25 = porta
        self.assertEqual(r.prisoner['pos'], [32, 25])

    async def test_guiar_ate_a_casa_conclui_dispensa_e_premia(self):
        r, p = await _ate_guiar()
        avancos = []
        async def adv(): avancos.append(1)
        r._advance_initiative = adv
        ouro = p['gold']; xp = p['xp']
        await r.handle_mover_prisioneiro_caminho(p['id'], CAMINHO)
        self.assertIsNone(r.prisoner)
        self.assertIn(LICAO, p['licoes_feitas'])
        self.assertIn(LICAO, p['tutorial_history'])
        self.assertEqual(p['gold'], ouro + S.TUTORIAL_RECOMPENSA_OURO)
        self.assertEqual(p['xp'] - xp, S.TUTORIAL_RECOMPENSA_XP)
        self.assertFalse(r.rescue_failed)
        self.assertEqual(p['licao_atual'], 'treino_sagrado')
        self.assertIsNone(r.animados_phase_pid)   # a janela do refém fechou
        self.assertEqual(avancos, [1])
        pay = r._game_state_payload()
        self.assertIsNone(pay['prisoner'])

    async def test_passo_a_passo_tambem_dispensa(self):
        r, p = await _ate_guiar()
        r._advance_initiative = lambda: asyncio.sleep(0)
        r.prisoner['pos'] = [33, 24]
        await r.handle_mover_prisioneiro(p['id'], -1, 0)
        self.assertIsNone(r.prisoner)
        self.assertIn(LICAO, p['licoes_feitas'])

    async def test_casa_errada_nao_conclui(self):
        r, p = await _ate_guiar()
        await r.handle_mover_prisioneiro_caminho(p['id'], [[-1, 0]])
        self.assertIsNotNone(r.prisoner)
        self.assertEqual(p['licao_atual'], LICAO)

    async def test_seguintes_nao_dependem_do_refem(self):
        r, p = await _ate_guiar()
        r._advance_initiative = lambda: asyncio.sleep(0)
        await r.handle_mover_prisioneiro_caminho(p['id'], CAMINHO)
        for lid in ('treino_sagrado', 'treino_sagrado_golpe', 'treino_regen', 'treino_luz', 'volta_paladin'):
            l = next(f for f in r.licoes if f['id'] == lid)
            self.assertNotIn('__prisioneiro__', json.dumps(l['tarefa']))
        self.assertTrue(r._licao_liberada(p, next(f for f in r.licoes if f['id'] == 'treino_sagrado')))

    async def test_dispensar_sem_refem_ou_fora_do_treino_nao_quebra(self):
        r, p = room('paladin')
        r.prisoner = None
        await r._dispensar_prisioneiro(p)          # no-op
        self.assertIsNone(r.prisoner)

    async def test_repetir_tutorial_devolve_o_refem(self):
        r, p = await _ate_guiar()
        r._advance_initiative = lambda: asyncio.sleep(0)
        await r.handle_mover_prisioneiro_caminho(p['id'], CAMINHO)
        self.assertIsNone(r.prisoner)
        p['pos'] = [33, 25]
        await r.handle_repetir_tutorial(p['id'])
        self.assertIsNotNone(r.prisoner)
        self.assertEqual(r.prisoner['pos'], D['prisoner']['pos'])
        self.assertFalse(r.prisoner['freed'])
        self.assertTrue(r.prisoner['training_refem'])
        self.assertEqual(p['licao_atual'], 'treino_refem')
        self.assertIn(LICAO, p['tutorial_history'])

    async def test_repetir_com_refem_vivo_recoloca_na_origem(self):
        r, p = room('paladin')
        await lesson(r, p, 'treino_refem', [34, 25])
        r.prisoner.update(freed=True, pos=[33, 24], hp=2)
        await r.handle_repetir_tutorial(p['id'])
        self.assertEqual(r.prisoner['pos'], D['prisoner']['pos'])
        self.assertEqual(r.prisoner['hp'], r.prisoner['max_hp'])

    async def test_foto_com_refem_dispensado_roundtrip(self):
        r, p = await _ate_guiar()
        r._advance_initiative = lambda: asyncio.sleep(0)
        await r.handle_mover_prisioneiro_caminho(p['id'], CAMINHO)
        body = S.foto_desempacotar(S.foto_empacotar(r._montar_foto(), onde='masmorra'))
        self.assertIsNone(body['sala']['prisoner'])
        fresh, q = room('paladin')
        restored = fresh._foto_aplicar_sala(body, {'paladin': 'nova'}, D)
        self.assertIsNone(fresh.prisoner)
        fresh.players = {'nova': restored['herois']['paladin']}
        q = fresh.players['nova']; q['id'] = 'nova'; q['pos'] = [33, 25]
        await fresh.handle_repetir_tutorial('nova')
        self.assertIsNotNone(fresh.prisoner)       # o molde viajou na foto


if __name__ == '__main__':
    unittest.main()
