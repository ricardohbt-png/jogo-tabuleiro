"""Server/client/asset contract: python -X utf8 tools/test_goblin_combatente_variants.py."""
import json
import re
import subprocess
import unittest
from pathlib import Path

from test_goblin_combatente_equipamento import S, spawn


ROOT = Path(__file__).resolve().parents[1]
# Literal expectations are independent of the production key builder.
VARIANTS = (
    ("lanca_curta", "goblinCombatente_lanca_curta_sem_escudo", "goblinCombatente_lanca_curta_com_escudo"),
    ("bordao", "goblinCombatente_bordao_sem_escudo", "goblinCombatente_bordao_com_escudo"),
    ("cajado_madeira", "goblinCombatente_cajado_madeira_sem_escudo", "goblinCombatente_cajado_madeira_com_escudo"),
    ("shortsword", "goblinCombatente_shortsword_sem_escudo", "goblinCombatente_shortsword_com_escudo"),
    ("maca", "goblinCombatente_maca_sem_escudo", "goblinCombatente_maca_com_escudo"),
    ("machado_basico", "goblinCombatente_machado_basico_sem_escudo", "goblinCombatente_machado_basico_com_escudo"),
)


def client_resolve(monsters):
    """Execute the real client resolvers without booting DOM/Three.js UI."""
    source = (ROOT / "game.js").read_text(encoding="utf-8")
    pieces = []
    for name in ("_MONSTER_TYPE_DEFAULT_IMAGE", "_MONSTER_GLB_MODELS"):
        match = re.search(r"const " + name + r" = Object\.freeze\(\{.*?^\}\);", source,
                          re.MULTILINE | re.DOTALL)
        if not match:
            raise AssertionError(f"Client resolver table missing: {name}")
        pieces.append(match.group())
    for name in ("_monsterImageName", "_metamorfoseVisualName", "_getMonster2DImg",
                 "_monsterGLBPath", "_facingToRotY", "_monsterFacingToRotY"):
        match = re.search(r"function " + name + r"\(.*?^\}", source,
                          re.MULTILINE | re.DOTALL)
        if not match:
            raise AssertionError(f"Client resolver function missing: {name}")
        pieces.append(match.group())
    # Only browser image construction and URL decoration are replaced. The
    # selected image key, PNG path and GLB path all come from production code.
    script = "\n".join(pieces) + "\n" + r"""
const _mon2DImg = {};
class Image {}
function _assetURL(path) { return path; }
function _rerender2DAfterAssetLoad() {}
const monsters = JSON.parse(require('fs').readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(monsters.map(monster => {
  const image = _monsterImageName(monster);
  const glb = _monsterGLBPath(image, monster.type);
  return {
    image,
    png: _getMonster2DImg(image)?.src || null,
    glb,
    facing: _monsterFacingToRotY([1, 0], image, monster.type, glb),
  };
})));
"""
    result = subprocess.run(["node", "-e", script], input=json.dumps(monsters),
                            text=True, capture_output=True, cwd=ROOT, check=True)
    return json.loads(result.stdout)


class CombatantVariantTests(unittest.TestCase):
    def test_each_server_key_matches_actual_weapon_and_optional_shield(self):
        for index, (weapon, without_shield, with_shield) in enumerate(VARIANTS):
            for shield, key in ((False, without_shield), (True, with_shield)):
                for potion in (False, True):
                    with self.subTest(weapon=weapon, shield=shield, potion=potion):
                        monster = spawn(index, 0 if shield else 0.99, 0 if potion else 0.99)
                        self.assertEqual(monster["combatant_weapon_id"], weapon)
                        self.assertEqual(monster["combatant_shield_id"], "escudo_p" if shield else None)
                        self.assertEqual(monster["image"], key)

    def test_variant_keys_reach_the_public_game_state(self):
        room = S.GameRoom("GOBLIN_VARIANT_TEST")
        expected = {}
        for index, (_weapon, without_shield, with_shield) in enumerate(VARIANTS):
            for shield, key in ((False, without_shield), (True, with_shield)):
                monster = spawn(index, 0 if shield else 0.99)
                room.monsters[monster["id"]] = monster
                expected[monster["id"]] = key
        payload = room._game_state_payload()
        self.assertEqual({m["id"]: m["image"] for m in payload["monsters"]}, expected)

    def test_client_resolves_all_twelve_keys_to_matching_png_and_glb(self):
        keys = [key for _weapon, *pair in VARIANTS for key in pair]
        resolved = client_resolve([{"type": "goblin_combatente", "image": key} for key in keys])
        for key, result in zip(keys, resolved):
            with self.subTest(key=key):
                self.assertEqual(result["image"], key)
                self.assertEqual(result["png"], f"assets/pawns/monstros/{key}/{key}.png")
                self.assertEqual(result["glb"], f"assets/models3d/monstros/{key}.glb")

    def test_all_twelve_matching_png_files_exist(self):
        for _weapon, *keys in VARIANTS:
            for key in keys:
                with self.subTest(key=key):
                    self.assertTrue((ROOT / "assets/pawns/monstros" / key / f"{key}.png").is_file())

    def test_all_twelve_matching_glb_files_exist(self):
        for _weapon, *keys in VARIANTS:
            for key in keys:
                with self.subTest(key=key):
                    self.assertTrue((ROOT / "assets/models3d/monstros" / f"{key}.glb").is_file())

    def test_goblin_dual_and_legacy_combatant_keep_existing_resolution(self):
        definition = next(d for d in S.MONSTER_DEFS if d["type"] == "goblin_dual")
        dual = S.make_monster(definition, {"id": 0, "cx": 3, "cy": 3})
        self.assertEqual(dual["image"], "goblinDual")
        self.assertNotIn("combatant_weapon_id", dual)
        self.assertNotIn("combatant_shield_id", dual)
        resolved = client_resolve([dual, {"type": "goblin_combatente", "image": "goblinCombatente"}])
        for key, result in zip(("goblinDual", "goblinCombatente"), resolved):
            with self.subTest(key=key):
                self.assertEqual(result["image"], key)
                self.assertEqual(result["png"], f"assets/pawns/monstros/{key}/{key}.png")
                self.assertEqual(result["glb"], "assets/models3d/monstros/goblin_combatente.glb")

    def test_new_variants_keep_the_legacy_combatant_facing(self):
        monsters = [{"type": "goblin_combatente", "image": key}
                    for _weapon, *keys in VARIANTS for key in keys]
        monsters.append({"type": "goblin_combatente", "image": "goblinCombatente"})
        resolved = client_resolve(monsters)
        for monster, result in zip(monsters[:-1], resolved[:-1]):
            with self.subTest(key=monster["image"]):
                self.assertEqual(result["facing"], resolved[-1]["facing"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
