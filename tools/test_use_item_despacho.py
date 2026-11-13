"""O despacho da mensagem `use_item` só pode passar argumentos que handle_use_item aceita.
Um argumento a mais dá TypeError em TODO uso de item ("Erro interno: TypeError").
Roda da raiz: python -X utf8 tools/test_use_item_despacho.py
"""
import ast
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fonte():
    with open(os.path.join(RAIZ, "server.py"), encoding="utf-8") as f:
        return ast.parse(f.read())


class DespachoUseItemTests(unittest.TestCase):
    def test_chamada_do_handler_cabe_na_assinatura(self):
        arvore = _fonte()
        assinatura = next(n for n in ast.walk(arvore)
                          if isinstance(n, ast.AsyncFunctionDef) and n.name == "handle_use_item")
        posicionais = [a.arg for a in assinatura.args.args][1:]        # sem self
        chamadas = [n for n in ast.walk(arvore)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "handle_use_item" and isinstance(n.func.value, ast.Name)
                    and n.func.value.id == "room"]
        self.assertTrue(chamadas, "não achei o despacho de use_item")
        for c in chamadas:
            self.assertLessEqual(len(c.args), len(posicionais),
                                 f"o despacho passa {len(c.args)} argumentos; handle_use_item aceita {len(posicionais)}")
            nomes = {k.arg for k in c.keywords}
            self.assertTrue(nomes <= set(posicionais), nomes - set(posicionais))


if __name__ == "__main__":
    unittest.main()
