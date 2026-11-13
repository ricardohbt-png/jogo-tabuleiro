"""Sala trancada sem porta nunca abriria: o jogo a destranca ao carregar o mapa e ao continuar uma foto.
Roda da raiz: python -X utf8 tools/test_sala_trancada_sem_porta.py"""
import asyncio
import copy
import json
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def mapa(arq="elara_graciero_beco.json"):
    with open(os.path.join(RAIZ, "dungeons", arq), encoding="utf-8") as f:
        return json.load(f)


def sala_de_jogo():
    r = S.GameRoom("TRANCA")
    r.players["p0"] = S.make_player("p0", "H", "warrior", 0)
    r.host_pid = "p0"; r.phase = "playing"

    async def nada(*a, **k): pass
    r.send_to = nada; r.broadcast = nada; r.push_state_or_city = nada; r.push_state = nada; r.gm_say = nada
    r._checkpoint_savegame = lambda: None
    return r


class CarregarTests(unittest.TestCase):
    def test_sala_trancada_sem_porta_nasce_destrancada(self):
        d = mapa()
        for x in d["rooms"]:
            x["doors"] = []
            if x.get("role") != "entrance":
                x["locked"] = True
        r = sala_de_jogo()
        r.load_authored_dungeon(d)
        self.assertFalse(any(x["locked"] for x in r.rooms))

    def test_sala_com_porta_continua_trancada(self):
        d = mapa()
        alvo = next(x for x in d["rooms"] if x.get("role") != "entrance")
        outra = next(x for x in d["rooms"] if x.get("role") != "entrance" and x is not alvo)
        alvo["locked"] = outra["locked"] = True
        alvo["doors"] = [[alvo["x"], alvo["y"]]]
        outra["doors"] = []
        r = sala_de_jogo()
        r.load_authored_dungeon(d)
        estado = {x["id"]: x["locked"] for x in r.rooms}
        self.assertTrue(estado[alvo["id"]])
        self.assertFalse(estado[outra["id"]])

    def test_monstro_da_sala_sem_porta_age(self):
        r = sala_de_jogo()
        r.load_authored_dungeon(mapa())
        m = next(m for m in r.monsters.values() if m.get("room_id") == 4)
        self.assertTrue(r._monstro_ativo_em_combate(m))

    def test_mapas_afetados(self):
        for arq in ("elara_graciero_beco.json", "charcos_4a_arredores.json"):
            r = sala_de_jogo()
            r.load_authored_dungeon(mapa(arq))
            self.assertFalse(any(x["locked"] for x in r.rooms), arq)


class FotoTests(unittest.TestCase):
    def _foto(self, sala):
        return {"sala": sala, "herois": {}, "pids": {}}

    def test_foto_antiga_destranca_sala_sem_porta(self):
        d = mapa()
        r = sala_de_jogo()
        r.load_authored_dungeon(d)
        salas = copy.deepcopy(r.rooms)
        for x in salas:
            x["locked"] = x.get("role") != "entrance"
        r._foto_aplicar_sala(self._foto({"rooms": salas, "door_rooms": {}}), {}, d)
        self.assertFalse(any(x["locked"] for x in r.rooms))

    def test_foto_conserva_tranca_de_sala_com_porta(self):
        d = mapa()
        r = sala_de_jogo()
        r.load_authored_dungeon(d)
        salas = copy.deepcopy(r.rooms)
        alvo = next(x for x in salas if x.get("role") != "entrance")
        alvo["locked"] = True
        r._foto_aplicar_sala(self._foto({"rooms": salas, "door_rooms": {(5, 5): [alvo["id"]]}}), {}, d)
        self.assertTrue(next(x for x in r.rooms if x["id"] == alvo["id"])["locked"])

    def test_foto_sem_indice_de_portas_nao_destranca(self):
        d = mapa()
        r = sala_de_jogo()
        r.load_authored_dungeon(d)
        salas = copy.deepcopy(r.rooms)
        alvo = next(x for x in salas if x.get("role") != "entrance")
        alvo["locked"] = True
        r._foto_aplicar_sala(self._foto({"rooms": salas}), {}, d)
        self.assertTrue(next(x for x in r.rooms if x["id"] == alvo["id"])["locked"])


class EditorTests(unittest.TestCase):
    def test_editor_avisa_e_o_aviso_tem_traducao(self):
        with open(os.path.join(RAIZ, "tools", "editor.js"), encoding="utf-8") as f:
            js = f.read()
        self.assertIn("ui.editor.masmorra.design.r7", js)
        with open(os.path.join(RAIZ, "src", "lang", "editor.js"), encoding="utf-8") as f:
            lang = f.read()
        bloco = re.search(r'"ui\.editor\.masmorra\.design\.r7":\s*\{(.*?)\n\s*\}', lang, re.S)
        self.assertIsNotNone(bloco)
        self.assertIn('"en"', bloco.group(1))
        self.assertIn('"pt"', bloco.group(1))


if __name__ == "__main__":
    unittest.main(verbosity=1)
