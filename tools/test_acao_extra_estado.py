"""A ação principal extra (Velocidade/Oportunidade) aparece como livre no estado enviado
ao cliente, que só libera ataque e habilidades quando `action_done` é falso.
Roda da raiz: python -X utf8 tools/test_acao_extra_estado.py"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S


def sala():
    tiles = [[0] * 5] + [[0, 1, 1, 1, 0] for _ in range(3)] + [[0] * 5]
    defn = {"schema_version": 1, "name": "t", "grid": {"w": 5, "h": 5}, "tiles": tiles,
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": 0, "x": 1, "y": 1, "w": 3, "h": 3, "role": "entrance"}],
            "monsters": [], "decorations": []}
    r = S.GameRoom("EXT")
    r.players["p0"] = S.make_player("p0", "Heroi", "warrior", 0)
    r.host_pid = "p0"; r.phase = "playing"
    r.load_authored_dungeon(defn)
    return r


def estado(r):
    return next(p for p in r._game_state_payload()["players"] if p["id"] == "p0")


class AcaoExtraTests(unittest.TestCase):
    def test_sem_efeito_action_done_e_o_real(self):
        r = sala(); p = r.players["p0"]
        p["action_done"] = True
        self.assertTrue(estado(r)["action_done"])
        self.assertFalse(estado(r)["acao_extra_disponivel"])
        p["action_done"] = False
        self.assertFalse(estado(r)["action_done"])

    def test_velocidade_com_acao_extra_pendente_aparece_livre(self):
        r = sala(); p = r.players["p0"]
        p.update(action_done=True, velocidade_rodadas=3, velocidade_extra_usada=False)
        e = estado(r)
        self.assertFalse(e["action_done"], "o cliente precisa liberar o ataque")
        self.assertTrue(e["acao_extra_disponivel"])
        self.assertTrue(p["action_done"], "o estado do servidor não é alterado")

    def test_depois_de_gastar_a_extra_volta_a_ficar_usada(self):
        r = sala(); p = r.players["p0"]
        p.update(action_done=True, velocidade_rodadas=3, velocidade_extra_usada=True)
        e = estado(r)
        self.assertTrue(e["action_done"])
        self.assertFalse(e["acao_extra_disponivel"])

    def test_ciclo_completo_dois_ataques_no_turno(self):
        r = sala(); p = r.players["p0"]
        p.update(action_done=False, velocidade_rodadas=3, velocidade_extra_usada=False)
        self.assertFalse(r._acao_bloqueada(p))       # 1ª ação principal
        p["action_done"] = True
        self.assertFalse(estado(r)["action_done"])   # cliente vê a extra livre
        self.assertFalse(r._acao_bloqueada(p))       # servidor consome a extra
        p["action_done"] = True
        self.assertTrue(estado(r)["action_done"])    # agora acabou
        self.assertTrue(r._acao_bloqueada(p))

    def test_oportunidade_so_na_rodada_do_credito(self):
        r = sala(); p = r.players["p0"]
        p.update(action_done=True, oportunidade_credito=True, oportunidade_round=r.round_num)
        self.assertFalse(estado(r)["action_done"])
        p["oportunidade_round"] = r.round_num + 1
        self.assertTrue(estado(r)["action_done"])


if __name__ == "__main__":
    unittest.main()
