"""Fluxo real da Sala das Reações de Terreno (Campo de Treinamento, fatia 20): mapa, lições,
gás, porta, água e frasco de socorro, com iniciativa e handlers reais.
Roda da raiz: python -X utf8 tools/test_sala_reacoes_fluxo.py"""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402

D = json.loads((RAIZ / "dungeons" / "campo_de_treinamento.json").read_text(encoding="utf-8"))
CLASSES = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")
PORTA_SALA, PORTA_GAS, LAGO, BAU = (51, 25), (51, 32), (51, 28), (51, 29)


async def sala_real(*classes, em=(51, 24)):
    """A masmorra real do Campo de Treinamento com os heróis a um passo da sala do gás."""
    r = S.GameRoom("SALA_REACOES")
    for i, cls in enumerate(classes):
        p = S.make_player(f"h{i}", f"Aluno{i}", cls, i)
        r.players[p["id"]] = p
    r.player_order = list(r.players)
    r.load_authored_dungeon(deepcopy(D)); r.phase = "playing"
    r.msgs = []

    async def send(pid, msg):
        r.msgs.append(msg)

    async def bc(msg, *a, **k):
        r.msgs.append(msg)

    async def noop(*a, **k):
        pass
    r.send_to = send; r.broadcast = bc; r.gm_say = noop; r.push_state = noop
    r._intro_masmorra_bloqueada = lambda: False
    r._rebuild_initiative(); r.initiative_active = True
    # determinismo: veneno do gás falha sempre; explosão 1d4 no máximo; Reflexos da explosão falha
    r._testar_save = lambda alvo, tipo, cd, *a, **k: (False, 10, 0, 10)
    r._rolar_dado = lambda expr: {"1d4": 4, "1": 1, "2d6": 12}.get(expr, 3)   # máximo de cada dado

    async def falha(alvo, tipo, cd, *a, **k):
        return False, 10, 0, 10
    r._save_mostrado = falha
    feitas = [f["id"] for f in r.licoes if f.get("ordem") is not None and not f.get("classe")
              and f["ordem"] <= 35]
    for p in r.players.values():
        p["licoes_feitas"] = list(feitas); p["licao_progresso"] = {i: 1 for i in feitas}
        p["pos"] = list(em); p["moves_left"] = 30; p["action_done"] = False
        r.licoes_feitas.update(feitas)
    first = next(iter(r.players.values()))
    r.initiative_index = next(i for i, a in enumerate(r.initiative_order) if a["id"] == first["id"])
    for p in r.players.values():
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
    return r


def erros(r):
    out = [getattr(m["msg"], "key", str(m["msg"])) for m in r.msgs if m.get("type") == "error"]
    r.msgs.clear()
    return out


def gas(r):
    return next((z for z in r.zonas_especiais if z.get("id") == "gas_tutorial"), None)


def oleos(p):
    return [i for i in p["bag"] if i.get("id") == "frasco_oleo"]


async def entrar_e_pegar(r, p):
    """Abre a porta da sala do gás, atravessa até o lago e pega os frascos do baú."""
    await r.handle_open_door(p["id"], *PORTA_SALA)
    for _ in range(4):
        await r.handle_move(p["id"], 0, 1)
    assert p["pos"] == list(LAGO), p["pos"]
    bau = next(c for c in r.chests.values() if c["pos"] == list(BAU))
    await r.handle_take_all_from_chest(p["id"], bau["id"]) if hasattr(r, "handle_take_all_from_chest") \
        else None
    return bau


class FluxoTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_sala_abre_a_licao_do_gas(self):
        r = await sala_real("warrior")
        p = r.players["h0"]
        self.assertEqual(p["licao_atual"], "fala_gas")
        self.assertIsNotNone(gas(r))
        self.assertTrue(gas(r)["ativa"])
        self.assertFalse(r._door_condition_satisfied(PORTA_GAS))

    async def test_heroi_solo_completa_a_sala(self):
        r = await sala_real("warrior")
        p = r.players["h0"]
        await entrar_e_pegar(r, p)
        self.assertEqual(len(oleos(p)), 3, "o baú da ilha entrega os 3 frascos")
        p["pos"] = [51, 31]                      # colado à porta de baixo, dentro do gás
        await r.handle_open_door("h0", *PORTA_GAS)
        self.assertEqual(erros(r), ["erro.porta_exige_gas_consumido"])
        self.assertNotIn(PORTA_GAS, r.opened_doors)
        p["pos"] = list(LAGO)
        antes = p["hp"]
        await r._processar_camara_gas_inicio_turno(p)
        self.assertEqual(p["hp"], antes - 1, "o gás causa 1 de dano por turno")
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 49, "ty": 27})
        self.assertEqual(erros(r), [])
        self.assertFalse(gas(r)["ativa"], "o gás explodiu e foi consumido")
        self.assertIn("fala_gas", p["licoes_feitas"])
        self.assertNotIn("fala_gas", p.get("licoes_puladas", []))
        self.assertGreaterEqual(p["hp"], 1)
        self.assertTrue(r._door_condition_satisfied(PORTA_GAS))
        p["pos"] = [51, 31]
        await r.handle_open_door("h0", *PORTA_GAS)
        self.assertIn(PORTA_GAS, r.opened_doors)

    async def test_agua_reduz_a_explosao_pela_metade(self):
        r = await sala_real("warrior", "rogue")
        agua, terra = r.players["h0"], r.players["h1"]
        agua["pos"] = list(LAGO); terra["pos"] = [49, 27]
        agua["bag"] = [S.hidratar_itens_bau([{"id": "frasco_oleo"}])[0]]
        a0, t0 = agua["hp"], terra["hp"]
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 48, "ty": 30})
        self.assertEqual(erros(r), [])
        self.assertEqual(t0 - terra["hp"], 4, "em terra firme: dano cheio (1d4 no máximo)")
        self.assertEqual(a0 - agua["hp"], 2, "na água: metade")

    async def test_nenhuma_classe_morre_no_pior_caso(self):
        for cls in CLASSES:
            r = await sala_real(cls)
            p = r.players["h0"]
            p["pos"] = [49, 27]
            p["hp"] = p["max_hp"] - 1              # já levou 1 de veneno do gás
            p["bag"] = [S.hidratar_itens_bau([{"id": "frasco_oleo"}])[0]]
            await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 48, "ty": 30})
            self.assertFalse(gas(r)["ativa"], f"{cls}: o gás explodiu")
            perda = p["max_hp"] - 1 - p["hp"]
            self.assertTrue(1 <= perda <= 4, f"{cls}: perdeu {perda} (explosão 1d4 no máximo; o Clérigo reduz 1)")
            self.assertGreaterEqual(p["hp"], 1, cls)
            self.assertTrue(p["alive"], cls)

    async def test_chegada_tardia_pula_a_licao_e_a_porta_ja_esta_aberta(self):
        r = await sala_real("warrior", "mage", em=(51, 20))
        a, b = r.players["h0"], r.players["h1"]
        a["pos"] = list(LAGO); b["pos"] = [51, 20]
        a["bag"] = [S.hidratar_itens_bau([{"id": "frasco_oleo"}])[0]]
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 49, "ty": 27})
        self.assertFalse(gas(r)["ativa"])
        b["pos"] = [51, 24]
        await r._verificar_falas(b, r._room_containing_point(b["pos"]))
        self.assertIn("fala_gas", b["licoes_puladas"])
        self.assertNotIn("fala_gas", b["tutorial_history"] if "tutorial_history" in b else [])
        self.assertTrue(r._door_condition_satisfied(PORTA_GAS))

    async def test_sem_frasco_nao_trava(self):
        r = await sala_real("warrior")
        p = r.players["h0"]
        await entrar_e_pegar(r, p)
        p["pos"] = [51, 24]
        for _ in range(3):                           # gasta os 3 fora do gás
            p["action_done"] = False
            await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 51, "ty": 23})
        self.assertEqual(oleos(p), [])
        self.assertTrue(gas(r)["ativa"])
        await r._start_initiative_player_turn(p)
        self.assertEqual(len(oleos(p)), 1, "o frasco de socorro aparece no início do turno")
        p["pos"] = list(LAGO); p["action_done"] = False
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 49, "ty": 27})
        self.assertFalse(gas(r)["ativa"])
        self.assertTrue(r._door_condition_satisfied(PORTA_GAS))

    async def test_mago_detona_de_fora_com_bola_de_fogo(self):
        r = await sala_real("mage")
        p = r.players["h0"]
        p["level"] = 5
        p["magias_conhecidas"] = list(dict.fromkeys(p.get("magias_conhecidas", []) + ["bola_fogo"]))
        p["pos"] = list(PORTA_SALA)               # fora do piso do gás
        await r.handle_magia("h0", {"magia_id": "bola_fogo", "tx": 51, "ty": 28})
        self.assertEqual(erros(r), [])
        self.assertFalse(gas(r)["ativa"], "a Bola de Fogo detona o gás de longe")
        self.assertIn("fala_gas", p["licoes_feitas"])
        self.assertTrue(r._door_condition_satisfied(PORTA_GAS))

    async def test_parte_2_piche_e_retirada(self):
        r = await sala_real("warrior")
        p = r.players["h0"]
        gas(r)["ativa"] = False                  # o gás já foi detonado
        p["licoes_feitas"].append("fala_gas"); r.licoes_feitas.add("fala_gas")
        p["pos"] = [51, 31]
        await r.handle_open_door("h0", *PORTA_GAS)
        self.assertEqual(erros(r), [])
        p["pos"] = [49, 34]
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertEqual(p["licao_atual"], "fala_piche")
        bau = next(c for c in r.chests.values() if c["pos"] == [49, 33])
        await r.handle_take_all_from_chest("h0", bau["id"])
        self.assertTrue([i for i in p["bag"] if i["id"] == "frasco_piche"])
        await r.handle_throw_item("h0", {"item_id": "frasco_piche", "tx": 53, "ty": 37})
        self.assertEqual(erros(r), [])
        self.assertEqual(p["licao_atual"], "fala_piche", "o piche sozinho não cumpre a lição")
        p["action_done"] = False
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 53, "ty": 37})
        self.assertEqual(erros(r), [])
        self.assertIn("fala_piche", p["licoes_feitas"], "o piche aceso cumpre a lição de quem lançou")
        gelo = [(x, y) for x in (51, 52, 53) for y in (36, 37, 38)]
        for t in gelo:
            mat = r.materiais.get(t)
            base = (r._terrenos_inverno.get(t) or {}).get("base")
            self.assertTrue(mat == "agua" or base == "agua" or mat == "piche",
                            f"o gelo em {t} derrete com o piche em chamas: {mat}/{base}")
        self.assertNotIn("piso_congelado", [r.materiais.get(t) for t in ((51, 36), (51, 37), (51, 38))])

    async def test_degelo_na_coluna_fora_do_piche(self):
        r = await sala_real("warrior")
        p = r.players["h0"]
        gas(r)["ativa"] = False
        p["pos"] = [49, 34]
        self.assertEqual(r.materiais.get((51, 37)), "piso_congelado")
        # piche e óleo reais do catálogo
        p["bag"] = [S._DUNGEON_ITEM_CATALOG["frasco_piche"] | {}, S._DUNGEON_ITEM_CATALOG["frasco_oleo"] | {}]
        await r.handle_throw_item("h0", {"item_id": "frasco_piche", "tx": 53, "ty": 37})
        p["action_done"] = False
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 53, "ty": 37})
        self.assertEqual(erros(r), [])
        for y in (36, 37, 38):
            self.assertEqual(r.materiais.get((51, y)), "agua", "o gelo encostado nas chamas vira água")


