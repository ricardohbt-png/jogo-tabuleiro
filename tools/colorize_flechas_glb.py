"""Recolor the arrow/quiver miniature from assets/itens/flechas.png.

Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_flechas_glb.py -- \
        <source.glb> assets/itens/flechas.glb assets/itens/flechas_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def _sample_color(pixels, mask, percentile: float):
    candidates = pixels[mask, :3]
    if len(candidates) < 100:
        raise RuntimeError("A referência não contém pixels suficientes para uma cor")
    luminance = candidates @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    threshold = float(np.quantile(luminance, percentile))
    band = candidates[np.abs(luminance - threshold) <= 0.015]
    if len(band) < 8:
        band = candidates[np.argsort(np.abs(luminance - threshold))[:128]]
    # Blender exposes imported PNG pixels in scene-linear color space already.
    # Keep those values as-is; converting them again would make the GLB too dark.
    linear = np.clip(np.median(band, axis=0), 0.0, 1.0)
    return tuple(float(channel) for channel in linear)


def _reference_palette(reference: Path):
    image = bpy.data.images.load(str(reference), check_existing=False)
    pixels = np.asarray(image.pixels[:], dtype=np.float32).reshape((-1, 4))
    spread = pixels[:, :3].max(axis=1) - pixels[:, :3].min(axis=1)
    warm = ((pixels[:, 3] > 0.72) & (pixels[:, 0] > pixels[:, 1] * 1.08)
            & (pixels[:, 1] > pixels[:, 2] * 1.05))
    neutral = (pixels[:, 3] > 0.72) & (spread < 0.20)
    wood = np.array(_sample_color(pixels, warm, 0.78), dtype=np.float32) * 0.58
    leather = np.array(_sample_color(pixels, warm, 0.58), dtype=np.float32) * 0.70
    feather = np.array(_sample_color(pixels, neutral, 0.90), dtype=np.float32)
    feather_lum = float(feather @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32))
    feather = np.array((feather_lum * 0.88, feather_lum * 0.92, feather_lum), dtype=np.float32)
    steel = np.array(_sample_color(pixels, neutral, 0.98), dtype=np.float32)
    steel_lum = float(steel @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32))
    steel = np.array((steel_lum * 0.88, steel_lum * 0.94, steel_lum), dtype=np.float32)
    palette = {
        "wood": (tuple(wood), 0.12, 0.58),
        "leather": (tuple(leather), 0.08, 0.70),
        "feather": (tuple(feather), 0.03, 0.65),
        "steel": (tuple(steel), 0.56, 0.42),
    }
    bpy.data.images.remove(image)
    return palette


def _material(name, color, metallic, roughness):
    material = bpy.data.materials.new(f"Flechas - {name}")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def _face_components(mesh):
    """Return connected face groups using shared vertices."""
    parent = list(range(len(mesh.polygons)))

    def find(value):
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    first_face_for_vertex = {}
    for face in mesh.polygons:
        for vertex in face.vertices:
            previous = first_face_for_vertex.setdefault(vertex, face.index)
            union(face.index, previous)
    groups = {}
    for face in mesh.polygons:
        groups.setdefault(find(face.index), []).append(face.index)
    return sorted(groups.values(), key=len, reverse=True)


def _assign_materials(meshes, palette):
    detailed = [obj for obj in meshes if len(obj.data.vertices) > 100]
    if len(detailed) != 1:
        raise RuntimeError(f"Esperava uma malha de flechas, encontrei {len(detailed)}")
    obj = detailed[0]
    mesh = obj.data
    names = list(palette)
    materials = {name: _material(name, *settings) for name, settings in palette.items()}
    indexes = {name: index for index, name in enumerate(names)}
    mesh.materials.clear()
    for name in names:
        mesh.materials.append(materials[name])

    groups = _face_components(mesh)
    largest = set(groups[0])
    small_parts = [set(group) for group in groups[1:] if len(group) < 400]
    counts = {name: 0 for name in names}
    axis_values = [mesh.polygons[index].center.y for group in groups[1:] for index in group]
    if not axis_values:
        raise RuntimeError("Não foi possível localizar as flechas separadas da aljava")
    axis_min, axis_max = min(axis_values), max(axis_values)

    for face in mesh.polygons:
        center = face.center
        if face.index in largest:
            # O conjunto principal é a aljava com as flechas guardadas; couro
            # reveste o estojo e as pontas metálicas ficam expostas na boca.
            if center.x < -0.40:
                name = "leather"
            elif center.y > axis_min + 0.62 * (axis_max - axis_min):
                name = "leather"
            elif center.y < axis_min + 0.20 * (axis_max - axis_min):
                name = "steel"
            else:
                name = "wood"
        elif any(face.index in part for part in small_parts):
            # As penas têm detalhes pequenos desconectados da haste no GLB.
            name = "feather"
        else:
            along = (center.y - axis_min) / max(axis_max - axis_min, 1e-6)
            if along < 0.16:
                name = "steel"
            elif along > 0.79:
                name = "feather"
            else:
                name = "wood"
        face.material_index = indexes[name]
        face.use_smooth = True
        counts[name] += 1

    if min(counts["wood"], counts["leather"], counts["feather"], counts["steel"]) < 50:
        raise RuntimeError(f"Segmentação de cores insuficiente: {counts}; componentes={list(map(len, groups))}")
    return counts, list(map(len, groups))


def _look_at(obj, target: Vector):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _render_preview(meshes, output: Path):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.45, -2.8, 1.65)) * span)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.40
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
    shader = floor_mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_mat)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 160
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia flechas")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def _signature(meshes):
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    bounds = tuple(min(point[i] for point in points) for i in range(3)) + tuple(
        max(point[i] for point in points) for i in range(3))
    return sum(len(obj.data.vertices) for obj in meshes), sum(len(obj.data.polygons) for obj in meshes), bounds


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    reference = Path(__file__).resolve().parents[1] / "assets" / "itens" / "flechas.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    original = _signature(meshes)
    counts, components = _assign_materials(meshes, _reference_palette(reference))
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
    output_signature = _signature(exported) if exported else None
    bounds_match = (output_signature is not None and all(
        abs(a - b) <= 1e-4 for a, b in zip(original[2], output_signature[2])))
    if (not exported or original[1] != output_signature[1] or not bounds_match
            or not any(obj.data.materials for obj in exported)):
        raise RuntimeError(f"GLB exportado inválido: origem={original}, saída={output_signature}")
    _render_preview(exported, preview)
    print(f"Malha preservada: faces={output_signature[1]}, bounds={output_signature[2]}")
    print(f"Componentes conectados: {components}")
    print(f"Faces por material: {counts}")
    print(f"Referência usada: {reference}")
    print(f"Modelo salvo: {destination}")
    print(f"Prévia salva: {preview}")


if __name__ == "__main__":
    main()
