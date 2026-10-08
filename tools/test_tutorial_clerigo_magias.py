"""Fatia 16: na sala exclusiva do Clérigo as magias não gastam slots e a trilha ensina a lançá-las.

Roda da raiz: python tools/test_tutorial_clerigo_magias.py
Handler real (`handle_magia`/`handle_move`) e `push_state` REAL (payload completo de `game_state`).
"""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

D = S.carregar_dungeon('campo_de_treinamento.json')
DENTRO = [34, 6]         # sala 35 (x31..37, y4..8)
BORDA = [31, 6]          # primeira casa de piso junto da porta
PORTA = [30, 6]          # porta: fora da sala (a sala só tem as casas de piso)
CORREDOR = [29, 6]

# Magias de círculos diferentes que o Clérigo tem em jogo: (id, argumentos extras).
MAGIAS = {"primeiro": ("abencoar_arma", {"target_id": "hero"}),
          "segundo": ("protecao_energia", {}),
          "terceiro": ("definhar", {"tx": 34, "ty": 7}),
          "quarto": ("olhar_petrificante", {})}


def sala(cls="cleric", training=True):
    r = S.GameRoom('SLOTS_TEST')
    p = S.make_player('hero', 'Lewis', cls, 0)
    r.players[p['id']] = p
    r.load_authored_dungeon(deepcopy(D))
    r.training_mode = training
    r.phase = 'playing'
    r._is_turn = lambda pid: True
    r.msgs, r.erros = [], []

    async def send(pid, msg):
        r.msgs.append(msg)
        if isinstance(msg, dict) and msg.get('type') == 'error':
            r.erros.append(msg.get('msg'))

    async def broadcast(msg, *a, **k):
        r.msgs.append(msg)

    async def noop(*a, **k):
        pass
    r.send_to = send; r.broadcast = broadcast; r.gm_say = noop; r._broadcast_dado = noop
    p['magias_conhecidas'] = [m for m, _ in MAGIAS.values()]
    p['level'] = 7
    p['fome'] = p['sede'] = 100
    p['pos'] = list(DENTRO)
    return r, p


def esgotar(r, p):
    mx = S.slots_max_para(p)
    p['slots_cooldown'] = {c: [r.round_num + 50] * mx.get(c, 0) for c in S.SLOT_REGEN}
    return {c: list(v) for c, v in p['slots_cooldown'].items()}


def avisos(r):
    return [m['motivo'] for m in r.msgs if m.get('type') == 'licao_dica'
            and str(m.get('motivo', '')).startswith('slots_treino')]


