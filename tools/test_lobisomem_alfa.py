"""Regressions for the ND 6 Lobisomem Alfa.

Run from the repository root with:
    python -X utf8 tools/test_lobisomem_alfa.py
"""
import asyncio
import unittest
import sys
import os
from pathlib import Path
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def definicao(tipo):
    return next((m for m in S.MONSTER_DEFS if m.get("type") == tipo), None)


def sala_teste():
    r = S.GameRoom("TEST")
    async def noop(*_a, **_k):
        pass
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.tiles = [[S.FLOOR] * 8 for _ in range(8)]
    r.map_w = r.map_h = 8
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda *_a, **_k: False
    r.monsters = {}
    return r


def alfa(r, hp=None):
    d = definicao("lobisomem_alfa")
    if d is None:
        return None
    m = S.make_monster(d, {"id": 1, "cx": 3, "cy": 3})
    m.update(id="alfa", pos=[3, 3], alive=True)
    if hp is not None:
        m["hp"] = hp
    r.monsters[m["id"]] = m
    return m


class LobisomemAlfaFichaEDano(unittest.TestCase):
    def test_ficha_alfa_e_ficha_comum(self):
        a = definicao("lobisomem_alfa")
        self.assertIsNotNone(a, "falta a ficha nativa lobisomem_alfa")
        self.assertEqual((a["name"], a["cr"], a["hp"], a["ac"]),
                         ("Lobisomem Alfa", 6, 85, 19))
        self.assertEqual(a["image"], "lobisomem_alfa")
        ataques = [(x["name"], x["atk_bonus"], x["damage"], x["num_attacks"])
                   for x in a["attacks"]]
        self.assertEqual(ataques, [
            ("Garras", 8, "2d6+5", 2),
            ("Mordida", 8, "2d8+5", 1),
        ])
        base = definicao("lobisomem")
        self.assertEqual((base["cr"], base["hp"], base["ac"]), (3, 31, 17))

    def test_miniatura_png_glb_e_mapeamento_do_cliente(self):
        raiz = Path(__file__).resolve().parents[1]
        png = raiz / "assets/pawns/monstros/lobisomem_alfa/lobisomem_alfa.png"
        glb = raiz / "assets/models3d/monstros/lobisomem_alfa.glb"
        self.assertTrue(png.is_file(), "falta PNG próprio do Alfa")
        self.assertTrue(glb.is_file(), "falta GLB próprio do Alfa")
        game = (raiz / "game.js").read_text(encoding="utf-8")
        self.assertRegex(game, r"lobisomem_alfa\s*:\s*'assets/models3d/monstros/lobisomem_alfa\.glb'")
        catalog = (raiz / "tools/editor_catalog.js").read_text(encoding="utf-8")
        self.assertIn('"type": "lobisomem_alfa"', catalog)

    def test_fisico_comum_e_prata_usam_regras_do_lobisomem(self):
        r = sala_teste()
        m = alfa(r)
        self.assertIsNotNone(m)
        normal = r._apply_damage_types(10, [S.DMG_PHYSICAL], m, {})
        prata = r._apply_damage_types(10, [S.DMG_PHYSICAL], m, {"silver": True})
        self.assertEqual(normal, 5)
        self.assertEqual(prata, 20)
        self.assertTrue(m.get("regeneracao_bloqueada"))

    def test_dano_magico_nao_letal_bloqueia_cura_passiva(self):
        r = sala_teste()
        m = alfa(r)
        self.assertIsNotNone(m)
        r._apply_damage_types(6, [S.DMG_MAGIC], m, None)
        self.assertTrue(m.get("regeneracao_bloqueada"))

    def test_fogo_aplicado_reduz_teto_e_dano_misto_conta_so_fogo(self):
        r = sala_teste()
        m = alfa(r)
        self.assertIsNotNone(m)
        r._registrar_dano_combate(m, 6, [S.DMG_FIRE])
        self.assertEqual(m.get("lobisomem_alfa_dano_fogo"), 6)
        r._registrar_dano_combate(
            m, 17, [S.DMG_PHYSICAL, S.DMG_FIRE], fire_damage_amount=7)
        self.assertEqual(m.get("lobisomem_alfa_dano_fogo"), 13)

    def test_fogo_zerado_por_resistencia_nao_reduz_teto(self):
        r = sala_teste()
        m = alfa(r)
        self.assertIsNotNone(m)
        m["resistances"] = [{"type": S.DMG_FIRE, "reduction": 99}]
        damage = r._apply_damage_types(5, [S.DMG_FIRE], m)
        self.assertEqual(damage, 0)
        self.assertEqual(m.get("lobisomem_alfa_dano_fogo", 0), 0)


