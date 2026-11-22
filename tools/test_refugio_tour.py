"""Elara: depois da fazenda, o Refúgio é apresentado pelo tour guiado do Mestre de
Armas (cliente), e não por um ponto/cena do Mestre no mapa de Alva e Luz.
Roda da raiz: python -X utf8 tools/test_refugio_tour.py
"""
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def sala(fatos=()):
    r = S.GameRoom("TOUR")
    r.world_location = "alva_e_luz"
    r.phase = "city"
    r.fatos = set(fatos)
    return r


class ServidorTests(unittest.TestCase):
    def test_sem_ponto_nem_cena_do_mestre(self):
        depois = sala({"elara_fazenda_vencida"})._city_points_payload()["alva_e_luz"]
        self.assertNotIn("mestre_armas_alva", depois)
        self.assertNotIn("mestre_armas_alva", S.CITY_SCENES.get("alva_e_luz", {}))

    def test_refugio_oculto_antes_da_fazenda(self):
        self.assertNotIn("ponto_1", sala()._city_points_payload()["alva_e_luz"])

    def test_tour_sai_ao_desbloquear(self):
        r = sala()
        self.assertIsNone(r._city_state_payload()["tutorial"]["tour_refugio_id"])
        r.fatos.add("elara_fazenda_vencida")
        primeiro = r._city_state_payload()["tutorial"]["tour_refugio_id"]
        self.assertTrue(primeiro, "o city_state que desbloqueia já leva o tour")
        self.assertEqual(r._city_state_payload()["tutorial"]["tour_refugio_id"], primeiro,
                         "o id não muda nos estados seguintes")

    def test_save_antigo_ja_desbloqueado_tambem_recebe(self):
        # Fazenda liberada antes do tour existir: o tour sai mesmo assim; o
        # cliente o mostra uma vez por conta (quem já viu ou pulou não vê).
        r = sala({"elara_fazenda_vencida"})
        r.refugio_state["unlocked"] = True
        self.assertEqual(r._city_state_payload()["tutorial"]["tour_refugio_id"], "refugio")
        self.assertEqual(sala({"elara_fazenda_vencida"})._city_state_payload()["tutorial"]["tour_refugio_id"],
                         "refugio", "mesmo id de quem libera agora")

    def test_abrir_refugio_fora_de_alva_nao_libera_a_fazenda(self):
        # Antes, sem Refúgio na cidade, o requisito virava {} e liberava tudo.
        import asyncio
        r = sala()
        r.world_location = "vila_corvin"
        r.players["p"] = S.make_player("p", "A", "warrior", 0)
        async def nada(*a, **k):
            pass
        r.send_to = nada
        r.broadcast = nada
        asyncio.run(r.handle_open_refugio("p"))
        self.assertFalse(r.refugio_state.get("unlocked"))
        r.world_location = "alva_e_luz"
        self.assertIsNone(r._city_state_payload()["tutorial"]["tour_refugio_id"])


class ClienteTests(unittest.TestCase):
    def setUp(self):
        self.js = open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()

    def test_passos_tem_texto_nos_dois_idiomas(self):
        passos = ("abertura", "mapa", "externa", "externa_sem_comum", "comum", "quarto")
        for p in passos:
            for campo in ("titulo", "texto"):
                k = f"ui.tutorial.refugio.{p}.{campo}"
                self.assertTrue((S.LANG_STRINGS.get(k) or {}).get("en"), k)

    def test_botoes_da_cena_tem_alvo_do_tour(self):
        alvos = re.search(r"_REFUGIO_TOUR_ALVO = \{([^}]*)\}", self.js).group(1)
        for acao in re.findall(r"'(\w+)'", alvos):
            if acao in ("externa", "comum", "quarto"):
                continue
            self.assertIn(f"'{acao}']", self.js, acao)

    def test_cartao_sai_fora_de_alva_e_fora_da_cidade(self):
        corpo = self.js.split("function _refugioTourRender(){", 1)[1].split("\nfunction ", 1)[0]
        trecho = corpo.split("if(!pontoId)", 1)[1][:300]
        self.assertIn("refugio-tour-card')?.remove()", trecho)
        show = self.js.split("function showScreen(id){", 1)[1][:1200]
        self.assertIn("refugio-tour-card", show)

    def test_controle_alcanca_o_cartao_no_mapa(self):
        self.assertIn("#refugio-tour-card:not(.refugio-tour-topo)", self.js)

    def test_tour_ligado_ao_city_state(self):
        self.assertIn("_refugioTourIniciarOuRetomar(msg.tutorial?.tour_refugio_id", self.js)


if __name__ == "__main__":
    unittest.main()