class ClerigoSlotsTreino(unittest.IsolatedAsyncioTestCase):
    async def lancar(self, r, p, circulo):
        p['action_done'] = False
        p['bonus_action_used'] = False
        p['moves_left'] = 6
        antes = len(r.erros)
        mid, extra = MAGIAS[circulo]
        msg = {'magia_id': mid, **{k: (p['id'] if v == 'hero' else v) for k, v in extra.items()}}
        await r.handle_magia(p['id'], msg)
        return r.erros[antes:]

    def test_helper_regra(self):
        r, p = sala()
        self.assertTrue(r._slots_livres_treino(p))
        self.assertTrue(r._slots_livres_treino(p, BORDA))
        self.assertFalse(r._slots_livres_treino(p, PORTA))
        self.assertFalse(r._slots_livres_treino(p, CORREDOR))
        self.assertFalse(r._slots_livres_treino(p, [-1, -1]))
        r2, p2 = sala(training=False)
        self.assertFalse(r2._slots_livres_treino(p2))
        r4, p4 = sala()
        p4['test_hero'] = True
        self.assertFalse(r4._slots_livres_treino(p4))
        r5, p5 = sala()
        p5['pos'] = [24, 3]                                         # sala do Guerreiro
        self.assertFalse(r5._slots_livres_treino(p5))

    def test_cada_classe_so_na_propria_sala(self):
        r, p = sala('mage')
        p['pos'] = list(DENTRO)
        self.assertFalse(r._slots_livres_treino(p))                 # Mago na sala do Clérigo
        r, p = sala('cleric')
        p['pos'] = [24, 24]
        self.assertFalse(r._slots_livres_treino(p))                 # Clérigo na sala do Mago
        r, p = sala('warrior')
        p['pos'] = list(DENTRO)
        self.assertFalse(r._slots_livres_treino(p))
        r, p = sala('mage')
        p['pos'] = [24, 24]
        self.assertTrue(r._slots_livres_treino(p))                  # a regra do Mago segue

    async def test_na_sala_nao_gasta_mesmo_com_slots_zerados(self):
        r, p = sala()
        antes = esgotar(r, p)
        for circulo in MAGIAS:
            erros = await self.lancar(r, p, circulo)
            self.assertEqual(erros, [], (circulo, erros))
        self.assertEqual(p['slots_cooldown'], antes)

    async def test_fome_e_sede_continuam_sendo_cobradas(self):
        r, p = sala()
        esgotar(r, p)
        f0, s0 = p['fome'], p['sede']
        self.assertEqual(await self.lancar(r, p, 'primeiro'), [])
        self.assertTrue(p['fome'] < f0 or p['sede'] < s0)

    async def test_fora_da_sala_gasta_ou_recusa(self):
        r, p = sala()
        esgotar(r, p)
        p['pos'] = list(CORREDOR)
        self.assertEqual(len(await self.lancar(r, p, 'primeiro')), 1)   # sem slot: recusada
        r, p = sala()
        p['pos'] = list(CORREDOR)
        p['slots_cooldown'] = {c: [] for c in S.SLOT_REGEN}
        self.assertEqual(await self.lancar(r, p, 'primeiro'), [])
        self.assertEqual(len(p['slots_cooldown']['primeiro']), 1)

    async def test_transicao_sala_corredor_restaura(self):
        r, p = sala()
        p['slots_cooldown'] = {c: [] for c in S.SLOT_REGEN}
        p['slots_cooldown']['primeiro'] = [r.round_num + 7]
        antes = {c: list(v) for c, v in p['slots_cooldown'].items()}
        for circulo in MAGIAS:
            self.assertEqual(await self.lancar(r, p, circulo), [])
        p['pos'] = list(CORREDOR)
        r._slot_prune(p, 'primeiro')
        self.assertEqual(p['slots_cooldown'], antes)
        self.assertEqual(len(await self.lancar(r, p, 'primeiro')), 0)
        self.assertEqual(len(p['slots_cooldown']['primeiro']), 2)

    async def test_habilidades_de_classe_nao_mudam(self):
        """Cura gasta água, não slot: nada de novo na sala; slots intactos."""
        r, p = sala()
        antes = esgotar(r, p)
        ally = next(iter(r.training_allies.values()))
        ally['pos'] = [p['pos'][0] + 1, p['pos'][1]]
        ally['hp'] = 3
        p['action_done'] = False
        s0 = p['sede']
        await r.handle_cura(p['id'], {'target_id': ally['id'], 'num_dados': 1, 'alcance_extra': 0})
        self.assertEqual(p['slots_cooldown'], antes)
        self.assertLess(p['sede'], s0)

    async def test_payload_push_state_real(self):
        r, p = sala()
        antes = esgotar(r, p)
        eu = next(x for x in r._game_state_payload()['players'] if x['id'] == p['id'])
        self.assertTrue(eu['slots_livres_treino'])
        for c in S.slots_max_para(p):
            self.assertEqual(eu['slots_remaining'][c], [], c)
        self.assertEqual(p['slots_cooldown'], antes)
        p['pos'] = list(CORREDOR)
        eu = next(x for x in r._game_state_payload()['players'] if x['id'] == p['id'])
        self.assertFalse(eu['slots_livres_treino'])
        self.assertEqual(len(eu['slots_remaining']['primeiro']), S.slots_max_para(p)['primeiro'])
        r.msgs.clear()
        p['pos'] = list(DENTRO)
        await r.push_state()
        gs = [m for m in r.msgs if m.get('type') == 'game_state'][-1]
        self.assertTrue(next(x for x in gs['players'] if x['id'] == p['id'])['slots_livres_treino'])

    async def test_avisos_so_nas_transicoes(self):
        r, p = sala()
        r._room_by_id(35)['locked'] = False
        p['pos'] = list(BORDA)
        p['moves_left'] = 9
        await r.handle_open_door(p['id'], 30, 6)
        r.msgs.clear()
        await r.handle_move(p['id'], 1, 0)                          # dentro -> dentro
        await r.handle_move(p['id'], -1, 0)
        self.assertEqual(avisos(r), [])
        await r.handle_move(p['id'], -1, 0)                         # borda -> porta
        self.assertEqual(p['pos'], PORTA)
        self.assertEqual(avisos(r), ['slots_treino_desliga'])
        await r.handle_move(p['id'], -1, 0)                         # porta -> corredor
        self.assertEqual(avisos(r), ['slots_treino_desliga'])
        await r.handle_move(p['id'], 1, 0)
        await r.handle_move(p['id'], 1, 0)                          # porta -> sala
        self.assertEqual(p['pos'], BORDA)
        self.assertEqual(avisos(r), ['slots_treino_desliga', 'slots_treino_liga'])

    async def test_grupo_cada_heroi_pela_propria_posicao(self):
        r, p = sala()
        q = S.make_player('hero2', 'Lewis2', 'cleric', 1)
        q['pos'] = list(CORREDOR)
        r.players[q['id']] = q
        self.assertTrue(r._slots_livres_treino(p))
        self.assertFalse(r._slots_livres_treino(q))

    def test_sem_estado_novo_na_foto(self):
        r, p = sala()
        antes = set(vars(r)); chaves = set(p)
        r._slots_livres_treino(p)
        self.assertEqual(antes, set(vars(r)))
        self.assertEqual(chaves, set(p))


