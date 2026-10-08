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

ALVO = [32, 25]   # a casa de chão logo à frente da porta [31,25], ortogonal a ela
LICAO = 'treino_guiar_refem'
CAMINHO = [[0, -1], [-1, 0], [-1, 0], [-1, 0], [0, 1]]   # 35,25 -> 35,24 -> 34,24 -> 33,24 -> 32,24 -> 32,25


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

    def test_alvo_fica_na_frente_da_porta(self):
        sala = next(r for r in D['rooms'] if r.get('allowed_class') == 'paladin')
        porta = sala['doors'][0]
        self.assertEqual(ALVO, [porta[0] + 1, porta[1]])           # ortogonal à porta, para dentro
        self.assertNotEqual(ALVO, D['prisoner']['pos'])
        fala = {f['id']: f for f in D['falas']}[LICAO]
        self.assertNotEqual(ALVO, fala['pos'])                      # nem a casa onde o herói costuma ficar
        guia = fala['guia']
        self.assertEqual(guia[-1]['ui'], 'casa:[32,25]')
        self.assertEqual(guia[0].get('conclui_com'), {'tipo': 'encerrar_turno'})
        # o refém (movimento 6) alcança a casa mesmo com o herói parado ao lado dele
        self.assertLessEqual(len(CAMINHO), 6)

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
        r.prisoner['pos'] = [33, 25]; p['pos'] = [34, 25]
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


# ── Fluxo COMPLETO como o jogador faz: iniciativa e push_state REAIS (sem _is_turn falso) ──────
async def _sala_real(heroi_em=(34, 25)):
    r = S.GameRoom('REFEM_REAL')
    p = S.make_player('hero', 'Aluno', 'paladin', 0)
    r.players[p['id']] = p; r.player_order = [p['id']]
    r.load_authored_dungeon(deepcopy(D)); r.phase = 'playing'
    r.msgs = []
    async def send(pid, msg): r.msgs.append(msg)
    async def bc(msg, **k): r.msgs.append(msg)
    async def noop(*a, **k): pass
    r.send_to = send; r.broadcast = bc; r.gm_say = noop
    r._intro_masmorra_bloqueada = lambda: False
    r._rebuild_initiative(); r.initiative_active = True
    done = [f['id'] for f in r.licoes if f.get('classe') == 'paladin'
            and f['ordem'] < next(x for x in r.licoes if x['id'] == 'treino_refem')['ordem']]
    p['licoes_feitas'] = done; p['licao_progresso'] = {i: 1 for i in done}
    p['pos'] = list(heroi_em)
    await r._verificar_falas(p, r._room_containing_point(p['pos']))
    assert p['licao_atual'] == 'treino_refem', p['licao_atual']
    return r, p


async def _esperar_vez(r, pid):
    for _ in range(400):
        if r.current_pid() == pid or r.animados_phase_pid == pid:
            return
        await asyncio.sleep(0.02)
    raise AssertionError('a vez do herói não voltou')


def _erros(r):
    out = [str(m['msg']) for m in r.msgs if m.get('type') == 'error']
    r.msgs.clear()
    return out


async def _etapa1(r, p):
    """Libertar, Protetor, Imposição das Mãos — a ordem do usuário."""
    pid = p['id']
    await r.handle_libertar_prisioneiro(pid)
    assert p['licao_atual'] == 'treino_protetor'
    await r.handle_protetor(pid, {'target_id': '__prisioneiro__'})
    await r.handle_end_turn(pid)                    # a demonstração fere o refém; abre a vez dele
    assert p['licao_atual'] == 'treino_maos'
    await r.handle_end_turn(pid)                    # passa a vez do refém
    await _esperar_vez(r, pid)
    await r.handle_imposicao_maos(pid, {'target_id': '__prisioneiro__'})
    assert p['licao_atual'] == 'treino_guiar_refem', p['licao_atual']


class FluxoRealTests(unittest.IsolatedAsyncioTestCase):
    async def test_etapa1_ordem_protetor_depois_imposicao(self):
        r, p = await _sala_real()
        pid = p['id']
        await r.handle_libertar_prisioneiro(pid)
        r.prisoner['hp'] = 3
        p['action_done'] = False
        await r.handle_imposicao_maos(pid, {'target_id': '__prisioneiro__'})
        self.assertEqual(p['licao_atual'], 'treino_protetor')   # curar antes do Protetor não cumpre nada
        self.assertNotIn('treino_maos', p['licoes_feitas'])

    async def test_refem_anda_ate_a_frente_da_porta_e_some(self):
        r, p = await _sala_real()
        await _etapa1(r, p)
        pid = p['id']
        await r.handle_end_turn(pid)                              # passo 1 do guia: abre a vez do refém
        self.assertEqual(r.animados_phase_pid, pid)
        self.assertEqual(r.prisoner['moves_left'], 6)
        self.assertEqual(r._animados_atual(pid), 'prisoner')      # já vem selecionado para o cliente
        self.assertEqual(r._game_state_payload()['animados_atual'][pid], 'prisoner')
        await r.handle_mover_prisioneiro_caminho(pid, CAMINHO)     # o que o clique na casa envia
        self.assertEqual(_erros(r), [])
        self.assertIsNone(r.prisoner)
        self.assertIn(LICAO, p['licoes_feitas'])
        self.assertEqual(p['licao_atual'], 'treino_sagrado')
        self.assertIsNone(r.animados_phase_pid)
        await _esperar_vez(r, pid)
        self.assertEqual(r.current_pid(), pid)                    # o herói segue jogando

    async def test_heroi_parado_na_casa_destino_nao_trava_para_sempre(self):
        r, p = await _sala_real()
        await _etapa1(r, p)
        pid = p['id']
        p['pos'] = list(ALVO)                                      # o herói está na casa marcada
        await r.handle_end_turn(pid)
        await r.handle_mover_prisioneiro_caminho(pid, CAMINHO)
        self.assertIsNotNone(r.prisoner)                           # não pisa em cima do herói
        self.assertEqual(r.prisoner['pos'], [32, 24])
        self.assertEqual(p['licao_atual'], LICAO)
        await r.handle_end_turn(pid)                               # fecha a vez do refém
        await _esperar_vez(r, pid)
        p['pos'] = [33, 25]                                        # o herói sai da casa (dica do guia)
        await r.handle_end_turn(pid)
        await r.handle_mover_prisioneiro_caminho(pid, [[0, 1]])
        self.assertIsNone(r.prisoner)
        self.assertEqual(p['licao_atual'], 'treino_sagrado')

    async def test_repetir_tutorial_apos_fluxo_real_devolve_o_refem(self):
        r, p = await _sala_real()
        await _etapa1(r, p)
        await r.handle_end_turn(p['id'])
        await r.handle_mover_prisioneiro_caminho(p['id'], CAMINHO)
        self.assertIsNone(r.prisoner)
        await _esperar_vez(r, p['id'])
        p['pos'] = [33, 25]
        await r.handle_repetir_tutorial(p['id'])
        self.assertIsNotNone(r.prisoner)
        self.assertEqual(p['licao_atual'], 'treino_refem')


if __name__ == '__main__':
    unittest.main()
