"""Fluxo da Parte 1 pelo motor real: pedido, destino, vitória, pressão do Templo e escolha.
Roda da raiz: python -X utf8 tools/test_elara_fluxo.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_campanha_elara as G


def sala(classes=("warrior",), fatos=()):
    r = S.GameRoom("ELARA")
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", c, i)
    r.host_pid = "p0"; r.phase = "city"; r.world_location = "alva_e_luz"
    r.fatos = set(fatos)
    r.enviados = []

    async def send_to(pid, msg): r.enviados.append(msg)

    async def broadcast(msg, skip=None, personalize=None): pass

    async def push(): pass
    r.send_to = send_to; r.broadcast = broadcast; r.push_state_or_city = push
    r._checkpoint_savegame = lambda: None
    return r


def conversas(r):
    cena = r._city_state_payload()["scenes"].get(G.CENA_ID) or {}
    return [c["id"] for s in cena.get("slots", []) for c in s.get("conversations", [])]


def falar(r, cid):
    asyncio.run(r.handle_scene_npc("p0", G.CENA_ID, G.NPC_ID, cid))


class FluxoTests(unittest.TestCase):
    def test_inicio_so_o_pedido(self):
        self.assertEqual(conversas(sala()), ["elara_pedido"])

    def test_aceitar_o_pedido_concede_o_fato_e_revela_o_destino(self):
        r = sala()
        adv = S.WORLD_ADVENTURES[G.AVENTURA]
        self.assertFalse(r._aventura_visivel(adv))
        falar(r, "elara_pedido")
        self.assertIn(G.F_PEDIU, r.fatos)
        self.assertTrue(r._aventura_visivel(adv))
        self.assertNotIn("elara_pedido", conversas(r), "uso único")

    def test_falas_extras_so_com_pedro_ou_henrique(self):
        r = sala(("warrior",), {G.F_PEDIU})
        self.assertNotIn("elara_pedro_irma", conversas(r))
        self.assertNotIn("elara_henrique_pilheria", conversas(r))
        r2 = sala(("warrior", "mage", "bard"), {G.F_PEDIU})
        self.assertIn("elara_pedro_irma", conversas(r2))
        self.assertIn("elara_henrique_pilheria", conversas(r2))

    def test_pressao_do_templo_rapido_e_lento(self):
        r = sala(fatos={G.F_FAZENDA})
        self.assertEqual([c for c in conversas(r) if c.startswith("elara_pos")], ["elara_pos_fazenda_rapido"])
        r2 = sala(fatos={G.F_FAZENDA, G.F_LENTO})
        r2.world_adventure_progress = {G.AVENTURA: 2}
        self.assertEqual([c for c in conversas(r2) if c.startswith("elara_pos")], ["elara_pos_fazenda_lento"])
        r3 = sala(fatos={G.F_LENTO})       # passou do limite ainda na fazenda: o Templo não fala antes do fim
        self.assertEqual([c for c in conversas(r3) if c.startswith("elara_pos")], [])

    def test_escolha_so_depois_da_pressao_e_nunca_bloqueia(self):
        for fatos in ({G.F_FAZENDA}, {G.F_FAZENDA, G.F_LENTO}):
            r = sala(fatos=fatos)
            r.world_adventure_progress = {G.AVENTURA: 2}
            self.assertNotIn("elara_escolher_mocas", conversas(r))
            falar(r, next(c for c in conversas(r) if c.startswith("elara_pos")))
            self.assertIn("elara_escolher_mocas", conversas(r))
            self.assertIn("elara_escolher_gilo", conversas(r), "as duas opções existem, rápido ou lento")

    def test_escolher_um_ramo_some_o_outro(self):
        r = sala(fatos={G.F_FAZENDA, G.F_PRESSIONOU})
        falar(r, "elara_escolher_gilo")
        self.assertIn(G.F_RAMO_B, r.fatos)
        self.assertNotIn("elara_escolher_mocas", conversas(r))
        self.assertNotIn("elara_escolher_gilo", conversas(r))


if __name__ == "__main__":
    unittest.main()
