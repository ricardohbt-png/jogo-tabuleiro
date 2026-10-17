"""Slides de história condicionais: o final do Covil da Garra Negra só diz que "talvez ninguém
tenha encontrado" o segredo se o grupo NÃO tem o Anel da Garra Negra, e depois do final o
grupo volta à cidade com o mapa aberto (não é fim de jogo).
Roda da raiz: python -X utf8 tools/test_final_condicional.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))
import server as S  # noqa: E402

FRASE = "talvez ninguém tenha encontrado"
REQ = {"item_id": "anel_garra_negra"}


def sala(com_anel):
    r = S.GameRoom("FINAL")
    p = S.make_player("p1", "Ana", "rogue", 0)
    if com_anel:
        p["bag"] = [dict(S._DUNGEON_ITEM_CATALOG["anel_garra_negra"])]
    r.players["p1"] = p
    r.player_order = ["p1"]
    return r


def textos(beat):
    return [s["text"] for s in (beat or {}).get("slides", [])]


class BeatTests(unittest.TestCase):
    PARTES = [{"slides": [
        {"text": "sempre"},
        {"text": "só sem anel", "requisito": REQ, "negar": True},
        {"text": "só com anel", "requisito": REQ},
        {"text": "sempre 2"}]}]

    def test_filtra_pela_condicao_e_nao_vaza_a_condicao_ao_cliente(self):
        com, sem = sala(True), sala(False)
        self.assertEqual(textos(S._story_beat("k", self.PARTES, com._requisito_do_slide)),
                         ["sempre", "só com anel", "sempre 2"])
        beat = S._story_beat("k", self.PARTES, sem._requisito_do_slide)
        self.assertEqual(textos(beat), ["sempre", "só sem anel", "sempre 2"])
        for sl in beat["slides"]:
            self.assertEqual(set(sl), {"text", "fit"}, "requisito/negar não viajam ao cliente")

    def test_sem_avaliador_descarta_o_condicional(self):
        self.assertEqual(textos(S._story_beat("k", self.PARTES)), ["sempre", "sempre 2"])

    def test_campo_sem_condicao_continua_igual(self):
        self.assertEqual(textos(S._story_beat("k", ["texto solto", {"slides": [{"text": "b"}]}])),
                         ["texto solto", "b"])

    def test_editor_grava_e_valida_a_condicao(self):
        campo = S._clean_story_field(self.PARTES[0])
        self.assertEqual(campo["slides"][1]["requisito"]["item_id"], "anel_garra_negra")
        self.assertTrue(campo["slides"][1]["negar"])
        self.assertNotIn("requisito", campo["slides"][0])
        self.assertTrue(S._validar_story(campo, "x")[0])
        self.assertFalse(S._validar_story({"slides": [{"text": "a", "requisito": "item"}]}, "x")[0])


class CovilTests(unittest.IsolatedAsyncioTestCase):
    async def _encerrar(self, com_anel):
        r = sala(com_anel)
        antes = {"story": "nao-chamou"}
        r.phase = "playing"; r.mission_complete_pending = True; r._objetivo_concluido = True
        r._route_exits_complete = lambda: True
        r.world_adventure_id = "sombras_covil"; r.world_adventure_index = 1
        r.world_adventure_revisit = False
        r.world_adventure_progress = {"sombras_covil": 1}

        async def noop(*a, **k): pass

        async def voltar(story=None, **k): antes["story"] = story
        r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
        r._voltar_para_cidade = voltar
        await r.handle_encerrar_missao("p1")
        return r, antes["story"]

    async def test_final_sem_o_anel_menciona_o_segredo(self):
        r, story = await self._encerrar(False)
        t = textos(story)
        self.assertTrue(any(FRASE in x for x in t), t)
        self.assertEqual(t[-1], "Outras estradas esperam por vocês no mapa.")

    async def test_final_com_o_anel_nao_menciona_o_segredo(self):
        r, story = await self._encerrar(True)
        t = textos(story)
        self.assertFalse(any(FRASE in x for x in t), t)
        self.assertEqual(t[-1], "Outras estradas esperam por vocês no mapa.")
        self.assertGreaterEqual(len(t), 4, "o resto do final continua inteiro")

    async def test_o_mapa_continua_depois_do_final(self):
        r, story = await self._encerrar(False)
        self.assertIsNone(r.world_adventure_id, "a rota fecha")
        self.assertEqual(r.world_adventure_progress["sombras_covil"], 2)
        self.assertNotEqual(r.phase, "ended", "não é fim de jogo: volta à cidade com o mapa")


class DadosTests(unittest.TestCase):
    def test_gerador_e_arquivo_concordam(self):
        import gerar_campanha_sombras as G
        gerado = G.destinos()["sombras_covil"]["outro_rota"]
        arq = next(a for a in json.loads((RAIZ / "world_adventures.json").read_text(encoding="utf-8")).values()
                   if a.get("id") == "sombras_covil")["outro_rota"]
        self.assertEqual(gerado, arq)

    def test_gerador_do_anel_nao_desfaz_preco_e_descricao(self):
        import gerar_campanha_sombras as G
        bruto = G.anel_bruto()
        ok, item = S._validate_custom_accessory(bruto)
        self.assertTrue(ok)
        atual = S._DUNGEON_ITEM_CATALOG["anel_garra_negra"]
        self.assertEqual((item["price"], item["descricao"]), (atual["price"], atual["descricao"]))


if __name__ == "__main__":
    unittest.main()
