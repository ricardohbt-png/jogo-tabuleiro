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

    def test_ids_e_cadeia_de_requisitos(self):
        self.assertEqual(set(self.dst), {"charcos_bordas", "charcos_palafitas", "charcos_travessia", "charcos_aldeia"})
        self.assertEqual(self.dst["charcos_bordas"]["requisito"]["fato"], G.FATO_GANCHO)
        self.assertEqual(self.dst["charcos_palafitas"]["requisito"]["aventura_id"], "charcos_bordas")
        self.assertEqual(self.dst["charcos_travessia"]["requisito"]["aventura_id"], "charcos_palafitas")
        self.assertEqual(self.dst["charcos_aldeia"]["requisito"]["aventura_id"], "charcos_travessia")

    def test_destinos_ocultos_ate_liberar(self):
        for d in self.dst.values():
            self.assertTrue(d["oculto_ate_liberar"], d["id"])

    def test_ultimo_destino_tem_duas_etapas_emendadas(self):
        et = self.dst["charcos_aldeia"]["dungeons"]
        self.assertEqual([e["file"] for e in et], ["charcos_4a_arredores.json", "charcos_4b_aldeia.json"])
        self.assertTrue(et[0]["encadear"])
        self.assertFalse(et[1]["encadear"])

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

    def test_conversa_calorosa_so_sem_tragedia_e_com_rota(self):
        c = next(c for c in G.conversas_taverna()["npc_ms42peq8"] if c["id"] == "charcos_gratidao")
        self.assertEqual(c["requisito"]["sem_fato"], G.FATO_MORTE)
        self.assertEqual(c["requisito"]["aventura_id"], "charcos_aldeia")

    def test_modificador_da_vila_so_para_o_marcador_da_morte(self):
        self.assertEqual(G.modificadores(), {"vila_dos_charcos": [{"fato": G.FATO_MORTE, "preco_mult": 1.5}]})

    def test_trofeu_valida_como_item_custom(self):
        ok, item = S._validate_custom_item(G.trofeu_bruto())
        self.assertTrue(ok, item)
        self.assertEqual(item["id"], G.ITEM_TROFEU)
        self.assertEqual(item["categoria"], "perfurante")
        self.assertTrue(item["finesse"])
        self.assertFalse(item["disponibilidade"]["loja"])

    def test_final_tem_slides_condicionais_por_marcador(self):
        slides = self.dst["charcos_aldeia"]["outro_rota"]["slides"]
        reqs = [(s.get("requisito") or {}, bool(s.get("negar"))) for s in slides]

        def texto(fatos):
            r = S.GameRoom("FIM"); r.fatos = set(fatos)
            beat = S._story_beat("fim:x", [self.dst["charcos_aldeia"]["outro_rota"]], r._requisito_do_slide)
            return " ".join(s["text"] for s in beat["slides"])

        vitoria = texto({G.FATO_FERRAO})
        fuga = texto(set())
        amargo = texto({G.FATO_FERRAO, G.FATO_MORTE})
        self.assertNotEqual(vitoria, fuga)
        self.assertNotEqual(vitoria, amargo)
        self.assertIn("tomba", vitoria.lower())
        self.assertNotIn("tomba", fuga.lower())
        self.assertIn("não vão voltar", amargo.lower())
        self.assertNotIn("não vão voltar", vitoria.lower())
        self.assertTrue(any(r.get("sem_fato") for r, _ in reqs))

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
