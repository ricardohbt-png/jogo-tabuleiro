"""Color the chainmail GLB to match assets/itens/chainmail.png.

Preserves the source mesh and assigns steel PBR materials by face orientation.
Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_cota_malha_glb.py -- \
        <source.glb> assets/itens/cota_malha.glb assets/itens/cota_malha_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "steel": ((0.22, 0.245, 0.265), 0.82, 0.36),
    "steel_light": ((0.39, 0.42, 0.44), 0.78, 0.30),
    "steel_shadow": ((0.085, 0.098, 0.11), 0.72, 0.48),
}


def make_material(name: str, color, metallic: float, roughness: float):
    mat = bpy.data.materials.new(f"Cota de malha - {name.replace('_', ' ')}")
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
        raise RuntimeError("A referência chainmail.png não pôde ser lida")
    detailed = [obj for obj in meshes if len(obj.data.vertices) > 100]
    if not detailed:
        raise RuntimeError("Não encontrei a malha detalhada da cota de malha")
    mats = {name: make_material(name, *settings) for name, settings in PALETTE.items()}
    indexes = {name: index for index, name in enumerate(PALETTE)}
    counts = {name: 0 for name in PALETTE}
    view = Vector((0.28, -0.38, 0.88)).normalized()

    for obj in detailed:
        mesh = obj.data
        mesh.materials.clear()
        for mat in mats.values():
            mesh.materials.append(mat)
        normal_matrix = obj.matrix_world.to_3x3()
        for face in mesh.polygons:
            normal = (normal_matrix @ face.normal).normalized()
            facing = normal.dot(view)
            if facing > 0.70:
                name = "steel_light"
            elif facing < -0.20:
                name = "steel_shadow"
            else:
                name = "steel"
            face.material_index = indexes[name]
            # Smooth shading keeps the individual knit relief readable without
            # adding texture artifacts over the scanned chain links.
            face.use_smooth = True
            counts[name] += 1

    bpy.data.images.remove(image)
    if counts["steel"] < 100 or counts["steel_light"] < 10 or counts["steel_shadow"] < 10:
        raise RuntimeError(f"A classificação do aço encontrou poucas faces: {counts}")
    return counts


def look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.35, -0.5, 2.7 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.22
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in [
        (Vector((-0.6, -0.8, 1.5)) * span, 130, span),
        (Vector((0.8, 0.1, 0.9)) * span, 70, 0.8 * span),
        (Vector((0.0, 0.9, 0.8)) * span, 48, 0.8 * span),
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
    scene.world = bpy.data.worlds.new("Prévia cota de malha")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    reference = Path(__file__).resolve().parents[1] / "assets" / "itens" / "chainmail.png"
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
    print(f"Faces coloridas por região: {counts}")
    print(f"Referência usada: {reference}")
    print(f"Modelo salvo: {destination}")
    print(f"Prévia salva: {preview}")


if __name__ == "__main__":
    main()
