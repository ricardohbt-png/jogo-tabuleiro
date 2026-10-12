"""Color the ring GLB to match the gold-and-ruby reference in assets/itens/ring.png.

Preserves the source mesh and assigns PBR materials by face. Run from the repo root:
    blender --background --factory-startup --python tools/colorize_anel_glb.py -- \
        <source.glb> assets/itens/anel.glb assets/itens/anel_preview.png
"""
from __future__ import annotations

import sys
import math
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "gold_base": ((0.28, 0.10, 0.012), 0.50, 0.40),
    "gold_highlight": ((0.46, 0.22, 0.04), 0.42, 0.38),
    "gold_shadow": ((0.08, 0.025, 0.003), 0.40, 0.50),
    "ruby_base": ((0.14, 0.001, 0.006), 0.05, 0.30),
    "ruby_highlight": ((0.24, 0.004, 0.014), 0.04, 0.28),
    "ruby_shadow": ((0.04, 0.001, 0.005), 0.04, 0.34),
}


def make_material(name: str, color, metallic: float, roughness: float):
    material = bpy.data.materials.new(f"Anel - {name.replace('_', ' ')}")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def assign_materials(meshes: list[bpy.types.Object]) -> tuple[int, int]:
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center_x = (low.x + high.x) * 0.5
    center_y = (low.y + high.y) * 0.5
    scale_x = max((high.x - low.x) * 0.5, 1e-6)
    scale_y = max((high.y - low.y) * 0.5, 1e-6)
    materials = {name: make_material(name, *settings) for name, settings in PALETTE.items()}
    indices = {name: index for index, name in enumerate(PALETTE)}
    used: set[str] = set()
    ruby_faces = 0

    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for material in materials.values():
            mesh.materials.append(material)
        normal_matrix = obj.matrix_world.to_3x3()
        for polygon in mesh.polygons:
            point = obj.matrix_world @ polygon.center
            normal = (normal_matrix @ polygon.normal).normalized()
            x = (point.x - center_x) / scale_x
            y = (point.y - center_y) / scale_y

            # The prominent stone sits on the front-left shoulder of the band
            # in the reference view. Limit the ruby to the raised face of that
            # setting so its surrounding prongs remain gold.
            dx, dy = x + 0.31, y + 0.70
            radial = dx * -0.40 + dy * -0.92
            tangent = dx * -0.92 + dy * 0.40
            in_ruby = (radial / 0.23) ** 2 + (tangent / 0.12) ** 2 < 1.0 and point.z > low.z + 0.22 * (high.z - low.z)

            if in_ruby:
                ruby_faces += 1
                facet = normal.z + 0.22 * math.sin(point.x * 39.0 + point.y * 53.0)
                name = "ruby_highlight" if facet > 0.62 else "ruby_shadow" if facet < -0.05 else "ruby_base"
            else:
                # Facets facing upward catch warm highlights; recessed and
                # downward-facing parts keep the ornamental band readable.
                facet = normal.z + 0.10 * math.sin(point.x * 24.0 + point.y * 31.0)
                name = "gold_highlight" if facet > 0.48 else "gold_shadow" if facet < -0.22 else "gold_base"
            polygon.material_index = indices[name]
            polygon.use_smooth = not in_ruby
            used.add(name)

    if ruby_faces < 10:
        raise RuntimeError(f"A pedra vermelha foi localizada em apenas {ruby_faces} faces")
    return len(used), ruby_faces


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.0, 0.0, 2.6 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.24
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in [
        (Vector((-0.7, -0.7, 1.5)) * span, 100, span),
        (Vector((0.8, 0.1, 0.9)) * span, 55, 0.8 * span),
        (Vector((0.0, 0.9, 0.7)) * span, 40, 0.8 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=center + offset)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 40, location=(center.x, center.y, low.z - 0.035 * span))
    floor = bpy.context.object
    floor_material = bpy.data.materials.new("Prévia - fundo")
    floor_material.use_nodes = True
    shader = floor_material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia anel")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <prévia.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    root = Path(__file__).resolve().parents[1]
    reference = root / "assets" / "itens" / "ring.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    material_count, ruby_faces = assign_materials(meshes)
    if material_count < 3:
        raise RuntimeError(f"A classificação encontrou só {material_count} regiões de material")

    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format="GLB", use_selection=True,
        export_materials="EXPORT", export_normals=True, export_texcoords=False,
        export_cameras=False, export_lights=False,
    )

    # Reimport the actual export to confirm the mesh and materials survived.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not exported or not exported[0].data.materials:
        raise RuntimeError("O GLB exportado perdeu a malha ou os materiais")
    render_preview(exported, preview)
    print(f"Materiais aplicados: {material_count} regiões; faces rubi: {ruby_faces}; referência: {reference}")
    print(f"Anel colorido salvo em: {destination}")
    print(f"Prévia renderizada em: {preview}")


if __name__ == "__main__":
    main()
