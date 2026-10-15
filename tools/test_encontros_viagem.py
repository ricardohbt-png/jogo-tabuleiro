"""Regras puras de viagens e validação do mapa de emboscada."""
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import server as S


class RegrasViagemTests(unittest.TestCase):
    def test_faixas_e_chances_por_custo_combinado(self):
        esperados = {
            0: ("curta", 10), 12: ("curta", 10), 14: ("curta", 10),
            15: ("media", 15), 16: ("media", 15), 20: ("media", 15),
            21: ("longa", 20), 28: ("longa", 20),
        }
        for total, esperado in esperados.items():
            with self.subTest(total=total):
                fome, sede = total // 2, total - total // 2
                self.assertEqual(S.tier_viagem(fome, sede), esperado[0])
                self.assertEqual(S.chance_encontro(fome, sede), esperado[1])

    def test_tarifa_base_mais_quinze_porcento_arredondado_para_cima(self):
        esperados = {
            (0, 0): 10, (6, 6): 12, (7, 7): 13,
            (8, 8): 23, (10, 10): 23, (11, 10): 34,
            (12, 12): 34, (14, 14): 35,
        }
        for custos, tarifa in esperados.items():
            with self.subTest(custos=custos):
                self.assertEqual(S.tarifa_caravana(*custos), tarifa)

    def test_selecao_tem_rng_injetavel(self):
        class RNG:
            def __init__(self):
                self.opcoes = None
            def choice(self, valores):
                self.opcoes = valores
                return valores[-1]
        rng = RNG()
        comp = S.selecionar_composicao_viagem([{"alive": True, "hp": 10, "level": 1}], "animais", rng)
        self.assertEqual(comp, ["lobo_cinzento"])
        self.assertEqual(len(rng.opcoes), 1)

    def test_grupo_considera_so_vivos_e_usa_niveis_sem_escalar_monstros(self):
        grupo = [
            {"alive": True, "hp": 10, "level": 1},
            {"alive": True, "hp": 10, "level": 5},
            {"alive": False, "hp": 0, "level": 30},
        ]
        comp = S.selecionar_composicao_viagem(grupo, "animais")
        self.assertGreaterEqual(len(comp), 1)
        self.assertLessEqual(len(comp), 3)
        self.assertTrue(all(any(m["type"] == tipo for m in S.MONSTER_DEFS) for tipo in comp))
        self.assertEqual(S.selecionar_composicao_viagem([{"alive": False, "hp": 0}], "animais"), [])

    def test_categoria_bandoleiros_usa_fichas_existentes(self):
        viajantes = [{"alive": True, "hp": 10, "level": 12} for _ in range(4)]
        comp = S.selecionar_composicao_viagem(viajantes, "bandoleiros")
        possiveis = {
            "goblin", "goblin_arqueiro", "goblin_combatente", "goblin_dual", "goblin_assassino",
            "goblin_xama", "orc", "orc_guerreiro", "kobold_lanceiro",
            "kobold_besteiro", "ogro_clava", "ogro_lanca",
        }
        self.assertTrue(comp)
        self.assertTrue(all(tipo in possiveis for tipo in comp))
        catalogo = {m["type"]: m for m in S.MONSTER_DEFS}
        self.assertLessEqual(sum(S.monster_cr(catalogo[t]) for t in comp), 24)

    def test_catalogo_de_bandoleiros_cobre_todas_as_variantes_aprovadas(self):
        esperados = {
            "goblin_arqueiro", "goblin_combatente", "goblin_dual", "goblin_assassino", "goblin_xama",
            "orc", "orc_guerreiro", "kobold_lanceiro", "kobold_besteiro", "ogro_clava", "ogro_lanca",
        }
        disponiveis = {tipo for comp in S._COMPOSICOES_ENCONTRO_VIAGEM["bandoleiros"] for tipo in comp}
        self.assertLessEqual(esperados, disponiveis)

    def test_mapa_eh_novo_aberto_sem_inimigos_fixos_ou_objetivos(self):
        caminho = os.path.join(ROOT, "dungeons", "estrada_floresta_emboscada.json")
        with open(caminho, encoding="utf-8") as f:
            mapa = json.load(f)
        self.assertEqual(S.validar_dungeon(mapa), (True, "ok"))
        self.assertEqual(mapa["name"], "Estrada")
        self.assertEqual(mapa["ambiente"], "ar_livre")
        self.assertEqual(mapa["grid"], {"w": 26, "h": 16})
        self.assertEqual(mapa.get("monsters"), [])
        self.assertFalse(mapa.get("objectives", {}).get("secondary"))
        self.assertEqual(mapa["objectives"]["primary"].get("xp", 0), 0)
        materiais = mapa["materiais"]
        self.assertGreater(sum(v == "terra" for v in materiais.values()), 60)
        self.assertGreater(sum(v == "grama" for v in materiais.values()), 180)
        self.assertGreater(len(mapa["decorations"]), 8)
        estrada = {tuple(map(int, k.split(","))) for k, v in materiais.items() if v == "terra"}
        alcancadas = set()
        fila = [p for p in estrada if p[0] == 0]
        while fila:
            atual = fila.pop()
            if atual in alcancadas:
                continue
            alcancadas.add(atual)
            x, y = atual
            fila.extend(q for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                        if q in estrada and q not in alcancadas)
        self.assertTrue(any(x == 25 for x, _ in alcancadas), "estrada deve cruzar o mapa")
        self.assertEqual(alcancadas, estrada, "estrada deve ser contínua, sem trechos isolados")
        self.assertFalse(any(tuple(d.get("pos", [])) in estrada for d in mapa["decorations"]
                             if d.get("type") == "arvore"), "árvores não bloqueiam a estrada")
        zonas = mapa["encounter_spawn_zones"]
        self.assertLess(zonas["heroes"]["x_max"] + 4, zonas["enemies"]["x_min"])


