"""Conversa de cena que grava vários fatos (`efeito.fatos`).
Roda da raiz: python -X utf8 tools/test_conversa_fatos.py"""
import asyncio
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402

CID, CENA, NPC = "alva_e_luz", "cena_fatos_teste", "npc_t"


def sala():
    r = S.GameRoom("FATOS")
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.host_pid = "p1"; r.phase = "city"; r.world_location = CID
    r.enviados = []

    async def send_to(pid, msg): r.enviados.append(msg)

    async def broadcast(msg, skip=None, personalize=None): pass

    async def push(): pass
    r.send_to = send_to; r.broadcast = broadcast; r.push_state_or_city = push
    r._checkpoint_savegame = lambda: None
    return r


class FatosTests(unittest.TestCase):
    def setUp(self):
        self._antes = copy.deepcopy(S.CITY_SCENES.get(CID, {}))
        convs = S._clean_scene_conversations([
            {"id": "c1", "texto": "oi", "efeito": {"fato": "a", "fatos": ["b", "c"]}},
            {"id": "c2", "texto": "tchau", "efeito": {"fato": "z"}}])
        S.CITY_SCENES[CID][CENA] = {"nome": "t", "background": "", "art_ratio": 1.5, "mode": "individual",
                                    "mask": "", "slots": [{"id": NPC, "name": "N", "image": "", "x": 0, "y": 0,
                                                           "w": 10, "h": 10, "z": 1, "dialog": "", "conversations": convs}]}

    def tearDown(self):
        S.CITY_SCENES[CID] = self._antes

    def test_limpa_e_limita(self):
        c = S._clean_scene_conversations([{"id": "x", "texto": "t", "efeito": {
            "fatos": [" a ", "", 5, "b" * 101, "c", "d", "e", "f", "g", "h"]}}])[0]["efeito"]
        self.assertEqual(c["fatos"], ["a", "c", "d", "e", "f", "g"], "texto válido, até 6, sem lixo")
        antiga = S._clean_scene_conversations([{"id": "x", "texto": "t", "efeito": {"fato": "a"}}])[0]["efeito"]
        self.assertNotIn("fatos", antiga, "conversa antiga fica idêntica")
        vazia = S._clean_scene_conversations([{"id": "x", "texto": "t", "efeito": {"fatos": []}}])[0]["efeito"]
        self.assertNotIn("fatos", vazia)

    def test_conversa_grava_todos_os_fatos(self):
        r = sala()
        asyncio.run(r.handle_scene_npc("p1", CENA, NPC, "c1"))
        self.assertTrue({"a", "b", "c"} <= r.fatos)
        self.assertNotIn("z", r.fatos)

    def test_conversa_antiga_continua_gravando_so_o_dela(self):
        r = sala()
        asyncio.run(r.handle_scene_npc("p1", CENA, NPC, "c2"))
        self.assertEqual(r.fatos, {"z"})

    def test_uso_unico_ainda_vale(self):
        r = sala()
        asyncio.run(r.handle_scene_npc("p1", CENA, NPC, "c1"))
        r.fatos.clear()
        asyncio.run(r.handle_scene_npc("p1", CENA, NPC, "c1"))
        self.assertEqual(r.fatos, set(), "segunda vez é recusada, nada é gravado")


if __name__ == "__main__":
    unittest.main()
