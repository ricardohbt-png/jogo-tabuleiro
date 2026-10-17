"""Requisito negado `sem_fato`: passa só enquanto o marcador NÃO existe.
Roda da raiz: python -X utf8 tools/test_requisito_sem_fato.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402


def sala(fatos=()):
    r = S.GameRoom("SEMFATO")
    r.fatos = set(fatos)
    return r


class SemFatoTests(unittest.TestCase):
    def test_clean_requirement_conserva_sem_fato(self):
        self.assertEqual(S._clean_requirement({"sem_fato": " x "})["sem_fato"], "x")
        self.assertEqual(S._clean_requirement({})["sem_fato"], "")

    def test_avalia_negado(self):
        r = sala({"a"})
        ok, motivos = r._avaliar_requisito({"sem_fato": "a"})
        self.assertFalse(ok)
        self.assertEqual(len(motivos), 1)
        self.assertTrue(r._avaliar_requisito({"sem_fato": "b"})[0])

    def test_combina_com_outros_campos(self):
        r = sala({"a"})
        self.assertTrue(r._avaliar_requisito({"fato": "a", "sem_fato": "b"})[0])
        r.fatos.add("b")
        self.assertFalse(r._avaliar_requisito({"fato": "a", "sem_fato": "b"})[0])

    def test_conversa_e_destino_usam_o_mesmo_requisito(self):
        convs = S._clean_scene_conversations([
            {"id": "c", "texto": "t", "requisito": {"sem_fato": "morto"}}])
        self.assertEqual(convs[0]["requisito"]["sem_fato"], "morto")

    def test_motivo_e_traduzivel(self):
        _, motivos = sala({"a"})._avaliar_requisito({"sem_fato": "a"})
        self.assertIsInstance(motivos[0], S.T)


if __name__ == "__main__":
    unittest.main()
