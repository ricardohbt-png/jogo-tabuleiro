"""Parte 1 da campanha O Resgate de Elara: dados do gerador (cena do Templo, destino, fatos).
Roda da raiz: python -X utf8 tools/test_campanha_elara_parte1.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_campanha_elara as G


class DadosTests(unittest.TestCase):
    def test_destino_unico_com_duas_etapas_emendadas_e_oculto_ate_o_pedido(self):
        d = G.destinos()[G.AVENTURA]
        self.assertEqual([e["file"] for e in d["dungeons"]], ["casa_secreta.json", "fazenda.json"])
        self.assertEqual([e["encadear"] for e in d["dungeons"]], [True, False])
        self.assertTrue(d["oculto_ate_liberar"])
        self.assertEqual(d["requisito"]["fato"], G.F_PEDIU)
        self.assertTrue(d["ocultar_apos_concluir"])
        self.assertFalse(d["revisitavel"])

    def test_conversas_do_templo(self):
        ids = [c["id"] for c in G.conversas_templo()]
        for esperado in ("elara_pedido", "elara_pedro_irma", "elara_henrique_pilheria",
                         "elara_pos_fazenda_rapido", "elara_pos_fazenda_lento",
                         "elara_escolher_mocas", "elara_escolher_gilo"):
            self.assertIn(esperado, ids)

    def test_escolhas_sao_exclusivas(self):
        c = {c["id"]: c for c in G.conversas_templo()}
        a, b = c["elara_escolher_mocas"], c["elara_escolher_gilo"]
        self.assertEqual(a["efeito"]["fato"], G.F_RAMO_A)
        self.assertEqual(b["efeito"]["fato"], G.F_RAMO_B)
        self.assertEqual(a["requisito"]["sem_fato"], G.F_RAMO_B)
        self.assertEqual(b["requisito"]["sem_fato"], G.F_RAMO_A)

    def test_falas_de_heroi_so_com_o_heroi(self):
        c = {c["id"]: c for c in G.conversas_templo()}
        self.assertEqual(c["elara_pedro_irma"]["requisito"]["heroi_no_grupo"], "mage")
        self.assertEqual(c["elara_henrique_pilheria"]["requisito"]["heroi_no_grupo"], "bard")

    def test_nada_de_ferdinand_nem_vael_mon(self):
        texto = json.dumps([G.conversas_templo(), G.destinos(), G.cena_templo()], ensure_ascii=False).lower()
        for proibido in ("ferdinand", "vael", "mãos puras", "maos puras"):
            self.assertNotIn(proibido, texto)

    def test_relogio_padrao_e_generoso(self):
        rel = G.relogio_padrao()
        self.assertEqual(rel["fato_ao_passar"], G.F_LENTO)
        self.assertGreaterEqual(rel["limite"], 40)
        self.assertTrue(all(a["em"] <= rel["limite"] for a in rel["avisos"]))


class DiscoTests(unittest.TestCase):
    def ler(self, nome):
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            return json.load(f)

    def test_templo_aponta_para_a_cena(self):
        pontos = self.ler("city_map_points.json")["alva_e_luz"]
        self.assertEqual(pontos["templo"]["scene"], G.CENA_ID)
        self.assertEqual(pontos["templo"]["type"], "templo", "o ponto continua sendo o templo (loja)")

    def test_cena_gravada(self):
        cenas = self.ler("city_scenes.json")["alva_e_luz"]
        self.assertIn(G.CENA_ID, cenas)
        slot = next(s for s in cenas[G.CENA_ID]["slots"] if s["id"] == G.NPC_ID)
        self.assertEqual(slot["name"], "Exequiel")
        gravadas = {c["id"] for c in slot["conversations"]}
        self.assertTrue({c["id"] for c in G.conversas_templo()} <= gravadas)

    def test_destino_gravado(self):
        a = self.ler("world_adventures.json")
        self.assertIn(G.AVENTURA, a)
        self.assertEqual(a[G.AVENTURA]["requisito"]["fato"], G.F_PEDIU)

    def test_mapas_do_autor_tem_relogio_e_fato_de_vitoria(self):
        for arquivo, fato in (("casa_secreta.json", G.F_CASA), ("fazenda.json", G.F_FAZENDA)):
            d = S.carregar_dungeon(arquivo)
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{arquivo}: {msg}")
            self.assertEqual(d["relogio"]["id"], G.RELOGIO_ID, arquivo)
            self.assertEqual(d["objectives"]["primary"].get("fato"), fato, arquivo)


if __name__ == "__main__":
    unittest.main()
