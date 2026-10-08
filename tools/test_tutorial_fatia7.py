"""Fatia 7 do tutorial: boneco de palha do óleo, veneno sem beco e lição de volta ao corredor."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import server as S
import gerar_guia_comum as G
from test_tutorial_salas import room, D

CLASSES = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")
PROXIMA_SALA = [28, 15]          # onde a trilha comum (fala_18) recomeça
COMUNS = [f for f in D["falas"] if f.get("ordem") is not None and not f.get("classe")]
_FALA = {f["id"]: f for f in D["falas"]}
# Sala dos consumíveis (baú, palha, bonecos do veneno): a que contém a fala_30. Antes da sala de hostilidade era a 22;
# hoje é a 47. Os testes leem do JSON, para não cravar posição de sala.
POS_CONSUMIVEIS = list(_FALA["fala_30"]["pos"])
ORDEM_APOS_PEGAR = _FALA["fala_30"]["ordem"]      # marcar_comuns_ate(p, isto) deixa a fala_30 como próxima
SALA_CONSUMIVEIS = next(r["id"] for r in D["rooms"]
                        if r["x"] <= POS_CONSUMIVEIS[0] < r["x"] + r["w"] and r["y"] <= POS_CONSUMIVEIS[1] < r["y"] + r["h"])


def def_monstro(tipo):
    return next(m for m in S.MONSTER_DEFS if m["type"] == tipo)


def marcar_comuns_ate(p, ordem_max):
    feitas = [f["id"] for f in COMUNS if f["ordem"] < ordem_max]
    p["licoes_feitas"] = list(feitas)
    p["licao_progresso"] = {i: 1 for i in feitas}
    p["licao_atual"] = None


class BonecoPalhaTests(unittest.TestCase):
    def test_bestiario_tem_o_boneco_inflamavel(self):
        m = def_monstro("boneco_palha")
        self.assertTrue(any(w.get("type") == "fire" and w.get("multiplier", 0) >= 2 for w in m["weaknesses"]))
        self.assertGreaterEqual(m["hp"], 20)                  # fatia 8: sobrevive ao 1º frasco, para o número aparecer
        self.assertEqual(m["movement"], 0)
        self.assertEqual(S.validar_dungeon(D), (True, "ok"))

    def test_sala_dos_consumiveis_tem_palha_para_o_oleo_e_bonecos_para_o_veneno(self):
        sala = next(r for r in D["rooms"] if r["id"] == SALA_CONSUMIVEIS)
        dentro = lambda pos: sala["x"] <= pos[0] < sala["x"] + sala["w"] and sala["y"] <= pos[1] < sala["y"] + sala["h"]
        palha = [m for m in D["monsters"] if m["type"] == "boneco_palha"]
        treino = [m for m in D["monsters"] if m["type"] == "boneco_treino_veneno" and dentro(m["pos"])]
        self.assertGreaterEqual(len(palha), 2)                # folga se um morrer a golpe de espada
        self.assertGreaterEqual(len(treino), 3)               # folga para o veneno
        ocupadas = [tuple(m["pos"]) for m in D["monsters"]]
        self.assertEqual(len(ocupadas), len(set(ocupadas)))
        for m in palha:
            self.assertTrue(dentro(m["pos"]), m)
            self.assertEqual(D["tiles"][m["pos"][1]][m["pos"][0]], 1)
            self.assertEqual(m["room_id"], SALA_CONSUMIVEIS)

    def test_guia_do_oleo_aponta_o_boneco_de_palha(self):
        uis = [p.get("ui") for p in G.guia_todos()["fala_30"]]
        self.assertIn("monstro:boneco_palha", uis)
        self.assertNotIn("monstro:boneco_treino", uis)
        fala = next(f for f in D["falas"] if f["id"] == "fala_30")
        self.assertIn("palha", fala["tarefa"]["texto_curto"].lower())
        self.assertIn("fogo", fala["texto"].lower())


class OleoNoServidorTests(unittest.IsolatedAsyncioTestCase):
    async def test_oleo_fere_a_palha_e_o_veneno_ainda_tem_alvo(self):
        r, p = room("warrior")
        marcar_comuns_ate(p, ORDEM_APOS_PEGAR)
        p["pos"] = list(POS_CONSUMIVEIS); p["action_done"] = False; p["bonus_action_used"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_30")
        p["bag"] = [{"id": "frasco_oleo", "name": "Frasco de Óleo Incendiário", "emoji": "🔥",
                     "item_slot": "bag", "effect": "throwable"}]
        palha = next(m for m in r.monsters.values() if m["type"] == "boneco_palha" and m["hp"] > 0)
        # pior caso do jogador: acerta sem crítico e rola o mínimo de dano
        with patch.object(S.random, "randint", return_value=10), patch.object(S, "roll_dice", return_value=1):
            await r.handle_throw_item(p["id"], {"item_id": "frasco_oleo", "target_id": palha["id"]})
        self.assertLess(palha["hp"], palha["max_hp"], "o óleo machucou a palha")
        self.assertIn("fala_30", p["licoes_feitas"])
        self.assertEqual(p["licao_atual"], "fala_31")
        treino = [m for m in r.monsters.values() if m["type"] == "boneco_treino_veneno" and m["room_id"] == SALA_CONSUMIVEIS and m["hp"] > 0]
        self.assertGreaterEqual(len(treino), 3)
        self.assertTrue(all(m["hp"] == m["max_hp"] for m in treino), "o óleo não encostou nos bonecos do veneno")
        # veneno: unta e acerta um boneco de treino sem travar
        await r._licao_evento(p, "usar_item", alvo="veneno_fungo_acre")
        self.assertEqual(p["licao_atual"], "fala_32")
        await r._licao_evento(p, "atacar", alvo="boneco_treino_veneno", contexto={"veneno": True})
        self.assertIn("fala_32", p["licoes_feitas"])
        self.assertEqual(p["licao_atual"], "fala_33")

    async def test_oleo_no_boneco_de_treino_ainda_conclui_a_licao(self):
        # lançar no boneco errado gasta o único frasco: a lição não pode travar por isso
        r, p = room("warrior")
        marcar_comuns_ate(p, ORDEM_APOS_PEGAR)
        p["pos"] = list(POS_CONSUMIVEIS); p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        await r._licao_evento(p, "arremessar_item", alvo="frasco_oleo")
        self.assertIn("fala_30", p["licoes_feitas"])


def ultima_real(r, cls):
    lic = [f for f in r.licoes if f.get("classe") == cls and not f["id"].startswith(("porta_", "volta_"))]
    return max(lic, key=lambda f: f["ordem"])


class VoltaAoCorredorTests(unittest.IsolatedAsyncioTestCase):
    def test_uma_licao_de_volta_por_classe_logo_apos_a_ultima(self):
        falas = {f["id"]: f for f in D["falas"]}
        guia = G.guia_todos()
        for cls in CLASSES:
            f = falas[f"volta_{cls}"]
            real = max((x for x in D["falas"] if x.get("classe") == cls and x.get("sala_exclusiva")),
                       key=lambda x: x["ordem"])
            sala = next(r for r in D["rooms"] if r.get("allowed_class") == cls)
            porta = tuple(sala["doors"][0])
            self.assertEqual(f["ordem"], real["ordem"] + 1, cls)
            self.assertEqual(f["pos"], real["pos"], cls)
            self.assertEqual(f["trigger"], {"tipo": "sala"}, cls)
            self.assertFalse(f.get("sala_exclusiva"), cls)        # concluir acontece fora da sala
            self.assertEqual(f["tarefa"]["tipo"], "mover_ate")
            self.assertEqual(f["tarefa"]["alvo"], PROXIMA_SALA)
            passos = guia[f"volta_{cls}"]
            self.assertEqual(len(passos), 2)
            # 1º passo: sair pela porta (conclui ao pisar nela); último: a casa da próxima sala
            self.assertEqual(passos[0]["ui"], "porta:" + json.dumps(list(porta)).replace(" ", ""))
            self.assertEqual(passos[0]["conclui"], {"tipo": "mover_ate", "alvo": list(porta)})
            self.assertEqual(passos[-1]["ui"], "casa:[28,15]")
            self.assertFalse(passos[-1].get("conclui"))
            self.assertIn("corredor", passos[0]["texto"][0].lower())
            self.assertIn("próxima sala", passos[-1]["texto"][0].lower())
        self.assertEqual(D["tiles"][15][28], 1)
        self.assertFalse([m for m in D["monsters"] if m["pos"] == PROXIMA_SALA])
        self.assertFalse([c for c in D["chests"] if c["pos"] == PROXIMA_SALA])

    async def test_fluxo_selo_premio_depois_mensagem_e_chegada(self):
        for cls in CLASSES:
            r, p = room(cls)
            ult = ultima_real(r, cls)
            feitas = [f["id"] for f in r.licoes if f.get("classe") == cls and f["ordem"] < ult["ordem"]]
            p["licoes_feitas"] = list(feitas)
            p["licao_progresso"] = {i: 1 for i in feitas}
            marcar_ate = [f["id"] for f in COMUNS if f["ordem"] <= 5]
            p["licoes_feitas"] += marcar_ate
            for i in marcar_ate: p["licao_progresso"][i] = 1
            p["tutorial_history"] = []
            p["pos"] = list(ult["pos"]); p["licao_atual"] = None
            await r._verificar_falas(p, r._room_containing_point(p["pos"]))
            self.assertEqual(p["licao_atual"], ult["id"], cls)
            ouro0 = p["gold"]
            r.messages.clear()
            await r._licao_concluir(p, ult)
            await r._verificar_falas(p, r._room_containing_point(p["pos"]))
            tipos = [(m["type"], m.get("licao_id")) for m in r.messages if m.get("licao_id")]
            self.assertEqual(tipos[0], ("licao_concluida", ult["id"]), (cls, tipos))
            self.assertEqual(tipos[1], ("fala", f"volta_{cls}"), (cls, tipos))   # a mensagem vem DEPOIS do selo
            self.assertEqual(p["licao_atual"], f"volta_{cls}")
            premio_ult = next(m for m in r.messages if m["type"] == "licao_concluida")["recompensa"]
            self.assertTrue(premio_ult["trilha"], "o bônus da trilha fica na última lição de verdade")
            ouro1 = p["gold"]
            self.assertEqual(ouro1 - ouro0, premio_ult["ouro"])
            sala = next(x for x in D["rooms"] if x.get("allowed_class") == cls)
            porta = list(sala["doors"][0])
            # andar numa casa qualquer não faz nada; a porta avança o passo; a chegada conclui
            await r._licao_evento(p, "mover_ate", alvo=[1, 1])
            self.assertEqual(p["licao_passo"], 0)
            await r._licao_evento(p, "mover_ate", alvo=porta)
            self.assertEqual((p["licao_atual"], p["licao_passo"]), (f"volta_{cls}", 1), cls)
            r.messages.clear()
            p["pos"] = list(PROXIMA_SALA)
            await r._licao_evento(p, "mover_ate", alvo=list(PROXIMA_SALA))
            self.assertIn(f"volta_{cls}", p["licoes_feitas"])
            conc = [m for m in r.messages if m["type"] == "licao_concluida" and m["licao_id"] == f"volta_{cls}"][0]
            self.assertFalse(conc["recompensa"]["trilha"], "bônus da trilha não se paga duas vezes")
            # a volta paga o prêmio comum (+ o da fala_17, que só explica e dispara em seguida)
            self.assertEqual(p["gold"] - ouro1, conc["recompensa"]["ouro"] + S.TUTORIAL_RECOMPENSA_OURO)
            self.assertLess(conc["recompensa"]["ouro"], 25)
            # e a trilha comum recomeça sozinha
            self.assertEqual(p["licao_atual"], "fala_18", cls)

    async def test_repetir_tutorial_tambem_refaz_a_volta(self):
        r, p = room("warrior")
        sala = next(x for x in D["rooms"] if x.get("allowed_class") == "warrior")
        p["pos"] = [sala["x"] + 1, sala["y"] + 1]
        p["licoes_feitas"] = [f["id"] for f in r.licoes if f.get("classe") == "warrior"]
        p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
        p["licao_atual"] = None
        r.licoes_feitas.update(p["licoes_feitas"])
        await r.handle_repetir_tutorial(p["id"])
        self.assertNotIn("volta_warrior", p["licoes_feitas"])
        self.assertNotIn("treino_mira", p["licoes_feitas"])
        self.assertIn("porta_warrior", p["licoes_feitas"])


if __name__ == "__main__":
    unittest.main()
