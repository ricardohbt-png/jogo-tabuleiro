"""Bardo da Caravana: Canção, Provocação, arma/instrumento sorteados e habilidade do instrumento.
Roda da raiz: python -X utf8 tools/test_bardo_caravana.py"""
import asyncio
import os
import random
import sys
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_montanha as G

G.garantir_registros(gravar=False)
TIPO = "bardo_da_caravana"


def ficha():
    return next(m for m in S.MONSTER_DEFS if m["type"] == TIPO)


def sala(herois=(("p0", "warrior"),)):
    r = S.GameRoom("BARDO")
    for i, (pid, cls) in enumerate(herois):
        r.players[pid] = S.make_player(pid, f"H{i}", cls, i)
    r.host_pid = herois[0][0]; r.phase = "playing"
    r.tiles = [[S.FLOOR] * 20 for _ in range(12)]
    r.map_w, r.map_h = 20, 12
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 20, "h": 12, "cx": 10, "cy": 6, "locked": False, "doors": []}]
    msgs = []

    async def nada(*a, **k): pass

    async def gm(*a, **k): msgs.append(a[0])
    r.send_to = nada; r.broadcast = nada; r.push_state = nada; r.gm_say = gm
    r.msgs = msgs
    return r


def bardo(r, pos, instrumento=None, arma=None):
    m = S.make_monster(ficha(), r.rooms[0])
    for k in ("instrumento", "instrumento_pronto_em"):
        m.pop(k, None)
    m["pos"] = list(pos); m["alertado"] = True
    if instrumento:
        m["instrumento"] = S.criar_instrumento(*instrumento); m["instrumento_pronto_em"] = 0
    r.monsters[m["id"]] = m
    return m


def alvos(r):
    return [{"kind": "player", "obj": p} for p in r.players.values()]


class FichaTests(unittest.TestCase):
    def test_habilidades_de_bardo(self):
        ids = {a["id"] for a in ficha()["special_abilities"]}
        self.assertEqual(ids, {"hero_bard_cancao_heroica", "hero_bard_provocacao"})
        self.assertTrue(ficha()["equipment_enabled"])

    def test_sorteio_de_arma_e_instrumento(self):
        random.seed(7)
        r = sala(); n = 600; arma = inst = ambos = 0
        bases = set()
        for _ in range(n):
            m = S.make_monster(ficha(), r.rooms[0])
            a = bool(m.get("equipped_items")); i = bool(m.get("instrumento"))
            arma += a; inst += i; ambos += a and i
            if i:
                bases.add(m["instrumento"]["base"])
                self.assertEqual(m["instrumento"]["origem"], "humana")
            if a:
                self.assertEqual(m["attacks"][0]["name"], S._DUNGEON_ITEM_CATALOG[m["equipped_items"][0]]["name"])
        self.assertAlmostEqual(arma / n, 0.70, delta=0.07)
        self.assertAlmostEqual(inst / n, 0.60, delta=0.07)
        self.assertGreater(ambos, 0)
        self.assertEqual(bases, {"harpa", "tambor", "trompa", "alaude", "sino", "lira", "flauta"})