async def sala_gargula(*classes):
    r = await sala_real(*classes)
    feitas = [f["id"] for f in r.licoes if f.get("ordem") is not None and not f.get("classe")
              and f["ordem"] <= 37]
    for p in r.players.values():
        p["licoes_feitas"] = list(feitas); p["licao_atual"] = None
        p["licao_progresso"] = {i: 1 for i in feitas}
        r.licoes_feitas.update(feitas)
        p["pos"] = [44, 35]
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
    return r


class GargulaTests(unittest.IsolatedAsyncioTestCase):
    async def test_armadilha_final_armada_e_gargula_liga(self):
        r = await sala_gargula("warrior")
        p = r.players["h0"]
        self.assertEqual(p["licao_atual"], "fala_gargula")
        self.assertIsNotNone(r._armadilha_no_tile(39, 35), "o teletransporte começa armado")
        garg = r._decor_by_id("decor_133")
        self.assertTrue(next(d for d in r._serializar_decoracoes() if d["id"] == "decor_133").get("interactive"),
                        "o cliente precisa saber que a gárgula é clicável")
        p["pos"] = [43, 36]
        await r.handle_interagir_decor("h0", "decor_133")
        self.assertIn("decor_mechanism", [m.get("type") for m in r.msgs])
        self.assertEqual(erros(r), [])
        await r.handle_activate_decor_mechanism("h0", "decor_133")
        self.assertEqual(erros(r), [])
        self.assertIsNone(r._armadilha_no_tile(39, 35), "a gárgula desliga o teletransporte")
        self.assertIn("fala_gargula", p["licoes_feitas"])
        self.assertEqual(r._armadilhas_do_mecanismo(garg), [])
        await r.handle_interagir_decor("h0", "decor_133")
        self.assertEqual(erros(r), ["erro.mecanismo_ja_ativado"])

    async def test_sem_a_gargula_o_teletransporte_devolve_ao_inicio(self):
        r = await sala_gargula("warrior")
        p = r.players["h0"]
        arm = r._armadilha_no_tile(39, 35)
        await r._disparar_armadilha(p, arm)
        self.assertEqual(p["pos"], [2, 15], "sem desligar, volta ao início do Campo")

    async def test_evento_vale_para_todos_e_quem_chega_depois_pula(self):
        r = await sala_gargula("warrior", "mage")
        a, b = r.players["h0"], r.players["h1"]
        self.assertEqual(b["licao_atual"], "fala_gargula")
        a["pos"] = [43, 36]
        await r.handle_activate_decor_mechanism("h0", "decor_133")
        self.assertIn("fala_gargula", a["licoes_feitas"])
        self.assertIn("fala_gargula", b["licoes_feitas"], "o mecanismo é da sala: vale para quem está na lição")
        # quem chega depois, com o mecanismo já ligado, pula a lição sem prêmio
        c = S.make_player("h9", "Tardio", "rogue", 9)
        r.players["h9"] = c
        c.update(licoes_feitas=list(a["licoes_feitas"][:-1]), licao_progresso={i: 1 for i in a["licoes_feitas"][:-1]},
                 licao_atual=None, pos=[44, 35], moves_left=5)
        await r._verificar_falas(c, r._room_containing_point(c["pos"]))
        self.assertIn("fala_gargula", c["licoes_feitas"])
        self.assertIn("fala_gargula", c["licoes_puladas"])

    async def test_retirada_na_sala_final(self):
        r = await sala_gargula("warrior")
        p = r.players["h0"]
        p["pos"] = [43, 36]
        await r.handle_activate_decor_mechanism("h0", "decor_133")
        p["pos"] = [37, 36]; p["moves_left"] = 10
        await r.handle_move("h0", -1, 0)
        self.assertEqual(p["pos"], [36, 36])
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        self.assertIn("fala_retirada", p["licoes_feitas"] + [p.get("licao_atual")])


if __name__ == "__main__":
    unittest.main()
