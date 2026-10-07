"""Sincronia do módulo do editor com o servidor + fiação estática no editor."""
import json, re, subprocess, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S

JS = (RAIZ / "tools" / "editor_guia_logic.js").read_text(encoding="utf-8")


def const_js(nome):
    m = re.search(r"const %s = ([\s\S]+?);\n" % re.escape(nome), JS)
    assert m, nome
    return m.group(1)


class SincroniaTests(unittest.TestCase):
    def test_regex_de_ui_igual_ao_servidor(self):
        fonte_js = json.loads(const_js("UI_RE_FONTE"))
        self.assertEqual(fonte_js, S.GUIA_UI_RE.pattern)

    def test_limites_iguais_ao_servidor(self):
        self.assertEqual(int(const_js("MAX_PASSOS")), S.GUIA_MAX_PASSOS)

    def test_verbos_iguais_ao_servidor(self):
        verbos_js = json.loads(const_js("VERBOS").replace("\n", " "))
        self.assertEqual(sorted(verbos_js), sorted(S.LICAO_VERBOS))


if __name__ == "__main__":
    unittest.main()
