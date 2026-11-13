"""Render a neutral studio preview of the giant black scorpion miniature."""
from pathlib import Path
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets/models3d/monstros/escorpiao_gigante_preto.glb"
OUTPUT = ROOT / "assets/models3d/monstros/escorpiao_gigante_preto_preview.png"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(MODEL))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("O GLB não trouxe malhas para renderizar")

bpy.context.view_layer.update()
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
minimum = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
maximum = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
center = (minimum + maximum) * 0.5
span = max(maximum - minimum)

floor_z = minimum.z - span * 0.035
bpy.ops.mesh.primitive_plane_add(size=span * 5, location=(center.x, center.y, floor_z))
floor = bpy.context.object
floor.name = "Preview Floor"
floor_mat = bpy.data.materials.new("Warm stone preview")
floor_mat.diffuse_color = (0.48, 0.45, 0.39, 1)
floor_mat.use_nodes = True
floor_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.48, 0.45, 0.39, 1)
floor_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
floor.data.materials.append(floor_mat)

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Preview Camera")
camera = bpy.data.objects.new("Preview Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = center + Vector((span * 1.6, -span * 2.2, span * 1.25))
aim(camera, center)
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 3.1
bpy.context.scene.camera = camera

for name, offset, power, size in (
    ("Key", (-span * 1.8, -span * 1.2, span * 2.6), 950, span * 1.5),
    ("Rim", (span * 1.6, span * 1.2, span * 2.0), 1150, span * 1.2),
    ("Fill", (span * 1.2, -span * 0.4, span * 0.8), 360, span * 1.6),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = center + Vector(offset)
    aim(light, center)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 64
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUTPUT)
scene.world.color = (0.12, 0.12, 0.12)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
bpy.ops.render.render(write_still=True)
print(f"saved {OUTPUT}")
