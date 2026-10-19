"""Janela pessoal ao entrar no Silêncio; sem mudar regras de área/imunidade."""
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class AvisosSilencio(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = server.GameRoom("SILENCIO_TEST")
        self.room.phase = "playing"
        self.room.round_num = 3
        self.hero = server.make_player("h1", "Teste", "mage", 0)
        self.hero.update(pos=[3, 3], alive=True)
        self.room.players = {"h1": self.hero}
        self.sent = []
        async def capture(pid, msg): self.sent.append((pid, msg))
        async def noop(*args, **kwargs): pass
        self.room.send_to = capture
        self.room.broadcast = noop
        self.room.gm_say = noop

    def zone(self, duration=4, **extra):
        z = dict(id="z1", tipo="silencio", cx=3, cy=3, lado=4,
                 duracao=duration, ativa=True)
        z.update(extra)
        self.room.zonas_especiais.append(z)
        return z

    def notices(self):
        return [(pid, m) for pid, m in self.sent if m.get("tipo") == "silencio"]

    async def test_entrada_por_push_privada_e_duracao(self):
        self.zone(4)
        await self.room.push_state()
        self.assertEqual(len(self.notices()), 1)
        pid, msg = self.notices()[0]
        self.assertEqual(pid, "h1")
        self.assertEqual(msg["duracao"], 4)
        self.assertEqual(msg["imagem"], "silencio.png")

    async def test_ticks_nao_repetem_sair_e_reentrar_avisa(self):
        z = self.zone(4)
        await self.room._avisar_silencio()
        z["duracao"] = 3
        await self.room._avisar_silencio()
        self.assertEqual(len(self.notices()), 1)
        self.hero["pos"] = [1, 3]  # Fora: o quadrado 4x4 vai de 2 a 5.
        await self.room._avisar_silencio()
        self.hero["pos"] = [5, 3]  # A borda ainda pertence à área.
        await self.room._avisar_silencio()
        self.assertEqual(len(self.notices()), 2)
        self.assertEqual(self.notices()[-1][1]["duracao"], 3)

    async def test_imunidade_respeitada_e_fim_da_imunidade(self):
        self.zone()
        self.hero["imune_silencio_ate"] = 3
        await self.room._avisar_silencio()
        self.assertFalse(self.notices())
        self.room.round_num = 4
        await self.room._avisar_silencio()
        self.assertEqual(len(self.notices()), 1)

    async def test_sobreposicao_usa_maior_duracao_sem_duplicar(self):
        self.zone(2)
        self.zone(5, id="z2")
        self.zone(99, id="fora", cx=20, cy=20)
        await self.room._avisar_silencio()
        self.assertEqual(self.notices()[0][1]["duracao"], 5)
        self.zone(8, id="z3")
        await self.room._avisar_silencio()
        self.assertEqual(len(self.notices()), 1)

    async def test_zona_inativa_fora_da_area_morto_cidade(self):
        z = self.zone(4, ativa=False)
        await self.room._avisar_silencio()
        z["ativa"] = True
        self.hero["pos"] = [6, 3]
        await self.room._avisar_silencio()
        self.hero["pos"] = [3, 3]
        self.hero["alive"] = False
        await self.room._avisar_silencio()
        self.hero["alive"] = True
        self.hero["fora_masmorra"] = True
        await self.room._avisar_silencio()
        self.assertFalse(self.notices())

    async def test_xama_cria_zona_sobre_heroi_parado(self):
        self.room._rolar_dado = lambda *args: 3
        await self.room._xama_silencio({"id": "x1", "name": "Xamã"}, [3, 3])
        await self.room.push_state()
        self.assertTrue(self.room._em_silencio(self.hero))
        self.assertEqual(self.notices()[0][1]["duracao"], 3)
        self.room.zonas_especiais.clear()
        await self.room._avisar_silencio()
        self.assertFalse(self.room._em_silencio(self.hero))


if __name__ == "__main__":
    unittest.main()
