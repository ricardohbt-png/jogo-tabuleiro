"""Abas do Mercador por tipo: elmos, anéis, botas, talismãs e amuletos, mochila e carga e
"outros equipamentos" além das que já existiam. Cada item cai em UMA aba, nada some e a
regra vale para o estoque real de cada cidade.
Roda da raiz: python -X utf8 tools/test_mercador_abas.py"""
import json
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

NODE = r"""
const fs = require('fs'), path = require('path'), vm = require('vm');
const ctx = { window: { LANG_STRINGS: {} }, WebSocket: class { constructor(){ this.readyState = 1; } send(){} close(){} },
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  location: { search: '', protocol: 'http:', host: 'x' }, setTimeout: () => 0, clearTimeout: () => {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(process.argv[1], 'src/gameState.js'), 'utf8') + '\nthis.api=GS;', ctx);
const GS = ctx.api;
const entrada = JSON.parse(fs.readFileSync(0, 'utf8'));
const saida = { abas: GS.ABAS_MERCADOR, itens: {} };
for (const [cidade, lista] of Object.entries(entrada)) saida.itens[cidade] = lista.map(i => [i.id, GS.abaMercadorDoItem(i)]);
process.stdout.write(JSON.stringify(saida));
"""


def itens_do_mercador():
    """O que o cliente recebe de cada cidade: o catálogo filtrado pelas ids da loja."""
    cat = {i["id"]: i for i in S.SHOP_MERCHANT}
    out = {}
    for cidade, lojas in S.CITY_SHOPS.items():
        ids = (lojas or {}).get("mercador")
        if ids:
            out[cidade] = [cat[i] for i in ids if i in cat]
    return out


def rodar_node(entrada):
    r = subprocess.run(["node", "-e", NODE, RAIZ], input=json.dumps(entrada), capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class AbasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entrada = itens_do_mercador()
        cls.res = rodar_node(cls.entrada)
        cls.abas = cls.res["abas"]

    def aba_de(self, item_id):
        for lista in self.res["itens"].values():
            for iid, aba in lista:
                if iid == item_id:
                    return aba
        self.fail(f"{item_id} não está em nenhum Mercador")

    def test_ordem_das_abas(self):
        self.assertEqual(self.abas, ["elmos", "aneis", "botas", "talismas_amuletos", "mochila_carga",
                                     "grimorios", "outros_equipamentos", "consumiveis", "instrumentos", "arremessaveis",
                                     "venenos", "pergaminhos", "vender"])
        self.assertEqual(self.abas[-1], "vender")

    def test_todo_item_cai_em_uma_aba_valida_e_nada_some(self):
        validas = set(self.abas) - {"vender"}
        for cidade, lista in self.res["itens"].items():
            self.assertEqual(len(lista), len(self.entrada[cidade]), cidade)
            for iid, aba in lista:
                self.assertIn(aba, validas, f"{cidade}: {iid} -> {aba}")

    def test_pedidos_do_usuario(self):
        for it in S.SHOP_MERCHANT:
            iid = it["id"]
            slot = it.get("item_slot")
            if iid not in {i for l in self.res["itens"].values() for i, _ in l}:
                continue
            if it.get("effect") in ("scroll", "throwable", "coat_poison") or it.get("tipo_item") == "instrumento":
                continue
            if slot == "head":
                self.assertEqual(self.aba_de(iid), "elmos", iid)
            elif slot == "ring":
                self.assertEqual(self.aba_de(iid), "aneis", iid)
            elif slot == "boots":
                self.assertEqual(self.aba_de(iid), "botas", iid)
            elif slot == "item" and it.get("effect") in ("bagslots", "utility_belt"):
                self.assertEqual(self.aba_de(iid), "mochila_carga", iid)

    def test_talismas_amuletos_e_sobras(self):
        for iid in ("talisma_despertar_forca", "talisma_ascensao_inteligencia", "amulet", "amulet_alcance_arcano",
                    "amuleto_jornada", "amuleto_jornada_infindavel", "relicario_jornada_eterna"):
            self.assertEqual(self.aba_de(iid), "talismas_amuletos", iid)
        self.assertEqual(self.aba_de("ultimo_suspiro"), "outros_equipamentos")

    def test_grimorios_e_bola_de_cristal(self):
        grimorios = [i["id"] for i in S.SHOP_MERCHANT if i.get("effect") == "grimoire"]
        self.assertEqual(len(grimorios), 10)
        for iid in grimorios + ["bola_cristal_clarividencia"]:
            self.assertEqual(self.aba_de(iid), "grimorios", iid)

    def test_mochilas_e_cintos_especificos(self):
        for iid in ("mochila_carga", "mochila_dimensional", "mochila_aljava_dimensional", "cinto_utilidades",
                    "cinto_arsenal_encantado", "alforge_explorador", "alforge_explorador_superior",
                    "maravilha_aventureiro_menor", "maravilha_aventureiro_maior"):
            self.assertEqual(self.aba_de(iid), "mochila_carga", iid)

    def test_abas_que_ja_existiam_continuam_iguais(self):
        self.assertEqual(self.aba_de("instrumento_alaude_padrao"), "instrumentos")
        self.assertEqual(self.aba_de("granada"), "arremessaveis")
        self.assertEqual(self.aba_de("veneno_aranha_sombria"), "venenos")
        self.assertEqual(self.aba_de("pocao_voo"), "consumiveis")
        self.assertEqual(self.aba_de("antidote"), "consumiveis")

    def test_cada_aba_nova_tem_itens_nas_cidades_grandes(self):
        lista = self.res["itens"]["alva_e_luz"]
        for aba in ("elmos", "aneis", "botas", "talismas_amuletos", "mochila_carga", "grimorios",
                    "outros_equipamentos", "consumiveis"):
            self.assertTrue(any(a == aba for _, a in lista), aba)


if __name__ == "__main__":
    unittest.main()
