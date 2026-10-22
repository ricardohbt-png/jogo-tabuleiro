"""Fluxo de Graciero pelo motor real: destinos, relógio, conversas, Olho, variantes do esconderijo e o final.
Roda da raiz: python -X utf8 tools/test_elara_graciero_fluxo.py"""
import asyncio
import itertools
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_graciero as R
import elara_graciero_fichas as F
import elara_graciero_mapas as M

R.garantir_registros(gravar=False)
CENA = "taverna"


def sala(fatos=(), classes=("warrior",), cidade="graciero"):
    r = S.GameRoom("GRACIERO")
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", c, i)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = cidade
    r.fatos = set(fatos)

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state_or_city = nada; r.push_state = nada; r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    return r


def conversas(r):
    cena = r._city_state_payload()["scenes"].get(CENA) or {}
    return {c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])}


def falar(r, cid):
    slot = next(s for s, convs in R.conversas().items() if any(c["id"] == cid for c in convs))
    asyncio.run(r.handle_scene_npc("p0", CENA, slot, cid))


def masmorra(arq, fatos=()):
    r = sala(fatos)
    r.load_authored_dungeon(S.carregar_dungeon(arq))
    r.phase = "playing"
    return r


class DestinosTests(unittest.TestCase):
    def setUp(self):
        S.WORLD_ADVENTURES.update(R.destinos())

    def tearDown(self):
        for k in R.destinos():
            S.WORLD_ADVENTURES.pop(k, None)

    def vis(self, r):
        return {k for k in R.destinos() if r._aventura_visivel(S.WORLD_ADVENTURES[k])}

    def test_sem_o_rumo_nada_aparece_e_com_ele_so_o_beco(self):
        self.assertEqual(self.vis(sala()), set())
        r = sala({R.F_RUMO})
        self.assertEqual(self.vis(r), {"elara_graciero_beco"})
        r.world_adventure_progress["elara_graciero_beco"] = 1
        self.assertEqual(self.vis(r), {"elara_graciero_cais"})

    def test_a_praca_depende_do_relogio_e_nunca_as_duas(self):
        r = sala({R.F_RUMO}); r.world_adventure_progress.update({"elara_graciero_beco": 1, "elara_graciero_cais": 1})
        self.assertEqual(self.vis(r), {"elara_graciero_praca_viva"})
        r.fatos.add(R.F_LENTO)
        self.assertEqual(self.vis(r), {"elara_graciero_praca_morta"})

    def test_esconderijo_normal_ou_alerta_nunca_os_dois(self):
        r = sala({R.F_GILO_MORREU})
        self.assertEqual(self.vis(r), {"elara_leonel_casa"})
        r.fatos.add(R.F_CAUTELOSO)
        self.assertEqual(self.vis(r), {"elara_leonel_casa_alerta"})
        self.assertEqual(self.vis(sala({R.F_CAUTELOSO})), set(), "sem a morte do Gilo, nenhum")


class ConversasTests(unittest.TestCase):
    def test_bardo_so_ajuda_ou_trai_se_foi_poupado(self):
        vistos = conversas(sala({R.F_GENTIL, R.F_MALTRATADO}))
        self.assertFalse(vistos & {"elara_graciero_bardo_ajuda", "elara_graciero_bardo_traicao"})
        gentil = sala({R.F_POUPADO, R.F_GENTIL})
        self.assertIn("elara_graciero_bardo_ajuda", conversas(gentil))
        self.assertNotIn("elara_graciero_bardo_traicao", conversas(gentil))
        falar(gentil, "elara_graciero_bardo_ajuda")
        self.assertTrue({R.F_AJUDOU, R.F_DICA_MONTANHA} <= gentil.fatos)
        mal = sala({R.F_POUPADO, R.F_MALTRATADO})
        self.assertIn("elara_graciero_bardo_traicao", conversas(mal))
        self.assertNotIn("elara_graciero_bardo_ajuda", conversas(mal))
        falar(mal, "elara_graciero_bardo_traicao")
        self.assertTrue({R.F_TRAIU, R.F_CAUTELOSO} <= mal.fatos)
        misto = sala({R.F_POUPADO, R.F_GENTIL, R.F_MALTRATADO})
        self.assertEqual(conversas(misto) & {"elara_graciero_bardo_ajuda", "elara_graciero_bardo_traicao"},
                         {"elara_graciero_bardo_traicao"}, "maltratado vence")

    def test_so_o_ramo_b_recebe_o_olho(self):
        b = sala({R.F_RAMO_B, R.F_GILO_MORREU})
        self.assertIn("elara_gilo_pertences", conversas(b))
        falar(b, "elara_gilo_pertences")
        self.assertTrue(b._grupo_tem_item(F.ID_OLHO)); self.assertIn(R.F_OLHO, b.fatos)
        self.assertNotIn("elara_gilo_pertences", conversas(b), "uma vez só")
        self.assertNotIn("elara_gilo_pertences", conversas(sala({R.F_RAMO_A, R.F_GILO_MORREU})))
        self.assertNotIn("elara_gilo_pertences", conversas(sala({R.F_RAMO_B})), "antes da morte, nada")

    def test_herois_so_falam_se_estiverem_no_grupo(self):
        self.assertNotIn("elara_graciero_pedro", conversas(sala({R.F_RUMO})))
        self.assertIn("elara_graciero_pedro", conversas(sala({R.F_RUMO}, ("mage",))))
        self.assertIn("elara_graciero_henrique", conversas(sala({R.F_RUMO}, ("bard",))))
        self.assertNotIn("elara_graciero_henrique", conversas(sala({R.F_RUMO}, ("mage",))))


