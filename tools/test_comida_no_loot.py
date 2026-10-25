"""Monstros humanoides têm 10% de chance de deixar uma comida transportável (mais barata = mais comum).
Roda da raiz: python -X utf8 tools/test_comida_no_loot.py
"""
import os
import sys
import unittest
from collections import Counter
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

DO_GRUPO = ["orc", "orc_guerreiro", "dark_mage", "bardo", "bardo_da_caravana", "goblin", "goblin_combatente",
            "goblin_dual", "goblin_arqueiro", "goblin_assassino", "goblin_xama", "xama_goblin_customizado",
            "troll", "bandido", "necromante", "kobold_lanceiro", "kobold_besteiro", "ogro_clava",
            "ogro_lanca", "soldado"]
FORA = ["urso_negro", "lobo_cinzento", "minotauro", "grotao", "esqueleto_humano", "zumbi_infectado",
        "bugbear_sombras", "gigante_guerra", "elemental_fogo", "rato"]
COMIDAS = {"pao", "garrafa_agua", "suco_fruta", "racao_viagem", "racao_completa", "cantil_agua",
           "banquete_viagem"}


def sala():
    r = S.GameRoom("COMIDA")
    async def noop(*a, **k):
        pass
    r.gm_say = r.broadcast = r.push_state = r.send_to = noop
    r.phase = "playing"
    r.map_w = r.map_h = 10
    r.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    r.players["p1"] = dict(S.make_player("p1", "Alvo", "warrior", 0), pos=[3, 4])
    return r


def monstro(tipo):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": 5, "cy": 5})
    m["pos"] = [5, 5]
    m["troll_morte_definitiva"] = True     # o troll só deixa saque na morte final (sem regenerar)
    return m


async def matar(r, m):
    r.monsters[m["id"]] = m
    m["hp"] = 0
    await r._monster_dies(m, None)
    return [it for c in r.chests.values() for it in c["items"]] + \
           [g["item"] for g in r.ground_items.values()]


class GrupoTests(unittest.TestCase):
    def test_a_chance_e_de_10_por_cento(self):
        self.assertEqual(S.CHANCE_COMIDA_MONSTRO, 0.10)

    def test_grupo_e_variantes(self):
        for tipo in DO_GRUPO:
            self.assertTrue(S._monstro_deixa_comida({"type": tipo}), tipo)
        for tipo in FORA:
            self.assertFalse(S._monstro_deixa_comida({"type": tipo}), tipo)

    def test_so_comida_transportavel_e_mais_barata_e_mais_comum(self):
        contagem = Counter(S._sortear_comida_monstro()["id"] for _ in range(4000))
        self.assertTrue(set(contagem) <= COMIDAS, set(contagem) - COMIDAS)
        self.assertGreater(contagem["pao"], contagem["garrafa_agua"])
        self.assertGreater(contagem["garrafa_agua"], contagem["suco_fruta"])
        self.assertGreater(contagem["suco_fruta"], contagem.get("racao_viagem", 0))
        for _ in range(50):
            self.assertNotIn("price", S._sortear_comida_monstro())


MARCA = {"id": "comida_de_teste", "name": "Comida de teste", "item_slot": "bag", "effect": "food"}


class DropTests(unittest.IsolatedAsyncioTestCase):
    """A comida sorteada vira uma marca fixa: o necromante e outros já soltam ração por conta própria."""

    async def _extras(self, tipo, chance):
        with patch.object(S, "CHANCE_COMIDA_MONSTRO", chance),                 patch.object(S, "_sortear_comida_monstro", lambda: dict(MARCA)):
            itens = await matar(sala(), monstro(tipo))
        return [i for i in itens if i["id"] == MARCA["id"]]

    async def test_com_sorte_cada_monstro_do_grupo_deixa_uma_comida(self):
        for tipo in DO_GRUPO:
            with self.subTest(tipo=tipo):
                self.assertEqual(len(await self._extras(tipo, 1.0)), 1)

    async def test_sem_sorte_nenhuma_comida_extra(self):
        for tipo in DO_GRUPO:
            with self.subTest(tipo=tipo):
                self.assertEqual(await self._extras(tipo, 0.0), [])

    async def test_monstro_fora_do_grupo_nunca_deixa(self):
        for tipo in ("lobo_cinzento", "urso_negro", "minotauro"):
            with self.subTest(tipo=tipo):
                self.assertEqual(await self._extras(tipo, 1.0), [])


if __name__ == "__main__":
    unittest.main()
