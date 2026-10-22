"""Requisito `heroi_no_grupo`: a classe pedida precisa estar entre os heróis da sala.
Roda da raiz: python -X utf8 tools/test_requisito_heroi.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402


def sala(classes=(), fatos=(), mestre=False):
    r = S.GameRoom("HEROI")
    r.fatos = set(fatos)
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = {"id": f"p{i}", "class_id": c, "level": 1}
    if mestre:
        r.players["m"] = {"id": "m", "class_id": "mage", "is_master": True, "level": 1}
    return r


class HeroiNoGrupoTests(unittest.TestCase):
    def test_clean_requirement_conserva_heroi(self):
        self.assertEqual(S._clean_requirement({"heroi_no_grupo": " mage "})["heroi_no_grupo"], "mage")
        self.assertNotIn("heroi_no_grupo", S._clean_requirement({}))
        self.assertNotIn("heroi_no_grupo", S._clean_requirement({"heroi_no_grupo": "dragao"}))

    def test_avalia_com_e_sem_o_heroi(self):
        self.assertTrue(sala(["mage", "warrior"])._avaliar_requisito({"heroi_no_grupo": "mage"})[0])
        ok, motivos = sala(["warrior"])._avaliar_requisito({"heroi_no_grupo": "mage"})
        self.assertFalse(ok)
        self.assertEqual(len(motivos), 1)
        self.assertIsInstance(motivos[0], S.T)

    def test_mestre_nao_conta_como_heroi(self):
        self.assertFalse(sala(["warrior"], mestre=True)._avaliar_requisito({"heroi_no_grupo": "mage"})[0])

    def test_requisitos_antigos_inalterados(self):
        r = sala(["warrior"], fatos={"x"})
        self.assertTrue(r._avaliar_requisito({})[0])
        self.assertTrue(r._avaliar_requisito({"fato": "x"})[0])
        self.assertFalse(r._avaliar_requisito({"fato": "y"})[0])

    def test_conversa_de_cena_guarda_o_requisito(self):
        convs = S._clean_scene_conversations([
            {"id": "c", "texto": "t", "requisito": {"heroi_no_grupo": "bard"}}])
        self.assertEqual(convs[0]["requisito"]["heroi_no_grupo"], "bard")

    def test_fala_de_masmorra_respeita_requisito(self):
        fala = {"id": "f", "trigger": {"tipo": "proximidade", "raio": 2}, "pos": [1, 1],
                "texto": "oi", "requisito": {"heroi_no_grupo": "bard"}}
        r = sala(["warrior"])
        self.assertFalse(r._fala_elegivel(r.players["p0"], dict(fala, disparada=False)))
        r2 = sala(["warrior", "bard"])
        self.assertTrue(r2._fala_elegivel(r2.players["p0"], dict(fala, disparada=False)))
        sem = {k: v for k, v in fala.items() if k != "requisito"}
        self.assertTrue(r._fala_elegivel(r.players["p0"], dict(sem, disparada=False)))

    def test_validador_aceita_fala_com_requisito(self):
        d = S.carregar_dungeon("amostra.json")
        import copy
        d = copy.deepcopy(d)
        d["falas"] = [{"id": "f", "pos": list(d["entrance"]) if isinstance(d.get("entrance"), list) else [1, 1],
                       "texto": "oi", "trigger": {"tipo": "manual"},
                       "requisito": {"heroi_no_grupo": "bard"}}]
        ok, msg = S.validar_dungeon(d)
        self.assertTrue(ok, msg)
        d["falas"][0]["requisito"] = "lixo"
        self.assertFalse(S.validar_dungeon(d)[0])


if __name__ == "__main__":
    unittest.main()
