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


EDITOR_JS = (RAIZ / "tools" / "editor.js").read_text(encoding="utf-8")
EDITOR_HTML = (RAIZ / "tools" / "editor.html").read_text(encoding="utf-8")


class FiacaoTests(unittest.TestCase):
    def test_html_carrega_o_modulo_antes_do_editor(self):
        i = EDITOR_HTML.find("editor_guia_logic.js")
        j = EDITOR_HTML.find('"editor.js"')
        self.assertTrue(0 <= i < j, "editor_guia_logic.js deve vir antes de editor.js em editor.html")

    def test_load_e_build_conhecem_o_guia(self):
        self.assertIn("EDITOR_GUIA.carregar(", EDITOR_JS)
        self.assertIn("EDITOR_GUIA.serializar(", EDITOR_JS)

    def test_build_escreve_guia_so_quando_ha_passos(self):
        # o campo só entra no JSON se serializar() devolveu lista (null = sem guia)
        self.assertRegex(EDITOR_JS, r"const\s+guia\s*=\s*EDITOR_GUIA\.serializar\(f\.guia\)")
        self.assertRegex(EDITOR_JS, r"if\s*\(guia\)\s*out\.guia\s*=\s*guia")

    def test_validacao_usa_o_modulo(self):
        self.assertRegex(EDITOR_JS, r"EDITOR_GUIA\.validar\(f\.guia\)")

    def test_chaves_de_validacao_existem_em_pt_e_en(self):
        lang = (RAIZ / "src" / "lang" / "editor.js").read_text(encoding="utf-8")
        for cod in ("guia_muitos", "guia_sem_texto", "guia_ui_invalida", "guia_dicas",
                    "guia_conclui_invalido", "guia_ultimo_conclui"):
            self.assertIn(f'"ui.editor.masmorra.valid.{cod}"', lang, cod)


if __name__ == "__main__":
    unittest.main()
