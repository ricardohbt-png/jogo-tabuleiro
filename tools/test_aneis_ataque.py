"""Anéis da Precisão, do Impacto e da Supremacia.
Rode da raiz: python -X utf8 tools/test_aneis_ataque.py"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(ouro=1000):
    r = S.GameRoom("ANEIS_TESTE")
    p = S.make_player("p1", "Ana", "warrior", 0)
    p["gold"] = ouro
    r.players["p1"] = p
    r.player_order = ["p1"]
    r.phase = "city"

    async def noop(*a, **k):
        pass

    r.send_to = noop
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.broadcast_city_state = noop
    r.push_state_or_city = noop
    return r, p


def dano_fixo(r, p):
    return r._bonus_fixo_dano_arma(p, p.get("weapon") or {}, 0, 0, 0, 0)


class AneisAtaqueTests(unittest.IsolatedAsyncioTestCase):
    def test_catalogo_precos_e_estoque(self):
        por_id = {i["id"]: i for i in S.SHOP_MERCHANT}
        self.assertEqual((por_id["ring_str"]["name"], por_id["ring_str"]["price"]),
                         ("Anel da Precisão", 50))
        self.assertEqual(por_id["anel_impacto"]["price"], 80)
        self.assertEqual(por_id["anel_supremacia"]["price"], 200)
        for i in ("ring_str", "anel_impacto", "anel_supremacia"):
            self.assertTrue((RAIZ / por_id[i]["icon"]).is_file(), i)
        lojas = json.loads((RAIZ / "city_shops.json").read_text(encoding="utf-8"))
        mercadores = [c for c, l in lojas.items() if "mercador" in l]
        self.assertEqual(len(mercadores), 5)
        for cidade in mercadores:
            ids = [i["id"] if isinstance(i, dict) else i for i in lojas[cidade]["mercador"]]
            for i in ("ring_str", "anel_impacto", "anel_supremacia"):
                self.assertEqual(ids.count(i), 1, f"{cidade}:{i}")

    async def _equipa(self, r, p, item_id):
        await r.handle_shop_buy("p1", "mercador", item_id)
        indice = next(i for i, it in enumerate(p["bag"]) if it["id"] == item_id)
        await r.handle_equip_from_bag("p1", indice)

    async def test_precisao_soma_acerto_sem_dano(self):
        r, p = sala()
        atk, dano = p["atk_bonus"], dano_fixo(r, p)
        await self._equipa(r, p, "ring_str")
        self.assertEqual(p["atk_bonus"], atk + 1)
        self.assertEqual(dano_fixo(r, p), dano)
        await r.handle_unequip("p1", "ring1")
        self.assertEqual(p["atk_bonus"], atk)

    async def test_impacto_soma_dano_sem_acerto(self):
        r, p = sala()
        atk, dano = p["atk_bonus"], dano_fixo(r, p)
        await self._equipa(r, p, "anel_impacto")
        self.assertEqual(dano_fixo(r, p), dano + 1)
        self.assertEqual(p["atk_bonus"], atk)
        await r.handle_unequip("p1", "ring1")
        self.assertEqual(dano_fixo(r, p), dano)
        self.assertEqual(p.get("gear_damage_bonus", 0), 0)

    async def test_supremacia_soma_os_dois_e_acumula_com_impacto(self):
        r, p = sala()
        atk, dano = p["atk_bonus"], dano_fixo(r, p)
        await self._equipa(r, p, "anel_supremacia")
        self.assertEqual(p["atk_bonus"], atk + 1)
        self.assertEqual(dano_fixo(r, p), dano + 1)
        await self._equipa(r, p, "anel_impacto")
        self.assertEqual(dano_fixo(r, p), dano + 2)
        await r.handle_unequip("p1", "ring1")
        await r.handle_unequip("p1", "ring2")
        self.assertEqual(p["atk_bonus"], atk)
        self.assertEqual(dano_fixo(r, p), dano)


if __name__ == "__main__":
    unittest.main()
