"""Velocidade (magia e poção): `dur` rodadas valem `dur` turnos com o efeito e o movimento
restante dobra já no turno do cast.
Roda da raiz: python -X utf8 tools/test_velocidade_duracao.py"""
import asyncio
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S


def sala(dado):
    tiles = [[0] * 5] + [[0, 1, 1, 1, 0] for _ in range(3)] + [[0] * 5]
    defn = {"schema_version": 1, "name": "t", "grid": {"w": 5, "h": 5}, "tiles": tiles,
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": 0, "x": 1, "y": 1, "w": 3, "h": 3, "role": "entrance"}],
            "monsters": [], "decorations": []}
    r = S.GameRoom("VEL")
    r.players["p0"] = S.make_player("p0", "Mago", "mage", 0)
    r.host_pid = "p0"; r.phase = "playing"
    r.load_authored_dungeon(defn)

    async def nada(*a, **k): pass
    r.gm_say = nada; r.send_to = nada; r.push_state = nada; r.broadcast = nada
    r._rolar_dado = lambda expressao: dado
    return r, r.players["p0"]


async def turnos_com_efeito(r, p, limite=10):
    """Conta os turnos seguintes ao cast em que o movimento vem dobrado."""
    total = 0
    for _ in range(limite):
        p["action_done"] = False; p["bonus_action_used"] = False
        await r._start_initiative_player_turn(p)
        if p["moves_left"] == p["spd"] * 2 and p.get("velocidade_rodadas"):
            total += 1
        elif not p.get("velocidade_rodadas"):
            break
    return total


class VelocidadeTests(unittest.TestCase):
    def test_duracao_vale_dur_turnos(self):
        for dado in (1, 2, 4):
            with self.subTest(dado=dado):
                r, p = sala(dado)
                p["moves_left"] = p["spd"]; p["action_done"] = True
                asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
                self.assertEqual(asyncio.run(turnos_com_efeito(r, p)), dado)
                self.assertNotIn("velocidade_rodadas", p)
                self.assertNotIn("velocidade_nova", p)

    def test_movimento_dobra_no_turno_do_cast(self):
        r, p = sala(3)
        p["moves_left"] = 4
        asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
        self.assertEqual(p["moves_left"], 8)

    def test_recast_com_efeito_ativo_nao_dobra_de_novo(self):
        r, p = sala(3)
        p["moves_left"] = 4
        asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
        asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
        self.assertEqual(p["moves_left"], 8)
        self.assertEqual(p["velocidade_rodadas"], 3)

    def test_cast_sem_movimento_sobrando_nao_cria_movimento(self):
        r, p = sala(2)
        p["moves_left"] = 0
        asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
        self.assertEqual(p["moves_left"], 0)

    def test_extra_continua_livre_no_turno_do_cast(self):
        r, p = sala(2)
        p["moves_left"] = 6; p["action_done"] = True
        asyncio.run(r._executar_velocidade(p, S.GRIMORIO["velocidade"], 0))
        self.assertFalse(r._acao_bloqueada(p))


if __name__ == "__main__":
    unittest.main()
