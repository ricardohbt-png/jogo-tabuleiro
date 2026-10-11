"""Contratos de autoria para rotas alternativas em masmorras."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S


def dungeon():
    tiles = [[S.FLOOR] * 6 for _ in range(5)]
    for x in range(6):
        tiles[0][x] = tiles[4][x] = S.WALL
    for y in range(5):
        tiles[y][0] = tiles[y][5] = S.WALL
    return {
        "schema_version": 1, "id": "routes_test", "name": "Routes test",
        "grid": {"w": 6, "h": 5}, "tiles": tiles,
        "entrance": {"x": 1, "y": 1},
        "rooms": [{"id": "r1", "x": 1, "y": 1, "w": 4, "h": 3,
                   "role": "entrance", "doors": []}],
        "monsters": [], "decorations": [], "chests": [], "traps": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }


class DungeonRouteSchemaTests(unittest.TestCase):
    def valid_routes(self):
        d = dungeon()
        d["routes"] = [
            {"id": "easy", "name": "Ala fácil", "monster_policy": "persistir_derrotas"},
            {"id": "hard", "name": "Galeria", "monster_policy": "reaparecer"},
        ]
        d["route_exits"] = [
            {"id": "exit_a", "name": "Saída leste", "pos": [4, 1], "route_id": "easy"},
            {"id": "exit_b", "name": "Saída norte", "pos": [4, 3], "route_id": "hard"},
        ]
        return d

    def test_validar_rotas_e_saidas_validas(self):
        ok, msg = S.validar_dungeon(self.valid_routes())
        self.assertTrue(ok, msg)

    def test_rejeita_ids_e_referencias_invalidas(self):
        cases = []
        d = self.valid_routes(); d["routes"][1]["id"] = "easy"; cases.append(d)
        d = self.valid_routes(); d["route_exits"][1]["id"] = "exit_a"; cases.append(d)
        d = self.valid_routes(); d["route_exits"][0]["route_id"] = "missing"; cases.append(d)
        d = self.valid_routes(); d["route_exits"][0]["pos"] = [0, 1]; cases.append(d)
        d = self.valid_routes(); d["routes"][0]["monster_policy"] = "random"; cases.append(d)
        for invalid in cases:
            with self.subTest(invalid=invalid):
                ok, _ = S.validar_dungeon(invalid)
                self.assertFalse(ok)

    def test_masmorra_legada_sem_rotas_continua_valida(self):
        ok, msg = S.validar_dungeon(dungeon())
        self.assertTrue(ok, msg)

    def test_monstros_com_referencia_de_rota_precisam_de_source_id_unico(self):
        d = self.valid_routes()
        d["monsters"] = [
            {"type": S.MONSTER_DEFS[0]["type"], "pos": [2, 1], "source_id": "mob_1", "route_id": "easy"},
            {"type": S.MONSTER_DEFS[0]["type"], "pos": [3, 1], "source_id": "mob_1", "route_id": "hard"},
        ]
        ok, _ = S.validar_dungeon(d)
        self.assertFalse(ok)

    def test_porta_aceita_requisito_externo_e_recusa_vazio(self):
        d = dungeon()
        d["tiles"][1][2] = S.DOOR
        d["rooms"][0]["doors"] = [[2, 1]]
        d["door_conditions"] = {"2,1": {"type": "requirement", "requirement": {"fato": "ponte_liberada"}}}
        ok, msg = S.validar_dungeon(d)
        self.assertTrue(ok, msg)
        d["door_conditions"]["2,1"]["requirement"] = {}
        ok, _ = S.validar_dungeon(d)
        self.assertFalse(ok)


class DungeonRouteRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.old_adventures = S.WORLD_ADVENTURES
        S.WORLD_ADVENTURES = {"routes_runtime": {
            "id": "routes_runtime", "dungeons": [
                {"file": "routes.json", "completion_mode": "route_exits", "required_exit_ids": ["exit_a"]},
                {"file": "routes_second.json", "completion_mode": "route_exits", "required_exit_ids": ["exit_a"]},
            ]}}
        self.room = S.GameRoom("RTE1")
        self.room.phase = "playing"
        self.room.world_adventure_id = "routes_runtime"
        self.room.world_adventure_index = 0
        self.room.route_exits = [{"id": "exit_a", "name": "Saída A", "pos": [2, 2], "route_id": "easy"}]
        self.room.players = {"hero": {"id": "hero", "alive": True, "pos": [2, 2], "class_id": "warrior"}}

    def tearDown(self):
        S.WORLD_ADVENTURES = self.old_adventures

    async def test_descoberta_compartilhada_idempotente_sem_mover_heroi(self):
        messages = []
        async def say(message): messages.append(message)
        self.room.gm_say = say
        before = list(self.room.players["hero"]["pos"])
        await self.room._discover_route_exits()
        await self.room._discover_route_exits()
        state = self.room.world_adventure_route_progress["routes_runtime:0"]
        self.assertEqual(state["found_exit_ids"], ["exit_a"])
        self.assertEqual(self.room.players["hero"]["pos"], before)
        self.assertEqual(len(messages), 1)

    async def test_objetivo_sem_saida_nao_libera_encerramento(self):
        from unittest.mock import AsyncMock, patch
        self.room.players["hero"]["pos"] = [1, 1]
        self.room.objectives = {"primary": {"type": "kill_all"}, "secondary": []}
        self.room.objective_status = None
        self.room._objetivo_concluido = False
        self.room.mission_complete_pending = False
        self.room.gm_say = AsyncMock()
        with patch.object(self.room, "_objetivo_cumprido", return_value=True), \
             patch.object(self.room, "_conceder_objetivo_reward", new=AsyncMock()):
            await self.room._check_objectives()
            self.assertTrue(self.room._objetivo_concluido)
            self.assertFalse(self.room.mission_complete_pending)
            self.room.world_adventure_route_progress["routes_runtime:0"]["found_exit_ids"] = ["exit_a"]
            await self.room._check_objectives()
            self.assertTrue(self.room.mission_complete_pending)

    async def test_snapshots_de_etapas_ficam_isolados(self):
        self.room.savegame = {"dungeon_snapshots": {}}
        self.room._guardar_foto_rota({"stage": 0})
        self.room.world_adventure_index = 1
        self.room._guardar_foto_rota({"stage": 1})
        self.assertEqual(self.room.savegame["dungeon_snapshots"], {
            "routes_runtime:0": {"stage": 0}, "routes_runtime:1": {"stage": 1}})


if __name__ == "__main__":
    unittest.main()
