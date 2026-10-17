"""Morte do refém com `primary.se_falhar`: renome/marcador na hora, uma vez só, sem encerrar a missão.
Roda da raiz: python -X utf8 tools/test_refem_consequencia.py"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

DEFN = {"schema_version": 1, "grid": {"w": 8, "h": 8}, "tiles": [[1] * 8 for _ in range(8)],
        "entrance": {"x": 1, "y": 1}, "rooms": [{"id": "r1", "role": "entrance", "x": 0, "y": 0, "w": 8, "h": 8}],
        "prisoner": {"pos": [4, 4], "room_id": "r1"},
        "objectives": {"primary": {"type": "rescue_prisoner",
                                   "se_falhar": {"renome": -5, "fato": "charcos_criancas_mortas"}},
                       "secondary": []}}


def sala(defn=DEFN):
    r = S.GameRoom("REFEM")
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.msgs = []

    async def noop(*a, **k): pass

    async def send(pid, m, *a, **k): r.msgs.append(m)
    r.gm_say = noop; r.broadcast = noop; r.send_to = send; r.push_state = noop
    r.load_authored_dungeon(deepcopy(defn))
    r.phase = "playing"
    r.world_adventure_id = "charcos_aldeia"
    return r


def morrer(r):
    asyncio.run(r._prisioneiro_morre())


class RefemConsequenciaTests(unittest.TestCase):
    def test_morte_aplica_renome_e_fato_uma_vez(self):
        r = sala(); r.renome = 10
        morrer(r); morrer(r)
        self.assertEqual(r.renome, 5)
        self.assertIn("charcos_criancas_mortas", r.fatos)
        self.assertTrue(r.rescue_failed)

    def test_piso_zero(self):
        r = sala(); r.renome = 2
        morrer(r)
        self.assertEqual(r.renome, 0)

    def test_nao_encerra_a_missao(self):
        r = sala()
        morrer(r)
        self.assertEqual(r.phase, "playing")
        self.assertEqual(r.world_adventure_id, "charcos_aldeia")

    def test_sem_se_falhar_nada_muda(self):
        d = deepcopy(DEFN); del d["objectives"]["primary"]["se_falhar"]
        r = sala(d); r.renome = 7
        morrer(r)
        self.assertEqual(r.renome, 7)
        self.assertEqual(set(r.fatos), set())
        self.assertTrue(r.rescue_failed)

    def test_foto_inclui_o_campo(self):
        self.assertEqual(S.FOTO_SALA_CATEGORIAS.get("_consequencia_refem_aplicada"), "foto")

    def test_nova_tentativa_reseta(self):
        r = sala(); r.renome = 10
        morrer(r)
        self.assertTrue(r._consequencia_refem_aplicada)
        r.load_authored_dungeon(deepcopy(DEFN))
        self.assertFalse(r._consequencia_refem_aplicada)
        self.assertFalse(r.rescue_failed)
        self.assertTrue(r.prisoner and r.prisoner.get("alive", True))
        self.assertEqual(r.renome, 5, "o renome perdido não volta")


if __name__ == "__main__":
    unittest.main()
