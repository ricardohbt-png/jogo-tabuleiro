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

class DerivacaoTests(unittest.TestCase):
    def test_ui_padrao_por_tarefa(self):
        f = S._guia_ui_padrao
        self.assertEqual(f({"tipo": "encerrar_turno"}), "botao:encerrar_turno")
        self.assertEqual(f({"tipo": "usar_habilidade", "alvo": "mira_certeira"}), "habilidade:mira_certeira")
        self.assertEqual(f({"tipo": "usar_tecnica", "alvo": "brutalidade"}), "habilidade:brutalidade")
        self.assertEqual(f({"tipo": "mover_ate", "alvo": [5, 15]}), "casa:[5,15]")
        self.assertEqual(f({"tipo": "abrir_porta", "alvo": [13, 15]}), "porta:[13,15]")
        self.assertEqual(f({"tipo": "atacar", "alvo": "boneco_treino"}), "monstro:boneco_treino")
        self.assertEqual(f({"tipo": "usar_item", "alvo": "racao_viagem"}), "bolsa:racao_viagem")
        self.assertIsNone(f({"tipo": "pegar_item"}))
        self.assertIsNone(f({"tipo": "atacar", "alvo": "Boneco Treino"}))

    def test_passos_sem_guia_gera_um_passo_auto(self):
        lic = {"id": "x", "texto": "Longo.", "tarefa": {"tipo": "encerrar_turno"}}
        passos = S._guia_passos(lic)
        self.assertEqual(len(passos), 1)
        self.assertTrue(passos[0]["auto"])
        self.assertEqual(passos[0]["ui"], "botao:encerrar_turno")

    def test_payload_marca_informativo_e_limita_indice(self):
        lic = {"id": "x", "guia": deepcopy(GUIA_MIRA), "tarefa": {"tipo": "usar_habilidade"}}
        p0 = S._guia_payload(lic, 0)
        self.assertEqual((p0["i"], p0["n"], p0["informativo"]), (0, 3, True))
        p1 = S._guia_payload(lic, 1)
        self.assertFalse(p1["informativo"])
        self.assertEqual(p1["dica"], ["O boneco está logo à frente.", "Clique nele."])
        p9 = S._guia_payload(lic, 9)
        self.assertEqual(p9["i"], 2)
        self.assertFalse(p9["informativo"])


class AvancoTests(unittest.IsolatedAsyncioTestCase):
    async def test_fala_leva_o_passo_0(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        self.assertEqual(p['licao_passo'], 0)
        fala = next(m for m in r.messages if m.get('licao_id') == 'treino_mira')
        self.assertEqual(fala['passo']['i'], 0)
        self.assertEqual(fala['passo']['n'], 3)
        self.assertTrue(fala['passo']['informativo'])

    async def test_sem_guia_a_fala_leva_passo_auto(self):
        r, p = room('warrior', None)
        await abrir_licao(r, p, 'treino_mira')
        fala = next(m for m in r.messages if m.get('licao_id') == 'treino_mira')
        self.assertTrue(fala['passo']['auto'])
        self.assertEqual(fala['passo']['ui'], 'habilidade:mira_certeira')

    async def test_entendi_avanca_so_passo_informativo(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        self.assertEqual(p['licao_passo'], 1)
        msg = [m for m in r.messages if m.get('type') == 'licao_passo'][-1]
        self.assertEqual(msg['passo']['i'], 1)
        self.assertEqual(msg['licao_id'], 'treino_mira')
        await r.handle_avancar_passo('hero')          # passo 1 tem conclui_com: não pula
        self.assertEqual(p['licao_passo'], 1)

    async def test_evento_certo_avanca_e_errado_nao(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        await r._licao_evento(p, 'atacar', alvo='esqueleto_humano')
        self.assertEqual(p['licao_passo'], 1)
        await r._licao_evento(p, 'atacar', alvo='boneco_treino')
        self.assertEqual(p['licao_passo'], 2)

    async def test_ultimo_passo_nao_avanca_sozinho_e_a_tarefa_conclui(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        p['licao_passo'] = 2
        await r.handle_avancar_passo('hero')
        await r._licao_evento(p, 'atacar', alvo='boneco_treino')
        self.assertEqual(p['licao_passo'], 2)
        await r._licao_evento(p, 'usar_habilidade', alvo='mira_certeira')
        self.assertIn('treino_mira', p['licoes_feitas'])
        self.assertNotEqual(p.get('licao_atual'), 'treino_mira')
        self.assertEqual(p['licao_passo'], 0)

    async def test_sem_licao_pendente_nada_acontece(self):
        r, p = room('warrior', None)
        await r.handle_avancar_passo('hero')
        self.assertEqual(p['licao_passo'], 0)
        await r.handle_avancar_passo('nao_existe')

    async def test_tutorial_payload_leva_o_passo(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        bloco = r._tutorial_payload()['por_classe']['warrior']
        self.assertEqual(bloco['passo']['i'], 0)
        p['licao_atual'] = None
        self.assertIsNone(r._tutorial_payload()['por_classe']['warrior']['passo'])

    async def test_passos_sao_por_heroi(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        outro = S.make_player('hero2', 'Outro', 'mage', 1)
        r.players['hero2'] = outro
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        self.assertEqual((p['licao_passo'], outro['licao_passo']), (1, 0))



if __name__ == '__main__':
    unittest.main(verbosity=2)
