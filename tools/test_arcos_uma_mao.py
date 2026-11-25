"""Arcos (inclusive o Arco Bruto do Combatente e variantes) são de UMA mão: as flechas ficam
equipadas na mão do escudo. Sem flechas lá (e sem aljava), o ataque é recusado.
Roda da raiz: python -X utf8 tools/test_arcos_uma_mao.py"""
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

BASES = ("arco_curto", "longbow", "arco_composto_curto", "arco_composto_longo", "arco_bruto_combatente")
MATERIAIS = ("freixo_negro", "cedro_rubro", "cerne_tita")


def arco_ids():
    ids = list(BASES)
    ids += [f"{b}_{m}" for b in BASES[2:] for m in MATERIAIS]
    return ids


def loja(item_id):
    return next(i for i in S.SHOP_WEAPONS if i["id"] == item_id)


class CatalogoTests(unittest.TestCase):
    def test_nenhum_arco_e_de_duas_maos(self):
        for wid in arco_ids():
            with self.subTest(arma=wid):
                self.assertFalse(S.WEAPONS[wid].get("two_handed"), "WEAPONS")
                self.assertFalse(loja(wid).get("two_handed"), "SHOP_WEAPONS")

    def test_descricao_nao_pede_duas_maos(self):
        for wid in arco_ids():
            self.assertNotIn("duas mãos", loja(wid).get("descricao", ""), wid)
            self.assertNotIn("Requer as duas mãos", S._descricao_arma_catalogo(loja(wid)), wid)


class Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("ARCO")
        self.room.phase = "playing"
        self.room.round_num = 3
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.erros = []

        async def noop(*a, **k): pass

        async def captura(pid, msg):
            if isinstance(msg, dict) and msg.get("type") == "error":
                self.erros.append(str(msg.get("msg")))

        self.room.push_state = self.room.broadcast_city_state = noop
        self.room.gm_say = noop
        self.room.broadcast = noop
        self.room.send_to = captura
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *a: True
        self.room._apply_damage_types = lambda dmg, *a, **k: dmg
        definicao = next(m for m in S.MONSTER_DEFS if m["type"] == "urso_negro")
        self.alvo = S.make_monster(definicao, {"id": 1, "cx": 8, "cy": 5})
        self.alvo.update(pos=[8, 5], hp=5000, max_hp=5000, ac=10)
        self.room.monsters = {self.alvo["id"]: self.alvo}

    def flechas(self, n=10):
        f = deepcopy(next(i for i in S.SHOP_AMMO if i["id"] == "flechas"))
        f.update(effect="ammo", ammo_count=n, item_slot="bag")
        return f

    def heroi(self, arco_id):
        p = S.make_player("h", "h", "warrior", 0)
        p.update(pos=[5, 5], action_done=False, bonus_action_used=False, fome=80, sede=80,
                 connected=True, alive=True)
        p["bag"] = []
        arma = deepcopy(loja(arco_id))
        p["gear"]["weapon"] = arma
        self.room._sincronizar_arma_de_combate(p, arma)
        self.room.players["h"] = p
        self.room.connections["h"] = object()
        return p

    async def atacar(self, p):
        p["action_done"] = False
        self.erros.clear()
        with patch.object(S, "d20_attack", return_value=(True, 12, 20, False)), \
                patch.object(S, "roll_dice", return_value=4):
            await self.room.handle_attack("h", self.alvo["id"])


class MunicaoTests(Base):
    async def test_flechas_so_na_bolsa_nao_bastam(self):
        for wid in arco_ids():
            with self.subTest(arma=wid):
                self.alvo["hp"] = 5000
                p = self.heroi(wid)
                p["bag"] = [self.flechas()]
                await self.atacar(p)
                self.assertTrue(self.erros, f"{wid}: atirou com as flechas só na bolsa")
                self.assertEqual(p["bag"][0]["ammo_count"], 10)
                self.assertEqual(self.alvo["hp"], 5000)

    async def test_flechas_na_mao_do_escudo_funcionam(self):
        for wid in arco_ids():
            with self.subTest(arma=wid):
                self.alvo["hp"] = 5000
                p = self.heroi(wid)
                p["gear"]["off_hand"] = self.flechas(10)
                await self.atacar(p)
                self.assertEqual(self.erros, [], wid)
                self.assertEqual(p["gear"]["off_hand"]["ammo_count"], 9, wid)
                self.assertLess(self.alvo["hp"], 5000, wid)

    async def test_escudo_na_mao_secundaria_impede_atirar(self):
        """Com escudo, as flechas não têm onde ficar equipadas: o arco não dispara."""
        p = self.heroi("arco_bruto_combatente")
        p["gear"]["off_hand"] = deepcopy(next(i for i in S.SHOP_ARMORS if i["id"] == "escudo_p"))
        p["bag"] = [self.flechas()]
        await self.atacar(p)
        self.assertTrue(self.erros)
        self.assertEqual(p["bag"][0]["ammo_count"], 10)


if __name__ == "__main__":
    unittest.main()
