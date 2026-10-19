"""O Frasco de Piche usa o mesmo PNG no catálogo, loja e inventário."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server

ICON = "assets/itens/frasco_piche.png"


class FrascoPicheIconTests(unittest.TestCase):
    def test_server_merchant_item_points_to_its_png(self):
        item = next(item for item in server.SHOP_MERCHANT if item["id"] == "frasco_piche")
        self.assertEqual(item.get("icon"), ICON)
        self.assertTrue((ROOT / ICON).is_file())

    def test_client_catalog_and_inventory_icon_use_the_same_png(self):
        script = r"""
const fs = require('fs'), vm = require('vm');
const context = {_assetURL: x => x};
vm.createContext(context);
vm.runInContext(fs.readFileSync('src/gameState.js', 'utf8') + '\nthis.GS = GS;', context);
const source = fs.readFileSync('game.js', 'utf8');
const start = source.indexOf('const ITEM_ICON_OVERRIDES =');
const end = source.indexOf('\nfunction _guardarSelecaoLoja', start);
vm.runInContext(source.slice(start, end), context);
console.log(JSON.stringify({
  item: context.GS.CATALOGO_ITENS.frasco_piche,
  html: context.itemIconHTML({id:'frasco_piche', emoji:'🛢️'}, '📦')
}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True,
                                encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["item"].get("icon"), ICON)
        self.assertIn(f'src="{ICON}"', data["html"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