class TransacaoViagemTests(unittest.IsolatedAsyncioTestCase):
    def sala(self, gold=100):
        r = S.GameRoom("VIA1")
        r.phase = "city"
        r.host_pid = "p1"
        r.world_location = "alva_e_luz"
        r.players = {"p1": {"id": "p1", "name": "Ana", "alive": True,
                             "level": 1, "gold": gold, "fome": 40, "sede": 40}}
        r.gm_say = AsyncMock()
        r.broadcast_city_state = AsyncMock()
        r._checkpoint_savegame = lambda: None
        return r

    async def test_estrada_cobra_provisoes_e_roda_uma_vez(self):
        r = self.sala()
        with patch.object(S.random, "random", return_value=0.99) as rolar:
            await r.handle_world_travel("p1", "vila_riacho", mode="road")
        self.assertEqual(rolar.call_count, 1)
        self.assertEqual((r.players["p1"]["fome"], r.players["p1"]["sede"]), (34, 34))
        self.assertEqual(r.world_location, "vila_riacho")

    async def test_caravana_cobra_tarifa_e_provisoes_sem_rolar_encontro(self):
        r = self.sala()
        with patch.object(S.random, "random") as rolar:
            await r.handle_world_travel("p1", "vila_riacho", mode="caravan")
        self.assertEqual(rolar.call_count, 0)
        self.assertEqual(r.players["p1"]["gold"], 88)
        self.assertEqual((r.players["p1"]["fome"], r.players["p1"]["sede"]), (34, 34))
        self.assertEqual(r.world_location, "vila_riacho")

    async def test_multiplayer_pede_cobertura_sem_divida_ou_debito_parcial(self):
        r = self.sala()
        r.players["p2"] = {"id": "p2", "name": "Beto", "alive": True,
                            "level": 1, "gold": 0, "fome": 40, "sede": 40}
        r.players["p3"] = {"id": "p3", "name": "Caio", "alive": True,
                            "is_master": True, "level": 1, "gold": 0, "fome": 40, "sede": 40}
        r.savegame = {"play_mode": "multiplayer"}
        r.send_to = AsyncMock()
        await r.handle_world_travel("p1", "vila_riacho", mode="caravan")
        pending = r.pending_world_travel
        self.assertEqual(pending["phase"], "sponsorship")
        self.assertEqual(r.players["p1"]["gold"], 100)
        self.assertEqual(r.players["p2"]["gold"], 0)
        self.assertEqual((r.players["p1"]["fome"], r.players["p2"]["fome"]), (40, 40))
        await r.handle_caravan_sponsorship_response("p3", pending["active_request_id"], True)
        self.assertIs(r.pending_world_travel, pending, "pagador fora da solicitação ativa não pode aceitar")
        await r.handle_caravan_sponsorship_response("p1", pending["active_request_id"], True)
        self.assertIsNone(r.pending_world_travel)
        self.assertEqual(r.players["p1"]["gold"], 76)
        self.assertEqual(r.players["p2"]["gold"], 0)
        self.assertEqual((r.players["p1"]["fome"], r.players["p2"]["fome"]), (34, 34))
        self.assertEqual(r.world_location, "vila_riacho")

    async def test_solo_grupo_nao_pode_patrocinar_passagem(self):
        r = self.sala()
        r.players["extra"] = {"id": "extra", "name": "Beto", "alive": True,
                               "level": 1, "gold": 100, "fome": 40, "sede": 40,
                               "controlador": "p1"}
        r.players["p2"] = {"id": "p2", "name": "Caio", "alive": True,
                           "level": 1, "gold": 0, "fome": 40, "sede": 40,
                           "controlador": "p1"}
        r.savegame = {"play_mode": "solo"}
        r.send_to = AsyncMock()
        await r.handle_world_travel("p1", "vila_riacho", mode="caravan")
        self.assertIsNone(r.pending_world_travel)
        self.assertEqual(r.world_location, "alva_e_luz")
        self.assertEqual(r.players["p1"]["gold"], 100)

    async def test_recusa_de_cobertura_nao_cobra_nem_registra_divida(self):
        r = self.sala()
        r.players["p2"] = {"id": "p2", "name": "Beto", "alive": True,
                            "level": 1, "gold": 0, "fome": 40, "sede": 40}
        r.savegame = {"play_mode": "multiplayer"}
        r.send_to = AsyncMock()
        await r.handle_world_travel("p1", "vila_riacho", mode="caravan")
        pending = r.pending_world_travel
        await r.handle_caravan_sponsorship_response("p1", pending["active_request_id"], False)
        self.assertIsNone(r.pending_world_travel)
        self.assertEqual(r.world_location, "alva_e_luz")
        self.assertEqual((r.players["p1"]["gold"], r.players["p2"]["gold"]), (100, 0))
        self.assertEqual((r.players["p1"]["fome"], r.players["p2"]["fome"]), (40, 40))
        self.assertFalse(any("debt" in p or "divida" in p for p in r.players.values()))

    async def test_emboscada_guarda_viagem_e_nao_roda_ao_repetir_mensagem(self):
        r = self.sala()
        capturada = {}
        async def iniciar(_pid, pending):
            capturada.update(pending)
            r.pending_world_travel = pending
        r._iniciar_encontro_viagem = iniciar
        with patch.object(S.random, "random", return_value=0.0) as rolar:
            await r.handle_world_travel("p1", "vila_riacho", mode="road")
            await r.handle_world_travel("p1", "vila_riacho", mode="road")
        self.assertEqual(rolar.call_count, 1)
        self.assertEqual(capturada["origin"], "alva_e_luz")
        self.assertEqual(capturada["destination"], "vila_riacho")
        self.assertTrue(capturada["charged"])
        self.assertTrue(capturada["roll_resolved"])
        self.assertEqual(r.world_location, "alva_e_luz")
        self.assertEqual(r.players["p1"]["fome"], 34)

    async def test_inicio_monta_mapa_temporario_e_preserva_a_continuacao(self):
        r = self.sala()
        r.enter_dungeon = AsyncMock()
        pending = {"destination_type": "city", "origin": "alva_e_luz", "destination": "vila_riacho",
                   "charged": True, "roll_resolved": True, "composition": ["ogro_clava", "kobold_besteiro"]}
        await r._iniciar_encontro_viagem("p1", pending)
        self.assertEqual(r.selected_dungeon, "estrada_floresta_emboscada.json")
        self.assertEqual(r.dungeon_def["ambiente"], "ar_livre")
        spawns = r.dungeon_def["monsters"]
        self.assertEqual([m["type"] for m in spawns], pending["composition"])
        self.assertEqual(len({tuple(m["pos"]) for m in spawns}), len(spawns))
        self.assertEqual(r.pending_world_travel["phase"], "combat")
        self.assertTrue(r.pending_world_travel["charged"])
        r.enter_dungeon.assert_awaited_once_with("p1", from_world_adventure=True)

    async def test_vitoria_de_encontro_de_cidade_retorna_ao_destino_sem_fim_de_missao(self):
        r = self.sala()
        r.phase = "playing"
        r.pending_world_travel = {
            "destination_type": "city", "origin": "alva_e_luz", "destination": "vila_riacho",
            "mode": "road", "charged": True, "roll_resolved": True, "phase": "combat",
        }
        r.monsters = {}
        await r._check_objectives()
        self.assertEqual(r.phase, "city")
        self.assertEqual(r.world_location, "vila_riacho")
        self.assertIsNone(r.pending_world_travel)
        self.assertFalse(r.mission_complete_pending)

    async def test_emboscada_de_masmorra_oferece_continuar_ou_retornar_sem_reembolso(self):
        adventure_id = "viagem_emboscada_teste"
        S.WORLD_ADVENTURES[adventure_id] = {
            "id": adventure_id, "nome": "Ruínas Teste", "fome": 6, "sede": 6,
            "dungeons": [{"file": "amostra.json"}],
        }
        r = self.sala()
        r.players["p1"]["class_id"] = "warrior"
        r.world_adventure_progress = {}
        r._avaliar_requisito = lambda _req: (True, [])
        r._iniciar_encontro_viagem = AsyncMock(side_effect=lambda _pid, pending: (
            pending.update({"phase": "combat"}), setattr(r, "pending_world_travel", pending)))
        r._continuar_entrada_pendente = AsyncMock()
        with patch.object(S.random, "random", return_value=0.0) as rolar:
            await r.handle_world_adventure("p1", adventure_id)
            self.assertEqual(r.players["p1"]["fome"], 34)
            r.phase = "playing"
            r.monsters = {}
            await r._check_objectives()
            self.assertEqual(r.phase, "city")
            self.assertEqual(r.pending_world_travel["phase"], "choice")
            await r.handle_world_adventure_encounter_choice("p1", "continue")
            self.assertEqual(r.players["p1"]["fome"], 34)
            self.assertEqual(rolar.call_count, 1)
        self.assertEqual(r.world_adventure_id, adventure_id)
        self.assertEqual(r._continuar_entrada_pendente.await_count, 1)
        self.assertIsNone(r.pending_world_travel)

        # Uma nova emboscada permite voltar sem devolver provisões.
        r = self.sala()
        r.players["p1"]["class_id"] = "warrior"
        r.world_adventure_progress = {}
        r._avaliar_requisito = lambda _req: (True, [])
        r._iniciar_encontro_viagem = AsyncMock(side_effect=lambda _pid, pending: (
            pending.update({"phase": "combat"}), setattr(r, "pending_world_travel", pending)))
        with patch.object(S.random, "random", return_value=0.0):
            await r.handle_world_adventure("p1", adventure_id)
        r.phase = "playing"
        r.monsters = {}
        await r._check_objectives()
        await r.handle_world_adventure_encounter_choice("p1", "return")
        self.assertEqual(r.players["p1"]["fome"], 34)
        self.assertEqual(r.world_location, "alva_e_luz")
        self.assertIsNone(r.pending_world_travel)


if __name__ == "__main__":
    unittest.main()
