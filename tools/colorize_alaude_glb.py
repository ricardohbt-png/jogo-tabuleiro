"""Color the dropped lute model to match assets/itens/alaude.png.

Keeps the supplied mesh, assigning PBR materials by its front-facing regions.
Run from the repository root with Blender 5.1:
    blender --background --factory-startup --python tools/colorize_alaude_glb.py -- \
        <source.glb> assets/itens/alaude.glb assets/itens/alaude_preview.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "soundboard": ((0.16, 0.004, 0.003), 0.0, 0.50),
    "soundboard_light": ((0.25, 0.009, 0.005), 0.0, 0.44),
    "soundboard_shadow": ((0.075, 0.002, 0.001), 0.0, 0.58),
    "dark_wine_back": ((0.045, 0.008, 0.004), 0.0, 0.72),
    "mahogany": ((0.075, 0.018, 0.006), 0.0, 0.56),
    "fretboard": ((0.018, 0.006, 0.003), 0.0, 0.64),
    "gold_trim": ((0.30, 0.13, 0.022), 0.66, 0.38),
    "gold_dark": ((0.15, 0.045, 0.007), 0.60, 0.48),
    "string_bronze": ((0.19, 0.095, 0.025), 0.68, 0.32),
}


def material(name: str, color, metallic: float, roughness: float):
    mat = bpy.data.materials.new(f"Alaúde - {name.replace('_', ' ')}")
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def assign_materials(meshes: list[bpy.types.Object], reference: Path) -> dict[str, int]:
    # Read the PNG as the palette source; the unsegmented scan is colored by
    # region so the photo's wood grain and ornament are not projected as noise.
    image = bpy.data.images.load(str(reference), check_existing=False)
    if image.size[0] < 1 or image.size[1] < 1:
        raise RuntimeError("A referência alaude.png não pôde ser lida")
    detailed = [obj for obj in meshes if len(obj.data.vertices) > 100]
    if not detailed:
        raise RuntimeError("Não encontrei a malha detalhada do alaúde")
    points = [obj.matrix_world @ vertex.co for obj in detailed for vertex in obj.data.vertices]
    center_x = (min(p.x for p in points) + max(p.x for p in points)) * 0.5
    width = max(max(p.x for p in points) - min(p.x for p in points), 1e-6)
    mats = {key: material(key, *settings) for key, settings in PALETTE.items()}
    indexes = {key: i for i, key in enumerate(PALETTE)}
    counts = {key: 0 for key in PALETTE}

    for obj in detailed:
        mesh = obj.data
        mesh.materials.clear()
        for mat in mats.values():
            mesh.materials.append(mat)
        normal_matrix = obj.matrix_world.to_3x3()
        for face in mesh.polygons:
            point = obj.matrix_world @ face.center
            normal = (normal_matrix @ face.normal).normalized()
            x = point.x - center_x
            y = point.y
            # The pear-shaped body is below the neck in the supplied scan.
            # Its outer front rim receives the gold inlay from the reference.
            if y < 0.105:
                local_half_width = 0.42 * width
                rim = abs(x) > 0.79 * local_half_width
                if rim:
                    key = "gold_trim" if abs(x) > 0.88 * local_half_width else "gold_dark"
                else:
                    key = "soundboard_shadow" if y < -0.19 else "soundboard"
            elif y < 0.225:
                # A dark fingerboard runs down the center of the neck. Fine
                # bronze bands follow the strings through the neck and body.
                relative_x = x / width
                string_step = 0.034
                nearest_string = round((relative_x + 0.15) / string_step)
                string_x = -0.15 + nearest_string * string_step
                on_string = (0 <= nearest_string <= 9
                             and abs(relative_x - string_x) < 0.006
                             and -0.20 < y < 0.22)
                if on_string:
                    key = "string_bronze"
                elif abs(x) < 0.145 * width:
                    key = "fretboard"
                else:
                    key = "mahogany"
            else:
                # Warm headstock wood with aged-gold tuning hardware at its
                # outer edges, matching the bright tuning pieces in the photo.
                hardware = y < 0.315 and abs(x) > 0.145 * width
                if hardware:
                    key = "gold_trim" if normal.z > -0.35 else "gold_dark"
                else:
                    key = "mahogany" if normal.z > -0.35 else "dark_wine_back"

            face.material_index = indexes[key]
            face.use_smooth = key not in ("gold_trim", "gold_dark", "string_bronze")
            counts[key] += 1

    bpy.data.images.remove(image)
    if counts["soundboard"] < 50 or counts["gold_trim"] < 10 or counts["fretboard"] < 10:
        raise RuntimeError(f"Classificação incompleta das regiões do alaúde: {counts}")
    return counts


def look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, 0.01)
    bpy.ops.object.camera_add(location=center + Vector((0.08, -0.20, 2.5 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.22
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for offset, energy, size in [
        (Vector((-0.60, -0.65, 1.5)) * span, 120, span),
        (Vector((0.75, 0.12, 1.0)) * span, 72, 0.8 * span),
        (Vector((0.0, 0.85, 0.8)) * span, 45, 0.8 * span),
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
    floor_shader = floor_material.node_tree.nodes.get("Principled BSDF")
    floor_shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    floor_shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 192
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia alaúde")
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 3:
        raise SystemExit("Uso: ... -- <origem.glb> <destino.glb> <preview.png>")
    source, destination, preview = (Path(value).resolve() for value in args)
    reference = Path(__file__).resolve().parents[1] / "assets" / "itens" / "alaude.png"
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
    bpy.context.view_layer.objects.active = next(
        obj for obj in meshes if len(obj.data.vertices) > 100
    )
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
    print(f"Alaúde colorido; faces por região: {counts}")
    print(f"Modelo salvo: {destination}")
    print(f"Prévia salva: {preview}")


if __name__ == "__main__":
    main()
