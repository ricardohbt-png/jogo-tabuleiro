"""O catálogo da Guilda viaja também no game_state (quem entra direto na masmorra não passa pelo
city_state): sem ele os botões das técnicas, inclusive as concedidas por itens, somem do HUD.
Roda da raiz: python -X utf8 tools/test_guild_catalog_game_state.py"""
import asyncio
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S


class FakeWS:
    def __init__(self): self.msgs = []
    async def send(self, data): self.msgs.append(json.loads(data))


def sala():
    r = S.GameRoom("GCAT"); r.phase = "playing"
    d = json.load(open(os.path.join(RAIZ, "dungeons", "calabouco_morte.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    p = S.make_player("p0", "Heroi", "warrior", 0)
    p["pos"] = [d["entrance"]["x"], d["entrance"]["y"]]
    r.players["p0"] = p; r.host_pid = "p0"
    r.connections["p0"] = FakeWS()
    return r


def estados(r):
    return [m for m in r.connections["p0"].msgs if m.get("type") == "game_state"]


class CatalogoNoEstadoTests(unittest.TestCase):
    def test_payload_traz_o_catalogo_com_o_ataque_giratorio(self):
        r = sala()
        cat = r._game_state_payload()["guild_catalog"]
        self.assertTrue(any(i["id"] == "tecnica_ataque_giratorio" for i in cat))
        self.assertEqual(len(cat), len(S.GUILD_CATALOG))

    def test_e_um_campo_diferivel(self):
        self.assertIn("guild_catalog", S.ESTADO_DIFERIVEL)

    def test_primeiro_envio_leva_e_o_seguinte_omite(self):
        r = sala()
        asyncio.run(r.push_state())
        asyncio.run(r.push_state())
        a, b = estados(r)[:2]
        self.assertIn("guild_catalog", a)
        self.assertNotIn("guild_catalog", b)
        self.assertIn("guild_catalog", b.get("diferidos", []))

    def test_voltar_da_cidade_reenvia(self):
        r = sala()
        asyncio.run(r.push_state())
        asyncio.run(r.broadcast_city_state())     # limpa o cache de envio da conexão
        asyncio.run(r.push_state())
        ultimo = estados(r)[-1]
        self.assertIn("guild_catalog", ultimo)


if __name__ == "__main__":
    unittest.main()
