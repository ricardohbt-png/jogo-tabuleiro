"""Migração do progresso dos Charcos (4 destinos antigos → a cadeia `charcos_mare`).

Roda da raiz:  python -X utf8 tools/test_charcos_migracao.py

REGRA
  • progresso: prefixo contínuo (bordas→palafitas→travessia→aldeia); aldeia conta até 2 etapas.
  • rota, diário, slides vistos e foto da masmorra passam para os ids/índices novos.
  • idempotente; dados sem os ids antigos ficam intactos; foto ilegível não quebra nada.
"""
import copy, os, sys, unittest
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

M = "charcos_mare"


def doc_antigo(**extra):
    d = {
        "world_adventure_progress": {"sombras_vau": 1, "charcos_bordas": 1, "charcos_palafitas": 1, "charcos_travessia": 1},
        "world_adventure_route_progress": {
            "sombras_vau:0": {"found_exit_ids": [], "objective_completed": True},
            "charcos_bordas:0": {"found_exit_ids": ["a"], "objective_completed": True},
            "charcos_palafitas:0": {"found_exit_ids": [], "objective_completed": True},
            "charcos_travessia:0": {"found_exit_ids": [], "objective_completed": True},
        },
        "adventurer_journal": {"missions": [
            {"adventure_id": "charcos_bordas", "stage_index": 0, "exit_ids": [], "complete": True, "completed_at": "t0"},
            {"adventure_id": "charcos_travessia", "stage_index": 0, "exit_ids": [], "complete": True, "completed_at": "t2"},
            {"adventure_id": "sombras_vau", "stage_index": 0, "exit_ids": [], "complete": True},
        ], "items": []},
        "story_beats_done": ["aventura:charcos_aldeia:0", "aventura:charcos_bordas:0", "aventura:sombras_vau:0",
                             "encadeada:charcos_aldeia:0", "fim:charcos_travessia:0", "fim:charcos_aldeia:1"],
    }
    d.update(extra)
    return d


class Migracao(unittest.TestCase):
    def test_progresso_em_prefixo(self):
        d = doc_antigo()
        self.assertTrue(S.migrar_charcos_cadeia(d))
        self.assertEqual(d["world_adventure_progress"], {"sombras_vau": 1, M: 3})
        for parcial, esperado in (({"charcos_bordas": 1}, 1), ({"charcos_bordas": 1, "charcos_palafitas": 1}, 2),
                                  ({"charcos_palafitas": 1}, 0), ({"charcos_bordas": 1, "charcos_travessia": 1}, 1)):
            d = {"world_adventure_progress": dict(parcial)}
            S.migrar_charcos_cadeia(d)
            self.assertEqual(d["world_adventure_progress"].get(M, 0), esperado, parcial)

    def test_aldeia_soma_ate_duas_etapas_so_com_o_prefixo_completo(self):
        d = {"world_adventure_progress": {"charcos_bordas": 1, "charcos_palafitas": 1, "charcos_travessia": 1, "charcos_aldeia": 1}}
        S.migrar_charcos_cadeia(d)
        self.assertEqual(d["world_adventure_progress"], {M: 4})
        d = {"world_adventure_progress": {"charcos_bordas": 1, "charcos_palafitas": 1, "charcos_travessia": 1, "charcos_aldeia": 2}}
        S.migrar_charcos_cadeia(d)
        self.assertEqual(d["world_adventure_progress"], {M: 5})
        d = {"world_adventure_progress": {"charcos_bordas": 1, "charcos_aldeia": 2}}
        S.migrar_charcos_cadeia(d)
        self.assertEqual(d["world_adventure_progress"], {M: 1}, "sem as do meio, a aldeia não conta")

    def test_rota(self):
        d = doc_antigo()
        S.migrar_charcos_cadeia(d)
        r = d["world_adventure_route_progress"]
        self.assertEqual(set(r), {"sombras_vau:0", f"{M}:0", f"{M}:1", f"{M}:2"})
        self.assertEqual(r[f"{M}:0"]["found_exit_ids"], ["a"])

    def test_diario(self):
        d = doc_antigo()
        S.migrar_charcos_cadeia(d)
        ms = {(m["adventure_id"], m["stage_index"]): m for m in d["adventurer_journal"]["missions"]}
        self.assertEqual(set(ms), {("sombras_vau", 0), (M, 0), (M, 2)})
        self.assertEqual(ms[(M, 2)]["completed_at"], "t2")

    def test_slides_vistos(self):
        d = doc_antigo()
        S.migrar_charcos_cadeia(d)
        self.assertEqual(sorted(d["story_beats_done"]), sorted([
            f"aventura:{M}:3", f"aventura:{M}:0", "aventura:sombras_vau:0",
            f"encadeada:{M}:3", f"encadeada:{M}:2", f"fim:{M}:4"]))

    def test_idempotente_e_nao_mexe_no_que_nao_e_dos_charcos(self):
        d = doc_antigo()
        S.migrar_charcos_cadeia(d)
        antes = copy.deepcopy(d)
        self.assertFalse(S.migrar_charcos_cadeia(d))
        self.assertEqual(d, antes)
        limpo = {"world_adventure_progress": {"sombras_vau": 1}, "story_beats_done": ["aventura:sombras_vau:0"]}
        c = copy.deepcopy(limpo)
        self.assertFalse(S.migrar_charcos_cadeia(c))
        self.assertEqual(c, limpo)
        self.assertFalse(S.migrar_charcos_cadeia({}))
        self.assertFalse(S.migrar_charcos_cadeia(None))

    def test_campos_malformados_nao_quebram(self):
        d = {"world_adventure_progress": "x", "world_adventure_route_progress": [], "adventurer_journal": 3,
             "story_beats_done": None, "dungeon_snapshot": "lixo"}
        self.assertFalse(S.migrar_charcos_cadeia(d))


