"""Fatia 8 do tutorial: o óleo mostra a cor, o veneno tem boneco suscetível e a trilha avança sozinha."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import server as S
import gerar_guia_comum as G
from test_tutorial_salas import room, D
from test_tutorial_fatia7 import marcar_comuns_ate, def_monstro, POS_CONSUMIVEIS, ORDEM_APOS_PEGAR, SALA_CONSUMIVEIS

# A sala dos consumíveis (baú, palha, bonecos) e as posições vêm do JSON: hoje é a 47, antes da sala de hostilidade era a 22.
SALA_ITENS = SALA_CONSUMIVEIS
_F = {f["id"]: f for f in D["falas"]}
ORDEM_F29 = _F["fala_29"]["ordem"]               # a 1ª lição da sala dos consumíveis
POS_F29 = list(_F["fala_29"]["pos"])
POS_F34 = list(_F["fala_34"]["pos"])             # a etapa seguinte (esqueletos)


def com_estado_real(r):
    """O helper `room` troca push_state/broadcast por stubs; aqui queremos o game_state de verdade."""
    del r.push_state

    async def broadcast(msg, skip=None):
        r.messages.append(msg)
    r.broadcast = broadcast


def msgs(r, tipo):
    return [m for m in r.messages if m.get("type") == tipo]


class OleoMostraACorTests(unittest.IsolatedAsyncioTestCase):
    def test_palha_sobrevive_ao_primeiro_frasco(self):
        # o dano máximo sem crítico (1d6 + DES alto) x2 de fogo tem de deixar o boneco em pé
        self.assertGreaterEqual(def_monstro("boneco_palha")["hp"], 20)

    async def test_game_state_leva_o_evento_vulneravel_com_o_boneco_vivo(self):
        r, p = room("warrior")
        com_estado_real(r)
        marcar_comuns_ate(p, ORDEM_APOS_PEGAR)
        p["pos"] = list(POS_CONSUMIVEIS); p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        p["dex"] = 16
        p["bag"] = [{"id": "frasco_oleo", "name": "Frasco de Óleo Incendiário", "emoji": "🔥",
                     "item_slot": "bag", "effect": "throwable"}]
        palha = next(m for m in r.monsters.values() if m["type"] == "boneco_palha")
        r.messages.clear()
        with patch.object(S.random, "randint", return_value=10), patch.object(S, "roll_dice", return_value=6):
            await r.handle_throw_item(p["id"], {"item_id": "frasco_oleo", "target_id": palha["id"]})
        estados = msgs(r, "game_state")
        self.assertTrue(estados)
        ev = [e for e in estados[-1]["combat_damage_events"] if e["target_id"] == palha["id"]]
        self.assertTrue(ev and ev[0]["damage_reaction"] == "vulnerable", ev)
        self.assertGreater(ev[0]["amount"], ev[0]["raw_amount"])
        vivos = {m["id"]: m for m in estados[-1]["monsters"]}
        self.assertIn(palha["id"], vivos, "o boneco continua no estado: o cliente desenha o número")
        self.assertLess(vivos[palha["id"]]["hp"], palha["max_hp"])

    async def test_oleo_conclui_a_licao_mesmo_no_pior_dano(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, ORDEM_APOS_PEGAR)
        p["pos"] = list(POS_CONSUMIVEIS); p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        p["bag"] = [{"id": "frasco_oleo", "name": "F", "emoji": "🔥", "item_slot": "bag", "effect": "throwable"}]
        palha = next(m for m in r.monsters.values() if m["type"] == "boneco_palha")
        with patch.object(S.random, "randint", return_value=10), patch.object(S, "roll_dice", return_value=1):
            await r.handle_throw_item(p["id"], {"item_id": "frasco_oleo", "target_id": palha["id"]})
        self.assertIn("fala_30", p["licoes_feitas"])
        self.assertGreater(palha["hp"], 0)

    def test_texto_do_oleo_manda_olhar_o_numero(self):
        fala = next(f for f in D["falas"] if f["id"] == "fala_30")
        self.assertIn("vermelho", fala["texto"].lower())
        self.assertIn("vulner", fala["texto"].lower())


class VenenoSuscetivelTests(unittest.IsolatedAsyncioTestCase):
    def test_bestiario_do_boneco_envenenavel(self):
        m = def_monstro("boneco_treino_veneno")
        self.assertTrue(any(w.get("type") == "poison" and w.get("multiplier", 0) >= 2 for w in m["weaknesses"]))
        self.assertNotEqual(m["subtipo"], "construto")          # construto é imune a veneno
        self.assertNotIn("poison", m["immunities"])
        self.assertLessEqual(m["fort"], -10)                      # o Fungo Acre (CD 10) nunca é resistido
        self.assertEqual(m["movement"], 0)
        self.assertGreaterEqual(m["hp"], 16)         # aguenta golpe + alguns tiques
        # o boneco de treino comum segue como era (construto, usado nas outras salas)
        self.assertEqual(def_monstro("boneco_treino")["subtipo"], "construto")

    def test_sala_dos_consumiveis_usa_o_boneco_novo_e_o_resto_fica_igual(self):
        sala = next(r for r in D["rooms"] if r["id"] == SALA_ITENS)
        dentro = lambda pos: sala["x"] <= pos[0] < sala["x"] + sala["w"] and sala["y"] <= pos[1] < sala["y"] + sala["h"]
        venenos = [m for m in D["monsters"] if m["type"] == "boneco_treino_veneno"]
        self.assertGreaterEqual(len(venenos), 3)
        for m in venenos:
            self.assertTrue(dentro(m["pos"])); self.assertEqual(m["room_id"], SALA_ITENS)
        self.assertFalse([m for m in D["monsters"] if m["type"] == "boneco_treino" and dentro(m["pos"])])
        self.assertEqual(S.validar_dungeon(D), (True, "ok"))

    def test_fala_32_exige_o_boneco_suscetivel_e_o_guia_aponta_para_ele(self):
        fala = next(f for f in D["falas"] if f["id"] == "fala_32")
        self.assertEqual(fala["tarefa"]["alvo"], "boneco_treino_veneno")
        passos = G.guia_todos()["fala_32"]
        self.assertEqual(passos[-1]["ui"], "monstro:boneco_treino_veneno")
        self.assertIn("vermelho", fala["texto"].lower())

    async def test_veneno_tica_pelo_funil_e_sai_vulneravel(self):
        r, p = room("warrior")
        com_estado_real(r)
        m = next(x for x in r.monsters.values() if x["type"] == "boneco_treino_veneno")
        with patch.object(S.random, "randint", return_value=20):   # d20 máximo: ainda assim falha o save
            await r._aplicar_veneno(m, "veneno_fungo_acre")
        self.assertTrue(m.get("efeitos_veneno"), "o Fungo Acre pegou no boneco")
        antes = m["hp"]
        r._combat_damage_events = []
        await r._processar_venenos_turno(m)
        self.assertEqual(m["hp"], antes - 2, "1 de veneno x2")
        ev = r._combat_damage_events
        self.assertTrue(ev and ev[-1]["damage_reaction"] == "vulnerable" and ev[-1]["damage_type"] == "poison", ev)
        self.assertEqual((ev[-1]["raw_amount"], ev[-1]["amount"]), (1, 2))

    async def test_veneno_continua_sem_efeito_no_construto(self):
        r, p = room("warrior")
        m = next(x for x in r.monsters.values() if x["type"] == "boneco_treino")
        await r._aplicar_veneno(m, "veneno_fungo_acre")
        self.assertFalse(m.get("efeitos_veneno"))

    async def test_licao_32_conclui_no_boneco_novo(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, _F["fala_32"]["ordem"])
        p["pos"] = list(POS_CONSUMIVEIS); p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_32")
        await r._licao_evento(p, "atacar", alvo="boneco_treino", contexto={"veneno": True})
        self.assertEqual(p["licao_atual"], "fala_32", "boneco comum não vale mais")
        await r._licao_evento(p, "atacar", alvo="boneco_treino_veneno", contexto={"veneno": True})
        self.assertIn("fala_32", p["licoes_feitas"])


class AvancaSemTravarTests(unittest.IsolatedAsyncioTestCase):
    async def chegar_em(self, r, p, pos):
        p["pos"] = list(pos); p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))

    async def test_sair_da_zona_pula_as_etapas_abandonadas(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, ORDEM_F29)
        ouro = p.get("gold", 0)
        await self.chegar_em(r, p, POS_F29)
        self.assertEqual(p["licao_atual"], "fala_29")
        r.messages.clear()
        await self.chegar_em(r, p, POS_F34)             # foi para a etapa seguinte sem pegar os itens
        pulou = [m["licao_id"] for m in msgs(r, "licao_pulada")]
        self.assertEqual(pulou[0], "fala_29")
        self.assertEqual(set(pulou), {"fala_29", "fala_30", "fala_31", "fala_32", "fala_33"})
        self.assertEqual(sorted(p["licoes_puladas"]), sorted(pulou))
        for i in pulou:
            self.assertIn(i, p["licoes_feitas"])
            self.assertNotIn(i, p.get("tutorial_history", []))
        # só a fala_34 (cumprida de verdade ao abrir) paga; as cinco puladas não
        self.assertEqual(p.get("gold", 0), ouro + S.TUTORIAL_RECOMPENSA_OURO, "pular não paga prêmio")
        self.assertEqual(p.get("tutorial_history", []), ["fala_34"])
        self.assertTrue(any(m.get("licao_id") == "fala_34" for m in msgs(r, "fala")), "a etapa seguinte dispara")
        ordem = [m["type"] for m in r.messages if m["type"] in ("licao_pulada", "fala")]
        self.assertLess(ordem.index("licao_pulada"), ordem.index("fala"), "fecha a janela antes de abrir a nova")
        self.assertNotIn(p["licao_atual"], pulou)      # a trilha seguiu para a próxima lição de verdade

    async def test_na_mesma_zona_nada_e_pulado(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, ORDEM_F29)
        await self.chegar_em(r, p, POS_F29)
        self.assertEqual(p["licao_atual"], "fala_29")
        r.messages.clear()
        for pos in ([POS_F29[0] + 2, 15], [POS_F29[0] - 2, 15], [POS_F29[0], 17], POS_F29):
            await self.chegar_em(r, p, pos)
        self.assertEqual(p["licao_atual"], "fala_29")
        self.assertEqual(p.get("licoes_puladas", []), [])
        self.assertFalse(msgs(r, "licao_pulada"))
        self.assertFalse([m for m in msgs(r, "fala") if m.get("licao_id") == "fala_30"])

    async def test_licao_de_classe_pendente_e_pulada_ao_voltar_ao_corredor(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, 7)
        classe = [l["id"] for l in r.licoes if l.get("classe") == "warrior" and l["ordem"] < 5]
        p["licoes_feitas"] += classe
        p["licao_progresso"].update({i: 1 for i in classe})
        p["pos"] = [20, 4]; p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "treino_golpe")
        await self.chegar_em(r, p, [28, 15])        # saiu da sala exclusiva e chegou na trilha comum
        self.assertIn("treino_golpe", p["licoes_puladas"])
        self.assertEqual(p["licao_atual"], "fala_18")

    async def test_ponte_de_volta_nao_e_pulada_a_caminho_do_destino(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, 7)
        feitas = [l["id"] for l in r.licoes if l.get("classe") == "warrior" and l["id"] != "volta_warrior"]
        p["licoes_feitas"] += feitas
        p["licao_progresso"].update({i: 1 for i in feitas})
        p["licao_atual"] = "volta_warrior"; p["licao_progresso"]["volta_warrior"] = 0
        await self.chegar_em(r, p, [26, 15])
        self.assertEqual(p["licao_atual"], "volta_warrior")
        self.assertEqual(p.get("licoes_puladas", []), [])

    async def test_trilha_pulada_nao_paga_o_bonus_de_trilha(self):
        r, p = room("warrior")
        classe = [l for l in r.licoes if l.get("classe") == "warrior" and not l["id"].startswith("volta_")]
        ultima = max(classe, key=lambda l: l["ordem"])
        outros = [l["id"] for l in classe if l is not ultima]
        p["licoes_feitas"] = list(outros)               # inclui a pulada, que conta como "feita"
        p["licoes_puladas"] = [outros[0]]
        p["tutorial_history"] = [i for i in outros if i != outros[0]]
        r.messages.clear()
        await r._licao_concluir(p, ultima)
        premio = msgs(r, "licao_concluida")[0]["recompensa"]
        self.assertFalse(premio["trilha"])
        self.assertEqual(premio["ouro"], S.TUTORIAL_RECOMPENSA_OURO)
        # sem nenhuma pulada o bônus volta a sair
        p["licoes_puladas"] = []; p["tutorial_history"] = list(outros); p["licoes_feitas"] = list(outros)
        r.messages.clear()
        await r._licao_concluir(p, ultima)
        self.assertTrue(msgs(r, "licao_concluida")[0]["recompensa"]["trilha"])

    async def test_repetir_o_tutorial_limpa_as_puladas_da_classe(self):
        r, p = room("warrior")
        p["pos"] = [20, 4]
        p["licoes_puladas"] = ["treino_mira", "fala_29"]
        p["licoes_feitas"] = ["fala_5", "fala_6", "porta_warrior", "treino_mira", "fala_29"]
        p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
        await r.handle_repetir_tutorial(p["id"])
        self.assertEqual(p["licoes_puladas"], ["fala_29"])


if __name__ == "__main__":
    unittest.main()
