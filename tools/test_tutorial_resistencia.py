"""Fluxo das lições de resistência e vulnerabilidade do Campo de Treinamento."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

import server as S
from test_tutorial_salas import D, room


class TutorialResistenciaTests(unittest.IsolatedAsyncioTestCase):
    async def test_consumiveis_nao_pulam_aulas_da_sala_seguinte(self):
        r, p = room('warrior')
        p['pos'] = [42, 15]
        await r._verificar_falas(p, r._room_containing_point(p['pos']))
        self.assertEqual(p['licao_atual'], 'fala_29')
        self.assertNotIn('fala_res', p['licoes_puladas'])
        self.assertNotIn('fala_vuln', p['licoes_puladas'])
        p['pos'] = [48, 15]
        await r._verificar_falas(p, r._room_containing_point(p['pos']))
        self.assertEqual(p['licao_atual'], 'fala_res')

    async def test_reentrada_com_historico_mostra_aula_sem_repetir_premio(self):
        r, p = room('warrior')
        p['tutorial_history'] = ['fala_res', 'fala_vuln', 'treino_mira']
        r.load_authored_dungeon(copy.deepcopy(D))
        self.assertIn('treino_mira', p['licoes_feitas'])
        p['pos'] = [48, 15]
        await r._verificar_falas(p, r._room_containing_point(p['pos']))
        self.assertEqual(p['licao_atual'], 'fala_res')
        ouro, xp = p['gold'], p['xp']
        await r._licao_concluir(p, next(f for f in r.licoes if f['id'] == 'fala_res'))
        self.assertEqual((p['gold'], p['xp']), (ouro, xp))

    def test_saida_da_aula_de_dano_fica_em_uma_sala_separada(self):
        d = copy.deepcopy(D)
        from aplicar_tutorial_missao import aplicar
        aplicar(d)

        salas = {s['id']: s for s in d['rooms']}
        aula, saida = salas[48], salas[49]
        self.assertEqual((aula['x'], aula['y'], aula['w'], aula['h']), (48, 12, 8, 7))
        self.assertEqual((saida['x'], saida['y'], saida['w'], saida['h']), (48, 21, 6, 6))
        self.assertIn([51, 19], aula['doors'])
        self.assertIn([51, 20], saida['doors'])
        self.assertEqual(d['grid']['w'], 57)
        self.assertTrue(all(len(row) == d['grid']['w'] for row in d['tiles']))
        self.assertEqual(d['tiles'][19][51], S.DOOR)
        self.assertEqual(d['tiles'][20][51], S.DOOR)
        self.assertEqual(d['exit'], {'x': 51, 'y': 24})

        fala = next(f for f in d['falas'] if f['id'] == 'fala_retirada')
        self.assertEqual(fala['pos'], [51, 24])
        self.assertEqual(fala['tarefa']['alvo'], [51, 24])
        self.assertEqual(fala['trigger'], {'tipo': 'proximidade', 'raio': 1})
        ok, msg = S.validar_dungeon(d)
        self.assertTrue(ok, msg)

    async def test_entrada_pela_porta_inicia_resistencia_e_retirada_pode_seguir(self):
        r, p = room('warrior')
        ordem_res = next(f['ordem'] for f in r.licoes if f['id'] == 'fala_res')
        anteriores = [f for f in r.licoes if f.get('ordem') is not None and f['ordem'] < ordem_res
                      and f['id'] != 'fala_atalhos']
        p['licoes_feitas'] = [f['id'] for f in anteriores]
        p['licao_progresso'] = {f['id']: 1 for f in anteriores}
        p['licoes_puladas'] = []
        p['licao_atual'] = 'fala_atalhos'
        p['pos'] = [46, 15]
        p['moves_left'] = 5
        p['moved_this_turn'] = False

        await r.handle_open_door(p['id'], 47, 15)
        await r.handle_move(p['id'], 1, 0)
        await r.handle_move(p['id'], 1, 0)
        self.assertEqual(p['pos'], [48, 15])
        self.assertEqual(p['licao_atual'], 'fala_res')
        self.assertIn('fala_atalhos', p['licoes_puladas'])

        # Chegar ao boneco não pode pular uma lição de resistência que já está aberta.
        p['pos'] = [50, 15]
        await r._verificar_falas(p, r._room_containing_point(p['pos']))
        self.assertEqual(p['licao_atual'], 'fala_res')
        self.assertNotIn('fala_res', p['licoes_puladas'])

        ordem_retirada = next(f['ordem'] for f in r.licoes if f['id'] == 'fala_retirada')
        for f in r.licoes:
            if f.get('ordem') is not None and f.get('classe') is None and f['ordem'] < ordem_retirada:
                if f['id'] not in {'fala_res', 'fala_vuln', 'fala_atalhos'}:
                    if f['id'] not in p['licoes_feitas']:
                        p['licoes_feitas'].append(f['id'])
        p['licao_atual'] = None
        p['pos'] = [51, 18]
        p['moves_left'] = 5
        p['moved_this_turn'] = False
        await r.handle_move(p['id'], 0, 1)
        self.assertEqual(p['pos'], [51, 19])
        await r.handle_open_door(p['id'], 51, 20)
        await r.handle_move(p['id'], 0, 1)
        await r.handle_move(p['id'], 0, 1)
        await r.handle_move(p['id'], 0, 1)
        await r.handle_move(p['id'], 0, 1)
        self.assertEqual(p['pos'], [51, 23])
        self.assertEqual(p['licao_atual'], 'fala_retirada')
        self.assertTrue({'fala_res', 'fala_vuln', 'fala_atalhos'}.issubset(p['licoes_puladas']))

    async def test_boneco_compartilhado_aceita_ataque_e_libera_as_proximas_etapas(self):
        r, p = room("warrior")
        fala_res = next(f for f in r.licoes if f["id"] == "fala_res")
        ids_chain = {"fala_res", "fala_vuln", "fala_retirada", "fala_atalhos"}
        ordem_atalhos = next(f["ordem"] for f in r.licoes if f["id"] == "fala_atalhos")
        anteriores = [f for f in r.licoes if f.get("ordem") is not None
                      and f["ordem"] < ordem_atalhos and f["id"] not in ids_chain]
        p["licoes_feitas"] = [f["id"] for f in anteriores]
        p["licao_progresso"] = {f["id"]: (f.get("tarefa") or {}).get("vezes", 1)
                                 for f in anteriores}
        p["licoes_puladas"] = []
        p["licao_atual"] = None
        p["pos"] = [48, 13]
        p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_res")

        boneco = next(m for m in r.monsters.values() if m.get("room_id") == 48)
        await r._licao_evento(p, "atacar", alvo="boneco_treino",
                              contexto={"categoria_arma": "cortante", "sala_alvo_id": 40})
        self.assertEqual(p["licao_atual"], "fala_res")

        p["pos"] = [50, 16]
        p["weapon"] = copy.deepcopy(S._DUNGEON_ITEM_CATALOG["cajado_madeira"])
        with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
            await r.handle_attack(p["id"], boneco["id"])
        self.assertEqual(p["licao_atual"], "fala_res")
        self.assertNotIn("fala_res", p["licoes_feitas"])

        p["action_done"] = False
        p["pos"] = [50, 15]
        p["weapon"] = copy.deepcopy(S._DUNGEON_ITEM_CATALOG["machado_basico"])
        with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
            await r.handle_attack(p["id"], boneco["id"])
        self.assertIn("fala_res", p["licoes_feitas"])
        self.assertEqual(p["licao_atual"], "fala_vuln")
        self.assertNotIn("fala_vuln", p["licoes_puladas"])

        p["pos"] = [52, 15]
        p["action_done"] = False
        p["weapon"] = copy.deepcopy(S._DUNGEON_ITEM_CATALOG["cajado_madeira"])
        with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
            await r.handle_attack(p["id"], boneco["id"])
        self.assertIn("fala_vuln", p["licoes_feitas"])

        self.assertIsNone(p["licao_atual"])
        p["pos"] = [51, 24]
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_retirada")

    async def test_boneco_compartilhado_aceita_todas_as_classes(self):
        for classe in ("warrior", "mage", "rogue", "cleric", "bard", "paladin"):
            r, p = room(classe)
            boneco = next(m for m in r.monsters.values() if m.get("room_id") == 48)
            p["pos"] = [50, 16]
            p["action_done"] = False
            p["weapon"] = copy.deepcopy(S._DUNGEON_ITEM_CATALOG["cajado_madeira"])
            with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
                await r.handle_attack(p["id"], boneco["id"])
            resultados = [m for m in r.messages if m.get("type") == "attack_feedback"
                          and m.get("phase") == "result" and m.get("hit")]
            self.assertTrue(resultados, f"ataque recusado para {classe}")

    async def test_conclusao_entrega_tour_na_cidade_nos_dois_acessos(self):
        for aventura in (None, 'treinamento'):
            r, p = room('warrior')
            r.selected_dungeon = 'campo_de_treinamento.json'
            r.world_adventure_id = aventura
            r.world_adventure_index = 0 if aventura else None
            r.mission_complete_pending = True
            r._objetivo_concluido = True
            self.assertTrue(r._tutorial_tem_tour_cidade())
            await r.handle_encerrar_missao(p['id'])
            self.assertEqual(r.phase, 'city')
            cidade = next(m for m in reversed(r.messages) if m['type'] == 'city_state')
            token = cidade['tutorial']['tour_cidade_id']
            self.assertTrue(token)
            self.assertEqual(r._city_state_payload()['tutorial']['tour_cidade_id'], token)
            # Retornar/reconectar não cria um novo passeio nem encerra outra missão.
            await r.handle_encerrar_missao(p['id'])
            self.assertEqual(r.tutorial_city_tour_id, token)

    async def test_sair_sem_concluir_nao_inicia_tour(self):
        r, p = room('warrior')
        r.selected_dungeon = 'campo_de_treinamento.json'
        await r._voltar_para_cidade()
        self.assertIsNone(r._city_state_payload()['tutorial']['tour_cidade_id'])
        r.training_mode = True
        r.selected_dungeon = 'outro_treino.json'
        self.assertFalse(r._tutorial_tem_tour_cidade())

    def test_foto_antiga_recupera_apenas_aulas_puladas(self):
        r, p = room('warrior')
        r.selected_dungeon = 'campo_de_treinamento.json'
        for l in r.falas + r.licoes:
            if l['id'] in {'fala_res', 'fala_vuln', 'fala_retirada'}:
                l['ordem'] = {'fala_res': 9, 'fala_vuln': 10, 'fala_retirada': 11}[l['id']]
        p['licoes_puladas'] = ['fala_res', 'fala_retirada']
        p['licoes_feitas'] = ['fala_res', 'fala_vuln', 'fala_retirada']
        p['licao_progresso'] = dict.fromkeys(p['licoes_feitas'], 1)
        p['tutorial_history'] = ['fala_vuln']
        r._tutorial_reparar_ordem_salva({'herois': {'warrior': p}})
        self.assertEqual(p['licoes_feitas'], ['fala_vuln'])
        self.assertEqual(p['licao_progresso'], {'fala_vuln': 1})
        self.assertEqual(p['tutorial_history'], ['fala_vuln'])
        self.assertEqual(next(l['ordem'] for l in r.licoes if l['id'] == 'fala_res'), 32)
        r._tutorial_reparar_ordem_salva({'herois': {'warrior': p}})
        self.assertEqual(p['licoes_feitas'], ['fala_vuln'])


if __name__ == "__main__":
    unittest.main()
