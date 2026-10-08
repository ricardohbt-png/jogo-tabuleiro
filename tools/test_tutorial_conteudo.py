"""Conteúdo do guia da trilha comum: regras de redação, paridade pt/en e validação."""
import json, re, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))

import tutorial_guia_comum as C
import gerar_guia_comum as G

IDS_ESPERADOS = ["fala_0", "fala_1", "fala_2", "fala_3", "fala_4", "fala_18", "fala_19",
                 "fala_29", "fala_30", "fala_31", "fala_32", "fala_33", "fala_36", "fala_37", "fala_38"]
UI_OK = re.compile(r"^(?:(?:botao|bolsa|monstro):[a-z0-9_]+|(?:casa|porta):\[\d+,\d+\])$")
TERMO = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def textos(passo):
    yield passo["texto"]
    if passo.get("porque"): yield passo["porque"]
    yield from passo.get("dica", [])


class ConteudoTests(unittest.TestCase):
    def test_cobre_as_quinze_licoes(self):
        self.assertEqual(sorted(C.GUIA), sorted(IDS_ESPERADOS))

    def test_regras_de_redacao(self):
        for lid, passos in C.GUIA.items():
            self.assertTrue(1 <= len(passos) <= 3, lid)
            for i, p in enumerate(passos):
                pt, en = p["texto"]
                limpo = TERMO.sub("x", pt)
                self.assertLessEqual(len(limpo.split()), 15, f"{lid}/{p['id']}: >15 palavras")
                self.assertTrue(pt.strip() and en.strip(), f"{lid}/{p['id']}")
                if p.get("ui"):
                    self.assertRegex(p["ui"], UI_OK, f"{lid}/{p['id']}")
                if i == len(passos) - 1:
                    self.assertFalse(p.get("conclui"), f"{lid}: último passo não conclui")
                self.assertLessEqual(len(p.get("dica", [])), 2, lid)

    def test_conclui_com_nunca_depende_de_evento_anterior(self):
        # evento que o jogador pode ter feito antes da lição travaria o passo
        for lid, passos in C.GUIA.items():
            for p in passos:
                c = p.get("conclui")
                if c: self.assertNotIn(c["tipo"], ("pegar_item", "equipar", "usar_item"), f"{lid}/{p['id']}")

    def test_termos_existem_no_glossario(self):
        for lid, passos in C.GUIA.items():
            for p in passos:
                for par in textos(p):
                    for lang in par:
                        for termo in TERMO.findall(lang):
                            self.assertIn(termo, C.GLOSSARIO, f"{lid}/{p['id']}: [[{termo}]]")

    def test_termos_iguais_em_pt_e_en(self):
        for lid, passos in C.GUIA.items():
            for p in passos:
                for pt, en in textos(p):
                    self.assertEqual(TERMO.findall(pt), TERMO.findall(en), f"{lid}/{p['id']}")

    def test_glossario_completo(self):
        esperados = {"turno", "movimento", "acao_livre", "acao_bonus", "ca", "fome_sede", "resistencia",
                     "d20", "acao_principal", "slot", "teste_resistencia", "manutencao", "furtivo", "critico"}
        self.assertEqual(set(C.GLOSSARIO), esperados)
        for k, v in C.GLOSSARIO.items():
            for campo in ("nome", "texto"):
                self.assertTrue(v[campo][0].strip() and v[campo][1].strip(), f"{k}.{campo}")

    def test_ui_bate_com_a_tarefa_da_licao(self):
        d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        falas = {f["id"]: f for f in d["falas"]}
        for lid, passos in C.GUIA.items():
            tar = falas[lid]["tarefa"]
            for p in passos:
                ui = p.get("ui") or ""
                if ui.startswith("casa:") or ui.startswith("porta:"):
                    self.assertEqual(ui.split(":", 1)[1], json.dumps(tar.get("alvo")).replace(" ", ""), lid)


class GeradorTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))

    def test_guia_todos_junta_os_modulos_existentes(self):
        todos = G.guia_todos()
        for lid in C.GUIA:
            self.assertIn(lid, todos)
        self.assertEqual(len(todos), len(set(todos)))

    def test_botao_do_grimorio_tem_marcador(self):
        gjs = (RAIZ / "game.js").read_text(encoding="utf-8")
        self.assertRegex(gjs, r'id="fab-magias"[^>]*data-guia="botao:magias"')

    def test_aplicar_guia_injeta_so_chaves_e_valida(self):
        import server
        G.aplicar_guia(self.d)
        for f in self.d["falas"]:
            if f["id"] in C.GUIA:
                self.assertEqual(len(f["guia"]), len(C.GUIA[f["id"]]))
                for s in f["guia"]:
                    self.assertTrue(s["texto"].startswith("ui.tutorial.guia."), s)
        ok, msg = server.validar_dungeon(self.d)
        self.assertTrue(ok, msg)

    def test_aplicar_guia_e_idempotente(self):
        G.aplicar_guia(self.d); a = json.dumps(self.d, sort_keys=True)
        G.aplicar_guia(self.d); self.assertEqual(a, json.dumps(self.d, sort_keys=True))

    def test_lang_tem_pt_e_en_para_toda_chave_usada(self):
        lang = G.gerar_lang()
        G.aplicar_guia(self.d)
        usadas = set()
        for f in self.d["falas"]:
            for s in f.get("guia", []):
                for campo in ("texto", "porque"):
                    if s.get(campo): usadas.add(s[campo])
                usadas.update(s.get("dica", []))
        self.assertTrue(usadas)
        for k in usadas:
            self.assertIn(k, lang, k)
            self.assertTrue(lang[k]["pt"] and lang[k]["en"], k)
        for termo in C.GLOSSARIO:
            self.assertIn(f"ui.tutorial.glossario.{termo}.nome", lang)
            self.assertIn(f"ui.tutorial.glossario.{termo}.texto", lang)

    def test_arquivo_gerado_esta_em_dia(self):
        arq = (RAIZ / "src/lang/tutorial_guia.js").read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(arq, G.render_lang(), "rode: python tools/gerar_guia_comum.py")


VERBOS_PT = ("clique", "ande", "ataque", "equipe", "abra", "use", "beba", "coma", "pegue",
             "arraste", "selecione", "escolha", "encerre", "aperte", "pressione", "lance",
             "arremesse", "unte", "ative", "desative", "fique", "aproxime", "toque", "arme",
             "cure", "derrube", "acerte", "esconda", "desarme", "crie", "comande", "liberte",
             "proteja", "passe", "confira", "leia", "mova", "gire", "cancele", "troque")
VAGOS_PT = ("mostre-me", "me mostra", "mostre", "demonstre", "veja como", "observe")


def _primeira_palavra(pt):
    return re.sub(r"\[\[[a-z0-9_]+\]\]", "x", pt).strip().lower().split()[0].strip(".,:;!?")


class RedacaoAcionavelTests(unittest.TestCase):
    def _todos(self):
        for modulo in G.modulos_de_guia():
            for lid, passos in modulo.items():
                for p in passos:
                    yield lid, p

    def test_todo_passo_com_ui_comeca_por_verbo_de_acao(self):
        ruins = [f"{lid}/{p['id']}: {p['texto'][0]!r}" for lid, p in self._todos()
                 if p.get("ui") and _primeira_palavra(p["texto"][0]) not in VERBOS_PT]
        self.assertEqual(ruins, [], "\n".join(ruins))

    def test_nenhum_texto_pede_para_so_mostrar(self):
        ruins = [f"{lid}/{p['id']}: {p['texto'][0]!r}" for lid, p in self._todos()
                 if any(p["texto"][0].lower().startswith(v) for v in VAGOS_PT)]
        self.assertEqual(ruins, [], "\n".join(ruins))


if __name__ == "__main__":
    unittest.main()
