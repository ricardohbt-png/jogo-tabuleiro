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


def zona_feno(r):
    return next((z for z in r.zonas_especiais if z.get("feno") and z.get("ativa")), None)


class FenoTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._roll = S.roll_dice
        S.roll_dice = lambda expr: 4          # dano máximo do 1d4
        self.r0 = None

    def tearDown(self):
        S.roll_dice = self._roll

    async def test_fogo_acende_o_monte_e_os_encostados_sem_trocar_a_imagem(self):
        r = sala()
        self.assertIn((5, 5), r._decor_block_tiles, "o feno bloqueia a passagem")
        await r._rx_registrar("fire", [(5, 5)])
        self.assertEqual(set(tipos(r).values()), {"monte_feno"}, "continua sendo feno: nada de fogueira")
        self.assertEqual([d["id"] for d in r.decorations if d.get("queimando")], ["f0", "f1"],
                         "queimam o monte e o encostado; o distante não")
        z = zona_feno(r)
        self.assertEqual((z["tipo"], z["dado"]), ("chamas_piche", "1d4"), "as chamas do piche, dano de fogueira")
        self.assertEqual(sorted(map(tuple, z["tiles"])), [(5, 5), (6, 5)])
        self.assertEqual(z["expira_em"], r.round_num + 3)
        self.assertNotIn((5, 5), r._decor_block_tiles, "em chamas já dá para entrar")
        self.assertEqual(r._fire_damage_tiles, {}, "o dano vem da zona, não de uma fogueira")
        anim = next(m for m in r.msgs if m.get("type") == "spell_animation")
        self.assertEqual(anim["spell_id"], "ignicao_piche", "a mesma animação do piche")
        self.assertIn("incendio", [m.get("tipo") for m in r.msgs if m.get("type") == "reacao_elemental"])
        d = next(x for x in r._serializar_decoracoes() if x["id"] == "f0")
        self.assertEqual(d["type"], "monte_feno")

    async def test_so_fogo_acende(self):
        r = sala()
        await r._rx_registrar("cold", [(5, 5)])
        await r._rx_registrar("lightning", [(5, 5)])
        self.assertIsNone(zona_feno(r))

    async def test_quem_esta_em_cima_queima_na_hora_sem_pegar_fogo(self):
        r = sala()
        p = r.players["h0"]
        p["pos"] = [5, 5]; hp = p["hp"]
        await r._rx_registrar("fire", [(5, 5)])
        self.assertEqual(p["hp"], hp - 4, "1d4 de fogo na hora")
        self.assertFalse(p.get("em_chamas_rodadas"), "como a fogueira: não incendeia o herói")

    async def test_dano_por_rodada_no_inicio_do_turno(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        p = r.players["h0"]
        p["pos"] = [6, 5]; hp = p["hp"]
        await r._processar_zona_molochus_inicio_turno(p)
        self.assertEqual(p["hp"], hp - 4)

    async def test_apos_tres_rodadas_some_e_deixa_fuligem(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        r.msgs.clear()
        for _ in range(2):
            await r._virada_de_rodada()
        self.assertTrue(zona_feno(r), "ainda arde na terceira rodada")
        self.assertEqual(len(r.decorations), 3)
        await r._virada_de_rodada()
        self.assertIsNone(zona_feno(r))
        self.assertEqual([d["id"] for d in r.decorations], ["f2"], "os montes queimados somem")
        self.assertNotIn((5, 5), r._decor_block_tiles)
        fuligem = [m for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "fuligem"]
        self.assertEqual(len(fuligem), 1)
        self.assertEqual(sorted(map(tuple, fuligem[0]["casas"])), [(5, 5), (6, 5)])

    async def test_feno_queimado_nao_reacende(self):
        r = sala()
        await r._rx_registrar("fire", [(5, 5)])
        antes = len([z for z in r.zonas_especiais if z.get("feno")])
        await r._rx_registrar("fire", [(5, 5)])
        self.assertEqual(len([z for z in r.zonas_especiais if z.get("feno")]), antes)

    async def test_frasco_de_oleo_real_acende_o_feno(self):
        r = sala()
        p = r.players["h0"]
        p["bag"] = [dict(S._DUNGEON_ITEM_CATALOG["frasco_oleo"])]
        p["moves_left"] = 6; p["action_done"] = False
        r._is_turn = lambda pid: True
        await r.handle_throw_item("h0", {"item_id": "frasco_oleo", "tx": 5, "ty": 5})
        self.assertEqual([m for m in r.msgs if m.get("type") == "error"], [])
        self.assertTrue(zona_feno(r))


class ClienteTests(unittest.TestCase):
    def test_fuligem_do_feno_usa_a_marca_da_explosao_de_gas(self):
        js = (RAIZ / "game.js").read_text(encoding="utf-8")
        self.assertIn("msg.tipo === 'explosao_gas' || msg.tipo === 'fuligem'", js)
        self.assertIn("if(msg.tipo !== 'fuligem') _reacoesAnims.push", js)
        est = (RAIZ / "src" / "reacoesElementais.js").read_text(encoding="utf-8")
        self.assertIn("fuligem:", est)


if __name__ == "__main__":
    unittest.main()
