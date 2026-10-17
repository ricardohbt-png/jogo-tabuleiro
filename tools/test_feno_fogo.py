"""Fogo no monte de feno: vira fogueira (dano na hora, atravessável), depois cinzas.
Roda da raiz: python -X utf8 tools/test_feno_fogo.py"""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S  # noqa: E402


def sala(feno=((5, 5), (6, 5), (9, 5))):
    r = S.GameRoom("FENO")
    p = S.make_player("h0", "Ana", "warrior", 0)
    r.players["h0"] = p
    r.player_order = ["h0"]
    w, h = 14, 10
    r.tiles = [[S.FLOOR] * w for _ in range(h)]
    r.materiais = {}; r.rooms = []; r.monsters = {}; r.chests = {}
    r.decorations = []
    for i, (x, y) in enumerate(feno):
        r.decorations.append({"id": f"f{i}", "type": "monte_feno", "pos": [x, y], "facing": [0, 1],
                              "loot": None, "tem_loot": False, "image": None,
                              "model3d": S.DECOR_MODEL3D.get("monte_feno")})
    r._rebuild_decor_index()
    p["pos"] = [5, 8]
    r.msgs = []

    async def send(pid, m): r.msgs.append(m)

    async def bc(m, *a, **k): r.msgs.append(m)

    async def noop(*a, **k): pass
    r.send_to = send; r.broadcast = bc; r.gm_say = noop; r.push_state = noop
    return r


def tipos(r):
    return {d["id"]: d["type"] for d in r.decorations}


class FenoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._roll = S.roll_dice
        S.roll_dice = lambda expr: 4          # dano máximo da fogueira (1d4)

    def tearDown(self):
        S.roll_dice = self._roll

    async def test_fogo_acende_o_monte_e_os_encostados(self):
        r = sala()
        self.assertIn((5, 5), r._decor_block_tiles, "o feno bloqueia a passagem")
        await r._rx_registrar("fire", [(5, 5)])
        self.assertEqual(tipos(r), {"f0": "fogueira", "f1": "fogueira", "f2": "monte_feno"},
                         "o monte e o encostado queimam; o distante não")
        self.assertNotIn((5, 5), r._decor_block_tiles, "em chamas já dá para entrar")
        self.assertEqual(r._fire_damage_tiles.get((5, 5)), "1d4", "dano de fogueira")
        self.assertEqual(r._fire_damage_tiles.get((6, 5)), "1d4")
        tipos_msg = [m.get("type") for m in r.msgs]
        self.assertIn("reacao_elemental", tipos_msg)
        anim = next(m for m in r.msgs if m.get("type") == "spell_animation")
        self.assertEqual(anim["spell_id"], "ignicao_piche")
        self.assertEqual(sorted(map(tuple, anim["tiles"])), [(5, 5), (6, 5)], "a mesma animação do piche")

    async def test_so_fogo_acende(self):
        r = sala()
        await r._rx_registrar("cold", [(5, 5)])
        await r._rx_registrar("lightning", [(5, 5)])
        self.assertEqual(set(tipos(r).values()), {"monte_feno"})

    async def test_quem_esta_em_cima_queima_na_hora(self):
        r = sala()
        p = r.players["h0"]
        p["pos"] = [5, 5]; hp = p["hp"]
        await r._rx_registrar("fire", [(5, 5)])
        self.assertLess(p["hp"], hp)

    async def test_vira_cinzas_depois_de_tres_rodadas(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        r.round_num += 2
        await r._apagar_feno_queimado()
        self.assertEqual(tipos(r)["f0"], "fogueira", "ainda queima na terceira rodada")
        r.round_num += 1
        await r._apagar_feno_queimado()
        self.assertEqual(tipos(r), {"f0": "cinzas", "f1": "cinzas", "f2": "monte_feno"})
        self.assertNotIn((5, 5), r._fire_damage_tiles, "cinzas não queimam")
        self.assertNotIn((5, 5), r._decor_block_tiles, "cinzas não bloqueiam")
        d = next(x for x in r._serializar_decoracoes() if x["id"] == "f0")
        self.assertEqual((d["type"], d["pisavel"]), ("cinzas", True))
        self.assertIsNone(d["model3d"])
        self.assertNotIn("queima_ate", r.decorations[0])

    async def test_cinzas_nao_reacendem(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        r.round_num += 3
        await r._apagar_feno_queimado()
        await r._rx_registrar("fire", [(5, 5)])
        self.assertEqual(tipos(r)["f0"], "cinzas")

    async def test_frasco_de_oleo_real_acende_o_feno(self):
        r = sala()
        p = r.players["h0"]
        p["bag"] = [dict(S._DUNGEON_ITEM_CATALOG["frasco_oleo"])]
        p["moves_left"] = 6; p["action_done"] = False
        r._is_turn = lambda pid: True
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 5, "ty": 5})
        erros = [m for m in r.msgs if m.get("type") == "error"]
        self.assertEqual(erros, [])
        self.assertEqual(tipos(r)["f0"], "fogueira")

    async def test_passa_pela_virada_de_rodada(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        for _ in range(3):
            await r._virada_de_rodada()
        self.assertEqual(tipos(r)["f0"], "cinzas")


if __name__ == "__main__":
    unittest.main()
