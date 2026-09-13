"""Create the common Zombie GLB variant from the zumbi.png palette."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import trimesh


# Palette sampled by material family from the supplied reference: gray-green
# dead skin, blue-gray coat, brown-charcoal trousers and nearly black hair.
PALETTE = {
    "zumbi_pele": ((0.18, 0.19, 0.16), 0.0, 0.88),
    "zumbi_casaco": ((0.065, 0.085, 0.095), 0.0, 0.92),
    "zumbi_calca": ((0.040, 0.032, 0.026), 0.0, 0.94),
    "zumbi_cabelo": ((0.010, 0.008, 0.006), 0.0, 0.96),
    "zumbi_base": ((0.025, 0.021, 0.016), 0.0, 0.98),
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
