"""Venenos aprimorados: versões mais fortes dos venenos da loja (mais CD, efeito e
duração), com a mesma mecânica e o PNG do veneno-base.

Cobre o catálogo (toda combinação de melhoria de todo veneno da loja), a descrição
mostrada ao jogador, a compra e o uso (arma corpo a corpo, munição, golpe aplicando o
efeito em monstro e herói) e o frasco do Assassino Goblin.
Roda da raiz:  python -X utf8 tools/test_venenos_aprimorados.py
"""
import asyncio
import itertools
import math
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

CD = ("nenhum", *S._VENENO_MELHORIAS_CD)
POT = ("nenhum", *S._VENENO_MELHORIAS_POTENCIA)
DUR = ("nenhum", *S._VENENO_MELHORIAS_DURACAO)
COMBOS = [c for c in itertools.product(CD, POT, DUR)]


def frascos():
    return [i for i in S.SHOP_MERCHANT if i.get("effect") == "coat_poison"]


def preparar(item, cd="nenhum", pot="nenhum", dur="nenhum"):
    return S._preparar_item_veneno(item, {"cd": cd, "potencia": pot, "duracao": dur})


class CatalogoTests(unittest.TestCase):
    def test_toda_combinacao_de_todo_veneno_da_loja_e_valida(self):
        self.assertGreaterEqual(len(frascos()), 9)
        for item in frascos():
            for cd, pot, dur in COMBOS:
                r = preparar(item, cd, pot, dur)
                self.assertIsNotNone(r, (item["id"], cd, pot, dur))
                self.assertEqual(r["id"], r["veneno_id"])
                self.assertTrue(S._veneno_id_valido(r["veneno_id"]), r["id"])
                self.assertEqual(r["effect"], "coat_poison")

    def test_ids_invalidos_sao_recusados(self):
        base = "veneno_fungo_acre"
        for ruim in (f"{base}__upgrade__nenhum_nenhum_nenhum", f"{base}__upgrade__mortal_nenhum",
                     f"{base}__upgrade__x_y_z", "veneno_inexistente__upgrade__mortal_nenhum_nenhum",
                     f"{base}__upgrade__a__upgrade__b_c_d"):
            self.assertFalse(S._veneno_id_valido(ruim), ruim)
        self.assertTrue(S._veneno_id_valido(base))

    def test_preco_cresce_com_as_melhorias(self):
        for item in frascos():
            base = int(item["price"])
            for cd, pot, dur in COMBOS:
                mult = (S._VENENO_MELHORIAS_CD.get(cd, (0, 1))[1]
                        * S._VENENO_MELHORIAS_POTENCIA.get(pot, (1, 1))[1]
                        * S._VENENO_MELHORIAS_DURACAO.get(dur, (0, 1))[1])
                self.assertEqual(preparar(item, cd, pot, dur)["price"], math.ceil(base * mult),
                                 (item["id"], cd, pot, dur))

    def test_cd_sobe_exatamente_o_bonus_da_melhoria(self):
        for item in frascos():
            base_cd = int(S.VENENOS[item["veneno_id"]]["dificuldade"])
            for cd in CD:
                r = preparar(item, cd)
                esperado = base_cd + (S._VENENO_MELHORIAS_CD[cd][0] if cd != "nenhum" else 0)
                self.assertEqual(S._veneno_com_melhorias(r["veneno_id"])["dificuldade"], esperado)
                self.assertEqual(r["dificuldade"], esperado)

    def test_usa_o_png_do_veneno_base(self):
        for item in frascos():
            for cd, pot, dur in COMBOS:
                r = preparar(item, cd, pot, dur)
                self.assertEqual(r["icon"], preparar(item)["icon"], (item["id"], cd, pot, dur))
                icone = r.get("icon") or f"assets/itens/{item['veneno_id']}.png"
                if item["id"] != "ensaio_sobre_a_cegueira":     # veneno do editor, sem arte própria
                    self.assertTrue((ROOT / icone).is_file(), f"{item['id']}: falta {icone}")

    def test_nome_traz_as_melhorias_e_fatal_e_o_maximo(self):
        item = next(i for i in frascos() if i["id"] == "veneno_fungo_acre")
        self.assertEqual(preparar(item, "aprimorado")["name"], "Fungo Acre Aprimorado")
        self.assertEqual(preparar(item, "mortal", "concentrado", "prolongado")["name"], "Fungo Acre Fatal")
        self.assertEqual(preparar(item)["name"], "Fungo Acre")

    def test_efeito_e_duracao_ficam_mais_fortes(self):
        aranha = S._veneno_com_melhorias("veneno_aranha_sombria__upgrade__nenhum_concentrado_prolongado")
        base = S.VENENOS["veneno_aranha_sombria"]
        self.assertEqual(aranha["valor"], "2d4")                 # dados dobrados
        self.assertEqual(aranha["_duracao_bonus"], 4)
        agonia = S._veneno_com_melhorias("veneno_agonia_sufocante__upgrade__nenhum_concentrado_nenhum")
        self.assertEqual(agonia["dano"], "2d4")
        escorpiao = S._veneno_com_melhorias("veneno_escorpiao_pedra__upgrade__nenhum_concentrado_nenhum")
        self.assertEqual(escorpiao["atributos"], [("ataque", -2), ("movimento", -2)])
        forte = S._veneno_com_melhorias("veneno_escorpiao_pedra__upgrade__nenhum_fortalecido_nenhum")
        self.assertEqual(forte["_potencia"], 1.5)
        self.assertEqual(base["valor"] if "valor" in base else "1d4", "1d4")


