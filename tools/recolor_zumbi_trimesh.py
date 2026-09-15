"""Create the common Zombie GLB variant from the zumbi.png palette."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh


# Palette matched to the supplied reference: gray-green dead skin, blue-gray
# coat, brown-charcoal trousers, nearly black hair and an earthy plinth.
PALETTE = {
    "zumbi_pele": ((0.30, 0.29, 0.25), 0.0, 0.88),
    "zumbi_casaco": ((0.18, 0.21, 0.23), 0.0, 0.92),
    "zumbi_calca": ((0.12, 0.095, 0.070), 0.0, 0.94),
    "zumbi_cabelo": ((0.06, 0.050, 0.040), 0.0, 0.96),
    "zumbi_base": ((0.12, 0.10, 0.070), 0.0, 0.98),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.reference.is_file():
        raise FileNotFoundError(args.reference)

    scene = trimesh.load(args.input, force="scene")
    if not isinstance(scene, trimesh.Scene) or not scene.geometry:
        raise RuntimeError(f"GLB sem geometria: {args.input}")

    changed = []
    for geometry in scene.geometry.values():
        material = getattr(geometry.visual, "material", None)
        if material is None or material.name not in PALETTE:
            continue
        color, metallic, roughness = PALETTE[material.name]
        material.baseColorFactor = np.array(
            [round(channel * 255) for channel in color] + [255], dtype=np.uint8
        )
        material.metallicFactor = metallic
        material.roughnessFactor = roughness
        changed.append(material.name)

    missing = sorted(set(PALETTE) - set(changed))
    if missing:
        raise RuntimeError("Materiais esperados ausentes: " + ", ".join(missing))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    scene.export(args.output, file_type="glb")
    print(f"saved {args.output} ({len(set(changed))} materials)")


if __name__ == "__main__":
    main()
