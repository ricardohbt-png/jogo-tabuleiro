"""Color the boots GLB to match assets/itens/boots.png while preserving geometry.

Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_botas_glb.py -- \
        <source.glb> assets/itens/botas.glb assets/itens/botas_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "leather_base": ((0.075, 0.027, 0.008), 0.0, 0.72),
    "leather_highlight": ((0.14, 0.055, 0.017), 0.0, 0.62),
    "leather_shadow": ((0.045, 0.016, 0.005), 0.0, 0.82),
    "leather_sole": ((0.018, 0.012, 0.008), 0.0, 0.86),
    "leather_lining": ((0.022, 0.008, 0.003), 0.0, 0.86),
    "buckle_brass": ((0.42, 0.22, 0.055), 0.62, 0.42),
}


def make_material(name: str, color, metallic: float, roughness: float):
    material = bpy.data.materials.new(f"Botas - {name.replace('_', ' ')}")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def assign_materials(meshes: list[bpy.types.Object]) -> tuple[int, dict[str, int]]:
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    height = max(high.z - low.z, 1e-6)
    preview_view = Vector((0.58, -0.68, 0.44)).normalized()
    materials = {name: make_material(name, *settings) for name, settings in PALETTE.items()}
    indices = {name: index for index, name in enumerate(PALETTE)}
    used: set[str] = set()
    counts = {name: 0 for name in PALETTE}

    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for material in materials.values():
            mesh.materials.append(material)
        normal_matrix = obj.matrix_world.to_3x3()
        for polygon in mesh.polygons:
            point = obj.matrix_world @ polygon.center
            normal = (normal_matrix @ polygon.normal).normalized()
            height_pos = (point.z - low.z) / height

            # Soles sit at the bottom of the boot shafts; the inside of each
            # cuff is dark leather. The raised buckle geometry is at the outer
            # ankle of each boot, above the foot and below the cuff.
            buckle_center = Vector((0.59, -0.90, 0.50))
            buckle = ((point - buckle_center).length < 0.10
                      and normal.dot(preview_view) > 0.25)
            sole = height_pos < 0.085
            lining = height_pos > 0.91

            if buckle:
                name = "buckle_brass"
            elif sole:
                name = "leather_sole"
            elif lining:
                name = "leather_lining"
            elif normal.z > 0.50:
                name = "leather_highlight"
            elif normal.z < -0.55:
                name = "leather_shadow"
            else:
                name = "leather_base"
            polygon.material_index = indices[name]
            polygon.use_smooth = name not in ("buckle_brass", "leather_sole")
            counts[name] += 1
            used.add(name)

    if counts["buckle_brass"] < 8:
        raise RuntimeError("Não encontrei faces suficientes para colorir as fivelas de bronze")
    return len(used), counts


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, 0.01)
    camera_direction = Vector((0.58, -0.68, 0.44)).normalized()
    bpy.ops.object.camera_add(location=center + camera_direction * (3.5 * span))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.22
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in [
        (Vector((-0.65, -0.8, 1.4)) * span, 115, span),
        (Vector((0.75, 0.2, 0.9)) * span, 65, 0.8 * span),
        (Vector((0.0, 0.9, 0.75)) * span, 40, 0.8 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=center + offset)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 40, location=(center.x, center.y, low.z - 0.025 * span))
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
    scene.world = bpy.data.worlds.new("Prévia botas")
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
    reference = root / "assets" / "itens" / "boots.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    material_count, counts = assign_materials(meshes)
    if material_count < 4:
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

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not exported or not exported[0].data.materials:
        raise RuntimeError("O GLB exportado perdeu a malha ou os materiais")
    render_preview(exported, preview)
    print(f"Materiais aplicados: {material_count} regiões; faces: {counts}; referência: {reference}")
    print(f"Botas coloridas salvas em: {destination}")
    print(f"Prévia renderizada em: {preview}")


if __name__ == "__main__":
    main()
