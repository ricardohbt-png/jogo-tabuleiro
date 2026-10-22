"""Mapas da rota do Olho. Roda da raiz: python -X utf8 tools/test_elara_montanha_mapas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_montanha_fichas as F

for _fn in (F.ficha_assassino, F.ficha_bardo_agente):
    _ok, _n = S._validate_custom_monster(_fn())
    if not any(m.get("type") == _n["type"] for m in S.MONSTER_DEFS):
        S.MONSTER_DEFS.append(dict(_n, _personalizado=True))
import elara_montanha_mapas as M
from elara_graciero_fichas import ID_OLHO
from gerar_campanha_sombras import salas_alcancaveis


class MapasTests(unittest.TestCase):
    def test_validam_e_sao_deterministicos(self):
        for arq, f in M.ARQUIVOS.items():
            d = f()
            ok, msg = S.validar_dungeon(d)
            self.assertTrue(ok, f"{arq}: {msg}")
            self.assertEqual(json.dumps(d, sort_keys=True), json.dumps(f(), sort_keys=True), arq)

    def test_salas_nd_grupo_poste_e_saida(self):
        for arq, f in M.ARQUIVOS.items():
            d = f()
            self.assertEqual(len(salas_alcancaveis(d)), len(d["rooms"]), arq)
            self.assertEqual(d["expected_party"], {"heroes": 4, "level": 5})
            self.assertEqual(d["marcador_entrada"], "poste")
            for rid, nd in M.nd_por_sala(d).items():
                self.assertTrue(M.ND_MIN <= nd <= M.ND_MAX, f"{arq} sala {rid}: {nd}")
        self.assertTrue(M.masmorra_trilha()["saida_permitida"])
        self.assertFalse(M.masmorra_desfiladeiro()["saida_permitida"])
        self.assertFalse(M.masmorra_caravana()["saida_permitida"])

    def test_objetivos_e_fatos(self):
        p1, p2, p3 = (f()["objectives"]["primary"] for f in (M.masmorra_trilha, M.masmorra_desfiladeiro, M.masmorra_caravana))
        self.assertEqual((p1["type"], p1["fato"]), ("reach_exit", M.F_TRILHA))
        self.assertEqual((p2["type"], p2["fato"]), ("reach_exit", M.F_DESFILADEIRO))
        self.assertEqual(p3["type"], "kill_target")
        self.assertEqual(set(p3["fatos"]), {M.F_ROTA, M.F_OLHO})
        self.assertEqual([i["id"] for i in p3["reward"]["items"]], [ID_OLHO])
        for p in (p1, p2):
            self.assertEqual(p["reward"]["items"], [])

    def test_assassino_unico_target_boss_com_fuga(self):
        d = M.masmorra_caravana()
        a = [m for m in d["monsters"] if m["type"] == F.TIPO_ASSASSINO]
        self.assertEqual(len(a), 1)
        self.assertTrue(a[0]["target"] and a[0]["boss"])
        self.assertEqual(a[0]["fuga_chefe"]["fato"], M.F_ASSASSINO_FUGIU)
        self.assertEqual(sum(1 for m in d["monsters"] if m["type"] == F.TIPO_BARDO), 1)

    def test_falas_por_via(self):
        for f in M.ARQUIVOS.values():
            for fl in f()["falas"]:
                req = fl.get("requisito")
                if fl["id"].endswith(("_guia", "_morte")):
                    self.assertEqual(req.get("fato"), M.F_BARDO_AJUDOU, fl["id"])
                    for proibido in ("salvar", "impedir", "poderiam"):
                        self.assertNotIn(proibido, fl["texto"].lower(), fl["id"])
                elif fl["id"].endswith(("_marcas", "_rastro")):
                    self.assertEqual(req.get("sem_fato"), M.F_BARDO_AJUDOU, fl["id"])
                else:
                    self.assertIsNone(req, fl["id"])

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([f() for f in M.ARQUIVOS.values()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
