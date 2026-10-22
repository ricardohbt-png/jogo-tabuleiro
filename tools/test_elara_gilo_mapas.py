"""Mapas do Ramo B (Adhadal e Corvin). Roda da raiz: python -X utf8 tools/test_elara_gilo_mapas.py"""
import hashlib
import json
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_gilo_ficha as G

_ok, _norm = S._validate_custom_monster(G.ficha_gilo())
if not any(m.get("type") == G.TIPO_GILO for m in S.MONSTER_DEFS):
    S.MONSTER_DEFS.append(dict(_norm, _personalizado=True))
import elara_gilo_mapas as M


def hash_arquivo(nome):
    with open(os.path.join(RAIZ, "dungeons", nome), "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


class MapasTests(unittest.TestCase):
    def test_todos_validam_e_sao_deterministicos(self):
        for arq, f in M.ARQUIVOS.items():
            d = f()
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{arq}: {msg}")
            self.assertEqual(json.dumps(d, sort_keys=True), json.dumps(f(), sort_keys=True), arq)

    def test_adhadal_entrada_e_saida_alcancaveis(self):
        for f in (M.masmorra_adhadal_1, M.masmorra_adhadal_2):
            d = f()
            dist = M.alcancaveis(d, (d["entrance"]["x"], d["entrance"]["y"]))
            self.assertIn((d["exit"]["x"], d["exit"]["y"]), dist, d["id"])
            self.assertEqual(d["marcador_entrada"], "poste")

    def test_adhadal_2_sem_volta_e_com_nd_contido(self):
        d = M.masmorra_adhadal_2()
        self.assertFalse(d["saida_permitida"])
        self.assertLessEqual(M.nd_total(d), M.ND_MAX_ADHADAL)
        self.assertEqual(d["objectives"]["primary"]["type"], "reach_exit")
        self.assertEqual(d["objectives"]["primary"]["fato"], M.F_ADHADAL)
        saida = (d["exit"]["x"], d["exit"]["y"])
        self.assertNotIn(saida, {tuple(m["pos"]) for m in d["monsters"]})
        self.assertNotIn(saida, M.casas_bloqueadas(d))

    def test_adhadal_so_difere_do_prototipo_nos_campos_combinados(self):
        for f, proto in ((M.masmorra_adhadal_1, "floresta"), (M.masmorra_adhadal_2, "floresta_2")):
            d, p = f(), M._proto(proto)
            for k in ("id", "name", "marcador_entrada", "expected_party", "traps", "falas", "objectives",
                      "monsters", "exit", "saida_permitida"):
                d.pop(k, None); p.pop(k, None)
            self.assertEqual(d, p, proto)

    def test_prototipos_do_autor_intactos(self):
        antes = {n: hash_arquivo(n + ".json") for n in ("floresta", "floresta_2")}
        for f in (M.masmorra_adhadal_1, M.masmorra_adhadal_2):
            f()
        self.assertEqual(antes, {n: hash_arquivo(n + ".json") for n in ("floresta", "floresta_2")})
        r = subprocess.run(["git", "diff", "--quiet", "--", "dungeons/floresta.json", "dungeons/floresta_2.json"],
                           cwd=RAIZ)
        self.assertEqual(r.returncode, 0)

    def test_corvin_salas_alcancaveis_e_gilo_foge(self):
        d = M.masmorra_corvin_gilo()
        gilo = [m for m in d["monsters"] if m["type"] == G.TIPO_GILO]
        self.assertEqual(len(gilo), 1)
        self.assertTrue(gilo[0]["target"])
        self.assertEqual(gilo[0]["fuga_chefe"]["fato"], M.F_GILO_FUGIU)
        self.assertEqual(d["objectives"]["primary"]["type"], "kill_target")
        self.assertEqual(d["objectives"]["primary"]["fato"], M.F_PISTA)
        for f in (M.masmorra_corvin_cacada, M.masmorra_corvin_gilo):
            dd = f()
            self.assertTrue(set(range(len(dd["rooms"]))) <= {r["id"] for r in dd["rooms"]})
            from gerar_campanha_sombras import salas_alcancaveis
            self.assertEqual(len(salas_alcancaveis(dd)), len(dd["rooms"]), dd["id"])
        self.assertEqual(M.masmorra_corvin_cacada()["objectives"]["primary"]["fato"], M.F_CACADA)

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([f() for f in M.ARQUIVOS.values()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "leonel"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
