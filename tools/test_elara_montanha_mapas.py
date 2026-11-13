"""Mapas da rota do Olho. Roda da raiz: python -X utf8 tools/test_elara_montanha_mapas.py"""
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import elara_montanha_fichas as F

for _fn in (F.ficha_assassino,):
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

    def test_desfiladeiro_usa_o_terreno_do_penhasco(self):
        d = M.masmorra_desfiladeiro()
        base = S.carregar_dungeon("penhasco.json")
        for campo in ("grid", "tiles", "materiais", "elevacoes", "pontes", "decorations", "entrance"):
            self.assertEqual(d[campo], base[campo], campo)
        self.assertEqual((d["id"], d["ambiente"], d["exit"]), ("elara_montanha_2", "ar_livre", {"x": 16, "y": 0}))
        self.assertEqual(base["monsters"], [], "o mapa do autor segue sem monstros")

    def test_monstros_de_cada_margem_em_chao_firme(self):
        d = M.masmorra_desfiladeiro()
        r = S.GameRoom("PENHASCO")
        r.load_authored_dungeon(d)
        ent = (d["entrance"]["x"], d["entrance"]["y"])
        armadilhas = {tuple(t["pos"]) for t in d["traps"]}
        casas = [tuple(m["pos"]) for m in d["monsters"]]
        self.assertEqual(len(casas), len(set(casas)))
        for m in d["monsters"]:
            x, y = m["pos"]
            self.assertEqual(m["room_id"], 0 if y >= 13 else 1, m)
            self.assertNotEqual(d["materiais"].get(f"{x},{y}"), "ceu_abismo", m)
            self.assertNotIn((x, y), r._ponte_tiles, m)
            self.assertFalse(r._blocks_tile(x, y), m)
            self.assertNotIn((x, y), armadilhas, m)
            self.assertGreaterEqual(max(abs(x - ent[0]), abs(y - ent[1])), 4, m)
        self.assertEqual(len(d["monsters"]), 25)
        self.assertLess(sum(M.nd_por_sala(d).values()), 20, "mais leve que as 38 criaturas do mapa antigo")

    def test_bau_de_pocoes_antes_da_ponte(self):
        d = M.masmorra_desfiladeiro()
        self.assertEqual(len(d["chests"]), 1)
        bau = d["chests"][0]
        x, y = bau["pos"]
        self.assertGreaterEqual(y, 14, "na margem sul, antes da ponte")
        self.assertNotEqual(d["materiais"].get(f"{x},{y}"), "ceu_abismo")
        self.assertEqual([i["id"] for i in bau["items"]], ["health_potion_improved"] * 4)
        self.assertFalse(bau["key_objective"])
        self.assertNotIn([x, y], [m["pos"] for m in d["monsters"]] + [t["pos"] for t in d["traps"]])
        r = S.GameRoom("BAU")
        r.load_authored_dungeon(d)
        self.assertFalse(r._blocks_tile(x + 1, y), "dá para chegar ao lado do baú")
        itens = [i for b in r.chests.values() for i in b["items"]]
        self.assertEqual([(i["id"], i["effect"]) for i in itens], [("health_potion_improved", "heal")] * 4)

    def test_ordem_dos_acontecimentos_na_travessia(self):
        d = M.masmorra_desfiladeiro()
        f = {x["id"]: x for x in d["falas"]}
        self.assertEqual(list(f), ["desfil_chegada", "desfil_morte", "desfil_rastro", "desfil_margem"])
        ent = (d["entrance"]["x"], d["entrance"]["y"])

        def alcanca(fala, casa):
            return max(abs(casa[0] - fala["pos"][0]), abs(casa[1] - fala["pos"][1])) <= fala["trigger"]["raio"]

        self.assertTrue(alcanca(f["desfil_chegada"], ent))
        for fid in ("desfil_morte", "desfil_rastro", "desfil_margem"):
            self.assertFalse(alcanca(f[fid], ent), f"{fid} não pode sair na chegada")
        self.assertFalse(alcanca(f["desfil_morte"], (12, 15)), "só com a guarda da ponte fora do caminho")
        self.assertTrue(alcanca(f["desfil_morte"], (12, 14)))
        self.assertTrue(alcanca(f["desfil_rastro"], (13, 14)))
        self.assertFalse(alcanca(f["desfil_margem"], (12, 13)), "a outra margem só depois da ponte")
        self.assertTrue(alcanca(f["desfil_margem"], (12, 5)))

    def test_nada_da_rede_por_nome(self):
        t = json.dumps([f() for f in M.ARQUIVOS.values()], ensure_ascii=False).lower()
        for p in ("ferdinand", "vael", "rede de bardos", "porto saledo"):
            self.assertNotIn(p, t)


if __name__ == "__main__":
    unittest.main()
