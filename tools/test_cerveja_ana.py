"""Cerveja Anã: +18 fome/sede e -1 CA por 10 rodadas, sem acumular.
Rode da raiz: python -X utf8 tools/test_cerveja_ana.py"""
import asyncio
import json
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S


def sala():
    r = S.GameRoom("CERVEJA")
    erros = []

    async def noop(*a, **k):
        return None

    async def send(pid, msg, *a, **k):
        erros.append(msg)

    r.gm_say = r.push_state = r.broadcast = noop
    r.send_to = send
    r._is_turn = lambda pid: True
    p = S.make_player("p1", "Aluna", "warrior", 0)
    p["fome"], p["sede"] = 10, 10
    p["bag"] = [deepcopy(next(i for i in S.SHOP_TAVERN if i["id"] == "cerveja_ana"))]
    r.players["p1"] = p
    return r, p, erros


class CervejaAnaTests(unittest.TestCase):
    def test_item_e_estoque_das_cinco_tavernas(self):
        item = next(i for i in S.SHOP_TAVERN if i["id"] == "cerveja_ana")
        self.assertEqual((item["price"], item["effect"], item["value"]), (8, "ale_ac", 18))
        self.assertEqual(item["icon"], "assets/itens/barril_de_cerveja.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        tavernas = [c for c, l in lojas.items() if "taverna" in l]
        self.assertEqual(len(tavernas), 5)
        for cidade in tavernas:
            self.assertEqual(lojas[cidade]["taverna"].count("cerveja_ana"), 1, cidade)

    def test_beber_restaura_e_reduz_a_ca(self):
        r, p, erros = sala()
        ca = r._player_effective_ac(p)
        asyncio.run(r.handle_use_item("p1", "cerveja_ana"))
        self.assertEqual([e for e in erros if e.get("type") == "error"], [])
        self.assertEqual((p["fome"], p["sede"]), (28, 28))
        self.assertEqual(r._player_effective_ac(p), ca - 1)
        self.assertEqual(p["cerveja_ana_ca_rodadas"], 10)
        self.assertEqual(p["bag"], [])

    def test_beber_outra_renova_sem_acumular(self):
        r, p, _ = sala()
        ca = r._player_effective_ac(p)
        asyncio.run(r.handle_use_item("p1", "cerveja_ana"))
        p["cerveja_ana_ca_rodadas"] = 3
        p["bag"] = [deepcopy(next(i for i in S.SHOP_TAVERN if i["id"] == "cerveja_ana"))]
        asyncio.run(r.handle_use_item("p1", "cerveja_ana"))
        self.assertEqual(p["cerveja_ana_ca_rodadas"], 10)
        self.assertEqual(r._player_effective_ac(p), ca - 1)

    def test_efeito_acaba_apos_dez_rodadas(self):
        r, p, _ = sala()
        ca = r._player_effective_ac(p)
        asyncio.run(r.handle_use_item("p1", "cerveja_ana"))
        for _ in range(9):
            asyncio.run(r._processar_cerveja_ana_turno(p))
        self.assertEqual(r._player_effective_ac(p), ca - 1)
        asyncio.run(r._processar_cerveja_ana_turno(p))
        self.assertEqual(r._player_effective_ac(p), ca)

    def test_nova_masmorra_limpa_o_efeito(self):
        r, p, _ = sala()
        ca = r._player_effective_ac(p)
        asyncio.run(r.handle_use_item("p1", "cerveja_ana"))
        r._resetar_cerveja(p)
        self.assertEqual(r._player_effective_ac(p), ca)
        self.assertEqual(p["cerveja_ana_ca_rodadas"], 0)


if __name__ == "__main__":
    unittest.main()
