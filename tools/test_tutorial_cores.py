"""As cores de dano (RESISTIDO/VULNERÁVEL) que as lições do boneco e do óleo prometem."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S
from test_tutorial_salas import room


def sala():
    r, _ = room("warrior")
    return r


def reacao(r, tipo, dano, tipos, arma=None):
    ms = r.monsters.values() if isinstance(r.monsters, dict) else r.monsters
    m = next(x for x in ms if x["type"] == tipo
             and (tipo != "boneco_treino" or x.get("room_id") == 48))
    final = r._apply_damage_types(dano, tipos, m, weapon=arma)
    ctx = r._damage_visual_context.get(id(m))
    return final, ctx["reaction"]


class CoresDasLicoesTests(unittest.TestCase):
    def test_corte_contra_boneco_sai_resistido(self):
        r = sala()
        final, reac = reacao(r, "boneco_treino", 6, ["physical"], {"categoria": "cortante"})
        self.assertEqual(final, 1)
        self.assertEqual(reac, "resisted")

    def test_contundente_contra_boneco_sai_vulneravel(self):
        final, reac = reacao(sala(), "boneco_treino", 6, ["physical"], {"categoria": "contundente"})
        self.assertEqual(final, 8)
        self.assertEqual(reac, "vulnerable")

    def test_fogo_contra_boneco_de_palha_sai_vulneravel(self):
        final, reac = reacao(sala(), "boneco_palha", 1, ["fire"])
        self.assertGreater(final, 1)
        self.assertEqual(reac, "vulnerable")


if __name__ == "__main__":
    unittest.main()
