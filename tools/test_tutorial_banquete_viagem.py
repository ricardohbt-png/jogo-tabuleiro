"""Contrato do banquete portátil exclusivo do baú do tutorial."""
import json
import asyncio
from copy import deepcopy
from pathlib import Path
import sys
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S


class BanqueteViagemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dungeon = S.carregar_dungeon("campo_de_treinamento.json")

    def test_item_portatil_recupera_40_e_reutiliza_imagem_do_banquete(self):
        item = S._DUNGEON_ITEM_CATALOG.get("banquete_viagem")
        self.assertIsNotNone(item)
        self.assertEqual(item.get("name"), "Banquete de Viagem")
        self.assertEqual(item.get("item_slot"), "bag")
        self.assertEqual(item.get("effect"), "meal_survival")
        self.assertEqual((item.get("fome"), item.get("sede")), (40, 40))
        self.assertEqual(item.get("price"), 100)
        self.assertEqual(item.get("icon"), "assets/itens/banquete.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        # Desde 2026-10-17 também é vendido nas tavernas (ver test_banquete_viagem_na_taverna.py).
        self.assertIn("banquete_viagem", {i["id"] for i in S.SHOP_TAVERN})
        self.assertEqual((S._DUNGEON_ITEM_CATALOG["racao_viagem"].get("fome"),
                          S._DUNGEON_ITEM_CATALOG["racao_viagem"].get("sede")), (20, 0))
        self.assertEqual((S._DUNGEON_ITEM_CATALOG["cantil_agua"].get("fome"),
                          S._DUNGEON_ITEM_CATALOG["cantil_agua"].get("sede")), (0, 20))

    def test_bau_da_cota_individual_de_provisoes_e_licao_comeca_em_zero(self):
        ok, msg = S.validar_dungeon(self.dungeon)
        self.assertEqual((ok, msg), (True, "ok"))
        bau = next(c for c in self.dungeon["chests"] if c["pos"] == [29, 14])
        itens = bau["items"]
        self.assertEqual(len(itens), 24)
        self.assertEqual({iid: sum(i.get("id") == iid for i in itens) for iid in
                          ("banquete_viagem", "racao_viagem", "cantil_agua")},
                         {"banquete_viagem": 12, "racao_viagem": 6, "cantil_agua": 6})
        self.assertTrue(all(i.get("tutorial_provision") is True for i in itens))
        falas = {f["id"]: f for f in self.dungeon["falas"]}
        self.assertEqual(falas["fala_18"]["tarefa"]["alvos"], ["banquete_viagem", "racao_viagem"])
        self.assertEqual(falas["fala_18"]["tarefa"]["vezes"], 3)
        self.assertEqual(falas["fala_19"]["tarefa"]["alvo"], "cantil_agua")
        self.assertEqual(falas["fala_17"]["efeito"], {"fome": 0, "sede": 0})

    def test_bau_hidrata_item_com_slot_imagem_e_marcador_de_emprestimo(self):
        for item_id in ("banquete_viagem", "racao_viagem", "cantil_agua"):
            item = S.hidratar_itens_bau([{"id": item_id, "tutorial_provision": True}])[0]
            self.assertEqual(item["item_slot"], "bag")
            self.assertTrue(item["tutorial_provision"])
            self.assertTrue(item["tutorial_loan"])
            if item_id == "banquete_viagem":
                self.assertEqual(item["icon"], "assets/itens/banquete.png")

    def test_heroi_usa_todas_as_provisoes_no_mesmo_turno_e_volta_a_100(self):
        async def run():
            room = S.GameRoom("BANQUETE_TEST")
            player = S.make_player("p1", "Aluna", "warrior", 0)
            player["fome"] = player["sede"] = 0
            player["bonus_action_used"] = True
            player["bag"] = S.hidratar_itens_bau([
                {"id": iid, "tutorial_provision": True}
                for iid in ("banquete_viagem", "banquete_viagem", "racao_viagem", "cantil_agua")
            ])
            room.players[player["id"]] = player
            room.training_mode = True
            room._is_turn = lambda pid: True
            errors = []

            async def noop(*args, **kwargs):
                return None

            async def send(pid, message):
                errors.append(message)

            room.gm_say = noop
            room.push_state = noop
            room.send_to = send

            await room.handle_use_item("p1", "banquete_viagem")
            await room.handle_use_item("p1", "banquete_viagem")
            await room.handle_use_item("p1", "racao_viagem")
            await room.handle_use_item("p1", "cantil_agua")
            self.assertEqual((player["fome"], player["sede"]), (100, 100))
            self.assertTrue(player["bonus_action_used"])
            self.assertEqual(len(player["bag"]), 0)
            self.assertEqual(room.training_state["provisoes_usadas_por_heroi"]["p1"], {
                "banquete_viagem": 2, "racao_viagem": 1, "cantil_agua": 1})
            self.assertFalse(any(e.get("type") == "error" for e in errors))
            extra = S.hidratar_itens_bau([
                {"id": "banquete_viagem", "tutorial_provision": True}])[0]
            player["bag"].append(extra)
            await room.handle_use_item("p1", "banquete_viagem")
            self.assertEqual(player["bag"], [extra])
            self.assertEqual(room.training_state["provisoes_usadas_por_heroi"]["p1"]["banquete_viagem"], 2)
            self.assertTrue(any(e.get("type") == "error" for e in errors))

        asyncio.run(run())

    def test_coleta_tudo_entrega_o_conjunto_individual_e_respeita_as_cotas(self):
        async def run():
            room = S.GameRoom("BANQUETE_PICKUP_TEST")
            room.load_authored_dungeon(self.dungeon)
            room.training_mode = True
            room.selected_dungeon = "campo_de_treinamento.json"
            room._is_turn = lambda pid: True
            players = []
            for index, class_id in enumerate(("warrior", "mage", "rogue", "cleric", "bard", "paladin")):
                player = S.make_player(f"p{index + 1}", f"Herói {index + 1}", class_id, index)
                player["pos"] = [29, 14]
                room.players[player["id"]] = player
                players.append(player)

            async def noop(*args, **kwargs):
                return None

            room.gm_say = noop
            room.push_state = noop
            chest = next(c for c in room.chests.values() if c["pos"] == [29, 14])
            for index, player in enumerate(players):
                await room.handle_take_all_from_chest(player["id"], chest["id"])
                self.assertEqual({iid: sum(i["id"] == iid for i in player["bag"]) for iid in
                                  ("banquete_viagem", "racao_viagem", "cantil_agua")},
                                 {"banquete_viagem": 2, "racao_viagem": 1, "cantil_agua": 1})
                self.assertEqual(room.training_state["provisoes_por_heroi"][player["id"]], {
                    "banquete_viagem": 2, "racao_viagem": 1, "cantil_agua": 1})
                if index == 0:
                    self.assertEqual(len(chest["items"]), 20)
                    await room.handle_take_all_from_chest(player["id"], chest["id"])
                    self.assertEqual(len(player["bag"]), 4)
                    self.assertEqual(len(chest["items"]), 20)
            self.assertEqual(len(chest["items"]), 0)

        asyncio.run(run())

    def test_tarefa_da_licao_conta_banquetes_e_racao_por_alvos(self):
        async def run():
            room = S.GameRoom("BANQUETE_LICAO_TEST")
            p = S.make_player("p1", "Aluna", "warrior", 0)
            p["licao_atual"] = "fala_18"
            fala = deepcopy(next(f for f in self.dungeon["falas"] if f["id"] == "fala_18"))
            room.licoes = [fala]
            room.training_mode = True
            room._training_requirements = lambda *_: True
            room._licao_no_lugar = lambda *_: True
            conclusoes = []

            async def noop(*args, **kwargs):
                return None

            async def concluir(*args, **kwargs):
                conclusoes.append(True)

            room._guia_evento = noop
            room._licao_concluir = concluir
            room._verificar_falas = noop
            await room._licao_evento(p, "usar_item", alvo="cantil_agua")
            self.assertEqual(p.get("licao_progresso", {}).get("fala_18", 0), 0)
            for item_id in ("banquete_viagem", "banquete_viagem", "racao_viagem"):
                await room._licao_evento(p, "usar_item", alvo=item_id)
            self.assertEqual(p["licao_progresso"]["fala_18"], 3)
            self.assertEqual(conclusoes, [True])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
