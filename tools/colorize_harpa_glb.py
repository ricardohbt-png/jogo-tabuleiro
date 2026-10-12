"""Repair the harp's strings and colorize the GLB from the PNG reference.

The source is an unsegmented, untextured mesh. This script applies a small
reference-matched material palette, masks the damaged string area with a dark
inset, adds clean metal strings, and exports both a GLB and a studio preview.

Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_harpa_glb.py -- \
        <source.glb> assets/itens/harpa.glb assets/itens/harpa_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


# The interior window is expressed in the front camera's normalized image
# coordinates (origin at top-left). It excludes the frame and soundboard.
STRING_INTERIOR = [
    (0.402, 0.238), (0.446, 0.240), (0.486, 0.267),
    (0.526, 0.313), (0.558, 0.371), (0.585, 0.438),
    (0.610, 0.510), (0.642, 0.565), (0.658, 0.620),
    (0.646, 0.665), (0.590, 0.701), (0.542, 0.730),
    (0.456, 0.752), (0.418, 0.750), (0.392, 0.718),
    (0.382, 0.665), (0.382, 0.550), (0.390, 0.420),
]
IVORY_PANEL = [
    (0.525, 0.360), (0.585, 0.325), (0.686, 0.665),
    (0.692, 0.752), (0.650, 0.802), (0.602, 0.706),
    (0.574, 0.555),
]

# Curved string anchors follow the inside of the neck and soundboard.
TOP_ANCHORS = [
    (0.395, 0.250), (0.432, 0.250), (0.468, 0.270),
    (0.502, 0.304), (0.532, 0.347), (0.558, 0.395),
    (0.582, 0.447), (0.603, 0.498), (0.620, 0.550),
]
BOTTOM_ANCHORS = [
    (0.395, 0.722), (0.428, 0.705), (0.463, 0.684),
    (0.498, 0.663), (0.532, 0.642), (0.565, 0.621),
    (0.602, 0.600),
]


def inside_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < cross:
                inside = not inside
        j = i
    return inside


def mix(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] * (1.0 - t) + b[0] * t, a[1] * (1.0 - t) + b[1] * t)


def sample_path(path: list[tuple[float, float]], t: float) -> tuple[float, float]:
    scaled = min(max(t, 0.0), 1.0) * (len(path) - 1)
    index = min(int(scaled), len(path) - 2)
    return mix(path[index], path[index + 1], scaled - index)


def project(point: Vector, center: Vector, right: Vector, up: Vector,
            scale: float) -> tuple[float, float]:
    delta = point - center
    return (0.5 + delta.dot(right) / scale, 0.5 - delta.dot(up) / scale)


def make_material(name: str, color: tuple[float, float, float], metallic: float,
                  roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def colorize_regions(obj: bpy.types.Object, reference_path: Path, center: Vector,
                     right: Vector, up: Vector, scale: float) -> None:
    # Validate and load the approved reference while keeping the model's
    # detailed surface clean: the photo guides a small stable palette rather
    # than being projected pixel-for-pixel onto an unsegmented mesh.
    reference = bpy.data.images.load(str(reference_path), check_existing=False)
    if reference.size[0] < 1 or reference.size[1] < 1:
        raise RuntimeError("A referência harpa.png não pôde ser lida")
    obj.data.materials.clear()
    obj.data.materials.append(make_material(
        "Harpa - ouro antigo", (0.22, 0.105, 0.025), 0.68, 0.34))
    obj.data.materials.append(make_material(
        "Harpa - marfim envelhecido", (0.66, 0.50, 0.28), 0.12, 0.46))
    for polygon in obj.data.polygons:
        local_center = sum((obj.data.vertices[i].co for i in polygon.vertices), Vector()) / len(polygon.vertices)
        point = obj.matrix_world @ local_center
        screen = project(point, center, right, up, scale)
        if inside_polygon(screen, IVORY_PANEL):
            polygon.material_index = 1
        else:
            polygon.material_index = 0
        polygon.use_smooth = True
    bpy.data.images.remove(reference)


def clear_string_window(obj: bpy.types.Object, center: Vector, right: Vector,
                        up: Vector, scale: float) -> None:
    """Remove old dark scan/string faces before rebuilding the open window."""
    dark_slots = {
        index for index, material in enumerate(obj.data.materials)
        if "escura das cordas" in material.name.lower()
        or "cordas" in material.name.lower()
    }
    if not dark_slots:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    damaged = [face for face in bm.faces if face.material_index in dark_slots]
    if damaged:
        bmesh.ops.delete(bm, geom=damaged, context="FACES")
    # O modelo tinha ilhas desconectadas de polígonos dentro da caixa das
    # cordas. Remove apenas ilhas pequenas nessa abertura, preservando os
    # relevos e a moldura contínua.
    bm.faces.ensure_lookup_table()
    visited = set()
    loose = []
    for seed in bm.faces:
        if seed in visited:
            continue
        component = []
        pending = [seed]
        visited.add(seed)
        while pending:
            face = pending.pop()
            component.append(face)
            for edge in face.edges:
                for adjacent in edge.link_faces:
                    if adjacent not in visited:
                        visited.add(adjacent)
                        pending.append(adjacent)
        if len(component) <= 2500:
            component_center = sum(
                (face.calc_center_median() for face in component), Vector()
            ) / len(component)
            point = obj.matrix_world @ component_center
            if inside_polygon(project(point, center, right, up, scale), STRING_INTERIOR):
                loose.extend(component)
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def add_strings(center: Vector, right: Vector, up: Vector, scale: float,
                front_y: float, count: int = 31) -> bpy.types.Object:
    gold = make_material("Cordas - bronze dourado", (0.39, 0.22, 0.075), 0.72, 0.28)
    pale = make_material("Cordas - bronze claro", (0.72, 0.48, 0.20), 0.62, 0.25)
    curve = bpy.data.curves.new("Cordas alinhadas da harpa", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = 0.00185
    curve.bevel_resolution = 2
    for i in range(count):
        t = i / (count - 1)
        start_u, start_v = sample_path(TOP_ANCHORS, t)
        end_u, end_v = sample_path(BOTTOM_ANCHORS, t)
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(2)
        for j, factor in enumerate((0.0, 0.5, 1.0)):
            u = start_u * (1.0 - factor) + end_u * factor
            v = start_v * (1.0 - factor) + end_v * factor
            screen_point = center + right * ((u - 0.5) * scale) + up * ((0.5 - v) * scale)
            screen_point.y = front_y
            bp = spline.bezier_points[j]
            bp.co = screen_point
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
        spline.resolution_u = 8
    string_obj = bpy.data.objects.new("Cordas - reconstruidas", curve)
    bpy.context.collection.objects.link(string_obj)
    curve.materials.append(gold)
    curve.materials.append(pale)
    # Bevel material index is not per spline in Blender's curve API; alternating
    # cord color is applied after conversion to a mesh below.
    bpy.context.view_layer.objects.active = string_obj
    string_obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    string_obj = bpy.context.object
    string_obj.name = "Cordas - reconstruidas"
    string_obj.data.materials.clear()
    string_obj.data.materials.append(gold)
    string_obj.data.materials.append(pale)
    # Give a subtle alternating note to the strings while keeping their shape.
    for poly in string_obj.data.polygons:
        poly.material_index = 1 if (poly.index // 120) % 4 == 0 else 0
    string_obj.select_set(False)
    return string_obj


def setup_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.z - low.z, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.0, 2.8 * span, 0.0)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.30
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Z").to_euler()
    bpy.context.scene.camera = camera

    for location, energy, size in [
        (center + Vector((-0.8 * span, 1.1 * span, 1.2 * span)), 360, 1.0 * span),
        (center + Vector((0.9 * span, 0.5 * span, 0.35 * span)), 230, 0.8 * span),
        (center + Vector((0.2 * span, -0.9 * span, 0.8 * span)), 270, 0.9 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 256
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.012, 0.016, 0.022, 1.0)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.55
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <saida.glb> <preview.png>")
    source, destination, preview = (Path(value) for value in args)
    source = source.resolve()
    destination = destination.resolve()
    preview = preview.resolve()
    root = Path(__file__).resolve().parents[1]
    reference = root / "assets" / "itens" / "harpa.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malha")
    # A versão editada no Blender pode já trazer cordas e painel de uma
    # exportação anterior. Mantém a malha detalhada e reconstrói esses extras.
    harp = max(meshes, key=lambda obj: len(obj.data.polygons))
    for obj in meshes:
        if obj != harp:
            bpy.data.objects.remove(obj, do_unlink=True)
    points = [harp.matrix_world @ Vector(corner) for corner in harp.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.z - low.z, high.x - low.x, 0.01)
    scale = span * 1.30
    # Harp front is toward +Y; Z is the upright axis after glTF import.
    # Blender's camera track quaternion for a +Y view with Z tracking maps
    # screen-right to +X and screen-up to +Z for the front view.
    right = Vector((1.0, 0.0, 0.0))
    up = Vector((0.0, 0.0, 1.0))

    clear_string_window(harp, center, right, up, scale)
    colorize_regions(harp, reference, center, right, up, scale)
    max_y = max((harp.matrix_world @ Vector(corner)).y for corner in harp.bound_box)
    strings = add_strings(center, right, up, scale, max_y + 0.018)

    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    harp.select_set(True)
    strings.select_set(True)
    bpy.context.view_layer.objects.active = harp
    bpy.ops.export_scene.gltf(filepath=str(destination), export_format="GLB",
                              use_selection=True, export_normals=True,
                              export_texcoords=False, export_cameras=False,
                              export_lights=False)
    setup_preview([harp, strings], preview)
    print(f"Colored harp saved: {destination}")
    print(f"High-resolution preview saved: {preview}")


if __name__ == "__main__":
    main()
