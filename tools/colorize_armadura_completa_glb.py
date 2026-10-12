"""Color the full plate GLB with the game's existing armor artwork palette.

The specifically named armadura_completa.png reference was not present when
this asset was prepared, so assets/objetos/armadura.png supplies the palette.
Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_armadura_completa_glb.py -- \
        <source.glb> assets/itens/armadura_completa.glb assets/itens/armadura_completa_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "steel_base": ((0.16, 0.19, 0.22), 0.82, 0.34),
    "steel_light": ((0.34, 0.38, 0.41), 0.78, 0.29),
    "steel_shadow": ((0.055, 0.068, 0.080), 0.76, 0.46),
    "steel_edge": ((0.23, 0.27, 0.30), 0.84, 0.27),
    "gold_trim": ((0.36, 0.19, 0.045), 0.72, 0.34),
    "gold_shadow": ((0.16, 0.068, 0.012), 0.66, 0.46),
}


def make_material(name: str, color, metallic: float, roughness: float):
    mat = bpy.data.materials.new(f"Armadura completa - {name.replace('_', ' ')}")
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign_materials(meshes: list[bpy.types.Object], reference: Path) -> dict[str, int]:
    image = bpy.data.images.load(str(reference), check_existing=False)
    if image.size[0] < 1 or image.size[1] < 1:
        raise RuntimeError(f"A referência não pôde ser lida: {reference}")
    detailed = [obj for obj in meshes if len(obj.data.vertices) > 100]
    if not detailed:
        raise RuntimeError("Não encontrei a malha detalhada da armadura")
    points = [obj.matrix_world @ vertex.co for obj in detailed for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    size = high - low
    center_x = (low.x + high.x) * 0.5
    center_y = (low.y + high.y) * 0.5
    center_z = (low.z + high.z) * 0.5
    mats = {name: make_material(name, *settings) for name, settings in PALETTE.items()}
    indexes = {name: index for index, name in enumerate(PALETTE)}
    counts = {name: 0 for name in PALETTE}
    view = Vector((0.24, -0.38, 0.89)).normalized()

    for obj in detailed:
        mesh = obj.data
        mesh.materials.clear()
        for mat in mats.values():
            mesh.materials.append(mat)
        normal_matrix = obj.matrix_world.to_3x3()
        for face in mesh.polygons:
            point = obj.matrix_world @ face.center
            normal = (normal_matrix @ face.normal).normalized()
            nx = (point.x - center_x) / max(size.x * 0.5, 1e-6)
            ny = (point.y - center_y) / max(size.y * 0.5, 1e-6)
            nz = (point.z - center_z) / max(size.z * 0.5, 1e-6)
            facing = normal.dot(view)

            # Gold follows the exposed outside edges and the upper shoulder
            # line; the broad plate surfaces remain steel like the reference.
            trim = (facing > 0.18 and
                    ((abs(nx) > 0.88 and abs(nz) < 0.88)
                     or (nz > 0.84 and abs(nx) < 0.74)))
            if trim:
                name = "gold_trim" if facing > 0.52 else "gold_shadow"
            elif facing > 0.68:
                name = "steel_light"
            elif facing < -0.18:
                name = "steel_shadow"
            elif abs(nx) > 0.88 or abs(nz) > 0.90:
                name = "steel_edge"
            else:
                name = "steel_base"
            face.material_index = indexes[name]
            face.use_smooth = name not in ("gold_trim", "gold_shadow")
            counts[name] += 1

    bpy.data.images.remove(image)
    if counts["steel_base"] < 100 or counts["gold_trim"] < 10:
        raise RuntimeError(f"Classificação insuficiente das regiões: {counts}")
    return counts


def look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.45, -2.8, 1.65)) * span)
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.30
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in [
        (Vector((-0.8, -1.1, 1.5)) * span, 150, span),
        (Vector((1.1, 0.1, 0.7)) * span, 80, 0.8 * span),
        (Vector((0.0, 1.0, 1.2)) * span, 55, span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=center + offset)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, low.z - 0.035 * span))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Prévia - fundo")
    floor_mat.use_nodes = True
    floor_shader = floor_mat.node_tree.nodes.get("Principled BSDF")
    floor_shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    floor_shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_mat)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 192
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia armadura completa")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    root = Path(__file__).resolve().parents[1]
    requested_reference = root / "assets" / "itens" / "armadura_completa.png"
    reference = requested_reference if requested_reference.is_file() else root / "assets" / "objetos" / "armadura.png"
    if not source.is_file() or not reference.is_file():
        raise FileNotFoundError(source if not source.is_file() else reference)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    counts = assign_materials(meshes, reference)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in meshes if len(obj.data.vertices) > 100)
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format="GLB", use_selection=True,
        export_materials="EXPORT", export_normals=True, export_texcoords=False,
        export_cameras=False, export_lights=False,
    )

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not exported or not any(obj.data.materials for obj in exported):
        raise RuntimeError("O GLB exportado perdeu a malha ou os materiais")
    render_preview(exported, preview)
    print(f"Materiais por região: {counts}")
    print(f"Referência usada: {reference}")
    print(f"Modelo salvo: {destination}")
    print(f"Prévia salva: {preview}")


if __name__ == "__main__":
    main()
