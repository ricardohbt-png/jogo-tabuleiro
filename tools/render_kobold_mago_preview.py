"""Render a neutral studio preview of an external Kobold Magician GLB.

Run with Blender 5.1:
  blender -b --python tools/render_kobold_mago_preview.py -- INPUT OUTPUT.png
"""
from __future__ import annotations

import argparse
import sys

import bpy
from mathutils import Vector


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    options = parser.parse_args(args)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=options.input)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError("GLB sem malhas")
    # The imported Cube is an unrelated six-face helper in this file; hide it
    # only in the preview and keep it untouched in the exported asset.
    for obj in meshes:
        if obj.name == "Cube":
            obj.hide_render = True

    points = [obj.matrix_world @ Vector(corner)
              for obj in meshes if obj.name != "Cube" for corner in obj.bound_box]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) * 0.5
    height = max(maximum.z - minimum.z, 0.001)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = options.output
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"

    world = bpy.data.worlds.new("Kobold preview world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.17, 0.18, 0.20, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    scene.world = world

    bpy.ops.object.camera_add(location=center + Vector((height * 1.8, -height * 2.6, height * 0.9)))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = height * 1.52
    look_at(camera, center + Vector((0.0, 0.0, height * 0.04)))
    scene.camera = camera

    for location, energy, size in [
        (center + Vector((height * 1.2, -height * 1.8, height * 2.2)), 680, height * 1.5),
        (center + Vector((-height * 1.8, -height * 0.4, height * 1.1)), 300, height * 1.8),
        (center + Vector((height * 0.2, height * 1.8, height * 1.8)), 520, height * 1.4),
    ]:
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        look_at(light, center)

    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
