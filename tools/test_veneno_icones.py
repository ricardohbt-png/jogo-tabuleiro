"""Confere que venenos aprimorados usam o PNG da variante base."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


class VenomIconTests(unittest.TestCase):
    def test_server_variants_keep_their_base_png(self):
        items = {
            item["id"]: item for item in server.SHOP_MERCHANT
            if item.get("effect") == "coat_poison"
        }
        self.assertTrue(items)
        for item_id, item in items.items():
            with self.subTest(item_id=item_id):
                upgraded = server._preparar_item_veneno(item, {"cd": "aprimorado"})
                expected_icon = f"assets/itens/{item_id}.png"
                self.assertEqual(upgraded["icon"], expected_icon)
                self.assertTrue((ROOT / expected_icon).is_file())

    def test_giant_scorpion_loot_uses_stone_scorpion_png(self):
        item = next(i for i in server.CHEST_ITEMS if i["id"] == "veneno_escorpiao_aprimorado")
        expected_icon = "assets/itens/veneno_escorpiao_pedra.png"
        self.assertEqual(item["icon"], expected_icon)
        self.assertTrue((ROOT / expected_icon).is_file())

    def test_client_resolves_legacy_upgrade_ids_to_base_png(self):
        ids = [
            item_id for item_id, item in {
                item["id"]: item for item in server.SHOP_MERCHANT
                if item.get("effect") == "coat_poison"
            }.items()
            if (ROOT / f"assets/itens/{item_id}.png").is_file()
        ]
        script = r"""
const fs = require('fs'), vm = require('vm');
const context = {_assetURL: x => x, GS: {CATALOGO_ITENS: {}}};
vm.createContext(context);
const source = fs.readFileSync('game.js', 'utf8');
const start = source.indexOf('const ITEM_ICON_OVERRIDES');
const end = source.indexOf('\nfunction _guardarSelecaoLoja', start);
vm.runInContext(source.slice(start, end), context);
const items = JSON.parse(process.argv[1]).map(id => ({
  id: `${id}__upgrade__aprimorado_nenhum_nenhum`, effect: 'coat_poison', emoji: '☠️'
}));
console.log(JSON.stringify(items.map(item => context.itemIconHTML(item, '📦'))));
"""
        result = subprocess.run(
            ["node", "-e", script, json.dumps(ids)], cwd=ROOT, text=True,
            encoding="utf-8", capture_output=True, check=True,
        )
        rendered = json.loads(result.stdout)
        self.assertEqual(len(rendered), len(ids))
        for item_id, html in zip(ids, rendered):
            with self.subTest(item_id=item_id):
                self.assertIn(f'src="assets/itens/{item_id}.png"', html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
