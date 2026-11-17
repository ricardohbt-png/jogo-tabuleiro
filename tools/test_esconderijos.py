"""Esconderijos: objeto com conteúdo escondido só aparece depois que um herói o nota.
Roda da raiz: python -X utf8 tools/test_esconderijos.py"""
import asyncio
import json
import os
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import esconder_tesouros as E


def mapa_minimo(escondido=True, cd=13):
    tiles = [[0] * 7] + [[0] + [1] * 5 + [0] for _ in range(5)] + [[0] * 7]
    dec = {"id": "barril_x", "type": "barril", "pos": [5, 1], "facing": [0, 1],
           "loot": {"gold": 7, "items": [{"id": "espada_magica"}]}}
    if escondido:
        dec.update({"escondido": True, "cd_busca": cd})
    return {"schema_version": 1, "name": "teste", "grid": {"w": 7, "h": 7}, "tiles": tiles,
            "entrance": {"x": 1, "y": 1},
            "rooms": [{"id": 0, "x": 1, "y": 1, "w": 5, "h": 5, "role": "entrance"}],
            "monsters": [], "decorations": [dec]}


def sala(defn, classe="warrior"):
    r = S.GameRoom("ESC")
    r.players["p0"] = S.make_player("p0", "Heroi", classe, 0)
    r.host_pid = "p0"; r.phase = "playing"
    r.load_authored_dungeon(defn)
    r.players["p0"]["pos"] = [1, 1]
    r.falas_enviadas, r.erros = [], []

    async def gm_say(t): r.falas_enviadas.append(str(t))
    async def send_to(pid, msg): r.erros.append(msg)
    async def nada(*a, **k): pass
    r.gm_say = gm_say; r.send_to = send_to; r.push_state = nada; r.broadcast = nada
    return r


def serial(r, did="barril_x"):
    return next(d for d in r._serializar_decoracoes() if d["id"] == did)


class MecanicaTests(unittest.TestCase):
    def test_validador(self):
        self.assertTrue(S.validar_dungeon(mapa_minimo())[0])
        sem_loot = mapa_minimo(); sem_loot["decorations"][0]["loot"] = None
        self.assertFalse(S.validar_dungeon(sem_loot)[0])
        cd_ruim = mapa_minimo(cd=99)
        self.assertFalse(S.validar_dungeon(cd_ruim)[0])

    def test_escondido_nao_aparece_nem_abre(self):
        r = sala(mapa_minimo())
        self.assertFalse(serial(r)["tem_loot"], "o 💰 não pode vazar")
        r.players["p0"]["pos"] = [4, 1]
        asyncio.run(r.handle_take_from_decor("p0", "barril_x", "gold", 0))
        self.assertEqual(r.decorations[0]["loot"]["gold"], 7, "não dá para pegar sem achar")

    def test_sem_escondido_continua_igual(self):
        r = sala(mapa_minimo(escondido=False))
        self.assertTrue(serial(r)["tem_loot"])
        self.assertNotIn("escondido", r.decorations[0])

    def test_achar_ao_passar_ao_lado(self):
        r = sala(mapa_minimo())
        r.players["p0"]["pos"] = [4, 2]
        with mock.patch.object(S.random, "randint", return_value=20):
            asyncio.run(r._procurar_esconderijos(r.players["p0"]))
        self.assertTrue(serial(r)["tem_loot"])
        self.assertTrue(any("barril" in f.lower() or "nota" in f.lower() for f in r.falas_enviadas))
        asyncio.run(r.handle_take_from_decor("p0", "barril_x", "item", 0))
        self.assertEqual(r.decorations[0]["loot"]["items"], [])

    def test_longe_nao_procura(self):
        r = sala(mapa_minimo())
        r.players["p0"]["pos"] = [1, 1]
        with mock.patch.object(S.random, "randint", return_value=20):
            asyncio.run(r._procurar_esconderijos(r.players["p0"]))
        self.assertFalse(serial(r)["tem_loot"])
        self.assertEqual(r.decorations[0]["buscado_por"], [])

    def test_uma_tentativa_por_heroi_e_falha_silenciosa(self):
        r = sala(mapa_minimo(cd=30))
        r.players["p0"]["pos"] = [4, 2]
        with mock.patch.object(S.random, "randint", return_value=1) as rnd:
            asyncio.run(r._procurar_esconderijos(r.players["p0"]))
            asyncio.run(r._procurar_esconderijos(r.players["p0"]))
        self.assertEqual(rnd.call_count, 1, "só um teste por herói e objeto")
        self.assertEqual(r.falas_enviadas, [], "a falha não pode denunciar o esconderijo")
        self.assertFalse(serial(r)["tem_loot"])

    def test_ladino_ganha_bonus(self):
        alvo = None
        for classe, esperado in (("warrior", False), ("rogue", True)):
            r = sala(mapa_minimo(), classe)
            p = r.players["p0"]; p["pos"] = [4, 2]
            alvo = r.decorations[0]["cd_busca"] - (r._get_percepcao_heroi(p) - 10) - 1
            with mock.patch.object(S.random, "randint", return_value=alvo):
                asyncio.run(r._procurar_esconderijos(p))
            self.assertEqual(serial(r)["tem_loot"], esperado, classe)

    def test_passo_real_procura(self):
        r = sala(mapa_minimo())
        r.players["p0"]["pos"] = [3, 1]
        r.players["p0"]["moves_left"] = 6
        r._is_turn = lambda pid: True
        with mock.patch.object(S.random, "randint", return_value=20):
            asyncio.run(r.handle_move("p0", 1, 0))
        self.assertEqual(r.players["p0"]["pos"], [4, 1])
        self.assertTrue(r.decorations[0].get("encontrado"))


class DadosTests(unittest.TestCase):
    def test_todos_os_esconderijos_existem_e_estao_ocultos(self):
        for mapa, did, tipo, cd, ouro, itens in E.ESCONDERIJOS:
            with open(os.path.join(S.DUNGEONS_DIR, f"{mapa}.json"), encoding="utf-8") as f:
                defn = json.load(f)
            d = next((x for x in defn.get("decorations", []) if x.get("id") == did), None)
            self.assertIsNotNone(d, f"{mapa}:{did}")
            self.assertEqual(d["type"], tipo)
            self.assertTrue(d.get("escondido"), f"{mapa}:{did}")
            self.assertEqual([i["id"] for i in d["loot"]["items"]], itens)
            self.assertTrue(S.validar_dungeon(defn)[0], mapa)
            r = sala(defn)
            self.assertFalse(serial(r, did)["tem_loot"], f"{mapa}:{did} vaza o 💰")

    def test_script_e_idempotente(self):
        self.assertEqual(len(E.aplicar(simular=True)), len(E.ESCONDERIJOS))

    def test_editor_preserva_os_campos(self):
        with open(os.path.join(RAIZ, "tools", "editor.js"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("o.escondido = true", src)
        self.assertIn("escondido: true, cd_busca", src)


if __name__ == "__main__":
    unittest.main()
