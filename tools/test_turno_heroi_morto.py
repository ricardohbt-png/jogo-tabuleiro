"""Herói que morre na própria vez (dano de terreno no início do turno, ou durante o turno)
não pode travar a iniciativa: a vez passa ao próximo ator.
Roda da raiz: python -X utf8 tools/test_turno_heroi_morto.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def sala():
    r = S.GameRoom("TMORTO")
    r.phase = "playing"
    r.monsters = {}
    r.armadilhas = []
    r.sent = []

    async def nada(*a, **k):
        pass

    async def captura(pid, msg):
        r.sent.append((pid, msg))

    r.gm_say = nada
    r.broadcast = nada
    r.push_state = nada
    r.send_to = captura
    ps = [S.make_player(f"p{i}", n, c, i) for i, (n, c) in enumerate((("A", "warrior"), ("B", "mage"), ("C", "cleric")), 1)]
    r.players = {p["id"]: p for p in ps}
    for p in ps:
        p["pos"] = [p["slot"] + 1, 1]
    r.player_order = list(r.players)
    r.initiative_active = True
    r.initiative_order = [{"kind": "player", "id": f"p{i}", "seq": i - 1, "initiative": 20 - i} for i in (1, 2, 3)]
    r.initiative_index = 0
    return r


def rodar(coro):
    return asyncio.run(coro)


class TurnoDoMortoTests(unittest.TestCase):
    def test_morte_por_lava_no_inicio_do_turno_passa_a_vez(self):
        r = sala()
        a = r.players["p1"]
        a["hp"] = 1
        r._is_lava_tile = lambda x, y: [x, y] == a["pos"]   # só a casa do herói da vez é lava

        async def roteiro():
            await r._activate_initiative_actor()
            await asyncio.sleep(0.05)

        rodar(roteiro())
        self.assertFalse(a["alive"], "a lava deveria ter matado o herói")
        self.assertEqual(r.current_pid(), "p2", "a vez devia passar ao próximo herói")

    def test_morte_no_meio_do_turno_passa_a_vez(self):
        r = sala()

        async def roteiro():
            await r._player_dies("p1")
            await asyncio.sleep(0.6)

        rodar(roteiro())
        self.assertFalse(r.players["p1"]["alive"])
        self.assertEqual(r.current_pid(), "p2", "a vez devia passar depois da morte")

    def test_morte_de_quem_nao_esta_na_vez_nao_avanca(self):
        r = sala()

        async def roteiro():
            await r._player_dies("p3")
            await asyncio.sleep(0.6)

        rodar(roteiro())
        self.assertFalse(r.players["p3"]["alive"])
        self.assertEqual(r.current_pid(), "p1", "a vez de p1 não pode ser pulada")

    def test_ultimo_heroi_vivo_morrendo_encerra_o_jogo_sem_avancar(self):
        r = sala()
        for pid in ("p2", "p3"):
            r.players[pid]["alive"] = False
            r.players[pid]["hp"] = 0
        fim = []

        async def end_game(victory, story=None):
            fim.append(victory)

        r.end_game = end_game

        async def roteiro():
            await r._player_dies("p1")
            await asyncio.sleep(0.6)

        rodar(roteiro())
        self.assertEqual(fim, [False])


if __name__ == "__main__":
    unittest.main()
