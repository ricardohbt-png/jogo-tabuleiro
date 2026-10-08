"""Fatia 15: na sala exclusiva do Mago do Campo de Treinamento as magias não gastam slots.

Roda da raiz: python tools/test_tutorial_mago_slots.py
Handler real (`handle_magia`/`handle_move`) e `push_state` REAL (payload completo de `game_state`).
"""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

D = S.carregar_dungeon('campo_de_treinamento.json')
DENTRO = [24, 24]        # sala 41 (x21..26, y22..27)
PORTA = [22, 21]         # porta da sala: fora da sala (a sala só tem as casas de piso)
CORREDOR = [22, 20]

# Uma magia implementada de cada círculo que o Mago tem em jogo (buffs de si mesmo: sem alvo).
MAGIAS = {"primeiro": "barreira_arcana", "segundo": "invisibilidade",
          "terceiro": "velocidade", "quarto": "olhar_petrificante"}


def sala(cls="mage", training=True):
    r = S.GameRoom('SLOTS_TEST')
    p = S.make_player('hero', 'Pedro', cls, 0)
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
    p['magias_conhecidas'] = list(MAGIAS.values())
    p['level'] = 5
    p['fome'] = p['sede'] = 100
    p['pos'] = list(DENTRO)
    return r, p


def esgotar(r, p):
    """Todos os slots de todos os círculos em recarga."""
    mx = S.slots_max_para(p)
    p['slots_cooldown'] = {c: [r.round_num + 50] * mx.get(c, 0) for c in S.SLOT_REGEN}
    return {c: list(v) for c, v in p['slots_cooldown'].items()}


def avisos(r):
    return [m['motivo'] for m in r.msgs if m.get('type') == 'licao_dica'
            and str(m.get('motivo', '')).startswith('slots_treino')]


