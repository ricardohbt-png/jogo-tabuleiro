"""Texturiza a miniatura GLB da cota de malha com a referência PNG, mantendo a malha."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\RICARDO\Downloads\cota_malha.glb")
REFERENCE = ROOT / "assets" / "itens" / "chainmail.png"
OUT = ROOT / "assets" / "itens"

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)
if not REFERENCE.is_file():
    raise FileNotFoundError(REFERENCE)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Esperava uma malha, encontrei {len(meshes)}")
obj = meshes[0]
mesh = obj.data
original_topology = (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))

# A malha não tem UVs. Projetamos a imagem frontal no plano XZ, que corresponde
# à frente do torso; a projeção também mantém o padrão de elos nas costas.
xs = [vertex.co.x for vertex in mesh.vertices]
zs = [vertex.co.z for vertex in mesh.vertices]
x_min, x_max = min(xs), max(xs)
z_min, z_max = min(zs), max(zs)
if x_max <= x_min or z_max <= z_min:
    raise RuntimeError("A malha não tem dimensões válidas para a projeção XZ")

image = bpy.data.images.load(str(REFERENCE), check_existing=True)
image.pack()
width, height = image.size
# Caixa do torso opaco na referência, sem o fundo e a sombra no chão.
u_min, u_max = 17 / width, 388 / width
pixel_y_top, pixel_y_bottom = 26, 479
v_top, v_bottom = 1 - pixel_y_top / height, 1 - pixel_y_bottom / height

uv_layer = mesh.uv_layers.active or mesh.uv_layers.new(name="ChainmailProjection")
for polygon in mesh.polygons:
    for loop_index in polygon.loop_indices:
        vertex = mesh.vertices[mesh.loops[loop_index].vertex_index]
        fx = (vertex.co.x - x_min) / (x_max - x_min)
        fz = (vertex.co.z - z_min) / (z_max - z_min)
        uv_layer.data[loop_index].uv = (
            u_min + fx * (u_max - u_min),
            v_bottom + fz * (v_top - v_bottom),
        )
    polygon.use_smooth = True

material = bpy.data.materials.new("Aço da cota de malha")
material.diffuse_color = (0.43, 0.44, 0.45, 1.0)
material.use_nodes = True
nodes = material.node_tree.nodes
principled = nodes.get("Principled BSDF")
principled.inputs["Metallic"].default_value = 0.55
principled.inputs["Roughness"].default_value = 0.42
texture = nodes.new("ShaderNodeTexImage")
texture.name = "Textura Chainmail"
texture.label = "Referência: chainmail.png"
texture.image = image
texture.interpolation = "Linear"
material.node_tree.links.new(texture.outputs["Color"], principled.inputs["Base Color"])
if "Alpha" in principled.inputs:
    material.node_tree.links.new(texture.outputs["Alpha"], principled.inputs["Alpha"])
if hasattr(material, "surface_render_method"):
    material.surface_render_method = "DITHERED"
mesh.materials.clear()
mesh.materials.append(material)
for polygon in mesh.polygons:
    polygon.material_index = 0

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.world = bpy.data.worlds.new("Fundo de estúdio")
scene.world.color = (0.12, 0.12, 0.12)

def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(2.3, -4.8, 1.05))
camera = bpy.context.object
camera.name = "Câmera de prévia"
camera.data.type = "ORTHO"
camera.data.ortho_scale = 2.38
point_at(camera, (0, 0, 0))
scene.camera = camera

for name, location, power, size, color in (
    ("Principal", (-3.0, -3.2, 3.5), 650, 2.4, (1.0, 0.91, 0.79)),
    ("Preenchimento", (3.2, -2.0, 1.0), 420, 2.8, (0.78, 0.86, 1.0)),
    ("Recorte", (0.0, 2.7, 2.8), 520, 2.0, (1.0, 0.95, 0.84)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = power
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    point_at(light, (0, 0, 0))

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
blend_path = OUT / "cota_malha.blend"
glb_path = OUT / "cota_malha.glb"
preview_path = OUT / "cota_malha_preview.png"
scene.render.filepath = str(preview_path)
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_materials="EXPORT",
    export_image_format="AUTO",
)

final_topology = (len(mesh.vertices), len(mesh.edges), len(mesh.polygons))
if final_topology != original_topology:
    raise RuntimeError(f"A malha foi alterada: {original_topology} -> {final_topology}")
print("COTA_MALHA_COLORIDA", "topologia=", original_topology, "glb=", glb_path)