class ObjetivosTests(unittest.IsolatedAsyncioTestCase):
    async def _cumpre_praca(self, arq):
        r = masmorra(arq)
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        return r

    async def test_praca_viva_grava_os_tres_fatos(self):
        r = await self._cumpre_praca("elara_graciero_praca_viva.json")
        self.assertTrue({R.F_GILO_MORREU, M.F_VIU_MORRER, R.F_DICA_MONTANHA} <= r.fatos)

    async def test_praca_morta_so_grava_a_morte(self):
        r = await self._cumpre_praca("elara_graciero_praca_morta.json")
        self.assertIn(R.F_GILO_MORREU, r.fatos)
        self.assertFalse(r.fatos & {M.F_VIU_MORRER, R.F_DICA_MONTANHA})

    async def test_frentes_gravam_o_fato_pelo_bau(self):
        for arq, fato in (("elara_graciero_beco.json", M.F_BECO), ("elara_graciero_cais.json", M.F_CAIS)):
            r = masmorra(arq); r.key_chest_opened = True
            await r._check_objectives()
            self.assertIn(fato, r.fatos, arq)

    async def test_porao_grava_leonel_e_a_cela_da_elara(self):
        r = masmorra("elara_leonel_2.json")
        r.key_chest_opened = True
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        self.assertTrue({M.F_LEONEL, M.F_ELARA} <= r.fatos)

    async def test_relogio_passa_e_grava_o_lento(self):
        r = masmorra("elara_graciero_beco.json")
        for _ in range(31):
            await r._relogio_tick()
        self.assertIn(R.F_LENTO, r.fatos)


class FinalTests(unittest.TestCase):
    """Toda combinação de ramo x Olho x bardo x Pedro/Henrique produz um final coerente."""

    def texto(self, fatos, classes, olho):
        r = sala(fatos, classes)
        if olho:
            r.players["p0"]["bag"].append(dict(S._DUNGEON_ITEM_CATALOG[F.ID_OLHO]))
        b = S._story_beat("fim:x", [R.outro_rota()], r._requisito_do_slide)
        return " || ".join(sl.get("text", "") for sl in b["slides"])

    def test_matriz(self):
        ramos = [{R.F_RAMO_A, R.F_MOCAS}, {R.F_RAMO_B}]
        bardos = [set(), {R.F_AJUDOU}, {R.F_TRAIU}]
        elencos = [("warrior",), ("mage",), ("bard",), ("mage", "bard")]
        n = 0
        for ramo, bardo, elenco, olho in itertools.product(ramos, bardos, elencos, (False, True)):
            t = self.texto(ramo | bardo, elenco, olho)
            n += 1
            self.assertIn("Elara", t)
            self.assertIn("muito maior", t, "o fecho de mistério sempre sai")
            self.assertEqual("volta ao Templo" in t, olho)
            self.assertEqual("não está aqui" in t, not olho)
            self.assertEqual("moças de Riacho" in t, R.F_RAMO_A in ramo)
            self.assertEqual("outras servas" in t, R.F_RAMO_B in ramo)
            self.assertEqual("abraça a irmã" in t, "mage" in elenco)
            self.assertEqual("reverência" in t, "bard" in elenco)
            self.assertEqual("de longe, ergue o chapéu" in t, R.F_AJUDOU in bardo)
            self.assertEqual("para outro lado" in t, R.F_TRAIU in bardo)
        self.assertEqual(n, 48)


if __name__ == "__main__":
    unittest.main()