class DescricaoTests(unittest.TestCase):
    def descricao(self, base, **u):
        item = next(i for i in frascos() if i["id"] == base)
        return preparar(item, u.get("cd", "nenhum"), u.get("pot", "nenhum"), u.get("dur", "nenhum"))["descricao"]

    def test_nunca_vaza_estrutura_python(self):
        for item in frascos():
            for cd, pot, dur in COMBOS:
                d = preparar(item, cd, pot, dur)["descricao"]
                for lixo in ("[(", "('", "[[", "{'", "None"):
                    self.assertNotIn(lixo, d, (item["id"], cd, pot, dur, d))
                self.assertNotIn("--", d, d)

    def test_mostra_o_cd_final(self):
        for item in frascos():
            base_cd = int(S.VENENOS[item["veneno_id"]]["dificuldade"])
            d = preparar(item, "mortal")["descricao"]
            self.assertIn(f"CD {base_cd + 6}", d, d)

    def test_petrificacao_mostra_a_duracao_final(self):
        d = self.descricao("veneno_basilisco", dur="prolongado")
        self.assertIn("petrificado por 5 rodada(s)", d)
        self.assertIn("-1 movimento", d)
        self.assertIn("Melhorias: duração +4 rodadas", d)

    def test_penalidade_mostra_o_valor_escalado(self):
        d = self.descricao("veneno_escorpiao_pedra", pot="fortalecido")
        self.assertIn("-2 ataque, -2 movimento", d)
        d = self.descricao("veneno_escorpiao_pedra", pot="concentrado")
        self.assertIn("-2 ataque, -2 movimento", d)

    def test_dano_mostra_dados_dobrados_e_duracao(self):
        d = self.descricao("veneno_agonia_sufocante", pot="concentrado", dur="prolongado")
        self.assertIn("2d4 de dano", d)
        self.assertIn("1d4+4 rodadas", d)

    def test_cegueira_mostra_valores_e_reteste_com_cd_melhorado(self):
        d = self.descricao("ensaio_sobre_a_cegueira", cd="mortal")
        self.assertIn("Fortitude CD 20", d)
        self.assertIn("novo Fortitude CD 20", d)       # o reteste também usa o CD melhorado
        self.assertIn("sem ataques à distância", d)

    def test_sem_melhoria_mantem_a_descricao_escrita_pelo_autor(self):
        item = next(i for i in frascos() if i["id"] == "ensaio_sobre_a_cegueira")
        self.assertEqual(preparar(item)["descricao"], item["descricao"])
        item = next(i for i in frascos() if i["id"] == "veneno_fungo_acre")
        self.assertEqual(preparar(item)["descricao"], item["descricao"])


class Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("VENENOS_TEST")
        self.room.phase = "playing"
        self.room.round_num = 2
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.msgs = []

        async def noop(*a, **k):
            pass

        async def capture(*a, **k):
            self.msgs.append(a[-1])

        self.room.push_state = self.room.broadcast_city_state = self.room.push_state_or_city = noop
        self.room.gm_say = noop
        self.room.broadcast = self.room.send_to = capture
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *a: True
        self.hero = S.make_player("h", "Lad", "rogue", 0)
        self.hero.update(pos=[5, 5], fome=80, sede=80, action_done=False, bonus_action_used=False,
                         connected=True, gold=99999)
        self.hero["bag"] = []
        self.room.players["h"] = self.hero
        self.room.connections["h"] = object()
        definicao = next(m for m in S.MONSTER_DEFS if m["type"] == "urso_negro")
        self.monstro = S.make_monster(definicao, {"id": 1, "cx": 6, "cy": 5})
        self.monstro.update(pos=[6, 5], hp=500, max_hp=500, ac=5)
        self.room.monsters[1] = self.monstro

    def erros(self):
        return [str(m.get("msg")) for m in self.msgs if isinstance(m, dict) and m.get("type") == "error"]

    def equipar(self, arma_id):
        arma = deepcopy(S.WEAPONS[arma_id])
        self.hero["gear"]["weapon"] = arma
        self.room._sincronizar_arma_de_combate(self.hero, arma)
        return arma

    async def comprar(self, base, cd="nenhum", pot="nenhum", dur="nenhum"):
        self.room.phase = "city"
        self.room.world_location = "alva_e_luz"
        await self.room.handle_shop_buy("h", "mercador", base, {"cd": cd, "potencia": pot, "duracao": dur})
        self.room.phase = "playing"
        return self.hero["bag"][-1] if self.hero["bag"] else None


