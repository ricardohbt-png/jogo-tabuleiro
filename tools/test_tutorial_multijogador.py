"""Campo de Treinamento com mais de um jogador (bugs do teste com Paladino + Bardo).

1. Uma lição-ponte que nunca abriu (`porta_<classe>`, tarefa `mover_ate` até a
   porta da sala) segurava as lições da sala enquanto o herói estivesse a 2 casas
   da porta: entrar na sala não mostrava nada.
2. Quem cai e volta na mesma sessão reentrava pela escada: no treinamento isso
   "teleportava" o herói para o início do mapa, longe da sala dele.
3. Com o resgatador desconectado, o refém de treino passava para outro herói e
   nunca voltava; ninguém além do Paladino consegue movê-lo dentro da sala.
4. Ao religar, a janela da lição em andamento não voltava.
"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as S
from test_tutorial_salas import D


class FakeWS:
    def __init__(self):
        self.sent = []

    async def send(self, data):
        self.sent.append(data)


def sala_com(*classes):
    r = S.GameRoom('TRAIN_MULTI')
    ps = []
    for i, cls in enumerate(classes):
        p = S.make_player(f'h{i}', cls.title(), cls, i)
        r.players[p['id']] = p
        ps.append(p)
    r.load_authored_dungeon(deepcopy(D))
    r.phase = 'playing'
    r._is_turn = lambda pid: True
    r.messages = []
    async def send(pid, msg): r.messages.append((pid, msg))
    async def broadcast(msg, **kw): r.messages.append(('*', msg))
    async def noop(*a, **kw): pass
    r.send_to = send; r.broadcast = broadcast; r.gm_say = noop; r.push_state = noop
    return r, ps


def pendente(p, feitas, atual):
    """Herói que acertou o boneco mas não terminou a lição seguinte (ela ficou aberta)."""
    p['licoes_feitas'] = list(feitas)
    p['licao_progresso'] = {i: 1 for i in feitas}
    p['licao_progresso'][atual] = 0
    p['licao_atual'] = atual
    p['licao_passo'] = 0
    p['moves_left'] = 30


class PonteNaoSeguraASala(unittest.IsolatedAsyncioTestCase):
    async def test_bardo_entra_e_a_sala_ensina(self):
        r, (pal, bar) = sala_com('paladin', 'bard')
        pendente(bar, ['fala_13'], 'fala_14')
        r._room_by_id(43)['locked'] = False
        bar['pos'] = [15, 23]                       # a porta da sala do Bardo
        await r.handle_move(bar['id'], -1, 0)       # primeira casa dentro da sala
        self.assertEqual(bar['pos'], [14, 23])
        self.assertEqual(bar['licao_atual'], 'treino_atalhos_bard')
        abertas = [m.get('licao_id') for pid, m in r.messages
                   if pid == bar['id'] and m.get('type') == 'fala']
        self.assertIn('treino_atalhos_bard', abertas)

    async def test_paladino_entra_e_a_sala_ensina(self):
        r, (pal, bar) = sala_com('paladin', 'bard')
        pendente(pal, ['fala_15'], 'fala_16')
        r._room_by_id(38)['locked'] = False
        pal['pos'] = [31, 25]
        await r.handle_move(pal['id'], 1, 0)
        self.assertEqual(pal['pos'], [32, 25])
        self.assertEqual(pal['licao_atual'], 'treino_atalhos_paladin')

    async def test_ponte_aberta_ainda_espera_o_heroi_chegar(self):
        """A ponte EM ANDAMENTO continua valendo perto do alvo (comportamento antigo)."""
        r, (bar,) = sala_com('bard')
        pendente(bar, ['fala_13', 'fala_14'], 'porta_bard')
        ponte = next(l for l in r.licoes if l['id'] == 'porta_bard')
        bar['pos'] = [16, 23]
        self.assertTrue(r._licao_zona_contem(bar, ponte))


def _cair_e_voltar(r, p):
    async def nada(*a, **k): pass
    r._forcar_fim_turno = nada
    r._iniciar_timer_turno = lambda: None
    return nada


class ReconexaoNoTreino(unittest.IsolatedAsyncioTestCase):
    async def test_volta_onde_estava_e_reabre_a_licao(self):
        r, (pal, bar) = sala_com('paladin', 'bard')
        pendente(pal, ['fala_15', 'fala_16', 'porta_paladin'], 'treino_refem')
        pal['pos'] = [34, 25]
        _cair_e_voltar(r, pal)
        await r.handle_disconnect_em_jogo(pal['id'])
        self.assertEqual(pal['pos'], [-1, -1])
        ws = FakeWS()
        r.messages.clear()
        await r.religar_heroi(pal, ws, 'nova_conexao', pal['name'])
        self.assertEqual(pal['pos'], [34, 25])                    # não volta pela escada
        reabertas = [m for pid, m in r.messages
                     if pid == pal['id'] and m.get('type') == 'fala' and m.get('licao_id') == 'treino_refem']
        self.assertEqual(len(reabertas), 1)
        self.assertIn('passo', reabertas[0])

    async def test_fora_do_treino_continua_pela_escada(self):
        r, (pal, bar) = sala_com('paladin', 'bard')
        r.training_mode = False
        pal['pos'] = [34, 25]
        _cair_e_voltar(r, pal)
        await r.handle_disconnect_em_jogo(pal['id'])
        await r.religar_heroi(pal, FakeWS(), 'nova_conexao', pal['name'])
        self.assertNotEqual(pal['pos'], [34, 25])


def _janela_pos_turno(r, p):
    """Encerrar o turno abre a janela dos servos/refém de quem os controla."""
    async def nada(*a, **k): pass
    r._advance_initiative = nada
    return r.handle_end_turn(p['id'])


class RefemDoTreino(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.r, (self.pal, self.bar) = sala_com('paladin', 'bard')
        self.r.prisoner.update(freed=True, rescuer_pid=self.pal['id'], rescuer_original=self.pal['id'])

    async def test_outro_heroi_nao_recebe_o_refem_de_treino(self):
        self.pal['connected'] = False
        await _janela_pos_turno(self.r, self.bar)
        self.assertNotEqual(self.r.prisoner.get('rescuer_pid'), self.bar['id'])
        self.assertNotEqual(self.r.animados_phase_pid, self.bar['id'])

    async def test_paladino_volta_e_retoma_o_refem(self):
        self.r.prisoner['rescuer_pid'] = self.bar['id']          # estado de um save antigo
        await _janela_pos_turno(self.r, self.pal)
        self.assertEqual(self.r.prisoner['rescuer_pid'], self.pal['id'])
        self.assertEqual(self.r.animados_phase_pid, self.pal['id'])


class RefemComum(unittest.IsolatedAsyncioTestCase):
    async def test_controle_emprestado_volta_ao_resgatador(self):
        r, (war, rog) = sala_com('warrior', 'rogue')
        r.prisoner.pop('training_refem', None)
        r.prisoner.update(freed=True, rescuer_pid=war['id'], pos=[5, 15])
        war['connected'] = False
        await _janela_pos_turno(r, rog)
        self.assertEqual(r.prisoner['rescuer_pid'], rog['id'])   # emprestado a quem está ativo
        war['connected'] = True
        r.animados_phase_pid = None
        await _janela_pos_turno(r, war)
        self.assertEqual(r.prisoner['rescuer_pid'], war['id'])   # e volta ao dono


if __name__ == '__main__':
    unittest.main(verbosity=2)
