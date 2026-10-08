"""Conteúdo do guia da trilha comum: regras de redação, paridade pt/en e validação."""
import json, re, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))

import tutorial_guia_comum as C
import gerar_guia_comum as G

IDS_ESPERADOS = ["fala_0", "fala_1", "fala_2", "fala_3", "fala_4", "fala_18", "fala_19",
                 "fala_29", "fala_30", "fala_31", "fala_32", "fala_33", "fala_atalhos", "fala_res", "fala_vuln"]
UI_OK = re.compile(r"^(?:(?:botao|bolsa|monstro):[a-z0-9_]+|(?:casa|porta):\[\d+,\d+\])$")
TERMO = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def textos(passo):
    yield passo["texto"]
    if passo.get("porque"): yield passo["porque"]
    yield from passo.get("dica", [])


class ConteudoTests(unittest.TestCase):
    def test_cobre_as_quinze_licoes(self):
        self.assertEqual(sorted(C.GUIA), sorted(IDS_ESPERADOS))

    def test_licao_de_atalhos_cobre_os_quatro_temas(self):
        txt = " ".join(p["texto"][0].lower() for p in C.GUIA["fala_atalhos"])
        for tema in ("atalho", " r ", "esc", "clique"):
            self.assertIn(tema, " " + txt.replace(".", " ") + " ", tema)

    def test_regras_de_redacao(self):
        for lid, passos in C.GUIA.items():
            self.assertTrue(1 <= len(passos) <= 4, lid)
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

    def test_licoes_de_dano_usam_o_esqueleto_e_o_glossario(self):
        for lid in ("fala_res", "fala_vuln"):
            self.assertTrue(any(p.get("ui") == "monstro:esqueleto_humano" for p in C.GUIA[lid]), lid)
            self.assertLessEqual(len(C.GUIA[lid]), 4, lid)
            for p in C.GUIA[lid]:
                self.assertLessEqual(len(p["texto"][0].split()), 15, f"{lid}/{p['id']}")
        self.assertIn("vulnerabilidade", C.GLOSSARIO)
        self.assertIn("resistencia", C.GLOSSARIO)
        # regra de ouro: equipar nunca conclui passo (pode ter ocorrido antes da lição)
        for p in C.GUIA["fala_vuln"]:
            self.assertNotEqual((p.get("conclui") or ""), "equipar")

    def test_licoes_de_dano_ficam_depois_dos_atalhos_e_em_ordem_estrita(self):
        d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        comuns = [f for f in d["falas"] if f.get("ordem") is not None and not f.get("classe")]
        o = {f["id"]: f["ordem"] for f in comuns}
        self.assertLess(o["fala_atalhos"], o["fala_res"])
        self.assertLess(o["fala_res"], o["fala_vuln"])
        self.assertEqual(len(o.values()), len(set(o.values())))
        # a ordem estrita libera as duas em sequência, e só depois de toda a trilha anterior
        import server, types
        sala = types.SimpleNamespace(licoes=comuns, _training_requirements=lambda p, f: True)
        lib = lambda p, f: server.GameRoom._licao_liberada(sala, p, f)
        fala = {f["id"]: f for f in comuns}
        feitas = [f["id"] for f in comuns if f["ordem"] <= o["fala_atalhos"]]
        p = {"licoes_feitas": feitas[:-1]}
        self.assertFalse(lib(p, fala["fala_res"]))
        p = {"licoes_feitas": feitas}
        self.assertTrue(lib(p, fala["fala_res"]))
        self.assertFalse(lib(p, fala["fala_vuln"]))
        p["licoes_feitas"] = feitas + ["fala_res"]
        self.assertTrue(lib(p, fala["fala_vuln"]))

    def test_esqueleto_tem_so_as_duas_licoes_de_dano(self):
        d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        ids = {f["id"] for f in d["falas"]}
        for velho in ("fala_36", "fala_37", "fala_38"):
            self.assertNotIn(velho, ids)
            self.assertNotIn(velho, C.GUIA)
        falas = {f["id"]: f for f in d["falas"]}
        for lid in ("fala_res", "fala_vuln"):
            self.assertEqual(falas[lid]["tarefa"]["tipo"], "atacar")
            self.assertEqual(falas[lid]["tarefa"]["alvo"], "esqueleto_humano")
        # um esqueleto por lição, com um de folga contra beco sem saída
        esq = [m for m in d["monsters"] if m["type"] == "esqueleto_humano"]
        self.assertEqual(len(esq), 2)

    def test_vuln_ensina_pegar_equipar_e_atacar(self):
        g = C.GUIA["fala_vuln"]
        self.assertEqual([p["id"] for p in g], ["pegar", "equipar", "atacar"])
        d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        bau = [c for c in d["chests"] if any(i["id"] == "maca_treino" for i in c["items"])][0]
        if g[0].get("ui"):
            self.assertEqual(g[0]["ui"], "casa:" + json.dumps(bau["pos"]).replace(" ", ""))
        for p in g[:2]:
            self.assertFalse(p.get("conclui"), p["id"])
        dicas = " ".join(x[0] for p in g for x in p.get("dica", [])).lower()
        self.assertIn("arma certa", dicas)

    def test_termos_iguais_em_pt_e_en(self):
        for lid, passos in C.GUIA.items():
            for p in passos:
                for pt, en in textos(p):
                    self.assertEqual(TERMO.findall(pt), TERMO.findall(en), f"{lid}/{p['id']}")

    def test_glossario_completo(self):
        esperados = {"turno", "movimento", "acao_livre", "acao_bonus", "ca", "fome_sede", "resistencia",
                     "d20", "acao_principal", "slot", "teste_resistencia", "manutencao", "furtivo", "critico", "atalho", "vulnerabilidade"}
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
                    alvo = ui.split(":", 1)[1]
                    baus = {json.dumps(c["pos"]).replace(" ", "") for c in d["chests"]}
                    # casa pode ser o alvo da tarefa ou o baú da sala (passo de pegar item)
                    self.assertIn(alvo, {json.dumps(tar.get("alvo")).replace(" ", "")} | baus, lid)


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
