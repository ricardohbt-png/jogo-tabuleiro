"""Testes do histórico compartilhado do Diário dos Aventureiros."""
import asyncio
import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import AsyncMock, patch

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


class CampaignJournalEventTests(unittest.TestCase):
    def _room(self):
        room = server.GameRoom("DIARIO")
        room.savegame = campaign(adventurer_journal={"missions": [], "items": []})
        room._checkpoint_savegame = lambda: None
        room.gm_say = AsyncMock()
        room.broadcast = AsyncMock()
        room.phase = "playing"
        room.players = {"p1": {"id": "p1", "alive": True, "pos": [2, 2]}}
        room.world_adventure_id = "rota_teste"
        room.world_adventure_index = 0
        room.world_adventure_route_progress = {}
        room.world_adventure_progress = {}
        room.route_exits = [{"id": "saida_a", "pos": [2, 2]}]
        room._etapa_com_saidas = lambda: True
        return room

    def test_discovered_exit_is_recorded_once_before_mission_completion(self):
        room = self._room()

        asyncio.run(room._discover_route_exits())
        asyncio.run(room._discover_route_exits())

        self.assertEqual(room.savegame["adventurer_journal"]["missions"], [{
            "adventure_id": "rota_teste", "stage_index": 0,
            "exit_ids": ["saida_a"], "complete": False,
        }])

    def test_mission_completion_records_only_after_all_authoritative_guards(self):
        adventure = {"id": "rota_teste", "nome": "Rota de teste",
                     "dungeons": [{"file": "teste.json"}]}

        async def attempt(*, pending, objective, exits):
            room = self._room()
            room.players = {"p1": {"id": "p1"}}
            room.mission_complete_pending = pending
            room._objetivo_concluido = objective
            room.world_adventure_route_progress = {"rota_teste:0": {"found_exit_ids": ["saida_a"]}}
            room.world_adventure_revisit = False
            room._route_exits_complete = lambda: exits
            room._tutorial_tem_tour_cidade = lambda: False
            room._progredir_maldicoes_missao = AsyncMock()
            room._trigger_campaign_scene = AsyncMock(return_value=False)
            room._voltar_para_cidade = AsyncMock()
            room.renome = 0
            room.mode = "authored"
            with patch.object(server, "WORLD_ADVENTURES", {"rota_teste": adventure}), \
                 patch.object(server, "write_savegame"), \
                 patch.object(server, "_story_beat", return_value=None):
                await room.handle_encerrar_missao("p1")
            return room.savegame["adventurer_journal"]["missions"]

        for kwargs in (
            {"pending": False, "objective": True, "exits": True},
            {"pending": True, "objective": False, "exits": True},
            {"pending": True, "objective": True, "exits": False},
        ):
            self.assertEqual(asyncio.run(attempt(**kwargs)), [])

        missions = asyncio.run(attempt(pending=True, objective=True, exits=True))
        self.assertEqual(len(missions), 1)
        self.assertTrue(missions[0]["complete"])
        self.assertEqual(missions[0]["exit_ids"], ["saida_a"])
        self.assertIn("completed_at", missions[0])

    def test_authored_key_item_event_is_persistent_and_ordinary_item_is_ignored(self):
        room = self._room()
        room.phase = "city"
        room.players["p1"]["fora_masmorra"] = True
        room.campaign = {"scene_triggers": [{"id": "relic_scene", "when": "key_item_obtained",
                                             "trigger_value": "reliquia_antiga", "scene_id": "reliquia"}]}
        room.active_scene = {"scene_id": "already_open"}

        asyncio.run(room._trigger_campaign_scene("key_item_obtained", "reliquia_antiga"))
        asyncio.run(room._trigger_campaign_scene("key_item_obtained", "espada_comum"))

        self.assertEqual(room.savegame["adventurer_journal"]["items"], [
            {"item_id": "reliquia_antiga", "acquired_at": unittest.mock.ANY},
        ])


class BestiaryRevealPolicyTests(unittest.TestCase):
    def setUp(self):
        self.monster = {
            "type": "teste", "name": "Criatura de teste", "emoji": "👾", "hp": 12, "ac": 14,
            "immunities": ["poison"], "resistances": [{"type": "physical", "reduction": 2}],
            "weaknesses": [{"type": "holy", "bonus_flat": 2}], "reducao_dano": 3,
            "attacks": [{"damage": "1d8", "damage_types": ["physical"]}],
            "str_": 16, "dex": 10, "con_": 14, "int_": 8, "fort": 5, "ref_": 2, "will": 1,
            "special_abilities": [{"id": "sopro", "dc": 14}], "xp": 25,
            "secret_internal_state": "must not leak",
        }

    def test_level_zero_has_no_diary_entry_and_never_reveals_secret_fields(self):
        self.assertIsNone(server._bestiary_reveal_entry(self.monster, 0))

    def test_milestone_15_reveals_defenses_but_not_combat_profile(self):
        entry = server._bestiary_reveal_entry(self.monster, 15)
        self.assertEqual(entry["level"], 1)
        self.assertIn("resistances", entry)
        self.assertIn("immunities", entry)
        self.assertIn("weaknesses", entry)
        self.assertIn("reducao_dano", entry)
        self.assertNotIn("attacks", entry)
        self.assertNotIn("str_", entry)
        self.assertNotIn("special_abilities", entry)
        self.assertNotIn("secret_internal_state", entry)

    def test_milestone_30_adds_profile_and_50_adds_special_abilities(self):
        studied = server._bestiary_reveal_entry(self.monster, 30)
        catalogued = server._bestiary_reveal_entry(self.monster, 50)
        self.assertIn("attacks", studied)
        self.assertIn("fort", studied)
        self.assertNotIn("special_abilities", studied)
        self.assertIn("special_abilities", catalogued)
        self.assertEqual(catalogued["special_abilities"][0]["dc"], 14)

    def test_living_bard_source_reveals_complete_ficha_without_changing_count(self):
        entry = server._bestiary_reveal_entry(self.monster, 1, bard=True)
        self.assertEqual(entry["level"], 3)
        self.assertEqual(entry["knowledge_source"], "bard")
        self.assertIn("special_abilities", entry)
        self.assertIn("xp", entry)
        self.assertEqual(entry["kills"], 1)
        self.assertNotIn("secret_internal_state", entry)


if __name__ == "__main__":
    unittest.main()
