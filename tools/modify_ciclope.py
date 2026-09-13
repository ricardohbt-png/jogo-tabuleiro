"""Make a monocular, darker cyclops variant from the existing GLB."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "Ciclope_pele": ((0.095, 0.030, 0.011), 0.0, 0.72),
    "Ciclope_pano": ((0.050, 0.012, 0.005), 0.0, 0.80),
    "Ciclope_vinco": ((0.036, 0.009, 0.004), 0.0, 0.82),
    "Ciclope_clava": ((0.060, 0.052, 0.043), 0.68, 0.48),
}


def material(name, color, metallic=0.0, roughness=0.6):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def load_source(path: Path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém uma malha")
    return max(meshes, key=lambda obj: len(obj.data.polygons))


def recolor_original(obj):
    changed = []
    for mat in obj.data.materials:
        if mat is None or mat.name not in PALETTE:
            continue
        color, metallic, roughness = PALETTE[mat.name]
        material(mat.name, color, metallic, roughness)
        changed.append(mat.name)
    if len(changed) != len(PALETTE):
        missing = sorted(set(PALETTE) - set(changed))
        raise RuntimeError("Materiais do ciclope ausentes: " + ", ".join(missing))
    obj["palette_reference"] = "assets/pawns/monstros/ciclope/ciclope.png"
    obj["geometry_adjustment"] = "single centered monocular eye added to facial plane"
    return changed


def add_monocular_eye():
    # The imported model faces -Y and its eye line is around Z=.76.  The eye
    # is deliberately low-poly to match the faceted source mesh.
    rim = material("Ciclope | contorno do olho", (0.028, 0.008, 0.003), 0.0, 0.72)
    sclera = material("Ciclope | olho envelhecido", (0.16, 0.075, 0.026), 0.0, 0.46)
    iris = material("Ciclope | íris âmbar escura", (0.060, 0.015, 0.004), 0.0, 0.32)
    pupil = material("Ciclope | pupila", (0.003, 0.001, 0.0005), 0.0, 0.25)
    glint = material("Ciclope | brilho do olho", (0.65, 0.46, 0.24), 0.0, 0.2)
    lid = material("Ciclope | pálpebra", (0.066, 0.021, 0.008), 0.0, 0.70)

    # A shallow socket/rim hides the old bilateral eye suggestion and makes
    # the center of the face read as one intentional eye.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(0.0, -0.455, 0.765))
    socket = bpy.context.object
    socket.name = "Ciclope_MonocularSocket"
    socket.scale = (0.105, 0.015, 0.075)
    socket.data.materials.append(rim)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(0.0, -0.474, 0.765))
    white = bpy.context.object
    white.name = "Ciclope_MonocularEye"
    white.scale = (0.078, 0.020, 0.054)
    white.data.materials.append(sclera)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(0.0, -0.495, 0.765))
    iris_obj = bpy.context.object
    iris_obj.name = "Ciclope_MonocularIris"
    iris_obj.scale = (0.033, 0.008, 0.035)
    iris_obj.data.materials.append(iris)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1, location=(0.0, -0.505, 0.765))
    pupil_obj = bpy.context.object
    pupil_obj.name = "Ciclope_MonocularPupil"
    pupil_obj.scale = (0.014, 0.004, 0.020)
    pupil_obj.data.materials.append(pupil)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=5, radius=1, location=(-0.008, -0.513, 0.777))
    highlight = bpy.context.object
    highlight.name = "Ciclope_MonocularEyeHighlight"
    highlight.scale = (0.005, 0.002, 0.007)
    highlight.data.materials.append(glint)

    # Subtle upper and lower lids partially overlap the socket so the eye
    # reads as part of the face, not as a ball attached to it.
    lids = []
    for name, z, sx, sz in [("Ciclope_UpperLid", 0.807, 0.074, 0.012), ("Ciclope_LowerLid", 0.722, 0.066, 0.010)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=1, location=(0.0, -0.486, z))
        part = bpy.context.object
        part.name = name
        part.scale = (sx, 0.012, sz)
        part.data.materials.append(lid)
        lids.append(part)

    for obj in [socket, white, iris_obj, pupil_obj, highlight, *lids]:
        for poly in obj.data.polygons:
            poly.use_smooth = False
    return [socket, white, iris_obj, pupil_obj, highlight]


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def save_outputs(glb_path: Path, blend_path: Path):
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", export_materials="EXPORT", export_apply=True, export_texcoords=True, export_normals=True, export_tangents=False, export_cameras=False, export_lights=False)


def preview(output: Path):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(c) for obj in meshes for c in obj.bound_box]
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (mn + mx) * 0.5
    h = mx.z - mn.z
    bpy.ops.object.camera_add(location=(h * .15, -h * 3.3, center.z + h * .85))
    cam = bpy.context.object
    look_at(cam, (center.x, center.y, center.z + h * .42))
    cam.data.lens = 58
    bpy.context.scene.camera = cam
    for loc, energy, size in [((h * 2, -h * 3, center.z + h * 2.8), 900, h * 1.8), ((-h * 2, -h * 1.4, center.z + h * 1.5), 350, h * 1.6), ((h * .5, h * 2.2, center.z + h * 1.8), 450, h * 1.6)]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        look_at(light, (center.x, center.y, center.z + h * .42))
    bpy.ops.mesh.primitive_plane_add(size=h * 8, location=(center.x, center.y, mn.z - h * .03))
    floor = bpy.context.object
    floor_mat = material("Preview floor", (0.012, 0.012, 0.016), 0.0, 0.9)
    floor.data.materials.append(floor_mat)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 850
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Ciclope preview world")
    scene.world.color = (0.004, 0.004, 0.006)
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
    obj = load_source(args.input)
    changed = recolor_original(obj)
    eye_parts = add_monocular_eye()
    print("materials_changed", changed)
    print("monocular_eye_parts", [part.name for part in eye_parts])
    save_outputs(args.out_glb, args.out_blend)
    preview(args.preview)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
