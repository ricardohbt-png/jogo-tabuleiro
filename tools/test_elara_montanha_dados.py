"""Rota do Olho: destino, slides, conversa-dica e fichas (dados do gerador + gravados em disco).
Roda da raiz: python -X utf8 tools/test_elara_montanha_dados.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_montanha as R
import gerar_elara_graciero as GG
import elara_montanha_fichas as F


class DadosTests(unittest.TestCase):
    def test_destino(self):
        d = R.destinos()["elara_montanha"]
        self.assertEqual([(e["file"], e["encadear"]) for e in d["dungeons"]],
                         [("elara_montanha_1.json", True), ("elara_montanha_2.json", True),
                          ("elara_montanha_3.json", False)])
        rq = d["requisito"]
        self.assertEqual((rq["fato"], rq["tambem_fato"], rq["sem_fato"]),
                         ("elara_dica_montanha", "elara_ramo_a", "elara_leonel_vencido"))
        self.assertTrue(d["oculto_ate_liberar"]); self.assertTrue(d["ocultar_apos_concluir"])

    def test_slides_com_requisitos_validos(self):
        slides = R.outro_rota()["slides"]
        self.assertGreaterEqual(len(slides), 5)
        for s in slides:
            if "requisito" in s:
                self.assertEqual(s["requisito"], S._clean_requirement(s["requisito"]))
        self.assertNotIn("requisito", slides[0]); self.assertNotIn("requisito", slides[-1])

    def test_conversa_dica_no_graciero(self):
        conv = next(c for convs in GG.conversas().values() for c in convs if c["id"] == "elara_graciero_serra")
        rq = conv["requisito"]
        self.assertEqual((rq["fato"], rq["tambem_fato"], rq["sem_fato"]),
                         ("elara_dica_montanha", "elara_ramo_a", "elara_leonel_vencido"))
        self.assertEqual(conv["efeito"]["fato"], "")

    def test_nada_da_rede_por_nome(self):
        texto = json.dumps([R.destinos(), GG.conversas()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, texto)


class DiscoTests(unittest.TestCase):
    def ler(self, nome):
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            return json.load(f)

    def test_destino_mapas_e_fichas_gravados(self):
        self.assertIn("elara_montanha", self.ler("world_adventures.json"))
        for arq in __import__("elara_montanha_mapas").ARQUIVOS:
            ok, msg = S.validar_dungeon(S.carregar_dungeon(arq))
            self.assertTrue(ok, f"{arq}: {msg}")
        tipos = {m["type"] for m in self.ler("monstros_personalizados.json")}
        self.assertIn(F.TIPO_ASSASSINO, tipos)
        self.assertNotIn(F.TIPO_BARDO, tipos, "o Bardo da Caravana é nativo (variante do Bardo), não ficha personalizada")
        with open(os.path.join(RAIZ, "tools", "editor_monsters_custom.js"), encoding="utf-8") as f:
            self.assertIn(F.TIPO_ASSASSINO, f.read())

    def test_conversa_dica_gravada_e_do_autor_preservadas(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["graciero"]["taverna"]["slots"]}
        ids = {c["id"] for c in slots["npc_ms2ef8oi"]["conversations"]}
        self.assertTrue({"elara_graciero_serra", "elara_graciero_elfo", "inicial", "fala_mulrezmy"} <= ids)


if __name__ == "__main__":
    unittest.main()
