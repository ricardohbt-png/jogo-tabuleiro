"""Recolor the zombie miniature and split its generic material by body area."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "zumbi_pele": ((0.090, 0.100, 0.082), 0.0, 0.88),
    "zumbi_casaco": ((0.026, 0.036, 0.043), 0.0, 0.92),
    "zumbi_calca": ((0.014, 0.012, 0.011), 0.0, 0.94),
    "zumbi_cabelo": ((0.005, 0.004, 0.003), 0.0, 0.96),
    "zumbi_base": ((0.010, 0.009, 0.008), 0.0, 0.98),
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


def ensure_materials():
    materials = {}
    for name, settings in PALETTE.items():
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        set_material(mat, *settings)
        materials[name] = mat
    return materials


def classify_face(center):
    """Choose a restrained zombie material from the mesh-local face position."""
    x, y, z = center
    side = abs(x)
    radius = (x * x + y * y) ** 0.5

    # The circular plinth occupies the lowest, widest ring of the mesh.
    if z < -0.82 and radius > 0.45:
        return "zumbi_base"

    # The upper cap is hair; the head and exposed extremities are dead skin.
    if z > 0.78:
        return "zumbi_cabelo"
    if z > 0.56:
        return "zumbi_pele"
    if side > 0.50 and z < 0.28:
        return "zumbi_pele"  # exposed forearms and hands
    if z < -0.33:
        return "zumbi_calca"
    return "zumbi_casaco"


def recolor(meshes):
    materials = ensure_materials()
    main = max(meshes, key=lambda obj: len(obj.data.polygons))

    # Replace the single generic material on the main mesh with readable zones.
    for mat in materials.values():
        if main.data.materials.get(mat.name) is None:
            main.data.materials.append(mat)
    slot_by_name = {mat.name: idx for idx, mat in enumerate(main.data.materials)}
    for poly in main.data.polygons:
        poly.material_index = slot_by_name[classify_face(poly.center)]

    # The small cube in the source GLB is the dark plinth/ground element.
    for obj in meshes:
        if obj is main:
            continue
        # Clear the generic imported slot so the exporter cannot retain its
        # original light material on part of the base.
        obj.data.materials.clear()
        obj.data.materials.append(materials["zumbi_base"])
        base_index = 0
        for poly in obj.data.polygons:
            poly.material_index = base_index
        obj["palette_reference"] = "assets/pawns/monstros/zumbi/zumbi.png"
        obj["palette_adjustment"] = "gray-green skin, dark blue-gray coat, black pants and hair"

    main["palette_reference"] = "assets/pawns/monstros/zumbi/zumbi.png"
    main["palette_adjustment"] = "gray-green skin, dark blue-gray coat, black pants and hair"
    return sorted(materials)


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
        location=(height * 2.3, -height * 3.1, center.z + height * 0.88)
    )
    camera = bpy.context.object
    look_at(camera, (center.x, center.y, center.z + height * 0.40))
    camera.data.lens = 58
    bpy.context.scene.camera = camera

    for location, energy, size in [
        ((height * 2.0, -height * 3.0, center.z + height * 2.8), 980, height * 1.8),
        ((-height * 2.0, -height * 1.0, center.z + height * 1.3), 360, height * 1.6),
        ((height * 0.4, height * 2.2, center.z + height * 1.8), 520, height * 1.5),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + height * 0.38))

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
    scene.world = bpy.data.worlds.new("Zombie preview world")
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
    print("materials_created", recolor(meshes))
    save_asset(args.out_blend, args.out_glb)
    make_preview(meshes, args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
