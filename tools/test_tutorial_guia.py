"""Guia do tutorial (fatia 1): validação, passos, avanço e foto.

Roda da raiz:  python tools/test_tutorial_guia.py
Dados isolados: monta salas em memória, não escreve saves.
"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

D = S.carregar_dungeon('campo_de_treinamento.json')

GUIA_MIRA = [
    {"id": "s1", "texto": "Olhe a barra de habilidades.", "ui": "habilidade:mira_certeira"},
    {"id": "s2", "texto": "Ataque um boneco.", "ui": "monstro:boneco_treino",
     "conclui_com": {"tipo": "atacar", "alvo": "boneco_treino"},
     "dica": ["O boneco está logo à frente.", "Clique nele."]},
    {"id": "s3", "texto": "Arme a Mira e ataque.", "ui": "habilidade:mira_certeira"},
]


def dungeon_com_guia(guia):
    d = deepcopy(D)
    f = next(x for x in d['falas'] if x['id'] == 'treino_mira')
    if guia is not None:
        f['guia'] = guia
    return d


def room(cls='warrior', guia=None):
    r = S.GameRoom('GUIA_TEST')
    p = S.make_player('hero', 'Aluno', cls, 0)
    r.players[p['id']] = p
    r.load_authored_dungeon(dungeon_com_guia(guia))
    r.phase = 'playing'
    r._is_turn = lambda pid: True
    r.messages = []

    async def send(pid, msg): r.messages.append(msg)
    async def broadcast(msg): r.messages.append(msg)
    async def noop(*a, **k): pass
    r.send_to = send; r.broadcast = broadcast; r.gm_say = noop; r.push_state = noop
    return r, p


async def abrir_licao(r, p, ident):
    target = next(f for f in r.licoes if f['id'] == ident)
    done = [f['id'] for f in r.licoes if f.get('classe') == p['class_id']
            and f.get('ordem', 0) < target['ordem']]
    p['licoes_feitas'] = done
    p['licao_progresso'] = {i: 1 for i in done}
    p['licao_atual'] = None
    p['pos'] = list(target['pos'])
    await r._verificar_falas(p, r._room_containing_point(p['pos']))
    if p['licao_atual'] != ident:
        raise AssertionError((ident, p['licao_atual']))


class ValidacaoTests(unittest.TestCase):
    def test_guia_valido_passa(self):
        self.assertEqual(S.validar_dungeon(dungeon_com_guia(deepcopy(GUIA_MIRA))), (True, 'ok'))

    def test_guia_vazio_ou_longo_demais(self):
        ok, _ = S.validar_dungeon(dungeon_com_guia([]))
        self.assertFalse(ok)
        longo = [{"texto": f"p{i}"} for i in range(S.GUIA_MAX_PASSOS + 1)]
        ok, _ = S.validar_dungeon(dungeon_com_guia(longo))
        self.assertFalse(ok)

    def test_passo_sem_texto(self):
        ok, msg = S.validar_dungeon(dungeon_com_guia([{"texto": "  "}]))
        self.assertFalse(ok); self.assertIn("texto", msg)

    def test_ui_invalida(self):
        for ui in ("botao", "xyz:abc", "casa:3,4", "habilidade:Mira Certeira", 5):
            ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "ui": ui}]))
            self.assertFalse(ok, ui)
        for ui in ("botao:encerrar_turno", "habilidade:mira_certeira", "casa:[3,4]",
                   "porta:[10,2]", "monstro:boneco_treino", "hud:fome"):
            ok, msg = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "ui": ui}]))
            self.assertTrue(ok, (ui, msg))

    def test_dica_e_conclui_com(self):
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "dica": ["x", "y", "z"]}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "dica": [""]}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia(
            [{"texto": "a", "conclui_com": {"tipo": "voar"}}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "conclui_com": "atacar"}]))
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
