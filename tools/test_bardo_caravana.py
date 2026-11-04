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
        self.assertEqual(bases, {"harpa", "tambor", "trompa", "alaude", "sino", "lira", "flauta", "violino", "gaita"})


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


class RequiemTests(unittest.TestCase):
    """Violino: Réquiem Final do monstro sobre um herói."""

    def _cena(self, pos_heroi=(8, 5), qual="padrao"):
        r = sala(); m = bardo(r, (5, 5), ("violino", qual))
        h = r.players["p0"]; h["pos"] = list(pos_heroi); h["hp"] = h["max_hp"] = 200
        return r, m, h

    def _abrir(self, r, m):
        with mock.patch.object(S.random, "random", return_value=0.0):
            return asyncio.run(r._monster_usar_instrumento(m, alvos(r)))

    def test_abre_forca_o_alvo_e_gasta_a_acao(self):
        r, m, h = self._cena()
        m["monster_ability_uses"] = {"hero_bard_cancao_heroica": 0, "hero_bard_provocacao": 0}
        with mock.patch.object(S.random, "random", return_value=0.0):
            consumiu = asyncio.run(r._monster_try_editor_ability(m, alvos(r)))
        self.assertTrue(consumiu)                         # violino é de 2 mãos
        self.assertEqual(m["requiem_monstro_alvo"], h["id"])
        self.assertEqual(h["runico_provocado_por"], m["id"])
        self.assertEqual(h["requiem_monstro_por"], m["id"])
        self.assertFalse(self._abrir(r, m))               # já está tocando

    def test_fora_do_alcance_ou_sem_visao_nao_abre(self):
        r, m, h = self._cena((18, 10))
        self.assertFalse(self._abrir(r, m))
        self.assertNotIn("requiem_monstro_alvo", m)

    def test_dano_cresce_ate_o_teto(self):
        r, m, h = self._cena(qual="velho")                # teto 3, d2
        self._abrir(r, m)
        r._testar_save = lambda *a, **k: (False, 1, 0, 1)
        antes = h["hp"]
        for _ in range(6):
            asyncio.run(r._processar_requiem_monstro_heroi(h))
        self.assertEqual(m["requiem_monstro_contador"], 3)
        self.assertLess(h["hp"], antes)
        self.assertLessEqual(antes - h["hp"], 2 * (1 + 2 + 3 + 3 + 3 + 3))

    def test_save_bem_sucedido_nao_causa_dano_mas_mantem_o_alvo_forcado(self):
        r, m, h = self._cena(); self._abrir(r, m)
        r._testar_save = lambda *a, **k: (True, 20, 0, 20)
        r.round_num += 1
        asyncio.run(r._processar_requiem_monstro_heroi(h))
        self.assertEqual(h["hp"], 200)
        self.assertEqual(h["runico_provocacao_ate"], r.round_num)

    def test_dano_no_bardo_testa_concentracao_e_falha_encerra(self):
        r, m, h = self._cena(); self._abrir(r, m)
        m["hp"] -= 5
        async def falha(*a, **k): return (False, 1, 0, 1)
        r._save_mostrado = falha
        asyncio.run(r._requiem_monstro_manter(m))
        self.assertFalse(m["requiem_monstro_alvo"])
        self.assertNotIn("requiem_monstro_por", h)
        self.assertNotIn("runico_provocado_por", h)

    def test_concentracao_passa_mantem(self):
        r, m, h = self._cena(); self._abrir(r, m)
        m["hp"] -= 5
        async def passa(*a, **k): return (True, 20, 0, 20)
        r._save_mostrado = passa
        asyncio.run(r._requiem_monstro_manter(m))
        self.assertEqual(m["requiem_monstro_alvo"], h["id"])

    def test_bardo_morto_ou_violino_trocado_encerra(self):
        r, m, h = self._cena(); self._abrir(r, m)
        m["hp"] = 0
        asyncio.run(r._processar_requiem_monstro_heroi(h))
        self.assertNotIn("requiem_monstro_por", h)
        self.assertNotIn("runico_provocado_por", h)
        r2, m2, h2 = self._cena(); self._abrir(r2, m2)
        m2["instrumento"] = S.criar_instrumento("harpa", "padrao")
        asyncio.run(r2._requiem_monstro_manter(m2))
        self.assertFalse(m2["requiem_monstro_alvo"])

    def test_heroi_caido_encerra(self):
        r, m, h = self._cena(); self._abrir(r, m)
        h["alive"] = False
        asyncio.run(r._requiem_monstro_manter(m))
        self.assertFalse(m["requiem_monstro_alvo"])

    def test_tick_roda_no_inicio_do_turno_do_heroi(self):
        r, m, h = self._cena(); self._abrir(r, m)
        r._testar_save = lambda *a, **k: (False, 1, 0, 1)
        asyncio.run(r._start_initiative_player_turn(h))
        self.assertLess(h["hp"], 200)


