"""Colorize both sides of the Bardo miniature from matching front/back art.

The Downloads GLB is a single unpainted mesh. Its front and rear polygons use
separate projections into a packed texture atlas, so the front painting is not
duplicated across the back of the character.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def _look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _bounds(meshes):
    points = [obj.matrix_world @ Vector(corner)
              for obj in meshes for corner in obj.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def _read_cutout(path: Path):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    rgba = pixels.reshape((height, width, 4))
    ys, xs = np.where(rgba[:, :, 3] > 0.25)
    if not len(xs):
        raise RuntimeError(f"A referência não contém pixels opacos: {path}")
    pad = 1
    bounds = (
        max(int(xs.min()) - pad, 0), min(int(xs.max()) + 1 + pad, width),
        max(int(ys.min()) - pad, 0), min(int(ys.max()) + 1 + pad, height),
    )
    return image, rgba, bounds


def _make_texture_atlas(front_path: Path, back_path: Path, output: Path):
    front, front_rgba, front_bounds = _read_cutout(front_path)
    back, back_rgba, back_bounds = _read_cutout(back_path)
    if tuple(front.size) != tuple(back.size):
        raise RuntimeError(
            f"As pinturas frontal e traseira precisam ter o mesmo tamanho: {front.size} / {back.size}"
        )
    width, height = tuple(front.size)
    fallback = np.array([0.020, 0.014, 0.010], dtype=np.float32)
    atlas = np.zeros((height, width * 2, 4), dtype=np.float32)
    for x_offset, rgba in ((0, front_rgba), (width, back_rgba)):
        alpha = rgba[:, :, 3:4]
        atlas[:, x_offset:x_offset + width, :3] = (
            rgba[:, :, :3] * alpha + fallback * (1.0 - alpha)
        )
        atlas[:, x_offset:x_offset + width, 3] = 1.0

    packed = bpy.data.images.new("Bardo frente e costas", width=width * 2,
                                 height=height, alpha=False, float_buffer=False)
    packed.pixels.foreach_set(atlas.reshape(-1))
    packed.file_format = "PNG"
    packed.filepath_raw = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    packed.save()
    packed.pack()
    bpy.data.images.remove(front)
    bpy.data.images.remove(back)
    return packed, front_bounds, back_bounds, (width, height)


def _project_uv(meshes, front_bounds, back_bounds, source_size,
                uv_name="BardoFrontBackProjection"):
    points = [(obj, obj.matrix_world @ vertex.co)
              for obj in meshes for vertex in obj.data.vertices]
    x_min = min(point.x for _, point in points)
    x_max = max(point.x for _, point in points)
    z_min = min(point.z for _, point in points)
    z_max = max(point.z for _, point in points)
    x_span, z_span = max(x_max - x_min, 1e-8), max(z_max - z_min, 1e-8)
    width, height = source_size

    for obj in meshes:
        mesh = obj.data
        layer = mesh.uv_layers.get(uv_name) or mesh.uv_layers.new(name=uv_name)
        for polygon in mesh.polygons:
            centroid = sum(
                (obj.matrix_world @ mesh.vertices[i].co for i in polygon.vertices), Vector()
            ) / len(polygon.vertices)
            # The model is a closed mesh, but some imported facets have
            # inconsistent winding. Classify by depth so rear facets always
            # receive the rear artwork, even when their normals are flipped.
            back_view = centroid.y > 0
            bounds = back_bounds if back_view else front_bounds
            x0, x1, y0, y1 = bounds
            for loop_index in polygon.loop_indices:
                point = obj.matrix_world @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
                x = min(max((point.x - x_min) / x_span, 0.0), 1.0)
                z = min(max((point.z - z_min) / z_span, 0.0), 1.0)
                if back_view:
                    # A rear-facing camera sees the model's X axis mirrored.
                    x = 1.0 - x
                    u = (width + x0 + x * (x1 - x0)) / (width * 2)
                else:
                    u = (x0 + x * (x1 - x0)) / (width * 2)
                v = (y0 + z * (y1 - y0)) / height
                layer.data[loop_index].uv = (float(u), float(v))
    return layer


def _material(image):
    mat = bpy.data.materials.new("Bardo • frente e costas")
    mat.use_nodes = True
    mat.diffuse_color = (0.20, 0.13, 0.08, 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.86
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Pintura frontal e traseira do Bardo"
    tex.label = "bardo.png + bardo_costas.png"
    tex.image = image
    tex.interpolation = "Linear"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _preview(meshes, output: Path, side: str):
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    direction = -1 if side == "front" else 1
    bpy.ops.object.camera_add(location=center + Vector((0.35, direction * 5.0, 1.05)))
    camera = bpy.context.object
    _look_at(camera, center + Vector((0, 0, (hi.z - lo.z) * 0.02)))
    camera.data.lens = 54
    bpy.context.scene.camera = camera

    lights = [
        (center + Vector((0.8, direction * 3.0, 3.3)), 260, 2.3),
        (center + Vector((-1.8, direction * 2.4, 1.7)), 150, 2.0),
        (center + Vector((0.5, -direction * 1.6, 2.7)), 180, 1.8),
    ]
    for loc, energy, size in lights:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        _look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new(f"Bardo preview {side}")
    scene.world.color = (0.012, 0.010, 0.009)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--back-reference", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--out-texture", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--back-preview", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(cli)
    for path in (args.input, args.reference, args.back_reference):
        if not path.is_file():
            raise FileNotFoundError(path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.input))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB de origem não contém malha")
    before = [(len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]

    image, front_bounds, back_bounds, source_size = _make_texture_atlas(
        args.reference, args.back_reference, args.out_texture)
    _project_uv(meshes, front_bounds, back_bounds, source_size)
    material = _material(image)
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj["palette_reference_front"] = str(args.reference)
        obj["palette_reference_back"] = str(args.back_reference)
        obj["source_glb_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()

    after = [(len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]
    if before != after:
        raise RuntimeError(f"A geometria mudou durante a colorização: {before} -> {after}")

    args.out_blend.parent.mkdir(parents=True, exist_ok=True)
    args.out_glb.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out_blend))
    bpy.ops.export_scene.gltf(
        filepath=str(args.out_glb), export_format="GLB", export_materials="EXPORT",
        export_apply=False, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )
    _preview(meshes, args.preview, "front")
    _preview(meshes, args.back_preview, "back")
    print("source", args.input)
    print("source_sha256", hashlib.sha256(args.input.read_bytes()).hexdigest())
    print("geometry", before)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_texture", args.out_texture)
    print("saved_preview", args.preview)
    print("saved_back_preview", args.back_preview)


if __name__ == "__main__":
    main()
