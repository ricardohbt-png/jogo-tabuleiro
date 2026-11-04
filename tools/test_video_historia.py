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
            self.assertEqual(len(slides), 5, fatos)
            self.assertTrue(all(s.get("text") for s in slides), fatos)
            self.assertIn("Gilo", slides[0]["text"])

    def test_a_fala_vem_no_meio_com_ele_ja_cercado(self):
        for fatos in ({"elara_ramo_a"}, {"elara_ramo_b"}):
            slides = self._abertura(fatos)
            com_fala = [i for i, s in enumerate(slides) if "não era para ser assim" in s["text"]]
            self.assertEqual(com_fala, [2], fatos)
            self.assertEqual(slides[2]["video"], "assets/story/gilo_cena_3_cerco.mp4")

    def test_a_ordem_dos_fatos_vai_da_chegada_as_roupas(self):
        slides = self._abertura({"elara_ramo_a"})
        self.assertIn("Praça de Graciero", slides[0]["text"])
        self.assertNotIn("escorpi", slides[0]["text"].lower())
        self.assertIn("besta", slides[1]["text"])
        self.assertIn("derruba", slides[3]["text"])
        self.assertIn("capa", slides[4]["text"])
        self.assertIn("grades", slides[4]["text"])

    def test_gilo_culpa_o_leonel_nos_dois_ramos(self):
        for fatos in ({"elara_ramo_a"}, {"elara_ramo_b"}):
            fala = self._abertura(fatos)[2]["text"]
            self.assertIn("A culpa é do Leonel!", fala)
            self.assertIn("pagou ouro demais para eu dizer não", fala)
        self.assertIn("Só mais uma rua... eu vou conseguir", self._abertura({"elara_ramo_b"})[2]["text"])

    def test_as_duas_pracas_abrem_com_a_mesma_cena(self):
        d = GG.destinos()
        self.assertEqual(d["elara_graciero_praca_pedra"]["dungeons"][0]["intro"],
                         d["elara_graciero_praca_viva"]["dungeons"][0]["intro"])

    def test_cada_transicao_parte_da_cena_anterior(self):
        """A imagem atrás do vídeo é a cena de onde ele parte: trocar de slide não pisca."""
        slides = self._abertura({"elara_ramo_a"})
        self.assertNotIn("video", slides[0])
        self.assertEqual([s["image"] for s in slides[1:]],
                         ["assets/story/gilo_cena_1_chegada.jpg", "assets/story/gilo_cena_2_susto.jpg",
                          IMAGEM, "assets/story/gilo_cena_4_queda.jpg"])

    def test_pista_da_montanha_so_no_ramo_em_que_o_olho_ja_partiu(self):
        self.assertIn("montanha", self._abertura({"elara_ramo_a"})[2]["text"])
        self.assertNotIn("montanha", self._abertura({"elara_ramo_b"})[2]["text"])
        self.assertIn("embrulho", self._abertura({"elara_ramo_b"})[2]["text"])

    def test_cenas_nao_dependem_de_fato_gravado_so_ao_vencer(self):
        self.assertEqual(self._abertura(set())[-1]["video"], "assets/story/gilo_cena_5_roupas.mp4")

    def test_encerramento_nao_repete_a_morte(self):
        self.assertEqual(GG.destinos()["elara_graciero_praca_viva"]["dungeons"][0]["outro"], "")

    def test_gravado_em_disco_igual_ao_gerador(self):
        with open(os.path.join(RAIZ, "world_adventures.json"), encoding="utf-8") as f:
            etapa = json.load(f)["elara_graciero_praca_viva"]["dungeons"][0]
        gerada = GG.destinos()["elara_graciero_praca_viva"]["dungeons"][0]
        self.assertEqual(S._clean_story_field(etapa["intro"]), S._clean_story_field(gerada["intro"]))
        self.assertEqual(etapa["outro"], "")

    def test_midia_existe(self):
        caminhos = {VIDEO, IMAGEM}
        for slide in self._abertura({"elara_ramo_a"}):
            caminhos |= {slide["image"], slide.get("video", slide["image"])}
        for caminho in caminhos:
            self.assertTrue(os.path.isfile(os.path.join(RAIZ, caminho)), caminho)

    def test_quem_chega_tarde_descobre_o_leonel_na_praca_vazia(self):
        with open(os.path.join(RAIZ, "dungeons", "elara_graciero_praca_morta.json"), encoding="utf-8") as f:
            fala = next(x for x in json.load(f)["falas"] if x["id"] == "pracam_corpo")
        self.assertIn("Leonel", fala["texto"])
        self.assertIn("bilhete", fala["texto"])
        self.assertEqual(fala["texto"], next(x for x in GG.mapas()["elara_graciero_praca_morta.json"]["falas"]
                                             if x["id"] == "pracam_corpo")["texto"])

    def test_mapa_nao_faz_o_morto_falar(self):
        with open(os.path.join(RAIZ, "dungeons", "elara_graciero_praca_viva.json"), encoding="utf-8") as f:
            falas = {x["id"]: x for x in json.load(f)["falas"]}
        self.assertNotIn("pracav_ultimas", falas)
        self.assertNotIn("cobrem o Gilo", falas["pracav_silencio"]["texto"])
        self.assertIn("garras", falas["pracav_silencio"]["texto"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
