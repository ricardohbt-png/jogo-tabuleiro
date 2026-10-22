"""Requisito `tambem_fato` e `fatos` no objetivo. Roda da raiz: python -X utf8 tools/test_tambem_fato.py"""
import copy
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def sala(fatos=()):
    r = S.GameRoom("TF")
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.fatos = set(fatos)

    async def nada(*a, **k): pass
    r.gm_say = nada; r.broadcast = nada; r.send_to = nada; r.push_state = nada
    return r


class RequisitoTests(unittest.TestCase):
    def test_limpeza_so_inclui_quando_preenchido(self):
        self.assertNotIn("tambem_fato", S._clean_requirement({"fato": "a"}))
        self.assertEqual(S._clean_requirement({"tambem_fato": " b "})["tambem_fato"], "b")
        self.assertEqual(S._clean_requirement({"fato": "a"}), S._clean_requirement({"fato": "a", "tambem_fato": ""}))

    def test_exige_os_dois_fatos(self):
        req = {"fato": "a", "tambem_fato": "b"}
        self.assertFalse(sala({"a"})._avaliar_requisito(req)[0])
        self.assertFalse(sala({"b"})._avaliar_requisito(req)[0])
        self.assertTrue(sala({"a", "b"})._avaliar_requisito(req)[0])
        self.assertTrue(sala({"a"})._avaliar_requisito({"fato": "a"})[0], "requisito antigo segue igual")

    def test_vale_em_destino_e_em_slide(self):
        ad = {"id": "x_t", "nome": "X", "dungeons": [{"file": "amostra.json"}], "oculto_ate_liberar": True,
              "requisito": S._clean_requirement({"fato": "a", "tambem_fato": "b"})}
        self.assertFalse(sala({"a"})._aventura_visivel(ad))
        self.assertTrue(sala({"a", "b"})._aventura_visivel(ad))
        slide = {"text": "s", "requisito": {"fato": "a", "tambem_fato": "b"}}
        beat = lambda r: S._story_beat("k", [{"slides": [slide]}], r._requisito_do_slide)
        self.assertTrue(beat(sala({"a", "b"})))
        self.assertFalse(beat(sala({"a"})))


class ObjetivoTests(unittest.IsolatedAsyncioTestCase):
    def defn(self, **extra):
        d = copy.deepcopy(S.carregar_dungeon("amostra.json"))
        d["monsters"][0]["target"] = True
        d["objectives"] = {"primary": dict({"type": "kill_target"}, **extra), "secondary": []}
        return d

    async def test_fatos_sao_gravados_com_o_fato(self):
        r = sala()
        r.load_authored_dungeon(self.defn(fato="a", fatos=["b", "c"]))
        r.phase = "playing"
        m = next(iter(r.monsters.values()))
        m["hp"] = 0
        await r._monster_dies(m, "p1")
        await r._check_objectives()
        self.assertTrue({"a", "b", "c"} <= r.fatos)

    def test_validador(self):
        self.assertTrue(S.validar_dungeon(self.defn(fato="a", fatos=["b"]))[0])
        for ruim in ("b", [1], [""], ["x"] * 7, ["y" * 101]):
            self.assertFalse(S.validar_dungeon(self.defn(fatos=ruim))[0], ruim)


if __name__ == "__main__":
    unittest.main()
