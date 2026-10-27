"""Kit de Reparo de Campo: remove 1 nível de corrosão por uso, gasta a ação principal e o kit.
Roda da raiz: python -X utf8 tools/test_kit_reparo.py
"""
import asyncio
import os
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def sala(nivel=2, destruida=False):
    r = S.GameRoom("KIT")
    erros = []
    async def noop(*a, **k):
        return None
    async def send(pid, msg, *a, **k):
        erros.append(msg)
    r.gm_say = r.push_state = r.broadcast = noop
    r.send_to = send
    r._is_turn = lambda pid: True
    p = S.make_player("p1", "Aluna", "warrior", 0)
    arma = deepcopy(S.SHOP_WEAPONS[0])
    arma["corrosion_level"] = nivel
    if destruida:
        arma["corrosion_destroyed"] = True
    p["gear"]["weapon"] = arma
    p["weapon"] = arma
    c = r._corr(p)
    c["arma_lvl"] = nivel
    c["arma_id"] = arma["id"]
    c["arma_destruida"] = destruida
    p["bag"] = [deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == "kit_reparo_campo"))]
    r.players["p1"] = p
    return r, p, erros


class KitReparoTests(unittest.TestCase):
    def test_item_da_loja(self):
        kit = next(i for i in S.SHOP_AMMO if i["id"] == "kit_reparo_campo")
        self.assertEqual((kit["price"], kit["effect"], kit["item_slot"]), (60, "repair_corrosion", "bag"))

    def test_remove_um_nivel_gasta_o_kit_e_a_acao_principal(self):
        r, p, erros = sala(nivel=2)
        asyncio.run(r.handle_use_item("p1", "kit_reparo_campo", "repair:gear:weapon"))
        self.assertEqual([e for e in erros if e.get("type") == "error"], [])
        self.assertEqual(p["gear"]["weapon"].get("corrosion_level"), 1)
        self.assertEqual(p["bag"], [])
        self.assertTrue(p["action_done"])

    def test_ultimo_nivel_limpa_a_corrosao(self):
        r, p, _ = sala(nivel=1)
        asyncio.run(r.handle_use_item("p1", "kit_reparo_campo", "repair:gear:weapon"))
        self.assertFalse(p["gear"]["weapon"].get("corrosion_level"))

    def test_sem_alvo_recusa_sem_gastar(self):
        r, p, erros = sala(nivel=2)
        asyncio.run(r.handle_use_item("p1", "kit_reparo_campo"))
        self.assertTrue(any(e.get("type") == "error" for e in erros))
        self.assertEqual(len(p["bag"]), 1)
        self.assertFalse(p.get("action_done"))

    def test_peca_destruida_nao_e_alvo(self):
        r, p, erros = sala(nivel=3, destruida=True)
        asyncio.run(r.handle_use_item("p1", "kit_reparo_campo", "repair:gear:weapon"))
        self.assertTrue(any(e.get("type") == "error" for e in erros))
        self.assertEqual(len(p["bag"]), 1)

    def test_acao_principal_ja_usada_recusa(self):
        r, p, erros = sala(nivel=2)
        p["action_done"] = True
        asyncio.run(r.handle_use_item("p1", "kit_reparo_campo", "repair:gear:weapon"))
        self.assertTrue(any(e.get("type") == "error" for e in erros))
        self.assertEqual(p["gear"]["weapon"].get("corrosion_level"), 2)
        self.assertEqual(len(p["bag"]), 1)


if __name__ == "__main__":
    unittest.main()
