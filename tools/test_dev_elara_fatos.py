"""Ferramenta dev_elara_fatos: cada ponto leva ao estado certo (checado pelas regras reais de visibilidade).
Roda da raiz: python -X utf8 tools/test_dev_elara_fatos.py"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import dev_elara_fatos as D
import gerar_campanha_elara as P1
import gerar_elara_riacho as RI
import gerar_elara_gilo as GI
import gerar_elara_graciero as GR
import gerar_elara_montanha as MO
import elara_graciero_mapas as GRM

for _g in (GI, GR, MO):
    _g.garantir_registros(False) if _g is not GI else GI.garantir_ficha(False)
DESTINOS = {}
for _g in (RI, GI, GR, MO):
    DESTINOS.update(_g.destinos())
DESTINOS.update(P1.destinos() if hasattr(P1, "destinos") else {})


def visiveis(ate, ramo="a", bardo="gentil", lento=False):
    fatos, prog, local = D.estado_ate(ate, ramo, bardo, lento)
    r = S.GameRoom("DEVE")
    r.players["p0"] = S.make_player("p0", "H0", "warrior", 0)
    r.fatos = set(fatos); r.world_adventure_progress = dict(prog)
    S.WORLD_ADVENTURES.update(DESTINOS)
    try:
        return {k for k in DESTINOS if k.startswith("elara_") and r._aventura_visivel(S.WORLD_ADVENTURES[k])}
    finally:
        for k in DESTINOS:
            S.WORLD_ADVENTURES.pop(k, None)


class PontosTests(unittest.TestCase):
    def test_cada_ponto_acumula_os_anteriores(self):
        antes = set()
        for ate in D.PONTOS:
            fatos, _p, _l = D.estado_ate(ate, "a", "gentil")
            self.assertTrue(antes <= fatos, ate)
            antes = fatos

    def test_ramo_a_destinos_por_ponto(self):
        self.assertEqual(visiveis("escolha", "a"), {"elara_riacho_casa"})
        self.assertEqual(visiveis("etapa1", "a"), set(), "casa feita; celeiro so depois da decisao")
        self.assertEqual(visiveis("rumo", "a"), {"elara_graciero_beco"})
        self.assertEqual(visiveis("beco", "a"), {"elara_graciero_cais"})
        self.assertEqual(visiveis("cais", "a"), {"elara_graciero_praca_viva"})
        self.assertEqual(visiveis("cais", "a", lento=True), {"elara_graciero_praca_morta"})

    def test_ramo_b_destinos_por_ponto(self):
        self.assertEqual(visiveis("escolha", "b"), {"elara_adhadal"})
        self.assertEqual(visiveis("etapa1", "b"), {"elara_corvin"})
        self.assertEqual(visiveis("etapa2", "b"), set())
        self.assertEqual(visiveis("rumo", "b"), {"elara_graciero_beco"})

    def test_praca_leva_ao_leonel_e_a_rota_do_olho_so_no_ramo_a(self):
        a = visiveis("praca", "a", "gentil")
        self.assertEqual(a, {"elara_leonel_casa", "elara_montanha"})
        self.assertEqual(visiveis("praca", "a", "morto"), {"elara_leonel_casa_alerta", "elara_montanha"})
        self.assertEqual(visiveis("praca", "b"), {"elara_leonel_casa"}, "ramo B nao ve a rota")
        self.assertEqual(visiveis("praca", "a", "gentil", lento=True), {"elara_leonel_casa"},
                         "lento: sem a dica da Praca viva nao ha rota")

    def test_bardos_gravam_o_tratamento(self):
        f_gentil = D.estado_ate("etapa2", "a", "gentil")[0]
        f_mal = D.estado_ate("etapa2", "a", "maltratado")[0]
        self.assertTrue({RI.F_POUPADO, RI.F_GENTIL} <= f_gentil and RI.F_MALTRATADO not in f_gentil)
        self.assertTrue({RI.F_POUPADO, RI.F_MALTRATADO} <= f_mal)
        self.assertIn(RI.F_LEONEL_CAUTELOSO, D.estado_ate("etapa2", "a", "morto")[0])

    def test_entradas_invalidas_sao_recusadas(self):
        for args in (("nada",), ("rumo", "x"), ("rumo", "a", "outro")):
            with self.assertRaises(ValueError):
                D.estado_ate(*args)


class AplicarTests(unittest.TestCase):
    def jogo(self):
        return {"id": "sg_abc123", "fatos": ["outra_campanha", "elara_ramo_b", "elara_gilo_fugiu"],
                "world_adventure_progress": {"charcos_mare": 5, "elara_adhadal": 2},
                "scene_conversations_done": ["graciero:taverna:barman:elara_gilo_pertences", "x:y:z:ficou"],
                "relogios": {"elara_p1": 9, "outro": 3}, "story_beats_done": ["fim:elara_x", "fim:charcos"],
                "world_location": "vila_corvin", "dungeon_snapshot": {"onde": "masmorra"}}

    def test_substitui_so_o_estado_de_elara(self):
        sg = self.jogo()
        D.aplicar_ao_jogo(sg, "rumo", "a", "gentil")
        self.assertIn("outra_campanha", sg["fatos"])
        self.assertNotIn("elara_gilo_fugiu", sg["fatos"]); self.assertNotIn("elara_ramo_b", sg["fatos"])
        self.assertIn("elara_rumo_graciero", sg["fatos"])
        self.assertEqual(sg["world_adventure_progress"]["charcos_mare"], 5)
        self.assertNotIn("elara_adhadal", sg["world_adventure_progress"])
        self.assertEqual(sg["scene_conversations_done"], ["x:y:z:ficou"])
        self.assertEqual(sg["relogios"], {"outro": 3})
        self.assertEqual(sg["story_beats_done"], ["fim:charcos"])
        self.assertEqual(sg["world_location"], "graciero")
        self.assertIn("dungeon_snapshot", sg, "a foto so sai com --limpar-foto")

    def test_inicio_zera_e_limpar_foto(self):
        sg = self.jogo()
        D.aplicar_ao_jogo(sg, "inicio", limpar_foto=True)
        self.assertEqual([f for f in sg["fatos"] if f.startswith("elara_")], [])
        self.assertNotIn("dungeon_snapshot", sg)
        self.assertEqual(sg["world_location"], "vila_corvin", "inicio nao mexe no local")


if __name__ == "__main__":
    unittest.main()
