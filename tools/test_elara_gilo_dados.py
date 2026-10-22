"""Ramo B: conversas, destinos e ficha (dados do gerador + gravados em disco).
Roda da raiz: python -X utf8 tools/test_elara_gilo_dados.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_gilo as R
import elara_gilo_ficha as G


def todas():
    return {c["id"]: (slot, c) for slot, convs in R.conversas().items() for c in convs}


class DadosTests(unittest.TestCase):
    def test_conversas_nos_slots_certos(self):
        esperado = {"elara_corvin_barman": "barman", "elara_corvin_garconete": "npc_ms2e74bw",
                    "elara_corvin_bardo": "patrono_fundo", "elara_corvin_sombrio": "npc_ms2e85ew"}
        t = todas()
        for cid, slot in esperado.items():
            self.assertEqual(t[cid][0], slot, cid)

    def test_so_com_o_ramo_b(self):
        for cid, (_s, c) in todas().items():
            self.assertEqual(c["requisito"]["fato"], R.F_RAMO_B, cid)
        self.assertEqual(todas()["elara_corvin_barman"][1]["efeito"]["fato"], R.F_CHEGADA)

    def test_destinos(self):
        d = R.destinos()
        ad, co = d["elara_adhadal"], d["elara_corvin"]
        self.assertEqual([(e["file"], e["encadear"]) for e in ad["dungeons"]],
                         [("elara_adhadal_1.json", True), ("elara_adhadal_2.json", False)])
        self.assertEqual([(e["file"], e["encadear"]) for e in co["dungeons"]],
                         [("elara_corvin_cacada.json", True), ("elara_corvin_gilo.json", False)])
        self.assertEqual(ad["requisito"]["fato"], R.F_RAMO_B)
        self.assertEqual(co["requisito"]["aventura_id"], "elara_adhadal")
        for x in (ad, co):
            self.assertTrue(x["oculto_ate_liberar"]); self.assertTrue(x["ocultar_apos_concluir"])

    def test_nada_da_rede_por_nome(self):
        texto = json.dumps([R.conversas(), R.destinos()], ensure_ascii=False).lower()
        for proibido in ("ferdinand", "vael", "mãos puras", "rede de bardos"):
            self.assertNotIn(proibido, texto)


class DiscoTests(unittest.TestCase):
    def ler(self, nome):
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            return json.load(f)

    def test_conversas_gravadas_e_slots_ativos(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["vila_corvin"]["taverna"]["slots"]}
        for slot, convs in R.conversas().items():
            self.assertFalse(slots[slot].get("removed"), slot)
            self.assertTrue({c["id"] for c in convs} <= {c["id"] for c in slots[slot]["conversations"]}, slot)
        for s in slots.values():
            if s.get("removed"):
                self.assertFalse([c for c in s["conversations"] if c["id"].startswith("elara_")], s["id"])

    def test_destinos_mapas_e_ficha_gravados(self):
        a = self.ler("world_adventures.json")
        for did in ("elara_adhadal", "elara_corvin"):
            self.assertIn(did, a)
        for arq in ("elara_adhadal_1.json", "elara_adhadal_2.json", "elara_corvin_cacada.json",
                    "elara_corvin_gilo.json"):
            ok, msg = S.validar_dungeon(S.carregar_dungeon(arq))
            self.assertTrue(ok, f"{arq}: {msg}")
        gravada = [m for m in self.ler("monstros_personalizados.json") if m["type"] == G.TIPO_GILO]
        self.assertEqual(len(gravada), 1)
        with open(os.path.join(RAIZ, "tools", "editor_monsters_custom.js"), encoding="utf-8") as f:
            self.assertIn(G.TIPO_GILO, f.read())

    def test_conversas_do_autor_preservadas(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["vila_corvin"]["taverna"]["slots"]}
        for s in slots.values():
            autor = [c for c in s["conversations"] if not c["id"].startswith("elara_")]
            self.assertEqual(len(autor), len(s["conversations"]) - len(
                [c for c in s["conversations"] if c["id"].startswith("elara_")]))


if __name__ == "__main__":
    unittest.main()
