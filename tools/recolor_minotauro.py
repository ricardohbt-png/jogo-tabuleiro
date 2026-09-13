"""Darken the minotaur GLB to match the supplied painted thumbnail."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    # deep brown-grey fur and face
    "pele": ((0.068, 0.031, 0.013), 0.0, 0.72),
    "cabeca": ((0.048, 0.020, 0.008), 0.0, 0.68),
    # warm, aged horn rather than ivory-white
    "chifre": ((0.19, 0.12, 0.050), 0.0, 0.52),
    # dark iron/steel with restrained reflectivity
    "lamina": ((0.060, 0.063, 0.060), 0.78, 0.42),
    "ombreira": ((0.052, 0.049, 0.044), 0.66, 0.48),
    # leather, wood and skirt
    "couro": ((0.045, 0.020, 0.009), 0.0, 0.78),
    "cabo": ((0.085, 0.040, 0.014), 0.0, 0.66),
    "saiote": ((0.060, 0.014, 0.006), 0.0, 0.76),
    "casco": ((0.022, 0.012, 0.007), 0.0, 0.82),
    # stone base and black plinth
    "pedra": ((0.048, 0.043, 0.036), 0.0, 0.88),
    "plinto": ((0.014, 0.014, 0.013), 0.0, 0.82),
}


def load(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    return max(meshes, key=lambda obj: len(obj.data.polygons))


def recolor(obj):
    changed = []
    missing = []
    for mat in obj.data.materials:
        if mat is None:
            continue
        if mat.name not in PALETTE:
            continue
        color, metallic, roughness = PALETTE[mat.name]
        mat.diffuse_color = (*color, 1.0)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*color, 1.0)
            bsdf.inputs["Metallic"].default_value = metallic
            bsdf.inputs["Roughness"].default_value = roughness
        changed.append(mat.name)
    for name in PALETTE:
        if name not in changed:
            missing.append(name)
    if missing:
        raise RuntimeError("Materiais esperados ausentes: " + ", ".join(missing))
    obj["palette_reference"] = "assets/pawns/monstros/minotauro/minotauro.png"
    obj["palette_adjustment"] = "dark brown-grey fur, aged horns, dark steel, dark leather"
    return changed


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def save_blend_and_glb(obj, blend_path: Path, glb_path: Path):
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


def make_preview(obj, output: Path):
    bounds = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_v = Vector((min(v.x for v in bounds), min(v.y for v in bounds), min(v.z for v in bounds)))
    max_v = Vector((max(v.x for v in bounds), max(v.y for v in bounds), max(v.z for v in bounds)))
    center = (min_v + max_v) * 0.5
    height = max_v.z - min_v.z
    bpy.ops.object.camera_add(location=(height * 2.1, -height * 3.0, center.z + height * 1.05))
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + height * 0.42))
    camera.data.lens = 58
    bpy.context.scene.camera = camera

    for location, energy, size in [
        ((height * 2.0, -height * 3.0, center.z + height * 3.0), 1050, height * 1.7),
        ((-height * 2.0, -height * 1.2, center.z + height * 1.3), 500, height * 1.5),
        ((height * 0.5, height * 2.4, center.z + height * 1.8), 650, height * 1.4),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + height * 0.45))

    floor_z = min_v.z - height * 0.035
    bpy.ops.mesh.primitive_plane_add(size=height * 8.0, location=(center.x, center.y, floor_z))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Preview floor")
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.018, 0.018, 0.022, 1.0)
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    floor.data.materials.append(floor_mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Minotaur preview world")
    scene.world.color = (0.008, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(cli)
    obj = load(args.input)
    changed = recolor(obj)
    print("materials_changed", changed)
    save_blend_and_glb(obj, args.out_blend, args.out_glb)
    make_preview(obj, args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