class LobisomemAlfaRegeneracao(unittest.IsolatedAsyncioTestCase):
    async def processar_inicio(self, r, m):
        helper = getattr(r, "_processar_regeneracao_lobisomem_alfa_inicio", None)
        self.assertTrue(callable(helper), "falta o prólogo de regeneração do Alfa")
        await helper(m)

    async def test_regenera_cinco_pv_e_respeita_o_teto_de_fogo(self):
        r = sala_teste()
        m = alfa(r, hp=40)
        self.assertIsNotNone(m)
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 45)
        m["lobisomem_alfa_dano_fogo"] = 42  # teto 43
        m["hp"] = 40
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 43)
        m["hp"] = 40
        m["regeneracao_bloqueada"] = True
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 40)
        self.assertFalse(m.get("regeneracao_bloqueada"))
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 43)

    async def test_retornar_com_um_pv_apos_queda_nao_final(self):
        r = sala_teste()
        m = alfa(r, hp=0)
        self.assertIsNotNone(m)
        m["lobisomem_alfa_dano_fogo"] = 80  # teto ainda positivo
        m["lobisomem_alfa_regenerando"] = True
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 1)
        self.assertFalse(m.get("lobisomem_alfa_regenerando"))

    async def test_teto_zero_impede_retorno_e_finaliza_morte(self):
        r = sala_teste()
        m = alfa(r, hp=0)
        self.assertIsNotNone(m)
        m["lobisomem_alfa_dano_fogo"] = m["max_hp"]
        m["lobisomem_alfa_regenerando"] = True
        await self.processar_inicio(r, m)
        self.assertEqual(m["hp"], 0)
        self.assertFalse(m.get("lobisomem_alfa_regenerando"))

    async def test_alfa_caido_permanece_na_iniciativa_real(self):
        r = sala_teste()
        m = alfa(r, hp=0)
        self.assertIsNotNone(m)
        m["lobisomem_alfa_regenerando"] = True
        r.players = {}
        r.player_order = []
        r.round_num = 1
        r._rebuild_initiative()
        self.assertEqual(r.initiative_order[0]["id"], m["id"])
        self.assertTrue(r._monster_regenerando_a_zero(m))

    async def test_golpe_letal_de_prata_e_marcado_na_aplicacao_de_dano(self):
        r = sala_teste()
        m = alfa(r, hp=10)
        self.assertIsNotNone(m)
        dano = r._apply_damage_types(6, [S.DMG_PHYSICAL], m, {"silver": True})
        m["hp"] = 0
        r._registrar_dano_combate(m, dano, [S.DMG_PHYSICAL])
        await r._monster_dies(m, None)
        self.assertFalse(m.get("lobisomem_alfa_regenerando"))
        self.assertTrue(m.get("lobisomem_alfa_morte_definitiva"))

    async def test_prata_nao_letal_nao_contamina_o_golpe_comum_letal_seguinte(self):
        r = sala_teste()
        m = alfa(r, hp=30)
        self.assertIsNotNone(m)
        r._apply_damage_types(4, [S.DMG_PHYSICAL], m, {"silver": True})
        r._registrar_dano_combate(m, 8, [S.DMG_PHYSICAL])
        m["hp"] = 0
        r._apply_damage_types(8, [S.DMG_PHYSICAL], m, {})
        r._registrar_dano_combate(m, 4, [S.DMG_PHYSICAL])
        await r._monster_dies(m, None)
        self.assertTrue(m.get("lobisomem_alfa_regenerando"))
        self.assertFalse(m.get("lobisomem_alfa_morte_definitiva"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