class MagoSlotsTreino(unittest.IsolatedAsyncioTestCase):
    async def lancar(self, r, p, circulo):
        p['action_done'] = False
        p['bonus_action_used'] = False
        p['moves_left'] = 6
        antes = len(r.erros)
        await r.handle_magia(p['id'], {'magia_id': MAGIAS[circulo]})
        return r.erros[antes:]

    def test_helper_regra(self):
        r, p = sala()
        self.assertTrue(r._slots_livres_treino(p))
        self.assertFalse(r._slots_livres_treino(p, PORTA))          # a porta não é a sala
        self.assertFalse(r._slots_livres_treino(p, CORREDOR))
        self.assertFalse(r._slots_livres_treino(p, [-1, -1]))
        r2, p2 = sala(training=False)
        self.assertFalse(r2._slots_livres_treino(p2))               # masmorra normal nunca
        r3, p3 = sala('cleric')
        p3['pos'] = list(DENTRO)
        self.assertFalse(r3._slots_livres_treino(p3))               # só o Mago
        r4, p4 = sala()
        p4['test_hero'] = True
        self.assertFalse(r4._slots_livres_treino(p4))               # mesa de teste do editor
        r5, p5 = sala()
        p5['pos'] = [24, 3]                                         # sala do Guerreiro
        self.assertFalse(r5._slots_livres_treino(p5))

    async def test_na_sala_nao_gasta_mesmo_com_slots_zerados(self):
        r, p = sala()
        antes = esgotar(r, p)
        for circulo in MAGIAS:
            erros = await self.lancar(r, p, circulo)
            self.assertEqual(erros, [], (circulo, erros))
        self.assertEqual(p['slots_cooldown'], antes)
        self.assertEqual(p.get('cajado_arcano_slot_pronto_em', 0), 0)

    async def test_fome_e_sede_continuam_sendo_cobradas(self):
        r, p = sala()
        esgotar(r, p)
        f0, s0 = p['fome'], p['sede']
        self.assertEqual(await self.lancar(r, p, 'primeiro'), [])
        self.assertLess(p['fome'], f0)
        self.assertLess(p['sede'], s0)

    async def test_fora_da_sala_volta_ao_normal(self):
        r, p = sala()
        esgotar(r, p)
        p['pos'] = list(CORREDOR)
        erros = await self.lancar(r, p, 'primeiro')
        self.assertEqual(len(erros), 1)                             # sem slot: recusada
        # com um slot livre, gasta de verdade
        r, p = sala()
        p['pos'] = list(CORREDOR)
        p['slots_cooldown'] = {c: [] for c in S.SLOT_REGEN}
        self.assertEqual(await self.lancar(r, p, 'primeiro'), [])
        self.assertEqual(len(p['slots_cooldown']['primeiro']), 1)

    async def test_nada_a_restaurar_ao_sair(self):
        """Os slots de antes de entrar são os de depois de sair: a regra é 'não gasta'."""
        r, p = sala()
        p['slots_cooldown'] = {c: [] for c in S.SLOT_REGEN}
        p['slots_cooldown']['primeiro'] = [r.round_num + 7]         # 1 de 3 em recarga
        antes = {c: list(v) for c, v in p['slots_cooldown'].items()}
        for circulo in MAGIAS:
            self.assertEqual(await self.lancar(r, p, circulo), [])
        p['pos'] = list(CORREDOR)
        r._slot_prune(p, 'primeiro')
        self.assertEqual(p['slots_cooldown'], antes)

    async def test_metamagia_e_velocidade_na_sala(self):
        r, p = sala()
        antes = esgotar(r, p)
        p['metamagia_fortalecer'] = True
        p['metamagia_aprimorar'] = True
        self.assertEqual(await self.lancar(r, p, 'terceiro'), [])   # Velocidade
        self.assertEqual(p['slots_cooldown'], antes)

    async def test_payload_push_state_real(self):
        r, p = sala()
        antes = esgotar(r, p)
        estado = r._game_state_payload()
        eu = next(x for x in estado['players'] if x['id'] == p['id'])
        self.assertTrue(eu['slots_livres_treino'])
        for c in S.slots_max_para(p):
            self.assertEqual(eu['slots_remaining'][c], [], c)       # nenhum slot em recarga na tela
        self.assertEqual(p['slots_cooldown'], antes)                # o estado real não foi tocado
        p['pos'] = list(CORREDOR)
        eu = next(x for x in r._game_state_payload()['players'] if x['id'] == p['id'])
        self.assertFalse(eu['slots_livres_treino'])
        self.assertEqual(len(eu['slots_remaining']['primeiro']), S.slots_max_para(p)['primeiro'])

    async def test_push_state_real_via_broadcast(self):
        r, p = sala()
        esgotar(r, p)
        r.msgs.clear()
        await r.push_state()
        gs = [m for m in r.msgs if m.get('type') == 'game_state'][-1]
        eu = next(x for x in gs['players'] if x['id'] == p['id'])
        self.assertTrue(eu['slots_livres_treino'])

    async def test_avisos_so_nas_transicoes(self):
        r, p = sala()
        r._room_by_id(41)['locked'] = False
        p['pos'] = [22, 22]
        p['moves_left'] = 6
        await r.handle_open_door(p['id'], 22, 21)
        r.msgs.clear()
        await r.handle_move(p['id'], 0, 1)                          # dentro -> dentro
        await r.handle_move(p['id'], 0, -1)                         # volta para [22,22]
        self.assertEqual(avisos(r), [])
        await r.handle_move(p['id'], 0, -1)                         # [22,22] -> porta [22,21]
        self.assertEqual(p['pos'], PORTA)
        self.assertEqual(avisos(r), ['slots_treino_desliga'])
        await r.handle_move(p['id'], 0, -1)                         # porta -> corredor
        self.assertEqual(avisos(r), ['slots_treino_desliga'])       # sem repetir
        await r.handle_move(p['id'], 0, 1)                          # corredor -> porta
        await r.handle_move(p['id'], 0, 1)                          # porta -> sala
        self.assertEqual(p['pos'], [22, 22])
        self.assertEqual(avisos(r), ['slots_treino_desliga', 'slots_treino_liga'])

    async def test_outra_classe_na_sala_do_mago_nao_ativa(self):
        r, p = sala('warrior')
        p['pos'] = list(DENTRO)
        self.assertFalse(r._slots_livres_treino(p))

    async def test_grupo_cada_heroi_pela_propria_posicao(self):
        r, p = sala()
        q = S.make_player('hero2', 'Lewis', 'mage', 1)
        q['pos'] = list(CORREDOR)
        r.players[q['id']] = q
        self.assertTrue(r._slots_livres_treino(p))
        self.assertFalse(r._slots_livres_treino(q))

    def test_cajado_nao_e_usado_na_sala(self):
        r, p = sala()
        esgotar(r, p)
        self.assertGreater(r._slots_disponiveis(p, 'primeiro'), 0)
        r._gastar_slot(p, 'primeiro')
        self.assertEqual(len(p['slots_cooldown']['primeiro']), S.slots_max_para(p)['primeiro'])

    def test_sem_estado_novo_na_foto(self):
        """O cálculo é derivado da posição: nenhum atributo novo na sala nem no herói."""
        r, p = sala()
        antes = set(vars(r)); chaves = set(p)
        r._slots_livres_treino(p)
        self.assertEqual(antes, set(vars(r)))
        self.assertEqual(chaves, set(p))


class LicoesDoMago(unittest.TestCase):
    def test_textos_refletem_a_regra(self):
        f = {x['id']: x for x in D['falas']}
        self.assertIn('não gastam', f['treino_magia']['texto'])
        self.assertIn('não gastam', f['treino_slots']['texto'])
        self.assertNotIn('uma magia sem slot não pode ser lançada', f['treino_slots']['texto'])
        self.assertIn('não gastam', f['porta_mage']['texto'])
        ordens = [x['ordem'] for x in D['falas'] if x.get('classe') == 'mage']
        self.assertEqual(len(ordens), len(set(ordens)))


if __name__ == '__main__':
    unittest.main()
