"""Espadas do Sangramento (longa e bastarda): perfil, progressão do Sangramento a cada
acerto sem limite por rodada, Hemorragia no crítico (19–20) e imunes.
Roda da raiz: python -X utf8 tools/test_espadas_sangramento.py"""
import json
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

ESPADAS = {"espada_sangramento_longa": ("1d8", 1500), "espada_sangramento_bastarda": ("1d10", 2000)}


def loja(item_id):
    return next(i for i in S.SHOP_WEAPONS if i["id"] == item_id)


class CatalogoTests(unittest.TestCase):
    def test_perfil(self):
        for wid, (dado, preco) in ESPADAS.items():
            it = loja(wid)
            self.assertEqual((it["die"], it["price"]), (dado, preco), wid)
            self.assertEqual(it["allowed_classes"], ["paladin", "warrior"], wid)
            self.assertEqual((it["atk_bonus"], it["damage_bonus"]), (1, 1), wid)
            self.assertEqual(it["crit_min_nat_roll"], 19, wid)
            self.assertTrue(it["magical"] and it["causa_sangramento"], wid)

    def test_nas_cinco_ferrarias(self):
        with open(ROOT / "city_shops.json", encoding="utf-8") as f:
            cidades = json.load(f)
        n = 0
        for cidade, lojas in cidades.items():
            lista = (lojas or {}).get("ferreiro_weapon")
            if lista is None:
                continue
            n += 1
            for wid in ESPADAS:
                self.assertIn(wid, lista, f"{wid} fora de {cidade}")
        self.assertEqual(n, 5)


class Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("SANGRA")
        self.room.phase = "playing"
        self.room.round_num = 3
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]

        async def noop(*a, **k): pass
        self.room.push_state = self.room.broadcast_city_state = noop
        self.room.gm_say = noop
        self.room.broadcast = self.room.send_to = noop
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *a: True
        self.room._apply_damage_types = lambda dmg, *a, **k: dmg
        self.alvo = self.novo_alvo("urso_negro")

    def novo_alvo(self, tipo):
        definicao = next(m for m in S.MONSTER_DEFS if m["type"] == tipo)
        m = S.make_monster(definicao, {"id": 1, "cx": 6, "cy": 5})
        m.update(pos=[6, 5], hp=5000, max_hp=5000, ac=10)
        self.room.monsters = {m["id"]: m}
        return m

    def heroi(self, item_id, classe="warrior"):
        p = S.make_player("h", "h", classe, 0)
        p.update(pos=[5, 5], action_done=False, bonus_action_used=False, fome=80, sede=80,
                 connected=True, alive=True)
        p["bag"] = []
        arma = deepcopy(loja(item_id))
        p["gear"]["weapon"] = arma
        self.room._sincronizar_arma_de_combate(p, arma)
        self.room.players["h"] = p
        self.room.connections["h"] = object()
        return p

    async def atacar(self, p, acerta=True, critico=False):
        p["action_done"] = False
        with patch.object(S, "d20_attack", return_value=(acerta, 20 if critico else 12, 20, critico)), \
                patch.object(S, "roll_dice", return_value=4), patch.object(S.random, "randint", return_value=4):
            await self.room.handle_attack("h", self.alvo["id"])


class CombateTests(Base):
    async def test_arma_de_combate_mantem_o_efeito(self):
        for wid in ESPADAS:
            p = self.heroi(wid)
            self.assertTrue(p["weapon"].get("causa_sangramento"), wid)

    async def test_acerto_aplica_e_erro_nao(self):
        for wid in ESPADAS:
            self.alvo = self.novo_alvo("urso_negro")
            p = self.heroi(wid)
            await self.atacar(p, acerta=False)
            self.assertFalse(self.alvo.get("sangramento_nivel"), f"{wid}: errou e sangrou")
            await self.atacar(p)
            self.assertEqual(self.alvo.get("sangramento_nivel"), 1, wid)

    async def test_progressao_sem_limite_por_rodada(self):
        """Vários acertos na MESMA rodada: níveis 1→3, depois Ferida Aberta, +2 rodadas por golpe."""
        p = self.heroi("espada_sangramento_longa")
        with patch.object(self.room, "_rolar_dado", lambda e: 3):
            await self.atacar(p)
            self.assertEqual((self.alvo["sangramento_nivel"], self.alvo["sangramento_rodadas"]), (1, 3))
            await self.atacar(p)
            self.assertEqual((self.alvo["sangramento_nivel"], self.alvo["sangramento_rodadas"]), (2, 5))
            await self.atacar(p)
            self.assertEqual((self.alvo["sangramento_nivel"], self.alvo["sangramento_rodadas"]), (3, 7))
            self.assertFalse(self.alvo.get("ferida_aberta"))
            await self.atacar(p)
            self.assertTrue(self.alvo.get("ferida_aberta"))
            self.assertEqual((self.alvo["sangramento_nivel"], self.alvo["sangramento_rodadas"]), (3, 9))

    async def test_critico_aplica_hemorragia_e_acerto_comum_nao(self):
        p = self.heroi("espada_sangramento_bastarda")
        await self.atacar(p)
        self.assertFalse(self.alvo.get("hemorragia"))
        await self.atacar(p, critico=True)
        self.assertTrue(self.alvo.get("hemorragia"))

    async def test_critico_com_19_natural(self):
        """crit_min_nat_roll 19: um 19 natural já é crítico (Hemorragia) e 18 não."""
        for rolagem, esperado in ((18, False), (19, True), (20, True)):
            self.alvo = self.novo_alvo("urso_negro")
            p = self.heroi("espada_sangramento_longa")
            p["action_done"] = False
            with patch.object(S.random, "randint", return_value=rolagem), \
                    patch.object(S, "roll_dice", return_value=4):
                await self.room.handle_attack("h", self.alvo["id"])
            self.assertEqual(bool(self.alvo.get("hemorragia")), esperado, f"rolagem {rolagem}")

    async def test_imune_nao_sangra(self):
        self.alvo = self.novo_alvo("esqueleto_humano")
        p = self.heroi("espada_sangramento_longa")
        await self.atacar(p)
        self.assertFalse(self.alvo.get("sangramento_nivel"))

    async def test_ferroada_tambem_aplica_sangramento(self):
        """A Ferroada usa o mesmo campo `causa_sangramento` e sofria do mesmo defeito."""
        p = self.heroi("ferroada")
        self.assertTrue(p["weapon"].get("causa_sangramento"))
        await self.atacar(p)
        self.assertEqual(self.alvo.get("sangramento_nivel"), 1)

    async def test_dano_bonus_mais_um(self):
        """O +1 de dano mágico entra no dano da espada (comparado a uma espada longa comum)."""
        p = self.heroi("espada_sangramento_longa")
        self.assertEqual(p["weapon"].get("damage_bonus"), 1)
        self.assertEqual(p["weapon"].get("atk_bonus"), 1)


if __name__ == "__main__":
    unittest.main()
