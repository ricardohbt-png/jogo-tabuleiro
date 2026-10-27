"""Placas da Besta: +3 CA, reduz 1 de cada instância de dano físico, resistente à corrosão.
Rode da raiz: python -X utf8 tools/test_placas_da_besta.py"""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(classe="warrior"):
    r = S.GameRoom("PLACAS")
    msgs = []

    async def noop(*a, **k):
        return None

    async def send(pid, msg, *a, **k):
        msgs.append(msg)

    r.send_to = send
    r.gm_say = r.broadcast = r.push_state = r.push_state_or_city = r.broadcast_city_state = noop
    p = S.make_player("p1", "Ana", classe, 0)
    p["gold"] = 1000
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"
    return r, p, msgs


class PlacasDaBestaTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_e_ferreiros_das_cinco_cidades(self):
        item = next(i for i in S.SHOP_ARMORS if i["id"] == "placas_da_besta")
        base = next(i for i in S.SHOP_ARMORS if i["id"] == "leather_plate")
        self.assertEqual((item["price"], item["ac_bonus"], item["kind"]), (250, 3, "armor"))
        self.assertEqual(item["allowed_classes"], base["allowed_classes"])
        self.assertEqual(sorted(item["allowed_classes"]), ["bard", "paladin", "rogue", "warrior"])
        self.assertEqual(item["corrosao_resistente"], 4)
        self.assertEqual(item["corrosao_niveis_penalidade"], 2)
        self.assertEqual(item["icon"], "assets/itens/placas_da_besta.png")
        self.assertTrue((RAIZ / item["icon"]).is_file())
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        ferreiros = [c for c, l in lojas.items() if "ferreiro_armor" in l]
        self.assertEqual(len(ferreiros), 5)
        for cidade in ferreiros:
            ids = [i["id"] if isinstance(i, dict) else i for i in lojas[cidade]["ferreiro_armor"]]
            self.assertEqual(ids.count("placas_da_besta"), 1, cidade)

    async def _compra_e_equipa(self, r, p):
        await r.handle_shop_buy("p1", "ferreiro_armor", "placas_da_besta")
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == "placas_da_besta")
        await r.handle_equip_from_bag("p1", indice)

    async def test_equipar_soma_3_de_ca_e_reduz_1_de_dano_fisico(self):
        r, p, _ = sala("warrior")
        ca = p["ac"]
        anterior = int((p["gear"].get("armor") or {}).get("ac_bonus", 0))
        fisico = r._apply_damage_types(10, [S.DMG_PHYSICAL], p)
        await self._compra_e_equipa(r, p)
        self.assertEqual(p["gold"], 750)
        self.assertEqual(p["gear"]["armor"]["id"], "placas_da_besta")
        self.assertEqual(p["ac"], ca - anterior + 3)
        self.assertEqual(r._apply_damage_types(10, [S.DMG_PHYSICAL], p), fisico - 1)

    async def test_nao_reduz_dano_nao_fisico(self):
        r, p, _ = sala("warrior")
        fogo = r._apply_damage_types(10, ["fire"], p)
        await self._compra_e_equipa(r, p)
        self.assertEqual(r._apply_damage_types(10, ["fire"], p), fogo)

    async def test_cada_instancia_reduz_1_e_desequipar_remove(self):
        r, p, _ = sala("warrior")
        antes = r._apply_damage_types(10, [S.DMG_PHYSICAL], p)
        await self._compra_e_equipa(r, p)
        self.assertEqual(r._apply_damage_types(10, [S.DMG_PHYSICAL], p), antes - 1)
        self.assertEqual(r._apply_damage_types(10, [S.DMG_PHYSICAL], p), antes - 1)  # sem acumular entre golpes
        await r.handle_unequip("p1", "armor")
        self.assertEqual(r._apply_damage_types(10, [S.DMG_PHYSICAL], p), antes)

    async def test_tolera_4_niveis_de_corrosao_sem_penalidade(self):
        r, p, _ = sala("warrior")
        await self._compra_e_equipa(r, p)
        monstro = {"id": "m1", "name": "Devorador", "hp": 10, "max_hp": 20}
        penalidades = []
        for _ in range(7):
            await r._corroer_equipamento(monstro, p, S.CORROSAO_ARMADURA_METAL, set(), notify=False)
            penalidades.append(r._corrosao_ca_pen(p))
        self.assertEqual(penalidades[:4], [0, 0, 0, 0])
        self.assertEqual(penalidades[4:6], [1, 2])
        self.assertTrue(r._corr(p).get("armadura_destruida"))

    async def test_mago_nao_pode_comprar(self):
        r, p, msgs = sala("mage")
        await r.handle_shop_buy("p1", "ferreiro_armor", "placas_da_besta")
        self.assertEqual(p["gold"], 1000)
        self.assertTrue([m for m in msgs if m.get("type") == "error"])


if __name__ == "__main__":
    unittest.main()
