"""Amaldiçoar do xamã: aviso privado, arte existente e duração autoritativa."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class AvisoAmaldicoarXama(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = server.GameRoom("XAMA_AVISO_TEST")
        self.room.phase = "playing"
        self.room._rolar_dado = lambda *a: 3
        self.sent = []
        async def capture(pid, msg): self.sent.append((pid, msg))
        async def noop(*a, **k): pass
        self.room.send_to = capture
        self.room.broadcast = noop
        self.room.gm_say = noop
        self.monster = {"id": "x1", "name": "Xamã"}

    def hero(self, pid, pos, alive=True):
        p = server.make_player(pid, pid, "warrior", 0)
        p.update(pos=list(pos), alive=alive)
        self.room.players[pid] = p
        return p

    async def test_apenas_herois_atingidos_recebem_imagem_e_efeitos(self):
        p = self.hero("h1", [3, 3])
        self.hero("h2", [4, 4])
        outside = self.hero("fora", [5, 3])
        self.hero("morto", [3, 3], False)
        await self.room._xama_amaldicoar(self.monster, [3, 3])
        self.assertEqual({pid for pid, _ in self.sent}, {"h1", "h2"})
        self.assertEqual(len(self.sent), 2)
        msg = self.sent[0][1]
        self.assertEqual(msg["type"], "trap_result")
        self.assertEqual(msg["tipo_id"], "amaldicoar_xama")
        self.assertEqual(msg["imagem"], "amaldicoado.png")
        self.assertEqual(msg["duracao"], 3)
        self.assertEqual(p["mods_magia"], dict(ataque=-1, dano=-1, ca=-1, resistencia=-1, rodadas=3))
        self.assertFalse(outside.get("mods_magia"))
        for lang in ("pt", "en"):
            rendered = [str(server._t_render(e, lang)) for e in msg["efeitos_extra"]]
            self.assertTrue(any("3" in e for e in rendered))
            self.assertTrue(any("-1" in e for e in rendered))
            self.assertTrue(any("automatic" in e.lower() for e in rendered))

    async def test_duracao_do_aviso_respeita_modificador_mais_longo(self):
        p = self.hero("h1", [3, 3])
        self.room._set_mod_magia(p, {"ataque": 1}, 7)
        await self.room._xama_amaldicoar(self.monster, [3, 3])
        self.assertEqual(p["mods_magia"]["rodadas"], 7)
        self.assertEqual(self.sent[0][1]["duracao"], 7)
        await self.room.push_state()
        await self.room.push_state()
        self.assertEqual(len(self.sent), 1, "Atualização do estado não repete a janela")


if __name__ == "__main__":
    unittest.main()
