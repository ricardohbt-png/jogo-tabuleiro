"""Cria variantes coloridas do Lorde e do Vampiro Ancião.

Rode com o Blender, na raiz do projeto:
  blender --background --python tools/create_lorde_vampiro_glb.py -- \
    --input assets/models3d/monstros/mestre_vampiro.glb \
    --output assets/models3d/monstros/lorde_vampiro.glb
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy


# Paleta da arte lorde_vampiro.png: sobretudo preto-azulado, vinho por dentro,
# ornamentos envelhecidos e piso de cripta quase preto.
PALETTE = {
    "pele": ((0.30, 0.285, 0.27), 0.0, 0.90),
    "cabelo": ((0.014, 0.012, 0.014), 0.0, 0.94),
    "sobretudo": ((0.017, 0.024, 0.035), 0.0, 0.93),
    "forro_vinho": ((0.060, 0.006, 0.012), 0.0, 0.95),
    "colete": ((0.027, 0.019, 0.018), 0.0, 0.91),
    "camisa": ((0.235, 0.210, 0.175), 0.0, 0.90),
    "ouro_antigo": ((0.22, 0.125, 0.035), 0.68, 0.48),
    "calca": ((0.016, 0.015, 0.017), 0.0, 0.96),
    "botas": ((0.023, 0.016, 0.012), 0.0, 0.92),
    "aco": ((0.10, 0.11, 0.12), 0.72, 0.58),
    "pedra": ((0.052, 0.047, 0.038), 0.0, 0.97),
    "base": ((0.010, 0.010, 0.012), 0.0, 0.96),
}

# O Ancião da arte mestre_vampiro.png é mais austero: sobretudo quase preto,
# dourado mais evidente nas bordas e camisa de linho pálida sob o colete vinho.
PALETTE_ANCIAO = {
    **PALETTE,
    "pele": ((0.32, 0.295, 0.275), 0.0, 0.90),
    "cabelo": ((0.012, 0.011, 0.013), 0.0, 0.94),
    "sobretudo": ((0.012, 0.017, 0.024), 0.0, 0.94),
    "forro_vinho": ((0.080, 0.008, 0.015), 0.0, 0.94),
    "colete": ((0.055, 0.012, 0.019), 0.0, 0.90),
    "camisa": ((0.285, 0.255, 0.210), 0.0, 0.90),
    "ouro_antigo": ((0.265, 0.150, 0.040), 0.72, 0.43),
    "aco": ((0.115, 0.125, 0.135), 0.75, 0.54),
    "pedra": ((0.060, 0.052, 0.042), 0.0, 0.97),
}


def material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def patch_noise(x, y, z):
    # Pequenas variações agrupadas para impedir que o sobretudo fique chapado.
    return (round(x * 8) * 17 + round(y * 8) * 29 + round(z * 8) * 43) % 13


def role(center):
    x, y, z = center
    radius = (x * x + y * y) ** 0.5

    if z < -0.90 and radius > 0.35:
        return "base"
    if z < -0.72:
        return "pedra"
    # A espada projetada para o lado esquerdo do modelo e os detalhes metálicos.
    if x < -0.57 and z < 0.18:
        return "aco"
    if -0.71 < z < -0.38 and abs(x) < 0.53:
        return "botas"
    if z > 0.78:
        return "cabelo"
    if z > 0.62 and abs(x) < 0.24 and y < -0.08:
        return "pele"
    # Mãos estendidas (a manga fica entre elas e o torso).
    if 0.03 < z < 0.48 and ((x > 0.54 and y < 0.18) or (x < -0.54 and y < 0.02)):
        return "pele"
    if -0.62 < z < 0.08 and abs(x) < 0.47:
        return "calca"
    # Botões, bordas frontais e ombreiras recebem o dourado do figurino.
    trim = (
        (-0.50 < z < 0.62 and y < -0.08 and 0.23 < abs(x) < 0.30)
        or (0.37 < z < 0.70 and 0.26 < abs(x) < 0.62 and y < 0.08)
        or (-0.48 < z < -0.18 and 0.27 < abs(x) < 0.47 and y < -0.05)
    )
    if trim and patch_noise(x, y, z) < 8:
        return "ouro_antigo"
    if 0.34 < z < 0.62 and abs(x) < 0.20 and y < -0.12:
        return "camisa"
    if 0.02 < z < 0.60 and abs(x) < 0.35 and y < -0.12:
        return "colete"
    # O forro só aparece nas dobras internas traseiras da capa.
    if y > 0.08 and -0.56 < z < 0.56 and (abs(x) > 0.26 or patch_noise(x, y, z) < 3):
        return "forro_vinho"
    return "sobretudo"


def main():
    cli = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("lorde", "anciao"), default="lorde")
    args = parser.parse_args(cli)
    if not args.input.is_file():
        raise FileNotFoundError(args.input)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.input))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB de origem não contém malha")

    palette = PALETTE_ANCIAO if args.variant == "anciao" else PALETTE
    materials = {name: material(name, *values) for name, values in palette.items()}
    names = list(palette)
    slots = {name: index for index, name in enumerate(names)}
    for obj in meshes:
        obj.data.materials.clear()
        for name in names:
            obj.data.materials.append(materials[name])
        for poly in obj.data.polygons:
            center = obj.matrix_world @ poly.center
            poly.material_index = slots[role(center)]
            poly.use_smooth = role(center) not in {"pedra", "base"}
        if args.variant == "anciao":
            obj["palette_reference"] = "assets/pawns/monstros/mestre_vampiro/mestre_vampiro.png"
            obj["palette_adjustment"] = "near-black coat, burgundy lining and vest, bright antique gold trim, charcoal crypt stone"
        else:
            obj["palette_reference"] = "assets/pawns/monstros/lorde_vampiro/lorde_vampiro.png"
            obj["palette_adjustment"] = "black-blue coat, dried wine lining, antique gold trim, charcoal crypt stone"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(args.output), export_format="GLB", export_materials="EXPORT",
        export_apply=True, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )
    print(f"saved {args.output} (materials={len(materials)})")


if __name__ == "__main__":
    main()
