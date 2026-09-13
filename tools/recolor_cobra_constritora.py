"""Recolor the constrictor-snake miniature to match its painted reference."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    # Olive-brown scales and muted golden highlights from the reference.
    "Cobra_escamas_oliva": ((0.100, 0.060, 0.020), 0.0, 0.88),
    "Cobra_escamas_dourada": ((0.220, 0.100, 0.025), 0.0, 0.84),
    "Cobra_manchas_pretas": ((0.003, 0.002, 0.001), 0.0, 0.92),
    "Cobra_barriga_oliva": ((0.120, 0.070, 0.025), 0.0, 0.88),
    # Mouth, tongue, teeth and amber eyes.
    "Cobra_boca": ((0.030, 0.002, 0.002), 0.0, 0.80),
    "Cobra_lingua": ((0.120, 0.004, 0.008), 0.0, 0.70),
    "Cobra_dentes": ((0.250, 0.150, 0.050), 0.0, 0.76),
    "Cobra_olhos_ambar": ((0.300, 0.070, 0.002), 0.0, 0.55),
    # Dark swamp base and subdued moss.
    "Cobra_base_pantano": ((0.006, 0.005, 0.003), 0.0, 0.97),
    "Cobra_musgo": ((0.030, 0.040, 0.008), 0.0, 0.97),
}


def load(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    return meshes


def set_material(mat, color, metallic, roughness):
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    specular = bsdf.inputs.get("Specular IOR Level")
    if specular is not None:
        specular.default_value = 0.24


def recolor(meshes):
    changed = set()
    for obj in meshes:
        for mat in obj.data.materials:
            if mat is None or mat.name not in PALETTE:
                continue
            set_material(mat, *PALETTE[mat.name])
            changed.add(mat.name)

    missing = sorted(set(PALETTE) - changed)
    if missing:
        raise RuntimeError("Materiais esperados ausentes: " + ", ".join(missing))

    for obj in meshes:
        obj["palette_reference"] = (
            "assets/pawns/monstros/cobraConstritora/cobraConstritora.png"
        )
        obj["palette_adjustment"] = (
            "olive-brown scales, aged gold highlights, black markings, amber eyes, swamp base"
        )
    return sorted(changed)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(meshes):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return mn, mx


def save_asset(blend_path: Path, glb_path: Path):
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_materials="EXPORT",
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=False,
        export_cameras=False,
        export_lights=False,
    )


def make_preview(meshes, output: Path):
    mn, mx = bounds(meshes)
    center = (mn + mx) * 0.5
    height = max(mx.z - mn.z, 0.001)

    bpy.ops.object.camera_add(
        location=(height * 2.0, -height * 3.0, center.z + height * 1.05)
    )
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + height * 0.32))
    camera.data.lens = 58
    bpy.context.scene.camera = camera

    for location, energy, size in [
        ((height * 2.0, -height * 3.0, center.z + height * 2.8), 920, height * 1.8),
        ((-height * 2.0, -height * 1.0, center.z + height * 1.2), 330, height * 1.6),
        ((height * 0.4, height * 2.2, center.z + height * 1.8), 460, height * 1.5),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + height * 0.34))

    bpy.ops.mesh.primitive_plane_add(
        size=height * 8.0, location=(center.x, center.y, mn.z - height * 0.035)
    )
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Preview floor")
    floor_mat.use_nodes = True
    floor_bsdf = floor_mat.node_tree.nodes["Principled BSDF"]
    floor_bsdf.inputs["Base Color"].default_value = (0.012, 0.012, 0.015, 1.0)
    floor_bsdf.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Constrictor snake preview world")
    scene.world.color = (0.006, 0.006, 0.008)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    args = parser.parse_args(cli)

    meshes = load(args.input)
    print("materials_changed", recolor(meshes))
    save_asset(args.out_blend, args.out_glb)
    make_preview(meshes, args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
