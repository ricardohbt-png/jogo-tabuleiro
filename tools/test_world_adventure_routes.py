"""Roundtrip/save contracts for optional route-exit completion on world stages."""
import copy
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

# Os saves do editor gravam os arquivos de dados reais: redireciona para uma pasta temporária para este
# teste nunca tocar em world_adventures.json (um conflito de acesso já o deixou com dados de teste).
import atexit, shutil, tempfile
_TMP_DADOS = tempfile.mkdtemp()
atexit.register(shutil.rmtree, _TMP_DADOS, True)
S.WORLD_ADVENTURES_FILE = os.path.join(_TMP_DADOS, "world_adventures.json")
S.WORLD_MAP_POINTS_FILE = os.path.join(_TMP_DADOS, "world_map_points.json")


class WorldAdventureRouteTests(unittest.TestCase):
    def setUp(self):
        self.old_adventures = S.WORLD_ADVENTURES
        self.old_locations = copy.deepcopy(S.WORLD_LOCATIONS)
        S.WORLD_ADVENTURES = {}
        self.dungeon = {"id": "route_dungeon", "name": "Route dungeon", "file": "route_dungeon.json",
                        "route_exits": [{"id": "easy_exit", "name": "Easy exit"},
                                        {"id": "hard_exit", "name": "Hard exit"}]}
        self.definition = {"route_exits": self.dungeon["route_exits"]}
        self.common_patches = [
            patch.object(S, "listar_dungeons", return_value=[self.dungeon]),
            patch.object(S, "carregar_dungeon", return_value=self.definition),
            patch.object(S, "_save_world_map_points"),
            patch.object(S, "_save_world_adventures"),
            patch.object(S, "_world_adventures_editor_payload", return_value={"ok": True}),
        ]
        for p in self.common_patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.common_patches):
            p.stop()
        S.WORLD_ADVENTURES = self.old_adventures
        S.WORLD_LOCATIONS.clear()
        S.WORLD_LOCATIONS.update(self.old_locations)

    def row(self, stages):
        return {"id": "route_test", "nome": "Route test", "x": 50, "y": 50,
                "dungeons": stages}

    def test_etapa_linear_roundtrip_preserva_formato_existente(self):
        self.assertEqual(S._etapa_obj("route_dungeon.json").get("completion_mode", "primary"), "primary")
        ok, _ = S._save_world_adventures_upload([], [self.row(["route_dungeon.json"])])
        self.assertTrue(ok)
        stage = S.WORLD_ADVENTURES["route_test"]["dungeons"][0]
        self.assertEqual(stage["file"], "route_dungeon.json")
        self.assertNotIn("completion_mode", stage)

    def test_etapa_por_saidas_roundtrip(self):
        raw = {"file": "route_dungeon.json", "encadear": False,
               "intro": "Abertura", "outro": "Fecho", "completion_mode": "route_exits",
               "required_exit_ids": ["easy_exit", "hard_exit"],
               "requisito": {"fato": "mapa_lateral_encontrado", "renome_min": 3},
               "scene_trigger": {"scene_id": "entry_scene", "once": True}}
        ok, _ = S._save_world_adventures_upload([], [self.row([raw])])
        self.assertTrue(ok)
        stage = S.WORLD_ADVENTURES["route_test"]["dungeons"][0]
        self.assertEqual(stage["completion_mode"], "route_exits")
        self.assertEqual(stage["required_exit_ids"], ["easy_exit", "hard_exit"])
        self.assertEqual(stage["intro"], "Abertura")
        self.assertEqual(stage["outro"], "Fecho")
        self.assertEqual(stage["requisito"]["fato"], "mapa_lateral_encontrado")
        self.assertEqual(stage["requisito"]["renome_min"], 3)
        self.assertEqual(S._etapa_obj(stage)["required_exit_ids"], ["easy_exit", "hard_exit"])

    def test_saida_obrigatoria_obsoleta_recusada_sem_apagar_destino(self):
        S.WORLD_ADVENTURES["route_test"] = {"id": "route_test", "nome": "Existing", "dungeons": []}
        row = self.row([{"file": "route_dungeon.json", "completion_mode": "route_exits",
                         "required_exit_ids": ["deleted_exit"]}])
        ok, message = S._save_world_adventures_upload([], [row])
        self.assertFalse(ok)
        self.assertIn("saídas inválidas", message)
        self.assertEqual(S.WORLD_ADVENTURES["route_test"]["nome"], "Existing")

    def test_etapa_linear_nao_duplica_masmorra(self):
        row = self.row(["route_dungeon.json", "route_dungeon.json"])
        ok, _ = S._save_world_adventures_upload([], [row])
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
