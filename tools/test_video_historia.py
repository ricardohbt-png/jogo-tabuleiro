"""Slide de história com vídeo e a morte do Gilo na abertura da Praça viva.
Roda da raiz: python -X utf8 tools/test_video_historia.py"""
import base64
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_graciero as GG

VIDEO = "assets/story/gilo_escorpioes_animacao.mp4"
IMAGEM = "assets/story/gilo_escorpioes_praca.png"


class SlideTests(unittest.TestCase):
    def test_slide_so_com_video_vale(self):
        n = S._story_norm({"slides": [{"video": VIDEO}]})
        self.assertEqual(n["slides"][0]["video"], VIDEO)

    def test_video_fora_da_pasta_ou_de_outro_tipo_e_descartado(self):
        for ruim in ("assets/itens/x.mp4", "assets/story/../../server.py", "assets/story/x.exe", 7):
            self.assertEqual(S._story_norm({"slides": [{"video": ruim}]})["slides"], [], ruim)
            self.assertFalse(S._validar_story({"slides": [{"video": ruim, "text": "x"}]}, "t")[0], ruim)

    def test_validar_e_gravar_preservam(self):
        campo = {"slides": [{"video": VIDEO, "image": IMAGEM, "text": "legenda"}]}
        self.assertTrue(S._validar_story(campo, "t")[0])
        self.assertEqual(S._clean_story_field(campo)["slides"][0]["video"], VIDEO)
        self.assertEqual(S._clean_story_field({"slides": [{"video": VIDEO}]})["slides"][0]["video"], VIDEO)

    def test_story_beat_entrega_o_video_ao_cliente(self):
        self.assertEqual(S._story_beat("k", [{"slides": [{"video": VIDEO}]}])["slides"][0]["video"], VIDEO)


class ArquivoTests(unittest.TestCase):
    def test_upload_aceita_video_e_recusa_outros(self):
        dados = base64.b64encode(b"\x00\x00\x00\x18ftypmp42").decode()
        with tempfile.TemporaryDirectory() as tmp:
            antigo, S.STORY_DIR = S.STORY_DIR, tmp
            try:
                self.assertEqual(S._save_story_upload("cena.mp4", dados), (True, "cena.mp4"))
                self.assertEqual(S._save_story_upload("cena.webm", dados), (True, "cena.webm"))
                self.assertFalse(S._save_story_upload("cena.avi", dados)[0])
            finally:
                S.STORY_DIR = antigo

    def _pedir(self, cabecalhos):
        class Req:
            path = "/" + VIDEO
            headers = cabecalhos
        return S._serve_static(Req())

    def test_video_sai_com_tipo_certo_e_aceita_faixa(self):
        inteiro = self._pedir({})
        self.assertEqual(inteiro.status, 200)
        self.assertEqual(inteiro.headers["Content-Type"], "video/mp4")
        self.assertEqual(inteiro.headers["Accept-Ranges"], "bytes")
        total = len(inteiro.body)
        parte = self._pedir({"Range": "bytes=10-19"})
        self.assertEqual(parte.status, 206)
        self.assertEqual(parte.headers["Content-Range"], f"bytes 10-19/{total}")
        self.assertEqual(parte.body, inteiro.body[10:20])
        aberta = self._pedir({"Range": f"bytes={total - 4}-"})
        self.assertEqual(aberta.body, inteiro.body[-4:])
        self.assertEqual(self._pedir({"Range": f"bytes={total + 5}-"}).status, 416)


class PracaVivaTests(unittest.TestCase):
    @staticmethod
    def _abertura(fatos):
        intro = GG.destinos()["elara_graciero_praca_viva"]["dungeons"][0]["intro"]

        def avaliar(req):
            return ((not req.get("fato") or req["fato"] in fatos)
                    and (not req.get("sem_fato") or req["sem_fato"] not in fatos))
        return S._story_beat("k", [intro], avaliar)["slides"]

    def test_ultimas_palavras_vem_antes_do_video(self):
        for fatos in ({"elara_ramo_a"}, {"elara_ramo_b"}):
            slides = self._abertura(fatos)
            self.assertEqual(len(slides), 2, fatos)
            self.assertEqual(slides[0]["image"], IMAGEM)
            self.assertIn("Gilo", slides[0]["text"])
            self.assertEqual(slides[1]["video"], VIDEO)

    def test_pista_da_montanha_so_no_ramo_em_que_o_olho_ja_partiu(self):
        self.assertIn("montanha", self._abertura({"elara_ramo_a"})[0]["text"])
        self.assertNotIn("montanha", self._abertura({"elara_ramo_b"})[0]["text"])

    def test_video_nao_depende_de_fato_gravado_so_ao_vencer(self):
        self.assertEqual(self._abertura(set())[-1]["video"], VIDEO)

    def test_encerramento_nao_repete_a_morte(self):
        self.assertEqual(GG.destinos()["elara_graciero_praca_viva"]["dungeons"][0]["outro"], "")

    def test_gravado_em_disco_igual_ao_gerador(self):
        with open(os.path.join(RAIZ, "world_adventures.json"), encoding="utf-8") as f:
            etapa = json.load(f)["elara_graciero_praca_viva"]["dungeons"][0]
        gerada = GG.destinos()["elara_graciero_praca_viva"]["dungeons"][0]
        self.assertEqual(S._clean_story_field(etapa["intro"]), S._clean_story_field(gerada["intro"]))
        self.assertEqual(etapa["outro"], "")

    def test_midia_existe(self):
        for caminho in (VIDEO, IMAGEM):
            self.assertTrue(os.path.isfile(os.path.join(RAIZ, caminho)), caminho)

    def test_mapa_nao_faz_o_morto_falar(self):
        with open(os.path.join(RAIZ, "dungeons", "elara_graciero_praca_viva.json"), encoding="utf-8") as f:
            falas = {x["id"]: x for x in json.load(f)["falas"]}
        self.assertNotIn("pracav_ultimas", falas)
        self.assertNotIn("cobrem o Gilo", falas["pracav_silencio"]["texto"])
        self.assertIn("garras", falas["pracav_silencio"]["texto"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
