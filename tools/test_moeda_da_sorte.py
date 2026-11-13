"""Moeda da Sorte: ativa por ação bônus e rerrola a primeira falha (ataque ou resistência).
Roda da raiz: python -X utf8 tools/test_moeda_da_sorte.py
"""
import asyncio
import os
import sys
import unittest
from copy import deepcopy
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def sala():
    r = S.GameRoom("MOEDA")
    erros = []

    async def noop(*a, **k):
        return None

    async def send(pid, msg, *a, **k):
        erros.append(msg)

    r.gm_say = r.push_state = r.broadcast = noop
    r.send_to = send
    r._is_turn = lambda pid: True
    p = S.make_player("p1", "Aluna", "warrior", 0)
    p["bag"] = [deepcopy(next(i for i in S.SHOP_MERCHANT if i["id"] == "moeda_da_sorte"))]
    r.players["p1"] = p
    return r, p, erros


class MoedaDaSorteTests(unittest.TestCase):
    def test_item_da_loja(self):
        item = next(i for i in S.SHOP_MERCHANT if i["id"] == "moeda_da_sorte")
        self.assertEqual((item["price"], item["effect"]), (120, "luck_coin"))
        self.assertIn("luck_coin", S.GameRoom.BONUS_ACTION_EFFECTS)

    def test_ativar_consome_item_e_liga_estado(self):
        r, p, erros = sala()
        asyncio.run(r.handle_use_item("p1", "moeda_da_sorte"))
        self.assertEqual([e for e in erros if e.get("type") == "error"], [])
        self.assertTrue(p["moeda_sorte_ativa"])
        self.assertEqual(p["bag"], [])

    def test_nao_ativa_duas_vezes(self):
        r, p, erros = sala()
        p["moeda_sorte_ativa"] = True
        asyncio.run(r.handle_use_item("p1", "moeda_da_sorte"))
        self.assertTrue(any(e.get("type") == "error" for e in erros))
        self.assertEqual(len(p["bag"]), 1)

    def test_rerrola_ataque_que_falha_e_consome(self):
        r, p, _ = sala()
        p["moeda_sorte_ativa"] = True
        rolagens = iter([(False, 3, 3, False), (True, 18, 20, False)])
        with mock.patch.object(S, "d20_attack", lambda *a, **k: next(rolagens)):
            hit, roll, *_ = r._rolar_ataque(5, 12, atacante=p)
        self.assertTrue(hit)
        self.assertEqual(roll, 18)
        self.assertFalse(p["moeda_sorte_ativa"])
        self.assertTrue(p.pop("_moeda_sorte_rolada"))

    def test_nao_rerrola_acerto(self):
        r, p, _ = sala()
        p["moeda_sorte_ativa"] = True
        with mock.patch.object(S, "d20_attack", lambda *a, **k: (True, 15, 20, False)):
            hit, roll, *_ = r._rolar_ataque(5, 12, atacante=p)
        self.assertTrue(hit)
        self.assertTrue(p["moeda_sorte_ativa"])

    def test_sem_moeda_nao_rerrola(self):
        r, p, _ = sala()
        rolagens = iter([(False, 3, 3, False), (True, 18, 20, False)])
        with mock.patch.object(S, "d20_attack", lambda *a, **k: next(rolagens)):
            hit, roll, *_ = r._rolar_ataque(5, 12, atacante=p)
        self.assertFalse(hit)

    def test_rerrola_teste_de_resistencia_que_falha(self):
        r, p, _ = sala()
        p["moeda_sorte_ativa"] = True
        valores = iter([2, 19])
        with mock.patch.object(S.random, "randint", lambda a, b: next(valores)):
            passou, d20, bonus, total = r._testar_save(p, "reflexos", 10)
        self.assertTrue(passou)
        self.assertEqual(d20, 19)
        self.assertFalse(p["moeda_sorte_ativa"])
        self.assertTrue(r._resistance_events[-1].get("rerolled"))


if __name__ == "__main__":
    unittest.main()