class Foto(unittest.TestCase):
    def registro(self, adv, idx, arquivo="charcos_4a_arredores.json"):
        corpo = {"onde": "masmorra", "sala": {"world_adventure_id": adv, "world_adventure_index": idx,
                                                "world_adventure_revisit": False, "round_num": 65},
                 "herois": {}, "pids": {}}
        return S.foto_empacotar(corpo, onde="masmorra", rodada=65, masmorra=arquivo, masmorra_nome="Arredores")

    def test_foto_antiga_ganha_ids_e_indice_novos_mantendo_o_resumo(self):
        d = {"dungeon_snapshot": self.registro("charcos_aldeia", 0)}
        gravado = d["dungeon_snapshot"]["gravado_em"]
        self.assertTrue(S.migrar_charcos_cadeia(d))
        reg = d["dungeon_snapshot"]
        corpo = S.foto_desempacotar(reg)
        self.assertEqual((corpo["sala"]["world_adventure_id"], corpo["sala"]["world_adventure_index"]), (M, 3))
        self.assertEqual(corpo["sala"]["round_num"], 65)
        self.assertEqual((reg["onde"], reg["rodada"], reg["masmorra"], reg["gravado_em"]),
                         ("masmorra", 65, "charcos_4a_arredores.json", gravado))

    def test_foto_segunda_etapa_da_aldeia_e_idempotente(self):
        d = {"dungeon_snapshot": self.registro("charcos_aldeia", 1, "charcos_4b_aldeia.json")}
        S.migrar_charcos_cadeia(d)
        corpo = S.foto_desempacotar(d["dungeon_snapshot"])
        self.assertEqual((corpo["sala"]["world_adventure_id"], corpo["sala"]["world_adventure_index"]), (M, 4))
        self.assertFalse(S.migrar_charcos_cadeia(d))

    def test_foto_de_outra_aventura_ou_ilegivel_fica_como_esta(self):
        outra = {"dungeon_snapshot": self.registro("sombras_vau", 0, "sombras_1.json")}
        copia = copy.deepcopy(outra)
        self.assertFalse(S.migrar_charcos_cadeia(outra))
        self.assertEqual(outra, copia)
        ruim = {"dungeon_snapshot": {"versao": 999, "dados": "xx", "masmorra": "charcos_4a_arredores.json"}}
        self.assertFalse(S.migrar_charcos_cadeia(ruim))

    def test_ponto_de_salvamento_inteiro(self):
        estado = doc_antigo(dungeon_snapshot=self.registro("charcos_travessia", 0, "charcos_3_travessia.json"))
        S.migrar_charcos_cadeia(estado)
        corpo = S.foto_desempacotar(estado["dungeon_snapshot"])
        self.assertEqual((corpo["sala"]["world_adventure_id"], corpo["sala"]["world_adventure_index"]), (M, 2))
        self.assertEqual(estado["world_adventure_progress"][M], 3)

    def test_sala_ao_aplicar_foto_antiga_tambem_e_remapeada(self):
        sala = {"world_adventure_id": "charcos_palafitas", "world_adventure_index": 0}
        S.charcos_remapear_sala(sala)
        self.assertEqual((sala["world_adventure_id"], sala["world_adventure_index"]), (M, 1))
        S.charcos_remapear_sala(sala)
        self.assertEqual((sala["world_adventure_id"], sala["world_adventure_index"]), (M, 1))


if __name__ == "__main__":
    unittest.main(verbosity=1)
