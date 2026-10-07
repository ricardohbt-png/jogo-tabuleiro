"""Regras de redação e coerência das lições por classe (fatia 4)."""
import json, re, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))

import gerar_guia_comum as G
import tutorial_guia_comum as C

TERMO = re.compile(r"\[\[([a-z0-9_]+)\]\]")
UI_OK = re.compile(r"^(?:botao:(?:encerrar_turno|inventario|magias)|monstro:[a-z0-9_]+|habilidade:[a-z0-9_]+)$")

POR_CLASSE = {
    "warrior": ["fala_5", "fala_6", "treino_mira", "treino_golpe", "treino_furia", "treino_furia_extra", "treino_guerreiro_fim"],
    "mage": ["fala_7", "fala_8", "treino_magia", "treino_slots", "treino_aprimorar_magia", "treino_estender_magia",
             "treino_fortalecer_magia", "treino_reviver", "treino_comando"],
    "rogue": ["fala_9", "fala_10", "treino_detectar", "treino_desarmar", "treino_esconder", "treino_furtivo",
              "treino_veneno", "treino_veneno_golpe", "treino_criar"],
    "cleric": ["fala_11", "fala_12", "treino_cura", "treino_cura_area", "treino_purificar", "treino_ressuscitar"],
    "bard": ["fala_13", "fala_14", "treino_cancao", "treino_cancao_manter", "treino_cancao_parar",
             "treino_provocar", "treino_instrumento"],
    "paladin": ["fala_15", "fala_16", "treino_refem", "treino_protetor", "treino_maos", "treino_sagrado",
                "treino_sagrado_golpe", "treino_regen", "treino_luz"],
}
TODAS = [i for ids in POR_CLASSE.values() for i in ids]


class ClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.todos = G.guia_todos()
        cls.d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        cls.falas = {f["id"]: f for f in cls.d["falas"]}

    def test_quarenta_e_sete_licoes(self):
        self.assertEqual(len(TODAS), 47)
        for lid in TODAS:
            self.assertIn(lid, self.todos, f"falta guia de {lid}")

    def test_cada_licao_pertence_a_classe_certa(self):
        for cls, ids in POR_CLASSE.items():
            for lid in ids:
                self.assertEqual(self.falas[lid].get("classe"), cls, lid)

    def test_regras_de_redacao(self):
        for lid in TODAS:
            passos = self.todos[lid]
            self.assertTrue(1 <= len(passos) <= 3, lid)
            for i, p in enumerate(passos):
                pt, en = p["texto"]
                self.assertTrue(pt.strip() and en.strip(), f"{lid}/{p['id']}")
                self.assertLessEqual(len(TERMO.sub("x", pt).split()), 15, f"{lid}/{p['id']}: >15 palavras")
                self.assertFalse(p.get("conclui"), f"{lid}/{p['id']}: nenhum passo desta fatia usa conclui")
                self.assertLessEqual(len(p.get("dica", [])), 2, lid)
                if p.get("ui"):
                    self.assertRegex(p["ui"], UI_OK, f"{lid}/{p['id']}")

    def test_habilidade_na_ui_e_o_alvo_da_tarefa(self):
        for lid in TODAS:
            alvo = self.falas[lid]["tarefa"].get("alvo")
            for p in self.todos[lid]:
                ui = p.get("ui") or ""
                if ui.startswith("habilidade:"):
                    self.assertEqual(ui.split(":", 1)[1], alvo, f"{lid}/{p['id']}")

    def test_termos_existem_e_batem_entre_idiomas(self):
        for lid in TODAS:
            for p in self.todos[lid]:
                pares = [p["texto"]] + ([p["porque"]] if p.get("porque") else []) + list(p.get("dica", []))
                for pt, en in pares:
                    self.assertEqual(TERMO.findall(pt), TERMO.findall(en), f"{lid}/{p['id']}")
                    for termo in TERMO.findall(pt):
                        self.assertIn(termo, C.GLOSSARIO, f"{lid}/{p['id']}: [[{termo}]]")

    def test_ultimo_passo_nunca_e_informativo_sem_acao(self):
        # o último passo precisa dizer o que FAZER (a tarefa o encerra); ids dos passos únicos por lição
        for lid in TODAS:
            ids = [p["id"] for p in self.todos[lid]]
            self.assertEqual(len(ids), len(set(ids)), lid)


if __name__ == "__main__":
    unittest.main()
