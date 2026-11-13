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
            if cid.startswith("elara_riacho_cor_"):
                continue    # cor local: aparece só para quem NÃO está no Ramo A (testada à parte)
            req = c["requisito"]
            ramo = req.get("fato") in (R.F_RAMO_A, R.F_SONDOU, R.F_EXPOSTO, R.F_DECIDIDO, R.F_POUPADO, R.F_MOCAS,
                                       R.F_PISTA_BOLSA)
            self.assertTrue(ramo, f"{cid} precisa depender (direta ou indiretamente) do ramo A")
        self.assertEqual(todas()["elara_riacho_barman"][1]["requisito"]["fato"], R.F_RAMO_A)
        # tudo o mais da sondagem só existe depois de o barman receber o grupo (ordem causal)
        for cid in ("elara_riacho_mesa", "elara_riacho_rua", "elara_t1_gentil", "elara_t1_ameaca", "elara_t1_ignorou"):
            self.assertEqual(todas()[cid][1]["requisito"]["fato"], R.F_SONDOU, cid)

    def test_toda_conversa_de_progresso_some_depois_de_usada(self):
        """Ordem e causa-efeito: cada conversa que grava um fato de história é de uso único ou se esconde por ele."""
        for cid, (_slot, c) in todas().items():
            grava = c["efeito"]["fato"] or c["efeito"].get("fatos")
            if not grava:
                continue
            self.assertTrue(c["uma_vez"] or c["requisito"]["sem_fato"], f"{cid} reapareceria depois de usada")

    def test_cadeia_causal_ate_a_casa_e_alem(self):
        t = todas()
        self.assertEqual(t["elara_riacho_barman"][1]["efeito"]["fato"], R.F_SONDOU)
        self.assertEqual(t["elara_riacho_dica_bardo"][1]["requisito"]["fato"], R.F_EXPOSTO)
        self.assertEqual(t["elara_riacho_dica_bardo"][1]["requisito"]["sem_fato"], R.F_DECIDIDO)
        serva = t["elara_riacho_serva"][1]
        self.assertEqual(serva["requisito"]["fato"], R.F_DECIDIDO, "a pista do celeiro vem depois de decidir sobre o bardo")

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
        self.assertEqual(casa["requisito"]["fato"], R.F_CASA_DESCOBERTA)
        self.assertEqual(celeiro["requisito"]["fato"], R.F_DECIDIDO)
        self.assertEqual(celeiro["requisito"]["tambem_fato"], R.F_CELEIRO_DESCOBERTO)
        for x in (casa, celeiro):
            self.assertTrue(x["oculto_ate_liberar"])
            self.assertTrue(x["ocultar_apos_concluir"])
            self.assertTrue(x["so_na_cidade"], "a entrada é um ponto dentro da vila, não um marcador do mapa-múndi")

    def test_pistas_da_casa_do_tome(self):
        t = todas()
        self.assertEqual(t["elara_riacho_mesa"][1]["efeito"]["fato"], R.F_PISTA_BOLSA)
        self.assertEqual(t["elara_riacho_rua"][1]["efeito"]["fato"], R.F_PISTA_RUA)
        self.assertEqual(t["elara_riacho_rua"][0], "npc_ms254rwd")
        fim = t["elara_riacho_endereco"][1]
        self.assertEqual(t["elara_riacho_endereco"][0], "barman")
        self.assertEqual((fim["requisito"]["fato"], fim["requisito"]["tambem_fato"], fim["requisito"]["sem_fato"]),
                         (R.F_PISTA_BOLSA, R.F_PISTA_RUA, R.F_CASA_DESCOBERTA))
        self.assertEqual(fim["efeito"]["fato"], R.F_CASA_DESCOBERTA)
        self.assertTrue(fim["uma_vez"])
        self.assertEqual(t["elara_riacho_serva"][1]["efeito"]["fato"], R.F_CELEIRO_DESCOBERTO)

    def test_pontos_da_vila(self):
        p = R.pontos()
        self.assertEqual(set(p), {R.PONTO_CASA, R.PONTO_CELEIRO})
        self.assertEqual(p[R.PONTO_CASA]["aventura"], "elara_riacho_casa")
        self.assertEqual(p[R.PONTO_CELEIRO]["aventura"], "elara_riacho_celeiro")
        for x in p.values():
            self.assertEqual(x["type"], "dungeon")
            self.assertTrue(0 <= x["x"] <= 100 and 0 <= x["y"] <= 100)

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

    def test_conversas_de_outra_cidade_foram_trocadas_por_falas_do_riacho(self):
        cena = self.ler("city_scenes.json")["vila_riacho"]["taverna"]
        ids = {c["id"] for sl in cena["slots"] for c in sl["conversations"]}
        self.assertFalse(ids & R.ANTIGAS_RIACHO, "as cópias da taverna de Alva e Luz saíram")
        self.assertNotIn("Alva e Luz", json.dumps(cena, ensure_ascii=False), "nada de outra cidade na taverna do Riacho")
        self.assertTrue({"elara_riacho_cor_barman", "elara_riacho_cor_mesa", "elara_riacho_cor_bardo"} <= ids)

    def test_fala_local_so_para_quem_nao_esta_no_ramo_a(self):
        for cid in ("elara_riacho_cor_barman", "elara_riacho_cor_mesa", "elara_riacho_cor_bardo"):
            self.assertEqual(todas()[cid][1]["requisito"]["sem_fato"], R.F_RAMO_A, cid)
            self.assertFalse(todas()[cid][1]["efeito"]["fato"] or todas()[cid][1]["efeito"].get("fatos"), cid)

    def test_nenhum_slot_removido_recebe_conversa(self):
        for s in self.ler("city_scenes.json")["vila_riacho"]["taverna"]["slots"]:
            if s.get("removed"):
                self.assertFalse([c for c in s["conversations"] if c["id"].startswith("elara_")], s["id"])

    def test_pontos_gravados_na_vila(self):
        pontos = self.ler("city_map_points.json")["vila_riacho"]
        for pid, esperado in R.pontos().items():
            self.assertEqual(pontos[pid]["aventura"], esperado["aventura"], pid)
            self.assertEqual(pontos[pid]["type"], "dungeon", pid)

    def test_destinos_e_mapas_gravados(self):
        a = self.ler("world_adventures.json")
        for did in ("elara_riacho_casa", "elara_riacho_celeiro"):
            self.assertIn(did, a)
        for arq in ("elara_riacho_casa.json", "elara_riacho_celeiro.json"):
            ok, msg = S.validar_dungeon(S.carregar_dungeon(arq))
            self.assertTrue(ok, f"{arq}: {msg}")


if __name__ == "__main__":
    unittest.main()
