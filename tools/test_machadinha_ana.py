"""Contrato da machadinha: compra, mãos, arremesso, desgaste e reparo."""
import json
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

IID = "machadinha_arremesso_ana"
ICON = f"assets/itens/{IID}.png"


class MachadinhaTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.assertIn(IID, S.WEAPONS, "falta a nova arma no catálogo autoritativo")
        self.r = S.GameRoom("MACHADINHA_TEST")
        self.r.phase = "playing"
        self.r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.messages = []

        async def noop(*args, **kwargs):
            pass

        async def capture(*args, **kwargs):
            self.messages.append(args[-1])

        self.r.push_state = self.r.broadcast_city_state = noop
        self.r.broadcast = capture
        self.r.send_to = capture
        self.r.gm_say = noop
        self.r._is_turn = lambda pid: True
        self.r._tem_linha_de_visao = lambda *args: True
        self.p = S.make_player("h", "Anão", "warrior", 0)
        self.p.update(pos=[5, 5], str_=18, dex=8, atk_bonus=5, level_bonus=1,
                      action_done=False, bonus_action_used=False, gold=100, fome=60, sede=60)
        self.p["bag"] = []
        self.p["gear"]["off_hand"] = None
        self.r.players["h"] = self.p
        mdef = next(m for m in S.MONSTER_DEFS if m["type"] == "urso_negro")
        self.m = S.make_monster(mdef, {"id": 1, "cx": 6, "cy": 5})
        self.m.update(pos=[6, 5], hp=100, max_hp=100, ac=15)
        self.r.monsters[self.m["id"]] = self.m

    def axe(self, level=0):
        item = deepcopy(next(w for w in S.SHOP_WEAPONS if w["id"] == IID))
        item.update(item_slot="weapon", effect="atk", value=0)
        if level:
            item["corrosion_level"] = level
        return item

    def equip(self, slot="weapon", level=0):
        item = self.axe(level)
        self.p["gear"][slot] = item
        if slot == "weapon":
            self.r._sincronizar_arma_de_combate(self.p, item)
        return item

    def drops(self):
        return [item for chest in self.r.chests.values() for item in chest["items"]]

    async def throw(self, roll, slot="weapon"):
        with patch.object(S.random, "randint", return_value=roll), \
                patch.object(S, "roll_dice", return_value=4):
            await self.r.handle_throw("h", self.m["id"], slot)

    async def attack(self):
        def fixed_attack(bonus, ac, *args, **kwargs):
            return 10 + bonus >= ac, 10, 10 + bonus, False
        with patch.object(S, "d20_attack", side_effect=fixed_attack) as rolls, \
                patch.object(S, "roll_dice", return_value=4):
            await self.r.handle_attack("h", self.m["id"])
        return rolls

    async def test_catalog_and_purchase_keep_weapon_rules(self):
        self.r.phase = "city"
        self.r.world_location = "alva_e_luz"
        await self.r.handle_shop_buy("h", "ferreiro_weapon", IID)
        self.assertEqual(self.p["gold"], 65)
        item = next(i for i in self.p["bag"] if i["id"] == IID)
        for key, value in {"die": "1d6", "throw_range": 3, "allowed_classes": ["warrior"],
                           "icon": ICON, "off_hand_stat": "str_",
                           "throw_nat1_damage_levels": 2, "corrosion_max": 3}.items():
            self.assertEqual(item.get(key), value, key)
        self.assertTrue((ROOT / ICON).is_file())
        from tools.export_catalog import build_catalog
        exported = next(i for i in build_catalog()["items"] if i["id"] == IID)
        self.assertEqual(exported["allowed_classes"], ["warrior"])
        self.assertEqual(exported["off_hand_stat"], "str_")

    async def test_class_restriction_all_equip_paths_even_without_copied_metadata(self):
        self.p["class_id"] = "mage"
        for handler in (self.r.handle_equip_from_bag, self.r.handle_quick_equip_from_bag,
                        self.r.handle_equip_offhand):
            with self.subTest(handler=handler.__name__):
                item = self.axe()
                item.pop("allowed_classes", None)
                self.p["bag"] = [item]
                await handler("h", 0)
                self.assertEqual(len(self.p["bag"]), 1)
                self.assertTrue(any(isinstance(x, dict) and x.get("type") == "error"
                                    for x in self.messages))
                self.messages.clear()

    async def test_equips_both_hands_and_blocks_two_handed_main(self):
        self.p["bag"] = [self.axe(), self.axe()]
        await self.r.handle_equip_from_bag("h", 0)
        await self.r.handle_equip_offhand("h", 0)
        self.assertEqual(self.p["gear"]["weapon"]["id"], IID)
        self.assertEqual(self.p["gear"]["off_hand"]["id"], IID)
        self.assertIsNot(self.p["gear"]["weapon"], self.p["gear"]["off_hand"])
        self.p["weapon"] = {"id": "espada2m", "two_handed": True}
        self.p["gear"]["off_hand"] = None
        self.p["bag"] = [self.axe()]
        await self.r.handle_equip_offhand("h", 0)
        self.assertIsNone(self.p["gear"]["off_hand"])

    async def test_offhand_uses_strength_and_bonus_action_once(self):
        self.equip()
        self.equip("off_hand")
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 2)
        self.assertEqual(rolls.call_args_list[-1].args[0], 5)
        self.assertEqual(self.m["hp"], 84)
        self.assertTrue(self.p["bonus_action_used"])
        self.p["action_done"] = False
        await self.attack()
        self.assertEqual(self.m["hp"], 76)

    async def test_offhand_does_not_attack_dead_or_nonadjacent_target(self):
        self.equip()
        self.equip("off_hand")
        self.m["hp"] = 1
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertFalse(self.p["bonus_action_used"])
        self.m.update(hp=100, pos=[7, 5])
        self.p["action_done"] = False
        self.p["weapon"] = deepcopy(S.WEAPONS["lanca"])
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertFalse(self.p["bonus_action_used"])

    async def test_throw_strength_range_and_action_budget(self):
        self.equip()
        self.equip("off_hand")
        self.m["pos"] = [8, 5]
        await self.throw(10)
        self.assertEqual(self.m["hp"], 92)
        self.assertTrue(self.p["action_done"])
        self.assertFalse(self.p["bonus_action_used"])
        self.assertIsNone(self.p["gear"]["weapon"])
        await self.throw(10, "off_hand")
        self.assertEqual(self.m["hp"], 84)
        self.assertTrue(self.p["bonus_action_used"])
        self.assertEqual(len(self.drops()), 2)

    async def test_invalid_throw_preserves_equipment_and_actions(self):
        item = self.equip()
        self.m["pos"] = [9, 5]
        await self.throw(1)
        self.assertIs(self.p["gear"]["weapon"], item)
        self.assertFalse(self.p["action_done"])
        self.m["pos"] = [7, 5]
        self.r._tem_linha_de_visao = lambda *args: False
        await self.throw(1)
        self.assertIs(self.p["gear"]["weapon"], item)
        self.assertEqual(self.r._nivel_corrosao_item(item), 0)

    async def test_nat1_damages_only_thrown_copy_and_can_be_recovered(self):
        other = self.equip()
        self.equip("off_hand")
        await self.throw(1, "off_hand")
        self.assertIs(self.p["gear"]["weapon"], other)
        self.assertEqual(self.r._nivel_corrosao_item(other), 0)
        self.assertEqual(len(self.drops()), 1)
        self.assertEqual(self.drops()[0]["corrosion_level"], 2)
        cid = next(iter(self.r.chests))
        await self.r.handle_take_from_chest("h", cid, "item", 0)
        item = next(i for i in self.p["bag"] if i["id"] == IID)
        self.assertEqual(item["corrosion_level"], 2)
        await self.r.handle_equip_offhand("h", self.p["bag"].index(item))
        self.p.update(action_done=False, bonus_action_used=False)
        self.m["ac"] = 13
        rolls = await self.attack()
        self.assertEqual(rolls.call_args_list[-1].args[0], 3)
        self.assertEqual(self.m["hp"], 86)  # principal 8 + secundária danificada 6

    async def test_nat1_destroys_already_damaged_weapon(self):
        for level in (1, 2):
            with self.subTest(level=level):
                self.r.chests.clear()
                self.equip(level=level)
                self.p.update(action_done=False, bonus_action_used=False)
                await self.throw(1)
                self.assertFalse(self.drops())
                self.assertIsNone(self.p["gear"]["weapon"])
                self.assertEqual(self.p["weapon"]["id"], "unarmed")

    async def test_acid_damage_also_counts_towards_destruction(self):
        self.equip()
        self.p["gear"]["armor"] = None
        await self.r._corroer_equipamento(None, self.p, S.CORROSAO_ARMADURA_METAL,
                                          S.CORROSAO_ARMA_METAL, notify=False)
        self.assertEqual(self.p["gear"]["weapon"]["corrosion_level"], 1)
        await self.throw(1)
        self.assertFalse(self.drops())
        self.assertEqual(self.p["weapon"]["id"], "unarmed")

    async def test_mainhand_wear_does_not_reduce_clean_offhand_attack(self):
        self.equip(level=2)
        self.equip("off_hand")
        self.m["ac"] = 13
        rolls = await self.attack()
        self.assertEqual(rolls.call_args_list[0].args[0], 3)
        self.assertEqual(rolls.call_args_list[1].args[0], 5)
        self.assertEqual(self.m["hp"], 86)

    async def test_thrown_and_secondary_attacks_respect_physical_immunity(self):
        self.equip()
        self.equip("off_hand")
        self.m["immunities"] = [S.DMG_PHYSICAL]
        await self.throw(20)
        self.assertEqual(self.m["hp"], 100)
        self.equip()
        self.p.update(action_done=False, bonus_action_used=False)
        await self.attack()
        self.assertEqual(self.m["hp"], 100)

    async def test_wear_survives_requip_and_does_not_penalize_other_weapon(self):
        item = self.equip(level=2)
        self.assertEqual(self.r._corrosao_arma_pen(self.p), 2)
        await self.r.handle_unequip("h", "weapon")
        self.assertEqual(item["corrosion_level"], 2)
        self.p["bag"].append(deepcopy(S.SHOP_WEAPONS[0]))
        await self.r.handle_equip_from_bag("h", len(self.p["bag"]) - 1)
        self.assertEqual(self.r._corrosao_arma_pen(self.p), 0)
        await self.r.handle_equip_from_bag("h", self.p["bag"].index(item))
        self.r._resetar_corrosao(self.p)
        self.assertEqual(self.r._corrosao_arma_pen(self.p), 2)
        await self.throw(10)
        self.assertEqual(self.m["hp"], 100)  # 10 + FOR 4 + nível 1 - desgaste 2 < CA 15
        self.assertEqual(self.drops()[0]["corrosion_level"], 2)

    async def test_repair_bag_and_equipped_offhand_restores_weapon(self):
        for location in ("bag", "off_hand", "weapon"):
            with self.subTest(location=location):
                self.p["bag"] = []
                self.p["gear"]["off_hand"] = None
                self.p["gear"]["weapon"] = None
                self.p["weapon"] = deepcopy(S.WEAPONS["unarmed"])
                if location == "bag":
                    item = self.axe(2)
                    self.p["bag"] = [item]
                else:
                    item = self.equip(location, 2)
                self.r.phase = "city"
                self.r.world_location = "alva_e_luz"
                before = self.p["gold"] = 100
                options = self.r._opcoes_reparo_ferreiro(self.p)
                self.assertEqual(len(options), 1)
                self.assertEqual(options[0]["cost"], 22)
                await self.r.handle_repair_item("h", options[0]["slot"], options[0]["bag_index"])
                self.assertEqual(self.p["gold"], before - 22)
                self.assertEqual(self.r._nivel_corrosao_item(item), 0)

    async def test_unauthorized_equipped_weapon_cannot_be_used(self):
        self.equip()
        self.p["class_id"] = "mage"
        await self.throw(20)
        await self.attack()
        self.assertEqual(self.m["hp"], 100)
        self.assertFalse(self.p["action_done"])
        self.assertIsNotNone(self.p["gear"]["weapon"])

    def test_client_catalog_slots_and_durability_tooltip(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const c={window:{LANG_STRINGS:{}},_assetURL:x=>x,_esc:String,
  _rotulo:x=>x,_itemAcaoMeta:()=>null,gerarHabilidadesEspeciais:()=>''};
vm.createContext(c);
vm.runInContext(fs.readFileSync('src/gameState.js','utf8')+'\nthis.api=GS;',c);
vm.runInContext(fs.readFileSync('src/lang/interface.js','utf8'),c);
vm.runInContext(fs.readFileSync('src/lang/catalogo.js','utf8'),c);
c.t=(key,args={})=>(c.window.LANG_STRINGS[key]?.pt||key).replace(/\{(\w+)\}/g,(_,k)=>args[k]??'');
const source=fs.readFileSync('game.js','utf8');
vm.runInContext(source.slice(source.indexOf('function renderLinhaTooltip('),
  source.indexOf('function gerarHabilidadesEspeciais(')),c);
const item=c.api.CATALOGO_ITENS.machadinha_arremesso_ana;
Object.defineProperty(c.api,'me',{configurable:true,value:{class_id:'warrior'}});
const main=c.api.canPlaceItem(item,'weapon',{}),off=c.api.canPlaceItem(item,'off_hand',{});
const two=c.api.canPlaceItem(item,'off_hand',{weapon:{two_handed:true}});
Object.defineProperty(c.api,'me',{configurable:true,value:{class_id:'mage'}});
const forbidden=c.api.canPlaceItem(item,'weapon',{});
console.log(JSON.stringify({item,main,off,two,forbidden,
  html:c.gerarConteudoTooltip({id:item.id,corrosion_level:2}),
  localized:c.window.LANG_CATALOGO['cat.item.machadinha_arremesso_ana.nome']}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["main"] and data["off"])
        self.assertFalse(data["two"] or data["forbidden"])
        self.assertEqual(data["item"]["preco"], 35)
        self.assertIn("1/3", data["html"])
        self.assertIn("-2", data["html"])
        self.assertEqual(data["localized"]["pt"], "Machadinha de Arremesso Anã")


if __name__ == "__main__":
    unittest.main(verbosity=2)
