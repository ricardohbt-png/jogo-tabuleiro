"""Campanha "A Maré do Charco": dados (6a), mapas (6b-6d) e calibração (6e).
Roda da raiz: python -X utf8 tools/test_campanha_charcos.py"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))
import server as S  # noqa: E402
import gerar_campanha_charcos as G  # noqa: E402


class DadosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dst = G.destinos()

    def test_um_unico_destino_liberado_pelo_gancho(self):
        self.assertEqual(set(self.dst), {G.AVENTURA})
        self.assertEqual(self.dst[G.AVENTURA]["requisito"]["fato"], G.FATO_GANCHO)

    def test_destinos_ocultos_ate_liberar(self):
        for d in self.dst.values():
            self.assertTrue(d["oculto_ate_liberar"], d["id"])

    def test_cinco_etapas_emendadas(self):
        et = self.dst[G.AVENTURA]["dungeons"]
        self.assertEqual([e["file"] for e in et], list(G.ARQUIVOS))
        self.assertEqual([e["encadear"] for e in et], [True, True, True, True, False])

    def test_arquivos_batem_com_os_destinos(self):
        usados = [e["file"] for d in self.dst.values() for e in d["dungeons"]]
        self.assertEqual(sorted(usados), sorted(G.ARQUIVOS))

    def test_conversa_do_gancho_so_antes_da_tragedia(self):
        c = next(c for c in G.conversas_taverna()["npc_ms42peq8"] if c["id"] == "charcos_gancho")
        self.assertEqual(c["requisito"]["sem_fato"], G.FATO_MORTE)
        self.assertEqual(c["efeito"]["fato"], G.FATO_GANCHO)
        self.assertTrue(c["uma_vez"])

    def test_conversas_hostis_exigem_o_marcador_da_morte(self):
        conv = G.conversas_taverna()
        hostis = [c for cs in conv.values() for c in cs if c["id"].startswith("charcos_hostil")]
        self.assertGreaterEqual(len(hostis), 3, "um NPC por slot")
        for c in hostis:
            self.assertEqual(c["requisito"]["fato"], G.FATO_MORTE)
            self.assertFalse(c["uma_vez"], "a raiva se repete")

    def test_conversa_calorosa_so_com_vila_agradecida(self):
        conv = {c["id"]: c for c in G.conversas_taverna()["npc_ms42peq8"]}
        self.assertEqual(conv["charcos_gratidao"]["requisito"], {"fato": "charcos_criancas_todas"})
        self.assertEqual(conv["charcos_gratidao_parcial"]["requisito"], {"fato": "charcos_criancas_salvas"})

    def test_luto_na_taverna(self):
        conv = G.conversas_taverna()["npc_ms42peq8"]
        luto = next(c for c in conv if c["id"] == "charcos_luto_ysa")
        self.assertEqual(luto["requisito"], {"fato": "charcos_criancas_perdidas"})
        self.assertTrue(luto["texto"].strip())
        r = S.GameRoom("LUTO")
        visiveis = lambda fatos: [c["id"] for c in conv
                                  if (setattr(r, "fatos", set(fatos)) or True) and r._avaliar_requisito(c["requisito"])[0]]
        self.assertIn("charcos_luto_ysa", visiveis({"charcos_criancas_perdidas"}))
        for fatos in (set(), {"charcos_criancas_todas"}, {"charcos_criancas_salvas"}, {G.FATO_MORTE}):
            self.assertNotIn("charcos_luto_ysa", visiveis(fatos), fatos)
        for fatos in ({"charcos_criancas_perdidas"}, {G.FATO_MORTE}, {"charcos_criancas_salvas"}):
            self.assertNotIn("charcos_gratidao", visiveis(fatos), fatos)
        self.assertIn("charcos_gratidao", visiveis({"charcos_criancas_todas"}))
        self.assertIn("charcos_gratidao_parcial", visiveis({"charcos_criancas_salvas"}))

    def test_rota_sem_renome_proprio(self):
        self.assertEqual(self.dst[G.AVENTURA]["renome_recompensa"], 0)

    def test_modificador_da_vila_so_para_o_marcador_da_morte(self):
        self.assertEqual(G.modificadores(), {"vila_dos_charcos": [{"fato": G.FATO_MORTE, "preco_mult": 1.5}]})

    def test_trofeu_valida_como_item_custom(self):
        ok, item = S._validate_custom_item(G.trofeu_bruto())
        self.assertTrue(ok, item)
        self.assertEqual(item["id"], G.ITEM_TROFEU)
        self.assertEqual(item["categoria"], "perfurante")
        self.assertTrue(item["finesse"])
        self.assertFalse(item["disponibilidade"]["loja"])

    def texto_do_fim(self, fatos):
        r = S.GameRoom("FIM"); r.fatos = set(fatos)
        beat = S._story_beat("fim:x", [self.dst[G.AVENTURA]["outro_rota"]], r._requisito_do_slide)
        return [s["text"] for s in beat["slides"]]

    def test_final_por_faixa(self):
        casos = {
            "todas": ({"charcos_criancas_todas"}, "seis pequenos"),
            "salvas": ({"charcos_criancas_salvas"}, "a maioria"),
            "perdidas": ({"charcos_criancas_perdidas"}, "nem todos"),
            "mortas": ({G.FATO_MORTE}, "não vão voltar"),
        }
        textos = {}
        for nome, (fatos, marca) in casos.items():
            with self.subTest(faixa=nome):
                slides = self.texto_do_fim(fatos)
                junto = " ".join(slides).lower()
                self.assertIn(marca, junto)
                for outro, (_, m2) in casos.items():
                    if outro != nome:
                        self.assertNotIn(m2, junto, f"{nome} não mostra o slide de {outro}")
                textos[nome] = slides
        self.assertEqual(len({tuple(v) for v in textos.values()}), 4)
        # o amargo só com zero salvas; a vila agradecida/de luto nunca vê o amargo
        for nome in ("todas", "salvas", "perdidas"):
            self.assertNotIn("não vão voltar", " ".join(textos[nome]).lower())
        # "Mais fundo no charco..." fecha o final de todo mundo, menos do amargo
        for nome in ("todas", "salvas", "perdidas"):
            self.assertIn("mais fundo", " ".join(textos[nome]).lower())
        self.assertNotIn("mais fundo", " ".join(textos["mortas"]).lower())

    def test_ferrao_morto_mantem_o_slide_proprio(self):
        com = " ".join(self.texto_do_fim({"charcos_criancas_salvas", G.FATO_FERRAO})).lower()
        sem = " ".join(self.texto_do_fim({"charcos_criancas_salvas"})).lower()
        amargo = " ".join(self.texto_do_fim({G.FATO_MORTE, G.FATO_FERRAO})).lower()
        self.assertIn("o ferrão tomba entre as chamas", com)
        self.assertNotIn("o ferrão tomba entre as chamas", sem)
        self.assertNotIn("o ferrão tomba entre as chamas", amargo)
        self.assertIn("não vão voltar", amargo)

    def test_conflito_se_masmorra_foi_editada(self):
        with tempfile.TemporaryDirectory() as d:
            c = self._caminhos(d)
            art = G.preparar(so_dados=True)
            G.aplicar(art, c, regen_editor=False)
            Path(d, "dungeons").mkdir(exist_ok=True)
            # sem masmorras (so_dados), nada a conflitar; com masmorra editada à mão, recusa
            arq = Path(d, "dungeons", "charcos_1_bordas.json")
            arq.write_text('{"editada": true}', encoding="utf-8")
            art2 = {"masmorras": {"charcos_1_bordas.json": {"x": 1}}, "destinos": art["destinos"],
                    "conversas": art["conversas"], "modificadores": art["modificadores"], "trofeu": art["trofeu"]}
            with self.assertRaises(G.Conflito):
                G.aplicar(art2, c, regen_editor=False)

    def test_aplicar_so_toca_em_charcos_e_e_idempotente(self):
        with tempfile.TemporaryDirectory() as d:
            c = self._caminhos(d)
            antes = json.loads(Path(c["adventures"]).read_text(encoding="utf-8"))
            art = G.preparar(so_dados=True)
            G.aplicar(art, c, regen_editor=False)
            G.aplicar(art, c, regen_editor=False)
            depois = json.loads(Path(c["adventures"]).read_text(encoding="utf-8"))
            for k, v in antes.items():
                self.assertEqual(depois[k], v, f"{k} não pode mudar")
            self.assertEqual({k for k in depois if k.startswith("charcos_")}, set(self.dst))
            cenas = json.loads(Path(c["scenes"]).read_text(encoding="utf-8"))
            slots = cenas["vila_dos_charcos"]["taverna"]["slots"]
            ysa = next(s for s in slots if s["id"] == "npc_ms42peq8")
            self.assertEqual(len([x for x in ysa["conversations"] if x["id"] == "charcos_gancho"]), 1)
            self.assertEqual(json.loads(Path(c["mods"]).read_text(encoding="utf-8")),
                             {"vila_dos_charcos": [{"fato": G.FATO_MORTE, "preco_mult": 1.5}]})
            itens = json.loads(Path(c["items"]).read_text(encoding="utf-8"))
            self.assertEqual([i["id"] for i in itens].count(G.ITEM_TROFEU), 1)

    def _caminhos(self, d):
        d = Path(d)
        (d / "dungeons").mkdir(exist_ok=True)
        for nome in ("world_adventures.json", "city_scenes.json", "itens_personalizados.json"):
            (d / nome).write_bytes((RAIZ / nome).read_bytes())
        (d / "cidade_modificadores.json").write_text("{}", encoding="utf-8")
        return {"dungeons_dir": str(d / "dungeons"), "adventures": str(d / "world_adventures.json"),
                "scenes": str(d / "city_scenes.json"), "items": str(d / "itens_personalizados.json"),
                "items_index": str(d / "editor_items_custom.js"), "mods": str(d / "cidade_modificadores.json"),
                "assinaturas": str(d / "assin.json")}


if __name__ == "__main__":
    unittest.main()
