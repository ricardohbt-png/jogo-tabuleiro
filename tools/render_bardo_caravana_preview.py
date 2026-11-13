"""Renderiza uma prévia frontal transparente do Bardo da Caravana."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets/models3d/monstros/bardo_da_caravana.glb"
OUTPUT = ROOT / "assets/models3d/monstros/bardo_da_caravana_preview.png"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(MODEL))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError("O GLB não trouxe malhas para renderizar")

bpy.context.view_layer.update()
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
lo = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
hi = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
center = (lo + hi) * 0.5
span = max(hi - lo)

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Bardo da Caravana Preview Camera")
camera = bpy.data.objects.new("Bardo da Caravana Preview Camera", camera_data)
bpy.context.collection.objects.link(camera)
camera.location = center + Vector((span * 0.12, -span * 3.0, span * 0.10))
aim(camera, center)
camera_data.type = "ORTHO"
camera_data.ortho_scale = span * 1.38
bpy.context.scene.camera = camera

for name, offset, power, size in (
    ("Key", (-span * 1.0, -span * 1.5, span * 1.7), 800, span * 1.25),
    ("Rim", (span * 1.4, span * 0.7, span * 1.4), 1000, span * 1.0),
    ("Fill", (span * 1.0, -span * 0.2, span * 0.5), 240, span * 1.4),
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
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True
scene.render.filepath = str(OUTPUT)
scene.world.color = (0.035, 0.030, 0.025)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(write_still=True)
print(f"saved {OUTPUT}")
