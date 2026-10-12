"""Regressões do protocolo de marcadores cooperativos em masmorras."""
import asyncio
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


class MarcadoresCooperativosTests(unittest.IsolatedAsyncioTestCase):
    async def create_marker(self, sala, *args, **kwargs):
        handler = getattr(sala, "handle_cooperative_marker", None)
        self.assertTrue(callable(handler), "GameRoom ainda não implementa handle_cooperative_marker")
        return await handler(*args, **kwargs)

    async def set_shared_vision(self, sala, *args, **kwargs):
        handler = getattr(sala, "handle_cooperative_vision_preference", None)
        self.assertTrue(callable(handler), "GameRoom ainda não sincroniza a preferência de visão")
        return await handler(*args, **kwargs)

    def nova_sala(self):
        sala = S.GameRoom("MARKERS-TEST")
        sala.phase = "playing"
        sala.map_w = sala.map_h = 20
        sala.tiles = [[S.FLOOR] * 20 for _ in range(20)]
        sala.rooms = []
        sala.opened_doors = set()
        sala.explored = {(x, y) for y in range(20) for x in range(20)}
        sala.players = {
            "p1": S.make_player("p1", "Ana", "warrior", 0),
            "p2": S.make_player("p2", "Bia", "mage", 1),
        }
        sala.players["p1"]["pos"] = [2, 2]
        sala.players["p2"]["pos"] = [17, 17]
        sala.connections = {"p1": object(), "p2": object()}
        sala.monsters = {
            "m1": {"id": "m1", "type": "skeleton", "name": "Esqueleto",
                   "pos": [5, 2], "hp": 8, "max_hp": 8},
            "m2": {"id": "m2", "type": "skeleton", "name": "Outro",
                   "pos": [12, 12], "hp": 8, "max_hp": 8},
        }
        sala._tem_linha_de_visao = lambda a, b, ignorar_objetos=False: True
        sala._tall_oclui_caminho = lambda *args: False

        async def noop(*args, **kwargs):
            return None
        sala.push_state = noop
        return sala

    async def test_marca_casa_visivel_e_substitui_marca_do_mesmo_jogador(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))
        await asyncio.sleep(0.26)
        self.assertTrue(await self.create_marker(sala, "p1", "move", "tile", pos=[3, 3]))
        markers = sala._cooperative_markers_for_pid("p1")
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["category"], "move")
        self.assertEqual(markers[0]["pos"], [3, 3])

    async def test_rejeita_categoria_e_posicao_invalidas_sem_alterar_estado(self):
        sala = self.nova_sala()
        for category, pos in (("teleport", [4, 2]), ("danger", [-1, 2]),
                              ("danger", [20, 2]), ("danger", [4, 2])):
            if pos == [4, 2]:
                sala.tiles[2][4] = S.WALL
            self.assertFalse(await self.create_marker(sala, "p1", category, "tile", pos=pos))
        self.assertEqual(sala.cooperative_markers, {})

    async def test_marca_inimigo_exige_alvo_vivo_existente_e_visivel(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        self.assertFalse(await self.create_marker(sala, "p1", "attack", "enemy", target_id="missing"))
        sala.monsters["m1"]["hp"] = 0
        self.assertFalse(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        self.assertFalse(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m2"))

    async def test_destinatario_sem_visao_nao_recebe_id_ou_posicao_oculta(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        self.assertEqual(len(sala._cooperative_markers_for_pid("p1")), 1)
        self.assertEqual(sala._cooperative_markers_for_pid("p2"), [])

    async def test_visao_compartilhada_reportada_habilita_recebimento_e_pode_ser_desligada(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        await self.set_shared_vision(sala, "p2", True)
        self.assertEqual(len(sala._cooperative_markers_for_pid("p2")), 1)
        await self.set_shared_vision(sala, "p2", False)
        self.assertEqual(sala._cooperative_markers_for_pid("p2"), [])

    async def test_hero_extra_nao_pode_marcar_por_outra_conexao(self):
        sala = self.nova_sala()
        sala.players["p1"]["controlador"] = "conn1"
        sala.players["p2"]["controlador"] = "conn2"
        self.assertFalse(await self.create_marker(sala,
            "conn2", "danger", "tile", pos=[4, 2], hero_id="p1"))
        self.assertEqual(sala.cooperative_markers, {})

    async def test_limite_de_frequencia_rejeita_spam_sem_mudar_marcacao(self):
        sala = self.nova_sala()
        sala._cooperative_marker_last_at = {"p1": time.monotonic() + 5}
        self.assertFalse(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))
        self.assertEqual(sala.cooperative_markers, {})

    async def test_desconectar_conexao_remove_marcas_e_preferencia(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))
        await self.set_shared_vision(sala, "p1", True)
        sala._clear_cooperative_markers_for_connection("p1")
        self.assertEqual(sala.cooperative_markers, {})
        self.assertNotIn("p1", sala.cooperative_vision_preferences)


if __name__ == "__main__":
    unittest.main(verbosity=2)
