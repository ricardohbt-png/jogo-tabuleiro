"""Fatia 11: Harpa Velha no baú, Nota Cortante no boneco, Alaúde e Sinfonia na Canção.

Handlers reais e push_state REAL (stub de push_state já escondeu bugs aqui)."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))
import server as S
from test_tutorial_salas import room, lesson, D
from test_tutorial_fatia8 import com_estado_real

HARPA = "instrumento_harpa_velho"
BAU = [10, 22]
BONECO = [12, 24]


def bau_da_sala(r):
    return next((c for c in r.chests.values() if c["pos"] == BAU), None)


def idx_bolsa(p, **chaves):
    return next(i for i, it in enumerate(p["bag"]) if all(it.get(k) == v for k, v in chaves.items()))


async def ate_pegar():
    r, p = room("bard"); com_estado_real(r)
    await lesson(r, p, "treino_harpa", [11, 22])
    return r, p


async def pegar_e_equipar(r, p):
    await r.handle_take_from_chest(p["id"], bau_da_sala(r)["id"], "item", 0)
    await r.handle_equip_from_bag(p["id"], idx_bolsa(p, id=HARPA))


async def ate_nota():
    r, p = await ate_pegar()
    await pegar_e_equipar(r, p)
    return r, p


class OrdemETrilhaTests(unittest.TestCase):
    def test_ordens_estritas_e_unicas_do_bardo(self):
        bard = [f for f in D["falas"] if f.get("classe") == "bard" and f.get("ordem") is not None]
        ordens = [f["ordem"] for f in bard]
        self.assertEqual(len(ordens), len(set(ordens)))
        por = {f["id"]: f["ordem"] for f in bard}
        sequencia = ["fala_13", "fala_14", "porta_bard", "treino_harpa", "treino_nota_cortante", "treino_alaude",
                     "treino_cancao", "treino_cancao_manter", "treino_cancao_parar", "treino_provocar", "volta_bard"]
        self.assertEqual(sorted(por, key=por.get), sequencia)
        self.assertNotIn("treino_instrumento", por)

    def test_bau_na_sala_43_em_chao_livre(self):
        sala = next(r for r in D["rooms"] if r["id"] == 43)
        bau = next(c for c in D["chests"] if c["pos"] == BAU)
        self.assertEqual(bau["items"], [{"id": HARPA}])
        self.assertTrue(sala["x"] <= BAU[0] < sala["x"] + sala["w"] and sala["y"] <= BAU[1] < sala["y"] + sala["h"])
        self.assertNotEqual(D["tiles"][BAU[1]][BAU[0]], S.WALL)
        self.assertNotIn(BAU, [m["pos"] for m in D["monsters"]])
        self.assertNotIn(BAU, [d["pos"] for d in D["decorations"]])
        self.assertNotIn(BAU, [t["pos"] for t in D["traps"]])
        self.assertEqual(len([c for c in D["chests"] if c["pos"] == BAU]), 1)

    def test_boneco_alinhado_com_o_alcance_da_harpa_velha(self):
        self.assertEqual(S.INSTRUMENTOS_BASE["harpa"]["stats"]["velho"]["alcance"], 3)
        self.assertIn(BONECO, [m["pos"] for m in D["monsters"] if m["type"] == "boneco_treino"])

    def test_dungeon_valida(self):
        self.assertEqual(S.validar_dungeon(D), (True, "ok"))


class FluxoTests(unittest.IsolatedAsyncioTestCase):
    async def test_bau_entrega_a_harpa_velha_na_bolsa(self):
        r, p = await ate_pegar()
        bau = bau_da_sala(r)
        self.assertEqual([i["id"] for i in bau["items"]], [HARPA])
        await r.handle_take_from_chest(p["id"], bau["id"], "item", 0)
        harpa = p["bag"][idx_bolsa(p, id=HARPA)]
        self.assertEqual((harpa["base"], harpa["qualidade"], harpa["tipo_item"]), ("harpa", "velho", "instrumento"))
        self.assertTrue(harpa["tutorial_loan"])
        self.assertEqual(p["gear"]["off_hand"]["base"], "alaude")      # ainda não equipou
        self.assertEqual(p["licao_atual"], "treino_harpa")             # pegar não basta
        self.assertIsNone(bau_da_sala(r))                              # baú vazio some, como os outros

    async def test_equipar_harpa_vai_ao_off_hand_e_alaude_a_bolsa(self):
        r, p = await ate_nota()
        self.assertEqual(p["gear"]["off_hand"]["base"], "harpa")
        self.assertTrue(any(i.get("base") == "alaude" for i in p["bag"]))
        self.assertEqual(p["licao_atual"], "treino_nota_cortante")

    async def test_nota_cortante_conclui_so_com_boneco_na_linha(self):
        r, p = await ate_nota()
        p["pos"] = [11, 22]; p["action_done"] = False; p["instrumento_usado"] = False
        r.messages.clear()
        await r.handle_usar_instrumento(p["id"], {"dir": [1, 0]})        # nada nessa linha
        self.assertEqual(p["licao_atual"], "treino_nota_cortante")
        self.assertTrue(any(m.get("type") == "error" for m in r.messages))
        await r.handle_usar_instrumento(p["id"], {})                     # sem direção
        self.assertEqual(p["licao_atual"], "treino_nota_cortante")
        p["pos"] = [12, 22]
        await r.handle_usar_instrumento(p["id"], {"dir": [0, 1]})        # boneco em [12,24], a 2 casas
        self.assertEqual(p["licao_atual"], "treino_alaude")
        self.assertIn("treino_nota_cortante", p["licoes_feitas"])
        self.assertTrue(any(m.get("type") == "spell_animation" and m.get("spell_id") == "nota_cortante"
                            for m in r.messages))

    async def test_outra_habilidade_de_instrumento_nao_conclui(self):
        r, p = await ate_nota()
        await r._licao_evento(p, "usar_instrumento", alvo="tambor")
        self.assertEqual(p["licao_atual"], "treino_nota_cortante")

    async def test_alaude_de_volta_e_sinfonia_na_cancao(self):
        r, p = await ate_nota()
        p["pos"] = [12, 22]; p["action_done"] = False
        await r.handle_usar_instrumento(p["id"], {"dir": [0, 1]})
        await r.handle_equip_from_bag(p["id"], idx_bolsa(p, base="alaude"))
        self.assertEqual(p["gear"]["off_hand"]["base"], "alaude")
        self.assertEqual(p["licao_atual"], "treino_cancao")
        # atributo que o Alaúde Velho NÃO cobre: a canção toca, a lição não conclui
        await r.handle_ativar_cancao(p["id"], {"atributos": ["dano"]})
        self.assertTrue(p["cancao_ativa"])
        self.assertEqual(p["licao_atual"], "treino_cancao")
        await r.handle_desativar_cancao(p["id"])
        await r.handle_ativar_cancao(p["id"], {"atributos": ["acerto"]})
        self.assertEqual(r._cancao_nivel_atributo(p, "acerto"), 2)       # +1 canção +1 Sinfonia
        self.assertEqual(p["licao_atual"], "treino_cancao_manter")
        self.assertIn("treino_cancao", p["licoes_feitas"])

    async def test_sem_alaude_equipado_a_cancao_nao_conclui(self):
        r, p = room("bard"); com_estado_real(r)
        await lesson(r, p, "treino_cancao", [11, 23])
        p["gear"]["off_hand"] = S.criar_instrumento("harpa", "velho")
        await r.handle_ativar_cancao(p["id"], {"atributos": ["acerto"]})
        self.assertTrue(p["cancao_ativa"])
        self.assertEqual(p["licao_atual"], "treino_cancao")

    async def test_game_state_real_traz_o_bau(self):
        r, p = await ate_pegar()
        r.messages.clear(); await r.push_state()
        est = [m for m in r.messages if m.get("type") == "game_state"][-1]
        self.assertTrue(any(c["pos"] == BAU for c in est["chests"]))


class LimpezaERepeticaoTests(unittest.IsolatedAsyncioTestCase):
    async def test_saida_devolve_o_alaude_e_remove_a_harpa(self):
        r, p = await ate_nota()
        r._training_cleanup()
        self.assertEqual(p["gear"]["off_hand"]["base"], "alaude")
        self.assertFalse(any(i.get("tutorial_loan") for i in p["bag"]))
        self.assertEqual([i for i in p["bag"] if i.get("base") == "alaude"], [])   # sem Alaúde duplicado

    async def test_saida_com_harpa_so_na_bolsa(self):
        r, p = await ate_pegar()
        await r.handle_take_from_chest(p["id"], bau_da_sala(r)["id"], "item", 0)
        r._training_cleanup()
        self.assertFalse(any(i.get("id") == HARPA for i in p["bag"]))
        self.assertEqual(p["gear"]["off_hand"]["base"], "alaude")

    async def test_repetir_tutorial_recoloca_o_bau_e_o_alaude(self):
        r, p = await ate_nota()
        sala = next(x for x in r.rooms if x.get("allowed_class") == "bard")
        p["pos"] = [sala["x"] + 1, sala["y"] + 1]
        self.assertIsNone(bau_da_sala(r))
        await r.handle_repetir_tutorial(p["id"])
        self.assertEqual(p["gear"]["off_hand"]["base"], "alaude")
        self.assertFalse(any(i.get("tutorial_loan") for i in p["bag"]))
        bau = bau_da_sala(r)
        self.assertIsNotNone(bau)
        self.assertEqual([i["id"] for i in bau["items"]], [HARPA])
        self.assertTrue(bau["items"][0]["tutorial_loan"])

    async def test_repetir_nao_duplica_a_harpa_no_bau(self):
        r, p = await ate_pegar()
        sala = next(x for x in r.rooms if x.get("allowed_class") == "bard")
        p["pos"] = [sala["x"] + 1, sala["y"] + 1]
        await r.handle_repetir_tutorial(p["id"])
        self.assertEqual([i["id"] for i in bau_da_sala(r)["items"]], [HARPA])

    async def test_foto_empacotada_e_restaurada_com_o_bau_e_o_molde(self):
        r, p = await ate_nota()
        body = S.foto_desempacotar(S.foto_empacotar(r._montar_foto(), onde="masmorra"))
        self.assertIn("baus_modelo", body["sala"]["training_state"])
        fresh, q = room("bard")
        restored = fresh._foto_aplicar_sala(body, {"bard": "nova"}, D)
        fresh.players = {"nova": restored["herois"]["bard"]}
        q = fresh.players["nova"]; q["id"] = "nova"
        self.assertEqual(q["gear"]["off_hand"]["base"], "harpa")
        self.assertTrue(q["gear"]["off_hand"]["tutorial_loan"])
        sala = next(x for x in fresh.rooms if x.get("allowed_class") == "bard")
        q["pos"] = [sala["x"] + 1, sala["y"] + 1]
        await fresh.handle_repetir_tutorial("nova")
        self.assertEqual(q["gear"]["off_hand"]["base"], "alaude")
        self.assertEqual([i["id"] for i in bau_da_sala(fresh)["items"]], [HARPA])

    async def test_outras_classes_nao_perdem_itens_na_saida(self):
        r, p = room("warrior"); com_estado_real(r)
        p["bag"].append({"id": "x", "name": "x"})
        r._training_cleanup()
        self.assertTrue(any(i["id"] == "x" for i in p["bag"]))


if __name__ == "__main__":
    unittest.main()
