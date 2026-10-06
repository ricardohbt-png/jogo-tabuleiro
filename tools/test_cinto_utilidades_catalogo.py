"""Catálogo e apresentação dos cintos. Rodar da raiz com python -X utf8."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server
from tools import export_catalog

BELTS = {
    "cinto_utilidades": (80, 4, "Cinto de Utilidades"),
    "cinto_com_bolsos": (30, 2, "Cinto com Bolsos"),
}
ICON = "assets/itens/cinto_e_bolsos.png"


class BeltCatalogTests(unittest.TestCase):
    def test_merchant_definitions(self):
        merchant = {item["id"]: item for item in server.SHOP_MERCHANT}
        for item_id, (price, pockets, name) in BELTS.items():
            with self.subTest(item_id=item_id):
                self.assertTrue(item_id in merchant, f"mercador: falta {item_id}")
                item = merchant[item_id]
                self.assertEqual(item["price"], price)
                self.assertEqual(item["item_slot"], "item")
                self.assertEqual(item["name"], name)
                self.assertEqual(item["icon"], ICON)
                self.assertIn(str(pockets), item["descricao"])
                self.assertIn("4 unidades iguais", item["descricao"])
                for word in ("arremessáveis", "frascos", "poções", "venenos", "equipado"):
                    self.assertIn(word, item["descricao"])
        self.assertTrue((ROOT / ICON).is_file())

    def test_dungeon_export_includes_both_belts(self):
        exported = {item["id"]: item for item in export_catalog.build_catalog()["items"]}
        for item_id in BELTS:
            with self.subTest(item_id=item_id):
                self.assertTrue(item_id in server._DUNGEON_ITEM_CATALOG, f"loot: falta {item_id}")
                self.assertTrue(item_id in exported, f"exportação: falta {item_id}")
                self.assertEqual(exported[item_id]["item_slot"], "item")

    def test_client_catalog_and_localization(self):
        script = r"""
const fs = require('fs'), vm = require('vm');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync('src/gameState.js', 'utf8') + '\nthis.catalog = GS.CATALOGO_ITENS;', context);
const locales = {window:{LANG_STRINGS:{}}};
vm.createContext(locales);
vm.runInContext(fs.readFileSync('src/lang/catalogo.js', 'utf8'), locales);
console.log(JSON.stringify({catalog:context.catalog, lang:locales.window.LANG_CATALOGO}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True,
                                encoding="utf-8", capture_output=True, check=True)
        data = json.loads(result.stdout)
        for item_id, (price, _, name) in BELTS.items():
            with self.subTest(item_id=item_id):
                self.assertTrue(item_id in data["catalog"], f"cliente: falta {item_id}")
                item = data["catalog"][item_id]
                self.assertEqual(item["nome"], name)
                self.assertEqual(item["preco"], price)
                self.assertEqual(item["tipo"], "itemMagico")
                self.assertEqual(item["item_slot"], "item")
                self.assertEqual(item["icon"], ICON)
                self.assertEqual(item["permitidoPara"], ["todos"])
                for field, value in (("nome", name), ("desc", item["descricao"])):
                    key = f"cat.item.{item_id}.{field}"
                    self.assertIn(key, data["lang"])
                    self.assertEqual(data["lang"][key]["pt"], value)
                    self.assertTrue(data["lang"][key]["en"])

    def test_shared_icon_and_existing_fallbacks(self):
        script = r"""
const fs = require('fs'), vm = require('vm');
const context = {_assetURL: x => x};
vm.createContext(context);
vm.runInContext(fs.readFileSync('src/gameState.js', 'utf8'), context);
const source = fs.readFileSync('game.js', 'utf8');
const start = source.indexOf('function itemIconHTML(');
const end = source.indexOf('\nfunction _guardarSelecaoLoja', start);
vm.runInContext(source.slice(start,end), context);
const items = [{id:'cinto_utilidades'}, {id:'cinto_com_bolsos'},
  {id:'cinto_utilidades',icon:'assets/itens/cinto_e_bolsos.png'},
  {id:'antidote'}, {id:'pergaminho_bola_fogo',effect:'scroll'},
  {id:'instrumento_harpa_velho',tipo_item:'instrumento',base:'harpa'}];
console.log(JSON.stringify(items.map(item => context.itemIconHTML(item,'📦'))));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True,
                                encoding="utf-8", capture_output=True, check=True)
        icons = json.loads(result.stdout)
        for index in range(3):
            self.assertIn(f'src="{ICON}"', icons[index])
        for index, file_id in ((3, "antidote"), (4, "pergaminho"), (5, "harpa")):
            self.assertIn(f'src="assets/itens/{file_id}.png"', icons[index])
            self.assertIn('data-fallback="📦"', icons[index])


if __name__ == "__main__":
    unittest.main(verbosity=2)
