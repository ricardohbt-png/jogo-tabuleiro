"""Contrato de atributos por arma, independente da classe e de saves legados."""
import sys
from pathlib import Path
from copy import deepcopy
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as s

class AtributosArmas(unittest.TestCase):
    def test_classes_armas_e_atributos(self):
        room = s.GameRoom("TEST")
        for classe in ("warrior", "mage", "cleric", "paladin", "rogue", "bard"):
            for forca, destreza in ((10,18),(18,10)):
                p = s.make_player("p", "Teste", classe, 0)
                room._apply_attribute_delta(p, "str_", forca-p["str_"])
                room._apply_attribute_delta(p, "dex", destreza-p["dex"])
                # Base sem o atributo embutido na ficha da classe.
                base = p["atk_bonus"]-s.mod(p[s._CLASS_ATK_ATTR[classe]])
                for wid, expected in (("shortsword",s.mod(forca)),("chicote",s.mod(forca)),
                    ("dagger",max(s.mod(forca),s.mod(destreza))),
                    ("longbow",s.mod(destreza)),("besta",s.mod(destreza))):
                    with self.subTest(classe=classe,forca=forca,arma=wid):
                        weapon = s.WEAPONS[wid]
                        self.assertEqual(s._hero_attack_bonus_with_weapon(p,weapon),base+expected)
                        self.assertEqual(room._bonus_atributo_dano_arma(p,weapon),expected)
                        self.assertEqual(s._hero_attack_bonus_with_weapon(p,{"id":wid}),base+expected)
    def test_arremesso_e_excecao(self):
        p = dict(str_=18,dex=12)
        for wid in ("dagger","lanca_curta"):
            self.assertEqual(s._weapon_attribute_modifier(p,{"id":wid},thrown=True),1)
        for wid in ("machado_basico","machado_basico_aco_damasco","machado_basico_obsidiana_ferro","machado_basico_liga_titanio","machado_basico_prata","machadinha_arremesso_ana","machadinha_ana_prata","machadinha_runica_vai_e_volta","machadinha_runica_vai_e_volta_maior"):
            self.assertEqual(s._weapon_attribute_modifier(p,{"id":wid},thrown=True),4)
    def test_material_nao_muda_atributo(self):
        p = s.make_player("p","Teste","rogue",0)
        for wid in ("shortsword_aco_damasco","shortsword_obsidiana_ferro"):
            self.assertEqual(s._hero_attack_bonus_with_weapon(p,s.WEAPONS[wid]),1)
        self.assertEqual(s._hero_attack_bonus_with_weapon(p,s.WEAPONS["dagger_aco_damasco"]),5)

    def test_arco_bruto_soma_forca_so_no_dano(self):
        """Arco Bruto do Combatente e variantes: acerto só com Destreza; dano com Destreza + Força."""
        room = s.GameRoom("TEST")
        ids = ("arco_bruto_combatente", "arco_bruto_combatente_freixo_negro",
               "arco_bruto_combatente_cedro_rubro", "arco_bruto_combatente_cerne_tita")
        for classe in ("warrior", "paladin"):
            p = s.make_player("p", "Teste", classe, 0)
            room._apply_attribute_delta(p, "str_", 18 - p["str_"])      # +4
            room._apply_attribute_delta(p, "dex", 14 - p["dex"])        # +2
            base = p["atk_bonus"] - s.mod(p[s._CLASS_ATK_ATTR[classe]])
            for wid in ids:
                with self.subTest(classe=classe, arma=wid):
                    self.assertIn(wid, s.WEAPONS)
                    for arma in (s.WEAPONS[wid], {"id": wid}):   # catálogo e cópia de combate sem o campo
                        self.assertEqual(s._hero_attack_bonus_with_weapon(p, arma), base + 2)
                        self.assertEqual(room._bonus_atributo_dano_arma(p, arma), 2 + 4)
        # as outras armas à distância continuam só com Destreza no dano
        p = s.make_player("p", "Teste", "warrior", 0)
        room._apply_attribute_delta(p, "str_", 18 - p["str_"])
        room._apply_attribute_delta(p, "dex", 14 - p["dex"])
        for wid in ("longbow", "arco_composto_longo", "besta_pesada"):
            self.assertEqual(room._bonus_atributo_dano_arma(p, s.WEAPONS[wid]), 2, wid)

    def test_arco_bruto_forca_negativa_reduz_o_dano(self):
        room = s.GameRoom("TEST")
        p = s.make_player("p", "Teste", "warrior", 0)
        room._apply_attribute_delta(p, "str_", 8 - p["str_"])           # -1
        room._apply_attribute_delta(p, "dex", 14 - p["dex"])            # +2
        self.assertEqual(room._bonus_atributo_dano_arma(p, s.WEAPONS["arco_bruto_combatente"]), 1)

if __name__ == "__main__": unittest.main()
