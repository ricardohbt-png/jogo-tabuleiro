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
    else:
        f.pop('guia', None)  # None = lição sem guia (a trilha real já tem)
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



class FotoTests(unittest.IsolatedAsyncioTestCase):
    async def test_licao_passo_faz_o_ciclo_da_foto(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        p['licao_passo'] = 2
        volta = S._foto_decodificar(S._foto_codificar(p))
        self.assertEqual(volta['licao_passo'], 2)
        self.assertEqual(volta['licao_atual'], 'treino_mira')

    def test_licao_guia_vai_na_foto_da_sala(self):
        # `licoes` e `falas` são categoria "foto": o guia autorado viaja junto.
        self.assertEqual(S.GameRoom.FOTO_SALA_CATEGORIAS.get('licoes') if hasattr(S.GameRoom, 'FOTO_SALA_CATEGORIAS')
                         else S.FOTO_SALA_CATEGORIAS.get('licoes'), 'foto')


class DicaErroTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        S._GUIA_DICA_ULTIMA.clear()

    def dicas(self, r):
        return [m for m in r.messages if m.get('type') == 'licao_dica']

    async def test_nao_e_o_seu_turno_vira_fora_da_vez(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        d = self.dicas(r)
        self.assertEqual(len(d), 1)
        self.assertEqual((d[0]['motivo'], d[0]['licao_id']), ('fora_da_vez', 'treino_mira'))

    async def test_acao_ja_usada_vira_sem_acao(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.acao_principal_ja_usada_neste_turno'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'sem_acao')

    async def test_alvo_fora_de_alcance_vira_longe_do_alvo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')                 # tarefa: atacar boneco_treino
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_fora_de_alcance'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'longe_do_alvo')

    async def test_alvo_invalido_vira_alvo_errado(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_invalido'))
        self.assertEqual(self.dicas(r)[0]['motivo'], 'alvo_errado')

    async def test_erro_desconhecido_nao_gera_dica(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.sala_nao_encontrada'))
        await r._guia_dica_por_erro('hero', "texto cru")
        await r._guia_dica_por_erro('hero', None)
        self.assertEqual(self.dicas(r), [])

    async def test_sem_licao_pendente_nao_gera_dica(self):
        r, p = room('warrior')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        await r._guia_dica_por_erro('nao_existe', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(self.dicas(r), [])

    async def test_alvo_errado_so_em_tarefa_com_alvo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_0')                 # tarefa: mover_ate (sem alvo de combate)
        await r._guia_dica_por_erro('hero', S.T('erro.alvo_invalido'))
        self.assertEqual(self.dicas(r), [])

    async def test_intervalo_minimo_entre_dicas(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'treino_mira')
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(len(self.dicas(r)), 1)
        S._GUIA_DICA_ULTIMA['hero'] -= S.GUIA_DICA_INTERVALO_S + 1
        await r._guia_dica_por_erro('hero', S.T('erro.nao_e_o_seu_turno'))
        self.assertEqual(len(self.dicas(r)), 2)

    async def test_send_to_real_chama_o_gancho_so_para_erros(self):
        r, p = room('warrior')
        vistos = []

        async def espia(pid, texto): vistos.append((pid, getattr(texto, 'key', texto)))
        r._guia_dica_por_erro = espia
        r.connections = {}
        await S.GameRoom.send_to(r, 'hero', {"type": "error", "msg": S.T('erro.nao_e_o_seu_turno')})
        await S.GameRoom.send_to(r, 'hero', {"type": "gm_narration", "text": "oi"})
        self.assertEqual(vistos, [('hero', 'erro.nao_e_o_seu_turno')])

    async def test_alvo_errado_quando_acerta_outro_tipo(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._licao_evento(p, 'atacar', alvo='esqueleto_humano')
        d = self.dicas(r)
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]['motivo'], 'alvo_errado')
        self.assertEqual(p['licao_atual'], 'fala_5')       # não concluiu


class ResultadoTests(unittest.IsolatedAsyncioTestCase):
    def resultados(self, r):
        return [m for m in r.messages if m.get('type') == 'licao_resultado']

    async def test_acerto(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_resultado_ataque(p, roll=14, total=17, ca=12, hit=True, crit=False)
        m = self.resultados(r)[0]
        self.assertEqual((m['chave'], m['roll'], m['bonus'], m['total'], m['ca']),
                         ('acerto', 14, 3, 17, 12))
        self.assertEqual(m['licao_id'], 'fala_5')

    async def test_critico_e_erro(self):
        r, p = room('warrior')
        await abrir_licao(r, p, 'fala_5')
        await r._guia_resultado_ataque(p, roll=20, total=23, ca=12, hit=True, crit=True)
        await r._guia_resultado_ataque(p, roll=3, total=6, ca=12, hit=False, crit=False)
        self.assertEqual([m['chave'] for m in self.resultados(r)], ['critico', 'erro'])

    async def test_sem_licao_pendente_nao_envia(self):
        r, p = room('warrior')
        await r._guia_resultado_ataque(p, roll=14, total=17, ca=12, hit=True, crit=False)
        self.assertEqual(self.resultados(r), [])

    def test_handle_attack_chama_o_resultado(self):
        import inspect
        self.assertIn('_guia_resultado_ataque(', inspect.getsource(S.GameRoom.handle_attack))


class RecompensaTests(unittest.TestCase):
    def _concluir(self, r, p, ident):
        lic = next(f for f in r.licoes if f['id'] == ident)
        asyncio.run(r._licao_concluir(p, lic))
        return lic

    def test_primeira_conclusao_paga_e_avisa(self):
        r, p = room()
        ouro = p['gold']
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro + S.TUTORIAL_RECOMPENSA_OURO)
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertEqual(msg['licao_id'], 'treino_mira')
        self.assertEqual(msg['recompensa']['ouro'], S.TUTORIAL_RECOMPENSA_OURO)
        self.assertEqual(msg['recompensa']['xp'], S.TUTORIAL_RECOMPENSA_XP)

    def test_repetir_nao_paga_de_novo(self):
        r, p = room()
        self._concluir(r, p, 'treino_mira')
        ouro = p['gold']
        r.messages.clear()
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro)
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertEqual(msg['recompensa'], {'ouro': 0, 'xp': 0, 'trilha': False})

    def test_fora_do_modo_treino_nao_paga(self):
        r, p = room()
        r.training_mode = False
        ouro = p['gold']
        self._concluir(r, p, 'treino_mira')
        self.assertEqual(p['gold'], ouro)
        self.assertFalse([m for m in r.messages if m['type'] == 'licao_concluida'])

    def test_bonus_de_trilha_quando_fecha_a_ultima_licao_da_classe(self):
        r, p = room()
        lics = [f for f in r.licoes if f.get('classe') == 'warrior']
        for f in lics[:-1]:
            self._concluir(r, p, f['id'])
        ouro = p['gold']
        r.messages.clear()
        self._concluir(r, p, lics[-1]['id'])
        msg = next(m for m in r.messages if m['type'] == 'licao_concluida')
        self.assertTrue(msg['recompensa']['trilha'])
        self.assertEqual(p['gold'], ouro + S.TUTORIAL_RECOMPENSA_OURO + S.TUTORIAL_BONUS_TRILHA_OURO)


class PassoOkTests(unittest.TestCase):
    def test_avancar_avisa_o_passo_concluido(self):
        r, p = room(guia=GUIA_MIRA)
        asyncio.run(abrir_licao(r, p, 'treino_mira'))
        r.messages.clear()
        lic = next(f for f in r.licoes if f['id'] == 'treino_mira')
        asyncio.run(r._guia_avancar(p, lic))
        tipos = [m['type'] for m in r.messages]
        self.assertEqual(tipos, ['licao_passo_ok', 'licao_passo'])
        ok = r.messages[0]
        self.assertEqual((ok['licao_id'], ok['passo'], ok['total']), ('treino_mira', 0, 3))


if __name__ == '__main__':
    unittest.main(verbosity=2)
