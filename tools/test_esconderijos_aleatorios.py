"""Esconderijos sorteados (tools/esconder_aleatorios.py): reprodutíveis, nunca vazios,
com mágicos e comida, sem tocar em objeto-chave/armadilha e sem repetir mágico na campanha.
Roda da raiz: python -X utf8 tools/test_esconderijos_aleatorios.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import esconder_aleatorios as A

COMIDAS = set(A.COMIDA) | set(A.BEBIDA)
MAGICOS = {i for lst in A.MAGICOS.values() for i in lst}


def copia_dos_mapas():
    pasta = tempfile.mkdtemp(prefix="esc_")
    for mapa in A.MAPAS:
        shutil.copy(os.path.join(S.DUNGEONS_DIR, f"{mapa}.json"), pasta)
    return pasta


def ler(pasta, mapa):
    with open(os.path.join(pasta, f"{mapa}.json"), encoding="utf-8") as f:
        return json.load(f)


class SorteioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = copia_dos_mapas()
        cls.ledger = {}
        cls.linhas = A.aplicar(pasta=cls.pasta, refazer=True, ledger=cls.ledger, anterior=A._ler_ledger())
        cls.mapas = {m: ler(cls.pasta, m) for m in A.MAPAS}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.pasta, ignore_errors=True)

    def esconderijos(self, defn):
        return [d for d in defn["decorations"] if d.get("escondido")]

    def test_nenhum_esconderijo_vazio_e_todos_validos(self):
        for mapa, defn in self.mapas.items():
            self.assertTrue(S.validar_dungeon(defn)[0], mapa)
            for d in self.esconderijos(defn):
                itens = d["loot"]["items"]
                self.assertTrue(itens, f"{mapa}: {d['id']} escondido e vazio")
                for it in itens:
                    self.assertIn(it["id"], S._DUNGEON_ITEM_CATALOG)
                self.assertTrue(5 <= d["cd_busca"] <= 30)

    def test_todo_mapa_com_candidatos_ganha_esconderijos(self):
        for mapa, defn in self.mapas.items():
            self.assertGreaterEqual(len(self.esconderijos(defn)), 2, mapa)

    def test_ha_magicos_e_comida_no_conjunto(self):
        itens = [it["id"] for defn in self.mapas.values() for d in self.esconderijos(defn)
                 for it in d["loot"]["items"]]
        self.assertTrue(set(itens) & MAGICOS, "nenhum item mágico escondido")
        self.assertTrue(set(itens) & COMIDAS, "nenhuma comida escondida")

    def test_mapas_tem_comida_escondida(self):
        com = sum(1 for defn in self.mapas.values()
                  if any(it["id"] in COMIDAS for d in self.esconderijos(defn) for it in d["loot"]["items"]))
        self.assertGreaterEqual(com, 15)

    def test_nao_toca_chave_armadilha_nem_conteudo_existente(self):
        for mapa in A.MAPAS:
            antes = {d["id"]: d for d in ler(S.DUNGEONS_DIR, mapa)["decorations"]}
            for d in self.mapas[mapa]["decorations"]:
                velho = antes[d["id"]]
                if velho.get("key_objective") or velho.get("trap") or velho.get("loot"):
                    self.assertEqual(d.get("loot"), velho.get("loot"), f"{mapa}: {d['id']} foi alterado")

    def test_mesmo_sorteio_nas_variantes(self):
        for a, b in (("elara_graciero_praca_viva", "elara_graciero_praca_morta"),
                     ("elara_graciero_praca_viva", "elara_graciero_praca_pedra"),
                     ("elara_leonel_1", "elara_leonel_1_alerta")):
            ea = {d["id"]: d["loot"] for d in self.esconderijos(self.mapas[a])}
            eb = {d["id"]: d["loot"] for d in self.esconderijos(self.mapas[b])}
            self.assertEqual(ea, eb, f"{a} e {b} divergem")

    def test_magico_sorteado_nao_repete_na_campanha(self):
        """Todo mágico que o sorteio colocou aparece uma única vez em toda a campanha
        (variantes que copiam outro mapa contam como o mesmo achado)."""
        variantes = {"elara_graciero_praca_morta", "elara_graciero_praca_pedra", "elara_leonel_1_alerta"}
        sorteados = {it["id"] for plano in self.ledger.values() for p in plano.values()
                     for it in p["itens"] if it["id"] in MAGICOS}
        for item in sorteados:
            onde = [m for m, defn in self.mapas.items() if m not in variantes
                    for d in self.esconderijos(defn) for it in d["loot"]["items"] if it["id"] == item]
            self.assertEqual(len(onde), 1, f"{item} aparece em {onde}")

    def test_reexecutar_reaplica_o_mesmo_resultado(self):
        antes = {m: json.dumps(d, sort_keys=True) for m, d in self.mapas.items()}
        A.aplicar(pasta=self.pasta, ledger=self.ledger)
        depois = {m: json.dumps(ler(self.pasta, m), sort_keys=True) for m in A.MAPAS}
        self.assertEqual(antes, depois)

    def test_sorteio_e_reproduzivel_com_a_mesma_semente(self):
        outra = copia_dos_mapas()
        try:
            ledger2 = {}
            A.aplicar(pasta=outra, refazer=True, ledger=ledger2, anterior=A._ler_ledger())
            self.assertEqual(self.ledger, ledger2)
        finally:
            shutil.rmtree(outra, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
