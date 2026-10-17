"""Descrição de anéis/botas custom: o campo `descricao` passa pelo validador e chega ao item
de bolsa/baú/loja; o Anel da Garra Negra explica os bônus e a habilidade que concede.
Roda da raiz: python -X utf8 tools/test_anel_garra_negra_descricao.py"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


class DescricaoTests(unittest.TestCase):
    def test_validador_e_dict_de_inventario_conservam_a_descricao(self):
        raw = {"id": "anel_teste_desc", "name": "Anel de Teste", "item_type": "ring",
               "bonuses": [{"effect": "atk_bonus", "value": 1}], "descricao": "  Um anel de teste.  "}
        ok, item = S._validate_custom_accessory(raw)
        self.assertTrue(ok)
        self.assertEqual(item["descricao"], "Um anel de teste.")
        self.assertEqual(S._custom_accessory_inventory_dict(item)["descricao"], "Um anel de teste.")
        raw.pop("descricao")
        ok, sem = S._validate_custom_accessory(raw)
        self.assertNotIn("descricao", sem)
        self.assertNotIn("descricao", S._custom_accessory_inventory_dict(sem))
        raw["descricao"] = "x" * 900
        self.assertEqual(len(S._validate_custom_accessory(raw)[1]["descricao"]), 600)

    def test_anel_da_garra_negra_descreve_bonus_e_habilidade(self):
        anel = S._DUNGEON_ITEM_CATALOG["anel_garra_negra"]
        d = anel["descricao"]
        for trecho in ("+1 de acerto", "+1 de visão", "Esconder nas Sombras", "ação bônus",
                       "🍖-2 💧-1", "Destreza", "invisível", "🍖-1 💧-1 por turno", "Ataque Furtivo"):
            self.assertIn(trecho, d)
        self.assertLessEqual(len(d), 600)
        efeitos = {(b["effect"], b["value"]) for b in anel["bonuses"]}
        self.assertEqual(efeitos, {("atk_bonus", 1), ("vision", 1)})
        self.assertEqual(anel["granted_ability"], "hero_rogue_esconder_sombras")
        self.assertEqual(anel["price"], 1000, "habilidade de classe + bônus: mais caro que a Lâmina do Vento (880)")

    def test_editor_serializa_a_descricao(self):
        js = (RAIZ / "tools" / "editor_items_logic.js").read_text(encoding="utf-8")
        self.assertIn("if (descricao) item.descricao = descricao;", js)
        ed = (RAIZ / "tools" / "editor_items_editor.js").read_text(encoding="utf-8")
        self.assertIn('id="ie-descricao"', ed)


if __name__ == "__main__":
    unittest.main()
