"""Campanha "A Maré do Charco": os cinco mapas (6b-6e).
Roda da raiz: python -X utf8 tools/test_campanha_charcos_mapas.py"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))
import server as S  # noqa: E402
import gerar_campanha_charcos as G  # noqa: E402


class MapasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        art = G.preparar()
        cls.mm = art["masmorras"]
        cls.defs = {m["type"]: m for m in S.MONSTER_DEFS}

    def tipos(self, arq, sala=None):
        return [m["type"] for m in self.mm[arq]["monsters"] if sala is None or m["room_id"] == sala]

    def aldeia(self):
        return self.mm["charcos_4b_aldeia.json"]

    def test_todas_validam_e_sao_alcancaveis(self):
        for arq, d in self.mm.items():
            self.assertTrue(S.validar_dungeon(d)[0], arq)
            todas = {r["id"] for r in d["rooms"]}
            self.assertEqual(G.salas_alcancaveis(d, passagens_abertas=True), todas, arq)

    def test_expected_party_e_ambiente(self):
        for arq, d in self.mm.items():
            self.assertEqual(d["ambiente"], "ar_livre", arq)
            self.assertEqual(d["expected_party"]["heroes"], 4)
            self.assertGreaterEqual(d["expected_party"]["level"], 2)

    # Bordas
    def test_bordas_tem_os_inimigos_pedidos(self):
        t = set(self.tipos("charcos_1_bordas.json"))
        for esperado in ("lobo_cinzento", "lobo_cinzento_customizado", "rato", "rato_gigante", "aranha_sombria",
                         "escorpiao_pedra", "escorpiao_pequeno", "cobra_venenosa"):
            self.assertIn(esperado, t)
        alvo = [m for m in self.mm["charcos_1_bordas.json"]["monsters"] if m["target"]]
        self.assertEqual([m["type"] for m in alvo], ["lobo_cinzento_customizado"])

    def test_bordas_pistas(self):
        d = self.mm["charcos_1_bordas.json"]
        self.assertTrue(any(i.get("id") == "carta" and "sapatinho" in i.get("texto", "")
                            for b in d["chests"] for i in b["items"]))
        self.assertTrue(any(x["type"] in ("monte_ossos", "ossos_semi_enterrados") for x in d["decorations"]))

    # Palafitas
    def test_palafitas_inimigos(self):
        t = set(self.tipos("charcos_2_palafitas.json"))
        for esperado in ("crocodilo_jovem", "jacare", "cobra_constritora", "cobra_venenosa",
                         "devorador_organico", "escorpiao_pedra", "escorpiao_pequeno"):
            self.assertIn(esperado, t)
        alvo = [m for m in self.mm["charcos_2_palafitas.json"]["monsters"] if m["target"]]
        self.assertEqual([m["type"] for m in alvo], ["jacare"])

    def test_palafitas_tem_agua_pontes_e_chao_ilusorio(self):
        d = self.mm["charcos_2_palafitas.json"]
        self.assertIn("agua", set(d["materiais"].values()))
        self.assertTrue(d["pontes"])
        arm = [t for t in d["traps"] if t["tipo"] == "chao_illusorio"]
        self.assertEqual(len(arm), 1)
        self.assertEqual(arm[0]["ponte_id"], d["pontes"][0]["id"])

    def test_palafitas_deposito_com_oleo_e_piche_e_carta(self):
        itens = [i for b in self.mm["charcos_2_palafitas.json"]["chests"] for i in b["items"]]
        ids = [i["id"] for i in itens]
        self.assertEqual(ids.count("frasco_oleo"), 2)
        self.assertEqual(ids.count("frasco_piche"), 2)
        self.assertTrue(any(i["id"] == "carta" and i.get("texto") for i in itens))

    # Travessia
    def test_travessia_pantano_e_agua(self):
        d = self.mm["charcos_3_travessia.json"]
        mats = list(d["materiais"].values())
        self.assertGreater(mats.count("pantano"), 100)
        self.assertIn("agua", mats)

    def test_travessia_inimigos(self):
        t = self.tipos("charcos_3_travessia.json")
        for esperado in ("crocodilo_jovem", "cobra_venenosa", "cobra_constritora", "rato_gigante", "escorpiao_pedra"):
            self.assertIn(esperado, t)
        self.assertEqual(t.count("zumbi_infectado"), 2)

    # Arredores
    def test_arredores_inimigos(self):
        t = self.tipos("charcos_4a_arredores.json")
        for esperado in ("esqueleto_humano", "esqueleto_animal", "goblin_xama", "zumbi_infectado"):
            self.assertIn(esperado, t)
        self.assertEqual(t.count("goblin_xama"), 1)

    def test_arredores_palicada_e_portao(self):
        d = self.mm["charcos_4a_arredores.json"]
        tipos = {x["type"] for x in d["decorations"]}
        self.assertIn("cerca_reta", tipos)
        self.assertIn("porteira_fechada", tipos)
        self.assertIn("exit", d)

    # Aldeia
    def test_aldeia_ferrao_e_alvo_hostil_a_todos(self):
        f = [m for m in self.aldeia()["monsters"] if m["type"] == "ferrao_charcos_adulto"]
        self.assertEqual(len(f), 1)
        self.assertTrue(f[0]["target"])
        self.assertTrue(f[0]["hostility_override"]["rules"]["all_monsters"])

    def test_bruxos_revidam_so_o_ferrao(self):
        bruxos = [m for m in self.aldeia()["monsters"] if m["type"] in ("goblin_xama", "necromante")]
        self.assertGreaterEqual(len(bruxos), 4)
        for m in bruxos:
            rules = m["hostility_override"]["rules"]
            self.assertEqual(rules["types"], ["ferrao_charcos_adulto"])
            self.assertFalse(rules["all_monsters"])

    def test_cela_do_ferrao_na_mesma_sala_dos_bruxos(self):
        d = self.aldeia()
        salas = {m["room_id"] for m in d["monsters"] if m["type"] in ("ferrao_charcos_adulto", "goblin_xama", "necromante")}
        self.assertEqual(len(salas), 1)
        f = next(m for m in d["monsters"] if m["type"] == "ferrao_charcos_adulto")
        x, y = f["pos"]
        self.assertEqual(d["tiles"][y][x - 3], S.WALL)       # a cela é um quarto murado (5×5)
        self.assertEqual(d["tiles"][y][x + 3], S.WALL)

    def test_alavanca_abre_a_passagem_da_cela(self):
        d = self.aldeia()
        sp = d["secret_passages"][0]
        corrente = next(x for x in d["decorations"] if x["id"] in sp["key_decor_ids"])
        self.assertTrue(corrente.get("key_objective"))
        self.assertEqual(d["tiles"][sp["pos"][1]][sp["pos"][0]], S.WALL)
        self.assertTrue(any(max(abs(fl["pos"][0] - corrente["pos"][0]), abs(fl["pos"][1] - corrente["pos"][1])) <= 3
                            for fl in d["falas"]), "a corrente tem pista")

    def test_sino_do_necromante_chefe_abre_o_cercado(self):
        d = self.aldeia()
        cond = d["door_conditions"]["41,18"]
        sino = next(x for x in d["decorations"] if x["id"] in cond["key_decor_ids"])
        self.assertTrue(sino.get("key_objective"))
        chefe = [m for m in d["monsters"] if m["type"] == "necromante" and
                 max(abs(m["pos"][0] - sino["pos"][0]), abs(m["pos"][1] - sino["pos"][1])) <= 2]
        self.assertTrue(chefe)
        self.assertEqual(d["prisoner"]["room_id"], 2)

    def test_ha_piche_e_feno_perto_da_cova(self):
        d = self.aldeia()
        f = next(m for m in d["monsters"] if m["type"] == "ferrao_charcos_adulto")
        perto = [k for k, v in d["materiais"].items() if v == "piche" and
                 max(abs(int(k.split(",")[0]) - f["pos"][0]), abs(int(k.split(",")[1]) - f["pos"][1])) <= 8]
        self.assertGreaterEqual(len(perto), 9)
        self.assertTrue(any(x["type"] == "monte_feno" for x in d["decorations"]))

    def test_objetivos_e_recompensas(self):
        o = self.aldeia()["objectives"]
        self.assertEqual(o["primary"]["type"], "rescue_prisoner")
        self.assertEqual(o["primary"]["se_falhar"], {"renome": -5, "fato": G.FATO_MORTE})
        sec = o["secondary"][0]
        self.assertEqual((sec["type"], sec["xp"], sec["renome"], sec["fato"]), ("kill_target", 600, 3, G.FATO_FERRAO))
        self.assertEqual(sec["reward"]["gold"], 250)
        self.assertEqual(sec["reward"]["items"], [{"id": G.ITEM_TROFEU}])
        alt = o["alternativo"]
        self.assertEqual((alt["type"], alt["xp"], alt["fato"]), ("kill_target", 150, G.FATO_FERRAO))
        self.assertEqual(alt["reward"]["gold"], 0)

    def test_alcancavel_com_passagem_aberta(self):
        self.assertEqual(G.salas_alcancaveis(self.aldeia(), passagens_abertas=True), {0, 1, 2})

    def test_nd_sem_o_ferrao_dentro_da_faixa(self):
        d = self.aldeia()
        sem = G.nd_por_sala(d)[1] - S.monster_cr(self.defs["ferrao_charcos_adulto"])
        self.assertIn(G.faixa(sem, 16), ("equilibrada", "dificil"))

    def test_nenhuma_sala_mortal_exceto_a_cova(self):
        for arq, d in self.mm.items():
            poder = d["expected_party"]["heroes"] * d["expected_party"]["level"]
            for rid, nd in G.nd_por_sala(d).items():
                if arq == "charcos_4b_aldeia.json" and rid == 1:
                    continue                      # a praça tem o Ferrão
                self.assertNotEqual(G.faixa(nd, poder), "mortal", (arq, rid, nd))

    def test_gerador_e_idempotente(self):
        self.assertEqual(G.masmorras(), G.masmorras())


class CalibracaoTests(unittest.TestCase):
    """6e. A curva de XP do jogo é lenta (nível N→N+1 custa N×1040 por herói, 80 XP por ponto de ND), então a
    campanha NÃO leva sozinha do 2 ao 4: ela rende cerca de um nível. O teste fixa o que importa — que a
    campanha vale a pena, que a fuga rende menos que a vitória e que nenhum herói pula níveis."""

    @classmethod
    def setUpClass(cls):
        cls.mm = G.preparar()["masmorras"]

    def test_xp_por_heroi_dentro_do_esperado(self):
        vitoria, fuga = G.xp_da_campanha(self.mm)
        self.assertGreater(vitoria, 1500)
        self.assertLess(vitoria, 2 * S.XP_POR_NIVEL + 3 * S.XP_POR_NIVEL, "não pula do nível 2 ao 4 numa só campanha")
        self.assertLess(fuga, vitoria)

    def test_fugir_rende_o_xp_do_resgate_mas_nao_o_do_ferrao(self):
        d = self.mm["charcos_4b_aldeia.json"]
        self.assertEqual(d["objectives"]["primary"]["xp"], 150)
        self.assertEqual(d["objectives"]["secondary"][0]["xp"], 600)

    def test_relatorio_mostra_o_xp(self):
        art = {"masmorras": self.mm}
        self.assertIn("XP por herói", G.relatorio(art))

    def test_niveis_esperados_crescem(self):
        niveis = [self.mm[a]["expected_party"]["level"] for a in G.ARQUIVOS]
        self.assertEqual(niveis, sorted(niveis))
        self.assertEqual((niveis[0], niveis[-1]), (2, 4))


if __name__ == "__main__":
    unittest.main()
