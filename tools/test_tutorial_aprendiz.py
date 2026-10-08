"""Fatia 14: o aprendiz de treino aparece no tabuleiro com a miniatura do Soldado."""
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

ROOT = Path(__file__).resolve().parents[1]
D = S.carregar_dungeon('campo_de_treinamento.json')


def sala(cls):
    r = S.GameRoom('APRENDIZ_TEST')
    p = S.make_player('hero', 'Aluno', cls, 0)
    r.players[p['id']] = p
    r.load_authored_dungeon(deepcopy(D))
    r.phase = 'playing'
    return r, p


class Aprendiz(unittest.TestCase):
    def test_arte_existe(self):
        self.assertTrue((ROOT / 'assets/pawns/monstros/soldado/soldado.png').exists())
        self.assertTrue((ROOT / 'assets/models3d/monstros/soldado.glb').exists())

    def test_payload_real_traz_aparencia(self):
        for cls, esperados in (('cleric', 2), ('bard', 1)):
            r, p = sala(cls)
            capt = []
            async def bc(msg, **kw): capt.append(msg)
            r.broadcast = bc
            asyncio.run(r.push_state())
            st = next(m for m in capt if m.get('type') == 'game_state')
            aps = [x for x in st['players'] if x.get('training_ally')]
            self.assertTrue(len(aps) >= esperados)
            for a in aps:
                self.assertEqual(a.get('pawn_override'), 'soldado')
                self.assertTrue(a['name'].startswith('Aprendiz '))
                self.assertFalse(a.get('is_master'))
            self.assertNotIn(aps[0]['id'], r.initiative_order)

    def test_aliado_nao_vira_jogador(self):
        r, p = sala('cleric')
        for a in r.training_allies.values():
            self.assertNotIn(a['id'], r.players)
            self.assertEqual(a['pawn_override'], 'soldado')


if __name__ == '__main__':
    unittest.main()
