"""Colorize and render the Bandido miniature from the matching PNG reference.

The Downloads GLB is a single unpainted mesh. This script keeps its vertices and
faces intact and projects the in-game bandido.png artwork onto it with a planar
front projection encoded as a normal glTF UV layer.
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
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Z").to_euler()


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
    # The cutout PNG has transparent black around and between parts of the
    # silhouette. Give those UV samples a deep leather tone so the projection
    # remains opaque on the sides/back of the sculpt.
    alpha = rgba[:, :, 3:4]
    fallback = np.array([0.020, 0.014, 0.010], dtype=np.float32)
    rgb = rgba[:, :, :3] * alpha + fallback * (1.0 - alpha)

    image = bpy.data.images.new("Bandido reference projection", width=width,
                                height=height, alpha=False, float_buffer=False)
    opaque = np.concatenate((rgb, np.ones((height, width, 1), dtype=np.float32)), axis=2)
    image.pixels.foreach_set(opaque.reshape(-1))
    image.file_format = "PNG"
    image.filepath_raw = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save()
    image.pack()
    bpy.data.images.remove(source)
    return image


def _project_uv(mesh, uv_name="BandidoFrontProjection"):
    coords = np.array([vertex.co[:] for vertex in mesh.vertices], dtype=np.float64)
    x_min, z_min = coords[:, 0].min(), coords[:, 2].min()
    x_max, z_max = coords[:, 0].max(), coords[:, 2].max()
    x_span, z_span = max(x_max - x_min, 1e-8), max(z_max - z_min, 1e-8)

    # Alpha bounds of bandido.png (threshold 64): x=103..938, y=29..1500.
    # UV V grows from the image bottom, while model Z grows upward.
    u_lo, u_hi = 103 / 1024, 938 / 1024
    v_lo, v_hi = 1 - 1500 / 1536, 1 - 29 / 1536
    layer = mesh.uv_layers.get(uv_name) or mesh.uv_layers.new(name=uv_name)
    for loop in mesh.loops:
        co = coords[loop.vertex_index]
        u = u_lo + ((co[0] - x_min) / x_span) * (u_hi - u_lo)
        v = v_lo + ((co[2] - z_min) / z_span) * (v_hi - v_lo)
        layer.data[loop.index].uv = (float(u), float(v))
    return layer


def _material(image):
    mat = bpy.data.materials.new("Bandido • cores da referência")
    mat.use_nodes = True
    mat.diffuse_color = (0.20, 0.13, 0.08, 1.0)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.86
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Paleta original do Bandido"
    tex.label = "assets/pawns/monstros/bandido/bandido.png"
    tex.image = image
    tex.interpolation = "Linear"
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _preview(meshes, output: Path):
    lo, hi = _bounds(meshes)
    center = (lo + hi) * 0.5
    height = max(hi.z - lo.z, 0.001)
    # The artwork is projected from the front (-Y), so keep the preview close
    # to that axis; a large side angle stretches the planar color projection.
    bpy.ops.object.camera_add(location=center + Vector((0.35, -5.0, 1.05)))
    camera = bpy.context.object
    _look_at(camera, center + Vector((0, 0, height * 0.02)))
    camera.data.lens = 54
    bpy.context.scene.camera = camera

    lights = [
        (center + Vector((0.8, -3.0, 3.3)), 260, 2.3),
        (center + Vector((-1.8, -2.4, 1.7)), 150, 2.0),
        (center + Vector((0.5, 1.6, 2.7)), 180, 1.8),
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
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Bandido preview world")
    scene.world.color = (0.012, 0.010, 0.009)
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
    before = [(len(obj.data.vertices), len(obj.data.polygons)) for obj in meshes]

    image = _make_opaque_reference(args.reference, args.out_texture)
    material = _material(image)
    for obj in meshes:
        _project_uv(obj.data)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj["palette_reference"] = str(args.reference)
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
    _preview(meshes, args.preview)
    print("source", args.input)
    print("source_sha256", hashlib.sha256(args.input.read_bytes()).hexdigest())
    print("geometry", before)
    print("saved_glb", args.out_glb)
    print("saved_blend", args.out_blend)
    print("saved_texture", args.out_texture)
    print("saved_preview", args.preview)


if __name__ == "__main__":
    main()
