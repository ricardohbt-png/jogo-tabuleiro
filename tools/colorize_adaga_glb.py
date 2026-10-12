"""Colorize the dagger GLB from the dagger PNG and render a front preview.

Run with Blender 5.1 from the repository root:
    blender --background --factory-startup --python tools/colorize_adaga_glb.py -- \
        <source.glb> assets/itens/adaga.glb assets/itens/adaga_preview.png

The source is one dense, unpainted mesh. Spatial material regions preserve its
geometry while matching the steel blade, bronze guard, and wrapped brown grip
in assets/itens/dagger.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "blade_steel": ((0.30, 0.32, 0.34), 0.72, 0.38),
    "blade_edge": ((0.43, 0.45, 0.46), 0.72, 0.34),
    "blade_shadow": ((0.19, 0.21, 0.23), 0.65, 0.43),
    "guard_bronze": ((0.30, 0.16, 0.045), 0.48, 0.48),
    "guard_highlight": ((0.43, 0.26, 0.075), 0.42, 0.46),
    "grip_wood": ((0.025, 0.008, 0.002), 0.0, 0.72),
    "grip_wrap": ((0.009, 0.005, 0.003), 0.0, 0.82),
    "grip_wrap_worn": ((0.025, 0.012, 0.004), 0.0, 0.78),
    "pommel_bronze": ((0.34, 0.20, 0.055), 0.0, 0.82),
}


def make_material(name: str, color, metallic: float, roughness: float) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    for socket_name in ("Base Color", "Metallic", "Roughness"):
        for link in list(shader.inputs[socket_name].links):
            material.node_tree.links.remove(link)
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return material


def material_for_face(point: Vector, low: Vector, span: Vector) -> str:
    nx = (point.x - low.x) / max(span.x, 1e-6)
    nz = (point.z - low.z) / max(span.z, 1e-6)
    # The blade tip is at low X/Z and the hilt at high X/Z in this model.
    along = (nx + nz) * 0.5
    across = abs(nx - nz)

    if along < 0.475:
        if across < 0.026:
            return "blade_edge"       # central ridge catches the light
        if across > 0.071:
            return "blade_shadow"    # sharpened bevels at either side
        return "blade_steel"
    if along <= 0.535:
        return "guard_highlight" if across > 0.085 else "guard_bronze"
    if along >= 0.90:
        return "pommel_bronze"
    if 0.575 <= along <= 0.855:
        band = int((along - 0.575) / 0.034)
        return "grip_wrap" if band % 2 == 0 else "grip_wrap_worn"
    return "grip_wood"


def color_mesh(meshes: list[bpy.types.Object]) -> int:
    vertices = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in vertices) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in vertices) for i in range(3)))
    span = high - low
    materials = {
        name: make_material(f"Adaga - {name.replace('_', ' ')}", *settings)
        for name, settings in PALETTE.items()
    }
    material_indices = {name: index for index, name in enumerate(PALETTE)}
    assigned = set()

    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        for material in materials.values():
            mesh.materials.append(material)
        for polygon in mesh.polygons:
            center = obj.matrix_world @ polygon.center
            name = material_for_face(center, low, span)
            polygon.material_index = material_indices[name]
            polygon.use_smooth = True
            assigned.add(name)

    return len(assigned)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.z - low.z, 0.01)

    bpy.ops.object.camera_add(location=center + Vector((0.10 * span, -2.6 * span, 0.20 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.22
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for location, energy, size in [
        (center + Vector((-0.8 * span, -1.0 * span, 1.4 * span)), 420, span),
        (center + Vector((0.8 * span, -0.3 * span, 0.6 * span)), 260, 0.8 * span),
        (center + Vector((0.0, 0.9 * span, 1.0 * span)), 180, 0.8 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 40, location=(center.x, center.y, low.z - 0.025 * span))
    floor = bpy.context.object
    floor_material = bpy.data.materials.new("Prévia - fundo")
    floor_material.use_nodes = True
    shader = floor_material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia adaga")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <source.glb> <output.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    root = Path(__file__).resolve().parents[1]
    reference = root / "assets" / "itens" / "dagger.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    count = color_mesh(meshes)
    if count < 5:
        raise RuntimeError(f"A classificação da adaga encontrou só {count} regiões de material")

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

    # Reopen the exported file before rendering to verify its material slots.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not exported or not exported[0].data.materials:
        raise RuntimeError("O GLB exportado perdeu a malha ou os materiais")
    render_preview(exported, preview)
    print(f"Materiais aplicados: {count} regiões; referência: {reference}")
    print(f"Adaga colorida salva em: {destination}")
    print(f"Prévia renderizada em: {preview}")


if __name__ == "__main__":
    main()
