"""Renderiza uma prévia neutra de um GLB de item para inspeção visual.

Uso (pelo Blender, da raiz):
    blender --background --factory-startup --python tools/render_item_preview.py -- item.glb preview.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Vector


def look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("Uso: ... render_item_preview.py -- <item.glb> <preview.png>")
    root = Path(__file__).resolve().parents[1]
    source, output = (Path(value) for value in args)
    source = source if source.is_absolute() else root / source
    output = output if output.is_absolute() else root / output
    if not source.is_file():
        raise FileNotFoundError(source)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB sem malhas")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, 0.01)

    bpy.ops.object.camera_add(location=center + Vector((0.10 * span, -0.24 * span, 2.5 * span)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.22
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for location, energy, size in [
        (center + Vector((-0.55 * span, -0.75 * span, 1.6 * span)), 55, span),
        (center + Vector((0.70 * span, 0.15 * span, 1.15 * span)), 30, 0.8 * span),
        (center + Vector((0.10 * span, 0.85 * span, 1.4 * span)), 38, 0.7 * span),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.mesh.primitive_plane_add(size=span * 8, location=(center.x, center.y, low.z - 0.025 * span))
    floor = bpy.context.object
    material = bpy.data.materials.new("preview_floor")
    material.diffuse_color = (0.025, 0.032, 0.045, 1.0)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.025, 0.032, 0.045, 1.0)
    shader.inputs["Roughness"].default_value = 0.92
    floor.data.materials.append(material)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    scene.world.color = (0.006, 0.008, 0.012)
    scene.view_settings.look = "AgX - Medium High Contrast"
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"Prévia renderizada em {output}")


if __name__ == "__main__":
    main()
