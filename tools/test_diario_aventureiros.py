"""Testes do histórico compartilhado do Diário dos Aventureiros."""
import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def campaign(**extra):
    data = {
        "id": "sg_diario1", "group_id": "grp_diario1", "owner": "teste",
        "members": {}, "slots": {}, "characters": {}, "mode": "campaign",
        "world_adventure_progress": {}, "world_adventure_route_progress": {},
        "journal": [{"kind": "campaign_created", "text": "Campanha criada"}],
    }
    data.update(extra)
    return data


class CampaignJournalMigrationTests(unittest.TestCase):
    def _migrate(self, data):
        group = {"campaign_ids": [data["id"]]}
        with patch.object(server, "load_group", return_value=group):
            server.ensure_campaign_schema(data)

    def test_legacy_campaign_gets_empty_diary_without_changing_journal_or_inventory(self):
        original_journal = [{"kind": "campaign_created", "text": "Campanha criada"}]
        data = campaign(journal=original_journal, characters={"teste": {"bag": [{"id": "pocao"}]}})

        self._migrate(data)

        self.assertEqual(data["adventurer_journal"], {"missions": [], "items": []})
        self.assertEqual(data["journal"], original_journal)
        self.assertEqual(data["characters"]["teste"]["bag"], [{"id": "pocao"}])

    def test_legacy_completed_progress_reconstructs_without_fabricated_dates(self):
        adventure = {"id": "rota_teste", "dungeons": [
            {"file": "facil.json"},
            {"file": "bifurcada.json", "completion_mode": "route_exits",
             "required_exit_ids": ["saida_a", "saida_b"]},
            {"file": "futura.json"},
        ]}
        data = campaign(
            world_adventure_progress={"rota_teste": 2},
            world_adventure_route_progress={
                "rota_teste:1": {"found_exit_ids": ["saida_a"], "objective_completed": False},
                "rota_teste:2": {"found_exit_ids": ["saida_x"], "objective_completed": False},
            },
        )

        with patch.object(server, "WORLD_ADVENTURES", {"rota_teste": adventure}):
            self._migrate(data)
            first = data["adventurer_journal"]
            self._migrate(data)

        missions = first["missions"]
        self.assertEqual(len(missions), 3)
        self.assertEqual(missions[0], {"adventure_id": "rota_teste", "stage_index": 0,
                                      "exit_ids": [], "complete": True})
        self.assertEqual(missions[1], {"adventure_id": "rota_teste", "stage_index": 1,
                                      "exit_ids": ["saida_a"], "complete": True})
        self.assertEqual(missions[2], {"adventure_id": "rota_teste", "stage_index": 2,
                                      "exit_ids": ["saida_x"], "complete": False})
        self.assertNotIn("completed_at", missions[0])
        self.assertEqual(data["adventurer_journal"], first)

    def test_diary_is_in_checkpoint_field_allowlist(self):
        self.assertIn("adventurer_journal", server.CAMPOS_DO_PONTO)

    def test_checkpoint_round_trip_restores_campaign_diary(self):
        data = campaign(
            id="sg_abcdef", capitulos=[{"n": 1, "nome": "", "pontos": []}],
            capitulo_atual=1, arquivado_por=[],
            adventurer_journal={"missions": [{"adventure_id": "rota", "stage_index": 0,
                                              "exit_ids": ["saida"], "complete": True}],
                               "items": [{"item_id": "chave_antiga"}]},
        )
        stored = {}

        def save(collection, key, value):
            stored[key] = deepcopy(value)

        with patch.object(server, "_new_savegame_id", return_value="pt_aaaaaa"), \
             patch.object(server.LOJA, "gravar", side_effect=save), \
             patch.object(server.LOJA, "ler", side_effect=lambda collection, key: stored.get(key)):
            point, error = server.registrar_ponto(data, "manual", nome="Antes")
            self.assertIsNone(error)
            data["adventurer_journal"] = {"missions": [], "items": []}
            with patch.object(server, "_new_savegame_id", return_value="pt_bbbbbb"):
                error = server.carregar_ponto_no_jogo(data, point["id"])

        self.assertIsNone(error)
        self.assertEqual(data["adventurer_journal"], {
            "missions": [{"adventure_id": "rota", "stage_index": 0,
                          "exit_ids": ["saida"], "complete": True}],
            "items": [{"item_id": "chave_antiga"}],
        })


if __name__ == "__main__":
    unittest.main()
