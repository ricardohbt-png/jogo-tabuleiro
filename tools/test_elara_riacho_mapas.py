"""Mapas do Ramo A (Vila do Riacho): a casa do morador comprado e o celeiro.
Roda da raiz: python -X utf8 tools/test_elara_riacho_mapas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_riacho_mapas as M
from gerar_campanha_sombras import nd_por_sala, faixa, salas_alcancaveis


class MapasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casa, cls.celeiro = M.masmorra_casa(), M.masmorra_celeiro()

    def test_validam(self):
        for d in (self.casa, self.celeiro):
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{d['id']}: {msg}")

    def test_todas_as_salas_alcancaveis(self):
        for d in (self.casa, self.celeiro):
            self.assertEqual(set(salas_alcancaveis(d, passagens_abertas=True)), {r["id"] for r in d["rooms"]}, d["id"])

    def test_porao_so_pela_estante(self):
        d = self.casa
        self.assertEqual(set(salas_alcancaveis(d)), {0, 1}, "o porão só existe depois de acionar a estante")
        chave = {x["id"]: x for x in d["decorations"]}["casa_estante"]
        self.assertFalse(chave.get("key_objective"), "acionar a estante não pode cumprir o objetivo do baú")
        for sp in d["secret_passages"]:
            self.assertEqual(sp["type"], "mechanism")
            self.assertEqual(sp["key_decor_ids"], ["casa_estante"])
        self.assertTrue(any("estante" in f["texto"] for f in d["falas"]), "uma fala precisa apontar a estante")

    def test_tome_e_o_alvo_e_o_bau_fica_no_porao(self):
        d = self.casa
        alvos = [m for m in d["monsters"] if m.get("target")]
        self.assertEqual(len(alvos), 1)
        self.assertEqual(alvos[0]["room_id"], 2)
        self.assertEqual(d["objectives"]["secondary"][0]["type"], "kill_target")
        porao = next(r for r in d["rooms"] if r["id"] == 2)
        bx, by = d["chests"][0]["pos"]
        self.assertTrue(porao["x"] <= bx < porao["x"] + porao["w"])

    def test_casa_com_bandidos_e_mais_armadilhas(self):
        d = self.casa
        self.assertGreaterEqual(len(d["traps"]), 5)
        self.assertGreaterEqual(sum(1 for m in d["monsters"] if m["type"] == M.TIPO_BANDIDO), 6)
        self.assertFalse([m for m in d["monsters"] if m["type"].startswith("goblin")], "casa só com gente da rede")
        self.assertGreaterEqual(len(d["decorations"]), 18)

    def test_casa_objetivo_armadilhas_e_bau_chave(self):
        d = self.casa
        self.assertEqual(d["id"], "elara_riacho_casa")
        self.assertEqual(d["objectives"]["primary"]["type"], "open_key_chest")
        self.assertEqual(d["objectives"]["primary"]["fato"], M.F_BARDO_EXPOSTO)
        self.assertGreaterEqual(len(d["traps"]), 2)
        self.assertTrue(any(c.get("key_objective") for c in d["chests"]))
        tipos = [m["type"] for m in d["monsters"]]
        self.assertGreaterEqual(tipos.count(M.TIPO_BANDIDO), 2)

    def test_celeiro_objetivo_refem_e_chefe(self):
        d = self.celeiro
        self.assertEqual(d["id"], "elara_riacho_celeiro")
        self.assertEqual(d["objectives"]["primary"]["type"], "rescue_prisoner")
        self.assertEqual(d["objectives"]["primary"]["fato"], M.F_MOCAS)
        self.assertNotIn("se_falhar", d["objectives"]["primary"], "sem castigo letal neste ramo")
        self.assertTrue(d["prisoner"])
        alvos = [m for m in d["monsters"] if m.get("target")]
        self.assertEqual(len(alvos), 1)
        self.assertGreaterEqual(sum(1 for m in d["monsters"] if m["type"] == M.TIPO_BANDIDO), 3)
        self.assertEqual(d.get("marcador_entrada"), "poste")

    def test_grupo_esperado_e_nenhuma_sala_mortal(self):
        for d in (self.casa, self.celeiro):
            self.assertEqual(d["expected_party"], {"heroes": 4, "level": 2})
            poder = d["expected_party"]["heroes"] * d["expected_party"]["level"]
            for rid, nd in nd_por_sala(d).items():
                self.assertNotEqual(faixa(nd, poder), "mortal", f"{d['id']} sala {rid} ND {nd}")

    def test_nao_e_um_passeio(self):
        for d in (self.casa, self.celeiro):
            poder = d["expected_party"]["heroes"] * d["expected_party"]["level"]
            nds = [nd for nd in nd_por_sala(d).values() if nd > 0]
            faixas = [faixa(nd, poder) for nd in nds]
            self.assertGreaterEqual(sum(1 for f in faixas if f != "facil"), len(faixas) // 2, d["id"])

    def test_deterministico(self):
        self.assertEqual(json.dumps(M.masmorra_casa(), sort_keys=True), json.dumps(self.casa, sort_keys=True))
        self.assertEqual(json.dumps(M.masmorra_celeiro(), sort_keys=True), json.dumps(self.celeiro, sort_keys=True))

    def test_nada_de_nomes_da_rede(self):
        texto = json.dumps([self.casa, self.celeiro], ensure_ascii=False).lower()
        for proibido in ("ferdinand", "vael", "mãos puras", "rede de bardos"):
            self.assertNotIn(proibido, texto)


if __name__ == "__main__":
    unittest.main()
