"""Create the movement-aligned and recolored Medusa GLB."""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "pele": ((0.105, 0.115, 0.065), 0.0, 0.74),
    "cobra": ((0.014, 0.032, 0.010), 0.0, 0.76),
    "cobra_esc": ((0.010, 0.021, 0.007), 0.0, 0.80),
    "pano": ((0.034, 0.012, 0.045), 0.0, 0.82),
    "bronze": ((0.11, 0.055, 0.018), 0.58, 0.48),
    "pedra": ((0.10, 0.085, 0.060), 0.0, 0.88),
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
    for mat in obj.data.materials:
        if mat is None or mat.name not in PALETTE:
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
    missing = sorted(set(PALETTE) - set(changed))
    if missing:
        raise RuntimeError("Materiais ausentes no medusa.glb: " + ", ".join(missing))
    obj["asset_name"] = "medusa_corrigida"
    obj["palette_reference"] = "assets/pawns/monstros/medusa/medusa.png"
    obj["orientation_adjustment"] = "-90 degrees around vertical axis; faces movement after runtime offset"
    return changed


def rotate_for_movement(obj):
    # Imported GLBs use quaternion rotation mode; explicitly switch to Euler so
    # the 90-degree correction is actually baked into the exported geometry.
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, -math.pi / 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def preview(output: Path):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (mn + mx) * 0.5
    h = mx.z - mn.z
    bpy.ops.object.camera_add(location=(-h * 3.2, 0.0, center.z + h * .80))
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + h * .43))
    camera.data.lens = 58
    bpy.context.scene.camera = camera
    for location, energy, size in [
        ((-h * 2.4, -h * 1.6, center.z + h * 2.8), 850, h * 1.8),
        ((h * 1.8, -h * .8, center.z + h * 1.4), 340, h * 1.5),
        ((-h * .8, h * 2.0, center.z + h * 1.8), 450, h * 1.6),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + h * .42))
    bpy.ops.mesh.primitive_plane_add(size=h * 8, location=(center.x, center.y, mn.z - h * .03))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Preview floor")
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.008, 0.008, 0.011, 1.0)
    floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    floor.data.materials.append(floor_mat)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Medusa preview world")
    scene.world.color = (0.002, 0.002, 0.004)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def save(blend_path: Path, glb_path: Path):
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", export_materials="EXPORT", export_apply=True, export_texcoords=True, export_normals=True, export_tangents=False, export_cameras=False, export_lights=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(cli)
    obj = load(args.input)
    print("materials_changed", recolor(obj))
    rotate_for_movement(obj)
    save(args.out_blend, args.out_glb)
    preview(args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
