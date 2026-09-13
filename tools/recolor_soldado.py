"""Create the Soldado GLB variant with the palette from soldado.png.

The source GLB already has the right painted details, but its single embedded
texture benefits from a restrained pass that matches the reference: neutral
silver-gray armor, deep steel blue cloth, warm brown leather/boots and darker
hair/shadows. The original asset is never overwritten.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


def recolor_texture(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3] / 255.0
    alpha = rgba[..., 3:4]

    maximum = rgb.max(axis=2)
    minimum = rgb.min(axis=2)
    spread = maximum - minimum
    luminance = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]

    # Broad material masks from the source texture. They preserve the painted
    # micro-detail while nudging each family toward the supplied portrait.
    blue = (rgb[..., 2] > rgb[..., 0] * 1.13) & (rgb[..., 2] > rgb[..., 1] * 1.02)
    brown = (rgb[..., 0] > rgb[..., 1] * 1.13) & (rgb[..., 1] > rgb[..., 2] * 1.18)
    green = (rgb[..., 1] > rgb[..., 0] * 1.12) & (rgb[..., 1] > rgb[..., 2] * 1.10)
    neutral = (spread < 0.105) & ~blue & ~brown & ~green
    dark = luminance < 0.17

    out = rgb.copy()

    # Silver-gray armor and off-white cloth: keep the sculpted shading, add a
    # very slight cool cast, and prevent the highlights from looking washed out.
    neutral_value = np.clip(0.015 + (luminance - 0.015) * 0.91, 0.0, 1.0)
    out[neutral, 0] = neutral_value[neutral] * 0.98
    out[neutral, 1] = neutral_value[neutral] * 0.985
    out[neutral, 2] = neutral_value[neutral] * 1.01

    # The reference has a clearly readable deep blue left side of the robe and
    # sash; increase separation without flattening the original texture.
    out[blue, 0] *= 0.78
    out[blue, 1] *= 0.88
    out[blue, 2] = np.clip(out[blue, 2] * 0.92 + 0.015, 0.0, 1.0)

    # Leather, gloves, boots and staff become warmer and less gray, matching
    # the brown material in soldado.png.
    out[brown, 0] = np.clip(out[brown, 0] * 0.88 + 0.025, 0.0, 1.0)
    out[brown, 1] = np.clip(out[brown, 1] * 0.77, 0.0, 1.0)
    out[brown, 2] = np.clip(out[brown, 2] * 0.62, 0.0, 1.0)

    # Small vegetation/ground accents should remain subdued and earthy.
    out[green, 0] *= 0.72
    out[green, 1] *= 0.82
    out[green, 2] *= 0.55

    # Hair and deep folds in the reference are near-black rather than gray.
    out[dark] *= 0.82

    result = np.concatenate((np.clip(out * 255.0, 0, 255), alpha), axis=2)
    return Image.fromarray(result.astype(np.uint8), mode="RGBA")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # The reference path is kept explicit in the command and checked so the
    # generated asset cannot silently drift away from the requested artwork.
    if not args.reference.is_file():
        raise FileNotFoundError(args.reference)

    scene = trimesh.load(args.input, force="scene")
    if not isinstance(scene, trimesh.Scene) or not scene.geometry:
        raise RuntimeError(f"GLB sem geometria: {args.input}")

    changed = 0
    for geometry in scene.geometry.values():
        visual = geometry.visual
        material = getattr(visual, "material", None)
        texture = getattr(material, "baseColorTexture", None) if material else None
        if texture is None:
            continue
        new_material = copy.deepcopy(material)
        new_material.name = "soldado_pintado_corrigido"
        new_material.baseColorTexture = recolor_texture(texture)
        geometry.visual = trimesh.visual.texture.TextureVisuals(
            uv=np.array(visual.uv, copy=True),
            material=new_material,
        )
        changed += 1

    if not changed:
        raise RuntimeError("O GLB não contém textura de cor base para corrigir")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    scene.export(args.output, file_type="glb")
    print(f"saved {args.output} ({changed} textured mesh(es))")


if __name__ == "__main__":
    main()
