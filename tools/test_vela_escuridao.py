"""Vela da Escuridão: oculta pelo turno de uso e por mais 1 rodada.
Rode da raiz: python -X utf8 tools/test_vela_escuridao.py"""
import asyncio
import os
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def sala(classe="warrior"):
    r = S.GameRoom("VELA")
    erros = []

    async def noop(*a, **k):
        return None

    async def send(pid, msg, *a, **k):
        erros.append(msg)

    r.gm_say = r.push_state = r.broadcast = noop
    r.send_to = send
    r._is_turn = lambda pid: True
    p = S.make_player("p1", "Aluna", classe, 0)
    p["bag"] = [deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == "vela_escuridao"))]
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "playing"
    return r, p, erros


class VelaEscuridaoTests(unittest.TestCase):
    def test_item_dura_duas_rodadas(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "vela_escuridao")
        self.assertEqual((item["price"], item["effect"], item["value"]), (50, "veil_shadow", 2))

    def test_usar_oculta_por_duas_rodadas(self):
        r, p, erros = sala()
        asyncio.run(r.handle_use_item("p1", "vela_escuridao"))
        self.assertEqual([e for e in erros if e.get("type") == "error"], [])
        self.assertTrue(p["oculto_vela"])
        self.assertEqual(p["oculto_vela_rodadas"], 2)
        self.assertEqual(p["bag"], [])

    def test_encerrar_turno_consome_uma_rodada_por_vez(self):
        r, p, _ = sala()
        p["oculto_vela"], p["oculto_vela_rodadas"] = True, 2
        asyncio.run(r.handle_end_turn("p1"))
        self.assertTrue(p.get("oculto_vela"))
        self.assertEqual(p.get("oculto_vela_rodadas"), 1)
        asyncio.run(r.handle_end_turn("p1"))
        self.assertFalse(p.get("oculto_vela"))
        self.assertNotIn("oculto_vela_rodadas", p)

    def test_vela_antiga_sem_contador_acaba_no_primeiro_fim_de_turno(self):
        r, p, _ = sala()
        p["oculto_vela"] = True
        asyncio.run(r.handle_end_turn("p1"))
        self.assertFalse(p.get("oculto_vela"))


if __name__ == "__main__":
    unittest.main()