class IaTests(unittest.TestCase):
    def test_provocacao_prende_o_heroi_no_bardo(self):
        r = sala(); m = bardo(r, (5, 5)); r.players["p0"]["pos"] = [7, 5]
        self.assertTrue(asyncio.run(r._monster_bardo_provocar(m, alvos(r))))
        p = r.players["p0"]
        self.assertEqual(p["runico_provocado_por"], m["id"])
        self.assertGreaterEqual(p["runico_provocacao_ate"], r.round_num)
        # recarga: não provoca de novo o mesmo herói nem gasta o 2º uso à toa
        self.assertFalse(asyncio.run(r._monster_bardo_provocar(m, alvos(r))))
        self.assertEqual(m["monster_ability_uses"]["hero_bard_provocacao"], 1)

    def test_provocacao_respeita_alcance(self):
        r = sala(); m = bardo(r, (1, 1)); r.players["p0"]["pos"] = [15, 9]
        self.assertFalse(asyncio.run(r._monster_bardo_provocar(m, alvos(r))))

    def test_heroi_provocado_so_ataca_o_bardo(self):
        r = sala(); m = bardo(r, (5, 5)); r.players["p0"]["pos"] = [6, 5]
        outro = bardo(r, (6, 6))
        asyncio.run(r._monster_bardo_provocar(m, alvos(r)))
        erros = []

        async def send(pid, msg): erros.append(msg)
        r.send_to = send; r._is_turn = lambda pid: True
        r.players["p0"]["action_done"] = False
        asyncio.run(r.handle_attack("p0", outro["id"], None, []))
        self.assertTrue(erros and erros[0]["type"] == "error")
        self.assertIn("Provocação", str(erros[0]["msg"]))
        self.assertEqual(outro["hp"], outro["max_hp"])

    def test_cancao_vai_pela_ia(self):
        r = sala(); m = bardo(r, (5, 5)); r.players["p0"]["pos"] = [12, 5]
        usou = asyncio.run(r._monster_try_editor_ability(m, alvos(r)))
        self.assertTrue(usou)
        self.assertTrue(m["cancao_ativa"])
        self.assertTrue(m.pop("_monster_editor_action_consumed"))

    def test_alaude_reforca_a_cancao(self):
        r = sala(); m = bardo(r, (5, 5), ("alaude", "padrao")); aliado = bardo(r, (6, 5))
        r._ativar_cancao_monstro(m, ["acerto", "ca"])
        self.assertEqual(r._cancao_monstro_bonus(aliado, "acerto"), 2)    # 1 + Sinfonia
        m2 = bardo(r, (15, 5)); r._ativar_cancao_monstro(m2, ["acerto"])
        a2 = bardo(r, (16, 5))
        self.assertEqual(r._cancao_monstro_bonus(a2, "acerto"), 1)        # sem alaúde

    def _instrumento(self, base, pos_heroi, pos_bardo=(5, 5), qual="padrao"):
        r = sala(); m = bardo(r, pos_bardo, (base, qual)); r.players["p0"]["pos"] = list(pos_heroi)
        r.players["p0"]["hp"] = r.players["p0"]["max_hp"] = 60
        random.seed(1)
        return r, m

    def test_harpa_acerta_a_linha_e_entra_em_recarga(self):
        r, m = self._instrumento("harpa", (8, 5))
        with mock.patch.object(S.random, "random", return_value=0.0):
            self.assertTrue(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))
            self.assertLess(r.players["p0"]["hp"], 60)
            self.assertGreater(m["instrumento_pronto_em"], r.round_num)
            self.assertFalse(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))

    def test_harpa_fora_da_linha_nao_toca(self):
        r, m = self._instrumento("harpa", (8, 7))
        self.assertFalse(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))
        self.assertEqual(r.players["p0"]["hp"], 60)

    def test_tambor_area(self):
        r, m = self._instrumento("tambor", (6, 6), qual="rustico")
        with mock.patch.object(S.random, "random", return_value=0.0):
            self.assertTrue(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))
        self.assertLess(r.players["p0"]["hp"], 60)

    def test_trompa_amedronta(self):
        r, m = self._instrumento("trompa", (7, 5))
        r._testar_save = lambda *a, **k: (False, 1, 0, 1)
        with mock.patch.object(S.random, "random", return_value=0.0):
            self.assertTrue(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))
        self.assertGreaterEqual(r.players["p0"]["ciclope_ataque_penalty_ate"], r.round_num + 1)

    def test_sem_instrumento_ou_alaude_nao_toca(self):
        r = sala(); m = bardo(r, (5, 5)); r.players["p0"]["pos"] = [7, 5]
        self.assertFalse(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))
        m["instrumento"] = S.criar_instrumento("alaude", "padrao"); m["instrumento_pronto_em"] = 0
        self.assertFalse(asyncio.run(r._monster_usar_instrumento(m, alvos(r))))

    def test_turno_completo_nao_quebra_e_ataca(self):
        r = sala(); m = bardo(r, (5, 5), ("harpa", "padrao")); r.players["p0"]["pos"] = [6, 5]
        r.players["p0"]["hp"] = r.players["p0"]["max_hp"] = 80
        for _ in range(4):
            asyncio.run(r._run_monster_ai(m, alvos(r)))
            r.round_num += 1
        self.assertLess(r.players["p0"]["hp"], 80)