class CompraEUsoTests(Base):
    async def test_comprar_e_usar_toda_combinacao_na_arma(self):
        for item in frascos():
            for cd, pot, dur in [("nenhum", "nenhum", "nenhum"), ("aprimorado", "nenhum", "nenhum"),
                                 ("nenhum", "fortalecido", "destilado"), ("mortal", "concentrado", "prolongado")]:
                self.hero["bag"] = []
                self.hero["gold"] = 99999
                self.hero["bonus_action_used"] = False
                self.msgs.clear()
                self.equipar("dagger")
                frasco = await self.comprar(item["id"], cd, pot, dur)
                self.assertIsNotNone(frasco, (item["id"], cd, pot, dur, self.erros()))
                await self.room.handle_use_item("h", frasco["id"])
                self.assertEqual(self.erros(), [], (item["id"], cd, pot, dur))
                slots = self.hero["gear"]["weapon"].get("poison_slots")
                self.assertTrue(slots and all(s == frasco["veneno_id"] for s in slots),
                                (item["id"], cd, pot, dur, slots))
                self.assertNotIn(frasco, self.hero["bag"])
                self.assertTrue(self.hero["bonus_action_used"], "frasco de veneno é ação bônus")

    async def test_golpe_aplica_o_veneno_melhorado_no_monstro(self):
        self.equipar("dagger")
        frasco = await self.comprar("veneno_escorpiao_pedra", "mortal", "fortalecido", "destilado")
        await self.room.handle_use_item("h", frasco["id"])
        with patch.object(S, "d20_attack", return_value=(True, 12, 25, False)), \
                patch.object(S, "roll_dice", return_value=2), \
                patch.object(S.GameRoom, "_testar_save", return_value=(False, 5, 0, 5)):
            await self.room.handle_attack("h", 1)
        efeitos = self.monstro.get("efeitos_veneno") or []
        self.assertEqual(len(efeitos), 1, self.erros())
        ef = efeitos[0]
        self.assertEqual(ef["atributos"], [("ataque", -2), ("movimento", -2)])   # ×1,5 arredondado p/ cima
        self.assertGreaterEqual(ef["duracao"], 1 + 2)                             # 1d6 + 2 de duração

    async def test_municao_aceita_o_frasco_melhorado(self):
        self.equipar("arco_curto")
        flechas = deepcopy(next(a for a in S.SHOP_AMMO if a["id"] == "flechas"))
        flechas["ammo_count"] = 10
        self.hero["bag"] = [flechas]
        frasco = await self.comprar("veneno_fungo_acre", "aprimorado", "concentrado", "nenhum")
        for metodo in ("frasco", "veneno_rapido"):
            self.hero["bag"] = [deepcopy(flechas), deepcopy(frasco)]
            self.hero["sede"] = 80
            self.hero["bonus_action_used"] = False
            self.msgs.clear()
            await self.room.handle_envenenar_municao("h", {
                "method": metodo, "ammo_source": "bag", "ammo_index": 0, "quantity": 10,
                "confirmed_partial": True, "poison_ids": [frasco["veneno_id"]],
                "item_id": frasco["id"], "veneno_id": frasco["veneno_id"]})
            self.assertEqual(self.erros(), [], metodo)
            self.assertEqual(self.hero["bag"][0]["poison_ids"], [frasco["veneno_id"]], metodo)

    async def test_aplicacao_direta_em_heroi_e_monstro_nao_quebra(self):
        alvo = S.make_player("a", "Alvo", "warrior", 0)
        alvo["alive"] = True
        self.room.players["a"] = alvo
        for item in frascos():
            vid = preparar(item, "mortal", "concentrado", "prolongado")["veneno_id"]
            await self.room._aplicar_veneno(self.monstro, vid)
            await self.room._aplicar_veneno(alvo, vid)

    async def test_armadilha_com_veneno_consome_o_frasco_melhorado(self):
        frasco = await self.comprar("veneno_aranha_sombria", "aprimorado")
        self.hero["bag"] = [frasco]
        self.hero["gold"] = 500
        self.hero["action_done"] = False
        formula = S.ARMADILHAS["lamina_escondida"].get("formula_guild_id")
        if formula:
            self.hero["guild_owned"]["especializacoes"].append(formula)
        self.msgs.clear()
        await self.room.handle_criar_armadilha("h", {
            "tipo": "lamina_escondida", "tx": 5, "ty": 5, "veneno_id": frasco["veneno_id"]})
        self.assertEqual(self.erros(), [])
        self.assertEqual(self.hero["bag"], [], "o frasco melhorado tem de ser consumido")
        self.assertEqual(self.room.armadilhas[-1]["veneno_id"], frasco["veneno_id"])


class AssassinoGoblinTests(Base):
    async def test_doses_do_assassino_sao_validas_e_a_melhorada_e_aplicada(self):
        import random
        random.seed(11)
        definicao = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin_assassino")
        for seed in range(25):
            random.seed(seed)
            m = S.make_monster(definicao, {"id": 9, "cx": 6, "cy": 5})
            doses = [i for i in m.get("equipment_consumables", []) if i.get("effect") == "coat_poison"]
            self.assertEqual(len(doses), 3)
            for dose in doses:
                self.assertTrue(S._veneno_id_valido(dose["veneno_id"]), dose["id"])
                self.assertTrue(dose.get("icon") or dose["veneno_id"].split("__upgrade__")[0])
            self.assertEqual(sum("__upgrade__" in d["veneno_id"] for d in doses), 1, seed)


if __name__ == "__main__":
    unittest.main(verbosity=1)
