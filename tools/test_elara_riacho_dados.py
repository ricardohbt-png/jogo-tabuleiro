"""Ramo A (Riacho): conversas, tratamento do bardo e destinos (dados do gerador + gravados em disco).
Roda da raiz: python -X utf8 tools/test_elara_riacho_dados.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_riacho as R


def todas():
    return {c["id"]: (slot, c) for slot, convs in R.conversas().items() for c in convs}


class DadosTests(unittest.TestCase):
    def test_conversas_existem_nos_slots_certos(self):
        t = todas()
        esperado = {
            "elara_riacho_barman": "barman", "elara_riacho_mesa": "patrono_fundo", "elara_riacho_serva": "npc_ms254rwd",
            "elara_t1_gentil": "cartas", "elara_t1_ameaca": "cartas", "elara_t1_ignorou": "cartas",
            "elara_bardo_matar": "cartas", "elara_bardo_interrogar": "cartas", "elara_bardo_poupar": "cartas",
            "elara_bardo_escoltar": "barman", "elara_bardo_entregar": "barman"}
        for cid, slot in esperado.items():
            self.assertIn(cid, t, cid)
            self.assertEqual(t[cid][0], slot, cid)

    def test_so_aparece_com_o_ramo_a(self):
        for cid, (_slot, c) in todas().items():
            req = c["requisito"]
            ramo = req.get("fato") == R.F_RAMO_A or req.get("fato") in (R.F_EXPOSTO, R.F_POUPADO, R.F_MOCAS)
            self.assertTrue(ramo, f"{cid} precisa depender (direta ou indiretamente) do ramo A")
        for cid in ("elara_riacho_barman", "elara_riacho_mesa", "elara_t1_gentil", "elara_t1_ameaca", "elara_t1_ignorou"):
            self.assertEqual(todas()[cid][1]["requisito"]["fato"], R.F_RAMO_A)

    def test_tratamento_1_e_exclusivo(self):
        for cid in ("elara_t1_gentil", "elara_t1_ameaca", "elara_t1_ignorou"):
            c = todas()[cid][1]
            self.assertEqual(c["requisito"]["sem_fato"], R.F_T1_FEITO, cid)
            self.assertIn(R.F_T1_FEITO, c["efeito"]["fatos"], cid)
        self.assertEqual(todas()["elara_t1_ameaca"][1]["efeito"]["fato"], R.F_T1_AMEACA)
        self.assertIn(R.F_MALTRATADO, todas()["elara_t1_ameaca"][1]["efeito"]["fatos"])
        self.assertIn(R.F_GENTIL, todas()["elara_t1_gentil"][1]["efeito"]["fatos"])

    def test_confronto_exclusivo_e_cada_opcao_grava_o_seu(self):
        esperado = {"elara_bardo_matar": (R.F_MORTO, {R.F_DECIDIDO, R.F_LEONEL_CAUTELOSO}),
                    "elara_bardo_interrogar": (R.F_INTERROGADO, {R.F_DECIDIDO, R.F_VILA_ABALADA}),
                    "elara_bardo_poupar": (R.F_POUPADO, {R.F_DECIDIDO})}
        for cid, (fato, extras) in esperado.items():
            c = todas()[cid][1]
            self.assertEqual(c["requisito"]["fato"], R.F_EXPOSTO, cid)
            self.assertEqual(c["requisito"]["sem_fato"], R.F_DECIDIDO, cid)
            self.assertEqual(c["efeito"]["fato"], fato, cid)
            self.assertEqual(set(c["efeito"]["fatos"]), extras, cid)

    def test_acoes_finais_do_poupado_sao_exclusivas(self):
        esc, ent = todas()["elara_bardo_escoltar"][1], todas()["elara_bardo_entregar"][1]
        for c in (esc, ent):
            self.assertEqual(c["requisito"]["fato"], R.F_POUPADO)
            self.assertEqual(c["requisito"]["sem_fato"], R.F_FINAL)
            self.assertIn(R.F_FINAL, c["efeito"]["fatos"])
        self.assertEqual(esc["efeito"]["fato"], R.F_GENTIL)
        self.assertEqual(ent["efeito"]["fato"], R.F_MALTRATADO)

    def test_destinos(self):
        d = R.destinos()
        casa, celeiro = d["elara_riacho_casa"], d["elara_riacho_celeiro"]
        self.assertEqual([e["file"] for e in casa["dungeons"]], ["elara_riacho_casa.json"])
        self.assertEqual([e["file"] for e in celeiro["dungeons"]], ["elara_riacho_celeiro.json"])
        self.assertEqual(casa["requisito"]["fato"], R.F_RAMO_A)
        self.assertEqual(celeiro["requisito"]["fato"], R.F_DECIDIDO)
        for x in (casa, celeiro):
            self.assertTrue(x["oculto_ate_liberar"])
            self.assertTrue(x["ocultar_apos_concluir"])

    def test_nada_da_rede_por_nome(self):
        texto = json.dumps([R.conversas(), R.destinos()], ensure_ascii=False).lower()
        for proibido in ("ferdinand", "vael", "mãos puras", "rede de bardos"):
            self.assertNotIn(proibido, texto)


class DiscoTests(unittest.TestCase):
    def ler(self, nome):
        with open(os.path.join(RAIZ, nome), encoding="utf-8") as f:
            return json.load(f)

    def test_conversas_gravadas_nos_slots(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["vila_riacho"]["taverna"]["slots"]}
        for slot, convs in R.conversas().items():
            gravadas = {c["id"] for c in slots[slot]["conversations"]}
            self.assertTrue({c["id"] for c in convs} <= gravadas, slot)

    def test_conversas_do_autor_preservadas(self):
        slots = {s["id"]: s for s in self.ler("city_scenes.json")["vila_riacho"]["taverna"]["slots"]}
        self.assertIn("fala_ms520tuz", {c["id"] for c in slots["barman"]["conversations"]})

    def test_nenhum_slot_removido_recebe_conversa(self):
        for s in self.ler("city_scenes.json")["vila_riacho"]["taverna"]["slots"]:
            if s.get("removed"):
                self.assertFalse([c for c in s["conversations"] if c["id"].startswith("elara_")], s["id"])

    def test_destinos_e_mapas_gravados(self):
        a = self.ler("world_adventures.json")
        for did in ("elara_riacho_casa", "elara_riacho_celeiro"):
            self.assertIn(did, a)
        for arq in ("elara_riacho_casa.json", "elara_riacho_celeiro.json"):
            ok, msg = S.validar_dungeon(S.carregar_dungeon(arq))
            self.assertTrue(ok, f"{arq}: {msg}")


if __name__ == "__main__":
    unittest.main()
