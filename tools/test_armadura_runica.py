"""Armadura Rúnica: +7 CA, exclusiva de Guerreiro/Paladino, Barreira Arcana ou Proteção
contra Energia por 5 rodadas (ação principal, recarga compartilhada de 30 rodadas).
Rode da raiz: python -X utf8 tools/test_armadura_runica.py"""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(classe="warrior", equipada=True):
    r = S.GameRoom("RUNICA")
    msgs = []

    async def noop(*a, **k):
        return None

    async def send(pid, msg, *a, **k):
        msgs.append(msg)

    r.send_to = send
    r.gm_say = r.broadcast = r.push_state = noop
    r._is_turn = lambda pid: True
    p = S.make_player("p1", "Ana", classe, 0)
    p["gold"] = 5000
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.round_num = 1
    r.phase = "playing"
    if equipada:
        p["gear"]["armor"] = deepcopy(next(i for i in S.SHOP_ARMORS if i["id"] == "armadura_runica"))
    return r, p, msgs


def erros(msgs):
    return [m for m in msgs if m.get("type") == "error"]


class ArmaduraRunicaTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_ferreiros_das_cinco_cidades(self):
        item = next(i for i in S.SHOP_ARMORS if i["id"] == "armadura_runica")
        placas = next(i for i in S.SHOP_ARMORS if i["id"] == "plate_armor") \
            if any(i["id"] == "plate_armor" for i in S.SHOP_ARMORS) else None
        self.assertEqual((item["price"], item["ac_bonus"], item["armor_category"]),
                         (2500, 7, "pesada"))
        self.assertEqual(sorted(item["allowed_classes"]), ["paladin", "warrior"])
        self.assertEqual(item["icon"], "assets/itens/armadura_runica.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        if placas:
            self.assertEqual(item["allowed_classes"], placas.get("allowed_classes", item["allowed_classes"]))
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        ferreiros = [c for c, l in lojas.items() if "ferreiro_armor" in l]
        self.assertEqual(len(ferreiros), 5)
        for cidade in ferreiros:
            ids = [i["id"] if isinstance(i, dict) else i for i in lojas[cidade]["ferreiro_armor"]]
            self.assertEqual(ids.count("armadura_runica"), 1, cidade)

    def test_id_do_loot_do_gigante_runico_continua_valido(self):
        self.assertIn("armadura_runica", S._DUNGEON_ITEM_CATALOG)

    async def test_guerreiro_compra_e_equipa_e_a_armadura_vale_7_de_ca(self):
        r, p, msgs = sala("warrior", equipada=False)
        r.phase = "city"
        ca = p["ac"]
        anterior = int((p["gear"].get("armor") or {}).get("ac_bonus", 0))
        await r.handle_shop_buy("p1", "ferreiro_armor", "armadura_runica")
        self.assertEqual(p["gold"], 2500)
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == "armadura_runica")
        await r.handle_equip_from_bag("p1", indice)
        self.assertEqual(p["gear"]["armor"]["id"], "armadura_runica")
        self.assertEqual(p["ac"], ca - anterior + 7)

    async def test_ladino_nao_pode_comprar(self):
        r, p, msgs = sala("rogue", equipada=False)
        r.phase = "city"
        await r.handle_shop_buy("p1", "ferreiro_armor", "armadura_runica")
        self.assertEqual(p["gold"], 5000)
        self.assertTrue(erros(msgs))

    async def test_barreira_arcana_por_5_rodadas_sem_gastar_slot(self):
        r, p, msgs = sala()
        slots = deepcopy(p.get("slots_remaining"))
        await r.handle_use_runic_armor("p1", {"spell_id": "barreira_arcana"})
        self.assertEqual(erros(msgs), [])
        self.assertEqual(p["barreira_arcana_rodadas"], 5)
        self.assertTrue(p["action_done"])
        self.assertEqual(p["gear"]["armor"]["armadura_runica_pronta_em"], 31)
        self.assertEqual(p.get("slots_remaining"), slots)

    async def test_protecao_energia_por_5_rodadas(self):
        r, p, msgs = sala()
        await r.handle_use_runic_armor("p1", {"spell_id": "protecao_energia"})
        self.assertEqual(erros(msgs), [])
        self.assertEqual(p["protecao_rodadas"], 5)

    async def test_recarga_compartilhada_entre_as_duas_protecoes(self):
        r, p, msgs = sala()
        await r.handle_use_runic_armor("p1", {"spell_id": "barreira_arcana"})
        p["action_done"] = False
        r.round_num = 20
        await r.handle_use_runic_armor("p1", {"spell_id": "protecao_energia"})
        self.assertTrue(erros(msgs))
        self.assertNotIn("protecao_rodadas", {k for k, v in p.items() if v})
        msgs.clear()
        r.round_num = 31
        await r.handle_use_runic_armor("p1", {"spell_id": "protecao_energia"})
        self.assertEqual(erros(msgs), [])
        self.assertEqual(p["protecao_rodadas"], 5)

    async def test_sem_a_armadura_equipada_ou_magia_invalida_recusa(self):
        r, p, msgs = sala(equipada=False)
        await r.handle_use_runic_armor("p1", {"spell_id": "barreira_arcana"})
        self.assertTrue(erros(msgs))
        r, p, msgs = sala()
        await r.handle_use_runic_armor("p1", {"spell_id": "bola_fogo"})
        self.assertTrue(erros(msgs))
        self.assertFalse(p.get("action_done"))

    async def test_acao_principal_ja_usada_recusa_sem_gastar_recarga(self):
        r, p, msgs = sala()
        p["action_done"] = True
        await r.handle_use_runic_armor("p1", {"spell_id": "barreira_arcana"})
        self.assertTrue(erros(msgs))
        self.assertNotIn("armadura_runica_pronta_em", p["gear"]["armor"])

    def test_habilidades_aparecem_so_para_guerreiro_ou_paladino_com_a_armadura(self):
        r, p, _ = sala("warrior")
        ids = [h["id"] for h in r._runic_armor_skills(p)]
        self.assertEqual(ids, ["usar_armadura_runica_barreira_arcana",
                               "usar_armadura_runica_protecao_energia"])
        r2, p2, _ = sala("warrior", equipada=False)
        self.assertEqual(r2._runic_armor_skills(p2), [])
        r3, p3, _ = sala("mage")
        self.assertEqual(r3._runic_armor_skills(p3), [])


if __name__ == "__main__":
    unittest.main()
