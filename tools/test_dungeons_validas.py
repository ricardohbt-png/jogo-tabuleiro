"""Toda masmorra de dungeons/ carrega e passa em validar_dungeon.

Pegou a regressão em que o laço de monstros do validador sobrescrevia as
dimensões do grid (w, h) e a checagem de elevação passava a recusar mapas válidos.
"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S


class MasmorrasTests(unittest.TestCase):
    def test_todas_as_masmorras_sao_validas(self):
        ruins = []
        for arq in sorted((RAIZ / "dungeons").glob("*.json")):
            if arq.name == "miniaturas.json":
                continue
            d = S.carregar_dungeon(arq.name)
            if not d:
                ruins.append(f"{arq.name}: não carrega")
                continue
            ok, motivo = S.validar_dungeon(d)
            if not ok:
                ruins.append(f"{arq.name}: {motivo}")
        self.assertEqual(ruins, [], "\n".join(ruins))

    def test_elevacao_usa_o_grid_e_nao_o_tamanho_do_ultimo_monstro(self):
        d = S.carregar_dungeon("floresta_2.json")
        self.assertTrue(d["elevacoes"], "o mapa de teste precisa de elevações")
        # um monstro 1x1 no fim da lista deixaria h=1; no bug, '2,1' caía fora do grid
        d["monsters"] = list(d.get("monsters") or []) + [d["monsters"][0]]
        self.assertEqual(S.validar_dungeon(d)[0], True)


if __name__ == "__main__":
    unittest.main()
