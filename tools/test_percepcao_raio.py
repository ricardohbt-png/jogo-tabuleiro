"""Percepção por raio: esconderijos e armadilhas escondidas são notados a até metade da
visão (com linha de visão), com teste ao entrar no raio e de novo a 2 e a 1 casa.
Roda da raiz: python -X utf8 tools/test_percepcao_raio.py"""
import asyncio
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S


def mapa(cd=13):
    """Corredor estreito 1x12: entrada no x=1, barril escondido no x=11."""
    w = 14
    tiles = [[0] * w, [0] + [1] * 12 + [0], [0] * w]
    dec = {"id": "barril_x", "type": "barril", "pos": [11, 1], "facing": [0, 1],
           "loot": {"gold": 7, "items": [{"id": "espada_magica"}]}, "escondido": True, "cd_busca": cd}
    return {"schema_version": 1, "name": "corredor", "grid": {"w": w, "h": 3}, "tiles": tiles,
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": 0, "x": 1, "y": 1, "w": 12, "h": 1, "role": "entrance"}],
            "monsters": [], "decorations": [dec]}


def sala(classe="warrior", cd=13):
    r = S.GameRoom("PER")
    r.players["p0"] = S.make_player("p0", "Heroi", classe, 0)
    r.host_pid = "p0"; r.phase = "playing"
    r.load_authored_dungeon(mapa(cd))
    r.falas, r.erros = [], []

    async def gm_say(t): r.falas.append(str(t))
    async def send_to(pid, msg): r.erros.append(msg)
    async def nada(*a, **k): pass
    r.gm_say = gm_say; r.send_to = send_to; r.push_state = nada; r.broadcast = nada
    return r


def andar(r, x, rolagem):
    p = r.players["p0"]; p["pos"] = [x, 1]
    with mock.patch.object(S.random, "randint", return_value=rolagem):
        asyncio.run(r._procurar_esconderijos(p))


class RaioTests(unittest.TestCase):
    def test_raio_e_metade_da_visao(self):
        r = sala("mage")
        p = r.players["p0"]
        self.assertEqual(r._raio_percepcao(p), (r._get_raio_visao(p) + 1) // 2)
        self.assertEqual(r._faixas_percepcao(4), [4, 2, 1])
        self.assertEqual(r._faixas_percepcao(3), [3, 2, 1])
        self.assertEqual(r._faixas_percepcao(1), [1])

    def test_fora_do_raio_nao_testa(self):
        r = sala("warrior")
        raio = r._raio_percepcao(r.players["p0"])
        andar(r, 11 - raio - 1, 20)
        self.assertTrue(r.decorations[0].get("escondido") and not r.decorations[0].get("encontrado"))
        self.assertFalse(r.decorations[0].get("buscado_por"))

    def test_acha_de_longe_dentro_do_raio(self):
        r = sala("mage", cd=5)
        raio = r._raio_percepcao(r.players["p0"])
        andar(r, 11 - raio, 20)
        self.assertTrue(r.decorations[0].get("encontrado"))

    def test_reteste_so_nas_faixas_2_e_1(self):
        r = sala("mage", cd=30)                    # nunca passa: só queremos contar rolagens
        p = r.players["p0"]; raio = r._raio_percepcao(p)
        self.assertGreaterEqual(raio, 3)
        rolagens = []
        orig = S.random.randint
        def contar(a, b):
            rolagens.append(1); return 1
        with mock.patch.object(S.random, "randint", contar):
            for x in range(11 - raio, 11):
                p["pos"] = [x, 1]
                asyncio.run(r._procurar_esconderijos(p))
                p["pos"] = [x, 1]
                asyncio.run(r._procurar_esconderijos(p))      # andar no mesmo lugar não repete
        self.assertEqual(len(rolagens), len(r._faixas_percepcao(raio)))

    def test_penalidade_por_distancia(self):
        r = sala("warrior", cd=12)
        p = r.players["p0"]; raio = r._raio_percepcao(p)
        bonus = r._get_percepcao_heroi(p) - 10
        dist = raio
        # rolagem justa para passar a distância 1 mas falhar a distância `raio` (>1)
        passa_perto = 12 - bonus
        andar(r, 11 - dist, passa_perto)
        self.assertFalse(r.decorations[0].get("encontrado"), "a distância penaliza")
        andar(r, 10, passa_perto)                              # adjacente: sem penalidade
        self.assertTrue(r.decorations[0].get("encontrado"))

    def test_sem_linha_de_visao_nao_testa(self):
        r = sala("mage", cd=5)
        r.tiles[1][9] = S.WALL
        andar(r, 7, 20)
        self.assertFalse(r.decorations[0].get("encontrado"))

    def test_save_antigo_com_lista_nao_repete(self):
        r = sala("mage", cd=30)
        r.decorations[0]["buscado_por"] = ["mage"]
        andar(r, 10, 20)
        self.assertFalse(r.decorations[0].get("encontrado"))

    def test_ladino_com_detectar_acha_sem_rolar(self):
        r = sala("rogue", cd=30)
        p = r.players["p0"]; p["detectar_ativo"] = True
        andar(r, 11 - r._get_raio_visao(p), 1)
        self.assertTrue(r.decorations[0].get("encontrado"))


class ArmadilhaTests(unittest.TestCase):
    def sala_com_armadilha(self, classe="warrior"):
        r = sala(classe)
        r.decorations.clear()
        r.armadilhas.append({"id": "t1", "tipo": "armadilha_urso", "pos": [11, 1], "ativada": False})
        return r

    def serial(self, r):
        return next(a for a in r._serializar_armadilhas() if a["id"] == "t1")

    def test_escondida_no_inicio(self):
        r = self.sala_com_armadilha()
        self.assertFalse(self.serial(r)["visivel"])

    def test_percepcao_comum_deixa_so_suspeita(self):
        r = self.sala_com_armadilha("mage")
        andar(r, 10, 20)
        s = self.serial(r)
        self.assertTrue(s["suspeita"] and s["visivel"])
        self.assertEqual(s["tipo"], "suspeita")
        self.assertNotIn("Urso", s["nome"].__str__())
        self.assertTrue(any("desconfia" in f for f in r.falas))

    def test_cd_da_armadilha_conta(self):
        r = self.sala_com_armadilha("mage")
        bonus = r._get_percepcao_heroi(r.players["p0"]) - 10
        andar(r, 10, 10 - bonus - 1)       # d20 + bonus = 9 < CD 10 da armadilha de urso
        self.assertFalse(self.serial(r)["visivel"])

    def test_detectar_armadilhas_identifica(self):
        r = self.sala_com_armadilha("rogue")
        r.armadilhas[0]["suspeita"] = True
        r._revelar_armadilhas_raio(r.players["p0"], 12)
        s = self.serial(r)
        self.assertEqual(s["tipo"], "armadilha_urso")
        self.assertFalse(s["suspeita"])

    def test_aliada_e_ativada_nao_entram(self):
        r = self.sala_com_armadilha("mage")
        r.armadilhas[0]["criador"] = "p0"
        self.assertEqual(r._alvos_de_percepcao(r.players["p0"], 12), [])

    def test_armadilha_em_objeto_revela_marcador(self):
        r = sala("mage")
        d = r.decorations[0]
        d.pop("escondido", None)
        d["trap"] = {"tipo": "armadilha_urso"}
        andar(r, 10, 20)
        self.assertTrue(d.get("trap_revealed"))
        self.assertTrue(any("armadilhado" in f for f in r.falas))


if __name__ == "__main__":
    unittest.main()