class AurasTests(unittest.TestCase):
    """Sino, Lira e Flauta: instrumentos de 1 mão (tocam e ainda atacam no turno)."""

    def _cena(self, base, pos_heroi=(7, 5)):
        r = sala(); m = bardo(r, (5, 5), (base, "padrao"))
        r.players["p0"]["pos"] = list(pos_heroi)
        r.players["p0"]["hp"] = r.players["p0"]["max_hp"] = 80
        return r, m

    def _tocar(self, r, m):
        with mock.patch.object(S.random, "random", return_value=0.0):
            return asyncio.run(r._monster_usar_instrumento(m, alvos(r)))

    def test_instrumento_de_uma_mao_nao_gasta_a_acao(self):
        r2, m2 = self._cena("sino")
        m2["monster_ability_uses"] = {"hero_bard_cancao_heroica": 0}
        with mock.patch.object(S.random, "random", return_value=0.0):
            consumiu = asyncio.run(r2._monster_try_editor_ability(m2, alvos(r2)))
        self.assertFalse(consumiu)                       # continua e ataca
        self.assertGreaterEqual(m2["ecos_dolorosos_ate"], r2.round_num)
        self.assertFalse(m2.pop("_monster_editor_action_consumed", False))

    def test_ecos_ferem_quem_ataca_de_perto(self):
        r, m = self._cena("sino")
        self.assertTrue(self._tocar(r, m))
        self.assertFalse(self._tocar(r, m))              # recarga
        h = r.players["p0"]; antes = h["hp"]
        asyncio.run(r._dano_retaliacao(m, h, True, 5))
        self.assertLess(h["hp"], antes)
        asyncio.run(r._dano_retaliacao(m, h, False, 5))   # à distância não retalia
        meio = h["hp"]
        asyncio.run(r._dano_retaliacao(m, h, False, 5))
        self.assertEqual(h["hp"], meio)

    def test_ecos_expiram(self):
        r, m = self._cena("sino"); self._tocar(r, m)
        r.round_num += 10; h = r.players["p0"]; antes = h["hp"]
        asyncio.run(r._dano_retaliacao(m, h, True, 5))
        self.assertEqual(h["hp"], antes)

    def test_flauta_ecoa_o_golpe_do_proprio_bardo(self):
        r, m = self._cena("flauta", (6, 5))
        self.assertTrue(self._tocar(r, m))
        h = r.players["p0"]; antes = h["hp"]
        asyncio.run(r._bardo_monstro_apos_acerto(m, {"kind": "player", "obj": h}, 20))
        self.assertEqual(antes - h["hp"], 20 * m["dueto_fantasma_fracao"] // 100)

    def test_lira_revida_com_ataque_gratis_uma_vez_por_rodada(self):
        r, m = self._cena("lira", (6, 6))
        aliado = bardo(r, (6, 5))
        self.assertTrue(self._tocar(r, m))
        h = r.players["p0"]; h["ac"] = 0
        golpes = []
        orig = r._execute_one_monster_attack

        async def espia(mm, atk, tobj):
            golpes.append(mm["id"]); return await orig(mm, atk, tobj)
        r._execute_one_monster_attack = espia
        alvo = {"kind": "player", "obj": h}
        asyncio.run(r._bardo_monstro_apos_acerto(aliado, alvo, 3))
        asyncio.run(r._bardo_monstro_apos_acerto(aliado, alvo, 3))
        self.assertEqual(golpes, [m["id"]])               # 1x por rodada
        r.round_num += 1; m["dueto_marcial_ate"] = r.round_num
        asyncio.run(r._bardo_monstro_apos_acerto(aliado, alvo, 3))
        self.assertEqual(golpes, [m["id"], m["id"]])

    def test_lira_exige_aliado_perto_e_aliado_colado(self):
        r, m = self._cena("lira", (6, 6))
        self.assertFalse(self._tocar(r, m))               # sozinho: sem dueto
        longe = bardo(r, (12, 9))
        h = r.players["p0"]
        m["dueto_marcial_ate"] = r.round_num + 3
        antes = h["hp"]
        asyncio.run(r._bardo_monstro_apos_acerto(longe, {"kind": "player", "obj": h}, 3))
        self.assertEqual(h["hp"], antes)                  # aliado longe do bardo: nada


if __name__ == "__main__":
    unittest.main(verbosity=2)
