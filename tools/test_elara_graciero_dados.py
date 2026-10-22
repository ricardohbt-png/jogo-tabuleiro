"""Graciero: conversas, destinos, slides, fichas e item (dados do gerador + gravados em disco).
Roda da raiz: python -X utf8 tools/test_elara_graciero_dados.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_graciero as R
import elara_graciero_fichas as F


def todas():
    return {c["id"]: (slot, c) for slot, convs in R.conversas().items() for c in convs}


class DadosTests(unittest.TestCase):
    def test_conversas_nos_slots_certos(self):
        esperado = {"elara_gilo_pertences": "barman", "elara_graciero_garconete": "npc_ms2ee41a",
                    "elara_graciero_bardo_ajuda": "npc_ms2ee41a", "elara_graciero_bardo_traicao": "npc_ms2ee41a",
                    "elara_graciero_nobre": "npc_ms2egify", "elara_graciero_henrique": "npc_ms2egify",
                    "elara_graciero_gnomo": "npc_ms2ej3o7", "elara_graciero_pedro": "npc_ms2ej3o7",
                    "elara_graciero_elfo": "npc_ms2ef8oi"}
        t = todas()
        for cid, slot in esperado.items():
            self.assertEqual(t[cid][0], slot, cid)

    def test_toda_conversa_tem_porteiro(self):
        for cid, (_s, c) in todas().items():
            req = c["requisito"]
            self.assertTrue(req["fato"] or req.get("heroi_no_grupo"), cid)

    def test_bardo_e_olho(self):
        t = todas()
        ajuda, traicao = t["elara_graciero_bardo_ajuda"][1], t["elara_graciero_bardo_traicao"][1]
        self.assertEqual((ajuda["requisito"]["fato"], ajuda["requisito"]["tambem_fato"], ajuda["requisito"]["sem_fato"]),
                         (R.F_POUPADO, R.F_GENTIL, R.F_MALTRATADO))
        self.assertEqual(ajuda["efeito"]["fatos"], [R.F_DICA_MONTANHA])
        self.assertEqual((traicao["requisito"]["fato"], traicao["requisito"]["tambem_fato"]), (R.F_POUPADO, R.F_MALTRATADO))
        self.assertEqual(traicao["efeito"]["fatos"], [R.F_CAUTELOSO])
        olho = t["elara_gilo_pertences"][1]
        self.assertEqual(olho["efeito"]["item_id"], F.ID_OLHO)
        self.assertEqual((olho["requisito"]["fato"], olho["requisito"]["sem_fato"]), (R.F_GILO_MORREU, R.F_RAMO_A))

    def test_destinos(self):
        d = R.destinos()
        self.assertEqual(d["elara_graciero_beco"]["requisito"]["fato"], R.F_RUMO)
        self.assertEqual(d["elara_graciero_cais"]["requisito"]["aventura_id"], "elara_graciero_beco")
        viva, morta = d["elara_graciero_praca_viva"]["requisito"], d["elara_graciero_praca_morta"]["requisito"]
        self.assertEqual((viva["aventura_id"], viva["sem_fato"]), ("elara_graciero_cais", R.F_LENTO))
        self.assertEqual((morta["aventura_id"], morta["fato"]), ("elara_graciero_cais", R.F_LENTO))
        n, a = d["elara_leonel_casa"], d["elara_leonel_casa_alerta"]
        self.assertEqual([(e["file"], e["encadear"]) for e in n["dungeons"]],
                        [("elara_leonel_1.json", True), ("elara_leonel_2.json", False)])
        self.assertEqual([e["file"] for e in a["dungeons"]], ["elara_leonel_1_alerta.json", "elara_leonel_2.json"])
        self.assertEqual((n["requisito"]["fato"], n["requisito"]["sem_fato"]), (R.F_GILO_MORREU, R.F_CAUTELOSO))
        self.assertEqual((a["requisito"]["fato"], a["requisito"]["tambem_fato"]), (R.F_GILO_MORREU, R.F_CAUTELOSO))
        self.assertEqual(n["outro_rota"], a["outro_rota"])
        for x in d.values():
            self.assertTrue(x["oculto_ate_liberar"]); self.assertTrue(x["ocultar_apos_concluir"])

    def test_slides_tem_requisitos_validos_e_fecho_de_misterio(self):
        slides = R.outro_rota()["slides"]
        self.assertEqual(slides[-1].get("requisito"), None)
        for s in slides:
            if "requisito" in s:
                self.assertEqual(s["requisito"], S._clean_requirement(s["requisito"]))

    def test_nada_da_rede_por_nome(self):
        texto = json.dumps([R.conversas(), R.destinos()], ensure_ascii=False).lower()
        for proibido in ("ferdinand", "vael", "mãos puras", "rede de bardos", "porto saledo"):
            self.assertNotIn(proibido, texto)


class DiscoTests(unittest.TestCase):
    def ler(self, nome):
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            return json.load(f)

    def test_conversas_gravadas_e_slots_ativos(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["graciero"]["taverna"]["slots"]}
        for slot, convs in R.conversas().items():
            self.assertFalse(slots[slot].get("removed"), slot)
            self.assertTrue({c["id"] for c in convs} <= {c["id"] for c in slots[slot]["conversations"]}, slot)
        for s in slots.values():
            if s.get("removed"):
                self.assertFalse([c for c in s["conversations"] if c["id"].startswith("elara_")], s["id"])

    def test_conversas_do_autor_preservadas(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["graciero"]["taverna"]["slots"]}
        self.assertTrue({"inicial", "fala_mulr73l3", "fala_mulrbvne"} <= {c["id"] for c in slots["barman"]["conversations"]})
        self.assertTrue({"inicial", "fala_mulrezmy", "fala_mulrgts9"} <= {c["id"] for c in slots["npc_ms2ef8oi"]["conversations"]})

    def test_destinos_mapas_fichas_e_item_gravados(self):
        a = self.ler("world_adventures.json")
        for did in R.destinos():
            self.assertIn(did, a)
        for arq in __import__("elara_graciero_mapas").ARQUIVOS:
            ok, msg = S.validar_dungeon(S.carregar_dungeon(arq))
            self.assertTrue(ok, f"{arq}: {msg}")
        tipos = {m["type"] for m in self.ler("monstros_personalizados.json")}
        self.assertTrue({F.TIPO_ESCORPIAO, F.TIPO_LEONEL} <= tipos)
        self.assertIn(F.ID_OLHO, {i["id"] for i in self.ler("itens_personalizados.json")})
        for arq, chave in (("tools/editor_monsters_custom.js", F.TIPO_LEONEL), ("tools/editor_items_custom.js", F.ID_OLHO)):
            with open(os.path.join(RAIZ, arq), encoding="utf-8") as f:
                self.assertIn(chave, f.read())


if __name__ == "__main__":
    unittest.main()
