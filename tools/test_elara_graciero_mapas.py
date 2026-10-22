"""Mapas de Graciero e do esconderijo do Leonel. Roda da raiz: python -X utf8 tools/test_elara_graciero_mapas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_graciero_fichas as F

for _fn in (F.ficha_escorpiao_gigante, F.ficha_leonel):
    _ok, _n = S._validate_custom_monster(_fn())
    if not any(m.get("type") == _n["type"] for m in S.MONSTER_DEFS):
        S.MONSTER_DEFS.append(dict(_n, _personalizado=True))
import elara_graciero_mapas as M
from gerar_campanha_sombras import salas_alcancaveis


def pares(d):
    return {(m["type"], tuple(m["pos"])) for m in d["monsters"]}


class MapasTests(unittest.TestCase):
    def test_todos_validam_e_sao_deterministicos(self):
        for arq, f in M.ARQUIVOS.items():
            d = f()
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{arq}: {msg}")
            self.assertEqual(json.dumps(d, sort_keys=True), json.dumps(f(), sort_keys=True), arq)

    def test_salas_alcancaveis_e_nd_contido(self):
        for arq, f in M.ARQUIVOS.items():
            d = f()
            self.assertEqual(len(salas_alcancaveis(d)), len(d["rooms"]), arq)
            poder = d["expected_party"]["heroes"] * d["expected_party"]["level"]
            for rid, nd in M.nd_por_sala(d).items():
                self.assertLessEqual(nd, 0.8 * poder, f"{arq} sala {rid}")

    def test_frentes_tem_relogio_baus_e_fatos(self):
        for f, fato in ((M.masmorra_beco, M.F_BECO), (M.masmorra_cais, M.F_CAIS)):
            d = f()
            rel = d["relogio"]
            self.assertEqual((rel["id"], rel["limite"], rel["fato_ao_passar"]), ("elara_graciero", 30, "elara_graciero_lento"))
            self.assertEqual(d["objectives"]["primary"]["type"], "open_key_chest")
            self.assertEqual(d["objectives"]["primary"]["fato"], fato)
            self.assertTrue(any(b.get("key_objective") for b in d["chests"]))
            self.assertEqual(d["expected_party"], {"heroes": 4, "level": 4})
        self.assertNotIn("leonel", json.dumps(M.masmorra_beco(), ensure_ascii=False).lower())
        self.assertIn("Leonel", json.dumps(M.masmorra_cais(), ensure_ascii=False))

    def test_pracas_mesma_planta_so_muda_fala_e_corpo(self):
        v, m = M.masmorra_praca_viva(), M.masmorra_praca_morta()
        self.assertEqual(pares(v), pares(m))
        self.assertEqual(v["tiles"], m["tiles"])
        self.assertEqual(sum(1 for x in v["monsters"] if x["type"] == F.TIPO_ESCORPIAO), len(v["monsters"]))
        pv, pm = v["objectives"]["primary"], m["objectives"]["primary"]
        self.assertEqual(pv["fato"], M.F_GILO_MORREU); self.assertEqual(pm["fato"], M.F_GILO_MORREU)
        self.assertEqual(set(pv["fatos"]), {M.F_VIU_MORRER, M.F_DICA_MONTANHA})
        self.assertNotIn("fatos", pm)
        self.assertFalse(any(x["type"] == "monte_ossos" for x in v["decorations"]))
        self.assertTrue(any(x["type"] == "monte_ossos" for x in m["decorations"]))
        self.assertTrue(any("montanha" in fl["texto"] for fl in v["falas"]))

    def test_alerta_acrescenta_sem_deslocar(self):
        n, a = M.masmorra_leonel_1(), M.masmorra_leonel_1_alerta()
        self.assertTrue(pares(n) < pares(a))
        self.assertEqual(len(a["monsters"]) - len(n["monsters"]), 2)
        self.assertEqual(len(a["traps"]) - len(n["traps"]), 1)
        self.assertEqual(n["tiles"], a["tiles"])

    def test_porao_tem_leonel_e_a_cela(self):
        d = M.masmorra_leonel_2()
        leo = [m for m in d["monsters"] if m["type"] == F.TIPO_LEONEL]
        self.assertEqual(len(leo), 1); self.assertTrue(leo[0]["target"])
        self.assertEqual(d["objectives"]["primary"]["type"], "kill_target")
        sec = d["objectives"]["secondary"][0]
        self.assertEqual((sec["type"], sec["fato"]), ("open_key_chest", M.F_ELARA))
        self.assertFalse(d["saida_permitida"])

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([f() for f in M.ARQUIVOS.values()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
