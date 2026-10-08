"""As cores de dano (RESISTIDO/VULNERÁVEL) que as lições do esqueleto e do óleo prometem."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S


def sala():
    r = S.GameRoom("CORES")
    r.load_authored_dungeon(S.carregar_dungeon("campo_de_treinamento.json"))
    return r


def reacao(r, tipo, dano, tipos, arma=None):
    ms = r.monsters.values() if isinstance(r.monsters, dict) else r.monsters
    m = next(x for x in ms if x["type"] == tipo)
    final = r._apply_damage_types(dano, tipos, m, weapon=arma)
    ctx = r._damage_visual_context.get(id(m))
    return final, ctx["reaction"]


class CoresDasLicoesTests(unittest.TestCase):
    def test_laminas_contra_esqueleto_saem_resistidas(self):
        r = sala()
        for cat in ("cortante", "perfurante"):
            final, reac = reacao(r, "esqueleto_humano", 6, ["physical"], {"categoria": cat})
            self.assertLess(final, 6, cat)
            self.assertEqual(reac, "resisted", cat)

    def test_impacto_contra_esqueleto_sai_vulneravel(self):
        final, reac = reacao(sala(), "esqueleto_humano", 6, ["physical"], {"categoria": "contundente"})
        self.assertGreater(final, 6)
        self.assertEqual(reac, "vulnerable")

    def test_fogo_contra_boneco_de_palha_sai_vulneravel(self):
        final, reac = reacao(sala(), "boneco_palha", 1, ["fire"])
        self.assertGreater(final, 1)
        self.assertEqual(reac, "vulnerable")


if __name__ == "__main__":
    unittest.main()