class LicoesDoClerigo(unittest.TestCase):
    def fala(self, i):
        return next(x for x in D['falas'] if x['id'] == i)

    def test_ordens_estritas_e_unicas(self):
        ordens = [x['ordem'] for x in D['falas'] if x.get('classe') == 'cleric']
        self.assertEqual(len(ordens), len(set(ordens)))
        self.assertEqual(sorted(ordens), list(range(1, len(ordens) + 1)))

    def test_licao_de_magia_vem_antes_das_habilidades(self):
        g = self.fala('treino_grimorio')
        self.assertEqual(g['classe'], 'cleric')
        self.assertTrue(g['sala_exclusiva'])
        self.assertEqual(g['tarefa']['tipo'], 'usar_magia')
        self.assertEqual(g['requisitos'], {'magia_tipo': 'qualquer'})
        self.assertIn('não gastam', g['texto'])
        self.assertEqual(g['ordem'], self.fala('porta_cleric')['ordem'] + 1)
        self.assertLess(g['ordem'], self.fala('treino_cura')['ordem'])
        t = self.fala('treino_grimorio_turno')
        self.assertEqual(t['tarefa']['tipo'], 'encerrar_turno')
        self.assertIn('não gastam', t['texto'])
        self.assertEqual(t['ordem'], g['ordem'] + 1)
        self.assertIn('não gastam', self.fala('porta_cleric')['texto'])

    def test_guia_do_grimorio(self):
        g = self.fala('treino_grimorio')
        self.assertEqual(g['guia'][0]['ui'], 'botao:magias')
        self.assertIsNone(g['guia'][-1].get('conclui_com'))


class LicaoConcluiPorMagia(unittest.IsolatedAsyncioTestCase):
    async def test_usar_magia_conclui(self):
        r, p = sala()
        r._training_add_unlocked_lessons()
        lic = next(l for l in r.licoes if l['id'] == 'treino_grimorio')
        self.assertTrue(r._training_requirements(p, lic))
        p['licao_atual'] = lic['id']
        await r._licao_evento(p, 'usar_magia', alvo='protecao_energia')
        self.assertIn('treino_grimorio', p['licoes_feitas'])

    async def test_sem_magia_conhecida_nao_trava(self):
        r, p = sala()
        p['magias_conhecidas'] = []
        lic = next(l for l in r.licoes if l['id'] == 'treino_grimorio')
        self.assertFalse(r._training_requirements(p, lic))


