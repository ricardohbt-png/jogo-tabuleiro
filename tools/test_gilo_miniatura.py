"""Verificações objetivas do modelo e da calibração 3D de Gilo."""
import json
from pathlib import Path

import trimesh


ROOT = Path(__file__).resolve().parents[1]
MODEL = "assets/models3d/monstros/gilo_dedos_sujos.glb"


def test_gilo_record_and_generator_use_own_model():
    records = json.loads((ROOT / "monstros_personalizados.json").read_text(encoding="utf-8"))
    gilo = [item for item in records if item.get("type") == "gilo_dedos_sujos"]
    assert len(gilo) == 1
    assert gilo[0].get("model3d") == MODEL
    generator = (ROOT / "tools/elara_gilo_ficha.py").read_text(encoding="utf-8")
    assert f'"model3d": "{MODEL}"' in generator


def test_editor_and_runtime_keep_gilo_scale_and_bandit_movement_calibration():
    editor_source = (ROOT / "tools/editor_monsters_custom.js").read_text(encoding="utf-8")
    editor_records = json.loads(editor_source.split("=", 1)[1].rsplit(";", 1)[0].strip())
    gilo = [item for item in editor_records if item.get("type") == "gilo_dedos_sujos"]
    assert len(gilo) == 1 and gilo[0].get("model3d") == MODEL

    game = (ROOT / "game.js").read_text(encoding="utf-8")
    assert f"gilo_dedos_sujos:  '{MODEL}'" in game
    assert "monsterType === 'gilo_dedos_sujos' ? 0.80548125" in game
    assert "'bandido', 'gilo_dedos_sujos', 'goblin_assassino', 'jacare'" in game


def test_gilo_glb_contains_body_and_added_accessory_meshes():
    path = ROOT / MODEL
    assert path.is_file(), f"GLB de Gilo ausente: {path}"
    scene = trimesh.load(path, force="scene")
    assert scene.geometry, "GLB sem geometria"
    assert len(scene.geometry) >= 4, "esperados corpo, duas bestas e chapéu como geometrias 3D"
    assert (ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview.png").is_file()
    assert (ROOT / "assets/models3d/monstros/gilo_dedos_sujos_preview_back.png").is_file()


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    errors = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:
            errors += 1
            print(f"FAIL {test.__name__}: {exc}")
    raise SystemExit(1 if errors else 0)
