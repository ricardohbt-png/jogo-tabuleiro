"""Create a low-profile medieval sewer grate prop and export its GLB."""
from pathlib import Path
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "objetos"
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, metallic=0.0, roughness=0.85):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m


STONE = mat("Weathered grey limestone", (0.31, 0.30, 0.27))
STONE_DARK = mat("Stone crevices", (0.17, 0.17, 0.15))
IRON = mat("Old rusted iron", (0.20, 0.105, 0.061), 0.72, 0.72)
WATER = mat("Sewer darkness", (0.025, 0.045, 0.04), 0.05, 1.0)


def cube(name, loc, dims, material, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Soft worn edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def cylinder(name, loc, radius, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("Rounded rivet", "BEVEL")
    bevel.width = 0.003
    bevel.segments = 1
    obj.modifiers.new("Rivet normals", "WEIGHTED_NORMAL")
    return obj


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Four chunky stone blocks form a square lip around the one-tile opening.
for name, loc, dims in [
    ("North stone curb", (0, 0, 0.07), (0.96, 0.16, 0.14)),
    ("South stone curb", (0, -0.84, 0.07), (0.96, 0.16, 0.14)),
    ("West stone curb", (-0.40, -0.42, 0.07), (0.16, 0.68, 0.14)),
    ("East stone curb", (0.40, -0.42, 0.07), (0.16, 0.68, 0.14)),
]:
    cube(name, loc, dims, STONE, 0.025)

# Dark well below the iron bars reads as a real opening at miniature scale.
cube("Black sewer beneath grate", (0, -0.42, -0.055), (0.65, 0.68, 0.025), WATER, 0.0)

# Heavy iron perimeter and evenly spaced crossbars.
for name, loc, dims in [
    ("Iron frame north", (0, -0.115, 0.145), (0.65, 0.045, 0.045)),
    ("Iron frame south", (0, -0.725, 0.145), (0.65, 0.045, 0.045)),
    ("Iron frame west", (-0.305, -0.42, 0.145), (0.045, 0.64, 0.045)),
    ("Iron frame east", (0.305, -0.42, 0.145), (0.045, 0.64, 0.045)),
]:
    cube(name, loc, dims, IRON, 0.012)
for i in range(5):
    x = -0.24 + i * 0.12
    cube(f"Grate crossbar {i+1}", (x, -0.42, 0.155), (0.035, 0.57, 0.045), IRON, 0.01)

# Rivets on the four corners make the frame legible from the isometric camera.
for x in (-0.30, 0.30):
    for y in (-0.12, -0.72):
        cylinder("Forged corner rivet", (x, y, 0.175), 0.025, 0.018, IRON)

# Camera and studio lighting for a transparent miniature preview.
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = True
scene.world.color = (0.05, 0.05, 0.05)

bpy.ops.object.camera_add(location=(2.5, -3.6, 3.0))
cam = bpy.context.object
cam.name = "Preview Camera"
cam.rotation_euler = (Vector((0, -0.42, 0.04)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
cam.data.ortho_scale = 1.7
scene.camera = cam

for loc, power, size in [((-3, -4, 5), 430, 4), ((3, 1, 3), 230, 3), ((0, -1, 4), 100, 2)]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = power
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector((0, -0.42, 0.04)) - light.location).to_track_quat("-Z", "Y").to_euler()

scene.render.filepath = str(OUT / "grade_esgoto_preview.png")
bpy.ops.render.render(write_still=True)

# Save the editable source file, then export only prop meshes (not camera/lights).
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "grade_esgoto.blend"))
meshes = [o for o in scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for obj in meshes:
    obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.export_scene.gltf(filepath=str(OUT / "grade_esgoto.glb"), export_format="GLB", use_selection=True)
