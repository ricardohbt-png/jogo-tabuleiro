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

    async def test_herois_da_mesma_conexao_compartilham_limite_de_uma_marca(self):
        sala = self.nova_sala()
        sala.players["p3"] = S.make_player("p3", "Caio", "warrior", 2)
        sala.players["p3"]["controlador"] = "p1"
        self.assertTrue(await self.create_marker(
            sala, "p1", "danger", "tile", pos=[4, 2], hero_id="p1"))
        await asyncio.sleep(0.26)
        self.assertTrue(await self.create_marker(
            sala, "p1", "move", "tile", pos=[3, 3], hero_id="p3"))
        markers = sala._cooperative_markers_for_pid("p1")
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["owner_id"], "p3")
        self.assertEqual(markers[0]["category"], "move")
        self.assertEqual(sala._cooperative_marker_last_at.keys(), {"p1"})

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

    async def test_marcador_de_inimigo_some_do_payload_quando_ele_fica_invisivel(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        sala.monsters["m1"]["invisivel_sombras"] = True
        self.assertEqual(sala._cooperative_markers_for_pid("p1"), [])
        self.assertEqual(sala._cooperative_markers_for_pid("p2"), [])

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

    async def test_broadcast_personaliza_marcadores_sem_enviar_alvo_oculto(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        enviados = {}

        async def broadcast(msg, skip=None, personalize=None):
            for pid in ("p1", "p2"):
                enviados[pid] = personalize(pid, msg) if personalize else msg

        async def noop(*args, **kwargs):
            return None

        sala.broadcast = broadcast
        sala._notificar_maldicoes_pendentes = noop
        sala._check_objectives = noop
        sala._atualizar_alertas_sobrevivencia = lambda: None
        sala._enviar_alertas_sobrevivencia = noop
        sala._condition_alerts = []
        await S.GameRoom.push_state(sala)
        self.assertEqual(enviados["p1"].get("cooperative_markers"), [
            {"owner_id": "p1", "category": "attack", "target_type": "enemy",
             "target_id": "m1", "pos": [5, 2], "expires_round": 2}])
        self.assertEqual(enviados["p2"].get("cooperative_markers"), [])

    async def test_marca_monstro_grande_visivel_por_uma_casa_do_footprint(self):
        sala = self.nova_sala()
        sala.players["p1"]["pos"] = [7, 2]
        sala.players["p2"]["pos"] = [17, 2]
        sala.monsters["big"] = {"id": "big", "type": "ogre", "name": "Ogro",
                                 "pos": [10, 2], "size": [2, 1], "hp": 8, "max_hp": 8}
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="big"))
        recipient_markers = sala._cooperative_markers_for_pid("p2")
        self.assertEqual(len(recipient_markers), 1)
        self.assertEqual(recipient_markers[0]["pos"], [10, 2])

    async def test_cegueira_ignora_visao_compartilhada_de_aliado(self):
        sala = self.nova_sala()
        sala.players["p2"]["cego"] = True
        await self.set_shared_vision(sala, "p2", True)
        self.assertTrue(await self.create_marker(sala, "p1", "attack", "enemy", target_id="m1"))
        self.assertEqual(sala._cooperative_markers_for_pid("p2"), [])

    async def test_marcador_de_casa_respeita_oclusao(self):
        sala = self.nova_sala()
        sala._tem_linha_de_visao = lambda a, b, ignorar_objetos=False: b == [2, 2]
        self.assertFalse(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))

    async def test_revelacao_remota_permite_ver_marcador_sem_dar_visao_compartilhada(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))
        sala.magic_reveal = {(4, 2): sala.round_num + 1}
        self.assertEqual(len(sala._cooperative_markers_for_pid("p2")), 1)

    async def test_marcador_dura_uma_rodada_completa_e_expira_na_virada_seguinte(self):
        sala = self.nova_sala()
        self.assertTrue(await self.create_marker(sala, "p1", "danger", "tile", pos=[4, 2]))
        async def noop(*args, **kwargs):
            return None
        sala._processar_recarga_slots_rodada = lambda: None
        sala._expirar_armadilhas_duracao = lambda: None
        sala._processar_efeitos_armadilha_turno = noop
        sala._processar_em_chamas_turno = noop
        sala._processar_acido_residual_turno = noop
        sala._processar_zonas_turno = noop
        sala._aplicar_exaustao_rodada = noop
        sala._tick_retorno_masmorra = noop
        await sala._virada_de_rodada()
        self.assertEqual(sala.round_num, 2)
        self.assertIn("p1", sala.cooperative_markers)
        await sala._virada_de_rodada()
        self.assertEqual(sala.round_num, 3)
        self.assertNotIn("p1", sala.cooperative_markers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
