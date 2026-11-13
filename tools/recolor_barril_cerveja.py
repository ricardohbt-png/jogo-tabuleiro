"""Colorize the dungeon beer barrel GLB from its in-game cutout reference."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def _bounds(meshes):
    points = [obj.matrix_world @ Vector(corner)
              for obj in meshes for corner in obj.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def _make_opaque_reference(path: Path, output: Path):
    source = bpy.data.images.load(str(path), check_existing=False)
    width, height = source.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    source.pixels.foreach_get(pixels)
    rgba = pixels.reshape((height, width, 4))
    alpha = rgba[:, :, 3:4]
    ys, xs = np.where(alpha[:, :, 0] > 0.05)
    if not len(xs):
        raise RuntimeError("A imagem de referência não contém pixels opacos")
    pad = 1
    bounds = (
        max(int(xs.min()) - pad, 0), min(int(xs.max()) + 1 + pad, width),
        max(int(ys.min()) - pad, 0), min(int(ys.max()) + 1 + pad, height),
    )
    # Keep projected samples on the barrel dark and wooden when they land
    # outside the transparent cutout (not transparent or black in-game).
    fallback = np.array([0.018, 0.008, 0.003], dtype=np.float32)
    rgb = rgba[:, :, :3] * alpha + fallback * (1.0 - alpha)

    image = bpy.data.images.new("Barril de cerveja - projeção", width=width,
                                height=height, alpha=False, float_buffer=False)
    opaque = np.concatenate((rgb, np.ones((height, width, 1), dtype=np.float32)), axis=2)
    image.pixels.foreach_set(opaque.reshape(-1))
    image.file_format = "PNG"
    image.filepath_raw = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save()
    image.pack()
    bpy.data.images.remove(source)
    return image, bounds


def _project_uv(meshes, camera_location: Vector, center: Vector,
                image: bpy.types.Image, bounds):
    rotation = (center - camera_location).to_track_quat("-Z", "Y")
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))
    projected = []
    for obj in meshes:
        projected.extend((obj.matrix_world @ vertex.co) for vertex in obj.data.vertices)
    x_values = [point.dot(right) for point in projected]
    y_values = [point.dot(up) for point in projected]
    x_min, x_max = min(x_values), max(x_values)
    y_min, y_max = min(y_values), max(y_values)
    x_span, y_span = max(x_max - x_min, 1e-8), max(y_max - y_min, 1e-8)

    width, height = image.size
    x0, x1, y0, y1 = bounds
    u_min, u_max = x0 / width, x1 / width
    v_min, v_max = y0 / height, y1 / height

    for obj in meshes:
        mesh = obj.data
        layer = mesh.uv_layers.get("BarrilProjection") or mesh.uv_layers.new(name="BarrilProjection")
        for loop in mesh.loops:
            point = obj.matrix_world @ mesh.vertices[loop.vertex_index].co
            u = u_min + ((point.dot(right) - x_min) / x_span) * (u_max - u_min)
            v = v_min + ((point.dot(up) - y_min) / y_span) * (v_max - v_min)
            layer.data[loop.index].uv = (float(u), float(v))


def _material(image):
    material = bpy.data.materials.new("Barril de cerveja - madeira da referência")
    material.use_nodes = True
    material.diffuse_color = (0.12, 0.055, 0.022, 1.0)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.88
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Cores de barril_de_cerveja.png"
    texture.label = "assets/itens/barril_de_cerveja.png"
    texture.image = image
    texture.interpolation = "Linear"
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    return material


def _look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _preview(meshes, output: Path):
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    size = max((hi - lo).length, 0.01)
    camera_location = center + Vector((size * 1.20, -size * 2.00, size * 0.96))
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.object
    _look_at(camera, center)
    camera.data.lens = 52
    bpy.context.scene.camera = camera

    for location, energy, area in (
        (center + Vector((size * 0.35, -size * 0.65, size * 0.95)), 420, 3.2),
        (center + Vector((-size * 0.65, -size * 0.30, size * 0.40)), 210, 2.4),
        (center + Vector((size * 0.25, size * 0.55, size * 0.70)), 260, 2.8),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = area
        _look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Preview do barril")
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out-glb", type=Path, required=True)
    parser.add_argument("--out-blend", type=Path, required=True)
    parser.add_argument("--out-texture", type=Path, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    cli = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(cli)
    for path in (args.input, args.reference):
        if not path.is_file():
            raise FileNotFoundError(path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.input))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB de origem não contém malha")
    geometry_before = [(len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    camera_location = center + Vector(((hi.x - lo.x) * 0.20,
                                       -(hi.y - lo.y) * 0.33,
                                       (hi.z - lo.z) * 0.16))

    # Reference depicts the end cap on the right, barrel running left to right.
    image, alpha_bounds = _make_opaque_reference(args.reference, args.out_texture)
    _project_uv(meshes, camera_location, center, image, alpha_bounds)
    material = _material(image)
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj["palette_reference"] = str(args.reference)
        obj["source_glb_sha256"] = hashlib.sha256(args.input.read_bytes()).hexdigest()

    geometry_after = [(len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]
    if geometry_before != geometry_after:
        raise RuntimeError(f"A geometria mudou durante a colorização: {geometry_before} -> {geometry_after}")

    args.out_blend.parent.mkdir(parents=True, exist_ok=True)
    args.out_glb.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out_blend))
    bpy.ops.export_scene.gltf(
        filepath=str(args.out_glb), export_format="GLB", export_materials="EXPORT",
        export_apply=False, export_texcoords=True, export_normals=True,
        export_tangents=False, export_cameras=False, export_lights=False,
    )
    _preview(meshes, args.preview)
    print("source_glb_sha256", hashlib.sha256(args.input.read_bytes()).hexdigest())
    print("geometry", geometry_before)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_texture", args.out_texture)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
