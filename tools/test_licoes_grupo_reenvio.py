"""Tutorial com vários heróis (Solo com grupo): a lição em andamento de CADA herói
volta à tela quando o jogo é retomado ou a conexão é religada.

Antes, a retomada (Continuar dentro da masmorra) só verificava lições novas — a
que estava no meio não era reenviada a ninguém — e o religar reenviava só a do
herói principal, nunca a dos extras.
Roda da raiz: python -X utf8 tools/test_licoes_grupo_reenvio.py"""
import asyncio, sys, unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as S
from test_tutorial_salas import D


def sala_grupo():
    """Campo de Treinamento com um guerreiro (conexão) e um ladino extra dele."""
    r = S.GameRoom('TRAIN_GRUPO')
    w = S.make_player('w', 'Victor', 'warrior', 0)
    g = S.make_player('g', 'Luccas', 'rogue', 1)
    g['controlador'] = 'w'
    r.players = {'w': w, 'g': g}
    r.load_authored_dungeon(deepcopy(D))
    r.phase = 'playing'
    r.enviados = []
    async def send(pid, msg): r.enviados.append((pid, msg))
    async def noop(*a, **k): pass
    r.send_to = send; r.broadcast = noop; r.gm_say = noop; r.push_state = noop
    r._activate_initiative_actor = noop
    for p in (w, g):
        p['pos'] = list(D['entrance'].values())[:2] if isinstance(D.get('entrance'), dict) else [2, 14]
        p['licoes_feitas'] = ['fala_intro']
        p['licao_progresso'] = {'fala_intro': 1, 'fala_camera': 0}
        p['licao_atual'] = 'fala_camera'
    w['licao_passo'] = 3
    g['licao_passo'] = 1
    return r


def licoes_enviadas(r):
    return {(pid, m.get('licao_id'), (m.get('passo') or {}).get('i'))
            for pid, m in r.enviados if m.get('type') == 'fala' and m.get('licao_id')}


class ReenvioTests(unittest.IsolatedAsyncioTestCase):
    async def test_retomada_reenvia_a_licao_de_cada_heroi(self):
        r = sala_grupo()
        r.dungeon_intro_active = True
        await r._liberar_intro_masmorra(False, retomada=True)
        enviadas = licoes_enviadas(r)
        self.assertIn(('w', 'fala_camera', 3), enviadas)
        self.assertIn(('g', 'fala_camera', 1), enviadas)

    async def test_religar_reenvia_tambem_a_dos_extras(self):
        r = sala_grupo()
        for p in r.players.values():
            p['connected'] = False
        class WS:
            async def send(self, data): pass
        await r.religar_heroi(r.players['w'], WS(), 'nova_conexao', 'Victor')
        enviadas = licoes_enviadas(r)
        self.assertIn(('w', 'fala_camera', 3), enviadas)
        self.assertIn(('g', 'fala_camera', 1), enviadas)


if __name__ == '__main__':
    unittest.main(verbosity=2)
