"""Regressoes de falhas de combate achadas por simulacao (2026-11-16):
Pisoteio Colossal quebrava ao montar o caminho, e a Cola Alquimica quebrava
em criatura que ja nao anda.
Roda da raiz: python -X utf8 tools/test_correcoes_combate.py"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def sala():
    r = S.GameRoom("CORRECOES")
    r.phase = "playing"
    r.map_w = r.map_h = 14
    r.tiles = [[S.FLOOR] * 14 for _ in range(14)]
    r.rooms = [{"id": "r0", "x": 0, "y": 0, "w": 14, "h": 14,
                "cx": 7, "cy": 7, "locked": False}]
    r.monsters = {}
    r.players = {}
    r.zonas_especiais = []

    async def nada(*_a, **_k):
        return None

    r.broadcast = nada
    r.push_state = nada
    r.gm_say = nada
    r.send_to = nada
    return r


def monstro(r, tipo, mid, pos):
    molde = next(m for m in S.MONSTER_DEFS if m["type"] == tipo)
    m = S.make_monster(molde, r.rooms[0])
    m["id"] = mid
    m["pos"] = list(pos)
    r.monsters[mid] = m
    return m


class PisoteioTests(unittest.TestCase):
    def test_pisoteio_atinge_quem_esta_no_caminho(self):
        r = sala()
        gigante = next(m["type"] for m in S.MONSTER_DEFS
                       if any(a.get("id") == "pisoteio_colossal"
                              for a in m.get("special_abilities", [])))
        g = monstro(r, gigante, "g", [2, 2])
        p = S.make_player("p0", "Heroi", "warrior", 0)
        p.update(pos=[5, 2], alive=True, connected=True, hp=500, max_hp=500)
        r.players["p0"] = p
        g["_ciclope_move_count"] = 6
        g["_ciclope_straight"] = True
        g["_ciclope_path"] = [[3, 2], [4, 2], [5, 2], [6, 2]]
        asyncio.run(r._ciclope_pisoteio(g))
        self.assertTrue(g.get("_ciclope_pisoteio_usado"))
        self.assertLess(p["hp"], 500)


class ColaTests(unittest.TestCase):
    def test_cola_em_criatura_imovel_nao_quebra(self):
        r = sala()
        m = monstro(r, "goblin", "m", [4, 4])
        m["movement"] = 0
        ctrl = {"tipo": "mov_reduzido", "duracao": 2}
        asyncio.run(r._aplicar_controle_arremesso(m, ctrl, attacker_id=None))
        self.assertEqual(m["mov_reduzido_rodadas"], 2)
        self.assertEqual(m["mov_reduzido_orig"], 0)
        self.assertTrue(m.get("cola_sem_movimento"))

    def test_cola_em_criatura_comum_guarda_o_movimento(self):
        r = sala()
        m = monstro(r, "goblin", "m", [4, 4])
        antes = m["movement"]
        asyncio.run(r._aplicar_controle_arremesso(
            m, {"tipo": "mov_reduzido", "duracao": 2}, attacker_id=None))
        self.assertEqual(m["movement"], 0)
        self.assertEqual(m["mov_reduzido_orig"], antes)
        self.assertEqual(m["mov_reduzido_rodadas"], 2)


if __name__ == "__main__":
    unittest.main()