# --- Fatia 17: o aprendiz é alvo de magia de aliado; erro de mira não conclui a lição -----------------
ALIADO = [('abencoar_arma', 'abencoar_arma'), ('saciar', 'saciar'), ('visao_escuro', 'visao_escuro'),
          ('voo', 'voo'), ('regeneracao_magica', 'regeneracao_magica')]


class AprendizComoAlvoDeMagia(unittest.IsolatedAsyncioTestCase):
    async def lancar(self, r, p, mid, **msg):
        p['action_done'] = False
        p['bonus_action_used'] = False
        p['moves_left'] = 6
        p['magias_conhecidas'] = [mid]
        antes = len(r.erros)
        await r.handle_magia(p['id'], {'magia_id': mid, **msg})
        return r.erros[antes:]

    async def test_magia_de_aliado_aceita_o_aprendiz_da_propria_sala(self):
        for mid, _ in ALIADO:
            r, p = sala()
            p['pos'] = [33, 6]
            ap = r.training_allies['__treino_cleric_1']
            self.assertEqual(ap['pos'], [34, 6])
            erros = await self.lancar(r, p, mid, target_id=ap['id'], tx=34, ty=6)
            self.assertEqual(erros, [], (mid, erros))

    async def test_aprendiz_de_outra_classe_ou_fora_da_sala_continua_invalido(self):
        r, p = sala()
        p['pos'] = [33, 6]
        erros = await self.lancar(r, p, 'abencoar_arma', target_id='__treino_bard_1')
        self.assertEqual(len(erros), 1)
        r, p = sala()
        p['pos'] = list(CORREDOR)                          # fora da sala do Clérigo
        erros = await self.lancar(r, p, 'abencoar_arma', target_id='__treino_cleric_1')
        self.assertEqual(len(erros), 1)

    async def test_erro_de_mira_nao_conclui_a_licao_nem_gasta_a_acao(self):
        r, p = sala()
        r._training_add_unlocked_lessons()
        lic = next(l for l in r.licoes if l['id'] == 'treino_grimorio')
        p['licao_atual'] = lic['id']
        erros = await self.lancar(r, p, 'abencoar_arma', target_id='nao_existe')
        self.assertEqual(len(erros), 1)
        self.assertNotIn('treino_grimorio', p['licoes_feitas'])
        self.assertFalse(p['action_done'])                  # a ação volta: dá para mirar de novo

        erros = await self.lancar(r, p, 'abencoar_arma', target_id=p['id'])
        self.assertEqual(erros, [])
        self.assertIn('treino_grimorio', p['licoes_feitas'])
        self.assertTrue(p['action_done'])


class GuiaDoGrimorioDizOQueFazer(unittest.TestCase):
    def passos(self):
        return next(x for x in D['falas'] if x['id'] == 'treino_grimorio')['guia']

    def test_aponta_para_a_aba_que_existe_no_desktop(self):
        game = (Path(__file__).resolve().parents[1] / 'game.js').read_text(encoding='utf-8')
        # o ✨ flutuante só existe em tela estreita: no desktop o halo precisa de uma aba visível
        import re
        abas = re.findall(r'<button[^>]*trocarAbaPainel\(.magias.\)[^>]*>', game)
        self.assertEqual(len(abas), 2)                      # Mago e Clérigo
        for a in abas:
            self.assertIn('data-guia="botao:magias"', a)

    def test_textos_falam_da_aba_e_do_alvo(self):
        passos = self.passos()
        g = S.GUIA_LANG if hasattr(S, 'GUIA_LANG') else None
        lang = (Path(__file__).resolve().parents[1] / 'src/lang/tutorial_guia.js').read_text(encoding='utf-8')
        self.assertIn('aba', lang.split('treino_grimorio.grimorio.texto')[1][:120].lower())
        pt = lang.split('treino_grimorio.lancar.texto')[1][:260]
        self.assertIn('aprendiz', pt)
        self.assertIn('casa livre', pt)
        self.assertEqual(len(passos), 2)


if __name__ == '__main__':
    unittest.main()
