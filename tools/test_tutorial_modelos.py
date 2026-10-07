"""Modelos de guia das lições geradas (treino_guild_*, treino_magia_*)."""
import json, sys, unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S


def render(payload, lang):
    return json.loads(json.dumps(payload, default=lambda o: S._t_render(o, lang)))


class ModelosTests(unittest.TestCase):
    def lic_magia(self):
        return {"id": "treino_magia_mage_bola_fogo", "classe": "mage", "texto": "x",
                "tarefa": {"tipo": "usar_magia", "alvo": "bola_fogo", "vezes": 1, "texto_curto": "x"},
                "guia_modelo": {"tipo": "magia", "id": "bola_fogo"}}

    def lic_guild(self):
        return {"id": "treino_guild_guerreiro_mira_3", "classe": "warrior", "texto": "x",
                "tarefa": {"tipo": "usar_habilidade", "alvo": "mira_certeira", "vezes": 1, "texto_curto": "x"},
                "guia_modelo": {"tipo": "guild", "id": "guerreiro_mira_3", "skill": "mira_certeira"}}

    def test_magia_tem_dois_passos_e_ui_certa(self):
        passos = S._guia_passos(self.lic_magia())
        self.assertEqual(len(passos), 2)
        self.assertEqual(passos[0]["ui"], "botao:magias")
        self.assertFalse(passos[0].get("conclui_com"))
        self.assertFalse(passos[1].get("conclui_com"))

    def test_guild_usa_a_habilidade_da_linha(self):
        passos = S._guia_passos(self.lic_guild())
        self.assertEqual(passos[-1]["ui"], "habilidade:mira_certeira")
        self.assertEqual(len(passos), 2)

    def test_guild_sem_skill_nao_inventa_ui(self):
        lic = self.lic_guild(); lic["guia_modelo"]["skill"] = None
        self.assertFalse(S._guia_passos(lic)[-1].get("ui"))

    def test_payload_resolve_o_nome_em_cada_idioma(self):
        pt = render(S._guia_payload(self.lic_magia(), 1), "pt")
        en = render(S._guia_payload(self.lic_magia(), 1), "en")
        self.assertNotEqual(pt["texto"], en["texto"])
        self.assertIn("Fireball", en["texto"])        # nome da magia em inglês vem do catálogo
        self.assertIn("Bola de Fogo", pt["texto"])
        self.assertNotIn("cat.magia", pt["texto"] + en["texto"] + pt["porque"] + en["porque"])
        self.assertTrue(en["porque"])                 # descrição de catálogo existe para bola_fogo
        self.assertTrue(render(S._guia_payload(self.lic_magia(), 0), "en")["informativo"])
        self.assertFalse(en["informativo"])           # último passo nunca é informativo

    def test_guild_payload_resolve(self):
        en = render(S._guia_payload(self.lic_guild(), 0), "en")
        self.assertNotIn("cat.guilda", en["texto"] + en["porque"])
        self.assertTrue(en["informativo"])            # 1º passo, sem conclui_com

    def test_id_sem_chave_nao_mostra_a_chave(self):
        lic = self.lic_magia(); lic["guia_modelo"]["id"] = "magia_que_nao_existe"
        for i in (0, 1):
            out = render(S._guia_payload(lic, i), "en")
            self.assertNotIn("cat.", out["texto"] + out["porque"])

    def test_lista_de_licoes_continua_serializavel(self):
        json.dumps(self.lic_magia()); json.dumps(self.lic_guild())    # a foto da masmorra grava isto

    def test_licao_sem_modelo_nao_muda(self):
        lic = {"id": "x", "texto": "t", "tarefa": {"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "x"}}
        self.assertTrue(S._guia_passos(lic)[0]["auto"])

    def test_geradas_ganham_guia_modelo(self):
        src = (RAIZ / "tutorial_training.py").read_text(encoding="utf-8")
        self.assertIn('guia_modelo', src)
        self.assertEqual(src.count('guia_modelo'), 2)     # um por família de lição gerada

    def test_cenario_real_gera_modelo_e_serializa(self):
        D = S.carregar_dungeon('campo_de_treinamento.json')
        # Guerreiro com especialização da Guilda
        r = S.GameRoom('TRAIN_MODELO')
        p = S.make_player('hero', 'Aluno', 'warrior', 0)
        p['guild_owned']['especializacoes'] = ['guerreiro_mira_3']
        r.players[p['id']] = p
        r.load_authored_dungeon(deepcopy(D))
        gen = [l for l in r.licoes if l['id'] == 'treino_guild_guerreiro_mira_3']
        self.assertEqual(len(gen), 1)
        self.assertEqual(gen[0]['guia_modelo']['tipo'], 'guild')
        self.assertNotIn('guia', gen[0])
        passos = S._guia_passos(gen[0])
        self.assertEqual(passos[-1]['ui'], f"habilidade:{gen[0]['tarefa']['alvo']}")
        json.dumps(r.licoes)
        # Mago com magia conhecida
        r = S.GameRoom('TRAIN_MODELO2')
        p = S.make_player('hero', 'Aluno', 'mage', 0)
        p['magias_conhecidas'] = ['raio_congelante']
        r.players[p['id']] = p
        r.load_authored_dungeon(deepcopy(D))
        gen = [l for l in r.licoes if l['id'].startswith('treino_magia_')]
        self.assertTrue(gen)
        self.assertEqual(gen[0]['guia_modelo'], {"tipo": "magia", "id": "raio_congelante"})
        json.dumps(r.licoes)
        out = render(S._guia_payload(gen[0], 1), "en")
        self.assertNotIn("cat.", out["texto"])


if __name__ == "__main__":
    unittest.main()
