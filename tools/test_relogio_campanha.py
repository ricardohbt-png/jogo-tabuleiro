"""Relógio de rodadas da campanha: soma entre masmorras, avisos, fato ao passar e desconto.
Roda da raiz: python -X utf8 tools/test_relogio_campanha.py"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S  # noqa: E402


def defn(relogio=None, passagem_desconto=None):
    d = copy.deepcopy(S.carregar_dungeon("amostra.json"))
    if relogio is not None:
        d["relogio"] = relogio
    return d


def sala(d=None, **kw):
    r = S.GameRoom("RELOGIO")
    r.msgs, r.falou = [], []

    async def noop(*a, **k): pass

    async def say(msg, *a, **k): r.falou.append(str(msg))

    async def bc(m, *a, **k): r.msgs.append(m)
    r.gm_say = say; r.broadcast = bc; r.send_to = noop; r.push_state = noop
    if d is not None:
        r.load_authored_dungeon(d)
    return r


REL = {"id": "p1", "limite": 4, "fato_ao_passar": "lento",
       "avisos": [{"em": 2, "texto": "A patrulha saiu."}, {"em": 4, "texto": "O sino tocou."}]}


class RelogioTests(unittest.IsolatedAsyncioTestCase):
    async def test_sem_relogio_na_masmorra_nada_acontece(self):
        r = sala(defn())
        for _ in range(3):
            await r._virada_de_rodada()
        self.assertEqual(r.relogios, {})

    async def test_soma_entre_duas_masmorras(self):
        r = sala(defn(REL))
        for _ in range(5):
            await r._virada_de_rodada()
        r.load_authored_dungeon(defn(REL))        # segunda masmorra, mesmo relógio
        for _ in range(4):
            await r._virada_de_rodada()
        self.assertEqual(r.relogios["p1"], 9)

    async def test_aviso_dispara_uma_vez_ao_cruzar(self):
        r = sala(defn(REL))
        for _ in range(6):
            await r._virada_de_rodada()
        self.assertEqual(r.falou.count("A patrulha saiu."), 1)
        self.assertEqual(r.falou.count("O sino tocou."), 1)

    async def test_fato_ao_passar_do_limite(self):
        r = sala(defn(REL))
        for _ in range(4):
            await r._virada_de_rodada()
        self.assertNotIn("lento", r.fatos, "no limite ainda é rápido")
        await r._virada_de_rodada()
        self.assertIn("lento", r.fatos)

    async def test_desconto_da_passagem_secreta(self):
        r = sala(defn(REL))
        for _ in range(3):
            await r._virada_de_rodada()
        r._relogio_descontar(2)
        self.assertEqual(r.relogios["p1"], 1)
        r._relogio_descontar(5)
        self.assertEqual(r.relogios["p1"], 0, "piso zero")

    async def test_passagem_aberta_aplica_o_desconto_uma_vez(self):
        d = defn(REL)
        d["secret_passages"] = []
        r = sala(d)
        r.secret_passages = [{"id": "s", "type": "mechanism", "pos": [1, 1], "key_decor_ids": [],
                              "keys_mode": "any", "activated_decor_ids": [], "opened": False,
                              "relogio_desconto": 2}]
        for _ in range(3):
            await r._virada_de_rodada()
        r._passagem_aberta(r.secret_passages[0])
        r._passagem_aberta(r.secret_passages[0])
        self.assertEqual(r.relogios["p1"], 1)

    def test_persiste_no_save_e_aceita_save_antigo(self):
        self.assertEqual(S._relogios_de_save({"relogios": {"p1": 7, "ruim": "x", "neg": -3}}), {"p1": 7, "neg": 0})
        self.assertEqual(S._relogios_de_save({}), {})
        self.assertEqual(S._relogios_de_save({"relogios": [1]}), {})
        self.assertEqual(S.CAMPOS_DO_PONTO.count("relogios"), 1)
        self.assertEqual(S.FOTO_SALA_CATEGORIAS.get("relogios"), "jogo_salvo")
        self.assertEqual(S.FOTO_SALA_CATEGORIAS.get("relogio_def"), "foto")

    def test_validador(self):
        self.assertTrue(S.validar_dungeon(defn(REL))[0])
        for ruim in ({"id": "", "limite": 3}, {"id": "p1", "limite": 0},
                     {"id": "p1", "limite": 3, "avisos": [{"em": 0, "texto": "x"}]},
                     {"id": "p1", "limite": 3, "avisos": [{"em": 1, "texto": ""}]}, "lixo"):
            self.assertFalse(S.validar_dungeon(defn(ruim))[0], ruim)


if __name__ == "__main__":
    unittest.main()
