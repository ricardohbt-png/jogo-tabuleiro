"""Cria uma variante verde e ouro do Bardo da Caravana sem alterar o Bardo base."""
from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MONSTERS = ROOT / "assets/models3d/monstros"
SOURCE = MONSTERS / "bardo.glb"
OUTPUT = MONSTERS / "bardo_da_caravana.glb"
ALBEDO = MONSTERS / "bardo_da_caravana_albedo.png"


def recolor_texture(image: Image.Image) -> Image.Image:
    """Muda somente os tecidos vermelhos para uma gama de verde musgo a ouro."""
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    hsv = np.array(
        Image.fromarray(rgba, mode="RGBA").convert("RGB").convert("HSV"),
        dtype=np.uint8,
        copy=True,
    )
    h = hsv[..., 0].astype(np.float32)
    s = hsv[..., 1].astype(np.float32) / 255.0
    v = hsv[..., 2].astype(np.float32) / 255.0

    # Vermelho/carmim saturado: tecidos do manto, echarpe e faixas. Exclui
    # tons quentes de pele e couro, que ficam fora deste intervalo estreito.
    height, width = h.shape
    yy, xx = np.mgrid[:height, :width]

    def ellipse(cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
        return (((xx / width - cx) / rx) ** 2 + ((yy / height - cy) / ry) ** 2) <= 1.0

    # O atlas contém duas vistas completas. Exclui rosto, mãos e alaúde para
    # que a seleção vermelha altere tecido e fitas sem tingir pele ou madeira.
    skin_and_instrument = (
        ellipse(0.265, 0.115, 0.052, 0.078)
        | ellipse(0.36, 0.34, 0.105, 0.10)
        | ellipse(0.12, 0.47, 0.035, 0.06)
        | ellipse(0.63, 0.43, 0.035, 0.055)
        | ellipse(0.90, 0.43, 0.035, 0.055)
    )
    red_cloth = (((h <= 12) | (h >= 246)) & (s >= 0.34) & (v >= 0.09) & ~skin_and_instrument)

    # A matiz uniforme mantém o pano verde sem colorir pele nem transformar
    # cada realce em manchas amarelas; os bordados dourados originais ficam.
    hsv[..., 0][red_cloth] = 75
    hsv[..., 1][red_cloth] = np.rint(hsv[..., 1][red_cloth] * 0.68).astype(np.uint8)
    hsv[..., 2][red_cloth] = np.rint(hsv[..., 2][red_cloth] * 0.65).astype(np.uint8)

    recolored = np.asarray(Image.fromarray(hsv, mode="HSV").convert("RGB"), dtype=np.uint8)
    rgba[..., :3] = recolored
    return Image.fromarray(rgba, mode="RGBA")


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
        new_material.name = "bardo_caravana_verde_musgo_e_ouro"
        new_material.baseColorTexture = painted
        geometry.visual = trimesh.visual.texture.TextureVisuals(
            uv=np.array(visual.uv, copy=True), material=new_material
        )
        changed += 1
    if not changed:
        raise RuntimeError("O GLB do Bardo não contém textura de cor base")
    scene.export(OUTPUT, file_type="glb")
    print(f"saved {OUTPUT} ({changed} malha(s) texturizada(s))")
    print(f"saved {ALBEDO}")


if __name__ == "__main__":
    main()
