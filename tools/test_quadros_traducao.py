"""Quadros (popups) do servidor saem no idioma de quem lê.
Roda da raiz: python -X utf8 tools/test_quadros_traducao.py"""
import asyncio
import ast
import functools
import json
import os
import re
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÂÇÉÊÍÓÕÔÚ]")


def em_ingles(msg):
    return json.loads(json.dumps(msg, default=functools.partial(S._t_render, lang="en")))


def sala():
    r = S.GameRoom("QD")
    r.players["p0"] = S.make_player("p0", "Ana", "warrior", 0)
    r.players["p0"]["pos"] = [1, 1]
    r.enviados = []

    async def send_to(pid, msg): r.enviados.append(msg)
    async def nada(*a, **k): pass
    r.send_to = send_to; r.gm_say = nada; r.broadcast = nada
    return r


class ChavesTests(unittest.TestCase):
    def test_toda_chave_quadro_usada_existe_com_ingles(self):
        src = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
        usadas = set(re.findall(r'T\("(quadro\.[a-z0-9_.]+)"', src))
        faltam = [k for k in usadas
                  if not (S.LANG_STRINGS.get(k) or {}).get("en")]
        self.assertEqual(faltam, [])
        self.assertGreater(len(usadas), 150)


class QuadrosTests(unittest.TestCase):
    def _sem_portugues(self, msg):
        texto = json.dumps(em_ingles(msg), ensure_ascii=False)
        self.assertIsNone(ACENTO.search(texto), texto)

    def test_sono(self):
        r = sala()
        asyncio.run(r._enviar_resultado_sono(r.players["p0"], 2))
        m = em_ingles(r.enviados[-1])
        self.assertEqual(m["nome"], "Sleep")
        self._sem_portugues(r.enviados[-1])

    def test_morte(self):
        self.assertEqual(S.t("quadro.voce_morreu", "en"), "You died")

    def test_equipamento_danificado(self):
        r = sala()
        asyncio.run(r._enviar_resultado_equipamento_danificado(
            r.players["p0"], S.T("quadro.corrosao"), "Espada", S.estado_corrosao_T("quebrado"),
            [S.T("quadro.ca_menos", n=2), S.T("quadro.corrosao_piora")]))
        m = em_ingles(r.enviados[-1])
        self.assertEqual(m["nome"], "Equipment Damaged")
        self.assertIn("broken", m["descricao"])
        self.assertEqual(m["efeitos_extra"][0], "AC -2")

    def test_armadilha_usa_nome_do_catalogo(self):
        r = sala()
        meta = S.ARMADILHAS["rede"]
        asyncio.run(r._enviar_trap_result(r.players["p0"], meta["nome"], "🕸️", False, 0, False,
                                          meta.get("desc", ""), [], tipo_id="rede"))
        m = em_ingles(r.enviados[-1])
        self.assertEqual(m["nome"], S.t("cat.armadilha.rede.nome", "en"))

    def test_comparacao_com_texto_segue_valendo(self):
        # O controle mental compara o nome da magia com o texto em português.
        self.assertTrue(S.T("quadro.sono") == "Sono")
        self.assertTrue(S.T("quadro.medo") == "Medo")

    def test_nomes_crus_traduzem_na_narracao(self):
        self.assertEqual(S._param_texto("armadilha de dardos", "en"), "dart trap")
        self.assertEqual(S._param_texto("Moedas de Ouro", "en"), "Gold Coins")


class VarreduraTests(unittest.TestCase):
    """Nenhum literal com acento sobra como argumento dos helpers de quadro."""

    def test_helpers_de_quadro_sem_texto_cru(self):
        src = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
        arvore = ast.parse(src)
        pai = {}
        for n in ast.walk(arvore):
            for c in ast.iter_child_nodes(n):
                pai[c] = n

        def dentro_de_T(n):
            while n in pai:
                n = pai[n]
                if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("T", "nome_cat", "estado_corrosao_T"):
                    return True
            return False
        sobras = []
        for n in ast.walk(arvore):
            if not isinstance(n, ast.Call):
                continue
            nome = getattr(n.func, "attr", None) or getattr(n.func, "id", "")
            if not re.match(r"_enviar_resultado|_enviar_trap_result$", nome or ""):
                continue
            for a in list(n.args) + [k.value for k in n.keywords]:
                for x in ast.walk(a):
                    if (isinstance(x, ast.Constant) and isinstance(x.value, str)
                            and ACENTO.search(x.value) and not dentro_de_T(x)
                            and not isinstance(pai.get(x), ast.Compare)):
                        sobras.append((x.lineno, x.value))
        self.assertEqual(sobras, [])


if __name__ == "__main__":
    unittest.main()
