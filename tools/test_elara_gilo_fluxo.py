"""Fluxo do Ramo B pelo motor real: conversas, destinos, objetivos dos mapas e a fuga do Gilo.
Roda da raiz: python -X utf8 tools/test_elara_gilo_fluxo.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_gilo as R
import elara_gilo_ficha as G
import elara_gilo_mapas as M

R.garantir_ficha(gravar=False)
CENA = "taverna"


def sala(fatos=(), cidade="vila_corvin"):
    r = S.GameRoom("CORVIN")
    r.players["p0"] = S.make_player("p0", "H0", "warrior", 0)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = cidade
    r.fatos = set(fatos)
    r.enviados = []

    async def send_to(pid, msg): r.enviados.append(msg)

    async def nada(*a, **k): pass
    r.send_to = send_to; r.broadcast = nada; r.push_state_or_city = nada; r.push_state = nada
    r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    return r


def conversas(r):
    cena = r._city_state_payload()["scenes"].get(CENA) or {}
    return {c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])}


def masmorra(arq, fatos=()):
    r = sala(fatos)
    r.load_authored_dungeon(S.carregar_dungeon(arq))
    r.phase = "playing"
    return r


class FluxoTests(unittest.TestCase):
    def test_sem_o_ramo_b_nada_aparece(self):
        vistos = conversas(sala())
        self.assertFalse(vistos & {"elara_corvin_barman", "elara_corvin_garconete", "elara_corvin_bardo",
                                   "elara_corvin_sombrio"})

    def test_com_o_ramo_b_aparecem_e_a_chegada_grava_o_fato(self):
        r = sala({R.F_RAMO_B})
        self.assertTrue({"elara_corvin_barman", "elara_corvin_sombrio"} <= conversas(r))
        slot = "barman"
        asyncio.run(r.handle_scene_npc("p0", CENA, slot, "elara_corvin_barman"))
        self.assertIn(R.F_CHEGADA, r.fatos)

    def test_destinos_na_ordem_certa(self):
        S.WORLD_ADVENTURES.update(R.destinos())
        try:
            ad, co = S.WORLD_ADVENTURES["elara_adhadal"], S.WORLD_ADVENTURES["elara_corvin"]
            r = sala()
            self.assertFalse(r._aventura_visivel(ad)); self.assertFalse(r._aventura_visivel(co))
            r.fatos.add(R.F_RAMO_B)
            self.assertTrue(r._aventura_visivel(ad)); self.assertFalse(r._aventura_visivel(co))
            r.world_adventure_progress["elara_adhadal"] = 2
            self.assertFalse(r._aventura_visivel(ad), "concluída, some do mapa")
            self.assertTrue(r._aventura_visivel(co))
        finally:
            for k in R.destinos():
                S.WORLD_ADVENTURES.pop(k, None)

    def test_corvin_acessivel_sem_conversar_com_ninguem(self):
        S.WORLD_ADVENTURES.update(R.destinos())
        try:
            r = sala({R.F_RAMO_B})
            r.world_adventure_progress["elara_adhadal"] = 2
            self.assertNotIn(R.F_CHEGADA, r.fatos)
            self.assertTrue(r._aventura_visivel(S.WORLD_ADVENTURES["elara_corvin"]))
        finally:
            for k in R.destinos():
                S.WORLD_ADVENTURES.pop(k, None)


class ObjetivosTests(unittest.IsolatedAsyncioTestCase):
    async def test_adhadal_2_chegar_na_saida_grava_o_fato(self):
        r = masmorra("elara_adhadal_2.json")
        r.players["p0"]["pos"] = list(r.exit_pos); r.players["p0"]["alive"] = True
        await r._check_objectives()
        self.assertIn(M.F_ADHADAL, r.fatos)

    async def test_cacada_bau_chave_grava_o_fato(self):
        r = masmorra("elara_corvin_cacada.json")
        r.key_chest_opened = True
        await r._check_objectives()
        self.assertIn(M.F_CACADA, r.fatos)


class GiloTests(unittest.IsolatedAsyncioTestCase):
    async def _gilo(self):
        r = masmorra("elara_corvin_gilo.json")
        gilo = next(m for m in r.monsters.values() if m["type"] == G.TIPO_GILO)
        return r, gilo

    async def _confere(self, r, gilo, baus0):
        self.assertNotIn(gilo["id"], r.corpses)
        self.assertEqual(set(r.chests), baus0, "sem baú de loot novo")
        self.assertTrue(gilo.get("fugiu"))
        self.assertIn(M.F_GILO_FUGIU, r.fatos)

    async def test_arma_foge(self):
        r, g = await self._gilo(); baus0 = set(r.chests)
        g["hp"] = 0
        await r._monster_dies(g, "p0")
        await self._confere(r, g, baus0)

    async def test_fogo_foge(self):
        r, g = await self._gilo(); baus0 = set(r.chests)
        await r._aplicar_dano_alvo(g, g["hp"] + 5, "fire", killer_pid="p0")
        await self._confere(r, g, baus0)

    async def test_veneno_foge(self):
        r, g = await self._gilo(); baus0 = set(r.chests)
        await r._dano_em_alvo(g, g["hp"] + 5, "poison", killer_pid="p0")
        await self._confere(r, g, baus0)

    async def test_objetivo_do_confronto_grava_a_pista(self):
        r, g = await self._gilo()
        g["hp"] = 0
        await r._monster_dies(g, "p0")
        await r._check_objectives()
        self.assertIn(M.F_PISTA, r.fatos)


if __name__ == "__main__":
    unittest.main()
