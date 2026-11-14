"""Variantes de material herdam as regras da arma-base e corroem como o material manda.

Cobre: alcance (bestas só ortogonais, arcos com metade na diagonal), veneno só na
munição, Disparo Duplo das repetidoras, Lança Curta nas 8 casas, as bases que
antes não corroíam (marreta, lança, alabarda, ganchos, arcos compostos, besta
pesada, repetidoras), a Prata (sem penalidade no 1º nível, destruída no 2º) e a
Obsidiana de Ferro / Cedro Rubro (o 1º golpe corrosivo destrói).
Roda da raiz:  python -X utf8 tools/test_armas_materiais_regras.py
"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

LISTAS = (S._MATERIAL_WEAPON_VARIANTS, S._MATERIAL_WEAPON_DAMAGE_VARIANTS,
          S._MATERIAL_WEAPON_CORROSION_VARIANTS)
VARIANTES = [(base, vid, mat) for lista in LISTAS for base, vid, _n, _i, mat in lista]
VARIANTES_PRATA = [(w["id"][:-len("_prata")], w["id"]) for w in S.SHOP_WEAPONS
                   if w.get("silver") and w["id"] != "machadinha_ana_prata"]
A_DISTANCIA = [v for v in VARIANTES if v[0] in S.RANGED_AMMO]


def sala():
    r = S.GameRoom("TEST")

    async def noop(*a, **k):
        pass
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r.phase = "playing"
    return r


def jogador(weapon_id, classe="warrior"):
    p = S.make_player("p1", "Teste", classe, 0)
    # Prata só existe no catálogo da loja (a cópia de combate nasce na compra).
    arma = deepcopy(S.WEAPONS.get(weapon_id) or next(w for w in S.SHOP_WEAPONS if w["id"] == weapon_id))
    p["weapon"] = arma
    p["gear"] = {k: None for k in ("armor", "off_hand", "head", "boots", "item1", "item2", "ring1", "ring2")}
    p["gear"]["weapon"] = deepcopy(arma)
    p["pos"] = [10, 10]
    return p


class BaseIdTests(unittest.TestCase):
    def test_toda_variante_resolve_para_a_base(self):
        self.assertGreater(len(VARIANTES), 80)
        for base, vid, _mat in VARIANTES:
            self.assertEqual(S._arma_base_id(vid), base, vid)
        for base, vid in VARIANTES_PRATA:
            self.assertEqual(S._arma_base_id(vid), base, vid)
        self.assertEqual(S._arma_base_id("machadinha_ana_prata"), "machadinha_arremesso_ana")

    def test_id_sem_material_volta_igual(self):
        for wid in ("besta", "hand_crossbow", "longbow", "lanca_curta", "unarmed", "", None):
            self.assertEqual(S._arma_base_id(wid), wid or "")


class AlcanceTests(unittest.TestCase):
    def test_variantes_de_arco_e_besta_seguem_a_regra_da_base(self):
        r = sala()
        casas = [(dx, dy) for dx in range(-9, 10) for dy in range(-9, 10) if (dx, dy) != (0, 0)]
        for base, vid, _mat in A_DISTANCIA:
            alcance = int(S.WEAPONS[base]["range"])
            pb, pv = jogador(base), jogador(vid)
            for dx, dy in casas:
                tile = [10 + dx, 10 + dy]
                self.assertEqual(
                    r._tile_no_alcance_arma_distancia(pv, tile, alcance),
                    r._tile_no_alcance_arma_distancia(pb, tile, alcance),
                    f"{vid} em ({dx},{dy})")

    def test_besta_variante_nao_atira_na_diagonal(self):
        r = sala()
        p = jogador("besta_pesada_freixo_negro")
        self.assertFalse(r._tile_no_alcance_arma_distancia(p, [13, 13], 12))
        self.assertTrue(r._tile_no_alcance_arma_distancia(p, [10, 22], 12))

    def test_arco_variante_tem_metade_do_alcance_na_diagonal(self):
        r = sala()
        p = jogador("arco_curto_freixo_negro")
        self.assertTrue(r._tile_no_alcance_arma_distancia(p, [13, 13], 6))
        self.assertFalse(r._tile_no_alcance_arma_distancia(p, [14, 14], 6))

    def test_arco_composto_variante_mantem_alcance_integral_na_diagonal(self):
        r = sala()
        p = jogador("arco_composto_longo_cedro_rubro")
        self.assertTrue(p["weapon"].get("range_all_directions"))
        self.assertTrue(r._tile_no_alcance_arma_distancia(p, [18, 18], 10))


class VenenoTests(unittest.TestCase):
    def test_veneno_continua_so_na_municao(self):
        for base, vid, _mat in A_DISTANCIA:
            self.assertIn(vid, S.RANGED_AMMO, vid)
            self.assertEqual(S.RANGED_AMMO[vid], S.RANGED_AMMO[base], vid)

    def test_capacidade_de_veneno_igual_a_da_base(self):
        r = sala()
        for base, vid, _mat in A_DISTANCIA:
            for espec in ([], ["ladino_veneno_3"]):
                pb, pv = jogador(base, "rogue"), jogador(vid, "rogue")
                for p in (pb, pv):
                    p["guild_owned"] = {"especializacoes": list(espec)}
                self.assertEqual(r._capacidade_poison_arma(pv, vid),
                                 r._capacidade_poison_arma(pb, base), f"{vid} {espec}")


class RepetidoraTests(unittest.TestCase):
    def test_variantes_das_repetidoras_usam_disparo_duplo(self):
        for base in ("besta_repetidora_patrulha", "besta_repetidora_guerra"):
            for b, vid, _mat in VARIANTES:
                if b != base:
                    continue
                self.assertTrue(S.WEAPONS[vid].get("repeating_crossbow"), vid)
                self.assertIn(S._arma_base_id(vid), {"besta_repetidora_patrulha", "besta_repetidora_guerra"})


class LancaCurtaTests(unittest.TestCase):
    def test_variantes_da_lanca_curta_atingem_as_8_casas(self):
        r = sala()
        alvo = {"id": "m1", "pos": [11, 11], "size": [1, 1], "hp": 5, "altura": S.ALTURA_MIN}
        for base, vid, _mat in VARIANTES:
            if base != "lanca_curta":
                continue
            p = jogador(vid)
            p["altura"] = S.ALTURA_MIN
            self.assertTrue(r._alvo_no_alcance_arma(p, alvo), f"{vid} na diagonal")
        p = jogador("lanca_curta_prata")
        self.assertTrue(r._alvo_no_alcance_arma(p, alvo))


def corroer(weapon_id, vezes, metal=True):
    """Aplica `vezes` golpes corrosivos do tipo certo e devolve (nivel, destruida, pen)."""
    r = sala()
    p = jogador(weapon_id)
    ids_armadura = S.CORROSAO_ARMADURA_METAL if metal else S.CORROSAO_ARMADURA_ORGANICA
    ids_arma = S.CORROSAO_ARMA_METAL if metal else S.CORROSAO_ARMA_MADEIRA

    async def rodar():
        for _ in range(vezes):
            await r._corroer_equipamento(None, p, ids_armadura, ids_arma)
    asyncio.run(rodar())
    c = r._corr(p)
    return c["arma_lvl"], c["arma_destruida"], r._corrosao_arma_pen(p)


class CorrosaoBasesTests(unittest.TestCase):
    BASES_METAL = ("marreta", "lanca", "lanca_curta", "alabarda", "gancho_corrente", "gancho_escorpiao_superior")
    BASES_MADEIRA = ("arco_composto_curto", "arco_composto_longo", "arco_bruto_combatente", "besta_pesada",
                     "besta_repetidora_patrulha", "besta_repetidora_guerra")

    def test_bases_de_metal_sao_corroidas_so_pelo_devorador_de_metal(self):
        for wid in self.BASES_METAL:
            self.assertEqual(corroer(wid, 1, metal=True)[0], 1, wid)
            self.assertEqual(corroer(wid, 1, metal=False)[0], 0, f"{wid} organico")

    def test_bases_de_madeira_sao_corroidas_so_pelo_devorador_organico(self):
        for wid in self.BASES_MADEIRA:
            self.assertEqual(corroer(wid, 1, metal=False)[0], 1, wid)
            self.assertEqual(corroer(wid, 1, metal=True)[0], 0, f"{wid} metal")

    def test_base_segue_a_regra_normal(self):
        # sem tolerancia: -1, -2, destruida no 3o golpe
        self.assertEqual(corroer("marreta", 1)[2], 1)
        self.assertEqual(corroer("marreta", 2)[2], 2)
        self.assertTrue(corroer("marreta", 3)[1])


class CorrosaoMateriaisTests(unittest.TestCase):
    def _variantes(self, sufixo):
        return [(b, v, m) for b, v, m in VARIANTES if v.endswith(sufixo)]

    def test_variante_corroi_pelo_mesmo_devorador_da_base(self):
        for base, vid, mat in VARIANTES:
            metal = mat == "metal"
            self.assertEqual(corroer(vid, 1, metal=metal)[0], 1, vid)
            self.assertEqual(corroer(vid, 1, metal=not metal)[0], 0, f"{vid} devorador errado")

    def test_obsidiana_e_cedro_quebram_no_primeiro_golpe(self):
        achadas = self._variantes("_obsidiana_ferro") + self._variantes("_cedro_rubro")
        self.assertGreaterEqual(len(achadas), 18 + 11)
        for _base, vid, mat in achadas:
            nivel, destruida, _pen = corroer(vid, 1, metal=(mat == "metal"))
            self.assertTrue(destruida, vid)

    def test_aco_e_freixo_toleram_um_nivel_e_quebram_no_quarto(self):
        for sufixo in ("_aco_damasco", "_freixo_negro"):
            for _base, vid, mat in self._variantes(sufixo):
                metal = mat == "metal"
                resultados = [corroer(vid, n, metal=metal) for n in (1, 2, 3, 4)]
                self.assertEqual([r[2] for r in resultados[:3]], [0, 1, 2], vid)
                self.assertFalse(resultados[2][1], vid)
                self.assertTrue(resultados[3][1], vid)

    def test_titania_e_cerne_toleram_dois_niveis_e_quebram_no_sexto(self):
        for sufixo in ("_liga_titanio", "_cerne_tita"):
            for _base, vid, mat in self._variantes(sufixo):
                metal = mat == "metal"
                resultados = [corroer(vid, n, metal=metal) for n in range(1, 7)]
                self.assertEqual([r[2] for r in resultados[:5]], [0, 0, 1, 2, 3], vid)
                self.assertFalse(resultados[4][1], vid)
                self.assertTrue(resultados[5][1], vid)

    def test_prata_corroi_pelo_metal_sem_penalidade_no_1o_e_quebra_no_2o(self):
        self.assertGreater(len(VARIANTES_PRATA), 15)
        for _base, vid in VARIANTES_PRATA:
            n1 = corroer(vid, 1, metal=True)
            self.assertEqual((n1[0], n1[1], n1[2]), (1, False, 0), vid)
            self.assertTrue(corroer(vid, 2, metal=True)[1], vid)
            self.assertEqual(corroer(vid, 1, metal=False)[0], 0, f"{vid} organico")

    def test_catalogo_declara_a_regra_de_obsidiana_e_cedro(self):
        for _base, vid, _mat in self._variantes("_obsidiana_ferro") + self._variantes("_cedro_rubro"):
            w = S.WEAPONS[vid]
            self.assertEqual(w.get("corrosion_max"), 1, vid)
            self.assertEqual(w.get("damage_bonus"), 1, vid)
            self.assertFalse(w.get("atk_bonus"), vid)
            self.assertNotIn("N=1/M=2", w.get("descricao", ""), vid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
