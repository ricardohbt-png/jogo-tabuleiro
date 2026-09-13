"""Create the dark-mage variant from the necromancer miniature."""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "manto": ((0.012, 0.005, 0.018), 0.0, 0.82),
    "pele": ((0.065, 0.028, 0.014), 0.0, 0.74),
    "osso": ((0.17, 0.095, 0.032), 0.0, 0.62),
    "madeira": ((0.070, 0.025, 0.008), 0.0, 0.70),
    "verde": ((0.006, 0.090, 0.018), 0.0, 0.58),
    "terra": ((0.016, 0.008, 0.004), 0.0, 0.88),
    "disco": ((0.008, 0.008, 0.011), 0.0, 0.86),
}


def load(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    return max(meshes, key=lambda obj: len(obj.data.polygons))


def set_material(mat, color, metallic, roughness):
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        return
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    # A restrained green magical accent is reserved for the existing `verde`
    # material and remains compatible with Three.js MeshStandardMaterial.
    if mat.name == "verde":
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.002, 0.022, 0.004, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = 0.35


def recolor(obj):
    changed = []
    for mat in obj.data.materials:
        if mat is None or mat.name not in PALETTE:
            continue
        set_material(mat, *PALETTE[mat.name])
        changed.append(mat.name)
    missing = sorted(set(PALETTE) - set(changed))
    if missing:
        raise RuntimeError("Materiais ausentes no necromante.glb: " + ", ".join(missing))
    return changed


def rotate_for_movement(obj):
    # Blender Z is the vertical axis; glTF/Three.js receives this as its
    # vertical Y.  The -90 degree asset turn cancels the old generic runtime
    # offset while keeping the original necromancer untouched.
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, -math.pi / 2)
    obj["asset_name"] = "mago_das_trevas"
    obj["orientation_adjustment"] = "-90 degrees around vertical axis; faces movement after runtime offset"
    obj["palette_reference"] = "assets/pawns/monstros/necromante/necromante.png"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def preview(path: Path):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (mn + mx) * 0.5
    h = mx.z - mn.z
    # The model's -90 degree correction turns its face toward -X in the
    # authoring preview, so look from that side to show the corrected front.
    bpy.ops.object.camera_add(location=(-h * 3.3, 0.0, center.z + h * .82))
    cam = bpy.context.object
    look_at(cam, (center.x, center.y, center.z + h * .43))
    cam.data.lens = 58
    bpy.context.scene.camera = cam
    for loc, energy, size in [
        ((-h * 2.6, -h * 1.7, center.z + h * 2.8), 850, h * 1.8),
        ((h * 1.7, -h * .7, center.z + h * 1.4), 320, h * 1.5),
        ((-h * .8, h * 2.0, center.z + h * 1.8), 450, h * 1.6),
    ]:
        bpy.ops.object.light_add(type="AREA", location=loc)
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
    scene.render.filepath = str(path)
    scene.world = bpy.data.worlds.new("Dark mage preview world")
    scene.world.color = (0.002, 0.002, 0.004)
    scene.view_settings.look = "AgX - Medium High Contrast"
    path.parent.mkdir(parents=True, exist_ok=True)
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
