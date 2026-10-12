"""Colorize the backpack GLB from the backpack PNG and render a front preview.

Run with Blender 5.1 from the repository root:
    blender --background --factory-startup --python tools/colorize_mochila_glb.py -- \
        <source.glb> assets/itens/mochila.glb assets/itens/mochila_preview.png

The source has a single unpainted triangular mesh. The reference photo is
projected onto its front surface; the hidden sides and back use a restrained
leather palette. The mesh itself is kept intact.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


LEATHER = (0.105, 0.047, 0.018, 1.0)
LEATHER_LIGHT = (0.19, 0.094, 0.038, 1.0)
LEATHER_DARK = (0.052, 0.023, 0.009, 1.0)
CANVAS = (0.16, 0.083, 0.034, 1.0)


def make_material(name: str) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.diffuse_color = LEATHER
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    for link in list(shader.inputs["Base Color"].links):
        material.node_tree.links.remove(link)
    color = nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Paint"
    material.node_tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.82
    return material


def make_front_material(image: bpy.types.Image) -> bpy.types.Material:
    material = bpy.data.materials.new("Mochila - pintura da referência")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    texture = nodes.new("ShaderNodeTexImage")
    texture.name = "Referência mochila.png"
    texture.image = image
    texture.interpolation = "Linear"
    material.node_tree.links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = 0.82
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    return material


def fallback_color(point: Vector, low: Vector, high: Vector) -> tuple[float, float, float, float]:
    height = (point.z - low.z) / max(high.z - low.z, 1e-6)
    # The exposed bedroll is lighter canvas; buckles and outer straps remain dark.
    if height > 0.77:
        return CANVAS
    if height > 0.48 and (abs(point.x) < 0.13 or abs(point.x) > 0.72):
        return LEATHER_DARK
    if (round(point.x * 12) + round(point.z * 15) + round(point.y * 9)) % 7 == 0:
        return LEATHER_LIGHT
    return LEATHER


def color_meshes(meshes: list[bpy.types.Object], texture_path: Path) -> None:
    vertices = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(point[i] for point in vertices) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in vertices) for i in range(3)))
    span_x = max(high.x - low.x, 1e-6)
    span_z = max(high.z - low.z, 1e-6)

    image = bpy.data.images.load(str(texture_path), check_existing=False)
    materials = make_material("Mochila - couro envelhecido (verso)")
    front_material = make_front_material(image)

    for obj in meshes:
        mesh = obj.data
        mesh.materials.clear()
        mesh.materials.append(materials)
        mesh.materials.append(front_material)
        uv_layer = mesh.uv_layers.active or mesh.uv_layers.new(name="FrontProjection")
        paint = mesh.color_attributes.get("Paint")
        if paint:
            mesh.color_attributes.remove(paint)
        paint = mesh.color_attributes.new(name="Paint", type="FLOAT_COLOR", domain="CORNER")

        for polygon in mesh.polygons:
            center = obj.matrix_world @ polygon.center
            front = center.y < -0.08
            polygon.material_index = 1 if front else 0
            # Smooth normals reduce the faceted scan look without moving vertices.
            polygon.use_smooth = True
            for loop_index in polygon.loop_indices:
                point = obj.matrix_world @ mesh.vertices[mesh.loops[loop_index].vertex_index].co
                rgba = fallback_color(point, low, high)
                paint.data[loop_index].color = rgba
                if front:
                    u = 0.08 + 0.84 * (point.x - low.x) / span_x
                    v_top = 0.055 + 0.89 * (high.z - point.z) / span_z
                    uv_layer.data[loop_index].uv = (u, 1.0 - v_top)

    image.pack()


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(meshes: list[bpy.types.Object], output: Path) -> None:
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.z - low.z, 0.01)

    bpy.ops.object.camera_add(location=center + Vector((0.12 * span, -2.5 * span, 0.52 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.30
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for location, energy, size in [
        (center + Vector((-0.75 * span, -1.1 * span, 1.45 * span)), 360, span),
        (center + Vector((0.8 * span, -0.2 * span, 0.8 * span)), 230, 0.8 * span),
        (center + Vector((0.1 * span, 0.9 * span, 1.1 * span)), 180, 0.8 * span),
        (center + Vector((0.0, -2.0 * span, 0.45 * span)), 260, 1.8 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 80, location=(center.x, center.y, low.z - 0.025 * span))
    floor = bpy.context.object
    floor_material = bpy.data.materials.new("Prévia - fundo")
    floor_material.diffuse_color = (0.025, 0.032, 0.045, 1.0)
    floor_material.use_nodes = True
    floor_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    floor_material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(floor_material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world = bpy.data.worlds.new("Prévia mochila")
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
    texture = root / "assets" / "itens" / "mochila_texture.png"
    if not source.is_file() or not texture.is_file():
        raise FileNotFoundError(source if not source.is_file() else texture)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("O GLB não contém malhas")
    color_meshes(meshes, texture)

    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(
        filepath=str(destination), export_format="GLB", use_selection=True,
        export_normals=True, export_texcoords=True, export_vertex_color="NAME",
        export_vertex_color_name="Paint",
        export_cameras=False, export_lights=False,
    )
    # Render the exported file itself so the preview also checks that its
    # vertex colors and material survived the GLB round trip.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(destination))
    exported_meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not exported_meshes or not any(obj.data.color_attributes for obj in exported_meshes):
        raise RuntimeError("O GLB exportado perdeu a malha ou as cores por vértice")
    render_preview(exported_meshes, preview)
    print(f"Mochila colorida salva em: {destination}")
    print(f"Prévia renderizada em: {preview}")


if __name__ == "__main__":
    main()
