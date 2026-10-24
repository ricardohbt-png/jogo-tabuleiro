"""A mão principal inicial (item reduzido em gear.weapon, sem `die`) também recebe veneno.
Roda da raiz: python -X utf8 tools/test_veneno_arma_principal.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

VENENO = "veneno_aranha_sombria"


def sala():
    r = S.GameRoom("VENENO")
    p = S.make_player("p0", "Luccas", "rogue", 0)
    p["sede"] = 10
    p["bag"] = [dict(next(i for i in S.SHOP_MERCHANT if i["id"] == VENENO)) for _ in range(2)]
    r.players["p0"] = p
    r.host_pid = "p0"
    r.phase = "playing"
    erros = []

    async def nada(*a, **k):
        pass

    async def enviar(pid, msg):
        if msg.get("type") == "error":
            erros.append(str(msg.get("msg")))
    r.send_to = enviar; r.broadcast = nada; r.push_state = nada; r.gm_say = nada
    r._is_turn = lambda pid: True
    return r, p, erros


class MaoPrincipalTests(unittest.TestCase):
    def test_o_item_inicial_da_mao_principal_nao_tem_dado(self):
        _r, p, _e = sala()
        self.assertFalse(p["gear"]["weapon"].get("die"), "premissa: o item inicial vem reduzido")
        self.assertTrue(p["weapon"].get("die"))

    def test_arma_do_slot_completa_a_principal(self):
        r, p, _e = sala()
        self.assertTrue(r._arma_do_slot(p, "weapon").get("die"))
        self.assertTrue(r._arma_do_slot(p, "off_hand").get("die"))
        self.assertIsNone(r._arma_do_slot(dict(p, gear={}), "off_hand"))

    def test_as_duas_maos_aceitam_o_veneno(self):
        r, p, _e = sala()
        for slot in ("weapon", "off_hand"):
            self.assertTrue(r._validar_aplicacao_veneno_arma(p, VENENO, slot), slot)

    def test_veneno_rapido_na_mao_principal_e_na_secundaria(self):
        for slot in ("weapon", "off_hand"):
            r, p, erros = sala()
            asyncio.run(r.handle_veneno_rapido("p0", {"veneno_id": VENENO, "weapon_slot": slot}))
            self.assertEqual(erros, [], slot)
            self.assertEqual(len(r._poison_slots_do_item(p, slot)), 3, slot)
            outro = "off_hand" if slot == "weapon" else "weapon"
            self.assertEqual(r._poison_slots_do_item(p, outro), [], "só a mão escolhida recebe")

    def test_frasco_da_bolsa_na_mao_principal(self):
        r, p, erros = sala()
        asyncio.run(r.handle_use_item("p0", VENENO, weapon_slot="weapon"))
        self.assertEqual(erros, [])
        self.assertEqual(len(r._poison_slots_do_item(p, "weapon")), 3)


if __name__ == "__main__":
    unittest.main()
