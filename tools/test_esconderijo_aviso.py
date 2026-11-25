"""Esconderijo notado: o servidor manda o aviso visível (toast + brilho) além do log.
Roda da raiz: python -X utf8 tools/test_esconderijo_aviso.py"""
import asyncio
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S


def sala(classe="warrior"):
    tiles = [[0] * 7] + [[0] + [1] * 5 + [0] for _ in range(5)] + [[0] * 7]
    dec = {"id": "barril_x", "type": "barril", "pos": [5, 1], "facing": [0, 1],
           "loot": {"gold": 7, "items": [{"id": "espada_magica"}]}, "escondido": True, "cd_busca": 5}
    defn = {"schema_version": 1, "name": "t", "grid": {"w": 7, "h": 7}, "tiles": tiles,
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": 0, "x": 1, "y": 1, "w": 5, "h": 5, "role": "entrance"}],
            "monsters": [], "decorations": [dec]}
    r = S.GameRoom("AVI")
    r.players["p0"] = S.make_player("p0", "Heroi", classe, 0)
    r.host_pid = "p0"; r.phase = "playing"
    r.load_authored_dungeon(defn)
    r.log, r.enviados = [], []

    async def gm_say(t): r.log.append(str(t))
    async def broadcast(m, *a, **k): r.enviados.append(m)
    async def nada(*a, **k): pass
    r.gm_say = gm_say; r.broadcast = broadcast; r.send_to = nada; r.push_state = nada
    return r


class AvisoTests(unittest.TestCase):
    def avisos(self, r):
        return [m for m in r.enviados if m.get("type") == "esconderijo_achado"]

    def test_percepcao_manda_aviso_e_log(self):
        r = sala(); p = r.players["p0"]; p["pos"] = [4, 1]
        with mock.patch.object(S.random, "randint", return_value=20):
            asyncio.run(r._procurar_esconderijos(p))
        av = self.avisos(r)
        self.assertEqual(len(av), 1)
        self.assertEqual(av[0]["decor_id"], "barril_x")
        self.assertEqual(av[0]["pos"], [5, 1])
        self.assertIn("Heroi", str(av[0]["texto"]))
        self.assertTrue(r.log, "o log de narração continua recebendo a linha")

    def test_falha_nao_avisa_nada(self):
        r = sala(); p = r.players["p0"]; p["pos"] = [4, 1]
        with mock.patch.object(S.random, "randint", return_value=1):
            asyncio.run(r._procurar_esconderijos(p))
        self.assertEqual(self.avisos(r), [])
        self.assertEqual(r.log, [])

    def test_detectar_armadilhas_tambem_avisa(self):
        r = sala("rogue"); p = r.players["p0"]; p["pos"] = [2, 1]; p["detectar_ativo"] = True
        with mock.patch.object(S.random, "randint", return_value=1):
            asyncio.run(r._procurar_esconderijos(p))
        av = self.avisos(r)
        self.assertEqual(len(av), 1)
        self.assertEqual(av[0]["decor_id"], "barril_x")

    def test_so_avisa_uma_vez(self):
        r = sala(); p = r.players["p0"]; p["pos"] = [4, 1]
        with mock.patch.object(S.random, "randint", return_value=20):
            asyncio.run(r._procurar_esconderijos(p))
            asyncio.run(r._procurar_esconderijos(p))
        self.assertEqual(len(self.avisos(r)), 1)


if __name__ == "__main__":
    unittest.main()
