"""Cria uma variante escura do Soldado para o Assassino da Serra.

Preserva malha, UVs e detalhes da textura original; escurece o metal para
grafite/preto e converte os tecidos azuis em marrom profundo. O GLB do Soldado
permanece intacto.
"""
from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/models3d/monstros/soldado.glb"
OUTPUT = ROOT / "assets/models3d/monstros/assassino_da_serra.glb"
ALBEDO = ROOT / "assets/models3d/monstros/assassino_da_serra_albedo.png"


def recolor_texture(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.float32)
    rgb = rgba[..., :3] / 255.0
    alpha = rgba[..., 3:4]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    spread = rgb.max(axis=2) - rgb.min(axis=2)

    blue = (b > r * 1.13) & (b > g * 1.02)
    brown = (r > g * 1.13) & (g > b * 1.18)
    green = (g > r * 1.12) & (g > b * 1.10)
    metal = (spread < 0.105) & ~blue & ~brown & ~green

    out = rgb.copy()

    # A armadura cinza original vira ferro negro, mantendo relevo e brilho.
    dark_metal = np.clip(0.006 + lum * 0.13, 0.0, 0.095)
    out[metal, 0] = dark_metal[metal] * 0.84
    out[metal, 1] = dark_metal[metal] * 0.88
    out[metal, 2] = dark_metal[metal] * 0.98

    # Tecidos azuis passam para marrom escuro, com as sombras originais.
    cloth_value = np.clip(lum * 0.62, 0.0, 0.42)
    out[blue, 0] = cloth_value[blue] * 0.82 + 0.025
    out[blue, 1] = cloth_value[blue] * 0.43 + 0.010
    out[blue, 2] = cloth_value[blue] * 0.22 + 0.006

    # Couro já marrom fica mais escuro e rico, sem perder as variações pintadas.
    out[brown, 0] = np.clip(r[brown] * 0.66 + 0.018, 0.0, 0.42)
    out[brown, 1] = np.clip(g[brown] * 0.48 + 0.008, 0.0, 0.22)
    out[brown, 2] = np.clip(b[brown] * 0.40 + 0.005, 0.0, 0.13)

    # Pequenos detalhes verdes viram couro/tecido marrom discreto.
    earthy = np.clip(lum * 0.35, 0.0, 0.20)
    out[green, 0] = earthy[green] * 0.80 + 0.018
    out[green, 1] = earthy[green] * 0.45 + 0.008
    out[green, 2] = earthy[green] * 0.22 + 0.004

    result = np.concatenate((np.clip(out * 255.0, 0, 255), alpha), axis=2)
    return Image.fromarray(result.astype(np.uint8), mode="RGBA")


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    scene = trimesh.load(SOURCE, force="scene")
    if not isinstance(scene, trimesh.Scene) or not scene.geometry:
        raise RuntimeError(f"GLB sem geometria: {SOURCE}")

    ALBEDO.parent.mkdir(parents=True, exist_ok=True)
    changed = 0
    for geometry in scene.geometry.values():
        visual = geometry.visual
        material = getattr(visual, "material", None)
        texture = getattr(material, "baseColorTexture", None) if material else None
        if texture is None:
            continue
        painted = recolor_texture(texture)
        painted.save(ALBEDO)
        new_material = copy.deepcopy(material)
        new_material.name = "assassino_da_serra_armadura_negra_couro_marrom"
        new_material.baseColorTexture = painted
        geometry.visual = trimesh.visual.texture.TextureVisuals(
            uv=np.array(visual.uv, copy=True), material=new_material
        )
        changed += 1
    if not changed:
        raise RuntimeError("O GLB do Soldado não contém textura de cor base")
    scene.export(OUTPUT, file_type="glb")
    print(f"saved {OUTPUT} ({changed} malha(s) texturizada(s))")
    print(f"saved {ALBEDO}")


if __name__ == "__main__":
    main()
