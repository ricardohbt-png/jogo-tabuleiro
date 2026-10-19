import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S


class DisparoDuploTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("DISPARO_DUPLO_TEST")
        self.room.phase = "playing"
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.messages = []

        async def noop(*args, **kwargs):
            pass

        async def capture(*args, **kwargs):
            self.messages.append(args[-1])

        self.room.push_state = self.room.broadcast_city_state = noop
        self.room.broadcast = self.room.send_to = capture
        self.room.gm_say = noop
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *args: True
        self.room._apply_damage_types = lambda dmg, *args, **kwargs: dmg
        self.player = S.make_player("h", "Arqueiro", "warrior", 0)
        self.player.update(pos=[5, 5], dex=16, atk_bonus=3, level_bonus=1,
                           action_done=False, bonus_action_used=False,
                           gold=500, fome=60, sede=60)
        self.player["bag"] = []
        self.player["gear"]["off_hand"] = None
        self.room.players["h"] = self.player
        definition = next(m for m in S.MONSTER_DEFS if m["type"] == "urso_negro")
        self.target = S.make_monster(definition, {"id": 1, "cx": 6, "cy": 5})
        self.target.update(pos=[6, 5], hp=100, max_hp=100, ac=12)
        self.room.monsters[self.target["id"]] = self.target

    def crossbow(self):
        return deepcopy(next(w for w in S.SHOP_WEAPONS if w["id"] == "hand_crossbow"))

    def equip_pair(self):
        main = self.crossbow()
        off = self.crossbow()
        self.player["gear"]["weapon"] = main
        self.room._sincronizar_arma_de_combate(self.player, main)
        self.player["gear"]["off_hand"] = off
        return main, off

    def add_bolts(self, count, ammo_type="virotes"):
        item = deepcopy(next(a for a in S.SHOP_AMMO if a["id"] == ammo_type))
        item["ammo_count"] = count
        self.player["bag"].append(item)
        return item

    async def attack(self, results=(True, True)):
        calls = iter(results)

        def fixed_attack(bonus, ac, *args, **kwargs):
            hit = next(calls)
            return hit, 10, 10 + bonus, False

        with patch.object(S, "d20_attack", side_effect=fixed_attack) as rolls, \
                patch.object(S, "roll_dice", return_value=2):
            await self.room.handle_attack("h", self.target["id"])
        return rolls

    async def test_catalog_and_purchase_are_universal_and_cost_250(self):
        entry = S.GUILD_CATALOG.get("disparo_duplo")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["categoria"], "especializacao")
        self.assertIsNone(entry["classe"])
        self.assertEqual(entry["preco"], 250)
        self.assertIn("ação bônus", entry["desc"].lower())
        self.assertIn("virote", entry["desc"].lower())
        old_dir = S.GUILD_SAVE_DIR
        try:
            with tempfile.TemporaryDirectory() as tmp:
                S.GUILD_SAVE_DIR = tmp
                for index, cls in enumerate(("warrior", "mage", "cleric", "rogue", "bard", "paladin")):
                    room = S.GameRoom(f"BUY_{cls}")
                    room.phase = "city"
                    room.push_state_or_city = room.broadcast_city_state = room.push_state = room.gm_say = \
                        asyncio_coroutine_noop
                    p = S.make_player(f"p{index}", cls, cls, 0)
                    p["gold"] = 250
                    room.players[p["id"]] = p
                    await room.handle_guild_buy(p["id"], "disparo_duplo")
                    self.assertIn("disparo_duplo", p["guild_owned"]["especializacoes"], cls)
                    self.assertEqual(p["gold"], 0, cls)
        finally:
            S.GUILD_SAVE_DIR = old_dir

    async def test_offhand_crossbow_requires_talent_and_main_crossbow(self):
        item = self.crossbow()
        self.player["bag"] = [item]
        await self.room.handle_equip_offhand("h", 0)
        self.assertIsNone(self.player["gear"]["off_hand"])
        self.assertEqual(len(self.player["bag"]), 1)

        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.player["weapon"] = deepcopy(S.WEAPONS["hand_crossbow"])
        self.player["gear"]["weapon"] = deepcopy(S.WEAPONS["hand_crossbow"])
        await self.room.handle_equip_offhand("h", 0)
        self.assertEqual(self.player["gear"]["off_hand"]["id"], "hand_crossbow")
        self.assertEqual(self.player["bag"], [])

    async def test_cannot_swap_main_weapon_while_secondary_crossbow_is_equipped(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        dagger = deepcopy(S.SHOP_WEAPONS[0])
        dagger.update(id="dagger", die="1d4", item_slot="weapon")
        self.player["bag"] = [dagger]
        await self.room.handle_equip_from_bag("h", 0)
        self.assertEqual(self.player["gear"]["weapon"]["id"], "hand_crossbow")
        self.assertEqual(self.player["bag"][0]["id"], "dagger")
        await self.room.handle_quick_equip_from_bag("h", 0)
        self.assertEqual(self.player["gear"]["weapon"]["id"], "hand_crossbow")
        self.assertEqual(self.player["bag"][0]["id"], "dagger")
        await self.room.handle_unequip("h", "weapon")
        self.assertEqual(self.player["gear"]["weapon"]["id"], "hand_crossbow")
        self.assertEqual(self.player["gear"]["off_hand"]["id"], "hand_crossbow")

    async def test_two_shots_hit_same_target_spend_two_bolts_and_bonus_action_once(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        bolts = self.add_bolts(2)
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 2)
        self.assertEqual(self.target["hp"], 90)
        self.assertEqual(self.player["bag"], [])
        self.assertTrue(self.player["action_done"])
        self.assertTrue(self.player["bonus_action_used"])
        self.assertEqual(self.player["fome"], 58)
        self.assertEqual(self.player["sede"], 59)
        self.assertTrue(any(isinstance(m, dict) and m.get("offhand") for m in self.messages))
        feedback = [m for m in self.messages
                    if isinstance(m, dict) and m.get("type") == "attack_feedback"]
        self.assertEqual([m["phase"] for m in feedback], ["start", "result", "start", "result"])

    async def test_each_shot_consumes_bolt_even_when_it_misses(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.add_bolts(2)
        rolls = await self.attack((False, False))
        self.assertEqual(rolls.call_count, 2)
        self.assertEqual(self.player["bag"], [])
        self.assertTrue(self.player["bonus_action_used"])
        self.assertEqual(self.target["hp"], 100)

    async def test_one_bolt_fires_only_main_shot_without_spending_bonus_action(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.add_bolts(1)
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertEqual(self.target["hp"], 95)
        self.assertEqual(self.player["bag"], [])
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player["fome"], 59)
        self.assertEqual(self.player["sede"], 60)

    async def test_preused_bonus_action_does_not_fire_or_consume_second_bolt(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.player["bonus_action_used"] = True
        self.add_bolts(2)
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertEqual(self.player["bag"][0]["ammo_count"], 1)

    async def test_additional_main_attack_cannot_repeat_offhand_shot_in_same_turn(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.add_bolts(4)
        first = await self.attack()
        self.assertEqual(first.call_count, 2)
        self.player["action_done"] = False  # e.g. an extra main attack from another ability.
        second = await self.attack()
        self.assertEqual(second.call_count, 1)
        self.assertTrue(self.player["bonus_action_used"])
        self.assertEqual(self.player["bag"][0]["ammo_count"], 1)

    async def test_empty_quiver_rejects_main_attack_without_spending_turn(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 0)
        self.assertFalse(self.player["action_done"])
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player["fome"], 60)
        self.assertEqual(self.player["sede"], 60)

    async def test_special_bolts_are_consumed_by_both_shots(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        special = self.add_bolts(2, "virotes_prata")
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 2)
        self.assertNotIn(special, self.player["bag"])

    async def test_incendiary_bolts_apply_their_extra_damage_on_both_hits(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.add_bolts(2, "virote_incendiario")
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 2)
        self.assertEqual(self.target["hp"], 86)
        self.assertEqual(self.player["bag"], [])

    async def test_primary_kill_suppresses_secondary_and_does_not_charge_bonus(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.target["hp"] = 1
        self.add_bolts(2)
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player["bag"][0]["ammo_count"], 1)

    async def test_secondary_requires_range_and_line_of_sight(self):
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.equip_pair()
        self.target["pos"] = [5, 20]  # beyond either crossbow's maximum range.
        self.assertIsNone(await self.room._disparo_duplo_validar_alvo(
            self.player, self.target, self.target["pos"]))
        self.target["pos"] = [5, 6]
        self.room._tem_linha_de_visao = lambda *args: False
        self.assertIsNone(await self.room._disparo_duplo_validar_alvo(
            self.player, self.target, self.target["pos"]))

    async def test_no_talent_no_second_shot_and_two_handed_weapon_blocks_pair(self):
        self.equip_pair()
        self.add_bolts(2)
        rolls = await self.attack()
        self.assertEqual(rolls.call_count, 1)
        self.assertFalse(self.player["bonus_action_used"])
        self.assertEqual(self.player["bag"][0]["ammo_count"], 1)

        self.player["action_done"] = False
        self.player["guild_owned"]["especializacoes"].append("disparo_duplo")
        self.player["weapon"]["two_handed"] = True
        self.player["gear"]["off_hand"] = None
        self.player["bag"] = [self.crossbow()]
        await self.room.handle_equip_offhand("h", 0)
        self.assertIsNone(self.player["gear"]["off_hand"])

    def test_client_only_offers_second_crossbow_for_valid_pair_and_owned_talent(self):
        script = r"""
const fs=require('fs'),vm=require('vm');
const c={window:{LANG_STRINGS:{}},_assetURL:x=>x,_esc:String,_rotulo:x=>x,
  _itemAcaoMeta:()=>null,gerarHabilidadesEspeciais:()=>''};
vm.createContext(c);
vm.runInContext(fs.readFileSync('src/gameState.js','utf8')+'\nthis.api=GS;',c);
const weapon={id:'hand_crossbow',die:'1d4',range:4,item_slot:'weapon'};
const p={id:'h',name:'H',class_id:'warrior',gear:{weapon,off_hand:null},
  guild_owned:{especializacoes:[],tecnicas:[]}};
c.api.injectPreviewState({type:'game_state',master_pid:'h',test_mode:true,players:[p]});
const withoutTalent=c.api.canPlaceItem(weapon,'off_hand',{weapon});
p.guild_owned.especializacoes.push('disparo_duplo');
const withTalent=c.api.canPlaceItem(weapon,'off_hand',{weapon});
const isOffhand=c.api.isOffhandWeapon(weapon);
const twoHanded=c.api.canPlaceItem(weapon,'off_hand',{weapon:{id:'espada2m',two_handed:true}});
p.gear.off_hand=weapon;
const cannotSwapMain=c.api.canPlaceItem({id:'dagger',die:'1d4',item_slot:'weapon'},'weapon',p.gear);
p.gear.weapon={id:'dagger',die:'1d4'};
const wrongMain=c.api.canPlaceItem(weapon,'off_hand',p.gear);
console.log(JSON.stringify({withoutTalent,withTalent,twoHanded,wrongMain,cannotSwapMain,isOffhand}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data["withoutTalent"] or data["twoHanded"] or data["wrongMain"]
                         or data["cannotSwapMain"])
        self.assertTrue(data["withTalent"] and data["isOffhand"])


async def asyncio_coroutine_noop(*args, **kwargs):
    pass


if __name__ == "__main__":
    unittest.main()
