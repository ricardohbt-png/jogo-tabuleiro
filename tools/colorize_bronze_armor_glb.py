"""Colorize the bronze armor miniature from the game's PNG reference.

Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_bronze_armor_glb.py -- \
        <source.glb> assets/itens/bronze_armor.glb assets/itens/bronze_armor_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def _srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _reference_palette(reference: Path) -> dict[str, tuple[tuple[float, float, float], float]]:
    image = bpy.data.images.load(str(reference), check_existing=False)
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape((-1, 4))
    warm = pixels[(pixels[:, 3] > 0.78)
                  & (pixels[:, 0] > pixels[:, 1] * 1.04)
                  & (pixels[:, 1] > pixels[:, 2] * 1.04), :3]
    bpy.data.images.remove(image)
    if len(warm) < 1000:
        raise RuntimeError("A imagem de referência não contém pixels bronze suficientes")

    luminance = warm @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    palette = {}
    for name, percentile, roughness in (("bronze", 0.78, 0.38),):
        threshold = float(np.quantile(luminance, percentile))
        band = warm[np.abs(luminance - threshold) <= 0.012]
        if len(band) < 8:
            band = warm[np.argsort(np.abs(luminance - threshold))[:128]]
        srgb = np.clip(np.median(band, axis=0), 0.0, 1.0)
        linear = tuple(_srgb_to_linear(float(channel)) for channel in srgb)
        palette[name] = (linear, roughness)
    return palette


def _make_material(name: str, color, roughness: float):
    material = bpy.data.materials.new(f"Armadura de Bronze - {name}")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = 0.62
    shader.inputs["Roughness"].default_value = roughness
    return material


def _assign_materials(meshes, palette):
    detailed = [obj for obj in meshes if len(obj.data.vertices) > 100]
    if not detailed:
        raise RuntimeError("O GLB não contém uma malha detalhada de armadura")
    materials = {name: _make_material(name, *settings) for name, settings in palette.items()}
    indexes = {name: index for index, name in enumerate(palette)}
    counts = {name: 0 for name in palette}

    for obj in detailed:
        mesh = obj.data
        mesh.materials.clear()
        for material in materials.values():
            mesh.materials.append(material)
        for face in mesh.polygons:
            name = "bronze"
            face.material_index = indexes[name]
            face.use_smooth = True
            counts[name] += 1

    if counts["bronze"] < 100:
        raise RuntimeError(f"Distribuição de materiais inesperada: {counts}")
    return counts


def _look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _render_preview(meshes, output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.45, -2.8, 1.65)) * span)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.35
    _look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in (
        (Vector((-0.8, -1.1, 1.5)) * span, 160, span),
        (Vector((1.1, 0.1, 0.7)) * span, 85, 0.8 * span),
        (Vector((0.0, 1.0, 1.2)) * span, 60, span),
    ):
        bpy.ops.object.light_add(type="AREA", location=center + offset)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        _look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, low.z - 0.035 * span))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Prévia - fundo")
    floor_mat.use_nodes = True
    floor_mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1)
    floor_mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 192
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia armadura bronze")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def _geometry_signature(meshes):
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    bounds = tuple(min(point[i] for point in points) for i in range(3)) + tuple(
        max(point[i] for point in points) for i in range(3))
    face_count = sum(len(obj.data.polygons) for obj in meshes)
    vertex_count = sum(len(obj.data.vertices) for obj in meshes)
    return vertex_count, face_count, bounds


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    reference = Path(__file__).resolve().parents[1] / "assets" / "itens" / "bronze_armor.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    original_geometry = _geometry_signature(meshes)
    counts = _assign_materials(meshes, _reference_palette(reference))
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = max(meshes, key=lambda obj: len(obj.data.vertices))
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format="GLB", use_selection=True,
        export_materials="EXPORT", export_normals=True, export_texcoords=True,
        export_cameras=False, export_lights=False,
    )

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    output_geometry = _geometry_signature(exported) if exported else None
    bounds_match = (output_geometry is not None and all(
        abs(a - b) <= 1e-4 for a, b in zip(original_geometry[2], output_geometry[2])))
    if (not exported or original_geometry[1] != output_geometry[1] or not bounds_match):
        raise RuntimeError(f"Geometria alterada: origem={original_geometry}, saída={output_geometry}")
    if not any(obj.data.materials for obj in exported):
        raise RuntimeError("O GLB exportado perdeu os materiais bronze")
    _render_preview(exported, preview)
    print(f"Malha preservada: faces={output_geometry[1]}, bounds={output_geometry[2]}; "
          f"vértices {original_geometry[0]} → {output_geometry[0]} por partição de materiais")
    print(f"Materiais por região: {counts}")
    print(f"Referência usada: {reference}")
    print(f"Modelo salvo: {destination}")
    print(f"Prévia salva: {preview}")


if __name__ == "__main__":
    main()