class GaitaTests(unittest.TestCase):
    """Gaita: Improviso (2d6) com os efeitos dos outros instrumentos, no tier dela."""

    def _cena(self, pos_heroi=(7, 5), qual="padrao"):
        r = sala(); m = bardo(r, (5, 5), ("gaita", qual))
        h = r.players["p0"]; h["pos"] = list(pos_heroi); h["hp"] = h["max_hp"] = 200
        return r, m, h

    def _improvisar(self, r, m, rolagens):
        it = iter(rolagens)
        r._rolar_2d6 = lambda: next(it)
        with mock.patch.object(S.random, "random", return_value=0.0):
            return asyncio.run(r._monster_usar_instrumento(m, alvos(r)))

    def test_nao_gasta_a_acao_e_entra_em_recarga(self):
        r, m, h = self._cena()
        r._rolar_2d6 = lambda: 3
        m["monster_ability_uses"] = {"hero_bard_cancao_heroica": 0, "hero_bard_provocacao": 0}
        with mock.patch.object(S.random, "random", return_value=0.0):
            consumiu = asyncio.run(r._monster_try_editor_ability(m, alvos(r)))
        self.assertFalse(consumiu)
        self.assertGreater(m["instrumento_pronto_em"], r.round_num)

    def test_7_nota_cortante_na_linha(self):
        r, m, h = self._cena((8, 5))
        self.assertTrue(self._improvisar(r, m, [7]))
        self.assertLess(h["hp"], 200)

    def test_7_sem_heroi_na_linha_vai_ao_vento(self):
        r, m, h = self._cena((7, 7))
        self.assertTrue(self._improvisar(r, m, [7]))
        self.assertEqual(h["hp"], 200)
        self.assertTrue(any("não encontra" in str(x) for x in r.msgs))

    def test_8_acorde_em_area(self):
        r, m, h = self._cena((6, 6))
        self.assertTrue(self._improvisar(r, m, [8]))
        self.assertLess(h["hp"], 200)

    def test_11_chamado_amedronta(self):
        r, m, h = self._cena((7, 5))
        r._testar_save = lambda *a, **k: (False, 1, 0, 1)
        self._improvisar(r, m, [11])
        self.assertGreaterEqual(h["ciclope_ataque_penalty_ate"], r.round_num + 1)

    def test_9_requiem_de_um_pulso(self):
        r, m, h = self._cena((8, 5))
        r._testar_save = lambda *a, **k: (False, 1, 0, 1)
        self._improvisar(r, m, [9])
        self.assertLess(h["hp"], 200)
        self.assertNotIn("requiem_monstro_alvo", m)       # só a 1ª rodada, sem sustentar

    def test_4_ecos_5_dueto_6_fantasma_duram_uma_rodada(self):
        for res, campo in ((4, "ecos_dolorosos_ate"), (5, "dueto_marcial_ate"), (6, "dueto_fantasma_ate")):
            r, m, h = self._cena()
            bardo(r, (6, 5))                               # aliado perto, para a Lira valer
            self._improvisar(r, m, [res])
            self.assertEqual(m[campo], r.round_num + 1, campo)

    def test_ecos_da_gaita_retaliam(self):
        r, m, h = self._cena(); self._improvisar(r, m, [4])
        asyncio.run(r._dano_retaliacao(m, h, True, 5))
        self.assertLess(h["hp"], 200)

    def test_fantasma_da_gaita_ecoa(self):
        r, m, h = self._cena((6, 5)); self._improvisar(r, m, [6])
        asyncio.run(r._bardo_monstro_apos_acerto(m, {"kind": "player", "obj": h}, 20))
        self.assertLess(h["hp"], 200)

    def test_dueto_marcial_da_gaita_revida(self):
        r, m, h = self._cena((6, 6)); aliado = bardo(r, (6, 5))
        self._improvisar(r, m, [5]); h["ac"] = 0
        golpes = []
        orig = r._execute_one_monster_attack
        async def espia(mm, atk, t): golpes.append(mm["id"]); return await orig(mm, atk, t)
        r._execute_one_monster_attack = espia
        asyncio.run(r._bardo_monstro_apos_acerto(aliado, {"kind": "player", "obj": h}, 3))
        self.assertEqual(golpes, [m["id"]])

    def test_2_desafina_e_3_falha(self):
        r, m, h = self._cena(); self._improvisar(r, m, [2])
        self.assertEqual(m["acorde_atk_pen_ate"], r.round_num + 1)
        self.assertEqual(r._bardo_monstro_cd(m), 8 + S.mod(m["dex"]) - 1)
        r2, m2, h2 = self._cena(); self._improvisar(r2, m2, [3])
        self.assertEqual(h2["hp"], 200)

    def test_10_sinfonia_reforca_a_cancao_por_uma_rodada(self):
        r, m, h = self._cena(); aliado = bardo(r, (6, 5))
        r._ativar_cancao_monstro(m, ["acerto"])
        self.assertEqual(r._cancao_monstro_bonus(aliado, "acerto"), 1)
        self._improvisar(r, m, [10])
        self.assertEqual(r._cancao_monstro_bonus(aliado, "acerto"), 2)
        r.round_num += 1                       # mesma regra do herói: vale até a rodada seguinte
        self.assertEqual(r._cancao_monstro_bonus(aliado, "acerto"), 2)
        r.round_num += 1
        self.assertEqual(r._cancao_monstro_bonus(aliado, "acerto"), 1)

    def test_12_encore_rola_mais_dois(self):
        r, m, h = self._cena((8, 5))
        self.assertTrue(self._improvisar(r, m, [12, 7, 3]))     # 12 → 2 rolagens extras
        self.assertLess(h["hp"], 200)                            # o 7 acertou a linha
        self.assertTrue(any("Bis" in str(x) for x in r.msgs))



if __name__ == "__main__":
    unittest.main(verbosity=2)
